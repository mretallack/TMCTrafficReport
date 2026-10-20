#!/usr/bin/env python3
"""Extract map-resident RDS-TMC LCD indexes from an NNG SET/FBL file.

This implements the descriptor format recovered from the exact MediaNav 4
6.0.12.2.1166_r2 ARM runtime (FUN_002f2e84/FUN_002f01a8).
It decodes the licensed 4096-byte block transform used by the exact ARM
runtime, searches structured SET member headers for length-prefixed descriptor
payloads, and exports decoded LCDs.

A candidate is accepted only when all LCD streams are monotonic without uint16
wrap and descriptor service fields are plausible. Use --cc/--ltn to select a
specific service.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import struct
from dataclasses import dataclass
from pathlib import Path


DEFAULT_KEY = Path(__file__).parents[2] / "MediaNavToolkit/analysis/xor_table_normal.bin"


class BitReader:
    def __init__(self, data: bytes):
        self.data = data
        self.bit = 0

    def read(self, width: int) -> int:
        if width < 0 or self.bit + width > len(self.data) * 8:
            raise EOFError
        value = 0
        for shift in range(width):
            pos = self.bit + shift
            value |= ((self.data[pos >> 3] >> (pos & 7)) & 1) << shift
        self.bit += width
        return value

    def extended(self, base_width: int, width_step: int) -> int:
        width = base_width
        total = 0
        value = self.read(width)
        while value == (1 << width) - 1:
            total += value
            width += width_step
            if width > 28:
                raise ValueError("invalid extended integer width")
            value = self.read(width)
        return total + value

    def lcd_delta(self) -> int:
        if self.read(1):
            return 1
        value = self.extended(4, 12)
        return value + (1 if value else 0)


@dataclass
class Descriptor:
    index: int
    cc: int
    ltn: int
    count: int
    map_reference: int
    ordinal_base: int
    lcds: list[int]


@dataclass
class Candidate:
    member_index: int
    member_start: int
    header_field_offset: int
    relative_offset: int
    payload_offset: int
    payload_size: int
    payload_sha256: str
    bits_consumed: int
    descriptors: list[Descriptor]


def decrypt(raw: bytes, key: bytes) -> bytes:
    """Decode FUN_005aa138's licensed IGOMAP random-access transform.

    Block zero is a direct wordwise XOR.  Its decoded word 3 supplies the seed
    used by later blocks.  For each later 4 KiB block, the key-word order is
    rotated by the 10-bit block number and that number plus the seed is added
    to each ciphertext word before XOR.  The 10-bit wrap follows the ARM
    ``(offset << 10) >> 22`` operations exactly.
    """
    if len(key) != 4096 or len(raw) < 16 or len(raw) % 4:
        raise ValueError("licensed FBL transform requires a 4096-byte key and word-aligned file")

    key_words = struct.unpack("<1024I", key)
    output = bytearray(len(raw))
    seed = 0
    for block_start in range(0, len(raw), 4096):
        word_count = min(1024, (len(raw) - block_start) // 4)
        ciphertext = struct.unpack_from(f"<{word_count}I", raw, block_start)
        block_number = (block_start >> 12) & 0x3FF
        adjustment = 0 if block_start == 0 else (seed + block_number) & 0xFFFFFFFF
        plaintext = [
            ((word + adjustment) & 0xFFFFFFFF) ^ key_words[(index + block_number) & 0x3FF]
            for index, word in enumerate(ciphertext)
        ]
        struct.pack_into(f"<{word_count}I", output, block_start, *plaintext)
        if block_start == 0:
            seed = plaintext[3]
    return bytes(output)


def decode_payload(payload: bytes, *, max_descriptors: int = 64) -> tuple[list[Descriptor], int]:
    reader = BitReader(payload)
    descriptor_count = reader.extended(4, 4)
    if not 1 <= descriptor_count <= max_descriptors:
        raise ValueError(f"implausible descriptor count {descriptor_count}")

    descriptors: list[Descriptor] = []
    ordinal_base = 0
    for index in range(descriptor_count):
        raw_cc = reader.read(4)
        ltn = reader.read(6)
        location_count = reader.read(16)
        map_reference = reader.read(32)
        # Exact FUN_002f01a8 semantics: bit 31 extends the 4-bit CC into
        # the 0x10..0x1f range; it is then removed from the reference.
        cc = raw_cc
        if map_reference & 0x80000000:
            map_reference &= 0x7FFFFFFF
            cc += 0x10
        current = 0
        lcds: list[int] = []
        for _ in range(location_count):
            next_lcd = (current + reader.lcd_delta()) & 0xFFFF
            if next_lcd < current:
                raise ValueError("LCD stream wrapped")
            lcds.append(next_lcd)
            current = next_lcd
        descriptors.append(
            Descriptor(index, cc, ltn, location_count, map_reference, ordinal_base, lcds)
        )
        ordinal_base += location_count
    return descriptors, reader.bit


def set_member_ranges(data: bytes) -> list[tuple[int, int, int]]:
    if data[:4] != b"SET\x00":
        raise ValueError("not an NNG SET container after XOR decryption")
    count = struct.unpack_from("<I", data, 0x0C)[0]
    if not 1 <= count <= 128:
        raise ValueError(f"implausible SET member count {count}")

    # SET v4.6.7.32 stores one 32-bit member value per entry from 0x10,
    # followed by a zero sentinel and count+1 physical boundaries.
    directory_offset = 0x10 + count * 4
    directory = struct.unpack_from(f"<{count + 2}I", data, directory_offset)
    boundaries = [value for value in directory if 0 < value <= len(data)]
    if len(boundaries) < count + 1:
        raise ValueError("incomplete SET member boundary table")
    return [(index, boundaries[index], boundaries[index + 1]) for index in range(count)]


def find_candidates(data: bytes, header_scan_size: int = 0x1000) -> list[Candidate]:
    candidates: list[Candidate] = []
    seen: set[tuple[int, int, int]] = set()
    for member_index, start, end in set_member_ranges(data):
        header_end = min(start + header_scan_size, end - 4)
        for field_pos in range(start, header_end):
            relative = struct.unpack_from("<I", data, field_pos)[0]
            target = start + relative
            if relative < 0x80 or target + 4 > end:
                continue
            size = struct.unpack_from("<I", data, target)[0]
            if not 8 <= size <= 4_000_000 or target + 4 + size > end:
                continue
            key = (start, target, size)
            if key in seen:
                continue
            seen.add(key)
            payload = data[target + 4 : target + 4 + size]
            try:
                descriptors, bits = decode_payload(payload)
            except (EOFError, ValueError, OverflowError):
                continue
            # Require at least one normal ALERT-C service descriptor. Random
            # length-prefixed data occasionally parses but rarely satisfies
            # this plus monotonic full-stream validation.
            if not any(d.cc <= 15 and d.ltn <= 63 and d.count for d in descriptors):
                continue
            candidates.append(
                Candidate(
                    member_index,
                    start,
                    field_pos - start,
                    relative,
                    target + 4,
                    size,
                    hashlib.sha256(payload).hexdigest(),
                    bits,
                    descriptors,
                )
            )
    return candidates


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fbl", type=Path)
    parser.add_argument("--key", type=Path, default=DEFAULT_KEY)
    parser.add_argument("--cc", type=lambda x: int(x, 0))
    parser.add_argument("--ltn", type=lambda x: int(x, 0))
    parser.add_argument("--member", type=lambda x: int(x, 0), help="select one SET member index")
    parser.add_argument("--csv", type=Path, help="write one row per decoded LCD")
    args = parser.parse_args()

    raw = args.fbl.read_bytes()
    data = decrypt(raw, args.key.read_bytes())
    candidates = find_candidates(data)

    selected: list[tuple[Candidate, Descriptor]] = []
    for candidate in candidates:
        if args.member is not None and candidate.member_index != args.member:
            continue
        matching = [
            descriptor
            for descriptor in candidate.descriptors
            if (args.cc is None or descriptor.cc == args.cc)
            and (args.ltn is None or descriptor.ltn == args.ltn)
        ]
        if not matching:
            continue
        print(
            f"member={candidate.member_index} member_start=0x{candidate.member_start:x} "
            f"header_field=+0x{candidate.header_field_offset:x} "
            f"relative=0x{candidate.relative_offset:x} payload=0x{candidate.payload_offset:x} "
            f"size={candidate.payload_size} sha256={candidate.payload_sha256} "
            f"descriptors={len(candidate.descriptors)} bits={candidate.bits_consumed}"
        )
        for descriptor in matching:
            print(
                f"  descriptor={descriptor.index} cc={descriptor.cc} ltn={descriptor.ltn} "
                f"count={descriptor.count} map_reference=0x{descriptor.map_reference:08x} "
                f"ordinal_base={descriptor.ordinal_base} "
                f"range={descriptor.lcds[0] if descriptor.lcds else '-'}.."
                f"{descriptor.lcds[-1] if descriptor.lcds else '-'}"
            )
            selected.append((candidate, descriptor))

    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", newline="") as output:
            writer = csv.writer(output, lineterminator="\n")
            writer.writerow(
                [
                    "member",
                    "payload_offset",
                    "descriptor",
                    "cc",
                    "ltn",
                    "map_reference",
                    "descriptor_ordinal_base",
                    "descriptor_index",
                    "map_ordinal",
                    "lcd",
                ]
            )
            for candidate, descriptor in selected:
                for index, lcd in enumerate(descriptor.lcds):
                    writer.writerow(
                        [
                            candidate.member_index,
                            candidate.payload_offset,
                            descriptor.index,
                            descriptor.cc,
                            descriptor.ltn,
                            descriptor.map_reference,
                            descriptor.ordinal_base,
                            index,
                            descriptor.ordinal_base + index,
                            lcd,
                        ]
                    )
        print(f"wrote {args.csv} ({sum(len(d.lcds) for _, d in selected)} rows)")

    if not selected:
        raise SystemExit("no matching descriptor found")


if __name__ == "__main__":
    main()

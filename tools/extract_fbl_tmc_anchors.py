#!/usr/bin/env python3
"""Export partial TMCLOCATION records from an NNG FBL TMC index.

Requires the map-resident descriptor extractor in extract_fbl_tmc_index.py.
For each selected LCD this decodes the indexed record start, predecessor and
successor LCD references, first affected-element category, and first raw GEODB
road anchor. It resolves that anchor through the type-9 area offset tables and
decodes the referenced road record's individual coordinate from FUN_0030ae88.
Anchorless records inherit the nearest such location through decoded
predecessor/successor links with an explicit hop count. Road names and full
link geometry remain future work.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

from extract_fbl_tmc_index import BitReader, Candidate, Descriptor, decrypt, find_candidates


@dataclass
class BlockDirectory:
    relative_offsets: list[int]
    auxiliary_offsets: list[int]


@dataclass
class RoadCodebook:
    nodes: list[int]
    descriptor_has_extra: list[bool]


def compact_tree(reader: BitReader) -> list[int]:
    """Decode the compact DFS tree used by the current GEODB codebooks."""
    if reader.read(1) == 0:
        return []
    nodes: list[int] = []
    current: int | None = None
    while True:
        ascended = False
        while True:
            bit = reader.read(1)
            next_node = current
            if ascended:
                assert current is not None
                next_node = (nodes[current] & ~3) // 4
                nodes[current] = (nodes[current] & 3) | ((len(nodes) - current) << 2)
                nodes[current] = (nodes[current] & ~2) | (bit << 1)
            if bit == 0:
                break
            if next_node is None or not 0 <= next_node < len(nodes):
                if reader.read(1):
                    reader.extended(7, 4)
                    return nodes
                return nodes + [0]
            current = next_node
            if not ascended:
                ascended = True
                nodes[current] |= 1
        parent = -0x20000000 if next_node is None else next_node
        nodes.append((parent << 2) & 0xFFFFFFFF)
        current = len(nodes) - 1


def compact_tree_count(reader: BitReader) -> int:
    """Consume a compact DFS tree and return its decoded element count."""
    return len(compact_tree(reader))


def tmc_location_widths(data: bytes, member_start: int) -> tuple[int, int, int, int]:
    """Recover FUN_0032943c's map-specific metadata and coordinate widths."""
    common = member_start + 0x256
    type2_relative = int.from_bytes(data[common + 0x14 : common + 0x18], "little")
    type2 = member_start + type2_relative
    size = int.from_bytes(data[type2 : type2 + 4], "little")
    reader = BitReader(data[type2 + 4 : type2 + 4 + size])
    for _ in range(compact_tree_count(reader)):
        reader.extended(16, 6)
        reader.extended(4, 4)
    metadata_width = reader.extended(6, 1)
    metadata_step = reader.extended(4, 1)

    import struct
    west, north, east, south = struct.unpack_from("<4i", data, common + 0x28)
    x_width = max(1, ((east - west) >> 6).bit_length())
    y_width = max(1, ((north - south) >> 6).bit_length())
    return metadata_width, metadata_step, x_width, y_width



def road_area_layout(data: bytes, member_start: int) -> tuple[list[int], int]:
    """Decode FUN_002fb39c's area-offset tables and return offsets/base."""
    common = member_start + 0x256
    type2_relative = int.from_bytes(data[common + 0x14 : common + 0x18], "little")
    type2 = member_start + type2_relative
    size = int.from_bytes(data[type2 : type2 + 4], "little")
    reader = BitReader(data[type2 + 4 : type2 + 4 + size])
    for _ in range(compact_tree_count(reader)):
        reader.extended(16, 6)
        reader.extended(4, 4)
    reader.extended(6, 1)
    reader.extended(4, 1)
    area_limits = [reader.extended(15, 7) for _ in range(8)]
    max_area = area_limits[-1]

    table_relative = int.from_bytes(data[common + 0x40 : common + 0x44], "little")
    road_base = int.from_bytes(data[common + 0x48 : common + 0x4C], "little")
    offsets: list[int] = []
    for high in range((max_area >> 8) + 1):
        count = (max_area & 0xFF) + 1 if high == (max_area >> 8) else 256
        position = member_start + table_relative + high * 0x204
        current = int.from_bytes(data[position : position + 4], "little")
        offsets.append(current)
        for low in range(1, count):
            delta_pos = position + 4 + (low - 1) * 2
            current += int.from_bytes(data[delta_pos : delta_pos + 2], "little")
            offsets.append(current)
    if len(offsets) != max_area + 1 or any(a > b for a, b in zip(offsets, offsets[1:])):
        raise ValueError("invalid GEODB road-area offset table")
    return offsets, member_start + road_base


def read_signed_extended(reader: BitReader, width: int, step: int) -> int:
    negative = reader.read(1)
    value = reader.extended(width, step)
    return ~value if negative else value


def decode_road_codebook(data: bytes, member_start: int) -> RoadCodebook:
    """Decode the type-13 selector tree used by FUN_0030ae88."""
    common = member_start + 0x256
    type2_relative = int.from_bytes(data[common + 0x14 : common + 0x18], "little")
    type2 = member_start + type2_relative
    type2_size = int.from_bytes(data[type2 : type2 + 4], "little")
    reader = BitReader(data[type2 + 4 + type2_size :])

    # Four FUN_0034acc8/FUN_002ea2e0 arrays.
    for _ in range(4):
        for _ in compact_tree(reader):
            reader.read(10)
            reader.read(9)
            reader.read(9)
            reader.extended(7, 3)
            reader.extended(7, 3)
            reader.read(8)
    # Two FUN_0034af38/FUN_002eaa6c arrays.
    for _ in range(2):
        for _ in compact_tree(reader):
            reader.read(3)
            reader.extended(2, 2)
            reader.extended(2, 2)
    # One FUN_0034b690/FUN_002ea5f8 array.
    for _ in compact_tree(reader):
        reader.extended(4, 4)

    nodes = compact_tree(reader)
    descriptor_has_extra: list[bool] = []
    for _ in nodes:
        read_signed_extended(reader, 2, 2)
        reader.extended(2, 2)
        reader.extended(2, 2)
        flags = [reader.read(1) for _ in range(9)]
        descriptor_has_extra.append(bool(flags[2]))
        read_signed_extended(reader, 3, 2)
    return RoadCodebook(nodes, descriptor_has_extra)


def decode_codebook_index(reader: BitReader, codebook: RoadCodebook) -> int:
    node = 0
    result = 0
    while True:
        while reader.read(1) == 0:
            if codebook.nodes[node] & 1:
                return result
            node += 1
        result += codebook.nodes[node] >> 2
        if codebook.nodes[node] & 2:
            return result
        node += codebook.nodes[node] >> 2


def decode_road_area_records(
    data: bytes,
    offsets: list[int],
    road_base: int,
    area: int,
    codebook: RoadCodebook,
) -> list[dict[str, int | float | bool]]:
    """Decode FUN_0030ae88 through the +0x84 road-record coordinate array."""
    if area <= 0 or area >= len(offsets):
        raise ValueError(f"invalid GEODB road area {area}")
    start = road_base + offsets[area - 1]
    end = road_base + offsets[area]
    reader = BitReader(data[start:end])
    bounds = [signed32(reader.read(32)) for _ in range(4)]
    west, north, east, south = bounds

    counts = [reader.extended(8, 1) for _ in range(9)]
    record_count = counts[0]
    y_delta_width = reader.extended(4, 4)
    y_delta_step = reader.extended(4, 4)
    reader.extended(4, 4)
    reader.extended(4, 4)
    reader.extended(8, 8)
    reader.extended(8, 8)
    for _ in range(4):
        reader.extended(3, 1)
    auxiliary_count = reader.extended(4, 4)
    area_id_width = max(1, len(offsets).bit_length())
    for _ in range(auxiliary_count):
        reader.read(area_id_width)

    raw_x_width = max(1, (east - west).bit_length())
    x_width = 1 if raw_x_width < 7 else raw_x_width - 6
    boundaries = counts[5:9]
    boundary_index = 0
    y = north
    scale = float(1 << 23)
    records: list[dict[str, int | float | bool]] = []
    for record_index in range(record_count):
        x = west + reader.read(x_width) * 0x40
        if boundary_index < len(boundaries) and record_index == boundaries[boundary_index]:
            y = north
            while (
                boundary_index < len(boundaries)
                and record_index == boundaries[boundary_index]
            ):
                boundary_index += 1
        y -= reader.extended(y_delta_width, y_delta_step) * 0x40
        descriptor_index = decode_codebook_index(reader, codebook)
        if descriptor_index >= len(codebook.descriptor_has_extra):
            raise ValueError(f"invalid road descriptor {descriptor_index}")
        if codebook.descriptor_has_extra[descriptor_index]:
            reader.read(16)
            reader.extended(8, 2)
        records.append(
            {
                "road_record_index": record_index,
                "road_record_lon": x / scale,
                "road_record_lat": y / scale,
                "road_descriptor_index": descriptor_index,
                "record_inside_area_bbox": west <= x <= east and south <= y <= north,
            }
        )
    return records


def resolve_area_bbox(
    data: bytes, offsets: list[int], road_base: int, area: int | None
) -> dict[str, int | float | None]:
    result: dict[str, int | float | None] = {
        "area_file_offset": None,
        "area_size": None,
        "bbox_west": None,
        "bbox_south": None,
        "bbox_east": None,
        "bbox_north": None,
        "area_center_lon": None,
        "area_center_lat": None,
    }
    if area is None or area <= 0 or area >= len(offsets):
        return result
    # FUN_0030d708 resolves object ID A from boundary offsets [A-1, A].
    start = road_base + offsets[area - 1]
    end = road_base + offsets[area]
    if end <= start or end > len(data):
        return result
    import struct
    west, north, east, south = struct.unpack_from("<4i", data, start)
    scale = float(1 << 23)
    result.update({
        "area_file_offset": start,
        "area_size": end - start,
        "bbox_west": west / scale,
        "bbox_south": south / scale,
        "bbox_east": east / scale,
        "bbox_north": north / scale,
        "area_center_lon": (west + east) / (2.0 * scale),
        "area_center_lat": (south + north) / (2.0 * scale),
    })
    return result

def signed_extended(reader: BitReader) -> int:
    """FUN_0033caa4(reader, 3, 8)."""
    negative = reader.read(1)
    value = reader.extended(3, 8)
    return ~value if negative else value


def add_representative_locations(rows: list[dict]) -> None:
    """Fill anchorless LCDs from the nearest decoded predecessor/successor node."""
    import collections
    import heapq

    by_lcd = {int(row["lcd"]): row for row in rows}
    adjacent: dict[int, set[int]] = collections.defaultdict(set)
    for row in rows:
        lcd = int(row["lcd"])
        for field in ("previous_lcd", "next_lcd"):
            linked = row[field]
            if linked is not None and int(linked) in by_lcd:
                adjacent[lcd].add(int(linked))
                adjacent[int(linked)].add(lcd)

    queue: list[tuple[int, int, int]] = []
    best: dict[int, tuple[int, int]] = {}
    for row in rows:
        if row["area_center_lon"] is not None:
            lcd = int(row["lcd"])
            best[lcd] = (0, lcd)
            heapq.heappush(queue, (0, lcd, lcd))
    while queue:
        hops, source, lcd = heapq.heappop(queue)
        if best.get(lcd) != (hops, source):
            continue
        for linked in adjacent[lcd]:
            candidate = (hops + 1, source)
            if linked not in best or candidate < best[linked]:
                best[linked] = candidate
                heapq.heappush(queue, (candidate[0], candidate[1], linked))

    coordinate_fields = (
        "bbox_west", "bbox_south", "bbox_east", "bbox_north",
        "area_center_lon", "area_center_lat", "road_record_lon", "road_record_lat",
    )
    for row in rows:
        lcd = int(row["lcd"])
        match = best.get(lcd)
        row["representative_source"] = None
        row["representative_source_lcd"] = None
        row["representative_hops"] = None
        for field in coordinate_fields:
            row[f"representative_{field}"] = None
        if match is None:
            continue
        hops, source = match
        row["representative_source"] = "direct" if hops == 0 else "linked_lcd"
        row["representative_source_lcd"] = source
        row["representative_hops"] = hops
        source_row = by_lcd[source]
        for field in coordinate_fields:
            row[f"representative_{field}"] = source_row[field]




def add_chain_bearings(rows: list[dict]) -> None:
    """Add bearings to directly decoded predecessor/successor LCD points."""
    import math

    by_lcd = {int(row["lcd"]): row for row in rows}
    for row in rows:
        for relation in ("previous", "next"):
            row[f"{relation}_road_record_lon"] = None
            row[f"{relation}_road_record_lat"] = None
            row[f"bearing_to_{relation}_deg"] = None
            linked = row[f"{relation}_lcd"]
            if linked is None or int(linked) not in by_lcd:
                continue
            linked_row = by_lcd[int(linked)]
            if row["road_record_lon"] is None or linked_row["road_record_lon"] is None:
                continue
            lon1 = math.radians(float(row["road_record_lon"]))
            lat1 = math.radians(float(row["road_record_lat"]))
            lon2 = math.radians(float(linked_row["road_record_lon"]))
            lat2 = math.radians(float(linked_row["road_record_lat"]))
            delta_lon = lon2 - lon1
            y = math.sin(delta_lon) * math.cos(lat2)
            x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon)
            bearing = (math.degrees(math.atan2(y, x)) + 360.0) % 360.0
            row[f"{relation}_road_record_lon"] = linked_row["road_record_lon"]
            row[f"{relation}_road_record_lat"] = linked_row["road_record_lat"]
            row[f"bearing_to_{relation}_deg"] = bearing
def signed32(value: int) -> int:
    return value if value < 0x80000000 else value - 0x100000000


def decode_block_directory(candidate: Candidate) -> BlockDirectory:
    payload = candidate_data[candidate.payload_offset : candidate.payload_offset + candidate.payload_size]
    total_records = sum(descriptor.count for descriptor in candidate.descriptors)
    block_count = (total_records + 63) // 64
    reader = BitReader(payload)
    reader.bit = candidate.bits_consumed

    current = candidate.relative_offset + 4 + candidate.payload_size
    offsets = [current]
    for _ in range(block_count):
        current += reader.extended(8, 8)
        offsets.append(current)
    auxiliary = [reader.extended(8, 8) for _ in range(block_count)]
    return BlockDirectory(offsets, auxiliary)


def record_offsets(block: bytes, absolute_start: int, auxiliary: int, count: int) -> list[int]:
    """Decode FUN_0032943c's auxiliary record-length index to starts."""
    # FUN_002edad8 copies each block into its own aligned buffer, so the
    # auxiliary byte offset is direct; original file alignment is irrelevant.
    # The ext(10,4) values are record bit lengths.  FUN_0032943c restores the
    # record-area cursor (bit zero) and advances cumulatively by each length.
    index_bit = auxiliary * 8
    reader = BitReader(block)
    reader.bit = index_bit
    lengths = [reader.extended(10, 4) for _ in range(count)]
    starts: list[int] = []
    current = 0
    for length in lengths:
        starts.append(current)
        current += length
    if current > index_bit:
        raise ValueError("TMCLOCATION records overlap their auxiliary length index")
    return starts


def decode_first_anchor(
    block: bytes,
    bit_offset: int,
    lcd: int,
    widths: tuple[int, int, int, int],
) -> dict[str, int | None]:
    reader = BitReader(block)
    reader.bit = bit_offset

    previous_delta = signed_extended(reader)
    next_delta = signed_extended(reader)
    previous = None if previous_delta == 0 else (lcd + signed32(previous_delta)) & 0xFFFF
    next_lcd = None if next_delta == 0 else (lcd + signed32(next_delta)) & 0xFFFF

    empty = False
    if previous is None and next_lcd is None and reader.read(1) == 0:
        empty = True

    category = group_count = run_length_minus_one = raw_anchor = None
    if not empty:
        metadata_width, metadata_step, x_width, y_width = widths
        for _ in range(6):
            reader.extended(metadata_width, metadata_step)
        reader.read(x_width)
        reader.read(y_width)

        for category_index in range(6):
            if reader.read(1) == 0:
                continue
            if category_index == 5:
                element_count = reader.extended(4, 4) + 1
                raw_anchor = reader.read(32) & 0x7FFFFFFF
                category = category_index
                group_count = 1
                run_length_minus_one = element_count - 1
                break
            groups = reader.extended(2, 2)
            if groups:
                chain_length_minus_one = reader.extended(4, 4)
                raw_anchor = reader.read(32) & 0x7FFFFFFF
                category = category_index
                group_count = groups
                run_length_minus_one = chain_length_minus_one
                break

    return {
        "previous_lcd": previous,
        "next_lcd": next_lcd,
        "category": category,
        "group_count": group_count,
        "run_length_minus_one": run_length_minus_one,
        "raw_anchor": raw_anchor,
        "geodb_area": raw_anchor >> 16 if raw_anchor is not None else None,
        "geodb_record": raw_anchor & 0xFFFF if raw_anchor is not None else None,
        "decoded_prefix_end_bit": reader.bit,
    }


def select_candidate(data: bytes, cc: int, ltn: int, member: int | None) -> tuple[Candidate, Descriptor]:
    matches = []
    for candidate in find_candidates(data):
        if member is not None and candidate.member_index != member:
            continue
        for descriptor in candidate.descriptors:
            if descriptor.cc == cc and descriptor.ltn == ltn:
                matches.append((candidate, descriptor))
    if len(matches) != 1:
        scope = f" in member {member}" if member is not None else ""
        raise ValueError(
            f"expected exactly one CC={cc}/LTN={ltn} descriptor{scope}, found {len(matches)}"
        )
    return matches[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fbl", type=Path)
    parser.add_argument("--key", type=Path, required=True)
    parser.add_argument("--cc", type=lambda value: int(value, 0), required=True)
    parser.add_argument("--ltn", type=lambda value: int(value, 0), required=True)
    parser.add_argument("--member", type=lambda value: int(value, 0), help="select one SET member")
    parser.add_argument("--csv", type=Path, required=True)
    args = parser.parse_args()

    global candidate_data
    candidate_data = decrypt(args.fbl.read_bytes(), args.key.read_bytes())
    candidate, descriptor = select_candidate(candidate_data, args.cc, args.ltn, args.member)
    widths = tmc_location_widths(candidate_data, candidate.member_start)
    area_offsets, road_base = road_area_layout(candidate_data, candidate.member_start)
    road_codebook = decode_road_codebook(candidate_data, candidate.member_start)
    directory = decode_block_directory(candidate)
    total_records = sum(item.count for item in candidate.descriptors)

    rows = []
    cached_indexes: dict[int, list[int]] = {}
    cached_road_records: dict[int, list[dict[str, int | float | bool]]] = {}
    for descriptor_index, lcd in enumerate(descriptor.lcds):
        ordinal = descriptor.ordinal_base + descriptor_index
        block_index = ordinal >> 6
        record_index = ordinal & 63
        relative_start = directory.relative_offsets[block_index]
        relative_end = directory.relative_offsets[block_index + 1]
        absolute_start = candidate.member_start + relative_start
        absolute_end = candidate.member_start + relative_end
        block = candidate_data[absolute_start:absolute_end]
        count = min(64, total_records - block_index * 64)
        if block_index not in cached_indexes:
            cached_indexes[block_index] = record_offsets(
                block, absolute_start, directory.auxiliary_offsets[block_index], count
            )
        bit_offset = cached_indexes[block_index][record_index]
        decoded = decode_first_anchor(block, bit_offset, lcd, widths)
        decoded.update(
            resolve_area_bbox(candidate_data, area_offsets, road_base, decoded["geodb_area"])
        )
        decoded.update(
            {
                "road_record_index": None,
                "road_record_lon": None,
                "road_record_lat": None,
                "road_descriptor_index": None,
                "record_inside_area_bbox": None,
            }
        )
        area = decoded["geodb_area"]
        road_record = decoded["geodb_record"]
        if area is not None and road_record is not None:
            if area not in cached_road_records:
                cached_road_records[area] = decode_road_area_records(
                    candidate_data, area_offsets, road_base, area, road_codebook
                )
            if road_record >= len(cached_road_records[area]):
                raise ValueError(
                    f"GEODB road record {area}:{road_record} exceeds area count "
                    f"{len(cached_road_records[area])}"
                )
            decoded.update(cached_road_records[area][road_record])
        rows.append(
            {
                "map_ordinal": ordinal,
                "lcd": lcd,
                **decoded,
                "record_bit_offset": bit_offset,
                "block_index": block_index,
                "block_file_offset": absolute_start,
                "block_size": len(block),
                "auxiliary_offset": directory.auxiliary_offsets[block_index],
                "block_alignment": absolute_start & 3,
            }
        )

    add_chain_bearings(rows)
    add_representative_locations(rows)

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with args.csv.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    anchors = sum(row["raw_anchor"] is not None for row in rows)
    print(
        f"member={candidate.member_index} payload=0x{candidate.payload_offset:x} "
        f"cc={descriptor.cc} ltn={descriptor.ltn} rows={len(rows)} anchors={anchors} "
        f"blocks={len(directory.auxiliary_offsets)} widths={widths} wrote={args.csv}"
    )


candidate_data = b""

if __name__ == "__main__":
    main()

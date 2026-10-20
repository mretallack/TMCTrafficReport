#!/usr/bin/env python3
"""Correlate Dutch VILD locations with an NNG FBL map without fabricating links.

VILD is the official Dutch Verkeersinformatie Locatie Database.  It supplies
stable LOC_NR location IDs, road attributes, offsets, and WGS84 point/line
geometries.  NNG FBL road sections are a proprietary tagged/pattern-matched
record stream; a bare 16-bit-code search is statistically meaningless.

This tool creates an auditable starting dataset for reverse engineering:

* ``vild_locations.csv``: normalized official VILD records and geometries;
* ``fbl_probe.json``: decrypted FBL header/section inventory and test results;
* ``candidate_matches.csv``: only *verified exact* coordinate anchors.

At present exact anchors are tested in NNG's known ``int32 / 2**23`` coordinate
representation.  A zero-row candidate file is a valid, useful result: it says
this representation is not the FBL location-link encoding.  Do not infer a
map link from proximity until the NNG tagged-record grammar is decoded.

Usage:
    python tools/correlate_vild_fbl.py \
      --vild-dir tmp/vild \
      --fbl tmp/Netherlands_osm.fbl \
      --out-dir tmp/vild-fbl-correlation
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import struct
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

SCALE = 1 << 23
ROAD_SECTIONS = (1, 4, 5, 8)
SECTION_ROLES = {
    0: "marker",
    1: "curves",
    2: "boundary_a",
    3: "boundary_b",
    4: "roads_main",
    5: "roads_secondary",
    6: "centroid",
    7: "centroid",
    8: "roads_tertiary",
    9: "marker",
    10: "features",
    11: "features",
    12: "features",
    13: "features",
    14: "features",
    15: "labels",
    16: "areas",
    17: "areas",
    18: "extended",
}


@dataclass(frozen=True)
class ShapeGeometry:
    """Small, CSV-friendly representation of a VILD Shapefile geometry."""

    geometry_type: str
    longitude: float | None
    latitude: float | None
    point_count: int
    min_longitude: float | None
    min_latitude: float | None
    max_longitude: float | None
    max_latitude: float | None


def decode_dbf_text(raw: bytes) -> str:
    """Decode official VILD DBF text while preserving an empty field as empty."""
    return raw.decode("latin-1", "replace").strip()


def read_dbf(path: Path) -> tuple[list[tuple[str, str, int, int]], list[dict[str, str]]]:
    """Read the uncomplicated dBASE III DBF variant used by the VILD release."""
    data = path.read_bytes()
    if len(data) < 33:
        raise ValueError(f"{path}: too small to be a DBF")

    row_count = struct.unpack_from("<I", data, 4)[0]
    header_size = struct.unpack_from("<H", data, 8)[0]
    record_size = struct.unpack_from("<H", data, 10)[0]

    fields: list[tuple[str, str, int, int]] = []
    offset = 32
    while offset < header_size and data[offset] != 0x0D:
        name = data[offset : offset + 11].split(b"\0", 1)[0].decode("latin-1")
        field_type = chr(data[offset + 11])
        length = data[offset + 16]
        decimals = data[offset + 17]
        fields.append((name, field_type, length, decimals))
        offset += 32

    rows: list[dict[str, str]] = []
    for row_index in range(row_count):
        start = header_size + row_index * record_size
        end = start + record_size
        if end > len(data):
            raise ValueError(f"{path}: truncated at DBF record {row_index}")
        record = data[start:end]
        if record[0] == 0x2A:  # deleted row
            continue
        row: dict[str, str] = {}
        field_offset = 1
        for name, _field_type, length, _decimals in fields:
            row[name] = decode_dbf_text(record[field_offset : field_offset + length])
            field_offset += length
        rows.append(row)
    return fields, rows


def read_shp(path: Path) -> list[ShapeGeometry | None]:
    """Read Point and PolyLine geometries from VILD's WGS84 ESRI Shapefile."""
    data = path.read_bytes()
    if len(data) < 100 or struct.unpack_from(">I", data, 0)[0] != 9994:
        raise ValueError(f"{path}: not an ESRI Shapefile")

    geometries: list[ShapeGeometry | None] = []
    offset = 100
    while offset + 8 <= len(data):
        _record_number, words = struct.unpack_from(">2I", data, offset)
        content_size = words * 2
        content_start = offset + 8
        content_end = content_start + content_size
        if content_end > len(data):
            raise ValueError(f"{path}: truncated geometry record at 0x{offset:x}")
        content = data[content_start:content_end]
        shape_type = struct.unpack_from("<I", content, 0)[0]

        if shape_type == 0:  # Null Shape
            geometries.append(None)
        elif shape_type == 1:  # Point
            longitude, latitude = struct.unpack_from("<2d", content, 4)
            geometries.append(
                ShapeGeometry(
                    "point", longitude, latitude, 1,
                    longitude, latitude, longitude, latitude,
                )
            )
        elif shape_type == 3:  # PolyLine
            min_lon, min_lat, max_lon, max_lat = struct.unpack_from("<4d", content, 4)
            _parts, point_count = struct.unpack_from("<2I", content, 36)
            geometries.append(
                ShapeGeometry(
                    "line", (min_lon + max_lon) / 2, (min_lat + max_lat) / 2,
                    point_count, min_lon, min_lat, max_lon, max_lat,
                )
            )
        else:
            raise ValueError(f"{path}: unsupported shape type {shape_type}")
        offset = content_end
    return geometries


def as_int(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def load_vild(vild_dir: Path) -> tuple[dict[int, dict[str, str]], dict[int, ShapeGeometry]]:
    """Load official VILD attributes plus its WGS84 point/line geometry indexes."""
    _fields, rows = read_dbf(vild_dir / "VILD6.13.A.dbf")
    attributes: dict[int, dict[str, str]] = {}
    for row in rows:
        code = as_int(row.get("LOC_NR", ""))
        if code is not None:
            attributes[code] = row

    geometries: dict[int, ShapeGeometry] = {}
    for stem in ("vild_point", "vild_line"):
        _geometry_fields, geometry_rows = read_dbf(vild_dir / "WGS84" / f"{stem}.dbf")
        shape_rows = read_shp(vild_dir / "WGS84" / f"{stem}.shp")
        if len(geometry_rows) != len(shape_rows):
            raise ValueError(
                f"{stem}: DBF has {len(geometry_rows)} rows but SHP has {len(shape_rows)} records"
            )
        for row, geometry in zip(geometry_rows, shape_rows, strict=True):
            code = as_int(row.get("LOC_NR", ""))
            if code is not None and geometry is not None:
                geometries[code] = geometry
    return attributes, geometries


def decrypt_fbl(path: Path, xor_key: Path) -> bytes:
    raw = path.read_bytes()
    key = xor_key.read_bytes()
    if not key:
        raise ValueError(f"{xor_key}: empty XOR key")
    return bytes(value ^ key[i % len(key)] for i, value in enumerate(raw))


def parse_fbl_sections(data: bytes) -> tuple[str, tuple[float, float, float, float], dict[int, tuple[int, int]]]:
    """Read FBL country metadata, bounding box, and non-overlapping section ranges."""
    if not data.startswith(b"SET\0"):
        raise ValueError("FBL does not decrypt to a SET container")

    table_start: int | None = None
    country = "UNK"
    bbox_raw: tuple[int, int, int, int] | None = None
    for offset in range(0x440, min(0x600, len(data) - 104)):
        if data[offset : offset + 3].isalpha() and data[offset + 3] in (0x40, 0x48, 0x49, 0x4B):
            country = data[offset : offset + 3].decode("ascii")
            lon_min, lat_max, lon_max, lat_min = struct.unpack_from("<4i", data, offset + 8)
            bbox_raw = (lon_min, lat_min, lon_max, lat_max)
            table_start = offset + 24
            break
    if table_start is None or bbox_raw is None:
        raise ValueError("could not locate FBL country/section table")

    offsets = [struct.unpack_from("<I", data, table_start + index * 4)[0] for index in range(20)]
    valid_starts = sorted({value for value in offsets if 0 < value < len(data)})
    ranges: dict[int, tuple[int, int]] = {}
    for index, start in enumerate(offsets):
        if start == 0 or start >= len(data):
            continue
        later = next((value for value in valid_starts if value > start), len(data))
        if later > start:
            ranges[index] = (start, later)

    lon_min, lat_min, lon_max, lat_max = bbox_raw
    bbox = (lon_min / SCALE, lat_min / SCALE, lon_max / SCALE, lat_max / SCALE)
    return country, bbox, ranges


def iter_exact_coordinate_anchors(
    fbl_data: bytes,
    ranges: dict[int, tuple[int, int]],
    geometry_by_code: dict[int, ShapeGeometry],
) -> Iterator[dict[str, object]]:
    """Yield only exact VILD point anchors in a known NNG coordinate representation.

    This does *not* use proximity.  Every emitted result is an eight-byte exact
    byte sequence for a public VILD point coordinate, tested in both byte orders.
    """
    patterns: dict[bytes, list[tuple[int, ShapeGeometry, str]]] = {}
    for code, geometry in geometry_by_code.items():
        if geometry.geometry_type != "point" or geometry.longitude is None or geometry.latitude is None:
            continue
        lon = round(geometry.longitude * SCALE)
        lat = round(geometry.latitude * SCALE)
        for endian, label in (("<", "little"), (">", "big")):
            packed = struct.pack(f"{endian}ii", lon, lat)
            patterns.setdefault(packed, []).append((code, geometry, label))

    for section in ROAD_SECTIONS:
        if section not in ranges:
            continue
        section_start, section_end = ranges[section]
        section_data = fbl_data[section_start:section_end]
        for relative_offset in range(len(section_data) - 7):
            matches = patterns.get(section_data[relative_offset : relative_offset + 8])
            if not matches:
                continue
            for code, geometry, endian in matches:
                yield {
                    "evidence_type": "exact_int32_pair",
                    "confidence": "verified",
                    "fbl_section": section,
                    "fbl_offset": section_start + relative_offset,
                    "loc_nr": code,
                    "longitude": geometry.longitude,
                    "latitude": geometry.latitude,
                    "coordinate_byte_order": endian,
                    "reason": "VILD WGS84 point equals an eight-byte FBL sequence after int32/2^23 quantization",
                }


def write_vild_csv(
    path: Path,
    attributes: dict[int, dict[str, str]],
    geometries: dict[int, ShapeGeometry],
) -> None:
    """Write a stable, compact, human-reviewable representation of VILD."""
    columns = [
        "loc_nr", "loc_type", "loc_description", "road_number", "road_name",
        "first_name", "second_name", "direction", "positive_offset", "negative_offset",
        "line_reference", "intersection_reference", "geometry_type", "longitude", "latitude",
        "point_count", "min_longitude", "min_latitude", "max_longitude", "max_latitude",
    ]
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        for code in sorted(attributes):
            row = attributes[code]
            geometry = geometries.get(code)
            writer.writerow({
                "loc_nr": code,
                "loc_type": row.get("LOC_TYPE", ""),
                "loc_description": row.get("LOC_DES", ""),
                "road_number": row.get("ROADNUMBER", ""),
                "road_name": row.get("ROADNAME", ""),
                "first_name": row.get("FIRST_NAME", ""),
                "second_name": row.get("SECND_NAME", ""),
                "direction": row.get("DIR", ""),
                "positive_offset": row.get("POS_OFF", ""),
                "negative_offset": row.get("NEG_OFF", ""),
                "line_reference": row.get("LIN_REF", ""),
                "intersection_reference": row.get("INTER_REF", ""),
                "geometry_type": geometry.geometry_type if geometry else "",
                "longitude": geometry.longitude if geometry else "",
                "latitude": geometry.latitude if geometry else "",
                "point_count": geometry.point_count if geometry else "",
                "min_longitude": geometry.min_longitude if geometry else "",
                "min_latitude": geometry.min_latitude if geometry else "",
                "max_longitude": geometry.max_longitude if geometry else "",
                "max_latitude": geometry.max_latitude if geometry else "",
            })


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vild-dir", required=True, type=Path, help="unpacked official VILD release directory")
    parser.add_argument("--fbl", required=True, type=Path, help="matching encrypted NNG Netherlands FBL")
    parser.add_argument("--out-dir", required=True, type=Path, help="directory for CSV/JSON evidence")
    parser.add_argument(
        "--xor-key",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "MediaNavToolkit" / "analysis" / "xor_table_normal.bin",
        help="NNG XOR table (default: MediaNavToolkit analysis table)",
    )
    args = parser.parse_args()

    attributes, geometries = load_vild(args.vild_dir)
    fbl_data = decrypt_fbl(args.fbl, args.xor_key)
    country, bbox, ranges = parse_fbl_sections(fbl_data)
    exact_matches = list(iter_exact_coordinate_anchors(fbl_data, ranges, geometries))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_vild_csv(args.out_dir / "vild_locations.csv", attributes, geometries)

    candidate_columns = [
        "evidence_type", "confidence", "fbl_section", "fbl_offset", "loc_nr",
        "longitude", "latitude", "coordinate_byte_order", "reason",
    ]
    with (args.out_dir / "candidate_matches.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=candidate_columns)
        writer.writeheader()
        writer.writerows(exact_matches)

    geometry_counts = Counter(geometry.geometry_type for geometry in geometries.values())
    probe = {
        "source": {
            "vild_dir": str(args.vild_dir),
            "fbl": str(args.fbl),
            "xor_key": str(args.xor_key),
        },
        "vild": {
            "attribute_records": len(attributes),
            "geometry_records": len(geometries),
            "geometry_counts": dict(sorted(geometry_counts.items())),
            "loc_nr_min": min(attributes),
            "loc_nr_max": max(attributes),
        },
        "fbl": {
            "country": country,
            "bbox_wgs84": {
                "min_longitude": bbox[0], "min_latitude": bbox[1],
                "max_longitude": bbox[2], "max_latitude": bbox[3],
            },
            "sections": [
                {
                    "index": index,
                    "role": SECTION_ROLES.get(index, "unknown"),
                    "start": start,
                    "end": end,
                    "bytes": end - start,
                }
                for index, (start, end) in sorted(ranges.items())
            ],
        },
        "hypotheses": {
            "plain_uint16_location_table": {
                "status": "rejected",
                "reason": "Known UK and VILD codes occur at ordinary 16-bit background frequency.",
            },
            "fixed_width_packed_coordinates": {
                "status": "rejected",
                "reason": "Production road sections decode to many out-of-bounds points under fixed N+M interpretation.",
            },
            "int32_pair_coordinate_anchor": {
                "status": "tested",
                "representation": "longitude and latitude as consecutive int32 / 2**23 values, both byte orders",
                "sections": list(ROAD_SECTIONS),
                "verified_matches": len(exact_matches),
            },
        },
        "conclusion": (
            "No candidate is emitted without exact evidence. A tagged-record/pattern-grammar decoder "
            "is required before spatial proximity can be used to identify FBL map links."
        ),
    }
    (args.out_dir / "fbl_probe.json").write_text(json.dumps(probe, indent=2) + "\n", encoding="utf-8")

    print(
        f"VILD: {len(attributes):,} records, {len(geometries):,} geometries; "
        f"FBL: {country}, {len(ranges)} sections; verified anchors: {len(exact_matches)}"
    )
    print(f"Wrote {args.out_dir / 'vild_locations.csv'}")
    print(f"Wrote {args.out_dir / 'candidate_matches.csv'}")
    print(f"Wrote {args.out_dir / 'fbl_probe.json'}")


if __name__ == "__main__":
    main()

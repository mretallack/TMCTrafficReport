#!/usr/bin/env python3
"""Build national UK TMC exports from validated per-member coordinate CSVs."""

from __future__ import annotations

import argparse
import collections
import csv
import json
import math
import re
from pathlib import Path

MEMBERS = (0, 1, 2, 3, 4, 5, 6, 10, 11, 12, 13, 14, 15, 16, 17)
EXPECTED_COUNTS = {
    0: 4529, 1: 2843, 2: 2344, 3: 3442, 4: 1808,
    5: 2177, 6: 1293, 10: 2839, 11: 2871, 12: 2820,
    13: 1982, 14: 3151, 15: 1458, 16: 2437, 17: 1713,
}
RDS_LINE = re.compile(
    r"^([0-9A-F]{4})\s+([0-9A-F]{4})\s+([0-9A-F]{4})\s+([0-9A-F]{4})\b",
    re.IGNORECASE,
)


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def haversine_km(a: dict, b: dict) -> float:
    lat1 = math.radians(float(a["representative_road_record_lat"]))
    lon1 = math.radians(float(a["representative_road_record_lon"]))
    lat2 = math.radians(float(b["representative_road_record_lat"]))
    lon2 = math.radians(float(b["representative_road_record_lon"]))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    value = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0088 * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def load_members(directory: Path) -> tuple[list[str], list[dict]]:
    fields: list[str] | None = None
    rows: list[dict] = []
    for member in MEMBERS:
        path = directory / f"locations-member-{member}.csv"
        with path.open(newline="") as source:
            reader = csv.DictReader(source)
            member_rows = list(reader)
            if fields is None:
                fields = list(reader.fieldnames or [])
            elif fields != list(reader.fieldnames or []):
                raise ValueError(f"schema mismatch in {path}")
        expected = EXPECTED_COUNTS[member]
        if len(member_rows) != expected:
            raise ValueError(f"member {member}: expected {expected} rows, got {len(member_rows)}")
        for row in member_rows:
            row = {"member": member, **row}
            rows.append(row)
    assert fields is not None
    return ["member", *fields], rows


def build_member_summary(rows: list[dict]) -> list[dict]:
    grouped: dict[int, list[dict]] = collections.defaultdict(list)
    for row in rows:
        grouped[int(row["member"])].append(row)
    result = []
    for member in MEMBERS:
        items = grouped[member]
        direct = [row for row in items if row["raw_anchor"]]
        result.append(
            {
                "member": member,
                "rows": len(items),
                "unique_lcds": len({row["lcd"] for row in items}),
                "direct_rows": len(direct),
                "linked_fallback_rows": sum(row["representative_source"] == "linked_lcd" for row in items),
                "unresolved_rows": sum(not row["representative_source"] for row in items),
                "unique_area_record_pairs": len({(row["geodb_area"], row["geodb_record"]) for row in direct}),
                "inside_area_rows": sum(row["record_inside_area_bbox"] == "True" for row in direct),
                "cross_boundary_rows": sum(row["record_inside_area_bbox"] == "False" for row in direct),
                "previous_bearings": sum(bool(row["bearing_to_previous_deg"]) for row in items),
                "next_bearings": sum(bool(row["bearing_to_next_deg"]) for row in items),
                "max_representative_hops": max(int(row["representative_hops"]) for row in items),
                "min_lon": min(float(row["representative_road_record_lon"]) for row in items),
                "max_lon": max(float(row["representative_road_record_lon"]) for row in items),
                "min_lat": min(float(row["representative_road_record_lat"]) for row in items),
                "max_lat": max(float(row["representative_road_record_lat"]) for row in items),
            }
        )
    return result


def build_candidates(rows: list[dict]) -> list[dict]:
    grouped: dict[int, list[dict]] = collections.defaultdict(list)
    for row in rows:
        grouped[int(row["lcd"])].append(row)
    result = []
    for lcd in sorted(grouped):
        items = sorted(grouped[lcd], key=lambda row: (int(row["member"]), int(row["map_ordinal"])))
        separations = [haversine_km(a, b) for index, a in enumerate(items) for b in items[index + 1 :]]
        max_separation = max(separations, default=0.0)
        preferred = min(
            items,
            key=lambda row: (
                row["representative_source"] != "direct",
                int(row["representative_hops"]),
                MEMBERS.index(int(row["member"])),
                int(row["map_ordinal"]),
            ),
        )
        candidates = [
            {
                "member": int(row["member"]),
                "map_ordinal": int(row["map_ordinal"]),
                "source": row["representative_source"],
                "source_lcd": int(row["representative_source_lcd"]),
                "hops": int(row["representative_hops"]),
                "lat": float(row["representative_road_record_lat"]),
                "lon": float(row["representative_road_record_lon"]),
                "area": int(row["geodb_area"]) if row["geodb_area"] else None,
                "record": int(row["geodb_record"]) if row["geodb_record"] else None,
            }
            for row in items
        ]
        result.append(
            {
                "lcd": lcd,
                "candidate_count": len(items),
                "members": ";".join(str(row["member"]) for row in items),
                "direct_candidate_count": sum(row["representative_source"] == "direct" for row in items),
                "linked_candidate_count": sum(row["representative_source"] == "linked_lcd" for row in items),
                "max_candidate_separation_km": f"{max_separation:.6f}",
                "geographically_ambiguous_5km": max_separation > 5.0,
                "convenience_member": preferred["member"],
                "convenience_source": preferred["representative_source"],
                "convenience_source_lcd": preferred["representative_source_lcd"],
                "convenience_hops": preferred["representative_hops"],
                "convenience_lat": preferred["representative_road_record_lat"],
                "convenience_lon": preferred["representative_road_record_lon"],
                "candidate_json": json.dumps(candidates, separators=(",", ":")),
            }
        )
    return result


def decode_uk_rds(directory: Path, candidates: dict[int, dict]) -> list[dict]:
    messages: dict[int, dict] = {}
    services: dict[Path, dict] = collections.defaultdict(lambda: {"ltn": set(), "sid": set(), "provider": {}})
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        for line in path.open(errors="ignore"):
            match = RDS_LINE.match(line)
            if not match:
                continue
            pi, block_b, block_c, block_d = (int(value, 16) for value in match.groups())
            group = block_b >> 12
            version_b = (block_b >> 11) & 1
            if group == 3 and version_b == 0 and block_d == 0xCD46:
                variant = (block_c >> 14) & 3
                if variant == 0:
                    services[path]["ltn"].add((block_c >> 6) & 0x3F)
                elif variant == 1:
                    services[path]["sid"].add((block_c >> 6) & 0x3F)
            if group != 8 or version_b:
                continue
            x = block_b & 0x1F
            tuning = bool((x >> 4) & 1)
            if tuning:
                variant = x & 0xF
                if variant in (4, 5):
                    services[path]["provider"][variant] = bytes(
                        [block_c >> 8, block_c & 0xFF, block_d >> 8, block_d & 0xFF]
                    )
                continue
            single_group = bool((x >> 3) & 1)
            if not single_group:
                continue
            location = block_d
            item = messages.setdefault(
                location,
                {
                    "lcd": location,
                    "transmissions": 0,
                    "events": set(),
                    "directions": set(),
                    "extents": set(),
                    "files": set(),
                    "pis": set(),
                    "ltns": set(),
                    "sids": set(),
                    "providers": set(),
                },
            )
            item["transmissions"] += 1
            item["events"].add(block_c & 0x7FF)
            item["directions"].add("negative" if (block_c >> 14) & 1 else "positive")
            item["extents"].add((block_c >> 11) & 7)
            item["files"].add(str(path.relative_to(directory.parent)))
            item["pis"].add(f"{pi:04X}")
    for path, service in services.items():
        provider = (service["provider"].get(4, b"") + service["provider"].get(5, b"")).decode(
            "latin1", errors="replace"
        )
        for item in messages.values():
            if str(path.relative_to(directory.parent)) in item["files"]:
                item["ltns"].update(service["ltn"])
                item["sids"].update(service["sid"])
                if provider:
                    item["providers"].add(provider)
    result = []
    for lcd in sorted(messages):
        item = messages[lcd]
        match = candidates.get(lcd)
        candidate_data = json.loads(match["candidate_json"]) if match else []
        in_uk = all(-9.0 <= float(c["lon"]) <= 3.0 and 49.0 <= float(c["lat"]) <= 62.0 for c in candidate_data)
        result.append(
            {
                "lcd": lcd,
                "transmissions": item["transmissions"],
                "event_codes": ";".join(str(value) for value in sorted(item["events"])),
                "directions": ";".join(sorted(item["directions"])),
                "extents": ";".join(str(value) for value in sorted(item["extents"])),
                "pis": ";".join(sorted(item["pis"])),
                "ltns": ";".join(str(value) for value in sorted(item["ltns"])),
                "sids": ";".join(str(value) for value in sorted(item["sids"])),
                "providers": ";".join(sorted(item["providers"])),
                "current_osm_candidate_count": int(match["candidate_count"]) if match else 0,
                "current_osm_members": match["members"] if match else "",
                "current_osm_points_in_uk_bounds": in_uk if match else "",
                "current_osm_candidate_json": match["candidate_json"] if match else "",
                "source_files": ";".join(sorted(item["files"])),
            }
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--members-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--rds-uk-dir", type=Path)
    args = parser.parse_args()

    fields, rows = load_members(args.members_dir)
    rows.sort(key=lambda row: (MEMBERS.index(int(row["member"])), int(row["map_ordinal"])))
    all_path = args.output_dir / "uk-tmc-locations-all-members-2026.03.csv"
    write_csv(all_path, fields, rows)

    member_summary = build_member_summary(rows)
    member_fields = list(member_summary[0])
    write_csv(args.output_dir / "uk-tmc-members-2026.03.csv", member_fields, member_summary)

    candidates = build_candidates(rows)
    candidate_fields = list(candidates[0])
    write_csv(args.output_dir / "uk-tmc-lcd-candidates-2026.03.csv", candidate_fields, candidates)

    if args.rds_uk_dir:
        by_lcd = {int(row["lcd"]): row for row in candidates}
        correlation = decode_uk_rds(args.rds_uk_dir, by_lcd)
        write_csv(
            args.output_dir / "uk-heart-2015-current-osm-correlation.csv",
            list(correlation[0]),
            correlation,
        )

    print(f"all-member rows={len(rows)}")
    print(f"unique LCD candidates={len(candidates)}")
    print(f"members={len(member_summary)}")


if __name__ == "__main__":
    main()

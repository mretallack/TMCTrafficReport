#!/usr/bin/env python3
"""
Extract TMC location codes from the MediaNav trafficevents files.

This parses the trafficevents_A.txt and trafficevents_B.txt files to extract
the 16-bit location codes and 11-bit event codes that the car's navigation
system understands.

Usage:
    python tools/extract_tmc_codes.py dump/trafficevents_A.txt
    python tools/extract_tmc_codes.py dump/
"""

import re
import sys
from pathlib import Path

# Event code descriptions (partial - from ISO 14819-2)
# Full list requires the ISO standard
EVENT_DESCRIPTIONS = {
    806: "stationary traffic",
    807: "queuing traffic",
    801: "accident",
    802: "roadworks",
    803: "road closed",
    804: "lane closed",
    805: "hazard on roadway",
    808: "slow traffic",
    809: "traffic congestion",
    810: "vehicle breakdown",
}

# Country codes
COUNTRY_CODES = {
    12: "United Kingdom",
    250: "France",
    276: "Germany",
    528: "Netherlands",
    56: "Belgium",
    756: "Switzerland",
}

# Location Table Numbers (LTN) - partial
LTN_NAMES = {
    10: "UK (Inrix)",
    1: "Germany (V-Traffic)",
    2: "France (V-Traffic)",
    3: "Netherlands (BeMobile)",
    4: "Belgium (BeMobile)",
}


def parse_trafficevents_file(filepath):
    """Parse a trafficevents_*.txt file and extract TMC codes."""
    codes = []

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line.startswith('EVENT '):
                continue

            # Parse EVENT line
            # Example: EVENT htmc=1 loc=17602 extent=1 dir=1 bidi=0 age=59 cc=12 ltn=10 new=1 tmc_source=0 sid=10 qdecoded=1 snd_id=0 event_1=807  loaded=1

            entry = {}

            # Extract key fields using regex
            loc_match = re.search(r'loc=(\d+)', line)
            event_match = re.search(r'event_1=(\d+)', line)
            extent_match = re.search(r'extent=(\d+)', line)
            dir_match = re.search(r'dir=(\d+)', line)
            cc_match = re.search(r'cc=(\d+)', line)
            ltn_match = re.search(r'ltn=(\d+)', line)
            age_match = re.search(r'age=(\d+)', line)

            if loc_match:
                entry['location_code'] = int(loc_match.group(1))
            if event_match:
                entry['event_code'] = int(event_match.group(1))
            if extent_match:
                entry['extent'] = int(extent_match.group(1))
            if dir_match:
                entry['direction'] = int(dir_match.group(1))
            if cc_match:
                entry['country_code'] = int(cc_match.group(1))
            if ltn_match:
                entry['ltn'] = int(ltn_match.group(1))
            if age_match:
                entry['age_minutes'] = int(age_match.group(1))

            if 'location_code' in entry and 'event_code' in entry:
                entry['event_desc'] = EVENT_DESCRIPTIONS.get(entry['event_code'], "unknown")
                entry['country'] = COUNTRY_CODES.get(entry.get('country_code', 0), "unknown")
                entry['ltn_name'] = LTN_NAMES.get(entry.get('ltn', 0), "unknown")
                codes.append(entry)

    return codes


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_tmc_codes.py <file or directory>")
        sys.exit(1)

    path = Path(sys.argv[1])

    # Find all trafficevents files
    if path.is_dir():
        files = list(path.glob("trafficevents_*.txt"))
    else:
        files = [path]

    all_codes = []

    for f in files:
        print(f"Parsing {f.name}...")
        codes = parse_trafficevents_file(f)
        all_codes.extend(codes)

    # Deduplicate by location code
    unique_locations = {}
    for entry in all_codes:
        loc = entry['location_code']
        if loc not in unique_locations:
            unique_locations[loc] = entry

    print(f"\n=== Found {len(all_codes)} total events, {len(unique_locations)} unique locations ===\n")

    # Print unique locations
    print("Unique Location Codes:")
    print("-" * 70)
    print(f"{'Location':<10} {'Event':<6} {'Event Desc':<20} {'LTN':<6} {'Country'}")
    print("-" * 70)

    for loc in sorted(unique_locations.keys()):
        e = unique_locations[loc]
        print(f"{loc:<10} {e['event_code']:<6} {e['event_desc']:<20} {e.get('ltn', '?'):<6} {e['country']}")

    # Output as C header for use in rds_tmc.c
    print("\n\n=== C Header Format (for rds_tmc.c) ===")
    print("// TMC location codes extracted from car dump")
    print("static const uint16_t tmc_location_codes[] = {")
    for loc in sorted(unique_locations.keys())[:20]:  # First 20
        print(f"    {loc},  // {unique_locations[loc]['event_desc']}")
    if len(unique_locations) > 20:
        print(f"    // ... and {len(unique_locations) - 20} more")
    print("};")


if __name__ == "__main__":
    main()
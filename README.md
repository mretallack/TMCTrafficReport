# TrafficReport — MediaNav RDS-TMC location research and transmitter prototype

This repository investigates the RDS-TMC service understood by a Dacia
MediaNav 4 head unit and contains:

- reproducible decoders for the TMC structures embedded in current OSM `.fbl`
  map files;
- exported LCD-to-road-record coordinates for the current UK map;
- exact ARM-runtime and file-format analysis supporting those decoders; and
- an early PiFmRds-based TMC transmitter prototype for bench testing.

The immediate map-decoding objective has been achieved for UK SET member 0.
The transmitter is **not yet validated** and must not be treated as a working
on-air service.

## Current status

| Area | Status |
|---|---|
| Exact MediaNav runtime identified | Complete: Linux `6.0.12.2.1166_r2`, iGO `9.12.184.822257` |
| Current UK OSM TMC descriptor decoder | Complete |
| Member-0 LCD index | Complete: 4,529 `CC=12/LTN=10` locations |
| Member-0 road coordinates | Complete: 4,222 direct road records; representative points for all 4,529 LCDs |
| Whole UK SET discovery | Complete at index level: 15 populated members, 30,044 unique LCD values |
| Road names/full link geometry | Not decoded yet |
| TMC transmitter encoding | Prototype only; not validated against `redsea` or the head unit |
| Real head-unit acceptance/re-routing | Not tested |
| Live traffic-feed integration | Not implemented |

The authoritative current result is documented in
[`docs/17-CURRENT-UK-TMC-INDEX-EXTRACTION.md`](docs/17-CURRENT-UK-TMC-INDEX-EXTRACTION.md).
The committed datasets and hashes are listed in
[`data/exports/README.md`](data/exports/README.md).

## Key result: current UK OSM mapping

Target map:

```text
HeadUnitUpdate-2026-10-19/NaviSync/content/map/UnitedKingdom_osm.fbl
SET v4.6.7.32
SHA-256 ed3cffccefc13389e8fe0ef24067168614dfc8f0023bcd17a0fba4103965eaea
```

Normal incoming UK messages select the descriptor:

```text
CC=12 (C hexadecimal), LTN=10
```

SET member 0 contains 4,529 sorted LCDs. The exact runtime path from an
incoming LCD to a road object is:

```text
CC/LTN/LCD
  -> descriptor selection
  -> LCD binary search
  -> TMCLOCATION record
  -> predecessor/successor LCD topology
  -> GEODB area + road-record index
  -> road-record coordinate
```

Member 0 is a Scotland/northern-UK map shard, not the complete national map.
Across all 15 members containing `CC=12/LTN=10` descriptors there are 37,707
rows including duplicates and 30,044 unique LCD values. The runtime iterates
map contexts and accepts the first usable road object.

Member-0 export results:

```text
4,529 total LCD rows
4,222 direct GEODB road anchors
3,578 unique (area, road-record) pairs
307 anchorless rows located through predecessor/successor links
3,278 direct points inside their local area bbox
944 cross-boundary road points
3,420 predecessor bearings
3,420 successor bearings
```

Every row has a representative road-record point. Linked fallback rows retain
`representative_source_lcd` and `representative_hops`; 125 fallbacks are more
than 10 links away and the maximum is 135, so consumers must use that field as
a confidence indicator.

Example current OSM locations:

| LCD | Latitude | Longitude | Notes |
|---:|---:|---:|---|
| 5734 | 57.466873 | -4.561485 | Direct member-0 road record |
| 5437 | 55.129082 | -3.442085 | Direct member-0 road record |

Google Maps accepts URLs in `latitude,longitude` order, for example:

```text
https://www.google.com/maps?q=57.466873,-4.561485
```

## Where the actual tables are, and how complete they are

The committed decoded tables are under [`data/exports/`](data/exports/):

```text
data/exports/uk-tmc-index-2026.03.csv
data/exports/uk-tmc-location-anchors-2026.03.csv
data/exports/netherlands-tmc-index-2025.09.csv
```

They are decoded data, not examples or raw-byte scans. The original compiled
location structures remain inside the locally held `.fbl` files, which are not
committed because they are large proprietary map inputs.

Completeness is scope-dependent:

| Scope | Completeness |
|---|---|
| UK OSM member-0 LCD membership | Complete: 4,529/4,529 descriptor entries |
| UK member-0 predecessor/successor records | Complete: all 4,529 TMCLOCATION records parsed |
| UK member-0 first GEODB anchors | 4,222 direct; 307 records contain no direct first anchor |
| UK member-0 usable coordinates | Complete for this scope: 4,222 direct road-record points plus 307 explicitly linked fallbacks |
| UK member-0 road names/full link shapes | Incomplete: names, second adjacency-selected endpoint and full polyline remain undecoded |
| Whole current UK OSM index | Discovered but not consolidated: 30,044 unique LCDs across 15 populated members |
| Whole current UK OSM coordinates | Not yet exported as one national table; the coordinate extractor currently requires a member selection |
| Historical Trafficmaster LTN 7 table | Not acquired; the Heart log contains messages, not the complete LCL |
| Historical installed HERE table | Not acquired as a decoded table; only cached event examples are retained |
| Netherlands member-0 index | Complete for that descriptor: 3,132 LCDs; coordinates are not exported |

Thus, `uk-tmc-location-anchors-2026.03.csv` is the complete usable table for
**one current OSM shard**, not a complete nationwide UK road-name table. A
national export requires running the coordinate extractor for each populated
SET member and then retaining member identity when merging duplicate LCDs.

## Do not mix the three UK datasets

Three related but non-interchangeable generations occur in this workspace:

| Evidence | Service/map generation | What it establishes |
|---|---|---|
| `rds-spy-logs/UK/...HEART.rds` | 2015 Trafficmaster, provider `" Tm TMC "`, LTN 7, SID 7 | Historical over-the-air 3A/8A groups and LCD/event pairs |
| `dump/trafficevents_A.txt` and `B.txt` | Installed HERE 2019.Q4 cache; messages report CC 12, LTN 10, SID 10 | Historical cached events including LCDs 17602 and 10024 |
| `UnitedKingdom_osm.fbl` and committed exports | Downloaded OSM map, CC 12/LTN 10 | Current map-resident LCD-to-road mapping |

The cached codes `17602` and `10024` are **not present in member 0**, so
they must not be used to validate the committed member-0 export. They do occur
in current OSM member 12 and resolve directly to:

| LCD | Current member | Latitude | Longitude |
|---:|---:|---:|---:|
| 10024 | 12 | 51.442833 | -0.927315 |
| 17602 | 12 | 51.077484 | -1.309616 |

This supports continuity of UK numeric assignments across the HERE-to-OSM
migration. The old cache still cannot by itself prove that every retained
number has identical segment/direction semantics in the current table.

The 2015 Heart capture contains 60 unique Trafficmaster LCDs. Forty-four of
those numbers occur somewhere in the current 15-member OSM union, which is
consistent with substantial continuity in UK location numbering. The service
identities still differ, so a shared number alone does not prove identical
semantics. One concrete retained example is Heart LCD 3043, which the current
OSM member 14 resolves to approximately `51.514252,-0.204216`.

## Repository layout

| Path | Contents |
|---|---|
| `data/exports/` | Authoritative generated CSVs, hashes, schemas and limitations |
| `docs/` | Investigation reports and exact decoder evidence |
| `tools/` | Reusable FBL/TMC extraction and correlation tools |
| `analysis/ghidra-scripts/` | Lightweight headless Ghidra/Jython analysis scripts |
| `src/rds_tmc.c` | Unvalidated PiFmRds transmitter prototype |
| `dump/` | Small historical HERE-era traffic-event samples |
| `tmp/` | Ignored local maps, firmware, Ghidra projects, logs and probes |

Large map files, firmware archives, runtime binaries, Ghidra databases,
license/key material and the Python virtual environment are intentionally not
committed.

## Using the exports

### LCD index

```text
data/exports/uk-tmc-index-2026.03.csv
```

Use this when only descriptor membership and ordinal lookup are required. It
contains one row per member-0 LCD, including `member`, `cc`, `ltn`,
`descriptor_index`, `map_ordinal` and `lcd`.

### Road-coordinate export

```text
data/exports/uk-tmc-location-anchors-2026.03.csv
```

Use this for location selection and map display. Important columns include:

- `lcd`, `previous_lcd`, `next_lcd` — TMC topology;
- `geodb_area`, `geodb_record`, `raw_anchor` — exact first GEODB anchor;
- `road_record_lon`, `road_record_lat` — directly decoded road-record point;
- `bbox_*`, `area_center_*` — containing GEODB area;
- `record_inside_area_bbox` — false for a legitimate cross-boundary record;
- `bearing_to_previous_deg`, `bearing_to_next_deg` — bearings between decoded
  LCD record points, not full road-shape tangents;
- `representative_*` — direct point or explicitly marked linked fallback.

Road names and the adjacency-selected second endpoint/full polyline are not yet
available.

## Reproducing the current exports

Run from the parent `TMS/` workspace. The map and XOR table are local research
inputs and are not stored in this repository.

```bash
python3 TrafficReport/tools/extract_fbl_tmc_index.py \
  HeadUnitUpdate-2026-10-19/NaviSync/content/map/UnitedKingdom_osm.fbl \
  --member 0 --cc 12 --ltn 10 \
  --csv TrafficReport/data/exports/uk-tmc-index-2026.03.csv

python3 TrafficReport/tools/extract_fbl_tmc_anchors.py \
  HeadUnitUpdate-2026-10-19/NaviSync/content/map/UnitedKingdom_osm.fbl \
  --key MediaNavToolkit/analysis/xor_table_normal.bin \
  --member 0 --cc 12 --ltn 10 \
  --csv TrafficReport/data/exports/uk-tmc-location-anchors-2026.03.csv
```

The tools implement the exact licensed IGOMAP 4 KiB block transform recovered
from the current ARM runtime. A simple repeating XOR is only correct for block
zero.

## RDS Spy logs: where they fit

`../rds-spy-logs/` is a corpus of raw over-the-air RDS groups. It validates the
wire protocol and realistic service cadence; it does not contain map
coordinates. `TrafficReport` provides the map-side lookup needed to turn a
compatible broadcast LCD into a road point.

For the UK Heart capture:

```text
536 type-8A groups
119 type-3A/CD46 announcements
471 repeated single-group messages
70 unique event/location combinations
60 unique LCDs
provider " Tm TMC ", LTN 7, SID 7, unencrypted
```

A future utility can decode the complete log corpus and join compatible
messages to every current SET member. The current committed road-coordinate
CSV intentionally covers member 0 only.

## Transmitter prototype: current limitations

`src/rds_tmc.c` was derived from PiFmRds and contains an early hard-coded 3A/8A
attempt. It has **not** been built and round-trip validated as part of this
repository, and its group packing must be checked against `redsea` and known
RDS Spy groups before transmission.

In particular:

- the hard-coded LCD 17602 came from a historical HERE-era cache, although the
  number is retained in current OSM member 12; its table/service semantics and
  receiver acceptance must still be verified before using it as a test;
- service signalling must consistently advertise the table expected by the
  target receiver;
- passing a raw-group decoder is required before trying the MediaNav;
- receiver acceptance, encryption expectations and re-routing remain
  device-specific experiments.

Recommended sequence:

1. Correct and unit-test the 3A and 8A block packers.
2. Feed generated groups directly to `redsea` and verify every field.
3. Add correct tuning information and repetition cadence.
4. Add runtime message injection rather than hard-coded values.
5. Test over a shielded wired RF connection to a bench receiver.
6. Only then test whether the target MediaNav accepts a current-map LCD.

## Safety and legal constraints

- Do not radiate an unlicensed FM signal. Use a short shielded cable into a
  bench receiver, with no antenna.
- PiFmRds output is harmonic-rich and must not be treated as compliant RF
  equipment.
- Never broadcast fabricated traffic messages where a vehicle in live traffic
  could receive or act on them.
- Keep firmware and head-unit update analysis read-only. Do not install
  firmware or place experimental payloads on vehicle update media.
- Neither this project nor `redsea` is safety-certified for navigation use.

## Documentation guide

Start with:

1. [`docs/17-CURRENT-UK-TMC-INDEX-EXTRACTION.md`](docs/17-CURRENT-UK-TMC-INDEX-EXTRACTION.md) — current authoritative OSM decoder and coordinates.
2. [`data/exports/README.md`](data/exports/README.md) — committed datasets, schemas and hashes.
3. [`docs/16-EXACT-LINUX-RUNTIME-RECOVERY.md`](docs/16-EXACT-LINUX-RUNTIME-RECOVERY.md) — exact firmware/runtime recovery.
4. [`docs/13-ULC2-TMC-FBL-DECODER.md`](docs/13-ULC2-TMC-FBL-DECODER.md) — earlier decoder work and superseding notes.
5. [`docs/07-UK-INRIX-SERVICE-METADATA.md`](docs/07-UK-INRIX-SERVICE-METADATA.md) — provider metadata; configuration is not proof of current FM availability.
6. [`docs/01-LOCATION-CODES-DUMP.md`](docs/01-LOCATION-CODES-DUMP.md) — historical cache evidence; read with doc 17's HERE/OSM correction.

Earlier reports are retained as an investigation record. Where they conflict,
doc 17 supersedes them.

## License

The modified PiFmRds source is distributed under GPL-3.0-or-later; see
[`LICENSE`](LICENSE). Research notes and generated data retain any applicable
source-data rights and are provided for experimental analysis only.

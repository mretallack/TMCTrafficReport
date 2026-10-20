# TrafficReport — MediaNav RDS-TMC location research and transmitter prototype

This repository investigates the RDS-TMC service understood by a Dacia
MediaNav 4 head unit and contains:

- reproducible decoders for the TMC structures embedded in current OSM `.fbl`
  map files;
- exported LCD-to-road-record coordinates for the current UK map;
- exact ARM-runtime and file-format analysis supporting those decoders; and
- an early PiFmRds-based TMC transmitter prototype for bench testing.

The current UK map-decoding objective has been completed for all 15 populated
SET members and packaged as member-aware national exports. The transmitter is
**not yet validated** and must not be treated as a working on-air service.

## Current status

| Area | Status |
|---|---|
| Exact MediaNav runtime identified | Complete: Linux `6.0.12.2.1166_r2`, iGO `9.12.184.822257` |
| Current UK OSM TMC descriptor decoder | Complete |
| Member-0 LCD/coordinate exports | Complete: retained as a documented Scotland/northern-UK shard |
| Whole UK member-aware coordinates | Complete: 37,707 rows across 15 populated members, zero unresolved rows |
| Unique UK LCD candidate view | Complete: 30,044 LCDs with every member candidate preserved |
| Duplicate resolution | Analysed: 5,171 duplicated LCDs; do not blindly select one member |
| Historical Heart correlation | Complete: 44/60 LCDs match current candidates; all matched coordinates are within UK bounds |
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
It remains committed as a useful small, reproducible subset. The complete
member-aware export now covers all 15 populated `CC=12/LTN=10` members:

```text
37,707 member-context rows
29,231 direct GEODB road anchors
8,476 linked predecessor/successor fallbacks
0 unresolved rows
30,044 unique LCD values
```

The 37,707-row table is the complete decoded current-map projection at the
implemented first-road-record level. The 30,044-row candidate summary preserves
all member alternatives for duplicated LCDs; it does not claim that an
arbitrary one-row choice reproduces runtime context precedence.

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
data/exports/uk-tmc-locations-all-members-2026.03.csv
data/exports/uk-tmc-lcd-candidates-2026.03.csv
data/exports/uk-tmc-members-2026.03.csv
data/exports/uk-heart-2015-current-osm-correlation.csv
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
| Whole current UK OSM member-aware coordinates | Complete: 37,707/37,707 rows across all 15 populated members; 29,231 direct and 8,476 linked; zero unresolved |
| Whole current UK OSM unique-LCD candidates | Complete: 30,044 rows preserving every member candidate as JSON |
| Duplicate LCD analysis | Complete: 5,171 duplicated LCDs; 4,913 have candidate points more than 5 km apart |
| UK member summaries | Complete: 15 rows with counts, coverage and geographic bounds |
| Historical Heart/current OSM correlation | Complete: 60 Heart LCDs, 44 current matches, 16 absent; all matched candidates inside UK bounds |
| Historical Trafficmaster LTN 7 table | Not acquired; the Heart log contains messages, not the complete LCL |
| Historical installed HERE table | Not acquired as a decoded table; only cached event examples are retained |
| Netherlands member-0 index | Complete for that descriptor: 3,132 LCDs; coordinates are not exported |

Thus, `uk-tmc-locations-all-members-2026.03.csv` is the complete current
member-aware UK table at the implemented coordinate level. The older
`uk-tmc-location-anchors-2026.03.csv` is retained as the member-0 subset. Road
names and full link shapes remain incomplete for every member.

## How the whole-UK tables were built

All 15 populated `CC=12/LTN=10` members have now been extracted and validated.
The members are:

```text
0, 1, 2, 3, 4, 5, 6, 10, 11, 12, 13, 14, 15, 16, 17
```

Members 7, 8 and 9 do not contain a matching descriptor. Every populated
member completed exact coordinate extraction and the validation gates below.

### 1. Export each member independently

Each member has its own GEODB bounds, area-offset tables, road data and type-13
codebook, so it must be decoded in its own context:

```bash
members=(0 1 2 3 4 5 6 10 11 12 13 14 15 16 17)
mkdir -p TrafficReport/tmp/uk-members

for member in "${members[@]}"; do
  python3 TrafficReport/tools/extract_fbl_tmc_index.py \
    HeadUnitUpdate-2026-10-19/NaviSync/content/map/UnitedKingdom_osm.fbl \
    --member "$member" --cc 12 --ltn 10 \
    --csv "TrafficReport/tmp/uk-members/index-member-${member}.csv"

  python3 TrafficReport/tools/extract_fbl_tmc_anchors.py \
    HeadUnitUpdate-2026-10-19/NaviSync/content/map/UnitedKingdom_osm.fbl \
    --key MediaNavToolkit/analysis/xor_table_normal.bin \
    --member "$member" --cc 12 --ltn 10 \
    --csv "TrafficReport/tmp/uk-members/locations-member-${member}.csv"
done
```

`tools/build_uk_national_exports.py` adds the invocation's member identity to
every location row while merging, so national rows retain their map context.

### 2. Validate each member before merging

For every member, require:

- location-row count equals that member's descriptor count;
- every decoded record prefix stays within its indexed record length;
- each direct `(area,record)` index is valid for that member;
- every direct point lies within that member's overall geographic bounds;
- predecessor/successor reciprocity and coordinate coverage are reported;
- direct, linked-fallback and unresolved counts are recorded separately;
- the source map hash and extraction-tool revision are identical for all runs.

A failed member must remain separate; it must not be hidden by concatenating
its partial output with successful members.

### 3. Create a member-aware master table

The resulting table contains exactly 37,707 rows, matching the sum of all 15
descriptor counts. Its primary audit key is:

```text
(member, map_ordinal, lcd)
```

All 37,707 rows have representative coordinates. Of these, 29,231 are direct
road anchors and 8,476 are explicitly linked fallbacks; none is unresolved.
The published output is:

```text
data/exports/uk-tmc-locations-all-members-2026.03.csv
```

### 4. Analyse duplicate LCDs

Grouping by LCD reduces the measured index from 37,707 member rows to 30,044
unique numbers. Do not simply keep the first CSV row. For each duplicated LCD,
compare:

- member and map ordinal;
- direct versus linked location source;
- GEODB area/record and road point;
- predecessor/successor LCDs;
- coordinate separation and chain bearings.

Duplicates may be identical copies, shard-boundary records, or context-specific
alternatives. The candidate export preserves every option in `candidate_json`.
Measured duplicate distribution:

```text
24,873 LCDs in one member
3,755 LCDs in two members
874 LCDs in three members
322 LCDs in four members
63 LCDs in five members
157 LCDs in seven members
```

There are 5,171 duplicated LCDs. For 4,913 of them, candidate representative
points differ by more than 5 km; the maximum observed separation is about
516.34 km. This confirms that blind first-row deduplication would be unsafe.

### 5. Reproduce runtime context precedence

An incoming RDS-TMC message carries `CC`, `LTN` and `LCD`; it does not carry a
SET member number. `FUN_00b21e7c` iterates active map contexts and accepts the
first context producing a usable road object. A resolved one-row-per-LCD table
must therefore either:

1. reproduce that active context order and first-usable rule; or
2. retain all candidate members and let the consumer select by geography.

The second option is safer until runtime member precedence is independently
verified.

### 6. Publish distinct audit and candidate outputs

The completed packaging contains:

```text
uk-tmc-locations-all-members-2026.03.csv
    all 37,707 validated member rows

uk-tmc-lcd-candidates-2026.03.csv
    30,044 LCD rows, preserving all member candidates as JSON

uk-tmc-members-2026.03.csv
    per-member validation and geographic summary
```

The all-members file is the authoritative audit source. The candidate file is
the convenient one-row-per-LCD view, but its `convenience_*` columns use a
documented deterministic heuristic—not proven runtime context precedence.
Consumers requiring correctness must inspect `candidate_json` or select by
geography.

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

### Complete member-aware UK coordinates

```text
data/exports/uk-tmc-locations-all-members-2026.03.csv
```

This is the authoritative complete current UK coordinate projection: 37,707
rows with `member` retained. Use it for auditing, geographic nearest-candidate
selection, and any workflow where duplicate LCD context matters.

### Unique-LCD candidate view

```text
data/exports/uk-tmc-lcd-candidates-2026.03.csv
```

This has one row for each of the 30,044 unique LCD values. It preserves every
member option in `candidate_json`, reports candidate separation, and flags
ambiguity over 5 km. The `convenience_*` fields are deterministic shortcuts,
not proven runtime choices.

### Member summary

```text
data/exports/uk-tmc-members-2026.03.csv
```

This records row/direct/fallback counts and coordinate bounds for all 15
members.

### Historical Heart correlation

```text
data/exports/uk-heart-2015-current-osm-correlation.csv
```

This joins the 60 LCDs observed in the 2015 UK Heart capture to current OSM
candidates. Forty-four match, sixteen are absent, and every matched candidate
point is inside broad UK bounds.

### Member-0 LCD index

```text
data/exports/uk-tmc-index-2026.03.csv
```

Use this when only descriptor membership and ordinal lookup are required. It
contains one row per member-0 LCD, including `member`, `cc`, `ltn`,
`descriptor_index`, `map_ordinal` and `lcd`.

### Member-0 road-coordinate subset

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

python3 TrafficReport/tools/build_uk_national_exports.py \
  --members-dir TrafficReport/tmp/uk-all-members \
  --output-dir TrafficReport/data/exports \
  --rds-uk-dir rds-spy-logs/UK
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

The committed correlation export confirms that 44 of the 60 historical Heart
LCDs have current OSM candidates and every matched point lies inside broad UK
bounds. Sixteen historical LCDs are absent. This validates substantial numeric
continuity while preserving the LTN 7 versus LTN 10 distinction.

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

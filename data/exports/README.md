# Decoded TMC table exports

This directory contains the authoritative CSV outputs currently committed to
the repository. These are structured decodes of map-resident TMC data, not
candidate byte searches.

The source `.fbl` maps and XOR/license inputs are not committed. They are large
or separately sourced and remain local research inputs.

## Export inventory

| File | Data rows | Scope | SHA-256 |
|---|---:|---|---|
| `uk-tmc-locations-all-members-2026.03.csv` | 37,707 | Complete member-aware UK OSM coordinate projection across all 15 populated members | `b3e0aec769898d0fff8221586d363451bf47ac5050ad7119afc3fc97f383c948` |
| `uk-tmc-lcd-candidates-2026.03.csv` | 30,044 | One row per unique LCD, preserving every member candidate in JSON | `01e3b0611e4f71b0e039407b022da8442ca49dee27852d323a2d2c217becdcad` |
| `uk-tmc-members-2026.03.csv` | 15 | Per-member extraction counts, coverage and coordinate bounds | `ebb7295b092dd1ded6439df5aa4cf14aa57779a8cd417e14fd183086e26fd62d` |
| `uk-heart-2015-current-osm-correlation.csv` | 60 | Historical UK Heart/Trafficmaster LCDs joined to current OSM candidates | `81785a54a5cb7950915c6f5f91c8425fc1bf6a9ce395d2c32280a20e6bf8d0eb` |
| `uk-tmc-index-2026.03.csv` | 4,529 | Legacy focused UK OSM SET member-0 index | `6c88797b5f05ecf1ee0f1300b9d96838bc5c3ff7ef0b008577bb68120916ba93` |
| `uk-tmc-location-anchors-2026.03.csv` | 4,529 | Legacy focused member-0 topology and coordinates | `ce4eb0902300cd9cce9bbcfa5c9dfe5dc42e15ae35aac8f17a6b63e92c84f23b` |
| `netherlands-tmc-index-2025.09.csv` | 3,132 | Netherlands OSM, SET member 0, CC=8/LTN=17 LCD descriptor | `8f748244c2c0bd22385bbb55781fbfdc350c89ae934a9ae1865e2cf4d137d888` |

Files use deterministic LF line endings. Verify them with:

```bash
sha256sum data/exports/*.csv
```

## Source provenance

### United Kingdom

```text
Input:  HeadUnitUpdate-2026-10-19/NaviSync/content/map/UnitedKingdom_osm.fbl
Format: SET v4.6.7.32
SHA-256: ed3cffccefc13389e8fe0ef24067168614dfc8f0023bcd17a0fba4103965eaea
Service selected: CC=12, LTN=10, SET members 0-6 and 10-17
```

The exact decoder behavior was recovered from the matching MediaNav ARM Linux
runtime `6.0.12.2.1166_r2`, not from the old Windows update-tool DLL. See
[`../../docs/17-CURRENT-UK-TMC-INDEX-EXTRACTION.md`](../../docs/17-CURRENT-UK-TMC-INDEX-EXTRACTION.md).

### Netherlands

```text
Input:  Netherlands_osm.fbl (local validation copy)
SHA-256: f9cf27f412577e409a85b7889975e23ce3a35df6af3ba1c79fce57792406d9d4
Service selected: CC=8, LTN=17, SET member 0
```

The Netherlands index is an independent descriptor-format check. It is not a
UK table and has no committed road-coordinate companion.

## What is an “actual table” here?

The national UK CSVs are actual decoded projections of the current compiled
map table:

```text
uk-tmc-locations-all-members-2026.03.csv
    every member-context row: LCD -> topology -> GEODB area/record -> coordinate

uk-tmc-lcd-candidates-2026.03.csv
    one row per unique LCD with every member candidate preserved

uk-tmc-members-2026.03.csv
    validation and geographic coverage for each populated member
```

The older member-0 index/location files remain useful focused subsets.

The original binary tables remain embedded in `UnitedKingdom_osm.fbl`. The CSVs
are their reproducible projection into fields useful for analysis and a future
transmitter. They are not the historical public Trafficmaster LCL and are not a
copy of a licensed textual road-name database.

## Completeness

### UK member 0

The committed UK files are complete for the selected member-0 descriptor:

```text
4,529 / 4,529 LCD index rows
4,529 / 4,529 TMCLOCATION records parsed
4,222 direct first GEODB anchors
3,578 unique direct (area, road-record) pairs
307 records with no direct first anchor
4,529 / 4,529 representative road-record points
3,278 direct rows inside their local area bbox
944 direct cross-boundary road points
3,420 predecessor bearings
3,420 successor bearings
```

The 307 anchorless records receive a reproducible location only through decoded
predecessor/successor topology. They are marked `representative_source =
linked_lcd`, with the source LCD and hop count retained. This is derived
fallback data, not a hidden direct anchor.

Member 0 covers Scotland/northern UK. It is not the complete nationwide table.

### Whole UK map

The current UK SET contains 18 members; 15 expose `CC=12/LTN=10` descriptors.
All 15 now have validated coordinate exports:

```text
37,707 / 37,707 member-context rows
29,231 direct road anchors
8,476 linked predecessor/successor fallbacks
0 unresolved rows
26,478 unique member-local (area,record) pairs
30,044 unique LCD values
```

Every direct road-record index is valid, every record prefix stays within its
indexed length, in-member topology is reciprocal, and all representative
points fall inside broad UK bounds.

The 30,044-row candidate view does not blindly deduplicate coordinates. There
are 5,171 LCDs occurring in multiple members; 4,913 have candidate points more
than 5 km apart, with a maximum separation of about 516.34 km. Every candidate
is retained in `candidate_json`. `convenience_*` uses the deterministic order
`direct`, then lowest hop count, then member/map order; it is not proven
runtime context precedence.

The historical cached LCDs 10024 and 17602 both occur in current OSM member 12,
although they are outside the committed member-0 tables. Their current decoded
points are approximately `51.442833,-0.927315` and
`51.077484,-1.309616`, respectively. This is evidence of numeric continuity,
not proof that every old and new table attribute is identical.

### Fields not yet decoded

These exports do not yet contain:

- road names;
- the adjacency-selected second road endpoint;
- full road-link polylines;
- a final road-link tangent/bearing independent of TMC LCD topology.

The committed bearings are between predecessor/successor LCD road-record
points. They are useful chain metadata but are not full road-shape bearings.

## National export schemas

### `uk-tmc-locations-all-members-2026.03.csv`

This is the authoritative complete member-aware table. Its first column is
`member`; the remaining columns match the detailed member-0 location schema
below. Treat `(member,map_ordinal,lcd)` as the audit identity.

### `uk-tmc-lcd-candidates-2026.03.csv`

| Column | Meaning |
|---|---|
| `lcd` | Unique 16-bit location code |
| `candidate_count`, `members` | Number/list of member contexts containing the LCD |
| `direct_candidate_count`, `linked_candidate_count` | Candidate source quality counts |
| `max_candidate_separation_km` | Greatest pairwise separation among representative points |
| `geographically_ambiguous_5km` | Whether any candidate separation exceeds 5 km |
| `convenience_*` | Deterministic direct/hops/member shortcut; not proven runtime selection |
| `candidate_json` | Complete list of member, ordinal, source, hops, point and GEODB IDs |

### `uk-tmc-members-2026.03.csv`

One row per populated member with descriptor rows, direct/fallback counts,
inside/cross-boundary counts, bearing coverage, maximum fallback hops and
coordinate bounds.

### `uk-heart-2015-current-osm-correlation.csv`

One row per historical Heart LCD, including transmissions, event/direction/
extent values, PI/LTN/SID/provider, current candidate count/members, a UK-bounds
check, and complete current candidates as JSON. It contains 44 current matches
and 16 absent historical LCDs.

## `uk-tmc-index-2026.03.csv` schema

| Column | Meaning |
|---|---|
| `member` | SET member index; all committed rows are member 0 |
| `payload_offset` | Absolute TMC descriptor payload offset in the decoded FBL |
| `descriptor` | Descriptor number within that payload |
| `cc`, `ltn` | Effective ALERT-C country code and location table number |
| `map_reference` | Descriptor map-reference field after CC-extension handling |
| `descriptor_ordinal_base` | First internal ordinal owned by the descriptor |
| `descriptor_index` | Zero-based LCD index within the descriptor |
| `map_ordinal` | Internal TMCLOCATION ordinal |
| `lcd` | Broadcast 16-bit location code |

## `uk-tmc-location-anchors-2026.03.csv` schema

The historical filename retains “anchors”, but the file now also contains
individual road-record points and directional chain metadata.

### TMC identity and topology

| Columns | Meaning |
|---|---|
| `map_ordinal`, `lcd` | Internal ordinal and broadcast location code |
| `previous_lcd`, `next_lcd` | Decoded TMC predecessor/successor references |
| `category`, `group_count`, `run_length_minus_one` | First affected-element projection from TMCLOCATION |

### Direct GEODB mapping

| Columns | Meaning |
|---|---|
| `raw_anchor` | First packed GEODB road anchor |
| `geodb_area`, `geodb_record` | Anchor high/low halves used by the runtime resolver |
| `area_file_offset`, `area_size` | Exact decoded road-area byte range |
| `bbox_west`, `bbox_south`, `bbox_east`, `bbox_north` | Containing GEODB area bounds in degrees |
| `area_center_lon`, `area_center_lat` | Arithmetic bbox center |
| `road_record_index` | Decoded road-record index; matches `geodb_record` for direct rows |
| `road_record_lon`, `road_record_lat` | Individual road-record point in degrees |
| `road_descriptor_index` | Type-13 road-codebook descriptor selected by the record |
| `record_inside_area_bbox` | Whether the point lies inside the local area bbox; false is retained for cross-boundary records |

All 4,222 direct road-record points lie inside member 0's overall geographic
bounds. A link may legitimately cross its local area boundary, explaining the
944 false values in `record_inside_area_bbox`.

### Chain coordinates and bearings

| Columns | Meaning |
|---|---|
| `previous_road_record_lon`, `previous_road_record_lat` | Direct point for an in-table predecessor when available |
| `bearing_to_previous_deg` | Initial bearing from this direct point to that predecessor |
| `next_road_record_lon`, `next_road_record_lat` | Direct point for an in-table successor when available |
| `bearing_to_next_deg` | Initial bearing from this direct point to that successor |

### Representative fallback

| Columns | Meaning |
|---|---|
| `representative_source` | `direct` or `linked_lcd` |
| `representative_source_lcd` | LCD supplying the representative point |
| `representative_hops` | Number of predecessor/successor links to the source; zero for direct rows |
| `representative_bbox_*` | Source area bbox |
| `representative_area_center_*` | Source area center |
| `representative_road_record_*` | Source road-record point |

For coarse use, every row has representative coordinates. For precision work,
prefer `representative_source = direct`; inspect `representative_hops` for
linked rows. The maximum fallback distance is 135 hops, and 125 rows exceed 10
hops.

### Decoder diagnostics

The remaining columns (`decoded_prefix_end_bit`, `record_bit_offset`,
`block_index`, `block_file_offset`, `block_size`, `auxiliary_offset`, and
`block_alignment`) make the export auditable against the packed source.

## Reproduction

Run from the parent `TMS/` workspace, where the source maps and XOR table are
available locally:

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

python3 TrafficReport/tools/extract_fbl_tmc_index.py \
  TrafficReport/tmp/Netherlands_osm.fbl \
  --member 0 --cc 8 --ltn 17 \
  --csv TrafficReport/data/exports/netherlands-tmc-index-2025.09.csv
```

Do not commit source maps, firmware archives, runtime binaries, Ghidra
projects, or license/key material merely to reproduce these outputs.

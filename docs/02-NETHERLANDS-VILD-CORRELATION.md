# Netherlands VILD ↔ NNG FBL correlation experiment

## Purpose

Use a public Dutch road-location database to identify how NNG links traffic-location
codes to map links. This is a **reverse-engineering reference experiment**, not a
claim that Dutch VILD codes are necessarily the same location-table variant used by
the `Netherlands-BeMobile` TMC service.

A valid reference table supplies many independent, known observations:

```
location code + road attributes + WGS84 point/line geometry + offsets
```

If the NNG FBL representation can be decoded for sufficiently many of those
observations, the discovered representation can then be tested against the UK map.

## Inputs

| Input | Source | Evidence |
|---|---|---|
| VILD 6.13.A | Netherlands NDW, public release, 25 August 2025 | `tmp/VILD6.13.A.zip`, unpacked under `tmp/vild/` |
| Netherlands map | Existing MediaNav backup | `tmp/Netherlands_osm.fbl` |
| NNG XOR key | Existing MediaNavToolkit extraction | `MediaNavToolkit/analysis/xor_table_normal.bin` |

The official NDW release supplies `VILD6.13.A.dbf` and WGS84 Point/Line/Area
Shapefiles. The main DBF contains **11,939** records. The geometry files contain
**9,844 points** and **1,405 lines**, joined by `LOC_NR`.

The map decrypts to an NNG `SET` v4.6.7.32 container. Its reported map bounding
box is `[0.2649, 51.6574]` to `[5.3139, 55.9208]`.

## Tool

`tools/correlate_vild_fbl.py` has no dependencies outside Python's standard library.
It:

1. parses the VILD DBF and WGS84 Point/Line Shapefiles;
2. exports normalized, auditable locations including road and offset references;
3. decrypts and inventories the NNG FBL container; and
4. tests only exact, reproducible FBL coordinate anchors.

Run it from the workspace root:

```bash
python3 TrafficReport/tools/correlate_vild_fbl.py \
  --vild-dir TrafficReport/tmp/vild \
  --fbl TrafficReport/tmp/Netherlands_osm.fbl \
  --out-dir TrafficReport/tmp/vild-fbl-correlation
```

It writes:

| Output | Meaning |
|---|---|
| `vild_locations.csv` | 11,939 VILD records with road attributes, offsets, and point/line geometry summaries |
| `fbl_probe.json` | FBL sections and every tested representation hypothesis |
| `candidate_matches.csv` | Only verified FBL ↔ VILD anchors; deliberately empty if no exact evidence exists |

## Result (2026-10-19)

The initial run completed successfully:

```
VILD: 11,939 records, 11,249 geometries; FBL: NED, 19 sections;
verified anchors: 0
```

`11,249 = 9,844` point geometries + `1,405` line geometries. The normalized CSV
contains useful records such as `LOC_NR=7262`, a `P3.3` point on road `A12` at
`4.437962817699, 52.050774994651`.

### Explicitly rejected approaches

These tests are negative results, not missing work:

1. **Bare uint16 search** — VILD `LOC_NR` values occur in the decrypted FBL at the
   ordinary frequency of arbitrary 16-bit values. They are not a plaintext code table.
2. **Fixed N+M bit pairs across road sections** — production section data yields many
   points outside the NED map bounding box. The section is not a flat coordinate stream.
3. **Consecutive `int32 / 2^23` coordinate pairs** — tested every WGS84 VILD point in
   both byte orders against road-related FBL sections 1, 4, 5 and 8. **Zero exact
   anchors** were found.

The tool intentionally does **not** output nearest-neighbour matches. That would
invent links: production FBL sections are tagged/pattern-matched data, and arbitrary
bit or int32 interpretations generate plausible-looking but false coordinates.

## Current limitation

MediaNavToolkit documents that real road geometry uses a tagged, nested/pattern-
matched record grammar. The existing pure-Python decoder emits an untrusted mixed
record stream; the DLL-reference path cannot currently run because Python's `unicorn`
module is absent. Therefore a VILD coordinate cannot yet be associated with one
specific NNG section-4 record or road segment.

## Next reverse-engineering step

Work on the **production FBL record grammar**, rather than searching code bytes:

1. make the existing DLL-reference decoder runnable (or port the required tagged
   record functions into pure Python);
2. decode tagged record type 2 (`lon:int32, lat:int32`) and the nested record groups
   in Netherlands sections 1 and 4;
3. use VILD's 9,844 known point geometries to match decoded junction/shape coordinates;
4. record the exact enclosing FBL record, field sequence and neighboring offset links
   for each confirmed VILD match;
5. identify a repeated code/link field across many matches; and only then apply that
   field grammar to `UnitedKingdom_osm.fbl`.

The Netherlands data remains valuable even if its VILD table is not identical to the
BeMobile broadcast table: it can reveal NNG's **map-link representation**. Before
using Dutch LCDs in a live TMC test, independently verify the provider's country,
LTN and table version.

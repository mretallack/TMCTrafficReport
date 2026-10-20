# Authoritative exports

This directory contains the durable, reproducible CSV outputs from the current
MediaNav TMC investigation. Temporary probes, firmware images, map binaries,
Ghidra projects, and intermediate logs remain outside version control.

## Files

| File | Rows | Purpose | SHA-256 |
|---|---:|---|---|
| `uk-tmc-index-2026.03.csv` | 4,529 | CC=12/LTN=10 LCD index from UK OSM SET member 0 | `6c88797b5f05ecf1ee0f1300b9d96838bc5c3ff7ef0b008577bb68120916ba93` |
| `uk-tmc-location-anchors-2026.03.csv` | 4,529 | UK LCD topology, GEODB anchors, road-record coordinates, area bounds, and chain bearings | `ce4eb0902300cd9cce9bbcfa5c9dfe5dc42e15ae35aac8f17a6b63e92c84f23b` |
| `netherlands-tmc-index-2025.09.csv` | 3,132 | Independent Netherlands CC=8/LTN=17 descriptor validation | `8f748244c2c0bd22385bbb55781fbfdc350c89ae934a9ae1865e2cf4d137d888` |

The UK files intentionally select SET member 0. It is a Scotland/northern-UK
map shard, not the complete national namespace. See
[`../../docs/17-CURRENT-UK-TMC-INDEX-EXTRACTION.md`](../../docs/17-CURRENT-UK-TMC-INDEX-EXTRACTION.md)
for exact scope, decoder evidence, field definitions, and limitations.

## Reproduction

Run from the parent TMS workspace, where the map and XOR table are held as
local research inputs:

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

Do not commit source map files, firmware archives, decompiler databases, or
license/key material merely to regenerate these exports.

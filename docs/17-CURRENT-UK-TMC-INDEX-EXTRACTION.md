# Current UK OSM TMC index and road-record coordinate extraction

## Result

The exact MediaNav 4 Linux runtime and current UK OSM FBL now yield a
reproducible TMC index, individual GEODB road-record coordinates, and
representative locations for every LCD in SET member 0.

Target:

```text
HeadUnitUpdate-2026-10-19/NaviSync/content/map/UnitedKingdom_osm.fbl
SET v4.6.7.32
SHA-256 ed3cffccefc13389e8fe0ef24067168614dfc8f0023bcd17a0fba4103965eaea
```

Tools:

```text
TrafficReport/tools/extract_fbl_tmc_index.py
TrafficReport/tools/extract_fbl_tmc_anchors.py
```

Exports:

```text
TrafficReport/data/exports/uk-tmc-index-2026.03.csv
4,529 data rows
SHA-256 6c88797b5f05ecf1ee0f1300b9d96838bc5c3ff7ef0b008577bb68120916ba93

TrafficReport/data/exports/uk-tmc-location-anchors-2026.03.csv
4,529 data rows
SHA-256 ce4eb0902300cd9cce9bbcfa5c9dfe5dc42e15ae35aac8f17a6b63e92c84f23b
```

The location export has:

- 4,222 records with a directly decoded first GEODB road anchor and individual
  road-record coordinate;
- 3,578 unique direct `(area, road-record)` pairs;
- 3,278 direct rows whose record point is inside the local area bbox and 944
  cross-boundary road points; all 4,222 are inside member-wide bounds;
- 307 records with no direct first anchor but a representative road point
  inherited from the nearest decoded predecessor/successor LCD;
- 4,529/4,529 rows with a representative road-record coordinate, bounding box,
  and area center;
- 3,420 predecessor and 3,420 successor chain bearings where both LCDs have
  direct record coordinates;
- 125 inherited locations farther than 10 links from their source, with a
  maximum of 135 links. Consumers must use `representative_hops` as a
  confidence indicator.

## Important scope correction: SET members are map shards

The current FBL contains 18 SET members. With the exact licensed stream
transform, 15 members expose valid `CC=12/LTN=10` descriptors. Member 0 has the
4,529-location descriptor that was the original extraction target, but it is
not the complete effective UK namespace.

Across those 15 populated members:

```text
37,707 descriptor rows (including duplicates)
30,044 unique LCD values
```

The exact runtime `FUN_00b21e7c` iterates map contexts and returns the first
context whose `FUN_002ec954` lookup yields a usable TMCLOCATION road object.
Consequently, member 0 is a valid primary geographic shard, not a proven
national singleton. Its decoded bounds cover Scotland/northern UK:

```text
longitude: -8.586235 .. -0.678986
latitude:  54.519516 .. 61.275787
```

Use `--member 0` when reproducing the 4,529-row files. Omitting `--member`
from the index extractor enumerates matching descriptors in every member.

## Exact licensed FBL transform

The former description of FBL decoding as only:

```python
plaintext[i] = ciphertext[i] ^ key[i % 4096]
```

was sufficient only for block zero. It is not correct for later 4 KiB blocks.
The exact ARM path is:

```text
ILICENSE_DISTRIBUTOR_IGOMAP
  -> FUN_005c11bc
  -> FUN_005aa324 / FUN_005aa230
  -> FUN_005bd24c
  -> FUN_005aa138
```

For each 32-bit word in a 4 KiB block:

```text
block_number = (block_start >> 12) & 0x3ff
key_index    = (word_index + block_number) & 0x3ff
adjustment   = 0                         for block zero
             = seed + block_number       for later blocks
plaintext    = (ciphertext + adjustment) XOR key[key_index]
seed         = decoded block-zero word 3
```

For this file the seed is `0x12`. Applying the exact transform yields `SET\0`
at file offset zero and the known member-0 TMC payload length 2,832. The
extractors now implement this exact transform.

## Exact current TMC lookup path

The matching 6.0.12.2.1166_r2 ARM runtime contains:

```text
FUN_002f2e84  TMC descriptor-vector builder
FUN_002f01a8  per-descriptor/LCD decoder
FUN_002ec898  CC/LTN descriptor selector
FUN_002ec7a8  LCD binary search
FUN_002ec954  TMCLOCATION lookup
FUN_00329d50  indexed TMCLOCATION block loader
FUN_0032943c  TMCLOCATION record decoder
FUN_0030ae88  GEODB road-area parser
FUN_002e7040  road-area offset lookup
```

Lookup flow:

```text
incoming CC/LTN/LCD
  -> FUN_00b21e7c iterates map contexts
  -> FUN_002ec954
  -> FUN_002ec898 selects descriptor
  -> FUN_002ec7a8 finds map ordinal
  -> FUN_0033dabc resolves object type 0x0c + ordinal
```

## Member-0 descriptor

Location:

```text
member start                 0x0200
relative-offset field        member + 0x02d7
relative TMC offset          0x03b2
length field                 absolute 0x05b2
payload start                absolute 0x05b6
payload size                 2,832 bytes
payload SHA-256              85bbdab2628b633d25777bebd1f617ca366638dad94145b28669b6c30d938110
```

Descriptors:

| Descriptor | Effective CC | LTN | Locations | Reference | LCD range |
|---:|---:|---:|---:|---:|---:|
| 0 | 12 (`C`) | 10 | 4,529 | 0 | 239–60,922 |
| 1 | 28 (`0x1c`) | 10 | 4,180 | 0 | 481–60,922 |

Normal incoming `CC=12/LTN=10` selects descriptor 0. The 32-bit descriptor
field's top bit extends the four-bit CC and is then cleared from the stored map
reference.

## Correct TMCLOCATION block/index semantics

There are 8,709 internal records in 137 blocks. Two earlier partial-decoder
assumptions were corrected against exact `FUN_0032943c` behavior:

1. The auxiliary index offset is direct within the aligned buffer returned by
   `FUN_002edad8`; original file alignment is irrelevant.
2. Its `extended(10,4)` entries are record **bit lengths**, not absolute record
   offsets. Record starts are cumulative sums from bit zero.

Before the six category-presence bits, non-empty records consume:

```text
previous LCD: signed extended(3,8)
next LCD:     signed extended(3,8)
6 x metadata: extended(17,1)
x selector:   21 bits
y selector:   20 bits
```

The map-specific `(17,1)` widths are recovered dynamically from GEODB type-2
metadata (`FUN_003157f8`). The coordinate widths are derived from the GEODB
common bounds. With these corrections, all 4,529 prefixes stay inside their
indexed record lengths; there are zero prefix overruns.

## GEODB road-area resolution

The member-0 GEODB type-2 metadata ends with maximum local area ID:

```text
10,596 = 0x2964
```

`FUN_002fb428/FUN_002fb39c` decode the type-9 fixed offset tables. Each high-byte
block consists of one 32-bit base offset followed by cumulative 16-bit deltas.
For member 0:

```text
type-9 fixed table           member + 0x0d9432
road-area data base          member + 0x0e3b12
road-area resolved span      absolute 0x000e3d12 .. 0x009125cc
```

All 1,357 directly referenced area IDs resolve to non-empty, monotonic ranges.
`FUN_0030d708` resolves area object ID `A` from boundary offsets `[A-1,A]`;
the earlier provisional `[A,A+1]` interpretation was corrected.
`FUN_0030ae88` begins each road-area block with four signed 32-bit bounds:

```text
west, north, east, south
```

Coordinates use `2^23` integer units per degree. The export includes the exact
area file offset and size, bbox and center, plus the individual coordinate from
the raw low-half road-record index (`index * 0x18` in the runtime array).

To reach each coordinate exactly, the extractor also reproduces the member-0
GEODB type-13 road codebook:

```text
FUN_003178a0  type-13 codebook parser
FUN_0034acc8  compact selector-tree parser
FUN_002ea2e0  primary codebook element parser
FUN_0034afdc  road-descriptor selector tree
FUN_002e9ee4  static 8-byte road descriptor
```

The selector tree has 124 nodes and 124 static descriptors. All 3,578 unique
referenced `(area,record)` pairs have valid record indices and decode without
errors. Record points range over:

```text
longitude -7.468300 .. -0.925552
latitude  54.685120 .. 60.603584
```

A road record can represent a link crossing its containing area's boundary;
therefore `record_inside_area_bbox` is exported rather than forcing/clamping
such coordinates. Every point remains within member 0's overall bounds.

Example:

```text
LCD 481
previous LCD 482
raw anchor 0x0909001d
area 2313, road record 29, descriptor 119
bbox -2.655800,55.997459 .. -2.476089,56.103027
road point -2.635635,56.034607
bearing to predecessor 144.592166 degrees
```

## Representative-location fields

Direct rows have:

```text
representative_source = direct
representative_source_lcd = same LCD
representative_hops = 0
```

The 307 records without a first direct anchor are located by an undirected
multi-source traversal of only their decoded predecessor/successor LCD links:

```text
representative_source = linked_lcd
representative_source_lcd = nearest directly located LCD
representative_hops = number of links
```

This does not pretend that an inherited point is the anchorless LCD's own road
record. It provides a reproducible nearest linked road point and an explicit
confidence metric. Direct and inherited point fields are kept separate.

Where both endpoints are direct, the export also gives:

```text
previous_road_record_lon / previous_road_record_lat
next_road_record_lon / next_road_record_lat
bearing_to_previous_deg
bearing_to_next_deg
```

These are TMC-chain bearings between decoded record points, not full road-link
shape bearings.

## Reproduction

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

## Remaining limitations

The current export now contains the individual road-record point, but not yet
the complete named road-link geometry:

- a road record's `+4/+8` point is decoded, while its adjacency-selected second
  endpoint and full polyline are not yet exported;
- `bearing_to_previous_deg` and `bearing_to_next_deg` describe the TMC LCD
  chain, not necessarily the final road-link tangent;
- road names still require following descriptor/resource string references;
- 944 direct rows are legitimate cross-boundary records and are marked with
  `record_inside_area_bbox = false` rather than clamped;
- inherited locations with large `representative_hops` are suitable for coarse
  lookup only.

The next refinement is road-record adjacency and name-resource decoding. This
can add a second endpoint, link bearing, and road label without changing the
proven LCD, anchor, area, or first-point mapping.

## HERE-to-OSM continuity

The old cached UK events came from the installed HERE 2019.Q4 map and were
initially compared only with SET member 0. They are absent from that 4,529-row
member-0 descriptor, but the later whole-SET extraction finds both codes in
current OSM member 12:

```text
LCD 10024 -> 51.442833, -0.927315
LCD 17602 -> 51.077484, -1.309616
```

This supports deliberate continuity in UK numeric location assignments across
the HERE-to-OSM migration. The old cache alone does not prove that every
retained LCD has identical segment, direction, or provider semantics, and the
two codes remain unsuitable as member-0 validation anchors.

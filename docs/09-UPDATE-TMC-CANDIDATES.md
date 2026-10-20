# 2026-Q1 update payload: TMC lookup-data candidate audit

## Scope

Audited the local reference copy:

```text
HeadUnitUpdate-2026-10-19/NaviSync/
```

The payload contains 692 files and approximately 3.1 GB of content. This note
distinguishes (1) TMC provider/service metadata, (2) TMC event/UI resources,
and (3) plausible storage for the static location-reference mapping.

## How large must a UK lookup be?

A national ALERT-C table cannot plausibly fit in the installed `.tmc` payload
sizes of 1,188–2,208 bytes.

A conservative lower bound for 30,000 UK locations is:

```text
16-bit LCD + 32-bit map-link/reference = 6 bytes × 30,000 = 180 KB
```

A useful topology needs directional predecessor/successor references as well:

```text
LCD + map link + positive offset + negative offset
≈ 10–14 bytes × 30,000 = 300–420 KB before names or compression
```

For comparison, the public Netherlands VILD 6.13.A reference set has 11,939
records in a 3.46 MB DBF, plus 9,844 point and 1,405 line geometries. A UK
compiled table can be substantially smaller than that, but not 1–2 KB.

Therefore an actual UK LCD→road association must be either:

1. compactly encoded inside a large map-related data file; or
2. generated from a large map graph plus a compact per-location reference layer.

## Update inventory by relevant file class

| Class | Files | Total bytes | TMC lookup assessment |
|---|---:|---:|---|
| `.fbl` | 30 | 1,690,454,528 | **Primary candidate**: large country road/map graphs |
| `.fpa` | 30 | 660,609,536 | Address/geocoding indexes; secondary future name-resolution aid |
| `.hnr` | 3 | 199,454,926 | Routing weights/road IDs; no demonstrated LCD mapping |
| `.poi` | 35 | 746,672,736 | Points-of-interest, not TMC road references |
| `.tmc.stm` | 6 | 582 | Shadow descriptors only |
| Actual `.tmc` | 0 | 0 | **Absent** |
| `global_cfg.zip` | 1 | 8,485,402 | Provider/LTN/service metadata and TMC UI assets, no location list |
| `FILECACHE` | 1 | 9,751,340 | Cached iGO resource ZIP streams: event/UI/config, no location table name found |

## Provider `.tmc` descriptors

The update contains only these shadows:

| File | Expected payload size |
|---|---:|
| `France-V-Trafic.tmc.stm` | 1,188 B |
| `UnitedKingdom-Inrix.tmc.stm` | 1,206 B |
| `Germany_HERE.tmc.stm` | 1,276 B |
| `Belgium-BeMobile-light.tmc.stm` | 2,208 B |
| `Luxembourg-BeMobile.tmc.stm` | 2,208 B |
| `Netherlands-BeMobile.tmc.stm` | 2,208 B |

The actual payload files are absent. Given the size bound above, these are
service/tuning descriptors, not national location lists.

## Candidate assessment

### 1. Country `.fbl` files — highest-priority candidate

The current UK FBL is 254,839,808 bytes. It is the only country-scale map file
large enough to carry location→map-link associations. It is XOR-obfuscated on
disk, but after the known XOR transform it has a structured NNG SET container.

Known LCDs 17602 and 10024 occur at ordinary random 16-bit frequency in the
FBL. This only rules out a **plain uint16 table**. It does not rule out:

- delta-coded location references;
- variable-length integer/dictionary encoding;
- references keyed by an internal segment/tile ID;
- a table interleaved with graph records; or
- a compressed secondary map section.

Therefore FBL remains the correct data target, but raw code searching is not an
extraction method.

### Direct variable-integer representations — also rejected

The FBL record grammar uses a UTF-8-like variable integer encoding, so the 32
observed UK codes were also tested as NNG three-byte varints and standard ULEB128
three-byte values. To avoid the known two-byte collision problem, only values
whose encoding length is three bytes were compared with randomly selected
three-byte controls.

| Representation | File | Known-code mean | Control mean | Result |
|---|---|---:|---:|---|
| NNG UTF-8-like varint | FBL | 14.48 | 16.28 | no enrichment |
| NNG UTF-8-like varint | FPA | 9.76 | 9.17 | no enrichment |
| ULEB128 | FBL | 15.35 | 16.47 | no enrichment |
| ULEB128 | FPA | 10.82 | 10.41 | no enrichment |

The association is therefore not a plainly stored LCD in raw, byte-swapped,
NNG-varint, or ULEB128 form. It must be represented indirectly, for example
through map-record IDs, a dictionary, or delta/bitstream coding.

### ULC2 9.1.3 runtime result — FBL-labelled country map-object delta index confirmed

Subsequent read-only analysis of the genuine ULC2 9.1.3 NNG navigation runtime
provided the missing implementation evidence. It has two separate paths:

```text
standalone *.tmc loader → small licensed TMC-content objects
country FBL map object  → encoded TMC index → LCD → internal map reference
```

The runtime refuses TMC service validation if the country FBL is absent, then
resolves CC/LTN/LCD through a country map object. Its map-section factory
constructs a TMC index object from a packed section buffer. The per-descriptor
decoder reads 4-bit CC, 6-bit LTN, a 16-bit location count, a packed
map-reference field, and a cumulative delta-coded LCD stream; it reconstructs
a sorted `uint16` LCD array and binary-searches it for traffic events.

This proves the **storage model** for the 9.1.3 map generation and strongly
supports the same encoded-FBL association for the current update. It does not
yet prove byte-identical outer section headers in the current 2026 `SET
v4.6.7.32` UK FBL. The current extraction target is its inner section/directory
boundary and the equivalent CC=C/LTN=10 descriptor. Full evidence and exact
function trace: `13-ULC2-TMC-FBL-DECODER.md`.

### 2. UK `.fpa` — rejected as a direct table, useful later

`UnitedKingdom_osm.fpa` is a 172,926,976-byte 2026.03 GBR address/geocoding
index. Both byte orders of 17602 and 10024 occur at statistical random baseline.
It contains no readable `INRIX`, `Trafficmaster`, `ITIS`, or provider metadata.

It is not a direct LCD table. It may become useful if reverse engineering yields
an internal road/address object ID that needs a human-readable name.

### 3. `FILECACHE` — inspected, not the national table

`save/FILECACHE` is a 9.75 MB concatenated iGO ZIP-resource cache. It contains
at least 930 local ZIP entries, including:

```text
config/tmceventlist.csv
config/tmcsettings.ini
config/tmcweight.dat
config/traffic_categories.csv
config/traffic_codeconfig.bin
config/traffic_codeconfig.csv
config/traffic_phrases.bin
ui_core/common/ui/tmc.lua
ui_core/common/ui/tmc.ui
```

This establishes that the installed iGO software has event definitions,
colour/weight rules, phrases, and TMC UI logic. It does not expose a
`POINTS.DAT`, `ROADS.DAT`, `POFFSETS.DAT`, `LOCATIONDATASETS.DAT`, `.tmc`, or
provider/location-table name. These are event/UI resources, not the static
country location graph.

### 4. `global_cfg.zip` — service selection only

This archive identifies the target service precisely:

```text
GBR / CC=C (decimal 12) / ECC=E1 / LTN=10 / SID=10
INRIX / Pay TMC / Light encryption
```

It contains provider selection, licence aliases, TMC icons, and event display
settings. It has no national location list. See
`07-UK-INRIX-SERVICE-METADATA.md`.

### 5. HNR — low-priority supporting candidate

The Europe HNR files contain routing-variant weights and opaque internal road
IDs. Current analysis has not linked those IDs to FBL segments, let alone LCDs.
They may help once the true map runtime is available, but are not a standalone
location table candidate.

## Services: configured versus live

The 2026 update configures six country/provider combinations. This proves only
that the navigation software recognises them; it does **not** prove that a
current FM broadcast exists.

| Update entry | Configuration fact | Current live-broadcast conclusion |
|---|---|---|
| UK INRIX | GBR / E1 / LTN 10 / SID 10 | Trafficmaster ended in 2023; current INRIX FM status requires direct verification and must not be inferred from config |
| France V-Trafic | bundled provider descriptor | plausible but not independently verified by this audit |
| Germany HERE | bundled descriptor; public-radio TMC historically widespread | strongest current public indication, but provider label is not the FM broadcaster |
| Belgium Be-Mobile | bundled descriptor | configured; current on-air status unverified here |
| Netherlands Be-Mobile | bundled descriptor | configured; current on-air status unverified here |
| Luxembourg Be-Mobile | bundled descriptor | config presence only; no evidence of a current national service |

A currently live non-UK country would be useful as a **validation source** only
if we can capture real 8A messages and independently associate them with a
known contemporaneous incident. It would not automatically reveal the UK
INRIX LTN-10 mapping.

## Best next extraction path

Assuming the static table was delivered with the offline update, the evidence
now ranks the paths as:

1. **Reverse the current UK FBL inner section/directory boundary** and apply the
   recovered ULC2 9.1.3 CC/LTN delta-index decoder. A candidate must validate
   against multiple observed UK LCDs, not raw-byte frequency.
2. **Recover/trace the actual current head-unit Linux navigation runtime** that
   opens the FBL if current `SET v4.6.7.32` outer/inner container changes block
   application of the reference decoder. This remains the definitive way to
   establish the current map-reference output semantics.
3. Use the FBL and, later, FPA to export an internal road graph/name index once
   the decoder yields the internal map references.
4. Use any verified live foreign RDS-TMC service only to validate generic
   ALERT-C parsing/encoding and any recovered map-reference model.

The Windows NaviExtras `nngine.dll`, the standalone `.tmc` shadows, global
configuration, and FILECACHE event/UI resources do not contain the UK lookup
in a directly usable form.

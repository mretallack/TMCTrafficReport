# Netherlands DLL calibration: current boundary

## Goal

Use the official Netherlands VILD location database to identify the NNG FBL
record structure that associates a traffic location with a road/map link, then
apply that structure to the UK map.

## Restored reference path

The line-level NNG DLL reference decoder is operational (see
[`03-NNG-DLL-REFERENCE-DECODER.md`](03-NNG-DLL-REFERENCE-DECODER.md)). It
emulates `FUN_1024A720`, converting one newline-delimited section pattern into
an ordered uint32 record stream.

## Section-4 profile

A deterministic 256-line sample of Netherlands section 4 was run through the
DLL reference decoder.

Stable control families occur in the output:

```
0x8000, 0x8001, 0x8008, 0x8009, 0x800A,
0x800D, 0x8016, 0x8017, 0x8018, 0x8019, 0x801F,
0x8030, 0x8032, 0x8033, 0x8036
```

They are grammar/structure controls, not Dutch location codes:

- all common families other than `0x8008` and `0x8018` carry payload `0`;
- `0x8008` carries only small values `1`–`3` in the sample;
- `0x8018` carries values such as `2`, `7`, `18` and `22`;
- neither nonzero payload family contains an official VILD `LOC_NR`.

The normal data values do not identify the table either. Among 2,425 decoded
scalar values in the range 1,000–65,535, 319 (13.15%) happened to be VILD
codes. The official VILD set occupies 18.38% of that numerical range, so this
is not an enrichment signal.

**Conclusion:** `FUN_1024A720` exposes the FBL grammar but does not attach a
VILD LCD to a specific map link. Searching its control payloads or scalar
values would be another false-positive method.

## Why the current higher-level wrapper is insufficient

The recovered Ghidra decompilation identifies the layers above the line parser:

```text
FUN_1024A720  pattern/unit → uint32 records
     ↓
FUN_10249210  repeatedly consumes record groups
     ↓
FUN_102460D0  graph builder / spatial-key serializer
```

`FUN_102460D0` does not accept an isolated line. It requires a populated
map-loader context, pattern tables, output buffers, record array, and spatial
index structures. The current `nng_emulator.py` legacy helper was corrected to
allocate a bounded output buffer suitable for a production map, but it returns
zero records when given an entire 5.66 MB section: the function must be called
through the full section-loading caller, not directly.

Likewise, the legacy tagged-gap reader begins at an `END` tag in the production
Netherlands gap area and cannot reveal link records without a correct loader
start/context.

## Exact next target

The next implementation task is to emulate the **section-loading caller of
`FUN_1024A720`**, not to add more code-value heuristics:

1. Recover the function entry and parameter layout surrounding the documented
   `FUN_1024A720` call in the decompilation (the map section loader).
2. Recreate the initial loader context fields and allocator callbacks used by
   that caller.
3. Trace its calls into `FUN_10249210` and capture the graph builder's emitted
   spatial keys and coordinate/tagged groups.
4. Match those decoded coordinate groups to the 9,844 VILD WGS84 points and
   1,405 VILD line geometries.
5. Only after a repeated VILD-to-record relationship is demonstrated, run the
   same loader on `UnitedKingdom_osm.fbl` and export its traffic location map.

## UK feasibility assessment

The DLL work remains the strongest available path to UK code-to-road mapping,
but this calibration has **not yet proved** that the Dutch VILD/BeMobile mapping
is stored in the same FBL layer. A successful full-loader trace is the next
go/no-go gate. If it still yields no VILD association, the UK `LTN=10` table is
more likely external/provider-specific and must be recovered independently.

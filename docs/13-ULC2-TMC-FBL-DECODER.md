# ULC2 9.1.3: TMC location index is country-map-container resident and bitstream encoded

> **Current result (2026-10-20):** the exact Linux ARM runtime confirmed this
> decoder, and the current UK OSM payload was found at absolute offset `0x5b6`.
> See `17-CURRENT-UK-TMC-INDEX-EXTRACTION.md` for the 4,529-code C/10 export
> and the installed-HERE map mismatch.

## Result

Static reverse engineering of the ULC2 9.1.3 Windows CE/MIPS `nngnavi.exe`
shows that TMC location resolution uses a **map-resident, compressed location
index**, not a plaintext national location list and not the standalone `.tmc`
file loader.

This is the first direct code evidence supporting the working hypothesis for
the current UK maps: the LCD → map-reference association is encoded within
map-container data, most plausibly the country FBL.

It does **not** yet prove that the 2026 Linux runtime uses byte-identical
section headers or that a particular outer section number in the current UK
FBL is the TMC index. The inner descriptor encoding and resolver design are
now known from the 9.1.3 reference runtime.

## Evidence chain

### 1. Standalone `.tmc` files use a separate path

`FUN_004dfcf4` enumerates `folders/*.tmc`, opens each file, checks its licence,
and creates a standalone TMC-content object. This is distinct from the map
section decoder below.

The small `.tmc` payload expected by current update metadata therefore remains
a service/tuning descriptor candidate, not a plausible national LCD table.

### 2. TMC service requires a country FBL map object

`FUN_0031e9b8` obtains a country map object from the map manager. If it cannot
find one it logs:

```text
TMCInfo validation failed: FBL(MAP) file for country not exist
```

`FUN_00319a78` handles country changes. It obtains the country FBL map context
and passes that context into the TMC subsystem; on failure it logs:

```text
country FBL file not found, TMC logic update GPS_COUNTRY_CHANGED_EVENT failed
```

### 3. Incoming CC/LTN/LCD is resolved through map contexts

`FUN_00829844` receives the decoded TMC event fields, iterates active map
contexts, and calls `FUN_0082555c`. If no record is returned it emits:

```text
TMC Location not found in map.
CC: 0x%02hhx LTN: 0x%02hhx LOCATIONID: 0x%04hx
```

`FUN_0082555c` obtains each map object then calls `FUN_0069a47c`, the immediate
map-resident location lookup. A successful result must identify a non-empty
map-link/record before the traffic event is accepted.

### 4. The map object binary-searches decoded LCDs

`FUN_0069a47c` selects a descriptor using service fields and calls
`FUN_0002c7d8` with the incoming 16-bit location code as the search key. The
searched memory is a sorted `uint16` array at descriptor offset `+0x14`.

The selected descriptor list is at map-object offset `+0x58`; the number of
descriptors is at `+0x5c`.

### 5. The LCD array is reconstructed from a packed bitstream

The sole caller of `FUN_00699e1c` is the generic map-container section factory
`FUN_006a240c`, case `12`. That case creates the 0x60-byte TMC map-index object
and passes a section buffer to the decoder.

`FUN_00699e1c` constructs the descriptor vector. For each descriptor it calls
`FUN_00699c5c`, which decodes:

| Decoded field | Width / representation | In-memory destination |
|---|---|---|
| CC/service selector | 4 bits (with an extension flag) | `descriptor + 0x04` |
| LTN | 6 bits | `descriptor + 0x05` |
| location count | 16 bits | `descriptor + 0x10` |
| packed map-reference field | aligned 32-bit field | `descriptor + 0x08` |
| cumulative LCD list | delta-coded packed bits | sorted `uint16[]` at `descriptor + 0x14` |

The LCD decoder is exact in `FUN_00699c5c`:

```text
for each of N locations:
    flag = read 1 bit
    if flag == 1:
        delta = 1
    else:
        delta = variable packed integer
        if delta != 0: delta += 1
    lcd = (previous_lcd + delta) modulo 65536
    append lcd as uint16
```

The variable integer begins with a 4-bit value and uses all-ones sentinel
values to extend its bit width. It is therefore not represented as a fixed
little- or big-endian `uint16` in the FBL byte stream.

The reference runtime uses LSB-first bit consumption within little-endian
32-bit words (`FUN_001e98fc` and `FUN_001e994c`).

## Why previous raw searches failed

The current UK FBL/FPA raw searches for `17602` and `10024` were correctly
rejected as random collisions. This decoder explains why:

1. location codes are stored as **deltas**, not a direct code array;
2. values occupy variable bit widths and may start at non-byte boundaries;
3. the runtime reconstructs a sorted `uint16` LCD index in memory before
   binary-searching it;
4. the index also carries a map-record/reference mapping, so code recovery
   requires the outer section and descriptor context, not just LCD values.

## Current UK FBL comparison

The current map is:

```text
HeadUnitUpdate-2026-10-19/NaviSync/content/map/UnitedKingdom_osm.fbl
SET v4.6.7.32
254,839,808 bytes encrypted / outer-XOR protected
SHA-256 ed3cffccefc13389e8fe0ef24067168614dfc8f0023bcd17a0fba4103965eaea
GBR map bbox [-8.5862, 54.5195] → [2.9152, 61.2758]
```

Its real 20-entry outer directory is a little-endian offset table at decrypted
file offset `0x58`. Its non-zero entries begin at `0x200` and end at
`0xF308C00`; all are 0x200-aligned. A prior coordinate-oriented parser latched
onto a later `GBR`-like byte sequence at `0x476` and therefore reported a
non-authoritative 16-section view. That parser must not be used as a current
container-directory source.

Applying the recovered decoder **at each outer section start** produces
syntactically plausible random bitstreams but no CC=C/LTN=10 descriptor. A
second byte-aligned scan of the three compact outer sections found many
superficial C/10 candidates, but none decoded all 32 observed UK LCDs; the best
matched only 26. Large random delta-decoded lists naturally include many
16-bit values, so these are explicitly rejected false positives.

The current FBL therefore has a recovered outer directory but its TMC index
starts at an **inner offset** selected by the current map loader, not at an
outer-section start or arbitrary byte position. The type-12 equivalent still
needs its inner section/directory boundary.

## Exact next target

To extract current UK mappings, locate the inner map-container section
boundaries and the `type 12` equivalent in the current FBL version, then apply
the recovered descriptor decoder and validate the candidate whose CC/LTN is
`C/10` and whose decoded LCD set contains the known car-event codes:

```text
17602, 10024, and the other 30 observed UK LTN-10 codes
```

A valid candidate must decode multiple known codes—not merely contain raw byte
patterns—and must expose a consistent map-reference progression.

## Evidence artifacts

```text
TrafficReport/tmp/ghidra-ulc2-913-tmc-resolver-refs.log
TrafficReport/tmp/ghidra-ulc2-913-tmc-resolver-core.log
TrafficReport/tmp/ghidra-ulc2-913-fbl-tmc-lookup-core.log
TrafficReport/tmp/ghidra-ulc2-913-tmc-index-builders.log
TrafficReport/tmp/ghidra-ulc2-913-tmc-descriptor-decoder.log
TrafficReport/tmp/ghidra-ulc2-913-map-section-factory-callers.log
TrafficReport/tmp/ghidra-ulc2-913-map-section-dispatcher-callers.log
```

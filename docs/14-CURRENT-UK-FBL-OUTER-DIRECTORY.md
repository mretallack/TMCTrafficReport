# Current UK FBL outer directory and descriptor-scan audit

> **Superseded update (2026-10-20):** the exact 6.0.12.2 ARM runtime was
> recovered and the inner payload was located at absolute FBL offset `0x5b6`.
> The current OSM CC=C/LTN=10 list has 4,529 LCDs. See
> `17-CURRENT-UK-TMC-INDEX-EXTRACTION.md`. This note remains the record of the
> earlier controlled negative scan before the logical GEODB offset was known.

## Purpose

This note records the first direct comparison of the recovered ULC2 9.1.3
map-resident TMC descriptor decoder with the current UK map:

```text
HeadUnitUpdate-2026-10-19/NaviSync/content/map/UnitedKingdom_osm.fbl
SET v4.6.7.32
SHA-256 ed3cffccefc13389e8fe0ef24067168614dfc8f0023bcd17a0fba4103965eaea
```

It supersedes the coordinate parser's accidental use of a later `GBR`-like
byte sequence as a section directory.

## Recovered outer directory

After normal outer XOR decoding, the true directory is 20 little-endian
absolute offsets at file offset `0x58`:

```text
index: offset
 0: 0x00000000
 1: 0x00000200
 2: 0x01F8A400
 3: 0x03977400
 4: 0x048D5C00
 5: 0x05A20C00
 6: 0x0642F800
 7: 0x06EBB800
 8: 0x074B7400
 9: 0x074F6E00
10: 0x07560800
11: 0x075A9C00
12: 0x08702800
13: 0x09DA8400
14: 0x0B107600
15: 0x0BE5B400
16: 0x0CE2C600
17: 0x0D6DAE00
18: 0x0E7F2C00
19: 0x0F308C00
```

All non-zero starts are 0x200-aligned. The last offset is near the actual file
end. The table is therefore a real outer FBL directory, not a random collision.

## Controlled descriptor tests

The ULC2 decoder was applied to each outer section beginning using its exact:

```text
LSB-first bit order in little-endian 32-bit words
4-bit CC
6-bit LTN
16-bit location count
32-bit packed map reference
cumulative delta-coded uint16 LCDs
```

Every outer section beginning can yield syntactically parseable values, but no
outer section starts with the target CC=C/LTN=10 descriptor.

A second scan considered every byte-aligned descriptor-looking start in the
three compact outer sections (8, 9, and 10). It rejected candidates unless they
had C/10, a plausible location count, and a fully decodable LCD stream. Many
false candidates remained because a random decoded list containing 50,000
values naturally includes many of 32 observed 16-bit codes. The best candidates
matched 26/32 observed LCDs; **none matched all 32**, including the anchor pair
`17602` and `10024` together.

For a representative 50,269-value uniform random list, one specified 16-bit
code appears with probability about `0.5356`, giving `17.14 ± 2.82` expected
matches out of 32. The single-candidate probability of 26 or more matches is
about `0.00107`; after the 946 descriptor candidates tested in these three
sections, the probability of at least one such result is about `0.636`. The
observed maximum of 26 is therefore not evidence of a table after accounting
for multiple testing (and the real candidate lists are not perfectly uniform).

This is a negative result, not a table extraction. It demonstrates that:

1. outer-section starts and arbitrary byte starts are not the decoder input;
2. matching a few location values is statistically insufficient;
3. the exact inner section offset/directory chosen by the current map loader is
   required before a descriptor can be trusted.

## Current boundary

The ULC2 map section accessor first reads a 4-byte length at a map-object field
such as `+0xBC`, then supplies an inner buffer and offset to the type-12 TMC
index decoder. The current UK FBL has the outer directory above, but this
specific current map-object field mapping has not yet been recovered.

Next: reverse the current runtime's FBL loader, or recover a matching 9.1.3
FBL sample with known inner offsets, to map current outer-section entries to
that inner buffer model. See `13-ULC2-TMC-FBL-DECODER.md` for the proven inner
decoder and runtime trace.

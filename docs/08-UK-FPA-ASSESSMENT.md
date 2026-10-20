# UK FPA assessment: address index, not a TMC location table

## File examined

```text
HeadUnitUpdate-2026-10-19/NaviSync/content/map/UnitedKingdom_osm.fpa
```

This is the address-search companion to the current 2026-Q1 UK map. It is
172,926,976 bytes on the update USB and decrypts with the established repeating
XOR key to an NNG `SET` v4.6.7.32 container.

Readable metadata confirms the country/map family:

```text
[nng]#COUNTRY# 2026.03
© 2026 NNG Ltd. with OpenStreetMap
_GBR|2026.03|||
```

The data was built on 5 June 2026 by `convl_nng` and `convp_rn`, consistent with
an address/geocoding/search-index build rather than a traffic provider payload.

## TMC evidence tests

Known car-cache codes were tested over every overlapping two-byte window in the
**decrypted** FPA. The expected random occurrence rate is 2,638.66 per 16-bit
value (standard deviation 51.37).

| Code | Byte order | Occurrences | Z score |
|---:|---|---:|---:|
| 17602 | little (`c2 44`) | 2,640 | +0.03 |
| 17602 | big (`44 c2`) | 2,624 | -0.29 |
| 10024 | little (`28 27`) | 2,579 | -1.16 |
| 10024 | big (`27 28`) | 2,574 | -1.26 |

None differs meaningfully from random byte occurrence. This rules out a plain
little- or big-endian LCD table in the FPA just as it did in the FBL.

The literal ASCII sequence `TMC` appears four times, but each occurrence is
surrounded by high-entropy binary data with no readable strings, structured
record boundary, or provider metadata. Four hits in a 173 MB binary are not
meaningful evidence of TMC content.

No `INRIX`, `Trafficmaster`, `ITIS`, or `Traffic` text exists in either ASCII or
UTF-16LE form after decryption.

## Conclusion

The `.fpa` is an **address-search/geocoding index**, not the UK INRIX location
code list:

- it contains no directly searchable `(LCD → road / coordinate / offset)` data;
- it contains no TMC provider/service metadata; and
- its matching values for known LCDs are random collisions.

It may still become useful later: if the actual head-unit navigation runtime is
reversed and yields an internal road/address object ID, the FPA could potentially
supply the human-readable road/address name for that object. It does not provide
a direct route from `loc=17602` to a road.

The relevant provider/LTN metadata remains in `global_cfg.zip`, documented in
`07-UK-INRIX-SERVICE-METADATA.md`.

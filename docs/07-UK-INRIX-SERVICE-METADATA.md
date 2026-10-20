# UK INRIX TMC service metadata from `global_cfg.zip`

## Source

Extracted read-only from the 2026-Q1 update reference copy:

```text
HeadUnitUpdate-2026-10-19/NaviSync/content/global_cfg/global_cfg.zip
```

Relevant members are retained under:

```text
TrafficReport/tmp/globalcfg-tmc/
```

| Member | Purpose | Size |
|---|---|---:|
| `config/tmc_cc_ecc_sid_ltn.csv` | Country/ECC/LTN/SID/provider selection matrix | 15,604 B |
| `config/tmc_info_database.ini` | Same provider records with labelled fields | 26,768 B |
| `config/tmc_provider_list.dat` | Broadcast/provider tuning metadata | 29,326 B |
| `config/tmc_interim_list.csv` | Licence-to-country/LTN/provider aliases | 383 B |

All but the interim CSV are UTF-16LE text.

## Decisive UK match

`tmc_info_database.ini` has labelled fields:

```text
version;Country;igocode;CC;ECC;LTN;ServiceProvider;
TMCtype;TMCencription;SID;SVK;TransmittedLTN;LICID
```

The active car cache records use:

```text
cc=12  ltn=10  sid=10
```

The matching archive row is:

```text
United Kingdom;GBR;C;E1;10;INRIX;Pay TMC;Light encryption;10;;10;1,266
```

Therefore the cache is specifically associated with:

| Field | Value |
|---|---|
| Country | United Kingdom / `GBR` |
| ALERT-C CC | `C` hexadecimal = decimal **12** |
| ECC | `E1` |
| LTN | **10** |
| Provider | **INRIX** |
| Service ID (SID) | **10** |
| TMC type | Pay TMC |
| Encryption mode | Light encryption |
| Transmitted LTN | **10** |
| Licence IDs | `1`, `266` |

This matches both known cached traffic events, including:

```text
loc=17602 ... cc=12 ltn=10 ... sid=10 event_1=807
loc=10024 ... cc=12 ltn=10 ... sid=10 event_1=806
```

## Related UK service records

The configuration also retains older/alternate UK services:

| Provider | LTN | SID | Encryption | Licence IDs |
|---|---:|---:|---|---|
| Trafficmaster | 7 | 7 | Light encryption | 2 |
| NAVTEQ TRAFFIC | 7 | — | Light encryption | 72 |
| INRIX | 10 | 10 | Light encryption | 1, 266 |
| INRIX | 10 | 11 | Conditional Access | 87 |

`tmc_interim_list.csv` further describes licence IDs `1` and `266` as
English TMC/INRIX with country code 12 and LTN 10.

`tmc_provider_list.dat` contains UK service records `10100` (Trafficmaster) and
`10101` (ITIS), the latter with UK/LTN/SID fields `GBR,10,10,12`. This is
consistent with the configured INRIX service identity but is tuning/provider
metadata, not road-location data.

## What is and is not present

This archive provides an **actionable service-selection map**:

```text
CC + ECC + LTN + SID + provider + encryption mode + licence alias
```

It does **not** contain an ALERT-C location list: no `POINTS.DAT`, `ROADS.DAT`,
`POFFSETS.DAT`, LCD-to-coordinate table, or road-segment mapping was found among
the archive members. The update's `UnitedKingdom-Inrix.tmc.stm` is still only a
97-byte shadow descriptor for an expected 1,206-byte payload.

The metadata proves that the target mapping must match the UK **INRIX LTN 10,
SID 10** table. It rules out accidentally using the older Trafficmaster LTN 7
or the INRIX SID 11 conditional-access variant.

# How We Found the TMC Location Codes

## Overview

This document details how we extracted the **TMC (Traffic Message Channel) location codes**
from the Dacia MediaNav head unit. These codes are what the car's navigation system uses
to map a 16-bit TMC location code to a specific road segment.

## Why This Matters

For RDS-TMC to work, the transmitter and receiver must use the **same location code table**.
If we transmit "location code 17602" but the car expects "17602 = M25 J23", it won't work.

The event cache supplies the **observed on-air location codes**, not the static
location table itself. The table must still be present in a form the navigation
runtime can resolve.

Current direct reverse-engineering evidence from the ULC2 9.1.3 NNG runtime
shows that the static TMC location index is built from a delta-coded bitstream
inside map-container data associated with the country FBL. The runtime
reconstructs a sorted `uint16` LCD array keyed by CC/LTN and binary-searches it
for an incoming event. Thus the FBL is not merely a separate road network: it
contains (or supplies the container section containing) the encoded
location→map-reference association. See
`13-ULC2-TMC-FBL-DECODER.md`.

Earlier candidate hypotheses were:
- In the `.tmc.stm` files (shadow containers — not the real data)
- In a plaintext/raw form in NNG/iGO `.fbl` map files (disproved)
- Fetched from the internet as a standalone table (not supported by the copied update)

## What We Found

### Source Files

| File | Location | Purpose |
|------|----------|---------|
| `trafficevents_A.txt` | `/NaviSync/save/` | Primary traffic event cache |
| `trafficevents_B.txt` | `/NaviSync/save/` | Backup traffic event cache |
| `tmc_provider_list.txt` | `/NaviSync/save/` | TMC provider configuration |

### Example Entry

From `trafficevents_A.txt`:

```
EVENT htmc=1 loc=17602 extent=1 dir=1 bidi=0 age=59 cc=12 ltn=10 new=1 tmc_source=0 sid=10 qdecoded=1 snd_id=0 event_1=807  loaded=1
EVENT htmc=2 loc=10024 extent=1 dir=1 bidi=0 age=59 cc=12 ltn=10 new=1 tmc_source=0 sid=10 qdecoded=1 snd_id=0 event_1=806  loaded=1
```

### Field Meanings (ALERT-C / ISO 14819)

| Field | Value | Meaning |
|-------|-------|---------|
| `loc` | 17602 | **16-bit location code** — this is the ALERT-C code for a specific road segment |
| `event_1` | 807 | **11-bit event code** — type of traffic event (e.g., queue, accident) |
| `extent` | 1 | How many location points the event spans |
| `dir` | 1 | Direction: 0 = both, 1 = positive, 2 = negative |
| `cc` | 12 | Country Code: 12 = United Kingdom (ISO 3166-1) |
| `ltn` | 10 | Location Table Number: 10 = UK |
| `bidi` | 0 | Bidirectional flag |
| `age` | 59 | Age of the event in minutes |

### Where These Files Come From

The files are stored in the MediaNav's **`/NaviSync/save/`** directory on the USB drive.
They are updated when:
1. The car connects to a phone with the Dacia MediaNav Update app
2. A map update is performed via USB
3. (Potentially) When connected to the official Renault/Dacia update service

The `.tmc.stm` files in `/NaviSync/content/tmc/` are **shadow containers** that point to
runtime data — the actual TMC payload is not stored in the map backup.

## How to Get Fresh Codes

To get more location codes:

1. **Drive with the car** — let it receive TMC data over FM (if a station is broadcasting)
   or via the phone app connection
2. **Extract the USB drive** after a drive
3. **Read `trafficevents_A.txt`** — it will contain the codes the car has learned

The more you drive, the more codes you'll accumulate in these files.

## Using These Codes in Transmission

These are the exact codes the car expects. To transmit a traffic event:

- Use `loc=17602` in the 8A TMC message
- Use `event_1=807` (or other event codes from ISO 14819-2)
- Set `ltn=10` (UK), `cc=12` (UK)

The car's navigation system will interpret these as real traffic events.

## File Locations in This Project

- Original dump: `/home/markretallack/buildhome/dacia/`
- USB backup: `/home/markretallack/buildhome/dacia/usb-disk/disk-backup-with-map-Apr2026.zip`
- Extracted files: `/home/markretallack/buildhome/TMS/TrafficReport/dump/`
  - `trafficevents_A.txt`
  - `trafficevents_B.txt`
  - `tmc_provider_list.txt`

## References

- ISO 14819-1: ALERT-C protocol & message structure
- ISO 14819-2: Event and information codes
- ISO 14819-3: Location referencing
- Wikipedia: Traffic Message Channel
- MediaNavToolkit: `/home/markretallack/buildhome/TMS/MediaNavToolkit/`
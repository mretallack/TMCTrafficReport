# MediaNav 4.1.0 `upgrade.lgu`: extraction and TMC runtime audit

## Safety and scope

This is a read-only extraction and static analysis of the user-supplied:

```text
/home/markretallack/Downloads/upgrade.lgu
SHA-256 435776c3305b344431ad294c25edcb3ca23c70d033d6e18464e9fc1c2bab3f3c
```

Its embedded `upgrade/Storage Card/System/Version_Info.txt` is exactly ASCII
`4.1.0`. An earlier attribution of this file to MediaNav Evolution v1 / 9.1.3
was incorrect and is superseded by this direct evidence. The separate ULC2
9.1.3 image is documented in `12-ULC2-9.1.3-FIRMWARE-TMC-AUDIT.md`.

This 4.1.0 image is a Windows CE/MIPS firmware image, not a candidate to
install on the current later Linux MediaNav. It is useful only as a reference
corpus for NNG map/TMC implementation research.

## LGU0 extraction

The file begins with `LGU0`, has a 1,024-byte wrapper header, and is not a GNU
tar archive. It was safely decoded using the reviewed public `lgu2dir` source
from `yosicovich/MediaNavMods`:

1. XOR all bytes after offset 1,024 with the LGU0 1,024-byte repeating key;
2. decode result is an encrypted ZIP (`69,791,720` bytes; SHA-256
   `a1e472a2078d2f36131bc6207754a7a23039be7cb0ca7f2c4be5c2a57090aed4`);
3. open with the LGU0 ZIP password from that reviewed source;
4. reject any member whose resolved path leaves the designated extract root.

Results:

```text
TrafficReport/tmp/medianav-evolution-v1-firmware/
├── lgu0-decoded.zip
└── files/                         # 1,163 files, 137,408,114 bytes
```

The original LGU was not modified.

## Recovered NNG runtime

The critical recovered files are:

```text
upgrade/Storage Card4/NNG/nngnavi.exe          10,375,192 B
upgrade/Storage Card4/NNG/data.zip             17,970,750 B
upgrade/Storage Card4/NNG/content/global_cfg/global_cfg.zip
                                                  7,865,637 B
```

`nngnavi.exe` is:

```text
PE32, Windows CE, MIPS R4000, 5 sections
SHA-256 df69ab57ca2d844bbc59ffaa13b0d1b92bf11d505e02584a10281399db664a1b
```

It contains the full old NNG TMC subsystem: `STATICTMC`, `TRAFFIC_MODULE`,
`IGPSTMC_EVENT_QUEUE`, `tmccache`, `show_ltn`, `show_tmc_location`,
`tmc_extract_all_segments`, and traffic/event/map-match logic.

## What the firmware contains

### Service selection metadata

The old `global_cfg.zip` contains the familiar metadata files:

```text
config/tmc_cc_ecc_sid_ltn.csv
config/tmc_info_database.ini
config/tmc_provider_list.dat
config/tmc_interim_list.csv
```

Its historical UK entries include:

```text
GBR; ECC=E1; CC=C; LTN=7;  Trafficmaster; SID=7
GBR; ECC=E1; CC=C; LTN=10; ITIS;          SID=10,11
```

This supports the known invariant that an LTN selects a location-list family.
It does not make the old ITIS LTN-10 mapping compatible with the current UK
INRIX LTN-10 map; map release and runtime generation still matter.

### Event/UI configuration

`data.zip` contains:

```text
config/tmccategory.dat
config/tmccode.dat
config/tmceventlist.csv
config/tmcevents*.{bin,dat}
config/tmcsettings.ini
config/tmcweight.dat
```

These are event-category/event-code, display, and weighting resources—not a
location-code-to-road list.

## What it does **not** contain

There are no extracted map or location-list assets:

```text
*.fbl  *.fpa  *.fda  *.fds  *.ftr  *.hnr  *.poi  *.tmc: 0
content/map/: 0 files
points/roads/offsets/LCL/location-dataset resources: 0
```

Therefore this firmware does **not** contain a national TMC LCD → road/link /
coordinate table to extract.

## Headless Ghidra findings

The MIPS PE was imported and analysed with the user-provided headless Ghidra
11.4.2 installation:

```text
TrafficReport/tmp/ghidra-v1-runtime/
TrafficReport/tmp/ghidra-v1-runtime.log
TrafficReport/tmp/ghidra-v1-unicode-maprefs.log
```

Relevant direct-reference results:

| Function | Evidence | Interpretation |
|---|---|---|
| `FUN_006300a8` | Opens `config/tmccategory.dat` under configured data location | TMC event-category loader, not LCD lookup |
| `FUN_00528830` | Reads config `cache_root` and `cache_name = tmccache` | TMC cache constructor/configuration |
| `FUN_004c90c0` | Reads `debug/show_tmc_location`, `debug/show_ltn`, and other debug flags | UI/debug settings, not resolver |
| `FUN_001b229c` | `STATICTMC` is one case in a licence/content dispatcher | Static-TMC licence gating |
| `FUN_0073fdd4` | Emits `<number_of_tmc_locations>` in `mapstat.xml` | Map statistics reporting, not table loading |
| `FUN_00890540` | Direct references to UTF-16 `map\\basemap.fbl` | Automatic 3D-test routine checking map selection/bounds; not an LCD resolver |

The map path had to be searched as UTF-16LE; an initial ASCII-only search did
not find it. This establishes that the engine knows FBL containers, but not
where the absent location table is stored internally.

## Consequence for the UK mapping effort

This is a successful recovery of an older, inspectable NNG runtime—not the
missing UK table.

It confirms the architectural split already seen in the current Linux update:

```text
firmware/runtime: TMC transport, service selection, event decoding, map API
map media:       national location association and road topology
```

The next high-value target remains the **actual current head-unit Linux
navigation runtime** that opens the 2026 UK `UnitedKingdom_osm.fbl`. A read-only
copy of its executable/shared libraries, or a dynamic trace of its FBL opens
and TMC-location lookup, can reveal the converted association required to map
current UK INRIX LTN-10 LCDs such as 17602 and 10024.

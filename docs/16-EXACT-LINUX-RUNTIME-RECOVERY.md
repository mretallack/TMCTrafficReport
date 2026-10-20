# Exact MediaNav 4 Linux firmware: current runtime recovery

## Exact firmware identity

The copied unit metadata reports:

```text
GNU/Linux 6.0.12.2.1166_r2
build 20240802072350
```

The downloaded matching image is:

```text
Firmware/x.0.12.2.1166_r2 - 20240802_Renault_Dacia_OS_Update.zip
SHA-256 b918dd3502de0411330217799fb79e9a0ad71d45e569ec3a452c6d2a67a3ba49
```

It contains one GNU-tar `upgrade.lgu`:

```text
Firmware/extracted-6.0.12.2.1166_r2/upgrade.lgu
SHA-256 8837fbe38c4da7989cc20852082f83134d007ecb149bae358686dd64bf768bdb
```

The outer firmware tar contains `HU/images/navibin.tar.gz`, i.MX6DL rootfs
images, boot/firmware packages, and signed/encrypted digest metadata. Source
archives are unmodified and the firmware must not be installed as part of this
analysis.

## Recovered runtime artifacts

`navibin.tar.gz` was extracted read-only at:

```text
Firmware/extracted-6.0.12.2.1166_r2/navibin/
```

Key files:

| Artifact | Identity / significance |
|---|---|
| `nngnavi` | exact current NNG navigation runtime; 32-bit ARM Linux ELF; SHA-256 `00c6b0992369f9ed34bf21de043d71007c44ddac94e5a6a11fcb2a49b62cc662` |
| `yellowtool/aoa2sock` | Linux ARM AOA bridge; has debug info; SHA-256 `87bd20057ecc5d2d33b477e06cf7810872b1f1a0a49171a1a662255520d3d341` |
| `yellowtool/src/` | readable YellowTool `.xs` service implementation |
| `xs/xs_modules/core/nftp.xs` | readable NFTP protocol implementation |
| `synctool/synctool` | current ARM Linux SyncTool |
| `synctool/ux/_phoneupdate.zip` | phone-update UI assets |

## Current ARM FBL/TMC resolver confirmation

The exact Linux `nngnavi` was imported into headless Ghidra as
`ARM:LE:32:v8:default`. Full-program analysis timed out after 1,200 seconds,
but the targeted TMC resolver and map lookup functions decompiled successfully.

The current Linux architecture matches ULC2 9.1.3:

```text
FUN_00b27edc  incoming TMC location processing
  -> FUN_00b21e7c  iterates country map contexts
     -> FUN_002ec954  map-object TMC lookup
        -> FUN_002ec898  selects CC/LTN descriptor from map+0x58 / count+0x5c
        -> FUN_002ec7a8  binary-searches descriptor uint16 LCD array at +0x14
                            and adds descriptor map-reference base at +0x0c
```

`FUN_002ec7a8` is direct evidence of the current lookup:

```text
search(sorted_uint16_array_at_descriptor+0x14, LCD)
return descriptor_base_at_+0x0c + matching_ordinal
```

The exact Linux runtime also retains these diagnostics:

```text
TMC Location not found in map. CC ... LTN ... LOCATIONID ...
TMCInfo validation failed: FBL(MAP) file for country not exist
country FBL file not found, TMC logic update GPS_COUNTRY_CHANGED_EVENT failed
```

This removes the earlier uncertainty over whether the 9.1.3 decoder model
applies to the installed 2025.09/2026.03 `SET v4.6.7.32` map generation. It
does. The remaining extraction problem is locating the current map object's
inner descriptor buffer/offset, not understanding the LCD lookup semantics.

## YellowTool read-only boundary

The exact stock `yellowtool/src/tool.xs` implements NFTP `GetFile`, but only
allows sanitized relative paths under:

```text
content/
license/
save/
```

It rejects arbitrary `/navi/...` paths, including direct `nngnavi` pulls. This
is a useful safety boundary. The firmware now supplies the runtime offline, so
read-only NFTP is needed only to pull installed map content, for example:

```text
content/map/UnitedKingdom.fbl
content/map/UnitedKingdom_osm.fbl
```

The latter may expose older HERE 2019.Q4 files named by
`save/preloads/mapmanager_A.prl` that SyncTool did not export as actual FBLs.

## Subsequent result

The backward trace has now been completed:

```text
FUN_002f2e84  exact current descriptor builder
FUN_002f01a8  current per-descriptor decoder
FUN_00316afc  section factory case 0x0c
FUN_0030f1b0  GEODBFILE parser and TMC relative-offset field
```

The current UK OSM TMC payload is at absolute FBL offset `0x5b6` and exports
4,529 CC=C/LTN=10 LCDs. See
`17-CURRENT-UK-TMC-INDEX-EXTRACTION.md` for extraction, validation, the
installed-HERE map mismatch, and road-reference next steps.

Ghidra evidence logs:

```text
Firmware/extracted-6.0.12.2.1166_r2/ghidra-nngnavi-tmc-refs.log
Firmware/extracted-6.0.12.2.1166_r2/ghidra-nngnavi-tmc-resolver-core.log
Firmware/extracted-6.0.12.2.1166_r2/ghidra-nngnavi-fbl-tmc-lookup.log
Firmware/extracted-6.0.12.2.1166_r2/ghidra-nngnavi-lcd-search.log
```

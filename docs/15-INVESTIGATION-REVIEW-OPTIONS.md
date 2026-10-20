# Investigation review and ranked next options

## Exact current platform and firmware match

The copied update itself identifies the target unit unambiguously:

```text
NaviSync/device_status.ini
os_name="GNU/Linux"
os_version="6.0.12.2.1166_r2"
os_build_version="20240802072350"
```

`synctool_log.txt` independently reports the same OS version and build. This
maps to the supplied catalogue entry:

```text
MediaNav 4 (Linux) / Media Display
x.0.12.2.1166_r2 — 2024-08-02_Renault_Dacia_OS_Update
```

This is the **only initial firmware image to download**. It is the exact current
firmware family/version and maximizes the chance that its Linux runtime parses
the installed 2025.09/2026.03 OSM FBL format. Download it for offline analysis
only; do not place it on update media or install it.

Optional second download, only if the exact image lacks a recoverable
YellowTool/phone-update package or its navigation payload is split elsewhere:

```text
MediaNav 4 x.0.10.2.1154_r6 — 2023-06-23_Renault_Dacia_OS_Update
```

This is the version family documented by the public YellowTool/NFTP research.
Do **not** download MN3 Evolution 2.0 or the MediaNav 1/2 Windows CE files for
this current-runtime objective; they are different hardware/software families.

## Current proven position

The target service remains:

```text
GBR, CC=C (12 decimal), ECC=E1, LTN=10, SID=10, INRIX
```

The 32 observed LCDs in `trafficevents_B.txt` are genuine event-cache inputs,
not a location table.

ULC2 9.1.3 Ghidra analysis proves that:

1. standalone `*.tmc` files are loaded through a distinct small-content path;
2. TMC validation requires a country map object explicitly labelled
   `FBL(MAP)` by runtime diagnostics;
3. the TMC resolver takes CC/LTN/LCD and searches that object;
4. its location index is reconstructed from an LSB-first packed bitstream with
   CC, LTN, count, map reference, and delta-coded LCD values.

One precision boundary remains: the map-container object is FBL-labelled and
architecturally co-resident with map sections, but its final backing-file open
has not been traced. Do not describe the exact current UK FBL file binding as
fully observed until that call is closed or the current runtime is traced.

## Re-audit results

### Current update payload

A magic-based scan of all 3,973 files in the copied update found no ELF or PE
runtime. The only actual top-level ZIP is `global_cfg.zip`; `FILECACHE` contains
an embedded ZIP stream. Apparent `MZ` byte pairs inside high-entropy map/image
files are random collisions, not PE executables.

No hidden `nngnavi`, `yellowtool.ipk`, `aoa2sock`, ELF shared library, or Linux
firmware component was found.

### Local firmware files

```text
Downloads/upgrade.lgu       = LGU0 4.1.0
Downloads/upgrade(1).lgu    = ULC2 9.1.3
TrafficReport/tmp/ulc2-9.1.3/upgrade.lgu
                            = byte-identical copy of the same 9.1.3 image
```

There is no additional Linux LGU in the searched home tree.

### Existing FBL calibration files

The locally extracted Netherlands and France FBLs are 2025.09 OSM `SET
v4.6.7.32`, not maps contemporaneous with ULC2 9.1.3. They therefore have the
same unresolved modern inner-directory problem and cannot independently
calibrate the old runtime's section offsets.

The 2025.09 and 2026.03 UK maps have nearly identical outer directory shapes,
but corresponding 256-byte block overlap is essentially zero outside 1.73% of
section 1. Revision-differencing is unlikely to isolate a compact table because
map conversion/compression changes avalanche through sections.

### Save/preload caches

No file named `tmccache` was present. `save/preloads/mapmanager_A.prl` is a
28-KB serialized map catalogue. It contains repeated metadata for older HERE
2019.Q4 map names—including `map/UnitedKingdom.fbl` and
`map/Netherlands.fbl`—but no current OSM inner offsets or national LCD array.

This metadata suggests the head unit may still contain actual HERE-era map
files under `/navi/content/map/`, even though SyncTool exported only `.stm`
shadows. A direct read-only head-unit pull could therefore recover both the
current Linux runtime and a useful older UK/HERE map.

## Ranked options

### 1. Read-only YellowTool/NFTP pull from the user's head unit — recommended

**Likelihood:** highest. **Value:** definitive current runtime plus installed
map files. **Head-unit modification:** none if the client is constrained to
`GET_FILE` only.

The public `goncalomb/mn4-tools` client already implements:

```text
ctrl-proto.py pull <remote> <local>
```

using YellowTool/NFTP `GET_FILE`. The official Android app's recovered
`connections.xs` independently confirms the same operation.

The **stock current YellowTool read allowlist is constrained** to relative
`content/`, `license/`, and `save/` paths. It can safely pull installed map
files, for example:

```text
content/map/UnitedKingdom.fbl
content/map/UnitedKingdom_osm.fbl
```

but it cannot pull `nngnavi` or arbitrary `/navi/...` system paths without
changing the service. That limitation is now acceptable: the exact current
Linux `nngnavi` has been recovered from the official matching firmware image.
An NFTP pull remains valuable for the installed HERE 2019.Q4 map files named
by `mapmanager_A.prl` and for any map file differing from the USB-exported
content.

The published hardware path uses a Raspberry Pi Zero 2 W in USB gadget mode
and a patched `g_serial` USB subclass to impersonate AOA. The existing Pi 3 B+
is not a suitable drop-in USB peripheral: its exposed USB-A ports are host-side
and the micro-USB connector is power-only. A Zero 2 W is the documented/tested
choice.

For safety, make a local pull-only fork that removes/disables `push` and
`delete`, uses a fixed remote-path allowlist, writes only to a local capture
directory, and hashes every received file. Keep the vehicle stationary and do
not invoke payload/backdoor scripts.

Alternative implementation: a small Android AOA client using the already
recovered NFTP protocol. This avoids the patched Pi kernel but requires building
and testing an Android application. Modifying/re-signing the official APK is
possible but less clean than a purpose-built pull-only client.

### 2. Obtain 6.0.10.2 through official Media Nav Toolbox

**Likelihood:** medium if the server still offers it to the unit; low if the
unit is already current. **Value:** complete Linux firmware and YellowTool
package. **Risk:** low if downloaded and never installed.

Use a genuine head-unit USB fingerprint and allow Toolbox to download an OS
update. Copy/hash the USB before installation. The referenced 2024 article
states its officially downloaded 6.0.10.2 `upgrade.lgu` is a GNU tar archive
and includes `yellowtool.ipk`, `aoa2sock`, and the Linux navigation stack.

The current Android app is not a substitute: it recognises OS-update content
type 26 but filters `x-firmware/os-update` from its normal package catalogue.

### 3. Continue static ULC2 9.1.3 Ghidra work

**Likelihood:** medium for format knowledge, low for current coordinates without
matching map media. **Value:** can close the remaining FBL file-binding gap and
recover more map-reference semantics.

Concrete targets:

- trace the country-map-manager vtable to its file-open/read implementation;
- determine exactly how map-object field `+0xBC` is populated;
- obtain a legally held 9.1.3-era/HERE FBL and validate the recovered decoder
  end-to-end against public Netherlands VILD.

This route requires no current firmware, but the local Netherlands/France FBLs
are modern 2025.09 files and are not the needed calibration generation.

### 4. Acquire installed HERE 2019.Q4 FBL via NFTP, even if runtime pull fails

This is really a subset of option 1 but has independent value. The preload cache
shows exact installed-era names. A matching older UK or Netherlands FBL may
work with the 9.1.3 decoder, allowing the inner section model to be calibrated
before porting it to the 2026 OSM map.

### 5. Ask the 6.0.10.2 article author/another owner for hashes or a lawful copy

Useful if official Toolbox will not re-offer the update. Verify any received
image as GNU tar, inspect it offline, and never install it merely because its
version string looks correct. No trustworthy public 6.0.10.2 download appeared
in the web search performed during this review.

## Low-value or rejected paths

- More raw `uint16`, varint, or arbitrary bit-offset scanning of the 2026 UK
  FBL: false-positive generator until the inner directory is known.
- Treating 26/32 matches as evidence: after 946 trials, the simplified null
  probability of at least one 26+ result is about 0.636.
- Revision block-diffing 2025.09 versus 2026.03: near-zero corresponding block
  reuse.
- `global_cfg`, FPA, HNR, FILECACHE, or 1.2-KB `.tmc` descriptors as a national
  LCD table: already contradicted by size, role, and runtime-path evidence.
- Running or installing the 4.1.0/9.1.3 Windows CE firmware on the current Linux
  unit: incompatible and unsafe.

## Recommended immediate sequence

1. Obtain a Pi Zero 2 W or choose the Android-client route.
2. Prepare and independently review a **pull-only** NFTP client.
3. Test it against the already extracted local YellowTool protocol fixtures or
   a simulated endpoint before connecting to the car.
4. Pull/hash `/navi/nngnavi` and the installed UK FBL path without writing or
   deleting anything.
5. Import the Linux runtime into Ghidra and locate the current equivalents of
   the proven ULC2 functions: country-map validation, descriptor builder,
   delta decoder, and LCD binary search.

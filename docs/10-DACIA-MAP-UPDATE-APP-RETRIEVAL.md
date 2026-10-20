# Dacia Map Update 1.8.13: package retrieval and transfer

## Scope and evidence

This is a static analysis of the locally supplied XAPK. Nothing in the APK was
executed, no account credentials were used, and no request was sent to the
Naviextras service.

Input:

```text
apk/Dacia+Map+Update_1.8.13_APKPure.xapk
SHA-256 d1bf080ccee42a9b90e5e58f19ae85975647e1c4f5ef71a665f18e25753037dc
package com.nng.pbmu.dacia, version 1.8.13 (version code 123)
```

The XAPK has a base APK and an ARM64 split.  The base APK bundles a 37.3 MB
`assets/resources.zip`, whose nested `resources/data.zip` contains the readable
XScript implementation. The app executes those scripts with the ARM64
`liblib_nng_sdk.so` runtime.

Key recovered local sources:

```text
apk/analysis/scripts/src/service/updateAPI.xs
apk/analysis/scripts/src/service/packages.xs
apk/analysis/scripts/src/service/datamodel.xs
apk/analysis/scripts/src/toolbox/download.xs
apk/analysis/scripts/src/toolbox/packages/packageModel.xs
apk/analysis/scripts/src/toolbox/packages/packageAndContent.xs
apk/analysis/scripts/src/toolbox/updater.xs
apk/analysis/scripts/src/toolbox/fileMapping.xs
apk/apktool/smali/com/nng/yellowbox/DownloadManagerModule.smali
```

## Conclusion

The app **does download update content from the Internet**. It does not contain
map packages or `upgrade.lgu` in the downloaded XAPK.

Its normal flow downloads individual, device-entitled content files (for
example `.fbl`, `.fpa`, `.poi`, `.tmc`, `global_cfg.zip`) from URLs returned by
the Naviextras backend. It validates each downloaded file with the server's MD5
then transfers it directly to the running head unit over USB Android Open
Accessory/NFTP; it does not produce the USB `NaviSync` package layout.

An `upgrade.lgu` could theoretically be returned as a device-entitled
firmware/OS content item, but this app version has no bundled LGU, no literal
LGU reference, and deliberately filters firmware OS-update packages from its
normal catalogue. A live answer therefore requires the server response for the
actual registered head unit, not further static inspection of this XAPK.

## Server discovery and selection flow

`yellowbox/src/service/updateAPI.xs` defines the fixed service base:

```text
https://stratus.naviextras.com/services/updateservice/1
```

All calls use JSON `POST`, `Content-type: application/json`, and the app's
versioned User-Agent. Relevant endpoints are:

| Endpoint | Purpose | Important request data |
|---|---|---|
| `/recognizeDeviceModel` | Identify a compatible Dacia/MediaNav model | device-model data extracted from the head unit |
| `/registerDevice` | Register the vehicle/head unit | `appcid`, brand/model, iGO version, IMEI, SWID, first-use time, optional VIN |
| `/uploadLicense` | Upload head-unit licence blobs | base64 licence data and names |
| `/getLicenses` | Retrieve licences for the registered device | `deviceName` |
| `/listRights` | Obtain entitled package/snapshot rights | `deviceName`, language |
| `/contentsBySnapshotCodes` | Obtain the actual files for entitled snapshots | `deviceName`, language, snapshot-code array |
| `/packages` | Shop/catalogue list | brand/model or registered device name, account token where applicable |

The package display flow is:

```text
head unit over AOA/NFTP
  -> identify device; read its content and licences
  -> recognizeDeviceModel
  -> registerDevice
  -> upload/get licences
  -> listRights
  -> each right supplies packageCode + snapshotCode
  -> contentsBySnapshotCodes(snapshotCode[])
  -> one Content record per downloadable file
```

The `Content` response schema in `datamodel.xs` contains the essential
per-file fields:

```text
contentTypeCode, contentTypeMime, downloadLocation,
fileName, filePath, size, md5, contentIds,
country, supplierName, versionString
```

`downloadLocation` is therefore not constructed from a public fixed content
URL in the app; it is returned by the service after device/rights selection.
This is the response to capture for an actual Dacia head unit.

## Internet download mechanics

`PackageDownloader.startDownloadingByUser()` in
`toolbox/packages/packageModel.xs` does this for every selected content item:

```xs
this.downloads.add(c.downloadLocation, c.localFileName,
                   #{expectedMd5: c.md5});
```

`PurchasedContent.localFileName` is:

```text
content/<filePath>/<fileName>
```

`toolbox/download.xs` delegates the transfer to `app://downloadManager`, stores
the URL/destination/expected MD5 in persistent `Storage("downloadList")`,
polls the job every second, and resumes incomplete Android download jobs after
an app restart. After the Android download reports success it calculates MD5
itself and marks the file failed unless it equals the service-provided MD5.

The Android binding is recovered as
`com.nng.yellowbox.DownloadManagerModule` in the base APK. Its `enqueue()`:

1. parses the supplied `downloadLocation` as an Android `Uri`;
2. constructs `android.app.DownloadManager.Request`;
3. calls `setDestinationInExternalFilesDir(context, null, destinationSubPath)`;
4. disables DownloadManager notifications;
5. applies `setAllowedOverMetered()` from the app's Wi-Fi-only preference;
6. enqueues with Android `DownloadManager`.

Thus the normal downloaded location on a phone is:

```text
/storage/emulated/0/Android/data/com.nng.pbmu.dacia/files/content/<filePath>/<fileName>
```

(The external-files root varies by device/user profile, but the package name and
relative `content/...` path are fixed by this build.) It is app-scoped external
storage, not the public Downloads directory.

## Head-unit transfer: separate from Internet download

The blog's `nftp.xs` observation is confirmed. `core/nftp.xs` and
`toolbox/connections.xs` implement an NNG file-transfer protocol over Android
Open Accessory. It is used only after package files are already on the phone.

`toolbox/updater.xs` sends each selected file as:

```text
local downloaded file
  -> NFTP PushFile
  -> <target>.new.part while streaming
  -> <target>.new after stream completion
  -> MD5 comparison on head unit
  -> rename to final target
```

On failure it retries; it does not replace the previous final file until the
checksum passes. It sends `PrepareForTransfer` before the operation and
`TransferFinished` afterward so YellowTool can stop/restart iGO as needed.

Built-in target mapping is content-only:

| Files/type | Head-unit target |
|---|---|
| `.fbl`, `.fpa`, `.hnr`, `.fda`, `.fds`, `.ftr`, `.fjv`, `.fjw`, `.fsp` | `content/map/` |
| `.poi` | `content/poi/` |
| `.spc` | `content/speedcam/` |
| `.tmc` | `content/tmc/` |
| language/global config/voice/dealer POI types | corresponding `content/...` directory |
| licences and `device.nng` | `license/` |

The unit can provide an additional dynamic file mapping through NFTP `queryInfo
@fileMapping`; that mapping is consulted after the built-in mapping.

## Firmware / `upgrade.lgu` finding

The suggested firmware hypothesis has a partial confirmation and an important
limitation.

`datamodel.xs` defines:

```xs
ContentTypeCodes.OsUpdate = 26
filteredMimes = Set.of("x-firmware/os-update")
```

`service/packages.xs` then removes every package having that MIME from the
normal catalogue, with the explicit developer comment:

```text
TODO: filtering the results here won't help when we need to process the OS update package
```

This proves the backend/application data model recognises OS-update packages,
but the normal app UI deliberately hides them and the implementation says their
processing is not complete.

Verified absence in this XAPK and all nested resource ZIPs:

```text
archive members named *.lgu, *.ipk, *upgrade*, or *firmware*: 0
literal "upgrade.lgu": 0
literal "yellowtool.ipk": 0
```

The built-in transfer map also has no `.lgu` rule and no `OsUpdate` type rule.
Therefore version 1.8.13 cannot be shown statically to download or install an
LGU through its regular map-update path. It would need both:

1. a relevant device entitlement from `/listRights` and
   `/contentsBySnapshotCodes`; and
2. either a target path supplied by the head unit's dynamic `fileMapping` or
   additional firmware-transfer code not present in this build.

## Best next acquisition, without guessing URLs

Do not probe the service with invented device names or copy account tokens into
scripts. The service selection is vehicle/rights dependent.

To determine whether this actual head unit is offered an OS update and recover
its authoritative URL, use a user-authorised phone/session connected to the
head unit and record only these JSON responses:

```text
POST /listRights
POST /contentsBySnapshotCodes
```

Preserve `contentTypeCode`, `contentTypeMime`, `fileName`, `filePath`, `size`,
`md5`, and `downloadLocation`; redact `userToken`, VIN, IMEI, SWID,
`deviceName`, licence bytes, and any signed URL query credentials before sharing
logs. An OS response should have type `26` or MIME `x-firmware/os-update` and
would identify the exact filename—possibly `upgrade.lgu`—rather than relying
on speculation.

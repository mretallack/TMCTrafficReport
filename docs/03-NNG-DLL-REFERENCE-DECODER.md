# NNG DLL reference decoder restored

## Purpose

`MediaNavToolkit/tools/maps/nng_decoder.py` can decode an FBL line through the
original NNG x86-32 routine (`FUN_1024A720`) under Unicorn. This is the
reference implementation for the FBL pattern grammar; the pure-Python decoder
is a useful fallback but must not be assumed correct for every production
record.

## Restored prerequisites

The local MediaNavToolkit checkout did not contain the DLL expected by the
decoder. On 2026-10-19 it was copied, with user approval, from the local
`flower` host:

```
flower:/home/mark/git/MediaNavToolbox/analysis/extracted/nngine.dll
  → MediaNavToolkit/analysis/extracted/nngine.dll
```

Verified artifact:

| Property | Value |
|---|---|
| Size | 3,348,480 bytes |
| Format | PE32 x86 Windows DLL, five sections |
| SHA-256 | `5dd1321ac2e24de3073ed570855502374cd7da18bf0feec785e43caf6ef7a611` |

The emulation dependency is deliberately isolated to the existing task-local
virtual environment:

```
TrafficReport/venv: unicorn==2.1.4
```

No system Python packages were installed.

## Use

Run Python from `TrafficReport/venv` and expose `MediaNavToolkit` as an import
root. Set `use_unicorn=True` explicitly, or set `NNG_DECODER_UNICORN=1` for
the decoder's automatic mode.

```python
from tools.maps.nng_decoder import decode_line

records = decode_line(raw_fbl_line, use_unicorn=True)
```

The DLL must remain at:

```
MediaNavToolkit/analysis/extracted/nngine.dll
```

## Production Netherlands validation

A sample of seven newline-delimited records from section 4 of
`TrafficReport/tmp/Netherlands_osm.fbl` was decoded through both paths.
Each entry is `record count / control-record count`.

| Section-4 line | Bytes | DLL reference | Pure Python | Result |
|---:|---:|---:|---:|---|
| 0 | 547 | 87 / 1 | 322 / 12 | Python over-emits after the DLL's 87-record prefix |
| 1 | 182 | 109 / 3 | 109 / 3 | exact |
| 10 | 326 | 142 / 6 | 142 / 6 | exact |
| 100 | 120 | 86 / 4 | 86 / 4 | exact |
| 1000 | 217 | 8 / 1 | 8 / 1 | exact |
| 10000 | 298 | 132 / 5 | 132 / 5 | exact |
| 22212 | 760 | 75 / 4 | 75 / 4 | exact |

The first 87 records of line 0 are identical in both paths. The DLL returns
normally after those records, so the reference result is treated as complete;
the pure parser is wrong for that input.

## Decoder hardening

`nng_decoder.py` previously returned whatever bytes happened to be in its
output buffer when Unicorn stopped. It now raises `RuntimeError` if it detects:

- its 50,000,000-instruction safety cap; or
- a Unicorn exception at an instruction pointer other than the intended return
  address; or
- a non-returning run that consumes its 60-second emulation allowance.

This prevents a genuinely incomplete emulation run from being mistaken for a
valid reference result. Normal DLL returns, including the 87-record first
Netherlands line, remain accepted.

## Consequence for VILD correlation

The DLL output is now the oracle for comparing or repairing
`nng_decoder_python.py`. The immediate next step is not a raw LCD byte search:
it is to run the reference decoder over selected Netherlands section-4 lines,
identify the record/control sequences that delimit coordinate/tagged groups,
and then correlate those groups against the public VILD point and line
geometries.

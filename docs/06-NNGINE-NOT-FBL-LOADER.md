# Correction: recovered `nngine.dll` is not a raw FBL map loader

## Question tested

Could the recovered Windows `nngine.dll` load a complete decrypted NNG `SET`/
`.fbl` container, dispatch its sub-sections, and build a road graph through:

```text
FUN_10243AE0 → FUN_1024A720 → FUN_10249210 → FUN_102460D0
```

If true, tracing this path on Vatican/Netherlands would have been a route to
map-link structures usable for TMC location correlation.

## Evidence

There is exactly **one** static caller of `FUN_10243AE0` in the recovered Ghidra
decompilation:

```text
FUN_101D31B0
```

That caller does not read an FBL file or SET header. It does this instead:

1. creates a stack buffer `local_4008[16384]`;
2. fills it through `FUN_101D46B0(...)`;
3. walks the buffer to its NUL terminator; and
4. calls:

```c
FUN_10243AE0(
    local_4008,
    strlen(local_4008),
    object_flags | 0x80000,
    status_out,
    consumed_out,
    parser_context
)
```

The parser therefore consumes a generated NUL-terminated text/program string,
including optional `(*...)` directives. It is not the component that accepts
raw binary FBL section bytes.

The production Netherlands FBL section 4 starts with binary bytes:

```text
56 de 5f 87 e2 01 84 d5 e9 4c 7b 79 ...
```

and has no such directive preamble. Directly passing it to `FUN_10243AE0` is
invalid by construction.

## What the experiment achieved

The Unicorn environment is nevertheless improved:

- restored the verified local `nngine.dll` analysis artifact;
- added a 64 MiB non-overlapping heap to `nng_emulator.py`;
- added minimal IAT stubs for `GetProcessHeap`, `HeapAlloc`, `HeapFree`, and
  `HeapReAlloc`;
- eliminated execution of the raw `KERNEL32!HeapAlloc` import thunk; and
- confirmed the raw-section call fails logically (`0x67` after 132 bytes), not
  because of missing heap/import support.

## Consequence

`nngine.dll` remains useful as a reference for the isolated pattern compiler
`FUN_1024A720`; it exposed a pure-Python decoder overrun on a real Netherlands
record. But it is **not evidence that the DLL loads the car's FBL map graph**.

Do not continue building an FBL-container harness around `FUN_10243AE0`.

## Correct next target

To learn the actual map-link/TMC association, obtain and analyze the
**head-unit navigation runtime** that opens `/navi/content/map/*.fbl` on the
MediaNav itself, rather than the Windows NaviExtras/Toolbox `nngine.dll`.

The practical non-licensed routes are:

1. read-only acquisition of the relevant head-unit navigation executable and
   its shared libraries from the user's own device, then find the FBL open/load
   path; or
2. dynamically trace the head-unit process while it loads a map, recording file
   reads and the in-memory structures that receive section data.

Either method must begin by identifying the actual `/navi` navigation binary;
the existing USB backup contains map files and shadow metadata, but not that
runtime binary.

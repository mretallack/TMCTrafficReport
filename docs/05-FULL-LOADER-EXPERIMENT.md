# Full-loader Unicorn experiment: boundary result

## Objective

Run the NNG DLL's apparent full section-loader (`FUN_10243AE0`) under Unicorn
on the production Netherlands FBL section 4, so that its graph-building path
(`FUN_10249210` → `FUN_102460D0`) can be captured for VILD correlation.

## Runtime support restored

The initial emulator had two concrete runtime deficiencies:

1. Its 8 MiB heap could not hold a production 5.66 MiB section plus output.
2. It did not patch the DLL import address table. The default allocator path
   reached the raw `KERNEL32!HeapAlloc` import thunk (`0x00309EC8`) and began
   executing import-name data as code.

`tools/maps/nng_emulator.py` now:

- uses a 64 MiB heap at `0x02000000`, away from the stop sentinel;
- patches only the loader-proven heap APIs:
  `GetProcessHeap`, `HeapAlloc`, `HeapFree`, and `HeapReAlloc`;
- provides a minimal bump allocator and correct stdcall return cleanup; and
- retains unpatched imports so future missing dependencies remain visible.

The restored DLL is verified as the PE32 x86 `nngine.dll` from the local
`flower` workspace (see `03-NNG-DLL-REFERENCE-DECODER.md`).

## Result

The full loader now executes over the complete **5,659,604-byte** Netherlands
section 4 without import-thunk execution or a Unicorn crash. It returns:

```text
EAX       = 0
error_out = 0x67
consumed  = 132 bytes
```

Instrumentation confirms that it enters `FUN_1024A720` once and never reaches:

```text
FUN_10245CA0  post-compile path
FUN_10249210  graph wrapper
FUN_102460D0  graph builder
```

## Why this is not a graph-loader invocation

`FUN_10243AE0` treats its input as directive-aware pattern/compiler text. It
only reaches the normal `FUN_1024A720` path when flag bit `0x80000` is clear.
The previously supplied `0x480080` flag selected its alternate path and caused
the observed `-8` class-token result.

With the loader-mode flag variants, it passes the binary section data to the
inner compiler but returns `0x67` at byte offset 132. The actual FBL section 4
begins with binary bytes:

```text
56 de 5f 87 e2 01 84 d5 e9 4c 7b 79 ...
```

and does not contain the loader's expected `(*...)` directives that establish
its parser configuration. Therefore this function is a generic parser/program
loader used by NNG internals, not a valid standalone API for raw production FBL
section data.

## Implication

This experiment removes a false route:

> Calling `FUN_10243AE0` directly with raw FBL section 4 will not recover the
> road graph, even with correct heap/import emulation.

The valid low-level primitive remains direct, per-LF-line execution of
`FUN_1024A720` with the explicitly constructed parser context in
`tools/maps/nng_decoder.py`.

To reach actual graph-level structures, the next reverse-engineering target
must be the **real map-file loader/caller that supplies section metadata and
compiler directives before it reaches `FUN_10243AE0`**, rather than
`FUN_10243AE0` itself. The recovered decompilation (`analysis/nngine_decompiled.c`)
can be used to identify that caller by tracing references to the FBL SET reader
and section-offset table.

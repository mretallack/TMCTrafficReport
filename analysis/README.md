# Analysis helpers

`ghidra-scripts/` contains the small headless Ghidra/Jython scripts used to
locate and decompile the exact MediaNav runtime functions documented under
`../docs/`.

The scripts are retained because they are lightweight and useful for repeating
or extending the analysis. Generated Ghidra projects (`*.gpr`, `*.rep/`),
decompiler logs, firmware executables, and map files are intentionally excluded
from Git because they are large, generated, or separately sourced.

Most scripts expect the local Ghidra project and binaries described in the
corresponding investigation document; they are not standalone decoders. The
reusable end-user extraction tools are under `../tools/`.

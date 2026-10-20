#@category MediaNav
# Print code references and compact decompilation for TMC/map-loader clue strings.
from ghidra.app.decompiler import DecompInterface
from jarray import array

TARGETS = [
    "map\\basemap.fbl",
    "<number_of_tmc_locations>%d</number_of_tmc_locations>",
    "tmccache",
    "show_ltn",
    "show_tmc_location",
    "STATICTMC",
    "/tmccategory.dat",
]

mem = currentProgram.getMemory()
fm = currentProgram.getFunctionManager()
start = mem.getMinAddress()
end = mem.getMaxAddress()
decomp = DecompInterface()
decomp.openProgram(currentProgram)
seen_functions = set()

for target in TARGETS:
    pat = array([ord(c) for c in target], 'b')
    addr = mem.findBytes(start, end, pat, None, True, monitor)
    print("\n=== TARGET: %s ===" % target)
    if addr is None:
        print("not found")
        continue
    matches = 0
    while addr is not None and matches < 20:
        matches += 1
        print("string @ %s" % addr)
        refs = currentProgram.getReferenceManager().getReferencesTo(addr)
        refcount = 0
        for ref in refs:
            refcount += 1
            f = fm.getFunctionContaining(ref.getFromAddress())
            fname = f.getName() if f else "<no function>"
            fentry = str(f.getEntryPoint()) if f else ""
            print("  ref from %s function=%s %s" % (ref.getFromAddress(), fname, fentry))
            if f and f.getEntryPoint() not in seen_functions:
                seen_functions.add(f.getEntryPoint())
                result = decomp.decompileFunction(f, 45, monitor)
                if result.decompileCompleted():
                    c = result.getDecompiledFunction().getC()
                    print("--- DECOMPILE %s ---\n%s\n--- END ---" % (f.getEntryPoint(), c[:12000]))
                else:
                    print("  decompile failed: %s" % result.getErrorMessage())
        if refcount == 0:
            print("  no direct references")
        addr = mem.findBytes(addr.add(1), end, pat, None, True, monitor)
print("\nDONE")

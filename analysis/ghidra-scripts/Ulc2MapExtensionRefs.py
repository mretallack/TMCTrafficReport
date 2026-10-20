#@category MediaNav
# Trace direct references to 9.1.3 Unicode map/TMC extension filters.
from ghidra.app.decompiler import DecompInterface
from jarray import array

TARGETS = ["*.fbl", "*.fpa", "*.hnr", "*.tmc"]
mem = currentProgram.getMemory()
fm = currentProgram.getFunctionManager()
start = mem.getMinAddress()
end = mem.getMaxAddress()
decomp = DecompInterface()
decomp.openProgram(currentProgram)
seen = set()

for target in TARGETS:
    pat = array([ord(c) for c in target.encode('utf-16le')], 'b')
    addr = mem.findBytes(start, end, pat, None, True, monitor)
    print("\n=== UTF16 EXTENSION: %s ===" % target)
    if addr is None:
        print("not found")
        continue
    found = 0
    while addr is not None and found < 30:
        found += 1
        print("string @ %s" % addr)
        refs = currentProgram.getReferenceManager().getReferencesTo(addr)
        nrefs = 0
        for ref in refs:
            nrefs += 1
            f = fm.getFunctionContaining(ref.getFromAddress())
            print("  ref from %s function=%s" % (ref.getFromAddress(), f.getEntryPoint() if f else '<none>'))
            if f and f.getEntryPoint() not in seen:
                seen.add(f.getEntryPoint())
                r = decomp.decompileFunction(f, 90, monitor)
                if r.decompileCompleted():
                    print("--- DECOMPILE %s ---\n%s\n--- END ---" % (f.getEntryPoint(), r.getDecompiledFunction().getC()[:24000]))
                else:
                    print("  decompile failed: %s" % r.getErrorMessage())
        if nrefs == 0:
            print("  no direct references")
        addr = mem.findBytes(addr.add(1), end, pat, None, True, monitor)
print("DONE")

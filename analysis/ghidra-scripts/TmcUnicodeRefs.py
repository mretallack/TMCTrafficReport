#@category MediaNav
# Follow UTF-16LE map-container path references in the recovered Windows CE NNG runtime.
from ghidra.app.decompiler import DecompInterface
from jarray import array

TARGETS = ["map\\basemap.fbl", "basemap.fbl"]
mem = currentProgram.getMemory()
fm = currentProgram.getFunctionManager()
start = mem.getMinAddress()
end = mem.getMaxAddress()
decomp = DecompInterface()
decomp.openProgram(currentProgram)
seen = set()

for target in TARGETS:
    raw = target.encode('utf-16le')
    pat = array([ord(c) for c in raw], 'b')
    addr = mem.findBytes(start, end, pat, None, True, monitor)
    print("\n=== UTF16 TARGET: %s ===" % target)
    if addr is None:
        print("not found")
        continue
    count = 0
    while addr is not None and count < 20:
        count += 1
        print("string @ %s" % addr)
        refs = currentProgram.getReferenceManager().getReferencesTo(addr)
        nrefs = 0
        for ref in refs:
            nrefs += 1
            f = fm.getFunctionContaining(ref.getFromAddress())
            print("  ref from %s function=%s" % (ref.getFromAddress(), f.getEntryPoint() if f else '<none>'))
            if f and f.getEntryPoint() not in seen:
                seen.add(f.getEntryPoint())
                r = decomp.decompileFunction(f, 60, monitor)
                if r.decompileCompleted():
                    print("--- DECOMPILE %s ---\n%s\n--- END ---" % (f.getEntryPoint(), r.getDecompiledFunction().getC()[:18000]))
                else:
                    print("  decompile failed: %s" % r.getErrorMessage())
        if nrefs == 0:
            print("  no direct references")
        addr = mem.findBytes(addr.add(1), end, pat, None, True, monitor)
print("DONE")

#@category MediaNav
# Decompile the map-object methods directly invoked by the TMC LCD resolver.
from ghidra.app.decompiler import DecompInterface

TARGETS = [0x0069a47c, 0x0069a3ac, 0x0064177c]
fm=currentProgram.getFunctionManager(); decomp=DecompInterface(); decomp.openProgram(currentProgram)
for a in TARGETS:
 addr=toAddr(a); f=fm.getFunctionAt(addr)
 print("\n=== FUNCTION %s ===" % addr)
 if f is None: print("not a function"); continue
 print("name=%s body=%s" % (f.getName(),f.getBody()))
 r=decomp.decompileFunction(f,240,monitor)
 if r.decompileCompleted(): print(r.getDecompiledFunction().getC()[:80000])
 else: print("decompile failed: %s" % r.getErrorMessage())
 print("=== CALLERS ===")
 for ref in currentProgram.getReferenceManager().getReferencesTo(addr):
  cf=fm.getFunctionContaining(ref.getFromAddress())
  print("%s from %s" % (ref.getFromAddress(),cf.getEntryPoint() if cf else '<none>'))

#@category MediaNav
# Decompile the ULC2 immediate TMC LCD-to-map resolver and helpers identified from the missing-location path.
from ghidra.app.decompiler import DecompInterface

TARGETS = [0x0082555c, 0x00829e18, 0x00829ed0, 0x008504c8]
fm=currentProgram.getFunctionManager()
decomp=DecompInterface(); decomp.openProgram(currentProgram)
for a in TARGETS:
 addr=toAddr(a); f=fm.getFunctionAt(addr)
 print("\n=== FUNCTION %s ===" % addr)
 if f is None:
  print("not a function"); continue
 print("name=%s body=%s" % (f.getName(), f.getBody()))
 r=decomp.decompileFunction(f,180,monitor)
 if r.decompileCompleted(): print(r.getDecompiledFunction().getC()[:60000])
 else: print("decompile failed: %s" % r.getErrorMessage())
 print("=== CALLERS ===")
 for ref in currentProgram.getReferenceManager().getReferencesTo(addr):
  cf=fm.getFunctionContaining(ref.getFromAddress())
  print("%s from %s" % (ref.getFromAddress(), cf.getEntryPoint() if cf else '<none>'))

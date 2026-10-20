#@category MediaNav
# Decompile the map-section buffer accessor used immediately before the type-12 TMC index decoder.
from ghidra.app.decompiler import DecompInterface
fm=currentProgram.getFunctionManager(); d=DecompInterface(); d.openProgram(currentProgram)
for a in [0x006a4234,0x0065ee80]:
 f=fm.getFunctionAt(toAddr(a)); print("\n=== FUNCTION %08x ===" % a)
 if not f: print("not a function"); continue
 print("body=%s" % f.getBody())
 r=d.decompileFunction(f,300,monitor)
 if r.decompileCompleted(): print(r.getDecompiledFunction().getC()[:120000])
 else: print(r.getErrorMessage())
 print("=== CALLERS ===")
 for ref in currentProgram.getReferenceManager().getReferencesTo(toAddr(a)):
  cf=fm.getFunctionContaining(ref.getFromAddress())
  print("%s from %s" % (ref.getFromAddress(),cf.getEntryPoint() if cf else '<none>'))

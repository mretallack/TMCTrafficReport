#@category MediaNav
# Decode the per-descriptor parser used by FUN_00699e1c to build TMC map indexes.
from ghidra.app.decompiler import DecompInterface
fm=currentProgram.getFunctionManager(); d=DecompInterface(); d.openProgram(currentProgram)
for a in [0x00699c5c,0x001e994c]:
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

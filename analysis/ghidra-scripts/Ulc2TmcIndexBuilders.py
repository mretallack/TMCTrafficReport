#@category MediaNav
# Examine likely constructors/parsers adjacent to the TMC map-index comparator.
from ghidra.app.decompiler import DecompInterface
TARGETS=[0x00698e50,0x00699e1c,0x0069aad4]
fm=currentProgram.getFunctionManager(); d=DecompInterface(); d.openProgram(currentProgram)
for a in TARGETS:
 f=fm.getFunctionAt(toAddr(a)); print("\n=== FUNCTION %08x ===" % a)
 if not f: print("not a function"); continue
 print("body=%s" % f.getBody())
 r=d.decompileFunction(f,300,monitor)
 if r.decompileCompleted(): print(r.getDecompiledFunction().getC()[:120000])
 else: print(r.getErrorMessage())

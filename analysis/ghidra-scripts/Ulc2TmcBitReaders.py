#@category MediaNav
# Decompile helpers used by the TMC descriptor decoder: variable integer and single-bit readers.
from ghidra.app.decompiler import DecompInterface
fm=currentProgram.getFunctionManager(); d=DecompInterface(); d.openProgram(currentProgram)
for a in [0x0036d864,0x001e98fc,0x001e994c]:
 f=fm.getFunctionAt(toAddr(a)); print("\n=== FUNCTION %08x ===" % a)
 if not f: print("not a function"); continue
 print("body=%s" % f.getBody())
 r=d.decompileFunction(f,180,monitor)
 if r.decompileCompleted(): print(r.getDecompiledFunction().getC()[:90000])
 else: print(r.getErrorMessage())

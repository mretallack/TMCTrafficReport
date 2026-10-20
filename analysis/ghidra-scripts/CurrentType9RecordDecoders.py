#@category MediaNav
from ghidra.app.decompiler import DecompInterface
fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram)
for a in [0x002eaf94,0x002eb0a4]:
 f=fm.getFunctionAt(toAddr(a));print('\n=== FUNCTION %08x ==='%a)
 if f:
  r=d.decompileFunction(f,900,monitor);print(r.getDecompiledFunction().getC()[:300000] if r.decompileCompleted() else r.getErrorMessage())

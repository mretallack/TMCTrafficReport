#@category MediaNav
from ghidra.app.decompiler import DecompInterface
fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram)
for a in [0x0034a9bc,0x002ea6cc]:
 f=fm.getFunctionAt(toAddr(a));print('\n=== FUNCTION %08x ==='%a)
 if f:
  r=d.decompileFunction(f,700,monitor);print(r.getDecompiledFunction().getC()[:260000] if r.decompileCompleted() else r.getErrorMessage())

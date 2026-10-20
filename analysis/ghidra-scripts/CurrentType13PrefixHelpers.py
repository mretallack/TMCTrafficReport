#@category MediaNav
from ghidra.app.decompiler import DecompInterface
d=DecompInterface();d.openProgram(currentProgram);fm=currentProgram.getFunctionManager()
for a in [0x0034acc8,0x002ea2e0,0x0034af38,0x0034b690,0x0034afdc,0x002e9ee4]:
 f=fm.getFunctionAt(toAddr(a));print('\n=== %08x ==='%a)
 if f:
  r=d.decompileFunction(f,600,monitor);print(r.getDecompiledFunction().getC() if r.decompileCompleted() else r.getErrorMessage())

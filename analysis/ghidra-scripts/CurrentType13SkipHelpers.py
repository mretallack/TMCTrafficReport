#@category MediaNav
from ghidra.app.decompiler import DecompInterface
d=DecompInterface();d.openProgram(currentProgram);fm=currentProgram.getFunctionManager()
for a in [0x0034ae00,0x002eaa6c,0x0034b558,0x002ea5f8]:
 f=fm.getFunctionAt(toAddr(a));print('\n=== %08x ==='%a)
 if f:
  r=d.decompileFunction(f,500,monitor);print(r.getDecompiledFunction().getC() if r.decompileCompleted() else r.getErrorMessage())

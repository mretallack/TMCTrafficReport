#@category MediaNav
from ghidra.app.decompiler import DecompInterface
d=DecompInterface();d.openProgram(currentProgram);fm=currentProgram.getFunctionManager()
for a in [0x000ccd78,0x000cae20,0x00b80f98]:
 f=fm.getFunctionAt(toAddr(a));print('\n=== %08x ==='%a)
 if f:
  r=d.decompileFunction(f,300,monitor);print(r.getDecompiledFunction().getC() if r.decompileCompleted() else r.getErrorMessage())

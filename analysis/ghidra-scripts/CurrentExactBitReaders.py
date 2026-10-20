#@category MediaNav
from ghidra.app.decompiler import DecompInterface
fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram)
for a in [0x0009070c,0x000b02c8,0x00135c5c,0x000d6d80]:
 f=fm.getFunctionAt(toAddr(a));print('\n=== FUNCTION %08x ==='%a)
 if f:
  r=d.decompileFunction(f,500,monitor);print(r.getDecompiledFunction().getC()[:180000] if r.decompileCompleted() else r.getErrorMessage())

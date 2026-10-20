#@category MediaNav
from ghidra.app.decompiler import DecompInterface
d=DecompInterface();d.openProgram(currentProgram);fm=currentProgram.getFunctionManager()
for a in [0x0033d254,0x0033d308]:
 f=fm.getFunctionAt(toAddr(a));print('\n=== %08x ==='%a);r=d.decompileFunction(f,400,monitor);print(r.getDecompiledFunction().getC() if r.decompileCompleted() else r.getErrorMessage())

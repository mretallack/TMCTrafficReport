#@category MediaNav
from ghidra.app.decompiler import DecompInterface
d=DecompInterface();d.openProgram(currentProgram);fm=currentProgram.getFunctionManager()
for a in [0x00349624,0x002e2e34]:
 f=fm.getFunctionAt(toAddr(a));print('\n=== %08x ==='%a);r=d.decompileFunction(f,500,monitor);print(r.getDecompiledFunction().getC() if r.decompileCompleted() else r.getErrorMessage())

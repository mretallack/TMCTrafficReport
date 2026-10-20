#@category MediaNav
from ghidra.app.decompiler import DecompInterface
mem=currentProgram.getMemory();fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram)
for a in [0x002f1128]:
 f=fm.getFunctionAt(toAddr(a));print('=== %08x ==='%a);r=d.decompileFunction(f,400,monitor);print(r.getDecompiledFunction().getC() if r.decompileCompleted() else r.getErrorMessage())

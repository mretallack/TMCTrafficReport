#@category MediaNav
from ghidra.app.decompiler import DecompInterface
d=DecompInterface();d.openProgram(currentProgram);fm=currentProgram.getFunctionManager()
for a in [0x0033ca18,0x002e6fb4]:
 f=fm.getFunctionAt(toAddr(a));print('\n=== %08x ==='%a);r=d.decompileFunction(f,300,monitor);print(r.getDecompiledFunction().getC() if r.decompileCompleted() else r.getErrorMessage())

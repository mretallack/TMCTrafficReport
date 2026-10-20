#@category MediaNav
from ghidra.app.decompiler import DecompInterface
d=DecompInterface();d.openProgram(currentProgram);fm=currentProgram.getFunctionManager();a=0x0033ca90
f=fm.getFunctionAt(toAddr(a));print('=== %08x ==='%a);r=d.decompileFunction(f,400,monitor);print(r.getDecompiledFunction().getC() if r.decompileCompleted() else r.getErrorMessage())

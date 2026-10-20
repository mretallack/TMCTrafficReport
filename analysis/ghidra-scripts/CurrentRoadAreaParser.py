#@category MediaNav
from ghidra.app.decompiler import DecompInterface
d=DecompInterface();d.openProgram(currentProgram);fm=currentProgram.getFunctionManager();a=0x0030ae88
f=fm.getFunctionAt(toAddr(a));print('=== %08x ==='%a);r=d.decompileFunction(f,1200,monitor);print(r.getDecompiledFunction().getC() if r.decompileCompleted() else r.getErrorMessage())

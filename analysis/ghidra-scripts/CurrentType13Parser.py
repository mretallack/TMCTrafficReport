#@category MediaNav
from ghidra.app.decompiler import DecompInterface
d=DecompInterface();d.openProgram(currentProgram);f=currentProgram.getFunctionManager().getFunctionAt(toAddr(0x003178a0));print('=== 003178a0 ===');r=d.decompileFunction(f,900,monitor);print(r.getDecompiledFunction().getC() if r.decompileCompleted() else r.getErrorMessage())

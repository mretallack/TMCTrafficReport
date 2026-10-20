#@category MediaNav
from ghidra.app.decompiler import DecompInterface
fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram)
a=0x000906dc;f=fm.getFunctionAt(toAddr(a));print('=== FUNCTION %08x ==='%a)
if f:
 r=d.decompileFunction(f,400,monitor);print(r.getDecompiledFunction().getC()[:160000] if r.decompileCompleted() else r.getErrorMessage())

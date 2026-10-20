#@category MediaNav
from ghidra.app.decompiler import DecompInterface
fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram)
for a in [0x0033caa4,0x0033ca90,0x0033cad8,0x0033ca64]:
 f=fm.getFunctionAt(toAddr(a));print('\n=== FUNCTION %08x ==='%a)
 if f:
  r=d.decompileFunction(f,500,monitor);print(r.getDecompiledFunction().getC()[:180000] if r.decompileCompleted() else r.getErrorMessage())

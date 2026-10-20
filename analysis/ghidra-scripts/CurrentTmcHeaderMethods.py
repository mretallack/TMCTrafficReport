#@category MediaNav
from ghidra.app.decompiler import DecompInterface
fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram)
for f in fm.getFunctions(toAddr(0x002ec720),True):
 if f.getEntryPoint().compareTo(toAddr(0x002ecaac))>=0:break
 print('\n=== FUNCTION %s size=%d ==='%(f.getEntryPoint(),f.getBody().getNumAddresses()))
 r=d.decompileFunction(f,300,monitor);print(r.getDecompiledFunction().getC()[:120000] if r.decompileCompleted() else r.getErrorMessage())

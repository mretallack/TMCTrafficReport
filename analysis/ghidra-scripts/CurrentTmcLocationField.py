#@category MediaNav
from ghidra.app.decompiler import DecompInterface
fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram)
a=0x002ec6ec;f=fm.getFunctionAt(toAddr(a));print('=== FUNCTION %08x ==='%a)
if f:
 r=d.decompileFunction(f,500,monitor);print(r.getDecompiledFunction().getC()[:200000] if r.decompileCompleted() else r.getErrorMessage())
 print('=== CALLERS ===')
 for ref in currentProgram.getReferenceManager().getReferencesTo(toAddr(a)):
  cf=fm.getFunctionContaining(ref.getFromAddress());print('%s from %s'%(ref.getFromAddress(),cf.getEntryPoint() if cf else '<none>'))

#@category MediaNav
# Decompile current ARM sole caller of TMC descriptor builder and enumerate its callers.
from ghidra.app.decompiler import DecompInterface
fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram)
a=0x00316afc;f=fm.getFunctionAt(toAddr(a));print('=== FUNCTION %08x ==='%a)
if f:
 print('body=%s'%f.getBody());r=d.decompileFunction(f,600,monitor)
 if r.decompileCompleted():print(r.getDecompiledFunction().getC()[:240000])
 else:print(r.getErrorMessage())
 print('=== CALLERS ===')
 for ref in currentProgram.getReferenceManager().getReferencesTo(toAddr(a)):
  cf=fm.getFunctionContaining(ref.getFromAddress());print('%s from %s'%(ref.getFromAddress(),cf.getEntryPoint() if cf else '<none>'))
else:print('not a function')

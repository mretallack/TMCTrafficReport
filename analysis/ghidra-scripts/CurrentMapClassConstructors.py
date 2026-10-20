#@category MediaNav
from ghidra.app.decompiler import DecompInterface
fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram)
for a in [0x0033ad38,0x0033b000,0x002fa504,0x002fa52c]:
 f=fm.getFunctionAt(toAddr(a));print('\n=== FUNCTION %08x ==='%a)
 if not f:print('not a function');continue
 r=d.decompileFunction(f,600,monitor)
 print(r.getDecompiledFunction().getC()[:220000] if r.decompileCompleted() else r.getErrorMessage())
 print('=== CALLERS ===')
 for ref in currentProgram.getReferenceManager().getReferencesTo(toAddr(a)):
  cf=fm.getFunctionContaining(ref.getFromAddress());print('%s from %s'%(ref.getFromAddress(),cf.getEntryPoint() if cf else '<none>'))

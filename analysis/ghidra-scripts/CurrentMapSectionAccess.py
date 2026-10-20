#@category MediaNav
# Decompile current section buffer accessor and sole caller of section factory.
from ghidra.app.decompiler import DecompInterface
fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram)
for a in [0x002ee300,0x002edad8,0x0033a384]:
 f=fm.getFunctionAt(toAddr(a));print('\n=== FUNCTION %08x ==='%a)
 if not f:print('not a function');continue
 print('body=%s'%f.getBody());r=d.decompileFunction(f,600,monitor)
 if r.decompileCompleted():print(r.getDecompiledFunction().getC()[:240000])
 else:print(r.getErrorMessage())
 print('=== CALLERS ===')
 for ref in currentProgram.getReferenceManager().getReferencesTo(toAddr(a)):
  cf=fm.getFunctionContaining(ref.getFromAddress());print('%s from %s'%(ref.getFromAddress(),cf.getEntryPoint() if cf else '<none>'))

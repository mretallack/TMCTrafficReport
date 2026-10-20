#@category MediaNav
# Decompile exact current TMC descriptor builder/decoder and enumerate callers.
from ghidra.app.decompiler import DecompInterface
fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram)
for a in [0x002f2e84,0x002f01a8]:
 f=fm.getFunctionAt(toAddr(a));print('\n=== FUNCTION %08x ==='%a)
 if not f:print('not a function');continue
 print('body=%s'%f.getBody());r=d.decompileFunction(f,420,monitor)
 if r.decompileCompleted():print(r.getDecompiledFunction().getC()[:180000])
 else:print(r.getErrorMessage())
 print('=== CALLERS ===')
 for ref in currentProgram.getReferenceManager().getReferencesTo(toAddr(a)):
  cf=fm.getFunctionContaining(ref.getFromAddress());print('%s from %s'%(ref.getFromAddress(),cf.getEntryPoint() if cf else '<none>'))

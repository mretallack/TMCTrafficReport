#@category MediaNav
# Decompile current ARM LCD index search helper called by the current map-object TMC lookup.
from ghidra.app.decompiler import DecompInterface
fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram)
a=0x002ec7a8;f=fm.getFunctionAt(toAddr(a));print('=== FUNCTION %08x ==='%a)
if f:
 print('body=%s'%f.getBody());r=d.decompileFunction(f,240,monitor)
 if r.decompileCompleted():print(r.getDecompiledFunction().getC()[:100000])
 else:print(r.getErrorMessage())
 print('=== CALLERS ===')
 for ref in currentProgram.getReferenceManager().getReferencesTo(toAddr(a)):
  cf=fm.getFunctionContaining(ref.getFromAddress());print('%s from %s'%(ref.getFromAddress(),cf.getEntryPoint() if cf else '<none>'))
else:print('not a function')

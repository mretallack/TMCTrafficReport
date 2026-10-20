#@category MediaNav
from ghidra.app.decompiler import DecompInterface
fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram)
for a in [0x0030efec,0x0030f1b0]:
 f=fm.getFunctionAt(toAddr(a));print('\n=== FUNCTION %08x ==='%a)
 if not f:continue
 r=d.decompileFunction(f,1200,monitor);print(r.getDecompiledFunction().getC()[:400000] if r.decompileCompleted() else r.getErrorMessage())
 print('=== CALLERS ===')
 for ref in currentProgram.getReferenceManager().getReferencesTo(toAddr(a)):
  cf=fm.getFunctionContaining(ref.getFromAddress());print('%s from %s'%(ref.getFromAddress(),cf.getEntryPoint() if cf else '<none>'))

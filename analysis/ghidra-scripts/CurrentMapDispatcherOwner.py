#@category MediaNav
# Follow current map section dispatcher upward through wrappers to the parsed file object owner.
from ghidra.app.decompiler import DecompInterface
fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram)
TARGETS=[0x0033a5c4]
seen=set()
for a in TARGETS:
 f=fm.getFunctionAt(toAddr(a));print('\n=== FUNCTION %08x ==='%a)
 if not f:print('not a function');continue
 r=d.decompileFunction(f,600,monitor)
 if r.decompileCompleted():print(r.getDecompiledFunction().getC()[:220000])
 else:print(r.getErrorMessage())
 print('=== CALLERS ===')
 for ref in currentProgram.getReferenceManager().getReferencesTo(toAddr(a)):
  cf=fm.getFunctionContaining(ref.getFromAddress());print('%s from %s'%(ref.getFromAddress(),cf.getEntryPoint() if cf else '<none>'))

#@category MediaNav
# Trace callers of current GEODBFILE main road-record parser FUN_0030ae88.
from ghidra.app.decompiler import DecompInterface
fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram)
a=toAddr(0x0030ae88);print('TARGET',a)
seen=set()
for ref in currentProgram.getReferenceManager().getReferencesTo(a):
 f=fm.getFunctionContaining(ref.getFromAddress());print('REF',ref.getFromAddress(),'FUNC',f.getEntryPoint() if f else '<none>')
 if f and f.getEntryPoint() not in seen:
  seen.add(f.getEntryPoint());r=d.decompileFunction(f,900,monitor)
  if r.decompileCompleted():print('--- DECOMPILE %s ---\n%s\n--- END ---'%(f.getEntryPoint(),r.getDecompiledFunction().getC()[:300000]))

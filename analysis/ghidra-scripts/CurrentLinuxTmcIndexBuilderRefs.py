#@category MediaNav
# Locate current ARM TMC descriptor-index builder by its license-distributor symbol.
from ghidra.app.decompiler import DecompInterface
from jarray import array
TARGETS=['ILICENSE_DISTRIBUTOR_TMC::NAME()','TMCEVENTTABLE::ClassifyEvent #2_2 (%i)']
mem=currentProgram.getMemory();fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram)
for target in TARGETS:
 addr=mem.findBytes(mem.getMinAddress(),mem.getMaxAddress(),array([ord(c) for c in target],'b'),None,True,monitor)
 print('\n=== TARGET: %s ==='%target)
 while addr is not None:
  print('string @',addr)
  for ref in currentProgram.getReferenceManager().getReferencesTo(addr):
   f=fm.getFunctionContaining(ref.getFromAddress());print('REF',ref.getFromAddress(),'FUNC',f.getEntryPoint() if f else '<none>')
   if f:
    r=d.decompileFunction(f,360,monitor)
    if r.decompileCompleted():print('--- DECOMPILE %s ---\n%s\n--- END ---'%(f.getEntryPoint(),r.getDecompiledFunction().getC()[:140000]))
    else:print(r.getErrorMessage())
  addr=mem.findBytes(addr.add(1),mem.getMaxAddress(),array([ord(c) for c in target],'b'),None,True,monitor)

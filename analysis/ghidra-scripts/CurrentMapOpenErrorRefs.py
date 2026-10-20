#@category MediaNav
from ghidra.app.decompiler import DecompInterface
from jarray import array
TARGETS=['INVALIDMAPFILE','content.map.map_file_open_error']
mem=currentProgram.getMemory();fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram);seen=set()
for t in TARGETS:
 p=array([ord(c) for c in t],'b');a=mem.findBytes(mem.getMinAddress(),mem.getMaxAddress(),p,None,True,monitor);print('\n=== TARGET',t,'===')
 while a is not None:
  print('string',a)
  for ref in currentProgram.getReferenceManager().getReferencesTo(a):
   f=fm.getFunctionContaining(ref.getFromAddress());print('REF',ref.getFromAddress(),'FUNC',f.getEntryPoint() if f else '<none>')
   if f and f.getEntryPoint() not in seen:
    seen.add(f.getEntryPoint());r=d.decompileFunction(f,600,monitor)
    print('--- DECOMPILE %s ---\n%s\n--- END ---'%(f.getEntryPoint(),r.getDecompiledFunction().getC()[:200000]) if r.decompileCompleted() else r.getErrorMessage())
  a=mem.findBytes(a.add(1),mem.getMaxAddress(),p,None,True,monitor)

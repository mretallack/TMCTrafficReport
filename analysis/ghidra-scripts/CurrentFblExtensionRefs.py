#@category MediaNav
# Trace current UTF-16 FBL file enumeration/filter into GEODBFILE creation.
from ghidra.app.decompiler import DecompInterface
from jarray import array
mem=currentProgram.getMemory();fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram)
for t in ['*.fbl','*.fpa','*.hnr','*.tmc']:
 p=array([ord(c) for c in t.encode('utf-16le')],'b');a=mem.findBytes(mem.getMinAddress(),mem.getMaxAddress(),p,None,True,monitor);print('\n=== TARGET %s ==='%t)
 while a is not None:
  print('string',a)
  for ref in currentProgram.getReferenceManager().getReferencesTo(a):
   f=fm.getFunctionContaining(ref.getFromAddress());print('REF',ref.getFromAddress(),'FUNC',f.getEntryPoint() if f else '<none>')
   if f:
    r=d.decompileFunction(f,700,monitor)
    if r.decompileCompleted():print('--- DECOMPILE %s ---\n%s\n--- END ---'%(f.getEntryPoint(),r.getDecompiledFunction().getC()[:240000]))
  a=mem.findBytes(a.add(1),mem.getMaxAddress(),p,None,True,monitor)

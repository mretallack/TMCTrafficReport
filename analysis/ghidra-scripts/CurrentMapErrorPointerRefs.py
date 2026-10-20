#@category MediaNav
# Find pointer objects referring to map-open diagnostic strings, then references to those objects.
from jarray import array
mem=currentProgram.getMemory();rm=currentProgram.getReferenceManager();fm=currentProgram.getFunctionManager()
for val in [0x00bdefd2,0x00c1cd88]:
 print('\n=== TARGET PTR %08x ==='%val)
 raw=[x if x<128 else x-256 for x in [val&255,(val>>8)&255,(val>>16)&255,(val>>24)&255]]
 pat=array(raw,'b');a=mem.findBytes(mem.getMinAddress(),mem.getMaxAddress(),pat,None,True,monitor);n=0
 while a is not None and n<100:
  n+=1;print('pointer bytes @',a)
  for r in rm.getReferencesTo(a):
   f=fm.getFunctionContaining(r.getFromAddress());print(' REF',r.getFromAddress(),'FUNC',f.getEntryPoint() if f else '<none>')
  a=mem.findBytes(a.add(1),mem.getMaxAddress(),pat,None,True,monitor)
 print('count',n)

#@category MediaNav
from jarray import array
mem=currentProgram.getMemory();rm=currentProgram.getReferenceManager();fm=currentProgram.getFunctionManager()
for val,name in [(0xc09980,'GEODBFILE_TI'),(0xc099a0,'GEODB_RESOURCEFILE_TI'),(0xbe4284,'GEODBOBJ_TI'),(0xbe42c8,'GEODBOBJ_BASED_TI')]:
 raw=[x if x<128 else x-256 for x in [val&255,(val>>8)&255,(val>>16)&255,(val>>24)&255]];pat=array(raw,'b')
 print('\n===',name,hex(val),'===');a=mem.findBytes(mem.getMinAddress(),mem.getMaxAddress(),pat,None,True,monitor);n=0
 while a is not None and n<100:
  n+=1;print('PTR_AT',a)
  for r in rm.getReferencesTo(a):
   f=fm.getFunctionContaining(r.getFromAddress());print(' REF',r.getFromAddress(),'FUNC',f.getEntryPoint() if f else '<none>')
  a=mem.findBytes(a.add(1),mem.getMaxAddress(),pat,None,True,monitor)
 print('COUNT',n)

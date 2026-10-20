#@category MediaNav
# Find code/data references to PHONEME_FILEOBJECT vtable address points.
mem=currentProgram.getMemory();rm=currentProgram.getReferenceManager();fm=currentProgram.getFunctionManager()
for val in range(0x00c09100,0x00c09278,4):
 refs=list(rm.getReferencesTo(toAddr(val)))
 if refs:
  print('\nTARGET %08x'%val)
  for r in refs:
   f=fm.getFunctionContaining(r.getFromAddress());print(' REF',r.getFromAddress(),'FUNC',f.getEntryPoint() if f else '<none>')

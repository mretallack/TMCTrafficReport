#@category MediaNav
# Resolve GEODB constructor literal globals and enumerate references to singleton storage.
mem=currentProgram.getMemory();rm=currentProgram.getReferenceManager();fm=currentProgram.getFunctionManager()
for lit in range(0x0033af9c,0x0033afdc,4):
 try:v=mem.getInt(toAddr(lit))&0xffffffff
 except:continue
 print('literal %08x -> %08x'%(lit,v))
 if 0x00c00000<=v<0x00d80000:
  for r in rm.getReferencesTo(toAddr(v)):
   f=fm.getFunctionContaining(r.getFromAddress());print(' REF global',r.getFromAddress(),'FUNC',f.getEntryPoint() if f else '<none>')

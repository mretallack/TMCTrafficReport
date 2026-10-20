#@category MediaNav
# List references to GEODB stream provider array storage.
rm=currentProgram.getReferenceManager();fm=currentProgram.getFunctionManager();a=toAddr(0x00d2a2ec)
print('TARGET',a)
for r in rm.getReferencesTo(a):
 f=fm.getFunctionContaining(r.getFromAddress())
 print('REF',r.getFromAddress(),'TYPE',r.getReferenceType(),'FUNC',f.getEntryPoint() if f else '<none>')

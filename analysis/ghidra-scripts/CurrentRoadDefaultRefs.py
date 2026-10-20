#@category MediaNav
rm=currentProgram.getReferenceManager();fm=currentProgram.getFunctionManager()
for a in [0x00d237e8,0x00d23878]:
 print('TARGET',hex(a))
 for r in rm.getReferencesTo(toAddr(a)):
  f=fm.getFunctionContaining(r.getFromAddress());print(r.getFromAddress(),r.getReferenceType(),f.getEntryPoint() if f else '<none>')

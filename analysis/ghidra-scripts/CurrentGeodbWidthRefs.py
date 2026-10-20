#@category MediaNav
listing=currentProgram.getListing();fm=currentProgram.getFunctionManager()
for ins in listing.getInstructions(True):
 s=ins.toString()
 if '#0x189' in s or '#0x18a' in s:
  f=fm.getFunctionContaining(ins.getAddress());print(ins.getAddress(),s,'FUNC',f.getEntryPoint() if f else '<none>')

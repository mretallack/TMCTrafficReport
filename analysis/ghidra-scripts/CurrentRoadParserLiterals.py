#@category MediaNav
mem=currentProgram.getMemory();fm=currentProgram.getFunctionManager();rm=currentProgram.getReferenceManager()
for a in range(0x0030be70,0x0030be90,4):
 try:v=mem.getInt(toAddr(a))&0xffffffff
 except:continue
 print('%08x -> %08x'%(a,v))
 try:
  vals=[mem.getInt(toAddr(v+i*4))&0xffffffff for i in range(40)]
  print(' data', ' '.join('%08x'%x for x in vals))
 except Exception as e:print(' no data')

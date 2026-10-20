#@category MediaNav
mem=currentProgram.getMemory();fm=currentProgram.getFunctionManager();rm=currentProgram.getReferenceManager()
def u32(a):
 try:return mem.getInt(toAddr(a))&0xffffffff
 except:return None
for a in range(0x002fc210,0x002fc244,4):
 v=u32(a);print('LIT %08x -> %08x'%(a,v or 0))
 if v and 0x00d00000<=v<0x00d80000:
  try:print(' DATA',' '.join('%08x'%(u32(v+i*4) or 0) for i in range(16)))
  except:pass

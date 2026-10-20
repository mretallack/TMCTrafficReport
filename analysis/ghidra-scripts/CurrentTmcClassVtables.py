#@category MediaNav
# Inspect TMCLOCATION/TMCHEADER vtables and all references to their address points.
mem=currentProgram.getMemory();fm=currentProgram.getFunctionManager();rm=currentProgram.getReferenceManager()
def u32(a):return mem.getInt(toAddr(a))&0xffffffff
for hdr,end,name in [(0x00c08fa0,0x00c08fc8,'TMCLOCATION'),(0x00c08fc8,0x00c090d8,'TMCHEADER')]:
 print('\n===',name,'===')
 ap=hdr+8
 for a in range(ap,end,4):
  v=u32(a);f=fm.getFunctionAt(toAddr(v));print('%08x +%02x -> %08x %s'%(a,a-ap,v,f.getName() if f else ''))
 print('--- address-point refs ---')
 for a in range(ap,end,4):
  for r in rm.getReferencesTo(toAddr(a)):
   f=fm.getFunctionContaining(r.getFromAddress());print('%08x <- %s func=%s'%(a,r.getFromAddress(),f.getEntryPoint() if f else '<none>'))

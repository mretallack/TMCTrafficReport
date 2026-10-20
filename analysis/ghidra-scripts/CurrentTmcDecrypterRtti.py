#@category MediaNav
# Enumerate TMCDECRYPTER RTTI/vtable and refs.
mem=currentProgram.getMemory();fm=currentProgram.getFunctionManager();rm=currentProgram.getReferenceManager()
def u32(a):
 try:return mem.getInt(toAddr(a))&0xffffffff
 except:return None
def cs(a):
 out=[]
 try:
  for i in range(300):
   b=mem.getByte(toAddr(a+i))&255
   if b==0:break
   if b<32 or b>126:return None
   out.append(chr(b))
  return ''.join(out) if out else None
 except:return None
for a in range(0x00ca0000,0x00cb0000,4):
 off=u32(a);ti=u32(a+4);fn=u32(a+8)
 if off is None or off not in (0,0xffffffff,0xfffffffc,0xfffffff8):continue
 if ti is None or fn is None or not (0x00b00000<=ti<0x00d80000) or not fm.getFunctionAt(toAddr(fn)):continue
 name=cs(u32(ti+4))
 if name and 'TMCDECRYPTER' in name:
  print('HEADER %s name=%s first=%08x'%(toAddr(a),name,fn))
  for x in range(a+8,a+0x80,4):
   v=u32(x);f=fm.getFunctionAt(toAddr(v)) if v is not None else None
   print(' SLOT %s +%02x %08x %s'%(toAddr(x),x-(a+8),v or 0,f.getName() if f else ''))
  for r in rm.getReferencesTo(toAddr(a+8)):
   f=fm.getFunctionContaining(r.getFromAddress());print(' REF',r.getFromAddress(),'FUNC',f.getEntryPoint() if f else '<none>')

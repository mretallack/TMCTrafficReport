#@category MediaNav
# Recover Itanium C++ vtable/typeinfo names around map section loader method.
mem=currentProgram.getMemory();fm=currentProgram.getFunctionManager()
def u32(a):return mem.getInt(toAddr(a))&0xffffffff
def cstr(a,maxn=300):
 out=[]
 try:
  for i in range(maxn):
   b=mem.getByte(toAddr(a+i))&255
   if b==0:break
   if b<32 or b>126:return None
   out.append(chr(b))
  return ''.join(out) if out else None
 except:return None
for a in range(0x00c08000,0x00c0a000,4):
 off=u32(a);ti=u32(a+4);fn=u32(a+8)
 if off not in (0,0xffffffff,0xfffffffc,0xfffffff8,0xfffffff4):continue
 if not (0x00b00000<=ti<0x00d80000):continue
 if fm.getFunctionAt(toAddr(fn)) is None:continue
 # common typeinfo object: vptr then name pointer
 namep=u32(ti+4);name=cstr(namep)
 if name and ('MAP' in name.upper() or 'FILE' in name.upper() or 'FBL' in name.upper()):
  print('vtable_header=%08x offset=%08x typeinfo=%08x name=%s firstfn=%08x'%(a,off,ti,name,fn))
  for j in range(0,0x100,4):
   v=u32(a+8+j);f=fm.getFunctionAt(toAddr(v))
   if f:print('  +%02x %08x %s'%(j,v,f.getName()))

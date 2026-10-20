#@category MediaNav
# Enumerate all Itanium vtable headers around map section dispatcher, no name filter.
mem=currentProgram.getMemory();fm=currentProgram.getFunctionManager()
def u32(a):return mem.getInt(toAddr(a))&0xffffffff
def cstr(a,maxn=400):
 out=[]
 try:
  for i in range(maxn):
   b=mem.getByte(toAddr(a+i))&255
   if b==0:break
   if b<32 or b>126:return None
   out.append(chr(b))
  return ''.join(out) if out else None
 except:return None
for a in range(0x00c08f00,0x00c09a00,4):
 off=u32(a);ti=u32(a+4);fn=u32(a+8)
 if off not in (0,0xffffffff,0xfffffffc,0xfffffff8,0xfffffff4,0xfffffff0,0xffffffec):continue
 if not (0x00b00000<=ti<0x00d80000):continue
 if fm.getFunctionAt(toAddr(fn)) is None:continue
 name=cstr(u32(ti+4))
 if name:print('%08x off=%08x ti=%08x name=%s first=%08x'%(a,off,ti,name,fn))

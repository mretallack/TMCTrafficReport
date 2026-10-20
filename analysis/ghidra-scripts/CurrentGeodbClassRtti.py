#@category MediaNav
# Enumerate all Itanium vtable headers for GEODB file/object classes.
mem=currentProgram.getMemory();fm=currentProgram.getFunctionManager();rm=currentProgram.getReferenceManager()
def u32(a):
 try:return mem.getInt(toAddr(a))&0xffffffff
 except:return None
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
wanted=('TMCDECRYPTER','I_TMC_DECRYPTER')
for a in range(0x00b00000,0x00d20000,4):
 off=u32(a);ti=u32(a+4);fn=u32(a+8)
 if off is None or ti is None or fn is None:continue
 if off not in (0,0xffffffff,0xfffffffc,0xfffffff8,0xfffffff4,0xfffffff0,0xffffffec):continue
 if not (0x00b00000<=ti<0x00d80000) or fm.getFunctionAt(toAddr(fn)) is None:continue
 name=cstr(u32(ti+4))
 if name and any(x in name for x in wanted):
  print('HEADER %08x off=%08x ti=%08x name=%s first=%08x'%(a,off,ti,name,fn))
  for aa in range(a+8,min(a+0x100,0x00d20000),4):
   # stop at next plausible vtable header
   if aa>a+8:
    try:
     oo=u32(aa);tt=u32(aa+4);ff=u32(aa+8)
     if oo in (0,0xffffffff,0xfffffffc,0xfffffff8) and 0x00b00000<=tt<0x00d80000 and fm.getFunctionAt(toAddr(ff)):break
    except:pass
   v=u32(aa);f=fm.getFunctionAt(toAddr(v));print(' SLOT %08x +%02x -> %08x %s'%(aa,aa-(a+8),v,f.getName() if f else ''))
  for r in rm.getReferencesTo(toAddr(a+8)):
   f=fm.getFunctionContaining(r.getFromAddress());print(' REF_AP',r.getFromAddress(),'FUNC',f.getEntryPoint() if f else '<none>')

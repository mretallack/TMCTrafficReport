#@category MediaNav
# Inspect vtables containing current packed map-section load method and references to their starts.
fm=currentProgram.getFunctionManager();mem=currentProgram.getMemory();rm=currentProgram.getReferenceManager()
for base in [0x00c09280,0x00c097a0]:
 print('\n=== VTABLE REGION %08x ==='%base)
 for off in range(0,0x100,4):
  a=toAddr(base+off)
  try:v=mem.getInt(a)&0xffffffff
  except:continue
  f=fm.getFunctionAt(toAddr(v))
  if f or v==0x0033a6f0:
   print('%s -> %08x %s'%(a,v,f.getName() if f else ''))
 print('--- refs into region ---')
 for off in range(0,0x100,4):
  a=toAddr(base+off)
  for r in rm.getReferencesTo(a):
   f=fm.getFunctionContaining(r.getFromAddress())
   print('%s <- %s func=%s'%(a,r.getFromAddress(),f.getEntryPoint() if f else '<none>'))

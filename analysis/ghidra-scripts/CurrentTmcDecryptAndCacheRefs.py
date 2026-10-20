#@category MediaNav
from ghidra.app.decompiler import DecompInterface
from jarray import array
TARGETS=['Decrypt called but SVK_TABLE not loaded','Decrypt called but ENCID not set yet','SetDecryptionParams error: sid=%d cc=%d ltnbe=%d encid=%d','EVENT:htmc=%d:loc=%d:extent=%d:dir=%d:bidi=%d:age=%d:cc=%d:ltn=%d:new=1:sid=%d:qdecoded=%d:','EVENT htmc=%u loc=%u extent=%u dir=%u bidi=%u age=%d cc=%u ltn=%u new=1 tmc_source=%u sid=%u qdecoded=%u snd_id=%u ']
mem=currentProgram.getMemory();fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram);seen=set()
for t in TARGETS:
 p=array([ord(c) for c in t],'b');a=mem.findBytes(mem.getMinAddress(),mem.getMaxAddress(),p,None,True,monitor);print('\n=== TARGET %s ==='%t)
 while a is not None:
  print('string',a)
  for ref in currentProgram.getReferenceManager().getReferencesTo(a):
   f=fm.getFunctionContaining(ref.getFromAddress());print('REF',ref.getFromAddress(),'FUNC',f.getEntryPoint() if f else '<none>')
   if f and f.getEntryPoint() not in seen:
    seen.add(f.getEntryPoint());r=d.decompileFunction(f,900,monitor)
    if r.decompileCompleted():print('--- DECOMPILE %s ---\n%s\n--- END ---'%(f.getEntryPoint(),r.getDecompiledFunction().getC()[:300000]))
  a=mem.findBytes(a.add(1),mem.getMaxAddress(),p,None,True,monitor)

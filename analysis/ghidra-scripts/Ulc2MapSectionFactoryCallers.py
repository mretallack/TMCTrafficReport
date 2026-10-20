#@category MediaNav
# Decompile callers of the generic map-container section factory that dispatches case 12 to the TMC index decoder.
from ghidra.app.decompiler import DecompInterface
addr=toAddr(0x006a240c); fm=currentProgram.getFunctionManager(); d=DecompInterface(); d.openProgram(currentProgram)
print('TARGET',addr)
seen=set()
for ref in currentProgram.getReferenceManager().getReferencesTo(addr):
 f=fm.getFunctionContaining(ref.getFromAddress()); print('REF',ref.getFromAddress(),'FUNC',f.getEntryPoint() if f else '<none>')
 if f and f.getEntryPoint() not in seen:
  seen.add(f.getEntryPoint()); r=d.decompileFunction(f,360,monitor)
  if r.decompileCompleted(): print('--- DECOMPILE %s ---\n%s\n--- END ---' % (f.getEntryPoint(),r.getDecompiledFunction().getC()[:140000]))
  else: print(r.getErrorMessage())

#@category MediaNav
from ghidra.app.decompiler import DecompInterface
addr=toAddr(0x00699e1c); fm=currentProgram.getFunctionManager(); d=DecompInterface(); d.openProgram(currentProgram)
print('TARGET',addr)
for ref in currentProgram.getReferenceManager().getReferencesTo(addr):
 f=fm.getFunctionContaining(ref.getFromAddress()); print('REF',ref.getFromAddress(),'FUNC',f.getEntryPoint() if f else '<none>')
 if f:
  r=d.decompileFunction(f,300,monitor)
  if r.decompileCompleted(): print('--- DECOMPILE %s ---\n%s\n--- END ---' % (f.getEntryPoint(),r.getDecompiledFunction().getC()[:120000]))

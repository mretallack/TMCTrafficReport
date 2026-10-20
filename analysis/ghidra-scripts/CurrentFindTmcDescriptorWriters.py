#@category MediaNav
# Structural decompilation search for writers of current TMC map-object descriptor fields.
from ghidra.app.decompiler import DecompInterface
fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram)
start=toAddr(0x002d0000);end=toAddr(0x00350000)
terms=['+ 0x58)', '+ 0x5c)', '+ 0x5e)', 'param_1 + 0x58', 'param_1 + 0x5c']
for f in fm.getFunctions(start,True):
 if f.getEntryPoint().compareTo(end)>=0:break
 if f.getBody().getNumAddresses()<80:continue
 r=d.decompileFunction(f,45,monitor)
 if not r.decompileCompleted():continue
 c=r.getDecompiledFunction().getC()
 score=sum(t in c for t in terms)
 if score>=2:
  print('\n=== MATCH %s size=%d score=%d ==='%(f.getEntryPoint(),f.getBody().getNumAddresses(),score))
  lines=c.splitlines()
  indexes=[i for i,line in enumerate(lines) if any(t in line for t in terms)]
  shown=set()
  for i in indexes:
   for j in range(max(0,i-8),min(len(lines),i+12)):
    if j not in shown: print('%04d %s'%(j+1,lines[j]));shown.add(j)

#@category MediaNav
# Find current map header parser by writes/uses of the section offset field cluster.
from ghidra.app.decompiler import DecompInterface
fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram)
start=toAddr(0x002d0000);end=toAddr(0x00350000)
terms=['+ 0x5c)', '+ 0x60)', '+ 0x80)', '+ 0x84)', '+ 0x9c)', '+ 0xa0)', '+ 0xb4)', '+ 0xb8)', '+ 0xbc)', '+ 0xdc)', '+ 0xe0)']
for f in fm.getFunctions(start,True):
 if f.getEntryPoint().compareTo(end)>=0:break
 if f.getBody().getNumAddresses()<120:continue
 r=d.decompileFunction(f,60,monitor)
 if not r.decompileCompleted():continue
 c=r.getDecompiledFunction().getC(); present=[t for t in terms if t in c]
 if len(present)>=5:
  print('\n=== MATCH %s size=%d fields=%s ==='%(f.getEntryPoint(),f.getBody().getNumAddresses(),','.join(present)))
  print(c[:100000])

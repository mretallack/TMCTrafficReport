#@category MediaNav
# Find allocations of large GEODBFILE-sized objects and show constructor context.
from ghidra.app.decompiler import DecompInterface
import re
fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram)
for f in fm.getFunctions(toAddr(0x002d0000),True):
 if f.getEntryPoint().compareTo(toAddr(0x00350000))>=0:break
 if f.getBody().getNumAddresses()<40:continue
 r=d.decompileFunction(f,70,monitor)
 if not r.decompileCompleted():continue
 c=r.getDecompiledFunction().getC()
 ms=re.findall(r'FUN_0042894c\(0x([0-9a-f]+)',c)
 sizes=[int(x,16) for x in ms]
 if any(0x140<=x<=0x400 for x in sizes):
  print('\n=== MATCH %s size=%d allocs=%s ==='%(f.getEntryPoint(),f.getBody().getNumAddresses(),','.join(hex(x) for x in sizes)));print(c[:140000])

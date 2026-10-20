#@category MediaNav
# Find writers/users of map-owner table at +8 around its current class module.
from ghidra.app.decompiler import DecompInterface
fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram)
for f in fm.getFunctions(toAddr(0x00336000),True):
 if f.getEntryPoint().compareTo(toAddr(0x00348000))>=0:break
 if f.getBody().getNumAddresses()<80:continue
 r=d.decompileFunction(f,70,monitor)
 if not r.decompileCompleted():continue
 c=r.getDecompiledFunction().getC()
 terms=['param_1 + 8','param_1[2]','+ 8)']
 if ('param_1 + 8' in c or 'param_1[2]' in c) and ('FUN_0042894c' in c or '= ' in c):
  print('\n=== MATCH %s size=%d ==='%(f.getEntryPoint(),f.getBody().getNumAddresses()))
  print(c[:100000])

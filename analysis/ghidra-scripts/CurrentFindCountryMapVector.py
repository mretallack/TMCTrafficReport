#@category MediaNav
# Find methods manipulating map-manager per-country object vector at full object offsets 0x0c/0x10/0x14.
from ghidra.app.decompiler import DecompInterface
fm=currentProgram.getFunctionManager();d=DecompInterface();d.openProgram(currentProgram)
for f in fm.getFunctions(toAddr(0x00338000),True):
 if f.getEntryPoint().compareTo(toAddr(0x0033c000))>=0:break
 if f.getBody().getNumAddresses()<40:continue
 r=d.decompileFunction(f,90,monitor)
 if not r.decompileCompleted():continue
 c=r.getDecompiledFunction().getC()
 terms=['param_1 + 0xc','param_1 + 0x10','param_1 + 0x14','param_1[3]','param_1[4]','param_1[5]']
 score=sum(t in c for t in terms)
 if score>=2:
  print('\n=== MATCH %s size=%d score=%d ==='%(f.getEntryPoint(),f.getBody().getNumAddresses(),score));print(c[:120000])

#@category MediaNav
from ghidra.app.decompiler import DecompInterface
d=DecompInterface();d.openProgram(currentProgram);fm=currentProgram.getFunctionManager();mem=currentProgram.getMemory()
for a in [0x000bd96c]:
 f=fm.getFunctionAt(toAddr(a));print('=== %08x ==='%a);r=d.decompileFunction(f,300,monitor);print(r.getDecompiledFunction().getC() if r.decompileCompleted() else r.getErrorMessage())
print('LITERALS')
for a in range(0x000cd1f8,0x000cd27c,4):
 try: print('%08x %08x'%(a,mem.getInt(toAddr(a))&0xffffffff))
 except: pass

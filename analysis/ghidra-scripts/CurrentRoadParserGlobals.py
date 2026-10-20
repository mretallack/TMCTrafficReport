#@category MediaNav
mem=currentProgram.getMemory()
for a in range(0x0030be70,0x0030bea0,4):
 try:print('%08x %08x'%(a,mem.getInt(toAddr(a))&0xffffffff))
 except:pass

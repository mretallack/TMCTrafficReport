#@category MediaNav
mem=currentProgram.getMemory();p=mem.getInt(toAddr(0x002f1300))&0xffffffff
print('VTABLE %08x'%p)
for i in range(12):print('%02x %08x'%(i*4,mem.getInt(toAddr(p+i*4))&0xffffffff))

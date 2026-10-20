#@category MediaNav
mem=currentProgram.getMemory();p=mem.getInt(toAddr(0x00316fac))&0xffffffff
print('VTABLE_BASE %08x'%p)
for i in range(40):
 try: print('%02x %08x'%(i*4,mem.getInt(toAddr(p+i*4))&0xffffffff))
 except: break

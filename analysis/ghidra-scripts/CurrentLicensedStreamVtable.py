#@category MediaNav
mem=currentProgram.getMemory();p=mem.getInt(toAddr(0x005aa280))&0xffffffff
print('BASE',hex(p))
for i in range(48):
 try: print('%02x %08x'%(i*4,mem.getInt(toAddr(p+i*4))&0xffffffff))
 except: break

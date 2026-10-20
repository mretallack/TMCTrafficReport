#@category MediaNav
listing=currentProgram.getListing()
for base,end in [(0x002eaf00,0x002eb000),(0x0034a9bc,0x0034ab90),(0x003168e8,0x00316afc)]:
 print('\n=== %08x ==='%base);cur=listing.getInstructionAt(toAddr(base))
 while cur and cur.getAddress().compareTo(toAddr(end))<0:
  print('%s: %s'%(cur.getAddress(),cur));cur=cur.getNext()

#@category MediaNav
listing=currentProgram.getListing()
for base in [0x000b0660,0x000b0700,0x00329800,0x00329980]:
 print('\n===',hex(base),'===');cur=listing.getInstructionAt(toAddr(base)) or listing.getInstructionAfter(toAddr(base))
 for i in range(100):
  if not cur or cur.getAddress().compareTo(toAddr(base+0x180))>=0:break
  print('%s: %s'%(cur.getAddress(),cur));cur=cur.getNext()

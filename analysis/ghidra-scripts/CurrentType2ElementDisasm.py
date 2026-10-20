#@category MediaNav
listing=currentProgram.getListing();cur=listing.getInstructionAt(toAddr(0x002e2e34))
while cur and cur.getAddress().compareTo(toAddr(0x002e2e70))<0:
 print('%s: %s'%(cur.getAddress(),cur));cur=cur.getNext()

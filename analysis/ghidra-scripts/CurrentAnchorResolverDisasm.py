#@category MediaNav
listing=currentProgram.getListing();cur=listing.getInstructionAt(toAddr(0x000b06a8))
while cur and cur.getAddress().compareTo(toAddr(0x000b0708))<0:
 print('%s: %s'%(cur.getAddress(),cur));cur=cur.getNext()

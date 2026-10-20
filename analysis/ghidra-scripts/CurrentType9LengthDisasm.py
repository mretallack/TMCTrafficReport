#@category MediaNav
listing=currentProgram.getListing();cur=listing.getInstructionAt(toAddr(0x0033ca90))
while cur and cur.getAddress().compareTo(toAddr(0x0033cac0))<0:
 print('%s: %s'%(cur.getAddress(),cur));cur=cur.getNext()

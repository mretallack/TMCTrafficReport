#@category MediaNav
# Dump instructions around unassigned caller of map manager constructor.
listing=currentProgram.getListing();fm=currentProgram.getFunctionManager();a=toAddr(0x0033afec);inst=listing.getInstructionContaining(a)
print('target',a,inst)
cur=inst
for i in range(100):
 p=cur.getPrevious()
 if not p:break
 cur=p
for i in range(260):
 if not cur:break
 print('%s: %s%s'%(cur.getAddress(),cur,' >>>' if cur.getAddress()==a else ''))
 cur=cur.getNext()

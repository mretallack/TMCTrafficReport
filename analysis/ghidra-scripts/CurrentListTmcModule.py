#@category MediaNav
# List current ARM functions around the known TMC descriptor lookup module.
fm=currentProgram.getFunctionManager()
start=toAddr(0x002e0000);end=toAddr(0x002f2000)
print('entry,end,size,name')
for f in fm.getFunctions(start,True):
 if f.getEntryPoint().compareTo(end)>=0:break
 print('%s,%s,%d,%s'%(f.getEntryPoint(),f.getBody().getMaxAddress(),f.getBody().getNumAddresses(),f.getName()))

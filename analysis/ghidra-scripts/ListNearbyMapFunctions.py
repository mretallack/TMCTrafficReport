#@category MediaNav
# List functions adjacent to the TMC map-index lookup implementation for loader/constructor triage.
fm=currentProgram.getFunctionManager()
start=toAddr(0x00690000); end=toAddr(0x006a0000)
print("entry,end,size,name")
for f in fm.getFunctions(start, True):
 if f.getEntryPoint().compareTo(end) >= 0: break
 print("%s,%s,%d,%s" % (f.getEntryPoint(), f.getBody().getMaxAddress(), f.getBody().getNumAddresses(), f.getName()))

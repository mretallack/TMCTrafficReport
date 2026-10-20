#@category MediaNav
# Trace ULC2 native TMC-to-map resolver diagnostics and map-loader references.
from ghidra.app.decompiler import DecompInterface
from jarray import array

TARGETS = [
 "TMC Location not found in map. CC: 0x%02hhx LTN: 0x%02hhx LOCATIONID: 0x%04hx",
 "TMC Location not found! Country: %d LTN: %d, Location:%d",
 "TMCInfo validation failed: FBL(MAP) file for country not exist",
 "country FBL file not found, TMC logic update GPS_COUNTRY_CHANGED_EVENT failed",
 "map_loader",
 "TMCEVENTTABLE::ClassifyEvent #2_2 (%i)",
]
mem=currentProgram.getMemory(); fm=currentProgram.getFunctionManager()
start=mem.getMinAddress(); end=mem.getMaxAddress()
decomp=DecompInterface(); decomp.openProgram(currentProgram)
seen=set()
for target in TARGETS:
 pat=array([ord(c) for c in target], 'b')
 addr=mem.findBytes(start,end,pat,None,True,monitor)
 print("\n=== ASCII TARGET: %s ===" % target)
 if addr is None:
  print("not found"); continue
 count=0
 while addr is not None and count<20:
  count+=1; print("string @ %s" % addr)
  refs=currentProgram.getReferenceManager().getReferencesTo(addr); n=0
  for ref in refs:
   n+=1; f=fm.getFunctionContaining(ref.getFromAddress())
   print("  ref from %s function=%s" % (ref.getFromAddress(),f.getEntryPoint() if f else '<none>'))
   if f and f.getEntryPoint() not in seen:
    seen.add(f.getEntryPoint()); r=decomp.decompileFunction(f,120,monitor)
    if r.decompileCompleted(): print("--- DECOMPILE %s ---\n%s\n--- END ---" % (f.getEntryPoint(),r.getDecompiledFunction().getC()[:40000]))
    else: print("  decompile failed: %s" % r.getErrorMessage())
  if n==0: print("  no direct references")
  addr=mem.findBytes(addr.add(1),end,pat,None,True,monitor)
print("DONE")

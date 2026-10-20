#@category MediaNav
# Print disassembly around a direct reference that Ghidra did not assign to a function.
from ghidra.program.model.address import Address
from ghidra.app.cmd.function import CreateFunctionCmd

addr = toAddr(0x0048d7f4)
listing = currentProgram.getListing()
inst = listing.getInstructionContaining(addr)
print("target=%s instruction=%s" % (addr, inst))
# Walk backwards far enough to find the surrounding MIPS function prologue/return.
first = inst
for i in range(160):
    prev = first.getPrevious()
    if prev is None: break
    first = prev
print("=== INSTRUCTIONS ===")
cur = first
for i in range(360):
    if cur is None: break
    mark = " >>>" if cur.getAddress() == addr else ""
    print("%s: %-12s %s%s" % (cur.getAddress(), cur.getMnemonicString(), cur.toString().split(None,1)[1] if len(cur.toString().split(None,1))>1 else '', mark))
    cur = cur.getNext()
print("=== NEARBY FUNCTIONS ===")
fm=currentProgram.getFunctionManager()
for f in fm.getFunctions(toAddr(0x00470000), True):
    if f.getEntryPoint().compareTo(toAddr(0x004a0000)) > 0: break
    print("%s %s body=%s" % (f.getEntryPoint(),f.getName(),f.getBody()))

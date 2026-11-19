import struct, sys
from capstone import Cs, CS_ARCH_PPC, CS_MODE_32, CS_MODE_BIG_ENDIAN
d=open('work/main.dol','rb').read()
offs=struct.unpack('>18I',d[0:0x48]); addrs=struct.unpack('>18I',d[0x48:0x90]); sizes=struct.unpack('>18I',d[0x90:0xD8])
def rd(a,n):
    for o,ad,s in zip(offs,addrs,sizes):
        if s and ad<=a<ad+s: return d[o+a-ad:o+a-ad+n]
md=Cs(CS_ARCH_PPC, CS_MODE_32|CS_MODE_BIG_ENDIAN)
a0,a1=int(sys.argv[1],16),int(sys.argv[2],16)
for i in md.disasm(rd(a0,a1-a0),a0):
    print(f"{i.address:08x} {i.mnemonic} {i.op_str}")

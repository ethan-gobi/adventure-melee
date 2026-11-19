import sys
sys.path.insert(0, r'C:\adventure-melee\scripts')
from hsd import *
f = HSDRawFile(sys.argv[1])
for r in f.Roots: print('root', r.Name, r.Data.GetType().Name)
root = [r for r in f.Roots if r.Data.GetType().Name == 'HSD_JOBJ'][0].Data
js = jobj_list(root)
print('joints', len(js))
for i,(j,p,d) in enumerate(js):
    nd=0; npo=0; info=[]
    dobj=j.Dobj
    while dobj is not None:
        nd+=1; po=dobj.Pobj
        while po is not None:
            npo+=1
            info.append(str(po.Flags))
            po=po.Next
        dobj=dobj.Next
    print(f"{i:2} p={p:2} {'  '*d}T=({j.TX:.2f},{j.TY:.2f},{j.TZ:.2f}) R=({j.RX:.2f},{j.RY:.2f},{j.RZ:.2f}) S=({j.SX:.2f},{j.SY:.2f},{j.SZ:.2f}) flags={j.Flags} dobj={nd} pobj={npo} {set(info) if info else ''}")

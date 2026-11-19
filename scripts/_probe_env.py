import sys
sys.path.insert(0, r'C:\adventure-melee\scripts')
from hsd import *
import numpy as np, math
from HSDRaw.Tools import GX_VertexAccessor
print([m.ToString() for m in clr.GetClrType(GX_VertexAccessor).GetMethods() if m.IsStatic])
f = HSDRawFile(r'C:\adventure-melee\work\v04\PlSnNr.dat')
root=[r for r in f.Roots if r.Data.GetType().Name=='HSD_JOBJ'][0].Data
js=jobj_list(root)
def local(j):
    cx,sx=math.cos(j.RX),math.sin(j.RX); cy,sy=math.cos(j.RY),math.sin(j.RY); cz,sz=math.cos(j.RZ),math.sin(j.RZ)
    Rx=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]]); Ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]); Rz=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    M=np.eye(4); M[:3,:3]=Rz@Ry@Rx@np.diag([j.SX,j.SY,j.SZ]); M[:3,3]=[j.TX,j.TY,j.TZ]; return M
W=[]
for j,p,d in js: W.append(local(j) if p<0 else W[p]@local(j))
idx={id(j._s):i for i,(j,p,d) in enumerate(js)}
def bi(j):
    for i,(q,p,d) in enumerate(js):
        if q._s == j._s: return i
    return -1
for i in (4,7,8,10,13,14,16,18,19,23,24,25,38,39,45,46,47): print('bone',i,'world',np.round(W[i][:3,3],2))
d=root.Dobj; n=0; shown=0
while d is not None and shown<6:
    po=d.Pobj
    while po is not None and shown<6:
        envs=po.EnvelopeWeights
        if envs is not None:
            dl=po.ToDisplayList(); verts=list(GX_VertexAccessor.GetDecodedVertices(dl, po)); envs=list(dl.Envelopes) if hasattr(dl,"Envelopes") else envs
            for ei,e in enumerate(envs):
                if e.EnvelopeCount==1 and shown<6:
                    b=bi(e.GetJOBJAt(0)); vs=np.array([[v.POS.X,v.POS.Y,v.POS.Z] for v in verts if v.PNMTXIDX//3==ei])
                    if len(vs):
                        print('dobj',n,'single env bone',b,'w',e.GetWeightAt(0),'bone world',np.round(W[b][:3,3],1),'vert mean',np.round(vs.mean(0),1),'n',len(vs)); shown+=1
        po=po.Next
    d=d.Next; n+=1

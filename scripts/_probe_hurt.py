import sys
sys.path.insert(0, r'C:\adventure-melee\scripts')
from hsd import *
f = HSDRawFile(r'C:\adventure-melee\work\v03\PlSn_v03.dat')
fd = f.Roots[0].Data
print([p.Name for p in fd.GetType().GetProperties()])
hb = fd.Hurtboxes
print(type(hb).__name__, [p.Name for p in hb.GetType().GetProperties()])
arr = hb.Hurtboxes if hasattr(hb,'Hurtboxes') else hb.Array
for i, h in enumerate(arr):
    print(i, 'bone', h.BoneIndex, 'p1', (round(h.X1,2),round(h.Y1,2),round(h.Z1,2)), 'p2', (round(h.X2,2),round(h.Y2,2),round(h.Z2,2)), 'r', round(h.Size,2), 'grab', h.Grabbable if hasattr(h,'Grabbable') else '', [p.Name for p in h.GetType().GetProperties()] if i==0 else '')

import sys, collections
sys.path.insert(0, r'C:\adventure-melee\scripts')
from hsd import *
from HSDRaw.Tools.Melee import FighterAJManager
from System.IO import File
aj = FighterAJManager(File.ReadAllBytes(r'C:\adventure-melee\work\v04\PlSnAJ.dat'))
syms = list(aj.GetAnimationSymbols())
print('animations', len(syms))
trans = collections.Counter(); seen_types = collections.Counter(); n=0
for s in syms:
    data = aj.GetAnimationData(s)
    f = HSDRawFile(data)
    ft = f.Roots[0].Data
    if n == 0: print('root type', type(ft).__name__, [p.Name for p in ft.GetType().GetProperties()][:12])
    nodes = list(ft.Nodes)
    for bi, node in enumerate(nodes):
        for tr in node.Tracks:
            jt = str(tr.JointTrackType); seen_types[jt]+=1
            if 'TRA' in jt: trans[(bi, jt)] += 1
    n += 1
print('track types', dict(seen_types))
for (bi, jt), c in sorted(trans.items()): print(f'bone {bi:2} {jt}: in {c} animations')

import json, math, sys, os, numpy as np
sys.path.insert(0, 'scripts')
from hsd import *
from System.IO import File
from HSDRaw.Tools.Melee import FighterAJManager
bd = json.load(open('work/v10/PlSnNr_sonic_bound.json'))
rest = [np.array(j[:9], dtype=float) for j in bd['joints']]; parent = [j[9] for j in bd['joints']]
def mat(v):
    tx, ty, tz, rx, ry, rz, sx, sy, sz = v
    cx, sxn, cy, syn, cz, szn = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    R = np.array([[cz, -szn, 0], [szn, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, syn], [0, 1, 0], [-syn, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sxn], [0, sxn, cx]])
    m = np.eye(4); m[:3, :3] = R @ np.diag([sx, sy, sz]); m[:3, 3] = [tx, ty, tz]; return m
W = []
for i, v in enumerate(rest): W.append(mat(v) if parent[i] < 0 else W[parent[i]] @ mat(v))
for i in range(len(rest)):
    print(i, parent[i], np.round(W[i][:3, 3], 2).tolist())
aj = FighterAJManager(File.ReadAllBytes('work/v10/PlSnAJ_v10r.dat'))
syms = list(aj.GetAnimationSymbols())
names = [s.split('ACTION_')[1].replace('_figatree', '') for s in syms]
print(len(names)); print(' '.join(f"{n}:{int(HSDRawFile(aj.GetAnimationData(s)).Roots[0].Data.FrameCount)}" for n, s in zip(names, syms)))
for want in ('AttackDash', 'AttackAirF', 'JumpF', 'DamageFall'):
    s = [x for x in syms if f'ACTION_{want}_figatree' in x][0]
    ft = HSDRawFile(aj.GetAnimationData(s)).Roots[0].Data
    print(want, ft.FrameCount, [(bi, [str(t.JointTrackType)[-4:] for t in ft.Nodes[bi].Tracks]) for bi in range(ft.Nodes.Count) if any('TRA' in str(t.JointTrackType) for t in ft.Nodes[bi].Tracks)])

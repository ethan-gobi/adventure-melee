"""Contact sheet of animations as they are stored in a PlSnAJ.dat (any animation, not only the ones sonic_moves.py writes).

Usage: python anim_sheet.py <PlSnAJ.dat> <out.png> <Action1,Action2,...> [frames per row, default 7] [yaw, default 65]
Draws the Sonic model flat shaded with every bone track of the stored animation applied, to spot broken poses offline.
"""
import sys
import io
import contextlib

import numpy as np

with contextlib.redirect_stdout(io.StringIO()):
    import sonic_anim_lib as L
from sonic_anim_lib import FighterAJManager, File, HSDRawFile

CH = {"HSD_A_J_TRAX": 0, "HSD_A_J_TRAY": 1, "HSD_A_J_TRAZ": 2, "HSD_A_J_ROTX": 3, "HSD_A_J_ROTY": 4, "HSD_A_J_ROTZ": 5,
      "HSD_A_J_SCAX": 6, "HSD_A_J_SCAY": 7, "HSD_A_J_SCAZ": 8}


class Raw:
    """One stored animation, solved to world matrices on every frame (same shape as sonic_anim_lib.Anim.solved)."""

    def __init__(self, aj, action):
        from HSDRaw.Tools import FOBJ_Player
        sym = [s_ for s_ in aj.GetAnimationSymbols() if s_.endswith(f"ACTION_{action}_figatree")][0]
        ft = HSDRawFile(aj.GetAnimationData(sym)).Roots[0].Data
        self.T = int(round(ft.FrameCount)) - 1 if ft.FrameCount > 1 else 0
        self.actions = [action]
        players = []
        for i in range(min(L.NB, ft.Nodes.Count)):
            for t in ft.Nodes[i].Tracks:
                nm = str(t.JointTrackType)
                if nm in CH:
                    players.append((i, CH[nm], FOBJ_Player(t.ToFOBJ())))
        self.solved = []
        for f in range(self.T + 1):
            vals = [v.copy() for v in L.rest]
            for i, c, pl in players:
                vals[i][c] = pl.GetValue(float(f))
            W = []
            for i, v in enumerate(vals):
                W.append(L.mat(v) if L.parent[i] < 0 else W[L.parent[i]] @ L.mat(v))
            self.solved.append((W, None))


if __name__ == "__main__":
    aj = FighterAJManager(File.ReadAllBytes(sys.argv[1]))
    names = sys.argv[3].split(",")
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 7
    yaw = float(sys.argv[5]) if len(sys.argv) > 5 else 65
    items = []
    for nm in names:
        r = Raw(aj, nm)
        fr = sorted({int(round(i * r.T / (n - 1))) for i in range(n)})
        items.append((f"{nm} T{r.T}", r, fr))
    L.sheet(items, sys.argv[2], yaw=yaw, cols=n)

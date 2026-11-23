"""Write Sonic's guard pose into the pose skeleton stored in PlSn.dat (see sonic_anim_lib.write_shield_pose).

Usage: python patch_shield_pose.py <PlSn.dat in> <PlSn.dat out>
The pose is the same curled-up one sonic_moves.py uses for the Guard animations (its build step also writes it); this
script applies it to an already built file.
"""
import contextlib
import io
import shutil
import sys

with contextlib.redirect_stdout(io.StringIO()):
    from sonic_anim_lib import P, Anim, write_shield_pose

src, dst = sys.argv[1], sys.argv[2]
PIV = (0, 2.0, 1.2)
TUCK = P(ground=0, pivot=PIV, chest=(40, 0, 0), head=(25, 0, 0), footL=20, footR=20,
         thighL=(0.25, 0.35, 1), shinL=(0.1, -1, -0.15), thighR=(-0.25, 0.35, 1), shinR=(-0.1, -1, -0.15),
         armL=(0.5, -0.5, 1), foreL=(-0.4, -0.2, 1), armR=(-0.5, -0.5, 1), foreR=(0.4, -0.2, 1))
SHIELD_Y = 4.6
GUARD = P(TUCK, root=(20, 0, 0), hip=(0, SHIELD_Y - 11.62, 0))
a = Anim("Guard", 1, [(0, GUARD), (1, GUARD)], shield_y=SHIELD_Y)
shutil.copyfile(src, dst)
print("shield pose joints written:", write_shield_pose(dst, a.solved[0][1]), "->", dst)

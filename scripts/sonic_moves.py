"""Sonic's own animations and attack scripts (v19). All values here are designed for this mod.

Usage: python sonic_moves.py preview <out dir>
       python sonic_moves.py build <PlSnAJ in> <PlSn.dat in> <PlSnAJ out> <PlSn.dat out> <changes.md>
Key frames are animation frames (0-based); hitbox frames are game frames (1-based), so game frame f shows animation frame f-1.
"""
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sonic_anim_lib import *  # noqa: E402,F401

# ------------------------------------------------------------------ poses
S = P(chest=(6, 0, 0))
PIV = (0, 2.0, 1.2)          # centre of the curled-up ball, relative to the hips
TUCK = P(ground=0, pivot=PIV, chest=(40, 0, 0), head=(25, 0, 0), footL=20, footR=20,
         thighL=(0.25, 0.35, 1), shinL=(0.1, -1, -0.15), thighR=(-0.25, 0.35, 1), shinR=(-0.1, -1, -0.15),
         armL=(0.5, -0.5, 1), foreL=(-0.4, -0.2, 1), armR=(-0.5, -0.5, 1), foreR=(0.4, -0.2, 1))


def tuck(pitch, **kw):
    return P(TUCK, root=(pitch, 0, 0), **kw)


FALL = P(ground=0, chest=(-5, 0, 0), footL=30, footR=30,
         armL=(1, 0.5, 0.1), foreL=(0.6, 1, 0.3), armR=(-1, 0.5, 0.1), foreR=(-0.6, 1, 0.3),
         thighL=(0.2, -1, 0.35), shinL=(0.12, -1, -0.35), thighR=(-0.2, -1, 0.0), shinR=(-0.12, -1, -0.6))
FALL2 = P(FALL, armL=(1, 0.65, 0.1), foreL=(0.7, 1, 0.3), armR=(-1, 0.65, 0.1), foreR=(-0.7, 1, 0.3),
          thighL=(0.2, -1, 0.42), thighR=(-0.2, -1, -0.07))
CROUCH = P(root=(30, 0, 0), chest=(30, 0, 0), head=(-35, 0, 0),
           thighL=(0.35, 0.15, 1), shinL=(0.1, -1, -0.5), thighR=(-0.35, 0.1, 1), shinR=(-0.1, -1, -0.55),
           armL=(0.5, -1, 0.5), foreL=(0.1, -1, 0.9), armR=(-0.5, -1, 0.5), foreR=(-0.1, -1, 0.9))
LAND = P(CROUCH, root=(8, 0, 0), armL=(1, -0.5, 0.2), foreL=(0.8, -1, 0.5), armR=(-1, -0.5, 0.2), foreR=(-0.8, -1, 0.5))
HELPLESS = P(FALL, root=(12, 0, 0), armL=(1, -0.3, -0.2), foreL=(1, -0.6, 0), armR=(-1, -0.3, -0.2), foreR=(-1, -0.6, 0))

A = []        # animations
SC = {}       # action name -> script bytes (filled in build)
HITS = {}     # label -> [(f0, f1, Hit)] for the preview and the script builder
PLAN = {}     # label -> dict(actions=[...], iasa=, aerial=, jab=, charge=)


def anim(actions, T, keys, **kw):
    a = Anim(actions, T, keys, **kw)
    A.append(a)
    return a


def move(label, actions, T, keys, events, prop=None, **plan):
    anim(actions, T, keys, prop=prop)
    HITS[label] = [(f0, f1, h) for f0, f1, hs in events for h in hs]
    PLAN[label] = dict(label=label, actions=[actions] if isinstance(actions, str) else list(actions), events=events, total=T, **plan)


def ball(dmg, angle, bkb, kbg, size=4.7, id=0, wdsk=0):
    return Hit(id, 2, dmg, size, angle, bkb, kbg, off=PIV, wdsk=wdsk)


def leg(side, dmg, angle, bkb, kbg, size=2.5, id=0, shin_dmg=None, wdsk=0):
    """Foot hitbox plus a slightly weaker, smaller shin hitbox."""
    th, sh, ft = LEGS[side]
    return [Hit(id, ft, dmg, size, angle, bkb, kbg, off=(1.6, 0, 0), wdsk=wdsk),
            Hit(id + 1, sh, shin_dmg or dmg, size * 0.8, angle, bkb, kbg, off=(2.4, 0, 0), wdsk=wdsk)]


# ------------------------------------------------------------------ movement
move("JumpF", "JumpF", 35, [(0, S), (5, tuck(60)), (30, tuck(630), "lin"), (35, P(FALL, root=(720, 0, 0)), "lin")], [], ball=(6, 31))
move("JumpB", "JumpB", 50, [(0, S), (5, tuck(-60)), (44, tuck(-990), "lin"), (50, P(FALL, root=(-1080, 0, 0)), "lin")], [], ball=(6, 45))
move("JumpAerialF", "JumpAerialF", 50, [(0, FALL), (4, tuck(90)), (44, tuck(990), "lin"), (50, P(FALL, root=(1080, 0, 0)), "lin")], [], ball=(5, 45))
move("JumpAerialB", "JumpAerialB", 35, [(0, FALL), (4, tuck(-90)), (30, tuck(-630), "lin"), (35, P(FALL, root=(-720, 0, 0)), "lin")], [], ball=(5, 31))
anim(["Fall", "FallAerial"], 8, [(0, FALL), (4, FALL2), (8, FALL)])
anim(["FallF", "FallAerialF"], 8, [(0, P(FALL, root=(10, 0, 0))), (4, P(FALL2, root=(10, 0, 0))), (8, P(FALL, root=(10, 0, 0)))])
anim(["FallB", "FallAerialB"], 8, [(0, P(FALL, root=(-10, 0, 0))), (4, P(FALL2, root=(-10, 0, 0))), (8, P(FALL, root=(-10, 0, 0)))])
anim(["Landing", "LandingAirN", "LandingAirF", "LandingAirB", "LandingAirHi", "LandingAirLw"], 30, [(0, LAND), (6, CROUCH), (30, S)])
BRAKE = P(root=(-22, 0, 0), chest=(10, 0, 0), thighL=(0.1, -1, 0.75), shinL=(0.1, -1, 0.45), thighR=(-0.1, -1, 0.3), shinR=(-0.1, -1, -0.1),
          footL=-25, armL=(1, -0.3, 0.3), foreL=(1, 0.1, 0.5), armR=(-1, -0.3, -0.3), foreR=(-1, 0.1, -0.1))
anim("RunBrake", 28, [(0, BRAKE), (18, P(BRAKE, root=(-16, 0, 0))), (28, S)])

# damage
HURT = P(root=(-22, 0, 0), chest=(-18, 0, 0), head=(-25, 0, 0), armL=(1, 0.3, 0.4), foreL=(0.7, 1, 0.3), armR=(-1, 0.2, 0.3), foreR=(-0.8, 0.8, 0.5),
         thighL=(0.15, -1, 0.5), shinL=(0.1, -1, 0.1), thighR=(-0.15, -1, 0.1), shinR=(-0.1, -1, -0.35))
HURT_HI = P(HURT, root=(-30, 0, 0), head=(-40, 0, 0), chest=(-25, 0, 0))
HURT_LW = P(root=(28, 0, 0), chest=(25, 0, 0), head=(15, 0, 0), armL=(0.5, -0.7, 1), foreL=(-0.2, -0.3, 1), armR=(-0.5, -0.7, 1), foreR=(0.2, -0.3, 1),
            thighL=(0.15, -1, 0.3), shinL=(0.1, -1, -0.4), thighR=(-0.15, -1, 0.1), shinR=(-0.1, -1, -0.6))
for nm, pose in (("N", HURT), ("Hi", HURT_HI), ("Lw", HURT_LW), ("Air", P(HURT, ground=0, thighL=(0.2, -0.6, 1), shinL=(0.1, -1, 0.3)))):
    g = pose["ground"]
    end = S if g else FALL
    for n, T in ((1, 12), (2, 24), (3, 30)):
        anim(f"Damage{nm}{n}", T, [(0, P(end, ground=g)), (3, pose, "out"), (T * 2 // 3, P(pose, root=(pose["root"][0] * 0.6, 0, 0))), (T, P(end, ground=g))])
FLY = P(ground=0, root=(-55, 0, 0), chest=(-15, 0, 0), head=(20, 0, 0), armL=(1, 0.2, 0.9), foreL=(0.5, 0.3, 1), armR=(-1, 0.2, 0.9), foreR=(-0.5, 0.3, 1),
        thighL=(0.3, -0.5, 1), shinL=(0.2, -0.8, 0.8), thighR=(-0.3, -0.7, 1), shinR=(-0.2, -1, 0.5))
FLY2 = P(FLY, armL=(1, 0.4, 0.8), armR=(-1, 0.0, 1), thighL=(0.3, -0.7, 1), thighR=(-0.3, -0.5, 1))
anim(["DamageFlyN", "DamageFlyHi", "DamageFlyLw"], 29, [(0, FLY), (14, FLY2), (29, FLY)])
anim("DamageFlyRoll", 16, [(0, tuck(0)), (16, tuck(-360), "lin")])
TUMBLE = P(FLY, root=(-75, 0, 0), head=(10, 0, 0))
anim("DamageFall", 29, [(0, TUMBLE), (14, P(FLY2, root=(-68, 0, 0), head=(10, 0, 0))), (29, TUMBLE)])

# rolls and air dodge as a ball (the game's own travel is kept)
anim("EscapeF", 32, [(0, S), (5, tuck(60, hip=(0, -5.3, 0))), (26, tuck(780, hip=(0, -5.3, 0)), "lin"), (32, P(S, root=(720, 0, 0)))], keep_root=True)
anim("EscapeB", 32, [(0, S), (5, tuck(-60, hip=(0, -5.3, 0))), (26, tuck(-780, hip=(0, -5.3, 0)), "lin"), (32, P(S, root=(-720, 0, 0)))], keep_root=True)

# ------------------------------------------------------------------ shield (bubble bone 61 is held 8.3 units above the floor: the middle of Sonic)
GUARD = P(root=(8, 0, 0), chest=(8, 0, 0), thighL=(0.25, -1, 0.45), shinL=(0.1, -1, -0.4), thighR=(-0.25, -1, 0.15), shinR=(-0.1, -1, -0.55),
          armL=(0.55, -1, 0.25), foreL=(0.3, -0.6, 1), armR=(-0.55, -1, 0.25), foreR=(-0.3, -0.6, 1))
anim("GuardOn", 8, [(0, S), (8, GUARD, "out")], shield_y=9.4)
anim("Guard", 370, [(0, GUARD), (185, P(GUARD, chest=(15, 0, 0))), (370, GUARD)], shield_y=9.4)
anim("GuardOff", 16, [(0, GUARD), (16, S)], shield_y=9.4)
anim("GuardDamage", 20, [(0, GUARD), (4, P(GUARD, root=(-8, 0, 0), chest=(4, 0, 0)), "out"), (20, GUARD)], shield_y=9.4)

# ------------------------------------------------------------------ ledge hang (hands placed where Falcon's scaled animation had them)
AJ_BASE = r"C:\adventure-melee\work\v10\PlSnAJ_v10r.dat"
HANG0 = P(ground=0, root=(-6, 0, 0), head=(-30, 0, 0), armL=(0.22, 1, 0.25), foreL=(0.1, 1, 0.2), armR=(-0.22, 1, 0.25), foreR=(-0.1, 1, 0.2),
          thighL=(0.1, -1, 0.12), shinL=(0.07, -1, -0.25), thighR=(-0.1, -1, -0.05), shinR=(-0.07, -1, -0.4), footL=45, footR=45)
_target = np.mean(orig_bone_pos(AJ_BASE, "CliffWait1", 0, (25, 47)), axis=0)
_w = solve(HANG0)[0]
_hands = (_w[25][:3, 3] + _w[47][:3, 3]) / 2
HANG = P(HANG0, hip=tuple(_target - _hands))
SWING = P(HANG, thighL=(0.1, -1, 0.3), thighR=(-0.1, -1, 0.15), shinL=(0.07, -1, -0.1), shinR=(-0.07, -1, -0.25))

HANGP = P(ground=0, head=(-30, 0, 0), armL=(0.22, 1, 0.2), foreL=(0.1, 1, 0.15), armR=(-0.22, 1, 0.2), foreR=(-0.1, 1, 0.15),
          thighL=(0.1, -1, 0.12), shinL=(0.07, -1, -0.25), thighR=(-0.1, -1, -0.05), shinR=(-0.07, -1, -0.4), footL=45, footR=45)
HANGS = P(HANGP, thighL=(0.1, -1, 0.3), thighR=(-0.1, -1, 0.15), shinL=(0.07, -1, -0.1), shinR=(-0.07, -1, -0.25))
anim("CliffCatch", 8, [(0, HANGS), (8, HANGP)], keep=(1, 2, 3))
anim("CliffWait1", 50, [(0, HANGP), (25, HANGS), (50, HANGP)], keep=(1, 2, 3))
anim("CliffWait2", 56, [(0, HANGP), (14, HANGS), (28, HANGP), (42, P(HANGP, head=(-10, 40, 0))), (56, HANGP)], keep=(1, 2, 3))

# ------------------------------------------------------------------ grab and throws (Falcon's scripts and timings; hit/release frames unchanged)
REACH = P(root=(22, 0, 0), chest=(10, 0, 0), head=(-20, 0, 0), armL=(0.3, 0.0, 1), foreL=(0.1, 0.05, 1), armR=(-0.3, 0.0, 1), foreR=(-0.1, 0.05, 1),
          thighL=(0.15, -1, 0.6), shinL=(0.1, -1, -0.2), thighR=(-0.15, -1, -0.3), shinR=(-0.1, -1, -0.6))
HOLD = P(root=(6, 0, 0), chest=(6, 0, 0), armL=(0.4, -0.25, 1), foreL=(-0.15, 0.25, 1), armR=(-0.4, -0.25, 1), foreR=(0.15, 0.25, 1))
anim("Catch", 30, [(0, S), (5, REACH, "out"), (9, REACH), (30, S)])
anim("CatchDash", 40, [(0, P(S, root=(20, 0, 0))), (9, P(REACH, root=(32, 0, 0)), "out"), (14, REACH), (40, S)], keep_root=True)
anim("CatchWait", 30, [(0, HOLD), (15, P(HOLD, chest=(9, 0, 0))), (30, HOLD)])
anim("CatchAttack", 24, [(0, HOLD), (3, P(HOLD, root=(-8, 0, 0), thighR=(-0.1, 0.35, 1), shinR=(-0.05, -1, 0.35)), "out"), (7, P(HOLD, root=(-8, 0, 0), thighR=(-0.1, 0.35, 1), shinR=(-0.05, -1, 0.35))), (24, HOLD)])
anim("CatchCut", 30, [(0, HOLD), (6, P(HURT, root=(-14, 0, 0))), (30, S)], keep_root=True)
PUNCH_L = P(S, root=(8, 0, 0), chest=(10, -40, 0), armL=(0.05, 0.1, 1), foreL=(-0.05, 0.1, 1), armR=(-0.5, -0.7, -0.6), foreR=(-0.4, -0.2, 0.7))
anim("ThrowF", 40, [(0, HOLD), (6, P(HOLD, chest=(0, 45, 0), armL=(0.6, -0.4, -0.5), foreL=(0.4, 0.2, 0.6)), "io"), (10, PUNCH_L, "out"), (18, PUNCH_L), (40, S)], keep_root=True)
TB = P(S, root=(0, 95, -28), chest=(0, -10, 10), head=(0, -35, 10), thighL=(1, 0.06, 0), shinL=(1, 0.1, 0), footL=-5,
       thighR=(-0.15, -1, 0.1), shinR=(-0.1, -1, -0.25), armL=(1, -0.5, 0.2), foreL=(1, -0.3, 0.1), armR=(-0.7, -0.2, 0.6), foreR=(-0.2, 0.6, 0.7))
anim("ThrowB", 50, [(0, HOLD), (7, P(HOLD, root=(0, 60, 0))), (11, TB, "out"), (20, P(TB, root=(0, 95, -24))), (32, P(S, root=(0, 60, 0))), (50, S)], keep_root=True)
UPPER = P(S, root=(-8, 0, 0), chest=(-8, -30, 0), head=(-20, 0, 0), armL=(0.1, 1, 0.4), foreL=(0.0, 1, 0.2), armR=(-0.6, -0.8, -0.3), foreR=(-0.5, -0.4, 0.5))
anim("ThrowHi", 44, [(0, HOLD), (6, P(CROUCH, armL=(0.4, -1, 0.5), foreL=(0.1, -0.5, 1))), (10, UPPER, "out"), (16, UPPER), (29, P(UPPER, root=(-4, 0, 0))), (44, S)], keep_root=True)
SLAM_UP = P(S, root=(-12, 0, 0), chest=(-10, 0, 0), armL=(0.3, 1, 0.3), foreL=(0.1, 1, 0.1), armR=(-0.3, 1, 0.3), foreR=(-0.1, 1, 0.1))
SLAM_DN = P(CROUCH, root=(30, 0, 0), chest=(25, 0, 0), armL=(0.3, -0.8, 1), foreL=(0.1, -1, 0.6), armR=(-0.3, -0.8, 1), foreR=(-0.1, -1, 0.6))
anim("ThrowLw", 40, [(0, HOLD), (8, SLAM_UP), (13, SLAM_DN, "in"), (20, SLAM_DN), (40, S)], keep_root=True)


# ------------------------------------------------------------------ taunt: the finger wag (Sonic 1 title screen / Sonic CD / SA1)
WAG0 = P(S, root=(0, -70, 0), chest=(0, -10, 0), head=(-5, -15, 0), armR=(-0.5, -0.4, 0.6), foreR=(-0.1, 1, 0.3), armL=(0.7, -1, -0.1), foreL=(0.2, -0.5, 0.8))
WAG1 = P(WAG0, foreR=(-0.5, 1, 0.3))
WAG2 = P(WAG0, foreR=(0.3, 1, 0.3))
_wag = [(0, S), (10, WAG0), (18, WAG1), (26, WAG2), (34, WAG1), (42, WAG2), (50, WAG0), (60, S)]
anim("AppealR", 60, _wag)
anim("AppealL", 60, [(f, mirror(p_) if p_ is not S else S) for f, p_ in _wag])

# ------------------------------------------------------------------ classic references (Sonic 1 - SA2 only)
# crouch: the Sonic 1 duck. Sits right down on his heels, knees up, curled over them with the head tucked in.
# v56 crouch, after the user's reference picture: sits low on his heels, curled forward with his head bowed toward his knees
# and his right glove over the top of his head; left arm round his shins. The glove is placed with reach() on the head surface.
_DB = P(root=(15, 0, 0), chest=(48, 0, 0), head=(40, 0, 0), footL=-5, footR=-5,
        thighL=(0.22, 0.25, 1), shinL=(0.06, -1, -0.5), thighR=(-0.22, 0.2, 1), shinR=(-0.06, -1, -0.55),
        armL=(0.45, -0.8, 0.8), foreL=(-0.1, -0.5, 1))
DUCK = reach(_DB, "R", head_point(_DB, (-0.6, 0.7, 0.6), 0.9), pole=(-1, 0.3, -0.5))
anim("Squat", 8, [(0, S), (8, DUCK, "out")])
anim("SquatWait", 158, [(0, DUCK), (79, P(DUCK, chest=(53, 0, 0))), (158, DUCK)])
anim("SquatRv", 10, [(0, DUCK), (10, S)])
# idle 3: the impatient foot tap, hands on hips, looking out at the player (Sonic 1/2/3)
TAP = P(S, root=(0, -72, 0), chest=(-4, 0, 0), head=(-4, -12, 0), armL=(0.9, -1, -0.2), foreL=(-0.7, -0.5, 0.4), armR=(-0.9, -1, -0.2), foreR=(0.7, -0.5, 0.4),
        thighL=(0.12, -1, 0.02), shinL=(0.08, -1, -0.05), thighR=(-0.25, -1, 0.3), shinR=(-0.1, -1, 0.0), footR=-30)
TAP2 = P(TAP, footR=0)
anim("Wait3", 64, [(0, S), (10, TAP), (16, TAP2), (22, TAP), (28, TAP2), (34, TAP), (40, TAP2), (46, TAP), (52, TAP2), (64, S)])
# teetering on an edge, arms windmilling (Sonic 1/2/3)
TEE1 = P(S, root=(22, 0, 0), chest=(8, 0, 0), head=(-15, 0, 0), armL=(0.5, 0.9, 0.5), foreL=(0.3, 1, 0.6), armR=(-0.7, -0.6, -0.8), foreR=(-0.6, -0.2, -1),
         thighL=(0.12, -1, -0.15), shinL=(0.08, -1, -0.3), thighR=(-0.12, -1, -0.2), shinR=(-0.08, -1, -0.35), footL=-20, footR=-20)
TEE2 = P(TEE1, root=(14, 0, 0), armL=(0.7, -0.6, -0.8), foreL=(0.6, -0.2, -1), armR=(-0.5, 0.9, 0.5), foreR=(-0.3, 1, 0.6))
anim("Ottotto", 8, [(0, S), (8, TEE1, "out")])
anim("OttottoWait", 80, [(0, TEE1), (10, TEE2), (20, TEE1), (30, TEE2), (40, TEE1), (50, TEE2), (60, TEE1), (70, TEE2), (80, TEE1)])
# launched straight up: the classic "ouch" pose, facing the player with arms and legs flung out (Sonic 1 hit/death sprite)
OUCH = P(ground=0, root=(-10, -80, 0), chest=(-10, 0, 0), head=(-20, 0, 0), armL=(1, 0.8, 0), foreL=(0.8, 1, 0.1), armR=(-1, 0.8, 0), foreR=(-0.8, 1, 0.1),
         thighL=(0.7, -1, 0.1), shinL=(0.5, -1, -0.3), thighR=(-0.7, -1, 0.1), shinR=(-0.5, -1, -0.3), footL=20, footR=20)
anim("DamageFlyTop", 60, [(0, OUCH), (30, P(OUCH, root=(-4, -80, 6))), (60, OUCH)])
# helpless fall after the Light Speed Dash: the spring-jump pose, arms straight up (classic spring bounce)
SPRING = P(ground=0, root=(4, 0, 0), head=(-20, 0, 0), armL=(0.25, 1, 0.05), foreL=(0.15, 1, 0.05), armR=(-0.25, 1, 0.05), foreR=(-0.15, 1, 0.05),
           thighL=(0.1, -1, 0.15), shinL=(0.07, -1, -0.15), thighR=(-0.1, -1, -0.05), shinR=(-0.07, -1, -0.35), footL=45, footR=45)
anim(["FallSpecial", "FallSpecialF", "FallSpecialB"], 8, [(0, SPRING), (4, P(SPRING, thighL=(0.1, -1, 0.22), thighR=(-0.1, -1, -0.12))), (8, SPRING)])

# ------------------------------------------------------------------ ground attacks
J1 = P(S, chest=(8, -30, 0), armL=(0.05, 0.05, 1), foreL=(-0.05, 0.05, 1), armR=(-0.5, -0.8, -0.5), foreR=(-0.4, -0.3, 0.8))
move("Jab1", "Attack11", 16, [(0, S), (2, J1, "out"), (5, J1), (16, S)],
     [(3, 4, [Hit(0, 25, 3, 2.2, 80, 0, 100, off=(0.5, 0, 0), wdsk=18, tpl="punch"), Hit(1, 24, 3, 1.8, 80, 0, 100, off=(1.2, 0, 0), wdsk=18, tpl="punch")])],
     jab=(5, 11), iasa=14)
J2 = P(S, chest=(8, 35, 0), armR=(-0.05, 0.05, 1), foreR=(0.05, 0.05, 1), armL=(0.5, -0.8, -0.6), foreL=(0.4, -0.3, 0.6))
move("Jab2", "Attack12", 18, [(0, J1), (2, J2, "out"), (6, J2), (18, S)],
     [(3, 5, [Hit(0, 47, 3, 2.3, 75, 0, 100, off=(0.5, 0, 0), wdsk=20, tpl="punch"), Hit(1, 46, 3, 1.8, 75, 0, 100, off=(1.2, 0, 0), wdsk=20, tpl="punch")])],
     jab=(6, 12), iasa=16)
# side kick: the body turns so the chest faces the camera, leans away, and the left leg shoots out sideways (sole first)
K_CH = P(S, root=(0, -60, 10), chest=(0, 15, 0), thighL=(0.9, 0.5, 0.2), shinL=(0.2, -1, 0.1), thighR=(-0.15, -1, 0.1), shinR=(-0.1, -1, -0.25),
         armL=(0.7, -0.4, 0.6), foreL=(0.2, 0.4, 0.9), armR=(-0.6, -0.5, 0.5), foreR=(-0.1, 0.5, 0.8))
K_EX = P(K_CH, root=(0, -85, 28), chest=(0, 10, -10), head=(0, 35, -10), thighL=(1, 0.06, 0), shinL=(1, 0.1, 0), footL=-5,
         armL=(1, -0.5, 0.2), foreL=(1, -0.3, 0.1), armR=(-0.7, -0.2, 0.6), foreR=(-0.2, 0.6, 0.7))
move("Jab3", "Attack13", 28, [(0, J2), (3, K_CH), (5, K_EX, "out"), (9, K_EX), (14, K_CH), (28, S)],
     [(6, 8, leg("L", 5, 361, 30, 90, size=2.4, shin_dmg=4))], iasa=24)

move("DashAttack", "AttackDash", 38,
     [(0, P(S, root=(20, 0, 0))), (4, tuck(90, hip=(0, -7.1, 0), move=6)), (16, tuck(810, hip=(0, -7.1, 0), move=30), "lin"),
      (23, P(CROUCH, root=(735, 0, 0), move=35), "out"), (38, P(S, root=(720, 0, 0), move=36))],
     [(6, 9, [ball(9, 60, 40, 70)]), (10, 16, [ball(6, 70, 20, 50, size=4.0)])], iasa=36, ball=(5, 18))

# Chaos Emerald thrust poses (SA1/SA2), used by the forward smash. He pulls an emerald back and jabs it out at arm's length; the hit is on the gem,
# beyond his hand, so his arm cannot be hit there (disjoint).
import json as _json
EM_C = tuple(_json.load(open('C:/adventure-melee/work/v19/emerald.json'))['centre'])   # gem centre in right-hand bone space (from the model builder)
EM_W = P(S, root=(4, 0, 0), chest=(4, -55, 0), head=(0, 30, 0), armR=(-0.5, -0.3, -0.9), foreR=(-0.3, 0.2, 0.6), armL=(0.5, -0.4, 0.9), foreL=(0.1, 0.3, 1))
EM_T = P(S, root=(12, 0, 0), chest=(8, 40, 0), head=(-8, -25, 0), armR=(-0.05, 0.08, 1), foreR=(0.0, 0.08, 1), armL=(0.6, -0.7, -0.6), foreL=(0.5, -0.2, 0.4),
         thighL=(0.12, -1, 0.75), shinL=(0.08, -1, -0.1), thighR=(-0.12, -1, -0.45), shinR=(-0.08, -1, -0.6))
def boom(far, t0, t_peak, t_back, spin=45):
    """Emerald flight for the prop bone: in the hand until frame t0, out to `far` (fighter space) by t_peak, back in the hand by t_back."""
    far = np.array(far, dtype=float)

    def f_(f, W):
        hand = (W[47] @ np.array([*EM_C, 1.0]))[:3]
        if f <= t0 or f >= t_back:
            return hand, 0
        if f <= t_peak:
            t = (f - t0) / float(t_peak - t0)
            t = 1 - (1 - t) ** 2
        else:
            t = 1 - (f - t_peak) / float(t_back - t_peak)
            t = t * t * (3 - 2 * t)
        return hand + (far - hand) * t, (f - t0) * spin
    return f_


# forward tilt (v54): Chaos Emerald boomerang, moved here from the down tilt. A quick underhand flick from standing; the gem
# spins out 17 units at waist height and comes back. It is a hitbox carried by the move, not a separate projectile.
BT_W = P(S, chest=(0, -50, 0), head=(0, 30, 0), armR=(-0.6, -0.5, -0.7), foreR=(-0.4, -0.2, 0.5), armL=(0.5, -0.5, 0.8), foreL=(0.2, 0.2, 1))
BT_T = P(S, root=(14, 0, 0), chest=(10, 40, 0), head=(-10, -25, 0), armR=(-0.1, -0.35, 1), foreR=(0.0, -0.3, 1), armL=(0.6, -0.7, -0.6), foreL=(0.5, -0.2, 0.4),
         thighL=(0.12, -1, 0.6), shinL=(0.08, -1, -0.1), thighR=(-0.12, -1, -0.4), shinR=(-0.08, -1, -0.5))
BT_C = P(S, root=(6, 0, 0), chest=(6, 15, 0), armR=(-0.2, -0.4, 1), foreR=(-0.1, 0.0, 1))
move("ForwardTilt", ["AttackS3Hi", "AttackS3HiS", "AttackS3S", "AttackS3LwS", "AttackS3Lw"], 32,
     [(0, S), (3, BT_W), (6, BT_T, "out"), (13, BT_T), (25, BT_C), (32, S)],
     [(6, 13, [Hit(0, 62, 8, 2.2, 70, 25, 60)]), (14, 25, [Hit(1, 62, 5, 2.0, 80, 15, 50)])], iasa=29, emerald=(5, 27),
     prop=boom((0.0, 5.5, 17.0), 5, 13, 25))


UTF = dict(ground=0, pivot=(0, 2.0, 0), thighL=(0.12, -1, 0.3), shinL=(0.08, -1, 0.12), thighR=(-0.12, -1, 0.3), shinR=(-0.08, -1, 0.12), footL=40, footR=40,
           armL=(1, -0.3, 0.2), foreL=(1, 0.1, 0.3), armR=(-1, -0.3, 0.2), foreR=(-1, 0.1, 0.3))
move("UpTilt", "AttackHi3", 28,
     [(0, S), (3, P(CROUCH, root=(-5, 0, 0))), (5, P(S, root=(-80, 0, 0), hip=(0, 1.5, 0), **UTF), "in"), (10, P(S, root=(-225, 0, 0), hip=(0, 3.0, 0), **UTF), "lin"),
      (15, tuck(-320, pivot=(0, 2.0, 0), hip=(0, 1.5, 0)), "lin"), (20, P(LAND, root=(-360, 0, 0)), "lin"), (28, P(S, root=(-360, 0, 0)))],
     [(6, 10, [Hit(0, 16, 8, 2.6, 92, 35, 95, off=(1.6, 0, 0)), Hit(1, 10, 8, 2.6, 92, 35, 95, off=(1.6, 0, 0)), Hit(2, 14, 7, 2.0, 92, 35, 95, off=(2.4, 0, 0))])], iasa=24)

# down tilt (v54): Somersault (SA2). From the duck he rolls forward along the floor as a ball (7 units), then pops a low kick
# out of the roll that launches upward for combos.
SOM_K = P(DUCK, root=(366, 0, 0), chest=(35, 0, 0), thighR=(-0.2, -0.05, 1), shinR=(-0.15, 0.0, 1), footR=-20, move=7.5)
move("DownTilt", "AttackLw3", 26,
     [(0, DUCK), (3, tuck(45, hip=(0, -7.1, 0), move=1.0)), (10, tuck(360, hip=(0, -7.1, 0), move=7.0), "lin"), (12, SOM_K, "out"), (15, SOM_K),
      (20, P(DUCK, root=(366, 0, 0), move=7.5)), (26, P(DUCK, root=(366, 0, 0), move=7.5))],
     [(4, 10, [ball(4, 60, 0, 100, size=4.0, wdsk=22)]), (12, 14, leg("R", 5, 85, 40, 70, size=2.6, shin_dmg=5))], iasa=23, ball=(3, 11))


# forward smash: Chaos Emerald thrust (swapped with the forward tilt in v47). v49: the wind-up peaks on the charge frame (7) with
# the gem raised back over his shoulder, then he steps in and drives it out at chest height. Chargeable; the gem is the strong hit.
EM_W1 = P(S, root=(-6, 0, 0), chest=(-4, -40, 0), head=(0, 25, 0), armR=(-0.55, 0.1, -0.85), foreR=(-0.3, 0.6, -0.5),
          armL=(0.5, -0.5, 0.8), foreL=(0.2, 0.2, 1), thighL=(0.12, -1, 0.3), shinL=(0.08, -1, -0.2), thighR=(-0.12, -1, -0.15), shinR=(-0.08, -1, -0.4))
EM_W2 = P(EM_W1, root=(-12, 0, 0), chest=(-10, -75, 0), head=(-5, 45, 0), armR=(-0.45, 0.55, -0.75), foreR=(-0.2, 0.9, -0.3),
          armL=(0.7, -0.2, 0.7), foreL=(0.4, 0.4, 0.9), thighL=(0.15, -1, 0.45), shinL=(0.08, -1, -0.35), thighR=(-0.15, -1, -0.25), shinR=(-0.08, -1, -0.55))
EM_T2 = P(EM_T, root=(24, 0, 0), chest=(10, 45, 0), head=(-15, -30, 0), move=3.5, thighL=(0.12, -1, 0.9), shinL=(0.08, -1, 0.05),
          thighR=(-0.12, -1, -0.65), shinR=(-0.08, -1, -0.55), footR=20)
EM_F = P(EM_T2, root=(16, 0, 0), chest=(6, 30, 0), armR=(-0.1, -0.25, 1), foreR=(-0.05, -0.3, 1))
_emhand = lambda f, W: ((W[47] @ np.array([*EM_C, 1.0]))[:3], 0)   # noqa: E731


# v54: the forward smash is a full boomerang throw. Same wind-up (charge on frame 7); on frame 15 the gem leaves his hand,
# spins out 24 units at chest height by frame 24 and is back in his hand by frame 38. Strong on the way out, weak on the way back.
FS_C = P(EM_F, root=(8, 0, 0), chest=(4, 20, 0), armR=(-0.2, -0.3, 1), foreR=(-0.1, 0.05, 1))
move("ForwardSmash", ["AttackS4Hi", "AttackS4S", "AttackS4Lw"], 50,
     [(0, S), (4, EM_W1, "out"), (7, EM_W2), (12, P(EM_W2, chest=(-12, -80, 0))), (14, P(EM_T2, move=2.0), "in"), (16, EM_T2, "out"),
      (22, EM_F), (38, FS_C), (50, P(S, move=3.5))],
     [(15, 24, [Hit(0, 62, 17, 2.8, 361, 35, 100)]), (25, 38, [Hit(1, 62, 8, 2.4, 361, 20, 70)])], charge=7, iasa=46, emerald=(3, 40),
     prop=boom((0.0, 7.0, 27.0), 14, 24, 38, spin=50))

# up smash: the ball spins on the spot for the four weak hits (so they keep connecting), then leaps for the last one
move("UpSmash", "AttackHi4", 48,
     [(0, S), (5, CROUCH), (8, tuck(120, hip=(0, -7.1, 0))), (18, tuck(620, hip=(0, -7.1, 0)), "lin"), (22, tuck(800, hip=(0, 3.5, 0)), "out"),
      (29, P(LAND, root=(1088, 0, 0)), "lin"), (48, P(S, root=(1080, 0, 0)))],
     [(8, 9, [ball(2, 90, 0, 100, wdsk=14)]), (11, 12, [ball(2, 90, 0, 100, wdsk=14)]), (14, 15, [ball(2, 90, 0, 100, wdsk=14)]),
      (17, 18, [ball(2, 90, 0, 100, wdsk=14)]), (20, 22, [ball(5, 88, 45, 110, size=5.6)])], charge=6, iasa=44, ball=(9, 24))


SPLIT = P(root=(0, 0, 0), chest=(25, 0, 0), head=(-20, 0, 0), thighL=(0.05, -0.16, 1), shinL=(0.05, -0.1, 1), thighR=(-0.05, -0.16, -1), shinR=(-0.05, -0.1, -1),
          footL=-15, footR=40, armL=(0.6, -1, 0.3), foreL=(0.3, -1, 0.2), armR=(-0.6, -1, 0.3), foreR=(-0.3, -1, 0.2))
move("DownSmash", "AttackLw4", 44, [(0, S), (4, CROUCH), (7, SPLIT, "out"), (10, SPLIT), (18, CROUCH), (44, S)],
     [(8, 10, [Hit(0, 10, 13, 2.6, 30, 30, 90, off=(1.6, 0, 0)), Hit(1, 8, 12, 2.0, 30, 30, 90, off=(2.4, 0, 0)),
               Hit(2, 16, 11, 2.6, 30, 30, 90, off=(1.6, 0, 0)), Hit(3, 14, 10, 2.0, 30, 30, 90, off=(2.4, 0, 0))])], charge=5, iasa=40)

# ------------------------------------------------------------------ aerials
move("NeutralAir", "AttackAirN", 39, [(0, FALL), (3, tuck(60)), (27, tuck(780), "lin"), (33, P(FALL, root=(720, 0, 0)), "lin"), (39, P(FALL, root=(720, 0, 0)))],
     [(4, 9, [ball(9, 361, 15, 95, size=5.8)]), (10, 27, [ball(5, 361, 10, 80, size=4.1)])], aerial=(3, 30), iasa=36, ball=(4, 29), insta=(4, 10))   # early hit = Insta-Shield (Sonic 3): wider for 6 frames

AX_W = P(TUCK, root=(-25, 0, 0), pivot=(0, 1.5, 0), armL=(0.8, 0.6, 0.3), foreL=(0.5, 1, 0.3), armR=(-0.8, 0.6, 0.3), foreR=(-0.5, 1, 0.3))
AX_UP = P(ground=0, pivot=(0, 1.5, 0), root=(-38, 0, 0), chest=(-10, 0, 0), head=(20, 0, 0), thighR=(0, 1, 0.45), shinR=(0, 1, 0.4), footR=25,
          thighL=(0.2, -0.2, 1), shinL=(0.1, -1, 0.1), footL=20,
          armL=(0.7, 0.8, 0.2), foreL=(0.4, 1, 0.2), armR=(-0.7, 0.8, 0.2), foreR=(-0.4, 1, 0.2))
AX_MID = P(AX_UP, root=(10, 0, 0), chest=(8, 0, 0), thighR=(0, 0.25, 1), shinR=(0, 0.3, 1), footR=-10,
           armL=(1, -0.2, -0.4), foreL=(1, -0.4, -0.6), armR=(-1, -0.2, -0.4), foreR=(-1, -0.4, -0.6))
AX_DN = P(AX_MID, root=(48, 0, 0), chest=(15, 0, 0), head=(-20, 0, 0), thighR=(0, -0.8, 1), shinR=(0, -0.9, 1), footR=-25,
          thighL=(0.2, -1, -0.5), shinL=(0.1, -0.6, -1), armL=(0.8, -0.3, -1), foreL=(0.7, -0.2, -1), armR=(-0.8, -0.3, -1), foreR=(-0.7, -0.2, -1))
move("ForwardAir", "AttackAirF", 42,
     [(0, FALL), (5, AX_W), (10, AX_UP, "out"), (13, AX_MID, "in"), (16, AX_DN, "out"),
      (23, P(AX_DN, root=(40, 0, 0), thighR=(0, -1, 0.5), shinR=(0, -1, 0.3))), (32, P(TUCK, root=(20, 0, 0), pivot=(0, 1.5, 0))), (42, FALL)],
     [(11, 13, [Hit(0, 16, 7, 2.3, 361, 25, 85, off=(1.6, 0, 0)), Hit(1, 14, 7, 2.0, 361, 25, 85, off=(2.4, 0, 0))]),
      (14, 17, [Hit(0, 16, 12, 2.6, 270, 20, 90, off=(1.2, -0.5, 0)), Hit(1, 14, 7, 1.6, 361, 25, 85, off=(1.2, 0, 0))])], aerial=(3, 30), iasa=38)

BK_T = P(FALL, root=(0, -50, -8), thighR=(-0.9, 0.5, 0.2), shinR=(-0.2, -1, 0.1), thighL=(0.2, -0.3, 1), shinL=(0.1, -1, 0.1))
BK = P(BK_T, root=(0, -100, -30), chest=(0, -10, 10), head=(0, -30, 10), thighR=(-1, 0.06, 0), shinR=(-1, 0.1, 0), footR=-5,
       thighL=(0.25, -0.5, 1), shinL=(0.1, -1, -0.2), armR=(-1, -0.5, 0.2), foreR=(-1, -0.3, 0.1), armL=(0.7, -0.2, 0.6), foreL=(0.2, 0.6, 0.7))
move("BackAir", "AttackAirB", 34, [(0, FALL), (2, BK_T), (4, BK, "out"), (11, P(BK, root=(0, -100, -24))), (18, BK_T), (34, FALL)],
     [(5, 7, leg("R", 12, 361, 20, 98, size=2.7, shin_dmg=10)), (8, 11, leg("R", 8, 361, 10, 90, size=2.4, shin_dmg=7))], aerial=(3, 24), iasa=30)


FLIP = dict(pivot=(0, 2.0, 0), thighL=(0.12, -1, 0.25), shinL=(0.08, -1, 0.1), thighR=(-0.12, -1, 0.25), shinR=(-0.08, -1, 0.1), footL=35, footR=35,
            armL=(1, -0.2, 0.2), foreL=(1, 0.2, 0.3), armR=(-1, -0.2, 0.2), foreR=(-1, 0.2, 0.3))
move("UpAir", "AttackAirHi", 30,
     [(0, FALL), (4, P(FALL, root=(-70, 0, 0), **FLIP), "in"), (9, P(FALL, root=(-215, 0, 0), **FLIP), "lin"), (15, tuck(-320, pivot=(0, 2.0, 0)), "lin"),
      (30, P(FALL, root=(-360, 0, 0)))],
     [(5, 7, [Hit(0, 16, 10, 2.5, 80, 20, 95, off=(1.6, 0, 0)), Hit(1, 10, 10, 2.5, 80, 20, 95, off=(1.6, 0, 0))]),
      (8, 10, [Hit(0, 16, 8, 2.3, 70, 15, 90, off=(1.6, 0, 0)), Hit(1, 10, 8, 2.3, 70, 15, 90, off=(1.6, 0, 0))])], aerial=(3, 22), iasa=28)

DRILL = P(ground=0, chest=(0, 0, 0), head=(15, 0, 0), footL=70, footR=70,
          thighR=(-0.07, -1, 0.03), shinR=(-0.05, -1, 0.0), thighL=(0.07, -1, 0.03), shinL=(0.05, -1, 0.0),
          armL=(0.3, 1, 0.05), foreL=(-0.2, 1, 0), armR=(-0.3, 1, 0.05), foreR=(0.2, 1, 0))
dh = lambda: leg("R", 2, 290, 0, 100, size=2.6, wdsk=25)  # noqa: E731
move("DownAir", "AttackAirLw", 44,
     [(0, FALL), (3, tuck(20)), (5, DRILL, "out"), (12, P(DRILL, hip=(0, -0.6, 0))), (19, DRILL), (26, P(DRILL, hip=(0, -0.6, 0))), (32, FALL), (44, FALL)],
     [(6, 7, dh()), (10, 11, dh()), (14, 15, dh()), (18, 19, dh()), (22, 23, dh()), (24, 26, leg("R", 3, 361, 30, 100, size=2.8))], aerial=(3, 34), iasa=40)

# ------------------------------------------------------------------ specials (states and movement are in fighter_code/sonic.c)
RISE = P(ground=0, pivot=(0, 2.0, 0), root=(6, 0, 0), chest=(-6, 0, 0), head=(-28, 0, 0), footL=65, footR=65,
         armR=(-0.12, 1, 0.12), foreR=(-0.04, 1, 0.06), armL=(0.45, -1, -0.3), foreL=(0.3, -1, -0.45),
         thighL=(0.07, -1, 0.0), shinL=(0.05, -1, -0.1), thighR=(-0.07, -1, -0.12), shinR=(-0.05, -1, -0.3))
FLY = P(ground=0, pivot=(0, 2.0, 0), root=(80, 0, 0), chest=(-12, 0, 0), head=(-55, 0, 0), footL=65, footR=65,
        armL=(0.45, -1, -0.25), foreL=(0.3, -1, -0.35), armR=(-0.45, -1, -0.25), foreR=(-0.3, -1, -0.35),
        thighL=(0.07, -1, -0.05), shinL=(0.05, -1, -0.12), thighR=(-0.07, -1, -0.12), shinR=(-0.05, -1, -0.25))
GB = dict(hip=(0, -7.1, 0))
move("HomingAttack", ["SpecialAirN", "SpecialN"], 40, [(0, FALL), (3, tuck(90)), (40, tuck(1200), "lin")],
     [(1, 40, [ball(8, 60, 40, 70)])], ball=(3, 0))
move("SpinDashCharge", "SpecialSStart", 190, [(0, S), (6, tuck(60, **GB)), (190, tuck(60 + 184 * 40, **GB), "lin")], [], ball=(7, 0))
move("SpinDash", "SpecialS", 40, [(0, tuck(0, **GB)), (4, tuck(128, hip=(0, -4.8, 0)), "out"), (9, tuck(288, **GB), "in"), (30, tuck(960, **GB), "lin"), (36, P(CROUCH, root=(1080, 0, 0)), "lin"), (40, P(S, root=(1080, 0, 0)))],
     [(1, 32, [ball(10, 50, 35, 75)])], ball=(1, 31))
# up B, v54: Super Peel-Out (Sonic CD). He revs in place for 8 frames with his feet blurred into the red figure-8 (model part
# 24), then shoots off still running on it: upright when rising, leaning hard when going sideways. No ball, no corkscrew.
RUN_A = dict(thighL=(0.08, -0.7, 0.75), shinL=(0.08, -0.95, -0.3), footL=-10, thighR=(-0.08, -0.75, -0.65), shinR=(-0.08, -0.25, -1), footR=40)
RUN_B = dict(thighR=(-0.08, -0.7, 0.75), shinR=(-0.08, -0.95, -0.3), footR=-10, thighL=(0.08, -0.75, -0.65), shinL=(0.08, -0.25, -1), footL=40)
PEEL_REV = P(S, ground=0, root=(28, 0, 0), chest=(-8, 0, 0), head=(-22, 0, 0), armL=(0.5, -0.5, -0.8), foreL=(0.35, -0.2, -0.9),
             armR=(-0.5, -0.5, -0.8), foreR=(-0.35, -0.2, -0.9))
PEEL_UP = P(PEEL_REV, root=(8, 0, 0), head=(-32, 0, 0))
PEEL_SIDE = P(PEEL_REV, root=(40, 0, 0), head=(-36, 0, 0))


def peel_keys(fly):
    ks = []
    for f in range(0, 27):
        base = PEEL_REV if f < 8 else fly
        if f in (8, 9):      # ease from the rev lean into the flight lean
            base = lerp_pose(PEEL_REV, fly, (f - 7) / 3.0)
        ks.append((f, P(base, **(RUN_A if (f // 2) % 2 == 0 else RUN_B)), "lin"))   # legs swap every 2 frames: a blur
    return ks + [(32, SPRING)]


def f8prop(f, W):
    """figure-8 under the feet: follows the hips and leans with the body."""
    R = W[2][:3, :3]
    return W[2][:3, 3] + R @ np.array([0.0, -9.0, 0.3]), 0, math.degrees(math.atan2(R[2, 1], R[1, 1]))


LSD_HIT = [(9, 29, [Hit(0, 2, 6, 3.8, 70, 30, 60, off=(0, 1.5, 0))])]   # v57: f9-22 -> f9-29, the whole dash (it ends at f30)
move("PeelOutUp", "SpecialAirHi", 32, peel_keys(PEEL_UP), LSD_HIT)
move("PeelOutSide", "SpecialHi", 32, peel_keys(PEEL_SIDE), LSD_HIT)
LD_READY = P(S, root=(-10, 0, 0), chest=(-6, 20, 0), thighL=(0.12, -1, 0.5), shinL=(0.08, -1, 0.1), thighR=(-0.12, -1, -0.5), shinR=(-0.08, -1, -0.5),
             armL=(0.7, -0.6, 0.6), foreL=(0.2, 0.5, 0.8), armR=(-0.7, -0.7, -0.6), foreR=(-0.6, -0.3, -0.7), ground=0.0)
move("LightDashCharge", "SpecialAirSStart", 80, [(0, S), (6, LD_READY), (18, P(LD_READY, root=(-16, 0, 0))), (80, P(LD_READY, root=(-16, 0, 0)))], [])
move("LightDash", "SpecialAirS", 45, [(0, P(FLY, root=(60, 0, 0))), (2, FLY, "out"), (14, P(FLY, root=(84, 0, 0))), (22, P(BRAKE, ground=0.0)), (45, P(S, ground=0.0))],
     [(1, 4, [Hit(0, 2, 16, 3.6, 361, 40, 100, off=(0, 1.5, 1.5))]), (5, 14, [Hit(0, 2, 5, 3.2, 361, 20, 60, off=(0, 1.5, 1.0))])], trail=(1, 17),
     prop=lambda f, W: ((W[2][0, 3], W[2][1, 3] + 1.2, W[2][2, 3] - 1.0), 0))
move("BounceAttack", "SpecialAirLw", 60, [(0, FALL), (4, tuck(90)), (60, tuck(1770), "lin")],
     [(3, 60, [ball(9, 70, 30, 80)])], ball=(5, 0))


def special_edit(name, log):
    """In-place style edits to Falcon's special hitboxes (fire removed, ball-centred, damage for Sonic)."""
    DMG = {"SpecialN": {27: 13, 25: 13, 23: 13}, "SpecialAirN": {27: 13, 25: 13, 23: 13},
           "SpecialLw": {15: 10, 12: 8, 9: 6}, "SpecialAirLw": {15: 10, 13: 9, 11: 8}}
    BALL = ("SpecialN", "SpecialAirN", "SpecialS", "SpecialAirS", "SpecialLw", "SpecialAirLw")

    def edit(data, c):
        p = dict(c["params"])
        if p["Element"] == 1:
            sa.set_param(data, c, "Element", 0)
            log.append(f"| {name} | {p['ID']} | Element | 1 (fire) | 0 (normal) |")
        nd = DMG.get(name, {}).get(p["Damage"])
        if nd:
            sa.set_param(data, c, "Damage", nd)
            log.append(f"| {name} | {p['ID']} | Damage | {p['Damage']} | {nd} |")
        if name in BALL and p["Damage"] > 0:
            for k, v in (("Bone", 2), ("Z-Offset", int(PIV[0] * 256)), ("Y-Offset", int(PIV[1] * 256)), ("X-Offset", int(PIV[2] * 256)), ("Size", int(4.3 * 256))):
                sa.set_param(data, c, k, v)
            log.append(f"| {name} | {p['ID']} | Bone/offset/size | bone {p['Bone']} size {p['Size']} | bone 2 ball centre size {int(4.3 * 256)} |")
    return edit


DROP = ("Graphic", "Sound", "SFX", "Aura", "Color Animation", "Wind", "Sword")
SPECIALS = []


# ------------------------------------------------------------------ sounds (v56)
# Sonic's own bank (sonic.ssm, bank 56): IDs 560000 + index, see scripts/make_sonic_soundbank.py. SA1 effects from P_SONICTAILS
# bank 03 and short grunts from the English voice bank. Melee's shared whooshes: 166 light, 165 medium, 164 heavy, 119 smash.
SB = 560000
HOMING, LD_HOLD, LD_LAUNCH, LD_ATTACK, SPIN_CHARGE, SPIN_RELEASE, SWIPE = (SB + i for i in range(7))
GRUNT = [SB + 7 + i for i in range(5)]
HURT = [SB + 12, SB + 13]
W1, W2, W3, WS, JUMP = 166, 165, 164, 119, 74
SW, SND, VOICE = 1, 0, 2            # "Behavior": 1 = swing, 0 = sound, 2 = voice
SFX = {
    "JumpF": [(2, JUMP, SND)], "JumpB": [(2, JUMP, SND)], "JumpAerialF": [(2, JUMP, SND)], "JumpAerialB": [(2, JUMP, SND)],
    "Jab1": [(2, W1, SW)], "Jab2": [(2, W1, SW)], "Jab3": [(4, W2, SW), (4, GRUNT[0], VOICE)],
    "DashAttack": [(4, SPIN_RELEASE, SND)],
    "ForwardTilt": [(5, SWIPE, SND)], "UpTilt": [(4, W2, SW)], "DownTilt": [(3, SPIN_RELEASE, SND), (11, W1, SW)],
    "ForwardSmash": [(14, WS, SND), (14, GRUNT[1], VOICE), (16, SWIPE, SND)], "UpSmash": [(7, SPIN_CHARGE, SND), (19, GRUNT[2], VOICE)],
    "DownSmash": [(6, W3, SW), (6, GRUNT[3], VOICE)],
    "NeutralAir": [(3, W1, SW)], "ForwardAir": [(9, W3, SW), (9, GRUNT[4], VOICE)], "BackAir": [(4, W3, SW)],
    "UpAir": [(4, W2, SW)], "DownAir": [(5, W3, SW)],
    "HomingAttack": [(1, HOMING, SND), (1, GRUNT[0], VOICE)],
    "SpinDashCharge": [(7, SPIN_CHARGE, SND)] + [(7 + 26 * k, SPIN_CHARGE, SND) for k in range(1, 7)],
    "SpinDash": [(1, SPIN_RELEASE, SND)],
    "PeelOutUp": [(1, LD_HOLD, SND), (9, LD_LAUNCH, SND), (9, GRUNT[2], VOICE)],
    "PeelOutSide": [(1, LD_HOLD, SND), (9, LD_LAUNCH, SND), (9, GRUNT[2], VOICE)],
    "LightDashCharge": [(2, LD_HOLD, SND)], "LightDash": [(1, LD_LAUNCH, SND), (1, GRUNT[1], VOICE)],
    "BounceAttack": [(3, W2, SW)],
}


def remap_voices(pl_path, tbase, acts_list):
    """Point every voice/sound ID of Falcon's bank (60000-69999) in the scripts Sonic keeps at Sonic's own bank, in place:
    damage and KO sounds -> hurt clips, everything else -> grunts. Returns the number of IDs changed."""
    raw = bytearray(open(pl_path, "rb").read())
    done, n = set(), 0
    for k, a in enumerate(acts_list):
        if not a.cmds:
            continue
        loc = 0x20 + struct.unpack(">I", raw[tbase + k * 0x18 + 0x0C: tbase + k * 0x18 + 0x10])[0]
        if loc in done or loc <= 0x20:
            continue
        done.add(loc)
        data = bytearray(raw[loc:loc + len(a.data)])
        if bytes(data) != a.data:
            continue
        hurt = a.name and ("Damage" in a.name or "Dead" in a.name or "Fura" in a.name)
        for c in sa.parse(bytes(data)):
            for key in [k_ for k_ in c["params"] if k_.startswith("SFX ID")]:
                v = c["params"][key]
                if 60000 <= v < 70000:
                    sa.set_param(data, c, key, (HURT[v % 2] if hurt else GRUNT[v % 5]))
                    n += 1
        raw[loc:loc + len(data)] = data
    open(pl_path, "wb").write(raw)
    return n


# scripts that keep the game's own commands and only get a command put in front
PREPEND = {}   # v55 put the Peel-Out figure-8 on the Run feet; removed in v56 (looked wrong in game)


def make_script(plan, charge_bytes):
    items = []
    ev = plan["events"]
    for n, (f0, f1, hits) in enumerate(ev):
        items.append((f0, 2, b"".join(h.bytes() for h in hits)))
        nxt = ev[n + 1] if n + 1 < len(ev) else None
        # a strong hit that decays straight into a weaker one must not clear in between, or the weak part hits a second time
        decays = nxt is not None and nxt[0] == f1 + 1 and max(h.dmg for h in nxt[2]) <= max(h.dmg for h in hits) and {h.id for h in nxt[2]} >= {h.id for h in hits}
        if not decays:
            items.append((f1 + 1, 1, CLEAR))
    if plan.get("aerial"):
        items += [(plan["aerial"][0], 0, flag(1)), (plan["aerial"][1], 3, flag(0))]
    if plan.get("jab"):
        items += [(plan["jab"][0], 3, cmd("Enable Jab Followup", Toggle=1)), (plan["jab"][1], 3, cmd("Enable Jab Followup", Toggle=0))]
    if plan.get("charge"):
        items.append((plan["charge"], 0, charge_bytes))
    if plan.get("iasa"):
        items.append((plan["iasa"], 4, IASA))
    if plan.get("emerald"):
        items += [(plan["emerald"][0], 0, cmd("Change Model State", **{"Struct ID": 1, "Object ID": 1})),
                  (plan["emerald"][1], 5, cmd("Change Model State", **{"Struct ID": 1, "Object ID": 0}))]
    MOUTH = lambda v: cmd("Change Model State", **{"Struct ID": 3, "Object ID": v})   # noqa: E731  0 closed (smile is in the body set), 1 open
    if ev and not plan.get("ball"):
        first, last = min(e[0] for e in ev), max(e[1] for e in ev)
        items.append((max(1, first - 3), 0, MOUTH(1)))                    # mouth opens as he attacks (a shout)
        if last + 5 < plan["total"]:
            items.append((last + 5, 5, MOUTH(0)))
    CMS = lambda g, v: cmd("Change Model State", **{"Struct ID": g, "Object ID": v})   # noqa: E731
    for f_, sid, beh in SFX.get(plan["label"], []):
        items.append((f_, 0, cmd("Sound Effect", Behavior=beh, Volume=127, Panning=64, **{"SFX ID": sid})))
    if plan.get("insta"):          # group 1 set 2 = Insta-Shield crescent
        items += [(plan["insta"][0], 0, CMS(1, 2)), (plan["insta"][1], 5, CMS(1, 0))]
    if plan.get("fig8"):           # group 2 set 2 = Peel-Out figure-8
        items.append((plan["fig8"][0], 0, CMS(2, 2)))
        if plan["fig8"][1]:
            items.append((plan["fig8"][1], 5, CMS(2, 0)))
    if plan.get("trail"):
        items += [(plan["trail"][0], 0, cmd("Change Model State", **{"Struct ID": 2, "Object ID": 1})),
                  (plan["trail"][1], 5, cmd("Change Model State", **{"Struct ID": 2, "Object ID": 0}))]
    if plan.get("ball"):
        items += [(plan["ball"][0], 0, cmd("Change Model State", **{"Struct ID": 0, "Object ID": 1}))]
        if plan["ball"][1]:
            items.append((plan["ball"][1], 5, cmd("Change Model State", **{"Struct ID": 0, "Object ID": 0})))
    items.sort(key=lambda x: (x[0], x[1]))
    out, cur = b"", 1
    for f, _, b in items:
        if f != cur:
            out += at(f)
            cur = f
        out += b
    return out + END


def frames_for(an, n=7):
    T = an.T
    return sorted({int(round(i * T / (n - 1))) for i in range(n)})


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "preview":
        out = sys.argv[2]
        byname = {a.actions[0]: a for a in A}
        lab = {v["actions"][0]: k for k, v in PLAN.items()}
        want = sys.argv[3].split(",") if len(sys.argv) > 3 else None
        items = []
        for a in A:
            label = lab.get(a.actions[0], a.actions[0])
            if want and label not in want:
                continue
            fr = frames_for(a)
            if label in HITS:      # make sure the hit frames are shown
                hf = sorted({f0 - 1 for f0, f1, h in HITS[label]} | {f1 - 1 for f0, f1, h in HITS[label]})
                fr = sorted(set(hf[:5]) | {0, a.T})[:7] if len(hf) >= 4 else sorted(set(hf) | set(frames_for(a, 7 - len(hf))))[:7]
            items.append((label, a, fr))
        for i in range(0, len(items), 6):
            sheet(items[i:i + 6], os.path.join(out, f"sheet_{i // 6:02d}.png"), hits=HITS)
    elif mode == "build":
        aj_in, pl_in, aj_out, pl_out, report = sys.argv[2:7]
        tmp_pl = pl_out + ".tmp"
        write_anims(A, aj_in, pl_in, aj_out, tmp_pl)
        load_templates(pl_in)
        acts = {a.name: a for a in sa.load(pl_in) if a.name}
        charge = next(acts["AttackS4S"].data[c["off"]:c["off"] + c["len"]] for c in acts["AttackS4S"].cmds if c["name"] == "Start Smash Charge")
        scripts, log = {}, ["| Action | Hitbox | Field | From | To |", "|---|---|---|---|---|"]
        for label, plan in PLAN.items():
            s = make_script(plan, charge)
            for act in plan["actions"]:
                scripts[act] = s
        for name in SPECIALS:
            a = acts[name]
            if a.cmds[-1]["name"] != "End Of Script" or any(c["name"] in ("Go To", "Subroutine", "Return") for c in a.cmds):
                print("special kept as is (has jumps):", name)
                continue
            ed, out = special_edit(name, log), b""
            for c in a.cmds:
                if any(d in c["name"] for d in DROP):
                    continue
                b = bytearray(a.data[c["off"]:c["off"] + c["len"]])
                if c["name"] == "Create Hitbox":
                    ed(b, sa.parse(bytes(b))[0])
                out += bytes(b)
            scripts[name] = out
        pointers = {}
        tb0, ta0 = action_table(bytearray(open(tmp_pl, "rb").read()), tmp_pl)
        print("Falcon voice IDs pointed at Sonic's bank:", remap_voices(tmp_pl, tb0, sa.load(tmp_pl)))
        raw_tmp = open(tmp_pl, "rb").read()
        tbase, tacts = action_table(bytearray(raw_tmp), tmp_pl)
        for name, (cname, cargs) in PREPEND.items():
            a = acts[name]
            pre = cmd(cname, **cargs)
            if a.cmds and a.cmds[-1]["name"] == "Go To" and not any(c["name"] in ("Go To", "Subroutine", "Return") for c in a.cmds[:-1]):
                # the script loops with a Go To back into the game's own copy: keep that pointer (it needs a relocation entry)
                k = next(i for i, t in enumerate(tacts) if t.SymbolName is not None and t.SymbolName.Value.endswith(f"ACTION_{name}_figatree"))
                loc = struct.unpack(">I", raw_tmp[tbase + k * 0x18 + 0x0C: tbase + k * 0x18 + 0x10])[0]
                goto = a.cmds[-1]["off"]
                target = struct.unpack(">I", raw_tmp[0x20 + loc + goto + 4: 0x20 + loc + goto + 8])[0]
                scripts[name] = pre + a.data[:goto + 8]
                pointers[name] = [(len(pre) + goto + 4, target)]
                print(f"{name}: command put in front; its loop still jumps to the original script at 0x{target:X} (script was at 0x{loc:X})")
            elif a.cmds and a.cmds[-1]["name"] == "End Of Script" and not any(c["name"] in ("Go To", "Subroutine", "Return") for c in a.cmds):
                scripts[name] = pre + a.data[:a.cmds[-1]["off"] + a.cmds[-1]["len"]]
            else:
                print("prepend skipped (script has other jumps):", name)
        install_scripts(tmp_pl, pl_out, scripts, pointers)
        os.remove(tmp_pl)
        with open(report, "w") as f:
            f.write("# v19 moves\n\n## New attacks (script written from scratch; game frames)\n\n")
            f.write("| Move | Actions | Total | IASA | Hit frames | Damage | Angle | BKB | KBG | Set KB | Size | Bone |\n|---|---|---|---|---|---|---|---|---|---|---|---|\n")
            for label, plan in PLAN.items():
                for f0, f1, hits in plan["events"]:
                    for h in hits:
                        f.write(f"| {label} | {', '.join(plan['actions'])} | {plan['total']} | {plan.get('iasa')} | {f0}-{f1} | {h.dmg} | {h.angle} | {h.bkb} | {h.kbg} | {h.wdsk} | {h.size} | {h.bone} |\n")
            f.write("\n## Specials (Falcon's scripts with graphics/sounds removed)\n\n" + "\n".join(log) + "\n")
        print("report", report)

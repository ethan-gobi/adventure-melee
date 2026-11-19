"""Sonic's own animations and attack scripts (v19). All values here are designed for this mod.

Usage: python sonic_moves.py preview <out dir>
       python sonic_moves.py build <PlSnAJ in> <PlSn.dat in> <PlSnAJ out> <PlSn.dat out> <changes.md>
Key frames are animation frames (0-based); hitbox frames are game frames (1-based), so game frame f shows animation frame f-1.
"""
import os
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
    PLAN[label] = dict(actions=[actions] if isinstance(actions, str) else list(actions), events=events, total=T, **plan)


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
DUCK = P(root=(6, 0, 0), chest=(50, 0, 0), head=(-22, 0, 0), footL=-8, footR=-8,
         thighL=(0.3, 0.5, 1), shinL=(0.08, -1, -0.62), thighR=(-0.3, 0.42, 1), shinR=(-0.08, -1, -0.66),
         armL=(0.55, -0.7, 1), foreL=(-0.35, -0.45, 1), armR=(-0.55, -0.7, 1), foreR=(0.35, -0.45, 1))
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
# forward tilt: the side kick again (swapped with the forward smash in v47)
FT_EX = P(K_EX, root=(0, -88, 36), thighL=(1, 0.22, 0), shinL=(1, 0.26, 0))
move("ForwardTilt", ["AttackS3Hi", "AttackS3HiS", "AttackS3S", "AttackS3LwS", "AttackS3Lw"], 28,
     [(0, S), (5, K_CH), (7, FT_EX, "out"), (11, FT_EX), (16, K_CH), (28, S)],
     [(8, 10, leg("L", 9, 361, 12, 95, size=2.5, shin_dmg=8))], iasa=26)


UTF = dict(ground=0, pivot=(0, 2.0, 0), thighL=(0.12, -1, 0.3), shinL=(0.08, -1, 0.12), thighR=(-0.12, -1, 0.3), shinR=(-0.08, -1, 0.12), footL=40, footR=40,
           armL=(1, -0.3, 0.2), foreL=(1, 0.1, 0.3), armR=(-1, -0.3, 0.2), foreR=(-1, 0.1, 0.3))
move("UpTilt", "AttackHi3", 28,
     [(0, S), (3, P(CROUCH, root=(-5, 0, 0))), (5, P(S, root=(-80, 0, 0), hip=(0, 1.5, 0), **UTF), "in"), (10, P(S, root=(-225, 0, 0), hip=(0, 3.0, 0), **UTF), "lin"),
      (15, tuck(-320, pivot=(0, 2.0, 0), hip=(0, 1.5, 0)), "lin"), (20, P(LAND, root=(-360, 0, 0)), "lin"), (28, P(S, root=(-360, 0, 0)))],
     [(6, 10, [Hit(0, 16, 8, 2.6, 92, 35, 95, off=(1.6, 0, 0)), Hit(1, 10, 8, 2.6, 92, 35, 95, off=(1.6, 0, 0)), Hit(2, 14, 7, 2.0, 92, 35, 95, off=(2.4, 0, 0))])], iasa=24)

# down tilt: Chaos Emerald boomerang. From the duck he flicks the emerald out along the floor; it spins out 13 units and comes back.
# The emerald rides the prop bone, so it is a moving hitbox tied to the move, not a separate projectile.
BM_W = P(DUCK, chest=(40, -45, 0), armR=(-0.6, -0.3, -0.8), foreR=(-0.4, 0.3, 0.3))
BM_T = P(DUCK, chest=(46, 35, 0), head=(-30, 0, 0), armR=(-0.1, -0.15, 1), foreR=(0.0, -0.1, 1))
BM_C = P(DUCK, chest=(48, 10, 0), armR=(-0.3, -0.4, 1), foreR=(-0.1, 0.1, 1))


def boomerang(f, W):
    hand = (W[47] @ np.array([*EM_C, 1.0]))[:3]
    far = np.array([0.0, 3.4, 17.0])
    if f <= 5:
        return hand, 0
    if f <= 13:
        t = (f - 5) / 8.0
        t = 1 - (1 - t) ** 2
    else:
        t = max(0.0, 1 - (f - 13) / 12.0)
        t = t * t * (3 - 2 * t)
    return hand + (far - hand) * t, (f - 5) * 45


move("DownTilt", "AttackLw3", 34, [(0, DUCK), (3, BM_W), (6, BM_T, "out"), (13, BM_T), (25, BM_C), (34, DUCK)],
     [(6, 13, [Hit(0, 62, 8, 2.2, 70, 25, 60)]), (14, 25, [Hit(1, 62, 5, 2.0, 80, 15, 50)])], iasa=31, emerald=(5, 27), prop=boomerang)


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
move("ForwardSmash", ["AttackS4Hi", "AttackS4S", "AttackS4Lw"], 44,
     [(0, S), (4, EM_W1, "out"), (7, EM_W2), (12, P(EM_W2, chest=(-12, -80, 0))), (14, P(EM_T2, move=2.0), "in"), (16, EM_T2, "out"),
      (21, EM_F), (32, P(EM_W1, root=(0, 0, 0), move=3.5)), (44, P(S, move=3.5))],
     [(15, 18, [Hit(0, 62, 22, 2.7, 361, 35, 102), Hit(1, 46, 12, 1.5, 361, 30, 95, off=(1.6, 0, 0))])], charge=7, iasa=42, emerald=(3, 28), prop=_emhand)

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
     [(4, 9, [ball(9, 361, 15, 95)]), (10, 27, [ball(5, 361, 10, 80, size=4.1)])], aerial=(3, 30), iasa=36, ball=(4, 29))

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
move("SpinDashCharge", "SpecialSStart", 80, [(0, S), (6, tuck(60, **GB)), (80, tuck(3020, **GB), "lin")], [], ball=(7, 0))
move("SpinDash", "SpecialS", 40, [(0, tuck(0, **GB)), (4, tuck(128, hip=(0, -4.8, 0)), "out"), (9, tuck(288, **GB), "in"), (30, tuck(960, **GB), "lin"), (36, P(CROUCH, root=(1080, 0, 0)), "lin"), (40, P(S, root=(1080, 0, 0)))],
     [(1, 32, [ball(10, 50, 35, 75)])], ball=(1, 31))
LSD_HIT = [(2, 16, [Hit(0, 2, 6, 3.8, 70, 30, 60, off=(0, 1.5, 0))])]
move("LightSpeedDashUp", "SpecialAirHi", 30,      # ball flash, then a rising corkscrew with one fist up
     [(0, tuck(0)), (4, tuck(200), "lin"), (6, RISE, "out"), (13, P(RISE, root=(10, 0, 0))), (20, RISE), (26, tuck(300, pivot=(0, 2.0, 0)), "in"), (30, P(FALL, root=(360, 0, 0)))],
     LSD_HIT, ball=(1, 5))
move("LightSpeedDashSide", "SpecialHi", 30,       # ball flash, then a head-first flying dash
     [(0, tuck(0)), (4, tuck(200), "lin"), (6, FLY, "out"), (13, P(FLY, root=(86, 0, 0))), (20, P(FLY, root=(76, 0, 0))), (26, tuck(380, pivot=(0, 2.0, 0)), "in"),
      (30, P(FALL, root=(360, 0, 0)))],
     LSD_HIT, ball=(1, 5))
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
        install_scripts(tmp_pl, pl_out, scripts)
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

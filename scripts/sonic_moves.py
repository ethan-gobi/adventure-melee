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


BALL_HIP = (0, -7.1, 0)     # hip offset that rests the spin ball (radius 4.5 round PIV) on the floor
INJECT = {}                 # action -> [(game frame, order, command bytes)] merged into the game's own script (v61)


def show_ball(names, f0, f1):
    """v61: show the spin-ball model from game frame f0 and the body again from f1, in a script that is otherwise kept.
    Until v60 the rolls, dodges and techs spun the curled-up body itself, which looked like a tumbling heap of limbs."""
    for nm in ([names] if isinstance(names, str) else names):
        INJECT.setdefault(nm, []).extend([(f0, 0, cmd("Change Model State", **{"Struct ID": 0, "Object ID": 1})),
                                          (f1, 9, cmd("Change Model State", **{"Struct ID": 0, "Object ID": 0}))])


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


def leg(side, dmg, angle, bkb, kbg, size=2.5, id=0, shin_dmg=None, wdsk=0, elem=0):
    """Foot hitbox plus a slightly weaker, smaller shin hitbox."""
    th, sh, ft = LEGS[side]
    return [Hit(id, ft, dmg, size, angle, bkb, kbg, off=(1.6, 0, 0), wdsk=wdsk, elem=elem),
            Hit(id + 1, sh, shin_dmg or dmg, size * 0.8, angle, bkb, kbg, off=(2.4, 0, 0), wdsk=wdsk, elem=elem)]


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
anim("EscapeF", 32, [(0, S), (5, tuck(60, hip=BALL_HIP)), (26, tuck(780, hip=BALL_HIP), "lin"), (32, P(S, root=(720, 0, 0)))], keep_root=True)
anim("EscapeB", 32, [(0, S), (5, tuck(-60, hip=BALL_HIP)), (26, tuck(-780, hip=BALL_HIP), "lin"), (32, P(S, root=(-720, 0, 0)))], keep_root=True)
show_ball(["EscapeF", "EscapeB"], 6, 27)

# shield: see after the crouch (v58)

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

# ------------------------------------------------------------------ ledge get-ups and techs (v60; these were still Falcon's)
# The game's root motion (bone 1) is kept and Falcon's body path (bone 3, which smooths the stepped root motion) is copied
# onto Sonic's hip (hip_from), so where he ends up and every frame-data number stay the same. Hitbox frames of the ledge
# attacks are unchanged: under 100% a two-foot kick on f24-29 (legs), over 100% a left-hand swipe on f37-40.


def hang_for(name):
    """the hanging pose with both hands on the ledge, at frame 0 of a ledge animation"""
    tgt = np.mean(orig_bone_pos(AJ_BASE, name, 0, (25, 47)), axis=0)
    root = falcon_track(name, 1, 0)[0][:3] - rest[1][:3]
    off3 = falcon_track(name, 3, 0)[0][:3] - rest[3][:3]
    w = solve(P(HANG0, fy=1.0))[0]
    hands = (w[25][:3, 3] + w[47][:3, 3]) / 2
    return P(HANG0, hip=tuple(tgt - root - off3 - hands))


LPULL = P(ground=0, root=(10, 0, 0), chest=(18, 0, 0), head=(-25, 0, 0), footL=30, footR=30,
          armL=(0.35, 0.5, 0.65), foreL=(0.05, 1, 0.25), armR=(-0.35, 0.5, 0.65), foreR=(-0.05, 1, 0.25),
          thighL=(0.1, -0.25, 1), shinL=(0.05, -1, 0.1), thighR=(-0.1, -0.6, 0.8), shinR=(-0.05, -1, -0.2))
LKNEE = P(ground=0, root=(25, 0, 0), chest=(20, 0, 0), head=(-30, 0, 0),
          armL=(0.3, -1, 0.35), foreL=(0.1, -1, 0.15), armR=(-0.3, -1, 0.35), foreR=(-0.1, -1, 0.15),
          thighL=(0.1, 0.2, 1), shinL=(0.05, -1, -0.1), thighR=(-0.1, -1, -0.3), shinR=(-0.05, -1, -0.5))
LBALL = lambda pitch: tuck(pitch, hip=BALL_HIP, fy=0.0)                                  # noqa: E731
LKICK = P(ground=1, root=(-40, 0, 0), chest=(12, 0, 0), head=(18, 0, 0), footL=-25, footR=-25,       # two-foot kick, sat back on his hands
          armL=(0.5, -1, -0.6), foreL=(0.2, -1, -0.25), armR=(-0.5, -1, -0.6), foreR=(-0.2, -1, -0.25),
          thighL=(0.15, -0.05, 1), shinL=(0.05, -0.1, 1), thighR=(-0.15, 0.05, 1), shinR=(-0.05, 0.0, 1))
LCOIL = P(LKICK, thighL=(0.15, 0.5, 0.8), shinL=(0.05, -1, 0.3), thighR=(-0.15, 0.55, 0.8), shinR=(-0.05, -1, 0.25))
LSWIPE0 = P(CROUCH, chest=(20, 40, 0), armL=(0.6, 0.3, -0.7), foreL=(0.3, 0.2, -1))                # left arm drawn back
LSWIPE = P(CROUCH, root=(15, 0, 0), chest=(15, -45, 0), armL=(0.05, 0.0, 1), foreL=(-0.05, 0.05, 1))  # swiped forward


def ledge(name, T, keys, pin=0, **kw):
    """Ledge animation: hang pose at frame 0, Falcon's body path on the hip, hands held on the ledge (arm IK) until frame
    `pin` (released over the last 3 frames). Written as one key per frame."""
    h = hang_for(name)
    carry = {id(HANGS): 1.0, id(HANGP): 1.0, id(LPULL): 0.7, id(LKNEE): 0.35}   # keep the hands-on-ledge offset, fading out
    ks = [(0, h)]
    for k_ in keys:
        f_, p_ = k_[0], k_[1]
        if id(p_) in carry:
            c_ = carry[id(p_)]
            p_ = P(p_, hip=tuple(np.array(h["hip"], dtype=float) * c_), root=tuple(np.array(h["root"], dtype=float) * c_ + np.array(p_["root"], dtype=float) * (1 - c_)))
        ks.append((f_, p_) + tuple(k_[2:]))
    off = falcon_track(name, 3, T)[:, :3] - rest[3][:3]
    tr = falcon_track(name, 1, T)[:, :3] - rest[1][:3]
    hand = {"L": orig_bone_pos(AJ_BASE, name, 0, (25,))[0], "R": orig_bone_pos(AJ_BASE, name, 0, (47,))[0]}
    dense = []
    for f_, p_ in enumerate(sample(ks, T)):
        o_ = off[f_].copy()
        o_[1] *= float(p_["fy"])
        p_ = P(p_, hip=tuple(np.array(p_["hip"], dtype=float) + o_))
        if f_ <= pin:
            w_ = 1.0 if f_ <= pin - 3 else (pin - f_) / 3.0
            q_ = p_
            for side, pole in (("L", (1, 0.2, -0.6)), ("R", (-1, 0.2, -0.6))):
                q_ = reach(q_, side, hand[side] - tr[f_], pole=pole)
            p_ = lerp_pose(p_, q_, w_)
        dense.append((f_, p_, "lin"))
    anim(name, T, dense, keep_root=True, **kw)


ledge("CliffClimbQuick", 33, [(7, LPULL), (14, LKNEE), (20, CROUCH), (33, S)], pin=17)
ledge("CliffClimbSlow", 59, [(12, HANGS), (20, HANGP), (27, LPULL), (34, LKNEE), (41, CROUCH), (59, S)], pin=37)
ledge("CliffEscapeQuick", 49, [(6, LPULL), (12, LKNEE), (18, LBALL(30)), (34, LBALL(390), "lin"), (40, P(CROUCH, root=(390, 0, 0))), (49, P(S, root=(360, 0, 0)))], pin=15)
ledge("CliffEscapeSlow", 79, [(10, HANGS), (18, LPULL), (28, LKNEE), (36, CROUCH), (42, LBALL(30)), (58, LBALL(390), "lin"),
                              (64, P(CROUCH, root=(390, 0, 0))), (79, P(S, root=(360, 0, 0)))], pin=32)
ledge("CliffAttackQuick", 55, [(6, LPULL), (13, LKNEE), (19, CROUCH), (22, LCOIL), (24, LKICK, "out"), (29, LKICK), (37, CROUCH), (55, S)], pin=16)
ledge("CliffAttackSlow", 69, [(10, HANGS), (18, LPULL), (24, LKNEE), (30, CROUCH), (35, LSWIPE0), (37, LSWIPE, "out"), (41, LSWIPE), (50, CROUCH), (69, S)], pin=27)
ledge("CliffJumpQuick1", 12, [(6, LPULL), (12, CROUCH)], pin=9)
ledge("CliffJumpSlow1", 19, [(7, HANGS), (13, LPULL), (19, CROUCH)], pin=15)
show_ball("CliffEscapeQuick", 19, 35)
show_ball("CliffEscapeSlow", 43, 59)
show_ball("CliffJumpQuick2", 5, 27)
show_ball("CliffJumpSlow2", 5, 30)
anim("CliffJumpQuick2", 33, [(0, CROUCH), (4, tuck(60)), (26, tuck(630), "lin"), (33, P(FALL, root=(720, 0, 0)), "lin")], keep_root=True)
anim("CliffJumpSlow2", 36, [(0, CROUCH), (4, tuck(60)), (29, tuck(630), "lin"), (36, P(FALL, root=(720, 0, 0)), "lin")], keep_root=True)
# techs: in place = a quick spin up off the floor; tech rolls = the same ball roll as his shield rolls
anim("Passive", 26, [(0, LBALL(-30)), (10, LBALL(330), "lin"), (16, P(CROUCH, root=(390, 0, 0))), (26, P(S, root=(360, 0, 0)))], keep_root=True)
anim("PassiveStandF", 40, [(0, LBALL(0)), (30, LBALL(720), "lin"), (35, P(CROUCH, root=(750, 0, 0))), (40, P(S, root=(720, 0, 0)))], keep_root=True)
anim("PassiveStandB", 40, [(0, LBALL(0)), (30, LBALL(-720), "lin"), (35, P(CROUCH, root=(-690, 0, 0))), (40, P(S, root=(-720, 0, 0)))], keep_root=True)

show_ball("Passive", 1, 11)
show_ball(["PassiveStandF", "PassiveStandB"], 1, 31)

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

# ------------------------------------------------------------------ shield (v58)
# v58 shielded in the curled crouch with the bubble bone at 6.6 (v57: upright guard, 9.4).
# v61: the curled crouch still looked broken in game: inside the bubble the dark fur blends into the bubble colour and only
# the skin-coloured arms, muzzle and thin legs show, as loose blocks. Sonic now guards the way he always has, curled into his
# spin ball (Sonic 1-3: rolled up he is protected; the Sonic 3 shields sit round him the same way). The ball model (part 19)
# is shown through the whole guard, so there are no limbs to come apart. Bubble bone height 6.6 -> 4.6 (the ball's centre).
# The game does not play the guard animations: it holds one frame of them (a first try with a 120-frame spinning Guard put
# him in the bind pose, the game reads frames up to the original 370) and it ignores model changes in their scripts. So
# every guard animation is the same still curled pose at its original length, and the ball model is switched on by the
# fighter code (OnFrame in fighter_code/sonic.c).
SHIELD_Y = 4.6
GUARD = tuck(20, hip=(0, SHIELD_Y - 11.62, 0))      # the ball's centre (PIV) sits SHIELD_Y above the floor
anim("GuardOn", 8, [(0, GUARD), (8, GUARD)], shield_y=SHIELD_Y)
anim("Guard", 370, [(0, GUARD), (370, GUARD)], shield_y=SHIELD_Y)
anim("GuardOff", 16, [(0, GUARD), (6, P(CROUCH, root=(20, 0, 0))), (16, S)], shield_y=SHIELD_Y)
anim("GuardDamage", 20, [(0, GUARD), (4, P(GUARD, root=(6, 0, 0)), "out"), (20, GUARD)], shield_y=SHIELD_Y)

# spot dodge and air dodge (v58; these were still Captain Falcon's animations): a quick spin curl in place, like the rolls.
# Same lengths as before (33 and 50 frames), and the game's own root motion is kept, so the dodge frame data do not change.
anim("EscapeN", 33, [(0, S), (3, tuck(30, hip=BALL_HIP)), (16, tuck(390, hip=BALL_HIP), "lin"), (21, P(S, root=(360, 0, 0))),
                     (33, P(S, root=(360, 0, 0)))], keep_root=True)
anim("EscapeAir", 50, [(0, FALL), (3, tuck(60)), (24, tuck(420), "lin"), (30, P(FALL, root=(360, 0, 0)), "lin"), (50, P(FALL, root=(360, 0, 0)))],
     keep_root=True)
show_ball("EscapeN", 4, 17)
# v61: the spot dodge is the Insta-Shield (Sonic 3: a split second of invincibility): the white crescent flashes round the ball
INJECT["EscapeN"] += [(5, 0, cmd("Change Model State", **{"Struct ID": 1, "Object ID": 2})), (15, 9, cmd("Change Model State", **{"Struct ID": 1, "Object ID": 0}))]
show_ball("EscapeAir", 4, 25)
# dizzy after a shield break (FuraFura, 100 frames; was Falcon's): swaying from side to side, head lolling, arms hanging
DZ1 = P(S, root=(12, 0, 9), chest=(10, 0, 0), head=(18, 0, 16), armL=(0.3, -1, 0.3), foreL=(0.15, -1, 0.35),
        armR=(-0.3, -1, 0.3), foreR=(-0.15, -1, 0.35))
DZ2 = P(DZ1, root=(12, 0, -9), head=(18, 0, -16))
anim("FuraFura", 100, [(0, DZ1), (25, DZ2), (50, DZ1), (75, DZ2), (100, DZ1)])
# ------------------------------------------------------------------ knockdown, get-ups, grabbed, asleep, walls (v61)
# All of these were still Captain Falcon's motion scaled onto Sonic: lying down he sank into the floor up to his ears, and
# the get-ups were a jumble. Same lengths as Falcon's, scripts (intangibility, hitbox frames) untouched. Lying poses rest on
# the floor by the lowest point of the whole body ("floor", sonic_anim_lib.lowest).


def fanim(name, t_auth, keys, **kw):
    """an animation written against a length of t_auth frames, stretched by moving its last key to the original length"""
    T = falcon_len(name)
    if abs(T - t_auth) > 1:
        print(f"note: {name} authored for {t_auth} frames, original has {T}")
    anim(name, T, [((T if k_[0] == t_auth else k_[0]),) + tuple(k_[1:]) for k_ in keys], **kw)


LIE_U = P(ground=0, floor=1, root=(-82, 0, 0), chest=(14, 0, 0), head=(38, 0, 0), footL=25, footR=25,          # on his back, feet forward
          armL=(1, 0.3, -0.12), foreL=(0.9, -0.5, -0.05), armR=(-1, -0.1, -0.12), foreR=(-0.6, 0.8, -0.05),
          thighL=(0.28, -1, 0.1), shinL=(0.12, -1, -0.12), thighR=(-0.22, -1, 0.34), shinR=(-0.1, -1, -0.5))
FLAIL_U = P(LIE_U, root=(-70, 0, 0), chest=(25, 0, 0), armL=(1, 0.2, 0.6), foreL=(0.6, 0.3, 1), armR=(-1, 0.2, 0.6), foreR=(-0.6, 0.3, 1),
            thighL=(0.3, -0.5, 1), shinL=(0.15, -1, 0.3), thighR=(-0.3, -0.3, 1), shinR=(-0.15, -1, 0.1))
SIT_U = P(ground=0, floor=1, root=(-28, 0, 0), chest=(26, 0, 0), head=(6, 0, 0), footL=10, footR=10,           # sitting up, hands on the floor
          armL=(0.45, -1, -0.55), foreL=(0.2, -1, -0.2), armR=(-0.45, -1, -0.55), foreR=(-0.2, -1, -0.2),
          thighL=(0.25, 0.1, 1), shinL=(0.08, -0.7, 0.75), thighR=(-0.25, 0.25, 1), shinR=(-0.08, -1, 0.3))
LIE_D = P(ground=0, floor=1, root=(84, 0, 0), chest=(-6, 0, 0), head=(-58, 0, 0), footL=55, footR=55,          # on his front, head forward
          armL=(0.75, 0.65, 0.12), foreL=(0.1, 1, 0.1), armR=(-0.9, -0.3, 0.12), foreR=(-0.4, -1, 0.1),
          thighL=(0.2, -1, 0.03), shinL=(0.1, -1, 0.06), thighR=(-0.3, -1, 0.03), shinR=(-0.12, -1, 0.1))
FLAIL_D = P(LIE_D, root=(72, 0, 0), head=(-45, 0, 0), armL=(1, 0.5, -0.4), foreL=(0.7, 0.6, -0.6), armR=(-1, 0.5, -0.4), foreR=(-0.7, 0.6, -0.6),
            thighL=(0.3, -1, -0.45), shinL=(0.15, -0.6, -1), thighR=(-0.3, -1, -0.3), shinR=(-0.15, -0.8, -1))
PUSH_D = P(ground=0, floor=1, root=(55, 0, 0), chest=(-10, 0, 0), head=(-45, 0, 0), footL=20, footR=20,        # pushing up on hands and knees
           armL=(0.3, -0.35, 1), foreL=(0.1, -0.3, 1), armR=(-0.3, -0.35, 1), foreR=(-0.1, -0.3, 1),
           thighL=(0.2, -0.4, 1), shinL=(0.1, -1, -0.5), thighR=(-0.2, -0.55, 1), shinR=(-0.1, -1, -0.45))
CRF = P(CROUCH, floor=1)
FB = lambda pitch: tuck(pitch, hip=BALL_HIP)        # noqa: E731  the spin ball rolling along the floor

fanim("DownBoundU", 25, [(0, P(FLAIL_U, up=0.0)), (9, P(FLAIL_U, root=(-95, 0, 0), up=3.4), "out"), (19, P(FLAIL_U, up=0.0), "in"), (25, LIE_U)])
fanim("DownWaitU", 69, [(0, LIE_U), (34, P(LIE_U, chest=(18, 0, 0), head=(34, 0, 0))), (69, LIE_U)])
fanim("DownDamageU", 13, [(0, LIE_U), (3, P(FLAIL_U, up=1.6), "out"), (9, LIE_U, "in"), (13, LIE_U)])
fanim("DownStandU", 29, [(0, LIE_U), (9, SIT_U), (17, CRF), (29, S)])
fanim("DownBoundD", 25, [(0, P(FLAIL_D, up=0.0)), (9, P(FLAIL_D, root=(95, 0, 0), up=3.4), "out"), (19, P(FLAIL_D, up=0.0), "in"), (25, LIE_D)])
fanim("DownWaitD", 69, [(0, LIE_D), (34, P(LIE_D, head=(-54, 0, 0), chest=(-9, 0, 0))), (69, LIE_D)])
fanim("DownDamageD", 13, [(0, LIE_D), (3, P(FLAIL_D, up=1.6), "out"), (9, LIE_D, "in"), (13, LIE_D)])
fanim("DownStandD", 29, [(0, LIE_D), (9, PUSH_D), (17, CRF), (29, S)])
fanim("DownSpotD", 19, [(0, S), (7, CRF), (13, PUSH_D), (19, LIE_D)])
# get-up rolls: curls up from the floor and rolls away (the game's travel kept), like his other rolls
fanim("DownFowardU", 35, [(0, LIE_U), (6, FB(30)), (26, FB(750), "lin"), (30, P(CRF, root=(750, 0, 0))), (35, P(S, root=(720, 0, 0)))], keep_root=True)
fanim("DownBackU", 35, [(0, LIE_U), (6, FB(-110)), (26, FB(-750), "lin"), (30, P(CRF, root=(-690, 0, 0))), (35, P(S, root=(-720, 0, 0)))], keep_root=True)
fanim("DownFowardD", 35, [(0, LIE_D), (6, FB(120)), (26, FB(750), "lin"), (30, P(CRF, root=(750, 0, 0))), (35, P(S, root=(720, 0, 0)))], keep_root=True)
fanim("DownBackD", 35, [(0, LIE_D), (6, FB(30)), (26, FB(-690), "lin"), (30, P(CRF, root=(-690, 0, 0))), (35, P(S, root=(-720, 0, 0)))], keep_root=True)
show_ball(["DownFowardU", "DownBackU", "DownFowardD", "DownBackD"], 7, 27)
# get-up attack from his back: a breakdance windmill (legs split, spinning on his shoulders). Falcon's script is kept: both
# legs hit on both sides at f19-20 and f28-29, 6% each, so the legs point forward/back on exactly those frames.
_WM = dict(ground=0, floor=1, chest=(30, 0, 0), head=(40, 0, 0), footL=-10, footR=-10,
           armL=(1, -0.2, -0.4), foreL=(0.6, -0.8, -0.3), armR=(-1, -0.2, -0.4), foreR=(-0.6, -0.8, -0.3),
           thighL=(0.1, -0.75, 1), shinL=(0.05, -0.8, 1), thighR=(-0.1, -0.55, -1), shinR=(-0.05, -0.5, -1))
WM = lambda yaw, pitch=-118: P(root=(pitch, yaw, 0), **_WM)      # noqa: E731
fanim("DownAttackU", 49, [(0, LIE_U), (9, P(TUCK, root=(-60, -150, 0), floor=1)), (15, WM(-60), "lin"), (18, WM(0), "lin"), (27.5, WM(180), "lin"),
                         (31, WM(250), "lin"), (37, P(CRF, root=(30, 360, 0))), (49, P(S, root=(0, 360, 0)))])
# get-up attack from his front: Falcon's script hits behind with the right leg at f20-21, then in front with it at f26-27:
# a mule kick back off his hands, then he swings the same leg round into a low kick forward.
MULE = P(ground=0, floor=1, root=(62, 0, 0), chest=(-12, 0, 0), head=(-50, 0, 0), footR=40,
         armL=(0.3, -0.4, 1), foreL=(0.1, -0.35, 1), armR=(-0.3, -0.4, 1), foreR=(-0.1, -0.35, 1),
         thighL=(0.25, -0.2, 1), shinL=(0.1, -1, -0.4), thighR=(-0.15, -1, -0.3), shinR=(-0.1, -1, -0.25))
MULE0 = P(MULE, thighR=(-0.2, -0.3, 1), shinR=(-0.1, -1, -0.6))
FKICK = P(ground=0, floor=1, root=(-28, 0, 0), chest=(22, 0, 0), head=(10, 0, 0), footR=-20,
          armL=(0.5, -1, -0.5), foreL=(0.2, -1, -0.2), armR=(-0.8, -0.3, -0.5), foreR=(-0.6, -0.5, 0.2),
          thighL=(0.2, -1, -0.1), shinL=(0.1, -1, -0.5), thighR=(-0.15, 0.25, 1), shinR=(-0.08, 0.2, 1))
fanim("DownAttackD", 49, [(0, LIE_D), (12, PUSH_D), (16, MULE0), (19, MULE, "out"), (21, MULE), (25, FKICK, "out"),
                         (27, P(FKICK, thighR=(-0.15, -0.05, 1), shinR=(-0.08, -0.1, 1))), (36, CRF), (49, S)])

# grabbed: standing (Hi) or dragged down on one knee (Lw), tugging at the hand on his chest and kicking
CAP_HI = P(root=(-12, 0, 0), chest=(-8, 0, 0), head=(-24, 0, 0), armL=(0.4, 0.25, 1), foreL=(-0.5, 0.6, 0.4), armR=(-0.4, 0.25, 1), foreR=(0.5, 0.6, 0.4),
           thighL=(0.14, -1, 0.3), shinL=(0.08, -1, -0.1), thighR=(-0.14, -1, 0.05), shinR=(-0.08, -1, -0.35))
CAP_HI2 = P(CAP_HI, root=(-6, 0, 6), head=(-14, 10, 0), thighL=(0.14, -1, 0.1), shinL=(0.08, -1, -0.35), thighR=(-0.14, -1, 0.35), shinR=(-0.08, -1, -0.05))
CAP_LW = P(root=(-20, 0, 0), chest=(-6, 0, 0), head=(-28, 0, 0), armL=(0.4, 0.5, 0.9), foreL=(-0.5, 0.7, 0.3), armR=(-0.4, 0.5, 0.9), foreR=(0.5, 0.7, 0.3),
           thighL=(0.2, -0.15, 1), shinL=(0.1, -1, 0.1), thighR=(-0.2, -1, 0.15), shinR=(-0.1, -0.15, -1), footR=50)
CAP_LW2 = P(CAP_LW, root=(-14, 0, 5), head=(-18, 12, 0))
CAP_OW = lambda b: P(b, root=(b["root"][0] - 14, 0, 0), head=(-45, 0, 0), armL=(1, 0.4, 0.3), foreL=(0.6, 1, 0.3), armR=(-1, 0.4, 0.3), foreR=(-0.6, 1, 0.3))  # noqa: E731
fanim("CapturePulledHi", 19, [(0, P(HURT, root=(10, 0, 0))), (8, CAP_HI2, "out"), (19, CAP_HI)])
fanim("CaptureWaitHi", 49, [(0, CAP_HI), (12, CAP_HI2), (24, CAP_HI), (36, mirror(CAP_HI2)), (49, CAP_HI)])
fanim("CaptureDamageHi", 19, [(0, CAP_HI), (3, CAP_OW(CAP_HI), "out"), (12, CAP_HI2), (19, CAP_HI)])
fanim("CapturePulledLw", 19, [(0, P(HURT, root=(10, 0, 0))), (8, CAP_LW2, "out"), (19, CAP_LW)])
fanim("CaptureWaitLw", 34, [(0, CAP_LW), (17, CAP_LW2), (34, CAP_LW)])
fanim("CaptureDamageLw", 19, [(0, CAP_LW), (3, CAP_OW(CAP_LW), "out"), (12, CAP_LW2), (19, CAP_LW)])
fanim("CaptureCut", 29, [(0, CAP_HI), (6, P(HURT, root=(-26, 0, 0)), "out"), (18, P(HURT, root=(-10, 0, 0))), (29, S)])
fanim("CaptureJump", 49, [(0, CAP_HI), (6, tuck(-40)), (30, tuck(-760), "lin"), (38, P(FALL, root=(-720, 0, 0))), (49, P(FALL, root=(-720, 0, 0)))])
show_ball("CaptureJump", 7, 31)

# asleep (Jigglypuff's Sing and the like): he sits down and nods off, chin on his chest, the way he gives up waiting in the
# old games; wakes with a start
SIT_Z = P(ground=0, floor=1, root=(-16, 0, 0), chest=(30, 0, 0), head=(34, 0, 8), footL=-10, footR=-10,
          armL=(0.5, -1, 0.3), foreL=(0.0, -0.8, 1), armR=(-0.5, -1, 0.3), foreR=(0.0, -0.8, 1),
          thighL=(0.4, 0.3, 1), shinL=(0.1, -0.9, 0.6), thighR=(-0.4, 0.3, 1), shinR=(-0.1, -0.9, 0.6))
SIT_Z2 = P(SIT_Z, chest=(36, 0, 0), head=(42, 0, -6))
fanim("FuraSleepStart", 29, [(0, S), (8, P(S, root=(8, 0, 6), head=(25, 0, 10))), (18, CRF), (29, SIT_Z)])
fanim("FuraSleepLoop", 109, [(0, SIT_Z), (54, SIT_Z2), (109, SIT_Z)])
fanim("FuraSleepEnd", 59, [(0, SIT_Z), (10, P(SIT_Z, chest=(10, 0, 0), head=(-20, 0, 0)), "out"), (24, P(SIT_Z, chest=(10, 0, 0), head=(-10, 40, 0))),
                          (38, CRF), (59, S)])

# small ones: attack clank recoil, dropping through a platform, wall and ceiling techs, bumping a wall or ceiling, wall splat
RECOIL = P(S, root=(-20, 0, 0), chest=(-14, 0, 0), head=(-20, 0, 0), armL=(0.9, 0.3, -0.5), foreL=(0.8, 0.8, 0.2), armR=(-0.9, 0.3, -0.5), foreR=(-0.8, 0.8, 0.2),
           thighL=(0.12, -1, 0.45), shinL=(0.08, -1, 0.05), thighR=(-0.12, -1, 0.1), shinR=(-0.08, -1, -0.4))
fanim("Rebound", 29, [(0, S), (4, RECOIL, "out"), (16, P(RECOIL, root=(-10, 0, 0))), (29, S)])
fanim("Pass", 29, [(0, P(CROUCH, ground=0, hip=(0, -3.0, 0))), (9, FALL), (19, FALL2), (29, FALL)])
fanim("PassiveWall", 25, [(0, tuck(-30)), (14, tuck(-390), "lin"), (19, P(FALL, root=(-360, 0, 0))), (25, P(FALL, root=(-360, 0, 0)))], keep_root=True)
fanim("PassiveWallJump", 39, [(0, tuck(-30)), (5, tuck(-60)), (30, tuck(-750), "lin"), (35, P(FALL, root=(-720, 0, 0))), (39, P(FALL, root=(-720, 0, 0)))], keep_root=True)
fanim("PassiveCeil", 25, [(0, tuck(30)), (14, tuck(390), "lin"), (19, P(FALL, root=(360, 0, 0))), (25, P(FALL, root=(360, 0, 0)))], keep_root=True)
show_ball(["PassiveWall", "PassiveCeil"], 1, 15)
show_ball("PassiveWallJump", 1, 31)
BUMP = P(S, root=(-14, 0, 0), chest=(-10, 0, 0), head=(-28, 0, 0), armL=(0.5, 0.2, 1), foreL=(0.2, 0.9, 0.6), armR=(-0.5, 0.2, 1), foreR=(-0.2, 0.9, 0.6))
fanim("StopWall", 20, [(0, P(S, root=(14, 0, 0))), (3, BUMP, "out"), (10, P(BUMP, root=(-8, 0, 0))), (20, S)], keep_root=True)
fanim("StopCeil", 7, [(0, P(FALL, head=(30, 0, 0), chest=(15, 0, 0), armL=(1, 0.9, 0.2), foreL=(0.3, 1, 0.4), armR=(-1, 0.9, 0.2), foreR=(-0.3, 1, 0.4))), (7, FALL)],
     keep_root=True)
fanim("MissFoot", 25, [(0, P(HURT, root=(-10, 0, 0))), (8, P(FLY, root=(-40, 0, 0))), (25, TUMBLE)])
SPLAT = P(ground=0, root=(-8, 0, 0), chest=(-12, 0, 0), head=(-30, 0, 0), armL=(1, 0.7, -0.3), foreL=(0.9, 1, -0.2), armR=(-1, 0.7, -0.3), foreR=(-0.9, 1, -0.2),
          thighL=(0.6, -1, -0.2), shinL=(0.4, -1, -0.4), thighR=(-0.6, -1, -0.2), shinR=(-0.4, -1, -0.4), footL=30, footR=30)
fanim("WallDamage", 49, [(0, SPLAT), (10, P(SPLAT, head=(-36, 0, 0))), (26, FLY), (49, TUMBLE)], keep_root=True)

# ------------------------------------------------------------------ items and the rest of Falcon's leftovers (v61)
# Picking up, throwing, swinging and shooting items, carrying crates, the hammer, the parasol, the Super Scope: about 45
# animations that were Falcon's joint values on Sonic's body (squashed, feet under the floor). They are re-posed frame by
# frame from Falcon's limb directions with Sonic's solver (sonic_anim_lib.retarget): same timing, same hand path for the
# item, feet planted. Scripts (release frames, item hitboxes) untouched.
for _nm in ("LightGet", "LightThrowF", "LightThrowB", "LightThrowHi", "LightThrowLw", "LightThrowDash", "LightThrowDrop",
            "HeavyGet", "HeavyWalk1", "HeavyWalk2", "HeavyThrowF", "HeavyThrowB", "HeavyThrowHi", "HeavyThrowLw",
            "Swing1", "Swing3", "Swing41", "Swing42", "SwingDash", "ItemHammerWait", "ItemHammerMove", "ItemParasolOpen",
            "ItemShoot", "ItemBlind", "ItemScopeStart", "ItemScopeRapid", "ItemScopeFire", "ItemScopeEnd",
            "Attack100Start", "Attack100Loop", "Attack100End"):
    _k = retarget(_nm)
    _n = len(_k) - 1
    # one-shot moves start and/or end in Sonic's own stance (Falcon's wide idle would pop against Sonic's idle)
    _in = _nm in ("LightGet", "LightThrowF", "LightThrowB", "LightThrowHi", "LightThrowLw", "LightThrowDrop", "Swing1", "Swing3", "Swing41", "Swing42", "ItemShoot")
    _out = _in or _nm in ("LightThrowDash", "SwingDash", "HeavyThrowF", "HeavyThrowB", "HeavyThrowHi", "HeavyThrowLw", "ItemScopeEnd", "Attack100End")
    _k = [(f_, lerp_pose(S, p_, min(1.0, (f_ / 4.0) if _in else 1.0, ((_n - f_) / 5.0) if _out else 1.0)), "lin") for f_, p_, _e in _k]
    anim(_nm, _n, _k, keep_root=True)
for _nm in ("LightThrowAirF", "LightThrowAirB", "LightThrowAirHi", "LightThrowAirLw", "ItemParasolFall", "ItemShootAir",
            "ItemScrewDamage", "ItemScopeAirStart", "ItemScopeAirRapid", "ItemScopeAirFire", "ItemScopeAirEnd"):
    _k = retarget(_nm, ground=0.0)
    anim(_nm, len(_k) - 1, _k, keep_root=True)
# Screw Attack item: his own spin jump
_T = len(falcon_frames("ItemScrew")) - 1
anim("ItemScrew", _T, [(0, S), (3, tuck(60)), (_T, tuck(60 + 36 * (_T - 3)), "lin")], keep_root=True)
_T = len(falcon_frames("ItemScrewAir")) - 1
anim("ItemScrewAir", _T, [(0, FALL), (3, tuck(60)), (_T, tuck(60 + 36 * (_T - 3)), "lin")], keep_root=True)

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
     [(4, 10, [ball(4, 60, 0, 100, size=4.0, wdsk=22)]), (12, 14, leg("R", 5, 85, 40, 70, size=2.6, shin_dmg=5, elem=1))], iasa=23, ball=(3, 11))   # v61: flame kick = SA2's Fire Somersault (Flame Ring)


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
# v58: 40 -> 70 frames so the animation outlasts the dash (24) + end lag (44); ball only during the dash, then he uncurls
# and falls for the end lag. Hitbox f1-40 -> f1-24 (the end lag no longer hits).
move("HomingAttack", ["SpecialAirN", "SpecialN"], 90, [(0, FALL), (3, tuck(90)), (26, tuck(895), "lin"), (33, P(FALL, root=(1080, 0, 0)), "lin"),
                                                       (90, P(FALL, root=(1080, 0, 0)))], [(1, 24, [ball(8, 60, 40, 70)])], ball=(3, 27))
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
        for name, extra in INJECT.items():        # v61: the game's own commands at their own frames, plus ours
            a = acts[name]
            if name in scripts or a.cmds[-1]["name"] != "End Of Script" or any(c["name"] in ("Go To", "Subroutine", "Return", "Set Loop", "Execute Loop") for c in a.cmds):
                print("inject skipped (script rewritten or has jumps):", name)
                continue
            cur, seq = 1, []
            for idx, c in enumerate(a.cmds[:-1]):
                bts = bytearray(a.data[c["off"]:c["off"] + c["len"]])
                pc = sa.parse(bytes(bts))[0]
                if c["name"] == "Asynchronous Timer":
                    cur = pc["params"]["Frame"]
                elif c["name"] == "Synchronous Timer":
                    cur += pc["params"]["Frame"]
                else:
                    for key in [k_ for k_ in pc["params"] if k_.startswith("SFX ID")]:
                        if 60000 <= pc["params"][key] < 70000:
                            sa.set_param(bts, pc, key, GRUNT[pc["params"][key] % 5])
                    seq.append((cur, 1, idx, bytes(bts)))
            seq += [(f_, o_, 10000 + n_, b_) for n_, (f_, o_, b_) in enumerate(extra)]
            seq.sort(key=lambda x: x[:3])
            out, cur = b"", 1
            for f_, _, _, b_ in seq:
                if f_ != cur:
                    out += at(f_)
                    cur = f_
                out += b_
            scripts[name] = out + END
            log.append(f"| {name} | - | spin-ball model | body shown all through | ball from f{extra[0][0]} to f{extra[1][0]} |")
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
        _g = next(a_ for a_ in A if a_.actions[0] == "Guard")
        print("shield pose written:", write_shield_pose(pl_out, _g.solved[0][1]), "joints (was Captain Falcon's full-size guard pose)")
        with open(report, "w") as f:
            f.write("# v19 moves\n\n## New attacks (script written from scratch; game frames)\n\n")
            f.write("| Move | Actions | Total | IASA | Hit frames | Damage | Angle | BKB | KBG | Set KB | Size | Bone |\n|---|---|---|---|---|---|---|---|---|---|---|---|\n")
            for label, plan in PLAN.items():
                for f0, f1, hits in plan["events"]:
                    for h in hits:
                        f.write(f"| {label} | {', '.join(plan['actions'])} | {plan['total']} | {plan.get('iasa')} | {f0}-{f1} | {h.dmg} | {h.angle} | {h.bkb} | {h.kbg} | {h.wdsk} | {h.size} | {h.bone} |\n")
            f.write("\n## Specials (Falcon's scripts with graphics/sounds removed)\n\n" + "\n".join(log) + "\n")
        print("report", report)

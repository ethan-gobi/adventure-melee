"""Sonic proportions on Captain Falcon's skeleton (v05).

compute(joints, W, data) -> (K, factors, G)
  K        uniform scale from SA1 units to Melee units
  factors  {bone index: factor} applied to that bone's rest translation AND to its animation translation keys
  G        function mapping an SA1 (Blender) point to Melee world space with the soles on the floor

The skeleton's bone directions and rotations are not changed, only segment lengths, so every Falcon
animation keeps its shape while Sonic's limbs, torso and hip height get his own SA1 proportions.
"""
import numpy as np

K = 1.7  # SA1 Sonic is 10.08 units tall -> ~17.1 in Melee (Falcon ~21)


def S(p):
    """Blender (Z up, Sonic faces -X) -> Melee axes (Y up, faces +Z, character's left is +X)."""
    return np.array([-p[1], p[2], -p[0]], dtype=float)


def make_G(data):
    sole = min(S(c["p"])[1] for part in data["parts"] if part["node"] in ("052", "053", "062", "063")
               for t in part["tris"] for c in t["v"])
    return lambda p: K * S(p) - np.array([0.0, K * sole, 0.0])


def compute(joints, W, data):
    G = make_G(data)
    n = {k: G(v["pos"]) for k, v in data["nodes"].items()}
    T = [np.array([j.TX, j.TY, j.TZ]) for j, _, _ in joints]
    f = {}

    def length(a, b):
        return float(np.linalg.norm(n[a] - n[b]))

    # legs: Sonic left leg = nodes 057/058/060 (Melee +X side), right = 047/048/050
    # Falcon: bones 6/7/8/9/10/11 = left leg (+X), 12..17 = right leg
    hip_lat = abs(n["057"][0])
    f[6] = f[12] = hip_lat / abs(T[6][0])
    f[8] = length("057", "058") / np.linalg.norm(T[8])
    f[9] = length("058", "060") / np.linalg.norm(T[9])
    f[14] = length("047", "048") / np.linalg.norm(T[14])
    f[15] = length("048", "050") / np.linalg.norm(T[15])
    f[11] = f[17] = 0.6
    # hip height: bone 2 (XRotN) carries it; bone 61 (ThrowN) cancels it to stay on the floor
    target_hip_y = (n["057"][1] + n["047"][1]) / 2
    f[2] = (target_hip_y - T[3][1] - T[4][1] - T[6][1] * f[6]) / T[2][1]
    f[61] = f[2]
    bone4_y = T[2][1] * f[2] + T[3][1] + T[4][1]
    # torso: waist 18, bust 19, (20), shoulders 21/42 share one factor so the shoulders land on Sonic's
    sh_y = (n["025"][1] + n["036"][1]) / 2
    s = (sh_y - bone4_y) / (T[18][1] + T[19][1] + T[21][1])
    for b in (18, 19, 20, 21, 42):
        f[b] = s
    sh_lat = (abs(n["025"][0]) + abs(n["036"][0])) / 2
    f[22] = f[44] = (sh_lat - abs(T[21][0]) * s) / abs(T[22][0])
    for b in (37, 43, 60):
        f[b] = f[22]
    neck_y = n["022"][1]
    f[38] = (neck_y - (bone4_y + (T[18][1] + T[19][1]) * s)) / T[38][1]
    f[39] = 0.2
    f[40] = f[41] = 0.5
    f[5] = 0.5
    # arms: Sonic left arm = 036/037/039 (+X), right = 025/026/028; Falcon left 23/24/25, right 45/46/47
    f[24] = length("036", "037") / np.linalg.norm(T[24])
    f[25] = length("037", "039") / np.linalg.norm(T[25])
    f[46] = length("025", "026") / np.linalg.norm(T[46])
    f[47] = length("026", "028") / np.linalg.norm(T[47])
    for b in list(range(26, 37)) + list(range(48, 60)):
        f.setdefault(b, 0.6)
    return K, f, G


# Hurtboxes: (bone, p1, p2, radius). Same bones as Falcon's; sized to Sonic's v05 body.
HURTBOXES = {
    0: (4, (0.0, 0.0, 1.0), (0.0, 0.0, 0.0), 2.0),      # hips
    1: (19, (0.0, 0.3, 0.0), (0.0, 0.9, 0.0), 2.4),     # chest
    2: (39, (0.0, 2.2, 0.0), (0.0, 3.6, -0.5), 2.8),    # head (big SA1 head + quills)
    3: (45, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 0.9),     # right upper arm
    4: (23, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 0.9),     # left upper arm
    5: (46, (0.0, 0.0, 0.0), (2.6, 0.0, 0.0), 0.9),     # right forearm
    6: (24, (0.0, 0.0, 0.0), (2.6, 0.0, 0.0), 0.9),     # left forearm
    7: (13, (0.0, 0.0, 0.0), (1.9, 0.0, 0.0), 1.3),     # right thigh
    8: (7, (0.0, 0.0, 0.0), (1.9, 0.0, 0.0), 1.3),      # left thigh
    9: (14, (0.0, 0.0, 0.0), (3.3, 0.0, 0.0), 1.1),     # right shin
    10: (8, (0.0, 0.0, 0.0), (3.3, 0.0, 0.0), 1.1),     # left shin
}

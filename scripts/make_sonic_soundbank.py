"""Pick Sonic's sounds from the extracted SA1 banks, resample to 32 kHz, write WAVs and a manifest for build_iso.ps1 -SoundBank.

Usage: python make_sonic_soundbank.py <sa1snd dir> <out dir>
Bank order = sound ID - 560000 (Sonic's bank is number 56 in the m-ex sound table). Names from the X-Hax SADX modding wiki
(Player Effect Soundbanks, P_SONICTAILS bank 03). Voice clips are short gameplay grunts from V_SONICTAILS_E bank 06.
Output is for the owner's personal use only (game assets).
"""
import json
import os
import sys
import wave

import numpy as np

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
S = os.path.join(src, "p_sonictails", "b3_p%03d_l0_s00.wav")
V = os.path.join(src, "v_sonictails_e", "b6_p%03d_l0_s00.wav")
BANK = [("homing", S % 0),          # SE_HORMJUMP
        ("ldash_hold", S % 1),      # SE_LDASHHOLD
        ("ldash_launch", S % 2),    # SE_LDASH
        ("ldash_attack", S % 3),    # SE_LATTACK
        ("spin_charge", S % 5),     # SE_SPINCHARGE
        ("spin_release", S % 6),    # SE_SPINDASH
        ("swipe", S % 11),          # SE_M_ATTACK (tail whip whoosh)
        ("grunt1", V % 2), ("grunt2", V % 4), ("grunt3", V % 9), ("grunt4", V % 14), ("grunt5", V % 15),
        ("hurt1", V % 1), ("hurt2", V % 6)]
man = []
for i, (name, path) in enumerate(BANK):
    w = wave.open(path)
    r = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(float)
    if r > 32000:
        t = np.arange(0, len(x) * 32000 // r) * r / 32000.0
        x = np.interp(t, np.arange(len(x)), x)
        r = 32000
    x = x - x.mean()
    pk = np.abs(x).max() or 1.0
    x = x * min(1.0, 30000.0 / pk)
    dst = os.path.abspath(os.path.join(out, f"{i:02d}_{name}.wav"))
    with wave.open(dst, "wb") as o:
        o.setnchannels(1)
        o.setsampwidth(2)
        o.setframerate(r)
        o.writeframes(x.astype("<i2").tobytes())
    man.append({"index": i, "id": 560000 + i, "name": name, "wav": dst, "seconds": round(len(x) / r, 3)})
json.dump(man, open(os.path.join(out, "bank.json"), "w"), indent=1)
print(f"{len(man)} sounds, {sum(m['seconds'] for m in man):.2f} s, manifest {os.path.join(out, 'bank.json')}")

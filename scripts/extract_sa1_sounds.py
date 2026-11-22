"""Extract the samples ("tones") of Sonic Adventure's Dreamcast sound banks (.MLT -> SMPB/SMDB banks) to 16-bit WAV files.

Usage: python extract_sa1_sounds.py <file.MLT> <out_dir>
Format from the open-source dakrk/manatools (mpb.cpp/mpb.hpp, docs/mpb.hexpat): MLT = 32-byte header + 32-byte entries
(fourcc, bank, offset, size, ...); each SMPB/SMDB bank has programs -> 4 layers -> 48-byte splits; a split points at its tone
(ptr = u16 at +2 | (jump & 0x7F) << 16; jump bit 7 = 8-bit PCM; flags bit 0 = ADPCM, bit 1 = loop; loopEnd at +6 = length in
samples). AICA ADPCM (Yamaha 4-bit, low nibble first) is decoded here. Sample rate: AICA 44100 Hz * 2^OCT * (1 + FNS/1024).
Writes <bank>_<program>_<layer>_<split>.wav plus index.csv. Output is for the owner's personal use only (game assets).
"""
import csv
import math
import os
import struct
import sys
import wave

import numpy as np

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
d = open(src, "rb").read()
assert d[:4] == b"SMLT", "not an MLT file"
n = struct.unpack("<I", d[8:12])[0]

MAG = [1, 3, 5, 7, 9, 11, 13, 15]
SCALE = [0x0E6, 0x0E6, 0x0E6, 0x0E6, 0x133, 0x199, 0x200, 0x266]


def adpcm(buf, count):
    out_ = np.zeros(count, dtype=np.int16)
    sig, q = 0, 0x7F
    for i in range(count):
        b = buf[i >> 1] if (i >> 1) < len(buf) else 0
        nib = (b >> 4) & 0xF if i & 1 else b & 0xF
        x = min(0x7FFF, (q * MAG[nib & 7]) >> 3)       # magnitude first, then sign: rounding is symmetric (floor division drifts)
        sig = max(-32768, min(32767, sig + (-x if nib & 8 else x)))
        q = (q * SCALE[nib & 7]) >> 8
        q = max(0x7F, min(0x6000, q))
        out_[i] = sig
    return out_


rows, seen = [], set()
for e in range(n):
    ent = d[0x20 + e * 0x20: 0x40 + e * 0x20]
    fourcc = ent[:4]
    bank, off, size, ram_off, file_size = struct.unpack("<5I", ent[4:24])
    if fourcc not in (b"SMPB", b"SMDB") or ram_off == 0xFFFFFFFF or file_size in (0, 0xFFFFFFFF):
        continue
    b = d[ram_off: ram_off + file_size]
    if b[:4] not in (b"SMPB", b"SMDB"):
        print(f"entry {e}: bank data not at its offset, skipped")
        continue
    u32 = lambda o: struct.unpack("<I", b[o:o + 4])[0]   # noqa: E731
    p_prog, n_prog = u32(16), u32(20)
    for pi in range(n_prog):
        pp = u32(p_prog + 4 * pi)
        if pp == 0 or pp >= len(b):
            continue
        for li in range(4):
            lp = u32(pp + 4 * li)
            if lp == 0 or lp >= len(b):
                continue
            ns, ps = u32(lp), u32(lp + 4)
            for si in range(min(ns, 128)):
                s = b[ps + 48 * si: ps + 48 * (si + 1)]
                if len(s) < 48:
                    break
                jump, flags = s[0], s[1]
                ptr = struct.unpack("<H", s[2:4])[0] | ((jump & 0x7F) << 16)
                loop_start, loop_end = struct.unpack("<HH", s[4:8])
                pitch = struct.unpack("<H", s[12:14])[0]
                fns, octv = pitch & 0x7FF, (pitch >> 11) & 0xF
                octv = octv - 16 if octv & 8 else octv
                base_note = s[38]
                key = (bank, ptr)
                if key in seen or loop_end in (0, 0xFFFF) or ptr >= len(b):
                    continue
                seen.add(key)
                if flags & 1:
                    fmt = "adpcm"
                    pcm = adpcm(b[ptr: ptr + (loop_end + 1) // 2], loop_end)
                elif jump & 0x80:
                    fmt = "pcm8"
                    pcm = (np.frombuffer(b[ptr: ptr + loop_end], dtype=np.int8).astype(np.int16) * 256)
                else:
                    fmt = "pcm16"
                    pcm = np.frombuffer(b[ptr: ptr + 2 * loop_end], dtype="<i2")
                rate = int(round(44100 * (2.0 ** octv) * (1 + fns / 1024.0)))
                rate = max(4000, min(48000, rate))
                name = f"b{bank}_p{pi:03d}_l{li}_s{si:02d}.wav"
                with wave.open(os.path.join(out, name), "wb") as w:
                    w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
                    w.writeframes(pcm.astype("<i2").tobytes())
                rows.append([name, bank, pi, li, si, fmt, loop_end, rate, round(loop_end / rate, 3), bool(flags & 2), base_note, octv, fns])
with open(os.path.join(out, "index.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["file", "bank", "program", "layer", "split", "format", "samples", "rate", "seconds", "loop", "base_note", "oct", "fns"])
    w.writerows(rows)
print(f"{src}: {len(rows)} samples -> {out}")

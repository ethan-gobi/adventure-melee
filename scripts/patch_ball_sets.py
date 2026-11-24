"""Give Sonic's part-visibility tables the spin ball and the Chaos Emerald. In place + append.

Usage: python patch_ball_sets.py <PlSn.dat in> <PlSn.dat out> <number of body parts N>
The game hides every part listed in a set that is not the selected one and shows the selected set (default 0; changed by
the script command "Change Model State <group> <set>"). A part must therefore appear in only one set.
  group 0: set 0 = body parts 0..N-1, set 1 = spin ball (part N)
  group 1: set 0 = nothing,           set 1 = Chaos Emerald (part N+1)   -> emerald can show together with the body
The lookup count goes 1 -> 2, so all four tables (HighPoly, LowPoly and the two metal ones) get new 2-entry arrays.
"""
import struct, sys
src, dst, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
n_tails = int(sys.argv[4]) if len(sys.argv) > 4 else 0      # v69: Tails parts n+9 .. n+8+n_tails (group 5)
raw = bytearray(open(src, "rb").read())
fsize, dsize, nrel, nroot, nref = struct.unpack(">5I", raw[:20])
data = bytearray(raw[0x20:0x20 + dsize])
rel = list(struct.unpack(f">{nrel}I", raw[0x20 + dsize:0x20 + dsize + 4 * nrel]))
tail = bytes(raw[0x20 + dsize + 4 * nrel:])
u = lambda o: struct.unpack(">I", data[o:o + 4])[0]
root = struct.unpack(">II", tail[:8])[0]
L = u(root + 8)
if u(L) != 1:
    raise SystemExit("expected exactly one visibility group")
costumes = u(L + 4)


def add(b):
    global data
    while len(data) % 4:
        data += b"\0"
    o = len(data)
    data += b + bytes(-len(b) % 4)
    return o


# n = body parts 0..n-1. Then: n smile, n+1 ball, n+2 emerald, n+3 glint, n+4 trail, n+5 open mouth, n+6 figure-8, n+7 Insta-Shield,
# n+8 eyelids (v64; the model must have that part).
a_off, b_off = add(bytes(range(n + 1))), add(bytes([n + 1]))   # body set includes the smile (part n)
e_off, t_off = add(bytes([n + 2, n + 3])), add(bytes([n + 4]))
op_off = add(bytes([n + 5]))
f8_off, is_off = add(bytes([n + 6])), add(bytes([n + 7]))   # Peel-Out figure-8, Insta-Shield
lid_off = add(bytes([n + 8]))                                # v64: eyelids (blink, asleep)
tails_off = add(bytes([n + 9 + i for i in range(max(1, n_tails))]))
sets0 = add(struct.pack(">IIII", n + 1, a_off, 1, b_off)); rel += [sets0 + 4, sets0 + 12]                 # group 0: body | ball
sets1 = add(struct.pack(">IIIIII", 0, 0, 2, e_off, 1, is_off)); rel += [sets1 + 12, sets1 + 20]        # group 1: nothing | emerald + glint | Insta-Shield
sets2 = add(struct.pack(">IIIIII", 0, 0, 1, t_off, 1, f8_off)); rel += [sets2 + 12, sets2 + 20]        # group 2: nothing | trail | figure-8
sets3 = add(struct.pack(">IIII", 0, 0, 1, op_off)); rel += [sets3 + 12]                              # group 3: nothing | open mouth
sets4 = add(struct.pack(">IIII", 0, 0, 1, lid_off)); rel += [sets4 + 12]                             # group 4: nothing | eyelids
sets5 = add(struct.pack(">IIII", 0, 0, max(1, n_tails), tails_off)); rel += [sets5 + 12]            # group 5: nothing | Tails
t01 = add(struct.pack(">IIIIIIIIIIII", 2, sets0, 3, sets1, 3, sets2, 2, sets3, 2, sets4, 2, sets5)); rel += [t01 + 4, t01 + 12, t01 + 20, t01 + 28, t01 + 36, t01 + 44]
for ti, name in ((0, "HighPoly"), (1, "LowPoly"), (2, "MetalPoly"), (3, "MetalMain")):
    ptr = costumes + ti * 4
    if ptr not in rel:
        raise SystemExit(f"{name}: table pointer is not relocated")
    t = u(ptr)
    if ti < 2:
        new = t01
    else:
        new = add(struct.pack(">IIIIIIIIIIII", u(t), u(t + 4), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)); rel += [new + 4]      # metal: old group kept, empty groups 1-5
    data[ptr:ptr + 4] = struct.pack(">I", new)
    print(f"{name}: table 0x{t:X} -> 0x{new:X} (6 groups)")
data[L:L + 4] = struct.pack(">I", 6)
out = struct.pack(">5I", 0x20 + len(data) + 4 * len(rel) + len(tail), len(data), len(rel), nroot, nref) + bytes(raw[20:0x20]) + bytes(data) + struct.pack(f">{len(rel)}I", *rel) + tail
open(dst, "wb").write(out)
print(f"lookup groups 1 -> 6; Tails parts {n_tails}; {src}: {len(raw)} -> {len(out)} bytes")

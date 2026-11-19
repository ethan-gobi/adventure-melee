"""v04 package: Sonic's SA1 model on every costume, plus visibility tables pointing at the new parts.

Usage: python make_v04_package.py <in_package.zip> <sonic_costume.dat> <out_package.zip>
"""
import io
import os
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hsd import *  # noqa: E402,F401
from System import Array, Byte  # noqa: E402

src_zip, costume_dat, out_zip = sys.argv[1:4]
zin = zipfile.ZipFile(src_zip)
tmp = tempfile.mkdtemp(prefix="v04_")

# ---- fighter data: visibility tables
pl_path = os.path.join(tmp, "PlSn.dat")
open(pl_path, "wb").write(zin.read("PlSn.dat"))
pl = HSDRawFile(pl_path)
lookup = pl.Roots[0].Data.ModelLookupTables
cost = HSDRawFile(costume_dat)
root = [r for r in cost.Roots if r.Data.GetType().Name == "HSD_JOBJ"][0].Data
n_dobj = 0
d = root.Dobj
while d is not None:
    n_dobj += 1
    d = d.Next
table = lookup.CostumeVisibilityLookups.Array[0]
new = {"HighPoly": list(range(n_dobj)), "LowPoly": list(range(n_dobj)),
       "MetalMainModel": list(range(n_dobj)), "MetalPoly": list(range(n_dobj))}
for name, idx in new.items():
    entry = getattr(table, name).Array[0].LookupEntries.Array[0]
    old = list(entry.Entries) if entry.Entries is not None else []
    entry.Entries = Array[Byte](idx)
    entry.Count = len(idx)
    print(f"{name}: {len(old)} entries (max index {max(old) if old else '-'}) -> {len(idx)} entries (0..{n_dobj - 1})")
pl.Save(pl_path)

# ---- costumes: same Sonic model in every slot, root symbol renamed per costume
costumes = {}
for c in ("Nr", "Gy", "Wh", "Gr", "Bu"):
    inner = zipfile.ZipFile(io.BytesIO(zin.read(f"PlSn{c}.zip")))
    old_dat = HSDRawFile(inner.read(f"PlSn{c}.dat"))
    symbol = old_dat.Roots[0].Name
    f = HSDRawFile(costume_dat)
    f.Roots[0].Name = symbol
    p = os.path.join(tmp, f"PlSn{c}.dat")
    f.Save(p)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zc:
        zc.writestr(f"PlSn{c}.dat", open(p, "rb").read())
        for i in inner.infolist():
            if not i.filename.endswith(".dat"):
                zc.writestr(i.filename, inner.read(i.filename))   # CSP / stock icon pngs (still Falcon's)
    costumes[f"PlSn{c}.zip"] = buf.getvalue()
    print(f"costume {c}: symbol {symbol}, {os.path.getsize(p)} bytes")

with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zout:
    for i in zin.infolist():
        if i.filename == "PlSn.dat":
            zout.writestr(i.filename, open(pl_path, "rb").read())
        elif i.filename in costumes:
            zout.writestr(i.filename, costumes[i.filename])
        else:
            zout.writestr(i.filename, zin.read(i.filename))
print("wrote", out_zip)

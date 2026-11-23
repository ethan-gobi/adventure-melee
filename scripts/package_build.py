"""Make a Sonic package zip for build_iso.ps1 from an earlier package plus new fighter files.

Usage: python package_build.py <base package.zip> <out package.zip> <PlSn.dat> <PlSnAJ.dat> [<PlSnNr model .dat>]
PlSn.dat and PlSnAJ.dat replace the ones in the base package. With a model file, every costume zip (PlSnNr/Gy/Wh/Gr/Bu)
gets that model, its root symbols renamed to the ones the costume's old file used (the game looks them up by name).
"""
import io
import os
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hsd import HSDRawFile  # noqa: E402

base, out, pl, aj = sys.argv[1:5]
model = sys.argv[5] if len(sys.argv) > 5 else None
tmp = tempfile.mkdtemp(prefix="sonic_pkg_")


def costume(data, name):
    zin = zipfile.ZipFile(io.BytesIO(data))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zc:
        for i in zin.infolist():
            d = zin.read(i.filename)
            if i.filename.lower().endswith(".dat"):
                old_p, new_p = os.path.join(tmp, "old_" + i.filename), os.path.join(tmp, "new_" + i.filename)
                open(old_p, "wb").write(d)
                names = [r.Name for r in HSDRawFile(old_p).Roots]
                f = HSDRawFile(model)
                assert f.Roots.Count == len(names), (name, f.Roots.Count, names)
                for r, n in zip(f.Roots, names):
                    r.Name = n
                f.Save(new_p)
                d = open(new_p, "rb").read()
                print(f"  {name}/{i.filename}: {i.file_size} -> {len(d)} bytes, roots {names}")
            zc.writestr(i.filename, d)
    return buf.getvalue()


zin = zipfile.ZipFile(base)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
    for i in zin.infolist():
        d = zin.read(i.filename)
        if i.filename == "PlSn.dat":
            d = open(pl, "rb").read()
        elif i.filename == "PlSnAJ.dat":
            d = open(aj, "rb").read()
        elif model and i.filename.startswith("PlSn") and i.filename.endswith(".zip"):
            d = costume(d, i.filename)
        zout.writestr(i.filename, d)        # by name: reusing the old ZipInfo made an archive .NET (MexTool) could not open
print("package", out, os.path.getsize(out), "bytes; PlSn.dat", os.path.getsize(pl), "PlSnAJ.dat", os.path.getsize(aj))

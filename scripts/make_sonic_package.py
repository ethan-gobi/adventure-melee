"""Turn an exported Captain Falcon MexTool package into a 'Sonic' package with its own file names.

Usage: python make_sonic_package.py <falcon_package.zip> <sonic_package.zip>

v01 is a straight clone: same model, animations, moves and attributes as Falcon, but in
separate files (PlSn*.dat) so later versions can change Sonic without touching Falcon.
"""
import io
import re
import sys
import zipfile

src, dst = sys.argv[1], sys.argv[2]

# files that become Sonic's own copies
RENAME = {
    "PlCa.dat": "PlSn.dat",
    "PlCaAJ.dat": "PlSnAJ.dat",
    "GmRstMCa.dat": "GmRstMSn.dat",
    "PlCaDViWaitAJ.dat": "PlSnDViWaitAJ.dat",
    "EfCaData.dat": "EfSnData.dat",
}
COSTUMES = ["Nr", "Gy", "Wh", "Gr", "Bu"]  # Falcon's red costume exports without its model file, so it is left out
for c in COSTUMES:
    RENAME[f"PlCa{c}.zip"] = f"PlSn{c}.zip"

zin = zipfile.ZipFile(src)
yml = zin.read("fighter.yml").decode("utf-8")

for old, new in RENAME.items():
    if old.endswith(".dat"):
        yml = yml.replace(old, new)
for c in COSTUMES:
    yml = yml.replace(f"PlCa{c}.dat", f"PlSn{c}.dat")

# drop the broken red costume entry
yml, n = re.subn(r"- fileName: PlCaRe\.\r?\n(?:  .*\r?\n)+", "", yml)
assert n == 1, "red costume entry not found"
# visibility indices stay as Falcon's; team colours point at remaining costumes
yml = re.sub(r"nameText: .*", "nameText: Sonic", yml)
yml = re.sub(r"redCostumeIndex: \d+", "redCostumeIndex: 0", yml)
yml = re.sub(r"blueCostumeIndex: \d+", "blueCostumeIndex: 4", yml)
yml = re.sub(r"greenCostumeIndex: \d+", "greenCostumeIndex: 3", yml)

with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
    zout.writestr("fighter.yml", yml)
    for info in zin.infolist():
        name = info.filename
        if name == "fighter.yml" or name == "PlCaRe.zip":
            continue
        data = zin.read(name)
        if name in RENAME and name.endswith(".zip"):
            inner = zipfile.ZipFile(io.BytesIO(data))
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zc:
                for i in inner.infolist():
                    zc.writestr(i.filename.replace("PlCa", "PlSn"), inner.read(i.filename))
            data = buf.getvalue()
        zout.writestr(RENAME.get(name, name), data)

print("wrote", dst)
for line in yml.splitlines():
    if re.match(r"^(nameText|fighterDataPath|animFile|rstAnimFile|demoFile|effectFile|\w+CostumeIndex)|^- fileName", line):
        print("  ", line)

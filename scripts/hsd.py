"""Load HSDRaw (MexTool's .NET Framework build) into Python via pythonnet."""
import sys
import clr
LIB = r'C:\adventure-melee\tools\mexTool\lib'
sys.path.append(LIB)
clr.AddReference(LIB + r'\HSDRaw.dll')
import System  # noqa: E402
import HSDRaw  # noqa: E402
from HSDRaw import HSDRawFile  # noqa: E402
from HSDRaw.Common import HSD_JOBJ, HSD_DOBJ, HSD_POBJ, HSD_MOBJ, HSD_TOBJ  # noqa: E402


def jobj_list(root):
    """Depth-first joint list in file order (this is the bone index order Melee uses)."""
    out = []

    def walk(j, parent, depth):
        idx = len(out)
        out.append((j, parent, depth))
        c = j.Child
        while c is not None:
            walk(c, idx, depth + 1)
            c = c.Next
    walk(root, -1, 0)
    return out

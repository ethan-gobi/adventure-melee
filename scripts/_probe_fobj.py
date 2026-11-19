import sys
sys.path.insert(0, r'C:\adventure-melee\scripts')
from hsd import *
import System
from System.Reflection import BindingFlags
asm=[a for a in System.AppDomain.CurrentDomain.GetAssemblies() if a.GetName().Name=='HSDRaw'][0]
bf=BindingFlags.Public|BindingFlags.Instance|BindingFlags.Static|BindingFlags.DeclaredOnly
for n in ['HSDRaw.Common.Animation.HSD_Track','HSDRaw.Common.Animation.HSD_FOBJ','HSDRaw.Common.Animation.HSD_FigaTree','HSDRaw.Common.Animation.FigaTreeNode','HSDRaw.Tools.FOBJKey','HSDRaw.Tools.FOBJFrameDecoder','HSDRaw.Tools.FOBJFrameEncoder','HSDRaw.Melee.Pl.SBM_FighterAction']:
    t=asm.GetType(n)
    if t is None: print('missing',n); continue
    print('==',n)
    for c in t.GetConstructors(): print('  ctor',c)
    for m in t.GetMethods(bf):
        if not m.Name.startswith(('get_','set_')): print('  ','static' if m.IsStatic else '',m)
    for p in t.GetProperties(bf): print('  prop',p.PropertyType.Name,p.Name)
    for fl in t.GetFields(bf): print('  field',fl.FieldType.Name,fl.Name)

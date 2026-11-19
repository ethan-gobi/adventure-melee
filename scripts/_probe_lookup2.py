import sys
sys.path.insert(0, r'C:\adventure-melee\scripts')
from hsd import *
f = HSDRawFile(r'C:\adventure-melee\work\v03\PlSn_v03.dat')
t = f.Roots[0].Data.ModelLookupTables
c0 = t.CostumeVisibilityLookups.Array[0]
for name in ('HighPoly','LowPoly','MetalPoly','MetalMainModel'):
    tab = getattr(c0, name).Array[0]
    es = tab.LookupEntries.Array
    for e in es:
        print(name, 'entry type', type(e).__name__, [(p.Name) for p in e.GetType().GetProperties() if p.Name!='TrimmedSize'])
        print('   Entries:', list(e.Entries) if e.Entries is not None else None)

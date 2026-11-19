import sys
sys.path.insert(0, r'C:\adventure-melee\scripts')
from hsd import *
f = HSDRawFile(r'C:\adventure-melee\work\v03\PlSn_v03.dat')
fd = f.Roots[0].Data
t = fd.ModelLookupTables
print(type(t).__name__)
def dump(o, ind=1, depth=0):
    if o is None or depth > 4: return
    for p in o.GetType().GetProperties():
        if p.Name in ('TrimmedSize',) or p.GetIndexParameters().Length: continue
        try: v = p.GetValue(o)
        except Exception as e: print(' '*ind, p.Name, 'ERR'); continue
        tn = p.PropertyType.Name
        if v is None: print(' '*ind, p.Name, '= None')
        elif tn in ('Int32','Byte','Int16','Single','UInt32','Boolean','String','UInt16'): print(' '*ind, p.Name, '=', v)
        elif p.PropertyType.IsArray:
            arr = list(v)
            if arr and type(arr[0]).__name__ in ('int','float'): print(' '*ind, p.Name, '=', arr)
            else:
                print(' '*ind, p.Name, f'[{len(arr)}]')
                for i, e in enumerate(arr[:12]):
                    print(' '*(ind+1), f'#{i}', type(e).__name__); dump(e, ind+3, depth+1)
        else:
            print(' '*ind, p.Name, ':', tn); dump(v, ind+2, depth+1)
dump(t)

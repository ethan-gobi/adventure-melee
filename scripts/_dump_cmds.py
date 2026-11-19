import sys, re
sys.path.insert(0, 'scripts')
import subactions as sa
flt = re.compile(sys.argv[2])
for a in sa.load(sys.argv[1]):
    if a.name and flt.fullmatch(a.name):
        print(f"== {a.name} idx {a.index} len {len(a.data)}")
        for c in a.cmds:
            p = c['params']
            if c['name'] == 'Create Hitbox':
                s = f"id{p['ID']} b{p['Bone']} d{p['Damage']} sz{p['Size']} off({p['X-Offset']},{p['Y-Offset']},{p['Z-Offset']}) a{p['Angle']} kbg{p['Knockback Growth']} wk{p['Weight Set Knockback']} bkb{p.get('Base Knockback')} el{p.get('Element')}"
            else:
                s = ','.join(f"{k}={v}" for k, v in p.items())[:90]
            print(f"  {c['off']:3d} {c['name']}: {s}")

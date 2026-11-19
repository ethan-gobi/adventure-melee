import bpy
objs = sorted(bpy.context.scene.objects, key=lambda o: o.name)
def depth(o):
    d = 0
    while o.parent: o = o.parent; d += 1
    return d
for o in objs:
    if o.type not in ('MESH', 'EMPTY'): continue
    w = o.matrix_world.translation
    nv = len(o.data.vertices) if o.type == 'MESH' else 0
    mats = [m.name.split('_')[-1] for m in o.data.materials] if o.type == 'MESH' else []
    print(f"NODE {o.name:38} d={depth(o)} parent={(o.parent.name[:3] if o.parent else '-'):3} {o.type[:4]} v={nv:3} pos=({w.x:6.2f},{w.y:6.2f},{w.z:6.2f}) mats={mats}")

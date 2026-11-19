"""Blender: export every Sonic mesh part as world-space triangles (JSON) for the Melee model builder.

Run: blender --background preview/sonic_sa1_import.blend --python scripts/export_sonic_parts.py -- <out.json>
Coordinates are Blender's (Z up, Sonic faces -X); the builder converts axes.
"""
import json
import sys

import bpy

out = sys.argv[sys.argv.index("--") + 1]
deps = bpy.context.evaluated_depsgraph_get()
data = {"nodes": {}, "parts": [], "materials": {}}
for o in bpy.context.scene.objects:
    if o.type in ("MESH", "EMPTY"):
        data["nodes"][o.name[:3]] = {"name": o.name, "parent": o.parent.name[:3] if o.parent else None,
                                     "pos": list(o.matrix_world.translation)}
for m in bpy.data.materials:
    if not m.node_tree:
        continue
    img = None
    for n in m.node_tree.nodes:
        if n.type == "TEX_IMAGE" and n.image:
            img = n.image.name
    sm = getattr(m, "saio_material", None)
    props = {}
    if sm is not None:
        for k in dir(sm):
            if k.startswith(("_", "bl_", "rna_")):
                continue
            v = getattr(sm, k)
            if isinstance(v, (bool, int, float, str)):
                props[k] = v
            elif hasattr(v, "__len__") and len(v) <= 4:
                try:
                    props[k] = [float(x) for x in v]
                except Exception:
                    pass
    data["materials"][m.name] = {"image": img, "saio": props}

for o in sorted(bpy.context.scene.objects, key=lambda x: x.name):
    if o.type != "MESH":
        continue
    me = o.evaluated_get(deps).to_mesh()
    me.calc_loop_triangles()
    mw = o.matrix_world
    nm = mw.to_3x3().inverted().transposed()
    uv = me.uv_layers.active.data if me.uv_layers.active else None
    col = me.color_attributes.active_color if me.color_attributes else None
    tris = []
    for t in me.loop_triangles:
        corners = []
        for li, vi in zip(t.loops, t.vertices):
            p = mw @ me.vertices[vi].co
            n = (nm @ (me.corner_normals[li].vector if hasattr(me, "corner_normals") else me.vertices[vi].normal)).normalized()
            c = None
            if col is not None:
                c = list(col.data[li].color) if col.domain == "CORNER" else list(col.data[vi].color)
            corners.append({"p": list(p), "n": list(n), "uv": list(uv[li].uv) if uv else [0, 0], "c": c})
        mat = o.material_slots[t.material_index].material.name if o.material_slots else None
        tris.append({"m": mat, "v": corners})
    data["parts"].append({"node": o.name[:3], "name": o.name, "tris": tris})
with open(out, "w") as f:
    json.dump(data, f)
print("EXPORTED parts", len(data["parts"]), "tris", sum(len(p["tris"]) for p in data["parts"]))

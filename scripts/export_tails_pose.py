"""Blender: import SA1 Tails (Miles), pose him on one frame of an SA1 animation and export every mesh part as world-space
triangles (same JSON format as export_sonic_parts.py) for the Melee model builder.

Run: blender --background --python export_tails_pose.py -- <model.sa1mdl> <texture index.txt> <anim.saanim> <frame> <out.json>
"""
import json
import os
import sys

import addon_utils
import bpy

mdl, tex_index, anim, frame, out = sys.argv[sys.argv.index("--") + 1:][:5]
bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("bl_ext.user_default.sonic_adventure_io", default_set=False)
scene = bpy.context.scene
world = bpy.data.worlds.new("TailsTextures")
scene.saio_scene.texture_world = world
print("TEX IMPORT:", bpy.ops.saio.textures_importpack(filepath=os.path.abspath(tex_index), mode="SCENE"))
bpy.ops.saio.import_mdl(filepath=os.path.abspath(mdl), files=[{"name": os.path.basename(mdl)}], import_as_armature=True)
for op, kw in (("material_updateprops", {"targetmode": "ALL"}), ("material_updatetextures", {"targetmode": "ALL", "mode": "IMAGE"})):
    try:
        print(op, getattr(bpy.ops.saio, op)(**kw))
    except Exception as e:
        print(op, "FAILED:", e)
arm = [o for o in scene.objects if o.type == "ARMATURE"][0]
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
if anim != "-":
    bpy.ops.saio.import_node_anim(filepath=os.path.abspath(anim), files=[{"name": os.path.basename(anim)}])
    act = arm.animation_data.action
    print("anim frames", act.frame_range[:])
scene.frame_set(int(frame))
deps = bpy.context.evaluated_depsgraph_get()
data = {"nodes": {}, "parts": [], "materials": {}}
for m in bpy.data.materials:
    img = None
    if m.node_tree:
        for n in m.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image:
                img = n.image.name
    data["materials"][m.name] = {"image": img}
for o in sorted(scene.objects, key=lambda x: x.name):
    if o.type != "MESH":
        continue
    me = o.evaluated_get(deps).to_mesh()
    me.calc_loop_triangles()
    mw = o.matrix_world
    nm = mw.to_3x3().inverted().transposed()
    uv = me.uv_layers.active.data if me.uv_layers.active else None
    tris = []
    for t in me.loop_triangles:
        corners = []
        for li, vi in zip(t.loops, t.vertices):
            p = mw @ me.vertices[vi].co
            n = (nm @ me.corner_normals[li].vector).normalized()
            corners.append({"p": list(p), "n": list(n), "uv": list(uv[li].uv) if uv else [0, 0]})
        mat = o.material_slots[t.material_index].material.name if o.material_slots else None
        tris.append({"m": mat, "v": corners})
    data["parts"].append({"name": o.name, "tris": tris})
json.dump(data, open(out, "w"))
print("EXPORTED parts", len(data["parts"]), "tris", sum(len(p["tris"]) for p in data["parts"]), [p["name"] for p in data["parts"]])

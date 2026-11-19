"""Blender: sample an SA1 animation on Sonic's node hierarchy and save world matrices per frame (JSON).

Run: blender --background --python export_sa1_anim.py -- <model.sa1mdl> <anim.saanim> <out.json>
Matrices are Blender world space (Z up); the retarget step converts axes.
"""
import json
import os
import sys

import addon_utils
import bpy

mdl, anim, out = sys.argv[sys.argv.index("--") + 1:][:3]
bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("bl_ext.user_default.sonic_adventure_io", default_set=False)
bpy.ops.saio.import_mdl(filepath=mdl, files=[{"name": os.path.basename(mdl)}], import_as_armature=True)
arm = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"][0]
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
rest = {b.name[:3]: [list(r) for r in (arm.matrix_world @ b.matrix_local)] for b in arm.data.bones}
bpy.ops.saio.import_node_anim(filepath=anim, files=[{"name": os.path.basename(anim)}])
act = arm.animation_data.action
f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
frames = []
for f in range(f0, f1 + 1):
    bpy.context.scene.frame_set(f)
    frames.append({pb.name[:3]: [list(r) for r in (arm.matrix_world @ pb.matrix)] for pb in arm.pose.bones})
json.dump({"anim": os.path.basename(anim), "rest": rest, "frames": frames}, open(out, "w"))
print("EXPORTED", os.path.basename(anim), "frames", len(frames))

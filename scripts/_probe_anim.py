import bpy, sys, os, math
import addon_utils
bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("bl_ext.user_default.sonic_adventure_io", default_set=False)
mdl = r"C:\adventure-melee\extract\sa1\figure\sonic\models\s_kihon10_sonic.nja.sa1mdl"
bpy.ops.saio.import_mdl(filepath=mdl, files=[{"name": os.path.basename(mdl)}], import_as_armature=True)
arm = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE'][0]
print("ARM bones", len(arm.data.bones), "meshes", len([o for o in bpy.context.scene.objects if o.type=='MESH']))
bpy.context.view_layer.objects.active = arm; arm.select_set(True)
for an in ("s_run0", "s_walk0"):
    p = rf"C:\adventure-melee\extract\sa1\figure\sonic\models\{an}.nam.saanim"
    try:
        r = bpy.ops.saio.import_node_anim(filepath=p, files=[{"name": os.path.basename(p)}])
    except Exception as e:
        print("ANIMFAIL", an, e); continue
    print("ANIM", an, r, [a.name for a in bpy.data.actions])
for act in bpy.data.actions:
    rng = {}
    fcs = act.fcurves if hasattr(act, "fcurves") and len(getattr(act, "fcurves", [])) else []
    if not fcs:
        for layer in act.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    fcs = list(fcs) + list(cb.fcurves)
    for fc in fcs:
        if "rotation" not in fc.data_path: continue
        bone = fc.data_path.split('"')[1]
        vals = [k.co[1] for k in fc.keyframe_points]
        rng[bone] = max(rng.get(bone, 0), max(vals) - min(vals))
    print("ACT", act.name, "frames", act.frame_range[:])
    for b in sorted(rng):
        if rng[b] > 0.05: print(f"  ROT {b:28} range={math.degrees(rng[b]) if rng[b] < 7 else rng[b]:.0f}")

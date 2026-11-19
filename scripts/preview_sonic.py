"""Import SA1 Dreamcast Sonic into Blender, report stats and render previews.

Run: blender --background --python preview_sonic.py -- <model.sa1mdl> <texture index.txt> <out_dir>
"""
import math
import os
import sys

import bpy
sys.stdout.reconfigure(line_buffering=True)
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
model_path, tex_index, out_dir = [os.path.abspath(a) for a in argv[:3]]
os.makedirs(out_dir, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
import addon_utils
addon_utils.enable("bl_ext.user_default.sonic_adventure_io", default_set=False)
addon_utils.enable("cycles", default_set=False)
scene = bpy.context.scene

# textures first, so the materials can resolve their texture IDs
world = bpy.data.worlds.new("SonicTextures")
scene.saio_scene.texture_world = world
print("TEX IMPORT:", bpy.ops.saio.textures_importpack(filepath=tex_index, mode="SCENE"))
print("TEX COUNT:", len(world.saio_texture_list))

print("MDL IMPORT:", bpy.ops.saio.import_mdl(filepath=model_path, files=[{"name": os.path.basename(model_path)}]))

for op, kw in (("material_updateprops", {"targetmode": "ALL"}), ("material_updatetextures", {"targetmode": "ALL", "mode": "IMAGE"})):
    try:
        print(op, getattr(bpy.ops.saio, op)(**kw))
    except Exception as e:  # report, do not hide
        print(op, "FAILED:", e)

# ---- stats ----
meshes = [o for o in scene.objects if o.type == "MESH"]
arms = [o for o in scene.objects if o.type == "ARMATURE"]
empties = [o for o in scene.objects if o.type == "EMPTY"]
deps = bpy.context.evaluated_depsgraph_get()
verts = tris = 0
lo = Vector((1e9, 1e9, 1e9))
hi = Vector((-1e9, -1e9, -1e9))
for o in meshes:
    me = o.evaluated_get(deps).to_mesh()
    me.calc_loop_triangles()
    verts += len(me.vertices)
    tris += len(me.loop_triangles)
    for v in me.vertices:
        w = o.matrix_world @ v.co
        lo = Vector(map(min, lo, w))
        hi = Vector(map(max, hi, w))
print("STATS objects:", len(scene.objects), "meshes:", len(meshes), "armatures:", len(arms), "empties:", len(empties))
for a in arms:
    print("STATS armature", a.name, "bones:", len(a.data.bones))
    print("BONES:", [b.name for b in a.data.bones])
print("STATS verts:", verts, "tris:", tris, "materials:", len(bpy.data.materials), "images:", len(bpy.data.images))
print("STATS bounds min:", tuple(round(c, 3) for c in lo), "max:", tuple(round(c, 3) for c in hi))
for m in bpy.data.materials:
    img = None
    if m.node_tree:
        for n in m.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image:
                img = n.image.name
    print("MAT", m.name, "| image:", img)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, "sonic_sa1_import.blend"))

# ---- render ----
center = (lo + hi) / 2
size = max(hi - lo)
cam_data = bpy.data.cameras.new("Cam")
cam_data.type = "ORTHO"
cam_data.ortho_scale = size * 1.25
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
target = bpy.data.objects.new("Target", None)
target.location = center
scene.collection.objects.link(target)
con = cam.constraints.new("TRACK_TO")
con.target = target
con.track_axis = "TRACK_NEGATIVE_Z"
con.up_axis = "UP_Y"

sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), 0, math.radians(30))
scene.collection.objects.link(sun)
render_world = bpy.data.worlds.new("RenderWorld")
render_world.use_nodes = True
bg = render_world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.35, 0.38, 0.42, 1)
    bg.inputs[1].default_value = 1.0
scene.world = render_world

scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.render.image_settings.file_format = "PNG"
engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
print("ENGINES:", engines)

views = {"side": 0, "threequarter": 35, "back": 90, "front": 270}  # model faces -X
# CPU path tracing: this machine's GPU (Intel HD 620) cannot run Blender's GPU renderers headless.
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 24
scene.cycles.use_denoising = False
for name, deg in views.items():
    a = math.radians(deg)
    d = size * 3
    cam.location = center + Vector((math.sin(a) * d, -math.cos(a) * d, size * 0.15))
    scene.render.filepath = os.path.join(out_dir, f"sonic_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)

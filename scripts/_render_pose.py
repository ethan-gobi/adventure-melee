import bpy, sys, math, glob, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--")+1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 24
sun = bpy.data.objects.new("s", bpy.data.lights.new("s", "SUN")); sc.collection.objects.link(sun); sun.rotation_euler = (0.9, 0.1, 0.5); sun.data.energy = 3
w = bpy.data.worlds.new("w"); sc.world = w; w.color = (0.75, 0.75, 0.8)
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 8; sc.cycles.use_denoising = False
sc.render.resolution_x = 420; sc.render.resolution_y = 420
for obj in a:
    for o in list(sc.objects):
        if o.type == 'MESH': bpy.data.objects.remove(o)
    bpy.ops.wm.obj_import(filepath=obj, forward_axis='NEGATIVE_Z', up_axis='Y')
    for name, ang in (("front", -25), ("side", 90)):
        r = math.radians(ang); cam.location = Vector((math.sin(r) * 40, -math.cos(r) * 40, 9)); cam.rotation_euler = (math.radians(90), 0, r)
        sc.render.filepath = obj.replace(".obj", f"_{name}.png"); bpy.ops.render.render(write_still=True)
    print("RENDERED", os.path.basename(obj))

import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--")+1:]
obj, out = a[0], a[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=obj, forward_axis='NEGATIVE_Z', up_axis='Y')
o = bpy.context.selected_objects[0]
m = bpy.data.materials.new("m"); m.diffuse_color=(0.3,0.4,0.9,1); o.data.materials.append(m)
sc = bpy.context.scene
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type='ORTHO'; cam.data.ortho_scale=22
sun = bpy.data.objects.new("s", bpy.data.lights.new("s","SUN")); sc.collection.objects.link(sun); sun.rotation_euler=(0.8,0.2,0.6); sun.data.energy=4
w = bpy.data.worlds.new("w"); sc.world = w; w.color=(0.6,0.6,0.6)
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=8; sc.cycles.use_denoising=False
sc.render.resolution_x=500; sc.render.resolution_y=500
for name, ang in (("front", 0), ("side", 90)):
    r = math.radians(ang); cam.location = Vector((math.sin(r)*-40, -math.cos(r)*40, 9)); cam.rotation_euler=(math.radians(90),0,math.radians(-ang))
    sc.render.filepath = out + f"_{name}.png"; bpy.ops.render.render(write_still=True); print("RENDERED", name)

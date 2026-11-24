"""
31 — Аттракцион "Mini Crazy Mill". Rasm: attraction-images-park/Mini_Crazy_Mill.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/31-mini-crazy-mill/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png

Tuzilish (xarita kodi: src/map/GltfModel.tsx):
    base      — qimirlamaydigan qism: dumaloq supa (chiroqchali chet), oltin panjara, boshqaruv shkafi,
                markazdagi kulgili tegirmon-minora (yuz, burun, tishlar), qizil cherepitsa tom, mo'ri, laylak uyasi
    rotor     — aylanadigan qism: qizil-jigarrang disk va uning ustidagi uch transport
    lift0..2  — transportlar (rotor bolalari): kema (to'p bilan), qovoq-arava, pushti qurtcha — yengil sakraydi
Asl o'lcham metrda: diametri ~5.4 m, balandligi ~4.4 m. Old tomoni — Blender'da -Y.
"""
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Euler, Vector

HERE = Path(__file__).resolve().parent
OUT_GLB = HERE / 'model.glb'
OUT_BLEND = HERE / 'model.blend'
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PREVIEW_DIR = Path(argv[0]) if argv else HERE

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

PALETTE = {
    'gold': (0.8, 0.6, 0.25), 'stone': (0.6, 0.6, 0.6), 'disc': (0.45, 0.12, 0.08), 'cream': (0.93, 0.88, 0.78),
    'roof': (0.8, 0.08, 0.06), 'brown': (0.42, 0.24, 0.12), 'wood': (0.62, 0.38, 0.18), 'red': (0.88, 0.05, 0.05),
    'white': (0.96, 0.96, 0.96), 'blue': (0.1, 0.35, 0.85), 'black': (0.04, 0.04, 0.05), 'yellow': (0.98, 0.78, 0.08),
    'orange': (0.95, 0.5, 0.1), 'green': (0.15, 0.6, 0.2), 'pink': (0.95, 0.5, 0.7), 'beige': (0.85, 0.83, 0.76),
    'teal': (0.1, 0.6, 0.65), 'gray': (0.45, 0.45, 0.47), 'copper': (0.72, 0.45, 0.2),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.45
    if name in ('gold', 'copper'):
        bsdf.inputs['Metallic'].default_value = 0.3  # xaritada atrof-muhit aksi yo'q — yuqori metallik qoraygan ko'rinadi
    m.diffuse_color = (*rgb, 1)
    MATS[name] = m


def obj(bm, mats):
    me = bpy.data.meshes.new('m')
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(MATS[m])
    ob = bpy.data.objects.new('o', me)
    scene.collection.objects.link(ob)
    return ob


def box(size, loc, mat, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return obj(bm, [mat])


def cyl(r, h, loc, mat, segs=12, rot=(0, 0, 0), r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return obj(bm, [mat])


def sphere(r, loc, mat, segs=10, scale=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=max(4, segs // 2), radius=r)
    bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return obj(bm, [mat])


def tube(a, b, r, mat, segs=6):
    a, b = Vector(a), Vector(b)
    v = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=segs, radius1=r, radius2=r, depth=v.length)
    ob = obj(bm, [mat])
    ob.rotation_euler = v.to_track_quat('Z', 'Y').to_euler()
    ob.location = (a + b) / 2
    return ob


def join(name, objs, origin=(0, 0, 0)):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    scene.cursor.location = origin
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return ob


GEMS = ['red', 'blue', 'green', 'yellow']

# ---------- BASE ----------
R_FENCE, R_PLAT = 2.7, 2.25
p = [cyl(R_FENCE + 0.05, 0.05, (0, 0, 0.025), 'stone', 24)]
p.append(cyl(R_PLAT, 0.32, (0, 0, 0.16), 'stone', 24))
for k in range(16):  # chetdagi rangli chiroqchalar
    a = 2 * math.pi * k / 16
    p.append(sphere(0.05, (math.cos(a) * (R_PLAT + 0.01), math.sin(a) * (R_PLAT + 0.01), 0.16), GEMS[k % 4], 6))
FH = 0.95
for k in range(10):
    a0, a1 = 2 * math.pi * k / 10, 2 * math.pi * (k + 1) / 10
    x0, y0, x1, y1 = R_FENCE * math.cos(a0), R_FENCE * math.sin(a0), R_FENCE * math.cos(a1), R_FENCE * math.sin(a1)
    p.append(tube((x0, y0, 0.05), (x0, y0, FH + 0.12), 0.035, 'gold', 6))
    p.append(sphere(0.05, (x0, y0, FH + 0.15), 'gold', 6))
    if k == 7:  # janub — kirish
        continue
    for z in (0.15, FH + 0.05):
        p.append(tube((x0, y0, z), (x1, y1, z), 0.02, 'gold', 4))
    for j in range(1, 8):
        t = j / 8
        p.append(tube((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 0.15), (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, FH + 0.05), 0.01, 'gold', 4))
# boshqaruv shkafi (panjaradan tashqarida, old-o'ng)
p.append(box((0.45, 0.35, 0.95), (2.35, -2.25, 0.48), 'beige', (0, 0, 0.6)))
p.append(box((0.4, 0.3, 0.08), (2.35, -2.25, 0.99), 'gray', (0, 0, 0.6)))
# tegirmon-minora (markazda, qimirlamaydi): krem silindr, yuz
TZ0, TZ1 = 0.35, 2.75
p.append(cyl(0.72, TZ1 - TZ0, (0, 0, (TZ0 + TZ1) / 2), 'cream', 16, r2=0.62))
for sx in (-1, 1):  # ko'zlar, qoshlar, yonoqlar
    p.append(sphere(0.13, (sx * 0.24, -0.62, 2.05), 'white', 8, (1, 0.5, 1.2)))
    p.append(sphere(0.07, (sx * 0.22, -0.68, 2.03), 'blue', 6))
    p.append(box((0.32, 0.05, 0.08), (sx * 0.26, -0.64, 2.3), 'brown', (0, sx * -0.35, 0)))
    p.append(sphere(0.1, (sx * 0.42, -0.55, 1.75), 'pink', 6, (1, 0.4, 0.7)))
    # yon tomondagi suv g'ildiraklari (jigarrang, toshli)
    p.append(cyl(0.6, 0.28, (sx * 0.82, 0.05, 1.75), 'wood', 14, (0, math.pi / 2, 0)))
    for k in range(8):
        a = 2 * math.pi * k / 8
        p.append(sphere(0.05, (sx * 0.97, 0.05 + math.cos(a) * 0.5, 1.75 + math.sin(a) * 0.5), GEMS[k % 4], 5))
p.append(sphere(0.13, (0, -0.74, 1.8), 'red', 8))                        # burun
p.append(sphere(0.3, (0, -0.6, 1.45), 'red', 10, (1.1, 0.35, 0.55)))      # og'iz
for sx in (-0.07, 0.07):
    p.append(box((0.1, 0.03, 0.14), (sx, -0.71, 1.52), 'white'))          # tishlar
for k in range(12):  # minora sirtidagi rangli "toshlar"
    a = 2 * math.pi * k / 12 + 0.3
    if -2.2 < a - 2 * math.pi < -0.9 or -2.2 < a < -0.9:
        continue
    p.append(sphere(0.06, (math.cos(a) * 0.7, math.sin(a) * 0.7, 2.45 - (k % 3) * 0.5), GEMS[k % 4], 6))
# tom: jigarrang karniz, qizil cherepitsa konus (qatorlar), rangli chiroqlar
p.append(cyl(0.95, 0.12, (0, 0, TZ1 + 0.06), 'brown', 18))
for i in range(4):
    r0 = 0.88 - i * 0.2
    p.append(cyl(r0, 0.32, (0, 0, TZ1 + 0.28 + i * 0.27), 'roof', 16, r2=r0 - 0.18))
    for k in range(10 - i * 2):
        a = 2 * math.pi * k / (10 - i * 2) + i * 0.3
        p.append(sphere(0.045, (math.cos(a) * (r0 - 0.05), math.sin(a) * (r0 - 0.05), TZ1 + 0.25 + i * 0.27), GEMS[(k + i) % 4], 5))
# laylak uyasi va laylak
NZ = TZ1 + 1.22
p.append(cyl(0.3, 0.12, (0, 0, NZ), 'copper', 12))
p.append(sphere(0.18, (0.05, 0, NZ + 0.2), 'white', 10, (1.5, 0.8, 0.8)))
p.append(tube((0.25, 0, NZ + 0.25), (0.33, 0, NZ + 0.6), 0.04, 'white', 5))   # bo'yin
p.append(sphere(0.07, (0.35, 0, NZ + 0.63), 'white', 6))
p.append(cyl(0.025, 0.22, (0.47, 0, NZ + 0.6), 'orange', 5, (0, math.pi / 2, 0), r2=0.005))  # tumshuq
p.append(box((0.2, 0.3, 0.04), (-0.1, 0, NZ + 0.28), 'blue', (0, 0.2, 0)))     # qanot uchlari
# mo'ri (mis quvur + qizil qalpoq)
p.append(tube((0.55, 0.3, TZ1 + 0.4), (0.62, 0.3, TZ1 + 1.15), 0.08, 'copper', 8))
p.append(cyl(0.14, 0.25, (0.62, 0.3, TZ1 + 1.3), 'red', 8, r2=0.0))
base = join('base', p)

# ---------- ROTOR: disk va transportlar ----------
rotor = join('rotor', [cyl(2.05, 0.06, (0, 0, 0.35), 'disc', 24), cyl(0.85, 0.05, (0, 0, 0.4), 'brown', 16)])
VR = 1.45   # transportlar markazi radiusi


def ship():
    q = [box((1.35, 0.7, 0.42), (0, 0, 0.62), 'yellow')]
    q.append(box((1.4, 0.74, 0.12), (0, 0, 0.88), 'red'))                       # bort cheti
    q.append(box((1.36, 0.72, 0.12), (0, 0, 0.47), 'green'))                     # rangli tasma
    q.append(box((0.3, 0.5, 0.35), (0.6, 0, 0.78), 'yellow', (0, 0.35, 0)))      # tumshuq
    for x in (-0.35, 0.25):
        q.append(cyl(0.1, 0.06, (x, -0.36, 0.42), 'brown', 10, (math.pi / 2, 0, 0)))
    q.append(tube((-0.55, 0.15, 0.6), (-0.55, 0.15, 1.6), 0.05, 'wood', 6))      # machta
    q.append(box((0.25, 0.02, 0.3), (-0.42, 0.15, 1.35), 'white'))               # bayroq
    q.append(tube((0.25, 0, 0.95), (0.55, 0, 1.05), 0.06, 'wood', 8))            # to'p
    q.append(box((0.55, 0.5, 0.06), (-0.15, 0, 0.72), 'black'))                  # o'rindiq
    q.append(box((0.04, 0.3, 0.2), (-0.62, -0.36, 0.7), 'blue'))                 # oyna bezagi
    return q


def pumpkin():
    q = [sphere(0.48, (0, 0, 0.62), 'orange', 12, (1.25, 0.95, 0.75))]
    q.append(box((0.75, 0.62, 0.3), (0, 0, 0.95), 'yellow'))
    for sx in (-0.3, 0.3):
        q.append(cyl(0.1, 0.03, (sx, -0.31, 1.1), 'red', 10, (math.pi / 2, 0, 0)))  # rul
    q.append(box((0.6, 0.5, 0.06), (0, 0, 0.82), 'black'))
    for x in (-0.45, 0.45):
        q.append(cyl(0.14, 0.08, (x, -0.38, 0.45), 'black', 10, (math.pi / 2, 0, 0)))
    q.append(box((0.12, 0.08, 0.15), (-0.35, 0.3, 1.15), 'orange', (0.5, 0, 0)))  # tulki quloqlari
    q.append(box((0.12, 0.08, 0.15), (0.35, 0.3, 1.15), 'orange', (0.5, 0, 0)))
    return q


def worm():
    q = [sphere(0.42, (0, 0, 0.62), 'yellow', 10, (1.3, 0.9, 0.7))]
    q.append(sphere(0.38, (0.55, 0, 1.0), 'pink', 12))                            # bosh
    for sy in (-0.12, 0.12):
        q.append(sphere(0.1, (0.82, sy, 1.05), 'white', 6, (0.6, 1, 0.6)))
        q.append(sphere(0.05, (0.88, sy, 1.02), 'green', 5))
        q.append(tube((0.5, sy, 1.35), (0.45, sy * 2, 1.65), 0.02, 'green', 4))  # mo'ylov
        q.append(sphere(0.05, (0.45, sy * 2, 1.67), 'red', 5))
    q.append(box((0.55, 0.45, 0.06), (-0.15, 0, 0.82), 'black'))
    q.append(box((0.15, 0.15, 0.15), (0.75, -0.25, 0.65), 'blue'))                # chiroqcha
    return q


for k, fn in enumerate((ship, pumpkin, worm)):
    a = 2 * math.pi * k / 3 + math.pi / 2
    v = join(f'lift{k}', fn())
    v.rotation_euler = (0, 0, a + math.pi / 2)   # lokal +X — aylanish yo'nalishiga (urinma)
    v.location = (math.cos(a) * VR, math.sin(a) * VR, 0)
    v.parent = rotor

tris = sum(len(pg.vertices) - 2 for o in scene.objects if o.type == 'MESH' for pg in o.data.polygons)
print(f'MILL tris={tris}')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'MILL glb={OUT_GLB.stat().st_size // 1024} KB')

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.location = (4.2, -7.5, 4.5)
cam.rotation_euler = (Vector((0, 0, 1.6)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 900, 900
world = bpy.data.worlds.new('w')
world.color = (0.93, 0.95, 0.98)
scene.world = world
scene.render.filepath = str(PREVIEW_DIR / 'preview.png')
bpy.ops.render.render(write_still=True)
print('MILL preview', scene.render.filepath)

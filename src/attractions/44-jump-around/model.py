"""
44 — Аттракцион "Jump around". Low-poly model, rasm: attraction-images-park/Jump_Around.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/44-jump-around/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png

Tuzilish (xarita kodi shu nomlarga tayanadi, src/map/GltfModel.tsx):
    base     — qimirlamaydigan qism: sakkiz qirrali maydon, oltin panjara, ko'k supa
    rotor    — aylanadigan qism: qizil baraban, shaxmat konus, chiroqli minora, bayroqlar, projektor
    lift0..5 — jip-mashinalar egilgan sariq qo'li bilan (rotor bolalari): navbat bilan sakraydi
Asl o'lcham metrda: diametri ~8.2 m, balandligi ~5.6 m.
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
    'floor': (0.55, 0.56, 0.58), 'gold': (0.88, 0.68, 0.12), 'blue': (0.08, 0.18, 0.6), 'red': (0.85, 0.05, 0.05),
    'white': (0.95, 0.95, 0.95), 'black': (0.05, 0.05, 0.06), 'yellow': (0.98, 0.8, 0.08), 'orange': (0.98, 0.4, 0.05),
    'pink': (0.9, 0.15, 0.45), 'green': (0.05, 0.55, 0.3), 'steel': (0.62, 0.63, 0.65), 'tire': (0.1, 0.1, 0.11),
    'lamp': (1.0, 0.85, 0.4),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.4
    if name in ('gold', 'steel'):
        bsdf.inputs['Metallic'].default_value = 0.3  # xaritada atrof-muhit aksi yo'q — yuqori metallik qoraygan ko'rinadi
    if name == 'lamp':
        bsdf.inputs['Emission Color'].default_value = (*rgb, 1)
        bsdf.inputs['Emission Strength'].default_value = 0.8
    m.diffuse_color = (*rgb, 1)
    MATS[name] = m


def new_obj(name, bm, mats):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(MATS[m])
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob


def box(name, size, loc, mat, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return new_obj(name, bm, [mat])


def cyl(name, r, h, loc, mat, segs=10, rot=(0, 0, 0), r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return new_obj(name, bm, [mat])


def lathe(name, profile, segs, mat_of, mats):
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r < 1e-6:
            v = bm.verts.new((0, 0, z))
            rings.append([v] * segs)
        else:
            rings.append([bm.verts.new((r * math.cos(2 * math.pi * k / segs), r * math.sin(2 * math.pi * k / segs), z))
                          for k in range(segs)])
    for i in range(len(profile) - 1):
        for k in range(segs):
            k2 = (k + 1) % segs
            vs = []
            for v in (rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]):
                if v not in vs:
                    vs.append(v)
            if len(vs) >= 3:
                bm.faces.new(vs).material_index = mat_of(i, k)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return new_obj(name, bm, mats)


def beam(name, a, b, w, d, mat):
    a, b = Vector(a), Vector(b)
    v = b - a
    ob = box(name, (v.length, w, d), (0, 0, 0), mat)
    ob.rotation_euler = v.to_track_quat('X', 'Z').to_euler()
    ob.location = (a + b) / 2
    return ob


def join(name, objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return ob


# ---------- BASE ----------
R, H0 = 4.1, 0.25
p = [lathe('floor', [(R, 0), (R, H0), (0, H0)], 12, lambda i, k: 0, ['floor'])]
FH, RF = 1.0, R - 0.12
for k in range(12):
    a0, a1 = 2 * math.pi * k / 12, 2 * math.pi * (k + 1) / 12
    x0, y0, x1, y1 = RF * math.cos(a0), RF * math.sin(a0), RF * math.cos(a1), RF * math.sin(a1)
    p.append(cyl('post', 0.05, FH + 0.1, (x0, y0, H0 + (FH + 0.1) / 2), 'gold', 6))
    p.append(cyl('knob', 0.07, 0.1, (x0, y0, H0 + FH + 0.12), 'gold', 6))
    if k == 9:  # janub — kirish
        continue
    for z in (H0 + 0.08, H0 + FH - 0.03):
        p.append(beam('rail', (x0, y0, z), (x1, y1, z), 0.035, 0.035, 'gold'))
    n = int(math.hypot(x1 - x0, y1 - y0) / 0.15)
    for j in range(1, n):
        t = j / n
        p.append(box('bar', (0.02, 0.02, FH - 0.1), (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, H0 + FH / 2), 'gold'))
p.append(lathe('platform', [(2.1, H0), (2.1, H0 + 0.4), (1.9, H0 + 0.45), (0, H0 + 0.45)], 8, lambda i, k: 0, ['blue']))
base = join('base', p)

# ---------- ROTOR ----------
q = []
Z1 = H0 + 0.45
q.append(lathe('drum', [(1.55, Z1), (1.55, Z1 + 1.1), (0, Z1 + 1.1)], 12, lambda i, k: 0, ['red']))
for k in range(6):  # baraban panellaridagi yozuv o'rni (oq-rangli tasma)
    a = k * math.pi / 3 + math.pi / 6
    q.append(box('logo', (0.04, 0.7, 0.25), (math.cos(a) * 1.57, math.sin(a) * 1.57, Z1 + 0.5), 'white', (0, 0, a)))
Z2 = Z1 + 1.1
# shaxmat naqshli kesik konus va qizil-sariq "ZAMPERLA" harflari o'rnida bloklar
q.append(lathe('checker', [(1.45, Z2), (1.25, Z2 + 0.45), (1.05, Z2 + 0.9), (0.95, Z2 + 0.9), (0, Z2 + 0.95)], 16,
               lambda i, k: (i + k) % 2 if i < 2 else 1, ['white', 'black']))
for k in range(8):
    a = k * math.pi / 4
    q.append(box('letter', (0.06, 0.3, 0.36), (math.cos(a) * 1.33, math.sin(a) * 1.33, Z2 + 0.45),
                 'red' if k % 2 else 'yellow', (0, -0.38, a)))
# chiroqli minora: qizil-oq yo'l-yo'l piramida, chiroqchalar
Z3 = Z2 + 0.95
q.append(lathe('spire', [(0.6, Z3), (0.45, Z3 + 0.6), (0.3, Z3 + 1.2), (0.12, Z3 + 1.75), (0, Z3 + 1.8)], 8,
               lambda i, k: k % 2, ['red', 'white']))
for k in range(8):
    a = k * math.pi / 4 + math.pi / 8
    for j in range(4):
        r = 0.55 - j * 0.12
        q.append(box('bulb', (0.06, 0.06, 0.06), (math.cos(a) * r, math.sin(a) * r, Z3 + 0.25 + j * 0.42), 'lamp'))
q.append(cyl('mast', 0.03, 0.4, (0, 0, Z3 + 2.0), 'steel', 6))
q.append(box('spot', (0.35, 0.12, 0.22), (0, 0, Z3 + 2.25), 'steel'))
# bayroqlar
for k, col in enumerate(['blue', 'yellow', 'black', 'green']):
    a = k * math.pi / 2 + math.pi / 4
    x, y = math.cos(a) * 0.8, math.sin(a) * 0.8
    q.append(cyl('fpole', 0.02, 1.6, (x, y, Z3 + 0.8), 'steel', 5))
    q.append(box('flag', (0.03, 0.55, 0.35), (x - math.sin(a) * 0.28, y + math.cos(a) * 0.28, Z3 + 1.4), col, (0, 0, a)))
rotor = join('rotor', q)

# ---------- Jiplar ----------
CAR_R = 2.75
COLS = [('pink', 'white'), ('blue', 'yellow'), ('yellow', 'green'), ('orange', 'white'), ('yellow', 'black'),
        ('orange', 'red')]


def jeep(n, body, accent, yaw):
    """Jip: markazi (0,0), lokal +Y — harakat yo'nalishi; keyin yaw ga burilib CAR_R ga suriladi"""
    c = [box('chassis', (1.05, 1.6, 0.28), (0, 0, 0.65), body)]
    c.append(box('hood', (0.95, 0.45, 0.25), (0, 0.6, 0.85), body))
    c.append(box('trunk', (1.0, 0.35, 0.32), (0, -0.65, 0.88), accent))
    c.append(box('engine', (0.5, 0.25, 0.3), (0, -0.9, 0.62), 'steel'))
    for sx in (-0.55, 0.55):
        for sy in (-0.55, 0.55):
            c.append(cyl('wheel', 0.3, 0.22, (sx, sy, 0.3), 'tire', 10, (0, math.pi / 2, 0)))
            c.append(cyl('spring', 0.06, 0.35, (sx * 0.75, sy, 0.6), 'red', 6))
    for sy in (-0.15, 0.3):  # ikki qator o'rindiq, rul
        c.append(box('seat', (0.8, 0.3, 0.1), (0, sy, 0.86), 'black'))
        c.append(box('back', (0.8, 0.06, 0.28), (0, sy - 0.16, 1.0), body))
    c.append(cyl('wheel_s', 0.13, 0.04, (0.2, 0.48, 1.08), 'black', 10, (0.9, 0, 0)))
    c.append(box('rollbar', (0.9, 0.04, 0.04), (0, 0.05, 1.3), 'steel'))
    for sx in (-0.45, 0.45):
        c.append(box('rollpost', (0.04, 0.04, 0.4), (sx, 0.05, 1.1), 'steel'))
    for k in range(4):
        c.append(box('light', (0.12, 0.03, 0.08), (-0.3 + k * 0.2, 0.84, 0.78), 'lamp'))
    c.append(box('num', (0.02, 0.3, 0.3), (0.53, 0.1, 0.72), 'white'))
    # egilgan sariq qo'l: jipning ichki tomonidan barabanga (rotor bilan birga, jip bilan sakraydi)
    arm_pts = [(-0.5, 0, 0.62), (-1.0, 0, 0.75), (-1.35, 0, 1.0), (-1.45, 0, 1.25)]
    for a, b in zip(arm_pts[:-1], arm_pts[1:]):
        c.append(beam('arm', a, b, 0.11, 0.11, 'yellow'))
    ob = join(f'lift{n}', c)
    return ob


for n in range(6):
    a = n * math.pi / 3
    car = jeep(n, *COLS[n], a)
    # jip markazdan CAR_R da, ichki tomoni (qo'li) markazga, burni aylanish yo'nalishiga
    car.rotation_euler = (0, 0, a)
    car.location = (math.cos(a) * CAR_R, math.sin(a) * CAR_R, 0)
    car.parent = rotor
# lokal o'qlar: jip uchun "ichki tomon" -X, burni +Y — rotor bilan birga soat teskarisiga aylanadi

tris = sum(len(pg.vertices) - 2 for o in scene.objects if o.type == 'MESH' for pg in o.data.polygons)
print(f'JUMP_AROUND tris={tris}')

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'JUMP_AROUND glb={OUT_GLB.stat().st_size // 1024} KB')

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.location = (9, -10, 7.5)
cam.rotation_euler = (Vector((0, 0, 1.8)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 1000, 900
world = bpy.data.worlds.new('w')
world.color = (0.93, 0.95, 0.98)
scene.world = world
scene.render.filepath = str(PREVIEW_DIR / 'preview.png')
bpy.ops.render.render(write_still=True)
print('JUMP_AROUND preview', scene.render.filepath)

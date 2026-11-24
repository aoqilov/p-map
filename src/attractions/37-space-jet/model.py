"""
37 — Аттракцион "Space Jet" (planda: "Mini jet 6"). Low-poly model, rasm: attraction-images-park/Space_Jet.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/37-space-jet/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png

Tuzilish (xarita kodi shu nomlarga tayanadi, src/map/GltfModel.tsx):
    base     — qimirlamaydigan qism: sakkiz qirrali maydon, oltin panjara, markaziy supa
    rotor    — aylanadigan qism: raketa (pushti-oq), olovli ustun
    arm0..5  — qo'l uyasi (bo'sh tugun, rotor bolasi)
    tilt0..5 — ko'k qo'l: origin — sharnirda, ko'tariladi/tushadi
    hang0..5 — qo'l uchidagi kosmik mashina (tilt bolasi): doim gorizontal turadi
Asl o'lcham metrda: diametri ~9 m, balandligi ~6.4 m.
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
    'floor': (0.62, 0.63, 0.65), 'gold': (0.85, 0.65, 0.15), 'blue': (0.1, 0.3, 0.72), 'navy': (0.08, 0.15, 0.4),
    'pink': (0.95, 0.5, 0.78), 'white': (0.95, 0.95, 0.96), 'red': (0.85, 0.05, 0.08), 'orange': (0.98, 0.45, 0.05),
    'yellow': (0.98, 0.8, 0.1), 'green': (0.45, 0.8, 0.12), 'purple': (0.55, 0.2, 0.6), 'magenta': (0.85, 0.2, 0.6),
    'dark': (0.12, 0.12, 0.14), 'steel': (0.65, 0.66, 0.68),
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
R, H0 = 4.5, 0.2
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
    L = math.hypot(x1 - x0, y1 - y0)
    for j in range(1, int(L / 0.15)):
        t = j / int(L / 0.15)
        p.append(box('bar', (0.02, 0.02, FH - 0.1), (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, H0 + FH / 2), 'gold'))
p.append(box('platform', (2.4, 2.4, 0.45), (0, 0, H0 + 0.225), 'navy'))
p.append(box('plate', (2.2, 2.2, 0.02), (0, 0, H0 + 0.46), 'steel'))
base = join('base', p)

# ---------- ROTOR: olovli ustun va raketa ----------
q = []
FIRE = ['orange', 'red', 'yellow', 'blue']
q.append(lathe('column', [(0.75, 0.65), (0.75, 2.4), (0.72, 2.4)], 16, lambda i, k: [0, 0, 1, 0, 3, 1, 0, 2][k % 8],
               ['orange', 'red', 'yellow', 'blue']))
q.append(cyl('hub', 0.95, 0.35, (0, 0, 1.3), 'blue', 12))
# raketa: oq-pushti tana, qizil kabina oynasi, yon qanotlar, tepada ko'k chiziq
q.append(lathe('rocket', [(0.95, 2.4), (1.1, 2.9), (1.1, 3.9), (0.95, 4.7), (0.65, 5.5), (0.3, 6.1), (0, 6.35)], 12,
               lambda i, k: 1 if i >= 3 else 0, ['white', 'pink']))
q.append(box('window', (0.12, 0.9, 0.95), (-1.02, 0, 3.95), 'red', (0, -0.2, 0)))
q.append(box('panel', (0.1, 1.0, 0.6), (-1.08, 0, 3.15), 'dark'))
for s in (-0.3, 0, 0.3):
    for z in (3.0, 3.3):
        q.append(box('light', (0.04, 0.16, 0.12), (-1.14, s, z), 'yellow'))
q.append(box('stripe', (0.1, 0.25, 1.0), (-0.78, 0, 5.0), 'blue', (0, -0.42, 0)))
for k in range(2):  # yon qanotlar (oq, uchi pushti)
    sy = -1 if k else 1
    q.append(box('wing', (0.9, 0.16, 1.2), (0.05, sy * 1.25, 2.95), 'white'))   # tik suzgich-qanot
    q.append(box('wingtop', (0.75, 0.17, 0.45), (0.12, sy * 1.25, 3.75), 'pink', (0, -0.35, 0)))
    for j in range(5):
        q.append(box('vent', (0.05, 0.18, 0.4), (-0.3 + j * 0.13, sy * 1.25, 2.6), 'dark'))
q.append(cyl('tip', 0.06, 0.25, (0, 0, 6.45), 'pink', 8))
rotor = join('rotor', q)

# ---------- Qo'llar va kosmik mashinalar ----------
HINGE_Z, HINGE_R, ARM_L = 1.3, 0.9, 2.2
REST = math.radians(14)   # tinch holatda qo'l pastga og'gan
CAR_COLS = [('blue', 'green'), ('orange', 'red'), ('magenta', 'blue'), ('purple', 'green'), ('blue', 'orange'),
            ('yellow', 'red')]


def car(body, accent):
    """Kosmik mashina: lokal +Y — harakat yo'nalishi, markazi origin, tagi z≈-0.55"""
    c = [box('hull', (1.15, 1.9, 0.45), (0, 0, -0.35), body)]
    c.append(box('nose', (0.95, 0.6, 0.3), (0, 1.15, -0.4), accent, (0.3, 0, 0)))
    c.append(box('tail', (1.2, 0.35, 0.5), (0, -1.05, -0.28), accent))
    for sx in (-0.55, 0.55):
        c.append(box('fin', (0.12, 0.7, 0.35), (sx, -0.85, -0.05), accent))
        c.append(cyl('lamp', 0.08, 0.05, (sx * 0.7, -1.24, -0.3), 'orange', 8, (math.pi / 2, 0, 0)))
    for y in (-0.35, 0.35):  # ikki qator o'rindiq
        c.append(box('seat', (0.85, 0.42, 0.12), (0, y, -0.08), 'dark'))
        c.append(box('back', (0.85, 0.08, 0.38), (0, y - 0.22, 0.1), body))
    c.append(box('bar', (0.9, 0.03, 0.03), (0, 0.6, 0.15), 'steel'))
    return c


for n in range(6):
    yaw = n * math.pi / 3 + math.pi / 6
    arm = bpy.data.objects.new(f'arm{n}', None)
    scene.collection.objects.link(arm)
    arm.parent = rotor
    arm.location = (math.cos(yaw) * HINGE_R, math.sin(yaw) * HINGE_R, HINGE_Z)
    arm.rotation_euler = (0, 0, yaw)

    t = [box('arm', (ARM_L, 0.24, 0.26), (ARM_L / 2, 0, 0), 'blue')]
    t.append(cyl('hinge', 0.2, 0.4, (0, 0, 0), 'navy', 10, (math.pi / 2, 0, 0)))
    t.append(beam('rod', (0.3, 0.12, -0.6), (1.9, 0.12, -0.05), 0.05, 0.05, 'steel'))  # tirgak
    for k in range(4):
        t.append(box('stud', (0.08, 0.27, 0.08), (0.5 + k * 0.6, 0, 0.14), FIRE[k % 3]))
    tilt = join(f'tilt{n}', t)
    tilt.parent = arm
    tilt.rotation_euler = (0, REST, 0)

    hang = join(f'hang{n}', car(*CAR_COLS[n]))
    hang.parent = tilt
    hang.location = (ARM_L, 0, 0)
    # mashina aylanish yo'nalishiga qaragan (lokal +Y), og'ish qaytarilgan — gorizontal
    hang.rotation_euler = (0, -REST, 0)

tris = sum(len(pg.vertices) - 2 for o in scene.objects if o.type == 'MESH' for pg in o.data.polygons)
print(f'SPACE_JET tris={tris}')

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'SPACE_JET glb={OUT_GLB.stat().st_size // 1024} KB')

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.location = (-11, -10, 8)
cam.rotation_euler = (Vector((0, 0, 2.4)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
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
print('SPACE_JET preview', scene.render.filepath)

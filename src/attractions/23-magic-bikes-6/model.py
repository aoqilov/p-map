"""
23 — Аттракцион "Magic bikes 6". Low-poly model, rasm: attraction-images-park/Magic_Bikes.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/23-magic-bikes-6/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png

Tuzilish (xarita kodi shu nomlarga tayanadi, src/map/GltfModel.tsx):
    base     — qimirlamaydigan qism: tosh poydevor, panjara, tosh minora, konus tom, yozuvlar
    rotor    — aylanadigan qism: minora atrofidagi halqa, 6 ta to'rsimon qo'l, tayanchlar
    lift0..5 — ikki o'rindiqli savatlar (rotor bolalari): yengil ko'tarilib-tushadi
    spin0..5 — qo'l uchidagi parraklar (rotor bolalari): o'z o'qi atrofida aylanadi
Asl o'lcham metrda: diametri ~9 m (savatlar bilan), balandligi ~8.2 m. Old tomoni — Blender'da -Y.
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
    'stone': (0.62, 0.56, 0.46), 'stone_dk': (0.46, 0.41, 0.34), 'dirt': (0.6, 0.52, 0.4), 'iron': (0.27, 0.26, 0.25),
    'roof': (0.2, 0.2, 0.21), 'blade': (0.86, 0.86, 0.83), 'seat': (0.5, 0.45, 0.37), 'wood': (0.4, 0.25, 0.15),
    'gold': (0.82, 0.66, 0.32), 'red': (0.75, 0.1, 0.08), 'green': (0.15, 0.55, 0.22), 'white': (0.95, 0.95, 0.95),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.7 if name in ('stone', 'stone_dk', 'dirt', 'wood') else 0.5
    if name in ('iron', 'gold'):
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


def cyl(name, r, h, loc, mat, segs=12, r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bmesh.ops.translate(bm, vec=(loc[0], loc[1], loc[2] + h / 2), verts=bm.verts)
    return new_obj(name, bm, [mat])


def beam(name, a, b, w, mat):
    """Ikki nuqta orasidagi to'rtburchak to'sin"""
    a, b = Vector(a), Vector(b)
    d = b - a
    ob = box(name, (d.length, w, w), (0, 0, 0), mat)
    ob.rotation_euler = d.to_track_quat('X', 'Z').to_euler()
    ob.location = (a + b) / 2
    return ob


def join(name, objs, apply=True):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.name = name
    if apply:
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return ob


# ---------- BASE ----------
S, H0 = 5.6, 0.6       # tosh poydevor tomoni va balandligi
TR, TOWER_TOP = 0.72, 6.3
p = []
p.append(box('plinth', (S, S, H0), (0, 0, H0 / 2), 'stone'))
p.append(box('plinth_cap', (S + 0.06, S + 0.06, 0.08), (0, 0, H0 - 0.04), 'stone_dk'))
p.append(box('dirt', (S - 0.3, S - 0.3, 0.04), (0, 0, H0 + 0.02), 'dirt'))
# minora ostidagi tosh supa va qora sakkiz qirrali halqa
p.append(box('pedestal', (2.2, 2.2, 0.9), (0, 0, H0 + 0.45), 'stone'))
p.append(cyl('ring', 0.95, 0.35, (0, 0, H0 + 0.9), 'roof', 8))
# minora: tosh silindr, tepasida tishli halqa va qora konus tom
p.append(cyl('tower', TR, TOWER_TOP - H0 - 1.25, (0, 0, H0 + 1.25), 'stone', 14))
for k in range(10):  # tosh qatorlari (gorizontal chiziqlar)
    p.append(cyl('course', TR + 0.015, 0.04, (0, 0, H0 + 1.5 + k * 0.45), 'stone_dk', 14))
p.append(cyl('crown', TR + 0.12, 0.35, (0, 0, TOWER_TOP), 'stone', 14))
for k in range(8):
    a = k * math.pi / 4
    p.append(box('merlon', (0.22, 0.16, 0.2), (math.cos(a) * (TR + 0.05), math.sin(a) * (TR + 0.05), TOWER_TOP + 0.45), 'stone', (0, 0, a)))
p.append(cyl('roof', TR + 0.35, 1.9, (0, 0, TOWER_TOP + 0.35), 'roof', 14, 0.02))

# Panjara (oltin), old tomonda kirish; ikkita yozuv taxtachasi
FH, edge = 0.95, S / 2 - 0.12
for (x0, y0), (x1, y1) in [((-edge, -edge), (edge, -edge)), ((edge, -edge), (edge, edge)),
                           ((edge, edge), (-edge, edge)), ((-edge, edge), (-edge, -edge))]:
    L = math.hypot(x1 - x0, y1 - y0)
    ang = math.atan2(y1 - y0, x1 - x0)
    front = y0 == y1 == -edge
    for k in range(int(L / 0.2) + 1):
        t = k / int(L / 0.2)
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        if front and -0.5 < x < 0.5:
            continue
        p.append(cyl('bar', 0.016, FH, (x, y, H0), 'gold', 5))
    for z in (H0 + 0.1, H0 + FH - 0.02):
        if front:
            for sx in (-1, 1):
                seg = edge - 0.5
                p.append(box('rail', (seg, 0.04, 0.04), (sx * (0.5 + seg / 2), y0, z), 'gold'))
        else:
            p.append(box('rail', (L, 0.04, 0.04), ((x0 + x1) / 2, (y0 + y1) / 2, z), 'gold', (0, 0, ang)))
p.append(box('sign_red', (0.9, 0.03, 0.4), (0.9, -edge - 0.03, H0 + 0.55), 'red'))
p.append(box('sign_red_txt', (0.7, 0.031, 0.06), (0.9, -edge - 0.035, H0 + 0.55), 'white'))
p.append(box('sign_green', (0.03, 0.8, 0.35), (edge + 0.03, -1.2, H0 + 0.6), 'green'))
p.append(box('booth', (0.35, 0.6, 1.0), (edge - 0.35, -1.6, H0 + 0.5), 'green'))
base = join('base', p)

# ---------- ROTOR: halqa, 6 ta to'rsimon qo'l, tayanchlar ----------
ARM_Z, ARM_R0, ARM_R1 = 4.55, TR + 0.05, 3.35
q = []
q.append(cyl('collar', TR + 0.12, 0.45, (0, 0, ARM_Z - 0.3), 'iron', 14))
q.append(cyl('collar_lo', TR + 0.1, 0.25, (0, 0, ARM_Z - 1.9), 'iron', 14))
for n in range(6):
    a = n * math.pi / 3
    ca, sa = math.cos(a), math.sin(a)
    P = lambda r, z, s=0.0: (ca * r - sa * s, sa * r + ca * s, z)
    for s in (-0.14, 0.14):  # ikki bo'ylama to'sin (tepa va past)
        q.append(beam('top', P(ARM_R0, ARM_Z + 0.12, s), P(ARM_R1, ARM_Z + 0.12, s), 0.05, 'iron'))
        q.append(beam('bot', P(ARM_R0, ARM_Z - 0.18, s), P(ARM_R1, ARM_Z - 0.18, s), 0.05, 'iron'))
    for k in range(7):  # yon tomondagi X panjara
        r0 = ARM_R0 + (ARM_R1 - ARM_R0) * k / 7
        r1 = ARM_R0 + (ARM_R1 - ARM_R0) * (k + 1) / 7
        for s in (-0.14, 0.14):
            q.append(beam('x', P(r0, ARM_Z - 0.18, s), P(r1, ARM_Z + 0.12, s), 0.025, 'iron'))
    # pastki qiya tayanch (halqadan qo'l o'rtasiga)
    q.append(beam('strut', P(TR + 0.1, ARM_Z - 1.85), P(2.2, ARM_Z - 0.2), 0.06, 'iron'))
    # qo'l uchida tik ustun (parrak shu ustida)
    q.append(box('endpost', (0.14, 0.14, 0.9), P(ARM_R1, ARM_Z + 0.2), 'iron'))
rotor = join('rotor', q)

# ---------- Savatlar (lift) va parraklar (spin) ----------
SEAT_Z = 2.1  # savat o'tirgichi balandligi (pastki holatda) — panjaradan baland
for n in range(6):
    a = n * math.pi / 3
    ca, sa = math.cos(a), math.sin(a)
    P = lambda r, z, s=0.0: (ca * r - sa * s, sa * r + ca * s, z)
    g = []
    # egilgan osma: qo'l uchidan tashqariga va pastga, keyin savatga
    g.append(beam('h1', P(ARM_R1, ARM_Z - 0.2), P(ARM_R1 + 0.35, ARM_Z - 0.9), 0.06, 'iron'))
    g.append(beam('h2', P(ARM_R1 + 0.35, ARM_Z - 0.9), P(ARM_R1 + 0.45, SEAT_Z + 1.0), 0.06, 'iron'))
    g.append(beam('h3', P(ARM_R1 + 0.45, SEAT_Z + 1.0), P(ARM_R1 + 0.35, SEAT_Z + 0.75), 0.06, 'iron'))
    # savat: yog'och taglik, ikki o'rindiq (tashqariga qaragan), suyanchiqlar, temir ramka, oyoq tirgagi
    rc = ARM_R1 + 0.55
    g.append(box('floor', (0.75, 1.25, 0.08), P(rc, SEAT_Z - 0.05), 'wood', (0, 0, a)))
    for s in (-0.3, 0.3):
        g.append(box('cushion', (0.42, 0.52, 0.12), P(rc, SEAT_Z + 0.06, s), 'seat', (0, 0, a)))
        g.append(box('back', (0.1, 0.52, 0.55), P(rc - 0.22, SEAT_Z + 0.35, s), 'seat', (0, 0, a)))
    for s in (-0.66, 0.66):  # yon ramkalar
        g.append(box('side', (0.7, 0.04, 0.04), P(rc, SEAT_Z + 0.45, s), 'iron', (0, 0, a)))
        g.append(box('side_v', (0.04, 0.04, 0.55), P(rc + 0.33, SEAT_Z + 0.2, s), 'iron', (0, 0, a)))
    g.append(box('footrest', (0.2, 1.1, 0.04), P(rc + 0.3, SEAT_Z - 0.28), 'wood', (0, 0, a)))
    for s in (-0.5, 0.5):  # tirgakni savatga ulovchi temir
        g.append(box('fr_bar', (0.04, 0.04, 0.26), P(rc + 0.3, SEAT_Z - 0.16, s), 'iron', (0, 0, a)))
    g.append(box('lapbar', (0.04, 1.2, 0.04), P(rc + 0.3, SEAT_Z + 0.42), 'iron', (0, 0, a)))
    lift = join(f'lift{n}', g)
    lift.parent = rotor

    # parrak: 4 ta tunuka qanot, markazi ustun tepasida; o'z markazida aylanishi uchun origin — markazda
    pr = [cyl('hub', 0.08, 0.12, (0, 0, -0.06), 'iron', 8)]
    for k in range(4):
        b = k * math.pi / 2
        pr.append(box('blade', (0.95, 0.16, 0.015), (math.cos(b) * 0.5, math.sin(b) * 0.5, 0), 'blade', (0.25, 0, b)))
    sp = join(f'spin{n}', pr)
    sp.location = P(ARM_R1, ARM_Z + 0.72)
    sp.parent = rotor

objs = [o for o in scene.objects if o.type == 'MESH']
tris = sum(len(pg.vertices) - 2 for o in objs for pg in o.data.polygons)
print(f'MAGIC_BIKES tris={tris} objects={[o.name for o in objs]}')

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'MAGIC_BIKES glb={OUT_GLB.stat().st_size // 1024} KB')

# ---------- Preview ----------
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.location = (11, -13, 10)
cam.rotation_euler = (Vector((0, 0, 3.6)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 900, 1000
world = bpy.data.worlds.new('w')
world.color = (0.93, 0.95, 0.98)
scene.world = world
scene.render.filepath = str(PREVIEW_DIR / 'preview.png')
bpy.ops.render.render(write_still=True)
print('MAGIC_BIKES preview', scene.render.filepath)

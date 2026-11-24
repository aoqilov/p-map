"""
42 — Аттракцион "Happy swing". Low-poly model, rasm: attraction-images-park/Happy_Swing.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/42-happy-swing/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png

Tuzilish (xarita kodi shu nomlarga tayanadi, src/map/GltfModel.tsx):
    base   — qimirlamaydigan qism: poydevor, qizil A-ramkalar, o'q, yozuv, delfin, bayroqlar, fonuslar
    swing0 — arg'imchoq (osma qo'llar + 6 o'rindiq): tepadagi o'q atrofida oldinga-orqaga tebranadi.
             Origin — o'q markazida (tebranish shu nuqta atrofida), o'q — Blender X bo'ylab.
Asl o'lcham metrda: 4.8 × 4.8 m poydevor, balandligi ~6.2 m (delfin bilan). Old tomoni — Blender'da -Y.
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
    'red': (0.82, 0.08, 0.06), 'orange': (0.98, 0.35, 0.03), 'yellow': (0.98, 0.78, 0.05), 'teal': (0.3, 0.75, 0.7),
    'blue': (0.15, 0.45, 0.85), 'steel': (0.6, 0.61, 0.63), 'purple': (0.5, 0.25, 0.7), 'gray': (0.55, 0.57, 0.6),
    'white': (0.95, 0.96, 0.97), 'dark': (0.1, 0.1, 0.11), 'green': (0.2, 0.7, 0.25),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.45
    if name == 'steel':
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
    """Silindr: markazi loc, o'qi Z (rot bilan buriladi)"""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return new_obj(name, bm, [mat])


def beam(name, a, b, w, d, mat):
    """a→b to'sin, kesimi w × d"""
    a, b = Vector(a), Vector(b)
    v = b - a
    ob = box(name, (v.length, w, d), (0, 0, 0), mat)
    ob.rotation_euler = v.to_track_quat('X', 'Z').to_euler()
    ob.location = (a + b) / 2
    return ob


def torus(name, major, minor, loc, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=16, minor_segments=5,
                                     location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(MATS[mat])
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
S, H0 = 4.8, 0.22
AX = 2.05          # A-ramkalar X bo'yicha (o'qning ikki uchi)
PIVOT_Z = 4.05     # tebranish o'qi balandligi
p = []
p.append(box('deck', (S, S, H0), (0, 0, H0 / 2), 'yellow'))
p.append(box('plate', (S - 0.5, S - 0.5, 0.02), (0, 0, H0 + 0.01), 'steel'))
p.append(box('ramp', (1.4, 0.3, 0.02), (-0.6, -S / 2 + 0.15, H0 + 0.012), 'steel'))

LIGHT_COLS = ['yellow', 'green', 'blue', 'red', 'white']
for sx in (-1, 1):
    x = sx * AX
    top = (x, 0, PIVOT_Z + 0.15)
    for sy in (-1, 1):  # A-ramkaning ikki oyog'i
        foot = (sx * (AX + 0.15), sy * 1.75, H0)
        p.append(beam('leg', foot, top, 0.2, 0.2, 'red'))
        for k in range(9):  # oyoqdagi rangli chiroqchalar
            t = 0.1 + k * 0.095
            px, py, pz = (foot[i] + (top[i] - foot[i]) * t for i in range(3))
            p.append(box('dot', (0.06, 0.06, 0.06), (px - sx * 0.11, py, pz), LIGHT_COLS[k % 5]))
    p.append(beam('cross', (sx * (AX + 0.1), -1.05, 1.6), (sx * (AX + 0.1), 1.05, 1.6), 0.08, 0.08, 'red'))
    # binafsha langar halqasi (ramka ichida)
    p.append(torus('wheel', 0.55, 0.05, (sx * (AX + 0.12), 0, 2.2), 'purple', (0, math.pi / 2, 0)))
    # langar: tik o'zak, tepada halqa va qisqa ko'ndalang, pastda yuqoriga egilgan ikki tirnoq
    ax_ = sx * (AX + 0.12)
    p.append(box('anchor_v', (0.05, 0.06, 0.75), (ax_, 0, 2.15), 'purple'))
    p.append(torus('anchor_ring', 0.08, 0.02, (ax_, 0, 2.6), 'purple', (0, math.pi / 2, 0)))
    p.append(box('anchor_h', (0.05, 0.36, 0.05), (ax_, 0, 2.4), 'purple'))
    for sy in (-1, 1):
        p.append(box('fluke', (0.05, 0.3, 0.05), (ax_, sy * 0.13, 1.86), 'purple', (sy * 0.7, 0, 0)))
        p.append(box('fluke_tip', (0.05, 0.08, 0.12), (ax_, sy * 0.25, 1.98), 'purple', (sy * -0.3, 0, 0)))
    p.append(cyl('bearing', 0.18, 0.3, (sx * (AX - 0.05), 0, PIVOT_Z), 'orange', 12, (0, math.pi / 2, 0)))
    # bayroq va fonus
    p.append(cyl('flagpole', 0.02, 0.9, (sx * AX, 0.25, PIVOT_Z + 0.75), 'yellow', 6))
    p.append(box('flag', (0.02, 0.35, 0.22), (sx * AX, 0.44, PIVOT_Z + 1.05), 'blue'))
    p.append(cyl('lamp', 0.07, 0.2, (sx * AX, -0.25, PIVOT_Z + 0.45), 'dark', 6))
# tepadagi to'q sariq o'q va ko'k to'sin
p.append(cyl('axle', 0.1, 2 * AX, (0, 0, PIVOT_Z), 'orange', 12, (0, math.pi / 2, 0)))
p.append(box('topbar', (2 * AX + 0.4, 0.14, 0.1), (0, 0, PIVOT_Z + 0.3), 'blue'))
# "HAPPY SWING" yozuvi — rangli harflar o'rnida bloklar
for k in range(10):
    col = ['orange', 'yellow', 'red', 'yellow', 'orange', 'white', 'yellow', 'orange', 'red', 'yellow'][k]
    p.append(box('letter', (0.26, 0.08, 0.34), (-1.35 + k * 0.3, -0.05, PIVOT_Z + 0.55), col))
# to'lqin va delfin
p.append(box('wave', (1.6, 0.1, 0.35), (0.1, 0.05, PIVOT_Z + 0.9), 'teal'))
p.append(box('foam', (1.3, 0.11, 0.12), (0.1, 0.04, PIVOT_Z + 1.08), 'white'))
# delfin: to'lqindan sakrayotgan, egilgan tana (ikki bo'lak), tumshuq, quyruq qanotlari, orqa suzgich
p.append(cyl('d_body', 0.2, 0.7, (0.35, 0.05, PIVOT_Z + 1.4), 'gray', 10, (0, math.radians(55), 0), 0.15))
p.append(cyl('d_rear', 0.15, 0.6, (-0.15, 0.05, PIVOT_Z + 1.7), 'gray', 10, (0, math.radians(-30), 0), 0.07))
p.append(cyl('snout', 0.08, 0.28, (0.72, 0.05, PIVOT_Z + 1.17), 'gray', 8, (0, math.radians(120), 0), 0.03))
for sy in (-1, 1):
    p.append(box('fluke', (0.12, 0.3, 0.04), (-0.32, 0.05 + sy * 0.13, PIVOT_Z + 2.0), 'gray', (sy * 0.3, 0, 0.2)))
p.append(box('fin', (0.18, 0.04, 0.2), (0.25, 0.05, PIVOT_Z + 1.62), 'gray', (0, -0.6, 0)))
base = join('base', p)

# ---------- SWING0: osma qo'llar va o'rindiqlar (o'q atrofida tebranadi) ----------
SEAT_Z = 0.85
q = []
for sx in (-1, 1):
    q.append(box('arm', (0.12, 0.12, PIVOT_Z - SEAT_Z), (sx * 1.6, 0, (PIVOT_Z + SEAT_Z) / 2), 'yellow'))
    for k in range(10):  # qo'ldagi chiroqchalar
        q.append(box('adot', (0.05, 0.05, 0.05), (sx * 1.6, -0.07, SEAT_Z + 0.4 + k * 0.28), LIGHT_COLS[k % 5]))
    q.append(cyl('hub', 0.14, 0.22, (sx * 1.6, 0, PIVOT_Z), 'yellow', 10, (0, math.pi / 2, 0)))
q.append(box('cradle', (3.1, 0.75, 0.32), (0, 0, SEAT_Z - 0.1), 'teal'))       # firuza rangli asos
for k in range(6):  # to'q sariq kovsh o'rindiqlar (oldga qaragan, -Y)
    x = -1.2 + k * 0.48
    q.append(box('pan', (0.42, 0.5, 0.08), (x, -0.05, SEAT_Z + 0.1), 'orange'))
    q.append(box('back', (0.42, 0.08, 0.7), (x, 0.24, SEAT_Z + 0.42), 'orange', (0.25, 0, 0)))
    for s in (-1, 1):
        q.append(box('side', (0.04, 0.45, 0.25), (x + s * 0.2, 0.0, SEAT_Z + 0.22), 'orange'))
q.append(cyl('lapbar', 0.03, 3.0, (0, -0.42, SEAT_Z + 0.55), 'steel', 6, (0, math.pi / 2, 0)))
q.append(cyl('footbar', 0.03, 3.0, (0, -0.42, SEAT_Z - 0.3), 'steel', 6, (0, math.pi / 2, 0)))
for k in range(7):
    q.append(box('foot', (0.03, 0.03, 0.3), (-1.45 + k * 0.48, -0.42, SEAT_Z - 0.15), 'steel'))
swing = join('swing0', q)
# Origin — o'q markaziga: tebranish shu nuqta atrofida
bpy.ops.object.select_all(action='DESELECT')
swing.select_set(True)
bpy.context.view_layer.objects.active = swing
scene.cursor.location = (0, 0, PIVOT_Z)
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

tris = sum(len(pg.vertices) - 2 for o in scene.objects if o.type == 'MESH' for pg in o.data.polygons)
print(f'HAPPY_SWING tris={tris} swing_origin={tuple(round(v, 2) for v in swing.location)}')

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'HAPPY_SWING glb={OUT_GLB.stat().st_size // 1024} KB')

# ---------- Preview (o'rindiqlar biroz tebrangan holatda) ----------
swing.rotation_euler = (math.radians(-35), 0, 0)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.location = (8.5, -9.5, 6.5)
cam.rotation_euler = (Vector((0, 0, 2.7)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
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
print('HAPPY_SWING preview', scene.render.filepath)

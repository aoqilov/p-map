"""
32 — Аттракцион "3 Loops Coaster" (planda: "Spining coaster"). Rasm: attraction-images-park/3_Loops_Coaster.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/32-3-loops-coaster/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, track.json, preview.png

Tuzilish (xarita kodi: src/map/GltfModel.tsx):
    base       — qimirlamaydigan qism: beton maydon, bekat (zina, budka, "3 loops coaster" yozuvi),
                 yashil panjarali trassa, kulrang A-tayanchlar, ma'lumot taxtasi
    car0..car3 — xonqizi vagonlar: kod track.json dagi chiziq bo'ylab yurgizadi
Trassa: bekat → ko'tarilish → 3 aylanali pastga tushuvchi spiral → orqadan qaytish → chap burilish → bekat.
Asl o'lcham metrda: ~23 × 15 m, balandligi ~6.5 m. Uzun o'qi — X, old tomoni (bekat, zina) — Blender'da -Y.
"""
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Euler, Vector

HERE = Path(__file__).resolve().parent
OUT_GLB = HERE / 'model.glb'
OUT_BLEND = HERE / 'model.blend'
OUT_TRACK = HERE / 'track.json'
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PREVIEW_DIR = Path(argv[0]) if argv else HERE

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

PALETTE = {
    'concrete': (0.32, 0.32, 0.33), 'green': (0.12, 0.5, 0.18), 'gray': (0.55, 0.56, 0.58), 'yellow': (0.98, 0.8, 0.08),
    'red': (0.8, 0.06, 0.05), 'black': (0.05, 0.05, 0.06), 'white': (0.95, 0.95, 0.95), 'steel': (0.66, 0.67, 0.69),
    'glass': (0.15, 0.2, 0.26), 'lime': (0.4, 0.7, 0.15), 'blue': (0.1, 0.35, 0.75),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.5
    if name == 'steel':
        bsdf.inputs['Metallic'].default_value = 0.3  # xaritada atrof-muhit aksi yo'q — yuqori metallik qoraygan ko'rinadi
    m.diffuse_color = (*rgb, 1)
    MATS[name] = m


def obj(name, bm, mat):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(MATS[mat])
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob


def box(size, loc, mat, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return obj('box', bm, mat)


def cyl(r, h, loc, mat, segs=8, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=h)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return obj('cyl', bm, mat)


def sphere(r, loc, mat, segs=10, scale=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=max(4, segs // 2), radius=r)
    bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return obj('sph', bm, mat)


def tube(a, b, r, mat, segs=6):
    a, b = Vector(a), Vector(b)
    v = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=segs, radius1=r, radius2=r, depth=v.length)
    ob = obj('tube', bm, mat)
    ob.rotation_euler = v.to_track_quat('Z', 'Y').to_euler()
    ob.location = (a + b) / 2
    return ob


def curve(pts, r, mat, cyclic=True):
    cu = bpy.data.curves.new('c', 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = r
    cu.bevel_resolution = 1
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for i, (x, y, z) in enumerate(pts):
        sp.points[i].co = (x, y, z, 1)
    sp.use_cyclic_u = cyclic
    ob = bpy.data.objects.new('c', cu)
    scene.collection.objects.link(ob)
    cu.materials.append(MATS[mat])
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target='MESH')
    return bpy.context.view_layer.objects.active


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


# ---------- Trassa ----------
ST_Z = 1.3                         # bekatdagi rels sathi
HC = (4.5, 0.6)                    # spiral markazi
R0, R1, TOP, LOW = 5.6, 3.0, 5.8, 1.7   # spiral: tashqi/ichki radius, yuqori/pastki sath
TURNS = 3


def build_path(step=0.25):
    pts = []

    def seg_line(a, b, z0, z1):
        L = math.dist(a, b)
        n = max(2, int(L / step))
        for i in range(n):
            t = i / n
            pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, z0 + (z1 - z0) * t))

    def seg_arc(c, ra, rb, a0, a1, z0, z1, ease=False):
        L = abs(a1 - a0) * (ra + rb) / 2
        n = max(4, int(L / step))
        for i in range(n):
            t = i / n
            a = a0 + (a1 - a0) * t
            r = ra + (rb - ra) * t
            zt = t if not ease else t * t * (3 - 2 * t)
            pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a), z0 + (z1 - z0) * zt))

    y0 = HC[1] - R0
    seg_line((-8.0, y0), (-3.5, y0), ST_Z, ST_Z)                         # bekat
    seg_line((-3.5, y0), (HC[0], y0), ST_Z, TOP)                         # zanjirli ko'tarilish
    seg_arc(HC, R0, R1, -math.pi / 2, -math.pi / 2 + 2 * math.pi * TURNS, TOP, LOW)   # 3 aylanali spiral
    seg_arc(HC, R1, R1, -math.pi / 2, math.pi / 2, LOW, 1.15)            # spiral ostidan chiqish
    ry = HC[1] + R1
    seg_line((HC[0], ry), (-8.0, ry), 1.15, 1.15)                        # orqadan qaytish
    cl = (-8.0, (ry + y0) / 2)
    seg_arc(cl, (ry - y0) / 2, (ry - y0) / 2, math.pi / 2, 3 * math.pi / 2, 1.15, ST_Z, ease=True)  # chap burilish
    return pts


path = build_path()
n = len(path)


def tangent(i):
    a, b = path[(i - 1) % n], path[(i + 1) % n]
    return Vector((b[0] - a[0], b[1] - a[1], b[2] - a[2])).normalized()


# ---------- BASE ----------
p = []
W, D = 24.5, 15.5
CX, CY = -0.8, -0.6
p.append(box((W, D, 0.12), (CX, CY, 0.06), 'concrete'))
# sariq panjara modelda emas — xaritada maydoncha chegarasi bo'ylab quriladi (config/map.ts → FENCES['32'])
# bekat: ko'tarilgan supa (qizil-yashil-sariq yon devor), zina, budka, yozuv
SY = HC[1] - R0
p.append(box((6.2, 1.5, ST_Z - 0.15), (-5.4, SY - 1.25, (ST_Z - 0.15) / 2), 'red'))
p.append(box((6.21, 1.51, 0.35), (-5.4, SY - 1.25, ST_Z - 0.55), 'lime'))
p.append(box((6.22, 1.52, 0.18), (-5.4, SY - 1.25, ST_Z - 0.28), 'yellow'))
p.append(box((6.2, 1.5, 0.06), (-5.4, SY - 1.25, ST_Z - 0.12), 'steel'))
for k in range(5):  # zina (oldga, -Y)
    h = ST_Z - 0.15 - k * (ST_Z - 0.15) / 5
    p.append(box((1.5, 0.32, 0.06), (-5.2, SY - 2.15 - k * 0.32, h), 'steel'))
for sx in (-0.75, 0.75):
    p.append(tube((-5.2 + sx, SY - 2.0, ST_Z + 0.9), (-5.2 + sx, SY - 3.6, 0.95), 0.03, 'yellow', 6))
    p.append(tube((-5.2 + sx, SY - 3.6, 0.1), (-5.2 + sx, SY - 3.6, 0.95), 0.03, 'yellow', 6))
for x in (-8.4, -2.4):  # bekat to'sig'i
    p.append(tube((x, SY - 1.95, ST_Z), (x, SY - 1.95, ST_Z + 0.9), 0.03, 'yellow', 6))
p.append(tube((-8.4, SY - 1.95, ST_Z + 0.9), (-6.0, SY - 1.95, ST_Z + 0.9), 0.03, 'yellow', 6))
p.append(tube((-4.4, SY - 1.95, ST_Z + 0.9), (-2.4, SY - 1.95, ST_Z + 0.9), 0.03, 'yellow', 6))
# operator budkasi
p.append(box((1.1, 1.1, 2.0), (-2.6, SY - 1.4, ST_Z + 1.0), 'glass'))
p.append(box((1.25, 1.25, 0.12), (-2.6, SY - 1.4, ST_Z + 2.06), 'green'))
for sx in (-0.55, 0.55):
    for sy in (-0.55, 0.55):
        p.append(box((0.06, 0.06, 2.0), (-2.6 + sx, SY - 1.4 + sy, ST_Z + 1.0), 'steel'))
# "3 loops coaster" yozuvi — bekat ustida yoy
for sx in (-8.3, -3.6):
    p.append(tube((sx, SY - 0.2, 0.1), (sx, SY - 0.2, 3.2), 0.05, 'steel', 6))
p.append(box((5.0, 0.12, 0.65), (-5.95, SY - 0.2, 3.25), 'yellow'))
p.append(box((5.06, 0.1, 0.71), (-5.95, SY - 0.15, 3.25), 'red'))
for k in range(9):
    p.append(box((0.34, 0.03, 0.34), (-7.7 + k * 0.44, SY - 0.28, 3.25), 'green'))
# ma'lumot taxtasi (oldida)
p.append(tube((3.0, CY - D / 2 + 1.3, 0.1), (3.0, CY - D / 2 + 1.3, 1.1), 0.05, 'steel', 6))
p.append(box((1.0, 0.06, 1.2), (3.0, CY - D / 2 + 1.3, 1.6), 'white'))
p.append(box((1.0, 0.065, 0.22), (3.0, CY - D / 2 + 1.3, 1.95), 'blue'))

# trassa: ikki yashil rels, ostida "umurtqa", orasida zigzag panjara, shpalalar
GA = 0.32
left, right, spine = [], [], []
for i, (x, y, z) in enumerate(path):
    t = tangent(i)
    s = Vector((-t.y, t.x, 0)).normalized()
    left.append((x + s.x * GA, y + s.y * GA, z))
    right.append((x - s.x * GA, y - s.y * GA, z))
    spine.append((x, y, z - 0.38))
p.append(curve(left[::2], 0.05, 'green'))
p.append(curve(right[::2], 0.05, 'green'))
p.append(curve(spine[::2], 0.06, 'green'))
for i in range(0, n, 4):
    p.append(tube(left[i], right[i], 0.03, 'green', 4))
    j = (i + 2) % n
    p.append(tube(left[i], spine[j], 0.022, 'green', 4))
    p.append(tube(right[i], spine[j], 0.022, 'green', 4))
# A-tayanchlar: har ~3 m da, trassa baland joylarda
placed_feet = []
for i in range(0, n, 6):
    x, y, z = path[i]
    # tayanchlar bir-biridan kamida 2.4 m uzoq (ichma-ich spiral halqalari ostida zich bo'lib ketmasin)
    if any(math.hypot(x - fx, y - fy) < 2.4 for fx, fy in placed_feet):
        continue
    placed_feet.append((x, y))
    if z < ST_Z + 0.2 and y < SY + 0.5:  # bekat ostida — supa bor
        continue
    t = tangent(i)
    s = Vector((-t.y, t.x, 0)).normalized()
    top = Vector((x, y, z - 0.42))
    w = 0.25 + 0.12 * z
    for sd in (-1, 1):
        foot = Vector((x, y, 0.12)) + s * (w * sd)
        p.append(tube(foot, top, 0.07, 'gray', 6))
        p.append(box((0.35, 0.35, 0.08), (foot.x, foot.y, 0.16), 'gray'))
    if z > 2.5:
        p.append(tube(Vector((x, y, 0.12 + z * 0.4)) + s * (w * 0.6), Vector((x, y, 0.12 + z * 0.4)) - s * (w * 0.6), 0.04, 'gray', 4))
base = join('base', p)

# ---------- Xonqizi vagonlar: lokal +X — harakat yo'nalishi, tagi z=0 (rels sathi) ----------
OFFSETS = [0.0, 1.25, 2.5, 3.75]
cars = []
for k, off in enumerate(OFFSETS):
    q = [box((1.05, 0.8, 0.18), (0, 0, 0.18), 'black')]
    q.append(sphere(0.62, (-0.05, 0, 0.42), 'red', 12, scale=(1.0, 0.72, 0.55)))        # qizil kosa
    q.append(box((0.62, 0.5, 0.3), (0.02, 0, 0.62), 'black'))                           # o'rindiq chuqurligi
    q.append(box((0.08, 0.5, 0.35), (-0.3, 0, 0.75), 'red'))                            # suyanchiq
    for sx, sy in ((-0.35, 0.33), (0.1, -0.36), (-0.15, -0.3), (0.3, 0.3), (-0.5, -0.1), (0.15, 0.38)):
        q.append(sphere(0.08, (sx, sy, 0.55), 'black', 6, scale=(1, 1, 0.5)))           # dog'lar
    q.append(sphere(0.25, (0.6, 0, 0.45), 'black', 10))                                  # bosh
    for sy in (-0.12, 0.12):
        q.append(sphere(0.07, (0.8, sy, 0.55), 'white', 6))
        q.append(sphere(0.035, (0.86, sy, 0.56), 'black', 4))
        q.append(tube((0.65, sy * 0.8, 0.68), (0.72, sy * 1.6, 0.95), 0.012, 'black', 3))   # mo'ylov
    q.append(tube((-0.05, -0.3, 0.85), (-0.05, 0.3, 0.85), 0.02, 'steel', 4))           # qo'l to'sig'i
    c = join(f'car{k}', q)
    c.location = (-4.2 - off, SY, ST_Z)
    cars.append(c)

# track.json (glTF: x, z, -y)
OUT_TRACK.write_text(json.dumps({
    'closed': True,
    'points': [[round(x, 3), round(z, 3), round(-y, 3)] for x, y, z in path[::2]],
    'cars': [{'name': c.name, 'offset': off} for c, off in zip(cars, OFFSETS)],
    'station': 5.4,   # trassa boshidan (bekat boshi x=-8) — vagonlar bekatda to'xtaydi
}, separators=(',', ':')))

tris = sum(len(pg.vertices) - 2 for o in scene.objects if o.type == 'MESH' for pg in o.data.polygons)
length = sum(math.dist(path[i], path[(i + 1) % n]) for i in range(n))
print(f'LOOPS tris={tris} track={length:.1f}m size={base.dimensions.x:.1f}x{base.dimensions.y:.1f}x{base.dimensions.z:.1f}')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'LOOPS glb={OUT_GLB.stat().st_size // 1024} KB')

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.location = (13, -26, 15)
cam.rotation_euler = (Vector((-0.5, 0, 2.2)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 1100, 800
world = bpy.data.worlds.new('w')
world.color = (0.93, 0.95, 0.98)
scene.world = world
scene.render.filepath = str(PREVIEW_DIR / 'preview.png')
bpy.ops.render.render(write_still=True)
print('LOOPS preview', scene.render.filepath)

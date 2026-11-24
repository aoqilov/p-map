"""
21 — Аттракцион "Flying tigers 6". Rasm: attraction-images-park/Flying_Tigers.png (samolyotlar, ustunlar, bulutlar),
joylashuvi — oval yo'lli to'rtburchak supa (foydalanuvchi ko'rsatgan namuna bo'yicha).

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/21-flying-tigers-6/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, track.json, preview.png

Tuzilish (xarita kodi: src/map/GltfModel.tsx):
    base       — supa, sariq panjara, 4 ta qizil-oq shaxmat ustun, tepadagi ko'k oval yo'l (ikki quvur), bulutlar
    car0..car5 — samolyotlar: aravacha + kumush osma ustun + samolyot. Kod track.json dagi oval bo'ylab yurgizadi
Asl o'lcham metrda: 10 × 6.8 m, balandligi ~4.6 m. Uzun o'qi — X, old tomoni (kirish) — Blender'da -Y.
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
    'concrete': (0.66, 0.65, 0.62), 'gold': (0.86, 0.66, 0.16), 'blue': (0.08, 0.22, 0.65), 'red': (0.8, 0.08, 0.07),
    'white': (0.95, 0.96, 0.97), 'steel': (0.72, 0.73, 0.75), 'dark': (0.2, 0.2, 0.22), 'brown': (0.45, 0.28, 0.15),
    'green': (0.1, 0.5, 0.18), 'yellow': (0.98, 0.78, 0.08), 'orange': (0.98, 0.42, 0.05), 'purple': (0.48, 0.2, 0.62),
    'pink': (0.9, 0.25, 0.55), 'sky': (0.15, 0.4, 0.85), 'black': (0.05, 0.05, 0.06), 'tan': (0.6, 0.42, 0.25),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.45
    if name in ('steel', 'gold'):
        bsdf.inputs['Metallic'].default_value = 0.3  # xaritada atrof-muhit aksi yo'q — yuqori metallik qoraygan ko'rinadi
    m.diffuse_color = (*rgb, 1)
    MATS[name] = m


def obj(name, bm, mats):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(MATS[m])
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob


def box(size, loc, mat, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return obj('box', bm, [mat])


def cyl(r, h, loc, mat, segs=10, rot=(0, 0, 0), r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return obj('cyl', bm, [mat])


def sphere(r, loc, mat, segs=10, scale=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=max(4, segs // 2), radius=r)
    bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return obj('sph', bm, [mat])


def tube(a, b, r, mat, segs=6):
    a, b = Vector(a), Vector(b)
    v = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=segs, radius1=r, radius2=r, depth=v.length)
    ob = obj('tube', bm, [mat])
    ob.rotation_euler = v.to_track_quat('Z', 'Y').to_euler()
    ob.location = (a + b) / 2
    return ob


def lathe_checker(r0, r1, z0, z1, rows, segs, mats, loc):
    """Shaxmat naqshli silindr (qizil-oq ustun)"""
    bm = bmesh.new()
    rings = []
    for i in range(rows + 1):
        z = z0 + (z1 - z0) * i / rows
        r = r0 + (r1 - r0) * i / rows
        rings.append([bm.verts.new((loc[0] + r * math.cos(2 * math.pi * k / segs), loc[1] + r * math.sin(2 * math.pi * k / segs), z))
                      for k in range(segs)])
    for i in range(rows):
        for k in range(segs):
            f = bm.faces.new([rings[i][k], rings[i][(k + 1) % segs], rings[i + 1][(k + 1) % segs], rings[i + 1][k]])
            f.material_index = (i + k) % 2
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj('chk', bm, mats)


def curve(pts, r, mat):
    cu = bpy.data.curves.new('c', 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = r
    cu.bevel_resolution = 1
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for i, (x, y, z) in enumerate(pts):
        sp.points[i].co = (x, y, z, 1)
    sp.use_cyclic_u = True
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


# ---------- Oval yo'l (stadion shakli) ----------
SA, RO = 2.4, 2.3      # to'g'ri qismning yarim uzunligi, yarim aylana radiusi
H = 4.1                # yo'l balandligi


def oval(r_off=0.0, step=0.12):
    """Stadion shaklidagi yopiq chiziq (soat teskarisiga), r_off — radiusga qo'shimcha"""
    R = RO + r_off
    pts = []
    for x0, x1, y in ((-SA, SA, -R),):
        n = int((x1 - x0) / step)
        pts += [(x0 + (x1 - x0) * i / n, y) for i in range(n)]
    n = int(math.pi * R / step)
    pts += [(SA + R * math.cos(-math.pi / 2 + math.pi * i / n), R * math.sin(-math.pi / 2 + math.pi * i / n)) for i in range(n)]
    n = int(2 * SA / step)
    pts += [(SA - 2 * SA * i / n, R) for i in range(n)]
    n = int(math.pi * R / step)
    pts += [(-SA + R * math.cos(math.pi / 2 + math.pi * i / n), R * math.sin(math.pi / 2 + math.pi * i / n)) for i in range(n)]
    return pts


# ---------- BASE ----------
p = []
W, D = 10.0, 6.8
p.append(box((W, D, 0.25), (0, 0, 0.125), 'concrete'))
p.append(box((W - 0.3, D - 0.3, 0.02), (0, 0, 0.26), 'dark'))
# sariq panjara, oldida (−Y) o'rtada kirish
FH, e = 1.0, 0.15
corners = [(-W / 2 + e, -D / 2 + e), (W / 2 - e, -D / 2 + e), (W / 2 - e, D / 2 - e), (-W / 2 + e, D / 2 - e)]
for i in range(4):
    (ax, ay), (bx, by) = corners[i], corners[(i + 1) % 4]
    L = math.hypot(bx - ax, by - ay)
    nb = int(L / 0.16)
    for j in range(nb + 1):
        t = j / nb
        x, y = ax + (bx - ax) * t, ay + (by - ay) * t
        if i == 0 and abs(x) < 0.6:
            continue
        p.append(tube((x, y, 0.25), (x, y, 0.25 + FH), 0.013 if j % 8 else 0.035, 'gold', 4 if j % 8 else 6))
    for z in (0.33, 0.25 + FH):
        if i == 0:
            for sx in (-1, 1):
                p.append(tube((sx * 0.6, ay, z), (sx * (W / 2 - e), ay, z), 0.022, 'gold', 5))
        else:
            p.append(tube((ax, ay, z), (bx, by, z), 0.022, 'gold', 5))
# 4 ta qizil-oq shaxmat ustun (markaziy chiziq bo'ylab), tepasida ko'k qopqoq
cols = [-2.7, -0.9, 0.9, 2.7]
for x in cols:
    p.append(lathe_checker(0.24, 0.2, 0.26, H - 0.25, 12, 8, ['red', 'white'], (x, 0, 0)))
    p.append(box((0.5, 0.5, 0.25), (x, 0, H - 0.12), 'blue'))
# ko'k oval yo'l: ikki quvur (aravacha yo'li), ustunlarga ko'ndalang qo'llar
for yoff in (-0.12, 0.12):
    p.append(curve([(x, y, H + yoff) for x, y in oval(0.0)[::2]], 0.07, 'blue'))
p.append(curve([(x, y, H + 0.35) for x, y in oval(-0.25)[::3]], 0.045, 'dark'))
for x in cols:
    for sy in (-1, 1):
        p.append(box((0.22, RO, 0.18), (x, sy * RO / 2, H), 'blue'))
for k, (x, y) in enumerate([(SA + RO, 0), (-SA - RO, 0), (SA, RO), (-SA, -RO), (SA, -RO), (-SA, RO)]):
    p.append(sphere(0.18, (x, y, H), 'blue', 8))
# bulutlar (oq) — ustunlar tepasida, fotodagidek
for x in cols:
    for dx, dz, r in ((0, 0.55, 0.38), (-0.3, 0.42, 0.28), (0.3, 0.42, 0.3), (0.12, 0.8, 0.24)):
        p.append(sphere(r, (x + dx, 0, H + dz), 'white', 10, scale=(1, 0.8, 0.85)))
base = join('base', p)

# ---------- Samolyotlar: lokal +X — harakat yo'nalishi, origin — yo'l (aravacha) sathida ----------
PLANES = [('green', '5'), ('orange', '6'), ('purple', '1'), ('yellow', '2'), ('pink', '3'), ('sky', '4')]
HANG = 2.85     # aravachadan samolyot o'rtasigacha
L_track = sum(math.dist(a, b) for a, b in zip(oval(), oval()[1:] + oval()[:1]))
cars = []
for k, (col, _num) in enumerate(PLANES):
    q = [box((0.45, 0.32, 0.22), (0, 0, -0.1), 'blue')]                         # aravacha
    q.append(tube((0, 0, -0.2), (0, 0, -HANG + 0.25), 0.045, 'steel', 8))         # kumush osma ustun
    q.append(box((0.22, 0.22, 0.2), (0, 0, -HANG + 0.35), 'brown'))               # burilish qutisi
    z = -HANG
    q.append(sphere(0.5, (0.05, 0, z), col, 12, scale=(1.55, 0.72, 0.62)))       # fyuzelyaj
    q.append(sphere(0.2, (0.85, 0, z + 0.02), 'white', 8, scale=(1.2, 1, 1)))      # tumshuq
    q.append(cyl(0.08, 0.25, (1.05, 0, z + 0.02), 'sky', 8, (0, math.pi / 2, 0), r2=0.0))  # parrak konusi
    for sy in (-1, 1):
        q.append(box((0.22, 0.03, 0.06), (0.6, sy * 0.33, z - 0.12), 'white'))    # akula tishlari tasmasi
    q.append(box((0.55, 1.7, 0.06), (0.1, 0, z - 0.05), col))                    # qanot
    q.append(box((0.3, 0.75, 0.05), (-0.65, 0, z + 0.05), col))                  # dum stabilizatori
    q.append(box((0.32, 0.05, 0.4), (-0.7, 0, z + 0.28), col, (0, -0.3, 0)))      # tik dum
    q.append(box((0.22, 0.06, 0.22), (-0.72, 0.03, z + 0.32), 'white'))           # raqam o'rni
    q.append(box((0.55, 0.42, 0.18), (-0.05, 0, z + 0.25), 'tan'))                # o'rindiq (jigarrang)
    q.append(box((0.08, 0.42, 0.35), (-0.3, 0, z + 0.38), 'tan'))
    q.append(tube((0.2, -0.22, z + 0.42), (0.2, 0.22, z + 0.42), 0.02, 'steel', 4))  # qo'l to'sig'i
    c = join(f'car{k}', q)
    c.location = (oval()[0][0], oval()[0][1], H)
    cars.append(c)

spacing = L_track / len(PLANES)
OUT_TRACK.write_text(json.dumps({
    'closed': True,
    'points': [[round(x, 3), round(H, 3), round(-y, 3)] for x, y in oval()[::2]],
    'cars': [{'name': c.name, 'offset': round(k * spacing, 3)} for k, c in enumerate(cars)],
    'station': 0,
}, separators=(',', ':')))

tris = sum(len(pg.vertices) - 2 for o in scene.objects if o.type == 'MESH' for pg in o.data.polygons)
print(f'TIGERS tris={tris} track={L_track:.1f}m')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'TIGERS glb={OUT_GLB.stat().st_size // 1024} KB')

# preview: samolyotlar oval bo'ylab teng joylashgan holatda
op = oval()
cum = [0]
for a, b in zip(op, op[1:] + op[:1]):
    cum.append(cum[-1] + math.dist(a, b))
for k, c in enumerate(cars):
    s = (L_track - k * spacing) % L_track
    i = max(j for j in range(len(op)) if cum[j] <= s)
    a, b = op[i], op[(i + 1) % len(op)]
    c.location = (a[0], a[1], H)
    c.rotation_euler = (0, 0, math.atan2(b[1] - a[1], b[0] - a[0]))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.location = (9, -12, 8)
cam.rotation_euler = (Vector((0, 0, 2.0)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 1000, 700
world = bpy.data.worlds.new('w')
world.color = (0.93, 0.95, 0.98)
scene.world = world
scene.render.filepath = str(PREVIEW_DIR / 'preview.png')
bpy.ops.render.render(write_still=True)
print('TIGERS preview', scene.render.filepath)

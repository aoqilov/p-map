"""
39 — Аттракцион "Speady coaster". Low-poly model, rasm: attraction-images-park/Coaster.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/39-speady-coaster/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, track.json, preview.png

Tuzilish (xarita kodi shu nomlarga tayanadi, src/map/GltfModel.tsx):
    base       — qimirlamaydigan qism: oval maydon, panjara, bekat, relslar, tayanchlar
    car0..car4 — parovoz va 4 ta vagon: kod ularni track.json dagi chiziq bo'ylab yurgizadi
track.json — trassa o'rta chizig'i (relslar ustki sathi), glTF koordinatalarida (x, y — tepaga, z), har ~0.5 m da;
             vagonlar ro'yxati (nomi va parovozdan orqaga masofasi). Trassa yopiq.
Asl o'lcham metrda: 30 × 13 m, balandligi ~5.8 m. Old tomoni (bekat, zina) — Blender'da -Y.
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

# ---------- Materiallar ----------
PALETTE = {
    'concrete': (0.62, 0.6, 0.56), 'steel': (0.45, 0.46, 0.48), 'rail': (0.62, 0.08, 0.06), 'fence': (0.15, 0.16, 0.17),
    'loco': (0.68, 0.1, 0.08), 'brass': (0.72, 0.55, 0.3), 'wood': (0.42, 0.2, 0.12), 'teal': (0.05, 0.5, 0.46),
    'dark': (0.08, 0.08, 0.09), 'plate': (0.55, 0.56, 0.58),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.55
    if name in ('steel', 'brass', 'plate'):
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


def cyl(name, r, h, loc, mat, segs=8, axis='Z', r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    if axis == 'X':
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler((0, math.pi / 2, 0), 'XYZ').to_matrix())
    elif axis == 'Y':
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler((math.pi / 2, 0, 0), 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return new_obj(name, bm, [mat])


def prism(name, pts, z0, z1, mat):
    """Tekis ko'pburchak (XY) z0 dan z1 gacha ko'tarilgan"""
    bm = bmesh.new()
    lo = [bm.verts.new((x, y, z0)) for x, y in pts]
    hi = [bm.verts.new((x, y, z1)) for x, y in pts]
    bm.faces.new(list(reversed(lo)))
    bm.faces.new(hi)
    n = len(pts)
    for k in range(n):
        bm.faces.new([lo[k], lo[(k + 1) % n], hi[(k + 1) % n], hi[k]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return new_obj(name, bm, [mat])


def tube(name, pts, r, mat, cyclic=True):
    """3D chiziq bo'ylab quvur (rels)"""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = r
    cu.bevel_resolution = 1
    cu.fill_mode = 'FULL'
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for i, (x, y, z) in enumerate(pts):
        sp.points[i].co = (x, y, z, 1)
    sp.use_cyclic_u = cyclic
    ob = bpy.data.objects.new(name, cu)
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


# ---------- Trassa (o'rta chiziq): to'g'ri chiziq va yoylardan, keyin balandligi silliqlanadi ----------
G0 = 0.3      # maydon sathi
STATION_Z = 0.95  # bekatdagi rels sathi
segs = []     # (turi, parametrlar, z_boshi, z_oxiri)


def line(a, b, z0, z1):
    segs.append(('line', (a, b), z0, z1))


def arc(c, r, a0, a1, z0, z1):
    segs.append(('arc', (c, r, a0, a1), z0, z1))


line((-9, -4.5), (5, -4.5), STATION_Z, STATION_Z)                               # oldi: bekat (chapdan o'ngga)
arc((5, 0), 4.5, -math.pi / 2, math.pi / 2, STATION_Z, 4.4)                      # o'ng chet: ko'tarilib burilish
line((5, 4.5), (-2.5, 4.5), 4.4, 4.3)                                           # orqa: baland yo'l
arc((-2.5, 1.3), 3.2, math.pi / 2, math.pi / 2 + 2 * math.pi, 4.3, 1.9)          # o'rtada spiral halqa (pastga)
line((-2.5, 4.5), (-9, 4.5), 1.9, 1.6)                                          # orqa: chapga
arc((-9, 0), 4.5, math.pi / 2, 3 * math.pi / 2, 1.6, STATION_Z)                  # chap chet: bekatga qaytish


def sample(step):
    pts = []
    for kind, prm, z0, z1 in segs:
        if kind == 'line':
            (ax, ay), (bx, by) = prm
            L = math.hypot(bx - ax, by - ay)
        else:
            c, r, a0, a1 = prm
            L = abs(a1 - a0) * r
        n = max(2, int(L / step))
        for i in range(n):
            t = i / n
            if kind == 'line':
                x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            else:
                a = a0 + (a1 - a0) * t
                x, y = c[0] + r * math.cos(a), c[1] + r * math.sin(a)
            pts.append([x, y, z0 + (z1 - z0) * t])
    # balandlikni silliqlash (yopiq chiziq, ~4 m oyna); bekat to'g'ri yo'li tekis qoladi
    n = len(pts)
    w = max(1, int(2.0 / step))
    zs = [p[2] for p in pts]
    sm = [sum(zs[(i + k) % n] for k in range(-w, w + 1)) / (2 * w + 1) for i in range(n)]
    for i, p in enumerate(pts):
        p[2] = STATION_Z if (p[1] < -4.4 and -8 < p[0] < 4) else sm[i]
    return pts


path = sample(0.25)
n = len(path)


def tangent(i):
    a, b = path[(i - 1) % n], path[(i + 1) % n]
    v = Vector((b[0] - a[0], b[1] - a[1], b[2] - a[2]))
    return v.normalized()


# ---------- BASE ----------
p = []
# Oval (stadion) maydon 30 × 13 m
R_END, HALF = 6.5, 8.5
stad = []
for k in range(13):
    a = -math.pi / 2 + k * math.pi / 12
    stad.append((HALF + R_END * math.cos(a), R_END * math.sin(a)))
for k in range(13):
    a = math.pi / 2 + k * math.pi / 12
    stad.append((-HALF + R_END * math.cos(a), R_END * math.sin(a)))
p.append(prism('ground', stad, 0, G0, 'concrete'))

# Panjara: ustunlar + ikki qator to'siq (old tomonda zina oldida ochiq)
fence = [(x * 1.0, y * 1.0) for x, y in stad]
FH = 1.1
for k in range(len(fence)):
    (x0, y0), (x1, y1) = fence[k], fence[(k + 1) % len(fence)]
    L = math.hypot(x1 - x0, y1 - y0)
    ang = math.atan2(y1 - y0, x1 - x0)
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    if abs(mx + 1) < 1.2 and my < -6:  # zina oldidagi kirish
        continue
    p.append(cyl('fpost', 0.035, FH, (x0, y0, G0 + FH / 2), 'fence', 6))
    for z in (G0 + 0.12, G0 + FH / 2, G0 + FH - 0.04):
        p.append(box('frail', (L, 0.03, 0.03), (mx, my, z), 'fence', (0, 0, ang)))

# Bekat platformasi (relslar yonida, old tomonda) va zina
p.append(box('station', (12.5, 1.3, 0.55), (-2.2, -5.75, G0 + 0.275), 'plate'))
p.append(box('station_edge', (12.5, 0.08, 0.06), (-2.2, -5.12, G0 + 0.58), 'steel'))
for k in range(3):  # zina pog'onalari (pastga, old tomonga)
    p.append(box('step', (1.2, 0.32, 0.18 * (3 - k)), (-1, -6.55 - k * 0.3, G0 + 0.09 * (3 - k)), 'plate'))
for sx in (-0.62, 0.62):
    p.append(box('handrail', (0.04, 1.0, 0.04), (-1 + sx, -6.85, G0 + 0.95), 'steel', (0.45, 0, 0)))
    for k in range(2):
        p.append(cyl('hpost', 0.025, 0.9, (-1 + sx, -6.55 - k * 0.6, G0 + 0.3 - k * 0.15 + 0.45), 'steel', 5))

# Relslar: ikki qizil quvur + shpalalar
GAUGE = 0.36
left, right = [], []
for i, (x, y, z) in enumerate(path):
    t = tangent(i)
    nx, ny = -t.y, t.x
    L = math.hypot(nx, ny) or 1
    nx, ny = nx / L, ny / L
    left.append((x + nx * GAUGE, y + ny * GAUGE, z))
    right.append((x - nx * GAUGE, y - ny * GAUGE, z))
p.append(tube('rail_l', left[::2], 0.055, 'rail'))
p.append(tube('rail_r', right[::2], 0.055, 'rail'))
for i in range(0, n, 4):  # shpalalar ~1 m da
    x, y, z = path[i]
    t = tangent(i)
    yaw = math.atan2(t.y, t.x)
    pitch = -math.asin(max(-1, min(1, t.z)))
    p.append(box('tie', (0.09, 2 * GAUGE + 0.1, 0.06), (x, y, z - 0.07), 'rail', (0, pitch, yaw)))
# Pastki "umurtqa" quvuri (relslar ostida, kulrang)
p.append(tube('spine', [(x, y, z - 0.32) for x, y, z in path[::4]], 0.07, 'steel'))

# Tayanchlar: har ~2.5 m da, trassa yerdan baland joylarda
for i in range(0, n, 10):
    x, y, z = path[i]
    if z < STATION_Z + 0.25:
        continue
    h = z - 0.32 - G0
    p.append(box('post', (0.14, 0.14, h), (x, y, G0 + h / 2), 'steel'))
    t = tangent(i)
    yaw = math.atan2(t.y, t.x)
    p.append(box('foot', (0.5, 0.5, 0.06), (x, y, G0 + 0.03), 'steel', (0, 0, yaw)))
    if h > 2.2:  # baland tayanchlarga qiya bog'lovchi
        nx, ny = -math.sin(yaw), math.cos(yaw)
        for s in (-1, 1):
            p.append(box('brace', (0.06, 0.06, h * 0.75),
                         (x + nx * 0.45 * s, y + ny * 0.45 * s, G0 + h * 0.38), 'steel', (s * 0.35, 0, yaw + math.pi / 2)))
base = join('base', p)

# ---------- Poyezd: car0 — parovoz, car1..4 — vagonlar. Har biri lokal +X ga qaragan, tagi z=0 (rels sathi) ----------
TRAIN = []


def car_obj(name, parts):
    ob = join(name, parts)
    return ob


def loco():
    q = []
    q.append(box('chassis', (2.0, 0.85, 0.22), (0, 0, 0.22), 'dark'))
    for wx in (-0.6, 0.0, 0.6):
        for wy in (-0.4, 0.4):
            q.append(cyl('wheel', 0.17, 0.08, (wx, wy, 0.17), 'dark', 10, 'Y'))
    q.append(cyl('boiler', 0.38, 1.15, (0.35, 0, 0.72), 'loco', 12, 'X'))
    q.append(cyl('front', 0.4, 0.06, (0.93, 0, 0.72), 'brass', 12, 'X'))
    q.append(cyl('chimney', 0.12, 0.45, (0.65, 0, 1.25), 'brass', 10, 'Z', 0.16))
    q.append(cyl('dome', 0.13, 0.22, (0.2, 0, 1.15), 'brass', 10))
    q.append(box('cab', (0.75, 0.85, 0.95), (-0.6, 0, 0.8), 'loco'))
    q.append(box('cab_roof', (0.85, 0.95, 0.06), (-0.6, 0, 1.3), 'dark'))
    q.append(box('plate', (0.02, 0.35, 0.16), (-0.98, 0, 0.75), 'teal'))
    return car_obj('car0', q)


def wagon(k):
    q = []
    q.append(box('chassis', (1.45, 0.85, 0.2), (0, 0, 0.22), 'dark'))
    for wx in (-0.45, 0.45):
        for wy in (-0.4, 0.4):
            q.append(cyl('wheel', 0.15, 0.08, (wx, wy, 0.15), 'dark', 10, 'Y'))
    # yog'och qutili vagon (devorlari) + ichida yashil-ko'k o'rindiqlar
    q.append(box('floor', (1.4, 0.9, 0.08), (0, 0, 0.36), 'wood'))
    for sy in (-0.43, 0.43):
        q.append(box('side', (1.4, 0.06, 0.5), (0, sy, 0.62), 'wood'))
    for sx in (-0.68, 0.68):
        q.append(box('end', (0.06, 0.9, 0.55), (sx, 0, 0.64), 'wood'))
    for sx in (-0.32, 0.32):
        q.append(box('seat', (0.42, 0.78, 0.12), (sx, 0, 0.5), 'teal'))
        q.append(box('back', (0.08, 0.78, 0.45), (sx - 0.2, 0, 0.75), 'teal'))
    return car_obj(f'car{k}', q)


TRAIN.append(loco())
for k in range(1, 5):
    TRAIN.append(wagon(k))
# Vagonlar orasidagi masofa (o'rtadan o'rtaga), parovozdan orqaga
OFFSETS = [0.0, 1.85, 3.45, 5.05, 6.65]
# Blender'da ko'rinishi uchun bekatga qo'yamiz (xaritada kod o'zi joylaydi)
for ob, off in zip(TRAIN, OFFSETS):
    ob.location = (1.5 - off, -4.5, STATION_Z)

# ---------- track.json (glTF koordinatalari: x, z, -y) ----------
track = [[round(x, 3), round(z, 3), round(-y, 3)] for x, y, z in path[::2]]
OUT_TRACK.write_text(json.dumps({
    'closed': True,
    'points': track,
    'cars': [{'name': ob.name, 'offset': off} for ob, off in zip(TRAIN, OFFSETS)],
    # bekat: poyezd shu masofada (trassa boshidan, m) to'xtaydi — parovoz bekat o'rtasida
    'station': 7.5,
}, separators=(',', ':')))

tris = sum(len(pg.vertices) - 2 for o in scene.objects if o.type == 'MESH' for pg in o.data.polygons)
length = sum(math.dist(path[i], path[(i + 1) % n]) for i in range(n))
print(f'COASTER tris={tris} size={base.dimensions.x:.2f}x{base.dimensions.y:.2f}x{base.dimensions.z:.2f} track={length:.1f}m')

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'COASTER glb={OUT_GLB.stat().st_size // 1024} KB')

# ---------- Preview ----------
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.location = (16, -24, 17)
cam.rotation_euler = (Vector((0, 0, 1.5)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
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
print('COASTER preview', scene.render.filepath)

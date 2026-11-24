"""
47 — Аттракцион "Колесо обозрения" (charxpalak). Low-poly model, rasm: attraction-images-park/koleso.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/47-koleso-obozreniya/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png, preview_close.png

Tuzilish (xarita kodi shu nomlarga tayanadi, src/map/GltfModel.tsx):
    base       — qimirlamaydigan qism: dumaloq oynali pavilyon, 4 ta tayanch oyoq, bog'lovchilar, o'q, "GO" belgisi
    wheel      — g'ildirak: ikki halqali panjara, yulduz kegaylar, arqon kegaylar. Origin — o'q markazida,
                 o'q — Blender Y bo'ylab (old tomon -Y). Kod uni o'z o'qi atrofida aylantiradi
    cabin0..35 — kabinalar (wheel bolalari): origin — ilgak nuqtasida, kod teskari buradi — doim tik turadi
Asl o'lcham metrda: g'ildirak diametri ~35 m, eng baland nuqtasi ~38 m, pavilyon diametri 18 m.
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
    'white': (0.9, 0.9, 0.88), 'offwhite': (0.8, 0.8, 0.78), 'glass': (0.12, 0.16, 0.22), 'yellow': (0.98, 0.78, 0.05),
    'black': (0.06, 0.06, 0.07), 'roof': (0.84, 0.84, 0.82), 'cable': (0.75, 0.76, 0.78), 'red': (0.8, 0.15, 0.1),
    'orange': (0.95, 0.5, 0.1), 'steel': (0.6, 0.61, 0.63), 'concrete': (0.66, 0.65, 0.62),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.15 if name == 'glass' else 0.5
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
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return new_obj(name, bm, [mat])


def tube(name, a, b, r, mat, segs=6):
    """a→b quvur (dumaloq kesim)"""
    a, b = Vector(a), Vector(b)
    v = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=segs, radius1=r, radius2=r, depth=v.length)
    ob = new_obj(name, bm, [mat])
    ob.rotation_euler = v.to_track_quat('Z', 'Y').to_euler()
    ob.location = (a + b) / 2
    return ob


def lathe(name, profile, segs, mat_of, mats, phase=0.0):
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r < 1e-6:
            v = bm.verts.new((0, 0, z))
            rings.append([v] * segs)
        else:
            rings.append([bm.verts.new((r * math.cos(phase + 2 * math.pi * k / segs), r * math.sin(phase + 2 * math.pi * k / segs), z))
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


# ---------- O'lchamlar ----------
HUB_Z = 20.0          # o'q balandligi
R_OUT, R_IN = 17.2, 16.0   # g'ildirak panjarasining tashqi va ichki halqasi
RING_Y = 1.1          # ikki halqa orasidagi yarim masofa (o'q bo'ylab)
N_SEG = 40            # halqa bo'laklari
N_CAB = 36            # kabinalar
PAV_R, PAV_H = 9.0, 3.4   # pavilyon

# ---------- BASE ----------
p = []
# 1) Pavilyon: beton taglik, 16 qirrali oynali devor (oq ustunlar, sariq "GO" bannerlari), qirrali tom, karniz
p.append(lathe('plinth', [(PAV_R + 0.4, 0), (PAV_R + 0.4, 0.3), (0, 0.3)], 32, lambda i, k: 0, ['concrete']))
SIDES = 16
p.append(lathe('glass_wall', [(PAV_R, 0.3), (PAV_R, PAV_H)], SIDES, lambda i, k: 0, ['glass'], phase=math.pi / SIDES))
for k in range(SIDES):
    a = 2 * math.pi * k / SIDES
    ca, sa = math.cos(a), math.sin(a)
    p.append(box('column', (0.28, 0.28, PAV_H - 0.3), (ca * (PAV_R + 0.02), sa * (PAV_R + 0.02), 0.3 + (PAV_H - 0.3) / 2), 'white', (0, 0, a)))
    side = 2 * PAV_R * math.sin(math.pi / SIDES)
    am = a + math.pi / SIDES
    cx, cy = math.cos(am) * PAV_R * math.cos(math.pi / SIDES), math.sin(am) * PAV_R * math.cos(math.pi / SIDES)
    if k % 2 == 0:
        # sariq banner (oyna ichida) va undagi qora "GO" chiziqlari
        p.append(box('banner', (0.04, side * 0.9, 2.3), (cx * 1.003, cy * 1.003, 1.55), 'yellow', (0, 0, am)))
        # qora "Go" harflari: G — halqa, o — kichik halqa
        for dx, r in ((-0.4, 0.42), (0.45, 0.27)):
            gx, gy = cx * 1.006 - math.sin(am) * dx, cy * 1.006 + math.cos(am) * dx
            p.append(cyl('go', r, 0.03, (gx, gy, 1.45), 'black', 12, (0, math.pi / 2, am)))
            p.append(cyl('go_in', r * 0.55, 0.035, (gx * 1.0005, gy * 1.0005, 1.45), 'yellow', 12, (0, math.pi / 2, am)))
    else:
        p.append(box('poster', (0.04, side * 0.7, 1.9), (cx * 1.003, cy * 1.003, 1.5), 'orange', (0, 0, am)))  # taom reklamasi
    # oynaning tepa va pastki ramkasi
    p.append(box('mullion', (0.06, side, 0.08), (cx, cy, 2.55), 'white', (0, 0, am)))
# kirish eshigi (old tomonda, -Y)
p.append(box('door', (1.8, 0.06, 2.2), (0, -PAV_R - 0.05, 1.4), 'glass'))
p.append(box('door_frame', (2.0, 0.1, 0.15), (0, -PAV_R - 0.06, 2.55), 'white'))
p.append(lathe('fascia', [(PAV_R + 0.25, PAV_H), (PAV_R + 0.25, PAV_H + 0.35), (PAV_R, PAV_H + 0.35)], SIDES,
               lambda i, k: 0, ['white'], phase=math.pi / SIDES))
# qirrali tom: past konus, bo'laklar orasida qovurg'alar
p.append(lathe('roof', [(PAV_R, PAV_H + 0.35), (PAV_R * 0.55, PAV_H + 1.3), (PAV_R * 0.35, PAV_H + 1.45), (0, PAV_H + 1.45)],
               SIDES, lambda i, k: 0, ['roof'], phase=math.pi / SIDES))
for k in range(SIDES):
    a = 2 * math.pi * k / SIDES
    p.append(tube('rib', (math.cos(a) * PAV_R, math.sin(a) * PAV_R, PAV_H + 0.38),
                  (math.cos(a) * PAV_R * 0.36, math.sin(a) * PAV_R * 0.36, PAV_H + 1.48), 0.05, 'white', 4))

# 2) Tayanch oyoqlar: o'qning har bir uchiga ikki oyoq (A-shakl, g'ildirak tekisligida yoyilgan) + orqaga qiya oyoq
AXLE_Y = RING_Y + 1.4     # o'q uchlari (tayanch shu yerda)
LEG_R = 0.38
feet = []
for sy in (-1, 1):
    top = (0, sy * AXLE_Y, HUB_Z)
    for sx in (-1, 1):
        foot = (sx * 8.5, sy * 6.5, 0.0)
        feet.append(foot)
        p.append(tube('leg', foot, top, LEG_R, 'white', 10))
    # tik o'rta oyoq (rasmda orqadagi uchinchi oyoq)
    p.append(tube('leg_mid', (0, sy * 9.0, 0), top, LEG_R * 0.8, 'white', 10))
    feet.append((0, sy * 9.0, 0))
# oyoq ostidagi plitalar
for fx, fy, _ in feet:
    p.append(box('footplate', (1.3, 1.3, 0.35), (fx, fy, 0.175), 'concrete'))
    p.append(box('flange', (0.9, 0.9, 0.2), (fx, fy, 0.45), 'white'))


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


# ko'ndalang bog'lovchilar: har bir A-ramkada 3 sathda gorizontal, ikki ramka orasida ham
for t in (0.25, 0.5, 0.72):
    pts = {}
    for sy in (-1, 1):
        top = (0, sy * AXLE_Y, HUB_Z)
        l, r = lerp((-8.5, sy * 6.5, 0), top, t), lerp((8.5, sy * 6.5, 0), top, t)
        m = lerp((0, sy * 9.0, 0), top, t)
        p.append(tube('brace', l, r, 0.16, 'white', 6))
        p.append(tube('brace', m, l, 0.12, 'white', 6))
        p.append(tube('brace', m, r, 0.12, 'white', 6))
        pts[sy] = (l, r)
    if t < 0.6:  # old va orqa ramkani bog'lash (pavilyon ustida)
        p.append(tube('tie', pts[-1][0], pts[1][0], 0.12, 'white', 6))
        p.append(tube('tie', pts[-1][1], pts[1][1], 0.12, 'white', 6))
# qiya X-bog'lovchilar pastki sathda
for sy in (-1, 1):
    top = (0, sy * AXLE_Y, HUB_Z)
    p.append(tube('xbrace', lerp((-8.5, sy * 6.5, 0), top, 0.25), lerp((8.5, sy * 6.5, 0), top, 0.5), 0.1, 'white', 6))
    p.append(tube('xbrace', lerp((8.5, sy * 6.5, 0), top, 0.25), lerp((-8.5, sy * 6.5, 0), top, 0.5), 0.1, 'white', 6))

# 3) O'q, podshipnik korpuslari va "GO" belgisi
p.append(cyl('axle', 0.55, 2 * AXLE_Y + 0.6, (0, 0, HUB_Z), 'steel', 14, (math.pi / 2, 0, 0)))
for sy in (-1, 1):
    p.append(box('bearing', (1.4, 0.9, 1.4), (0, sy * AXLE_Y, HUB_Z), 'white'))
# sariq "GO" belgi — o'qning old uchida, biroz yumaloq burchakli kvadrat
GY = -AXLE_Y - 0.6
# yumaloq burchakli sariq kvadrat (markaziy kvadrat + 4 ta burchak doirasi)
SX, SZ = 0.9, HUB_Z - 0.2
p.append(box('go_sign', (2.6, 0.25, 1.8), (SX, GY, SZ), 'yellow'))
p.append(box('go_sign2', (1.8, 0.25, 2.6), (SX, GY, SZ), 'yellow'))
for dx in (-0.9, 0.9):
    for dz in (-0.9, 0.9):
        p.append(cyl('go_corner', 0.4, 0.25, (SX + dx, GY, SZ + dz), 'yellow', 10, (math.pi / 2, 0, 0)))
# "G": qora halqa, o'ng tomoni ochiq (sariq qopqoq), ichida gorizontal tirnoq; "o": kichik halqa
p.append(cyl('G', 0.62, 0.05, (SX - 0.35, GY - 0.14, SZ), 'black', 16, (math.pi / 2, 0, 0)))
p.append(cyl('G_in', 0.36, 0.06, (SX - 0.35, GY - 0.145, SZ), 'yellow', 16, (math.pi / 2, 0, 0)))
p.append(box('G_gap', (0.4, 0.07, 0.35), (SX - 0.05, GY - 0.15, SZ + 0.2), 'yellow'))
p.append(box('G_bar', (0.38, 0.07, 0.13), (SX - 0.1, GY - 0.155, SZ - 0.02), 'black'))
p.append(cyl('o', 0.36, 0.05, (SX + 0.65, GY - 0.14, SZ - 0.22), 'black', 14, (math.pi / 2, 0, 0)))
p.append(cyl('o_in', 0.18, 0.06, (SX + 0.65, GY - 0.145, SZ - 0.22), 'yellow', 14, (math.pi / 2, 0, 0)))
base = join('base', p)

# ---------- WHEEL (origin — o'q markazi) ----------
w = []
ring = lambda r, y: [(math.cos(2 * math.pi * k / N_SEG) * r, y, HUB_Z + math.sin(2 * math.pi * k / N_SEG) * r) for k in range(N_SEG)]
rings = {(r, y): ring(r, y) for r in (R_OUT, R_IN) for y in (-RING_Y, RING_Y)}
for (r, y), pts in rings.items():   # 4 ta halqa (tashqi/ichki × old/orqa)
    for k in range(N_SEG):
        w.append(tube('ring', pts[k], pts[(k + 1) % N_SEG], 0.13 if r == R_OUT else 0.1, 'white', 4))
for k in range(N_SEG):  # panjara: radial, o'q bo'ylab va qiya bog'lovchilar
    for y in (-RING_Y, RING_Y):
        w.append(tube('lat', rings[(R_OUT, y)][k], rings[(R_IN, y)][k], 0.06, 'offwhite', 3))
        w.append(tube('diag', rings[(R_OUT, y)][k], rings[(R_IN, y)][(k + 1) % N_SEG], 0.045, 'offwhite', 3))
    w.append(tube('cross', rings[(R_OUT, -RING_Y)][k], rings[(R_OUT, RING_Y)][k], 0.06, 'offwhite', 3))
    if k % 2 == 0:
        w.append(tube('cross_in', rings[(R_IN, -RING_Y)][k], rings[(R_IN, RING_Y)][(k + 1) % N_SEG], 0.045, 'offwhite', 4))
# Markaz (hub) halqasi
w.append(cyl('hub', 1.3, 2 * RING_Y + 0.8, (0, 0, HUB_Z), 'white', 16, (math.pi / 2, 0, 0)))
# 6 ta yulduz kegay: har biri uchburchak kesimli panjara (old/orqa hubdan ichki halqaga), uchi ingichka
for s in range(6):
    a = 2 * math.pi * s / 6 + math.pi / 2
    tip = (math.cos(a) * R_IN, 0, HUB_Z + math.sin(a) * R_IN)
    for y in (-RING_Y - 0.3, RING_Y + 0.3):
        root = (math.cos(a) * 1.2, y, HUB_Z + math.sin(a) * 1.2)
        w.append(tube('star', root, (tip[0], y * 0.3, tip[2]), 0.12, 'white', 6))
    # yon qirra (tekislikda) — kegay "uchburchagi"
    for da in (-0.09, 0.09):
        root = (math.cos(a + da) * 1.3, 0, HUB_Z + math.sin(a + da) * 1.3)
        w.append(tube('star_side', root, tip, 0.08, 'white', 5))
    for j in range(1, 7):  # kegay ichidagi zinapoyasimon bog'lovchilar
        t = j / 7
        r = 1.2 + (R_IN - 1.2) * t
        y = (RING_Y + 0.3) * (1 - 0.7 * t)
        c = (math.cos(a) * r, 0, HUB_Z + math.sin(a) * r)
        w.append(tube('star_rung', (c[0], -y, c[2]), (c[0], y, c[2]), 0.04, 'offwhite', 4))
# Arqon kegaylar: hubning old va orqa chetidan ichki halqaga (kesishgan holda)
for k in range(0, N_SEG, 2):
    for y, sh in ((-RING_Y - 0.4, 1), (RING_Y + 0.4, -1)):
        a = 2 * math.pi * k / N_SEG
        root = (math.cos(a) * 1.1, y, HUB_Z + math.sin(a) * 1.1)
        end = rings[(R_IN, -y / abs(y) * RING_Y)][(k + sh * 3) % N_SEG]
        w.append(tube('cable', root, end, 0.022, 'cable', 3))
wheel = join('wheel', w)
# origin — o'q markaziga
bpy.ops.object.select_all(action='DESELECT')
wheel.select_set(True)
bpy.context.view_layer.objects.active = wheel
scene.cursor.location = (0, 0, HUB_Z)
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

# ---------- Kabinalar (origin — ilgak nuqtasi; kabina ilgakdan pastda osilib turadi) ----------
R_PIVOT = R_OUT + 0.35


def cabin(k):
    c = []
    # tuxumsimon kabina: pastda sariq, o'rtada qora oyna tasmasi, tepada oq qalpoq
    prof = [(0, -2.3), (0.5, -2.27), (0.82, -2.08), (0.95, -1.8), (0.97, -1.5), (0.95, -1.1), (0.84, -0.85), (0.55, -0.66), (0, -0.6)]
    # 0..2 — sariq pastki qism, 3..4 — qora oyna tasmasi, 5.. — oq qalpoq
    mat = lambda i, kk: 0 if i <= 2 else (1 if i <= 4 else 2)
    body = lathe('cab', prof, 12, mat, ['yellow', 'glass', 'white'])
    body.scale = (1.0, 0.85, 1.0)  # biroz yassi (g'ildirak tekisligida uzun)
    c.append(body)
    for sx in (-1, 1):  # eshik ramkalari (oq tik chiziqlar)
        c.append(box('frame', (0.05, 0.05, 0.55), (sx * 0.4, -0.82, -1.42), 'white'))
    c.append(cyl('logo', 0.17, 0.03, (0, -0.83, -1.95), 'black', 10, (math.pi / 2, 0, 0)))  # sariq qismdagi qora spiral belgi
    c.append(cyl('logo_in', 0.09, 0.035, (0, -0.835, -1.95), 'yellow', 10, (math.pi / 2, 0, 0)))
    c.append(box('hanger', (0.14, 0.14, 0.62), (0, 0, -0.3), 'white'))           # ilgak
    c.append(box('hanger_bar', (0.14, 0.7, 0.14), (0, 0, 0), 'white'))           # halqaga mahkamlagich
    ob = join(f'cabin{k}', c)
    a = 2 * math.pi * k / N_CAB
    ob.location = (math.cos(a) * R_PIVOT, 0, HUB_Z + math.sin(a) * R_PIVOT)
    # wheel bolasi: lokal koordinata — wheel origin (o'q markazi) ga nisbatan
    ob.parent = wheel
    ob.location = (math.cos(a) * R_PIVOT, 0, math.sin(a) * R_PIVOT)
    return ob


cabins = [cabin(k) for k in range(N_CAB)]

objs = [o for o in scene.objects if o.type == 'MESH']
tris = sum(len(pg.vertices) - 2 for o in objs for pg in o.data.polygons)
top = HUB_Z + R_PIVOT
print(f'KOLESO tris={tris} top={top:.1f}m objects={len(objs)}')

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'KOLESO glb={OUT_GLB.stat().st_size // 1024} KB')

# ---------- Preview: umumiy va yaqin ----------
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
world = bpy.data.worlds.new('w')
world.color = (0.93, 0.95, 0.98)
scene.world = world
for name, loc, target, res in [('preview.png', (34, -52, 26), (0, 0, 18), (900, 1000)),
                               ('preview_close.png', (13, -17, 7), (0, 0, 4), (1000, 800)),
                               ('preview_hub.png', (7, -14, 14.5), (0, -2, 16.5), (1000, 800))]:
    cam.location = loc
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = str(PREVIEW_DIR / name)
    bpy.ops.render.render(write_still=True)
print('KOLESO preview done')

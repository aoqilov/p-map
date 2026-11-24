"""
Eyfel minorasi — bezak (attraksion emas). Rasm: attraction-images-park/efil.png
Haqiqiy minora (330 m) proporsiyalarida, panjarali (to'r) konstruksiya: to'rt egilgan oyoq, ular orasida ravoqlar,
1-qavat (panjarali friz, galereya, burchak pavilyonlari), 2-qavat, oyoqlar qo'shilgan tana, 3-qavat kabinasi,
chiroqxona va antenna. Tagida tosh maydoncha va oyoq poydevorlari.

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/decor/eyfel-minorasi/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png

Bitta `base` obyekti (animatsiya yo'q). Asl o'lcham: balandligi H_TOTAL (antenna uchigacha), asosi ~0.38 × H.
Xaritadagi o'lcham — config.ts dagi `size`.
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
    'iron': (0.3, 0.24, 0.19),        # "Eyfel jigarrangi"
    'iron_light': (0.4, 0.33, 0.26),
    'stone': (0.72, 0.7, 0.66), 'stone_dark': (0.55, 0.53, 0.5), 'glass': (0.75, 0.8, 0.82), 'bulb': (1.0, 0.85, 0.55),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.6
    if name.startswith('iron'):
        bsdf.inputs['Metallic'].default_value = 0.25
    if name == 'bulb':
        bsdf.inputs['Emission Color'].default_value = (*rgb, 1)
        bsdf.inputs['Emission Strength'].default_value = 1.5
    m.diffuse_color = (*rgb, 1)
    MATS[name] = m

# Barcha to'sinlar bitta bmesh'ga yig'iladi (minglab obyekt o'rniga) — material bo'yicha
BMS = {}


def bm_for(mat):
    if mat not in BMS:
        BMS[mat] = bmesh.new()
    return BMS[mat]


def add_box(mat, size, loc, rot_q=None):
    bm = bm_for(mat)
    geom = bmesh.ops.create_cube(bm, size=1.0)
    vs = geom['verts']
    bmesh.ops.scale(bm, vec=size, verts=vs)
    if rot_q is not None:
        bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=rot_q.to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=vs)


def bar(a, b, w, mat='iron'):
    """a → b to'sin (kvadrat kesim w)"""
    a, b = Vector(a), Vector(b)
    v = b - a
    if v.length < 1e-4:
        return
    add_box(mat, (v.length, w, w), (a + b) / 2, v.to_track_quat('X', 'Z'))


def add_cyl(mat, r, h, loc, segs=12, r2=None):
    bm = bm_for(mat)
    geom = bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bmesh.ops.translate(bm, vec=loc, verts=geom['verts'])


def add_ball(mat, r, loc):
    bm = bm_for(mat)
    geom = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
    bmesh.ops.translate(bm, vec=loc, verts=geom['verts'])


def lattice_face(p00, p01, p10, p11, chord, diag, cells=1):
    """To'rtburchak yuz (p00-p01 pastki qirra, p10-p11 ustki): ichida X-bog'lovchilar (cells ta katak eni bo'yicha)"""
    for k in range(cells):
        a0 = Vector(p00).lerp(Vector(p01), k / cells)
        a1 = Vector(p00).lerp(Vector(p01), (k + 1) / cells)
        b0 = Vector(p10).lerp(Vector(p11), k / cells)
        b1 = Vector(p10).lerp(Vector(p11), (k + 1) / cells)
        bar(a0, b1, diag)
        bar(a1, b0, diag)
        if 0 < k:
            bar(a0, b0, diag * 1.1)


# ====================== o'lchamlar ======================
H_TOTAL = 13.0                    # antenna uchigacha, m (xaritada — config.ts → size)
S = H_TOTAL / 330.0               # haqiqiy minora → model
Z1, Z2, Z3, ZTOP = 57 * S, 115 * S, 276 * S, 300 * S
CH = 0.075 * H_TOTAL / 13          # asosiy ustun (chord) qalinligi
DG = 0.03 * H_TOTAL / 13           # bog'lovchilar


def outer(z):
    """Minora tashqi yarim eni (z balandlikda) — Eyfel egri chizig'i"""
    zz = z / S
    return S * (62.5 * math.exp(-zz / 95.0) + 2.2 * (1 - zz / 330.0))


def inner(z):
    """Oyoqlar ichki yarim eni: asosda 37.5 m, 2-qavatgacha (115 m) nolga yaqinlashadi — oyoqlar qo'shiladi"""
    zz = z / S
    if zz >= 112:
        return 0.0
    t = zz / 112.0
    return S * 37.5 * (1 - t) ** 1.35


# ---------- tosh maydoncha va poydevorlar ----------
B0 = outer(0)
add_box('stone', (2 * B0 + 1.6, 2 * B0 + 1.6, 0.12), (0, 0, 0.06))
add_box('stone_dark', (2 * B0 + 1.7, 2 * B0 + 1.7, 0.04), (0, 0, 0.02))
for sx in (-1, 1):
    for sy in (-1, 1):
        c = (outer(0) + inner(0)) / 2
        add_box('stone_dark', (outer(0) - inner(0) + 0.3, outer(0) - inner(0) + 0.3, 0.22), (sx * c, sy * c, 0.23))

# ---------- to'rt oyoq (z: 0 → Z2) ----------
NL = 14
zs = [Z2 * (k / NL) ** 1.0 for k in range(NL + 1)]
G = 0.34          # yerdan oyoq boshlanishi (poydevor ustida)
zs[0] = G
for sx in (-1, 1):
    for sy in (-1, 1):
        def corners(z):
            o, i = outer(z), inner(z)
            # oyoq kesimi: tashqi burchak (o,o), ichki burchak (i,i) — to'rt qirra
            return [(sx * o, sy * o, z), (sx * o, sy * i, z), (sx * i, sy * i, z), (sx * i, sy * o, z)]
        prev = corners(zs[0])
        for k in range(1, len(zs)):
            cur = corners(zs[k])
            for j in range(4):
                bar(prev[j], cur[j], CH)                                  # asosiy ustunlar
            for j in range(4):                                             # to'rt yuzida X-bog'lovchilar
                a, b = j, (j + 1) % 4
                width = (Vector(prev[a]) - Vector(prev[b])).length
                lattice_face(prev[a], prev[b], cur[a], cur[b], CH, DG, cells=2 if width > 0.55 else 1)
            for j in range(4):                                             # gorizontal halqa
                bar(cur[j], cur[(j + 1) % 4], DG * 1.4)
            prev = cur

# ---------- ravoqlar (oyoqlar orasida, to'rt tomonda) va 1-qavat ostidagi friz ----------
ARCH_TOP = 39 * S
for face in range(4):
    ang = face * math.pi / 2
    ca, sa = math.cos(ang), math.sin(ang)

    def P(u, z, d):
        """yuz koordinatasi: u — yon (yuz bo'ylab), d — markazdan uzoqlik"""
        return (ca * d - sa * u, sa * d + ca * u, z)
    # ravoq: ikki egri (ichki va tashqi), orasida bog'lovchilar
    pts_in, pts_out = [], []
    NA = 16
    for k in range(NA + 1):
        t = k / NA
        th = math.pi * t
        # ravoq oyoqlarning ichki qirrasidan (z ~ 20 m) boshlanib, markazda 39 m ga ko'tariladi
        z_spring = 18 * S
        u0 = inner(z_spring)
        u = -u0 * math.cos(th)
        z = z_spring + (ARCH_TOP - z_spring) * math.sin(th)
        d = outer(z) - 0.02
        pts_in.append(P(u, z, d))
        pts_out.append(P(u, z + 0.28 * H_TOTAL / 13, outer(z + 0.28 * H_TOTAL / 13) - 0.02))
    for k in range(NA):
        bar(pts_in[k], pts_in[k + 1], CH * 0.8)
        bar(pts_out[k], pts_out[k + 1], DG * 1.4)
        bar(pts_in[k], pts_out[k + 1], DG)
        bar(pts_in[k + 1], pts_out[k], DG)
    # friz: 1-qavat ostidagi panjarali kamar (z: Z1-0.55 .. Z1)
    zf0, zf1 = Z1 - 0.5 * H_TOTAL / 13, Z1
    o0, o1 = outer(zf0) + 0.02, outer(zf1) + 0.06
    NF = 10
    for k in range(NF):
        u_a = -o0 + 2 * o0 * k / NF
        u_b = -o0 + 2 * o0 * (k + 1) / NF
        u_c = -o1 + 2 * o1 * k / NF
        u_d = -o1 + 2 * o1 * (k + 1) / NF
        bar(P(u_a, zf0, o0), P(u_d, zf1, o1), DG)
        bar(P(u_b, zf0, o0), P(u_c, zf1, o1), DG)
        bar(P(u_a, zf0, o0), P(u_c, zf1, o1), DG)
    bar(P(-o0, zf0, o0), P(o0, zf0, o0), CH * 0.8)
    bar(P(-o1, zf1, o1), P(o1, zf1, o1), CH)
    # friz o'rtasidagi kichik ravoqchalar (bezak)
    for k in range(6):
        uc = -o0 * 0.8 + k * (1.6 * o0) / 5
        for j in range(6):
            th1, th2 = math.pi * j / 6, math.pi * (j + 1) / 6
            r = 0.1 * H_TOTAL / 13
            bar(P(uc + r * math.cos(th1), zf0 + 0.08 + r * math.sin(th1), o0 + 0.01),
                P(uc + r * math.cos(th2), zf0 + 0.08 + r * math.sin(th2), o0 + 0.01), DG * 0.8)


def platform(z, half, thick, rail_h, posts, pavilions=False):
    """Qavat: maydoncha, chetida galereya panjarasi, burchaklarda pavilyonlar"""
    add_box('iron_light', (2 * half, 2 * half, thick), (0, 0, z + thick / 2))
    hole = inner(z) * 0.95
    rail_z = z + thick
    for face in range(4):
        ang = face * math.pi / 2
        ca, sa = math.cos(ang), math.sin(ang)

        def P(u, zz, d=half):
            return (ca * d - sa * u, sa * d + ca * u, zz)
        bar(P(-half, rail_z + rail_h), P(half, rail_z + rail_h), DG * 1.6)
        bar(P(-half, rail_z + rail_h * 0.5), P(half, rail_z + rail_h * 0.5), DG)
        for k in range(posts + 1):
            u = -half + 2 * half * k / posts
            bar(P(u, rail_z), P(u, rail_z + rail_h), DG)
        if pavilions:  # burchak pavilyoni (kichik kabina, oynali)
            pass
    if pavilions:
        for sx in (-1, 1):
            for sy in (-1, 1):
                c = half * 0.72
                pw = half * 0.35
                add_box('iron_light', (pw, pw, 0.3 * H_TOTAL / 13), (sx * c, sy * c, rail_z + 0.15 * H_TOTAL / 13))
                add_box('glass', (pw * 0.9, pw * 1.02, 0.16 * H_TOTAL / 13), (sx * c, sy * c, rail_z + 0.17 * H_TOTAL / 13))
                add_box('iron', (pw * 1.1, pw * 1.1, 0.04), (sx * c, sy * c, rail_z + 0.32 * H_TOTAL / 13))
    for sx in (-1, 1):  # burchak chiroqlari
        for sy in (-1, 1):
            add_ball('bulb', 0.05 * H_TOTAL / 13, (sx * half, sy * half, rail_z + rail_h + 0.06))


# ---------- 1-qavat va 2-qavat ----------
platform(Z1, outer(Z1) + 0.12, 0.08 * H_TOTAL / 13, 0.22 * H_TOTAL / 13, 8, pavilions=True)
platform(Z2, outer(Z2) + 0.1, 0.06 * H_TOTAL / 13, 0.18 * H_TOTAL / 13, 5)
# 1–2 qavat orasidagi gorizontal "kamar"
for z in (Z1 + (Z2 - Z1) * 0.5,):
    o = outer(z)
    for face in range(4):
        ang = face * math.pi / 2
        ca, sa = math.cos(ang), math.sin(ang)
        bar((ca * o - sa * -o, sa * o + ca * -o, z), (ca * o - sa * o, sa * o + ca * o, z), DG * 1.5)

# ---------- tana: 2-qavatdan 3-qavatgacha (to'rt qirrali, torayib boradi) ----------
NS = 14
zs2 = [Z2 + (Z3 - Z2) * k / NS for k in range(NS + 1)]


def shaft(z):
    o = outer(z)
    return [(o, o, z), (-o, o, z), (-o, -o, z), (o, -o, z)]


prev = shaft(zs2[0])
for k in range(1, len(zs2)):
    cur = shaft(zs2[k])
    for j in range(4):
        bar(prev[j], cur[j], CH * (1 - 0.4 * k / NS))
    for j in range(4):
        a, b = j, (j + 1) % 4
        lattice_face(prev[a], prev[b], cur[a], cur[b], CH, DG * 0.9, cells=2 if k < NS * 0.4 else 1)
        bar(cur[a], cur[b], DG * 1.2)
    if k % 4 == 0:  # ichki ko'ndalang (diafragma)
        bar(cur[0], cur[2], DG)
        bar(cur[1], cur[3], DG)
    prev = cur

# ---------- 3-qavat (kabina), chiroqxona, antenna ----------
o3 = outer(Z3)
add_box('iron_light', (2 * o3 + 0.22, 2 * o3 + 0.22, 0.05), (0, 0, Z3 + 0.025))
add_box('glass', (2 * o3, 2 * o3, 0.22 * H_TOTAL / 13), (0, 0, Z3 + 0.05 + 0.11 * H_TOTAL / 13))
for sx in (-1, 1):
    for sy in (-1, 1):
        bar((sx * o3, sy * o3, Z3 + 0.05), (sx * o3, sy * o3, Z3 + 0.27 * H_TOTAL / 13), DG * 1.5)
add_box('iron', (2 * o3 + 0.06, 2 * o3 + 0.06, 0.04), (0, 0, Z3 + 0.29 * H_TOTAL / 13))
for face in range(4):  # 3-qavat galereya panjarasi
    ang = face * math.pi / 2
    ca, sa = math.cos(ang), math.sin(ang)
    d = o3 + 0.11
    zr = Z3 + 0.05 + 0.1 * H_TOTAL / 13
    bar((ca * d - sa * -d, sa * d + ca * -d, zr), (ca * d - sa * d, sa * d + ca * d, zr), DG)
zt = Z3 + 0.3 * H_TOTAL / 13
ot = outer(ZTOP)
for sx in (-1, 1):     # chiroqxonagacha to'rt ustun
    for sy in (-1, 1):
        bar((sx * o3 * 0.8, sy * o3 * 0.8, zt), (sx * ot, sy * ot, ZTOP), DG * 1.6)
add_box('iron_light', (2 * ot + 0.08, 2 * ot + 0.08, 0.05), (0, 0, ZTOP))
add_cyl('iron', ot * 0.9, 0.22 * H_TOTAL / 13, (0, 0, ZTOP + 0.13 * H_TOTAL / 13), 8)
add_ball('bulb', ot * 0.6, (0, 0, ZTOP + 0.27 * H_TOTAL / 13))
add_cyl('iron', ot * 0.7, 0.06, (0, 0, ZTOP + 0.34 * H_TOTAL / 13), 8, ot * 0.4)
add_cyl('iron', 0.025 * H_TOTAL / 13, H_TOTAL - ZTOP - 0.36 * H_TOTAL / 13,
        (0, 0, (ZTOP + 0.36 * H_TOTAL / 13 + H_TOTAL) / 2), 6, 0.008)

# ====================== yig'ish ======================
objs = []
for mat, bm in BMS.items():
    me = bpy.data.meshes.new(mat)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(MATS[mat])
    ob = bpy.data.objects.new(mat, me)
    scene.collection.objects.link(ob)
    objs.append(ob)
bpy.ops.object.select_all(action='DESELECT')
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.join()
base = bpy.context.view_layer.objects.active
base.name = base.data.name = 'base'

tris = sum(len(pg.vertices) - 2 for pg in base.data.polygons)
xs = [v.co.x for v in base.data.vertices]
top = max(v.co.z for v in base.data.vertices)
print(f'EIFFEL tris={tris} width={max(xs) - min(xs):.2f} top={top:.2f}')

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'EIFFEL glb={OUT_GLB.stat().st_size // 1024} KB')

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
scene.camera = cam
cam.location = (11.0, -14.0, 7.0)
cam.rotation_euler = (Vector((0, 0, 5.6)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 900, 1100
world = bpy.data.worlds.new('w')
world.color = (0.95, 0.96, 0.97)
scene.world = world
scene.render.filepath = str(PREVIEW_DIR / 'preview.png')
bpy.ops.render.render(write_still=True)
print('EIFFEL preview', scene.render.filepath)

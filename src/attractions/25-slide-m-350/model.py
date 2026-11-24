"""
25 — Аттракцион "Slide M 350" (ko'p yo'lakli to'lqinli tepalik). Rasm: attraction-images-park/Multi_Track_Slide.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/25-slide-m-350/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png (va preview_top.png — start minorasi yaqindan)

Bitta qimirlamaydigan `base` obyekti (animatsiya yo'q):
    6 ta rangli to'lqinli yo'lak (ko'k, yashil, sariq, to'q sariq, qizil, pushti), ikki yonida to'lqinli havorang devor
    (bulutlar bilan), yo'lak ostida tayanch ustunlar, start minorasi (panjarali ramka, X-bog'lovchilar), start maydonchasi
    va quyosh rasmli orqa taxta, yon tomonda uzun zina (panjaralar bilan), chiroqli "palma" ustunlar (qizil egilgan
    shoxlarda oq chiroqlar).
Joylashuv (lokal): uzunligi — Y; start minorasi +Y uchida, tushish -Y uchida (old tomon). Zina — +X tomonda.
Asl o'lcham metrda: 37.0 × 6.1 m, start maydonchasi 8.5 m, chiroqlar bilan ~12.6 m.
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

LANE_COLS = ['l_blue', 'l_green', 'l_yellow', 'l_orange', 'l_red', 'l_pink']
PALETTE = {
    'l_blue': (0.1, 0.42, 0.85), 'l_green': (0.25, 0.7, 0.2), 'l_yellow': (0.98, 0.82, 0.1), 'l_orange': (0.98, 0.5, 0.1),
    'l_red': (0.9, 0.15, 0.15), 'l_pink': (0.8, 0.25, 0.6), 'sky': (0.55, 0.76, 0.95), 'cloud': (0.97, 0.98, 1.0),
    'steel': (0.6, 0.62, 0.64), 'steel_dark': (0.42, 0.43, 0.45), 'grate': (0.65, 0.66, 0.68), 'red': (0.78, 0.1, 0.12),
    'bulb': (1.0, 0.96, 0.85), 'sun': (0.98, 0.78, 0.1), 'sun_ray': (0.98, 0.6, 0.05), 'dark': (0.12, 0.1, 0.1),
    'under': (0.35, 0.55, 0.8),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.25 if name.startswith('l_') else 0.5
    if name in ('steel', 'steel_dark', 'grate'):
        bsdf.inputs['Metallic'].default_value = 0.3  # xaritada atrof-muhit aksi yo'q — yuqori metallik qoraygan ko'rinadi
    if name == 'bulb':
        bsdf.inputs['Emission Color'].default_value = (*rgb, 1)
        bsdf.inputs['Emission Strength'].default_value = 1.2
    m.diffuse_color = (*rgb, 1)
    MATS[name] = m


# ====================== yordamchilar ======================
def new_obj(name, bm, mat):
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
    return new_obj('box', bm, mat)


def cyl(r, h, loc, mat, segs=12, rot=(0, 0, 0), r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return new_obj('cyl', bm, mat)


def ball(r, loc, mat, sub=1, scale=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return new_obj('ball', bm, mat)


def beam(a, b, w, d, mat):
    a, b = Vector(a), Vector(b)
    v = b - a
    ob = box((v.length, w, d), (0, 0, 0), mat)
    ob.rotation_euler = v.to_track_quat('X', 'Z').to_euler()
    ob.location = (a + b) / 2
    return ob


def limb(a, b, r1, r2, mat, segs=6):
    a, b = Vector(a), Vector(b)
    d = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r1, radius2=r2, depth=d.length)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix())
    bmesh.ops.translate(bm, vec=(a + b) / 2, verts=bm.verts)
    return new_obj('limb', bm, mat)


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
    ob.data.shade_smooth()
    ob.data.set_sharp_from_angle(angle=math.radians(50))
    return ob


# ====================== o'lchamlar va yo'lak profili ======================
Y_END, Y_TOP0, Y_TOP1 = -18.4, 15.4, 18.5     # tushish uchi, start maydonchasi (Y oralig'i)
Z_TOP = 8.5                                     # start maydonchasi
Z_RUN = 0.65                                    # tushish (gorizontal qismi) balandligi
Y_RUN = -12.5                                   # qiyalik tugaydigan joy
LW = 0.76                                       # yo'lak eni
X_L = -3.0                                      # chap (−X) devor ichki qirrasi
X_R = X_L + 6 * LW                              # o'ng devor (zina tomonida)
DEPTH = 0.22                                    # yo'lak chuqurligi
WAVES = 3.5                                     # to'lqinlar soni (qiyalikda)


def zc(y):
    """Yo'lak o'rta chizig'i (tub emas — qirralar) balandligi"""
    if y >= Y_TOP0 - 0.4:
        return Z_TOP
    if y <= Y_RUN:
        # gorizontal tushish, uchida biroz ko'tarilgan lab
        t = (Y_RUN - y) / (Y_RUN - Y_END)
        return Z_RUN + 0.12 * t ** 3
    t = (y - Y_RUN) / (Y_TOP0 - 0.4 - Y_RUN)
    s = 0.5 * t + 0.5 * (3 * t * t - 2 * t ** 3)
    wave = 0.42 * math.sin(math.pi * t) * math.sin(2 * math.pi * WAVES * t)
    return Z_RUN + (Z_TOP - Z_RUN) * s + wave


YS = [Y_END + i * 0.25 for i in range(int((Y_TOP0 - Y_END) / 0.25) + 1)]

p = []
# ---------- 6 ta yo'lak (U-kesim, chegara qirralari) ----------
for i, col in enumerate(LANE_COLS):
    x0 = X_L + i * LW
    bm = bmesh.new()
    rings = []
    NK = 10
    for y in YS:
        z = zc(y)
        ring = []
        for k in range(NK + 1):
            u = k / NK
            x = x0 + u * LW
            dz = -DEPTH * math.sin(math.pi * u) ** 0.8 + 0.05 * (1 - math.sin(math.pi * u))   # qirralari ko'tarilgan
            ring.append(bm.verts.new((x, y, z + dz)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(NK):
            bm.faces.new([a[k], a[k + 1], b[k + 1], b[k]])   # normal tepaga (x→, y→)
    # tushish uchidagi "lab": oxirgi kesimdan pastga
    p.append(new_obj('lane', bm, col))
# yo'laklar osti (pastdan ko'rinadi) — normal pastga
bm = bmesh.new()
rings = []
for y in YS:
    z = zc(y) - DEPTH - 0.18
    rings.append([bm.verts.new((X_L - 0.05, y, z)), bm.verts.new((X_R + 0.05, y, z))])
for a, b in zip(rings, rings[1:]):
    bm.faces.new([a[0], b[0], b[1], a[1]])
p.append(new_obj('under', bm, 'under'))
# tushish uchi (old yuz)
p.append(box((X_R - X_L + 0.1, 0.06, DEPTH + 0.25), ((X_L + X_R) / 2, Y_END - 0.02, zc(Y_END) - DEPTH / 2), 'under'))


# ---------- yon devorlar: to'lqinli tepa (havorang, bulutlar) ----------
def wall_top(y, side):
    t = (y - Y_END) / (Y_TOP0 - Y_END)
    return zc(y) + 0.42 + 0.22 * math.sin(2 * math.pi * (t * 9 + (0.25 if side > 0 else 0)))


for side, xw in ((-1, X_L - 0.04), (1, X_R + 0.04)):
    bm = bmesh.new()
    rows = []
    for y in YS:
        zb = zc(y) - DEPTH - 0.2
        zt = wall_top(y, side)
        rows.append((bm.verts.new((xw + side * 0.04, y, zb)), bm.verts.new((xw + side * 0.04, y, zt)),
                     bm.verts.new((xw - side * 0.04, y, zb)), bm.verts.new((xw - side * 0.04, y, zt))))
    for a, b in zip(rows, rows[1:]):
        # tashqi yuz (side yo'nalishida), ichki yuz, tepa qirra
        if side > 0:
            bm.faces.new([a[0], b[0], b[1], a[1]])
            bm.faces.new([a[2], a[3], b[3], b[2]])
        else:
            bm.faces.new([a[0], a[1], b[1], b[0]])
            bm.faces.new([a[2], b[2], b[3], a[3]])
        bm.faces.new([a[1], b[1], b[3], a[3]] if side > 0 else [a[1], a[3], b[3], b[1]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    p.append(new_obj('wall', bm, 'sky'))
    # bulutlar (tashqi yuzda oq dog'lar)
    for k in range(26):
        y = Y_END + 0.8 + k * (Y_TOP0 - Y_END - 1.2) / 25
        zt = wall_top(y, side)
        zb = zc(y) - DEPTH - 0.2
        z = zb + (zt - zb) * (0.35 + 0.3 * ((k * 7) % 5) / 4)
        for j, (dy, dz, r) in enumerate(((0, 0, 0.16), (0.18, 0.04, 0.12), (-0.17, 0.02, 0.11))):
            p.append(ball(r, (xw + side * 0.085, y + dy, z + dz), 'cloud', 1, (0.25, 1.4, 0.8)))

# ---------- tayanch ustunlar (yo'lak ostida) ----------
for y in (-15.5, -10.5, -6.0, -1.5, 3.0, 7.5, 11.5):
    z_top = zc(y) - DEPTH - 0.2
    for x in (X_L + 0.35, X_R - 0.35):
        p.append(cyl(0.1, z_top, (x, y, z_top / 2), 'steel', 10))
        p.append(box((0.4, 0.4, 0.05), (x, y, 0.025), 'steel_dark'))
    p.append(beam((X_L, y, z_top - 0.05), (X_R, y, z_top - 0.05), 0.12, 0.12, 'steel'))
    if z_top > 2.5:
        p.append(beam((X_L + 0.35, y, 0.3), (X_R - 0.35, y, z_top - 0.3), 0.06, 0.06, 'steel'))

# ---------- start minorasi: ramka, X-bog'lovchilar, maydoncha ----------
TX0, TX1 = X_L - 0.05, 3.05
for x in (TX0, (TX0 + TX1) / 2, TX1):
    for y in (Y_TOP0 + 0.1, Y_TOP1 - 0.1):
        p.append(box((0.16, 0.16, Z_TOP), (x, y, Z_TOP / 2), 'steel'))
        p.append(box((0.45, 0.45, 0.05), (x, y, 0.025), 'steel_dark'))
for z in (0.25, Z_TOP / 3, 2 * Z_TOP / 3, Z_TOP - 0.15):
    for y in (Y_TOP0 + 0.1, Y_TOP1 - 0.1):
        p.append(beam((TX0, y, z), (TX1, y, z), 0.1, 0.1, 'steel'))
    for x in (TX0, TX1):
        p.append(beam((x, Y_TOP0 + 0.1, z), (x, Y_TOP1 - 0.1, z), 0.1, 0.1, 'steel'))
for z0, z1 in ((0.25, Z_TOP / 3), (Z_TOP / 3, 2 * Z_TOP / 3), (2 * Z_TOP / 3, Z_TOP - 0.15)):
    for x in (TX0, TX1):   # yon yuzlarida X
        p.append(beam((x, Y_TOP0 + 0.1, z0), (x, Y_TOP1 - 0.1, z1), 0.06, 0.06, 'steel'))
        p.append(beam((x, Y_TOP1 - 0.1, z0), (x, Y_TOP0 + 0.1, z1), 0.06, 0.06, 'steel'))
    for y in (Y_TOP0 + 0.1, Y_TOP1 - 0.1):
        for xa, xb in ((TX0, (TX0 + TX1) / 2), ((TX0 + TX1) / 2, TX1)):
            p.append(beam((xa, y, z0), (xb, y, z1), 0.06, 0.06, 'steel'))
            p.append(beam((xb, y, z0), (xa, y, z1), 0.06, 0.06, 'steel'))
p.append(box((TX1 - TX0 + 0.1, Y_TOP1 - Y_TOP0 + 0.4, 0.15), ((TX0 + TX1) / 2, (Y_TOP0 + Y_TOP1) / 2 - 0.2, Z_TOP - 0.08),
             'grate'))
# start joyi: yo'laklar ustidagi to'siq-bar (har yo'lakda)
for i in range(6):
    x = X_L + (i + 0.5) * LW
    p.append(beam((x - 0.3, Y_TOP0 + 0.2, Z_TOP + 0.6), (x + 0.3, Y_TOP0 + 0.2, Z_TOP + 0.6), 0.04, 0.04, 'steel'))
    p.append(box((0.04, 0.04, 0.6), (x - 0.35, Y_TOP0 + 0.2, Z_TOP + 0.3), 'steel'))
# orqa taxta: havorang, bulutlar, quyosh (yuzli)
BX0, BX1 = X_L - 0.05, X_R + 0.05
BZ0, BZ1 = Z_TOP, Z_TOP + 2.4
BY = Y_TOP1 - 0.05
p.append(box((BX1 - BX0, 0.08, BZ1 - BZ0), ((BX0 + BX1) / 2, BY, (BZ0 + BZ1) / 2), 'sky'))
for k in range(9):
    x = BX0 + 0.3 + (k * 0.53) % (BX1 - BX0 - 0.6)
    z = BZ0 + 0.3 + ((k * 0.71) % 1.8)
    p.append(ball(0.18, (x, BY - 0.05, z), 'cloud', 1, (1.6, 0.25, 0.8)))
SC = Vector(((BX0 + BX1) / 2 + 0.3, BY - 0.07, BZ0 + 1.25))
for k in range(14):   # nurlar
    a = 2 * math.pi * k / 14
    p.append(box((0.22, 0.03, 0.5), (SC.x + 0.62 * math.cos(a), SC.y, SC.z + 0.62 * math.sin(a)), 'sun_ray',
                 (0, -a + math.pi / 2, 0)))
p.append(cyl(0.55, 0.06, tuple(SC), 'sun', 24, (math.pi / 2, 0, 0)))
for s in (-1, 1):   # ko'zlar
    p.append(ball(0.07, (SC.x + s * 0.18, SC.y - 0.05, SC.z + 0.12), 'dark', 1, (1, 0.4, 1.3)))
for k in range(7):  # tabassum
    a = math.radians(200 + k * 140 / 6)
    p.append(ball(0.035, (SC.x + 0.25 * math.cos(a), SC.y - 0.05, SC.z - 0.05 + 0.25 * math.sin(a)), 'l_red'))
p.append(ball(0.08, (SC.x, SC.y - 0.06, SC.z - 0.02), 'sun_ray', 1, (1, 0.5, 1)))
p.append(box((BX1 - BX0 + 0.06, 0.1, 0.06), ((BX0 + BX1) / 2, BY, BZ1), 'steel'))

# ---------- zina (+X tomonda): pog'onalar, ikki tomonda panjara ----------
SX0, SX1 = X_R + 0.15, 3.05
SY0, SY1 = 0.6, Y_TOP0 + 0.1
n_steps = 46
for k in range(n_steps):
    t = (k + 1) / n_steps
    y = SY0 + (SY1 - SY0) * t
    z = Z_TOP * t
    p.append(box((SX1 - SX0, (SY1 - SY0) / n_steps + 0.02, 0.05), ((SX0 + SX1) / 2, y, z - 0.025), 'grate'))
for x in (SX0, SX1):  # tetivalar
    p.append(beam((x, SY0, 0.0), (x, SY1, Z_TOP - 0.1), 0.06, 0.25, 'steel'))
for y in (5.0, 10.0):  # zina tayanchlari
    z = Z_TOP * (y - SY0) / (SY1 - SY0)
    for x in (SX0, SX1):
        p.append(box((0.1, 0.1, z), (x, y, z / 2), 'steel'))


def rail_line(a, b, posts, mat='steel', h=1.0, bal=0.18):
    a, b = Vector(a), Vector(b)
    p.append(beam(a + Vector((0, 0, h)), b + Vector((0, 0, h)), 0.05, 0.05, mat))
    p.append(beam(a + Vector((0, 0, 0.08)), b + Vector((0, 0, 0.08)), 0.03, 0.03, mat))
    L = (b - a).length
    n = max(1, int(L / bal))
    for k in range(n + 1):
        c = a.lerp(b, k / n)
        w = 0.05 if k % max(1, int(n / posts)) == 0 else 0.018
        p.append(box((w, w, h), (c.x, c.y, c.z + h / 2), mat))


for x in (SX0, SX1):
    rail_line((x, SY0, 0.0), (x, SY1, Z_TOP), 10)
rail_line((TX1, SY1, Z_TOP), (TX1, Y_TOP1, Z_TOP), 2)
rail_line((TX0, Y_TOP0, Z_TOP), (TX0, Y_TOP1, Z_TOP), 2)


# ---------- chiroqli "palma" ustunlar ----------
def palm(x, y, z0, h, side):
    top = Vector((x, y, z0 + h))
    p.append(cyl(0.06, h, (x, y, z0 + h / 2), 'steel', 8))
    p.append(cyl(0.1, 0.12, (x, y, z0 + h), 'steel_dark', 8))
    for sy in (-1, 1):               # ikki tomonga egilgan shoxlar (Y bo'ylab), har tomonda ikkitadan
        for kind, (spread, rise) in enumerate(((0.75, 0.55), (0.5, 0.95))):
            pts = []
            for k in range(9):
                t = k / 8
                ang = math.pi * 0.5 * (1 - t) + math.radians(-25) * t
                yy = y + sy * spread * math.sin(math.pi * 0.5 * t) * 1.2
                zz = z0 + h + rise * math.sin(math.pi * t * 0.85) - 0.25 * t * t
                pts.append(Vector((x, yy, zz)))
            for a, b in zip(pts, pts[1:]):
                p.append(limb(a, b, 0.03, 0.025, 'red', 5))
            for k in range(1, 9, 1):
                p.append(ball(0.05, pts[k] + Vector((0, 0, 0.06)), 'bulb'))
    for k in range(4):               # ustundagi chiroqlar
        p.append(ball(0.045, (x + side * 0.07, y, z0 + h - 0.3 - k * 0.3), 'bulb'))


for y in (-11.0, -5.0, 1.0, 7.0, 13.0):           # zina tomonda (zina panjarasi yonida)
    z0 = max(0.0, Z_TOP * (y - SY0) / (SY1 - SY0)) if y > SY0 else 0.0
    palm(SX1 + 0.15, y, z0, 2.6 if z0 > 0 else 3.4, 1)
for y in (-8.0, 3.5, 12.0):                        # chap devor bo'ylab (devorga mahkamlangan)
    z0 = wall_top(y, -1) - 0.3
    palm(X_L - 0.2, y, z0, 2.6, -1)
    p.append(beam((X_L - 0.2, y, z0), (X_L - 0.2, y, zc(y) - DEPTH - 0.2), 0.05, 0.05, 'steel'))

base = join('base', p)

tris = sum(len(pg.vertices) - 2 for pg in base.data.polygons)
xs = [v.co.x for v in base.data.vertices]
ys = [v.co.y for v in base.data.vertices]
top = max(v.co.z for v in base.data.vertices)
print(f'SLIDE tris={tris} x={min(xs):.2f}..{max(xs):.2f} y={min(ys):.2f}..{max(ys):.2f} top={top:.2f}')

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'SLIDE glb={OUT_GLB.stat().st_size // 1024} KB')

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 1200, 900
world = bpy.data.worlds.new('w')
world.color = (0.95, 0.96, 0.97)
scene.world = world
for fname, loc, tgt in (('preview.png', (-22.0, -26.0, 14.0), (0, 0, 3.5)),
                        ('preview_top.png', (-8.0, 7.0, 12.0), (0, 15.0, 8.5))):
    cam.location = loc
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(PREVIEW_DIR / fname)
    bpy.ops.render.render(write_still=True)
    print('SLIDE preview', scene.render.filepath)

"""
14 — Тир (otish joyi), "Wild West" uslubidagi yog'och bino. Rasm: attraction-images-park/Untitled - 31 июля 2026 г. в 11.55.04.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/14-tir/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png (va preview_close.png — old tomon yaqindan)

Tuzilish: bitta qimirlamaydigan `base` obyekti (animatsiya yo'q):
    shag'al maydoncha, yog'och supa va pandus, yog'och devorlar (vertikal taxtalar), tekis qora tom,
    old tomonda ravoqli "false front" peshtoq ("TIR" yozuvi, chiroqchalar), ayvon ustunlari tirgaklari bilan,
    shisha vitrina va eshik (ichida nishonlar, peshtaxtalar, devordagi miltiqlar), arava g'ildiraklari, fonuslar,
    o'ng tomonda temir yo'l izi.
Asl o'lcham metrda: maydoncha 8.6 × 6.8 m, balandligi ~4.5 m (ravoq tepasi). Old tomoni — Blender'da -Y.
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

GLASS_ALPHA = 0.3
PALETTE = {
    'gravel': (0.42, 0.37, 0.32), 'pebble': (0.3, 0.26, 0.22), 'wood': (0.66, 0.42, 0.2), 'wood_dark': (0.45, 0.27, 0.12),
    'seam': (0.36, 0.2, 0.08), 'deck': (0.5, 0.32, 0.17), 'roof': (0.13, 0.13, 0.14), 'sign': (0.26, 0.15, 0.08),
    'letter': (0.95, 0.88, 0.72), 'bulb': (1.0, 0.93, 0.75), 'glass': (0.75, 0.85, 0.9), 'iron': (0.12, 0.12, 0.13),
    'lamp': (1.0, 0.8, 0.4), 'red': (0.8, 0.12, 0.12), 'white': (0.96, 0.95, 0.92), 'gun': (0.18, 0.12, 0.08),
    'counter': (0.55, 0.35, 0.18), 'steel': (0.55, 0.56, 0.58), 'sleeper': (0.3, 0.2, 0.12), 'poster': (0.85, 0.75, 0.55),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.1 if name == 'glass' else 0.7
    if name == 'glass':  # shaffof vitrina — ichi ko'rinib turadi
        bsdf.inputs['Alpha'].default_value = GLASS_ALPHA
    if name in ('bulb', 'lamp'):
        bsdf.inputs['Emission Color'].default_value = (*rgb, 1)
        bsdf.inputs['Emission Strength'].default_value = 1.5
    m.diffuse_color = (*rgb, GLASS_ALPHA if name == 'glass' else 1)
    MATS[name] = m


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


def front_poly(pts, y, t, mat):
    """XZ tekislikdagi ko'pburchak (old tomondan qaraganda soat strelkasiga teskari) → Y bo'yicha qalinligi t"""
    bm = bmesh.new()
    f = [bm.verts.new((x, y - t / 2, z)) for x, z in pts]
    b = [bm.verts.new((x, y + t / 2, z)) for x, z in pts]
    bm.faces.new(f)
    bm.faces.new(b[::-1])
    n = len(pts)
    for k in range(n):
        bm.faces.new([f[(k + 1) % n], f[k], b[k], b[(k + 1) % n]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return new_obj('front', bm, mat)


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


# ====================== o'lchamlar ======================
GW, GD = 8.6, 6.8            # shag'al maydoncha
DZ = 0.3                     # supa usti
BX = 3.7                     # bino yarim eni (X)
Y_FRONT = -2.75              # ayvon old cheti (peshtoq shu yerda)
Y_GLASS = -1.2               # vitrina (bino old devori)
Y_BACK = 2.6                 # orqa devor
WALL_TOP = 3.3               # tom
BEAM_Z = 2.45                # ayvon to'sini (peshtoq pastki cheti)

p = []
# ---------- shag'al maydoncha va toshlar ----------
p.append(box((GW, GD, 0.06), (0, 0, 0.03), 'gravel'))
for i in range(70):  # yirikroq toshlar (tasodifiy emas — takrorlanadigan naqsh)
    x = -GW / 2 + 0.2 + ((i * 37) % 83) / 83 * (GW - 0.4)
    y = -GD / 2 + 0.2 + ((i * 53) % 71) / 71 * (GD - 0.4)
    if -BX - 0.1 < x < BX + 0.1 and Y_FRONT - 0.15 < y < Y_BACK + 0.1:
        continue
    p.append(ball(0.06 + 0.03 * (i % 3), (x, y, 0.06), 'pebble', 1, (1.2, 1, 0.5)))

# ---------- yog'och supa (taxtalar) va pandus ----------
p.append(box((2 * BX + 0.2, Y_BACK - Y_FRONT + 0.25, DZ - 0.06), (0, (Y_BACK + Y_FRONT) / 2 - 0.05, 0.06 + (DZ - 0.06) / 2),
             'deck'))
for k in range(22):  # supa taxtalari chiziqlari (X bo'ylab)
    y = Y_FRONT - 0.1 + k * 0.075
    if y > Y_GLASS:
        break
    p.append(box((2 * BX + 0.2, 0.012, 0.004), (0, y, DZ + 0.002), 'seam'))
RW = 2.0
p.append(box((RW, 1.2, 0.08), (-0.3, Y_FRONT - 0.7, DZ / 2 + 0.02), 'deck', (math.atan2(DZ - 0.04, 1.2), 0, 0)))
for k in range(9):
    p.append(box((0.012, 1.2, 0.004), (-0.3 - RW / 2 + 0.1 + k * 0.225, Y_FRONT - 0.7, DZ / 2 + 0.065), 'seam',
                 (math.atan2(DZ - 0.04, 1.2), 0, 0)))
p.append(box((RW + 0.1, 0.12, 0.1), (-0.3, Y_FRONT - 1.3, 0.05), 'wood_dark'))

# ---------- devorlar: yon va orqa (vertikal taxtalar) ----------
WH = WALL_TOP - DZ
for sx in (-1, 1):
    x = sx * BX
    p.append(box((0.12, Y_BACK - Y_GLASS, WH), (x, (Y_BACK + Y_GLASS) / 2, DZ + WH / 2), 'wood'))
    n = int((Y_BACK - Y_GLASS) / 0.2)
    for k in range(1, n):
        p.append(box((0.01, 0.02, WH), (x + sx * 0.062, Y_GLASS + k * 0.2, DZ + WH / 2), 'seam'))
p.append(box((2 * BX, 0.12, WH), (0, Y_BACK, DZ + WH / 2), 'wood'))
for k in range(1, int(2 * BX / 0.2)):
    p.append(box((0.02, 0.01, WH), (-BX + k * 0.2, Y_BACK + 0.062, DZ + WH / 2), 'seam'))
# o'ng devordagi taxta-yozuv va fonus
p.append(box((0.04, 0.5, 1.3), (BX + 0.08, 0.9, 1.6), 'sign'))
p.append(box((0.045, 0.4, 0.05), (BX + 0.09, 0.9, 2.0), 'letter'))
p.append(box((0.045, 0.3, 0.05), (BX + 0.09, 0.9, 1.75), 'letter'))

# ---------- tom (tekis, qora) va parapet ----------
p.append(box((2 * BX + 0.3, Y_BACK - Y_FRONT, 0.12), (0, (Y_BACK + Y_FRONT) / 2 + 0.05, WALL_TOP + 0.06), 'roof'))  # oldi peshtoq orqasida
for sx in (-1, 1):  # yon parapetlar: oldda past, orqa burchakda baland (pog'onali)
    x = sx * (BX + 0.1)
    p.append(box((0.12, Y_BACK - Y_FRONT, 0.3), (x, (Y_BACK + Y_FRONT) / 2, WALL_TOP + 0.27), 'wood'))
    p.append(box((0.12, 1.2, 0.55), (x, Y_BACK - 0.6, WALL_TOP + 0.4), 'wood'))
p.append(box((2 * BX + 0.3, 0.12, 0.45), (0, Y_BACK + 0.05, WALL_TOP + 0.34), 'wood'))

# ---------- old "false front" peshtoq: pog'onali silueti, o'rtada ravoq ----------
FX = BX + 0.15
prof = [(-FX, BEAM_Z), (FX, BEAM_Z), (FX, 3.6), (2.55, 3.6), (2.35, 3.82), (1.4, 3.82)]
for i in range(13):  # ravoq (yarim aylana), o'ngdan chapga
    t = math.pi * i / 12
    prof.append((1.4 * math.cos(t), 3.82 + 0.68 * math.sin(t)))
prof += [(-1.4, 3.82), (-2.35, 3.82), (-2.55, 3.6), (-FX, 3.6)]
# takroriy nuqtalarni olib tashlash
clean = []
for pt in prof:
    if not clean or (abs(pt[0] - clean[-1][0]) > 1e-4 or abs(pt[1] - clean[-1][1]) > 1e-4):
        clean.append(pt)
if abs(clean[0][0] - clean[-1][0]) < 1e-4 and abs(clean[0][1] - clean[-1][1]) < 1e-4:
    clean.pop()
p.append(front_poly(clean, Y_FRONT, 0.14, 'wood'))
for k in range(int(2 * FX / 0.2)):  # vertikal taxta choklari (peshtoq old yuzida)
    x = -FX + 0.1 + k * 0.2
    top = 3.6 if abs(x) > 2.45 else (3.82 if abs(x) > 1.4 else 3.82 + 0.68 * math.sqrt(max(0, 1 - (x / 1.4) ** 2)))
    p.append(box((0.012, 0.01, top - BEAM_Z - 0.04), (x, Y_FRONT - 0.075, (BEAM_Z + top) / 2), 'seam'))
p.append(box((2 * FX + 0.2, 0.22, 0.12), (0, Y_FRONT - 0.02, BEAM_Z + 0.02), 'wood_dark'))   # pastki karniz
p.append(box((2 * FX + 0.1, 0.18, 0.06), (0, Y_FRONT - 0.03, 3.62), 'wood_dark'))
# chiroqchalar: peshtoq tepa chizig'i bo'ylab va pastki karniz bo'ylab
edge = clean[2:] + [clean[0]] if False else clean[2:]
pts_top = []
for (x0, z0), (x1, z1) in zip(edge, edge[1:]):
    L = math.hypot(x1 - x0, z1 - z0)
    n = max(1, round(L / 0.28))
    for i in range(n):
        pts_top.append((x0 + (x1 - x0) * i / n, z0 + (z1 - z0) * i / n))
for x, z in pts_top:
    p.append(ball(0.05, (x, Y_FRONT - 0.1, z - 0.08), 'bulb'))
for k in range(27):
    p.append(ball(0.045, (-FX + 0.15 + k * (2 * FX - 0.3) / 26, Y_FRONT - 0.14, BEAM_Z + 0.12), 'bulb'))
for k in range(int((Y_BACK - Y_FRONT) / 0.3)):  # yon parapet ustidagi chiroqlar
    for sx in (-1, 1):
        p.append(ball(0.045, (sx * (BX + 0.1), Y_FRONT + 0.2 + k * 0.3, WALL_TOP + 0.47), 'bulb'))
# "TIR" yozuvi: to'q taxta, chiroqli ramka, och harflar (bloklar)
SZ = 3.45
p.append(box((2.3, 0.06, 0.8), (0, Y_FRONT - 0.1, SZ), 'sign'))
for k in range(5):
    p.append(box((2.3, 0.065, 0.01), (0, Y_FRONT - 0.1, SZ - 0.32 + k * 0.16), 'seam'))
for k in range(16):
    p.append(ball(0.04, (-1.2 + k * 0.16, Y_FRONT - 0.14, SZ + 0.45), 'bulb'))
    p.append(ball(0.04, (-1.2 + k * 0.16, Y_FRONT - 0.14, SZ - 0.45), 'bulb'))
for z in (SZ - 0.3, SZ - 0.1, SZ + 0.1, SZ + 0.3):
    for sx in (-1, 1):
        p.append(ball(0.04, (sx * 1.22, Y_FRONT - 0.14, z), 'bulb'))
LY, LT = Y_FRONT - 0.15, 0.06       # harflar: old yuzasi, qalinligi
LH = 0.5
# T
p.append(box((0.42, LT, 0.1), (-0.62, LY, SZ + LH / 2 - 0.05), 'letter'))
p.append(box((0.1, LT, LH), (-0.62, LY, SZ), 'letter'))
for sx in (-1, 1):  # serif
    p.append(box((0.04, LT, 0.16), (-0.62 + sx * 0.2, LY, SZ + LH / 2 - 0.08), 'letter'))
p.append(box((0.22, LT, 0.05), (-0.62, LY, SZ - LH / 2 + 0.025), 'letter'))
# I
p.append(box((0.1, LT, LH), (0.0, LY, SZ), 'letter'))
for dz in (-1, 1):
    p.append(box((0.24, LT, 0.06), (0.0, LY, SZ + dz * (LH / 2 - 0.03)), 'letter'))
# R
RXc = 0.55
p.append(box((0.1, LT, LH), (RXc - 0.13, LY, SZ), 'letter'))
p.append(box((0.24, LT, 0.06), (RXc - 0.05, LY, SZ + LH / 2 - 0.03), 'letter'))
p.append(box((0.24, LT, 0.06), (RXc - 0.05, LY, SZ + 0.0), 'letter'))
p.append(box((0.08, LT, 0.22), (RXc + 0.1, LY, SZ + 0.12), 'letter'))
p.append(box((0.08, LT, 0.3), (RXc + 0.04, LY, SZ - 0.12), 'letter', (0, -0.5, 0)))   # oyog'i: yuqori-chapdan past-o'ngga
p.append(box((0.24, LT, 0.05), (RXc - 0.13, LY, SZ - LH / 2 + 0.025), 'letter'))

# ---------- ayvon: ustunlar, tirgaklar, to'siqlar, g'ildiraklar, fonuslar ----------
POSTS = (-3.55, -1.15, 1.15, 3.55)
for x in POSTS:
    p.append(box((0.18, 0.18, BEAM_Z - DZ), (x, Y_FRONT + 0.15, DZ + (BEAM_Z - DZ) / 2), 'wood'))
    p.append(box((0.26, 0.26, 0.08), (x, Y_FRONT + 0.15, DZ + 0.04), 'wood_dark'))
    for s in (-1, 1):  # burchak tirgaklari
        if abs(x + s * 0.5) > BX + 0.1:
            continue
        p.append(beam((x, Y_FRONT + 0.15, BEAM_Z - 0.55), (x + s * 0.5, Y_FRONT + 0.15, BEAM_Z - 0.05), 0.1, 0.1, 'wood'))
    # fonus: kronshteyn, qora ramka, ichida chiroq
    fx = x + (0.0 if abs(x) > 2 else 0.0)
    p.append(box((0.04, 0.25, 0.04), (fx, Y_FRONT + 0.0, 2.05), 'iron'))
    p.append(box((0.16, 0.16, 0.26), (fx, Y_FRONT - 0.14, 1.92), 'iron'))
    p.append(box((0.12, 0.17, 0.18), (fx, Y_FRONT - 0.14, 1.92), 'lamp'))
    p.append(cyl(0.11, 0.08, (fx, Y_FRONT - 0.14, 2.09), 'iron', 4, (0, 0, math.pi / 4), 0.02))
p.append(box((0.04, 0.25, 0.04), (BX + 0.15, -0.3, 2.3), 'iron'))       # yon devordagi fonus
p.append(box((0.16, 0.16, 0.26), (BX + 0.27, -0.3, 2.17), 'iron'))
p.append(box((0.17, 0.12, 0.18), (BX + 0.27, -0.3, 2.17), 'lamp'))
for x0, x1 in ((POSTS[0], POSTS[1]), (POSTS[2], POSTS[3])):  # ustunlar orasidagi to'siq
    for z in (0.95, 1.15):
        p.append(box((x1 - x0, 0.1, 0.08), ((x0 + x1) / 2, Y_FRONT + 0.15, DZ + z - 0.2), 'wood'))
for sx in (-1, 1):  # yon to'siqlar (ayvon yonlari)
    p.append(box((0.1, Y_GLASS - Y_FRONT - 0.15, 0.08), (sx * 3.55, (Y_GLASS + Y_FRONT) / 2 + 0.08, DZ + 0.85), 'wood'))


def wagon_wheel(cx, cz, y, tilt):
    """Arava g'ildiragi (XZ tekislikda), biroz suyalgan"""
    res = []
    R = 0.52
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=0.045, major_segments=24, minor_segments=5,
                                     location=(cx, y, cz), rotation=(math.pi / 2 + tilt, 0, 0))
    t = bpy.context.active_object
    t.data.materials.append(MATS['wood'])
    res.append(t)
    res.append(cyl(0.09, 0.14, (cx, y, cz), 'wood_dark', 10, (math.pi / 2 + tilt, 0, 0)))
    for k in range(10):
        a = 2 * math.pi * k / 10
        # g'ildirak tekisligi tilt bo'yicha X atrofida burilgan
        dx, dz = math.cos(a) * R * 0.95, math.sin(a) * R * 0.95
        end = Vector((cx + dx, y - dz * math.sin(tilt), cz + dz * math.cos(tilt)))
        res.append(beam((cx, y, cz), end, 0.035, 0.035, 'wood'))
    return res


p.extend(wagon_wheel(-2.35, DZ + 0.52, Y_FRONT - 0.02, 0.12))
p.extend(wagon_wheel(2.35, DZ + 0.52, Y_FRONT - 0.02, 0.12))

# ---------- vitrina: shisha devor, eshik, ramalar ----------
GH = BEAM_Z - DZ
for x0, x1 in ((-BX, -0.95), (0.95, BX)):
    p.append(box((x1 - x0, 0.03, GH), ((x0 + x1) / 2, Y_GLASS, DZ + GH / 2), 'glass'))
for x in (-BX, -2.3, -0.95, 0.95, 2.3, BX):
    p.append(box((0.08, 0.1, GH), (x, Y_GLASS, DZ + GH / 2), 'wood_dark'))
p.append(box((2 * BX, 0.12, 0.1), (0, Y_GLASS, BEAM_Z - 0.05), 'wood_dark'))
p.append(box((2 * BX, 0.12, 0.25), (0, Y_GLASS, DZ + 0.125), 'wood'))
for sx in (-1, 1):  # ikki tabaqali shisha eshik, tutqichlar
    p.append(box((0.9, 0.03, GH - 0.15), (sx * 0.47, Y_GLASS - 0.02, DZ + (GH - 0.15) / 2), 'glass'))
    p.append(box((0.03, 0.04, 0.6), (sx * 0.08, Y_GLASS - 0.06, DZ + 1.0), 'steel'))
p.append(box((0.08, 0.1, GH), (0, Y_GLASS - 0.01, DZ + GH / 2), 'steel'))
# yon vitrina (ayvon yon tomonlari shishasi)
for sx in (-1, 1):
    p.append(box((0.03, Y_GLASS - Y_FRONT - 0.3, GH - 0.3), (sx * 3.6, (Y_GLASS + Y_FRONT) / 2 + 0.1, DZ + 0.3 + (GH - 0.3) / 2),
                 'glass'))

# ---------- ichki qism: nishonlar, peshtaxtalar, devordagi miltiqlar, javonlar ----------
p.append(box((2 * BX - 0.15, Y_BACK - Y_GLASS - 0.1, 0.02), (0, (Y_BACK + Y_GLASS) / 2, DZ + 0.01), 'wood_dark'))
for x in (-1.0, 1.0):  # qizil-oq nishonlar (orqa devorda, eshik qarshisida)
    for k, r in enumerate((0.62, 0.5, 0.38, 0.26, 0.14)):
        p.append(cyl(r, 0.02, (x, Y_BACK - 0.08 - k * 0.006, 1.55), 'red' if k % 2 == 0 else 'white', 24, (math.pi / 2, 0, 0)))
p.append(box((1.4, 0.03, 0.8), (0, Y_BACK - 0.08, 2.5), 'poster'))     # orqa devordagi rasm (sahro)
p.append(box((1.2, 0.035, 0.25), (0, Y_BACK - 0.09, 2.3), 'wood'))
for x0, x1 in ((-BX + 0.2, -1.8), (1.8, BX - 0.2)):  # peshtaxtalar (ichida miltiqlar)
    cx = (x0 + x1) / 2
    p.append(box((x1 - x0, 0.6, 0.9), (cx, 0.2, DZ + 0.45), 'counter'))
    p.append(box((x1 - x0 + 0.06, 0.66, 0.05), (cx, 0.2, DZ + 0.92), 'wood_dark'))
    for k in range(3):
        p.append(box((0.6, 0.025, 0.06), (cx - 0.3 + k * 0.3, -0.11, DZ + 0.35 + k * 0.15), 'gun', (0, 0.1, 0)))
    for k in range(4):  # peshtaxta ustidagi o'yinchoqlar/sovrinlar
        p.append(cyl(0.05, 0.18, (cx - 0.45 + k * 0.3, 0.25, DZ + 1.04), ('red', 'white', 'letter', 'steel')[k], 8))
for x0, x1 in ((-BX + 0.1, -1.7), (1.7, BX - 0.1)):  # devordagi miltiqlar (qatorlar) va javon
    for row in range(4):
        z = 1.35 + row * 0.3
        for k in range(int((x1 - x0) / 0.32)):
            p.append(box((0.26, 0.02, 0.05), (x0 + 0.2 + k * 0.32, Y_BACK - 0.08, z), 'gun', (0, 0.15, 0)))
    p.append(box((x1 - x0, 0.25, 0.04), ((x0 + x1) / 2, Y_BACK - 0.18, 1.15), 'wood_dark'))
for sx in (-1, 1):  # yon devordagi miltiqlar
    for row in range(3):
        for k in range(6):
            p.append(box((0.02, 0.28, 0.05), (sx * (BX - 0.08), -0.6 + k * 0.4, 1.4 + row * 0.3), 'gun', (0.15, 0, 0)))

# ---------- temir yo'l izi (o'ng tomonda) ----------
TX = BX + 0.55
for k in range(22):
    y = -GD / 2 + 0.2 + k * 0.3
    p.append(box((0.7, 0.12, 0.05), (TX, y, 0.085), 'sleeper'))
for dx in (-0.22, 0.22):
    p.append(box((0.04, GD - 0.3, 0.06), (TX + dx, 0, 0.14), 'steel'))

base = join('base', p)

objs = [o for o in scene.objects if o.type == 'MESH']
tris = sum(len(pg.vertices) - 2 for o in objs for pg in o.data.polygons)
top = max(v.co.z for o in objs for v in o.data.vertices)
xs = [v.co.x for o in objs for v in o.data.vertices]
ys = [v.co.y for o in objs for v in o.data.vertices]
print(f'TIR tris={tris} top={top:.2f} x={min(xs):.2f}..{max(xs):.2f} y={min(ys):.2f}..{max(ys):.2f}')

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'TIR glb={OUT_GLB.stat().st_size // 1024} KB')

# ---------- Preview ----------
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 1000, 1000
world = bpy.data.worlds.new('w')
world.color = (0.93, 0.95, 0.98)
scene.world = world
for fname, loc, tgt in (('preview.png', (-8.5, -11.5, 7.0), (0.3, 0, 1.8)),
                        ('preview_close.png', (-2.5, -7.5, 2.4), (0.2, -1.5, 2.0))):
    cam.location = loc
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(PREVIEW_DIR / fname)
    bpy.ops.render.render(write_still=True)
    print('TIR preview', scene.render.filepath)

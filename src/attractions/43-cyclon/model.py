"""
43 — Аттракцион "Cyclon" (spiral coaster, alohida vagonlar). Rasm: attraction-images-park/Cyclone_Coaster.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/43-cyclon/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, track.json, preview.png (va preview_station.png)

Tuzilish (xarita kodi: src/map/GltfModel.tsx):
    base        — qimirlamaydigan qism: ko'k trassa (ikki rels + ko'ndalang zinapoyalar), kulrang tayanch ustunlar
                  (tagida plita, yuqorida ko'ndalang to'sin; spiral ostida — yon tomonga surilgan, qo'l bilan), bekat
                  (panjarali metall supa, ko'k-qizil yo'l-yo'l soyabon, chiroqlar), kirish pandusi va chiqish zinasi
    car0..car4  — alohida vagonlar (ulanmagan): kod har birini track.json bo'ylab alohida yurgizadi
                  (anim.follow.independent) — bekatda navbat bilan to'xtab, bittadan jo'naydi
track.json  — trassa o'rta chizig'i (rels ustki sathi), glTF koordinatalarida (x, y — tepaga, z), har ~0.5 m da

Joylashuv (lokal, metr): uzun o'qi X (~38.6 m), eni Y (~14.4 m). Old tomoni (bekat, suv tomoni) — Blender'da -Y.
Model X bo'yicha aks ettirilgan (MIRROR): bekat va kirish — chap (-X) uchida, spiral — o'ng (+X) uchida.
Vagonlar bekatda +X yo'nalishda yuradi: -X uchida — kirish pandusi (vagonlar kirib keladigan tomon),
bekatning +X uchida — chiqish zinasi (vagon to'xtagan joy, yo'lovchilar tushadi) → yo'lka bo'ylab burchakka.
Trassa: bekat → ko'tarilish (7.3 m) → 1.5 aylanali spiral (pastga) → to'lqinli orqa yo'l → burilish → bekat.
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

GLASS_ALPHA = 0.35
PALETTE = {
    'rail': (0.1, 0.45, 0.85), 'steel': (0.55, 0.57, 0.6), 'steel_dark': (0.35, 0.36, 0.38), 'grate': (0.62, 0.63, 0.65),
    'concrete': (0.7, 0.7, 0.7), 'roof_blue': (0.18, 0.4, 0.75), 'roof_red': (0.88, 0.2, 0.2), 'glass': (0.8, 0.88, 0.92),
    'bulb': (1.0, 0.93, 0.7), 'purple': (0.5, 0.2, 0.7), 'yellow': (0.98, 0.78, 0.08), 'seat': (0.1, 0.1, 0.11),
    'chassis': (0.15, 0.15, 0.17), 'green': (0.3, 0.75, 0.2), 'orange': (0.98, 0.5, 0.1), 'white': (0.96, 0.96, 0.96),
    'sign': (0.15, 0.6, 0.25),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.1 if name == 'glass' else 0.45
    if name in ('steel', 'steel_dark', 'grate'):
        bsdf.inputs['Metallic'].default_value = 0.3  # xaritada atrof-muhit aksi yo'q — yuqori metallik qoraygan ko'rinadi
    if name == 'glass':
        bsdf.inputs['Alpha'].default_value = GLASS_ALPHA
    if name == 'bulb':
        bsdf.inputs['Emission Color'].default_value = (*rgb, 1)
        bsdf.inputs['Emission Strength'].default_value = 1.2
    m.diffuse_color = (*rgb, GLASS_ALPHA if name == 'glass' else 1)
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


def limb(a, b, r1, r2, mat, segs=8):
    a, b = Vector(a), Vector(b)
    d = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r1, radius2=r2, depth=d.length)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix())
    bmesh.ops.translate(bm, vec=(a + b) / 2, verts=bm.verts)
    return new_obj('limb', bm, mat)


def join(name, objs, smooth=True):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if smooth:
        ob.data.shade_smooth()
        ob.data.set_sharp_from_angle(angle=math.radians(50))
    return ob


# ====================== trassa ======================
STATION_Z = 1.1          # bekatdagi rels sathi
PLAT_Z = 1.0             # bekat supasi
TRACK_Y = -4.5           # bekat yo'li (old tomon)
HX, HY, HR = -12.5, 1.0, 4.8          # spiral markazi va radiusi
H_TOP, H_BOT, H_TURNS = 7.3, 3.0, 1.5
TX, TR = 14.5, 4.6                    # +X uchidagi burilish

ctrl = [(TX, TRACK_Y, STATION_Z), (9.0, TRACK_Y, STATION_Z), (4.0, TRACK_Y, STATION_Z),
        # ko'tarilish (zanjirli)
        (1.5, TRACK_Y, 1.35), (-2.0, TRACK_Y, 3.6), (-5.5, TRACK_Y, 6.4), (-8.5, TRACK_Y + 0.25, H_TOP)]
# spiral: pastki nuqtadan (-X ga qarab) soat strelkasi bo'yicha 1.5 aylana, balandligi kamayib
n_h = int(H_TURNS * 12)
for i in range(n_h + 1):
    t = i / n_h
    th = math.radians(-90 - 360 * H_TURNS * t)
    ctrl.append((HX + HR * math.cos(th), HY + HR * math.sin(th), H_TOP + (H_BOT - H_TOP) * t))
# orqa yo'l (to'lqinlar) — spiral tepasidan +X ga
ctrl += [(-9.0, 4.95, 2.7), (-5.0, 4.8, 1.35), (-1.0, 4.8, 3.3), (3.0, 4.8, 1.4), (7.0, 4.7, 2.5), (10.5, 4.6, 1.5)]
# +X uchidagi burilish (yarim aylana) bekatga
for i in range(1, 8):
    th = math.radians(90 - 180 * i / 8)
    ctrl.append((TX + TR * math.cos(th), TR * math.sin(th) * (abs(TRACK_Y) / TR), 1.4 - 0.3 * i / 8))


def catmull_closed(pts, per_m=6):
    """Yopiq Catmull-Rom (sentripetal) — zich nuqtalar"""
    P = [Vector(p) for p in pts]
    n = len(P)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = P[(i - 1) % n], P[i], P[(i + 1) % n], P[(i + 2) % n]

        def tj(ti, a, b):
            return ti + max((b - a).length, 1e-4) ** 0.5
        t0 = 0.0
        t1 = tj(t0, p0, p1)
        t2 = tj(t1, p1, p2)
        t3 = tj(t2, p2, p3)
        steps = max(2, int((p2 - p1).length * per_m))
        for k in range(steps):
            t = t1 + (t2 - t1) * k / steps
            a1 = p0 * ((t1 - t) / (t1 - t0)) + p1 * ((t - t0) / (t1 - t0))
            a2 = p1 * ((t2 - t) / (t2 - t1)) + p2 * ((t - t1) / (t2 - t1))
            a3 = p2 * ((t3 - t) / (t3 - t2)) + p3 * ((t - t2) / (t3 - t2))
            b1 = a1 * ((t2 - t) / (t2 - t0)) + a2 * ((t - t0) / (t2 - t0))
            b2 = a2 * ((t3 - t) / (t3 - t1)) + a3 * ((t - t1) / (t3 - t1))
            out.append(b1 * ((t2 - t) / (t2 - t1)) + b2 * ((t - t1) / (t2 - t1)))
    return out


def resample(pts, step):
    """Yopiq chiziq bo'ylab teng qadamli nuqtalar"""
    seg = [(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
    total = sum((b - a).length for a, b in seg)
    n = int(total / step)
    step = total / n
    out, acc, i = [], 0.0, 0
    a, b = seg[0]
    L = (b - a).length
    for k in range(n):
        d = k * step
        while acc + L < d:
            acc += L
            i += 1
            a, b = seg[i]
            L = (b - a).length
        out.append(a.lerp(b, (d - acc) / L if L else 0))
    return out, total


dense = catmull_closed(ctrl)
path, LENGTH = resample(dense, 0.25)       # 0.25 m — geometriya uchun
N = len(path)


def frame(i):
    """i-nuqtada: yo'nalish (t), gorizontal yon (n) — rels ikki tomoni"""
    t = (path[(i + 1) % N] - path[i - 1]).normalized()
    n = t.cross(Vector((0, 0, 1)))
    if n.length < 1e-4:
        n = Vector((0, 1, 0))
    return t, n.normalized()


def tube(offset_n, dz, r, mat, segs=8):
    """Trassa bo'ylab quvur (rels): yon siljish offset_n, balandlik dz"""
    bm = bmesh.new()
    rings = []
    for i in range(N):
        t, n = frame(i)
        up = n.cross(t).normalized()
        c = path[i] + n * offset_n + Vector((0, 0, dz))
        rings.append([bm.verts.new(c + (n * math.cos(2 * math.pi * k / segs) + up * math.sin(2 * math.pi * k / segs)) * r)
                      for k in range(segs)])
    for i in range(N):
        a, b = rings[i], rings[(i + 1) % N]
        for k in range(segs):
            j = (k + 1) % segs
            bm.faces.new([a[k], a[j], b[j], b[k]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return new_obj('tube', bm, mat)


RAIL = 0.42
p = []
for s in (-1, 1):
    p.append(tube(s * RAIL, -0.06, 0.06, 'rail'))
p.append(tube(0.0, -0.32, 0.09, 'rail'))                      # pastki markaziy quvur (umurtqa)
for i in range(0, N, 3):                                      # ko'ndalang zinapoyalar (har ~0.75 m)
    t, n = frame(i)
    c = path[i] + Vector((0, 0, -0.1))
    p.append(beam(c - n * RAIL, c + n * RAIL, 0.07, 0.07, 'rail'))
    if i % 6 == 0:  # umurtqaga tirgak
        p.append(beam(c, path[i] + Vector((0, 0, -0.32)), 0.05, 0.05, 'rail'))
# ko'tarilishdagi zanjir (qora chiziq o'rtada)
for i in range(N):
    q = path[i]
    if 1.3 < q.z < H_TOP - 0.1 and q.y < TRACK_Y + 0.4 and -9 < q.x < 2:
        if i % 2 == 0:
            t, n = frame(i)
            p.append(beam(q + Vector((0, 0, -0.02)), path[(i + 2) % N] + Vector((0, 0, -0.02)), 0.06, 0.04, 'chassis'))


# ====================== tayanch ustunlar ======================
def track_below(xy, z, skip):
    """Shu vertikal chiziq ostida (yaqinida) trassaning boshqa qismi bormi"""
    for j in range(0, N, 2):
        if abs(j - skip) < 12 or abs(j - skip) > N - 12:
            continue
        q = path[j]
        if q.z < z - 0.3 and math.hypot(q.x - xy[0], q.y - xy[1]) < 1.0:
            return True
    return False


def in_station(q):
    return 3.0 < q.x < 16.0 and q.y < TRACK_Y + 0.5 and q.z < 1.5


SUP_STEP = 12            # har 3 m da
for i in range(0, N, SUP_STEP):
    q = path[i]
    if in_station(q) or q.z < 0.5:
        continue
    t, n = frame(i)
    top = q.z - 0.4
    base_xy = None
    for off in (0.0, 1.1, -1.1, 1.8, -1.8):
        xy = (q.x + n.x * off, q.y + n.y * off)
        if abs(xy[1]) > 7.1 or abs(xy[0]) > 19.3:
            continue
        if not track_below(xy, top + 0.2, i):
            base_xy = (xy, off)
            break
    if base_xy is None:
        continue
    (bx, by), off = base_xy
    r = 0.11 if q.z > 4 else 0.09
    p.append(cyl(r, top, (bx, by, top / 2), 'steel', 10))
    p.append(box((0.45, 0.45, 0.06), (bx, by, 0.03), 'steel_dark'))
    for dx, dy in ((0.15, 0.15), (-0.15, 0.15), (0.15, -0.15), (-0.15, -0.15)):
        p.append(cyl(0.025, 0.05, (bx + dx, by + dy, 0.08), 'steel_dark', 6))
    if abs(off) < 0.01:
        p.append(beam(q - n * 0.5 + Vector((0, 0, -0.42)), q + n * 0.5 + Vector((0, 0, -0.42)), 0.12, 0.1, 'steel'))
    else:  # yon tomonga surilgan ustun — trassaga qo'l
        p.append(beam((bx, by, top), (q.x, q.y, top), 0.12, 0.12, 'steel'))
        p.append(beam((bx, by, top - 0.7), ((bx + q.x) / 2, (by + q.y) / 2, top - 0.02), 0.07, 0.07, 'steel'))
    if top > 4.5:  # baland ustunlarga o'rta bog'lovchi
        p.append(box((0.3, 0.3, 0.1), (bx, by, top * 0.5), 'steel_dark'))
# spiral minorasi: to'rt burchakli ramka (rasmdagidek tik ustunlar va ko'ndalang to'sinlar)
for sx in (-1, 1):
    for sy in (-1, 1):
        x, y = HX + sx * 1.6, HY + sy * 1.6
        p.append(cyl(0.13, H_TOP + 0.3, (x, y, (H_TOP + 0.3) / 2), 'steel', 10))
        p.append(box((0.5, 0.5, 0.06), (x, y, 0.03), 'steel_dark'))
for z in (2.5, 5.0, H_TOP + 0.25):
    for (x0, y0), (x1, y1) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
        p.append(beam((HX + x0 * 1.6, HY + y0 * 1.6, z), (HX + x1 * 1.6, HY + y1 * 1.6, z), 0.12, 0.12, 'steel'))
for i in range(N):  # spiral halqalariga minoradan radial qo'llar (har ~2 m)
    q = path[i]
    d = math.hypot(q.x - HX, q.y - HY)
    if abs(d - HR) < 0.6 and q.z > H_BOT - 0.3 and i % 8 == 0:
        a = math.atan2(q.y - HY, q.x - HX)
        inner = Vector((HX + 1.6 * math.cos(a) / max(abs(math.cos(a)), abs(math.sin(a))),
                        HY + 1.6 * math.sin(a) / max(abs(math.cos(a)), abs(math.sin(a))), q.z - 0.4))
        p.append(beam(inner, Vector((q.x, q.y, q.z - 0.4)), 0.1, 0.1, 'steel'))


# ====================== bekat ======================
SX0, SX1 = 3.4, 15.6          # supa X oralig'i
PY0, PY1 = -7.1, -5.15        # supa Y oralig'i (old tomonda)
p.append(box((SX1 - SX0, PY1 - PY0, 0.1), ((SX0 + SX1) / 2, (PY0 + PY1) / 2, PLAT_Z - 0.05), 'grate'))
for k in range(int((SX1 - SX0) / 0.3)):          # panjara (tekstura o'rnida chiziqlar)
    p.append(box((0.015, PY1 - PY0, 0.004), (SX0 + 0.15 + k * 0.3, (PY0 + PY1) / 2, PLAT_Z + 0.002), 'steel_dark'))
p.append(box((SX1 - SX0, 0.06, PLAT_Z), ((SX0 + SX1) / 2, PY0 + 0.03, PLAT_Z / 2), 'steel'))   # old yuzasi (etak)
for x in (SX0 + 0.05, SX1 - 0.05):
    p.append(box((0.06, PY1 - PY0, PLAT_Z), (x, (PY0 + PY1) / 2, PLAT_Z / 2), 'steel_dark'))
# yo'l ostidagi supa (rels orasida, bekatda)
p.append(box((SX1 - SX0, 2.2, 0.08), ((SX0 + SX1) / 2, TRACK_Y + 0.1, 0.5), 'steel_dark'))
for x in range(4, 16, 2):
    p.append(box((0.2, 1.0, 0.5), (x, TRACK_Y, 0.25), 'steel_dark'))
# panjara: old chet bo'ylab (shisha panellar, metall tayoqlar), orqa tomonda (rels ortida) past to'siq
for k in range(int((SX1 - SX0) / 1.5)):
    x0 = SX0 + k * 1.5
    p.append(box((1.45, 0.02, 0.85), (x0 + 0.75, PY0 + 0.08, PLAT_Z + 0.5), 'glass'))
    p.append(box((0.05, 0.05, 1.05), (x0, PY0 + 0.08, PLAT_Z + 0.52), 'steel'))
p.append(beam((SX0, PY0 + 0.08, PLAT_Z + 1.05), (SX1, PY0 + 0.08, PLAT_Z + 1.05), 0.06, 0.06, 'steel'))
for k in range(int((SX1 - SX0) / 1.5) + 1):
    x = SX0 + k * 1.5
    p.append(box((0.05, 0.05, 1.0), (x, TRACK_Y + 0.85, 0.5 + 0.5), 'steel'))
for z in (0.7, 1.4):
    p.append(beam((SX0, TRACK_Y + 0.85, z), (SX1, TRACK_Y + 0.85, z), 0.04, 0.04, 'steel'))
# soyabon: ustunlar, ko'k panellar, qizil diagonal yo'llar, chetida chiroqlar
RZ0, RZ1 = 3.45, 3.75         # soyabon balandligi (old va orqa cheti — biroz qiya)
RY0, RY1 = -7.35, -3.3
for x in (SX0 + 0.2, (SX0 + SX1) / 2 - 2.0, (SX0 + SX1) / 2 + 2.0, SX1 - 0.2):
    p.append(box((0.12, 0.12, RZ0 - PLAT_Z), (x, PY0 + 0.25, (PLAT_Z + RZ0) / 2), 'steel'))
    p.append(box((0.12, 0.12, RZ1), (x, RY1 + 0.15, RZ1 / 2), 'steel'))
    p.append(beam((x, RY0, RZ0), (x, RY1, RZ1), 0.1, 0.14, 'steel_dark'))
ang = math.atan2(RZ1 - RZ0, RY1 - RY0)
RW = math.hypot(RY1 - RY0, RZ1 - RZ0)
RC = Vector(((SX0 + SX1) / 2, (RY0 + RY1) / 2, (RZ0 + RZ1) / 2 + 0.06))
p.append(box((SX1 - SX0 + 0.6, RW, 0.06), RC, 'roof_blue', (ang, 0, 0)))
for k in range(5):  # qizil diagonal yo'llar (ustida)
    x = SX0 + 0.8 + k * 2.6
    p.append(box((1.0, RW * 0.98, 0.02), (x, RC.y, RC.z + 0.045), 'roof_red', (ang, 0, -0.35)))
for k in range(int((SX1 - SX0) / 0.5)):
    p.append(ball(0.04, (SX0 + 0.2 + k * 0.5, RY0 + 0.05, RZ0 - 0.04), 'bulb'))
# kirish pandusi (+X uchida, yerga tushadi) va chiqish zinasi (-X uchida, old tomonga)
RX1 = 19.1
p.append(box((RX1 - SX1, PY1 - PY0, 0.08), ((SX1 + RX1) / 2, (PY0 + PY1) / 2, PLAT_Z / 2), 'grate',
             (0, math.atan2(PLAT_Z, RX1 - SX1), 0)))
for y in (PY0 + 0.05, PY1 - 0.05):
    p.append(beam((SX1, y, PLAT_Z + 1.0), (RX1, y, 1.0), 0.05, 0.05, 'steel'))
    for k in range(4):
        x = SX1 + k * (RX1 - SX1) / 3
        z = PLAT_Z * (1 - (x - SX1) / (RX1 - SX1))
        p.append(box((0.05, 0.05, 1.0), (x, y, z + 0.5), 'steel'))
p.append(box((0.9, 0.04, 0.35), (RX1 - 0.3, PY0 - 0.02, 1.4), 'sign'))                   # KIRISH
p.append(box((0.6, 0.045, 0.05), (RX1 - 0.3, PY0 - 0.03, 1.45), 'white'))
p.append(box((0.05, 0.05, 1.5), (RX1 - 0.3, PY0 - 0.02, 0.75), 'steel'))
EX0 = SX0 - 3.2                                                                           # chiqish zinasi
for k in range(6):
    x = SX0 - (k + 0.5) * (SX0 - EX0) / 6
    h = PLAT_Z * (1 - (k + 1) / 7)
    p.append(box(((SX0 - EX0) / 6, PY1 - PY0 - 0.2, 0.06), (x, (PY0 + PY1) / 2, h), 'grate'))
    p.append(box(((SX0 - EX0) / 6, 0.04, h), (x, PY0 + 0.05, h / 2), 'steel_dark'))
for y in (PY0 + 0.05, PY1 - 0.15):
    p.append(beam((SX0, y, PLAT_Z + 1.0), (EX0, y, 1.0), 0.05, 0.05, 'steel'))
    p.append(box((0.05, 0.05, 1.0), (EX0, y, 0.5), 'steel'))
p.append(box((0.9, 0.04, 0.35), (EX0 + 0.4, PY0 - 0.02, 1.4), 'sign'))                   # CHIQISH
p.append(box((0.6, 0.045, 0.05), (EX0 + 0.4, PY0 - 0.03, 1.45), 'white'))
p.append(box((0.05, 0.05, 1.5), (EX0 + 0.4, PY0 - 0.02, 0.75), 'steel'))
p.append(box((0.6, 0.6, 1.1), (SX0 + 0.6, PY0 + 0.45, PLAT_Z + 0.55), 'white'))         # operator pulti
for k, col in enumerate(('roof_red', 'green', 'yellow')):
    p.append(cyl(0.04, 0.03, (SX0 + 0.45 + k * 0.15, PY0 + 0.45, PLAT_Z + 1.11), col, 8))
base = join('base', p)

# ---------- Ko'zgu (X bo'yicha): bekat/kirish — chap (-X) uchida, spiral — o'ng (+X) uchida ----------
# Hammasi yuqorida "bekat +X da" deb yasalgan; xaritadagi joyiga mos bo'lishi uchun aks ettiramiz.
# Vagonlar aks ettirilmaydi (oldi lokal +X bo'lib qoladi) — faqat trassa nuqtalari
MIRROR = True
if MIRROR:
    bpy.ops.object.select_all(action='DESELECT')
    base.select_set(True)
    bpy.context.view_layer.objects.active = base
    base.scale.x = -1
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)  # normallarni ham to'g'rilaydi
    path = [Vector((-q.x, q.y, q.z)) for q in path]

# ---------- Yurish yo'nalishi: REVERSE — vagonlar teskari aylanadi (bekatda -X ga, spiralga pastdan kiradi) ----------
REVERSE = True
if REVERSE:
    path = path[::-1]


# ====================== vagonlar (car0..car4) ======================
def car(k, body):
    """Vagon: lokal +X — oldinga, origin — rels sathida markazda"""
    g = []
    g.append(box((1.9, 1.0, 0.22), (0, 0, 0.12), 'chassis'))
    for wx in (-0.6, 0.6):
        for wy in (-0.45, 0.45):
            g.append(cyl(0.1, 0.08, (wx, wy, -0.02), 'chassis', 10, (math.pi / 2, 0, 0)))
    g.append(box((1.85, 1.3, 0.42), (0, 0, 0.42), body))                                   # korpus
    for sy in (-1, 1):
        g.append(box((1.6, 0.1, 0.32), (-0.05, sy * 0.62, 0.78), body))                   # yon devorlar
        g.append(ball(0.13, (0.25, sy * 0.66, 0.45), 'green', 1, (1, 0.3, 1)))           # yon bezaklar
        g.append(ball(0.09, (-0.45, sy * 0.66, 0.5), 'orange', 1, (1, 0.3, 1)))
        g.append(box((0.5, 0.03, 0.06), (-0.2, sy * 0.67, 0.68), 'yellow' if body == 'purple' else 'purple'))
    # old "burun": yumaloq, ko'zlar (yashil doiralar), bamper
    g.append(cyl(0.55, 1.28, (0.92, 0, 0.5), body, 16, (math.pi / 2, 0, 0)))
    g.append(box((0.5, 1.28, 0.5), (0.72, 0, 0.6), body))
    for sy in (-1, 1):
        g.append(ball(0.14, (1.42, sy * 0.32, 0.6), 'green', 1, (0.4, 1, 1)))
        g.append(ball(0.07, (1.47, sy * 0.32, 0.62), 'white', 1, (0.4, 1, 1)))
    g.append(box((0.08, 0.4, 0.08), (1.47, 0, 0.35), 'yellow'))
    g.append(box((0.12, 1.32, 0.12), (-0.98, 0, 0.32), 'chassis'))                       # orqa bamper
    # ikki qator, har birida ikki o'rindiq (qora, baland suyanchiq), tutqich-bar
    for row, x in enumerate((0.25, -0.55)):
        for sy in (-0.3, 0.3):
            g.append(box((0.4, 0.48, 0.1), (x, sy, 0.68), 'seat'))
            g.append(box((0.1, 0.48, 0.55), (x - 0.22, sy, 0.92), 'seat', (0, -0.12, 0)))
            g.append(ball(0.12, (x - 0.24, sy, 1.18), 'seat', 1, (0.6, 1.6, 0.8)))         # bosh suyanchig'i
        g.append(limb((x + 0.22, -0.5, 0.95), (x + 0.22, 0.5, 0.95), 0.025, 0.025, 'steel', 6))
        for sy in (-0.5, 0.5):
            g.append(limb((x + 0.22, sy, 0.95), (x + 0.05, sy, 0.7), 0.02, 0.02, 'steel', 6))
    return join(f'car{k}', g)


BODIES = ['purple', 'yellow', 'purple', 'yellow', 'purple']
CARS = [car(k, b) for k, b in enumerate(BODIES)]
GAP = 2.8                                  # vagonlar orasidagi eng kichik masofa (o'rtadan o'rtaga), m
# bekat: birinchi vagon to'xtaydigan joy (trassa boshidan, m) — supaning vagonlar jo'naydigan uchida
_stop_x = (-3.4 - 0.85) if (MIRROR and not REVERSE) else (-15.6 + 1.1) if MIRROR else (3.4 + 0.85)
_cand = [i for i, q in enumerate(path) if abs(q.y - TRACK_Y) < 0.3 and q.z < STATION_Z + 0.1]
STATION_S = round(min(_cand, key=lambda i: abs(path[i].x - _stop_x)) * LENGTH / N, 2)
OFFSETS = [k * GAP for k in range(len(CARS))]


def at_s(s):
    s %= LENGTH
    i = int(s / (LENGTH / N))
    return path[i % N], path[(i + 1) % N]


for ob, off in zip(CARS, OFFSETS):        # Blender'da ko'rinishi uchun bekatga qo'yamiz (xaritada kod joylaydi)
    a, b = at_s(STATION_S - off)
    d = (b - a).normalized()
    ob.location = a
    ob.rotation_euler = (0, -math.asin(max(-1, min(1, d.z))), math.atan2(d.y, d.x))

# ====================== track.json (glTF: x, z, -y) ======================
track = [[round(q.x, 3), round(q.z, 3), round(-q.y, 3)] for q in path[::2]]
OUT_TRACK.write_text(json.dumps({
    'closed': True,
    'points': track,
    'cars': [{'name': ob.name, 'offset': off} for ob, off in zip(CARS, OFFSETS)],
    # bekat: birinchi vagon shu masofada (trassa boshidan, m) to'xtaydi — supaning chiqish zinasi tomonida
    'station': STATION_S,
}, separators=(',', ':')))

objs = [o for o in scene.objects if o.type == 'MESH']
tris = sum(len(pg.vertices) - 2 for o in objs for pg in o.data.polygons)
bpy.context.view_layer.update()
allv = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
print(f'CYCLON tris={tris} track={LENGTH:.1f}m points={len(track)} x={min(v.x for v in allv):.2f}..{max(v.x for v in allv):.2f} '
      f'y={min(v.y for v in allv):.2f}..{max(v.y for v in allv):.2f} top={max(v.z for v in allv):.2f}')
st_pt, _ = at_s(STATION_S)
print(f'CYCLON station point={tuple(round(c, 2) for c in st_pt)}')

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'CYCLON glb={OUT_GLB.stat().st_size // 1024} KB')

# ---------- Preview: vagonlarni trassaga tarqatib qo'yamiz ----------
for ob, s in zip(CARS, (STATION_S, 30.0, 55.0, 80.0, 105.0)):
    a, b = at_s(s)
    d = (b - a).normalized()
    ob.location = a
    ob.rotation_euler = (0, -math.asin(max(-1, min(1, d.z))), math.atan2(d.y, d.x))
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
world.color = (0.93, 0.95, 0.98)
scene.world = world
for fname, loc, tgt in (('preview.png', (22.0, -30.0, 22.0), (0, 0, 2.5)),
                        ('preview_station.png', (19.0, -14.0, 5.0), (8.0, -5.0, 1.5))):
    cam.location = loc
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(PREVIEW_DIR / fname)
    bpy.ops.render.render(write_still=True)
    print('CYCLON preview', scene.render.filepath)

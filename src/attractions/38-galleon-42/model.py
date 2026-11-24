"""
38 — Аттракцион "Galleon 42" (tebranuvchi kema). Rasm: attraction-images-park/galeon.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/38-galleon-42/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png (va preview_ship.png — kema yaqindan)

Tuzilish (xarita kodi: src/map/GltfModel.tsx):
    base    — qimirlamaydigan qism: ikki qizil A-ramka (chiroqchali oyoqlar, tayanch plitalari), tepadagi o'q va
              yuritgich, yoysimon "GALLEON" yozuvi (harflari chiroqlardan), qizil etakli supa, panjaralar, ikki zina
    swing0  — kema oq panjarali osma qo'llari bilan: o'q atrofida tebranadi (origin — o'qda, o'q — Blender X).
              Qizil korpus (pastida to'q tasma), oltin hoshiya va illyuminatorlar, 42 o'rindiq (7 qator × 6),
              machta (savatcha, arqonlar), orqada ko'k-oltin derazali galereya va fonuslar, oldida bushprit
Joylashuv (lokal): kema uzunligi — Y (tebranish yo'nalishi), o'q — X. Zinalar -X tomonda.
Asl o'lcham metrda: ~21.6 × 9.4 m, balandligi ~15.4 m (yozuv bilan).
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
    'frame': (0.55, 0.06, 0.08), 'frame_dark': (0.38, 0.04, 0.05), 'white': (0.94, 0.94, 0.93), 'steel': (0.7, 0.71, 0.73),
    'grate': (0.6, 0.61, 0.63), 'skirt': (0.62, 0.07, 0.09), 'hull': (0.62, 0.08, 0.08), 'hull_dark': (0.15, 0.08, 0.05),
    'wood': (0.55, 0.33, 0.15), 'gold': (0.86, 0.64, 0.25), 'blue': (0.2, 0.45, 0.75), 'seat': (0.7, 0.1, 0.12),
    'glass': (0.3, 0.35, 0.4), 'bulb': (1.0, 0.95, 0.8), 'dark': (0.12, 0.12, 0.13), 'rope': (0.85, 0.82, 0.75),
    'lamp': (1.0, 0.8, 0.45),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.45
    if name in ('gold', 'steel', 'grate'):
        bsdf.inputs['Metallic'].default_value = 0.3  # xaritada atrof-muhit aksi yo'q — yuqori metallik qoraygan ko'rinadi
    if name in ('bulb', 'lamp'):
        bsdf.inputs['Emission Color'].default_value = (*rgb, 1)
        bsdf.inputs['Emission Strength'].default_value = 1.3
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


def beam(a, b, w, d, mat, roll_up='Z'):
    a, b = Vector(a), Vector(b)
    v = b - a
    ob = box((v.length, w, d), (0, 0, 0), mat)
    ob.rotation_euler = v.to_track_quat('X', roll_up).to_euler()
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
PIV_Z = 13.0             # tebranish o'qi
FX = 3.3                 # A-ramkalar X bo'yicha (o'q uchlari)
FOOT_Y = 10.3            # oyoqlar tagi Y bo'yicha
FOOT_X = 3.6
PL_X, PL_Y, PL_Z = 2.8, 6.6, 1.3     # supa yarim eni, yarim uzunligi, balandligi

# ====================== BASE ======================
p = []
# --- A-ramkalar: to'rt oyoq (qizil quti-to'sin, tashqi yuzida chiroqchalar), tayanch plitalari ---
for sx in (-1, 1):
    top = Vector((sx * FX, 0, PIV_Z))
    for sy in (-1, 1):
        foot = Vector((sx * FOOT_X, sy * FOOT_Y, 0.0))
        p.append(beam(foot + Vector((0, 0, 0.2)), top, 0.55, 0.4, 'frame'))
        p.append(box((1.0, 1.0, 0.08), (foot.x, foot.y, 0.04), 'frame_dark'))
        p.append(box((0.7, 0.7, 0.5), (foot.x, foot.y, 0.3), 'frame_dark'))
        for k in range(1, 5):  # oyoq tagidagi bo'g'inlar (flans)
            if k > 1:
                break
            c = foot.lerp(top, 0.1)
            p.append(box((0.75, 0.75, 0.12), (c.x, c.y, c.z), 'frame_dark', (sy * math.atan2(FOOT_Y, PIV_Z), 0, 0)))
        # chiroqchalar: oyoqning ichki (kema tomondagi) qirrasi bo'ylab
        d = (top - foot)
        n_in = Vector((0, -sy, 0)).cross(Vector((1, 0, 0))) * 0  # (soddalik uchun — X tomondagi yuz)
        for k in range(46):
            t = 0.08 + 0.88 * k / 45
            c = foot.lerp(top, t)
            for side in (-1, 1):
                p.append(ball(0.05, (c.x + side * 0.29, c.y + sy * 0.0, c.z), 'bulb'))
    # A-ramka ichidagi ko'ndalang bog'lovchi (pastda)
    p.append(beam((sx * FOOT_X, -FOOT_Y + 0.6, 0.35), (sx * FOOT_X, FOOT_Y - 0.6, 0.35), 0.12, 0.12, 'frame_dark'))
# --- tepadagi o'q, podshipniklar, yuritgich qutisi ---
p.append(cyl(0.32, 2 * FX + 0.6, (0, 0, PIV_Z), 'steel', 16, (0, math.pi / 2, 0)))
for sx in (-1, 1):
    p.append(box((0.6, 1.3, 1.1), (sx * FX, 0, PIV_Z + 0.1), 'frame_dark'))
    p.append(cyl(0.5, 0.25, (sx * (FX - 0.45), 0, PIV_Z), 'dark', 16, (0, math.pi / 2, 0)))
p.append(box((1.4, 1.1, 0.9), (0, 0.0, PIV_Z + 0.75), 'dark'))
p.append(box((0.9, 0.7, 0.7), (-1.6, 0, PIV_Z + 0.65), 'frame'))      # yuritgich motori

# --- "GALLEON" yozuvi: yoy bo'ylab qizil harf plitalari, harflar chiroqlardan (5×7 nuqta) ---
FONT = {
    'G': ['01110', '10001', '10000', '10111', '10001', '10001', '01110'],
    'A': ['01110', '10001', '10001', '11111', '10001', '10001', '10001'],
    'L': ['10000', '10000', '10000', '10000', '10000', '10000', '11111'],
    'E': ['11111', '10000', '10000', '11110', '10000', '10000', '11111'],
    'O': ['01110', '10001', '10001', '10001', '10001', '10001', '01110'],
    'N': ['10001', '11001', '10101', '10101', '10011', '10001', '10001'],
}
WORD = 'GALLEON'
SR, SZC = 3.4, PIV_Z + 0.4          # yoy radiusi va markazi
SXP = -0.75                          # yozuv tekisligi (X) — zinalar tomonga
DOT = 0.17
for i, ch in enumerate(WORD):
    th = math.radians(150 - i * (120 / (len(WORD) - 1)))
    y = -SR * math.cos(th)
    z = SZC + SR * math.sin(th)
    alpha = math.pi / 2 - th            # plita "yuqorisi" — yoy radiusi bo'ylab tashqariga
    rot = (alpha, 0, 0)
    p.append(box((0.12, 1.05, 1.4), (SXP + 0.05, y, z), 'frame', rot))
    p.append(box((0.13, 1.15, 0.06), (SXP + 0.05, y - 0.7 * math.sin(alpha) * -1 * 0, z), 'frame_dark', rot))
    rows = FONT[ch]
    for r, row in enumerate(rows):
        for c, bit in enumerate(row):
            if bit != '1':
                continue
            # harf tekisligidagi lokal (u — o'qish yo'nalishi = -Y, v — yuqori)
            u = (c - 2) * DOT
            v = (3 - r) * DOT
            # lokal → dunyo: u bo'ylab −Y (burilgan), v bo'ylab radial
            dy = -u * math.cos(alpha) - v * math.sin(alpha)
            dz = -u * math.sin(alpha) * -1 * 0 + v * math.cos(alpha) + u * math.sin(alpha) * 0
            # aniq: plita X atrofida alpha ga burilgan — lokal (0, uy, vz) → (0, uy cos - vz sin, uy sin + vz cos)
            ly, lz = -u, v
            wy = ly * math.cos(alpha) - lz * math.sin(alpha)
            wz = ly * math.sin(alpha) + lz * math.cos(alpha)
            p.append(ball(0.06, (SXP - 0.04, y + wy, z + wz), 'bulb'))
# yozuvni o'qqa ulovchi tirgaklar
for i in (0, 3, 6):
    th = math.radians(150 - i * 20)
    p.append(beam((SXP + 0.1, 0, PIV_Z + 0.9), (SXP + 0.1, -SR * 0.85 * math.cos(th), SZC + SR * 0.85 * math.sin(th)),
                  0.08, 0.08, 'white'))
# chap tomondagi qizil qutichalar (rasmdagidek — yuritgich bloklari)
for k in range(2):
    p.append(box((0.5, 0.55, 0.45), (SXP + 0.1, SR + 0.6 + k * 0.6, SZC + 0.9 - k * 0.25), 'frame'))

# --- supa: qizil etak, panjarali ust, panjaralar, ikki zina (-X tomonda) ---
p.append(box((2 * PL_X, 2 * PL_Y, PL_Z - 0.06), (0, 0, (PL_Z - 0.06) / 2), 'skirt'))
p.append(box((2 * PL_X + 0.1, 2 * PL_Y + 0.1, 0.06), (0, 0, PL_Z - 0.03), 'grate'))
for k in range(1, 6):  # etak panellari choklari
    p.append(box((0.03, 0.06, PL_Z - 0.1), (-PL_X - 0.01, -PL_Y + k * 2 * PL_Y / 6, (PL_Z - 0.1) / 2), 'frame_dark'))
STAIRS_Y = (-4.6, 4.6)
SW = 1.3
for sy in STAIRS_Y:   # zinalar: supadan -X tomonga tushadi
    n = 7
    run = 2.0
    for k in range(n):
        h = PL_Z * (n - k) / (n + 1)
        x = -PL_X - (k + 0.5) * run / n
        p.append(box((run / n, SW, 0.06), (x, sy, h), 'grate'))
        p.append(box((run / n, SW, h), (x, sy, h / 2), 'skirt'))
    for side in (-1, 1):
        y = sy + side * SW / 2
        p.append(beam((-PL_X, y, PL_Z + 1.0), (-PL_X - run, y, 1.0), 0.05, 0.05, 'steel'))
        p.append(beam((-PL_X, y, PL_Z + 0.5), (-PL_X - run, y, 0.5), 0.03, 0.03, 'steel'))
        p.append(box((0.05, 0.05, 1.0), (-PL_X - run, y, 0.5), 'steel'))


def rail(a, b, h=1.0):
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    p.append(beam(a + Vector((0, 0, h)), b + Vector((0, 0, h)), 0.05, 0.05, 'steel'))
    p.append(beam(a + Vector((0, 0, h * 0.5)), b + Vector((0, 0, h * 0.5)), 0.03, 0.03, 'steel'))
    n = max(1, round(L / 1.2))
    for k in range(n + 1):
        c = a.lerp(b, k / n)
        p.append(box((0.05, 0.05, h), (c.x, c.y, c.z + h / 2), 'steel'))
        if k < n:  # vertikal tayoqchalar
            for j in range(1, 6):
                d = a.lerp(b, (k + j / 6) / n)
                p.append(box((0.02, 0.02, h - 0.1), (d.x, d.y, d.z + (h - 0.1) / 2), 'steel'))


Z = PL_Z
# old (-X) panjara: zinalar oldida ochiq
segs = [(-PL_Y, STAIRS_Y[0] - SW / 2), (STAIRS_Y[0] + SW / 2, STAIRS_Y[1] - SW / 2), (STAIRS_Y[1] + SW / 2, PL_Y)]
for y0, y1 in segs:
    rail((-PL_X, y0, Z), (-PL_X, y1, Z))
rail((PL_X, -PL_Y, Z), (PL_X, PL_Y, Z))
rail((-PL_X, -PL_Y, Z), (PL_X, -PL_Y, Z))
rail((-PL_X, PL_Y, Z), (PL_X, PL_Y, Z))
# kema ostidagi ichki to'siq (yo'lovchilar kema yo'lagiga kirmasin)
rail((-1.95, -PL_Y + 0.4, Z), (-1.95, PL_Y - 0.4, Z), 0.9)
rail((1.95, -PL_Y + 0.4, Z), (1.95, PL_Y - 0.4, Z), 0.9)
base = join('base', p)

# ====================== SWING0: kema va osma qo'llar ======================
L, HW = 11.0, 1.55       # kema uzunligi (Y), yarim eni
KZ = 2.25                # tinch holatda kil (eng past nuqta) balandligi
TZ = 3.55                # o'rtada bort tepasi
NSEC, NPH = 28, 10


def sec(t):
    """t ∈ [-1, 1] (−1 — burun, +1 — quyruq): yarim en, kil va bort tepasi"""
    hw = HW * max(0.12, (1 - abs(t) ** 2.6)) ** 0.55
    zb = KZ + 0.75 * t * t
    zt = TZ + 0.55 * t ** 4 + (0.45 * max(0.0, t - 0.55) / 0.45 if t > 0.55 else 0.0)
    return hw, zb, zt


def hull_points(t, inset=0.0, ph0=0.0, ph1=math.pi):
    hw, zb, zt = sec(t)
    hw = max(0.05, hw - inset)
    zb = zb + inset
    pts = []
    for k in range(NPH + 1):
        ph = ph0 + (ph1 - ph0) * k / NPH
        x = -hw * math.cos(ph)
        z = zt - (zt - zb) * math.sin(ph) ** 0.75
        pts.append(Vector((x, t * L / 2, z)))
    return pts


def hull_surface(mat, inset=0.0, ph0=0.0, ph1=math.pi, inward=False, zcut=None):
    """Korpus yuzasi: kesimlar (U-shakl) Y bo'ylab. inward — normallar ichkariga (ichki devor)"""
    bm = bmesh.new()
    rings = []
    for i in range(NSEC + 1):
        t = -1 + 2 * i / NSEC
        pts = hull_points(t, inset, ph0, ph1)
        if zcut is not None:
            pts = [Vector((q.x, q.y, min(q.z, zcut(t)))) for q in pts]
        rings.append([bm.verts.new(q) for q in pts])
    for i in range(NSEC):
        a, b = rings[i], rings[i + 1]
        for k in range(len(a) - 1):
            if inward:
                bm.faces.new([a[k], a[k + 1], b[k + 1], b[k]])
            else:
                bm.faces.new([a[k], b[k], b[k + 1], a[k + 1]])
    if not inward:  # burun va quyruq qopqoqlari
        for ring, rev in ((rings[0], True), (rings[-1], False)):
            vs = ring if not rev else ring[::-1]
            try:
                bm.faces.new(vs)
            except ValueError:
                pass
    return new_obj('hull', bm, mat)


s = []
PH_BAND = 1.05           # yuqori (qizil) va pastki (to'q) qism chegarasi (burchak)
s.append(hull_surface('hull', 0.0, 0.0, PH_BAND))
s.append(hull_surface('hull_dark', 0.0, PH_BAND, math.pi - PH_BAND))
s.append(hull_surface('hull', 0.0, math.pi - PH_BAND, math.pi))
s.append(hull_surface('wood', 0.08, 0.0, math.pi, inward=True))    # ichki devor va tag (yog'och)
# bort tepasi bo'ylab oltin hoshiya (ikki tomonda) va tasmalar
for side in (0, NPH):
    tops = [hull_points(-1 + 2 * i / NSEC)[side] for i in range(NSEC + 1)]
    for a, b in zip(tops, tops[1:]):
        s.append(limb(a + Vector((0, 0, 0.04)), b + Vector((0, 0, 0.04)), 0.07, 0.07, 'gold', 6))
    band = [hull_points(-1 + 2 * i / NSEC)[2 if side == 0 else NPH - 2] for i in range(NSEC + 1)]
    for a, b in zip(band, band[1:]):
        s.append(limb(a, b, 0.035, 0.035, 'gold', 5))
# illyuminatorlar va oltin bezak plitalari (ikki yon tomonda)
for i in range(1, 12):
    t = -0.82 + 1.5 * i / 11
    for side in (-1, 1):
        hw, zb, zt = sec(t)
        z = zt - 0.55
        x = side * (hw * 0.93 + 0.03)
        y = t * L / 2
        s.append(cyl(0.16, 0.06, (x, y, z), 'gold', 12, (0, math.pi / 2, 0)))
        s.append(cyl(0.1, 0.07, (x + side * 0.005, y, z), 'glass', 10, (0, math.pi / 2, 0)))
        s.append(box((0.04, 0.12, 0.42), (x, y + 0.42, z - 0.05), 'gold'))
# o'rindiqlar: 7 qator × 6 (qizil yumshoq o'rindiq, oltin suyanchiq)
for r in range(7):
    y = -3.4 + r * 1.05
    t = y / (L / 2)
    hw, zb, zt = sec(t)
    seat_z = zb + 0.55
    s.append(box((2 * hw - 0.35, 0.45, 0.12), (0, y, seat_z), 'seat'))
    s.append(box((2 * hw - 0.35, 0.08, 0.5), (0, y + 0.25, seat_z + 0.25), 'gold'))
    s.append(box((2 * hw - 0.35, 0.06, 0.3), (0, y + 0.22, seat_z + 0.2), 'seat'))
    for k in range(1, 3):  # o'rindiqlar orasidagi tirsakliklar
        s.append(box((0.05, 0.4, 0.18), (-hw + 0.17 + k * (2 * hw - 0.35) / 3, y, seat_z + 0.12), 'gold'))
    s.append(limb((-hw + 0.2, y - 0.3, seat_z + 0.45), (hw - 0.2, y - 0.3, seat_z + 0.45), 0.025, 0.025, 'steel', 6))
# quyruq galereyasi (+Y): ko'k-oltin derazali "kayuta", fonuslar
yq0, yq1 = 3.9, 5.25
hw_q, zb_q, zt_q = sec(0.85)
s.append(box((2 * hw_q + 0.25, yq1 - yq0, 1.0), (0, (yq0 + yq1) / 2, zt_q + 0.25), 'wood'))
s.append(box((2 * hw_q + 0.3, yq1 - yq0 + 0.05, 0.45), (0, (yq0 + yq1) / 2, zt_q + 0.3), 'blue'))
for k in range(4):
    for side in (-1, 1):
        s.append(box((0.04, 0.24, 0.3), (side * (hw_q + 0.16), yq0 + 0.25 + k * 0.3, zt_q + 0.3), 'gold'))
for k in range(3):
    s.append(box((0.35, 0.04, 0.32), (-0.45 + k * 0.45, yq1 + 0.03, zt_q + 0.3), 'gold'))
    s.append(box((0.27, 0.05, 0.24), (-0.45 + k * 0.45, yq1 + 0.035, zt_q + 0.3), 'glass'))
s.append(box((2 * hw_q + 0.4, yq1 - yq0 + 0.2, 0.08), (0, (yq0 + yq1) / 2, zt_q + 0.8), 'gold'))
s.append(box((2 * hw_q + 0.3, yq1 - yq0 + 0.1, 0.2), (0, (yq0 + yq1) / 2, zt_q - 0.15), 'blue'))
for side in (-1, 1):  # fonuslar
    s.append(cyl(0.03, 0.7, (side * (hw_q - 0.05), yq1 - 0.1, zt_q + 1.15), 'gold', 6))
    s.append(cyl(0.12, 0.28, (side * (hw_q - 0.05), yq1 - 0.1, zt_q + 1.6), 'lamp', 6))
    s.append(cyl(0.15, 0.12, (side * (hw_q - 0.05), yq1 - 0.1, zt_q + 1.8), 'blue', 6, r2=0.02))
# burun (−Y): bushprit, oltin haykalcha
hw_b, zb_b, zt_b = sec(-0.96)
s.append(limb((0, -L / 2 + 0.2, zt_b - 0.2), (0, -L / 2 - 1.3, zt_b + 0.55), 0.07, 0.04, 'wood', 8))
s.append(ball(0.18, (0, -L / 2 - 0.05, zt_b - 0.3), 'gold', 1, (0.7, 1.2, 1.0)))
s.append(box((0.6, 0.12, 0.35), (0, -L / 2 + 0.3, zt_b - 0.05), 'gold'))
# machta: savatcha, arqonlar (qayiq bortiga), arqon-narvon
MY = -0.55
MZ0, MZ1 = KZ + 0.4, PIV_Z - 3.2
s.append(cyl(0.1, MZ1 - MZ0, (0, MY, (MZ0 + MZ1) / 2), 'wood', 10, r2=0.07))
s.append(cyl(0.32, 0.35, (0, MY, MZ1 - 1.4), 'blue', 10))
s.append(cyl(0.34, 0.05, (0, MY, MZ1 - 1.2), 'gold', 10))
s.append(cyl(0.35, 0.05, (0, MY, MZ1 - 1.58), 'gold', 10))
s.append(beam((-0.9, MY, MZ1 - 2.6), (0.9, MY, MZ1 - 2.6), 0.06, 0.06, 'wood'))
for side in (-1, 1):
    for dy in (-1.5, -0.5, 0.6):
        hw, zb, zt = sec((MY + dy) / (L / 2))
        s.append(limb((side * (hw - 0.05), MY + dy, zt), (0, MY, MZ1 - 1.4), 0.012, 0.012, 'rope', 4))
# osma qo'llar: o'qdan kema bortiga — oq panjarali V (ikki tomonda), kema ostidan ko'ndalang
ARM_Y = 2.3
for side in (-1, 1):
    x = side * 1.15
    for sy in (-1, 1):
        hw, zb, zt = sec(sy * ARM_Y / (L / 2))
        a = Vector((x * 0.6, 0, PIV_Z))
        b = Vector((side * (hw + 0.05), sy * ARM_Y, zt - 0.2))
        for off in (-0.12, 0.12):  # ikki chord
            s.append(beam(a + Vector((off * 0, off, 0)), b + Vector((0, off, 0)), 0.1, 0.1, 'white'))
        n = 12
        for k in range(1, n):  # zinapoya-bog'lovchilar
            c = a.lerp(b, k / n)
            s.append(beam(c + Vector((0, -0.12, 0)), c + Vector((0, 0.12, 0)), 0.05, 0.05, 'white'))
    s.append(cyl(0.38, 0.35, (x * 0.6, 0, PIV_Z), 'white', 14, (0, math.pi / 2, 0)))
s.append(beam((-1.0, 0, PIV_Z), (1.0, 0, PIV_Z), 0.3, 0.3, 'white'))
s.append(beam((-HW - 0.05, -ARM_Y, sec(-ARM_Y / (L / 2))[2] - 0.2), (HW + 0.05, -ARM_Y, sec(-ARM_Y / (L / 2))[2] - 0.2), 0.08, 0.08,
              'white'))
s.append(beam((-HW - 0.05, ARM_Y, sec(ARM_Y / (L / 2))[2] - 0.2), (HW + 0.05, ARM_Y, sec(ARM_Y / (L / 2))[2] - 0.2), 0.08, 0.08,
              'white'))
swing = join('swing0', s)
bpy.ops.object.select_all(action='DESELECT')
swing.select_set(True)
bpy.context.view_layer.objects.active = swing
scene.cursor.location = (0, 0, PIV_Z)
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

objs = [o for o in scene.objects if o.type == 'MESH']
tris = sum(len(pg.vertices) - 2 for o in objs for pg in o.data.polygons)
bpy.context.view_layer.update()
allv = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
print(f'GALLEON tris={tris} x={min(v.x for v in allv):.2f}..{max(v.x for v in allv):.2f} '
      f'y={min(v.y for v in allv):.2f}..{max(v.y for v in allv):.2f} top={max(v.z for v in allv):.2f}')

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'GALLEON glb={OUT_GLB.stat().st_size // 1024} KB')

# ---------- Preview (kema biroz og'gan) ----------
swing.rotation_euler = (math.radians(-28), 0, 0)
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
world.color = (0.95, 0.96, 0.97)
scene.world = world
for fname, loc, tgt in (('preview.png', (-26.0, -14.0, 11.0), (0, 0, 7.0)),
                        ('preview_ship.png', (-9.0, -6.0, 8.5), (0, 1.0, 4.5))):
    cam.location = loc
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(PREVIEW_DIR / fname)
    bpy.ops.render.render(write_still=True)
    print('GALLEON preview', scene.render.filepath)

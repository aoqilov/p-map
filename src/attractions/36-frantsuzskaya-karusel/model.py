"""
36 — Аттракцион "Французская карусель" (Central carousel) — park ramzi. Rasm: attraction-images-park/Central_Carousel.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/36-frantsuzskaya-karusel/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png (va preview_close.png — yaqin ko'rinish)

Tuzilish (xarita kodi: src/map/GltfModel.tsx):
    base          — qimirlamaydigan qism: beton halqa, oltin panjara, yog'och zinapoya (old tomonda, -Y),
                    aylanuvchi supa ostidagi to'q etak
    rotor         — aylanadigan qism: yog'och supa (taxtali), mis ustunlar, 12 qirrali markaziy baraban (ravoqli rasmli
                    oynalar, chiroqli pilyastrlar), soyabon (rasmli oval panellar oltin ramkada chiroqlar bilan,
                    chig'anoqli tojlar, ko'k tishli valans), havorang-oq yo'l-yo'l tom, gumbazcha va shpil, ikki karet
    lift0..2      — otlar va jirafa (rotor bolalari), uch guruh: navbat bilan ko'tarilib-tushadi (anim.lift, stagger).
                    Har bir ot alohida obyekt emas — telefonda draw call kam bo'lsin
Aylanish — soat strelkasiga teskari (ustdan), otlar shu yo'nalishga qaragan.
Asl o'lcham metrda: panjara diametri ~14.9 m, balandligi ~7.7 m (shpil bilan). Old tomoni (zinapoya) — Blender'da -Y.
"""
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

HERE = Path(__file__).resolve().parent
OUT_GLB = HERE / 'model.glb'
OUT_BLEND = HERE / 'model.blend'
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PREVIEW_DIR = Path(argv[0]) if argv else HERE

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

PALETTE = {
    # konstruksiya
    'concrete': (0.78, 0.79, 0.8), 'skirt': (0.25, 0.18, 0.12), 'wood': (0.42, 0.24, 0.12), 'plank': (0.3, 0.16, 0.08),
    'stair': (0.48, 0.3, 0.16), 'gold': (0.86, 0.66, 0.28), 'brass': (0.82, 0.66, 0.36),
    'cream': (0.96, 0.92, 0.78), 'ivory': (0.99, 0.97, 0.9), 'pink': (0.86, 0.62, 0.66),
    'sky_blue': (0.6, 0.75, 0.9), 'roof_white': (0.97, 0.96, 0.93), 'valance': (0.42, 0.58, 0.8),
    'underside': (0.55, 0.68, 0.85),
    # rasmlar
    'paint_sky': (0.62, 0.78, 0.92), 'paint_sea': (0.38, 0.55, 0.75), 'paint_cloud': (0.95, 0.96, 0.98),
    'window': (0.45, 0.62, 0.85), 'bulb': (1.0, 0.92, 0.6),
    # otlar
    'h_white': (0.96, 0.94, 0.9), 'h_brown': (0.5, 0.3, 0.16), 'h_gray': (0.62, 0.63, 0.66), 'h_dark': (0.2, 0.14, 0.1),
    'hoof': (0.15, 0.13, 0.12), 'sad_blue': (0.45, 0.62, 0.85), 'sad_red': (0.62, 0.08, 0.1), 'velvet': (0.55, 0.05, 0.08),
    'giraffe': (0.85, 0.6, 0.3), 'spot': (0.45, 0.25, 0.1), 'eye': (0.05, 0.05, 0.05),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.35 if name.startswith('h_') else 0.5
    if name in ('gold', 'brass'):
        bsdf.inputs['Metallic'].default_value = 0.35  # xaritada atrof-muhit aksi yo'q — yuqori metallik qoraygan ko'rinadi
    if name == 'bulb':
        bsdf.inputs['Emission Color'].default_value = (1.0, 0.9, 0.6, 1)
        bsdf.inputs['Emission Strength'].default_value = 1.5
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


def limb(a, b, r1, r2, mat, segs=8):
    """a → b konus/silindr (a da r1, b da r2)"""
    a, b = Vector(a), Vector(b)
    d = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r1, radius2=r2, depth=d.length)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=q.to_matrix())
    bmesh.ops.translate(bm, vec=(a + b) / 2, verts=bm.verts)
    return new_obj('limb', bm, mat)


def lathe(profile, mat, segs=48, cap_bottom=False, cap_top=False, mats=None):
    """Aylanish yuzasi: profile [(r, z), ...]. Yuza normali: profil yuqoriga yursa — tashqariga, ichkariga yursa — tepaga.
    mats=(m0, m1) — sektorlar navbatma-navbat ikki rangda (tom yo'llari): ikki obyekt qaytadi"""
    def build(parity):
        bm = bmesh.new()
        rings = [[bm.verts.new((r * math.cos(2 * math.pi * i / segs), r * math.sin(2 * math.pi * i / segs), z))
                  for i in range(segs)] for r, z in profile]
        for a, b in zip(rings, rings[1:]):
            for i in range(segs):
                if parity is not None and i % 2 != parity:
                    continue
                j = (i + 1) % segs
                bm.faces.new([a[i], a[j], b[j], b[i]])
        if cap_bottom:
            bm.faces.new(rings[0][::-1])
        if cap_top:
            bm.faces.new(rings[-1])
        loose = [v for v in bm.verts if not v.link_faces]
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
        return bm
    if mats:
        return [new_obj('lathe', build(0), mats[0]), new_obj('lathe', build(1), mats[1])]
    return new_obj('lathe', build(None), mat)


def wall_pt(a, r, u, v, off=0.0, curved=True):
    """Devordagi nuqta: a — burchak, r — radius (silindr) yoki apofema (tekis yuz), u — gorizontal (soat strelkasiga
    teskari tomonga), v — balandlik, off — devordan tashqariga"""
    if curved:
        ang = a + u / r
        return Vector((math.cos(ang) * (r + off), math.sin(ang) * (r + off), v))
    n = Vector((math.cos(a), math.sin(a), 0))
    t = Vector((-math.sin(a), math.cos(a), 0))
    return n * (r + off) + t * u + Vector((0, 0, v))


def wall_poly(a, r, pts, mat, off=0.0, curved=True, double=False):
    """Devorga yopishgan ko'pburchak: pts — [(u, v), ...] tashqaridan qaraganda soat strelkasiga teskari tartibda"""
    bm = bmesh.new()
    vs = [bm.verts.new(wall_pt(a, r, u, v, off, curved)) for u, v in pts]
    bm.faces.new(vs)
    if double:
        vb = [bm.verts.new(wall_pt(a, r, u, v, off - 0.006, curved)) for u, v in pts]
        bm.faces.new(vb[::-1])
    return new_obj('wall', bm, mat)


def ellipse(w, h, n=20, cx=0.0, cy=0.0):
    return [(cx + w / 2 * math.cos(2 * math.pi * k / n), cy + h / 2 * math.sin(2 * math.pi * k / n)) for k in range(n)]


def beam(a, b, w, d, mat):
    a, b = Vector(a), Vector(b)
    v = b - a
    ob = box((v.length, w, d), (0, 0, 0), mat)
    ob.rotation_euler = v.to_track_quat('X', 'Z').to_euler()
    ob.location = (a + b) / 2
    return ob


def place(objs, M):
    """Lokal koordinatada yasalgan obyektlarni M matritsa bilan joyiga qo'yadi"""
    for o in objs:
        o.matrix_world = M @ o.matrix_basis
    return objs


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
    # burchak bo'yicha silliqlash: otlar, ustunlar, tom yumaloq ko'rinadi, qirralar (qutilar, qopqoqlar) o'tkir qoladi;
    # glTF'da silliq qo'shni uchburchaklar verteksni bo'lishadi — fayl ancha kichik
    ob.data.shade_smooth()
    ob.data.set_sharp_from_angle(angle=math.radians(50))
    return ob


# ====================== o'lchamlar ======================
GROUND_Z = 0.1           # beton halqa usti
DECK_Z = 0.6             # aylanuvchi supa usti
R_DECK = 6.0
R_FENCE = 7.35
R_GROUND = 7.6
UNDER_Z = DECK_Z + 3.3   # soyabon osti
R_RIM = 6.4              # soyabon gardishi (frizi)
RIM_BOT, RIM_TOP = UNDER_Z - 0.1, UNDER_Z + 1.0
R_DRUM = 2.05            # markaziy baraban (12 qirra, uchlari radiusi)
R_OUT, N_OUT = 4.9, 16   # tashqi qator otlar
R_IN, N_IN = 3.4, 12     # ichki qator otlar
HZ = DECK_Z + 1.15       # ot tanasi markazi balandligi (pastki holatda)


# ====================== BASE ======================
p = []
p.append(cyl(R_GROUND, GROUND_Z, (0, 0, GROUND_Z / 2), 'concrete', 64))
p.append(cyl(R_DECK - 0.08, DECK_Z - 0.12 - GROUND_Z, (0, 0, GROUND_Z + (DECK_Z - 0.12 - GROUND_Z) / 2), 'skirt', 48))

# oltin panjara: 32 bo'lak, old tomonda (-Y) bitta ochiq bo'lak — zinapoya
NS, FH = 32, 1.0
GAP = 24                 # 24-bo'lak markazi = 270° (-Y)
for k in range(NS):
    a0, a1 = 2 * math.pi * (k - 0.5) / NS, 2 * math.pi * (k + 0.5) / NS
    pa = Vector((R_FENCE * math.cos(a0), R_FENCE * math.sin(a0), GROUND_Z))
    pb = Vector((R_FENCE * math.cos(a1), R_FENCE * math.sin(a1), GROUND_Z))
    p.append(box((0.09, 0.09, FH + 0.1), (pa.x, pa.y, GROUND_Z + (FH + 0.1) / 2), 'gold', (0, 0, a0)))
    p.append(cyl(0.06, 0.06, (pa.x, pa.y, GROUND_Z + FH + 0.13), 'gold', 8))
    p.append(ball(0.05, (pa.x, pa.y, GROUND_Z + FH + 0.2), 'gold'))
    if k == GAP:
        continue
    for z in (0.08, 0.2, FH - 0.04):
        p.append(beam(pa + Vector((0, 0, z)), pb + Vector((0, 0, z)), 0.03, 0.03, 'gold'))
    for i in range(1, 12):
        q = pa.lerp(pb, i / 12)
        p.append(box((0.018, 0.018, FH - 0.1), (q.x, q.y, GROUND_Z + 0.06 + (FH - 0.1) / 2), 'gold'))
        if i % 2 == 0:  # tepa uchlari (nayza)
            p.append(cyl(0.02, 0.07, (q.x, q.y, GROUND_Z + FH + 0.01), 'gold', 4, r2=0.0))

# yog'och zinapoya: beton halqadan supaga (3 pog'ona), yonida oltin tutqichlar
SW = 1.3
for s in range(3):
    r0 = R_FENCE + 0.05 - s * 0.42
    h = GROUND_Z + (s + 1) * (DECK_Z - GROUND_Z) / 4
    p.append(box((SW, 0.42, h - 0.02), (0, -(r0 - 0.21), (h - 0.02) / 2 + 0.01), 'stair'))
    p.append(box((SW + 0.02, 0.04, 0.03), (0, -(r0 - 0.41), h), 'plank'))
for sx in (-1, 1):
    x = sx * (SW / 2 + 0.03)
    p.append(beam((x, -(R_FENCE + 0.05), GROUND_Z + 0.95), (x, -(R_DECK + 0.1), DECK_Z + 0.85), 0.04, 0.04, 'gold'))
    for y, z in ((R_FENCE + 0.05, GROUND_Z), (R_DECK + 0.1, DECK_Z - 0.1)):
        p.append(box((0.05, 0.05, 0.95), (x, -y, z + 0.47), 'gold'))
base = join('base', p)


# ====================== ROTOR ======================
q = []
# --- yog'och supa: taxtalar, chetida oltin hoshiya ---
q.append(cyl(R_DECK, 0.12, (0, 0, DECK_Z - 0.06), 'wood', 64))
for k in range(32):  # radial taxta chiziqlari
    a = 2 * math.pi * k / 32
    rm = (R_DRUM + R_DECK) / 2
    q.append(box((R_DECK - R_DRUM - 0.1, 0.02, 0.01), (rm * math.cos(a), rm * math.sin(a), DECK_Z + 0.002), 'plank',
                 (0, 0, a)))
for r in (2.7, 4.15, 5.55):  # aylana taxta chiziqlari
    q.append(lathe([(r - 0.012, DECK_Z + 0.003), (r + 0.012, DECK_Z + 0.003)][::-1], 'plank', 64))
q.append(lathe([(R_DECK, DECK_Z - 0.12), (R_DECK + 0.02, DECK_Z - 0.1), (R_DECK + 0.02, DECK_Z), (R_DECK - 0.04, DECK_Z + 0.02)],
               'gold', 64))

# --- markaziy baraban: 12 qirra, ravoqli rasmli oynalar, chiroqli pilyastrlar ---
DH = UNDER_Z - DECK_Z
q.append(cyl(R_DRUM, DH, (0, 0, DECK_Z + DH / 2), 'cream', 12))
q.append(cyl(R_DRUM + 0.1, 0.22, (0, 0, DECK_Z + 0.11), 'ivory', 12))
q.append(cyl(R_DRUM + 0.12, 0.06, (0, 0, DECK_Z + 0.25), 'gold', 12))
APO = R_DRUM * math.cos(math.pi / 12)
for k in range(12):
    a = 2 * math.pi * k / 12 + math.pi / 12   # yuz markazi
    arch = [(-0.38, 0)] + [(0.38 * math.cos(math.pi * i / 10) * -1 * -1 if False else 0.38 * math.cos(math.pi - math.pi * i / 10) * -1,
                            1.45 + 0.38 * math.sin(math.pi * i / 10)) for i in range(0)]
    # ravoq: pastki to'g'ri burchak + yarim doira (soat strelkasiga teskari tartib)
    pts = [(-0.38, 0.0), (0.38, 0.0)] + [(0.38 * math.cos(math.pi * i / 10), 1.45 + 0.38 * math.sin(math.pi * i / 10))
                                         for i in range(11)]
    z0 = DECK_Z + 0.55
    pts = [(u, v + z0) for u, v in pts]
    frame = [(u * 1.2, z0 + (v - z0) * 1.06 - 0.05) for u, v in pts]
    q.append(wall_poly(a, APO, frame, 'gold', 0.012, curved=False))
    q.append(wall_poly(a, APO, pts, 'window', 0.02, curved=False))
    # oynadagi rasm: bulut va daraxt silueti
    q.append(wall_poly(a, APO, ellipse(0.45, 0.22, 10, -0.05, z0 + 1.55), 'paint_cloud', 0.025, curved=False))
    q.append(wall_poly(a, APO, ellipse(0.3, 0.16, 10, 0.15, z0 + 1.25), 'paint_cloud', 0.025, curved=False))
    q.append(wall_poly(a, APO, [(-0.38, z0), (0.38, z0), (0.38, z0 + 0.35), (0.1, z0 + 0.5), (-0.2, z0 + 0.4),
                                (-0.38, z0 + 0.45)], 'paint_sea', 0.025, curved=False))
    # ravoq ustida oltin tugun va pastida tokcha
    c = wall_pt(a, APO, 0, z0 + 1.95, 0.05, False)
    q.append(ball(0.07, c, 'gold'))
    q.append(box((0.08, 0.95, 0.06), wall_pt(a, APO, 0, z0 - 0.08, 0.04, False), 'ivory', (0, 0, a)))
for k in range(12):  # pilyastrlar (qirralarda) va chiroqlar
    a = 2 * math.pi * k / 12
    c = Vector((math.cos(a), math.sin(a), 0)) * (R_DRUM + 0.03)
    q.append(box((0.12, 0.2, DH - 0.3), (c.x, c.y, DECK_Z + 0.25 + (DH - 0.3) / 2), 'ivory', (0, 0, a)))
    for j in range(11):
        z = DECK_Z + 0.45 + j * (DH - 0.75) / 10
        q.append(ball(0.032, (c.x * 1.045, c.y * 1.045, z), 'bulb'))
# baraban tepasidagi karniz, chiroqlar qatori va ko'k "bulut" valans
q.append(cyl(R_DRUM + 0.18, 0.28, (0, 0, UNDER_Z - 0.14), 'cream', 12))
q.append(cyl(R_DRUM + 0.2, 0.05, (0, 0, UNDER_Z - 0.3), 'gold', 12))
for k in range(36):
    a = 2 * math.pi * k / 36
    q.append(ball(0.03, ((R_DRUM + 0.22) * math.cos(a), (R_DRUM + 0.22) * math.sin(a), UNDER_Z - 0.14), 'bulb'))
for k in range(24):
    a = 2 * math.pi * k / 24
    q.append(wall_poly(a, R_DRUM + 0.19, [(-0.28, 0), (0.28, 0)] +
                       [(0.28 * math.cos(math.pi + math.pi * i / 6 * -1 + 0), 0) for i in range(0)] +
                       [(0.28 * math.cos(-math.pi * i / 6), -0.2 * math.sin(math.pi * i / 6)) for i in range(7)][::-1][1:-1][::-1],
                       'valance', 0.0, True, True))

# --- mis ustunlar: otlar ustunlari (tagida krem g'ilof) va tashqi tayanch ustunlar ---
def pole(x, y, r=0.035, sleeve=True):
    res = [cyl(r, UNDER_Z - DECK_Z, (x, y, (DECK_Z + UNDER_Z) / 2), 'brass', 8)]
    res.append(cyl(r * 2.3, 0.08, (x, y, UNDER_Z - 0.04), 'gold', 8))
    if sleeve:
        res.append(cyl(0.085, 0.38, (x, y, DECK_Z + 0.19), 'ivory', 10))
        res.append(cyl(0.1, 0.05, (x, y, DECK_Z + 0.38), 'gold', 10))
    for z in (DECK_Z + 1.9, DECK_Z + 2.6):  # buralgan mis halqalari
        res.append(cyl(r * 1.5, 0.05, (x, y, z), 'gold', 8))
    return res


SLOTS = []               # (radius, burchak, tur)
for k in range(N_OUT):
    SLOTS.append((R_OUT, 2 * math.pi * k / N_OUT, 'chariot' if k in (4, 12) else 'horse'))
for k in range(N_IN):
    SLOTS.append((R_IN, 2 * math.pi * k / N_IN + math.pi / N_IN, 'giraffe' if k == 7 else 'horse'))
for r, a, kind in SLOTS:
    if kind != 'chariot':
        q.extend(pole(r * math.cos(a), r * math.sin(a)))
for k in range(24):
    a = 2 * math.pi * (k + 0.5) / 24
    q.extend(pole(5.78 * math.cos(a), 5.78 * math.sin(a), 0.03, False))

# --- soyabon osti (ko'k), gardish (krem friz), tishli valans ---
q.append(cyl(R_RIM - 0.02, 0.06, (0, 0, UNDER_Z + 0.03), 'underside', 64))
for k in range(16):  # soyabon ostidagi radial qovurg'alar
    a = 2 * math.pi * k / 16
    q.append(beam((2.2 * math.cos(a), 2.2 * math.sin(a), UNDER_Z - 0.03), ((R_RIM - 0.1) * math.cos(a), (R_RIM - 0.1) * math.sin(a),
                                                                       UNDER_Z - 0.03), 0.08, 0.06, 'ivory'))
q.append(lathe([(R_RIM, RIM_BOT), (R_RIM, RIM_TOP)], 'cream', 96))
q.append(lathe([(R_RIM - 0.25, RIM_BOT), (R_RIM, RIM_BOT)][::-1], 'cream', 96))   # gardish osti (pastga qaragan)
for z, h in ((RIM_BOT, 0.07), (RIM_TOP - 0.04, 0.08)):   # oltin hoshiyalar (past va tepa)
    q.append(lathe([(R_RIM + 0.03, z), (R_RIM + 0.03, z + h)], 'gold', 96))
    q.append(lathe([(R_RIM, z + h), (R_RIM + 0.03, z + h)][::-1], 'gold', 96))
# tishli valans: gardish ostida yarim doira "tillar" (ko'k), orasida oltin tomchilar
NV = 72
for k in range(NV):
    a = 2 * math.pi * k / NV
    w = 2 * math.pi * R_RIM / NV / 2
    pts = [(w * math.cos(-math.pi * i / 8), RIM_BOT - 0.01 - 0.22 * math.sin(math.pi * i / 8)) for i in range(9)][::-1]
    pts = [(-w, RIM_BOT - 0.01)] + [pp for pp in pts[1:-1]] + [(w, RIM_BOT - 0.01)]
    pts = sorted(pts, key=lambda uv: uv[0])
    pts = [pts[0]] + pts[1:-1] + [pts[-1]]
    poly = [(-w, RIM_BOT)] + [(w * math.cos(math.pi - math.pi * i / 8), RIM_BOT - 0.22 * math.sin(math.pi * i / 8))
                               for i in range(9)][1:-1] + [(w, RIM_BOT)]
    q.append(wall_poly(a, R_RIM - 0.02, poly, 'valance', 0.0, True, True))
    if k % 2 == 0:
        q.append(ball(0.03, wall_pt(a + math.pi / NV, R_RIM, 0, RIM_BOT - 0.12, 0.0), 'gold'))

# rasmli oval panellar (8 ta), oltin ramka va chiroqlar
NB = 8
OW, OH = 3.1, 0.72
OZ = (RIM_BOT + RIM_TOP) / 2 - 0.02
for k in range(NB):
    a = 2 * math.pi * k / NB
    q.append(wall_poly(a, R_RIM, ellipse(OW + 0.34, OH + 0.3, 32, 0, OZ), 'ivory', 0.012))      # bo'rtma fon
    q.append(wall_poly(a, R_RIM, ellipse(OW + 0.16, OH + 0.14, 32, 0, OZ), 'gold', 0.02))       # oltin ramka
    q.append(wall_poly(a, R_RIM, ellipse(OW, OH, 32, 0, OZ), 'paint_sky', 0.03))               # osmon
    sea = [(u, v) for u, v in ellipse(OW, OH, 32, 0, OZ) if v <= OZ - 0.02]
    sea = sorted(sea, key=lambda uv: math.atan2(uv[1] - OZ, uv[0]))
    q.append(wall_poly(a, R_RIM, [(-OW / 2 * 0.97, OZ - 0.02)] + sea + [(OW / 2 * 0.97, OZ - 0.02)], 'paint_sea', 0.034))
    for cu, cv, cw in ((-0.8, 0.12, 0.6), (0.4, 0.2, 0.5), (0.95, 0.05, 0.35)):                 # bulutlar
        q.append(wall_poly(a, R_RIM, ellipse(cw, 0.14, 10, cu, OZ + cv), 'paint_cloud', 0.036))
    q.append(wall_poly(a, R_RIM, [(-0.2, OZ - 0.08), (0.25, OZ - 0.08), (0.18, OZ - 0.16), (-0.12, OZ - 0.16)],
                       'paint_cloud', 0.038))                                                    # kema korpusi
    q.append(wall_poly(a, R_RIM, [(0.0, OZ - 0.07), (0.12, OZ - 0.07), (0.0, OZ + 0.18)], 'paint_cloud', 0.038))  # yelkan
    for i in range(18):  # ramka atrofidagi chiroqlar
        t = 2 * math.pi * i / 18
        q.append(ball(0.035, wall_pt(a, R_RIM, (OW / 2 + 0.17) * math.cos(t), OZ + (OH / 2 + 0.15) * math.sin(t), 0.05),
                      'bulb'))
    for s in (-1, 1):  # ramka yonidagi jingalaklar va tepasidagi "toj"
        q.append(ball(0.09, wall_pt(a, R_RIM, s * (OW / 2 + 0.3), OZ, 0.04), 'gold', 1, (1, 1, 1.4)))
    q.append(wall_poly(a, R_RIM, [(-0.25, OZ + OH / 2 + 0.12), (0.25, OZ + OH / 2 + 0.12), (0.12, OZ + OH / 2 + 0.28),
                                  (0, OZ + OH / 2 + 0.34), (-0.12, OZ + OH / 2 + 0.28)], 'gold', 0.04))
    q.append(wall_poly(a, R_RIM, [(-0.3, OZ - OH / 2 - 0.12), (0, OZ - OH / 2 - 0.3), (0.3, OZ - OH / 2 - 0.12)][::-1][::-1],
                       'gold', 0.04))

# chig'anoqli tojlar (panellar orasida): pilyastr, pushti tomchi, tepada yelpig'ich-chig'anoq, chiroqlar
for k in range(NB):
    a = 2 * math.pi * (k + 0.5) / NB
    q.append(wall_poly(a, R_RIM, [(-0.3, RIM_BOT - 0.05), (0.3, RIM_BOT - 0.05), (0.3, RIM_TOP), (-0.3, RIM_TOP)], 'ivory',
                       0.05))
    for s in (-1, 1):
        q.append(wall_poly(a, R_RIM, [(s * 0.22 - 0.03, RIM_BOT + 0.1), (s * 0.22 + 0.03, RIM_BOT + 0.1),
                                      (s * 0.22 + 0.03, RIM_TOP - 0.15), (s * 0.22 - 0.03, RIM_TOP - 0.15)], 'gold', 0.06))
    q.append(wall_poly(a, R_RIM, ellipse(0.16, 0.5, 12, 0, RIM_BOT + 0.42), 'pink', 0.06))
    q.append(limb(wall_pt(a, R_RIM, 0, RIM_BOT - 0.05, 0.06), wall_pt(a, R_RIM, 0, RIM_BOT - 0.4, 0.06), 0.07, 0.0, 'pink', 8))
    q.append(ball(0.05, wall_pt(a, R_RIM, 0, RIM_BOT - 0.08, 0.08), 'gold'))
    # chig'anoq: tishli yelpig'ich (ikki tomonlama — tom tomondan ham ko'rinadi)
    CR = 0.78
    shell = [(-0.45, RIM_TOP - 0.02)]
    for i in range(25):
        t = math.pi * i / 24
        rr = CR * (1 + 0.07 * math.cos(9 * t))
        shell.append((-rr * math.cos(t) * 0.75 * -1 * -1 if False else rr * math.cos(math.pi - t) * 0.75,
                      RIM_TOP + 0.05 + rr * math.sin(t)))
    shell.append((0.45, RIM_TOP - 0.02))
    q.append(wall_poly(a, R_RIM, shell, 'ivory', 0.04, True, True))
    q.append(wall_poly(a, R_RIM, ellipse(0.55, 0.62, 14, 0, RIM_TOP + 0.36), 'pink', 0.06))
    for i in range(7):  # chig'anoq qovurg'alari
        t = math.pi * (i + 1) / 8
        q.append(limb(wall_pt(a, R_RIM, 0, RIM_TOP + 0.1, 0.08),
                      wall_pt(a, R_RIM, 0.55 * math.cos(math.pi - t), RIM_TOP + 0.1 + 0.65 * math.sin(t), 0.08), 0.025, 0.012,
                      'gold', 5))
    for i in range(11):
        t = math.pi * i / 10
        q.append(ball(0.04, wall_pt(a, R_RIM, 0.7 * math.cos(math.pi - t), RIM_TOP + 0.05 + 0.82 * math.sin(t), 0.07), 'bulb'))
    q.append(ball(0.08, wall_pt(a, R_RIM, 0, RIM_TOP + 0.95, 0.05), 'gold'))

# --- tom: havorang-oq yo'llar (biroz botiq chodir), tepada gumbazcha va shpil ---
ROOF = [(R_RIM - 0.02, RIM_TOP), (4.6, RIM_TOP + 0.75), (2.6, RIM_TOP + 1.3), (1.0, RIM_TOP + 1.6), (0.42, RIM_TOP + 1.68)]
q.extend(lathe(ROOF, None, 24, mats=('sky_blue', 'roof_white')))
q.append(lathe([(r - 0.002, z - 0.03) for r, z in ROOF][::-1], 'underside', 24))           # tom ichki yuzasi (pastdan)
for k in range(24):  # yo'llar orasidagi ingichka oltin chok
    a = 2 * math.pi * k / 24
    for (r0, z0), (r1, z1) in zip(ROOF, ROOF[1:]):
        q.append(beam((r0 * math.cos(a), r0 * math.sin(a), z0 + 0.01), (r1 * math.cos(a), r1 * math.sin(a), z1 + 0.01),
                      0.025, 0.012, 'gold'))
TZ = RIM_TOP + 1.68
q.append(cyl(0.45, 0.32, (0, 0, TZ + 0.16), 'ivory', 16))
for k in range(8):
    a = 2 * math.pi * k / 8
    q.append(box((0.03, 0.12, 0.2), (0.46 * math.cos(a), 0.46 * math.sin(a), TZ + 0.16), 'gold', (0, 0, a)))
q.append(cyl(0.5, 0.06, (0, 0, TZ + 0.34), 'gold', 16))
q.append(lathe([(0.42, TZ + 0.37), (0.4, TZ + 0.5), (0.3, TZ + 0.62), (0.15, TZ + 0.7), (0.0, TZ + 0.72)], 'ivory', 16))
q.append(cyl(0.06, 0.16, (0, 0, TZ + 0.78), 'gold', 8))
q.append(ball(0.09, (0, 0, TZ + 0.92), 'ivory', 2, (1, 1, 1.3)))
q.append(cyl(0.035, 0.35, (0, 0, TZ + 1.15), 'gold', 8, r2=0.0))

# --- karetlar (qizil baxmal o'rindiq, oltin jingalak yonlar) ---
def chariot():
    """Lokal: +X — oldinga (aylanish yo'nalishi), origin — supa ustida"""
    g = [box((1.35, 0.95, 0.18), (0, 0, 0.12), 'gold')]
    g.append(box((1.2, 0.85, 0.22), (0, 0, 0.32), 'velvet'))                       # tag qismi
    g.append(box((0.5, 0.75, 0.16), (-0.25, 0, 0.5), 'velvet'))                    # o'rindiq
    g.append(box((0.14, 0.85, 0.75), (-0.58, 0, 0.75), 'velvet', (0, -0.15, 0)))  # suyanchiq
    g.append(limb((-0.62, -0.42, 1.12), (-0.62, 0.42, 1.12), 0.07, 0.07, 'gold', 8))
    for s in (-1, 1):
        g.append(box((1.25, 0.06, 0.45), (0, s * 0.45, 0.5), 'velvet'))
        g.append(box((1.27, 0.07, 0.05), (0, s * 0.46, 0.73), 'gold'))
        for x in (-0.35, 0.25):  # jingalaklar
            bpy.ops.mesh.primitive_torus_add(major_radius=0.13, minor_radius=0.025, major_segments=12, minor_segments=4,
                                             location=(x, s * 0.49, 0.48), rotation=(math.pi / 2, 0, 0))
            t = bpy.context.active_object
            t.data.materials.append(MATS['gold'])
            g.append(t)
        g.append(ball(0.07, (0.62, s * 0.45, 0.75), 'gold'))
    # old tomoni: egilgan "oqqush bo'yni"
    g.append(limb((0.6, 0, 0.35), (0.85, 0, 0.75), 0.12, 0.07, 'gold', 8))
    g.append(limb((0.85, 0, 0.75), (0.72, 0, 0.98), 0.07, 0.05, 'gold', 8))
    g.append(ball(0.08, (0.7, 0, 1.0), 'gold'))
    return g


for r, a, kind in SLOTS:
    if kind == 'chariot':
        M = Matrix.Translation((r * math.cos(a), r * math.sin(a), DECK_Z)) @ Matrix.Rotation(a + math.pi / 2, 4, 'Z')
        q.extend(place(chariot(), M))
rotor = join('rotor', q)


# ====================== OTLAR (lift0..2) ======================
# poza: (old chap, old o'ng, orqa chap, orqa o'ng) — har biri (son, tizza, tuyoq) nuqtalari, y — ishora bilan
POSES = [
    # 0 — chopayotgan (old oyoqlar bukilgan oldinga, orqalari orqaga cho'zilgan)
    [((0.42, -0.15), (0.68, -0.3), (0.58, -0.56)), ((0.42, -0.15), (0.64, -0.36), (0.74, -0.6)),
     ((-0.42, -0.15), (-0.56, -0.48), (-0.82, -0.6)), ((-0.42, -0.15), (-0.62, -0.42), (-0.9, -0.5))],
    # 1 — tik turib sakrovchi (old oyoqlar baland, orqalari pastda)
    [((0.42, -0.12), (0.72, -0.1), (0.66, -0.4)), ((0.42, -0.12), (0.7, -0.18), (0.6, -0.45)),
     ((-0.42, -0.15), (-0.46, -0.55), (-0.56, -0.9)), ((-0.42, -0.15), (-0.5, -0.55), (-0.62, -0.88))],
    # 2 — qadamlayotgan (bitta old oyoq ko'tarilgan)
    [((0.42, -0.15), (0.7, -0.3), (0.62, -0.58)), ((0.42, -0.15), (0.46, -0.55), (0.5, -0.9)),
     ((-0.42, -0.15), (-0.48, -0.55), (-0.5, -0.9)), ((-0.42, -0.15), (-0.62, -0.45), (-0.78, -0.75))],
]
COATS = [  # (tana, yol/dum, egar)
    ('h_white', 'gold', 'sad_blue'), ('h_white', 'h_gray', 'sad_red'), ('h_brown', 'h_dark', 'sad_blue'),
    ('h_white', 'gold', 'sad_red'), ('h_gray', 'ivory', 'sad_blue'), ('h_white', 'h_brown', 'sad_blue'),
    ('h_brown', 'ivory', 'sad_red'),
]


def horse(pose, coat, mane, saddle, head_up=0.0):
    """Ot: lokal +X — oldinga, origin — tana markazi (ustun shu yerdan o'tadi)"""
    g = [ball(0.3, (0, 0, 0), coat, 2, (2.0, 0.85, 1.0))]
    g.append(ball(0.27, (0.38, 0, 0.06), coat, 2, (1.0, 0.9, 1.05)))
    g.append(ball(0.28, (-0.38, 0, 0.03), coat, 2, (1.0, 0.95, 1.0)))
    hn = Vector((0.72, 0, 0.6 + head_up))
    g.append(limb((0.45, 0, 0.12), hn, 0.17, 0.11, coat, 10))
    hd = hn + Vector((0.28, 0, -0.24))
    g.append(limb(hn + Vector((-0.02, 0, 0.06)), hd, 0.1, 0.066, coat, 10))
    g.append(ball(0.072, hd + Vector((0.01, 0, -0.01)), coat, 1, (1.1, 0.9, 0.9)))
    for s in (-1, 1):
        g.append(ball(0.022, hn + Vector((0.1, s * 0.075, -0.01)), 'eye'))
        g.append(limb(hn + Vector((-0.02, s * 0.045, 0.1)), hn + Vector((-0.05, s * 0.055, 0.22)), 0.032, 0.004, coat, 5))
        g.append(ball(0.012, hd + Vector((0.06, s * 0.03, -0.01)), 'eye'))           # burun teshigi
        g.append(limb(hd + Vector((-0.04, s * 0.06, 0.0)), hn + Vector((-0.04, s * 0.09, 0.12)), 0.01, 0.01, 'gold', 4))  # jilov
    for i in range(8):  # yol (to'lqinli bo'laklar)
        t = i / 7
        c = Vector((0.46, 0, 0.32)).lerp(hn + Vector((-0.06, 0, 0.12)), t)
        g.append(box((0.1, 0.07, 0.17 - t * 0.05), c + Vector((-0.06, 0, 0)), mane, (0, -0.7 + (i % 2) * 0.25, 0)))
    g.append(box((0.12, 0.06, 0.1), hn + Vector((0.04, 0, 0.12)), mane, (0, 0.6, 0)))   # peshona kokili
    g.append(limb((-0.6, 0, 0.12), (-0.82, 0, -0.12), 0.075, 0.06, mane, 8))
    g.append(limb((-0.82, 0, -0.12), (-0.88, 0, -0.48), 0.06, 0.02, mane, 8))
    for (hip, knee, hoof), s in zip(POSES[pose], (1, -1, 1, -1)):
        y = s * 0.13
        g.append(limb((hip[0], y, hip[1]), (knee[0], y, knee[1]), 0.085, 0.058, coat, 8))
        g.append(limb((knee[0], y, knee[1]), (hoof[0], y, hoof[1]), 0.052, 0.04, coat, 8))
        g.append(ball(0.058, (knee[0], y, knee[1]), coat))
        d = (Vector(hoof) - Vector(knee)).normalized() * 0.07
        g.append(limb((hoof[0], y, hoof[1]), (hoof[0] + d.x, y, hoof[1] + d.y), 0.048, 0.055, 'hoof', 8))
    # egar, yopinchiq (tilla hoshiyali), uzangi, ko'krak bezagi
    g.append(box((0.44, 0.58, 0.08), (0.02, 0, 0.3), saddle, (0, 0.05, 0)))
    g.append(box((0.06, 0.42, 0.12), (-0.19, 0, 0.37), 'gold'))
    g.append(ball(0.05, (0.22, 0, 0.36), 'gold'))
    for s in (-1, 1):
        g.append(box((0.5, 0.025, 0.32), (0.02, s * 0.27, 0.1), saddle))
        g.append(box((0.52, 0.03, 0.04), (0.02, s * 0.275, -0.06), 'gold'))
        g.append(ball(0.03, (0.02, s * 0.285, 0.1), 'gold'))
        g.append(limb((0.02, s * 0.29, 0.2), (0.04, s * 0.32, -0.28), 0.008, 0.008, 'gold', 4))
        g.append(box((0.08, 0.06, 0.02), (0.04, s * 0.32, -0.3), 'gold'))
    for i in range(7):
        t = -0.9 + 1.8 * i / 6
        g.append(ball(0.03 if i % 3 else 0.045, (0.56 + 0.06 * math.cos(t * 1.2), 0.27 * math.sin(t), 0.02 - 0.08 * math.cos(t)),
                      'gold' if i % 3 else saddle))
    return g


def giraffe():
    """Jirafa: lokal +X — oldinga, origin — tana markazi"""
    g = [ball(0.3, (0, 0, 0), 'giraffe', 2, (1.6, 0.8, 1.0))]
    nt = Vector((0.62, 0, 1.2))
    g.append(limb((0.35, 0, 0.12), nt, 0.15, 0.08, 'giraffe', 10))
    hd = nt + Vector((0.24, 0, -0.08))
    g.append(limb(nt + Vector((-0.04, 0, 0.04)), hd, 0.085, 0.055, 'giraffe', 10))
    for s in (-1, 1):
        g.append(limb(nt + Vector((-0.02, s * 0.04, 0.08)), nt + Vector((-0.04, s * 0.05, 0.2)), 0.02, 0.018, 'spot', 5))
        g.append(ball(0.03, nt + Vector((-0.04, s * 0.05, 0.21)), 'spot'))
        g.append(ball(0.02, nt + Vector((0.08, s * 0.065, 0.0)), 'eye'))
        g.append(limb(nt + Vector((-0.06, s * 0.05, 0.06)), nt + Vector((-0.12, s * 0.12, 0.08)), 0.025, 0.01, 'giraffe', 5))
    for x, z, rx in ((0.3, 0.2, 0.0), (0.42, 0.55, 0.0), (0.52, 0.85, 0.0)):     # bo'yin dog'lari
        for s in (-1, 1):
            g.append(box((0.1, 0.02, 0.08), (x, s * (0.12 - z * 0.03), z), 'spot', (0, -0.5, 0)))
    for x in (-0.3, -0.1, 0.12, 0.3):                                           # tana dog'lari
        for s in (-1, 1):
            g.append(box((0.12, 0.02, 0.1), (x, s * 0.24, 0.05 + 0.04 * (x > 0)), 'spot'))
    g.append(limb((0.32, 0, 0.3), (0.55, 0, 1.05), 0.03, 0.03, 'spot', 4))      # yol
    for (hx, s) in ((0.3, 1), (0.3, -1), (-0.3, 1), (-0.3, -1)):
        y = s * 0.13
        g.append(limb((hx, y, -0.1), (hx + 0.02, y, -0.55), 0.07, 0.05, 'giraffe', 8))
        g.append(limb((hx + 0.02, y, -0.55), (hx, y, -1.0), 0.045, 0.04, 'giraffe', 8))
        g.append(cyl(0.05, 0.07, (hx, y, -1.0), 'hoof', 8))
    g.append(limb((-0.46, 0, 0.1), (-0.6, 0, -0.35), 0.03, 0.015, 'giraffe', 5))
    g.append(ball(0.04, (-0.6, 0, -0.37), 'spot'))
    g.append(box((0.42, 0.5, 0.08), (0.02, 0, 0.3), 'sad_red'))
    for s in (-1, 1):
        g.append(box((0.45, 0.025, 0.3), (0.02, s * 0.25, 0.12), 'sad_red'))
        g.append(box((0.47, 0.03, 0.04), (0.02, s * 0.255, -0.02), 'gold'))
    return g


groups = [[], [], []]
hi = 0
for idx, (r, a, kind) in enumerate(SLOTS):
    if kind == 'chariot':
        continue
    x, y = r * math.cos(a), r * math.sin(a)
    if kind == 'giraffe':
        M = Matrix.Translation((x, y, HZ + 0.15)) @ Matrix.Rotation(a + math.pi / 2, 4, 'Z')
        groups[idx % 3].extend(place(giraffe(), M))
        continue
    coat, mane, saddle = COATS[hi % len(COATS)]
    pose = (hi * 2 + (r < 4)) % 3
    M = Matrix.Translation((x, y, HZ + (0.1 if pose == 1 else 0))) @ Matrix.Rotation(a + math.pi / 2, 4, 'Z')
    groups[idx % 3].extend(place(horse(pose, coat, mane, saddle, 0.05 * (hi % 2)), M))
    hi += 1

lifts = []
for n, g in enumerate(groups):
    lf = join(f'lift{n}', g)
    lf.parent = rotor
    lifts.append(lf)

objs = [o for o in scene.objects if o.type == 'MESH']
tris = sum(len(pg.vertices) - 2 for o in objs for pg in o.data.polygons)
bpy.context.view_layer.update()
top = max((o.matrix_world @ v.co).z for o in objs for v in o.data.vertices)
xmax = max(abs((o.matrix_world @ v.co).x) for o in objs for v in o.data.vertices)
print(f'CAROUSEL tris={tris} top={top:.2f} width={2 * xmax:.2f} mats_per_obj='
      f'{[(o.name, len(o.data.materials)) for o in objs]}')

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'CAROUSEL glb={OUT_GLB.stat().st_size // 1024} KB')

# ---------- Preview: umumiy va yaqin ko'rinish ----------
lifts[1].location.z = 0.2
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
for fname, loc, tgt in (('preview.png', (13.0, -17.0, 9.5), (0, 0, 3.0)),
                        ('preview_close.png', (3.5, -8.6, 2.6), (1.0, -3.6, 2.0))):
    cam.location = loc
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(PREVIEW_DIR / fname)
    bpy.ops.render.render(write_still=True)
    print('CAROUSEL preview', scene.render.filepath)

"""
Pirate jet (planda raqamsiz attraksion) — qaroqchi kemachalari aylanadi va ko'tarilib-tushadi. Rasm: attraction-images-park/pirates.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/pirate-jet/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png (va preview_close.png — qaroqchi va kema yaqindan)

Tuzilish (xarita kodi: src/map/GltfModel.tsx):
    base       — qimirlamaydigan qism: dumaloq supa, tosh qasr-minora (tishli tepa, ravoqli oynalarda chayka rasmi, rangli
                 chiroqchalar), tepasida o't, sandiq va qilichli qaroqchi haykali (qizil uch burchakli shlyapa, qizil kamzul)
    rotor      — aylanadigan markaz halqasi (minora atrofida)
    arm0..5    — qo'l uyasi (bo'sh tugun, rotor bolasi)
    tilt0..5   — yog'och qo'llar (rangli chiroqchalar, ko'k tirgak): origin — sharnirda, ko'tariladi/tushadi
    hang0..5   — kemachalar (tilt bolasi): doim gorizontal; burni aylanish yo'nalishiga qaragan. Har birida yog'och
                 tag, rangli bort, kayuta (oltin derazalar, oltin minorachalar), machta (savat-bochka, oq yelkan),
                 shturval, langar, yumshoq o'rindiqlar
Asl o'lcham metrda: diametri ~8.9 m, balandligi ~5.6 m (qaroqchi shlyapasi bilan). Old tomoni — Blender'da -Y.
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
    'deck': (0.3, 0.42, 0.62), 'deck_side': (0.18, 0.28, 0.45), 'stone': (0.82, 0.83, 0.84), 'stone_dark': (0.6, 0.61, 0.63),
    'grass': (0.25, 0.65, 0.2), 'wood': (0.5, 0.27, 0.12), 'wood_dark': (0.32, 0.17, 0.08), 'gold': (0.9, 0.7, 0.2),
    'window': (0.45, 0.65, 0.9), 'white': (0.97, 0.97, 0.96), 'beak': (0.98, 0.55, 0.1), 'eye': (0.06, 0.06, 0.08),
    'skin': (1.0, 0.8, 0.7), 'hair': (0.35, 0.2, 0.1), 'coat': (0.85, 0.15, 0.15), 'scarf': (0.98, 0.82, 0.2),
    'pants': (0.2, 0.45, 0.85), 'boot': (0.4, 0.22, 0.1), 'silver': (0.8, 0.82, 0.85), 'iris': (0.2, 0.5, 0.9),
    'sail': (0.96, 0.94, 0.88), 'cable': (0.15, 0.4, 0.85), 'red': (0.85, 0.12, 0.12), 'blue': (0.2, 0.5, 0.9),
    'pink': (0.95, 0.62, 0.78), 'yellow': (0.98, 0.78, 0.12), 'green_l': (0.2, 0.8, 0.3), 'iron': (0.35, 0.36, 0.38),
    'c_blue': (0.25, 0.6, 0.95), 'c_red': (0.85, 0.18, 0.2), 'c_pink': (0.98, 0.7, 0.85), 'c_yellow': (0.98, 0.85, 0.3),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.4
    if name in ('gold', 'silver', 'iron'):
        bsdf.inputs['Metallic'].default_value = 0.3  # xaritada atrof-muhit aksi yo'q — yuqori metallik qoraygan ko'rinadi
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
    a, b = Vector(a), Vector(b)
    d = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r1, radius2=r2, depth=d.length)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix())
    bmesh.ops.translate(bm, vec=(a + b) / 2, verts=bm.verts)
    return new_obj('limb', bm, mat)


def beam(a, b, w, d, mat):
    a, b = Vector(a), Vector(b)
    v = b - a
    ob = box((v.length, w, d), (0, 0, 0), mat)
    ob.rotation_euler = v.to_track_quat('X', 'Z').to_euler()
    ob.location = (a + b) / 2
    return ob


def torus(R, r, loc, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=14, minor_segments=4, location=loc, rotation=rot)
    t = bpy.context.active_object
    t.data.materials.append(MATS[mat])
    return t


def face_poly(a, apo, pts, mat, off=0.0):
    """Ko'pburchak yuzidagi shakl (u — gorizontal, v — z), tashqaridan qaraganda soat strelkasiga teskari"""
    n = Vector((math.cos(a), math.sin(a), 0))
    t = Vector((-math.sin(a), math.cos(a), 0))
    bm = bmesh.new()
    bm.faces.new([bm.verts.new(n * (apo + off) + t * u + Vector((0, 0, v))) for u, v in pts])
    return new_obj('face', bm, mat)


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


JEWELS = ['red', 'yellow', 'green_l', 'blue', 'white']

# ====================== BASE: supa, qasr-minora, qaroqchi ======================
R_DECK, H0 = 4.45, 0.15
p = [cyl(R_DECK, H0, (0, 0, H0 / 2), 'deck_side', 48), cyl(R_DECK - 0.06, 0.02, (0, 0, H0 + 0.01), 'deck', 48)]
NT = 10
R_T, T_TOP = 0.95, 2.6
HALF = math.pi / NT
APO = R_T * math.cos(HALF)
p.append(cyl(1.3, 0.25, (0, 0, H0 + 0.125), 'cable', NT, (0, 0, HALF)))            # ko'k taglik halqa
p.append(cyl(1.12, 0.7, (0, 0, H0 + 0.6), 'stone_dark', NT, (0, 0, HALF)))
p.append(cyl(R_T, T_TOP - H0 - 0.95, (0, 0, (H0 + 0.95 + T_TOP) / 2), 'stone', NT, (0, 0, HALF)))
for k in range(NT):
    a = 2 * math.pi * k / NT
    # ravoqli oyna: ko'k fon, oltin ramka, chayka (oq bosh, to'q sariq tumshuq, ko'zlar)
    z0, w = 1.35, 0.42
    arch = [(-w / 2, z0), (w / 2, z0)] + [(w / 2 * math.cos(math.pi * i / 8), z0 + 0.55 + w / 2 * math.sin(math.pi * i / 8))
                                          for i in range(9)]
    p.append(face_poly(a, APO, [(u * 1.2, z0 - 0.05 + (v - z0) * 1.08) for u, v in arch], 'gold', 0.01))
    p.append(face_poly(a, APO, arch, 'window', 0.02))
    n = Vector((math.cos(a), math.sin(a), 0))
    t = Vector((-math.sin(a), math.cos(a), 0))
    c = n * (APO + 0.05) + Vector((0, 0, z0 + 0.45))
    p.append(ball(0.15, c, 'white', 1, (0.4, 1, 1.05)))
    p.append(ball(0.09, c + n * 0.06 + Vector((0, 0, -0.06)), 'beak', 1, (0.8, 1.1, 0.5)))
    for s in (-1, 1):
        p.append(ball(0.025, c + n * 0.06 + t * (s * 0.05) + Vector((0, 0, 0.05)), 'eye'))
    # pastki qismdagi eshikcha va chiroqchalar
    p.append(face_poly(a, 1.12 * math.cos(HALF), [(-0.18, H0 + 0.3), (0.18, H0 + 0.3), (0.18, H0 + 0.85), (-0.18, H0 + 0.85)],
                       'wood', 0.01))
    for j in range(3):
        p.append(ball(0.035, n * (APO + 0.03) + t * (0.27 * (1 if k % 2 else -1)) + Vector((0, 0, 1.3 + j * 0.35)),
                      JEWELS[(j + k) % 5]))
# tishli tepa (merlonlar) va tosh choklari
p.append(cyl(R_T + 0.08, 0.12, (0, 0, T_TOP - 0.06), 'stone_dark', NT, (0, 0, HALF)))
for k in range(NT):
    a = 2 * math.pi * k / NT
    p.append(box((0.22, 0.45, 0.3), ((R_T + 0.02) * math.cos(a), (R_T + 0.02) * math.sin(a), T_TOP + 0.15), 'stone', (0, 0, a)))
p.append(cyl(R_T - 0.05, 0.08, (0, 0, T_TOP + 0.04), 'grass', NT, (0, 0, HALF)))
# sandiq (o'rindiq), to'p
TZ = T_TOP + 0.08
p.append(box((0.85, 0.55, 0.45), (0, 0.05, TZ + 0.22), 'wood'))
p.append(cyl(0.28, 0.85, (0, 0.05, TZ + 0.45), 'wood', 12, (0, math.pi / 2, 0)))
for x in (-0.3, 0.3):
    p.append(box((0.06, 0.58, 0.48), (x, 0.05, TZ + 0.24), 'gold'))
p.append(cyl(0.12, 0.6, (0.55, -0.15, TZ + 0.18), 'silver', 12, (math.pi / 2 - 0.25, 0, 0.3)))
p.append(cyl(0.16, 0.1, (0.55, 0.15, TZ + 0.15), 'wood_dark', 10, (0, math.pi / 2, 0)))

# --- qaroqchi (o'tirgan, -Y ga qaragan) ---
HZ = TZ + 0.62               # son (o'tirish) balandligi
for s in (-1, 1):            # oyoqlar: son, boldir, etik
    hip = Vector((s * 0.18, 0.0, HZ))
    knee = Vector((s * 0.24, -0.5, HZ + 0.05))
    foot = Vector((s * 0.26, -0.62, TZ + 0.05))
    p.append(limb(hip, knee, 0.15, 0.13, 'pants', 10))
    p.append(ball(0.13, knee, 'pants'))
    p.append(limb(knee, foot + Vector((0, 0, 0.15)), 0.12, 0.11, 'boot', 10))
    p.append(ball(0.14, foot + Vector((0, -0.08, 0.08)), 'boot', 1, (1, 1.5, 0.8)))
    p.append(cyl(0.15, 0.1, knee + Vector((0, -0.02, -0.12)), 'boot', 10))
p.append(ball(0.32, (0, 0.05, HZ + 0.05), 'pants', 1, (1.15, 0.9, 0.6)))                       # tos
p.append(limb((0, 0.05, HZ + 0.05), (0, 0.08, HZ + 0.85), 0.36, 0.32, 'coat', 12))              # tana (kamzul)
p.append(limb((0, 0.12, HZ + 0.1), (0, 0.4, HZ - 0.25), 0.36, 0.25, 'coat', 10))               # kamzul etagi
for s in (-1, 1):
    p.append(box((0.05, 0.03, 0.6), (s * 0.12, -0.27, HZ + 0.45), 'gold'))                     # tugmalar qatori
    for k in range(4):
        p.append(ball(0.025, (s * 0.08, -0.3, HZ + 0.25 + k * 0.15), 'gold'))
p.append(ball(0.2, (0, -0.18, HZ + 0.8), 'scarf', 1, (1.3, 0.7, 0.8)))                         # sariq sharf
p.append(limb((0, -0.22, HZ + 0.72), (0.06, -0.3, HZ + 0.45), 0.08, 0.05, 'scarf', 8))
SH = Vector((0, 0.08, HZ + 0.85))
p.append(limb(SH, SH + Vector((0, 0, 0.18)), 0.12, 0.12, 'skin', 10))                          # bo'yin
HD = SH + Vector((0, -0.04, 0.45))
p.append(ball(0.32, HD, 'skin', 2, (0.95, 0.95, 1.05)))                                         # bosh
p.append(ball(0.07, HD + Vector((0, -0.31, -0.02)), 'skin', 1, (1, 1.3, 1)))                   # burun
for s in (-1, 1):
    p.append(ball(0.07, HD + Vector((s * 0.12, -0.26, 0.07)), 'white', 1, (1, 0.6, 1.2)))
    p.append(ball(0.04, HD + Vector((s * 0.12, -0.31, 0.07)), 'iris'))
    p.append(ball(0.06, HD + Vector((s * 0.3, -0.02, 0.0)), 'skin', 1, (0.5, 1, 1)))            # quloqlar
p.append(limb(HD + Vector((-0.1, -0.27, -0.14)), HD + Vector((0.1, -0.27, -0.14)), 0.02, 0.02, 'coat', 6))   # tabassum
p.append(ball(0.31, HD + Vector((0, 0.08, 0.03)), 'hair', 1, (1.02, 0.9, 1.0)))                # soch (orqa)
# uch burchakli qizil shlyapa: keng gardish, toj, oltin hoshiya, pat
HT = HD + Vector((0, 0, 0.27))
p.append(cyl(0.3, 0.3, HT + Vector((0, 0, 0.14)), 'coat', 12, r2=0.25))                    # toj
for k in range(3):   # uch tomonga yuqoriga qayrilgan qirralar (bir burchagi oldinga — -Y)
    a = -math.pi / 2 + math.pi / 3 + k * 2 * math.pi / 3
    d = Vector((math.cos(a), math.sin(a), 0))
    c = HT + d * 0.32 + Vector((0, 0, 0.1))
    tb = 0.35   # qirra tashqariga og'ishi (radian): Y atrofida musbat — tepasi tashqariga
    p.append(box((0.08, 0.62, 0.3), c, 'coat', (0, tb, a)))
    p.append(box((0.05, 0.64, 0.05), c + d * (0.15 * math.sin(tb)) + Vector((0, 0, 0.15 * math.cos(tb))), 'gold', (0, tb, a)))
p.append(cyl(0.42, 0.05, HT + Vector((0, 0, 0.0)), 'coat', 3, (0, 0, math.pi / 2)))         # ostki gardish
p.append(limb(HT + Vector((0.22, 0.1, 0.2)), HT + Vector((0.45, 0.3, 0.55)), 0.03, 0.005, 'white', 5))
# qo'llar: o'ng — tepaga ko'tarilgan qilich, chap — tizzada
RS = SH + Vector((0.36, 0, -0.05))
RE = RS + Vector((0.22, -0.15, -0.22))
RH = RE + Vector((0.05, -0.28, 0.12))
p.append(limb(RS, RE, 0.11, 0.1, 'coat', 10))
p.append(limb(RE, RH, 0.1, 0.09, 'coat', 10))
p.append(ball(0.1, RH, 'skin'))
blade = [RH + Vector((0, 0, 0.1)), RH + Vector((0.08, -0.08, 0.5)), RH + Vector((0.28, -0.12, 0.85))]  # yuzdan chetga, tepaga
p.append(box((0.22, 0.05, 0.05), RH + Vector((0, 0, 0.08)), 'gold'))
for a, b in zip(blade, blade[1:]):
    p.append(limb(a, b, 0.05, 0.035, 'silver', 6))
LS = SH + Vector((-0.36, 0, -0.05))
LE = LS + Vector((-0.08, -0.25, -0.3))
LH = Vector((-0.24, -0.45, HZ + 0.22))
p.append(limb(LS, LE, 0.11, 0.1, 'coat', 10))
p.append(limb(LE, LH, 0.1, 0.09, 'coat', 10))
p.append(ball(0.1, LH, 'skin'))
base = join('base', p)

# ====================== ROTOR: markaz halqasi ======================
q = [cyl(1.25, 0.3, (0, 0, 1.0), 'wood_dark', NT, (0, 0, HALF)), cyl(1.28, 0.06, (0, 0, 1.17), 'gold', NT, (0, 0, HALF))]
for k in range(NT * 2):
    a = 2 * math.pi * k / (NT * 2)
    q.append(ball(0.04, (1.27 * math.cos(a), 1.27 * math.sin(a), 1.0), JEWELS[k % 5]))
q.append(cyl(1.05, 0.12, (0, 0, 2.15), 'cable', NT, (0, 0, HALF)))       # tirgaklar halqasi (yuqorida)
rotor = join('rotor', q)

# ====================== Qo'llar va kemachalar ======================
HINGE_R, HINGE_Z = 1.15, 1.0
ARM_L = 2.35
REST = math.radians(8)
SHIPS = [('c_blue', 'blue'), ('c_red', 'yellow'), ('c_pink', 'white'), ('c_yellow', 'red'), ('c_red', 'blue'), ('c_blue', 'pink')]


def ship(col, trim):
    """Kemacha: lokal +Y — burun (aylanish yo'nalishi), +X — tashqariga; origin — qo'l uchida"""
    g = []
    L, W = 2.4, 1.35
    cx = 0.45                 # kema markazi qo'l uchidan tashqarida
    ZB = -0.45                # kil (qo'l uchidan pastda)
    NSEC, NPH = 14, 8

    def sec(t):
        hw = W / 2 * (1 - 0.88 * max(0.0, t) ** 2.2) * (0.92 if t < -0.85 else 1.0)
        zb = ZB + 0.3 * max(0.0, t) ** 2 + 0.08 * max(0.0, -t) ** 3
        zt = ZB + 0.72 + 0.22 * max(0.0, t) ** 3 + 0.1 * max(0.0, -t) ** 2
        return hw, zb, zt

    def surf(mat, ph0, ph1, inset=0.0, inward=False):
        bm = bmesh.new()
        rings = []
        for i in range(NSEC + 1):
            t = -1 + 2 * i / NSEC
            hw, zb, zt = sec(t)
            hw = max(0.04, hw - inset)
            ring = []
            for k in range(NPH + 1):
                ph = ph0 + (ph1 - ph0) * k / NPH
                ring.append(bm.verts.new((cx - hw * math.cos(ph), t * L / 2, zt - (zt - zb - inset) * math.sin(ph) ** 0.6)))
            rings.append(ring)
        for a, b in zip(rings, rings[1:]):
            for k in range(NPH):
                f = [a[k], a[k + 1], b[k + 1], b[k]] if inward else [a[k], b[k], b[k + 1], a[k + 1]]
                bm.faces.new(f)
        if not inward:
            for ring, rev in ((rings[0], True), (rings[-1], False)):
                try:
                    bm.faces.new(ring[::-1] if rev else ring)
                except ValueError:
                    pass
        return new_obj('hull', bm, mat)
    g.append(surf(col, 0.0, 0.75))
    g.append(surf('wood', 0.75, math.pi - 0.75))
    g.append(surf(col, math.pi - 0.75, math.pi))
    g.append(surf(col, 0.0, math.pi, 0.06, inward=True))
    for side in (-1, 1):  # bort hoshiyasi (oltin/rangli), chiroqchalar, langar
        tops = []
        for i in range(NSEC + 1):
            t = -1 + 2 * i / NSEC
            hw, zb, zt = sec(t)
            tops.append(Vector((cx + side * hw, t * L / 2, zt + 0.02)))
        for a, b in zip(tops, tops[1:]):
            g.append(limb(a, b, 0.04, 0.04, trim, 6))
        for k in range(5):
            t = -0.7 + k * 0.32
            hw, zb, zt = sec(t)
            g.append(ball(0.035, (cx + side * (hw + 0.01), t * L / 2, zt - 0.16), JEWELS[k % 5]))
        hw, zb, zt = sec(0.35)
        ax = cx + side * (hw * 0.9 + 0.03)
        g.append(box((0.03, 0.04, 0.26), (ax, 0.42, zt - 0.3), 'iron'))
        g.append(box((0.03, 0.2, 0.04), (ax, 0.42, zt - 0.2), 'iron'))
        g.append(torus(0.09, 0.018, (ax, 0.42, zt - 0.43), 'iron', (0, math.pi / 2, 0)))
    # o'rindiqlar (yumshoq, bort rangida) — ikki qator
    for y in (-0.15, 0.45):
        g.append(box((W - 0.4, 0.4, 0.14), (cx, y, ZB + 0.38), col))
        g.append(box((W - 0.4, 0.08, 0.35), (cx, y - 0.22, ZB + 0.55), col))
    # kayuta (orqada): derazalar, oltin minorachalar
    yk = -L / 2 + 0.32
    hw, zb, zt = sec(-0.8)
    g.append(box((2 * hw + 0.08, 0.55, 0.55), (cx, yk, zt + 0.22), trim))
    g.append(box((2 * hw + 0.1, 0.6, 0.06), (cx, yk, zt + 0.52), 'gold'))
    for side in (-1, 1):
        for k in range(2):
            g.append(box((0.02, 0.14, 0.22), (cx + side * (hw + 0.05), yk - 0.12 + k * 0.24, zt + 0.22), 'window'))
            g.append(box((0.015, 0.17, 0.25), (cx + side * (hw + 0.045), yk - 0.12 + k * 0.24, zt + 0.22), 'gold'))
        g.append(cyl(0.1, 0.18, (cx + side * hw, yk - 0.25, zt + 0.62), 'gold', 8))
        g.append(cyl(0.1, 0.22, (cx + side * hw, yk - 0.25, zt + 0.82), 'gold', 8, r2=0.0))
    for k in range(3):
        g.append(box((0.18, 0.02, 0.2), (cx - 0.25 + k * 0.25, yk - 0.29, zt + 0.22), 'window'))
    hw_b, zb_b, zt_b = sec(0.85)
    for side in (-1, 1):  # burundagi oltin minorachalar
        g.append(cyl(0.07, 0.12, (cx + side * (hw_b + 0.05), L / 2 * 0.8, zt_b + 0.08), 'gold', 8))
        g.append(cyl(0.07, 0.16, (cx + side * (hw_b + 0.05), L / 2 * 0.8, zt_b + 0.22), 'gold', 8, r2=0.0))
    # shturval (kumush), machta, savat-bochka, yelkan
    g.append(torus(0.16, 0.02, (cx, yk + 0.38, zt + 0.3), 'silver', (math.pi / 2, 0, 0)))
    for k in range(4):
        a = k * math.pi / 4
        g.append(beam((cx - 0.2 * math.cos(a), yk + 0.38, zt + 0.3 - 0.2 * math.sin(a)),
                      (cx + 0.2 * math.cos(a), yk + 0.38, zt + 0.3 + 0.2 * math.sin(a)), 0.02, 0.02, 'silver'))
    MY = 0.15
    g.append(cyl(0.05, 2.1, (cx, MY, ZB + 0.3 + 1.05), 'wood', 8, r2=0.035))
    g.append(cyl(0.12, 0.2, (cx, MY, ZB + 2.0), 'wood_dark', 10, r2=0.14))
    g.append(cyl(0.025, 0.25, (cx, MY, ZB + 2.5), 'wood', 6, r2=0.01))
    YZ = ZB + 1.65
    g.append(limb((cx - 0.55, MY, YZ), (cx + 0.55, MY, YZ), 0.025, 0.025, 'wood', 6))
    bm = bmesh.new()   # yelkan: biroz shishgan (oldinga) varaq, ikki tomonlama
    for face_side, off in ((0, 0.0), (1, -0.006)):   # old va orqa yuz — alohida vertekslar
        rows = []
        for i in range(5):
            u = -1 + 2 * i / 4
            col_v = []
            for j in range(4):
                v = j / 3
                bulge = 0.12 * (1 - u * u) * math.sin(math.pi * v)
                col_v.append(bm.verts.new((cx + u * 0.5, MY + 0.05 + bulge + off, YZ - 0.05 - v * 0.55)))
            rows.append(col_v)
        for a, b in zip(rows, rows[1:]):
            for j in range(3):
                bm.faces.new([a[j], b[j], b[j + 1], a[j + 1]] if face_side == 0 else [a[j], a[j + 1], b[j + 1], b[j]])
    g.append(new_obj('sail', bm, 'sail'))
    return g


for n in range(6):
    yaw = n * math.pi / 3 + math.pi / 6
    arm = bpy.data.objects.new(f'arm{n}', None)
    scene.collection.objects.link(arm)
    arm.parent = rotor
    arm.location = (math.cos(yaw) * HINGE_R, math.sin(yaw) * HINGE_R, HINGE_Z)
    arm.rotation_euler = (0, 0, yaw)
    t = [box((ARM_L, 0.24, 0.26), (ARM_L / 2, 0, 0), 'wood')]
    t.append(box((ARM_L - 0.3, 0.26, 0.04), (ARM_L / 2 + 0.1, 0, 0.14), 'wood_dark'))
    for k in range(6):
        t.append(ball(0.045, (0.35 + k * 0.36, 0, 0.17), JEWELS[k % 5]))
        t.append(box((0.04, 0.27, 0.06), (0.35 + k * 0.36, 0, 0.0), 'wood_dark'))
    t.append(cyl(0.14, 0.32, (0, 0, 0), 'iron', 10, (math.pi / 2, 0, 0)))
    t.append(box((0.25, 0.3, 0.35), (ARM_L - 0.05, 0, -0.05), 'iron'))                     # uchidagi sharnir qutisi
    t.append(limb((1.2, 0, 0.13), (-0.15, 0, 1.15), 0.035, 0.035, 'cable', 6))            # ko'k tirgak (yuqori halqaga)
    tilt = bpy.data.objects.new('tmp', None)
    tl = join(f'tilt{n}', t)
    bpy.data.objects.remove(tilt)
    tl.parent = arm
    tl.location = (0, 0, 0)
    tl.rotation_euler = (0, REST, 0)      # Blender'da +Y atrofida musbat burchak — uchi pastga
    hang = join(f'hang{n}', ship(*SHIPS[n]))
    hang.parent = tl
    hang.location = (ARM_L, 0, 0.05)
    hang.rotation_euler = (0, -REST, 0)

objs = [o for o in scene.objects if o.type == 'MESH']
tris = sum(len(pg.vertices) - 2 for o in objs for pg in o.data.polygons)
bpy.context.view_layer.update()
allv = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
print(f'PIRATE tris={tris} x={min(v.x for v in allv):.2f}..{max(v.x for v in allv):.2f} '
      f'y={min(v.y for v in allv):.2f}..{max(v.y for v in allv):.2f} z={min(v.z for v in allv):.2f}..{max(v.z for v in allv):.2f}')

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'PIRATE glb={OUT_GLB.stat().st_size // 1024} KB')

# ---------- Preview (ikki kema ko'tarilgan) ----------
for o in objs:
    if o.name in ('tilt1', 'tilt4'):
        o.rotation_euler.y = REST - math.radians(22)
        o.children[0].rotation_euler.y = -(REST - math.radians(22))
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
for fname, loc, tgt in (('preview.png', (7.5, -10.5, 6.5), (0, 0, 1.8)),
                        ('preview_close.png', (1.5, -5.0, 4.6), (0, 0, 3.4))):
    cam.location = loc
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(PREVIEW_DIR / fname)
    bpy.ops.render.render(write_still=True)
    print('PIRATE preview', scene.render.filepath)

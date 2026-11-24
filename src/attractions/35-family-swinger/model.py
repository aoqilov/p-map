"""
35 — Аттракцион "Family swinger" (zanjirli karusel, savatchali). Rasm: attraction-images-park/Family_Swinger.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/35-family-swinger/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png (va preview_close.png — yaqin ko'rinish)

Tuzilish (xarita kodi: src/map/GltfModel.tsx):
    base        — qimirlamaydigan qism: qizil dumaloq poydevor, 12 qirrali ustun (krem panellar oltin jingalak va gulli
                  ovallar bilan, qizil chiroqli pilyastrlar), rasmli ovallar qatori
    rotor       — aylanadigan qism: soyabon osti (krem konus, qizil qovurg'alar, chiroqlar), 12 qirrali friz (rasmli
                  oval panellar, qizil ramka, ravoqli tishli tepa, chiroqlar), qizil-krem yo'l-yo'l tom, oltin shpil
    swing0..23  — to'rli savatlar zanjirlarda (rotor bolalari): origin — ilgakda, lokal +Y — tashqariga;
                  kod ularni tashqariga og'diradi (markazdan qochma kuch) — lokal X o'qi atrofida
Asl o'lcham metrda: soyabon diametri ~9.4 m, balandligi ~8.4 m. Old tomoni — Blender'da -Y.
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
    'red': (0.6, 0.06, 0.08), 'red_dark': (0.42, 0.04, 0.05), 'cream': (0.95, 0.88, 0.7), 'ivory': (0.99, 0.96, 0.88),
    'gold': (0.86, 0.66, 0.28), 'pink': (0.9, 0.62, 0.62), 'bulb': (1.0, 0.93, 0.7), 'steel': (0.7, 0.71, 0.73),
    'paint_sky': (0.62, 0.8, 0.9), 'paint_sea': (0.3, 0.55, 0.68), 'paint_build': (0.93, 0.9, 0.82),
    'paint_dark': (0.25, 0.3, 0.32), 'flower_r': (0.8, 0.2, 0.25), 'flower_g': (0.3, 0.55, 0.3),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.4
    if name in ('gold', 'steel'):
        bsdf.inputs['Metallic'].default_value = 0.35  # xaritada atrof-muhit aksi yo'q — yuqori metallik qoraygan ko'rinadi
    if name == 'bulb':
        bsdf.inputs['Emission Color'].default_value = (1.0, 0.92, 0.7, 1)
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


def limb(a, b, r1, r2, mat, segs=6):
    a, b = Vector(a), Vector(b)
    d = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r1, radius2=r2, depth=d.length)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix())
    bmesh.ops.translate(bm, vec=(a + b) / 2, verts=bm.verts)
    return new_obj('limb', bm, mat)


def lathe(profile, mat, segs=48, mats=None, phase=0.0):
    """Aylanish yuzasi [(r, z), ...]: profil yuqoriga yursa — normal tashqariga, ichkariga yursa — tepaga.
    mats=(m0, m1) — sektorlar navbatma-navbat ikki rangda (ikki obyekt)"""
    def build(parity):
        bm = bmesh.new()
        rings = [[bm.verts.new((r * math.cos(phase + 2 * math.pi * i / segs), r * math.sin(phase + 2 * math.pi * i / segs), z))
                  for i in range(segs)] for r, z in profile]
        for a, b in zip(rings, rings[1:]):
            for i in range(segs):
                if parity is not None and i % 2 != parity:
                    continue
                j = (i + 1) % segs
                bm.faces.new([a[i], a[j], b[j], b[i]])
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        return bm
    if mats:
        return [new_obj('lathe', build(0), mats[0]), new_obj('lathe', build(1), mats[1])]
    return new_obj('lathe', build(None), mat)


def face_pt(a, apo, u, v, off=0.0):
    """Ko'pburchak yuzidagi nuqta: a — yuz markazi burchagi, apo — apofema, u — gorizontal (soat strelkasiga teskari), v — z"""
    n = Vector((math.cos(a), math.sin(a), 0))
    t = Vector((-math.sin(a), math.cos(a), 0))
    return n * (apo + off) + t * u + Vector((0, 0, v))


def face_poly(a, apo, pts, mat, off=0.0, double=False):
    """Yuzga yopishgan ko'pburchak (tashqaridan qaraganda soat strelkasiga teskari tartib)"""
    bm = bmesh.new()
    bm.faces.new([bm.verts.new(face_pt(a, apo, u, v, off)) for u, v in pts])
    if double:
        bm.faces.new([bm.verts.new(face_pt(a, apo, u, v, off - 0.006)) for u, v in pts][::-1])
    return new_obj('face', bm, mat)


def ellipse(w, h, n=20, cx=0.0, cy=0.0):
    return [(cx + w / 2 * math.cos(2 * math.pi * k / n), cy + h / 2 * math.sin(2 * math.pi * k / n)) for k in range(n)]


def painting(a, apo, w, h, cz, off, variant):
    """Oval rasm: osmon, dengiz, oq binolar/kema (variant bo'yicha)"""
    res = [face_poly(a, apo, ellipse(w, h, 24, 0, cz), 'paint_sky', off)]
    sea = [(u, v) for u, v in ellipse(w, h, 24, 0, cz) if v <= cz - h * 0.12]
    sea = sorted(sea, key=lambda uv: math.atan2(uv[1] - cz, uv[0]))
    res.append(face_poly(a, apo, [(-w / 2 * 0.93, cz - h * 0.12)] + sea + [(w / 2 * 0.93, cz - h * 0.12)], 'paint_sea', off + 0.004))
    if variant % 3 == 0:    # kema
        res.append(face_poly(a, apo, [(-w * 0.22, cz - h * 0.1), (w * 0.2, cz - h * 0.1), (w * 0.15, cz - h * 0.2),
                                      (-w * 0.17, cz - h * 0.2)], 'paint_dark', off + 0.008))
        res.append(face_poly(a, apo, [(-w * 0.05, cz - h * 0.09), (w * 0.05, cz - h * 0.09), (w * 0.03, cz + h * 0.05),
                                      (-w * 0.03, cz + h * 0.05)], 'paint_build', off + 0.008))
    elif variant % 3 == 1:  # ustunli bino
        res.append(face_poly(a, apo, [(-w * 0.28, cz - h * 0.12), (w * 0.28, cz - h * 0.12), (w * 0.28, cz + h * 0.12),
                                      (-w * 0.28, cz + h * 0.12)], 'paint_build', off + 0.008))
        for k in range(5):
            x = -w * 0.22 + k * w * 0.11
            res.append(face_poly(a, apo, [(x - 0.012, cz - h * 0.1), (x + 0.012, cz - h * 0.1), (x + 0.012, cz + h * 0.08),
                                          (x - 0.012, cz + h * 0.08)], 'paint_dark', off + 0.012))
    else:                   # minoralar
        for x, hh in ((-w * 0.2, 0.32), (w * 0.05, 0.22), (w * 0.22, 0.28)):
            res.append(face_poly(a, apo, [(x - w * 0.04, cz - h * 0.12), (x + w * 0.04, cz - h * 0.12), (x + w * 0.04, cz + h * hh),
                                          (x - w * 0.04, cz + h * hh)], 'paint_build', off + 0.008))
    return res


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
N = 12                         # qirralar soni
HALF = math.pi / N
R_CAN = 4.7                    # soyabon (friz) uchlari radiusi
APO_CAN = R_CAN * math.cos(HALF)
FRIEZE_BOT, FRIEZE_TOP = 5.5, 6.5
R_COL = 1.3                    # ustun pastki qismi (12 qirra)
APO_COL = R_COL * math.cos(HALF)
COL_TOP = 2.65
R_UP = 1.08                    # ustun yuqori qismi (rasmli ovallar)
UP_TOP = 3.55
CONE_BOT = 4.3                 # soyabon osti konusining pastki uchi

# ====================== BASE: poydevor va ustun ======================
p = []
p.append(cyl(2.35, 0.22, (0, 0, 0.11), 'red_dark', 48))
p.append(cyl(2.3, 0.04, (0, 0, 0.24), 'red', 48))
p.append(cyl(1.55, 0.12, (0, 0, 0.32), 'red', N, (0, 0, HALF)))
p.append(cyl(R_COL, COL_TOP - 0.38, (0, 0, 0.38 + (COL_TOP - 0.38) / 2), 'cream', N, (0, 0, HALF)))
for k in range(N):
    a = 2 * math.pi * k / N            # yuz markazi (cyl rot=HALF — uchlari yuzlar orasida)
    w = R_COL * math.sin(HALF) * 2 * 0.78
    z0, z1 = 0.55, COL_TOP - 0.15
    # pastki krem panel: oltin ramka, tepada yarim aylana, oltin jingalak, gulli oval
    frame = [(-w / 2, z0), (w / 2, z0)] + [(w / 2 * math.cos(math.pi * i / 10), z1 - w / 2 + w / 2 * math.sin(math.pi * i / 10))
                                         for i in range(11)]
    p.append(face_poly(a, APO_COL, frame, 'gold', 0.01))
    inner = [(u * 0.86, z0 + 0.04 + (v - z0) * 0.95) for u, v in frame]
    p.append(face_poly(a, APO_COL, inner, 'ivory', 0.015))
    p.append(face_poly(a, APO_COL, ellipse(w * 0.46, 0.5, 16, 0, 1.25), 'gold', 0.02))
    p.append(face_poly(a, APO_COL, ellipse(w * 0.38, 0.42, 16, 0, 1.25), 'ivory', 0.025))
    for (du, dv, col) in ((0, 0.06, 'flower_r'), (-0.06, -0.04, 'flower_r'), (0.06, -0.04, 'pink'), (0, -0.12, 'flower_g'),
                          (-0.08, 0.1, 'flower_g'), (0.08, 0.1, 'flower_g')):
        p.append(ball(0.035, face_pt(a, APO_COL, du, 1.25 + dv, 0.04), col))
    for s in (-1, 1):  # jingalaklar (tepada)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.08, minor_radius=0.018, major_segments=10, minor_segments=4,
                                         location=face_pt(a, APO_COL, s * 0.09, z1 - 0.28, 0.03),
                                         rotation=(math.pi / 2, 0, a + math.pi / 2))
        t = bpy.context.active_object
        t.data.materials.append(MATS['gold'])
        p.append(t)
    p.append(ball(0.05, face_pt(a, APO_COL, 0, z1 - 0.1, 0.04), 'gold'))
    p.append(face_poly(a, APO_COL, [(-w * 0.35, 0.42), (w * 0.35, 0.42), (w * 0.35, 0.5), (-w * 0.35, 0.5)], 'gold', 0.02))
for k in range(N):  # qizil pilyastrlar (qirralarda) chiroqchalar bilan
    a = 2 * math.pi * k / N + HALF
    c = Vector((math.cos(a), math.sin(a), 0)) * (R_COL + 0.01)
    p.append(box((0.1, 0.13, COL_TOP - 0.38), (c.x, c.y, 0.38 + (COL_TOP - 0.38) / 2), 'red', (0, 0, a)))
    for j in range(9):
        p.append(ball(0.026, (c.x * 1.05, c.y * 1.05, 0.55 + j * 0.24), 'bulb'))
p.append(cyl(R_COL + 0.1, 0.14, (0, 0, COL_TOP + 0.07), 'red', N, (0, 0, HALF)))
for k in range(36):
    a = 2 * math.pi * k / 36
    p.append(ball(0.03, ((R_COL + 0.13) * math.cos(a), (R_COL + 0.13) * math.sin(a), COL_TOP + 0.07), 'bulb'))
# ustun yuqori qismi: qizil, 12 ta rasmli oval (pushti ramka, chiroqlar)
APO_UP = R_UP * math.cos(HALF)
p.append(cyl(R_UP, UP_TOP - COL_TOP - 0.14, (0, 0, (COL_TOP + 0.14 + UP_TOP) / 2), 'red', N, (0, 0, HALF)))
for k in range(N):
    a = 2 * math.pi * k / N
    cz = (COL_TOP + 0.14 + UP_TOP) / 2
    p.append(face_poly(a, APO_UP, ellipse(0.5, 0.56, 20, 0, cz), 'pink', 0.01))
    p.append(face_poly(a, APO_UP, ellipse(0.42, 0.46, 20, 0, cz), 'gold', 0.014))
    p.extend(painting(a, APO_UP, 0.36, 0.38, cz, 0.018, k))
    for i in range(10):
        t = 2 * math.pi * i / 10
        p.append(ball(0.022, face_pt(a, APO_UP, 0.25 * math.cos(t), cz + 0.28 * math.sin(t), 0.02), 'ivory'))
p.append(cyl(R_UP + 0.06, 0.1, (0, 0, UP_TOP + 0.05), 'gold', N, (0, 0, HALF)))
base = join('base', p)

# ====================== ROTOR: soyabon ======================
q = []
# soyabon osti: krem konus (ustundan frizga), qizil qovurg'alar, qovurg'alarda chiroqlar
q.append(cyl(0.95, CONE_BOT - UP_TOP - 0.1, (0, 0, (UP_TOP + 0.1 + CONE_BOT) / 2), 'red', N, (0, 0, HALF)))
CONE = [(0.95, CONE_BOT), (R_CAN - 0.05, FRIEZE_BOT)]
q.extend(lathe(CONE, None, 2 * N, ('cream', 'cream'), HALF))     # pastga qaragan (profil tashqariga/yuqoriga — normal pastga)
for k in range(N):
    a = 2 * math.pi * k / N + HALF
    r0, z0 = 1.0, CONE_BOT - 0.02
    r1, z1 = R_CAN - 0.1, FRIEZE_BOT - 0.05
    q.append(limb((r0 * math.cos(a), r0 * math.sin(a), z0), (r1 * math.cos(a), r1 * math.sin(a), z1), 0.07, 0.06, 'red', 6))
    for j in range(7):
        t = (j + 1) / 8
        q.append(ball(0.035, ((r0 + (r1 - r0) * t) * math.cos(a), (r0 + (r1 - r0) * t) * math.sin(a),
                              z0 + (z1 - z0) * t - 0.07), 'ivory'))
q.append(cyl(R_CAN * 0.98, 0.05, (0, 0, FRIEZE_BOT + 0.02), 'cream', N, (0, 0, HALF)))  # friz osti (pastdan ko'rinadi)

# 12 qirrali friz: krem panellar, qizil ramka, oval rasmlar, chiroqlar
q.append(cyl(R_CAN, FRIEZE_TOP - FRIEZE_BOT, (0, 0, (FRIEZE_BOT + FRIEZE_TOP) / 2), 'red', N, (0, 0, HALF)))
PW = 2 * R_CAN * math.sin(HALF)
for k in range(N):
    a = 2 * math.pi * k / N
    cz = (FRIEZE_BOT + FRIEZE_TOP) / 2
    hw, hh = PW / 2 - 0.14, (FRIEZE_TOP - FRIEZE_BOT) / 2 - 0.1
    c = 0.14  # qirqilgan burchaklar
    panel = [(-hw + c, cz - hh), (hw - c, cz - hh), (hw, cz - hh + c), (hw, cz + hh - c), (hw - c, cz + hh), (-hw + c, cz + hh),
             (-hw, cz + hh - c), (-hw, cz - hh + c)]
    q.append(face_poly(a, APO_CAN, panel, 'cream', 0.01))
    q.append(face_poly(a, APO_CAN, ellipse(1.15, 0.62, 24, 0, cz), 'red', 0.015))
    q.append(face_poly(a, APO_CAN, ellipse(1.02, 0.52, 24, 0, cz), 'gold', 0.018))
    q.extend(painting(a, APO_CAN, 0.92, 0.44, cz, 0.022, k))
    for i in range(16):  # oval atrofida chiroqlar
        t = 2 * math.pi * i / 16
        q.append(ball(0.03, face_pt(a, APO_CAN, 0.72 * math.cos(t), cz + 0.39 * math.sin(t), 0.03), 'ivory'))
    for s in (-1, 1):  # yon tomondagi qizil "jingalak" bo'rtmalar
        q.append(face_poly(a, APO_CAN, [(s * hw * 0.78 - 0.08, cz - 0.2), (s * hw * 0.78 + 0.08, cz - 0.2),
                                        (s * hw * 0.78 + 0.08, cz + 0.2), (s * hw * 0.78 - 0.08, cz + 0.2)][::s or 1], 'red', 0.016))
    # pastki va tepa qirradagi chiroqlar qatori
    for i in range(9):
        u = -PW / 2 + 0.15 + i * (PW - 0.3) / 8
        q.append(ball(0.032, face_pt(a, APO_CAN, u, FRIEZE_BOT + 0.02, 0.03), 'ivory'))
    # tepa: ravoqli tishli chet (qizil, krem hoshiya, chiroqlar) — ikki tomonlama, tom tomondan ham ko'rinadi
    arch = [(-PW / 2, FRIEZE_TOP - 0.02)] + [(PW / 2 * math.cos(math.pi - math.pi * i / 12), FRIEZE_TOP + 0.05 + 0.28 *
                                              math.sin(math.pi * i / 12)) for i in range(13)] + [(PW / 2, FRIEZE_TOP - 0.02)]
    arch = [arch[0]] + arch[1:-1] + [arch[-1]]
    arch_pts = [(u, v) for u, v in arch]
    q.append(face_poly(a, APO_CAN, [arch_pts[0], arch_pts[-1]] + arch_pts[-2:0:-1][::-1][::-1], 'red', 0.0, True))
    inner_arch = [(u * 0.9, FRIEZE_TOP + (v - FRIEZE_TOP) * 0.72) for u, v in arch_pts]
    q.append(face_poly(a, APO_CAN, [inner_arch[0], inner_arch[-1]] + inner_arch[-2:0:-1][::-1][::-1], 'cream', 0.01))
    for i in range(11):
        t = math.pi * (i + 1) / 12
        q.append(ball(0.032, face_pt(a, APO_CAN, PW / 2 * math.cos(math.pi - t), FRIEZE_TOP + 0.05 + 0.28 * math.sin(t), 0.03),
                      'ivory'))
for k in range(N):  # qirralardagi qizil pilyastrlar (tishli chet orasida uchli)
    a = 2 * math.pi * k / N + HALF
    c = Vector((math.cos(a), math.sin(a), 0)) * (R_CAN + 0.02)
    q.append(box((0.12, 0.2, FRIEZE_TOP - FRIEZE_BOT + 0.25), (c.x, c.y, (FRIEZE_BOT + FRIEZE_TOP) / 2 + 0.05), 'red_dark', (0, 0, a)))
    q.append(ball(0.06, (c.x, c.y, FRIEZE_TOP + 0.22), 'ivory'))
    q.append(limb((c.x, c.y, FRIEZE_BOT), (c.x * 0.99, c.y * 0.99, FRIEZE_BOT - 0.22), 0.06, 0.0, 'red_dark', 6))

# tom: qizil-krem yo'llar (24), tepada krem baraban, oltin yoqa va shar
ROOF = [(R_CAN * 0.97, FRIEZE_TOP), (3.0, FRIEZE_TOP + 0.55), (1.2, FRIEZE_TOP + 0.95), (0.5, FRIEZE_TOP + 1.08)]
q.extend(lathe(ROOF, None, 2 * N, ('red', 'cream'), HALF))
TZ = FRIEZE_TOP + 1.08
q.extend(lathe([(0.5, TZ), (0.48, TZ + 0.3)], None, 16, ('red', 'cream')))
q.append(cyl(0.58, 0.08, (0, 0, TZ + 0.34), 'gold', 16))
q.append(lathe([(0.5, TZ + 0.38), (0.36, TZ + 0.48), (0.12, TZ + 0.55)], 'cream', 16))
q.append(cyl(0.13, 0.07, (0, 0, TZ + 0.55), 'cream', 16))
q.append(cyl(0.06, 0.18, (0, 0, TZ + 0.66), 'gold', 8))
q.append(ball(0.17, (0, 0, TZ + 0.88), 'gold', 2, (1, 1, 1.15)))
q.append(cyl(0.04, 0.12, (0, 0, TZ + 1.08), 'gold', 8, r2=0.0))
rotor = join('rotor', q)

# ====================== SWING0..23: to'rli savatlar ======================
NSW = 24
R_HOOK = APO_CAN - 0.35
Z_HOOK = FRIEZE_BOT - 0.1
SEAT_Z = 0.75                 # savat tagi (tinch holatda)
L = SEAT_Z - Z_HOOK           # manfiy
BW, BD, BH = 0.62, 0.55, 0.5  # savat: eni (tangensial), chuqurligi (radial), balandligi
for k in range(NSW):
    a = 2 * math.pi * (k + 0.5) / NSW
    s = []
    # savat: qizil tag, to'rli devorlar (vertikal va gorizontal simlar), ichida o'rindiq
    s.append(box((BW, BD, 0.05), (0, 0, L + 0.025), 'red'))
    corners = [(-BW / 2, -BD / 2), (BW / 2, -BD / 2), (BW / 2, BD / 2), (-BW / 2, BD / 2)]
    for i in range(4):
        (x0, y0), (x1, y1) = corners[i], corners[(i + 1) % 4]
        for z in (L + 0.05, L + 0.25, L + BH):
            s.append(limb((x0, y0, z), (x1, y1, z), 0.012, 0.012, 'steel', 4))
        for j in range(5 if abs(x1 - x0) > 0.3 else 4):
            t = j / (5 if abs(x1 - x0) > 0.3 else 4)
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            s.append(limb((x, y, L + 0.05), (x, y, L + BH), 0.009, 0.009, 'steel', 4))
    s.append(box((BW - 0.1, 0.25, 0.06), (0, -0.1, L + 0.3), 'red'))
    s.append(box((BW - 0.1, 0.05, 0.25), (0, -BD / 2 + 0.06, L + 0.42), 'red'))
    # zanjirlar: savat burchaklaridan ilgakka (ikki nuqta), pastki qismi qizil g'ilofda
    for (cx, cy) in corners:
        top = Vector((cx * 0.6, cy * 0.3, 0.0))
        bot = Vector((cx, cy, L + BH))
        s.append(limb(bot, top, 0.009, 0.009, 'steel', 4))
        sl = bot.lerp(top, 0.45)
        s.append(limb(bot + (top - bot).normalized() * 0.05, sl, 0.018, 0.018, 'red', 6))
    s.append(limb((-BW * 0.3, 0, 0.0), (BW * 0.3, 0, 0.0), 0.02, 0.02, 'steel', 6))   # ilgak to'sini
    sw = join(f'swing{k}', s)
    sw.rotation_euler = (0, 0, a - math.pi / 2)   # lokal +Y — tashqariga
    sw.location = (math.cos(a) * R_HOOK, math.sin(a) * R_HOOK, Z_HOOK)
    sw.parent = rotor

objs = [o for o in scene.objects if o.type == 'MESH']
tris = sum(len(pg.vertices) - 2 for o in objs for pg in o.data.polygons)
bpy.context.view_layer.update()
top = max((o.matrix_world @ v.co).z for o in objs for v in o.data.vertices)
xmax = max(abs((o.matrix_world @ v.co).x) for o in objs for v in o.data.vertices)
print(f'FAMILY_SWINGER tris={tris} top={top:.2f} width={2 * xmax:.2f}')

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'FAMILY_SWINGER glb={OUT_GLB.stat().st_size // 1024} KB')

# ---------- Preview (savatlar tashqariga og'gan) ----------
for o in objs:
    if o.name.startswith('swing'):
        o.rotation_euler.x = math.radians(22)
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
for fname, loc, tgt in (('preview.png', (10.5, -15.0, 7.5), (0, 0, 3.6)),
                        ('preview_close.png', (2.2, -6.0, 3.2), (0, 0, 3.6))):
    cam.location = loc
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(PREVIEW_DIR / fname)
    bpy.ops.render.render(write_still=True)
    print('FAMILY_SWINGER preview', scene.render.filepath)

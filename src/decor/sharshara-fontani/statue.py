"""
Fontan haykali: boshida mevali savat ko'targan ayol (klassik marmar haykal). model.py dan chaqiriladi: build_statue(k, base_z, yaw).

Usul: tana — "skelet" (bo'g'inlar + suyaklar) ustiga Skin modifikatori (har bo'g'inga radius) + Subdivision → silliq, tirik shakl.
Ustiga: burmali, pastga kengaygan etak (lathe + burma to'lqini), bel bog'ichi, bosh (soch tugunchasi bilan),
ikki qo'l bilan ushlangan keng oval savat (ustida meva va uzum, chetidan osilgan shingillar),
o'ng yonida (tomoshabindan) yerga tushgan mato-tirgak — uzum barglari va shingillari bilan, boshi ortida savatdan tushgan mato.
Old tomoni −Y; yaw — Z o'qi atrofida burish (radian). Balandligi: tagidan savat ustigacha ~2.35 m.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

# ---------- skelet: bo'g'in → (x, y, z, radius) ----------
J = {
    'pelvis': (0.0, 0.0, 0.98, 0.15),
    'waist': (0.0, 0.015, 1.15, 0.1),
    'chest': (0.0, 0.0, 1.33, 0.13),
    'neck': (0.0, 0.02, 1.53, 0.05),
    'sh_r': (-0.17, 0.02, 1.46, 0.06), 'sh_l': (0.17, 0.02, 1.46, 0.06),
    'el_r': (-0.37, 0.02, 1.7, 0.046), 'el_l': (0.36, 0.02, 1.69, 0.046),
    'wr_r': (-0.3, 0.0, 1.98, 0.034), 'wr_l': (0.29, 0.0, 1.98, 0.034),
    'hp_r': (-0.09, 0.0, 0.92, 0.1), 'hp_l': (0.09, 0.0, 0.92, 0.1),
    # kontrapost: chap tizza biroz oldinga va ichkariga bukilgan, og'irlik o'ng oyoqda
    'kn_r': (-0.09, 0.0, 0.52, 0.068), 'kn_l': (0.06, -0.06, 0.53, 0.068),
    'an_r': (-0.09, 0.02, 0.12, 0.042), 'an_l': (0.07, -0.02, 0.13, 0.042),
    'ft_r': (-0.1, -0.11, 0.04, 0.04), 'ft_l': (0.09, -0.14, 0.05, 0.04),
}
BONES = [('pelvis', 'waist'), ('waist', 'chest'), ('chest', 'neck'), ('chest', 'sh_r'), ('chest', 'sh_l'),
         ('sh_r', 'el_r'), ('el_r', 'wr_r'), ('sh_l', 'el_l'), ('el_l', 'wr_l'),
         ('pelvis', 'hp_r'), ('pelvis', 'hp_l'), ('hp_r', 'kn_r'), ('kn_r', 'an_r'), ('an_r', 'ft_r'),
         ('hp_l', 'kn_l'), ('kn_l', 'an_l'), ('an_l', 'ft_l')]


def _apply_mods(ob):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


def _body(k, mat):
    names = list(J)
    me = bpy.data.meshes.new('body')
    me.from_pydata([J[n][:3] for n in names], [(names.index(a), names.index(b)) for a, b in BONES], [])
    ob = bpy.data.objects.new('body', me)
    k.scene.collection.objects.link(ob)
    ob.modifiers.new('skin', 'SKIN')
    for i, n in enumerate(names):
        r = J[n][3]
        sv = me.skin_vertices[0].data[i]
        # tana yonlama kengroq, old-orqa yupqaroq
        wide = {'pelvis': (1.35, 0.85), 'chest': (1.3, 0.8), 'waist': (1.15, 0.85)}.get(n, (1.0, 1.0))
        sv.radius = (r * wide[0], r * wide[1])
        sv.use_root = n == 'pelvis'
    sub = ob.modifiers.new('sub', 'SUBSURF')
    sub.levels = 2
    _apply_mods(ob)
    me.materials.append(k.mats[mat])
    return ob


def _skirt(k, mat, z_top=1.02, z_hem=0.28, rings=12, segs=40, base0=0.15, grow=0.17, fold0=0.05):
    """Etak: belda tor, pastga kengayadi; burmalar (to'lqin) pastga qarab chuqurlashadi; old tomoni oyoqqa yopishgan"""
    bm = bmesh.new()
    grid = []
    rnd = random.Random(3)
    phase = [rnd.uniform(0, 6.28) for _ in range(3)]
    for i in range(rings + 1):
        t = i / rings
        z = z_top + (z_hem - z_top) * t
        base = base0 + grow * t ** 1.3
        row = []
        for j in range(segs):
            a = 2 * math.pi * j / segs
            fold = (fold0 + 0.16 * t) * (math.sin(9 * a + phase[0]) * 0.6 + math.sin(5 * a + phase[1]) * 0.4)
            front = max(0.0, -math.sin(a))          # −Y (old) tomon: oyoqlarga yopishgan, kamroq kengaygan
            r = base * (1 + fold) * (1 - 0.22 * front * t)
            # etak pastki cheti oldinda biroz baland (oyoq ko'rinadi), orqada past
            zz = z + (0.06 * front - 0.03) * t ** 3
            row.append(bm.verts.new((r * math.cos(a), r * 0.85 * math.sin(a), zz)))
        grid.append(row)
    for i in range(rings):
        for j in range(segs):
            bm.faces.new([grid[i][j], grid[i][(j + 1) % segs], grid[i + 1][(j + 1) % segs], grid[i + 1][j]])
    # qalinlik — ichki tomoni ham ko'rinsin (pastdan qaralganda)
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.025)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return k.obj('skirt', bm, mat)


def _lathe(k, profile, mat, segs=32, sx=1.0, sy=1.0, z0=0.0):
    bm = bmesh.new()
    rings = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        rings.append([bm.verts.new((r * math.cos(a) * sx, r * math.sin(a) * sy, z0 + z)) for r, z in profile])
    n = len(profile)
    for i in range(segs):
        A, Bv = rings[i], rings[(i + 1) % segs]
        for j in range(n - 1):
            bm.faces.new([A[j], Bv[j], Bv[j + 1], A[j + 1]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return k.obj('lathe', bm, mat)


def _drape(k, pts, w, t, mat):
    """Tik mato bo'lagi: o'rta chizig'i nuqtalari bo'ylab eni w, qalinligi t (yon tomonga burmali)"""
    bm = bmesh.new()
    rows = []
    for i, (x, y, z) in enumerate(pts):
        wave = 0.03 * math.sin(i * 1.7)
        rows.append([bm.verts.new((x + dx, y + wave * (1 if dx > 0 else -1) + dy, z))
                     for dx, dy in ((-w / 2, -t / 2), (w / 2, -t / 2), (w / 2, t / 2), (-w / 2, t / 2))])
    for i in range(len(rows) - 1):
        for j in range(4):
            bm.faces.new([rows[i][j], rows[i][(j + 1) % 4], rows[i + 1][(j + 1) % 4], rows[i + 1][j]])
    bm.faces.new(rows[0][::-1])
    bm.faces.new(rows[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return k.obj('drape', bm, mat)


def build_statue(k, base_z, yaw=0.0, mat='marble', mat2='marble_d'):
    rnd = random.Random(11)
    parts = []
    # tagidagi kvadrat poydevorcha
    parts.append(k.box((0.62, 0.62, 0.1), (0, 0, 0.05), mat2))
    parts.append(k.box((0.54, 0.54, 0.06), (0, 0, 0.13), mat))
    Z0 = 0.16
    body = _body(k, mat)
    body.data.transform(Matrix.Translation(Vector((0, 0, Z0))))
    parts.append(body)
    parts.append(_skirt(k, mat2, z_top=Z0 + 1.03, z_hem=Z0 + 0.3))
    # ko'kragi yopiq: yelkadan belgacha mato (ko'ylak ustki qismi)
    parts.append(_lathe(k, [(0.0, 1.0), (0.15, 1.0), (0.13, 1.1), (0.15, 1.24), (0.155, 1.36), (0.14, 1.46), (0.08, 1.52),
                            (0.0, 1.52)], mat2, segs=24, sx=1.12, sy=0.8, z0=Z0))
    # beldagi qiya bog'ich (mato o'ramasi) va son ustidagi tugun
    sash = k.cyl(0.185, 0.04, (0, 0.0, Z0 + 1.03), mat2, segs=24)
    sash.rotation_euler = (0.0, math.radians(-9), 0.0)
    parts.append(sash)
    parts.append(k.ball(0.06, (0.15, -0.07, Z0 + 0.98), mat2, sub=2, scale=(1.0, 0.8, 1.4)))
    # etak pastidagi qisqa jingalak qavat (ruffle): kengaygan to'lqinli halqa
    parts.append(_skirt(k, mat, z_top=Z0 + 0.42, z_hem=Z0 + 0.26, rings=3, segs=48, base0=0.27, grow=0.08, fold0=0.12))
    # bosh: biroz pastga egilgan, ortida soch tugunchasi, peshonada soch to'lqini
    hz = Z0 + 1.66
    parts.append(k.ball(0.095, (0, -0.01, hz), mat, sub=3, scale=(0.88, 1.0, 1.18)))
    parts.append(k.ball(0.085, (0, 0.035, hz + 0.04), mat2, sub=2, scale=(1.05, 1.0, 1.0)))      # soch
    parts.append(k.ball(0.06, (0, 0.1, hz + 0.0), mat2, sub=2))                                   # tuguncha
    parts.append(k.ball(0.018, (0, -0.098, hz - 0.01), mat, sub=1, scale=(0.7, 1.0, 1.3)))       # burun
    # qo'l panjalari — savat chetida
    for sx in (-1, 1):
        parts.append(k.ball(0.045, (sx * 0.33, 0.0, Z0 + 2.03), mat, sub=2, scale=(0.8, 1.0, 1.3)))
    # savat: keng oval tovoq, chetida to'qilgan naqsh, ustida meva uyumi, chetidan osilgan uzum shingillari
    SZ = Z0 + 1.97
    parts.append(_lathe(k, [(0.0, 0.0), (0.16, 0.0), (0.27, 0.06), (0.32, 0.2), (0.3, 0.21), (0.26, 0.12), (0.0, 0.12)],
                        mat2, segs=28, sx=1.2, sy=0.95, z0=SZ))
    for j in range(14):
        a = 2 * math.pi * j / 14
        parts.append(k.ball(0.03, (0.31 * 1.2 * math.cos(a), 0.31 * 0.95 * math.sin(a), SZ + 0.2), mat, sub=1))
    for _ in range(16):
        a, r = rnd.uniform(0, 6.28), rnd.uniform(0, 0.3)
        parts.append(k.ball(rnd.uniform(0.06, 0.09), (r * 1.1 * math.cos(a), r * 0.8 * math.sin(a), SZ + 0.2 + (0.3 - r) * 0.35),
                            mat, sub=1))
    # boshi ortida savatdan tushgan mato (haykalni orqadan o'rab turadi)
    parts.append(_drape(k, [(0.0, 0.16, SZ + 0.02 - i * 0.12) for i in range(9)], 0.5, 0.05, mat2))
    # o'ng yondagi (tomoshabindan) mato-tirgak: savatdan yergacha, uzum barglari va shingillari bilan
    pts = [(0.3 + 0.04 * math.sin(i * 0.6), 0.1, SZ + 0.05 - i * (SZ + 0.05 - 0.12) / 14) for i in range(15)]
    parts.append(_drape(k, pts, 0.2, 0.16, mat2))
    for i in range(10):
        z = 0.35 + i * 0.17
        x = 0.3 + rnd.uniform(-0.06, 0.08)
        parts.append(k.ball(0.075, (x + 0.04, -0.01, Z0 + z), mat, sub=2, scale=(1.2, 0.3, 1.0)))         # barg
        if i % 3 == 1:
            for g in range(5):
                parts.append(k.ball(0.028, (x + 0.02 + rnd.uniform(-0.03, 0.03), -0.04, Z0 + z - 0.06 - g * 0.035), mat, sub=1))
    # hammasini joyiga: Z0 asosida base_z ga ko'tarish va yaw ga burish
    M = Matrix.Translation(Vector((0, 0, base_z))) @ Matrix.Rotation(yaw, 4, 'Z')
    for o in parts:
        o.matrix_world = M @ o.matrix_world
    return parts

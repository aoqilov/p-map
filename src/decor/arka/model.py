"""
Arka — sharshara boshidagi yarim aylana g'isht arkada (rasm: foydalanuvchi panoramasi, "Central Park").

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/decor/arka/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png, preview_back.png

Tuzilish (bitta `base` obyekt, animatsiyasiz): yoy bo'ylab (botiq tomoni −Y — maydonga, orqasi +Y — sharsharaga):
ikki chetida qalin g'isht ustun (pilon), o'rtada 4 ta ingichka g'isht ustun (asos va kapitel bilan), ular orasida 5 ta uchli
(gotik) ravoq, ravoqlar ustida g'isht devor (tepa chizig'i o'rtada pastroq), ustunlar ustida o'yma rozetkalar,
ravoqlar ostida pastki qismida cho'yan panjara (X naqsh), oldida tosh plitali pol.
Model markazi — yoy o'rtasi (orqa devor). Asl o'lcham: eni ~10.6 m, chuqurligi ~5 m, balandligi 5.4 m.
"""
import math
import bmesh
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from blender_kit import Kit  # noqa: E402

PALETTE = {
    'brick': (0.62, 0.36, 0.22), 'brick2': (0.7, 0.44, 0.28), 'mortar': (0.5, 0.3, 0.19), 'stone_l': (0.78, 0.62, 0.48),
    'iron': (0.12, 0.12, 0.13), 'flag': (0.62, 0.5, 0.46), 'flag2': (0.55, 0.44, 0.4), 'drystone': (0.55, 0.42, 0.32),
    'granite': (0.72, 0.7, 0.66),
}
k = Kit(PALETTE)
rnd = random.Random(5)
p = []

R = 7.25                    # yoy radiusi
PHI = math.radians(43.6)    # yarim burchak (vatar ~10 m, chuqurlik ~2 m)
L = 2 * R * PHI             # yoy uzunligi
T = 0.5                     # devor qalinligi
SPRING = 3.0                # ravoq boshlanishi
PIER_W, COL_W = 1.0, 0.42
N_OPEN = 5
OPEN_W = (L - 2 * PIER_W - 4 * COL_W) / N_OPEN


def frame(s):
    """Yoy bo'ylab masofa s (o'rtadan, chapdan o'ngga) → (x, y, burilish). Mahalliy X — urinma, −Y — maydon tomoni"""
    a = s / R
    return R * math.sin(a), R * math.cos(a) - R, -a


def bake(obj):
    """Obyektning o'z burilishi/joyini meshga singdirish (beam kabi) — keyin local() uni yoyga qo'ya oladi"""
    obj.data.transform(obj.matrix_basis)
    obj.matrix_basis.identity()
    return obj


def local(obj, s):
    """Mahalliy koordinatada (X — urinma, Y — yoyga perpendikulyar) yasalgan obyektni yoydagi s nuqtaga qo'yish"""
    x, y, rz = frame(s)
    obj.rotation_euler = (0, 0, rz)
    obj.location = (x, y, 0)
    return obj


def brick_stack(s, w, d, z0, z1, course=0.24):
    """G'isht qatorlari: navbatma-navbat ikki rang (uzoqdan g'isht teksturasi kabi)"""
    res = []
    n = max(1, round((z1 - z0) / course))
    h = (z1 - z0) / n
    for i in range(n):
        res.append(local(k.box((w + (0.02 if i % 2 else 0), d + (0.02 if i % 2 else 0), h * 0.96),
                               (0, 0, z0 + h * (i + 0.5)), 'brick' if i % 2 else 'brick2'), s))
    return res


# ---------- tayanchlar: pilonlar va ustunlar ----------
TOP_END, TOP_MID = 5.0, 4.4


def wall_top(s):
    return TOP_MID + (TOP_END - TOP_MID) * (abs(s) / (L / 2)) ** 2


supports = [-L / 2 + PIER_W / 2]
x = -L / 2 + PIER_W + OPEN_W
for i in range(4):
    supports.append(x + COL_W / 2)
    x += COL_W + OPEN_W
supports.append(L / 2 - PIER_W / 2)
for i, s in enumerate(supports):
    pier = i in (0, len(supports) - 1)
    if pier:
        top = TOP_END + 0.35
        p.extend(brick_stack(s, PIER_W, T + 0.3, 0.0, top))
        p.append(local(k.box((PIER_W + 0.12, T + 0.42, 0.12), (0, 0, top + 0.06), 'stone_l'), s))
        p.append(local(k.box((PIER_W + 0.1, T + 0.4, 0.1), (0, 0, SPRING + 0.4), 'stone_l'), s))   # karniz
    else:
        p.append(local(k.box((0.58, T + 0.1, 0.3), (0, 0, 0.15), 'stone_l'), s))                    # asos
        p.extend(brick_stack(s, COL_W, T - 0.05, 0.3, SPRING - 0.2))
        p.append(local(k.box((0.58, T + 0.1, 0.2), (0, 0, SPRING - 0.1), 'stone_l'), s))            # kapitel
        top = wall_top(s)
        p.append(local(k.box((COL_W + 0.1, T, top - SPRING + 0.02), (0, 0, (SPRING + top) / 2), 'brick'), s))  # ustun ustidagi devor
        # ustun ustida o'yma rozetka (old va orqa tomonda)
        for side in (-1, 1):
            p.append(local(k.disc_y(0.24, side * (T / 2 + 0.02), SPRING + 0.75, 0, 0.05, 'stone_l', segs=16), s))
            p.append(local(k.disc_y(0.13, side * (T / 2 + 0.05), SPRING + 0.75, 0, 0.05, 'mortar', segs=12), s))
            p.append(local(k.ball(0.07, (0, side * (T / 2 + 0.06), SPRING + 0.75), 'stone_l', sub=1), s))


# ---------- ravoqlar ustidagi devor (har ochiq joy uchun uchli ravoq kesimi) ----------
def arch_wall(s_mid, w):
    r = w * 0.75
    pts = []
    n = 8
    t_end = math.acos(1 - (w / 2) / r)
    for i in range(n + 1):                          # chap yoy: pastdan cho'qqigacha
        t = t_end * i / n
        pts.append((-w / 2 + r * (1 - math.cos(t)), SPRING + r * math.sin(t)))
    for i in range(n - 1, -1, -1):                  # o'ng yoy: cho'qqidan pastga
        t = t_end * i / n
        pts.append((w / 2 - r * (1 - math.cos(t)), SPRING + r * math.sin(t)))
    e = 0.02
    # kontur: o'ng-tepa → chap-tepa → chap tag → ravoq bo'ylab → o'ng tag
    poly = [(w / 2 + e, wall_top(s_mid + w / 2)), (-w / 2 - e, wall_top(s_mid - w / 2))] + \
        [(x0, z) for x0, z in sorted(pts, key=lambda q: q[0])]
    ob = k.prism_y(poly, -T / 2, T / 2, 'brick')
    res = [local(ob, s_mid)]
    # g'isht qatorlarini bildiruvchi ingichka chiziqlar (old va orqa yuzada)
    for zz in [SPRING + 0.2 + 0.24 * j for j in range(10)]:
        if zz > wall_top(s_mid) - 0.1:
            break
        for side in (-1, 1):
            if zz > SPRING + w * 0.7:            # ravoq cho'qqisidan yuqori — to'liq eni
                res.append(local(k.box((w + 0.02, 0.02, 0.025), (0, side * (T / 2 + 0.005), zz), 'mortar'), s_mid))
    # ravoq hoshiyasi (ichki chetida ochroq tosh)
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        res.append(local(bake(k.beam((a[0], -T / 2 - 0.02, a[1]), (b[0], -T / 2 - 0.02, b[1]), 0.06, 0.08, 'stone_l')), s_mid))
    return res


for i in range(N_OPEN):
    s0 = supports[i] + (PIER_W if i == 0 else COL_W) / 2
    s1 = supports[i + 1] - (PIER_W if i + 1 == len(supports) - 1 else COL_W) / 2
    s_mid, w = (s0 + s1) / 2, s1 - s0
    p.extend(arch_wall(s_mid, w + 0.04))
    # pastki cho'yan panjara (X naqsh)
    fz0, fz1 = 0.15, 1.05
    p.append(local(k.box((w, 0.04, 0.04), (0, 0, fz1), 'iron'), s_mid))
    p.append(local(k.box((w, 0.04, 0.04), (0, 0, fz0), 'iron'), s_mid))
    for j in range(3):
        xa = -w / 2 + w * j / 3
        xb = xa + w / 3
        p.append(local(bake(k.beam((xa, 0, fz0), (xb, 0, fz1), 0.03, 0.03, 'iron')), s_mid))
        p.append(local(bake(k.beam((xb, 0, fz0), (xa, 0, fz1), 0.03, 0.03, 'iron')), s_mid))
# devor tepasidagi tosh qopqoq (yoy bo'ylab bo'laklar)
for i in range(24):
    sa = -L / 2 + PIER_W + (L - 2 * PIER_W) * i / 24
    sb = -L / 2 + PIER_W + (L - 2 * PIER_W) * (i + 1) / 24
    sm = (sa + sb) / 2
    p.append(local(k.box((sb - sa + 0.03, T + 0.08, 0.1), (0, 0, wall_top(sm) + 0.03), 'stone_l'), sm))

# ---------- oldidagi tosh plitali pol ----------
xe, ye, _ = frame(L / 2)
FRONT_Y = ye - 2.8
pts = [(R * math.sin(a) * (R - 0.3) / R, (R - 0.3) * math.cos(a) - R) for a in
       [-PHI + 2 * PHI * i / 20 for i in range(21)]]
pts = pts[::-1] + [(-xe - 0.3, FRONT_Y), (xe + 0.3, FRONT_Y)]


def slab(poly, z0, z1, mat):
    bm = bmesh.new()
    bot = [bm.verts.new((x0, y0, z0)) for x0, y0 in poly]
    top = [bm.verts.new((x0, y0, z1)) for x0, y0 in poly]
    bm.faces.new(top)
    bm.faces.new(bot[::-1])
    for i in range(len(poly)):
        j = (i + 1) % len(poly)
        bm.faces.new([bot[i], bot[j], top[j], top[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return k.obj('slab', bm, mat)


p.append(slab(pts, 0.0, 0.2, 'flag'))
# alohida plitalar (notekis, ikki rang)
for _ in range(26):
    xx = rnd.uniform(-xe + 0.6, xe - 0.6)
    yy = rnd.uniform(FRONT_Y + 0.4, -0.6)
    if yy > R * math.cos(math.asin(max(-1, min(1, xx / R)))) - R - 0.5:
        continue
    p.append(k.box((rnd.uniform(0.5, 0.9), rnd.uniform(0.4, 0.7), 0.02), (xx, yy, 0.205), 'flag2', rot=(0, 0, rnd.uniform(0, 1.5))))

k.finish('ARKA', p, HERE, [
    ('preview.png', (2.0, -14.0, 3.0), (0, -1.0, 2.6)),
    ('preview_back.png', (-9.0, 9.0, 7.0), (0, -1.0, 2.0)),
])

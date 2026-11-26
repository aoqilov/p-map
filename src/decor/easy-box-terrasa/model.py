"""
"EASY Box" kafesining tashqi o'tirish zonasi (terrasa) — foydalanuvchi fotosurati bo'yicha:
past granit supa, chetlarida to'q jigarrang yog'och tuvaklar (ichida yashil butalar), dumaloq stollar atrofida
to'qilgan (rattan) stullar, ustida oq-krem kvadrat soyabonlar (markaziy ustunli). Kirish oldida skameyka va rangli
axlat qutilari (qizil, sariq, yashil).

Shakli — shape.json (park metrlarida ko'pburchak; #editor da nuqtalarini sudrab o'zgartirish mumkin): bir qirrasi
EASY Box binosining janubi-sharqiy devori bo'ylab (u yerda tuvak yo'q). Koordinatalar park o'qlarida (config bearing 180 →
Blender X — sharq, Y — shimol), origin — nuqtalar o'rtachasi (config.ts ham shunday hisoblaydi).

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/decor/easy-box-terrasa/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png, preview_top.png
"""
import json
import math
import random
import sys
from pathlib import Path

import bmesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from blender_kit import Kit  # noqa: E402

random.seed(5)
PALETTE = {
    'granite': (0.5, 0.5, 0.52), 'deck': (0.62, 0.6, 0.57), 'planter': (0.2, 0.14, 0.1), 'planter_l': (0.28, 0.2, 0.14),
    'bush': (0.22, 0.45, 0.18), 'bush2': (0.3, 0.52, 0.22), 'canvas': (0.93, 0.9, 0.82), 'pole': (0.85, 0.85, 0.85),
    'table': (0.12, 0.12, 0.13), 'rattan': (0.55, 0.38, 0.22), 'wood': (0.85, 0.55, 0.2), 'iron': (0.08, 0.08, 0.09),
    'bin_r': (0.85, 0.12, 0.1), 'bin_y': (0.95, 0.75, 0.1), 'bin_g': (0.15, 0.65, 0.2),
}
k = Kit(PALETTE)
p = []

# ---------- shakl: EASY Box izining janubi-sharqiy qirrasi (S → E burchak) bo'ylab ----------
S, E = (-12.13, 30.87), (-3.14, 39.96)                 # building-131 izining janubiy va sharqiy burchaklari (park.json)
L = math.hypot(E[0] - S[0], E[1] - S[1])
DIR = ((E[0] - S[0]) / L, (E[1] - S[1]) / L)            # devor bo'ylab
NRM = (DIR[1], -DIR[0])                                 # tashqariga (janubi-sharq)


def pt(along, out):
    return (S[0] + DIR[0] * along + NRM[0] * out, S[1] + DIR[1] * along + NRM[1] * out)


TRI_PARK = [tuple(v) for v in json.loads((HERE / 'shape.json').read_text(encoding='utf-8'))['poly']]
N = len(TRI_PARK)
AT = (round(sum(v[0] for v in TRI_PARK) / 3, 2), round(sum(v[1] for v in TRI_PARK) / 3, 2))
TRI = [(x - AT[0], y - AT[1]) for x, y in TRI_PARK]
print('TERRASA at =', AT, 'nuqtalar =', N)

PH = 0.22                                               # supa balandligi


def slab(pts, z0, z1, mat):
    bm = bmesh.new()
    bot = [bm.verts.new((x, y, z0)) for x, y in pts]
    top = [bm.verts.new((x, y, z1)) for x, y in pts]
    bm.faces.new(top)
    bm.faces.new(bot[::-1])
    n = len(pts)
    for i in range(n):
        bm.faces.new([bot[i], bot[(i + 1) % n], top[(i + 1) % n], top[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return k.obj('slab', bm, mat)


def inset(pts, d):
    """Uchburchakni ichkariga d ga qisqartirish (markazga qarab, taxminiy)"""
    cx = sum(x for x, _ in pts) / len(pts)
    cy = sum(y for _, y in pts) / len(pts)
    out = []
    for x, y in pts:
        dx, dy = x - cx, y - cy
        r = math.hypot(dx, dy)
        f = max(0.0, (r - d * 2.0) / r)
        out.append((cx + dx * f, cy + dy * f))
    return out


def inside(q, pts, margin):
    """Nuqta ko'pburchak ichida va har bir qirradan kamida margin uzoqda"""
    c = False
    n = len(pts)
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        if (y0 > q[1]) != (y1 > q[1]) and q[0] < x0 + (q[1] - y0) * (x1 - x0) / (y1 - y0):
            c = not c
    if not c:
        return False
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        ex, ey = x1 - x0, y1 - y0
        t = max(0.0, min(1.0, ((q[0] - x0) * ex + (q[1] - y0) * ey) / (ex * ex + ey * ey)))
        if math.hypot(x0 + ex * t - q[0], y0 + ey * t - q[1]) < margin:
            return False
    return True


if sum(TRI[i][0] * TRI[(i + 1) % N][1] - TRI[(i + 1) % N][0] * TRI[i][1] for i in range(N)) < 0:
    TRI.reverse()

# ---------- granit supa ----------
p.append(slab(TRI, 0.0, PH, 'granite'))
p.append(slab(inset(TRI, 0.12), PH, PH + 0.03, 'deck'))

# ---------- tashqi qirralarda yog'och tuvaklar (devor tomonida yo'q); kirish — uzun qirra o'rtasida ----------
_wm = pt(6.75, 0.25)
_wm = (_wm[0] - AT[0], _wm[1] - AT[1])                  # devor qirrasining o'rtasi (model koordinatasida)
wall_edge = min(range(N), key=lambda i: math.hypot((TRI[i][0] + TRI[(i + 1) % N][0]) / 2 - _wm[0],
                                                   (TRI[i][1] + TRI[(i + 1) % N][1]) / 2 - _wm[1]))
PW, PHT = 0.7, 0.85                                       # tuvak eni, balandligi
entrances = []
for i in range(N):
    if i == wall_edge:
        continue
    (x0, y0), (x1, y1) = TRI[i], TRI[(i + 1) % N]
    el = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / el, (y1 - y0) / el
    nx, ny = uy, -ux                                      # CCW → tashqi normal
    rot = math.atan2(uy, ux)
    long_edge = el > 9
    gap = (el / 2 - 1.0, el / 2 + 1.0) if long_edge else None
    if gap:
        entrances.append(((x0 + x1) / 2 + nx * 1.4, (y0 + y1) / 2 + ny * 1.4, rot))
    s = 0.9
    while s < el - 0.9:
        seg = min(1.8, el - 0.9 - s)
        a, b = s, s + seg
        if gap and b > gap[0] and a < gap[1]:
            if a < gap[0]:
                b = gap[0]
            else:
                s = gap[1]
                continue
        if b - a > 0.4:
            m = (a + b) / 2
            cx, cy = x0 + ux * m - nx * PW / 2, y0 + uy * m - ny * PW / 2
            p.append(k.box((b - a - 0.06, PW, PHT), (cx, cy, PH + PHT / 2), 'planter', rot=(0, 0, rot)))
            for j in range(3):   # gorizontal taxtalar chizig'i
                p.append(k.box((b - a - 0.04, PW + 0.02, 0.03), (cx, cy, PH + 0.2 + j * 0.25), 'planter_l', rot=(0, 0, rot)))
            for j in range(max(1, int((b - a) / 0.6))):
                t = a + 0.3 + j * 0.6
                p.append(k.ball(random.uniform(0.32, 0.42), (x0 + ux * t - nx * PW / 2, y0 + uy * t - ny * PW / 2,
                                                             PH + PHT + 0.25), random.choice(('bush', 'bush2')), sub=1,
                                scale=(1.1, 1.0, 0.9)))
        s = b + 0.06


# ---------- stollar, stullar, soyabonlar ----------
def umbrella(x, y, size=3.0, h=2.75):
    parts = [k.cyl(0.05, h, (x, y, PH + h / 2), 'pole', segs=8),
             k.box((0.5, 0.5, 0.12), (x, y, PH + 0.06), 'iron')]
    bm = bmesh.new()
    s = size / 2
    rim = [bm.verts.new((x + dx * s, y + dy * s, PH + h - 0.45)) for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    top = bm.verts.new((x, y, PH + h))
    for i in range(4):
        bm.faces.new([rim[i], rim[(i + 1) % 4], top])
    bm.faces.new(rim[::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(k.obj('canvas', bm, 'canvas'))
    for dx, dy, w, d in ((0, -1, size, 0.04), (0, 1, size, 0.04), (-1, 0, 0.04, size), (1, 0, 0.04, size)):   # osilgan hoshiya
        parts.append(k.box((w, d, 0.22), (x + dx * s, y + dy * s, PH + h - 0.55), 'canvas'))
    return parts


def table_set(x, y, chairs=4):
    parts = [k.cyl(0.38, 0.04, (x, y, PH + 0.74), 'table', segs=14), k.cyl(0.04, 0.72, (x, y, PH + 0.37), 'iron', segs=6)]
    a0 = random.uniform(0, math.pi / 2)
    for i in range(chairs):
        a = a0 + 2 * math.pi * i / chairs
        cx, cy = x + 0.75 * math.cos(a), y + 0.75 * math.sin(a)
        parts.append(k.box((0.44, 0.44, 0.06), (cx, cy, PH + 0.46), 'rattan', rot=(0, 0, a)))
        bx, by = x + 0.97 * math.cos(a), y + 0.97 * math.sin(a)
        parts.append(k.box((0.06, 0.44, 0.45), (bx, by, PH + 0.7), 'rattan', rot=(0, 0, a)))
        for lx, ly in ((-0.18, -0.18), (0.18, 0.18), (-0.18, 0.18), (0.18, -0.18)):
            parts.append(k.box((0.03, 0.03, 0.44), (cx + lx, cy + ly, PH + 0.22), 'iron'))
    return parts


# stol joylari: devor bo'ylab va uchiga qarab, tuvaklardan uzoqda
spots = []
for along in [1.6 + 3.0 * i for i in range(12)]:
    for out in [2.0 + 3.0 * j for j in range(8)]:
        q = pt(along, out)
        q = (q[0] - AT[0], q[1] - AT[1])
        if inside(q, TRI, 1.5):
            spots.append(q)
for i, (x, y) in enumerate(spots):
    p += table_set(x, y, 4 if i % 3 else 2)
    p += umbrella(x, y, 2.8 if i % 2 else 3.2)

# ---------- kirish oldida skameyka va axlat qutilari ----------
for ex, ey, rot in entrances:
    c, s_ = math.cos(rot), math.sin(rot)
    for off in (-2.2, 2.2):
        bx, by = ex + c * off, ey + s_ * off
        for j in range(3):
            p.append(k.box((1.9, 0.12, 0.05), (bx + -s_ * (j * 0.13 - 0.13), by + c * (j * 0.13 - 0.13), 0.46), 'wood',
                           rot=(0, 0, rot)))
        for lo in (-0.8, 0.8):
            p.append(k.box((0.08, 0.45, 0.46), (bx + c * lo, by + s_ * lo, 0.23), 'iron', rot=(0, 0, rot)))
    bx, by = ex + c * 3.9, ey + s_ * 3.9
    for j, m in enumerate(('bin_r', 'bin_y', 'bin_g')):
        o = -0.27 + 0.27 * j
        p.append(k.box((0.24, 0.3, 0.6), (bx + c * o, by + s_ * o, 0.36), m, rot=(0, 0, rot)))
    p.append(k.box((0.85, 0.36, 0.05), (bx, by, 0.9), 'iron', rot=(0, 0, rot)))

k.finish('TERRASA', p, HERE, [
    ('preview.png', (TRI[1][0] + 8, TRI[1][1] - 6, 7.0), (0, 0, 1.0)),
    ('preview_top.png', (0, -0.1, 22.0), (0, 0, 0)),
])

"""
Mashg'ulot (workout) maydoni — foydalanuvchi fotosuratlari bo'yicha:
bordo rezina qoplama, chetlari va o'rtasidagi uzun yo'lak — to'q yashil rezina; sariq ustunli turnik/brusya
majmualari (ustida qora "rukoxod" narvonlari, ustunlar orasida qora turniklar), qora shved devorlari, qora U-shakl
brusyalar; yo'lka tomonida sariq ustunli yog'och skameykalar va axlat qutilari, qora fonar ustunlari.
Sharqiy uzun qirra — park chegarasidagi bino devori (firuza mural + sariq bo'yalgan qism), shimoliy keng uchi —
oq reklama bannerlari (sariq ustunlarda), janubiy tor uchi — kirish.

Shakli — shape.json (park metrlarida to'rtburchak; #editor da nuqtalarini sudrab o'zgartirish mumkin, keyin skript
qayta ishga tushiriladi). Eng qisqa qirra — kirish, unga qarama-qarshisi — bannerlar, sharqdagi yon qirra — devor.
Koordinatalar park o'qlarida (config bearing 180 → Blender X — sharq, Y — shimol), origin — nuqtalar o'rtachasi.

Ishga tushirish (loyiha ildizidan):
    D:/blender-program/blender.exe -b --factory-startup -P src/decor/mashgulot-maydoni/model.py [-- <preview_papka>]
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

random.seed(7)
PALETTE = {
    'rubber': (0.42, 0.13, 0.15), 'rubber_g': (0.1, 0.19, 0.17), 'curb': (0.62, 0.62, 0.6), 'line': (0.9, 0.9, 0.85),
    'yellow': (0.98, 0.76, 0.05), 'black': (0.06, 0.06, 0.07), 'wood': (0.4, 0.26, 0.16),
    'teal': (0.1, 0.72, 0.62), 'pink': (0.92, 0.15, 0.5), 'green': (0.35, 0.75, 0.25), 'purple': (0.4, 0.25, 0.7),
    'navy': (0.1, 0.12, 0.2), 'wall_y': (0.95, 0.68, 0.12), 'roof': (0.22, 0.16, 0.12),
    'banner': (0.94, 0.94, 0.94), 'ad_g': (0.2, 0.65, 0.35), 'ad_b': (0.15, 0.4, 0.85), 'ad_r': (0.85, 0.25, 0.3),
    'ad_t': (0.1, 0.6, 0.65),
}
k = Kit(PALETTE)
p = []

PARK = [tuple(v) for v in json.loads((HERE / 'shape.json').read_text(encoding='utf-8'))['poly']]
N = len(PARK)
assert N == 4, "shape.json — 4 ta nuqta bo'lishi kerak (kirish, ikki yon, bannerlar)"
AT = (round(sum(v[0] for v in PARK) / N, 2), round(sum(v[1] for v in PARK) / N, 2))
POLY = [(x - AT[0], y - AT[1]) for x, y in PARK]
if sum(POLY[i][0] * POLY[(i + 1) % N][1] - POLY[(i + 1) % N][0] * POLY[i][1] for i in range(N)) < 0:
    POLY.reverse()                                       # CCW
print('MASHGULOT at =', AT)

# ---------- maydon o'qlari: kirish (eng qisqa qirra) → bannerlar ----------
elen = [math.dist(POLY[i], POLY[(i + 1) % N]) for i in range(N)]
e0 = min(range(N), key=lambda i: elen[i])
P0, P1, P2, P3 = (POLY[(e0 + j) % N] for j in range(4))  # P0→P1 kirish, P1→P2 yon, P2→P3 bannerlar, P3→P0 yon


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


# yon qirralar: SA(t) = P0→P3, SB(t) = P1→P2; devor — sharqdagisi (park chegarasi)
SA = lambda t: lerp(P0, P3, t)                           # noqa: E731
SB = lambda t: lerp(P1, P2, t)                           # noqa: E731
WALL_IS_B = (P1[0] + P2[0]) > (P0[0] + P3[0])
WALL = SB if WALL_IS_B else SA
PATH = SA if WALL_IS_B else SB
LEN = math.dist(lerp(P0, P1, 0.5), lerp(P3, P2, 0.5))


def at(t, s):
    """t — kirishdan bannerlarga (0..1), s — o'rta chiziqdan devorga (+) yoki yo'lka tomonga (−), metr"""
    w, q = WALL(t), PATH(t)
    m = lerp(q, w, 0.5)
    d = math.dist(q, w)
    return (m[0] + (w[0] - q[0]) / d * s, m[1] + (w[1] - q[1]) / d * s)


def half(t):
    return math.dist(WALL(t), PATH(t)) / 2


def ang(t):
    """Ko'ndalang yo'nalish burchagi (yo'lkadan devorga)"""
    w, q = WALL(t), PATH(t)
    return math.atan2(w[1] - q[1], w[0] - q[0])


def along_ang(t):
    a, b = at(max(0, t - 0.01), 0), at(min(1, t + 0.01), 0)
    return math.atan2(b[1] - a[1], b[0] - a[0])


def tt(m):
    """Kirishdan m metr → t"""
    return m / LEN


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
    """Qavariq CCW ko'pburchakni har bir qirradan d ga ichkariga surish"""
    lines = []
    n = len(pts)
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        el = math.hypot(x1 - x0, y1 - y0)
        nx, ny = -(y1 - y0) / el, (x1 - x0) / el            # ichki normal (CCW)
        lines.append(((x0 + nx * d, y0 + ny * d), (x1 - x0, y1 - y0)))
    out = []
    for i in range(n):
        (a, u), (b, v) = lines[i - 1], lines[i]
        den = u[0] * v[1] - u[1] * v[0]
        s = ((b[0] - a[0]) * v[1] - (b[1] - a[1]) * v[0]) / den
        out.append((a[0] + u[0] * s, a[1] + u[1] * s))
    return out


def post(x, y, h, r=0.06, cap=True):
    parts = [k.cyl(r, h, (x, y, FL + h / 2), 'yellow', segs=8)]
    if cap:
        parts.append(k.cyl(r + 0.012, 0.12, (x, y, FL + h - 0.06), 'black', segs=8))
    return parts


def bar(a, b, z, mat='black', r=0.022):
    """Gorizontal quvur a → b (balandligi z, poldan)"""
    length = math.dist(a, b)
    rot = (0, math.pi / 2, math.atan2(b[1] - a[1], b[0] - a[0]))
    return k.cyl(r, length, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, FL + z), mat, segs=6, rot=rot)


# ---------- qoplama: chetida to'q yashil hoshiya, ichi bordo, o'rtasida to'q yashil yo'lak ----------
FL = 0.16                                                # pol sathi — xaritadagi yo'l plitkasidan (0.12) baland
p.append(slab(POLY, 0.0, FL - 0.02, 'rubber_g'))
p.append(slab(inset(POLY, 0.9), FL - 0.02, FL, 'rubber'))
STRIP = 0.9                                              # yo'lak yarim eni
p.append(slab([at(0.0, -STRIP), at(0.0, STRIP), at(1.0, STRIP), at(1.0, -STRIP)][::1], FL - 0.02, FL + 0.005, 'rubber_g'))
# poldagi oq yoysimon chiziqlar (banner tomonda)
for cx_t, r_ in ((0.86, 2.4), (0.72, 1.8)):
    c = at(cx_t, -half(cx_t) * 0.55)
    for i in range(10):
        a0 = along_ang(cx_t) + math.pi * (0.15 + 0.07 * i)
        a1 = a0 + 0.07
        p.append(bar((c[0] + r_ * math.cos(a0), c[1] + r_ * math.sin(a0)),
                     (c[0] + r_ * math.cos(a1), c[1] + r_ * math.sin(a1)), 0.004, 'line', r=0.04))

# ---------- bordyur (devordan boshqa qirralar bo'ylab) ----------
for i in range(N):
    a, b = POLY[i], POLY[(i + 1) % N]
    mid = lerp(a, b, 0.5)
    if math.dist(mid, lerp(WALL(0), WALL(1), 0.5)) < 0.5:
        continue
    el = math.dist(a, b)
    nx, ny = -(b[1] - a[1]) / el * 0.08, (b[0] - a[0]) / el * 0.08   # ozgina ichkariga
    p.append(k.box((el, 0.16, FL + 0.12), (mid[0] + nx, mid[1] + ny, (FL + 0.12) / 2), 'curb',
                   rot=(0, 0, math.atan2(b[1] - a[1], b[0] - a[0]))))

# ---------- devor (park chegarasi): firuza mural, keyin sariq bo'yalgan qism ----------
WH = 3.2
wa, wb = WALL(0), WALL(1)
wdir = math.atan2(wb[1] - wa[1], wb[0] - wa[0])
wl = math.dist(wa, wb)
out_n = (math.cos(ang(0.5)) * 0.15, math.sin(ang(0.5)) * 0.15)   # devor tashqariga 0.15 m
SPLIT = 0.62                                             # mural / sariq chegarasi (t)
for t0, t1, mat in ((0.0, SPLIT, 'teal'), (SPLIT, 1.0, 'wall_y')):
    a, b = lerp(wa, wb, t0), lerp(wa, wb, t1)
    m = lerp(a, b, 0.5)
    p.append(k.box((wl * (t1 - t0), 0.25, WH), (m[0] + out_n[0], m[1] + out_n[1], WH / 2), mat, rot=(0, 0, wdir)))
p.append(k.box((wl + 0.6, 0.7, 0.18), (lerp(wa, wb, 0.5)[0] + out_n[0] * 2.2, lerp(wa, wb, 0.5)[1] + out_n[1] * 2.2,
                                         WH + 0.09), 'roof', rot=(0, 0, wdir)))   # tom chetidan chiqib turgan qism
# muraldagi qiya rangli chiziqlar (devorning ichki yuzida)
inner = (-math.cos(ang(0.5)) * 0.005, -math.sin(ang(0.5)) * 0.005)
face = (out_n[0] - math.cos(ang(0.5)) * 0.13, out_n[1] - math.sin(ang(0.5)) * 0.13)
cols = ['pink', 'green', 'navy', 'purple', 'green', 'pink', 'navy']
s = 1.5
j = 0
while s < wl * SPLIT - 2.5:
    a2 = lerp(wa, wb, s / wl)
    b2 = lerp(wa, wb, (s + 1.6) / wl)
    p.append(k.beam((a2[0] + face[0] + inner[0], a2[1] + face[1] + inner[1], 0.15),
                    (b2[0] + face[0] + inner[0], b2[1] + face[1] + inner[1], WH - 0.25), 0.03, 0.45, cols[j % len(cols)]))
    s += random.uniform(2.6, 4.2)
    j += 1
q = lerp(wa, wb, SPLIT - 0.06)                           # QR-kod (oq kvadrat)
p.append(k.box((0.7, 0.04, 0.7), (q[0] + face[0], q[1] + face[1], 2.1), 'banner', rot=(0, 0, wdir)))

# ---------- bannerlar (keng uch): sariq ustunlar orasida oq panellar, ustida rangli reklama bloklari ----------
ba, bb = P3, P2
bl = math.dist(ba, bb)
bdir = math.atan2(bb[1] - ba[1], bb[0] - ba[0])
nb = int(bl // 3.0)
bin_n = (-math.sin(bdir), math.cos(bdir))                # bannerlar qirrasiga normal (u yoki bu tomon)
cen = lerp(lerp(P0, P1, 0.5), lerp(P3, P2, 0.5), 0.5)
mb = lerp(ba, bb, 0.5)
if (cen[0] - mb[0]) * bin_n[0] + (cen[1] - mb[1]) * bin_n[1] < 0:
    bin_n = (-bin_n[0], -bin_n[1])                       # maydon ichiga
for i in range(nb + 1):
    x, y = lerp(ba, bb, (0.4 + i * (bl - 0.8) / nb) / bl)
    x, y = x + bin_n[0] * 0.3, y + bin_n[1] * 0.3
    p += post(x, y, 2.7, r=0.07)
ads = ['ad_g', 'ad_b', 'ad_r', 'ad_t', 'ad_g', 'ad_b']
for i in range(nb):
    t0 = (0.4 + i * (bl - 0.8) / nb) / bl
    t1 = (0.4 + (i + 1) * (bl - 0.8) / nb) / bl
    m = lerp(ba, bb, (t0 + t1) / 2)
    m = (m[0] + bin_n[0] * 0.3, m[1] + bin_n[1] * 0.3)
    w = bl * (t1 - t0) - 0.18
    p.append(k.box((w, 0.04, 2.0), (m[0], m[1], FL + 1.25), 'banner', rot=(0, 0, bdir)))
    for dz, dw, dh in ((1.55, 0.55, 0.5), (0.85, 0.35, 0.55)):    # rasm va yozuv bloklari
        c = ads[(i + int(dz)) % len(ads)]
        off = random.uniform(-0.2, 0.2) * w
        p.append(k.box((w * dw, 0.05, dh), (m[0] + math.cos(bdir) * off + bin_n[0] * 0.01,
                                            m[1] + math.sin(bdir) * off + bin_n[1] * 0.01, FL + dz), c, rot=(0, 0, bdir)))

# ---------- turnik majmualari: sariq ustunlar qatori, ustida qora narvon ("rukoxod"), orasida turniklar ----------
def rig(t_from, t_to, side):
    """side: +1 devor tomoni, −1 yo'lka tomoni. Ko'ndalang qatorlar har 2.2 m, ustunlar ko'ndalang har 1.6 m"""
    parts = []
    rows = []
    m = t_from * LEN
    while m <= t_to * LEN:
        t = tt(m)
        hw = half(t)
        offs = []
        o = STRIP + 0.9
        while o < hw - 1.2:
            offs.append(o)
            o += 1.6
        rows.append((t, offs))
        m += 2.2
    for ri, (t, offs) in enumerate(rows):
        hs = []
        for j, o in enumerate(offs):
            h = 2.7 if (j + ri) % 3 else 2.3
            x, y = at(t, side * o)
            parts.extend(post(x, y, h))
            hs.append(h)
        for j in range(len(offs) - 1):               # ko'ndalang turniklar (ikki ustun orasida)
            a, b = at(t, side * offs[j]), at(t, side * offs[j + 1])
            parts.append(bar(a, b, min(hs[j], hs[j + 1]) - 0.15))
            if (j + ri) % 2:
                parts.append(bar(a, b, 1.25))        # past turnik (bruslar / otjimaniya)
    for ri in range(len(rows) - 1):                  # bo'ylama: rukoxod narvon (birinchi ikki ustun ustida)
        (t0, o0), (t1, o1) = rows[ri], rows[ri + 1]
        if len(o0) < 2 or len(o1) < 2 or ri % 3 == 2:
            continue
        for j in (0, 1):
            parts.append(bar(at(t0, side * o0[j]), at(t1, side * o1[j]), 2.25))
        for r_ in range(1, 6):                       # zinapoyalar
            f = r_ / 6
            a = lerp(at(t0, side * o0[0]), at(t1, side * o1[0]), f)
            b = lerp(at(t0, side * o0[1]), at(t1, side * o1[1]), f)
            parts.append(bar(a, b, 2.25, r=0.018))
        if len(o0) > 2 and len(o1) > 2 and ri % 2 == 0:     # chetki qatorda — oddiy bo'ylama turnik
            parts.append(bar(at(t0, side * o0[-1]), at(t1, side * o1[-1]), 2.0))
    return parts


p += rig(tt(5.0), tt(LEN * 0.6), +1)
p += rig(tt(6.1), tt(LEN * 0.55), -1)


# ---------- qora shved devorlari (sariq ustunlar orasida) ----------
def wall_bars(t, s, h=2.6, w=0.9):
    x, y = at(t, s)
    a = along_ang(t)
    c, sn = math.cos(a), math.sin(a)
    parts = []
    for e in (-1, 1):
        parts += post(x + c * e * (w / 2 + 0.08), y + sn * e * (w / 2 + 0.08), h + 0.1, r=0.065)
    for e in (-1, 1):
        parts.append(k.box((0.05, 0.05, h), (x + c * e * w / 2, y + sn * e * w / 2, FL + h / 2), 'black', rot=(0, 0, a)))
    z = 0.3
    while z < h:
        parts.append(bar((x - c * w / 2, y - sn * w / 2), (x + c * w / 2, y + sn * w / 2), z, r=0.017))
        z += 0.3
    return parts


for m in (4.0, 9.5, LEN * 0.62 + 1.0):
    t = tt(m)
    p += wall_bars(t, half(t) - 0.9)
t = tt(LEN * 0.6 + 0.8)
p += wall_bars(t, -(half(t) - 1.0))


# ---------- qora U-shakl brusyalar (banner tomonda) ----------
def parallel_bars(t, s, length=2.6, gap=0.55, h=1.2):
    x, y = at(t, s)
    a = along_ang(t)
    c, sn = math.cos(a), math.sin(a)
    nx, ny = -sn, c
    parts = []
    for e in (-1, 1):
        ox, oy = x + nx * e * gap / 2, y + ny * e * gap / 2
        a0 = (ox - c * length / 2, oy - sn * length / 2)
        a1 = (ox + c * length / 2, oy + sn * length / 2)
        parts.append(bar(a0, a1, h, r=0.03))
        for px, py in (a0, a1):
            parts.append(k.cyl(0.03, h, (px, py, FL + h / 2), 'black', segs=6))
    return parts


m = LEN * 0.66
while m < LEN - 3.0:
    t = tt(m)
    hw = half(t)
    for side in (-1, 1):
        o = STRIP + 1.0
        n = 0
        while o < hw - 2.0 and n < 3:
            p += parallel_bars(t, side * o, h=1.1 + 0.15 * (n % 2))
            o += 1.5
            n += 1
    m += 4.0

# devor bo'ylab uzun turnik qatori (sariq ustunlar, 2.3 m da qora quvur) — sariq devor oldida
m = LEN * 0.64
prev = None
while m < LEN - 1.2:
    t = tt(m)
    xy = at(t, half(t) - 0.8)
    p += post(*xy, 2.5)
    if prev:
        p.append(bar(prev, xy, 2.3))
    prev = xy
    m += 3.0

# ---------- yo'lka tomonida: sariq ustunli skameykalar, axlat qutilari, fonar ustunlari ----------
def bench(t, s):
    x, y = at(t, s)
    a = along_ang(t)
    c, sn = math.cos(a), math.sin(a)
    parts = [k.box((1.6, 0.4, 0.06), (x, y, FL + 0.45), 'wood', rot=(0, 0, a))]
    for e in (-1, 1):
        for f in (-1, 1):
            parts += post(x + c * e * 0.85 + -sn * f * 0.12, y + sn * e * 0.85 + c * f * 0.12, 0.6, r=0.065)
    return parts


def trash(t, s):
    x, y = at(t, s)
    a = along_ang(t)
    c, sn = math.cos(a), math.sin(a)
    parts = [k.cyl(0.28, 0.5, (x, y, FL + 0.55), 'black', segs=4, r2=0.2, rot=(0, 0, a + math.pi / 4))]
    for e in (-1, 1):
        parts += post(x + c * e * 0.42, y + sn * e * 0.42, 0.85, r=0.065)
    return parts


def lamp(t, s):
    x, y = at(t, s)
    a = ang(t)
    c, sn = math.cos(a), math.sin(a)
    parts = [k.box((0.14, 0.14, 4.2), (x, y, FL + 2.1), 'black', rot=(0, 0, a))]
    parts.append(k.beam((x, y, FL + 4.15), (x + c * 0.9, y + sn * 0.9, FL + 4.4), 0.1, 0.1, 'black'))
    parts.append(k.box((0.45, 0.2, 0.12), (x + c * 1.0, y + sn * 1.0, FL + 4.35), 'black', rot=(0, 0, a)))
    return parts


m = 4.6
i = 0
while m < LEN - 2.0:
    t = tt(m)
    s_ = -(half(t) - 0.6)
    p += trash(t, s_) if i % 3 == 1 else bench(t, s_)
    m += 4.5
    i += 1
for m in (3.4, LEN * 0.5, LEN - 3.5):
    t = tt(m)
    p += lamp(t, -(half(t) - 0.25))

# ---------- kirish uchida 3 pog'onali tribuna (maydonga qaragan): beton pog'onalar, ustida yog'och o'rindiqlar ----------
TB0, TD, TH = 0.5, 0.8, 0.42                             # kirishdan boshlanishi, pog'ona chuqurligi va balandligi, m
for i in range(3):                                       # i=0 — eng baland (orqa) qator
    m0 = TB0 + i * TD
    m1 = m0 + TD
    h = (3 - i) * TH
    t0, t1 = tt(m0), tt(m1)
    w0, w1 = half(t0) - 0.5, half(t1) - 0.5
    p.append(slab([at(t0, -w0), at(t0, w0), at(t1, w1), at(t1, -w1)], FL - 0.01, FL + h, 'curb'))
    for j in range(3):                                   # o'rindiq taxtalari (ko'ndalang)
        mm = m0 + 0.18 + j * 0.2
        t = tt(mm)
        w = 2 * (half(t) - 0.6)
        p.append(k.box((w, 0.16, 0.05), (*at(t, 0), FL + h + 0.03), 'wood', rot=(0, 0, ang(t))))
    t = tt(m1 - 0.01)                                    # old qirrasidagi sariq hoshiya (ozgina chiqib turadi)
    p.append(k.box((2 * (half(t) - 0.5), 0.06, 0.06), (*at(t, 0), FL + h - 0.03), 'yellow', rot=(0, 0, ang(t))))

xs = [v[0] for v in POLY]
ys = [v[1] for v in POLY]
k.finish('MASHGULOT', p, HERE, [
    ('preview.png', (min(xs) - 14, (min(ys) + max(ys)) / 2 - 8, 14.0), (0, 0, 0.5)),
    ('preview_top.png', (0, -0.1, 75.0), (0, 0, 0)),
    ('preview_in.png', (*at(0.02, 0), 2.0), (*at(1.0, 0), 1.2)),
    ('preview_tribuna.png', (*at(0.3, -3), 4.0), (*at(0.02, 0), 0.8)),
])

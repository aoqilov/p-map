"""
Oqqushlar haykali — dam olish maskani (foydalanuvchi fotosuratlari bo'yicha):
plitkali maydon o'rtasida oval gulzor (past beton bordyur), uning o'rtasida to'q kulrang silindr postament, tepasida
oq to'lqinsimon "ko'pik" (chetidan jingalaklar osilib turadi), ustida ikki oq oqqush: biri qanotlarini keng yoyib, bo'ynini
tik ko'targan; ikkinchisi oldida — bo'ynini egib, dum patlarini yelpig'ichdek yoygan. Gulzorda magnoliya butasi,
paporotniklar, lilyalar (to'q sariq gullar) va past o'tlar; orqasida ikki yog'och skameyka va axlat qutilari.

Ishga tushirish (loyiha ildizidan):
    D:/blender-program/blender.exe -b --factory-startup -P src/decor/oqqush-haykali/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png, preview_back.png

Old tomoni (oqqushlar qaragan) — Blender'da -Y. Gulzor: 6.5 × 4.2 m (building.ts dagi iz), skameykalar bilan ~9.6 m.
"""
import math
import random
import sys
from pathlib import Path

import bmesh
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from blender_kit import Kit  # noqa: E402

random.seed(11)
PALETTE = {
    'curb': (0.62, 0.61, 0.58), 'soil': (0.2, 0.15, 0.1), 'ped': (0.27, 0.28, 0.29), 'ped_d': (0.2, 0.21, 0.22),
    'white': (0.96, 0.96, 0.95), 'white_s': (0.86, 0.87, 0.88), 'beak': (0.85, 0.5, 0.15), 'eye': (0.05, 0.05, 0.05),
    'leaf': (0.2, 0.42, 0.15), 'leaf_d': (0.13, 0.3, 0.1), 'leaf_y': (0.62, 0.68, 0.2), 'leaf_l': (0.35, 0.55, 0.2),
    'stem': (0.3, 0.22, 0.12), 'lily': (0.95, 0.45, 0.08), 'wood': (0.82, 0.52, 0.2), 'iron': (0.08, 0.08, 0.09),
    'bin': (0.6, 0.6, 0.6), 'bin_d': (0.35, 0.35, 0.36),
}
k = Kit(PALETTE)
p = []

Z0 = 0.12                       # xaritadagi plitka sathi
A, B = 5.0, 4.75                # gulzor yarim o'qlari (x — eni, y — chuqurligi) — building.ts dagi 10 × 9.5 m iz
SX, SY = A / 3.25, B / 2.1      # o'simliklar joyi dastlabki (6.5 × 4.2 m) gulzordan cho'zib olinadi
PR, PH = 0.66, 1.45             # postament radiusi va balandligi
PC = (0.0, 0.25)                # postament markazi (gulzorda biroz orqaroq)
T = Z0 + 0.1 + PH               # postament tepasi


def oval(a, b, n=40):
    return [(a * math.cos(2 * math.pi * i / n), b * math.sin(2 * math.pi * i / n)) for i in range(n)]


def prism(pts, z0, z1, mat):
    bm = bmesh.new()
    bot = [bm.verts.new((x, y, z0)) for x, y in pts]
    top = [bm.verts.new((x, y, z1)) for x, y in pts]
    bm.faces.new(top)
    bm.faces.new(bot[::-1])
    n = len(pts)
    for i in range(n):
        bm.faces.new([bot[i], bot[(i + 1) % n], top[(i + 1) % n], top[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return k.obj('prism', bm, mat)


def in_bed(x, y, margin=0.25):
    return (x / (A - margin)) ** 2 + (y / (B - margin)) ** 2 < 1


# ---------- gulzor: beton bordyur, tuproq ----------
p.append(prism(oval(A, B), 0.0, Z0 + 0.16, 'curb'))
p.append(prism(oval(A - 0.14, B - 0.14), Z0 + 0.16, Z0 + 0.17, 'leaf_d'))   # yerni qoplagan past o'simliklar (zich gulzor)
p.append(prism(oval(A - 0.16, B - 0.16), 0.0, Z0 + 0.12, 'soil'))

# ---------- postament: to'q kulrang silindr, pastida halqa ----------
p.append(k.cyl(PR, PH, (*PC, Z0 + 0.1 + PH / 2), 'ped', segs=28))
p.append(k.cyl(PR + 0.05, 0.12, (*PC, Z0 + 0.16), 'ped_d', segs=28))

# ---------- to'lqinsimon "ko'pik" (oq): markaziy disk, chetida bo'rtiqlar, osilib turgan jingalaklar ----------
p.append(k.cyl(PR + 0.12, 0.22, (*PC, T + 0.11), 'white', segs=28))
N = 16
for i in range(N):
    a = 2 * math.pi * i / N + random.uniform(-0.08, 0.08)
    r = PR + 0.12 + random.uniform(-0.03, 0.05)
    x, y = PC[0] + r * math.cos(a), PC[1] + r * math.sin(a)
    p.append(k.ball(random.uniform(0.15, 0.2), (x, y, T + 0.16 + random.uniform(-0.03, 0.06)), 'white', sub=2,
                    scale=(1.35, 1.35, 0.75)))
    if i % 2 == 0:   # chetdan osilgan jingalak (to'lqin uchi)
        r2_ = PR + 0.17
        cx, cy = PC[0] + r2_ * math.cos(a + 0.1), PC[1] + r2_ * math.sin(a + 0.1)
        p.append(k.ball(0.12, (cx, cy, T - 0.02), 'white', sub=2, scale=(1.5, 1.5, 1.0)))   # to'lqin uchi — pastga qayrilgan
        p.append(k.ball(0.07, (PC[0] + (r2_ + 0.06) * math.cos(a + 0.1), PC[1] + (r2_ + 0.06) * math.sin(a + 0.1), T - 0.1),
                        'white_s', sub=1, scale=(1.3, 1.3, 0.8)))
for i in range(7):   # tepadagi kichik to'lqin qirralari
    a = 2 * math.pi * i / 7 + 0.3
    p.append(k.ball(0.16, (PC[0] + 0.42 * math.cos(a), PC[1] + 0.42 * math.sin(a), T + 0.27), 'white', sub=2,
                    scale=(1.4, 1.0, 0.55)))


def neck(pts, r0, r1, mat='white', steps=28, segs=10):
    """Bo'yin: nuqtalar orqali silliq egri (Catmull-Rom) bo'ylab trubka, radiusi r0 → r1"""
    cur = []
    for st in range(steps + 1):
        t = st / steps * (len(pts) - 1)
        i = min(int(t), len(pts) - 2)
        f = t - i
        p0, p1_, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, len(pts) - 1)]
        cur.append(Vector([0.5 * ((2 * p1_[j]) + (-p0[j] + p2[j]) * f + (2 * p0[j] - 5 * p1_[j] + 4 * p2[j] - p3[j]) * f * f +
                                  (-p0[j] + 3 * p1_[j] - 3 * p2[j] + p3[j]) * f ** 3) for j in range(3)]))
    bm = bmesh.new()
    rings = []
    up = Vector((1, 0, 0))
    for st, c in enumerate(cur):
        tng = (cur[min(st + 1, steps)] - cur[max(st - 1, 0)]).normalized()
        n1 = tng.cross(up)
        if n1.length < 1e-4:
            n1 = tng.cross(Vector((0, 1, 0)))
        n1.normalize()
        n2 = tng.cross(n1).normalized()
        r = r0 + (r1 - r0) * st / steps
        rings.append([bm.verts.new(c + (n1 * math.cos(2 * math.pi * q / segs) + n2 * math.sin(2 * math.pi * q / segs)) * r)
                      for q in range(segs)])
    for a, b in zip(rings, rings[1:]):
        for q in range(segs):
            bm.faces.new([a[q], a[(q + 1) % segs], b[(q + 1) % segs], b[q]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return [k.obj('neck', bm, mat), k.ball(r0, tuple(cur[0]), mat, sub=2), k.ball(r1, tuple(cur[-1]), mat, sub=2)]


def head(at, dirx, diry, dirz):
    """Bosh (shar), tumshuq (konus) at → (dir) yo'nalishida, ko'zlar"""
    parts = [k.ball(0.1, at, 'white', sub=2, scale=(0.9, 1.2, 0.9))]
    L = math.sqrt(dirx * dirx + diry * diry + dirz * dirz)
    dx, dy, dz = dirx / L, diry / L, dirz / L
    tip = (at[0] + dx * 0.3, at[1] + dy * 0.3, at[2] + dz * 0.3)
    parts.append(k.beam((at[0] + dx * 0.06, at[1] + dy * 0.06, at[2] + dz * 0.06), tip, 0.07, 0.05, 'white'))
    parts.append(k.beam((at[0] + dx * 0.05, at[1] + dy * 0.05, at[2] + dz * 0.05 + 0.02),
                        (at[0] + dx * 0.13, at[1] + dy * 0.13, at[2] + dz * 0.13 + 0.02), 0.075, 0.06, 'white_s'))
    for s in (-1, 1):
        parts.append(k.ball(0.017, (at[0] + s * 0.075, at[1] + dy * 0.03, at[2] + 0.03), 'eye', sub=1))
    return parts


# ---------- 1-oqqush: qanotlari keng yoyilgan, bo'yni tik ----------
SB = (PC[0], PC[1] + 0.12, T + 0.62)                                  # tana markazi
p.append(k.ball(0.5, SB, 'white', sub=2, scale=(0.82, 1.15, 0.78)))
p.append(k.ball(0.32, (SB[0], SB[1] + 0.5, SB[2] + 0.12), 'white', sub=1, scale=(0.7, 0.9, 0.6)))   # dum
p += neck([(0, SB[1] - 0.38, SB[2] + 0.18), (0, SB[1] - 0.5, SB[2] + 0.55), (0, SB[1] - 0.42, SB[2] + 0.95),
           (0, SB[1] - 0.3, SB[2] + 1.25), (0, SB[1] - 0.36, SB[2] + 1.45)], 0.15, 0.075)
p += head((0, SB[1] - 0.42, SB[2] + 1.5), 0, -0.6, -0.5)


def wing(side):
    """Yoyilgan qanot: yelkadan tashqariga-tepaga patlar yelpig'ichi (2 qator), ichki qismi — keng plastinka"""
    parts = []
    sh = (side * 0.32, SB[1] + 0.05, SB[2] + 0.28)                     # yelka
    parts.append(k.ball(0.4, (side * 0.75, SB[1] + 0.08, SB[2] + 0.62), 'white', sub=2, scale=(1.45, 0.22, 0.8)))   # qanot asosi
    parts.append(k.ball(0.3, (side * 1.2, SB[1] + 0.1, SB[2] + 0.82), 'white', sub=2, scale=(1.4, 0.18, 0.75)))
    rows = ((1.5, 1.2, 0.3, 0.02), (1.05, 0.9, 0.3, 0.06))           # uchlari uzunligi (yuqori, past), eni, Y siljishi
    for li, (l_top, l_bot, w, yo) in enumerate(rows):
        n = 8
        for i in range(n):
            f = i / (n - 1)
            ang = math.radians(36 - 34 * f)                            # tepadan (36°) pastga (2°)
            L = l_top + (l_bot - l_top) * f + 0.05 * math.sin(f * math.pi)
            tip = (sh[0] + side * L * math.cos(ang), sh[1] + yo + 0.06 * f,
                   sh[2] + L * math.sin(ang) + 0.18)
            root = (sh[0] + side * 0.1, sh[1] + yo, sh[2] + 0.1 + 0.08 * (1 - f))
            parts.append(k.beam(root, tip, 0.05, w, 'white' if (i + li) % 2 else 'white_s'))
        # qanot uchlari tepaga ozgina qayrilgan (birinchi qatorning ustki pati)
    return parts


p += wing(-1)
p += wing(1)

# ---------- 2-oqqush (oldida): bo'yni egilgan, dum patlari yelpig'ich ----------
S2 = (PC[0] + 0.1, PC[1] - 0.42, T + 0.42)
p.append(k.ball(0.42, S2, 'white', sub=2, scale=(1.15, 0.75, 0.65)))
fan_c = (S2[0] - 0.4, S2[1] - 0.05, S2[2] + 0.05)
for i in range(9):                                                     # yelpig'ich dum (chapda)
    a = math.radians(95 + 13 * i)
    tip = (fan_c[0] + 0.55 * math.cos(a) * 0.9, fan_c[1] - 0.06, fan_c[2] + 0.55 * math.sin(a) * 0.9 + 0.12)
    if tip[2] < S2[2] - 0.15:
        continue
    p.append(k.beam(fan_c, tip, 0.05, 0.13, 'white' if i % 2 else 'white_s'))
p += neck([(S2[0] + 0.35, S2[1] - 0.1, S2[2] + 0.12), (S2[0] + 0.45, S2[1] - 0.22, S2[2] + 0.5),
           (S2[0] + 0.3, S2[1] - 0.25, S2[2] + 0.78), (S2[0] + 0.05, S2[1] - 0.2, S2[2] + 0.82)], 0.12, 0.07)
p += head((S2[0] - 0.05, S2[1] - 0.22, S2[2] + 0.76), -0.7, -0.2, -0.45)

# ---------- gulzor o'simliklari ----------
# magnoliya butasi (oldi-chapda, baland, sariq-yashil barglar)
MB = (-1.45, -0.55)
p.append(k.cyl(0.05, 1.0, (MB[0], MB[1], Z0 + 0.6), 'stem', segs=6))
for i in range(16):
    a = random.uniform(0, 2 * math.pi)
    r = random.uniform(0.1, 0.55)
    z = Z0 + random.uniform(0.6, 2.1)
    rr = 0.32 - 0.06 * (z - Z0 - 0.6)
    p.append(k.ball(max(0.18, rr), (MB[0] + r * math.cos(a), MB[1] + r * math.sin(a), z),
                    random.choice(('leaf_y', 'leaf', 'leaf_l')), sub=1, scale=(1.0, 1.0, 0.85)))


def fern(cx, cy, n=9, L=0.75):
    parts = []
    for i in range(n):
        a = 2 * math.pi * i / n + random.uniform(-0.2, 0.2)
        l = L * random.uniform(0.8, 1.1)
        mid = (cx + math.cos(a) * l * 0.5, cy + math.sin(a) * l * 0.5, Z0 + 0.12 + l * 0.55)
        tip = (cx + math.cos(a) * l, cy + math.sin(a) * l, Z0 + 0.12 + l * 0.3)
        base = (cx, cy, Z0 + 0.14)
        parts.append(k.beam(base, mid, 0.02, 0.16, 'leaf_l'))
        parts.append(k.beam(mid, tip, 0.02, 0.12, 'leaf_l'))
    return parts


for fx, fy in ((1.55, 0.3), (1.0, 1.1), (2.2, -0.4), (-0.9, 1.25), (-2.2, -0.9), (0.1, 1.6), (2.6, 0.9), (-2.6, 1.0)):
    p += fern(fx * SX * 0.9, fy * SY * 0.85, L=0.9)


def lily(cx, cy):
    """Lilya: ingichka barglar to'pi va to'q sariq gullar"""
    parts = []
    for i in range(10):
        a = 2 * math.pi * i / 10 + random.uniform(-0.3, 0.3)
        l = random.uniform(0.45, 0.7)
        parts.append(k.beam((cx, cy, Z0 + 0.13), (cx + math.cos(a) * l * 0.6, cy + math.sin(a) * l * 0.6, Z0 + 0.13 + l),
                            0.015, 0.05, 'leaf'))
    for j in range(3):
        fx, fy = cx + random.uniform(-0.15, 0.15), cy + random.uniform(-0.15, 0.15)
        h = random.uniform(0.75, 0.95)
        parts.append(k.cyl(0.01, h, (fx, fy, Z0 + 0.13 + h / 2), 'leaf_d', segs=4))
        parts.append(k.cyl(0.09, 0.06, (fx, fy, Z0 + 0.13 + h), 'lily', segs=6, r2=0.02))
    return parts


for lx, ly in ((0.3, -1.45), (1.0, -1.2), (-0.4, -1.55), (1.9, -0.95), (-2.3, 0.4), (-1.2, -1.5), (2.5, -0.2), (-2.6, -0.4), (1.5, 1.6), (-1.6, 1.6)):
    p += lily(lx * SX * 0.85, ly * SY * 0.8)

# qo'shimcha yumaloq butalar (gulzor chetlarida)
for bx_, by_ in ((-3.4, -1.6), (3.3, -1.9), (-3.0, 2.6), (3.6, 1.8), (0.6, 3.6)):
    for j in range(5):
        p.append(k.ball(random.uniform(0.35, 0.5), (bx_ + random.uniform(-0.4, 0.4), by_ + random.uniform(-0.4, 0.4),
                                                    Z0 + random.uniform(0.35, 0.75)), random.choice(('leaf', 'leaf_l', 'leaf_d')),
                        sub=1, scale=(1.1, 1.1, 0.9)))

# past o'tlar / yer qoplovchilar
for i in range(110):
    x, y = random.uniform(-A, A), random.uniform(-B, B)
    if not in_bed(x, y, 0.3) or math.hypot(x - PC[0], y - PC[1]) < PR + 0.15:
        continue
    p.append(k.ball(random.uniform(0.14, 0.24), (x, y, Z0 + 0.15), random.choice(('leaf', 'leaf_d', 'leaf_l')), sub=1,
                    scale=(1.2, 1.2, 0.6)))


# ---------- skameykalar (orqa tomonda, haykalga qaragan) va axlat qutilari ----------
def bench(x, y, rot):
    c, s = math.cos(rot), math.sin(rot)
    parts = []

    def L(lx, ly):                                                     # lokal (eni bo'ylab, oldga) → dunyo
        return (x + c * lx - s * ly, y + s * lx + c * ly)

    for j in range(4):                                                 # o'rindiq taxtalari
        parts.append(k.box((1.9, 0.09, 0.04), (*L(0, -0.2 + j * 0.11), Z0 + 0.45), 'wood', rot=(0, 0, rot)))
    for j in range(3):                                                 # suyanchiq
        parts.append(k.box((1.9, 0.04, 0.09), (*L(0, 0.2), Z0 + 0.6 + j * 0.12), 'wood', rot=(0, 0, rot)))
    for lx in (-0.8, 0.8):
        parts.append(k.box((0.06, 0.5, 0.06), (*L(lx, 0), Z0 + 0.42), 'iron', rot=(0, 0, rot)))
        parts.append(k.box((0.06, 0.06, 0.44), (*L(lx, -0.2), Z0 + 0.22), 'iron', rot=(0, 0, rot)))
        parts.append(k.box((0.06, 0.06, 0.88), (*L(lx, 0.22), Z0 + 0.44), 'iron', rot=(0, 0, rot)))
    return parts


def trash(x, y):
    return [k.box((0.42, 0.36, 0.75), (x, y, Z0 + 0.375), 'bin'), k.box((0.46, 0.4, 0.06), (x, y, Z0 + 0.78), 'bin_d'),
            k.box((0.2, 0.01, 0.2), (x, y - 0.185, Z0 + 0.48), 'bin_d')]


for th in (math.radians(125), math.radians(55)):                     # gulzor chetidan 1.2 m tashqarida, orqa tomonda
    bx, by = (A + 1.2) * math.cos(th), (B + 1.2) * math.sin(th)
    rot = math.atan2(PC[0] - bx, -(PC[1] - by))                        # lokal −Y (o'tirgan odam qarashi) → haykal tomon
    p += bench(bx, by, rot)
p += trash((A + 1.0) * math.cos(math.radians(152)), (B + 1.0) * math.sin(math.radians(152)))
p += trash((A + 1.0) * math.cos(math.radians(28)), (B + 1.0) * math.sin(math.radians(28)))

k.finish('OQQUSH', p, HERE, [
    ('preview.png', (2.5, -11.0, 4.0), (0, 0, 1.8)),
    ('preview_back.png', (-9.0, 10.0, 7.5), (0, 0, 1.0)),
])

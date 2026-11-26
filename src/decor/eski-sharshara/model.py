"""
Eski sharshara — "Замок эльфов" kafesi yonidagi qoyali fontan (foydalanuvchi fotosurati bo'yicha):
old tomonda yarim doira past granit bordyur, ichida o'tli tasma; o'rtada mayda toshli mozaika kosa (yassi tosh labli,
old yuzida bronza baliqlar bo'rtmasi); orqada pog'onali kulrang qoyalar, ustida ikkita yotgan bronza kiyik (jayron),
qoyalarda butalar va osilib turgan pechak. Sharshara to'xtatilgan — suv yo'q: kosa ichi quruq tuproq va o't.
Bezak-bino: building.ts (plandagi yo'l plitkasi ustida — izi kesiladi, marshrut o'tmaydi).

O'qlar: old tomon (bordyur yoyi, maydon) — Blender -Y, origin — iz markazi. Iz: W × D (building.ts dagi width × depth).

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/decor/eski-sharshara/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png, preview_top.png
"""
import math
import random
import sys
from pathlib import Path

import bmesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from blender_kit import Kit  # noqa: E402

random.seed(11)
PALETTE = {
    'granite': (0.42, 0.44, 0.45), 'granite_l': (0.62, 0.62, 0.6), 'soil': (0.45, 0.38, 0.24), 'dry': (0.72, 0.62, 0.32),
    'mosaic': (0.55, 0.5, 0.44), 'ledge': (0.68, 0.66, 0.62), 'rock1': (0.6, 0.59, 0.56), 'rock2': (0.52, 0.5, 0.47),
    'rock3': (0.66, 0.64, 0.6), 'bronze': (0.62, 0.47, 0.25), 'bronze_d': (0.45, 0.33, 0.17),
    'bush': (0.2, 0.42, 0.18), 'bush2': (0.32, 0.52, 0.22), 'ivy': (0.26, 0.5, 0.2), 'fl_y': (0.98, 0.85, 0.2),
}
k = Kit(PALETTE)
p = []

# ---------- o'lchamlar, m ----------
W, D = 13.0, 11.0
CY = 0.6                    # bordyur yoyi markazi (Y)
R_OUT, R_IN = 6.3, 5.85     # bordyur tashqi / ichki radiusi
CURB_H = 0.55
BOWL = (-0.4, -0.2)         # kosa markazi
BOWL_R, BOWL_H = 3.0, 1.15
SOIL_Z = BOWL_H - 0.25        # kosa ichidagi quruq tuproq sathi


def sector(r_in, r_out, a0, a1, z0, z1, mat, cx=0.0, cy=CY, segs=28):
    """Halqa bo'lagi (bordyur, tokcha): a0..a1 gradus"""
    bm = bmesh.new()
    ring = []
    for i in range(segs + 1):
        a = math.radians(a0 + (a1 - a0) * i / segs)
        ring.append((cx + r_out * math.cos(a), cy + r_out * math.sin(a)))
    for i in range(segs, -1, -1):
        a = math.radians(a0 + (a1 - a0) * i / segs)
        ring.append((cx + r_in * math.cos(a), cy + r_in * math.sin(a)))
    bot = [bm.verts.new((x, y, z0)) for x, y in ring]
    top = [bm.verts.new((x, y, z1)) for x, y in ring]
    bm.faces.new(top)
    bm.faces.new(bot[::-1])
    n = len(ring)
    for i in range(n):
        bm.faces.new([bot[i], bot[(i + 1) % n], top[(i + 1) % n], top[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return k.obj('sector', bm, mat)


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


def rock(x, y, z, r, flat=0.6, mat=None):
    s = (random.uniform(1.0, 1.4), random.uniform(0.8, 1.1), flat * random.uniform(0.85, 1.15))
    return k.ball(r, (x, y, z + r * s[2] * 0.5), mat or random.choice(('rock1', 'rock2', 'rock3')), sub=2, scale=s)


def rball(r, loc, mat, scale, rot, sub=1):
    """Cho'zilgan va burilgan shar: o'z markazi atrofida buriladi (k.ball tepalarni joyiga suradi)"""
    ob = k.ball(r, (0, 0, 0), mat, sub=sub, scale=scale)
    ob.rotation_euler = rot
    ob.location = loc
    return ob


# ---------- yarim doira granit bordyur (old tomon) va uning ichidagi o'tli tasma ----------
p.append(sector(R_IN, R_OUT, 180, 360, 0.0, CURB_H, 'granite'))
p.append(sector(R_IN - 0.08, R_OUT + 0.06, 180, 360, CURB_H, CURB_H + 0.09, 'granite_l'))      # tepadagi silliq plita
for side in (-1, 1):   # yoy uchlaridan orqaga to'g'ri davomi (qoyalar ostigacha)
    x = side * (R_IN + R_OUT) / 2
    p.append(k.box((R_OUT - R_IN, 3.2, CURB_H), (x, CY + 1.6, CURB_H / 2), 'granite'))
    p.append(k.box((R_OUT - R_IN + 0.14, 3.2, 0.09), (x, CY + 1.6, CURB_H + 0.045), 'granite_l'))
half = [(R_IN * math.cos(math.radians(a)), CY + R_IN * math.sin(math.radians(a))) for a in range(180, 361, 8)]
p.append(slab(half + [(R_IN, CY + 3.2), (-R_IN, CY + 3.2)], 0.0, 0.32, 'soil'))
# quruq va yashil o't tutamlari, sariq gullar
for i in range(46):
    a = math.radians(random.uniform(185, 355))
    r = random.uniform(3.4, R_IN - 0.3)
    x, y = r * math.cos(a), CY + r * math.sin(a)
    mat = 'dry' if i % 3 else 'bush2'
    p.append(k.ball(random.uniform(0.16, 0.3), (x, y, 0.36), mat, sub=1, scale=(1.2, 1.2, random.uniform(0.9, 1.6))))
for i in range(10):
    a = math.radians(random.uniform(220, 300))
    r = random.uniform(3.3, 4.2)
    p.append(k.ball(0.08, (BOWL[0] + r * math.cos(a), BOWL[1] + r * math.sin(a), 0.7), 'fl_y', sub=1))

# ---------- mozaika kosa (yassi tosh labli), bronza baliqlar ----------
p.append(k.cyl(BOWL_R, BOWL_H, (BOWL[0], BOWL[1], BOWL_H / 2), 'mosaic', segs=32))
# notekis yassi tosh lab — bir necha bo'lak, biroz turlicha qalinlikda
for i in range(9):
    a0 = i * 40
    p.append(sector(BOWL_R - 0.45, BOWL_R + 0.28 + random.uniform(-0.05, 0.08), a0, a0 + 40, BOWL_H - 0.02,
                    BOWL_H + 0.22 + random.uniform(-0.03, 0.04), 'ledge', cx=BOWL[0], cy=BOWL[1], segs=5))
ring = [(BOWL[0] + (BOWL_R - 0.45) * math.cos(math.radians(a)), BOWL[1] + (BOWL_R - 0.45) * math.sin(math.radians(a)))
        for a in range(0, 360, 12)]
p.append(slab(ring, BOWL_H - 0.5, SOIL_Z, 'soil'))     # suv yo'q — quruq tuproq
for i in range(14):                                     # kosa ichida o'sib ketgan quruq o't
    a = math.radians(random.uniform(0, 360))
    r = random.uniform(0.3, BOWL_R - 0.7)
    p.append(k.ball(random.uniform(0.2, 0.32), (BOWL[0] + r * math.cos(a), BOWL[1] + r * math.sin(a), SOIL_Z + 0.08),
                    'dry' if i % 3 else 'bush2', sub=1, scale=(1.2, 1.2, random.uniform(0.9, 1.5))))
# old yuzidagi bronza baliqlar va suv o'tlari bo'rtmasi
for a, s in ((215, 1.0), (245, 0.85), (275, 1.1), (305, 0.9), (330, 0.8)):
    ar = math.radians(a)
    x, y = BOWL[0] + (BOWL_R + 0.03) * math.cos(ar), BOWL[1] + (BOWL_R + 0.03) * math.sin(ar)
    p.append(rball(0.28 * s, (x, y, 0.55), 'bronze', (1.5, 0.35, 0.8), (0, 0, ar + math.pi / 2)))
    tail = k.ball(0.14 * s, (x - 0.38 * s * math.sin(ar) * -1, y + 0.38 * s * math.cos(ar) * -1, 0.6), 'bronze_d', sub=1,
                  scale=(0.6, 0.3, 1.2))
    p.append(tail)
for a in (230, 290):   # suv o'ti (tik bronza barglar)
    ar = math.radians(a)
    x, y = BOWL[0] + (BOWL_R + 0.03) * math.cos(ar), BOWL[1] + (BOWL_R + 0.03) * math.sin(ar)
    p.append(k.box((0.12, 0.05, 0.9), (x, y, 0.55), 'bronze_d', rot=(0, 0.15, ar + math.pi / 2)))

# ---------- orqadagi pog'onali qoyalar ----------
TIERS = [  # (y markazi, z asosi, yarim eni, toshlar soni, radius)
    (1.9, 0.0, 6.2, 9, 1.05),
    (3.1, 0.7, 5.6, 8, 1.0),
    (4.3, 1.4, 4.8, 7, 0.95),
]
for yc, z0, hw, n, r in TIERS:
    # pog'ona asosi — qatlamli tosh plita
    p.append(slab([(-hw, yc - 0.9), (hw, yc - 0.9), (hw - 0.3, yc + 1.4), (-hw + 0.3, yc + 1.4)], 0.0, z0 + 0.45, 'rock2'))
    for i in range(n):
        x = -hw + 0.6 + (2 * hw - 1.2) * i / (n - 1) + random.uniform(-0.25, 0.25)
        p.append(rock(x, yc + random.uniform(-0.3, 0.3), z0 + 0.2, r * random.uniform(0.8, 1.15), flat=0.7))
# qatlamli yassi plitalar (fotodagi gorizontal tosh qatlamlari)
for x, y, z, w in ((-2.2, 2.4, 1.05, 2.6), (1.4, 3.5, 1.75, 2.2), (-0.9, 4.6, 2.35, 2.8), (3.0, 2.2, 1.0, 1.8)):
    p.append(k.box((w, 1.1, 0.28), (x, y, z), 'rock3', rot=(0, 0, random.uniform(-0.15, 0.15))))
# kiyiklar uchun katta tekis qoyalar (chapda past, o'ngda baland)
L_ROCK = (-3.6, 1.4, 1.35)
R_ROCK = (3.4, 1.2, 1.7)
p.append(k.ball(1.3, (L_ROCK[0], L_ROCK[1], L_ROCK[2] - 0.45), 'rock1', sub=2, scale=(1.4, 1.1, 0.42)))
p.append(k.ball(1.6, (R_ROCK[0], R_ROCK[1], R_ROCK[2] - 0.55), 'rock3', sub=2, scale=(1.35, 1.1, 0.4)))
p.append(k.ball(1.2, (4.4, 2.4, 2.0), 'rock2', sub=2, scale=(1.0, 1.0, 0.9)))      # o'ng orqadagi baland xarsang

# ---------- qoyadagi quruq tarnov (suv shu yerdan tushardi) ----------
LIP = (0.0, 1.05, 1.95)
p.append(k.box((1.1, 0.7, 0.16), (LIP[0], LIP[1] + 0.25, LIP[2] - 0.05), 'ledge'))


# ---------- bronza kiyiklar (yotgan jayron) ----------
def deer(x, y, z, yaw, s=1.0):
    """Yotgan kiyik: tana, buklangan oyoqlar, tik bo'yin, bosh, uzun shoxlar. yaw — boshi qaragan tomon (radian, 0 — +X)"""
    parts = []
    c, si = math.cos(yaw), math.sin(yaw)

    def at(lx, ly, lz):
        return (x + (lx * c - ly * si) * s, y + (lx * si + ly * c) * s, z + lz * s)

    parts.append(rball(0.5 * s, at(0, 0, 0.32), 'bronze', (1.6, 0.75, 0.62), (0, 0, yaw), sub=2))
    for lx, ly in ((0.45, 0.32), (0.45, -0.32), (-0.5, 0.33), (-0.5, -0.33)):   # buklangan oyoqlar
        leg = k.box((0.75 * s, 0.13 * s, 0.13 * s), at(lx + 0.1, ly, 0.08), 'bronze_d', rot=(0, 0, yaw))
        parts.append(leg)
    parts.append(k.beam(at(0.55, 0, 0.45), at(0.78, 0, 1.15), 0.2 * s, 0.24 * s, 'bronze'))        # bo'yin
    parts.append(rball(0.17 * s, at(0.92, 0, 1.2), 'bronze', (1.6, 0.8, 0.85), (0, 0.35, yaw)))
    for ly in (0.06, -0.06):                                                                    # shoxlar
        parts.append(k.beam(at(0.82, ly, 1.33), at(0.72, ly * 1.6, 1.75), 0.04 * s, 0.04 * s, 'bronze_d'))
        parts.append(k.beam(at(0.72, ly * 1.6, 1.75), at(0.55, ly * 2.0, 1.98), 0.035 * s, 0.035 * s, 'bronze_d'))
    for ly in (0.1, -0.1):                                                                      # quloqlar
        parts.append(k.ball(0.06 * s, at(0.8, ly * 1.5, 1.33), 'bronze_d', sub=1, scale=(0.6, 1.2, 0.5)))
    parts.append(k.ball(0.09 * s, at(-0.78, 0, 0.45), 'bronze_d', sub=1))                      # dum
    return parts


p += deer(L_ROCK[0], L_ROCK[1], L_ROCK[2] - 0.05, math.radians(25), 1.0)     # chapdagi — o'ngga, maydon tomonga qaragan
p += deer(R_ROCK[0], R_ROCK[1] + 0.1, R_ROCK[2] - 0.05, math.radians(160), 1.2)  # o'ngdagi kattaroq — chapga qaragan

# ---------- yashillik: qoyalardagi butalar, kosadagi pechak ----------
for x, y, z, r in ((-5.6, 3.2, 1.0, 0.7), (-4.8, 4.6, 1.8, 0.8), (5.5, 3.6, 1.6, 0.75), (2.2, 4.9, 2.5, 0.65),
                   (-1.8, 5.0, 2.6, 0.6), (5.9, 1.6, 0.6, 0.6), (-6.0, 1.4, 0.5, 0.55), (0.6, 5.1, 2.7, 0.55)):
    p.append(k.ball(r, (x, y, z), random.choice(('bush', 'bush2')), sub=1, scale=(1.2, 1.0, 0.9)))
for i in range(7):   # kosaning o'ng-old yuzida osilib turgan pechak
    a = math.radians(300 + i * 8)
    x, y = BOWL[0] + (BOWL_R + 0.12) * math.cos(a), BOWL[1] + (BOWL_R + 0.12) * math.sin(a)
    h = random.uniform(0.5, 1.0)
    p.append(k.box((0.3, 0.08, h), (x, y, BOWL_H + 0.1 - h / 2), 'ivy', rot=(0, 0, a + math.pi / 2)))
for i in range(6):   # o'ng qoyadan osilgan pechak
    x = 2.3 + i * 0.4
    h = random.uniform(0.6, 1.3)
    p.append(k.box((0.28, 0.08, h), (x, 0.2, 1.2 - h / 2 + 0.3), 'ivy'))

k.finish('ESKI-SHARSHARA', p, HERE, [
    ('preview.png', (1.5, -15.0, 5.0), (0, 1.0, 1.2)),
    ('preview_top.png', (-9.0, -9.0, 11.0), (0, 0.5, 0.8)),
])

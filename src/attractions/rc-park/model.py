"""
RC Park — masofadan boshqariladigan mashinalar maydoni (rasmlar: "car rc park" — rally treki, qoyali crawler zonasi,
cho'l). Maysazor ichidagi to'rtburchak maydon (place.ts: 32.5 × 24.8 m):
  * oldi chapda (yo'l tomonda) — oynasiz bino (rasm: "YETI RC PARK" fasadi): bej-jigarrang siding, tik plankalar, beton
    sokol, yagona kirish eshigi, katta kulrang lavha ("YETI RC PARK", pultlar va mashinalar rasmi); tomida katta yashil
    RC mashina va katta pult (reklama haykallari); yonida haydovchilar supasi;
  * oldi o'ngda — rally treki: tuproq yo'l (ikki sakrash tepaligi), chetida oq-qora shina to'siqlari, o'rtasi maysa;
    yo'lda 4 ta RC mashina (car0..car3) aylanib yuradi (track.json, anim.follow);
  * orqa o'ngda — cho'l zonasi: qum, tepaliklar, qoyalar, kaktuslar, sakrash ramasi;
  * orqa chapda — o'rmon/crawler zonasi: qoyalar, yog'ochlar, taxta ko'prik, archalar, kichik ko'lmak, so'qmoq,
    qoyada turgan ikki crawler;
  * atrofida yashil panjara (bino va haydovchilar supasi oldida kirish).

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/rc-park/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, track.json, preview.png, preview_roof.png, preview_front.png, preview_top.png

Old tomoni (bino, yo'l) — Blender'da -Y. Markaz — maydoncha o'rtasi. Asl o'lcham: 32.4 × 19.4 m (orqa qismi BACK_CUT ga qisqartirilgan), balandligi ~8.8 m (tomdagi pult antennasi).
"""
import json
import math
import random
import sys
from pathlib import Path

import bmesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'decor'))
from blender_kit import Kit  # noqa: E402

PALETTE = {
    'base': (0.2, 0.15, 0.08), 'dirt': (0.36, 0.2, 0.08), 'track': (0.25, 0.12, 0.05), 'grass': (0.12, 0.32, 0.08),
    'sand': (0.75, 0.52, 0.25), 'sand_d': (0.6, 0.38, 0.16), 'soil': (0.18, 0.12, 0.06), 'rock': (0.35, 0.33, 0.3),
    'rock_r': (0.5, 0.25, 0.12), 'log': (0.3, 0.16, 0.06), 'plank': (0.55, 0.35, 0.15), 'pine': (0.05, 0.25, 0.08),
    'pine_l': (0.1, 0.38, 0.1), 'cactus': (0.15, 0.45, 0.12), 'water': (0.08, 0.3, 0.45), 'trail': (0.45, 0.3, 0.15),
    'wall': (0.06, 0.06, 0.07), 'orange': (0.95, 0.3, 0.02), 'white': (0.9, 0.9, 0.9), 'black': (0.02, 0.02, 0.02),
    'glass': (0.25, 0.45, 0.6), 'steel': (0.6, 0.62, 0.64), 'fence': (0.07, 0.25, 0.1), 'tyre': (0.03, 0.03, 0.03),
    'red': (0.8, 0.04, 0.03), 'green': (0.2, 0.7, 0.05), 'yellow': (0.95, 0.65, 0.02), 'blue': (0.03, 0.25, 0.85),
    'siding': (0.42, 0.3, 0.2), 'siding_d': (0.3, 0.2, 0.13), 'trim': (0.55, 0.42, 0.28), 'concrete': (0.55, 0.55, 0.53),
    'roof': (0.2, 0.18, 0.17), 'door': (0.18, 0.1, 0.05), 'board': (0.32, 0.33, 0.34), 'board_l': (0.42, 0.43, 0.44),
    'green_d': (0.02, 0.35, 0.18), 'glass_d': (0.1, 0.15, 0.2),
}
k = Kit(PALETTE, glass=('glass',), glass_alpha=0.6)
rnd = random.Random(7)
p = []

HX, HY = 16.2, 12.35        # maydon yarim o'lchami
# Orqa tomon (+Y, cho'l va o'rmon zonalari) qisqartirilgan: #editor da maydoncha chuqurligi 24.8 → 19.5 m (old qirra joyida).
# Model avval to'liq (HY) quriladi, oxirida SPLIT dan orqadagilar BACK_CUT ga siqiladi va markaz izga suriladi (pastda).
BACK_CUT = 5.3
SPLIT = 1.6                 # rally zonasi orqa chegarasi — undan oldingi qism (bino, trek) o'zgarmaydi
Z = 0.16                    # yer usti (maydoncha ostidagi plitka 0.1 m dan baland)


def slab(pts, z0, z1, mat):
    bm = bmesh.new()
    bot = [bm.verts.new((x, y, z0)) for x, y in pts]
    top = [bm.verts.new((x, y, z1)) for x, y in pts]
    bm.faces.new(top)
    bm.faces.new(bot[::-1])
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new([bot[i], bot[j], top[j], top[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return k.obj('slab', bm, mat)


def ribbon(pts, zs, width, mat, closed=True, lift=0.02):
    """Chiziq bo'ylab tasma (yo'l): har nuqtada perpendikulyar kesim, balandlik zs bo'yicha"""
    bm = bmesh.new()
    n = len(pts)
    L, R = [], []
    for i in range(n):
        a = pts[(i - 1) % n] if closed or i > 0 else pts[i]
        b = pts[(i + 1) % n] if closed or i < n - 1 else pts[i]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        z = zs[i] + lift
        L.append(bm.verts.new((pts[i][0] + nx * width / 2, pts[i][1] + ny * width / 2, z)))
        R.append(bm.verts.new((pts[i][0] - nx * width / 2, pts[i][1] - ny * width / 2, z)))
    for i in range(n if closed else n - 1):
        j = (i + 1) % n
        bm.faces.new([L[i], R[i], R[j], L[j]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    return k.obj('ribbon', bm, mat)


# ====================== yer qatlamlari ======================
p.append(k.box((2 * HX, 2 * HY, Z), (0, 0, Z / 2), 'base'))
# zonalar (tepada ozgina farq bilan): rally — tuproq, cho'l — qum, o'rmon — qora tuproq
RX0, RX1, RY0, RY1 = 1.2, HX - 0.3, -HY + 0.3, 1.6          # rally
p.append(k.box((RX1 - RX0, RY1 - RY0, 0.02), ((RX0 + RX1) / 2, (RY0 + RY1) / 2, Z + 0.01), 'dirt'))
p.append(k.box((HX - 0.3 - 2.2, HY - 0.3 - 2.0, 0.02), ((2.2 + HX - 0.3) / 2, (2.0 + HY - 0.3) / 2, Z + 0.01), 'sand'))
p.append(k.box((2.0 + HX - 0.3, HY - 0.3 + 4.8, 0.02), ((-HX + 0.3 + 2.0) / 2, (-4.8 + HY - 0.3) / 2, Z + 0.01), 'soil'))
# zonalar orasidagi yog'och to'siqlar
p.append(k.box((HX - 1.8, 0.18, 0.25), ((1.4 + HX) / 2, 1.8, Z + 0.12), 'log'))
p.append(k.box((0.18, 14.0, 0.25), (2.1, 5.2, Z + 0.12), 'log'))

# ====================== rally treki ======================
CX, CY, AX, AY = (RX0 + RX1) / 2, (RY0 + RY1) / 2, (RX1 - RX0) / 2 - 1.4, (RY1 - RY0) / 2 - 1.3
N = 72
track, tz = [], []
for i in range(N):
    t = 2 * math.pi * i / N
    dent = 1.8 * math.exp(-((t - math.pi / 2) / 0.45) ** 2)          # tepada ichkariga botiq (buyrak shakli)
    x = CX + AX * math.cos(t) * (1 + 0.08 * math.cos(2 * t))
    y = CY + (AY - dent) * math.sin(t)
    track.append((x, y))
    hump = 0.0
    for tc in (0.0, math.pi):                                       # ikki sakrash tepaligi (to'g'ri qismlarda)
        dt = math.atan2(math.sin(t - tc - math.pi / 2), math.cos(t - tc - math.pi / 2))
        hump = max(hump, 0.35 * math.exp(-(dt / 0.22) ** 2))
    tz.append(Z + 0.02 + hump)
p.append(ribbon(track, tz, 1.9, 'track'))
def offset_track(d):
    """Trek o'rta chizig'idan d m tashqariga (manfiy — ichkariga) siljigan nuqtalar"""
    out = []
    for i, a in enumerate(track):
        b0, b1 = track[i - 1], track[(i + 1) % N]
        dx, dy = b1[0] - b0[0], b1[1] - b0[1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = dy / ln, -dx / ln                                  # soat strelkasiga teskari aylanishda — tashqariga
        out.append((a[0] + nx * d, a[1] + ny * d))
    return out


p.append(slab(offset_track(-1.05), Z + 0.01, Z + 0.035, 'grass'))   # o'rtadagi maysa (trek ichki chetigacha)
for i, (x, y) in enumerate(offset_track(1.3)):                       # shina to'siqlari (tashqi chetda, oq-qora)
    if i % 2:
        continue
    p.append(k.cyl(0.22, 0.22, (x, y, Z + 0.13), 'tyre' if (i // 2) % 2 else 'white', segs=8))

# ====================== cho'l zonasi ======================
for _ in range(9):                                                  # qum tepaliklari
    x, y = rnd.uniform(3.5, HX - 1.5), rnd.uniform(3.2, HY - 1.5)
    r = rnd.uniform(0.9, 1.8)
    p.append(k.ball(r, (x, y, Z), 'sand_d' if rnd.random() < 0.5 else 'sand', sub=2, scale=(1.3, 1, 0.28)))
for _ in range(7):                                                  # qizg'ish qoyalar
    x, y = rnd.uniform(3.2, HX - 1), rnd.uniform(3, HY - 1)
    p.append(k.ball(rnd.uniform(0.3, 0.6), (x, y, Z + 0.15), 'rock_r', sub=1, scale=(1.2, 0.9, 0.8)))
for x, y, h in ((6.0, 9.5, 1.3), (12.5, 6.0, 1.0), (14.5, 10.5, 1.5), (9.0, 4.2, 0.8)):   # kaktuslar
    p.append(k.cyl(0.13, h, (x, y, Z + h / 2), 'cactus', segs=8))
    p.append(k.ball(0.13, (x, y, Z + h), 'cactus', sub=1))
    for s in (-1, 1):
        p.append(k.beam((x, y, Z + h * 0.5), (x + s * 0.3, y, Z + h * 0.5), 0.12, 0.12, 'cactus'))
        p.append(k.cyl(0.09, h * 0.35, (x + s * 0.3, y, Z + h * 0.5 + h * 0.17), 'cactus', segs=6))
p.append(k.prism_x([(7.2, Z), (8.8, Z), (8.8, Z + 0.55)], 10.0, 11.4, 'plank'))       # sakrash ramasi

# ====================== o'rmon / crawler zonasi ======================
trail = [(-14.5, -3.8), (-11.5, -2.0), (-9.0, 0.5), (-10.5, 3.5), (-7.5, 6.0), (-4.0, 5.0), (-2.0, 8.0), (-5.5, 10.8), (-11.0, 10.5), (-14.0, 8.0)]
p.append(ribbon(trail, [Z + 0.02] * len(trail), 1.0, 'trail', closed=False))
for _ in range(14):                                                 # qoyalar (crawler uchun)
    x, y = rnd.uniform(-15.3, 1.2), rnd.uniform(-4.2, HY - 1)
    r = rnd.uniform(0.35, 0.9)
    p.append(k.ball(r, (x, y, Z + r * 0.35), 'rock', sub=1, scale=(1.3, 1.0, 0.75)))
for x, y, a in ((-6.5, 1.5, 0.4), (-12.5, 5.5, 1.2), (-1.0, 3.0, 2.0), (-8.5, 9.0, 0.1)):  # yog'ochlar
    p.append(k.cyl(0.2, 2.2, (x, y, Z + 0.2), 'log', segs=8, rot=(0, math.pi / 2, a)))
# taxta ko'prik (ko'lmak ustidan)
p.append(k.ball(1.3, (-8.0, 7.6, Z - 0.02), 'water', sub=2, scale=(1.4, 0.8, 0.05)))
for i in range(9):
    x = -9.6 + i * 0.4
    p.append(k.box((0.34, 1.0, 0.06), (x, 7.6, Z + 0.35 + 0.15 * math.sin(math.pi * i / 8)), 'plank'))
for x in (-9.7, -6.3):
    for y in (7.1, 8.1):
        p.append(k.box((0.08, 0.08, 0.4), (x, y, Z + 0.2), 'log'))
# archalar (kichik, past) — ko'rinishi o'rmon
for x, y in ((-15.0, 11.3), (-13.0, 2.2), (-15.2, 5.0), (-3.2, 11.5), (-0.5, 9.8), (-10.0, -2.8), (-6.2, 11.6), (0.6, -0.6), (-15.3, -2.5)):
    h = rnd.uniform(1.8, 2.8)
    p.append(k.cyl(0.1, 0.5, (x, y, Z + 0.25), 'log', segs=6))
    p.append(k.cyl(0.75, h * 0.6, (x, y, Z + 0.4 + h * 0.3), 'pine', segs=7, r2=0.25))
    p.append(k.cyl(0.55, h * 0.5, (x, y, Z + 0.4 + h * 0.65), 'pine_l', segs=7, r2=0.02))

# ====================== bino (rasm: "YETI RC PARK" fasadi) va haydovchilar supasi ======================
# Oynasiz oddiy bino: bej-jigarrang gorizontal siding (panel chiziqlari), tik och yog'och planka, beton sokol, tekis tom;
# fasadda faqat kirish eshigi va katta kulrang lavha ("YETI RC PARK", pultlar va mashinalar rasmi).
BX0, BX1, BY0, BY1, BH = -HX + 0.4, -3.2, -HY + 0.25, -5.6, 3.8
bw, bd = BX1 - BX0, BY1 - BY0
bcx, bcy = (BX0 + BX1) / 2, (BY0 + BY1) / 2
p.append(k.box((bw + 0.06, bd + 0.06, 0.3), (bcx, bcy, Z + 0.15), 'concrete'))                 # beton sokol
p.append(k.box((bw, bd, BH - Z - 0.3), (bcx, bcy, (BH + Z + 0.3) / 2), 'siding'))
SID = 0.24                                                           # siding panel eni
for i in range(int((BH - Z - 0.4) / SID)):                           # panel chiziqlari (to'rt tomonda)
    z = Z + 0.42 + i * SID
    p.append(k.box((bw + 0.02, 0.02, 0.025), (bcx, BY0 - 0.005, z), 'siding_d'))
    p.append(k.box((bw + 0.02, 0.02, 0.025), (bcx, BY1 + 0.005, z), 'siding_d'))
    p.append(k.box((0.02, bd + 0.02, 0.025), (BX0 - 0.005, bcy, z), 'siding_d'))
    p.append(k.box((0.02, bd + 0.02, 0.025), (BX1 + 0.005, bcy, z), 'siding_d'))
for x in [BX0 + 0.05, BX0 + bw / 3, BX0 + 2 * bw / 3, BX1 - 0.05]:   # tik plankalar (old va orqa)
    for y in (BY0 - 0.02, BY1 + 0.02):
        p.append(k.box((0.12, 0.04, BH - Z - 0.3), (x, y, (BH + Z + 0.3) / 2), 'trim'))
for y in (BY0 + 0.05, BY1 - 0.05):
    for x in (BX0 - 0.02, BX1 + 0.02):
        p.append(k.box((0.04, 0.12, BH - Z - 0.3), (x, y, (BH + Z + 0.3) / 2), 'trim'))
p.append(k.box((bw + 0.3, bd + 0.3, 0.2), (bcx, bcy, BH + 0.1), 'trim'))                      # tom chekkasi
p.append(k.box((bw, bd, 0.1), (bcx, bcy, BH + 0.2), 'roof'))
# kirish eshigi (yagona) — o'ng tomonda, haydovchilar supasi yonida
DOOR_X = BX1 - 1.6
p.append(k.box((1.15, 0.06, 2.25), (DOOR_X, BY0 - 0.03, Z + 0.3 + 1.12), 'door'))
p.append(k.box((1.35, 0.08, 0.1), (DOOR_X, BY0 - 0.04, Z + 0.3 + 2.3), 'trim'))
for sx in (-1, 1):
    p.append(k.box((0.1, 0.08, 2.3), (DOOR_X + sx * 0.62, BY0 - 0.04, Z + 0.3 + 1.15), 'trim'))
p.append(k.box((0.05, 0.06, 0.3), (DOOR_X + 0.4, BY0 - 0.08, Z + 0.3 + 1.05), 'steel'))     # tutqich
p.append(k.box((1.6, 1.0, 0.15), (DOOR_X, BY0 - 0.5, Z + 0.075), 'concrete'))               # eshik oldi zinasi
# katta lavha: kulrang, chap tomonda yozuv, o'ngda pultlar va mashinalar rasmi
SW, SH, SZ = 6.4, 2.5, 2.05                                          # lavha eni, balandligi, markazi
SX = BX0 + 0.6 + SW / 2
SY = BY0 - 0.07
p.append(k.box((SW, 0.08, SH), (SX, SY + 0.02, SZ), 'board'))
for i in range(5):                                                   # relyef (kontur) chiziqlari
    p.append(k.box((SW - 0.3, 0.01, 0.02), (SX, SY - 0.025, SZ - 0.9 + i * 0.45), 'board_l'))
FY = SY - 0.05                                                       # lavha yuzasi oldi
LX = SX - SW / 2 + 1.35                                              # yozuv markazi
p.append(k.text('YETI', 0.62, (LX, FY, SZ + 0.68), 'orange', face='-Y', depth=0.05))
p.append(k.box((1.75, 0.03, 0.62), (LX, FY + 0.02, SZ + 0.05), 'blue'))
p.append(k.text('RC', 0.62, (LX, FY - 0.01, SZ + 0.05), 'orange', face='-Y', depth=0.05))
p.append(k.box((1.75, 0.03, 0.5), (LX, FY + 0.02, SZ - 0.55), 'white'))
p.append(k.text('PARK', 0.46, (LX, FY - 0.01, SZ - 0.55), 'green_d', face='-Y', depth=0.05))
p.append(k.text('RC CARS SPACE', 0.16, (LX, FY, SZ - 1.0), 'white', face='-Y', depth=0.02))


def flat_remote(x, z, s, accent):
    """Lavhadagi pult rasmi (yassi): tutqich, bosh qismi, rul g'ildiragi"""
    p.append(k.beam((x + 0.05 * s, FY, z - 0.45 * s), (x + 0.15 * s, FY, z), 0.16 * s, 0.03, 'black'))
    p.append(k.box((0.55 * s, 0.03, 0.25 * s), (x + 0.05 * s, FY, z + 0.08 * s), 'black'))
    p.append(k.cyl(0.16 * s, 0.04, (x - 0.2 * s, FY - 0.02, z + 0.05 * s), accent, segs=12, rot=(math.pi / 2, 0, 0)))
    p.append(k.box((0.35 * s, 0.03, 0.08 * s), (x + 0.1 * s, FY, z - 0.48 * s), accent))


def flat_car(x, z, s, body, low):
    """Lavhadagi mashina rasmi (yassi, yon ko'rinish)"""
    p.append(k.box((1.3 * s, 0.03, 0.28 * s), (x, FY, z), body))
    p.append(k.box((0.7 * s, 0.03, 0.22 * s), (x - 0.05 * s, FY, z + 0.24 * s), body))
    p.append(k.box((0.5 * s, 0.035, 0.14 * s), (x - 0.05 * s, FY - 0.005, z + 0.25 * s), 'glass_d'))
    p.append(k.box((1.3 * s, 0.035, 0.07 * s), (x, FY - 0.005, z - 0.1 * s), low))
    for wx in (-0.42, 0.42):
        p.append(k.cyl(0.17 * s, 0.05, (x + wx * s, FY - 0.02, z - 0.15 * s), 'tyre', segs=12, rot=(math.pi / 2, 0, 0)))


flat_remote(SX + 0.1, SZ + 0.55, 1.0, 'red')
flat_car(SX + 1.9, SZ + 0.55, 1.15, 'white', 'blue')                 # oq poyga mashinasi (277)
flat_car(SX + 0.6, SZ - 0.6, 1.1, 'red', 'black')                   # qizil jip
p.append(k.box((0.9, 0.04, 0.08), (SX + 0.6, FY - 0.01, SZ - 0.18), 'black'))              # jip tomidagi yuk
flat_remote(SX + 2.45, SZ - 0.55, 1.0, 'blue')
# haydovchilar supasi: baland taxta pol, panjara, zina (trek tomonga qaragan)
DX0, DX1, DY0, DY1, DH = -2.9, 0.6, -10.6, -6.4, 1.3
p.append(k.box((DX1 - DX0, DY1 - DY0, 0.12), ((DX0 + DX1) / 2, (DY0 + DY1) / 2, DH), 'plank'))
for x in (DX0 + 0.15, DX1 - 0.15):
    for y in (DY0 + 0.15, DY1 - 0.15):
        p.append(k.box((0.14, 0.14, DH), (x, y, DH / 2), 'steel'))
for (xa, ya), (xb, yb) in (((DX0, DY1), (DX1, DY1)), ((DX1, DY0), (DX1, DY1)), ((DX0, DY0), (DX0 + 1.8, DY0))):
    p.append(k.beam((xa, ya, DH + 1.0), (xb, yb, DH + 1.0), 0.06, 0.06, 'orange'))
    p.append(k.beam((xa, ya, DH + 0.5), (xb, yb, DH + 0.5), 0.04, 0.04, 'steel'))
    for t in (0, 0.5, 1):
        p.append(k.box((0.06, 0.06, 1.0), (xa + (xb - xa) * t, ya + (yb - ya) * t, DH + 0.5), 'steel'))
for i in range(5):                                                   # zina (oldidan)
    h = DH * (i + 1) / 6
    p.append(k.box((1.2, 0.3, h), (DX1 - 0.75, DY0 - 1.5 + i * 0.3, h / 2), 'plank'))
p.append(k.box((DX1 - DX0, 0.4, 0.4), ((DX0 + DX1) / 2, DY1 - 0.3, DH + 0.3), 'black'))   # pult stoli

# ====================== panjara (bino va supa oldida kirish) ======================
fence = [(1.6, -HY + 0.15), (HX - 0.15, -HY + 0.15), (HX - 0.15, HY - 0.15), (-HX + 0.15, HY - 0.15), (-HX + 0.15, BY1 + 0.2), (BX0 + 0.1, BY1 + 0.2)]
for a, b in zip(fence, fence[1:]):
    L = math.dist(a, b)
    n = max(1, round(L / 2.0))
    for i in range(n + 1):
        t = i / n
        p.append(k.box((0.08, 0.08, 1.2), (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, Z + 0.6), 'fence'))
    for z in (Z + 0.2, Z + 0.7, Z + 1.15):
        p.append(k.beam((a[0], a[1], z), (b[0], b[1], z), 0.04, 0.04, 'fence'))

# ====================== crawler mashinalar (qoyada, qimirlamaydi) va trekdagi RC mashinalar ======================
def rc_car(col, scale=1.0):
    s = scale
    q = [k.box((0.75 * s, 0.42 * s, 0.14 * s), (0, 0, 0.3 * s), col),
         k.box((0.38 * s, 0.36 * s, 0.14 * s), (-0.05 * s, 0, 0.43 * s), 'black'),
         k.box((0.08 * s, 0.5 * s, 0.05 * s), (-0.36 * s, 0, 0.5 * s), col)]                 # qanot (spoiler)
    for wx in (0.27 * s, -0.27 * s):
        for wy in (-0.26 * s, 0.26 * s):
            q.append(k.cyl(0.16 * s, 0.13 * s, (wx, wy, 0.16 * s), 'tyre', segs=10, rot=(math.pi / 2, 0, 0)))
    return q


# ---------- bino tomida reklama haykallari: katta RC mashina va katta pult (uzoqdan ko'rinsin) ----------
ROOF = BH + 0.25
p.append(k.box((4.6, 3.2, 0.18), (bcx - 2.6, bcy + 0.6, ROOF + 0.09), 'orange'))        # mashina supasi
show = k.join('show_car', rc_car('green', 4.4))
show.rotation_euler = (0, 0, math.radians(-28))
show.location = (bcx - 2.6, bcy + 0.6, ROOF + 0.18)
p.append(show)
# pult (pistolet tutqichli transmitter): bosh qismi, yon tomonda rul g'ildiragi, pastga tutqich, tepkich, antenna
RX_, RY_, RZ0, RS = bcx + 3.0, bcy + 0.8, ROOF, 1.4                         # RS — pult kattaligi


def rp(dx, dy, dz):
    """Pultning mahalliy nuqtasi → model koordinatasi (RS marta kattalashtirilgan)"""
    return (RX_ + dx * RS, RY_ + dy * RS, RZ0 + dz * RS)


p.append(k.box((1.0 * RS, 1.0 * RS, 0.2), rp(0, 0, 0.1 / RS), 'black'))                   # tagkursi
p.append(k.beam(rp(0.15, 0, 0.2), rp(0.45, 0, 1.45), 0.42 * RS, 0.34 * RS, 'black'))      # tutqich
p.append(k.box((0.12 * RS, 0.2 * RS, 0.32 * RS), rp(-0.1, 0, 1.35), 'orange'))            # tepkich (gaz)
p.append(k.box((1.5 * RS, 0.55 * RS, 0.6 * RS), rp(0.05, 0, 1.75), 'black'))              # bosh qismi
p.append(k.box((1.52 * RS, 0.57 * RS, 0.1 * RS), rp(0.05, 0, 1.6), 'orange'))             # to'q sariq hoshiya
p.append(k.box((0.45 * RS, 0.05 * RS, 0.3 * RS), rp(0.35, -0.29, 1.85), 'glass'))         # ekran
p.append(k.cyl(0.42 * RS, 0.12 * RS, rp(-0.35, -0.4, 1.6), 'tyre', segs=16, rot=(math.pi / 2, 0, 0)))   # rul g'ildiragi
p.append(k.cyl(0.26 * RS, 0.14 * RS, rp(-0.35, -0.4, 1.6), 'orange', segs=12, rot=(math.pi / 2, 0, 0)))
p.append(k.beam(rp(-0.35, -0.28, 1.6), rp(-0.35, -0.4, 1.6), 0.08 * RS, 0.08 * RS, 'steel'))
p.append(k.cyl(0.035 * RS, 1.3 * RS, rp(0.6, 0.1, 2.65), 'steel', segs=6))                # antenna
p.append(k.ball(0.07 * RS, rp(0.6, 0.1, 3.3), 'red', sub=1))


for (x, y, zz, a, col) in ((-12.2, 2.4, 0.5, 0.6, 'green'), (-4.5, 7.4, 0.35, 2.5, 'red')):
    parts = rc_car(col, 1.1)
    for o in parts:
        o.location = (o.location.x, o.location.y, o.location.z)
    ob = k.join('crawler', parts)
    ob.rotation_euler = (0.15, 0, a)
    ob.location = (x, y, Z + zz)
    p.append(ob)

cars = []
for i, col in enumerate(('red', 'yellow', 'blue', 'green')):
    cars.append(k.join(f'car{i}', rc_car(col, 1.25)))

L_track = sum(math.dist(a, b) for a, b in zip(track, track[1:] + track[:1]))
spacing = L_track / len(cars) * 0.37                                 # to'da bo'lib yurishadi (poyga)
cum = [0.0]
for a, b in zip(track, track[1:] + track[:1]):
    cum.append(cum[-1] + math.dist(a, b))
for i, c in enumerate(cars):
    s = (L_track - i * spacing) % L_track
    j = max(m for m in range(N) if cum[m] <= s)
    a, b = track[j], track[(j + 1) % N]
    c.location = (a[0], a[1], tz[j] + 0.02)
    c.rotation_euler = (0, 0, math.atan2(b[1] - a[1], b[0] - a[0]))
# ---------- orqa qismni siqish va markazni izga surish ----------
HB = HY - BACK_CUT                                                   # yangi orqa chegara
KB = (HB - SPLIT) / (HY - SPLIT)
SHIFT = (HY - HB) / 2                                                # [-HY, HB] o'rtasi → 0


def remap(y):
    return y if y <= SPLIT else SPLIT + (y - SPLIT) * KB


from mathutils import Matrix  # noqa: E402

for ob in p:
    ys = [(ob.matrix_world @ v.co).y for v in ob.data.vertices]
    if max(ys) - min(ys) > 3.0 and max(ys) > SPLIT:
        # katta yuza (zamin, zona, panjara, so'qmoq) — tepalari bo'yicha cho'ziladi
        ob.data.transform(ob.matrix_world)
        ob.matrix_world = Matrix.Identity(4)
        for v in ob.data.vertices:
            v.co.y = remap(v.co.y)
    else:
        # mayda narsa (archa, qoya, kaktus, mashina) — shakli saqlanadi, faqat ko'chadi
        cy = (max(ys) + min(ys)) / 2
        ob.location.y += remap(cy) - cy
    ob.location.y += SHIFT
for c in cars:
    c.location.y += SHIFT
track = [(x, y + SHIFT) for x, y in track]

(HERE / 'track.json').write_text(json.dumps({
    'closed': True,
    'points': [[round(x, 3), round(zz + 0.02, 3), round(-y, 3)] for (x, y), zz in zip(track, tz)],
    'cars': [{'name': c.name, 'offset': round(i * spacing, 3)} for i, c in enumerate(cars)],
    'station': 0,
}, separators=(',', ':')))
print(f'RC-PARK track={L_track:.1f}m')

k.finish('RC-PARK', p, HERE, [
    ('preview.png', (14.0, -30.0, 18.0), (1.0, 0, 0.5)),
    ('preview_roof.png', (-4.0, -22.0, 10.0), (-9.5, -8.5, 4.5)),
    ('preview_front.png', (-8.0, -24.0, 3.2), (-9.3, -12.0, 2.3)),
    ('preview_top.png', (0.01, -4.0, 42.0), (0, 0, 0)),
])

"""
Kassa (chipta sotish budkasi) — foydalanuvchi fotosurati bo'yicha (attraction-images-park/kasa.png):
krem rangli plastik (stekloplastik) budka — vertikal qirralari qiya kesilgan, pastida ozgina kengroq sokol, tepasida
chetlari chiqib turgan qopqoq. Old tomonida bo'rtma ramkali kassa oynasi (tepada metall reyka, ichida e'lonlar —
ko'k va qizil sarlavhali oq qog'ozlar, pastki qismida surma oyna va pul uzatish tokchasi), pastda chuqurlashgan
to'rtburchak panel. Chap old qirrada ko'k "Kassa bu yerda" stikeri va QR-kodlar (Click, Payme).
Tepasida — qora dumaloq belgi: oq hoshiya, "КАССА" / "GAZNA" yozuvlari, o'rtada budka belgisi (kechasi yonadi).
Orqa tomonda kassir eshigi (dastagi, qulfi bilan), yonlarda shamollatish panjarasi.

Ishga tushirish (loyiha ildizidan):
    D:/blender-program/blender.exe -b --factory-startup -P src/decor/kassa/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png, preview_back.png

Old tomoni (oyna) — Blender'da -Y. Asl o'lcham: 1.4 × 1.0 m, balandligi ~2.6 m (belgi bilan).
"""
import math
import random
import sys
from pathlib import Path

import bmesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from blender_kit import Kit  # noqa: E402

random.seed(3)
PALETTE = {
    'shell': (0.93, 0.88, 0.76), 'shell_d': (0.83, 0.78, 0.66), 'shell_l': (0.97, 0.94, 0.85), 'seam': (0.62, 0.59, 0.53),
    'glass': (0.6, 0.7, 0.75), 'inside': (0.12, 0.1, 0.09), 'paper': (0.97, 0.97, 0.95), 'ink': (0.35, 0.35, 0.38),
    'blue': (0.1, 0.55, 0.85), 'red': (0.85, 0.15, 0.15), 'steel': (0.6, 0.6, 0.62), 'dark': (0.15, 0.15, 0.16),
    'sign': (0.17, 0.17, 0.18), 'sign_w': (0.95, 0.95, 0.95), 'qr': (0.05, 0.05, 0.05), 'sticker': (0.1, 0.55, 0.9),
}
k = Kit(PALETTE, glow=('sign_w',), glass=('glass',), glass_alpha=0.3)
p = []

# ====================== o'lchamlar ======================
Z0 = 0.12                    # xaritadagi yo'l plitkasi sathi
W, D = 1.36, 0.96            # eni (old tomon bo'ylab), chuqurligi
C = 0.14                     # vertikal qirralar qiyaligi
H = 2.15                     # korpus tepasi (Z0 dan)
YF = -D / 2                  # old yuza


def octagon(w, d, c):
    x, y = w / 2, d / 2
    return [(-x + c, -y), (x - c, -y), (x, -y + c), (x, y - c), (x - c, y), (-x + c, y), (-x, y - c), (-x, -y + c)]


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


def front(w, h, x, z, depth, mat, y=YF):
    """Old yuzadan `depth` ga chiqib turgan to'rtburchak (x, z — markazi)"""
    return k.box((w, depth, h), (x, y - depth / 2, z), mat)


def frame(w, h, x, z, t, depth, mat, y=YF):
    """Old yuzadagi bo'rtma ramka (ichi ochiq)"""
    return [front(w, t, x, z + h / 2 - t / 2, depth, mat, y), front(w, t, x, z - h / 2 + t / 2, depth, mat, y),
            front(t, h - 2 * t, x - w / 2 + t / 2, z, depth, mat, y), front(t, h - 2 * t, x + w / 2 - t / 2, z, depth, mat, y)]


# ---------- korpus: sokol, qiya qirrali tana, qopqoq ----------
p.append(prism(octagon(W + 0.05, D + 0.05, C + 0.02), 0.0, Z0 + 0.1, 'shell_d'))          # sokol
p.append(prism(octagon(W, D, C), Z0 + 0.1, Z0 + H, 'shell'))
p.append(prism(octagon(W + 0.08, D + 0.08, C + 0.03), Z0 + H, Z0 + H + 0.07, 'shell_l'))  # qopqoq
p.append(prism(octagon(W - 0.02, D - 0.02, C), Z0 + H + 0.07, Z0 + H + 0.1, 'shell_d'))
# qiya qirralardagi tikuvlar (old va orqa panellar yon bilan qo'shilgan joy)
for sx in (-1, 1):
    for sy in (-1, 1):
        x, y = sx * (W / 2 - C), sy * D / 2
        p.append(k.box((0.012, 0.012, H - 0.12), (x, y + sy * 0.003, Z0 + 0.1 + (H - 0.12) / 2), 'seam'))
        x, y = sx * W / 2, sy * (D / 2 - C)
        p.append(k.box((0.012, 0.012, H - 0.12), (x + sx * 0.003, y, Z0 + 0.1 + (H - 0.12) / 2), 'seam'))
# sokol ustidagi gorizontal tikuv
p.append(prism(octagon(W + 0.012, D + 0.012, C), Z0 + 0.1, Z0 + 0.115, 'seam'))

# ---------- kassa oynasi ----------
WZ = Z0 + 1.42                # oyna bloki markazi
p.append(front(0.86, 1.0, 0, WZ, 0.025, 'shell_l'))                    # tashqi bo'rtma panel
p += frame(0.86, 1.0, 0, WZ, 0.035, 0.035, 'shell_d')                  # uning cheti
p += frame(0.72, 0.84, 0, WZ, 0.06, 0.06, 'shell_l', y=YF - 0.025)     # ichki ramka (qalin)
GW, GH = 0.58, 0.72
p.append(front(GW, GH, 0, WZ, 0.012, 'inside', y=YF - 0.02))           # ichkari (qorong'i)
# e'lonlar — yuqori qism, ikki ustun
for cx in (-0.145, 0.145):
    p.append(front(0.27, 0.36, cx, WZ + 0.15, 0.004, 'paper', y=YF - 0.032))
    for j in range(7):
        zz = WZ + 0.31 - j * 0.045
        if j in (0, 3) or (cx > 0 and j == 5):
            p.append(front(0.24, 0.022, cx, zz, 0.003, 'blue' if not (cx > 0 and j == 5) else 'red', y=YF - 0.036))
        else:
            ln = random.uniform(0.14, 0.23)
            p.append(front(ln, 0.008, cx - (0.23 - ln) / 2, zz, 0.003, 'ink', y=YF - 0.036))
# pastki qism: qog'ozlar va qizil yorliq, o'rtada gorizontal ajratgich
p.append(front(GW, 0.025, 0, WZ - 0.04, 0.02, 'steel', y=YF - 0.032))
p.append(front(0.22, 0.15, -0.15, WZ - 0.15, 0.004, 'paper', y=YF - 0.032))
p.append(front(0.22, 0.12, 0.13, WZ - 0.13, 0.004, 'paper', y=YF - 0.032))
for j in range(4):
    p.append(front(0.17, 0.007, 0.13, WZ - 0.09 - j * 0.022, 0.003, 'ink', y=YF - 0.036))
p.append(front(0.2, 0.03, -0.12, WZ - 0.24, 0.004, 'red', y=YF - 0.036))
# oyna (shisha), tepada metall reyka, pastda surma oyna izi va pul tokchasi
p.append(front(GW, GH, 0, WZ, 0.004, 'glass', y=YF - 0.05))
p.append(front(GW + 0.02, 0.03, 0, WZ + GH / 2 - 0.02, 0.03, 'steel', y=YF - 0.03))
p.append(front(GW, 0.012, 0, WZ - 0.2, 0.01, 'steel', y=YF - 0.05))
p.append(front(0.5, 0.025, 0, WZ - GH / 2 - 0.02, 0.12, 'shell_d', y=YF - 0.03))           # tokcha
p.append(front(0.3, 0.015, 0, WZ - GH / 2 - 0.0, 0.09, 'steel', y=YF - 0.03))

# ---------- pastki chuqurlashgan panel ----------
PZ = Z0 + 0.5
p.append(front(0.86, 0.36, 0, PZ, 0.012, 'shell_l'))
p += frame(0.86, 0.36, 0, PZ, 0.05, 0.03, 'shell_d')
p += frame(0.76, 0.26, 0, PZ, 0.02, 0.022, 'shell_l', y=YF - 0.012)

# ---------- chap old qirradagi stikerlar: ko'k "Kassa bu yerda" va QR-kodlar ----------
cx0, cy0 = -(W / 2 - C / 2), -(D / 2 - C / 2)          # qiya qirra markazi
rot = math.atan2(C, C)                                  # qiya yuza burchagi (45°)
nx, ny = -math.sin(math.pi / 4), -math.cos(math.pi / 4)   # tashqi normal


def chamfer_box(u, z, w, h, depth, mat, off=0.0):
    """Chap old qiya yuzaga yopishgan to'rtburchak; u — yuza bo'ylab (o'ngga +), z — balandlik"""
    ux, uy = math.cos(-rot), math.sin(-rot)
    x = cx0 + ux * u + nx * (off + depth / 2)
    y = cy0 + uy * u + ny * (off + depth / 2)
    return k.box((w, depth, h), (x, y, z), mat, rot=(0, 0, -rot))


p.append(chamfer_box(-0.02, Z0 + 1.45, 0.11, 0.2, 0.004, 'sticker'))
p.append(chamfer_box(-0.02, Z0 + 1.51, 0.08, 0.018, 0.003, 'paper', 0.004))
p.append(chamfer_box(-0.02, Z0 + 1.47, 0.08, 0.018, 0.003, 'paper', 0.004))
for i, zq in enumerate((Z0 + 1.2, Z0 + 1.32, Z0 + 1.62)):
    p.append(chamfer_box(0.0, zq, 0.11, 0.11, 0.004, 'paper'))
    for a in range(5):                                  # QR "piksellari"
        for b in range(5):
            corner = (a < 2 and b < 2) or (a > 2 and b < 2) or (a < 2 and b > 2)
            if corner and not (a in (0, 4) or b in (0, 4) or (a, b) in ((1, 1), (3, 1), (1, 3))):
                continue
            if corner or random.random() < 0.45:
                p.append(chamfer_box(-0.04 + a * 0.02, zq + 0.04 - b * 0.02, 0.018, 0.018, 0.002, 'qr', 0.004))

# ---------- tepadagi dumaloq belgi: "КАССА / GAZNA" ----------
SZ, SR = Z0 + H + 0.18, 0.32                            # belgi markazi va radiusi
SY = YF - 0.05                                          # qopqoq old chetidan oldinda
p.append(k.disc_y(SR, SY - 0.0, SZ, 0, 0.04, 'sign_w', segs=40))     # oq hoshiya
p.append(k.disc_y(SR - 0.025, SY - 0.025, SZ, 0, 0.012, 'sign', segs=40))
p.append(k.disc_y(SR - 0.05, SY - 0.033, SZ, 0, 0.004, 'sign_w', segs=40))   # ichki ingichka halqa
p.append(k.disc_y(SR - 0.06, SY - 0.037, SZ, 0, 0.004, 'sign', segs=40))
p.append(k.disc_y(SR - 0.025, SY + 0.025, SZ, 0, 0.012, 'sign', segs=40))   # orqa yuzasi ham qora
TY = SY - 0.045
p.append(k.text('КАССА', 0.085, (0, TY, SZ + 0.17), 'sign_w', depth=0.008))
p.append(k.text('GAZNA', 0.085, (0, TY, SZ - 0.18), 'sign_w', depth=0.008))
p.append(k.text('КАССА', 0.085, (0, SY + 0.04, SZ + 0.17), 'sign_w', face='+Y', depth=0.008))
p.append(k.text('GAZNA', 0.085, (0, SY + 0.04, SZ - 0.18), 'sign_w', face='+Y', depth=0.008))
# o'rtadagi budka belgisi: tom (chiziqli soyabon), tana, oyna — oq chiziqlar
IW, IH = 0.13, 0.17
for y_, face in ((TY, -1), (SY + 0.04, 1)):
    def ic(w, h, x, z, m='sign_w'):
        return k.box((w, 0.006, h), (x, y_, SZ + z), m)
    p.append(ic(IW + 0.05, 0.012, 0, 0.075))           # soyabon tepasi
    for j in range(5):                                  # soyabon chiziqlari
        p.append(ic(0.012, 0.045, -0.07 + j * 0.035, 0.05))
    p.append(ic(IW + 0.05, 0.01, 0, 0.026))
    for x in (-IW / 2, IW / 2):                        # tana yon chiziqlari
        p.append(ic(0.012, IH - 0.04, x, -0.06))
    p.append(ic(IW, 0.012, 0, -0.14))
    p.append(ic(0.07, 0.01, 0, 0.0))                    # oyna
    p.append(ic(0.07, 0.01, 0, -0.06))
    p.append(ic(0.01, 0.06, -0.035, -0.03))
    p.append(ic(0.01, 0.06, 0.035, -0.03))
    p.append(ic(0.01, 0.06, 0, -0.03))
# belgi tutqichi (qopqoqqa mahkamlangan)
p.append(k.box((0.08, 0.04, 0.12), (0, SY + 0.04, Z0 + H + 0.05), 'dark'))

# ---------- orqa tomonda kassir eshigi ----------
YB = D / 2
DW, DH = 0.7, 1.85
p.append(k.box((DW, 0.01, DH), (0, YB + 0.005, Z0 + 0.14 + DH / 2), 'shell_l'))
for x in (-DW / 2, DW / 2):
    p.append(k.box((0.012, 0.016, DH), (x, YB + 0.008, Z0 + 0.14 + DH / 2), 'seam'))
p.append(k.box((DW, 0.016, 0.012), (0, YB + 0.008, Z0 + 0.14 + DH), 'seam'))
p.append(k.box((0.5, 0.012, 0.3), (0, YB + 0.012, Z0 + 0.6), 'shell_d'))           # eshikdagi panel
p.append(k.box((0.5, 0.012, 0.5), (0, YB + 0.012, Z0 + 1.45), 'shell_d'))
p.append(k.box((0.025, 0.05, 0.16), (DW / 2 - 0.08, YB + 0.03, Z0 + 1.05), 'steel'))   # dastak
p.append(k.cyl(0.018, 0.02, (DW / 2 - 0.08, YB + 0.015, Z0 + 1.2), 'dark', segs=10, rot=(math.pi / 2, 0, 0)))  # qulf

# ---------- yonlarda shamollatish panjarasi va kabel kirishi ----------
for sx in (-1, 1):
    for j in range(6):
        p.append(k.box((0.012, 0.3, 0.018), (sx * (W / 2 + 0.006), 0.1, Z0 + H - 0.25 - j * 0.04), 'dark'))
    p.append(k.box((0.01, 0.34, 0.27), (sx * (W / 2 + 0.002), 0.1, Z0 + H - 0.35), 'shell_d'))
p.append(k.cyl(0.03, 0.2, (W / 2 - 0.25, D / 2 - 0.12, Z0 + 0.0), 'dark', segs=8))

k.finish('KASSA', p, HERE, [
    ('preview.png', (-2.8, -5.0, 2.3), (0, 0, 1.35)),
    ('preview_sign.png', (0, -2.2, 2.5), (0, 0, 2.3)),
    ('preview_back.png', (3.0, 4.4, 2.2), (0, 0, 1.3)),
])

"""
"EASY Box — casual food" kafesi (planda building-131) — foydalanuvchi fotosurati bo'yicha:
bir qavatli bino, och kulrang-bej tosh plitkali devorlar va pilyastrlar, granit sokol, katta to'q oynalar (pastida
xira tasma "EASY"), jigarrang suv quvurlari, oq karniz; to'q kulrang shingl to'rt qiyali tom, old qiyalikda uchta qizil
g'ishtli mansard (o'rtadagisi kattaroq), mansardlar orasida qora "EASY Box / casual food" peshtaxtasi (kechasi yonadi),
o'ng burchakda firuza dumaloq osma belgi. Oldida uchta skameyka va rangli axlat qutilari (qizil, sariq, yashil).

O'qlar: old tomon — Blender -Y, origin — iz markazi. Iz: W × D (building.ts dagi rect); old devor izdan 1.5 m ichkarida —
skameykalar iz ichida qoladi.

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/decor/easy-box/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png, preview_top.png
"""
import sys
from pathlib import Path

import bmesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from blender_kit import Kit  # noqa: E402

PALETTE = {
    'stone': (0.72, 0.68, 0.6), 'stone_d': (0.62, 0.58, 0.5), 'granite': (0.38, 0.38, 0.4), 'paving': (0.5, 0.5, 0.52),
    'glass': (0.12, 0.15, 0.17), 'frame': (0.2, 0.2, 0.22), 'frost': (0.78, 0.8, 0.8), 'pipe': (0.36, 0.2, 0.14),
    'cornice': (0.93, 0.92, 0.9), 'roof': (0.27, 0.26, 0.27), 'roof_l': (0.34, 0.33, 0.34),
    'brick': (0.62, 0.25, 0.18), 'trim': (0.95, 0.94, 0.92), 'sign': (0.06, 0.06, 0.07), 'sign_w': (0.98, 0.95, 0.85),
    'teal': (0.1, 0.62, 0.6), 'wood': (0.85, 0.55, 0.2), 'iron': (0.08, 0.08, 0.09),
    'bin_r': (0.85, 0.12, 0.1), 'bin_y': (0.95, 0.6, 0.1), 'bin_g': (0.15, 0.65, 0.2), 'lamp': (0.1, 0.1, 0.1),
}
k = Kit(PALETTE, glow=('sign_w',))
_g = k.mats['glass'].node_tree.nodes['Principled BSDF']
_g.inputs['Roughness'].default_value = 0.08
_g.inputs['Metallic'].default_value = 0.4
p = []

# ---------- o'lchamlar, m ----------
W, D = 13.0, 12.8
X0, X1 = -W / 2 + 0.6, W / 2 - 0.6          # devorlar (X)
Y0, Y1 = -D / 2 + 1.5, D / 2 - 0.6          # old / orqa devor (Y)
PL = 0.45                                   # granit sokol
WH = 3.5                                    # devor tepasi
OV = 0.55                                   # tom chiqishi
RH = 2.4                                    # tom balandligi (karnizdan qirragacha)
wx, wy = X1 - X0, Y1 - Y0
cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2

# ---------- yer plitasi, sokol, devorlar ----------
p.append(k.box((W, D, 0.06), (0, 0, 0.03), 'paving'))
p.append(k.box((wx + 0.12, wy + 0.12, PL), (cx, cy, PL / 2), 'granite'))
p.append(k.box((wx, wy, WH - PL), (cx, cy, (PL + WH) / 2), 'stone'))
# karniz (oq tasma) va soffit
p.append(k.box((wx + 0.3, wy + 0.3, 0.32), (cx, cy, WH + 0.08), 'cornice'))


# ---------- oynalar: old devorda ikki katta guruh, yonlarda bittadan ----------
def window_front(xc, w, y, face):
    """face: -1 — old (−Y), +1 — orqa; ramka, oyna, pastida xira tasma"""
    z0, z1 = 0.75, 2.95
    d = face * 0.03
    parts = [k.box((w, 0.06, z1 - z0), (xc, y + d, (z0 + z1) / 2), 'glass'),
             k.box((w, 0.08, 0.62), (xc, y + d * 1.6, z0 + 0.31), 'frost')]
    for i in range(4):   # tik ramkalar
        x = xc - w / 2 + w * i / 3
        parts.append(k.box((0.09, 0.1, z1 - z0), (x, y + d * 2, (z0 + z1) / 2), 'frame'))
    for z in (z0, z0 + 0.62, z1):
        parts.append(k.box((w + 0.09, 0.1, 0.08), (xc, y + d * 2, z), 'frame'))
    for i in range(2):   # xira tasmadagi "EASY" yozuvlari
        if face < 0:
            parts.append(k.text('EASY', 0.18, (xc - w / 4 + i * w / 2, y - 0.09, z0 + 0.3), 'stone_d'))
    return parts


GROUPS = [(-3.4, 3.4), (1.6, 3.4)]          # (markaz, eni) — old devor
for xc, w in GROUPS:
    p += window_front(xc, w, Y0, -1)
p += window_front(4.6, 0.9, Y0, -1)[:1]     # o'ngdagi tor oyna (faqat oyna)
p.append(k.box((0.9, 0.1, 0.08), (4.6, Y0 - 0.06, 2.95), 'frame'))
for xc in (-2.0, 2.0):
    p += window_front(xc, 2.6, Y1, 1)
# yon devorlardagi oynalar
for side in (-1, 1):
    x = side * X1 if side > 0 else X0
    for yc in (cy - 2.0, cy + 2.0):
        p.append(k.box((0.06, 2.2, 2.0), (x + side * 0.03, yc, 1.95), 'glass'))
        p += k.frame_x(x + side * 0.06, yc, 1.95, 2.2, 2.0, 0.09, 'frame', depth=0.08)
# pilyastrlar (tosh ustunlar, biroz chiqib turadi) va suv quvurlari
for x in (X0 + 0.35, -0.85, 3.85, X1 - 0.35):
    p.append(k.box((0.75, 0.16, WH - PL), (x, Y0 - 0.08, (PL + WH) / 2), 'stone_d'))
for x in (X0 + 0.75, -1.25, 3.45, X1 - 0.75):
    p.append(k.cyl(0.06, WH - 0.2, (x, Y0 - 0.22, (WH - 0.2) / 2 + 0.1), 'pipe', segs=8))
# devor chiroqlari (qora)
for x in (X0 + 0.35, -0.85, 3.85, X1 - 0.35):
    p.append(k.box((0.12, 0.14, 0.3), (x, Y0 - 0.22, 2.2), 'lamp'))


# ---------- to'rt qiyali tom ----------
def hip_roof(x0, x1, y0, y1, z0, h, ridge_frac, mat):
    bm = bmesh.new()
    a = [bm.verts.new(v) for v in ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0))]
    rl = (x1 - x0) * ridge_frac / 2
    my = (y0 + y1) / 2
    mx = (x0 + x1) / 2
    r1, r2 = bm.verts.new((mx - rl, my, z0 + h)), bm.verts.new((mx + rl, my, z0 + h))
    bm.faces.new([a[0], a[1], r2, r1])      # old qiyalik
    bm.faces.new([a[1], a[2], r2])
    bm.faces.new([a[2], a[3], r1, r2])
    bm.faces.new([a[3], a[0], r1])
    bm.faces.new([a[3], a[2], a[1], a[0]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return k.obj('roof', bm, mat)


RZ = WH + 0.24
p.append(hip_roof(X0 - OV, X1 + OV, Y0 - OV, Y1 + OV, RZ, RH, 0.25, 'roof'))
# shingl qatorlari (old qiyalikda ingichka chiziqlar)
slope_d = cy - (Y0 - OV)
for i in range(1, 6):
    t = i / 6
    y = (Y0 - OV) + slope_d * t
    z = RZ + RH * t + 0.02
    half = (wx / 2 + OV) * (1 - t) + (wx / 2 + OV) * 0.25 * t
    p.append(k.box((2 * half, 0.05, 0.03), (cx, y, z), 'roof_l'))


# ---------- mansardlar (qizil g'isht, ikki qiyali tom, oq ramkali deraza) ----------
def dormer(xc, w, h, y_front):
    """y_front — old yuzi; tom qiyaligiga botib turadi"""
    parts = []
    dep = 2.4
    zb = RZ + 0.2
    parts.append(k.box((w, dep, h), (xc, y_front + dep / 2, zb + h / 2), 'brick'))
    parts.append(k.box((w + 0.1, 0.08, 0.16), (xc, y_front - 0.02, zb + h - 0.2), 'trim'))      # oq tasma
    ww, wh = w * 0.5, h * 0.42
    parts.append(k.box((ww, 0.06, wh), (xc, y_front - 0.03, zb + h * 0.45), 'glass'))
    parts += k.frame_y(xc, y_front - 0.05, zb + h * 0.45, ww, wh, 0.12, 'pipe', depth=0.06)
    parts.append(k.box((0.05, 0.07, wh), (xc, y_front - 0.06, zb + h * 0.45), 'frame'))
    parts.append(k.box((ww, 0.07, 0.05), (xc, y_front - 0.06, zb + h * 0.45), 'frame'))
    # ikki qiyali tom (old tomonga frontón)
    rh = w * 0.42
    parts.append(k.prism_x([(y_front - 0.3, zb + h), (y_front + dep, zb + h), (y_front + dep, zb + h + rh),
                            (y_front - 0.3, zb + h + rh)], xc - 0.01, xc + 0.01, 'roof'))
    parts.append(k.prism_y([(xc - w / 2 - 0.25, zb + h), (xc + w / 2 + 0.25, zb + h), (xc, zb + h + rh)],
                           y_front - 0.3, y_front + dep, 'roof'))
    parts.append(k.prism_y([(xc - w / 2 + 0.05, zb + h - 0.02), (xc + w / 2 - 0.05, zb + h - 0.02), (xc, zb + h + rh - 0.15)],
                           y_front - 0.02, y_front + 0.2, 'brick'))
    return parts


YD = Y0 - OV + 0.9
p += dormer(-4.0, 1.9, 1.5, YD)
p += dormer(-0.6, 2.4, 1.9, YD - 0.15)
p += dormer(4.2, 1.9, 1.5, YD)
p += dormer(0.0, 1.9, 1.4, Y1 + OV - 3.3)    # orqa qiyalikda bitta (orqasi ham bo'sh ko'rinmasin)

# ---------- "EASY Box / casual food" peshtaxtasi ----------
SX, SZ = 2.0, RZ + 1.25
p.append(k.box((2.6, 0.12, 1.15), (SX, YD + 0.2, SZ), 'sign'))
p.append(k.text('EASY', 0.5, (1.55, YD + 0.13, SZ + 0.12), 'sign_w'))
p.append(k.text('Box', 0.32, (2.85, YD + 0.13, SZ + 0.12), 'sign_w'))
p.append(k.text('casual  food', 0.14, (SX, YD + 0.13, SZ - 0.36), 'sign_w'))
p.append(k.box((0.08, 0.6, 0.6), (SX - 1.0, YD + 0.5, SZ - 0.5), 'iron'))
p.append(k.box((0.08, 0.6, 0.6), (SX + 1.0, YD + 0.5, SZ - 0.5), 'iron'))

# ---------- firuza dumaloq osma belgi (o'ng burchak) ----------
p.append(k.beam((X1 - 0.1, Y0 - 0.1, 2.95), (X1 + 0.75, Y0 - 0.1, 2.95), 0.05, 0.05, 'iron'))
sign = k.cyl(0.42, 0.08, (0, 0, 0), 'teal', segs=24, rot=(1.5708, 0, 0))
sign.rotation_euler = (0, 0, 1.5708)
sign.location = (X1 + 0.5, Y0 - 0.1, 2.5)
p.append(sign)

# ---------- skameykalar va axlat qutilari (old devor oldida) ----------
BY = Y0 - 0.95


def bench(xc):
    parts = [k.box((2.2, 0.12, 0.05), (xc, BY - 0.12 + 0.13 * i, 0.46), 'wood') for i in range(3)]
    parts += [k.box((2.2, 0.05, 0.11), (xc, BY + 0.22, 0.62 + 0.14 * i), 'wood') for i in range(3)]
    for x in (xc - 0.95, xc + 0.95):
        parts.append(k.box((0.08, 0.5, 0.46), (x, BY, 0.23), 'iron'))
        parts.append(k.box((0.08, 0.06, 0.5), (x, BY + 0.24, 0.72), 'iron'))
    return parts


def bins(xc):
    parts = [k.box((0.8, 0.36, 0.05), (xc, BY + 0.1, 0.9), 'iron')]
    for i, m in enumerate(('bin_r', 'bin_y', 'bin_g')):
        parts.append(k.box((0.24, 0.3, 0.6), (xc - 0.27 + 0.27 * i, BY + 0.1, 0.36), m))
    for x in (xc - 0.42, xc + 0.42):
        parts.append(k.box((0.04, 0.04, 0.9), (x, BY + 0.1, 0.45), 'iron'))
    return parts


for xc in (-4.4, 0.3, 4.6):
    p += bench(xc)
for xc in (-2.1, 2.45):
    p += bins(xc)

k.finish('EASY-BOX', p, HERE, [
    ('preview.png', (1.0, -17.0, 4.5), (0, 0, 3.0)),
    ('preview_top.png', (-12.0, -13.0, 12.0), (0, 0, 2.5)),
])

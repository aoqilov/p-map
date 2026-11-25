"""
Paravoz — relssiz park poyezdi (rasm: attraction-images-park/paravoz.png): lokomotiv va 3 ta vagon.
  * lokomotiv: oldida qiya qora to'siq (kumush tik plankalar, oq boltlar), qora qozon (oq nuqtalar qatori), oldida to'q
    qizil va tilla halqali yuz, o'rtasida yonib turgan fara; ustida qizil bug' gumbazi va qizil-qora mo'ri (olmos uchli);
    yonida tilla chiziqli to'q qizil quti, uchta to'q qizil parrakli g'ildirak (oq boltlar, tilla gupchak), tilla tasma;
    kabina: to'q qizil pastki qism, qora ustunlar, tilla ravoqli ochiq derazalar, ichida o'rindiq va rul, yon oyna,
    qora egri tom, tilla hoshiya, ustida oq chiroqchali ustqurma;
  * vagonlar: qora rama, kumush diskli rezina g'ildiraklar, to'q qizil pastki qism (tilla chiziqlar, eshikda tilla
    oval emblema), qora ustunlar va tilla ravoqli ochiq derazalar (yonida uchtadan, oldi-orqada bittadan), ichida
    o'rindiqlar, qora tom (tilla hoshiya) va oq chiroqchali ustqurma; vagonlar orasida ulagich.

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/paravoz/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png, preview_close.png

Poyezd bo'yi — Blender'da Y o'qi bo'ylab, lokomotiv oldi — -Y. G'ildiraklar yo'l plitkasi ustida (z = 0.12).
Asl o'lcham: uzunligi ~12.1 m, eni 1.4 m, balandligi ~2.45 m.
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'decor'))
from blender_kit import Kit  # noqa: E402

PALETTE = {
    'black': (0.015, 0.015, 0.018), 'black_l': (0.05, 0.05, 0.055), 'maroon': (0.28, 0.02, 0.03), 'red': (0.45, 0.02, 0.03),
    'gold': (0.95, 0.6, 0.02), 'silver': (0.7, 0.72, 0.75), 'white': (0.92, 0.92, 0.9), 'bulb': (1.0, 0.95, 0.85),
    'lamp': (1.0, 0.95, 0.8), 'tyre': (0.02, 0.02, 0.02), 'seat': (0.04, 0.04, 0.045), 'glass': (0.05, 0.06, 0.08),
}
k = Kit(PALETTE, glow=('lamp', 'bulb'))
p = []
G = 0.12                    # yo'l plitkasi yuzasi

LOCO_L, CAR_L, GAP = 3.5, 2.55, 0.32
TOTAL = LOCO_L + 3 * (CAR_L + GAP)
Y0 = -TOTAL / 2             # lokomotiv oldi


def wheel(x, y, r, w, rim='silver'):
    p.append(k.cyl(r, w, (x, y, G + r), 'tyre', segs=16, rot=(0, math.pi / 2, 0)))
    p.append(k.cyl(r * 0.6, w + 0.02, (x, y, G + r), rim, segs=10, rot=(0, math.pi / 2, 0)))
    p.append(k.cyl(r * 0.18, w + 0.04, (x, y, G + r), 'black', segs=8, rot=(0, math.pi / 2, 0)))


def bulbs_row(x, y0, y1, z, n):
    for i in range(n):
        y = y0 + (y1 - y0) * (i + 0.5) / n
        p.append(k.ball(0.035, (x, y, z), 'bulb', sub=1))


def arch_frame(x, yc, z0, w, h, mat='gold', t=0.05):
    """Yon devordagi (YZ tekislik, x da) ravoqli ochiq deraza ramkasi: ikki tik + yoy"""
    r = w / 2
    zs = z0 + h - r
    for s in (-1, 1):
        p.append(k.box((0.04, t, h - r), (x, yc + s * r, z0 + (h - r) / 2), mat))
    pts = [(yc + r * math.cos(math.pi * i / 6), zs + r * math.sin(math.pi * i / 6)) for i in range(7)]
    for a, b in zip(pts, pts[1:]):
        p.append(k.beam((x, a[0], a[1]), (x, b[0], b[1]), t, t, mat))


def arch_frame_y(y, xc, z0, w, h, mat='gold', t=0.05):
    """Old/orqa devordagi (XZ tekislik, y da) ravoqli deraza ramkasi"""
    r = w / 2
    zs = z0 + h - r
    for s in (-1, 1):
        p.append(k.box((t, 0.04, h - r), (xc + s * r, y, z0 + (h - r) / 2), mat))
    pts = [(xc + r * math.cos(math.pi * i / 6), zs + r * math.sin(math.pi * i / 6)) for i in range(7)]
    for a, b in zip(pts, pts[1:]):
        p.append(k.beam((a[0], y, a[1]), (b[0], y, b[1]), t, t, mat))


def cabin_top(y0, y1, w, z_roof, bulbs=7):
    """Qora egri tom (tilla hoshiya) va ustida oq chiroqchali ustqurma"""
    L = y1 - y0
    yc = (y0 + y1) / 2
    prof = [(-w / 2 - 0.08, z_roof), (w / 2 + 0.08, z_roof), (w / 2 + 0.08, z_roof + 0.08), (w / 4, z_roof + 0.16),
            (-w / 4, z_roof + 0.16), (-w / 2 - 0.08, z_roof + 0.08)]
    p.append(k.prism_y(prof, y0 - 0.08, y1 + 0.08, 'black'))
    for s in (-1, 1):
        p.append(k.box((0.04, L + 0.18, 0.06), (s * (w / 2 + 0.1), yc, z_roof + 0.03), 'gold'))
    p.append(k.box((0.04 + w + 0.2, 0.04, 0.06), (0, y0 - 0.1, z_roof + 0.03), 'gold'))
    p.append(k.box((0.04 + w + 0.2, 0.04, 0.06), (0, y1 + 0.1, z_roof + 0.03), 'gold'))
    mw, ml = w * 0.6, L * 0.75                                          # ustqurma
    p.append(k.box((mw, ml, 0.2), (0, yc, z_roof + 0.26), 'black_l'))
    p.append(k.box((mw + 0.06, ml + 0.06, 0.04), (0, yc, z_roof + 0.38), 'black'))
    for s in (-1, 1):
        bulbs_row(s * (mw / 2 + 0.01), yc - ml / 2, yc + ml / 2, z_roof + 0.27, bulbs)
        p.append(k.box((0.03, ml, 0.03), (s * (mw / 2 + 0.01), yc, z_roof + 0.17), 'gold'))


# ====================== vagonlar ======================
def coach(yf):
    """Vagon: oldi y = yf, orqasi y = yf + CAR_L"""
    W = 1.32
    y0, y1 = yf, yf + CAR_L
    yc = (y0 + y1) / 2
    p.append(k.box((W - 0.2, CAR_L - 0.1, 0.18), (0, yc, G + 0.32), 'black'))             # rama
    for wy in (y0 + 0.5, y1 - 0.5):
        for s in (-1, 1):
            wheel(s * (W / 2 - 0.1), wy, 0.22, 0.16)
    # pastki qism: to'q qizil, tilla chiziqlar
    ZB0, ZB1 = G + 0.42, G + 1.1
    p.append(k.box((W, CAR_L, ZB1 - ZB0), (0, yc, (ZB0 + ZB1) / 2), 'maroon'))
    p.append(k.box((W + 0.02, CAR_L + 0.02, 0.1), (0, yc, ZB0 + 0.05), 'black'))
    for z in (ZB0 + 0.13, ZB1 - 0.03):
        p.append(k.box((W + 0.04, CAR_L + 0.04, 0.05), (0, yc, z), 'gold'))
    for s in (-1, 1):
        x = s * (W / 2 + 0.025)
        p.append(k.box((0.02, 0.06, ZB1 - ZB0 - 0.2), (x, yc - 0.45, (ZB0 + ZB1) / 2), 'gold'))   # eshik chiziqlari
        p.append(k.box((0.02, 0.06, ZB1 - ZB0 - 0.2), (x, yc + 0.45, (ZB0 + ZB1) / 2), 'gold'))
        p.append(k.cyl(0.17, 0.03, (x, yc, (ZB0 + ZB1) / 2 + 0.05), 'gold', segs=16, rot=(0, math.pi / 2, 0)))   # emblema
        p.append(k.cyl(0.12, 0.035, (s * (W / 2 + 0.03), yc, (ZB0 + ZB1) / 2 + 0.05), 'maroon', segs=14, rot=(0, math.pi / 2, 0)))
        for yb in (y0 + 0.15, y1 - 0.15):
            p.append(k.ball(0.025, (s * (W / 2 + 0.03), yb, ZB0 + 0.05), 'white', sub=1))
    # ustunlar, ochiq derazalar (tilla ravoqlar), tom
    ZR = G + 2.0
    for yy in (y0 + 0.06, y0 + 0.88, y1 - 0.88, y1 - 0.06):
        for s in (-1, 1):
            p.append(k.box((0.08, 0.1, ZR - ZB1), (s * (W / 2 - 0.04), yy, (ZB1 + ZR) / 2), 'black'))
    for s in (-1, 1):
        for yy in (y0 + 0.47, yc, y1 - 0.47):
            arch_frame(s * (W / 2 - 0.02), yy, ZB1 + 0.02, 0.62, ZR - ZB1 - 0.12)
        p.append(k.box((0.06, CAR_L, 0.14), (s * (W / 2 - 0.03), yc, ZR - 0.07), 'black'))
    for yy in (y0 + 0.03, y1 - 0.03):
        p.append(k.box((W, 0.06, 0.14), (0, yy, ZR - 0.07), 'black'))
        arch_frame_y(yy - 0.01 if yy < yc else yy + 0.01, 0, ZB1 + 0.02, 0.8, ZR - ZB1 - 0.12)
    for yy in (y0 + 0.65, y1 - 0.65):                                    # o'rindiqlar
        p.append(k.box((W - 0.2, 0.45, 0.12), (0, yy, ZB1 - 0.15), 'seat'))
        p.append(k.box((W - 0.2, 0.08, 0.45), (0, yy + 0.22, ZB1 + 0.08), 'seat'))
    cabin_top(y0, y1, W, ZR)
    # ulagich (oldingi vagon/lokomotivga)
    p.append(k.box((0.12, GAP + 0.3, 0.08), (0, y0 - GAP / 2, G + 0.35), 'silver'))


# ====================== lokomotiv ======================
LW = 1.28
LY1 = Y0 + LOCO_L
# shassi va qiya old to'siq (qora, kumush tik plankalar)
p.append(k.box((LW, LOCO_L - 0.55, 0.42), (0, (Y0 + 0.55 + LY1) / 2, G + 0.36), 'black'))
skirt = [(Y0, G + 0.12), (Y0 + 0.6, G + 0.12), (Y0 + 0.6, G + 0.62), (Y0 + 0.35, G + 0.62)]
p.append(k.prism_x([(y, z) for y, z in skirt], -LW / 2, LW / 2, 'black'))
for s in (-1, 1):                                                        # yon qiya burchaklar
    p.append(k.box((0.06, 0.6, 0.5), (s * (LW / 2 + 0.02), Y0 + 0.32, G + 0.37), 'black'))
for i in range(9):                                                       # oldidagi kumush plankalar
    x = -LW / 2 + 0.12 + i * (LW - 0.24) / 8
    p.append(k.beam((x, Y0 + 0.06, G + 0.2), (x, Y0 + 0.28, G + 0.56), 0.05, 0.03, 'silver'))
    p.append(k.ball(0.025, (x, Y0 + 0.04, G + 0.18), 'white', sub=1))
p.append(k.box((LW + 0.04, 0.6, 0.04), (0, Y0 + 0.32, G + 0.64), 'black_l'))
for s in (-1, 1):
    p.append(k.box((0.04, LOCO_L - 0.6, 0.06), (s * (LW / 2 + 0.02), (Y0 + 0.6 + LY1) / 2, G + 0.6), 'gold'))   # tilla tasma
    # uchta bezak g'ildirak (to'q qizil, parrakli, oq boltlar, tilla gupchak)
    for j, wy in enumerate((Y0 + 1.1, Y0 + 1.62, Y0 + 2.14)):
        x = s * (LW / 2 + 0.04)
        p.append(k.cyl(0.26, 0.06, (x, wy, G + 0.3), 'red', segs=18, rot=(0, math.pi / 2, 0)))
        p.append(k.cyl(0.21, 0.07, (x, wy, G + 0.3), 'maroon', segs=18, rot=(0, math.pi / 2, 0)))
        for q in range(6):
            a = math.pi * q / 6
            p.append(k.box((0.02, 0.4 * abs(math.cos(a)) + 0.03, 0.4 * abs(math.sin(a)) + 0.03),
                           (x + s * 0.03, wy, G + 0.3), 'red', rot=(a, 0, 0)))
        p.append(k.cyl(0.06, 0.09, (x + s * 0.01, wy, G + 0.3), 'gold', segs=10, rot=(0, math.pi / 2, 0)))
        for q in range(8):
            a = 2 * math.pi * q / 8
            p.append(k.ball(0.018, (x + s * 0.04, wy + 0.22 * math.cos(a), G + 0.3 + 0.22 * math.sin(a)), 'white', sub=1))
    p.append(k.box((0.06, 0.4, 0.3), (s * (LW / 2 + 0.03), Y0 + 2.6, G + 0.32), 'maroon'))   # g'ildirak orqasidagi qopqoq
    p.append(k.box((0.07, 0.44, 0.04), (s * (LW / 2 + 0.03), Y0 + 2.6, G + 0.48), 'gold'))
# qozon: qora silindr, oq nuqtalar, oldida to'q qizil yuz, tilla halqa, fara
BZ, BR = G + 1.02, 0.44
BY0, BY1 = Y0 + 0.62, Y0 + 2.15
p.append(k.cyl(BR, BY1 - BY0, (0, (BY0 + BY1) / 2, BZ), 'black', segs=20, rot=(math.pi / 2, 0, 0)))
p.append(k.box((LW, BY1 - BY0, BZ - G - 0.58), (0, (BY0 + BY1) / 2, (BZ + G + 0.58) / 2), 'black'))   # qozon osti
for row in range(3):
    a = math.radians(-30 + row * 45)
    for s in (-1, 1):
        for q in range(5):
            y = BY0 + 0.2 + q * 0.3
            p.append(k.ball(0.028, (s * (BR + 0.01) * math.cos(a), y, BZ + (BR + 0.01) * math.sin(a)), 'white', sub=1))
p.append(k.cyl(BR + 0.05, 0.1, (0, BY0 - 0.02, BZ), 'maroon', segs=20, rot=(math.pi / 2, 0, 0)))
p.append(k.cyl(BR + 0.07, 0.05, (0, BY0 - 0.06, BZ), 'red', segs=20, rot=(math.pi / 2, 0, 0)))
p.append(k.cyl(0.3, 0.06, (0, BY0 - 0.1, BZ), 'gold', segs=20, rot=(math.pi / 2, 0, 0)))
p.append(k.cyl(0.22, 0.07, (0, BY0 - 0.11, BZ), 'maroon', segs=18, rot=(math.pi / 2, 0, 0)))
p.append(k.cyl(0.13, 0.08, (0, BY0 - 0.13, BZ), 'silver', segs=14, rot=(math.pi / 2, 0, 0)))
p.append(k.cyl(0.1, 0.09, (0, BY0 - 0.14, BZ), 'lamp', segs=12, rot=(math.pi / 2, 0, 0)))      # fara
p.append(k.box((LW + 0.1, 0.3, 0.06), (0, BY0 - 0.05, G + 0.66), 'black_l'))                   # yuz osti tokcha
# mo'ri (qizil konus + qora olmos uch) va bug' gumbazi (qizil, qopqoqli)
p.append(k.cyl(0.11, 0.2, (0, BY0 + 0.25, BZ + BR + 0.08), 'red', segs=12))
p.append(k.cyl(0.09, 0.42, (0, BY0 + 0.25, BZ + BR + 0.38), 'red', segs=12, r2=0.13))
p.append(k.cyl(0.14, 0.05, (0, BY0 + 0.25, BZ + BR + 0.53), 'black', segs=12))
p.append(k.cyl(0.13, 0.16, (0, BY0 + 0.25, BZ + BR + 0.63), 'black', segs=8, r2=0.2))
p.append(k.cyl(0.2, 0.18, (0, BY0 + 0.25, BZ + BR + 0.8), 'black', segs=8, r2=0.04))
p.append(k.cyl(0.13, 0.22, (0, BY0 + 0.95, BZ + BR + 0.05), 'red', segs=12))
p.append(k.ball(0.13, (0, BY0 + 0.95, BZ + BR + 0.18), 'red', sub=1, scale=(1, 1, 0.8)))
p.append(k.cyl(0.03, 0.12, (0, BY0 + 0.95, BZ + BR + 0.32), 'red', segs=6))
p.append(k.ball(0.04, (0, BY0 + 0.95, BZ + BR + 0.39), 'red', sub=1))
for s in (-1, 1):                                                        # qozon ustidagi tilla tutqich
    p.append(k.beam((s * 0.3, BY0 + 1.2, BZ + 0.36), (s * 0.3, BY1 - 0.05, BZ + 0.36), 0.025, 0.025, 'gold'))
# yonidagi tilla chiziqli to'q qizil quti (kabina oldida)
for s in (-1, 1):
    x = s * (LW / 2 + 0.02)
    p.append(k.box((0.05, 0.6, 0.6), (x, BY1 - 0.35, G + 0.98), 'maroon'))
    for i in range(6):
        p.append(k.box((0.06, 0.52, 0.03), (x, BY1 - 0.35, G + 0.74 + i * 0.09), 'gold'))
    p.append(k.cyl(0.05, 0.07, (s * (LW / 2 + 0.04), BY1 - 0.35, G + 0.98), 'maroon', segs=10, rot=(0, math.pi / 2, 0)))
# kabina
CY0, CY1 = BY1 - 0.05, LY1
cyc = (CY0 + CY1) / 2
ZB0, ZB1, ZR = G + 0.58, G + 1.2, G + 2.1
p.append(k.box((LW, CY1 - CY0, ZB1 - ZB0), (0, cyc, (ZB0 + ZB1) / 2), 'maroon'))
p.append(k.box((LW + 0.04, CY1 - CY0 + 0.04, 0.05), (0, cyc, ZB1 - 0.02), 'gold'))
for s in (-1, 1):
    p.append(k.box((0.03, 0.06, ZB1 - ZB0 - 0.1), (s * (LW / 2 + 0.01), CY0 + 0.08, (ZB0 + ZB1) / 2), 'gold'))
    p.append(k.box((0.03, 0.06, ZB1 - ZB0 - 0.1), (s * (LW / 2 + 0.01), CY1 - 0.08, (ZB0 + ZB1) / 2), 'gold'))
for yy in (CY0 + 0.05, CY1 - 0.05):
    for s in (-1, 1):
        p.append(k.box((0.09, 0.1, ZR - ZB1), (s * (LW / 2 - 0.045), yy, (ZB1 + ZR) / 2), 'black'))
p.append(k.box((LW, 0.08, 0.3), (0, CY0 + 0.04, ZR - 0.15), 'black'))      # old oyna tepasi
p.append(k.box((LW, 0.06, 0.5), (0, CY0 + 0.03, ZB1 + 0.25), 'black'))     # old oyna pasti
p.append(k.box((LW - 0.2, 0.03, 0.55), (0, CY0 + 0.02, ZB1 + 0.78), 'glass'))
for s in (-1, 1):
    arch_frame(s * (LW / 2 - 0.02), cyc, ZB1 + 0.03, 0.85, ZR - ZB1 - 0.15)
    p.append(k.box((0.05, CY1 - CY0, 0.14), (s * (LW / 2 - 0.03), cyc, ZR - 0.07), 'black'))
    p.append(k.box((0.04, 0.12, 0.22), (s * (LW / 2 + 0.16), CY0 + 0.15, ZB1 + 0.3), 'black'))   # yon oyna
    p.append(k.beam((s * (LW / 2), CY0 + 0.15, ZB1 + 0.3), (s * (LW / 2 + 0.14), CY0 + 0.15, ZB1 + 0.3), 0.03, 0.03, 'black'))
p.append(k.box((LW - 0.2, 0.5, 0.12), (0, CY1 - 0.4, ZB1 - 0.1), 'seat'))
p.append(k.box((LW - 0.2, 0.08, 0.5), (0, CY1 - 0.12, ZB1 + 0.15), 'seat'))
p.append(k.cyl(0.17, 0.03, (-0.15, CY0 + 0.4, ZB1 + 0.25), 'black', segs=14, rot=(1.0, 0, 0)))   # rul
cabin_top(CY0, CY1, LW, ZR, bulbs=5)
p.append(k.box((0.1, 0.2, 0.08), (0, LY1 + 0.05, G + 0.35), 'silver'))     # orqa ulagich

# ====================== vagonlar joyi ======================
y = LY1 + GAP
for i in range(3):
    coach(y)
    y += CAR_L + GAP

k.finish('PARAVOZ', p, HERE, [
    ('preview.png', (5.5, -10.5, 4.0), (0, -2.0, 1.0)),
    ('preview_close.png', (3.2, Y0 - 2.2, 2.0), (0, Y0 + 1.6, 1.0)),
])

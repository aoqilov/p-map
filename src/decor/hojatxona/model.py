"""
Hojatxona (Общественный туалет, planda 7 va 8) — oq bino jigarrang sokolda (bezak-bino: src/decor/hojatxona/building.ts).
Tepasidagi WC kartasi modelda emas — config.ts → card (doim ko'ruvchiga qaragan, Decor.tsx).

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/decor/hojatxona/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png, preview_back.png

Tuzilish (bitta `base` obyekt, animatsiyasiz): plitka maydoncha (plandagi iz 10 × 10 m), jigarrang sokol, oq devorlar,
jigarrang karniz va tekis tom (shamollatish quvurlari), old tomonda ikki eshik (chapda erkaklar — ko'k belgi, o'ngda
ayollar — qizil belgi) va o'rtada nogironlar xonasi eshigi, umumiy soyabon, pandus, tor yuqori derazalar,
yonlarda gul tuvaklari va axlat qutisi.
Old tomoni (eshiklar) — Blender'da -Y. Asl o'lcham: 10 × 10 m, balandligi 4.3 m (quvurlar bilan).
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from blender_kit import Kit  # noqa: E402

PALETTE = {
    'slab': (0.7, 0.69, 0.66), 'wall': (0.96, 0.96, 0.95), 'brown': (0.42, 0.26, 0.15), 'brown_d': (0.3, 0.18, 0.1),
    'roof': (0.5, 0.48, 0.46), 'glass': (0.55, 0.68, 0.76), 'door': (0.52, 0.33, 0.19), 'steel': (0.65, 0.66, 0.68),
    'step': (0.6, 0.6, 0.6), 'blue': (0.15, 0.4, 0.78), 'red': (0.85, 0.2, 0.3), 'icon': (1.0, 1.0, 1.0),
    'pot': (0.42, 0.26, 0.15), 'leaf': (0.22, 0.5, 0.24), 'bin': (0.25, 0.45, 0.3), 'dark': (0.2, 0.2, 0.2),
}
k = Kit(PALETTE)
p = []

# ====================== o'lchamlar ======================
S, PZ = 10.0, 0.12          # maydoncha
BX = 4.4                    # bino yarim eni
YF, YB = -3.0, 4.6          # old / orqa devor
YM = (YF + YB) / 2
WALL = 3.4                  # devor tepasi
SOK = 0.75                  # sokol balandligi
FLOOR = 0.3

# ---------- maydoncha, sokol, devorlar, karniz, tom ----------
p.append(k.box((S, S, PZ), (0, 0, PZ / 2), 'slab'))
p.append(k.box((2 * BX + 0.12, YB - YF + 0.12, SOK), (0, YM, PZ + SOK / 2), 'brown'))
p.append(k.box((2 * BX + 0.16, YB - YF + 0.16, 0.08), (0, YM, PZ + SOK + 0.04), 'brown_d'))   # sokol qopqog'i
p.append(k.box((2 * BX, YB - YF, WALL - PZ), (0, YM, (WALL + PZ) / 2), 'wall'))
p.append(k.box((2 * BX + 0.5, YB - YF + 0.5, 0.3), (0, YM, WALL + 0.15), 'brown'))            # karniz
p.append(k.box((2 * BX + 0.3, YB - YF + 0.3, 0.12), (0, YM, WALL + 0.36), 'roof'))
for x, y in ((-2.5, 2.8), (2.5, 2.8), (0, 3.6)):
    p.append(k.cyl(0.1, 0.5, (x, y, WALL + 0.6), 'steel', segs=10))
    p.append(k.cyl(0.16, 0.06, (x, y, WALL + 0.88), 'dark', segs=10))
# burchaklarda jigarrang vertikal hoshiya
for x in (-BX, BX):
    for y in (YF, YB):
        p.append(k.box((0.18, 0.18, WALL - PZ - SOK), (x, y, (WALL + PZ + SOK) / 2), 'brown'))


# ---------- eshiklar: erkaklar (chap), nogironlar (o'rta), ayollar (o'ng) ----------
def door(x, w, sign):
    res = [k.box((w, 0.06, 2.2), (x, YF - 0.02, FLOOR + 1.1), 'door')]
    res.extend(k.frame_y(x, YF - 0.05, FLOOR + 1.1, w, 2.2, 0.1, 'brown_d'))
    res.append(k.box((0.05, 0.06, 0.3), (x + w / 2 - 0.15, YF - 0.09, FLOOR + 1.05), 'steel'))     # tutqich
    for i in range(3):  # eshikdagi gorizontal panellar
        res.append(k.box((w - 0.2, 0.03, 0.04), (x, YF - 0.06, FLOOR + 0.5 + i * 0.6), 'brown_d'))
    # eshikdagi belgi plastinkasi (yozuvsiz, faqat belgi)
    zc = FLOOR + 1.65
    res.append(k.disc_y(0.28, YF - 0.08, zc, x, 0.04, {'man': 'blue', 'woman': 'red', 'wheel': 'blue'}[sign], segs=24))
    iy = YF - 0.12
    if sign in ('man', 'woman'):
        res.append(k.ball(0.055, (x, iy, zc + 0.13), 'icon', sub=2))
        if sign == 'man':
            res.append(k.box((0.12, 0.02, 0.17), (x, iy, zc), 'icon'))
            for dx in (-0.035, 0.035):
                res.append(k.box((0.045, 0.02, 0.12), (x + dx, iy, zc - 0.14), 'icon'))
        else:
            res.append(k.prism_y([(x - 0.1, zc - 0.1), (x + 0.1, zc - 0.1), (x + 0.04, zc + 0.07), (x - 0.04, zc + 0.07)],
                                 iy - 0.01, iy + 0.01, 'icon'))
            for dx in (-0.03, 0.03):
                res.append(k.box((0.035, 0.02, 0.08), (x + dx, iy, zc - 0.15), 'icon'))
    else:  # nogironlar aravachasi belgisi
        res.append(k.ball(0.045, (x - 0.02, iy, zc + 0.15), 'icon', sub=2))
        res.append(k.box((0.04, 0.02, 0.15), (x - 0.03, iy, zc + 0.03), 'icon'))
        res.append(k.box((0.12, 0.02, 0.035), (x + 0.03, iy, zc - 0.04), 'icon'))
        res.append(k.cyl(0.09, 0.02, (x - 0.01, iy, zc - 0.08), 'icon', segs=16, rot=(math.pi / 2, 0, 0)))
    return res


for x, w, s in ((-2.6, 1.1, 'man'), (0, 1.3, 'wheel'), (2.6, 1.1, 'woman')):
    p.extend(door(x, w, s))
# ayvon (pol balandligi), uzun soyabon, ikki ustun
p.append(k.box((7.6, 1.4, FLOOR - PZ), (0, YF - 0.7, (FLOOR + PZ) / 2), 'step'))
CZ = FLOOR + 2.95
p.append(k.box((8.0, 1.7, 0.12), (0, YF - 0.85, CZ), 'brown'))
p.append(k.box((8.04, 0.06, 0.22), (0, YF - 1.7, CZ - 0.02), 'brown_d'))
for x in (-3.8, 3.8):
    p.append(k.cyl(0.06, CZ - FLOOR, (x, YF - 1.55, (CZ + FLOOR) / 2), 'steel', segs=10))
# old tomonda pastga tushish: o'rtada pandus (nogironlar eshigi oldida), yonlarda pog'ona
p.append(k.prism_x([(YF - 1.4, FLOOR), (YF - 2.0, PZ), (YF - 1.4, PZ)], -0.9, 0.9, 'step'))
for x in (-0.95, 0.95):
    p.append(k.beam((x, YF - 1.4, FLOOR + 0.85), (x, YF - 2.0, PZ + 0.85), 0.04, 0.04, 'steel'))
    p.append(k.cyl(0.02, 0.85, (x, YF - 1.95, PZ + 0.43), 'steel', segs=8))
for x in (-2.6, 2.6):
    p.append(k.box((1.8, 0.3, 0.1), (x, YF - 1.55, PZ + 0.05), 'step'))

# ---------- tor yuqori derazalar (sut rangli oyna) ----------
WZ = 2.75
for y in (-1.2, 0.8, 2.8):
    for x in (-BX, BX):
        sgn = 1 if x > 0 else -1
        p.append(k.box((0.04, 1.2, 0.45), (x + sgn * 0.01, y, WZ), 'glass'))
        p.extend(k.frame_x(x + sgn * 0.04, y, WZ, 1.2, 0.45, 0.07, 'brown_d'))
for x in (-3.0, -1.0, 1.0, 3.0):
    p.append(k.box((1.2, 0.04, 0.45), (x, YB + 0.01, WZ), 'glass'))
    p.extend(k.frame_y(x, YB + 0.04, WZ, 1.2, 0.45, 0.07, 'brown_d'))

# ---------- gul tuvaklari va axlat qutisi ----------
for x in (-4.4, 4.4):
    p.append(k.box((0.6, 0.6, 0.55), (x, YF - 0.9, PZ + 0.275), 'pot'))
    p.append(k.ball(0.4, (x, YF - 0.9, PZ + 0.85), 'leaf', sub=1))
p.append(k.cyl(0.22, 0.75, (-3.6, YF - 1.75, PZ + 0.375), 'bin', segs=12))
p.append(k.cyl(0.25, 0.06, (-3.6, YF - 1.75, PZ + 0.78), 'dark', segs=12))

k.finish('WC', p, HERE, [
    ('preview.png', (10.0, -14.0, 8.0), (0, 0, 1.6)),
    ('preview_back.png', (-11.0, 12.0, 9.0), (0, 0.5, 1.8)),
])

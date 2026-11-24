"""
Tibbiyot xonasi — sobiq basseyn o'rnidagi bir qavatli oq bino (bezak-bino: src/decor/tibbiyot-xonasi/building.ts).

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/decor/tibbiyot-xonasi/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png, preview_back.png

Tuzilish (bitta `base` obyekt, animatsiyasiz): beton maydoncha (sobiq basseyn izi 17.1 × 6.4 m), oq devorlar ko'k-kulrang
sokolda, tekis tom ko'k peshtoq bilan (yozuvsiz), shisha eshik soyabon ostida, zinapoya va
nogironlar aravachasi uchun pandus (panjara bilan), derazalar, devorda va tom ustida yonib turadigan qizil xoch,
tomdagi konditsionerlar, skameyka va gul tuvaklari, orqada xizmat eshigi.
Old tomoni (eshigi) — Blender'da -Y. Asl o'lcham: 17.1 × 6.4 m, balandligi 4.8 m (tomdagi xoch qutisi bilan).
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from blender_kit import Kit  # noqa: E402

PALETTE = {
    'slab': (0.72, 0.71, 0.68), 'wall': (0.95, 0.95, 0.94), 'base': (0.42, 0.5, 0.58), 'roof': (0.55, 0.56, 0.58),
    'blue': (0.1, 0.36, 0.7), 'white': (0.98, 0.98, 0.98), 'red': (0.86, 0.1, 0.12), 'glass': (0.42, 0.6, 0.74),
    'frame': (0.25, 0.27, 0.3), 'steel': (0.62, 0.64, 0.66), 'step': (0.6, 0.6, 0.6), 'wood': (0.6, 0.4, 0.22),
    'pot': (0.55, 0.32, 0.22), 'leaf': (0.2, 0.5, 0.22), 'ac': (0.86, 0.87, 0.87), 'dark': (0.15, 0.15, 0.16),
    'sign': (0.99, 0.99, 0.97),
}
k = Kit(PALETTE, glow=('sign',))
p = []

# ====================== o'lchamlar ======================
PW, PD, PZ = 17.1, 6.4, 0.15   # maydoncha (sobiq basseyn izi)
BX = 7.4                       # bino yarim eni
YF, YB = -1.6, 2.9             # old / orqa devor
WALL = 3.8                     # devor tepasi
FLOOR = 0.45                   # ichki pol (ayvon usti)

# ---------- maydoncha, sokol, devorlar, tom ----------
p.append(k.box((PW, PD, PZ), (0, 0, PZ / 2), 'slab'))
p.append(k.box((2 * BX + 0.1, YB - YF + 0.1, 0.5), (0, (YF + YB) / 2, PZ + 0.25), 'base'))
p.append(k.box((2 * BX, YB - YF, WALL - PZ), (0, (YF + YB) / 2, (WALL + PZ) / 2), 'wall'))
p.append(k.box((2 * BX + 0.5, YB - YF + 0.5, 0.18), (0, (YF + YB) / 2, WALL + 0.09), 'roof'))
# ko'k peshtoq (parapet) — to'rt tomonda, ustida oq qopqoq
for y in (YF - 0.27, YB + 0.27):
    p.append(k.box((2 * BX + 0.6, 0.1, 0.5), (0, y, WALL + 0.2), 'blue'))
for x in (-BX - 0.27, BX + 0.27):
    p.append(k.box((0.1, YB - YF + 0.6, 0.5), (x, (YF + YB) / 2, WALL + 0.2), 'blue'))
p.append(k.box((2 * BX + 0.7, 0.14, 0.05), (0, YF - 0.27, WALL + 0.47), 'white'))
p.append(k.box((2 * BX + 0.7, 0.14, 0.05), (0, YB + 0.27, WALL + 0.47), 'white'))
# devor burchaklarida ko'k vertikal chiziqlar
for x in (-BX, BX):
    for y in (YF, YB):
        p.append(k.box((0.16, 0.16, WALL - 0.7), (x, y, (WALL + 0.65) / 2), 'blue'))


def cross(cx, y, cz, s, face, panel=True):
    """Qizil xoch oq doira ustida (face: '-Y' old yoki '+Y' orqa)"""
    sgn = -1 if face == '-Y' else 1
    res = []
    if panel:
        res.append(k.disc_y(s * 0.62, y + sgn * 0.02, cz, cx, 0.04, 'sign'))
    a, b = s * 0.78, s * 0.26
    res.append(k.box((a, 0.04, b), (cx, y + sgn * 0.05, cz), 'red'))
    res.append(k.box((b, 0.04, a), (cx, y + sgn * 0.05, cz), 'red'))
    return res


# ---------- old tomon: eshik, soyabon, ayvon, zinapoya, pandus ----------
DW, DH = 1.8, 2.3
p.append(k.box((DW, 0.05, DH), (0, YF - 0.01, FLOOR + DH / 2), 'glass'))
p.extend(k.frame_y(0, YF - 0.04, FLOOR + DH / 2, DW, DH, 0.09, 'frame'))
p.append(k.box((0.06, 0.06, DH), (0, YF - 0.05, FLOOR + DH / 2), 'frame'))   # ikki tabaqa
for x in (-0.18, 0.18):
    p.append(k.box((0.03, 0.06, 0.5), (x, YF - 0.1, FLOOR + 1.1), 'steel'))   # tutqichlar
# ayvon (pol balandligida) va ikki pog'ona
p.append(k.box((3.4, 1.2, FLOOR - PZ), (0, YF - 0.6, (FLOOR + PZ) / 2), 'step'))
p.append(k.box((3.4, 0.3, 0.2), (0, YF - 1.35, PZ + 0.1), 'step'))
# soyabon: oq plita, ko'k chet, ikki po'lat ustun
CZ = 2.75
p.append(k.box((3.8, 1.5, 0.14), (0, YF - 0.75, CZ), 'white'))
p.append(k.box((3.84, 0.06, 0.2), (0, YF - 1.5, CZ), 'blue'))
for x in (-1.7, 1.7):
    p.append(k.cyl(0.05, CZ - FLOOR, (x, YF - 1.35, (CZ + FLOOR) / 2), 'steel', segs=10))
# eshik ustida (soyabon bilan tom orasida) qizil xoch
p.extend(cross(0, YF, 3.3, 0.7, '-Y'))
# pandus: ayvondan o'ngga, maydonchagacha tushadi; tashqi chetida panjara
RX0, RX1, RY0, RY1 = 1.7, 5.4, YF - 0.05, YF - 1.25
p.append(k.prism_y([(RX0, PZ), (RX1, PZ), (RX0, FLOOR)], RY0, RY1, 'step'))
for i in range(5):
    t = i / 4
    x = RX0 + t * (RX1 - RX0)
    z = FLOOR + (PZ - FLOOR) * t
    p.append(k.cyl(0.025, 0.9, (x, RY1 + 0.08, z + 0.45), 'steel', segs=8))
p.append(k.beam((RX0, RY1 + 0.08, FLOOR + 0.9), (RX1, RY1 + 0.08, PZ + 0.9), 0.05, 0.05, 'steel'))
p.append(k.beam((-1.7, YF - 1.25, FLOOR + 0.9), (-1.7, YF - 0.05, FLOOR + 0.9), 0.05, 0.05, 'steel'))
p.append(k.cyl(0.025, 0.9, (-1.7, YF - 1.2, FLOOR + 0.45), 'steel', segs=8))

# ---------- derazalar ----------
WW, WH, WZ = 1.6, 1.4, 1.85


def window_y(x, y, face):
    sgn = -1 if face == '-Y' else 1
    res = [k.box((WW, 0.04, WH), (x, y + sgn * 0.01, WZ), 'glass')]
    res.extend(k.frame_y(x, y + sgn * 0.04, WZ, WW, WH, 0.08, 'frame'))
    res.append(k.box((0.05, 0.06, WH), (x, y + sgn * 0.05, WZ), 'frame'))           # o'rta ramka
    res.append(k.box((WW + 0.25, 0.22, 0.06), (x, y + sgn * 0.1, WZ - WH / 2 - 0.07), 'white'))  # tokcha
    return res


for x in (-5.6, -3.1, 3.1, 5.6):
    p.extend(window_y(x, YF, '-Y'))
for x in (-5.4, -2.7, 0, 2.7):
    p.extend(window_y(x, YB, '+Y'))
for x in (-BX, BX):
    sgn = 1 if x > 0 else -1
    p.append(k.box((0.04, WW, WH), (x + sgn * 0.01, 0.65, WZ), 'glass'))
    p.extend(k.frame_x(x + sgn * 0.04, 0.65, WZ, WW, WH, 0.08, 'frame'))
    p.append(k.box((0.22, WW + 0.25, 0.06), (x + sgn * 0.1, 0.65, WZ - WH / 2 - 0.07), 'white'))

# ---------- orqa tomon: qizil xoch va xizmat eshigi ----------
p.extend(cross(-1.35, YB, 3.25, 0.6, '+Y'))
p.append(k.box((1.0, 0.05, 2.1), (5.6, YB + 0.01, PZ + 0.35 + 1.05), 'frame'))
p.extend(k.frame_y(5.6, YB + 0.04, PZ + 0.35 + 1.05, 1.0, 2.1, 0.07, 'steel'))
p.append(k.box((1.4, 0.28, 0.2), (5.6, YB + 0.14, PZ + 0.1), 'step'))
p.append(k.box((1.4, 0.3, 0.08), (5.6, YB + 0.15, 2.85), 'white'))

# ---------- tom: yonib turadigan xoch qutisi va konditsionerlar ----------
LZ = WALL + 0.18 + 0.3
for x in (-0.3, 0.3):
    p.append(k.cyl(0.04, 0.35, (x, 0.2, WALL + 0.35), 'steel', segs=8))
p.append(k.box((0.95, 0.5, 0.95), (0, 0.2, LZ + 0.42), 'sign'))
for face, y in (('-Y', 0.2 - 0.25), ('+Y', 0.2 + 0.25)):
    p.extend(cross(0, y, LZ + 0.42, 0.8, face, panel=False))
for x in (-4.6, -3.2, 3.6):
    p.append(k.box((1.0, 0.7, 0.6), (x, 1.8, WALL + 0.48), 'ac'))
    p.append(k.cyl(0.24, 0.04, (x, 1.8 - 0.36, WALL + 0.48), 'dark', segs=16, rot=(math.pi / 2, 0, 0)))
for x in (-6.2, 5.8):
    p.append(k.cyl(0.08, 0.5, (x, 0.3, WALL + 0.43), 'steel', segs=8))
    p.append(k.cyl(0.13, 0.08, (x, 0.3, WALL + 0.72), 'steel', segs=8))

# ---------- old tomondagi skameyka va gul tuvaklari ----------
SX, SY = -4.4, YF - 1.05
p.append(k.box((1.8, 0.42, 0.06), (SX, SY, PZ + 0.45), 'wood'))
p.append(k.box((1.8, 0.06, 0.38), (SX, SY + 0.22, PZ + 0.72), 'wood'))
for dx in (-0.75, 0.75):
    p.append(k.box((0.06, 0.4, 0.45), (SX + dx, SY, PZ + 0.225), 'frame'))
for x in (-2.45, 6.3, -6.6):
    p.append(k.cyl(0.26, 0.5, (x, YF - 0.75, PZ + 0.25), 'pot', segs=12, r2=0.32))
    p.append(k.ball(0.38, (x, YF - 0.75, PZ + 0.78), 'leaf', sub=1, scale=(1, 1, 0.9)))

k.finish('TIBBIYOT', p, HERE, [
    ('preview.png', (9.0, -13.0, 7.0), (0, -0.5, 1.6)),
    ('preview_back.png', (-8.0, 12.0, 8.0), (0, 0.5, 1.8)),
])

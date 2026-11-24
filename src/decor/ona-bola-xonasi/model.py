"""
Ona va bola xonasi — tibbiyot xonasi yonidagi maydonda kichik yashil uycha (bezak-bino: src/decor/ona-bola-xonasi/building.ts).

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/decor/ona-bola-xonasi/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png, preview_back.png

Tuzilish (bitta `base` obyekt, animatsiyasiz): och maydoncha, och yashil devorlar to'q yashil sokolda, oq burchaklar,
to'q yashil ikki nishabli tom, old tomonda uchburchak
peshtoqli ayvon (ichida ona va bola belgisi tushirilgan dumaloq medalyon; yozuvlar yo'q), shisha eshik, zinapoya va aravacha uchun
pandus, gul yashikli derazalar, yon tomonlarda dumaloq derazalar, eshik yonida bolalar aravachasi.
Old tomoni (eshigi) — Blender'da -Y. Asl o'lcham: 9 × 6.5 m, balandligi ~4.7 m.
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from blender_kit import Kit  # noqa: E402

PALETTE = {
    'slab': (0.8, 0.77, 0.72), 'wall': (0.66, 0.86, 0.56), 'mint': (0.28, 0.6, 0.38), 'trim': (0.99, 0.98, 0.96),
    'roof': (0.2, 0.5, 0.28), 'glass': (0.5, 0.68, 0.82), 'step': (0.68, 0.66, 0.64), 'steel': (0.65, 0.66, 0.68),
    'flower_p': (0.95, 0.4, 0.62), 'flower_y': (1.0, 0.85, 0.3),
    'leaf': (0.25, 0.55, 0.25), 'box': (0.55, 0.36, 0.24), 'pram': (0.42, 0.62, 0.9), 'tyre': (0.12, 0.12, 0.13),
    'icon': (1.0, 1.0, 1.0),
}
k = Kit(PALETTE)
p = []

# ====================== o'lchamlar ======================
PW, PD, PZ = 9.0, 6.5, 0.12    # maydoncha
BX = 3.6                       # bino yarim eni
YF, YB = -1.6, 2.6             # old / orqa devor
YM = (YF + YB) / 2             # tom tizmasi
WALL = 3.2                     # devor (tom osti) balandligi
RIDGE = 4.6                    # tom tizmasi
OV = 0.35                      # tom chiqib turishi
FLOOR = 0.35                   # ichki pol

# ---------- maydoncha, sokol, devorlar ----------
p.append(k.box((PW, PD, PZ), (0, 0, PZ / 2), 'slab'))
p.append(k.box((2 * BX + 0.08, YB - YF + 0.08, 0.45), (0, YM, PZ + 0.225), 'mint'))
p.append(k.box((2 * BX, YB - YF, WALL - PZ), (0, YM, (WALL + PZ) / 2), 'wall'))
# uchburchak frontonlar (yon tomonlar) — devor rangida
p.append(k.prism_x([(YF, WALL), (YB, WALL), (YM, RIDGE - 0.12)], -BX, BX, 'wall'))
# burchaklardagi oq pilyastrlar va tom ostidagi oq karniz
for x in (-BX, BX):
    for y in (YF, YB):
        p.append(k.box((0.2, 0.2, WALL - PZ - 0.65), (x, y, (WALL - 0.25 + PZ + 0.4) / 2), 'trim'))
p.append(k.box((2 * BX + 0.1, 0.12, 0.14), (0, YF - 0.03, WALL - 0.3), 'trim'))
p.append(k.box((2 * BX + 0.1, 0.12, 0.14), (0, YB + 0.03, WALL - 0.3), 'trim'))

# ---------- tom: ikki nishab, chetlari oq ----------
sl = (RIDGE - WALL) / (YM - YF)  # nishab


def roof_z(y):
    return RIDGE - sl * abs(y - YM)


e0, e1 = YF - OV, YB + OV
p.append(k.prism_x([(e0, roof_z(e0) - 0.16), (e0, roof_z(e0)), (YM, RIDGE + 0.02), (e1, roof_z(e1)), (e1, roof_z(e1) - 0.16),
                    (YM, RIDGE - 0.14)], -BX - OV, BX + OV, 'roof'))
for x in (-BX - OV - 0.02, BX + OV + 0.02):  # frontondagi oq hoshiya
    p.append(k.beam((x, e0, roof_z(e0) - 0.08), (x, YM, RIDGE - 0.06), 0.1, 0.18, 'trim'))
    p.append(k.beam((x, YM, RIDGE - 0.06), (x, e1, roof_z(e1) - 0.08), 0.1, 0.18, 'trim'))
p.append(k.cyl(0.07, 2 * BX + 2 * OV, (0, YM, RIDGE + 0.04), 'trim', segs=8, rot=(0, math.pi / 2, 0)))


# ---------- old tomon: ayvon (uchburchak peshtoq + medalyon), eshik ----------
DW, DH = 1.5, 2.15
p.append(k.box((DW, 0.05, DH), (0, YF - 0.01, FLOOR + DH / 2), 'glass'))
p.extend(k.frame_y(0, YF - 0.04, FLOOR + DH / 2, DW, DH, 0.1, 'mint'))
p.append(k.box((0.06, 0.06, DH), (0, YF - 0.05, FLOOR + DH / 2), 'mint'))
p.append(k.box((DW - 0.1, 0.06, 0.06), (0, YF - 0.05, FLOOR + 1.0), 'trim'))   # eshikdagi bolalar uchun past tutqich
AY0, AY1, AX = YF, YF - 1.3, 1.35  # ayvon chuqurligi, yarim eni
p.append(k.box((2 * AX + 0.4, AY0 - AY1, FLOOR - PZ), (0, (AY0 + AY1) / 2, (FLOOR + PZ) / 2), 'step'))
p.append(k.box((2 * AX + 0.4, 0.28, 0.12), (0, AY1 - 0.14, PZ + 0.06), 'step'))
PZT = 2.6  # ayvon ustunlari tepasi
for x in (-AX, AX):
    p.append(k.box((0.16, 0.16, PZT - FLOOR), (x, AY1 + 0.12, (PZT + FLOOR) / 2), 'trim'))
p.append(k.box((2 * AX + 0.2, 0.18, 0.16), (0, AY1 + 0.12, PZT), 'trim'))
PR = PZT + 0.85  # ayvon tomi tizmasi
p.append(k.prism_y([(-AX - 0.3, PZT), (-AX - 0.3, PZT + 0.14), (0, PR + 0.14), (AX + 0.3, PZT + 0.14), (AX + 0.3, PZT), (0, PR)],
                   AY1 - 0.15, AY0, 'roof'))
p.append(k.prism_y([(-AX + 0.05, PZT + 0.08), (AX - 0.05, PZT + 0.08), (0, PR - 0.02)], AY1 + 0.05, AY1 + 0.1, 'trim'))
# medalyon: yalpiz doira, ichida oq "ona bolani ko'tarib turibdi" belgisi
MZ, MY = PZT + 0.36, AY1 + 0.02
p.append(k.disc_y(0.3, MY, MZ, 0, 0.05, 'mint', segs=28))
p.append(k.disc_y(0.33, MY + 0.01, MZ, 0, 0.04, 'trim', segs=28))
IY = MY - 0.04
p.append(k.ball(0.055, (-0.05, IY, MZ + 0.15), 'icon', sub=2))                                   # onaning boshi
p.append(k.prism_y([(-0.17, MZ - 0.2), (0.07, MZ - 0.2), (0.0, MZ + 0.08), (-0.1, MZ + 0.08)], IY - 0.01, IY + 0.02, 'icon'))
p.append(k.ball(0.04, (0.08, IY - 0.01, MZ + 0.06), 'icon', sub=2))                              # bolaning boshi
p.append(k.ball(0.07, (0.07, IY - 0.01, MZ - 0.03), 'icon', sub=1, scale=(0.8, 0.4, 1.0)))       # yo'rgak
# pandus: ayvondan chapga, maydonchagacha (aravacha uchun)
RX0, RX1 = -AX - 0.2, -BX + 0.05
p.append(k.prism_y([(RX1, PZ), (RX0, PZ), (RX0, FLOOR)], AY0 - 0.05, AY1, 'step'))
p.append(k.beam((RX0, AY1 + 0.05, FLOOR + 0.85), (RX1, AY1 + 0.05, PZ + 0.85), 0.05, 0.05, 'steel'))
for t in (0.0, 0.5, 1.0):
    x = RX0 + (RX1 - RX0) * t
    p.append(k.cyl(0.025, 0.85, (x, AY1 + 0.05, FLOOR + (PZ - FLOOR) * t + 0.42), 'steel', segs=8))

# ---------- derazalar: oq ramka, yalpiz panjara, ostida gul yashigi ----------
WW, WH, WZ = 1.15, 1.25, 1.75


def window_y(x, y, face, flowers=True):
    sgn = -1 if face == '-Y' else 1
    res = [k.box((WW, 0.04, WH), (x, y + sgn * 0.01, WZ), 'glass')]
    res.extend(k.frame_y(x, y + sgn * 0.04, WZ, WW, WH, 0.09, 'trim'))
    res.append(k.box((0.05, 0.06, WH), (x, y + sgn * 0.05, WZ), 'mint'))
    res.append(k.box((WW, 0.06, 0.05), (x, y + sgn * 0.05, WZ + 0.2), 'mint'))
    if flowers:
        res.append(k.box((WW + 0.1, 0.25, 0.2), (x, y + sgn * 0.15, WZ - WH / 2 - 0.15), 'box'))
        for i in range(5):
            fx = x - WW / 2 + 0.1 + i * (WW - 0.2) / 4
            res.append(k.ball(0.11, (fx, y + sgn * 0.15, WZ - WH / 2 - 0.02), 'leaf', sub=1))
            res.append(k.ball(0.06, (fx + 0.03, y + sgn * 0.2, WZ - WH / 2 + 0.05), 'flower_p' if i % 2 else 'flower_y', sub=1))
    return res


for x in (-2.45, 2.45):
    p.extend(window_y(x, YF, '-Y'))
for x in (-2.3, 0, 2.3):
    p.extend(window_y(x, YB, '+Y'))
# yon tomonlar: oddiy deraza va frontonda dumaloq deraza
for x in (-BX, BX):
    sgn = 1 if x > 0 else -1
    p.append(k.box((0.04, WW, WH), (x + sgn * 0.01, YM, WZ), 'glass'))
    p.extend(k.frame_x(x + sgn * 0.04, YM, WZ, WW, WH, 0.09, 'trim'))
    p.append(k.cyl(0.32, 0.06, (x + sgn * 0.02, YM, WALL + 0.55), 'trim', segs=24, rot=(0, math.pi / 2, 0)))
    p.append(k.cyl(0.24, 0.07, (x + sgn * 0.03, YM, WALL + 0.55), 'glass', segs=24, rot=(0, math.pi / 2, 0)))

# ---------- bolalar aravachasi (eshik yonida, o'ngda) ----------
SX, SY = 2.55, AY1 - 0.15
for dx in (-0.25, 0.25):
    for dy in (-0.22, 0.22):
        p.append(k.cyl(0.12 if dx > 0 else 0.09, 0.04, (SX + dx, SY + dy, PZ + (0.12 if dx > 0 else 0.09)), 'tyre', segs=12,
                       rot=(math.pi / 2, 0, 0)))
p.append(k.box((0.62, 0.5, 0.06), (SX, SY, PZ + 0.3), 'steel'))
p.append(k.ball(0.33, (SX, SY, PZ + 0.52), 'pram', sub=2, scale=(1.0, 0.8, 0.55)))
p.append(k.ball(0.3, (SX + 0.12, SY, PZ + 0.62), 'pram', sub=2, scale=(0.75, 0.82, 0.8)))   # soyabon
p.append(k.beam((SX - 0.3, SY, PZ + 0.55), (SX - 0.55, SY, PZ + 0.95), 0.04, 0.04, 'steel'))
p.append(k.cyl(0.025, 0.46, (SX - 0.55, SY, PZ + 0.95), 'tyre', segs=8, rot=(math.pi / 2, 0, 0)))

# ---------- gul tuvaklari (ayvon yonlarida) ----------
for x in (-AX - 0.15, AX + 0.15):
    p.append(k.cyl(0.18, 0.35, (x, AY1 - 0.45, PZ + 0.175), 'mint', segs=12, r2=0.22))
    p.append(k.ball(0.26, (x, AY1 - 0.45, PZ + 0.55), 'leaf', sub=1))
    for a in range(3):
        ang = a * 2.1
        p.append(k.ball(0.07, (x + 0.15 * math.cos(ang), AY1 - 0.45 + 0.15 * math.sin(ang), PZ + 0.72), 'flower_p', sub=1))

k.finish('ONA-BOLA', p, HERE, [
    ('preview.png', (9.5, -13.0, 8.5), (0, 0, 2.2)),
    ('preview_back.png', (-9.0, 12.0, 9.0), (0, 0.5, 2.4)),
])

"""
Кафе "Замок эльфов" (planda n13) — foydalanuvchi fotosurati bo'yicha: bir qavatli shisha pavilon, tepasida kulrang beton
quti (parapet), atrofida zang-sariq metall fermali yog'och soyabon, burchaklarda beton ustunlar; old va chap tomonda
oq banner-to'siq (ko'k bloklar, "click" yozuvlari) qora oyoqlarda.

O'qlar: old tomon (banner, plaza) — Blender -Y, origin — iz markazi, eni X bo'yicha, chuqurligi Y bo'yicha.
Izi — building.ts dagi rect (W × D), model shu o'lchamga aynan to'g'ri keladi.

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/decor/zamok-elfov/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png, preview_side.png, preview_top.png
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from blender_kit import Kit  # noqa: E402

PALETTE = {
    'paving': (0.62, 0.6, 0.57), 'concrete': (0.55, 0.56, 0.56), 'concrete_d': (0.42, 0.43, 0.44), 'cap': (0.68, 0.68, 0.67),
    'glass': (0.1, 0.13, 0.14), 'frame': (0.12, 0.13, 0.14), 'mullion_y': (0.75, 0.62, 0.2),
    'rust': (0.78, 0.42, 0.12), 'wood': (0.62, 0.45, 0.28), 'wood_d': (0.45, 0.32, 0.2),
    'banner': (0.95, 0.95, 0.94), 'blue': (0.1, 0.5, 0.85), 'blue_d': (0.05, 0.3, 0.6), 'black': (0.06, 0.06, 0.07),
    'interior': (0.2, 0.17, 0.14), 'rock': (0.42, 0.38, 0.33), 'red': (0.8, 0.1, 0.08),
}
k = Kit(PALETTE, glow=('banner',))
_g = k.mats['glass'].node_tree.nodes['Principled BSDF']
_g.inputs['Roughness'].default_value = 0.08
_g.inputs['Metallic'].default_value = 0.4
_b = k.mats['banner'].node_tree.nodes['Principled BSDF']   # kechasi banner yengil yorishadi
_b.inputs['Emission Strength'].default_value = 0.25
p = []

# ---------- o'lchamlar, m ----------
W, D = 22.0, 14.0           # umumiy iz (soyabon chetigacha) — building.ts dagi rect
GW, GD = 19.0, 11.0         # shisha quti
GH = 4.0                    # shisha devor balandligi
CZ = 4.15                   # soyabon sathi
BX0, BX1 = -9.0, 9.2        # beton quti (X)
BY0, BY1 = -2.6, 5.5        # beton quti (Y): oldidan ~2.9 m orqaga surilgan
BH = 6.9                    # beton quti tepasi
gx, gy = GW / 2, GD / 2
cx, cy = W / 2, D / 2

# ---------- pol, ichki qism ----------
p.append(k.box((W, D, 0.12), (0, 0, 0.06), 'paving'))
p.append(k.box((GW - 0.3, GD - 0.3, GH - 0.1), (0, 0, 0.12 + (GH - 0.1) / 2), 'interior'))   # ichi qorong'i
# ichkaridagi "qoya" bezaklari (fotoda shisha ortida ko'rinadi)
for x, y, r in ((3.5, -gy + 1.4, 1.1), (6.8, -gy + 1.2, 0.8), (-4.0, -gy + 1.3, 0.9)):
    p.append(k.ball(r, (x, y - 0.25, 0.12 + r * 0.7), 'rock', sub=1, scale=(1.3, 0.9, 1.0)))

# ---------- shisha devorlar va ramkalar ----------
T = 0.04
p.append(k.box((GW, T, GH), (0, -gy, 0.12 + GH / 2), 'glass'))
p.append(k.box((GW, T, GH), (0, gy, 0.12 + GH / 2), 'glass'))
p.append(k.box((T, GD, GH), (-gx, 0, 0.12 + GH / 2), 'glass'))
p.append(k.box((T, GD, GH), (gx, 0, 0.12 + GH / 2), 'glass'))
BAY = 2.4
for side in (-1, 1):
    y = side * gy
    n = round(GW / BAY)
    for i in range(n + 1):
        x = -gx + i * GW / n
        mat = 'mullion_y' if i in (2, 4) else 'frame'   # fotodagi sariq ustunchalar
        p.append(k.box((0.1, 0.12, GH), (x, y, 0.12 + GH / 2), mat))
    for z in (0.18, 2.7, GH + 0.05):
        p.append(k.box((GW, 0.12, 0.1), (0, y, z), 'frame'))
for side in (-1, 1):
    x = side * gx
    n = round(GD / BAY)
    for i in range(n + 1):
        y = -gy + i * GD / n
        p.append(k.box((0.12, 0.1, GH), (x, y, 0.12 + GH / 2), 'frame'))
    for z in (0.18, 2.7, GH + 0.05):
        p.append(k.box((0.12, GD, 0.1), (x, 0, z), 'frame'))
# shisha ustidagi plita (soyabon ichki qismi)
p.append(k.box((GW + 0.2, GD + 0.2, 0.25), (0, 0, GH + 0.12 + 0.12), 'concrete_d'))

# ---------- beton quti (tepasida) ----------
p.append(k.box((BX1 - BX0, BY1 - BY0, BH - CZ), ((BX0 + BX1) / 2, (BY0 + BY1) / 2, (CZ + BH) / 2), 'concrete'))
p.append(k.box((BX1 - BX0 + 0.16, BY1 - BY0 + 0.16, 0.14), ((BX0 + BX1) / 2, (BY0 + BY1) / 2, BH + 0.07), 'cap'))
# old yuzidagi panel choklari (beton plitalar)
for x in (-6.0, -2.4, 1.2, 4.8):
    p.append(k.box((0.06, 0.04, BH - CZ - 0.3), (x, BY0 - 0.01, (CZ + BH) / 2), 'concrete_d'))
# chap uchidagi tik qovurg'a (fotoda beton qutining chap burchagi)
p.append(k.box((0.35, 0.35, BH - CZ), (BX0 + 0.1, BY0 - 0.1, (CZ + BH) / 2), 'concrete_d'))

# ---------- soyabon: zang-sariq metall chet to'sin, fermalar, yog'och reykalar ----------
EB = 0.22
for y in (-cy + EB / 2, cy - EB / 2):
    p.append(k.box((W, EB, 0.32), (0, y, CZ), 'rust'))
for x in (-cx + EB / 2, cx - EB / 2):
    p.append(k.box((EB, D, 0.32), (x, 0, CZ), 'rust'))
# chet to'sinning pastki tokchasi (ferma ko'rinishi)
for y in (-cy + EB / 2, cy - EB / 2):
    p.append(k.box((W, 0.1, 0.08), (0, y, CZ - 0.42), 'rust'))
for x in (-cx + EB / 2, cx - EB / 2):
    p.append(k.box((0.1, D, 0.08), (x, 0, CZ - 0.42), 'rust'))
# ferma diagonallari (old va yon tomonlarda)
STEP = 1.1
n = int(W / STEP)
for side in (-1, 1):
    y = side * (cy - EB / 2)
    for i in range(n):
        x0 = -cx + i * W / n
        x1 = x0 + W / n
        a, b = (x0, y, CZ - 0.4), (x1, y, CZ - 0.12)
        if i % 2:
            a, b = (x0, y, CZ - 0.12), (x1, y, CZ - 0.4)
        p.append(k.beam(a, b, 0.05, 0.05, 'rust'))
n = int(D / STEP)
for side in (-1, 1):
    x = side * (cx - EB / 2)
    for i in range(n):
        y0 = -cy + i * D / n
        y1 = y0 + D / n
        a, b = (x, y0, CZ - 0.4), (x, y1, CZ - 0.12)
        if i % 2:
            a, b = (x, y0, CZ - 0.12), (x, y1, CZ - 0.4)
        p.append(k.beam(a, b, 0.05, 0.05, 'rust'))
# shisha devordan chetgacha to'sinlar (old/orqa — Y bo'ylab, yonlar — X bo'ylab)
for i in range(13):
    x = -gx + i * GW / 12
    for s in (-1, 1):
        p.append(k.box((0.12, cy - gy, 0.18), (x, s * (gy + (cy - gy) / 2), CZ + 0.02), 'rust'))
for i in range(7):
    y = -gy + i * GD / 6
    for s in (-1, 1):
        p.append(k.box((cx - gx, 0.12, 0.18), (s * (gx + (cx - gx) / 2), y, CZ + 0.02), 'rust'))
# yog'och reykalar (soyabon qopqog'i) — chet bo'ylab, oraliqli
SL = 0.16
for s in (-1, 1):
    n = int((cy - gy) / 0.3)
    for i in range(n):
        y = s * (gy + 0.15 + i * (cy - gy - 0.2) / n)
        p.append(k.box((W - 0.3, SL, 0.05), (0, y, CZ + 0.14), 'wood' if i % 3 else 'wood_d'))
    n = int((cx - gx) / 0.3)
    for i in range(n):
        x = s * (gx + 0.15 + i * (cx - gx - 0.2) / n)
        p.append(k.box((SL, GD + 0.2, 0.05), (x, 0, CZ + 0.14), 'wood' if i % 3 else 'wood_d'))

# ---------- ustunlar (burchaklarda beton, oraliqda ingichka metall) ----------
for sx in (-1, 1):
    for sy in (-1, 1):
        p.append(k.box((0.45, 0.45, CZ - 0.2), (sx * (cx - 0.35), sy * (cy - 0.35), (CZ - 0.2) / 2 + 0.06), 'concrete'))
for x in (-cx / 3, cx / 3):
    for sy in (-1, 1):
        p.append(k.cyl(0.07, CZ - 0.3, (x, sy * (cy - 0.3), (CZ - 0.3) / 2 + 0.06), 'rust', segs=8))

# ---------- banner-to'siq: old va chap tomonda, qora oyoqlarda ----------
BZ0, BZ1 = 0.45, 2.0        # banner pasti / tepasi
by = -gy - 0.9              # old banner chizig'i
bx = -gx - 0.9              # chap banner chizig'i
FX0, FX1 = -gx - 0.9, gx - 0.6
p.append(k.box((FX1 - FX0, 0.04, BZ1 - BZ0), ((FX0 + FX1) / 2, by, (BZ0 + BZ1) / 2), 'banner'))
p.append(k.box((0.04, GD + 1.2, BZ1 - BZ0), (bx, 0.3, (BZ0 + BZ1) / 2), 'banner'))
for i in range(13):
    x = FX0 + i * (FX1 - FX0) / 12
    p.append(k.box((0.05, 0.05, BZ0 + 0.05), (x, by + 0.05, BZ0 / 2 + 0.06), 'black'))
    p.append(k.beam((x, by + 0.05, 0.08), (x, by + 0.55, 0.08), 0.05, 0.04, 'black'))   # oyoq tayanchi
for i in range(8):
    y = -gy - 0.3 + i * (GD + 1.2) / 7
    p.append(k.box((0.05, 0.05, BZ0 + 0.05), (bx + 0.05, y, BZ0 / 2 + 0.06), 'black'))
# bannerdagi ko'k bloklar va yozuvlar (old yuz, −Y)
fy = by - 0.03
for x0, x1, z0, z1, m in ((-8.6, -5.6, 0.6, 1.25, 'blue'),      # "Совершайте пожертвования"
                          (-0.4, 1.6, 0.65, 1.9, 'blue'),       # avto
                          (2.6, 5.8, 0.85, 1.75, 'blue'),        # "Авиабилеты"
                          (-5.3, -2.8, 0.55, 1.95, 'blue_d')):   # bolalar surati
    p.append(k.box((x1 - x0, 0.03, z1 - z0), ((x0 + x1) / 2, fy, (z0 + z1) / 2), m))
p.append(k.text('Inson Uchun', 0.26, (-7.1, fy - 0.01, 1.62), 'blue_d'))
p.append(k.text('click', 0.34, (-1.8, fy - 0.01, 0.85), 'blue_d'))
p.append(k.text('click', 0.3, (7.2, fy - 0.01, 0.65), 'blue_d'))
p.append(k.text('Мое авто', 0.24, (-1.9, fy - 0.01, 1.55), 'black'))
# chap banner yuzida ham ko'k bloklar
for y0, y1 in ((-3.5, -0.5), (1.5, 4.5)):
    p.append(k.box((0.03, y1 - y0, 0.9), (bx - 0.03, (y0 + y1) / 2, 1.2), 'blue'))

# o't o'chirgich (o'ng burchakda, qizil)
p.append(k.box((0.5, 0.35, 0.9), (gx + 0.7, -gy - 0.4, 0.57), 'red'))

k.finish('zamok-elfov', p, HERE, [
    ('preview.png', (-14, -26, 9), (0, 0, 3)),
    ('preview_side.png', (24, -10, 6), (0, 0, 3)),
    ('preview_top.png', (-6, -18, 30), (0, 0, 2)),
])

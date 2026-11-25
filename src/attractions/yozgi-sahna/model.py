"""
Yozgi sahna (dam olish maskani) — oq bandshell: yarim aylana gumbazsimon soyabon (ko'p qirrali fasad, oltin rozetkalar),
ikki katta old ustun va arka, ichida qora LED ekran va chiroqlar fermasi, ikki yonida past qanotlar (yulduz-zigzag naqsh),
beton-tosh supa, old burchaklarida zinapoyalar, yonida g'ilofli kolonkalar. Rasm: foydalanuvchi fotosuratlari.
Skameykalar — alohida bezak (src/decor/sahna-skameykalari).

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/yozgi-sahna/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png, preview_back.png

Tuzilish (bitta `base` obyekt, animatsiyasiz). Old tomoni (tomoshabinlar) — Blender'da -Y. Markaz — xaritadagi maydoncha
izining o'rtasi (place.ts: 18 × 9 m), yer — z = 0. Asl o'lcham: eni ~17.6 m, chuqurligi ~8.6 m, balandligi ~6.9 m.
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'decor'))
from blender_kit import Kit  # noqa: E402

PALETTE = {
    'white': (0.88, 0.88, 0.86), 'white_d': (0.66, 0.66, 0.64), 'stone': (0.62, 0.55, 0.42), 'stone_d': (0.48, 0.42, 0.32),
    'step': (0.56, 0.52, 0.45), 'gold': (0.62, 0.42, 0.16), 'screen': (0.02, 0.02, 0.025), 'truss': (0.6, 0.62, 0.64),
    'lamp': (0.05, 0.05, 0.06), 'tarp': (0.72, 0.74, 0.77), 'brick': (0.36, 0.3, 0.25),
}
k = Kit(PALETTE)
p = []

# ====================== o'lchamlar (metr) ======================
PLAT_H = 0.9                # supa balandligi
YF = -2.9                   # supaning old cheti
YB = 3.6                    # orqa devor
PX = 6.6                    # supa old chetining yarim eni
COL_X, COL_Y = 4.7, -2.0    # old ustunlar
CAN_Z0, CAN_Z1 = 5.4, 6.5   # soyabon fasadi: pasti / tepasi


def polygon_prism(pts, z0, z1, mat):
    """XY tekislikdagi ko'pburchak → Z bo'yicha z0..z1 prizma"""
    import bmesh
    bm = bmesh.new()
    bot = [bm.verts.new((x, y, z0)) for x, y in pts]
    top = [bm.verts.new((x, y, z1)) for x, y in pts]
    bm.faces.new(top)
    bm.faces.new(bot[::-1])
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([bot[i], bot[j], top[j], top[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return k.obj('prism', bm, mat)


# ---------- supa: old tomoni to'g'ri, orqasi ko'p qirrali (yarim o'nikkiburchak) ----------
back = []
for i in range(7):
    a = math.pi * i / 6                                             # 0..180°: o'ngdan chapga orqa tomon bo'ylab
    back.append((PX * math.cos(a), YF + 1.0 + (YB - 0.3 - YF - 1.0) * math.sin(a) ** 0.6))   # orqa devor ichida tugaydi
plat = [(-PX, YF), (PX, YF), (PX, YF + 1.0)] + back[1:-1] + [(-PX, YF + 1.0)]
p.append(polygon_prism(plat, 0, PLAT_H - 0.06, 'stone'))
p.append(polygon_prism([(x * 1.01, y + (0.04 if y > YF + 0.1 else -0.04)) for x, y in plat], PLAT_H - 0.06, PLAT_H, 'stone_d'))  # chekka
for x in (-4.4, -2.2, 0, 2.2, 4.4):                                 # old yuzadagi panel choklari
    p.append(k.box((0.04, 0.03, PLAT_H - 0.2), (x, YF - 0.01, PLAT_H / 2), 'stone_d'))
p.append(k.box((2 * PX, 0.03, 0.04), (0, YF - 0.01, 0.12), 'stone_d'))

# ---------- zinapoyalar: old burchaklarda, tomoshabinlardan supaga ko'tariladi ----------
N_ST = 5
for sx in (-1, 1):
    for i in range(N_ST):
        h = PLAT_H * (i + 1) / (N_ST + 0.2)
        dp = (N_ST - i) * 0.3                                       # pastki zina eng oldinda
        p.append(k.box((2.0, dp, h), (sx * (PX - 1.0), YF - dp / 2 + 0.01, h / 2), 'step'))

# ---------- orqa devor, LED ekran, yon devorlar ----------
p.append(k.box((10.4, 0.4, CAN_Z0 + 0.2), (0, YB - 0.4, (CAN_Z0 + 0.2) / 2), 'white'))
p.append(k.box((7.6, 0.15, 3.4), (0, YB - 0.7, PLAT_H + 0.3 + 1.7), 'screen'))
for sx in (-1, 1):
    p.append(k.box((0.35, YB - COL_Y, CAN_Z0), (sx * (COL_X + 0.25), (COL_Y + YB) / 2, CAN_Z0 / 2), 'white'))
    p.append(k.box((0.12, 0.12, 4.0), (sx * 4.1, YB - 0.9, PLAT_H + 2.0), 'lamp'))   # ekran yonidagi tirgak

# ---------- old ustunlar va arka ----------
for sx in (-1, 1):
    x = sx * COL_X
    p.append(k.box((0.8, 0.8, CAN_Z0), (x, COL_Y, CAN_Z0 / 2), 'white'))
    p.append(k.box((1.0, 1.0, 0.25), (x, COL_Y, 0.125), 'white_d'))                    # asos
    # arka: ustundan ichkariga egilgan yoy (bo'laklar)
    for i in range(6):
        a0, a1 = math.pi / 2 * i / 6, math.pi / 2 * (i + 1) / 6
        r = 1.6
        xa, za = x - sx * (r - r * math.cos(a0)), 3.8 + r * math.sin(a0)
        xb, zb = x - sx * (r - r * math.cos(a1)), 3.8 + r * math.sin(a1)
        b = k.beam((xa, COL_Y, za), (xb, COL_Y, zb), 0.55, 0.35, 'white')
        p.append(b)
p.append(k.box((2 * COL_X - 3.0, 0.55, 0.5), (0, COL_Y, CAN_Z0 - 0.2), 'white'))         # arka tepasi

# ---------- soyabon: oldinga bo'rtgan ko'p qirrali fasad, rozetkalar ----------
SEG = 8
front = []
for i in range(SEG + 1):
    t = -1 + 2 * i / SEG
    front.append((t * 6.0, COL_Y - 0.2 - 1.8 * (1 - t * t)))   # chetlari orqaroq, o'rtasi oldinda (yoy)
canopy = [front[0]] + front[1:] + [(6.0, YB), (-6.0, YB)]
p.append(polygon_prism(canopy, CAN_Z0, CAN_Z1, 'white'))
p.append(polygon_prism([(x * 1.03, y - 0.15 if y < YB - 0.1 else y + 0.1) for x, y in canopy], CAN_Z1, CAN_Z1 + 0.12, 'white_d'))  # karniz
p.append(polygon_prism([(x * 0.6, (y - 0.7) * 0.6 + 0.7) for x, y in canopy], CAN_Z0 - 0.08, CAN_Z0, 'white_d'))  # ship oval
# fasad qirralari orasidagi tik "tishlar" va rozetkalar
for i in range(SEG):
    (xa, ya), (xb, yb) = front[i], front[i + 1]
    ang = math.atan2(yb - ya, xb - xa)
    mx, my = (xa + xb) / 2, (ya + yb) / 2
    nx, ny = math.sin(ang), -math.cos(ang)                          # tashqi normal (oldga)
    if i % 2 == 0 or i in (3, 4):
        cz = (CAN_Z0 + CAN_Z1) / 2
        p.append(k.cyl(0.36, 0.06, (mx + nx * 0.03, my + ny * 0.03, cz), 'gold', segs=20, rot=(math.pi / 2, 0, ang)))
        p.append(k.cyl(0.22, 0.08, (mx + nx * 0.05, my + ny * 0.05, cz), 'white', segs=16, rot=(math.pi / 2, 0, ang)))
        p.append(k.ball(0.08, (mx + nx * 0.08, my + ny * 0.08, cz), 'gold', sub=1))
    p.append(k.box((0.18, 0.18, CAN_Z1 - CAN_Z0 + 0.3), (xa, ya, (CAN_Z0 + CAN_Z1) / 2 + 0.15), 'white_d'))
p.append(k.box((0.18, 0.18, CAN_Z1 - CAN_Z0 + 0.3), (front[-1][0], front[-1][1], (CAN_Z0 + CAN_Z1) / 2 + 0.15), 'white_d'))

# ---------- chiroqlar fermasi ----------
TZ = 4.7
for dy in (-0.15, 0.15):
    for dz in (-0.15, 0.15):
        p.append(k.box((8.6, 0.04, 0.04), (0, COL_Y + 0.9 + dy, TZ + dz), 'truss'))
for i in range(11):
    x = -4.0 + i * 0.8
    p.append(k.box((0.04, 0.34, 0.34), (x, COL_Y + 0.9, TZ), 'truss'))
    p.append(k.box((0.22, 0.22, 0.26), (x + 0.4, COL_Y + 0.9, TZ - 0.36), 'lamp'))

# ---------- yon qanotlar: past oq bloklar, zigzag-yulduz naqsh, ravoqli tokcha ----------
for sx in (-1, 1):
    cx = sx * 7.15
    p.append(k.box((3.0, 4.6, 3.3), (cx, 1.0, 1.65), 'white'))
    p.append(k.box((3.2, 4.8, 0.14), (cx, 1.0, 3.37), 'white_d'))                       # karniz
    p.append(k.box((3.02, 4.62, 0.35), (cx, 1.0, 0.175), 'brick'))                     # tosh sokol
    yf = 1.0 - 2.3 - 0.03
    for j in range(3):                                                                  # zigzag (V) naqsh
        x0 = cx - 1.2 + j * 0.8
        p.append(k.beam((x0, yf, 2.95), (x0 + 0.4, yf, 2.45), 0.06, 0.06, 'white_d'))
        p.append(k.beam((x0 + 0.4, yf, 2.45), (x0 + 0.8, yf, 2.95), 0.06, 0.06, 'white_d'))
        p.append(k.box((0.06, 0.06, 0.35), (x0 + 0.4, yf, 2.2), 'white_d'))
    p.append(k.box((1.6, 0.06, 1.8), (cx, yf - 0.01, 1.3), 'white_d'))                  # ravoqli tokcha (soya)
    p.append(k.cyl(0.8, 0.06, (cx, yf - 0.01, 2.2), 'white_d', segs=16, rot=(math.pi / 2, 0, 0)))
    # g'ilofli kolonka (kumush brezent)
    p.append(k.box((1.0, 0.9, 1.9), (sx * 5.6, -2.9, 0.95), 'tarp'))
    p.append(k.box((1.06, 0.96, 0.08), (sx * 5.6, -2.9, 1.9), 'tarp'))

k.finish('YOZGI-SAHNA', p, HERE, [
    ('preview.png', (4.0, -19.0, 5.0), (0, 0, 3.0)),
    ('preview_back.png', (-14.0, 12.0, 12.0), (0, 0, 2.0)),
])

"""
Kirish darvozasi — "Central Park" sirk uslubidagi darvoza (rasm: foydalanuvchi fotosi). Bosh kirish yo'lagida, fontan oldida.

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/decor/kirish-darvoza/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png, preview_back.png

Tuzilish (bitta `base` obyekt, animatsiyasiz), old tomoni −Y (fontan va kiruvchilar tomoni):
  * 5 ta oltin ustun (qizil spiral chiziqli), har birining oldida orqa oyog'ida turgan oq ot haykali;
  * ustunlar ustida keng peshtoq: oltin ramka, jigarrang panellar, oq ot bo'rtmalari, o'rtada pushti "Central Park" taxtasi;
  * peshtoq ostida qizil parda gulchambarlari (har oraliqda) va ustunlar yonida tushgan parda uchlari;
  * tepada 4 ta chodir tom: qizil-krem chiziqli, botiq qirrali piramida, ostida oltin naqshli qizil belbog', uchida oltin shar;
  * chetki oraliqlarda oltin panjarali darvoza tabaqalari (o'rtadagi ikki oraliq ochiq — o'tish joyi);
  * ikki chetida qizil-oq romb naqshli past devorchalar.
Asl o'lcham: eni 16.6 m, chuqurligi ~1.6 m, balandligi ~9 m.
"""
import math
import sys
from pathlib import Path

import bmesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from blender_kit import Kit  # noqa: E402

SIGN_TEXT = 'Central Park'   # bo'sh qator ('') — taxta yozuvsiz qoladi

PALETTE = {
    'red': (0.78, 0.07, 0.1), 'red_d': (0.55, 0.04, 0.07), 'cream': (0.98, 0.9, 0.72), 'gold': (0.86, 0.66, 0.22),
    'gold_d': (0.65, 0.47, 0.14), 'brown': (0.42, 0.27, 0.16), 'pink': (0.86, 0.18, 0.5), 'white': (0.97, 0.97, 0.95),
    'horse': (0.96, 0.95, 0.93), 'grey': (0.75, 0.74, 0.72),
}
k = Kit(PALETTE)
p = []

COLS = [-6.0, -3.0, 0.0, 3.0, 6.0]      # ustunlar (X)
COL_TOP = 5.0                           # peshtoq osti
FR_Z0, FR_Z1 = 5.0, 6.25                # peshtoq
BAND_Z0, BAND_Z1 = 6.25, 6.95           # chodirlar ostidagi belbog'
FR_D = 0.6                              # peshtoq chuqurligi
TENTS = [-4.5, -1.5, 1.5, 4.5]
TENT_H = 1.35                           # chodir yarim eni
TENT_TOP = 1.95                         # chodir balandligi

# ====================== ustunlar ======================
for x in COLS:
    p.append(k.box((0.7, 0.7, 0.3), (x, 0, 0.15), 'gold_d'))                       # asos
    p.append(k.cyl(0.3, 0.15, (x, 0, 0.37), 'gold', segs=16))
    p.append(k.cyl(0.22, COL_TOP - 0.45, (x, 0, (COL_TOP + 0.45) / 2), 'gold', segs=16))
    # qizil spiral chiziq
    n = 24
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        a0, a1 = t0 * 6 * math.pi, t1 * 6 * math.pi
        z0, z1 = 0.5 + t0 * (COL_TOP - 0.7), 0.5 + t1 * (COL_TOP - 0.7)
        p.append(k.beam((x + 0.225 * math.cos(a0), 0.225 * math.sin(a0), z0), (x + 0.225 * math.cos(a1), 0.225 * math.sin(a1), z1),
                        0.09, 0.04, 'red'))
    p.append(k.cyl(0.32, 0.18, (x, 0, COL_TOP - 0.18), 'gold_d', segs=16, r2=0.24))  # kapitel
    for zz in (1.2, 3.6):                                                             # oltin halqalar
        p.append(k.cyl(0.26, 0.08, (x, 0, zz), 'gold_d', segs=16))


# ====================== oq ot haykali (orqa oyoqlarida turgan) ======================
def horse(cx, cy, cz, face=1):
    """face: +1 — o'ngga (X+) qaragan, −1 — chapga. cz — tuyoq osti"""
    res = []
    f = face

    def P(x, y, z):
        return (cx + f * x, cy + y, cz + z)
    # tana: qiya (oldi baland)
    body = k.ball(0.33, (0, 0, 0), 'horse', sub=1, scale=(1.5, 0.7, 0.78))
    body.rotation_euler = (0, -f * math.radians(38), 0)
    body.location = P(0.05, 0, 0.78)
    res.append(body)
    res.append(k.ball(0.24, P(-0.28, 0, 0.52), 'horse', sub=1, scale=(1.0, 0.8, 1.0)))      # sag'ri
    # bo'yin va bosh
    res.append(k.beam(P(0.3, 0, 1.0), P(0.42, 0, 1.38), 0.26, 0.2, 'horse'))
    head = k.ball(0.13, (0, 0, 0), 'horse', sub=1, scale=(1.7, 0.75, 0.8))
    head.rotation_euler = (0, f * math.radians(25), 0)
    head.location = P(0.55, 0, 1.4)
    res.append(head)
    for dy in (-0.05, 0.05):                                                                  # quloqlar
        res.append(k.cyl(0.03, 0.1, P(0.43, dy, 1.53), 'horse', segs=6, r2=0.005))
    # yol (yollar) — bo'yin ustida
    for i in range(5):
        res.append(k.ball(0.06, P(0.27 + i * 0.04, 0, 1.06 + i * 0.09), 'grey', sub=1, scale=(1.0, 0.6, 1.3)))
    # orqa oyoqlar (yerda), old oyoqlar (havoda, bukilgan)
    for dy in (-0.1, 0.1):
        res.append(k.beam(P(-0.3, dy, 0.45), P(-0.2, dy, 0.18), 0.12, 0.11, 'horse'))
        res.append(k.beam(P(-0.2, dy, 0.18), P(-0.24, dy, 0.0), 0.07, 0.07, 'horse'))
        res.append(k.beam(P(0.32, dy, 0.85), P(0.5, dy + 0.02, 0.68), 0.1, 0.1, 'horse'))
        res.append(k.beam(P(0.5, dy + 0.02, 0.68), P(0.47, dy, 0.48), 0.065, 0.065, 'horse'))
    # dum
    res.append(k.beam(P(-0.42, 0, 0.58), P(-0.62, 0, 0.25), 0.08, 0.06, 'grey'))
    res.append(k.beam(P(-0.62, 0, 0.25), P(-0.6, 0, 0.05), 0.07, 0.05, 'grey'))
    return res


for i, x in enumerate(COLS):
    face = -1 if x > 0 else 1
    # tagida oltin tokcha (ustunga mahkamlangan)
    p.append(k.cyl(0.38, 0.12, (x, -0.5, 1.95), 'gold', segs=16))
    p.append(k.box((0.12, 0.3, 0.12), (x, -0.32, 1.88), 'gold_d'))
    p.extend(horse(x, -0.5, 2.01, face))

# ====================== peshtoq (frieze) ======================
W = 2 * 7.0
p.append(k.box((W, FR_D, FR_Z1 - FR_Z0), (0, 0, (FR_Z0 + FR_Z1) / 2), 'brown'))
for z in (FR_Z0 + 0.06, FR_Z1 - 0.06):                                               # oltin ramka (yuqori/past)
    for y in (-FR_D / 2 - 0.03, FR_D / 2 + 0.03):
        p.append(k.box((W + 0.1, 0.08, 0.14), (0, y, z), 'gold'))
for x in (-W / 2, W / 2):
    p.append(k.box((0.14, FR_D + 0.14, FR_Z1 - FR_Z0), (x, 0, (FR_Z0 + FR_Z1) / 2), 'gold'))


def horse_relief(cx, y, cz, face, side):
    """Peshtoqdagi oq ot bo'rtmasi (yassi, ikki oyoqda turgan) — jigarrang panel ustida"""
    s = side  # −1 — old yuz (−Y), +1 — orqa
    res = [k.box((1.5, 0.05, 0.95), (cx, y + s * 0.01, cz), 'gold_d'), k.box((1.38, 0.06, 0.83), (cx, y + s * 0.03, cz), 'brown')]
    yy = y + s * 0.06
    f = face
    res.append(k.ball(0.22, (cx, yy, cz - 0.02), 'white', sub=2, scale=(1.5, 0.25, 0.7)))
    res.append(k.beam((cx + f * 0.25, yy, cz + 0.05), (cx + f * 0.38, yy, cz + 0.3), 0.14, 0.05, 'white'))
    res.append(k.ball(0.09, (cx + f * 0.47, yy, cz + 0.32), 'white', sub=1, scale=(1.6, 0.35, 0.8)))
    for dx in (-0.22, -0.12):
        res.append(k.beam((cx + f * dx, yy, cz - 0.1), (cx + f * (dx - 0.04), yy, cz - 0.38), 0.05, 0.04, 'white'))
    for dx in (0.18, 0.26):
        res.append(k.beam((cx + f * dx, yy, cz), (cx + f * (dx + 0.15), yy, cz - 0.12), 0.05, 0.04, 'white'))
    res.append(k.beam((cx - f * 0.32, yy, cz), (cx - f * 0.5, yy, cz - 0.28), 0.06, 0.04, 'white'))
    return res


FZ = (FR_Z0 + FR_Z1) / 2
for side in (-1, 1):
    y = side * FR_D / 2
    for cx, face in ((-5.6, 1), (-3.7, -1), (3.7, 1), (5.6, -1)):
        p.extend(horse_relief(cx, y, FZ, face if side < 0 else -face, side))
    # o'rtadagi pushti taxta
    p.append(k.box((3.4, 0.06, 1.0), (0, y + side * 0.03, FZ), 'gold'))
    p.append(k.box((3.2, 0.08, 0.84), (0, y + side * 0.05, FZ), 'pink'))
    if SIGN_TEXT:
        p.append(k.text(SIGN_TEXT, 0.42, (0, y + side * 0.1, FZ), 'white', '-Y' if side < 0 else '+Y'))
    # oraliq oltin naqshlar (romb)
    for cx in (-4.65, -2.25, 2.25, 4.65):
        p.append(k.box((0.3, 0.05, 0.3), (cx, y + side * 0.03, FZ), 'gold', rot=(0, math.pi / 4, 0)))

# ====================== qizil parda gulchambarlari ======================
def swag(x0, x1, z_top, sag, depth_y, folds=5, cols=12, rows=4):
    """Peshtoq ostidagi osilgan parda (gulchambar): pastki cheti zanjir chizig'i, burmalar — Y bo'ylab to'lqin"""
    bm = bmesh.new()
    grid = []
    for r in range(rows + 1):
        t = r / rows
        row = []
        for c in range(cols + 1):
            u = c / cols
            x = x0 + (x1 - x0) * u
            bottom = z_top - 0.25 - sag * math.sin(math.pi * u)
            z = z_top + (bottom - z_top) * t
            y = depth_y - 0.06 * math.sin(folds * 2 * math.pi * u) * t - 0.08 * math.sin(math.pi * u) * t
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for r in range(rows):
        for c in range(cols):
            bm.faces.new([grid[r][c], grid[r][c + 1], grid[r + 1][c + 1], grid[r + 1][c]])
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.04)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return k.obj('swag', bm, 'red')


for i in range(len(COLS) - 1):
    a, b = COLS[i] + 0.25, COLS[i + 1] - 0.25
    p.append(swag(a, b, FR_Z0 + 0.02, 0.85, -FR_D / 2 - 0.08))
    p.append(swag(a + 0.1, b - 0.1, FR_Z0 - 0.02, 0.45, -FR_D / 2 - 0.16, folds=4))   # ustki qisqa qavat
# ustunlar yonidagi tushgan parda uchlari (bog'langan)
for x in COLS:
    for s in (-1, 1):
        if (x == COLS[0] and s < 0) or (x == COLS[-1] and s > 0):
            continue
        xx = x + s * 0.32
        p.append(k.beam((xx, -FR_D / 2 - 0.1, FR_Z0), (xx + s * 0.05, -0.36, 3.6), 0.22, 0.08, 'red'))
        p.append(k.cyl(0.08, 0.6, (xx + s * 0.07, -0.36, 3.3), 'red_d', segs=8, r2=0.14))
        p.append(k.cyl(0.07, 0.06, (xx + s * 0.05, -0.36, 3.62), 'gold', segs=8))      # bog'ich
# chetki ustunlar tashqarisidagi katta parda
for s in (-1, 1):
    x = s * 6.35
    p.append(k.beam((x, -FR_D / 2 - 0.1, FR_Z0), (x + s * 0.1, -0.35, 2.4), 0.36, 0.1, 'red'))
    p.append(k.cyl(0.1, 1.0, (x + s * 0.12, -0.35, 1.9), 'red_d', segs=8, r2=0.2))

# ====================== chodirlar ======================
def tent(cx, z0):
    """Botiq qirrali to'rt qirrali chodir: har yon 8 ta chiziq, navbatma-navbat qizil va krem"""
    rows, stripes = 8, 8
    objs = {'red': bmesh.new(), 'cream': bmesh.new()}
    sides = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    for sx, sy in sides:
        nx, ny = -sy, sx                                    # yon bo'ylab yo'nalish
        for st in range(stripes):
            bm = objs['red' if st % 2 == 0 else 'cream']
            grid = []
            for r in range(rows + 1):
                t = r / rows
                f = (1 - t) ** 1.5
                z = z0 + TENT_TOP * (1 - (1 - t) ** 1.15)
                row = []
                for u in (st / stripes, (st + 1) / stripes):
                    uu = (u * 2 - 1)
                    x = cx + (sx * TENT_H + nx * uu * TENT_H) * f
                    y = (sy * TENT_H + ny * uu * TENT_H) * f
                    row.append(bm.verts.new((x, y, z)))
                grid.append(row)
            for r in range(rows):
                bm.faces.new([grid[r][0], grid[r][1], grid[r + 1][1], grid[r + 1][0]])
    res = []
    for mat, bm in objs.items():
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        res.append(k.obj('tent', bm, mat))
    # qirralar bo'ylab oltin hoshiya va uchida shar
    for cxs, cys in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        prev = None
        for r in range(9):
            t = r / 8
            f = (1 - t) ** 1.5
            pt = (cx + cxs * TENT_H * f, cys * TENT_H * f, z0 + TENT_TOP * (1 - (1 - t) ** 1.15))
            if prev:
                res.append(k.beam(prev, pt, 0.05, 0.05, 'gold'))
            prev = pt
    res.append(k.ball(0.11, (cx, 0, z0 + TENT_TOP + 0.08), 'gold', sub=2))
    res.append(k.cyl(0.02, 0.35, (cx, 0, z0 + TENT_TOP + 0.3), 'gold_d', segs=6))
    return res


for cx in TENTS:
    # belbog': qizil, oltin hoshiya, oldida oltin rombchalar (bezak)
    p.append(k.box((2 * TENT_H + 0.25, 2 * TENT_H + 0.25, BAND_Z1 - BAND_Z0), (cx, 0, (BAND_Z0 + BAND_Z1) / 2), 'red'))
    for z in (BAND_Z0 + 0.04, BAND_Z1 - 0.04):
        p.append(k.box((2 * TENT_H + 0.33, 2 * TENT_H + 0.33, 0.07), (cx, 0, z), 'gold'))
    for side in (-1, 1):
        for j in range(5):
            xx = cx - TENT_H + 0.27 + j * (2 * TENT_H - 0.54) / 4
            p.append(k.box((0.24, 0.04, 0.24), (xx, side * (TENT_H + 0.14), (BAND_Z0 + BAND_Z1) / 2), 'gold', rot=(0, math.pi / 4, 0)))
    # pastki tishli (festonli) chet
    for j in range(7):
        xx = cx - TENT_H + 0.2 + j * (2 * TENT_H - 0.4) / 6
        for side in (-1, 1):
            p.append(k.cyl(0.17, 0.04, (xx, side * (TENT_H + 0.13), BAND_Z0 - 0.02), 'gold', segs=8,
                           rot=(math.pi / 2, 0, 0)))
    p.extend(tent(cx, BAND_Z1))

# ====================== oltin panjarali darvoza tabaqalari (chetki oraliqlar) ======================
for a, b in ((COLS[0], COLS[1]), (COLS[3], COLS[4])):
    x0, x1 = a + 0.3, b - 0.3
    gy = 0.45
    p.append(k.box((x1 - x0, 0.06, 0.08), (0.5 * (x0 + x1), gy, 0.15), 'gold'))
    p.append(k.box((x1 - x0, 0.06, 0.08), (0.5 * (x0 + x1), gy, 1.6), 'gold'))
    n = 14
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        top = 2.6 + 0.5 * math.sin(math.pi * i / n)
        p.append(k.box((0.04, 0.04, top - 0.15), (x, gy, (top + 0.15) / 2), 'gold'))
        p.append(k.cyl(0.05, 0.1, (x, gy, top + 0.03), 'gold', segs=4, r2=0.0))
    for i in range(n):                                                    # pastki qismdagi aylana naqshlar
        x = x0 + (x1 - x0) * (i + 0.5) / n
        p.append(k.cyl(0.08, 0.03, (x, gy, 0.85), 'gold', segs=6, rot=(math.pi / 2, 0, 0)))

# ====================== chetki romb naqshli devorchalar ======================
for s in (-1, 1):
    x0, x1 = s * 6.45, s * 8.3
    cx, w = (x0 + x1) / 2, abs(x1 - x0)
    H = 2.4
    p.append(k.box((w, 0.3, H), (cx, 0, H / 2), 'red'))
    p.append(k.box((w + 0.12, 0.38, 0.12), (cx, 0, H + 0.06), 'gold'))
    p.append(k.box((w + 0.12, 0.38, 0.12), (cx, 0, 0.06), 'gold'))
    for xe in (x0, x1):
        p.append(k.box((0.1, 0.36, H), (xe, 0, H / 2), 'gold'))
    # oq rombchalar (old va orqa yuzada) — shaxmat tartibida
    nx, nz = 4, 6
    for i in range(nx):
        for j in range(nz):
            if (i + j) % 2:
                continue
            xx = min(x0, x1) + (i + 0.5) * w / nx
            zz = 0.2 + (j + 0.5) * (H - 0.4) / nz
            for side in (-1, 1):
                p.append(k.box((0.3, 0.03, 0.3), (xx, side * 0.16, zz), 'white', rot=(0, math.pi / 4, 0)))
    # tepasida kichik oltin shar ustunchalar
    for xe in (x0, x1):
        p.append(k.ball(0.12, (xe, 0, H + 0.22), 'gold', sub=2))

k.finish('DARVOZA', p, HERE, [
    ('preview.png', (2.0, -21.0, 4.5), (0, 0, 4.2)),
    ('preview_back.png', (-12.0, 14.0, 8.0), (0, 0, 4.0)),
])

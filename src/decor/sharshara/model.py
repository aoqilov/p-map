"""
Sharshara — "Замок эльфов" (13) yonidagi kichik kaskad. Haqiqatda relyef bo'yicha tushadi; xaritada yer tekis, shuning uchun
tekis yerga qo'yilgan "etajerka": tosh pog'onalar, har birida sayoz hovuzcha, chetidan pastkisiga suv pardasi tushadi.
Bezak-bino: src/decor/sharshara/building.ts (plandagi yo'l o'rnida — plitka kesiladi, marshrut o'tmaydi).

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/decor/sharshara/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, basins.json, preview.png, preview_top.png

Tuzilish (bitta `base` obyekt): 5 ta tosh pog'ona (+Y — eng baland, boshi), har birida suv, old cheti — silliq tosh
"til" (suv shu yerdan quyiladi), pastda (−Y) yer sathidagi hovuzcha. Chetlarda xarsang toshlar, butalar, gullar,
kechasi yonadigan suv osti chiroqlari.
Materiallar nomi bilan Decor.tsx da jonlantiriladi: `fall` — suv pardalari (tekstura pastga oqadi, UV: v — tushish bo'ylab),
`water` — hovuzchalar: xaritada ular o'rniga hovuz suvi shaderi chiziladi (konturlar → basins.json).
Old tomoni (pastki hovuzcha, suv oqib boradigan tomon) — Blender'da -Y. Asl o'lcham: 7 × 22.4 m, balandligi ~2 m.
"""
import json
import math
import random
import sys
from pathlib import Path

import bmesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from blender_kit import Kit  # noqa: E402

random.seed(7)
PALETTE = {
    'stone': (0.55, 0.52, 0.48), 'stone_d': (0.4, 0.38, 0.35), 'rock1': (0.5, 0.47, 0.43), 'rock2': (0.45, 0.37, 0.3),
    'lip': (0.66, 0.64, 0.6), 'water': (0.18, 0.5, 0.72), 'fall': (0.85, 0.94, 1.0), 'foam': (0.95, 0.98, 1.0),
    'bush': (0.22, 0.48, 0.22), 'bush2': (0.3, 0.56, 0.26), 'fl_p': (0.92, 0.4, 0.6), 'fl_y': (1.0, 0.85, 0.3),
    'fl_w': (0.98, 0.97, 0.95), 'glow': (0.75, 0.92, 1.0),
}
k = Kit(PALETTE, glow=('glow',), glass=('fall',), glass_alpha=0.8)
p = []

# ====================== o'lchamlar ======================
Y_END = 11.0                                # boshi (eng baland pog'ona orqa cheti)
FRONT = [-6.8, -3.0, 0.8, 4.4, 7.8]         # pog'onalarning old cheti (pastdan yuqoriga)
TOP = [0.5, 0.82, 1.14, 1.46, 1.78]         # pog'ona usti
HW = [3.2, 3.0, 2.75, 2.5, 2.25]            # yarim eni
POOL_Y0, POOL_Y1, POOL_HW = -11.1, -6.2, 3.4
POOL_WATER = 0.2


def rrect(x0, x1, y0, y1, r, n=4, jitter=0.0):
    """Burchaklari yumaloq to'rtburchak (soat strelkasiga teskari), ozgina notekis — tabiiy tosh"""
    r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            j = 1 + random.uniform(-jitter, jitter)
            pts.append((cx + r * j * math.cos(a), cy + r * j * math.sin(a)))
    return pts


def slab(pts, z0, z1, mat):
    """XY konturni z0..z1 oralig'ida qalin plita qilish"""
    bm = bmesh.new()
    bot = [bm.verts.new((x, y, z0)) for x, y in pts]
    top = [bm.verts.new((x, y, z1)) for x, y in pts]
    bm.faces.new(top)
    bm.faces.new(bot[::-1])
    n = len(pts)
    for i in range(n):
        bm.faces.new([bot[i], bot[(i + 1) % n], top[(i + 1) % n], top[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return k.obj('slab', bm, mat)


def curtain(x0, x1, y_lip, z_top, z_bot, mat='fall', cols=6, rows=6):
    """Suv pardasi: lab chetidan ozgina oldinga egilib tushadi. UV: u — eni bo'ylab (1 m = 1), v — tushish bo'ylab"""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    drop = z_top - z_bot
    grid, rc = [], {}
    for r in range(rows + 1):
        s = r / rows
        y = y_lip - 0.35 * math.sqrt(s) * min(1.0, drop / 0.35)   # parabola: tepada oldinga otiladi
        z = z_top - drop * s
        row = []
        for c in range(cols + 1):
            v = bm.verts.new((x0 + (x1 - x0) * c / cols, y, z))
            rc[v] = (r, c)
            row.append(v)
        grid.append(row)
    for r in range(rows):
        for c in range(cols):
            f = bm.faces.new([grid[r][c], grid[r][c + 1], grid[r + 1][c + 1], grid[r + 1][c]])
            for loop in f.loops:
                ri, ci = rc[loop.vert]
                loop[uv].uv = ((x1 - x0) * ci / cols, drop * 2.5 * ri / rows)
    return k.obj('fall', bm, mat)


def rock(x, y, z, r, mat=None):
    s = (random.uniform(0.9, 1.3), random.uniform(0.8, 1.2), random.uniform(0.55, 0.85))
    return k.ball(r, (x, y, z + r * s[2] * 0.45), mat or random.choice(('rock1', 'rock2', 'stone_d')), sub=1, scale=s)


# ---------- pastki hovuzcha (yer sathida) ----------
p.append(slab(rrect(-POOL_HW, POOL_HW, POOL_Y0, POOL_Y1, 1.6, n=5, jitter=0.04), 0.0, 0.12, 'stone_d'))
BASINS = []  # suv sirtlari → basins.json (xaritada hovuz suvi shaderi bilan chiziladi, Decor.tsx)


def water(pts, z0, z1):
    BASINS.append({'poly': [[round(x, 3), round(y, 3)] for x, y in pts], 'z': round(z1, 3)})
    return slab(pts, z0, z1, 'water')


p.append(water(rrect(-POOL_HW + 0.35, POOL_HW - 0.35, POOL_Y0 + 0.35, POOL_Y1 + 0.4, 1.3, n=5), 0.12, POOL_WATER))
# hovuzcha atrofidagi xarsanglar (old va yon tomonlar)
for i in range(16):
    a = math.pi * (1.05 + 0.9 * i / 15)
    x = POOL_HW * 0.98 * math.cos(a)
    y = (POOL_Y0 + POOL_Y1) / 2 + (POOL_Y1 - POOL_Y0) / 2 * 1.02 * math.sin(a)
    p.append(rock(x, y, 0.0, random.uniform(0.28, 0.42)))
for side in (-1, 1):
    for y in (-8.0, -6.9):
        p.append(rock(side * (POOL_HW - 0.05), y, 0.0, random.uniform(0.32, 0.45)))

# ---------- pog'onalar ----------
for i, (f, t, hw) in enumerate(zip(FRONT, TOP, HW)):
    p.append(slab(rrect(-hw, hw, f, Y_END, 0.9, n=4, jitter=0.05), 0.0, t, 'stone'))
    # suv: shu pog'onaning ustida, keyingi pog'ona old chetigacha
    back = FRONT[i + 1] - 0.05 if i + 1 < len(FRONT) else Y_END - 0.45
    p.append(water(rrect(-hw + 0.4, hw - 0.4, f + 0.12, back, 0.5, n=3), t, t + 0.07))
    # old lab: silliq yassi tosh, suv shu yerdan quyiladi
    lw = hw - 0.6
    p.append(k.box((2 * lw, 0.4, 0.1), (0, f - 0.02, t + 0.03), 'lip'))
    # suv pardasi pastki pog'ona (yoki hovuzcha) suviga
    z_bot = TOP[i - 1] + 0.07 if i > 0 else POOL_WATER
    p.append(curtain(-lw + 0.1, lw - 0.1, f - 0.2, t + 0.08, z_bot))
    # tushgan joyda ko'pik
    for j in range(6):
        x = -lw + 0.3 + (2 * lw - 0.6) * j / 5
        p.append(k.ball(random.uniform(0.18, 0.26), (x, f - 0.6 - random.uniform(0, 0.2), z_bot + 0.02), 'foam', sub=1,
                        scale=(1.3, 1.0, 0.3)))
    # yon chetlarda xarsanglar (suvni ushlab turadi)
    n = max(3, int((back - f) / 0.8))
    for j in range(n):
        y = f + 0.3 + (back - f - 0.4) * j / max(1, n - 1)
        for side in (-1, 1):
            p.append(rock(side * (hw - 0.2), y, t - 0.05, random.uniform(0.22, 0.34)))
    # lab yonlaridagi kattaroq toshlar
    for side in (-1, 1):
        p.append(rock(side * (hw - 0.25), f + 0.05, t - 0.1, 0.42))
# eng tepada: suv chiqadigan tosh to'plami (buloq)
for x, y, r in ((0, Y_END - 0.2, 0.6), (-0.9, Y_END - 0.35, 0.45), (0.95, Y_END - 0.3, 0.5), (-0.4, Y_END - 0.8, 0.35),
                (0.5, Y_END - 0.75, 0.32)):
    p.append(rock(x, y, TOP[-1] - 0.05, r))

# ---------- chetlarda butalar va gullar (yerda) ----------
for i in range(14):
    y = -9.5 + 20.0 * i / 13
    hw = next((h for f, h in zip(reversed(FRONT), reversed(HW)) if y >= f), POOL_HW)
    for side in (-1, 1):
        x = side * (hw + random.uniform(0.25, 0.5))
        if abs(x) > 3.45:
            x = side * 3.45
        p.append(k.ball(random.uniform(0.3, 0.42), (x, y + random.uniform(-0.3, 0.3), 0.25), random.choice(('bush', 'bush2')),
                        sub=1, scale=(1, 1, 0.8)))
        if i % 2 == 0:
            for c in range(3):
                p.append(k.ball(0.07, (x + random.uniform(-0.25, 0.25), y + random.uniform(-0.25, 0.25), 0.5),
                                random.choice(('fl_p', 'fl_y', 'fl_w')), sub=1))

# ---------- kechasi yonadigan suv osti chiroqlari (har lab ostida va hovuzchada) ----------
for i, f in enumerate(FRONT):
    z = TOP[i - 1] + 0.05 if i > 0 else POOL_WATER - 0.02
    for x in (-0.8, 0.8):
        p.append(k.cyl(0.12, 0.04, (x, f - 0.9, z), 'glow', segs=10))

(HERE / 'basins.json').write_text(json.dumps(BASINS), encoding='utf8')
k.finish('SHARSHARA', p, HERE, [
    ('preview.png', (9.0, -17.0, 7.0), (0, -2.0, 0.8)),
    ('preview_top.png', (-10.0, 8.0, 12.0), (0, 0, 0.8)),
])

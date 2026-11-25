"""
Sharli fontan — dumaloq maydon o'rtasidagi granit havza (rasm: foydalanuvchi fotosurati): past tashqi devor, ustida keng
tekis qirra (o'tirsa bo'ladi), ichki baland halqa, havzada suv va kichik favvoralar, qirrada 8 ta granit postament ustida
granit sharlar. Atrofidagi 4 ta skameyka — config.ts da (sahna skameykasi modeli), joyi va to'siq — building.ts.

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/decor/sharli-fontan/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, basins.json, preview.png

Materiallar: `water` — havza suvi (xaritada hovuz shaderi bilan, basins.json), `jet` — favvoralar (oqim teksturasi).
Markaz — (0, 0), yer — z = 0. Asl o'lcham: diametri 10 m, balandligi ~1.45 m (sharlar tepasi).
"""
import json
import math
import sys
from pathlib import Path

import bmesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from blender_kit import Kit  # noqa: E402

PALETTE = {
    'granite': (0.52, 0.47, 0.4), 'granite_l': (0.64, 0.6, 0.53), 'granite_d': (0.36, 0.33, 0.29), 'ball': (0.6, 0.6, 0.57),
    'floor': (0.25, 0.3, 0.22), 'water': (0.3, 0.42, 0.3), 'jet': (0.85, 0.93, 0.97),
}
k = Kit(PALETTE)
p = []

R_OUT = 5.0                 # tashqi devor radiusi
R_LEDGE = 3.75              # keng qirraning ichki cheti
R_IN = 3.45                 # ichki halqa (suv cheti)
H_OUT = 0.5                 # tashqi devor / qirra balandligi
H_IN = 0.66                 # ichki halqa balandligi
FLOOR, WATER_Z = 0.15, 0.5
SEGS = 56


def lathe(profile, mat, segs=SEGS):
    """(r, z) profil → aylanma jism (yopiq profil)"""
    bm = bmesh.new()
    rings = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        rings.append([bm.verts.new((r * math.cos(a), r * math.sin(a), z)) for r, z in profile])
    n = len(profile)
    for i in range(segs):
        A, B = rings[i], rings[(i + 1) % segs]
        for j in range(n):
            jj = (j + 1) % n
            bm.faces.new([A[j], B[j], B[jj], A[jj]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return k.obj('lathe', bm, mat)


# ---------- havza: tashqi devor + keng qirra (bir jism), ichki halqa, tub ----------
p.append(lathe([(R_LEDGE, FLOOR), (R_LEDGE, H_OUT), (R_OUT - 0.06, H_OUT), (R_OUT, H_OUT - 0.06), (R_OUT, 0.0), (R_LEDGE, 0.0)], 'granite'))
p.append(lathe([(R_OUT + 0.06, 0.0), (R_OUT + 0.06, 0.08), (R_OUT - 0.02, 0.08), (R_OUT - 0.02, 0.0)], 'granite_d'))   # tagidagi bordyur
p.append(lathe([(R_IN, FLOOR), (R_IN, H_IN), (R_LEDGE + 0.02, H_IN), (R_LEDGE + 0.02, H_OUT - 0.01), (R_IN, H_OUT - 0.01)], 'granite_l'))
p.append(k.cyl(R_IN, FLOOR, (0, 0, FLOOR / 2), 'floor', segs=SEGS))
BASIN = [(round((R_IN - 0.02) * math.cos(2 * math.pi * i / 40), 3), round((R_IN - 0.02) * math.sin(2 * math.pi * i / 40), 3))
         for i in range(40)]
p.append(k.cyl(R_IN - 0.02, WATER_Z - FLOOR, (0, 0, (WATER_Z + FLOOR) / 2), 'water', segs=40))

# ---------- qirradagi 8 ta postament va granit sharlar ----------
R_PED = (R_LEDGE + R_OUT) / 2 + 0.05
for i in range(8):
    a = 2 * math.pi * i / 8 + math.pi / 8                          # yo'laklar (diagonallar) orasida emas, teng bo'lingan
    x, y = R_PED * math.cos(a), R_PED * math.sin(a)
    p.append(k.box((0.72, 0.72, 0.5), (x, y, H_OUT + 0.25), 'granite_l', rot=(0, 0, a)))
    p.append(k.box((0.78, 0.78, 0.05), (x, y, H_OUT + 0.025), 'granite_d', rot=(0, 0, a)))
    p.append(k.ball(0.34, (x, y, H_OUT + 0.5 + 0.32), 'ball', sub=2))


# ---------- favvoralar: kichik tik suv ustunchalari (UV — oqim bo'ylab, xaritada pastga oqadi) ----------
def jet(x, y, h, r0=0.05, r1=0.11, sides=8):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    rows = []
    for t in (0.0, 0.7, 1.0):
        z = WATER_Z + h * t
        rr = r0 + (r1 - r0) * (t / 0.7 if t <= 0.7 else 1 - (t - 0.7) / 0.3 * 0.9)
        rows.append(([bm.verts.new((x + rr * math.cos(2 * math.pi * s / sides), y + rr * math.sin(2 * math.pi * s / sides), z))
                      for s in range(sides)], t))
    for (ra, ta), (rb, tb) in zip(rows, rows[1:]):
        for s in range(sides):
            f = bm.faces.new([ra[s], ra[(s + 1) % sides], rb[(s + 1) % sides], rb[s]])
            for loop, (u, v) in zip(f.loops, [(s / sides, ta), ((s + 1) / sides, ta), ((s + 1) / sides, tb), (s / sides, tb)]):
                loop[uv].uv = (u, v * 2)
    return k.obj('jet', bm, 'jet')


p.append(jet(0, 0, 0.9, r0=0.06, r1=0.16))
for i in range(6):
    a = 2 * math.pi * i / 6
    p.append(jet(2.0 * math.cos(a), 2.0 * math.sin(a), 0.45))

(HERE / 'basins.json').write_text(json.dumps([{'poly': [list(v) for v in BASIN], 'z': WATER_Z}]), encoding='utf8')
k.finish('SHARLI-FONTAN', p, HERE, [('preview.png', (5.5, -9.0, 5.0), (0, 0, 0.5))])

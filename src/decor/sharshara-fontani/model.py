"""
Sharshara ostidagi fontan — aylana maydon o'rtasida (bezak-bino: src/decor/sharshara-fontani/building.ts). Rasm: foydalanuvchi
panoramasi (qizil granit qiya devorli dumaloq havza, o'rtada qirrali ustun ustida boshida savat ko'targan ayol haykali).

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/decor/sharshara-fontani/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, basins.json, preview.png, preview_close.png

Tuzilish (bitta `base` obyekt): havza (tashqi devori qiya qizil granit, ustida keng granit qirra, tubi och plitka),
o'rtada granit supa, qirrali (kannelyurali) oq ustun, oq marmar haykal (statue.py: boshida mevali savat ko'targan ayol,
burmali etak, yonida uzum barglari tushirilgan mato-tirgak), qirra ustidagi bronza quvurchalardan markazga qarab otiladigan suv yoylari,
maydon chetida fontanga qaragan 4 ta to'q sariq yog'och skameyka.
Materiallar: `water` — havza suvi (xaritada hovuz/basseyn shaderi bilan, basins.json), `jet` — suv yoylari (pastga oqadi).
Koordinata: model markazi = fontan markazi, +X — sharq, +Y — shimol (config.ts da bearing 180). Havza radiusi 5.2 m.
"""
import json
import math
import sys
from pathlib import Path

import bmesh
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from blender_kit import Kit  # noqa: E402

sys.path.insert(0, str(HERE))
from statue import build_statue  # noqa: E402

PALETTE = {
    'granite': (0.42, 0.2, 0.18), 'granite_l': (0.55, 0.3, 0.27), 'tile': (0.86, 0.86, 0.82), 'water': (0.5, 0.75, 0.8),
    'marble': (0.93, 0.91, 0.86), 'marble_d': (0.82, 0.79, 0.73), 'bronze': (0.45, 0.35, 0.2), 'jet': (0.88, 0.95, 1.0),
    'wood': (0.93, 0.58, 0.12), 'iron': (0.15, 0.15, 0.16),
}
k = Kit(PALETTE, glass=('jet',), glass_alpha=0.75)
p = []

R_OUT, R_TOP, R_IN = 5.2, 4.9, 4.45     # havza: devor tagi, devor tepasi, ichki chet
H_WALL = 0.6                             # devor balandligi
FLOOR, WATER_Z = 0.12, 0.45


def lathe(profile, mat, segs=48):
    """(r, z) profil → aylanma jism (yopiq profil, soat strelkasiga teskari)"""
    bm = bmesh.new()
    rings = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        rings.append([bm.verts.new((r * math.cos(a), r * math.sin(a), z)) for r, z in profile])
    n = len(profile)
    for i in range(segs):
        A, B = rings[i], rings[(i + 1) % segs]
        for j in range(n - 1):
            bm.faces.new([A[j], B[j], B[j + 1], A[j + 1]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return k.obj('lathe', bm, mat)


# ---------- havza ----------
# tashqi qiya devor va ustki keng qirra (yopiq profil: tashqi tag → qirra → ichki devor → tub)
p.append(lathe([(R_IN - 0.01, FLOOR), (R_IN, H_WALL + 0.05), (R_TOP + 0.08, H_WALL + 0.05), (R_TOP + 0.08, H_WALL - 0.02),
                (R_OUT, 0.0), (R_IN - 0.01, 0.0)], 'granite'))
p.append(lathe([(R_IN - 0.02, H_WALL + 0.05), (R_IN - 0.02, H_WALL + 0.09), (R_TOP + 0.1, H_WALL + 0.09),
                (R_TOP + 0.1, H_WALL + 0.05)], 'granite_l'))
p.append(k.cyl(R_IN - 0.02, FLOOR, (0, 0, FLOOR / 2), 'tile', segs=48))
BASIN = [(round((R_IN - 0.03) * math.cos(2 * math.pi * i / 40), 3), round((R_IN - 0.03) * math.sin(2 * math.pi * i / 40), 3))
         for i in range(40)]
p.append(k.cyl(R_IN - 0.03, WATER_Z - FLOOR, (0, 0, (WATER_Z + FLOOR) / 2), 'water', segs=40))

# ---------- markaziy supa va qirrali ustun ----------
p.append(k.cyl(1.15, 0.5, (0, 0, 0.25), 'granite', segs=32))
p.append(k.cyl(0.95, 0.12, (0, 0, 0.56), 'granite_l', segs=32))
# ustun: pastda keng (qo'ng'iroqsimon), qirralari tik bo'rtiqlar
p.append(k.cyl(0.7, 0.25, (0, 0, 0.745), 'marble_d', segs=24, r2=0.55))
COL0, COL1 = 0.87, 2.2
p.append(k.cyl(0.42, COL1 - COL0, (0, 0, (COL0 + COL1) / 2), 'marble', segs=24, r2=0.3))
for i in range(16):
    a = 2 * math.pi * i / 16
    p.append(k.beam((0.43 * math.cos(a), 0.43 * math.sin(a), COL0), (0.31 * math.cos(a), 0.31 * math.sin(a), COL1),
                    0.06, 0.06, 'marble_d'))
p.append(k.cyl(0.48, 0.12, (0, 0, COL1 + 0.06), 'marble', segs=24))
p.append(k.box((0.75, 0.75, 0.15), (0, 0, COL1 + 0.2), 'marble_d'))

# ---------- haykal: boshida savat ko'targan ayol (statue.py) — yuzi sharsharaga teskari, maydonga (janubi-sharq) ----------
p.extend(build_statue(k, COL1 + 0.275, yaw=math.radians(38)))

# ---------- suv yoylari: qirradagi bronza quvurchalardan markazga ----------
def jet_arc(x0, y0, z0, x1, y1, z1, apex, r=0.025, n=10, sides=6):
    """Parabolik suv yoyi (ingichka naycha). UV: v — oqim bo'ylab"""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    rings = []
    L = math.dist((x0, y0), (x1, y1))
    dx, dy = (x1 - x0) / L, (y1 - y0) / L
    for i in range(n + 1):
        t = i / n
        cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        cz = z0 + (z1 - z0) * t + 4 * apex * t * (1 - t)
        rr = r * (1 + 0.8 * t)
        ring = []
        for s in range(sides):
            a = 2 * math.pi * s / sides
            ox, oz = -dy * math.cos(a) * rr, math.sin(a) * rr
            oy = dx * math.cos(a) * rr
            v = bm.verts.new((cx + ox, cy + oy, cz + oz))
            ring.append((v, s, t))
        rings.append(ring)
    for i in range(n):
        for s in range(sides):
            a, b = rings[i][s], rings[i][(s + 1) % sides]
            c, d = rings[i + 1][(s + 1) % sides], rings[i + 1][s]
            f = bm.faces.new([a[0], b[0], c[0], d[0]])
            for loop, (_, sv, tv) in zip(f.loops, (a, b, c, d)):
                loop[uv].uv = (sv / sides * 0.3, tv * L * 1.5)
    return k.obj('jet', bm, 'jet')


NJ = 12
for i in range(NJ):
    a = 2 * math.pi * (i + 0.5) / NJ
    rx, ry = (R_IN + 0.15) * math.cos(a), (R_IN + 0.15) * math.sin(a)
    p.append(k.cyl(0.05, 0.12, (rx, ry, H_WALL + 0.15), 'bronze', segs=8))
    p.append(jet_arc((R_IN - 0.2) * math.cos(a), (R_IN - 0.2) * math.sin(a), H_WALL + 0.2,
                     1.5 * math.cos(a), 1.5 * math.sin(a), WATER_Z, 0.8))
# supa atrofidagi kichik tik oqimlar
for i in range(6):
    a = 2 * math.pi * i / 6
    x, y = 1.6 * math.cos(a), 1.6 * math.sin(a)
    p.append(k.cyl(0.05, 0.1, (x, y, WATER_Z), 'bronze', segs=8))
    p.append(jet_arc(x, y, WATER_Z + 0.05, x * 0.92, y * 0.92, WATER_Z, 0.35, r=0.02, n=6))

# ---------- 4 ta skameyka (maydon chetida, fontanga qaragan) ----------
def bench(ang_deg, r=9.2):
    """Kompas burchagi (0 — shimol, 90 — sharq); skameyka o'rindig'i markazga qaragan"""
    a = math.radians(ang_deg)
    cx, cy = r * math.sin(a), r * math.cos(a)
    rot = (0, 0, -a)          # mahalliy +Y (orqa suyanchiq tomoni) → markazdan tashqariga
    out = []
    M = Matrix.Rotation(-a, 3, 'Z')

    def at(x, y, z):
        v = M @ Vector((x, y, 0))
        return (cx + v.x, cy + v.y, z)
    for j in range(4):  # o'rindiq taxtalari
        out.append(k.box((2.2, 0.1, 0.05), at(0, -0.17 + j * 0.12, 0.45), 'wood', rot))
    for j in range(3):  # suyanchiq taxtalari
        out.append(k.box((2.2, 0.04, 0.1), at(0, 0.25, 0.6 + j * 0.14), 'wood', rot))
    for x in (-0.9, 0.9):  # cho'yan oyoqlar
        out.append(k.box((0.06, 0.5, 0.06), at(x, 0.0, 0.41), 'iron', rot))
        out.append(k.box((0.06, 0.06, 0.42), at(x, -0.2, 0.21), 'iron', rot))
        out.append(k.box((0.06, 0.06, 0.88), at(x, 0.22, 0.44), 'iron', rot))
    return out


BENCHES = (15, 95, 195, 275)
for ang in BENCHES:
    p.extend(bench(ang))

(HERE / 'basins.json').write_text(json.dumps([{'poly': [list(v) for v in BASIN], 'z': WATER_Z}]), encoding='utf8')
k.finish('FONTAN', p, HERE, [
    ('preview.png', (6.0, -22.0, 10.0), (0, 0, 1.2)),
    ('preview_close.png', (3.3, -4.3, 4.0), (0, 0, 3.6)),
])

"""
Baby Car — park bo'ylab aylanib yurish uchun ijaraga beriladigan bolalar elektromashinalari, maysazor chetida yonma-yon
turibdi (rasm: attraction-images-park/Baby_Car.png): sariq sport mashina (ochiq, ikki qora o'rindiq), qizil bagi
(qora rama, katta g'ildiraklar, qizil disklar) va to'q sariq-oq bagi (to'q sariq ramali, oq yon panellar).

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/baby-car/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, tours.json, preview.png

Tuzilish: `base` — to'xtash joyi chiziqlari va "BABY CAR" lavhasi; tour0..tour2 — mashinalar (lokal +X — oldi).
Mashinalar navbat bilan bittadan sayrga chiqadi (anim.tour, tours.json): joyidan oldinga chiqib, yo'lakning o'ng chizig'i
bo'ylab Французская карусель (36) oldigacha boradi, burilib qarama-qarshi chiziqdan qaytadi va joyiga orqasi bilan kiradi.
Yo'l — park.json marshrut grafidagi yo'lak o'rta chizig'i (ROUTE, park koordinatasi) → model koordinatasi (place.ts at, bearing).
Joyida turganda oldi — Blender'da -Y (yo'lakka), qator — X bo'ylab. G'ildiraklar yo'l plitkasi ustida (z = 0.12).
Asl o'lcham: 4.0 × 1.45 m, balandligi 1.4 m.
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'decor'))
from blender_kit import Kit  # noqa: E402
from mathutils import Matrix  # noqa: E402

PALETTE = {
    'yellow': (0.95, 0.65, 0.02), 'red': (0.65, 0.02, 0.02), 'orange': (0.95, 0.25, 0.02), 'white': (0.9, 0.9, 0.9),
    'black': (0.03, 0.03, 0.035), 'seat': (0.05, 0.05, 0.05), 'tyre': (0.02, 0.02, 0.02), 'rim': (0.7, 0.7, 0.72),
    'glass': (0.1, 0.12, 0.15), 'light': (0.9, 0.95, 1.0),
}
k = Kit(PALETTE, glow=('light',))
G = 0.12                    # yo'l plitkasi yuzasi
p = []


def wheels(x, r, w, rim, xs=0.43, ys=(-0.45, 0.45)):
    for wy in ys:
        for sx in (-1, 1):
            p.append(k.cyl(r, w, (x + sx * xs, wy, G + r), 'tyre', segs=14, rot=(0, math.pi / 2, 0)))
            p.append(k.cyl(r * 0.55, w + 0.02, (x + sx * xs, wy, G + r), rim, segs=10, rot=(0, math.pi / 2, 0)))


def seats(x, y, z, col='seat'):
    for sx in (-0.2, 0.2):
        p.append(k.box((0.3, 0.3, 0.08), (x + sx, y, z), col))
        p.append(k.box((0.3, 0.08, 0.42), (x + sx, y + 0.17, z + 0.2), col, rot=(0.2, 0, 0)))


# ---------- 1. sariq sport mashina ----------
n0 = len(p)
X = 0.0
p.append(k.box((0.88, 1.3, 0.28), (X, 0, G + 0.3), 'yellow'))
p.append(k.prism_x([(-0.68, G + 0.3), (-0.3, G + 0.3), (-0.3, G + 0.52), (-0.68, G + 0.4)], X - 0.44, X + 0.44, 'yellow'))   # kapot
p.append(k.box((0.86, 0.35, 0.2), (X, 0.45, G + 0.52), 'yellow'))                              # orqa qism
p.append(k.box((0.9, 0.06, 0.08), (X, -0.68, G + 0.22), 'black'))                              # old bamper
for sx in (-1, 1):
    p.append(k.box((0.14, 0.04, 0.05), (X + sx * 0.3, -0.69, G + 0.38), 'light'))              # faralar
p.append(k.beam((X - 0.38, -0.25, G + 0.5), (X - 0.38, -0.12, G + 0.72), 0.04, 0.04, 'black'))   # old oyna ramkasi
p.append(k.beam((X + 0.38, -0.25, G + 0.5), (X + 0.38, -0.12, G + 0.72), 0.04, 0.04, 'black'))
p.append(k.box((0.76, 0.03, 0.2), (X, -0.19, G + 0.62), 'glass', rot=(0.5, 0, 0)))
seats(X, 0.1, G + 0.48)
p.append(k.cyl(0.1, 0.03, (X - 0.2, -0.08, G + 0.62), 'black', segs=10, rot=(1.0, 0, 0)))     # rul
wheels(X, 0.17, 0.12, 'rim', xs=0.42, ys=(-0.42, 0.42))

car_parts = [p[n0:]]
del p[n0:]

# ---------- 2. qizil bagi ----------
X = 0.0
p.append(k.box((0.7, 1.3, 0.12), (X, 0, G + 0.3), 'black'))                                   # rama
p.append(k.box((0.8, 0.45, 0.3), (X, -0.45, G + 0.48), 'red'))                                 # old kuzov
p.append(k.box((0.82, 0.05, 0.18), (X, -0.68, G + 0.38), 'black'))                             # panjara
for sx in (-1, 1):
    p.append(k.box((0.06, 0.75, 0.28), (X + sx * 0.4, 0.15, G + 0.5), 'red'))                  # yon panellar
    p.append(k.box((0.12, 0.04, 0.05), (X + sx * 0.25, -0.7, G + 0.52), 'light'))
p.append(k.box((0.78, 0.3, 0.25), (X, 0.55, G + 0.5), 'red'))
seats(X, 0.1, G + 0.45)
for sx in (-1, 1):                                                                             # qora himoya ramasi
    p.append(k.beam((X + sx * 0.36, -0.2, G + 0.6), (X + sx * 0.33, -0.05, G + 1.2), 0.05, 0.05, 'black'))
    p.append(k.beam((X + sx * 0.36, 0.45, G + 0.6), (X + sx * 0.33, 0.4, G + 1.2), 0.05, 0.05, 'black'))
    p.append(k.beam((X + sx * 0.33, -0.05, G + 1.2), (X + sx * 0.33, 0.4, G + 1.2), 0.05, 0.05, 'black'))
p.append(k.beam((X - 0.33, -0.05, G + 1.2), (X + 0.33, -0.05, G + 1.2), 0.05, 0.05, 'black'))
p.append(k.beam((X - 0.33, 0.4, G + 1.2), (X + 0.33, 0.4, G + 1.2), 0.05, 0.05, 'black'))
p.append(k.cyl(0.1, 0.03, (X - 0.2, -0.15, G + 0.68), 'black', segs=10, rot=(1.0, 0, 0)))
wheels(X, 0.22, 0.16, 'red', xs=0.43, ys=(-0.45, 0.45))

car_parts.append(p[n0:])
del p[n0:]

# ---------- 3. to'q sariq-oq bagi (Can-Am uslubi) ----------
X = 0.0
p.append(k.box((0.7, 1.3, 0.12), (X, 0, G + 0.3), 'black'))
p.append(k.box((0.8, 0.45, 0.28), (X, -0.45, G + 0.47), 'orange'))
p.append(k.box((0.6, 0.06, 0.16), (X, -0.69, G + 0.4), 'black'))
for sx in (-1, 1):
    p.append(k.box((0.06, 0.75, 0.3), (X + sx * 0.4, 0.15, G + 0.5), 'white'))
    p.append(k.box((0.07, 0.3, 0.12), (X + sx * 0.4, -0.05, G + 0.45), 'orange'))
    p.append(k.box((0.12, 0.04, 0.05), (X + sx * 0.25, -0.7, G + 0.52), 'light'))
p.append(k.box((0.78, 0.3, 0.22), (X, 0.55, G + 0.48), 'orange'))
seats(X, 0.1, G + 0.45)
for sx in (-0.2, 0.2):
    p.append(k.box((0.22, 0.05, 0.18), (X + sx, 0.24, G + 0.82), 'orange', rot=(0.2, 0, 0)))   # o'rindiq bezagi
for sx in (-1, 1):                                                                             # to'q sariq egri rama
    pts = [(X + sx * 0.38, -0.45, G + 0.62), (X + sx * 0.34, -0.1, G + 1.15), (X + sx * 0.3, 0.3, G + 1.25), (X + sx * 0.36, 0.6, G + 0.7)]
    for a, b in zip(pts, pts[1:]):
        p.append(k.beam(a, b, 0.06, 0.06, 'orange'))
p.append(k.beam((X - 0.34, -0.1, G + 1.15), (X + 0.34, -0.1, G + 1.15), 0.06, 0.06, 'orange'))
p.append(k.beam((X - 0.3, 0.3, G + 1.25), (X + 0.3, 0.3, G + 1.25), 0.06, 0.06, 'orange'))
p.append(k.cyl(0.1, 0.03, (X - 0.2, -0.15, G + 0.68), 'black', segs=10, rot=(1.0, 0, 0)))
wheels(X, 0.22, 0.16, 'orange', xs=0.43, ys=(-0.45, 0.45))

car_parts.append(p[n0:])
del p[n0:]

# ====================== to'xtash joyi: oq chiziqlar va "BABY CAR" lavhasi (base) ======================
SLOTS = [-1.5, 0.0, 1.5]                # mashinalar joyi (X), qator — maysazor cheti bo'ylab
for x in (-2.25, -0.75, 0.75, 2.25):
    p.append(k.box((0.07, 1.6, 0.012), (x, 0.0, G + 0.006), 'white'))
p.append(k.cyl(0.04, 1.7, (2.15, 0.55, G + 0.85), 'rim', segs=8))
p.append(k.box((0.7, 0.05, 0.42), (2.15, 0.52, G + 1.6), 'yellow'))
p.append(k.text('BABY CAR', 0.11, (2.15, 0.49, G + 1.6), 'black', face='-Y', depth=0.02))


# ====================== mashinalar — alohida tugunlar tour0..2 (lokal +X — oldi) ======================
cars = []
for i, parts in enumerate(car_parts):
    ob = k.join(f'tour{i}', parts)
    ob.data.transform(Matrix.Rotation(math.pi / 2, 4, 'Z'))        # oldi -Y → +X (GltfModel: mashina +X ga qaragan)
    ob.location = (SLOTS[i], 0, 0)                                  # preview uchun joyida (xaritada kod joylaydi)
    ob.rotation_euler = (0, 0, -math.pi / 2)
    cars.append(ob)

# ====================== sayr yo'llari (park koordinatasidan model koordinatasiga) ======================
AT, BEAR = (-44.2, 80.0), 41.8          # place.ts dagi at, bearing
EX = (math.sin(math.radians(BEAR - 90)), math.cos(math.radians(BEAR - 90)))   # model +X
EY = (math.sin(math.radians(BEAR + 180)), math.cos(math.radians(BEAR + 180)))  # model +Y (orqa)


def to_local(pt):
    dx, dy = pt[0] - AT[0], pt[1] - AT[1]
    return (dx * EX[0] + dy * EX[1], dx * EY[0] + dy * EY[1])


# Yo'lak o'rta chizig'i (park.json marshrut grafi): Baby Car → uychalar oldidagi yo'lak → Французская карусель (36) oldi
ROUTE = [(-46.34, 87.17), (-36.74, 78.59), (-31.5, 77.86), (-25.31, 70.47), (-26.27, 65.81), (-23.76, 61.72), (-19.04, 59.29),
         (-18.08, 56.82), (-12.07, 53.66), (-7.39, 49.88), (-0.74, 42.96), (0.62, 40.59), (1.06, 39.6), (1.41, 38.55),
         (1.66, 37.44), (2.05, 34.55), (6.47, 32.33), (7.31, 32.34), (10.16, 30.66), (11.19, 29.92), (12.13, 29.13),
         (12.97, 28.28), (14.81, 26.0), (16.87, 24.77), (17.85, 24.02), (20.3, 21.75), (23.96, 17.96)]
LANE = 1.0                              # yo'lak o'rtasidan har bir chiziqqa, m (o'ng tomondan yuriladi)


def chaikin(pts, it=3):
    for _ in range(it):
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            out += [(a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25), (a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75)]
        out.append(pts[-1])
        pts = out
    return pts


center = chaikin([to_local(q) for q in ROUTE], 3)


def offset(pts, d):
    """Harakat yo'nalishiga nisbatan o'ngga d m (manfiy — chapga)"""
    out = []
    for i, q in enumerate(pts):
        a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        out.append((q[0] + dy / ln * d, q[1] - dx / ln * d))
    return out


out_lane = offset(center, LANE)                                     # borish (o'ng chiziq)
ret_lane = offset(center, -LANE)[::-1]                              # qaytish (qarama-qarshi chiziq)
# oxirida burilish: oxirgi nuqta atrofida yarim aylana (o'ng chiziqdan chap chiziqqa, oldinga qarab)
E = center[-1]
fx, fy = center[-1][0] - center[-2][0], center[-1][1] - center[-2][1]
fl = math.hypot(fx, fy)
fx, fy = fx / fl, fy / fl
uturn = []
for j in range(1, 8):
    a = math.pi * j / 8                                             # 0 — o'ng, π/2 — oldinda, π — chap
    rx, ry = fy, -fx                                                # o'ng normal
    uturn.append((E[0] + (rx * math.cos(a) + fx * math.sin(a)) * LANE * 1.6, E[1] + (ry * math.cos(a) + fy * math.sin(a)) * LANE * 1.6))


def seg_len(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


tours = []
for i, xi in enumerate(SLOTS):
    j0 = next(j for j, q in enumerate(out_lane) if q[0] < xi - 2.8)
    k1 = next(j for j, q in enumerate(ret_lane) if j > len(ret_lane) // 2 and q[0] > xi + 2.6)
    fwd = [(xi, 0.0), (xi, -0.9), (xi, -1.7)] + out_lane[j0:] + uturn + ret_lane[:k1 + 1]
    fwd = [fwd[0], fwd[1]] + chaikin(fwd[1:], 2)
    qx, qy = fwd[-1]
    rev = chaikin([(qx, qy), (xi + 1.3, (qy - 1.6) / 2), (xi + 0.25, -1.7), (xi, -0.9), (xi, 0.0)], 2)
    path = fwd + rev[1:]
    tours.append({'name': cars[i].name, 'back': round(seg_len(fwd), 2),
                  'points': [[round(x, 2), 0.0, round(-y, 2)] for x, y in path]})
    print(f'BABY-CAR tour{i}: {seg_len(path):.0f} m (orqaga {seg_len(rev):.1f} m)')
(HERE / 'tours.json').write_text(json.dumps(tours, separators=(',', ':')))

k.finish('BABY-CAR', p, HERE, [('preview.png', (2.6, -4.2, 2.2), (0, 0, 0.5))])

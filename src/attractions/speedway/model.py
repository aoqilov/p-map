"""
Speedway — bolalar jiplari oval yo'lda aylanadi (rasm: attraction-images-park/Speedway.png): 12 qirrali kulrang supa,
chetida tilla rang panjara (ustunlar ustida sharchalar, oldida kirish), supada oval yo'l (relslar), o'rtada boshqaruv qutisi,
yo'lda 6 ta jip (yashil, qizil, ko'k, to'q sariq, sariq, ko'k) — ochiq kuzov, qora g'ildiraklar, ustida himoya ramasi.

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/speedway/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, track.json, preview.png

Tuzilish: `base` — supa, panjara, yo'l, quti; car0..car5 — jiplar (lokal +X — oldi), track.json dagi oval bo'ylab yuradi
(GltfModel → anim.follow). Old tomoni (kirish) — Blender'da -Y. Asl o'lcham: diametri 9.6 m, balandligi ~1.45 m.
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'decor'))
from blender_kit import Kit  # noqa: E402

PALETTE = {
    'deck': (0.42, 0.43, 0.45), 'deck_d': (0.3, 0.31, 0.33), 'rail': (0.18, 0.19, 0.2), 'gold': (0.62, 0.42, 0.14),
    'box': (0.6, 0.62, 0.64), 'tyre': (0.03, 0.03, 0.03), 'rim': (0.75, 0.75, 0.75), 'black': (0.05, 0.05, 0.05),
    'green': (0.25, 0.7, 0.05), 'red': (0.7, 0.03, 0.03), 'blue': (0.03, 0.3, 0.8), 'orange': (0.85, 0.2, 0.02),
    'yellow': (0.9, 0.6, 0.02), 'seat': (0.08, 0.08, 0.09),
}
k = Kit(PALETTE)
p = []

R = 4.8                     # supa (12 qirrali) tashqi radiusi
DECK_Z = 0.35               # supa usti (yo'l plitkasi 0.12 dan baland)
N_SIDE = 12
FENCE_H = 1.0
GATE = 0                    # kirish — old (-Y) qirrada


def ngon(r, n=N_SIDE, rot=math.pi / N_SIDE):
    return [(r * math.cos(rot + 2 * math.pi * i / n - math.pi / 2), r * math.sin(rot + 2 * math.pi * i / n - math.pi / 2)) for i in range(n)]


def prism(pts, z0, z1, mat):
    import bmesh
    bm = bmesh.new()
    bot = [bm.verts.new((x, y, z0)) for x, y in pts]
    top = [bm.verts.new((x, y, z1)) for x, y in pts]
    bm.faces.new(top)
    bm.faces.new(bot[::-1])
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new([bot[i], bot[j], top[j], top[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return k.obj('prism', bm, mat)


# ---------- supa: ikki pog'onali 12 qirrali ----------
p.append(prism(ngon(R), 0, DECK_Z - 0.08, 'deck_d'))
p.append(prism(ngon(R - 0.25), DECK_Z - 0.08, DECK_Z, 'deck'))

# ---------- oval yo'l (stadion shakli): relslar va o'rtadagi quti ----------
SA, RA = 1.2, 1.65          # to'g'ri qism yarim uzunligi (X), yarim aylana radiusi


def stadium(r, n=14):
    pts = []
    for i in range(n + 1):                                          # o'ng yarim aylana (+X), pastdan tepaga
        a = -math.pi / 2 + math.pi * i / n
        pts.append((SA + r * math.cos(a), r * math.sin(a)))
    for i in range(n + 1):                                          # chap yarim aylana
        a = math.pi / 2 + math.pi * i / n
        pts.append((-SA + r * math.cos(a), r * math.sin(a)))
    return pts


for rr in (RA - 0.35, RA + 0.35):                                   # ikki rels (yo'lning ikki cheti)
    ring = stadium(rr)
    for a, b in zip(ring, ring[1:] + ring[:1]):
        if math.dist(a, b) < 1e-3:
            continue
        p.append(k.beam((a[0], a[1], DECK_Z + 0.01), (b[0], b[1], DECK_Z + 0.01), 0.07, 0.03, 'rail'))
p.append(k.box((0.8, 0.8, 0.55), (0, 0, DECK_Z + 0.275), 'box'))
p.append(k.box((0.6, 0.6, 0.02), (0, 0, DECK_Z + 0.56), 'deck_d'))

# ---------- tilla rang panjara (kirish oldida ochiq) ----------
corners = ngon(R - 0.15)
for i in range(N_SIDE):
    a, b = corners[i], corners[(i + 1) % N_SIDE]
    p.append(k.cyl(0.05, FENCE_H + 0.1, (a[0], a[1], DECK_Z + (FENCE_H + 0.1) / 2), 'gold', segs=8))
    p.append(k.ball(0.08, (a[0], a[1], DECK_Z + FENCE_H + 0.15), 'gold', sub=1))
    if i == GATE:
        continue
    for z in (DECK_Z + 0.12, DECK_Z + FENCE_H - 0.04):
        p.append(k.beam((a[0], a[1], z), (b[0], b[1], z), 0.04, 0.04, 'gold'))
    for j in range(1, 7):
        t = j / 7
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        p.append(k.box((0.022, 0.022, FENCE_H - 0.16), (x, y, DECK_Z + 0.12 + (FENCE_H - 0.16) / 2), 'gold'))


# ---------- jiplar (har biri alohida obyekt, lokal +X — oldi) ----------
def jeep(col):
    q = []
    q.append(k.box((1.5, 0.82, 0.32), (0, 0, 0.42), col))                     # kuzov pasti
    q.append(k.box((0.5, 0.8, 0.2), (0.5, 0, 0.66), col))                      # kapot
    q.append(k.box((0.06, 0.82, 0.3), (-0.73, 0, 0.71), col))                  # orqa bort
    for sy in (-1, 1):
        q.append(k.box((1.0, 0.06, 0.26), (-0.2, sy * 0.38, 0.69), col))       # yon bortlar
        q.append(k.box((0.34, 0.12, 0.08), (0.52, sy * 0.44, 0.55), 'black'))  # qanot (old)
    q.append(k.box((0.05, 0.7, 0.18), (0.76, 0, 0.5), 'black'))                # panjara (grille)
    q.append(k.box((0.06, 0.86, 0.1), (0.78, 0, 0.3), 'black'))                # bamper
    q.append(k.box((0.06, 0.86, 0.1), (-0.78, 0, 0.3), 'black'))
    for sx in (-0.15, -0.5):                                                   # o'rindiqlar
        q.append(k.box((0.28, 0.6, 0.12), (sx, 0, 0.62), 'seat'))
        q.append(k.box((0.08, 0.6, 0.3), (sx - 0.14, 0, 0.78), 'seat'))
    # himoya ramasi (roll bar) va old oyna ramkasi
    for sy in (-1, 1):
        q.append(k.beam((-0.35, sy * 0.36, 0.8), (-0.35, sy * 0.36, 1.12), 0.04, 0.04, 'black'))
        q.append(k.beam((0.25, sy * 0.36, 0.76), (0.18, sy * 0.36, 1.02), 0.04, 0.04, 'black'))
    q.append(k.beam((-0.35, -0.36, 1.12), (-0.35, 0.36, 1.12), 0.04, 0.04, 'black'))
    q.append(k.beam((0.18, -0.36, 1.02), (0.18, 0.36, 1.02), 0.04, 0.04, 'black'))
    q.append(k.cyl(0.12, 0.03, (0.12, 0, 0.86), 'black', segs=10, rot=(0, -0.9, 0)))   # rul
    # g'ildiraklar
    for wx in (0.5, -0.48):
        for sy in (-1, 1):
            q.append(k.cyl(0.22, 0.18, (wx, sy * 0.44, 0.22), 'tyre', segs=12, rot=(math.pi / 2, 0, 0)))
            q.append(k.cyl(0.12, 0.19, (wx, sy * 0.44, 0.22), 'rim', segs=8, rot=(math.pi / 2, 0, 0)))
    return q


COLORS = ['green', 'red', 'blue', 'orange', 'yellow', 'blue']
cars = []
for i, col in enumerate(COLORS):
    parts = jeep(col)
    for o in parts:
        o.location.z += DECK_Z
    cars.append(k.join(f'car{i}', parts))

# ---------- trassa: stadion o'rta chizig'i (soat strelkasiga teskari) ----------
track = stadium(RA, n=24)
clean = [track[0]]
for pt in track[1:]:
    if math.dist(pt, clean[-1]) > 1e-3:
        clean.append(pt)
if math.dist(clean[0], clean[-1]) < 1e-3:
    clean.pop()
L_track = sum(math.dist(a, b) for a, b in zip(clean, clean[1:] + clean[:1]))
spacing = L_track / len(cars)
cum = [0.0]
for a, b in zip(clean, clean[1:] + clean[:1]):
    cum.append(cum[-1] + math.dist(a, b))
for i, c in enumerate(cars):                                            # preview uchun yo'lga qo'yish
    s = (L_track - i * spacing) % L_track
    j = max(m for m in range(len(clean)) if cum[m] <= s)
    a, b = clean[j], clean[(j + 1) % len(clean)]
    c.location = (a[0], a[1], 0)
    c.rotation_euler = (0, 0, math.atan2(b[1] - a[1], b[0] - a[0]))
(HERE / 'track.json').write_text(json.dumps({
    'closed': True,
    'points': [[round(x, 3), round(DECK_Z, 3), round(-y, 3)] for x, y in clean],
    'cars': [{'name': c.name, 'offset': round(i * spacing, 3)} for i, c in enumerate(cars)],
    'station': 0,
}, separators=(',', ':')))
print(f'SPEEDWAY track={L_track:.1f}m spacing={spacing:.2f}m')

k.finish('SPEEDWAY', p, HERE, [('preview.png', (6.0, -10.0, 6.5), (0, 0, 0.5))])

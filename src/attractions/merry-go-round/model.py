"""
Merry Go Round — tilla rang otli karusel (rasm: attraction-images-park/Merry_Go_Round.png): 10 qirrali kulrang supa va
tilla rang panjara (oldida kirish), aylanadigan yog'och-tilla supa, o'rtada guldon shaklidagi tilla ustun, tepasida
tilla toj (gajak ravoqlar, orasida rangli manzara panellari, chiroqchalar), uchida shpil va qizil uchlik; burama kumush
ustunlarda 12 ta ot (jigarrang, qora-oq, to'q sariq, yollari sariq/oq).

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/merry-go-round/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png

Tuzilish: `base` — supa va panjara; `rotor` — aylanadigan qism (supa, ustun, toj, ustunchalar);
lift0..2 — otlar (rotor bolalari), uch guruh navbat bilan ko'tarilib-tushadi (anim.lift).
Old tomoni (kirish) — Blender'da -Y. Asl o'lcham: diametri 8.4 m, balandligi ~5.3 m.
"""
import math
import sys
from pathlib import Path

import bmesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'decor'))
from blender_kit import Kit  # noqa: E402

PALETTE = {
    'deck': (0.5, 0.5, 0.52), 'deck_d': (0.35, 0.35, 0.37), 'gold': (0.66, 0.45, 0.12), 'gold_l': (0.8, 0.6, 0.2),
    'wood': (0.45, 0.25, 0.08), 'pole': (0.7, 0.7, 0.72), 'sky': (0.1, 0.4, 0.75), 'leaf': (0.12, 0.42, 0.15),
    'bulb': (1.0, 0.92, 0.7), 'red': (0.6, 0.08, 0.04), 'teal': (0.05, 0.5, 0.45),
    'brown': (0.5, 0.18, 0.04), 'black': (0.03, 0.03, 0.03), 'orange': (0.85, 0.32, 0.04), 'white': (0.85, 0.85, 0.85),
    'mane_y': (0.95, 0.7, 0.1), 'saddle': (0.08, 0.04, 0.03), 'saddle_r': (0.6, 0.04, 0.04),
}
k = Kit(PALETTE, glow=('bulb',))

R_BASE = 4.2                # tashqi supa / panjara radiusi
BASE_Z = 0.25
R_ROT = 3.3                 # aylanadigan supa radiusi
ROT_Z = BASE_Z + 0.25
CAN_Z = 3.7                 # toj pasti
R_CAN = 3.6
R_POLE = 2.6                # ot ustunlari doirasi


def prism(pts, z0, z1, mat):
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


def ngon(r, n, rot=0.0):
    return [(r * math.cos(rot + 2 * math.pi * i / n - math.pi / 2), r * math.sin(rot + 2 * math.pi * i / n - math.pi / 2)) for i in range(n)]


# ====================== base: supa va panjara ======================
base = [prism(ngon(R_BASE, 10, math.pi / 10), 0, BASE_Z, 'deck'), prism(ngon(R_BASE + 0.08, 10, math.pi / 10), 0, 0.06, 'deck_d')]
corners = ngon(R_BASE - 0.12, 10, math.pi / 10)
for i in range(10):
    a, b = corners[i], corners[(i + 1) % 10]
    base.append(k.box((0.09, 0.09, 1.05), (a[0], a[1], BASE_Z + 0.52), 'gold'))
    base.append(k.ball(0.07, (a[0], a[1], BASE_Z + 1.1), 'gold', sub=1))
    if i == 0:                                                      # kirish (old tomonda)
        continue
    for z in (BASE_Z + 0.1, BASE_Z + 0.98):
        base.append(k.beam((a[0], a[1], z), (b[0], b[1], z), 0.04, 0.04, 'gold'))
    for j in range(1, 8):
        t = j / 8
        base.append(k.box((0.025, 0.025, 0.86), (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, BASE_Z + 0.54), 'gold'))

# ====================== rotor ======================
rot = []
rot.append(k.cyl(R_ROT, 0.25, (0, 0, BASE_Z + 0.125), 'wood', segs=32))
rot.append(k.cyl(R_ROT + 0.05, 0.06, (0, 0, BASE_Z + 0.03), 'gold', segs=32))
# markaziy ustun: guldon shakli (pastda keng, o'rtada ingichka, tepada kengayadi)
rot.append(k.cyl(0.95, 0.4, (0, 0, ROT_Z + 0.2), 'gold', segs=12, r2=0.75))
rot.append(k.cyl(0.75, 1.3, (0, 0, ROT_Z + 1.05), 'gold_l', segs=12, r2=0.55))
rot.append(k.cyl(0.55, 1.2, (0, 0, ROT_Z + 2.3), 'gold', segs=12, r2=1.0))
for i in range(12):                                                 # ustundagi naqsh (tik bo'rtiqlar)
    a = 2 * math.pi * i / 12
    rot.append(k.beam((0.74 * math.cos(a), 0.74 * math.sin(a), ROT_Z + 0.45), (0.56 * math.cos(a), 0.56 * math.sin(a), ROT_Z + 1.7), 0.06, 0.05, 'gold'))
    rot.append(k.ball(0.09, (0.68 * math.cos(a), 0.68 * math.sin(a), ROT_Z + 1.2), 'teal', sub=1))
# toj: pastki halqa, rangli panellar, gajak ravoqlar
rot.append(k.cyl(R_CAN, 0.18, (0, 0, CAN_Z), 'gold', segs=24))
rot.append(k.cyl(R_CAN - 0.1, 0.06, (0, 0, CAN_Z - 0.12), 'gold_l', segs=24))
N_P = 8
for i in range(N_P):
    a0, a1 = 2 * math.pi * i / N_P, 2 * math.pi * (i + 1) / N_P
    am = (a0 + a1) / 2
    x0, y0 = R_CAN * math.cos(a0), R_CAN * math.sin(a0)
    x1, y1 = R_CAN * math.cos(a1), R_CAN * math.sin(a1)
    xm, ym = (R_CAN - 0.05) * math.cos(am), (R_CAN - 0.05) * math.sin(am)
    ang = am + math.pi / 2
    w = math.dist((x0, y0), (x1, y1))
    rot.append(k.box((w * 0.8, 0.06, 0.55), (xm, ym, CAN_Z + 0.42), 'sky' if i % 2 else 'leaf', rot=(0, 0, ang)))   # manzara
    rot.append(k.box((w * 0.5, 0.07, 0.2), (xm, ym, CAN_Z + 0.32), 'leaf' if i % 2 else 'sky', rot=(0, 0, ang)))
    # gajak ravoq (panel ustida yoy) va burchakdagi baland gajak
    for t in range(6):
        ta, tb = t / 6, (t + 1) / 6
        za = CAN_Z + 0.75 + 0.25 * math.sin(math.pi * ta)
        zb = CAN_Z + 0.75 + 0.25 * math.sin(math.pi * tb)
        pa = (R_CAN * math.cos(a0 + (a1 - a0) * ta), R_CAN * math.sin(a0 + (a1 - a0) * ta))
        pb = (R_CAN * math.cos(a0 + (a1 - a0) * tb), R_CAN * math.sin(a0 + (a1 - a0) * tb))
        rot.append(k.beam((pa[0], pa[1], za), (pb[0], pb[1], zb), 0.12, 0.1, 'gold'))
    rot.append(k.beam((x0, y0, CAN_Z + 0.08), (x0, y0, CAN_Z + 1.25), 0.2, 0.16, 'gold_l'))
    rot.append(k.ball(0.13, (x0 * 1.01, y0 * 1.01, CAN_Z + 1.1), 'teal', sub=1))
    rot.append(k.beam((x0, y0, CAN_Z + 0.08), (x1, y1, CAN_Z + 0.08), 0.1, 0.1, 'gold'))
    for t in range(1, 5):                                           # chiroqchalar
        bx, by = x0 + (x1 - x0) * t / 5, y0 + (y1 - y0) * t / 5
        rot.append(k.ball(0.05, (bx * 1.02, by * 1.02, CAN_Z + 0.08), 'bulb', sub=1))
# tom: konus va shpil
rot.append(k.cyl(R_CAN - 0.2, 1.1, (0, 0, CAN_Z + 0.6), 'gold_l', segs=16, r2=0.5))
rot.append(k.cyl(0.5, 0.4, (0, 0, CAN_Z + 1.35), 'gold', segs=12, r2=0.06))
rot.append(k.cyl(0.08, 0.5, (0, 0, CAN_Z + 1.75), 'gold', segs=8))
rot.append(k.ball(0.14, (0, 0, CAN_Z + 2.05), 'red', sub=1))
# ot ustunlari (burama kumush) — supadan tojgacha
N_H = 12
for i in range(N_H):
    a = 2 * math.pi * (i + 0.5) / N_H
    x, y = R_POLE * math.cos(a), R_POLE * math.sin(a)
    rot.append(k.cyl(0.035, CAN_Z - ROT_Z, (x, y, (ROT_Z + CAN_Z) / 2), 'pole', segs=6))
rotor = k.join('rotor', rot)


# ====================== otlar (lift0..2, rotor bolalari) ======================
def horse(x, y, yaw, body, mane):
    """Ot: aylana bo'ylab yugurayotgan holda (boshi harakat yo'nalishida). Lokal: +X — oldi"""
    q = []
    q.append(k.ball(0.32, (0, 0, 1.05), body, sub=2, scale=(1.55, 0.7, 0.75)))          # tana
    q.append(k.beam((0.38, 0, 1.12), (0.6, 0, 1.5), 0.2, 0.17, body))                     # bo'yin
    q.append(k.ball(0.14, (0.72, 0, 1.52), body, sub=1, scale=(1.6, 0.8, 0.85)))         # bosh
    q.append(k.beam((0.4, 0, 1.3), (0.6, 0, 1.68), 0.06, 0.08, mane))                     # yol
    q.append(k.beam((-0.48, 0, 1.12), (-0.68, 0, 0.75), 0.07, 0.1, mane))                 # dum
    q.append(k.box((0.36, 0.42, 0.06), (-0.02, 0, 1.3), 'saddle'))                        # egar
    q.append(k.box((0.3, 0.44, 0.03), (-0.02, 0, 1.25), 'saddle_r'))
    for lx, ang in ((0.32, -0.6), (0.3, 0.2), (-0.32, 0.6), (-0.3, -0.25)):              # oyoqlar (yugurish)
        for sy in (-1, 1):
            if (sy > 0) == (ang > 0):
                continue
        for sy in (-0.12, 0.12):
            q.append(k.beam((lx, sy, 0.95), (lx + 0.45 * math.sin(ang), sy, 0.95 - 0.45 * math.cos(ang)), 0.07, 0.07, body))
    ob = k.join('h', q)
    ob.rotation_euler = (0, 0, yaw)
    ob.location = (x, y, ROT_Z - 0.35)
    return ob


STYLES = [('brown', 'mane_y'), ('black', 'white'), ('orange', 'mane_y'), ('white', 'black')]
groups = [[], [], []]
for i in range(N_H):
    a = 2 * math.pi * (i + 0.5) / N_H
    body, mane = STYLES[i % len(STYLES)]
    yaw = a + math.pi / 2                                           # soat strelkasiga teskari aylanish yo'nalishida
    groups[i % 3].append(horse(R_POLE * math.cos(a), R_POLE * math.sin(a), yaw, body, mane))
for g, objs in enumerate(groups):
    lf = k.join(f'lift{g}', objs)
    lf.parent = rotor

k.finish('MERRY-GO-ROUND', base, HERE, [('preview.png', (6.0, -10.5, 5.0), (0, 0, 2.2))])

"""
Kiddie Rides — tanga bilan ishlaydigan 6 ta bolalar mashinasi bir qatorda (rasmlar: attraction-images-park/payloader.png,
Screenshot_1.png): Smurf samolyoti (sariq, propeller, ko'k Smurf oq qalpoqda), Hello Kitty mashinasi (pushti, oq g'ildirak),
ekskavator, yuklagich (old cho'mich), yo'l katogi (kumush baraban), samosval — hammasi sariq "ZAP" texnikasi.
Har biri yashil gulli tagkursida turadi, ostida umumiy rezina maydoncha.

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/kiddie-rides/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png

Tuzilish: `base` — maydoncha va tagkursilar; swing0..swing5 — mashinalar (origin — tagkursi ustida, o'q — model X):
oldinga-orqaga tebranadi (anim.swing). Mashinalar oldi — Blender'da -Y (yo'lakka). Qator — X bo'ylab.
Asl o'lcham: 9.1 × 2.9 m, balandligi ~1.75 m.
"""
import math
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'decor'))
from blender_kit import Kit  # noqa: E402

PALETTE = {
    'mat': (0.1, 0.35, 0.12), 'mat_e': (0.6, 0.06, 0.04), 'grass': (0.15, 0.55, 0.08), 'grass_d': (0.08, 0.35, 0.05),
    'flower_r': (0.75, 0.05, 0.04), 'flower_w': (0.9, 0.9, 0.88), 'yellow': (0.92, 0.6, 0.02), 'yellow_d': (0.7, 0.42, 0.01),
    'white': (0.9, 0.9, 0.9), 'smurf': (0.1, 0.45, 0.85), 'black': (0.03, 0.03, 0.03), 'purple': (0.15, 0.05, 0.35),
    'pink': (0.95, 0.35, 0.55), 'pink_d': (0.8, 0.05, 0.3), 'glass': (0.45, 0.7, 0.9), 'steel': (0.65, 0.66, 0.68),
    'red': (0.75, 0.05, 0.04), 'nose': (0.95, 0.75, 0.1),
}
k = Kit(PALETTE)

N, PITCH = 6, 1.5
MAT_W, MAT_D, MAT_Z = 9.0, 2.8, 0.18          # maydoncha (yo'l plitkasi 0.12 dan baland)
PED_H = 0.32                                    # tagkursi balandligi (maydoncha ustidan)
PIV = MAT_Z + PED_H                             # tebranish o'qi balandligi

base = [k.box((MAT_W, MAT_D, MAT_Z), (0, 0, MAT_Z / 2), 'mat'),
        k.box((MAT_W + 0.1, MAT_D + 0.1, 0.06), (0, 0, 0.03), 'mat_e')]


def pedestal(x):
    q = [k.box((0.95, 1.55, 0.08), (x, 0, MAT_Z + 0.04), 'grass_d'),
         k.cyl(0.42, PED_H - 0.08, (x, 0, MAT_Z + 0.08 + (PED_H - 0.08) / 2), 'grass', segs=4, rot=(0, 0, math.pi / 4), r2=0.3)]
    for fx, fy, col in ((-0.25, -0.38, 'flower_r'), (0.2, -0.4, 'flower_w'), (0.36, 0.1, 'flower_r'), (-0.36, 0.15, 'flower_w')):
        q.append(k.ball(0.05, (x + fx, fy, MAT_Z + 0.2), col, sub=1))
    return q


# ---------- mashinalar: lokal koordinata, (0, 0, 0) — tebranish o'qi (tagkursi usti), oldi — -Y ----------
def wheel(x, y, z, r, w, tyre='black', hub='yellow'):
    return [k.cyl(r, w, (x, y, z), tyre, segs=12, rot=(0, math.pi / 2, 0)),
            k.cyl(r * 0.55, w + 0.02, (x, y, z), hub, segs=8, rot=(0, math.pi / 2, 0))]


def smurf_plane():
    q = [k.cyl(0.26, 1.2, (0, 0, 0.42), 'yellow', segs=12, rot=(math.pi / 2, 0, 0)),
         k.cyl(0.26, 0.2, (0, -0.68, 0.42), 'white', segs=12, rot=(math.pi / 2, 0, 0), r2=0.18),
         k.box((1.25, 0.3, 0.05), (0, -0.25, 0.4), 'yellow_d'),                       # qanotlar
         k.box((0.6, 0.18, 0.04), (0, 0.55, 0.5), 'yellow_d'),                        # dum
         k.box((0.05, 0.22, 0.3), (0, 0.58, 0.65), 'yellow'),
         k.box((0.06, 0.42, 0.3), (0.28, -0.05, 0.5), 'white'),                       # bulut yozuv (yonida)
         k.box((0.06, 0.42, 0.3), (-0.28, -0.05, 0.5), 'white'),
         k.box((0.04, 0.3, 0.12), (0.31, -0.05, 0.5), 'smurf'), k.box((0.04, 0.3, 0.12), (-0.31, -0.05, 0.5), 'smurf'),
         k.box((0.32, 0.25, 0.18), (0, -0.25, 0.7), 'yellow'),                        # kabina
         k.cyl(0.06, 0.05, (0, -0.83, 0.42), 'steel', segs=8, rot=(math.pi / 2, 0, 0))]
    for a in (0, math.pi / 2):                                                         # propeller
        q.append(k.box((0.04, 0.02, 0.5), (0, -0.86, 0.42), 'yellow_d', rot=(0, a, 0)))
    # Smurf: ko'k bosh, oq qalpoq, tana
    q += [k.ball(0.13, (0, 0.2, 0.78), 'smurf', sub=1, scale=(1, 0.9, 1.1)), k.ball(0.15, (0, 0.18, 1.02), 'smurf', sub=2),
          k.cyl(0.14, 0.24, (0, 0.2, 1.18), 'white', segs=10, r2=0.03), k.ball(0.06, (0, 0.06, 1.0), 'smurf', sub=1)]
    return q


def kitty_car():
    q = [k.box((0.7, 1.4, 0.3), (0, 0, 0.35), 'pink'), k.box((0.66, 0.5, 0.18), (0, -0.42, 0.56), 'pink_d'),
         k.box((0.6, 0.06, 0.22), (0, -0.16, 0.72), 'glass'), k.box((0.72, 0.08, 0.1), (0, -0.72, 0.3), 'steel'),
         k.box((0.72, 0.08, 0.1), (0, 0.72, 0.3), 'steel'), k.box((0.6, 0.4, 0.2), (0, 0.45, 0.58), 'pink_d')]
    for wy in (-0.45, 0.45):
        for sx in (-1, 1):
            q += wheel(sx * 0.36, wy, 0.2, 0.18, 0.12, tyre='white', hub='pink_d')
    # Hello Kitty: oq bosh (keng), pushti bant, pushti tana
    q += [k.ball(0.14, (0, 0.18, 0.72), 'pink', sub=1, scale=(1, 0.8, 1.1)), k.ball(0.18, (0, 0.16, 1.0), 'white', sub=2, scale=(1.3, 1, 0.95)),
          k.cyl(0.05, 0.08, (-0.15, 0.16, 1.15), 'white', segs=4, r2=0.0), k.cyl(0.05, 0.08, (0.15, 0.16, 1.15), 'white', segs=4, r2=0.0),
          k.ball(0.07, (0.14, 0.1, 1.14), 'pink_d', sub=1, scale=(1.4, 0.6, 1)), k.ball(0.03, (0, -0.02, 0.98), 'nose', sub=1)]
    return q


def excavator():
    q = []
    for sx in (-1, 1):                                                                 # gusenitsalar
        q.append(k.box((0.18, 1.1, 0.24), (sx * 0.28, 0, 0.12), 'purple'))
        for wy in (-0.4, 0, 0.4):
            q.append(k.cyl(0.08, 0.2, (sx * 0.28, wy, 0.12), 'yellow', segs=8, rot=(0, math.pi / 2, 0)))
    q += [k.box((0.7, 0.9, 0.22), (0, 0.05, 0.36), 'yellow'), k.box((0.55, 0.5, 0.55), (0.05, 0.2, 0.75), 'yellow'),
          k.box((0.45, 0.04, 0.38), (0.05, -0.06, 0.78), 'glass'), k.box((0.6, 0.55, 0.05), (0.05, 0.2, 1.05), 'yellow_d'),
          k.beam((-0.22, -0.1, 0.55), (-0.22, -0.6, 0.95), 0.12, 0.12, 'yellow'), k.beam((-0.22, -0.6, 0.95), (-0.22, -0.85, 0.5), 0.1, 0.1, 'yellow'),
          k.box((0.3, 0.2, 0.2), (-0.22, -0.88, 0.38), 'yellow_d'), k.box((0.02, 0.3, 0.12), (0.33, 0.25, 0.55), 'red')]
    return q


def loader():
    q = [k.box((0.62, 1.0, 0.3), (0, 0.05, 0.42), 'yellow'), k.box((0.5, 0.4, 0.45), (0, 0.25, 0.78), 'yellow'),
         k.box((0.4, 0.04, 0.3), (0, 0.04, 0.82), 'glass'), k.box((0.55, 0.45, 0.05), (0, 0.25, 1.02), 'yellow_d'),
         k.box((0.8, 0.28, 0.25), (0, -0.78, 0.25), 'purple'), k.box((0.82, 0.06, 0.3), (0, -0.66, 0.32), 'yellow'),
         k.beam((0.22, -0.2, 0.55), (0.22, -0.66, 0.35), 0.06, 0.06, 'yellow'), k.beam((-0.22, -0.2, 0.55), (-0.22, -0.66, 0.35), 0.06, 0.06, 'yellow')]
    for wy in (-0.32, 0.42):
        for sx in (-1, 1):
            q += wheel(sx * 0.36, wy, 0.24, 0.24, 0.16)
    return q


def roller():
    q = [k.box((0.62, 0.8, 0.35), (0, 0.15, 0.45), 'yellow'), k.box((0.5, 0.35, 0.4), (0, 0.3, 0.82), 'yellow'),
         k.box((0.55, 0.4, 0.05), (0, 0.3, 1.04), 'black'), k.box((0.7, 0.25, 0.25), (0, -0.45, 0.55), 'yellow'),
         k.cyl(0.3, 0.75, (0, -0.55, 0.3), 'steel', segs=14, rot=(0, math.pi / 2, 0)),
         k.box((0.78, 0.04, 0.06), (0, -0.82, 0.42), 'red'), k.box((0.62, 0.04, 0.05), (0, -0.16, 0.66), 'red')]
    for sx in (-1, 1):
        q += wheel(sx * 0.36, 0.42, 0.24, 0.24, 0.16)
    return q


def dump_truck():
    q = [k.box((0.6, 0.45, 0.45), (0, -0.48, 0.55), 'yellow'), k.box((0.5, 0.04, 0.25), (0, -0.71, 0.6), 'black'),
         k.box((0.5, 0.04, 0.22), (0, -0.48, 0.92), 'glass'), k.box((0.55, 0.45, 0.06), (0, -0.48, 1.06), 'yellow_d'),
         k.box((0.62, 0.8, 0.12), (0, 0.15, 0.4), 'black'), k.box((0.72, 0.85, 0.08), (0, 0.18, 0.5), 'yellow')]
    for sx in (-1, 1):                                                                 # kuzov bortlari
        q.append(k.box((0.06, 0.85, 0.3), (sx * 0.36, 0.18, 0.68), 'yellow'))
    q.append(k.box((0.72, 0.06, 0.35), (0, -0.22, 0.75), 'yellow'))
    q.append(k.box((0.72, 0.06, 0.22), (0, 0.6, 0.62), 'yellow_d'))
    for wy in (-0.45, 0.35):
        for sx in (-1, 1):
            q += wheel(sx * 0.36, wy, 0.22, 0.22, 0.16)
    return q


RIDES = [smurf_plane, kitty_car, excavator, loader, roller, dump_truck]
for i, build in enumerate(RIDES):
    x = (i - (N - 1) / 2) * PITCH
    base += pedestal(x)
    parts = build()
    for o in parts:
        o.location.x += x
        o.location.z += PIV
    ob = k.join(f'swing{i}', parts)
    # origin — tebranish o'qiga (tagkursi usti): GltfModel lokal X atrofida tebratadi
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    k.scene.cursor.location = (x, 0, PIV)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

k.finish('KIDDIE-RIDES', base, HERE, [('preview.png', (3.5, -6.5, 3.2), (0, 0, 0.7))])

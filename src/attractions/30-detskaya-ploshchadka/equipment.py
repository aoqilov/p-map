"""
30 — Детская площадка: 18 ta jihoz bitta faylda. Rasmlar: attraction-images-park/<Nomi>.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/30-detskaya-ploshchadka/equipment.py [-- <preview_papka> [nom ...]]
Natija shu papkada: equipment.blend, equipment.glb, preview/<nom>.png

Tuzilish (xarita kodi: src/map/PlaygroundEquipment.tsx):
    item_<nom> — har bir jihozning ildiz tuguni; origin — jihoz markazi yer sathida, old tomoni -Y (Blender).
                 Joylashuv — layout.json (nom shu bo'yicha). Blender'da jihozlar ko'rish uchun yonma-yon terilgan,
                 xaritada ularning o'rni e'tiborga olinmaydi.
    Harakatlanadigan qismlar (src/map/GltfModel.tsx qoidalari, raqamlari fayl bo'yicha noyob):
    spin<N>  — tik o'q atrofida aylanadi;  swing<N> — origin atrofida (lokal X o'qi) tebranadi.
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kit  # noqa: E402
from kit import box, cyl, tube, sphere, lathe, pyramid_roof, leaf_roof, chute, curve_tube, spiral, net, ladder, stairs, \
    platform, join, empty  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PREVIEW_DIR = Path(argv[0]) if argv else HERE / 'preview'
ONLY = set(argv[1:])

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
kit.init_materials()
COUNTER = {'spin': 0, 'swing': 0}


def anim_name(kind):
    n = f'{kind}{COUNTER[kind]}'
    COUNTER[kind] += 1
    return n


ITEMS = {}


def item(fn):
    ITEMS[fn.__name__] = fn
    return fn


# ======================= 1-guruh: komplekslar =======================

@item
def playground_complex():
    """Yog'och ustunli katta kompleks: palma-tomli 3 minora, ko'priklar, to'g'ri va spiral slayd, to'rlar, yoy-narvon (~12 × 8 m)"""
    p = []
    towers = [(-3.6, 0.6, 1.8), (0.4, 1.4, 2.1), (3.8, 0.2, 1.6)]  # (x, y, pol balandligi)
    for x, y, z in towers:
        p += platform(x, y, z, 1.6, 1.6, 'post', 'deck', post_h_extra=1.7, rail_mat='green', open_sides=('e', 'w'))
        p.append(tube((x, y, z + 1.7), (x, y, z + 2.4), 0.06, 'post', 6))
        p.append(leaf_roof(1.4, (x, y, z + 2.3), 'green', n=7))
        p.append(sphere(0.12, (x, y, z + 2.7), 'red', 8))
    # ko'priklar: 1-2 — sariq yopiq quvur, 2-3 — arqonli ko'prik
    p.append(curve_tube([(-2.8, 0.8, 1.95), (-1.6, 1.0, 2.1), (-0.4, 1.3, 2.25)], 0.42, 'yellow', 12))
    for k in range(9):
        t = k / 8
        x, y, z = 1.2 + 1.8 * t, 1.3 - 1.1 * t, 2.1 - 0.5 * t + 0.08 * math.sin(math.pi * t)
        p.append(box((0.12, 0.9, 0.05), (x, y, z), 'deck', (0, 0, -0.55)))
    for sd in (-1, 1):
        p.append(tube((1.2, 1.3 + sd * 0.45, 2.9), (3.0, 0.2 + sd * 0.45, 2.4), 0.025, 'green', 4))
    # to'g'ri slayd (kumush, qizil chetli) — o'rta minoradan oldinga
    pts = [(0.4, 0.6 - i * 0.35, 2.15 - 2.0 * (i / 10) ** 1.2) for i in range(11)]
    pts += [(0.4, pts[-1][1] - 0.35 * k, 0.15) for k in range(1, 3)]
    p.append(chute(pts, 0.6, 'steel'))
    for sd in (-1, 1):
        p.append(curve_tube([(0.4 + sd * 0.32, y, z + 0.28) for _, y, z in pts], 0.05, 'red', 6))
    # sariq spiral slayd — chap minoradan
    sp = spiral(-4.9, -0.6, 1.1, 1.8, 0.2, 1.1, start=0.5, n=28)
    p.append(chute(sp, 0.55, 'yellow'))
    # o'ng minora: zina, yashil to'r, yoy-narvon
    p += stairs(5.4, 0.2, 1.6, math.pi, 0.7, 'deck', 'green')
    p += net((3.0, -0.6, 0.2), (4.6, -0.6, 0.2), (4.6, -0.6, 1.6), (3.0, -0.6, 1.6), 6, 6, 'green')
    for k in range(7):
        a = math.pi * k / 6
        for sx in (-0.35, 0.35):
            pass
    arc = [(-1.8 + sx, -2.2 + 1.3 * math.cos(math.pi * k / 10), 1.6 * math.sin(math.pi * k / 10)) for sx in (0,) for k in range(11)]
    for sx in (-0.35, 0.35):
        p.append(curve_tube([(x + sx, y, z) for x, y, z in arc], 0.04, 'green', 6))
    for x, y, z in arc[1:-1]:
        p.append(tube((x - 0.35, y, z), (x + 0.35, y, z), 0.025, 'green', 4))
    # orqa tomonda tirmashish devori
    p.append(box((1.4, 0.12, 1.8), (-3.6, 1.45, 0.9), 'beige', (0.25, 0, 0)))
    for k in range(6):
        p.append(sphere(0.07, (-4.1 + (k % 3) * 0.45, 1.6 - 0.05 * (k // 3), 0.4 + k * 0.25), ['red', 'yellow', 'blue'][k % 3], 6))
    return join('item_playground_complex', p)


@item
def blue_playground():
    """Ko'k tomli kompleks: 3 minora, to'lqinli ochiq slayd, spiral quvur slayd, tirmashish devori (~8 × 6 m)"""
    p = []
    towers = [(-2.0, 0.6, 1.5, 2.0), (0.6, 0.9, 2.0, 2.6), (2.6, 0.2, 1.5, 1.8)]  # x, y, pol, tom balandligi
    for x, y, z, roof in towers:
        p += platform(x, y, z, 1.5, 1.5, 'beige', 'deck', post_h_extra=roof - z + 1.2, rail_mat='blue', open_sides=('e', 'w'))
        p.append(pyramid_roof(1.5, 1.5, 0.7, (x, y, z + roof - z + 1.2), 'blue'))
        p.append(box((1.5, 0.06, 0.55), (x, y - 0.78, z + 0.5), 'navy'))  # old panel
    p.append(cyl(0.12, 0.3, (0.6, 0.9, 3.9), 'red', 6))                    # bayroqcha o'rni
    # to'lqinli ochiq slayd (ko'k) — chap minoradan chapga
    pts = [(-2.8 - 0.3 * i, 0.6 - 0.05 * i, 1.5 - 1.4 * i / 12 + 0.12 * math.sin(i * 1.3)) for i in range(13)]
    p.append(chute(pts, 0.6, 'blue'))
    # spiral yopiq slayd (ko'k quvur) — o'ng minoradan
    sp = spiral(3.6, -0.6, 0.9, 1.5, 0.3, 1.2, start=1.0, n=26)
    p.append(curve_tube(sp, 0.38, 'sky', 12))
    # tirmashish devori (beige) va zina
    p.append(box((1.3, 0.14, 1.9), (0.6, -0.5, 0.95), 'beige', (-0.35, 0, 0)))
    for k in range(7):
        p.append(sphere(0.07, (0.25 + (k % 3) * 0.35, -0.75 + 0.08 * (k // 3), 0.35 + k * 0.22), ['red', 'yellow', 'blue', 'green'][k % 4], 6))
    p += stairs(-2.0, -1.3, 1.5, math.pi / 2, 0.7, 'deck', 'blue')
    # minoralar orasidagi o'tish ko'prigi
    for x0, x1, z0, z1 in ((-1.25, -0.15, 1.5, 2.0), (1.35, 1.85, 2.0, 1.5)):
        p.append(box((x1 - x0, 0.8, 0.06), ((x0 + x1) / 2, 0.75, (z0 + z1) / 2), 'deck', (0, math.atan2(z0 - z1, x1 - x0), 0)))
    return join('item_blue_playground', p)


@item
def tube_slide():
    """Baland minora (yashil palma tom), katta sariq quvur slayd, yog'och zina, arqon ko'prik, ikkinchi minora (~9 × 5 m)"""
    p = []
    p += platform(-1.5, 0.5, 2.6, 1.6, 1.6, 'post', 'deck', post_h_extra=1.8, rail_mat='brown')
    p.append(leaf_roof(1.5, (-1.5, 0.5, 4.5), 'green', n=7))
    p.append(sphere(0.12, (-1.5, 0.5, 4.95), 'red', 8))
    p += platform(2.8, 0.8, 1.8, 1.4, 1.4, 'post', 'deck', post_h_extra=1.5, rail_mat='brown', open_sides=('w',))
    p.append(leaf_roof(1.3, (2.8, 0.8, 3.4), 'green', n=6))
    # arqon ko'prik
    for k in range(10):
        t = k / 9
        p.append(box((0.14, 0.85, 0.05), (-0.7 + 2.8 * t, 0.55 + 0.25 * t, 2.6 - 0.8 * t - 0.15 * math.sin(math.pi * t)), 'deck'))
    for sd in (-1, 1):
        p.append(curve_tube([(-0.7 + 2.8 * t, 0.55 + 0.25 * t + sd * 0.45, 3.4 - 0.8 * t - 0.1 * math.sin(math.pi * t))
                             for t in [i / 8 for i in range(9)]], 0.025, 'brown', 4))
    # katta sariq quvur slayd: minoradan oldinga, egilib pastga, oxirida ochiq tarnov
    pts = [(-1.5, -0.4, 2.7), (-1.2, -1.4, 2.2), (-0.3, -2.0, 1.6), (0.8, -2.0, 1.0), (1.6, -1.5, 0.55)]
    p.append(curve_tube(pts, 0.45, 'yellow', 12))
    p.append(chute([(1.6, -1.5, 0.3), (2.0, -1.2, 0.2), (2.4, -0.9, 0.15)], 0.7, 'yellow'))
    # yog'och zina (orqa tomonda) va kichik slayd ikkinchi minoradan
    p += stairs(-1.5, 2.6, 2.6, -math.pi / 2, 0.8, 'deck', 'brown')
    p.append(chute([(3.6, 0.8 - 0.0, 1.8), (4.2, 0.6, 1.2), (4.7, 0.4, 0.5), (5.0, 0.3, 0.2)], 0.55, 'orange'))
    return join('item_tube_slide', p)


@item
def rope_tunnel():
    """To'q ustunli kompleks: arqon to'r tunneli, ko'k slayd, ustunda radial arqon "piramida", rangli qadamchalar (~9 × 4 m)"""
    p = []
    p += platform(-2.8, 0, 1.5, 1.5, 1.5, 'dark', 'dark', post_h_extra=0.9, rail_mat='dark')
    p += platform(2.4, 0, 1.5, 1.5, 1.5, 'dark', 'dark', post_h_extra=0.9, rail_mat='dark')
    # arqon tunnel: halqalar va bo'ylama arqonlar
    for k in range(7):
        x = -1.9 + k * 0.58
        p.append(curve_tube([(x, 0.55 * math.cos(a), 1.95 + 0.55 * math.sin(a)) for a in [2 * math.pi * j / 12 for j in range(13)]],
                            0.03, 'steel', 4))
    for j in range(10):
        a = 2 * math.pi * j / 10
        p.append(tube((-1.9, 0.55 * math.cos(a), 1.95 + 0.55 * math.sin(a)), (1.6, 0.55 * math.cos(a), 1.95 + 0.55 * math.sin(a)),
                      0.015, 'gray', 4))
    # ustun va radial arqonlar (piramida)
    p.append(tube((0, 0.4, 0), (0, 0.4, 4.6), 0.06, 'dark', 8))
    for k in range(6):
        a = 2 * math.pi * k / 6
        p.append(tube((0, 0.4, 4.6), (math.cos(a) * 1.4, 0.4 + math.sin(a) * 1.4, 2.6), 0.02, 'dark', 4))
        p.append(tube((0, 0.4, 4.1), (math.cos(a) * 0.9, 0.4 + math.sin(a) * 0.9, 4.25), 0.04, 'dark', 4))
    # ko'k slayd o'ng platformadan
    p.append(chute([(3.15 + 0.3 * i, 0 - 0.1 * i, 1.5 - 1.35 * i / 7) for i in range(8)], 0.55, 'blue'))
    # rangli qadamchalar (chap platformaga), ko'k panel, to'r devor
    for k, col in enumerate(['blue', 'green', 'red', 'yellow']):
        x = -4.6 + k * 0.4
        p.append(cyl(0.18, 0.12, (x, -0.5, 0.25 + k * 0.32), col, 8))
        p.append(tube((x, -0.5, 0.3 + k * 0.32), (x, -0.5, 2.0), 0.012, 'gray', 4))
    p.append(box((1.5, 0.06, 1.0), (-2.8, -0.78, 2.0), 'sky'))
    p.append(cyl(0.3, 0.07, (-2.8, -0.82, 2.0), 'yellow', 10, (math.pi / 2, 0, 0)))
    p += net((1.65, 0.75, 0.1), (3.15, 0.75, 0.1), (3.15, 0.75, 1.5), (1.65, 0.75, 1.5), 6, 5, 'dark')
    p += ladder(-2.8, 0.85, 0, 1.5, 0.6, 0, 'dark', 'steel')
    return join('item_rope_tunnel', p)


@item
def stepping_pods():
    """Ko'k tomli minora, katta arqon ramka (to'r devorlar, markazda ustun va radial arqonlar), osma qadamchalar, slayd (~9 × 6 m)"""
    p = []
    p += platform(-3.4, 0.6, 1.4, 1.5, 1.5, 'dark', 'dark', post_h_extra=1.3, rail_mat='dark')
    p.append(pyramid_roof(1.5, 1.5, 0.6, (-3.4, 0.6, 2.7), 'blue'))
    p.append(box((1.5, 0.06, 0.9), (-3.4, -0.18, 1.95), 'sky'))
    # katta to'rtburchak ramka (6 × 4 m, 2.4 m baland) — burchaklarda ustun, tepada to'sinlar
    W, D, H = 5.6, 4.0, 2.4
    cx = 0.8
    corners = [(cx - W / 2, -D / 2), (cx + W / 2, -D / 2), (cx + W / 2, D / 2), (cx - W / 2, D / 2)]
    for x, y in corners:
        p.append(tube((x, y, 0), (x, y, H), 0.06, 'dark', 8))
    for i in range(4):
        (ax, ay), (bx, by) = corners[i], corners[(i + 1) % 4]
        p.append(tube((ax, ay, H), (bx, by, H), 0.05, 'dark', 6))
        if i != 0:  # old tomon ochiq — qadamchalar shu yerda
            p += net((ax, ay, 0.3), (bx, by, 0.3), (bx, by, H - 0.1), (ax, ay, H - 0.1), 8, 5, 'dark')
    # markaziy ustun va radial arqonlar
    p.append(tube((cx, 0, 0), (cx, 0, 4.6), 0.07, 'dark', 8))
    for x, y in corners + [(cx, -D / 2), (cx, D / 2), (cx - W / 2, 0), (cx + W / 2, 0)]:
        p.append(tube((cx, 0, 4.6), (x, y, H), 0.02, 'dark', 4))
    # old tomondagi osma qadamchalar (rangli)
    for k, col in enumerate(['blue', 'gray', 'red', 'green', 'yellow', 'orange', 'blue', 'red']):
        x = cx - W / 2 + 0.4 + k * (W - 0.8) / 7
        p.append(tube((x, -D / 2, H), (x, -D / 2, 0.55), 0.012, 'gray', 4))
        p.append(lathe([(0, 0), (0.16, 0.05), (0.2, 0.18), (0, 0.2)], 8, col, loc=(x, -D / 2, 0.35)))
    # slayd ramka ichidan o'ngga
    p.append(chute([(cx + W / 2 + 0.2 + 0.35 * i, 1.2, 1.4 - 1.25 * i / 6) for i in range(7)], 0.55, 'blue'))
    p += platform(cx + W / 2 - 0.6, 1.2, 1.4, 1.0, 1.0, 'dark', 'dark', rails=False)
    return join('item_stepping_pods', p)


# ======================= 2-guruh: harakatlanuvchi jihozlar =======================

@item
def spinning_platform():
    """Aylanuvchi platforma: qora disk, qizil ramkali 4 ta sariq o'rindiq (⌀ ~2.5 m). Disk + o'rindiqlar — spin"""
    base = [cyl(0.25, 0.12, (0, 0, 0.06), 'gray', 12)]
    s = [cyl(1.25, 0.08, (0, 0, 0.2), 'black', 24), cyl(0.18, 0.55, (0, 0, 0.5), 'red', 10)]
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        ca, sa = math.cos(a), math.sin(a)
        s.append(box((0.42, 0.55, 0.05), (ca * 0.72, sa * 0.72, 0.5), 'yellow', (0, 0, a)))
        s.append(box((0.05, 0.55, 0.35), (ca * 0.5, sa * 0.5, 0.7), 'yellow', (0, 0, a)))
        for sd in (-1, 1):  # qizil quvur ramka
            ox, oy = -sa * 0.3 * sd, ca * 0.3 * sd
            s.append(tube((ca * 0.95 + ox, sa * 0.95 + oy, 0.25), (ca * 0.95 + ox, sa * 0.95 + oy, 0.85), 0.03, 'red', 6))
            s.append(tube((ca * 0.95 + ox, sa * 0.95 + oy, 0.85), (ca * 0.45 + ox, sa * 0.45 + oy, 0.95), 0.03, 'red', 6))
        s.append(tube((ca * 0.45 - sa * 0.3, sa * 0.45 + ca * 0.3, 0.95), (ca * 0.45 + sa * 0.3, sa * 0.45 - ca * 0.3, 0.95), 0.03, 'red', 6))
        s.append(tube((ca * 0.18, sa * 0.18, 0.6), (ca * 0.45, sa * 0.45, 0.95), 0.03, 'red', 6))
    root = join('item_spinning_platform', base)
    sp = join(anim_name('spin'), s)
    sp.parent = root
    return root


@item
def spinning_cone():
    """Aylanuvchi arqon konus: rangli sektorli disk, markazda oq ustun, tepada sariq shar, rangli arqonlar va tugunlar (⌀ 3 m)"""
    base = [cyl(0.3, 0.1, (0, 0, 0.05), 'gray', 12)]
    cols = ['red', 'green', 'yellow', 'blue']
    s = [lathe([(1.5, 0.12), (1.5, 0.22), (0, 0.22)], 24, None, mats=['white'] + cols,
               mat_of=lambda i, k: 0 if i == 0 else 1 + (k * 4 // 24))]
    s.append(cyl(0.3, 0.06, (0, 0, 0.25), 'white', 16))
    s.append(tube((0, 0, 0.2), (0, 0, 3.0), 0.07, 'white', 8))
    s.append(sphere(0.18, (0, 0, 3.1), 'yellow', 10))
    N = 12
    for k in range(N):
        a = 2 * math.pi * k / N
        s.append(tube((0, 0, 2.95), (math.cos(a) * 1.35, math.sin(a) * 1.35, 0.3), 0.018, cols[k % 4], 4))
    for lvl in range(1, 6):
        t = lvl / 6
        r = 1.35 * (1 - t)
        z = 0.3 + (2.95 - 0.3) * t
        pts = [(math.cos(2 * math.pi * k / N) * r, math.sin(2 * math.pi * k / N) * r, z) for k in range(N + 1)]
        s.append(curve_tube(pts, 0.015, 'rope', 4))
        for x, y, zz in pts[:-1]:
            s.append(sphere(0.045, (x, y, zz), 'black', 6))
    root = join('item_spinning_cone', base)
    sp = join(anim_name('spin'), s)
    sp.parent = root
    return root


@item
def nest_swing():
    """Ikki savatli arg'imchoq: jigarrang A-ramkalar, tepadagi to'sin, zanjirlar, pushti to'r savat (~7 × 3 m)"""
    p = []
    H = 2.4
    for x in (-3.0, 0, 3.0):
        for sy in (-1, 1):
            p.append(tube((x, sy * 1.2, 0), (x, 0, H), 0.05, 'brown', 8))
        p.append(tube((x, -0.6, 1.2), (x, 0.6, 1.2), 0.03, 'brown', 6))
    p.append(tube((-3.1, 0, H), (3.1, 0, H), 0.06, 'brown', 8))
    root = join('item_nest_swing', p)
    for cx in (-1.5, 1.5):
        s = []
        for dx in (-0.45, 0.45):
            for dy in (-0.35, 0.35):
                s.append(tube((cx + dx * 0.4, 0, H), (cx + dx, dy, 0.6), 0.012, 'gray', 4))
        s.append(curve_tube([(cx + math.cos(a) * 0.55, math.sin(a) * 0.55, 0.55) for a in [2 * math.pi * j / 16 for j in range(17)]],
                            0.06, 'black', 8))
        s.append(cyl(0.53, 0.03, (cx, 0, 0.5), 'pink', 18))
        for j in range(6):
            a = math.pi * j / 6
            s.append(tube((cx + math.cos(a) * 0.5, math.sin(a) * 0.5, 0.52), (cx - math.cos(a) * 0.5, -math.sin(a) * 0.5, 0.52), 0.01, 'white', 3))
        sw = join(anim_name('swing'), s, origin=(cx, 0, H))
        sw.parent = root
    return root


@item
def seesaw():
    """Ikki qizil qo'sh arg'imchoq, oq o'rindiqlar; to'sin Y bo'ylab, X o'qi atrofida tebranadi"""
    root = join('item_seesaw', [box((1.6, 0.3, 0.02), (0, 0, 0.01), 'gray')])
    for cx in (-0.65, 0.65):
        bj = join('seesaw_base', [box((0.3, 0.45, 0.4), (cx, 0, 0.2), 'red'),
                                  cyl(0.06, 0.4, (cx, 0, 0.45), 'white', 8, (0, math.pi / 2, 0))])
        bj.parent = root
        s = [box((0.16, 3.0, 0.1), (cx, 0, 0.5), 'red')]
        for sy in (-1, 1):
            s.append(lathe([(0, 0), (0.2, 0.02), (0.22, 0.06), (0, 0.07)], 10, 'white', loc=(cx, sy * 1.32, 0.55)))
            s.append(box((0.08, 0.06, 0.3), (cx, sy * 1.05, 0.7), 'red'))
            s.append(tube((cx - 0.15, sy * 1.05, 0.85), (cx + 0.15, sy * 1.05, 0.85), 0.025, 'red', 6))
        sw = join(anim_name('swing'), s, origin=(cx, 0, 0.5))
        sw.parent = root
    return root


@item
def spring_rider():
    """Ikki prujinali o'yinchoq (mototsikl-shakl): qizil va sariq; Y bo'ylab uzun, X o'qi atrofida chayqaladi"""
    root = join('item_spring_rider', [box((2.0, 0.4, 0.02), (0, 0, 0.01), 'gray')])
    for cx, body, acc in ((-0.75, 'red', 'white'), (0.75, 'yellow', 'sky')):
        b = join('rider_base', [cyl(0.25, 0.06, (cx, 0, 0.03), 'gray', 12)])
        b.parent = root
        s = []
        for k in range(6):  # prujina o'ramlari
            s.append(curve_tube([(cx + math.cos(a) * 0.13, math.sin(a) * 0.13, 0.08 + k * 0.07 + a / (2 * math.pi) * 0.07)
                                 for a in [2 * math.pi * j / 10 for j in range(11)]], 0.02, 'black', 4))
        s.append(box((0.32, 1.1, 0.25), (cx, 0, 0.62), body))
        s.append(box((0.3, 0.3, 0.22), (cx, -0.6, 0.75), body, (0.5, 0, 0)))
        s.append(box((0.34, 0.45, 0.08), (cx, 0.15, 0.78), acc))
        s.append(box((0.3, 0.12, 0.12), (cx, -0.3, 0.68), 'white'))
        s.append(tube((cx, -0.4, 0.75), (cx, -0.48, 1.15), 0.03, 'steel', 6))
        s.append(tube((cx - 0.22, -0.48, 1.15), (cx + 0.22, -0.48, 1.15), 0.03, 'steel', 6))
        for sd in (-1, 1):
            s.append(sphere(0.05, (cx + sd * 0.24, -0.48, 1.15), 'black', 6))
        sw = join(anim_name('swing'), s, origin=(cx, 0, 0.1))
        sw.parent = root
    return root


# ======================= 3-guruh: tirmashish =======================

@item
def climbing_dome():
    """Geodezik tirmashish gumbazi: qora quvur ramka, uchlarida sariq/kumush sharlar, ichida qizil arqonlar (⌀ 4 m)"""
    p = []
    R = 1.9
    phi = (1 + 5 ** 0.5) / 2
    raw = [(-1, phi, 0), (1, phi, 0), (-1, -phi, 0), (1, -phi, 0), (0, -1, phi), (0, 1, phi), (0, -1, -phi), (0, 1, -phi),
           (phi, 0, -1), (phi, 0, 1), (-phi, 0, -1), (-phi, 0, 1)]
    verts = [Vector(v).normalized() * R for v in raw]
    z0 = min(v.z for v in verts)
    verts = [v - Vector((0, 0, z0)) for v in verts]  # eng past uchlari yerda
    L0 = (verts[0] - verts[1]).length
    edges = [(i, j) for i in range(12) for j in range(i + 1, 12) if abs((verts[i] - verts[j]).length - L0) < 0.05]
    c = Vector((0, 0, -z0))
    for i, j in edges:
        p.append(tube(verts[i], verts[j], 0.045, 'dark', 6))
        m = (verts[i] + verts[j]) / 2
        p.append(tube(m, c + (m - c) * 0.3, 0.012, 'rope', 3))
    for k, v in enumerate(verts):
        p.append(sphere(0.09, v, 'yellow' if k % 3 == 0 else 'steel', 8))
    return join('item_climbing_dome', p)


@item
def climbing_wall():
    """Ikki tirmashish devori: kulrang qoya-panel (rangli tutqichlar) va firuza nishabli devor arqon bilan"""
    p = [box((1.1, 0.25, 2.4), (-0.6, 0.3, 1.2), 'gray')]
    for k in range(10):  # tutqichlar old yuzada (y = 0.3 - 0.125)
        p.append(sphere(0.06, (-1.0 + (k % 3) * 0.38, 0.15, 0.3 + k * 0.21), ['red', 'teal', 'yellow', 'green'][k % 4], 6))
    for x in (-1.2, 0.0):
        p.append(tube((x, 0.45, 0), (x, 0.45, 2.6), 0.05, 'dark', 6))
    # nishabli devor: yerdan (y=-0.9) tepadagi maydonchagacha (y=0.5, z=1.6)
    th = math.atan2(1.6, 1.4)
    L = math.hypot(1.4, 1.6)
    p.append(box((1.0, L, 0.15), (0.65, -0.2, 0.8), 'teal', (th, 0, 0)))
    p.append(box((1.0, 0.6, 0.12), (0.65, 0.75, 1.6), 'teal'))
    for y in (0.5, 1.0):
        p.append(box((0.08, 0.08, 1.6), (0.2, y, 0.8), 'dark'))
        p.append(box((0.08, 0.08, 1.6), (1.1, y, 0.8), 'dark'))
    nx, nz = -math.sin(th) * 0.09, math.cos(th) * 0.09
    for k in range(5):
        t = 0.15 + k * 0.17
        p.append(sphere(0.06, (0.45 + (k % 2) * 0.35, -0.9 + 1.4 * t + nx, 1.6 * t + nz), ['red', 'yellow', 'green'][k % 3], 6))
    p.append(tube((0.65, 0.5, 1.75), (0.65, -0.85, 0.12), 0.02, 'rope', 4))
    return join('item_climbing_wall', p)


@item
def obstacle_course():
    """To'siqli yo'l: jigarrang yoy ramka, osma oq halqalar, qadam tumbalar, to'r devor, kichik minora (~7 × 3 m)"""
    p = []
    arc = [(-2.6 + 1.0 * (1 - math.cos(math.pi * k / 12)), 2.0 * math.sin(math.pi * k / 12)) for k in range(13)]
    for sy in (-0.6, 0.6):
        p.append(curve_tube([(x, sy, z) for x, z in arc], 0.05, 'brown', 6))
        p.append(tube((-0.6, sy, 2.0), (2.8, sy, 2.0), 0.05, 'brown', 6))
        p.append(tube((2.8, sy, 0), (2.8, sy, 2.0), 0.05, 'brown', 6))
    p.append(tube((-2.6, -0.6, 0), (-2.6, 0.6, 0), 0.05, 'brown', 6))
    for k in range(4):
        x = -0.2 + k * 0.5
        p.append(tube((x, 0, 2.0), (x, 0, 1.4), 0.012, 'gray', 4))
        p.append(curve_tube([(x + 0.12 * math.sin(a), 0, 1.15 + 0.25 * math.cos(a)) for a in [2 * math.pi * j / 12 for j in range(13)]],
                            0.03, 'white', 5))
    for k, col in enumerate(['blue', 'blue', 'gray', 'blue']):
        h = 0.25 + 0.1 * (k % 2)
        p.append(cyl(0.16, h, (-0.1 + k * 0.5, 0, h / 2), col, 8))
    p += net((1.9, -0.6, 0.2), (2.8, -0.6, 0.2), (2.8, -0.6, 1.8), (1.9, -0.6, 1.8), 5, 7, 'dark')
    p.append(box((0.9, 1.2, 0.06), (2.35, 0.0, 1.0), 'deck'))
    p.append(box((0.5, 0.05, 0.8), (2.4, 0.6, 1.4), 'sky'))
    return join('item_obstacle_course', p)


@item
def ring_tunnel():
    """Halqa tunnel: 8 ta rangli po'lat halqa ketma-ket, pastida oyoqchalar (Y bo'ylab ~5 m)"""
    p = []
    cols = ['blue', 'green', 'yellow', 'orange', 'beige', 'purple', 'navy', 'red']
    for k, col in enumerate(cols):
        y = -2.2 + k * 0.63
        p.append(curve_tube([(0.62 * math.cos(a), y, 0.72 + 0.62 * math.sin(a)) for a in [2 * math.pi * j / 18 for j in range(19)]],
                            0.045, col, 6))
        for sx in (-0.4, 0.4):
            p.append(box((0.1, 0.1, 0.05), (sx, y, 0.03), col))
    return join('item_ring_tunnel', p)


# ======================= 4-guruh: o'yin jihozlari =======================

@item
def caterpillar_tunnel():
    """Qurtcha tunnel: yashil halqali quvur, qora oyoqlar, ko'k bosh — katta ko'zlar, mo'ylovlar (X bo'ylab ~4.5 m)"""
    p = []
    for k in range(4):
        x = -1.8 + k * 0.85
        p.append(cyl(0.48, 0.75, (x, 0, 0.85), 'green', 14, (0, math.pi / 2, 0), caps=False))
        p.append(cyl(0.52, 0.1, (x + 0.38, 0, 0.85), 'lime', 14, (0, math.pi / 2, 0), caps=False))
        for sy in (-1, 1):
            p.append(tube((x, sy * 0.3, 0.45), (x + 0.1, sy * 0.65, 0.0), 0.03, 'black', 5))
    p.append(sphere(0.55, (1.9, 0, 1.3), 'navy', 12))
    for sy in (-0.22, 0.22):
        p.append(sphere(0.18, (2.3, sy, 1.42), 'sky', 8))
        p.append(sphere(0.08, (2.43, sy, 1.42), 'black', 6))
        p.append(tube((1.95, sy, 1.75), (2.0, sy * 1.6, 2.15), 0.02, 'black', 4))
        p.append(sphere(0.06, (2.0, sy * 1.6, 2.15), 'yellow', 6))
    p.append(tube((1.6, 0, 0.9), (1.9, 0, 0.0), 0.05, 'yellow', 6))
    return join('item_caterpillar_tunnel', p)


@item
def fish_and_dome():
    """Sariq baliq (og'zi — to'q sariq halqali teshik) va firuza-kulrang teshikli gumbaz (X bo'ylab ~4 m)"""
    p = [sphere(0.7, (-1.2, 0, 0.75), 'yellow', 14)]
    p.append(curve_tube([(-1.2 + 0.35 * math.cos(a), -0.66, 0.75 + 0.35 * math.sin(a)) for a in [2 * math.pi * j / 14 for j in range(15)]],
                        0.08, 'orange', 6))
    p.append(cyl(0.3, 0.1, (-1.2, -0.68, 0.75), 'black', 12, (math.pi / 2, 0, 0)))
    p.append(box((0.08, 0.6, 0.7), (-1.95, 0.25, 0.8), 'yellow', (0, 0, 0.4)))
    p.append(box((0.5, 0.08, 0.35), (-1.2, 0.2, 1.45), 'yellow'))
    p.append(sphere(0.12, (-0.8, -0.45, 1.15), 'white', 8))
    p.append(sphere(0.06, (-0.78, -0.55, 1.15), 'black', 6))
    p.append(lathe([(0.95, 0), (0.92, 0.3), (0.75, 0.65), (0.45, 0.88), (0, 0.95)], 14, None, loc=(1.0, 0, 0),
                   mats=['teal', 'gray'], mat_of=lambda i, k: (k // 2) % 2))
    for k in range(7):
        a = 2 * math.pi * k / 7
        p.append(cyl(0.12, 0.05, (1.0 + math.cos(a) * 0.84, math.sin(a) * 0.84, 0.45), 'navy', 8, (math.pi / 2, 0, a + math.pi / 2)))
    return join('item_fish_and_dome', p)


@item
def musical_pipes():
    """Musiqa quvurlari: sariq ramka, turli uzunlikdagi kumush quvurlar (X bo'ylab ~3 m)"""
    p = []
    for x in (-1.5, -0.4, 0.5, 1.5):
        h = 1.6 if abs(x) < 1 else 1.9
        p.append(tube((x, 0, 0), (x, 0, h), 0.04, 'yellow', 8))
        p.append(sphere(0.06, (x, 0, h + 0.02), 'yellow', 6))
    p.append(tube((-1.5, 0, 0.55), (1.5, 0, 0.55), 0.03, 'yellow', 6))
    p.append(tube((-1.5, 0, 1.2), (1.5, 0, 1.2), 0.03, 'yellow', 6))
    for k in range(14):
        x = -1.35 + k * 0.205
        h = 0.6 + 0.12 * (k % 7) + (0.4 if k > 9 else 0)
        p.append(tube((x, 0.07, 0.6), (x, 0.07, 0.6 + h), 0.035, 'steel', 8))
    return join('item_musical_pipes', p)


@item
def talk_tubes():
    """Gaplashish quvurlari: rangli egilgan quvurlar, voronkalar, qora tumbalar (~4 × 3 m)"""
    p = []
    cols = ['green', 'sky', 'purple', 'yellow', 'blue']
    for k, col in enumerate(cols):
        a = k * 2 * math.pi / 5
        cx, cy = math.cos(a) * 1.1, math.sin(a) * 1.1
        dx, dy = -math.sin(a), math.cos(a)
        pts = [(cx + dx * (t - 0.5) * 1.2, cy + dy * (t - 0.5) * 1.2, 0.3 + 0.7 * abs(math.sin(math.pi * 1.5 * t)))
               for t in [j / 16 for j in range(17)]]
        p.append(curve_tube(pts, 0.06, col, 6))
        p.append(lathe([(0.06, 0), (0.16, 0.12), (0.18, 0.16)], 10, col, loc=pts[0]))
        p.append(lathe([(0.06, 0), (0.16, 0.12), (0.18, 0.16)], 10, col, loc=pts[-1]))
    for x, y in ((0.3, -0.4), (-0.7, 0.9), (1.4, 0.8)):
        p.append(cyl(0.18, 0.35, (x, y, 0.17), 'black', 10))
    return join('item_talk_tubes', p)


# ======================= Soya daraxti =======================

@item
def shade_tree():
    """Katta soya beruvchi daraxt: yo'g'on tana, 4 shox, keng zich toj (bir necha bo'lak, ikki xil yashil), ~9 m baland, toj ⌀ ~8 m"""
    p = [cyl(0.32, 3.2, (0, 0, 1.6), 'brown', 9, r2=0.24), cyl(0.5, 0.25, (0, 0, 0.12), 'brown', 9, r2=0.32)]
    crowns = [((0, 0, 6.3), 2.6), ((1.9, 0.6, 5.6), 1.9), ((-1.8, 0.9, 5.7), 2.0), ((0.5, -1.9, 5.5), 1.9),
              ((-0.9, -1.4, 6.6), 1.7), ((1.0, 1.6, 6.9), 1.6), ((0, 0, 7.7), 1.6)]
    for (x, y, z), r in crowns:
        p.append(tube((0, 0, 3.0), (x * 0.75, y * 0.75, z - r * 0.6), 0.13, 'brown', 6))  # shox
    for k, ((x, y, z), r) in enumerate(crowns):
        bm_mat = 'green' if k % 2 == 0 else 'lime'
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=r, location=(x, y, z))
        o = bpy.context.active_object
        o.scale = (1.0, 1.0, 0.78)
        o.data.materials.append(kit.MATS[bm_mat])
        p.append(o)
    return join('item_shade_tree', p)


# ======================= Qurish, eksport, preview =======================

def main():
    names = [n for n in ITEMS if not ONLY or n in ONLY]
    roots = []
    for i, name in enumerate(names):
        root = ITEMS[name]()
        root.location = (i * 16.0, 0, 0)  # Blender'da ko'rish uchun yonma-yon
        roots.append(root)
        tris = sum(len(pg.vertices) - 2 for o in [root, *root.children_recursive] if o.type == 'MESH' for pg in o.data.polygons)
        print(f'PG {name}: tris={tris}')
    if not ONLY:
        bpy.ops.wm.save_as_mainfile(filepath=str(HERE / 'equipment.blend'))
        bpy.ops.export_scene.gltf(filepath=str(HERE / 'equipment.glb'), export_format='GLB', export_apply=True, export_yup=True)
        print(f"PG glb={(HERE / 'equipment.glb').stat().st_size // 1024} KB")
    # preview: har bir jihoz alohida
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    scene.collection.objects.link(cam)
    scene.camera = cam
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'MATERIAL'
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.render.resolution_x, scene.render.resolution_y = 700, 560
    world = bpy.data.worlds.new('w')
    world.color = (0.93, 0.95, 0.98)
    scene.world = world
    for root in roots:
        for o in roots:
            for x in [o, *o.children_recursive]:
                x.hide_render = o is not root
        objs = [o for o in [root, *root.children_recursive] if o.type == 'MESH']
        pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        size = max((hi - lo).x, (hi - lo).y, (hi - lo).z, 1.5)
        c = (lo + hi) / 2
        cam.location = c + Vector((0.9, -1.25, 0.75)) * size * 1.15
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(PREVIEW_DIR / f"{root.name.replace('item_', '')}.png")
        bpy.ops.render.render(write_still=True)
    print('PG preview done')


main()

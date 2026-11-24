"""
30 — Детская площадка: jihozlar joylashuvi → src/attractions/30-detskaya-ploshchadka/layout.json

Ishga tushirish (park.json tayyor bo'lgach): python scripts/genplan/playground_layout.py [--force]
layout.json mavjud bo'lsa, --force siz qayta yozilmaydi (qo'lda tuzatilgan joylashuv saqlanib qoladi).

Qoidalar:
- Yirik komplekslar va aylanuvchi jihozlar plandagi yashil halqalar markaziga (FIXED).
- Qolganlari kattasidan boshlab, maydonchaning eng bo'sh joyiga: boshqa jihozlardan xavfsizlik oralig'i (SAFETY),
  panjaradan FENCE_GAP, yashil halqalar ustiga tushmaydi. 0° / 90° / maydoncha qirrasiga parallel burilishlardan
  eng ko'p bo'sh joy qoldiradigani tanlanadi.
"""
import json
import math
import sys
from pathlib import Path

from shapely.geometry import Polygon, Point, box as sbox
from shapely.ops import unary_union
from shapely import affinity

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'src' / 'attractions' / '30-detskaya-ploshchadka' / 'layout.json'
SAFETY = 1.8      # jihozlar orasidagi bo'sh joy, m (EN 1176 xavfsizlik zonasi taxminan)
FENCE_GAP = 1.5   # panjaradan
TREES = 4         # katta soya daraxtlari (equipment.py → shade_tree). Eslatma: sharqiy daraxt (36.2, 81.9) layout.json dan qo'lda olib tashlangan
TREE_GAP = 2.5    # daraxt tanasidan eng yaqin jihozgacha, m
TREE_EDGE = 4.5   # daraxt tanasidan panjaragacha, m

# nomi: (eni, chuqurligi) — metr, lokal X × Y (equipment.py dagi modellar o'lchami)
SIZES = {
    'playground_complex': (12.0, 8.0), 'blue_playground': (11.5, 4.5), 'tube_slide': (8.5, 5.5),
    'rope_tunnel': (10.5, 3.0), 'stepping_pods': (10.5, 4.5), 'obstacle_course': (7.0, 3.0),
    'nest_swing': (7.0, 3.0), 'caterpillar_tunnel': (4.5, 1.6), 'ring_tunnel': (1.6, 5.0),
    'fish_and_dome': (4.2, 1.8), 'talk_tubes': (4.0, 3.0), 'seesaw': (1.8, 3.2),
    'climbing_wall': (2.6, 2.6), 'climbing_dome': (4.0, 4.0), 'musical_pipes': (3.2, 0.8),
    'spinning_cone': (3.0, 3.0), 'spinning_platform': (2.6, 2.6), 'spring_rider': (2.2, 1.4),
}
# plandagi yashil halqalar (markaz, park metrlari) — shu jihozlar uchun
FIXED = {
    'playground_complex': (21.1, 55.9),
    'blue_playground': (22.0, 100.6),
    'spinning_platform': (20.6, 77.8),
    'spinning_cone': (5.8, 65.5),
    'spring_rider': (29.3, 88.7),
}


def rect(name, x, y, rot):
    w, d = SIZES[name]
    return affinity.rotate(sbox(x - w / 2, y - d / 2, x + w / 2, y + d / 2), rot, origin=(x, y))


def main():
    if OUT.exists() and '--force' not in sys.argv:
        print(f'{OUT.relative_to(ROOT)} bor — o\'zgartirilmadi (qayta yozish: --force)')
        return
    data = json.loads((ROOT / 'src' / 'map' / 'park.json').read_text(encoding='utf8'))
    pg = Polygon([a for a in data['playgrounds'] if a['id'] == 'n30'][0]['poly'][0])
    green = unary_union([Polygon(s['poly'][0]) for s in data.get('surfaces', []) if s['kind'] == 'rubber_green'])
    free_area = pg.buffer(-FENCE_GAP)
    # qirralar yo'nalishlari (maydonchaga parallel burilish uchun)
    ring = list(pg.exterior.coords)
    edge_angles = sorted({round(math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180)
                          for a, b in zip(ring[:-1], ring[1:]) if math.dist(a, b) > 8})

    placed = []
    for name, (x, y) in FIXED.items():
        placed.append({'name': name, 'x': x, 'y': y, 'rot': 0})
    occupied = [rect(p['name'], p['x'], p['y'], p['rot']) for p in placed]

    rest = sorted((n for n in SIZES if n not in FIXED), key=lambda n: -SIZES[n][0] * SIZES[n][1])
    minx, miny, maxx, maxy = free_area.bounds
    grid = [(minx + i * 0.75, miny + j * 0.75) for i in range(int((maxx - minx) / 0.75) + 1)
            for j in range(int((maxy - miny) / 0.75) + 1)]
    for name in rest:
        best = None
        blockers = unary_union([o.buffer(SAFETY) for o in occupied] + [green.buffer(0.3)])
        for x, y in grid:
            if not free_area.contains(Point(x, y)):
                continue
            for rot in [0, 90] + edge_angles:
                r = rect(name, x, y, rot)
                if not free_area.contains(r) or r.intersects(blockers):
                    continue
                # eng bo'sh joy: boshqa jihozlar va panjaradan eng uzoq
                score = min(r.distance(unary_union(occupied)), r.distance(pg.exterior) * 1.5)
                if best is None or score > best[0]:
                    best = (score, x, y, rot)
        if not best:
            print(f'⚠ {name}: joy topilmadi')
            continue
        _, x, y, rot = best
        placed.append({'name': name, 'x': round(x, 2), 'y': round(y, 2), 'rot': rot})
        occupied.append(rect(name, x, y, rot))
        print(f'✓ {name}: ({x:.1f}, {y:.1f}) {rot}° — bo\'sh joy {best[0]:.1f} m')
    # Katta soya daraxtlari: jihozlardan TREE_GAP, panjaradan TREE_EDGE uzoqda, bir-biridan iloji boricha uzoq
    items_u = unary_union(occupied)
    trees = []
    inner = pg.buffer(-TREE_EDGE)  # toj (radiusi ~4 m) maydoncha ichida qolsin — soyasi o'yin joyiga tushadi
    for k in range(TREES):
        best = None
        for x, y in grid:
            pt = Point(x, y)
            if not inner.contains(pt) or pt.distance(items_u) < TREE_GAP:
                continue
            # bir-biridan uzoq (soya maydoncha bo'ylab tarqalsin), jihozlardan esa yetarli (lekin juda uzoq shart emas)
            spread = min([pt.distance(Point(t['x'], t['y'])) for t in trees] or [30.0])
            score = min(spread, 30.0) + min(pt.distance(items_u), 4.0) * 2
            if best is None or score > best[0]:
                best = (score, x, y)
        if not best:
            print(f'⚠ daraxt {k + 1}: joy topilmadi')
            break
        trees.append({'name': 'shade_tree', 'x': round(best[1], 2), 'y': round(best[2], 2), 'rot': (k * 73) % 360})
        print(f'✓ soya daraxti {k + 1}: ({best[1]:.1f}, {best[2]:.1f})')
    placed += trees

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({'note': 'x, y — park metrlari (x sharq, y shimol), rot — gradus soat teskarisiga. '
                                       'Qo\'lda o\'zgartirsa bo\'ladi.', 'items': placed}, indent=1, ensure_ascii=False),
                   encoding='utf8')
    print(f'→ {OUT.relative_to(ROOT)}: {len(placed)} ta jihoz')


if __name__ == '__main__':
    main()

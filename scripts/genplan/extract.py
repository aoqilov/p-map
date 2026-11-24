"""
Gen plan PDF → data/genplan/genplan.geojson

Ishga tushirish (Python 3.11+, pypdfium2, shapely, numpy):
    python scripts/genplan/extract.py

1. PDF dagi to'ldirilgan shakllar rangiga qarab turga ajratiladi (maysa, suv, bino, attraksion...).
2. Park chegarasi — plandagi qalin qizil chiziq (yer uchastkasi chegarasi).
3. Yo'l/maydon yuzasi = chegara − (maysa, suv, bino, attraksion, maydoncha, parking).
4. Raqamli yozuvlar eksplikatsiya (explication.py) bilan bog'lanadi → obyektlar.
5. Marshrut uchun yo'l markaz chiziqlari (medial o'q) quriladi.
6. Planda faqat ingichka chiziq bilan chizilgan mavjud binolar, ariq va ko'priklar — data/genplan/existing.geojson dan.

Koordinatalarni bog'lash: scripts/genplan/georef.json (PDF pt → metr).
"""
import json, math, re, sys
from collections import defaultdict

import numpy as np
from shapely.geometry import Point, LineString, MultiPoint, Polygon, MultiPolygon, mapping, shape
from shapely.ops import unary_union, linemerge, polygonize
from shapely import minimum_bounding_circle, voronoi_polygons, simplify

sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from common import ROOT, OUT_DIR, read_pdf, load_georef, pt_to_m, m_to_lonlat, lonlat_to_m  # noqa: E402
from explication import DROP_AT, E, HEIGHT, HEIGHT_DEFAULT, MERGE_GAPS, MERGE_PADS, NAME_AT, PAD_AT  # noqa: E402

# ---------- Ranglar → turlar ----------
COLOR_KIND = {
    (128, 204, 40): 'lawn',
    (175, 217, 170): 'lawn',
    (173, 221, 247): 'water',
    (139, 57, 24): 'building',
    (39, 118, 187): 'building',      # КН — hojatxona / kichik bino
    (147, 149, 152): 'building',
    (118, 118, 118): 'building',
    (255, 159, 127): 'building',     # 49 — Развлекательный центр
    (242, 113, 114): 'attraction',   # pushti maydonchalar
    (122, 175, 223): 'attraction',   # 28 — Водные гусеницы
    (209, 156, 199): 'attraction',   # Автодром
    (242, 103, 34): 'playground',    # 30 — Детская площадка
    (19, 103, 52): 'playground',
    (181, 28, 33): 'playground',
    (226, 155, 110): 'playground',   # 55 — Детский лабиринт
    (254, 204, 102): 'plaza',        # 72 atrofi
    (199, 200, 202): 'plaza',        # kulrang maydon; 51 yozuvi turgan qismi — parking
}
SURFACE_COLORS = {(242, 103, 34): 'rubber', (19, 103, 52): 'rubber_green', (181, 28, 33): 'rubber_edge'}
MIN_AREA = {'lawn': 2.0, 'water': 4.0, 'building': 2.0, 'attraction': 3.0, 'playground': 2.0, 'plaza': 4.0}

# Eski xaritadan olinadigan (planda rang bilan to'ldirilmagan) obyektlar
OLD_BUILDINGS = {  # eski nom → eksplikatsiya raqami (bo'lsa)
    'Ariston Park': '2', 'DAR': '3', 'Bino_1': None, 'Bino_2': None, 'More_Bino': None, 'Bani': None,
}
OLD_HEIGHT = {'Bino_1': 4.5, 'Bino_2': 4, 'More_Bino': 5.5, 'Bani': 6}


def parts(g):
    if g.is_empty:
        return []
    return [p for p in getattr(g, 'geoms', [g]) if p.geom_type == 'Polygon']


def clean(g, eps=0.15):
    return g.buffer(eps, join_style=2).buffer(-eps, join_style=2)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    G = load_georef()
    fills, strokes, texts, _ = read_pdf()
    # Planda faqat ingichka chiziq bilan chizilgan mavjud obyektlar (sputnikdan chizilgan): binolar, Salor kanali, ko'priklar
    old = json.loads((ROOT / 'data' / 'genplan' / 'existing.geojson').read_text(encoding='utf8'))
    old_m = [(f['properties']['name'], lonlat_to_m(shape(f['geometry']))) for f in old['features']]

    # ---------- 1. Rangli shakllar (metrda) ----------
    kinds = defaultdict(list)
    for c, g in fills.items():
        k = COLOR_KIND.get(c)
        if not k:
            continue
        for p in parts(pt_to_m(g, G)):
            if p.area >= MIN_AREA[k]:
                kinds[k].append(p)
    for k in kinds:
        kinds[k] = parts(clean(unary_union(kinds[k])))
        print(f'  {k:11s} {len(kinds[k]):4d} ta, {round(sum(p.area for p in kinds[k]))} m²')

    # ---------- 2. Chegara ----------
    red = [pt_to_m(l, G) for l in strokes.get(((255, 0, 0), 24.0), [])]
    merged = linemerge(unary_union(red))
    lines = list(getattr(merged, 'geoms', [merged]))
    # Uzilishlar: faqat uzun bo'laklar (> 50 m) uchlari orasida, ≤ 25 m bo'lsa ulanadi
    longs = [l for l in lines if not l.is_ring and l.length > 50]
    ends = [Point(c) for l in longs for c in (l.coords[0], l.coords[-1])]
    bridges = []
    for i, a in enumerate(ends):
        others = [b for j, b in enumerate(ends) if j // 2 != i // 2 and a.distance(b) > 0.01]
        best = min(others, key=a.distance, default=None)
        if best is not None and a.distance(best) <= 25:
            bridges.append(LineString([a, best]))
    polys = sorted(polygonize(unary_union(longs + bridges)), key=lambda p: -p.area)
    boundary = polys[0]
    solid_all = unary_union([p for k in kinds for p in kinds[k]])
    boundary = clean(unary_union([boundary, solid_all.buffer(0.5)]), 1.0)
    boundary = max(parts(boundary), key=lambda p: p.area)
    boundary = Polygon(boundary.exterior)
    print(f'✓ Chegara: {round(boundary.area)} m² ({round(boundary.length)} m perimetr)')

    # ---------- 2a. Mashina kirishidagi fontan maydoni (9) — uchastka chegarasidan tashqarida ----------
    entrance = entrance_fountain(fills, strokes, texts, G)
    if entrance:
        boundary = Polygon(max(parts(clean(unary_union([boundary, entrance['plaza'].buffer(0.05)]), 0.3)),
                               key=lambda p: p.area).exterior)
        print(f"✓ 9-fontan maydoni: {round(entrance['plaza'].area)} m², hovuz r={entrance['r']:.1f} m, "
              f"{len(entrance['beds'])} gulzor")

    # ---------- 3. Eski xaritadan: ariq, ko'priklar, mavjud binolar ----------
    plan_solid = unary_union([p for k in ('building', 'attraction', 'playground', 'water') for p in kinds[k]])
    extra_bld = []
    for name, g in old_m:
        if name in OLD_BUILDINGS and g.geom_type == 'Polygon':
            ov = g.intersection(plan_solid).area / g.area
            if ov < 0.2:
                extra_bld.append((name, g))
            else:
                print(f'  · eski "{name}" plandagi shakl bilan ustma-ust ({ov:.0%}) — plan olinadi')
    ariq = [g for n, g in old_m if n == 'Ariq']
    kopriks = [g for n, g in old_m if n == 'Koprik' and g.geom_type == 'LineString'
               and any(g.intersects(a) for a in ariq)]

    # ---------- 4. Parking: 51 — kulrang maydon; 50 — pastdagi ko'k joylar chizig'i ----------
    labels = []
    seen = set()
    for t in texts:
        s = t['t'].strip()
        if t['c'] == (255, 0, 0) and 15 <= t['h'] <= 26 and s in E:
            p = pt_to_m(Point(t['x'], t['y']), G)
            key = (s, round(p.x / 3), round(p.y / 3))
            if key not in seen:
                seen.add(key)
                labels.append((s, p))
    parking = []
    for s, p in labels:
        if s == '51':
            pl = min(kinds['plaza'], key=lambda q: q.distance(p))
            if pl.distance(p) < 10:
                kinds['plaza'].remove(pl)
                parking.append(('51', pl))
    blue = [pt_to_m(l, G) for k, v in strokes.items() if k[0] == (0, 0, 255) for l in v]
    lab50 = next(p for s, p in labels if s == '50')
    south = [l for l in blue if l.distance(lab50) < 90 and l.length < 30]
    if south:
        hull = unary_union(south).convex_hull.buffer(1.0).intersection(boundary)
        hull = hull.difference(unary_union(kinds['building'] + kinds['lawn']).buffer(0.3))
        p50 = max(parts(hull), key=lambda q: q.area)
        parking.append(('50', p50))
        print(f'✓ 50-parking: {round(p50.area)} m² ({len(south)} ta joy chizig\'i)')

    # ---------- 5. Yo'l / maydon yuzasi ----------
    water_all = unary_union(kinds['water'] + ariq)
    occupied = unary_union(kinds['lawn'] + kinds['building'] + kinds['attraction'] + kinds['playground']
                           + [g for _, g in extra_bld] + [g for _, g in parking] + [water_all]
                           + (entrance['beds'] + [entrance['basin']] if entrance else []))
    paving = clean(boundary.difference(occupied), 0.2)
    paving = unary_union([p for p in parts(paving) if p.area > 3])
    print(f'✓ Yo\'l va maydonlar: {round(paving.area)} m², {len(parts(paving))} bo\'lak')

    # ---------- 6. Raqamli obyektlar ----------
    by_kind = {
        'attraction': kinds['attraction'] + kinds['playground'],
        'playground': kinds['playground'] + kinds['attraction'],
        'building': kinds['building'] + [g for _, g in extra_bld],
        'fountain': kinds['water'] + kinds['attraction'] + kinds['building'],
        'parking': [g for _, g in parking],
        'entrance': [],
    }
    used = set()
    objects = []
    for s, p in sorted(labels, key=lambda x: float(x[0])):
        name, kind, cat = E[s]
        cands = by_kind[kind]
        fp = None
        if s in PAD_AT:  # qo'lda bog'langan: yozuv emas, ko'rsatilgan nuqtadagi maydoncha
            p = Point(PAD_AT[s])
            if not any(q.contains(p) for q in cands):
                # planda boshqa rang bilan (masalan, bino rangida) chizilgan maydoncha — shu nuqtadagi istalgan shakl
                anyk = [q for k in ('building', 'plaza', 'playground', 'attraction') for q in kinds[k] if q.contains(p)]
                if anyk:
                    cands = anyk
        if cands:
            inside = [q for q in cands if q.contains(p)]
            near = min(cands, key=lambda q: q.distance(p))
            # yozuv obyekt ichida yoki yonida (≤ 6 m) turadi; juda katta maydon (maysa) olinmaydi
            fp = inside[0] if inside else (near if near.distance(p) <= 6 else None)
            if fp is not None and fp.area > 6000 and kind != 'parking':
                fp = None
        if fp is not None and id(fp) in used and kind not in ('parking', 'playground'):
            fp = None if fp.area > 400 else fp
        if fp is not None:
            used.add(id(fp))
        if s == '9' and entrance:  # yozuv chiziqcha bilan chetga chiqarilgan — pin fontan markazida tursin
            p, fp = entrance['center'], None
        objects.append(dict(num=s, name=name, kind=kind, category=cat, at=p, fp=fp))
    miss = [o['num'] for o in objects if o['fp'] is None]
    print(f'✓ Obyektlar: {len(objects)} ta yozuv; shaklsiz (nuqta) qolganlari: {", ".join(miss)}')

    # Raqamsiz pushti attraksion maydonchalari (Батут, Sky tower, ...) — yaqin qora yozuv nomi bilan
    black = [(t['t'].strip(), pt_to_m(Point(t['x'], t['y']), G)) for t in texts
             if t['c'] == (0, 0, 0) and re.search(r'[A-Za-zА-Яа-я]{3,}', t['t']) and t['h'] > 6]
    unnamed = []
    for q in kinds['attraction']:
        if id(q) in used:
            continue
        lbl = [s for s, p in black if q.buffer(1).contains(p) and s.lower() not in ('аттракцион', 'attraction')]
        unnamed.append(dict(num=None, name=' '.join(dict.fromkeys(lbl)) or 'Аттракцион', kind='attraction', category='fun',
                            at=q.representative_point(), fp=q))
    # Bo'laklarga bo'lingan maydoncha (explication.py → MERGE_PADS): nomsiz bo'laklar raqamliga qo'shiladi, bitta doira
    merged_pieces = []
    for num, pts in MERGE_PADS.items():
        o = next((o for o in objects if o['num'] == num and o['fp'] is not None), None)
        if not o:
            continue
        pieces = [u for u in unnamed if any(u['fp'].contains(Point(xy)) for xy in pts)]
        if not pieces:
            continue
        # bo'laklar doiraning bir qismini (sektor kesilgan) qoplaydi — eng kichik o'rab oluvchi doira
        hull = minimum_bounding_circle(unary_union([o['fp']] + [u['fp'] for u in pieces]))
        unnamed = [u for u in unnamed if u not in pieces]
        merged_pieces.extend([id(o['fp'])] + [id(u['fp']) for u in pieces])  # asl bo'laklar alohida chizilmasin
        o['fp'] = hull
        paving = unary_union([q for q in parts(paving.difference(hull)) if q.area > 3])
        print(f'✓ {num}: {len(pieces)} ta bo\'lak qo\'shildi → {round(hull.area, 1)} m²')
    print(f'✓ Raqamsiz attraksion maydonchalari: {len(unnamed)} ta ({", ".join(o["name"] for o in unnamed)})')

    # ---------- 6a. Maydonchaga qo'shiladigan tor oraliqlar (explication.py → MERGE_GAPS) ----------
    # Masalan, 30 (bolalar maydonchasi) va 28 (suv attraksioni) orasidagi ~1.4 m plitka — aslida maydoncha hududi
    extra_rubber = []
    for a_num, b_num, gap in MERGE_GAPS:
        fa = next((o for o in objects if o['num'] == a_num and o['fp'] is not None), None)
        fb = next((o for o in objects if o['num'] == b_num and o['fp'] is not None), None)
        if not fa or not fb:
            continue
        fill = unary_union([fa['fp'], fb['fp']]).buffer(gap, join_style=2).buffer(-gap, join_style=2)
        fill = fill.difference(fa['fp']).difference(fb['fp']).intersection(paving)
        fill = unary_union([q for q in parts(fill) if q.area > 2])
        if fill.is_empty:
            continue
        fa['fp'] = max(parts(unary_union([fa['fp'], fill.buffer(0.02)])), key=lambda q: q.area)
        paving = unary_union([q for q in parts(paving.difference(fill.buffer(0.02))) if q.area > 3])
        extra_rubber += parts(fill)
        print(f"✓ {a_num} ga qo'shildi ({b_num} bilan oraliq): {round(fill.area)} m²")

    # ---------- 7. Marshrut chiziqlari (medial o'q) ----------
    paths = centerlines(paving)
    print(f'✓ Markaz chiziqlari: {len(paths)} ta, {round(sum(l.length for l in paths))} m')

    # ---------- Yozish ----------
    feats = []

    def add(geom, **props):
        feats.append({'type': 'Feature', 'properties': props, 'geometry': mapping(m_to_lonlat(simplify(geom, 0.05)))})

    add(boundary, layer='boundary', source='plan')
    for p in parts(paving):
        add(p, layer='paving', source='plan')
    for k in ('lawn', 'water', 'plaza'):
        for p in kinds[k]:
            add(p, layer=k, source='plan')
    # Bolalar maydonchasi qoplamasi (yumshoq rezina): plandagi ranglar alohida — to'q sariq asos, to'q yashil halqalar,
    # qizil chetlar. Chizish tartibi shu (keyingisi ustida)
    for c, kind in SURFACE_COLORS.items():
        for q in parts(clean(pt_to_m(fills.get(c, Polygon()), G), 0.05)):
            if q.area >= 0.5:
                add(q, layer='surface', surface=kind, source='plan')
        if kind == 'rubber':
            for q in extra_rubber:
                add(q, layer='surface', surface='rubber', source='merge')
    for g in ariq:
        add(g, layer='water', name='Канал Салар', source='existing')
    for g in kopriks:
        add(g, layer='bridge', source='existing')
    obj_fps = {id(o['fp']) for o in objects + unnamed if o['fp'] is not None} | set(merged_pieces)
    for k in ('building', 'attraction', 'playground'):
        for p in kinds[k]:
            if id(p) not in obj_fps and not any(p.contains(Point(xy)) for xy in DROP_AT):
                named = next((v for xy, v in NAME_AT.items() if k == 'building' and p.contains(Point(xy))), None)
                if named:  # explication.py → NAME_AT: nomsiz binoga nom, kategoriya, rang
                    name, cat, color = named
                    add(p, layer=k, name=name, category=cat, height=HEIGHT_DEFAULT, color=color, source='plan')
                    print(f'✓ Nomsiz bino → {name}')
                else:
                    add(p, layer=k, source='plan')
    for name, g in extra_bld:
        num = OLD_BUILDINGS[name]
        if num and any(o['num'] == num and o['fp'] is not None for o in objects):
            continue
        if num:
            o = next((o for o in objects if o['num'] == num), None)
            if o:
                o['fp'] = g
                continue
        add(g, layer='building', name=name, height=OLD_HEIGHT.get(name, HEIGHT_DEFAULT), source='existing')
    for num, g in parking:
        o = next(o for o in objects if o['num'] == num)
        o['fp'] = g
    for o in objects + unnamed:
        layer = {'fountain': 'fountain', 'entrance': 'entrance'}.get(o['kind'], o['kind'])
        props = dict(layer=layer, num=o['num'], name=o['name'], category=o['category'], source='plan')
        if o['kind'] == 'building':
            props['height'] = HEIGHT.get(o['num'], HEIGHT_DEFAULT)
            color = next((v[2] for xy, v in NAME_AT.items() if o['fp'] is not None and o['fp'].contains(Point(xy))), None)
            if color:  # explication.py → NAME_AT: raqamli bino faqat rang oladi
                props['color'] = color
        add(o['fp'] if o['fp'] is not None else o['at'], **props)
        if o['fp'] is not None:  # yozuv nuqtasi ham kerak (pin uchun)
            pass
    for l in paths:
        add(l, layer='path', source='plan')
    if entrance:
        add(entrance['basin'], layer='fountain_basin', num='9', radius=round(entrance['r'], 2), source='plan')
        for b in entrance['beds']:
            add(b, layer='bed', source='plan')

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / 'genplan.geojson'
    out.write_text(json.dumps({'type': 'FeatureCollection', 'features': feats}, ensure_ascii=False, separators=(',', ':')),
                   encoding='utf8')
    print(f'→ {out.relative_to(ROOT)} ({len(feats)} ta obyekt, {out.stat().st_size // 1024} KB)')


def entrance_fountain(fills, strokes, texts, G):
    """9 — mashina kirishidagi fontan: maydon (qora/qizil chiziqlar yopgan poligon), gulzorlar (to'q sariq kontur),
    sakkiz qirrali hovuz (markazi — halqadagi 4 ta och jigarrang bo'lak o'rtasi)."""
    t9 = next((t for t in texts if t['t'].strip() == '9' and t['c'] == (255, 0, 0) and t['h'] > 15), None)
    if not t9:
        return None
    lab = pt_to_m(Point(t9['x'], t9['y']), G)
    segs = [q for q in parts(pt_to_m(fills.get((221, 165, 110), Polygon()), G)) if q.distance(lab) < 25 and q.area < 10]
    if len(segs) < 3:
        return None
    cx = sum(q.centroid.x for q in segs) / len(segs)
    cy = sum(q.centroid.y for q in segs) / len(segs)
    center = Point(cx, cy)
    ring_r = sum(q.centroid.distance(center) for q in segs) / len(segs)
    r = ring_r + 0.9  # plandagi sakkiz qirrali tashqi chegara halqa bo'laklaridan ~0.9 m tashqarida
    basin = Polygon([(cx + r * math.cos(math.pi / 8 + k * math.pi / 4), cy + r * math.sin(math.pi / 8 + k * math.pi / 4))
                     for k in range(8)])
    near = lambda key: [m for m in (pt_to_m(l, G) for l in strokes.get(key, [])) if m.distance(center) < 45]
    beds = [b for b in polygonize(unary_union(near(((255, 63, 0), 24.0)))) if 20 < b.area < 200]
    lines = near(((0, 0, 0), 12.0)) + near(((0, 0, 0), 24.0)) + near(((255, 0, 0), 12.0)) + near(((255, 0, 0), 24.0))
    lines += near(((0, 255, 255), 12.0))  # janubiy cheti — havorang chiziq
    plazas = [q for q in polygonize(unary_union(lines)) if 800 < q.area < 6000 and Polygon(q.exterior).contains(center)]
    if not plazas:
        return None
    return dict(center=center, r=r, basin=basin, beds=beds, plaza=plazas[0])


def centerlines(paving, step=0.6, min_half=0.6, spur=6.0):
    """Yo'l yuzasining medial o'qi: chegara nuqtalarining Voronoi qirralari, chegaradan uzoq qismlari."""
    pts = []
    for p in parts(paving):
        for ring in [p.exterior, *p.interiors]:
            n = max(4, int(ring.length / step))
            pts += [ring.interpolate(i / n, normalized=True) for i in range(n)]
    edges = voronoi_polygons(MultiPoint(pts), only_edges=True)
    inner = paving.buffer(-min_half)
    keep = [e for e in getattr(edges, 'geoms', [edges]) if inner.contains(e)]
    net = linemerge(unary_union(keep))
    lines = list(getattr(net, 'geoms', [net]))
    # Kalta "tukchalar"ni (bir uchi ochiq, qisqa) bir necha marta kesamiz
    for _ in range(4):
        deg = defaultdict(int)
        key = lambda c: (round(c[0], 2), round(c[1], 2))
        for l in lines:
            deg[key(l.coords[0])] += 1
            deg[key(l.coords[-1])] += 1
        lines = [l for l in lines if not (l.length < spur and (deg[key(l.coords[0])] == 1 or deg[key(l.coords[-1])] == 1))]
        net = linemerge(unary_union(lines))
        lines = list(getattr(net, 'geoms', [net]))
    return [smooth(simplify(l, 0.5)) for l in lines if l.length > 0.5]


def smooth(line, iterations=2):
    """Chaikin silliqlash: Voronoi o'qining mayda "titrashi"ni yo'qotadi, uchlar (tutashgan joylar) qimirlamaydi."""
    pts = list(line.coords)
    for _ in range(iterations):
        if len(pts) < 3:
            break
        out = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            out += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]),
                    (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        out.append(pts[-1])
        pts = out
    return LineString(pts)


if __name__ == '__main__':
    main()

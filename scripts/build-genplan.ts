/**
 * data/genplan/genplan.geojson → src/map/park.json
 * Ishga tushirish: npm run build:genplan   (avval: python scripts/genplan/extract.py)
 *
 * Gen plandagi aniq shakllar ishlatiladi: yo'l yuzasi plandagidek (chiziq + kenglik emas),
 * marshrut grafi — yo'l yuzasining markaz chiziqlari (extract.py hisoblaydi).
 * Attraksionlar hozircha plandagi maydoncha shaklidagi quti (attractions.tsx → AttractionBox);
 * Blender modeli tayyor bo'lsa, ATTRACTION_MODELS ga qo'shiladi.
 */
import fs from 'node:fs';
import path from 'node:path';
import * as turf from '@turf/turf';
import type { Feature, FeatureCollection, Geometry, MultiPolygon, Point, Polygon, Position, LineString } from 'geojson';
import { ATTRACTION_SIZES, KASSA, type AttractionSize, type Category } from '../src/map/config';
import { project, type XY } from '../src/map/projection';
import type { Area, Attraction, Bridge, Building, MultiPoly, ParkData, Poi, Poly } from '../src/map/types';
import { distToBoundary, distToPoly, inPoly } from '../src/map/geo';

const ROOT = path.resolve(import.meta.dirname, '..');
const SRC = path.join(ROOT, 'data/genplan/genplan.geojson');
const OUT = path.join(ROOT, 'src/map/park.json');

interface Props {
  layer: string;
  num?: string | null;
  name?: string;
  category?: Category | null;
  height?: number;
  radius?: number;
  source?: string;
}
const fc: FeatureCollection<Polygon | MultiPolygon | LineString | Point, Props> = JSON.parse(fs.readFileSync(SRC, 'utf8'));
const layer = (l: string) => fc.features.filter((f) => f.properties.layer === l);

const r2 = (v: number) => Math.round(v * 100) / 100;
const P = (c: Position): XY => {
  const [x, y] = project(c);
  return [r2(x), r2(y)];
};
const toPoly = (coords: Position[][]): Poly => coords.map((ring) => ring.map(P));
type PolyFeature = Feature<Polygon | MultiPolygon>;
const toMulti = (f: PolyFeature | null): MultiPoly =>
  !f ? [] : f.geometry.type === 'Polygon' ? [toPoly(f.geometry.coordinates)] : f.geometry.coordinates.map(toPoly);
const polysOf = (f: Feature): Poly[] =>
  f.geometry.type === 'Polygon' ? [toPoly((f.geometry as Polygon).coordinates)]
    : f.geometry.type === 'MultiPolygon' ? (f.geometry as MultiPolygon).coordinates.map(toPoly) : [];
const unionAll = (fs: PolyFeature[]): PolyFeature | null =>
  fs.length === 0 ? null : fs.length === 1 ? fs[0] : turf.union(turf.featureCollection(fs));
const minus = (a: PolyFeature | null, b: PolyFeature | null): PolyFeature | null =>
  !a ? null : !b ? a : turf.difference(turf.featureCollection([a, b]));
const isPoly = (f: Feature<Geometry, Props>): f is Feature<Polygon | MultiPolygon, Props> => f.geometry.type === 'Polygon' || f.geometry.type === 'MultiPolygon';

const area = (poly: Poly): number => {
  let a = 0;
  const r = poly[0];
  for (let i = 0; i < r.length - 1; i++) a += r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1];
  return Math.abs(a) / 2 - poly.slice(1).reduce((s, h) => s + area([h]), 0);
};
const bbox = (poly: Poly) => {
  const xs = poly[0].map((p) => p[0]), ys = poly[0].map((p) => p[1]);
  return { minX: Math.min(...xs), minY: Math.min(...ys), maxX: Math.max(...xs), maxY: Math.max(...ys) };
};
/** Pin nuqtasi: poligon ichidagi, chegaradan eng uzoq nuqta (taxminan) */
const anchorOf = (poly: Poly): XY => {
  const b = bbox(poly);
  const step = Math.max(0.5, Math.min(b.maxX - b.minX, b.maxY - b.minY) / 20);
  let best: XY = poly[0][0], bd = -1;
  for (let x = b.minX; x <= b.maxX; x += step) {
    for (let y = b.minY; y <= b.maxY; y += step) {
      if (!inPoly([x, y], poly)) continue;
      const d = distToBoundary([x, y], poly);
      if (d > bd) { bd = d; best = [r2(x), r2(y)]; }
    }
  }
  return best;
};

// ---------- Chegara va yer ----------
const boundaryF = layer('boundary')[0] as Feature<Polygon>;
const ground: Poly = [toPoly(boundaryF.geometry.coordinates)[0]];
const bounds = bbox(ground);

// ---------- Suv: eng kattasi — Hovuz (baliqlar shu yerda), kanal — Ariq, sharqdagi basseynlar — Basseyn ----------
const waterF = layer('water').filter(isPoly);
const waterAreas: Area[] = [];
{
  const sized = waterF.map((f) => ({ f, polys: polysOf(f), a: turf.area(f) })).sort((a, b) => b.a - a.a);
  const pondCenter = sized[0] ? turf.centroid(sized[0].f).geometry.coordinates : [0, 0];
  let pools = 0, ponds = 0;
  sized.forEach(({ f, polys }, i) => {
    let name: string;
    if (f.properties.name === 'Канал Салар') name = 'Ariq';
    else if (i === 0) name = 'Hovuz';
    // Basseynlar majmuasi — ko'ldan sharqda (taxminan 120 m dan uzoq)
    else if (turf.distance(turf.centroid(f), turf.point(pondCenter), { units: 'meters' }) > 120 &&
      P(turf.centroid(f).geometry.coordinates)[0] > P(pondCenter)[0]) name = 'Basseyn';
    else name = 'Suv';
    const n = name === 'Basseyn' ? ++pools : name === 'Suv' ? ++ponds : 1;
    polys.forEach((poly, k) => waterAreas.push({ id: `${name.toLowerCase()}-${n}${k ? `-${k}` : ''}`, name, poly }));
  });
}
const waterUnion = unionAll(waterF);
const groundCut: MultiPoly = toMulti(minus(boundaryF as PolyFeature, waterUnion));

// ---------- Yo'l va maydonlar (plitka) ----------
const roadsF = unionAll([...layer('paving'), ...layer('plaza')].filter(isPoly));
const roads = toMulti(roadsF);

// ---------- Ko'priklar ----------
const bridges: Bridge[] = layer('bridge').map((f, i) => ({
  id: `bridge-${i + 1}`,
  line: (f.geometry as LineString).coordinates.map(P),
  width: 3,
}));

// ---------- Obyektlar ----------
const pois: Poi[] = [];
const buildings: Building[] = [];
const parking: Area[] = [];
const playgrounds: Area[] = [];
const attractions: Attraction[] = [];
// Bir raqam planda bir necha joyda yozilgan bo'lishi mumkin ("Сладкий домик (2 шт.)", 69.1) — id noyob bo'lsin
const usedIds = new Set<string>();
const slug = (f: Feature<Geometry, Props>, i: number) => {
  const base = f.properties.num ? `n${f.properties.num.replace('.', '-')}` : `${f.properties.layer}-${i + 1}`;
  let id = base;
  for (let k = 2; usedIds.has(id); k++) id = `${base}-${k}`;
  usedIds.add(id);
  return id;
};

// Bir xil nomdagilar (Французский домик x8) — yorliqqa raqami qo'shiladi
const nameCount = new Map<string, number>();
for (const f of fc.features) if (f.properties.name && f.properties.num) nameCount.set(f.properties.name, (nameCount.get(f.properties.name) ?? 0) + 1);
const labelOf = (p: Props) => (p.name && (nameCount.get(p.name) ?? 0) > 1 && p.num ? `${p.name} (${p.num})` : p.name ?? '');

/** Attraksion o'lcham sinfi — maydoncha diametri bo'yicha */
const sizeFor = (d: number): AttractionSize => (d <= 7 ? 1 : d <= 14 ? 2 : d <= 24 ? 3 : 4);
/** Plandagi aniq balandlik (eksplikatsiyada berilgan) */
const HEIGHT_OVERRIDE: Record<string, number> = { '40': 38 };
/** Shakli planda chizilmagan attraksion uchun standart quti, m */
const DEFAULT_BOX = 6;

const pending: { props: Props; id: string; anchor: XY; elevation: number }[] = [];
fc.features.forEach((f, i) => {
  const p = f.properties;
  const id = slug(f, i);
  const polys = polysOf(f);
  const poly = polys.sort((a, b) => area(b) - area(a))[0];
  if (!['building', 'parking', 'playground', 'attraction', 'fountain', 'entrance'].includes(p.layer)) return;
  const at: XY = f.geometry.type === 'Point' ? P((f.geometry as Point).coordinates) : anchorOf(poly);
  switch (p.layer) {
    case 'building': {
      const h = p.height ?? 3.5;
      polys.forEach((pp, k) => buildings.push({ id: k ? `${id}-${k}` : id, name: p.name ?? 'Bino', poly: pp, height: h }));
      if (p.category && p.name) pending.push({ props: p, id, anchor: at, elevation: h });
      break;
    }
    case 'parking':
      if (poly) parking.push({ id, name: p.name ?? 'Parking', poly });
      pending.push({ props: { ...p, category: 'parking' }, id, anchor: at, elevation: 0.3 });
      break;
    case 'playground':
      polys.forEach((pp, k) => playgrounds.push({ id: k ? `${id}-${k}` : id, name: p.name ?? 'Maydoncha', poly: pp }));
      if (p.name) pending.push({ props: p, id, anchor: at, elevation: 0.3 });
      break;
    case 'attraction': {
      let footprint: Poly;
      if (poly) footprint = poly;
      else {
        const h = DEFAULT_BOX / 2;
        footprint = [[[at[0] - h, at[1] - h], [at[0] + h, at[1] - h], [at[0] + h, at[1] + h], [at[0] - h, at[1] + h], [at[0] - h, at[1] - h]]];
      }
      const d = 2 * Math.sqrt(area(footprint) / Math.PI);
      const size = sizeFor(d);
      const height = p.num && HEIGHT_OVERRIDE[p.num] ? HEIGHT_OVERRIDE[p.num] : null;
      attractions.push({ id, name: p.name ?? 'Аттракцион', at, size, bearing: 0, height, num: p.num ?? null, footprint });
      pending.push({ props: { ...p, category: p.category ?? 'fun' }, id, anchor: at, elevation: (height ?? ATTRACTION_SIZES[size].height) + 1 });
      break;
    }
    case 'fountain':
    case 'entrance':
      pending.push({ props: p, id, anchor: at, elevation: 0.5 });
      break;
  }
});

// ---------- Marshrut grafi: markaz chiziqlari, umumiy uchlar bitta tugun ----------
const nodes: XY[] = [];
const grid = new Map<string, number[]>();
const CELL = 1;
const SNAP = 0.4;
function nodeId(p: XY): number {
  const gx = Math.floor(p[0] / CELL), gy = Math.floor(p[1] / CELL);
  for (let dx = -1; dx <= 1; dx++)
    for (let dy = -1; dy <= 1; dy++)
      for (const id of grid.get(`${gx + dx},${gy + dy}`) ?? [])
        if (Math.hypot(nodes[id][0] - p[0], nodes[id][1] - p[1]) < SNAP) return id;
  nodes.push([r2(p[0]), r2(p[1])]);
  const key = `${gx},${gy}`;
  grid.set(key, [...(grid.get(key) ?? []), nodes.length - 1]);
  return nodes.length - 1;
}
const edgeMap = new Map<string, [number, number, number]>();
for (const f of layer('path')) {
  const pts = (f.geometry as LineString).coordinates.map(P);
  for (let k = 0; k < pts.length - 1; k++) {
    const a = nodeId(pts[k]), b = nodeId(pts[k + 1]);
    if (a === b) continue;
    const key = a < b ? `${a}-${b}` : `${b}-${a}`;
    if (!edgeMap.has(key)) edgeMap.set(key, [a, b, r2(Math.hypot(nodes[a][0] - nodes[b][0], nodes[a][1] - nodes[b][1]))]);
  }
}
// Ko'priklar ham graf qismi: uchlari eng yaqin markaz chizig'i tuguniga ulanadi
for (const b of bridges) {
  const ids = b.line.map(nodeId);
  for (let k = 0; k < ids.length - 1; k++) {
    const [a, c] = [ids[k], ids[k + 1]];
    edgeMap.set(`${a}-${c}`, [a, c, r2(Math.hypot(nodes[a][0] - nodes[c][0], nodes[a][1] - nodes[c][1]))]);
  }
  for (const end of [ids[0], ids[ids.length - 1]]) {
    let best = -1, bd = Infinity;
    nodes.forEach((n, j) => {
      if (ids.includes(j)) return;
      const d = Math.hypot(n[0] - nodes[end][0], n[1] - nodes[end][1]);
      if (d < bd) { bd = d; best = j; }
    });
    if (best >= 0 && bd < 15) edgeMap.set(`${end}-${best}`, [end, best, r2(bd)]);
  }
}
const edges = [...edgeMap.values()];
const adj = nodes.map(() => [] as number[]);
for (const [a, b] of edges) { adj[a].push(b); adj[b].push(a); }
const comp = new Array(nodes.length).fill(-1);
const compSizes: number[] = [];
for (let s = 0; s < nodes.length; s++) {
  if (comp[s] !== -1) continue;
  const stack = [s];
  comp[s] = compSizes.length;
  let size = 0;
  while (stack.length) {
    const v = stack.pop()!;
    size++;
    for (const w of adj[v]) if (comp[w] === -1) { comp[w] = compSizes.length; stack.push(w); }
  }
  compSizes.push(size);
}
const mainComp = compSizes.indexOf(Math.max(...compSizes));
console.log(`✓ Graf: ${nodes.length} tugun, ${edges.length} qirra, ${compSizes.length} komponent (asosiysi ${compSizes[mainComp]} tugun)`);
const nearestNode = (p: XY) => {
  let best = -1, bd = Infinity;
  nodes.forEach((n, i) => {
    if (comp[i] !== mainComp) return;
    const d = Math.hypot(n[0] - p[0], n[1] - p[1]);
    if (d < bd) { bd = d; best = i; }
  });
  return best;
};

for (const { props, id, anchor, elevation } of pending) {
  if (!props.category || !props.name) continue;
  pois.push({ id, name: props.name, label: labelOf(props), category: props.category, anchor, elevation, node: nearestNode(anchor), num: props.num ?? null });
}

// Kassalar (config.ts → KASSA): plan raqami yonida (`near`) yoki aniq koordinatada (`lonLat`)
for (const k of KASSA) {
  const base = k.near ? pois.find((p) => p.num === k.near) : null;
  const anchor: XY | null = k.lonLat ? P(k.lonLat) : base ? [r2(base.anchor[0] + 3), r2(base.anchor[1] - 3)] : null;
  if (!anchor) { console.warn(`⚠ Kassa "${k.label}": joyi topilmadi (near: ${k.near})`); continue; }
  pois.push({ id: k.id, name: k.label, label: k.label, category: 'kassa', anchor, elevation: 0.5, node: nearestNode(anchor),
    hours: k.hours, info: k.info });
}
if (KASSA.length) console.log(`✓ Kassalar: ${pois.filter((p) => p.category === 'kassa').length}`);

// ---------- Daraxtlar: maysazorlarga, yo'l/bino/attraksiondan uzoqda (seed — har safar bir xil) ----------
let seed = 20261123;
const rand = () => {
  seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
  let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};
const lawns = layer('lawn').flatMap(polysOf);
const blockers: { poly: Poly; gap: number; box: ReturnType<typeof bbox> }[] = [
  ...roads.map((poly) => ({ poly, gap: 2 })),
  ...waterAreas.map((a) => ({ poly: a.poly, gap: 2 })),
  ...buildings.map((b) => ({ poly: b.poly, gap: 2.5 })),
  ...attractions.map((a) => ({ poly: a.footprint!, gap: 2.5 })),
  ...playgrounds.map((a) => ({ poly: a.poly, gap: 1 })),
  ...parking.map((a) => ({ poly: a.poly, gap: 1.5 })),
].map((b) => ({ ...b, box: bbox(b.poly) }));
const TREE_SPACING = 9; // m, daraxtlar orasidagi taxminiy masofa (mobil uchun soni cheklangan)
const trees: [number, number, number][] = [];
for (const lawn of lawns) {
  const b = bbox(lawn);
  const target = Math.floor(area(lawn) / (TREE_SPACING * TREE_SPACING));
  let tries = target * 12;
  let placed = 0;
  while (placed < target && tries-- > 0) {
    const p: XY = [b.minX + rand() * (b.maxX - b.minX), b.minY + rand() * (b.maxY - b.minY)];
    if (!inPoly(p, lawn) || distToBoundary(p, lawn) < 1.2) continue;
    if (blockers.some((k) => p[0] > k.box.minX - k.gap && p[0] < k.box.maxX + k.gap && p[1] > k.box.minY - k.gap &&
      p[1] < k.box.maxY + k.gap && (inPoly(p, k.poly) || distToPoly(p, k.poly) < k.gap))) continue;
    if (trees.some((t) => Math.hypot(t[0] - p[0], t[1] - p[1]) < TREE_SPACING * 0.6)) continue;
    trees.push([r2(p[0]), r2(p[1]), r2(0.8 + rand() * 0.5)]);
    placed++;
  }
}
console.log(`✓ Daraxtlar: ${trees.length}`);

// ---------- Fonuslar: markaz chiziqlari bo'ylab har ~30 m, yo'l chetiga (maysa tomonga) ----------
const LAMP_EVERY = 30;
const lamps: [number, number][] = [];
for (const f of layer('path')) {
  const line = f as Feature<LineString>;
  const len = turf.length(line, { units: 'meters' });
  if (len < 12) continue;
  for (let d = LAMP_EVERY / 2; d < len; d += LAMP_EVERY) {
    const c = P(turf.along(line, d, { units: 'meters' }).geometry.coordinates);
    const road = roads.find((r) => inPoly(c, r));
    if (!road) continue;
    // eng yaqin chet nuqtasi va undan 0.4 m tashqariga
    let best: XY | null = null, bd = Infinity;
    for (const ring of road) {
      for (let k = 0; k < ring.length - 1; k++) {
        const [a, b] = [ring[k], ring[k + 1]];
        const dx = b[0] - a[0], dy = b[1] - a[1];
        const L = dx * dx + dy * dy || 1;
        const t = Math.max(0, Math.min(1, ((c[0] - a[0]) * dx + (c[1] - a[1]) * dy) / L));
        const q: XY = [a[0] + t * dx, a[1] + t * dy];
        const dd = Math.hypot(q[0] - c[0], q[1] - c[1]);
        if (dd < bd) { bd = dd; best = q; }
      }
    }
    if (!best || bd > 6) continue; // keng maydon o'rtasiga fonus qo'ymaymiz
    const ux = (best[0] - c[0]) / (bd || 1), uy = (best[1] - c[1]) / (bd || 1);
    const p: XY = [r2(best[0] + ux * 0.4), r2(best[1] + uy * 0.4)];
    if (lamps.some((l) => Math.hypot(l[0] - p[0], l[1] - p[1]) < LAMP_EVERY * 0.5)) continue;
    if (waterAreas.some((w) => inPoly(p, w.poly))) continue;
    lamps.push(p);
  }
}
console.log(`✓ Fonuslar: ${lamps.length}`);

// ---------- Fontanlar va gulzorlar ----------
const fountains: NonNullable<ParkData['fountains']> = layer('fountain_basin').filter(isPoly).map((f, i) => {
  const ring = polysOf(f)[0][0];
  const at: XY = [r2(ring.slice(0, -1).reduce((s, p) => s + p[0], 0) / (ring.length - 1)),
    r2(ring.slice(0, -1).reduce((s, p) => s + p[1], 0) / (ring.length - 1))];
  return { id: `fountain-${f.properties.num ?? i + 1}`, num: f.properties.num ?? null, at, r: Number(f.properties.radius ?? 5) };
});
const beds = layer('bed').flatMap(polysOf);
console.log(`✓ Fontanlar: ${fountains.length}, gulzorlar: ${beds.length}`);

// ---------- Natija ----------
const roadKm = edges.reduce((s, e) => s + e[2], 0) / 1000;
const data: ParkData = {
  bounds,
  ground,
  groundCut,
  water: waterAreas,
  roads,
  bridges,
  parking,
  playgrounds,
  buildings,
  attractions,
  trees,
  lamps,
  fountains,
  beds,
  graph: { nodes, edges },
  pois,
  stats: {
    roadKm: Math.round(roadKm * 100) / 100,
    areaHa: Math.round(turf.area(boundaryF) / 1000) / 10,
    objects: pois.length,
  },
};
fs.writeFileSync(OUT, JSON.stringify(data));
console.log(`✓ ${path.relative(ROOT, OUT)}: ${(fs.statSync(OUT).size / 1024).toFixed(0)} KB — ` +
  `${buildings.length} bino, ${attractions.length} attraksion, ${waterAreas.length} suv, ${pois.length} pin, ` +
  `${data.stats.areaHa} ga, yo'llar ${data.stats.roadKm} km`);

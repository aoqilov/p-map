/**
 * map.geojson → src/map/park.json
 * Ishga tushirish: npm run build:map
 *
 * 1. Snap: uzilgan yo'l uchlarini eng yaqin yo'lga yopishtiradi
 * 2. Buffer + union: chiziqlardan haqiqiy kenglikdagi bitta yo'l yuzasini quradi, suvni kesib tashlaydi
 * 3. Graf: kesishmalarda tugun qo'yib, marshrut uchun graf quradi
 * 4. Daraxtlar: bo'sh joylarga daraxt nuqtalarini sochadi
 * Hamma og'ir hisob shu yerda, brauzer faqat tayyor JSON'ni o'qiydi.
 */
import fs from 'node:fs';
import path from 'node:path';
import * as turf from '@turf/turf';
import type { Feature, FeatureCollection, LineString, MultiPolygon, Point, Polygon, Position } from 'geojson';
import {
  ATTRACTION_SIZES, BUILDING_LOOKS, CONSTRUCTION, DEFAULT_BEARING, ENTRANCES, OBJECTS, PARKING_LAYOUT, POOL_AREA, ROAD_WIDTH, SNAP_METERS, STREET_LAMP_ROADS, WATER, WATER_PLANTS,
  type AttractionSize,
  PLAYGROUND, PLAYGROUND_RIDES,
} from '../src/map/config';
import { project, unproject, type XY } from '../src/map/projection';
const unprojectXY = (p: XY) => unproject(p);
import type { Area, Attraction, Building, MultiPoly, ParkData, ParkingLayout, Poi, Poly } from '../src/map/types';
import { distToBoundary, distToPoly, distToSeg, inPoly } from '../src/map/geo';
import { createRouter } from '../src/map/route';
import { layoutParking } from './parking-layout';

const ROOT = path.resolve(import.meta.dirname, '..');
const SRC = path.join(ROOT, 'data/map.geojson');
const DRAFT = path.join(ROOT, 'data/roads-draft.geojson');
const OUT = path.join(ROOT, 'src/map/park.json');
const LAMPS = path.join(ROOT, 'data/lamps.geojson');
const PLANTS = path.join(ROOT, 'data/water-plants.geojson');
const POOLS = path.join(ROOT, 'data/pools-shape.geojson');
const EXTRA = path.join(ROOT, 'data/extra-objects.geojson');
const PARKING_SHAPE = path.join(ROOT, 'data/parking-shape.geojson');

const src: FeatureCollection = JSON.parse(fs.readFileSync(SRC, 'utf8'));
const draft: FeatureCollection = fs.existsSync(DRAFT)
  ? JSON.parse(fs.readFileSync(DRAFT, 'utf8'))
  : { type: 'FeatureCollection', features: [] };

type Line = Feature<LineString, { name: string; draft?: boolean }>;
type Plaza = Feature<Polygon, { name: string }>;

const nameOf = (f: Feature) => String(f.properties?.name ?? '');
const isRoadName = (n: string) => n in ROAD_WIDTH;

// ---------- 0. Ajratish ----------
const lines: Line[] = [];
const plazas: Plaza[] = [];
const objects: { f: Feature<Polygon>; index: number }[] = [];
const points: Feature<Point, { name: string; size?: number; bearing?: number; height?: number }>[] = [];

src.features.forEach((f, index) => {
  const n = nameOf(f);
  if (f.geometry.type === 'LineString' && isRoadName(n)) lines.push(f as Line);
  else if (f.geometry.type === 'Polygon' && isRoadName(n)) plazas.push(f as Plaza);
  else if (f.geometry.type === 'Polygon' && OBJECTS[n]) objects.push({ f: f as Feature<Polygon>, index });
  else if (f.geometry.type === 'Point' && OBJECTS[n]?.kind === 'attraction') points.push(f as (typeof points)[number]);
  else console.warn(`⚠ #${index} "${n}" (${f.geometry.type}) config.ts da yo'q — o'tkazib yuborildi`);
});
// Qo'shimcha obyektlar (asl map.geojson da yo'q): data/extra-objects.geojson. "Plitka" — basseyn plitkasiga qo'shiladigan maydon
const extraSrc: FeatureCollection = fs.existsSync(EXTRA)
  ? JSON.parse(fs.readFileSync(EXTRA, 'utf8'))
  : { type: 'FeatureCollection', features: [] };
const extraPaving: Feature<Polygon>[] = [];
extraSrc.features.forEach((f, k) => {
  const n = nameOf(f);
  if (f.geometry.type !== 'Polygon') return;
  if (n === 'Plitka') extraPaving.push(f as Feature<Polygon>);
  else if (OBJECTS[n]) objects.push({ f: f as Feature<Polygon>, index: src.features.length + k });
  else console.warn(`⚠ extra-objects.geojson: "${n}" config.ts da yo'q — o'tkazib yuborildi`);
});
if (extraSrc.features.length) console.log(`✓ Qo'shimcha obyektlar: ${extraSrc.features.map(nameOf).join(', ')}`);

for (const f of draft.features) {
  if (f.geometry.type === 'LineString' && isRoadName(nameOf(f))) {
    lines.push({ ...(f as Line), properties: { name: nameOf(f), draft: true } });
  }
}
// Asl faylni o'zgartirmaslik uchun koordinatalarni nusxalaymiz
for (const l of lines) l.geometry.coordinates = l.geometry.coordinates.map((c) => [c[0], c[1]]);

// Basseyn shakllari: data/pools-shape.geojson dagi Polygon shu nomdagi suvning konturini almashtiradi (asl map.geojson o'zgarmaydi)
const poolSrc: FeatureCollection = fs.existsSync(POOLS)
  ? JSON.parse(fs.readFileSync(POOLS, 'utf8'))
  : { type: 'FeatureCollection', features: [] };
for (const f of poolSrc.features) {
  if (f.geometry.type !== 'Polygon') continue;
  const o = objects.find((x) => nameOf(x.f) === nameOf(f) && OBJECTS[nameOf(f)]?.kind === 'water');
  if (!o) continue;
  o.f = { ...o.f, geometry: f.geometry as Polygon };
  console.log(`✓ Shakl: ${nameOf(f)} — pools-shape.geojson dan`);
}

// Parking shakllari: data/parking-shape.geojson dagi Polygon shu nomdagi parkingning konturini almashtiradi (fotoga qarab);
// `of` xossali nuqta/chiziqlar — o'sha parkingning darvozasi, piyoda kirishi, binosi, soyaboni
const parkingSrc: FeatureCollection = fs.existsSync(PARKING_SHAPE)
  ? JSON.parse(fs.readFileSync(PARKING_SHAPE, 'utf8'))
  : { type: 'FeatureCollection', features: [] };
for (const f of parkingSrc.features) {
  if (f.geometry.type !== 'Polygon' || f.properties?.of) continue;
  const o = objects.find((x) => nameOf(x.f) === nameOf(f) && OBJECTS[nameOf(f)]?.kind === 'parking');
  if (!o) continue;
  o.f = { ...o.f, geometry: f.geometry as Polygon };
  console.log(`✓ Shakl: ${nameOf(f)} — parking-shape.geojson dan`);
}

// ---------- 1. Snap ----------
const rings = plazas.map((p) => turf.lineString(p.geometry.coordinates[0]));
let snapped = 0;
const unsnapped: string[] = [];
for (const line of lines) {
  const c = line.geometry.coordinates;
  for (const i of [0, c.length - 1]) {
    const pt = turf.point(c[i]);
    let best: { d: number; at: Position } | undefined;
    for (const t of [...lines, ...rings]) {
      if (t === line) continue;
      const np = turf.nearestPointOnLine(t as Feature<LineString>, pt);
      const d = turf.distance(pt, np, { units: 'meters' });
      if (!best || d < best.d) best = { d, at: np.geometry.coordinates };
    }
    if (!best) continue;
    if (best.d > 0.01 && best.d <= SNAP_METERS) {
      c[i] = best.at;
      snapped++;
    } else if (best.d > SNAP_METERS) {
      unsnapped.push(`${line.properties.name} ${i === 0 ? 'boshi' : 'oxiri'}: ${best.d.toFixed(1)} m`);
    }
  }
}
console.log(`✓ Snap: ${snapped} ta uch yopishtirildi`);
console.log(`  Ochiq qolgan uchlar (${unsnapped.length}) — kirish/parking/bino eshigi bo'lsa normal:`);
unsnapped.forEach((s) => console.log('   ·', s));

// ---------- 2. Yo'l yuzasi ----------
type PolyFeature = Feature<Polygon | MultiPolygon>;
const unionAll = (fs: PolyFeature[]): PolyFeature | null =>
  fs.length === 0 ? null : fs.length === 1 ? fs[0] : turf.union(turf.featureCollection(fs));
const minus = (a: PolyFeature | null, b: PolyFeature | null): PolyFeature | null =>
  !a ? null : !b ? a : turf.difference(turf.featureCollection([a, b]));

const bufferLine = (l: Line) =>
  turf.buffer(l, ROAD_WIDTH[l.properties.name] / 2, { units: 'meters', steps: 10 }) as PolyFeature | undefined;

const groundLines = lines.filter((l) => l.properties.name !== 'Koprik');
const base = unionAll([
  ...groundLines.filter((l) => !l.properties.draft).map(bufferLine).filter((x): x is PolyFeature => !!x),
  ...plazas,
]);
const draftSurface = unionAll(
  groundLines.filter((l) => l.properties.draft).map(bufferLine).filter((x): x is PolyFeature => !!x),
);
const water = objects.filter((o) => OBJECTS[nameOf(o.f)].kind === 'water');
const waterUnion = unionAll(water.map((w) => w.f));

const roadSurface = minus(unionAll([base, draftSurface].filter((x): x is PolyFeature => !!x)), waterUnion);
const draftOnly = minus(minus(draftSurface, base), waterUnion);

// ---------- Proyeksiya yordamchilari ----------
const r2 = (v: number) => Math.round(v * 100) / 100;
const P = (c: Position): XY => {
  const [x, y] = project(c);
  return [r2(x), r2(y)];
};
const toPoly = (coords: Position[][]): Poly => coords.map((ring) => ring.map(P));
const toMulti = (f: PolyFeature | null): MultiPoly =>
  !f ? [] : f.geometry.type === 'Polygon' ? [toPoly(f.geometry.coordinates)] : f.geometry.coordinates.map(toPoly);

// ---------- 3. Graf ----------
// Hamma hisob metrda. Har bir chiziq kesishmasida ikkala chiziqqa ham bir xil nuqta qo'shiladi.
const polylines: { pts: XY[]; plaza?: number }[] = [
  ...lines.map((l) => ({ pts: l.geometry.coordinates.map(project) })),
  ...plazas.map((p, i) => ({ pts: p.geometry.coordinates[0].map(project), plaza: i })),
];

const TOL = 0.05;
type Split = { seg: number; t: number; p: XY };
const splits: Split[][] = polylines.map(() => []);

function segIntersect(a: XY, b: XY, c: XY, d: XY): { t: number; u: number; p: XY }[] {
  const r: XY = [b[0] - a[0], b[1] - a[1]];
  const s: XY = [d[0] - c[0], d[1] - c[1]];
  const den = r[0] * s[1] - r[1] * s[0];
  const out: { t: number; u: number; p: XY }[] = [];
  if (Math.abs(den) > 1e-12) {
    const t = ((c[0] - a[0]) * s[1] - (c[1] - a[1]) * s[0]) / den;
    const u = ((c[0] - a[0]) * r[1] - (c[1] - a[1]) * r[0]) / den;
    const lr = Math.hypot(...r), ls = Math.hypot(...s);
    if (t >= -TOL / lr && t <= 1 + TOL / lr && u >= -TOL / ls && u <= 1 + TOL / ls) {
      const tc = Math.min(1, Math.max(0, t));
      out.push({ t: tc, u: Math.min(1, Math.max(0, u)), p: [a[0] + tc * r[0], a[1] + tc * r[1]] });
    }
  }
  // Uchlar boshqa segmentga juda yaqin bo'lsa (snap natijasi) — T-kesishma
  const near = (p: XY, q0: XY, q1: XY) => {
    const dx = q1[0] - q0[0], dy = q1[1] - q0[1];
    const L = dx * dx + dy * dy;
    const k = L === 0 ? 0 : Math.max(0, Math.min(1, ((p[0] - q0[0]) * dx + (p[1] - q0[1]) * dy) / L));
    return { k, d: Math.hypot(p[0] - (q0[0] + k * dx), p[1] - (q0[1] + k * dy)) };
  };
  for (const [p, isA, tp] of [[a, true, 0], [b, true, 1], [c, false, 0], [d, false, 1]] as const) {
    const m = isA ? near(p, c, d) : near(p, a, b);
    if (m.d < TOL) out.push(isA ? { t: tp, u: m.k, p: [...p] as XY } : { t: m.k, u: tp, p: [...p] as XY });
  }
  return out;
}

for (let i = 0; i < polylines.length; i++) {
  for (let j = i + 1; j < polylines.length; j++) {
    const A = polylines[i].pts, B = polylines[j].pts;
    for (let sa = 0; sa < A.length - 1; sa++) {
      for (let sb = 0; sb < B.length - 1; sb++) {
        for (const hit of segIntersect(A[sa], A[sa + 1], B[sb], B[sb + 1])) {
          splits[i].push({ seg: sa, t: hit.t, p: hit.p });
          splits[j].push({ seg: sb, t: hit.u, p: hit.p });
        }
      }
    }
  }
}

// Tugunlar: 0.15 m ichidagi nuqtalar bitta tugun
const nodes: XY[] = [];
const grid = new Map<string, number[]>();
const CELL = 0.5;
function nodeId(p: XY): number {
  const gx = Math.floor(p[0] / CELL), gy = Math.floor(p[1] / CELL);
  for (let dx = -1; dx <= 1; dx++)
    for (let dy = -1; dy <= 1; dy++)
      for (const id of grid.get(`${gx + dx},${gy + dy}`) ?? [])
        if (Math.hypot(nodes[id][0] - p[0], nodes[id][1] - p[1]) < 0.15) return id;
  nodes.push([p[0], p[1]]);
  const key = `${gx},${gy}`;
  grid.set(key, [...(grid.get(key) ?? []), nodes.length - 1]);
  return nodes.length - 1;
}

const edgeMap = new Map<string, [number, number, number]>();
const addEdge = (a: number, b: number) => {
  if (a === b) return;
  const key = a < b ? `${a}-${b}` : `${b}-${a}`;
  if (!edgeMap.has(key)) edgeMap.set(key, [a, b, r2(Math.hypot(nodes[a][0] - nodes[b][0], nodes[a][1] - nodes[b][1]))]);
};

const plazaNodes: Set<number>[] = plazas.map(() => new Set());
polylines.forEach((pl, i) => {
  const seq: number[] = [];
  for (let s = 0; s < pl.pts.length - 1; s++) {
    seq.push(nodeId(pl.pts[s]));
    splits[i]
      .filter((x) => x.seg === s)
      .sort((a, b) => a.t - b.t)
      .forEach((x) => seq.push(nodeId(x.p)));
  }
  seq.push(nodeId(pl.pts[pl.pts.length - 1]));
  for (let k = 0; k < seq.length - 1; k++) addEdge(seq[k], seq[k + 1]);
  if (pl.plaza !== undefined) seq.forEach((id) => plazaNodes[pl.plaza!].add(id));
});

// Maydonchani to'g'ridan-to'g'ri kesib o'tish: markaz ↔ kesishma tugunlari
const degree = () => {
  const deg = new Map<number, number>();
  for (const [a, b] of edgeMap.values()) {
    deg.set(a, (deg.get(a) ?? 0) + 1);
    deg.set(b, (deg.get(b) ?? 0) + 1);
  }
  return deg;
};
const deg0 = degree();
plazas.forEach((p, i) => {
  const ring = p.geometry.coordinates[0].slice(0, -1).map(project);
  const cx = ring.reduce((s, q) => s + q[0], 0) / ring.length;
  const cy = ring.reduce((s, q) => s + q[1], 0) / ring.length;
  const center = nodeId([cx, cy]);
  for (const id of plazaNodes[i]) if ((deg0.get(id) ?? 0) >= 3) addEdge(center, id);
});

const edges = [...edgeMap.values()];

// Bog'lanish komponentlari
const adj = nodes.map(() => [] as number[]);
for (const [a, b] of edges) {
  adj[a].push(b);
  adj[b].push(a);
}
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
console.log(`✓ Graf: ${nodes.length} tugun, ${edges.length} qirra, ${compSizes.length} komponent ` +
  `(asosiysi ${compSizes[mainComp]} tugun${compSizes.length > 1 ? `; qolganlari: ${compSizes.filter((_, i) => i !== mainComp).join(', ')}` : ''})`);

// ---------- 4. Obyektlar ----------
const buildings: Building[] = [];
const waterAreas: Area[] = [];
const parking: Area[] = [];
const playgrounds: Area[] = [];
let bog: Poly = [];
const pois: Poi[] = [];

const centroid = (ring: XY[]): XY => {
  // Yuza bo'yicha og'irlik markazi; botiq shakllarda ichkariga tushmasa — eng yaqin uchga yaqinlashtiramiz
  let a = 0, cx = 0, cy = 0;
  for (let i = 0; i < ring.length - 1; i++) {
    const f = ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1];
    a += f; cx += (ring[i][0] + ring[i + 1][0]) * f; cy += (ring[i][1] + ring[i + 1][1]) * f;
  }
  return [r2(cx / (3 * a)), r2(cy / (3 * a))];
};
/**
 * Pin turadigan nuqta: og'irlik markazi polygon ichida bo'lsa — o'sha. Aks holda (o'rtasida orol bor yoki botiq shakl)
 * chegaradan eng uzoq ichki nuqta — masalan, lagunda pin orol ustiga emas, suv ustiga tushadi
 */
const anchorOf = (poly: Poly): XY => {
  const c = centroid(poly[0]);
  if (inPoly(c, poly)) return c;
  const xs = poly[0].map((p) => p[0]), ys = poly[0].map((p) => p[1]);
  let best: XY = c, bd = -1;
  for (let x = Math.min(...xs); x <= Math.max(...xs); x += 0.5) {
    for (let y = Math.min(...ys); y <= Math.max(...ys); y += 0.5) {
      if (!inPoly([x, y], poly)) continue;
      const d = distToBoundary([x, y], poly);
      if (d > bd) { bd = d; best = [r2(x), r2(y)]; }
    }
  }
  return best;
};
const nearestNode = (poly: Poly | null, p: XY) => {
  let best = -1, bd = Infinity;
  nodes.forEach((n, i) => {
    if (comp[i] !== mainComp) return;
    const d = poly ? distToPoly(n, poly) : Math.hypot(n[0] - p[0], n[1] - p[1]);
    if (d < bd) { bd = d; best = i; }
  });
  return best;
};

const nameCount = new Map<string, number>();
for (const { f, index } of objects) {
  const name = nameOf(f);
  const def = OBJECTS[name];
  const poly = toPoly(f.geometry.coordinates);
  const n = (nameCount.get(name) ?? 0) + 1;
  nameCount.set(name, n);
  const id = `${name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-${n}`;
  const area: Area = { id, name, poly };

  if (def.kind === 'ground') bog = poly;
  else if (def.kind === 'water') waterAreas.push(area);
  else if (def.kind === 'parking') parking.push(area);
  else if (def.kind === 'playground') playgrounds.push(area);
  else if (def.kind === 'building') buildings.push({ ...area, height: def.height ?? 4 });

  if (def.category) {
    const total = objects.filter((o) => nameOf(o.f) === name).length;
    pois.push({
      id,
      name,
      label: total > 1 ? `${def.label} ${n}` : def.label,
      category: def.category,
      anchor: anchorOf(poly),
      elevation: def.kind === 'building' ? (def.height ?? 4) : 0.3,
      node: nearestNode(poly, [0, 0]),
    });
  }
  void index;
}

// Attraksionlar (nuqtalar): marshrut uchun eng yaqin tugun — odatda turgan maydonchasining markazi
const attractionCount = new Map<string, number>();
const attractions: Attraction[] = points.map((f) => {
  const name = f.properties.name;
  const def = OBJECTS[name];
  const at = P(f.geometry.coordinates);
  const n = (attractionCount.get(name) ?? 0) + 1;
  attractionCount.set(name, n);
  const id = `${name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-${n}`;
  const raw = Number(f.properties.size);
  const size = (raw in ATTRACTION_SIZES ? raw : 2) as AttractionSize;
  if (!(raw in ATTRACTION_SIZES)) console.warn(`⚠ "${name}": size 1–4 bo'lishi kerak (berilgan: ${f.properties.size}) — 2 olindi`);
  const bearing = Number.isFinite(Number(f.properties.bearing)) ? Number(f.properties.bearing) : DEFAULT_BEARING;
  const height = Number(f.properties.height) > 0 ? Number(f.properties.height) : null;
  const elevation = (height ?? ATTRACTION_SIZES[size].height) + 1;
  pois.push({ id, name, label: def.label, category: def.category ?? 'fun', anchor: at, elevation, node: nearestNode(null, at) });
  return { id, name, at, size, bearing, height };
});

for (const e of ENTRANCES) {
  const f = src.features[e.fromFeature] as Feature<LineString>;
  const pts = f.geometry.coordinates.map(project);
  const anchor: XY = pts.length > 10
    ? [r2(pts.reduce((s, p) => s + p[0], 0) / pts.length), r2(pts.reduce((s, p) => s + p[1], 0) / pts.length)]
    : [r2(pts[0][0]), r2(pts[0][1])];
  pois.push({ id: e.id, name: e.id, label: e.label, category: 'entrance', anchor, elevation: 0.3, node: nearestNode(null, anchor) });
}

// ---------- 5. Daraxtlar ----------
let seed = 20261016;
const rand = () => {
  seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
  let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};
const roadPolys = toMulti(roadSurface);
const blockers: { poly: Poly; gap: number }[] = [
  ...roadPolys.map((poly) => ({ poly, gap: 3 })),
  ...waterAreas.map((a) => ({ poly: a.poly, gap: 2 })),
  ...parking.map((a) => ({ poly: a.poly, gap: 1.5 })),
  ...playgrounds.map((a) => ({ poly: a.poly, gap: 1 })),
  ...buildings.map((a) => ({ poly: a.poly, gap: 2.5 })),
];
const bbox = (poly: Poly) => {
  const xs = poly[0].map((p) => p[0]), ys = poly[0].map((p) => p[1]);
  return { minX: Math.min(...xs), minY: Math.min(...ys), maxX: Math.max(...xs), maxY: Math.max(...ys) };
};
const blockerBoxes = blockers.map((b) => ({ ...b, box: bbox(b.poly) }));
// Yer plitasi = Bog' + undan chiqib turgan yo'l/parking atrofi (kirish maydoni havoda osilib qolmasligi uchun)
const bogFeature = objects.find((o) => OBJECTS[nameOf(o.f)].kind === 'ground')!.f;
const apron = unionAll([
  bogFeature,
  ...[roadSurface, ...objects.filter((o) => OBJECTS[nameOf(o.f)].kind === 'parking').map((o) => o.f)]
    .filter((x): x is PolyFeature => !!x)
    .map((f) => turf.buffer(f, 2, { units: 'meters', steps: 6 }) as PolyFeature),
]);
const apronPolys = toMulti(apron).sort((a, b) => bbox(b).maxX - bbox(b).minX - (bbox(a).maxX - bbox(a).minX));
const ground: Poly = [apronPolys[0][0]]; // faqat tashqi chegara, ichki teshiklarsiz
const bounds = bbox(ground);
// Chizish uchun: yer plitasidan suv o'rni kesib olinadi (suv yerdan pastda turadi, orollar alohida bo'lak bo'lib qoladi)
const groundCut: MultiPoly = (() => {
  const geom = apron!.geometry;
  const outers = geom.type === 'Polygon' ? [geom.coordinates[0]] : geom.coordinates.map((c) => c[0]);
  const lonSpan = (r: Position[]) => Math.max(...r.map((c) => c[0])) - Math.min(...r.map((c) => c[0]));
  const outer = outers.sort((a, b) => lonSpan(b) - lonSpan(a))[0];
  return toMulti(minus(turf.polygon([outer]), waterUnion));
})();

// Basseynlar majmuasi plitkasi: basseynlarni o'rab olgan qavariq maydon + zaxira, suv va binolar o'rni teshik
const deckFeature: PolyFeature | null = (() => {
  const pools = objects.filter((o) => POOL_AREA.pools.includes(nameOf(o.f))).map((o) => o.f);
  if (!pools.length) return null;
  const hull = turf.convex(turf.featureCollection(pools.flatMap((f) => f.geometry.coordinates[0].map((c) => turf.point(c)))));
  if (!hull) return null;
  let d: PolyFeature | null = turf.buffer(hull, POOL_AREA.margin, { units: 'meters', steps: 8 }) as PolyFeature;
  if (extraPaving.length) d = unionAll([d!, ...extraPaving]);
  d = minus(d, waterUnion);
  // Suv ichidagi oroldagi bino (lagun bari) plitka ustida turadi — uni teshmaymiz
  const onIsland = (f: Feature<Polygon>) => {
    const c = toPoly(f.geometry.coordinates)[0][0];
    return waterAreas.some((a) => a.poly.slice(1).some((h) => inPoly(c, [h])));
  };
  // Plitka devorgacha boradi (oraliqda maysa tasmasi qolmasin)
  const blds = unionAll(objects.filter((o) => OBJECTS[nameOf(o.f)].kind === 'building' && !onIsland(o.f))
    .map((o) => turf.buffer(o.f, 0.1, { units: 'meters', steps: 4 }) as PolyFeature));
  d = minus(d, blds);
  return d && apron ? turf.intersect(turf.featureCollection([d, apron])) as PolyFeature | null : d; // park chegarasidan chiqmasin
})();
const deck: MultiPoly = toMulti(deckFeature);
if (deck.length) console.log(`✓ Basseyn plitkasi: ${Math.round(turf.area(deckFeature!))} m²`);

// ---------- 4a. Qurilish maydonlari ----------
// To'siq hududi: bino + `fenceMargin`, yo'l va suvdan 0.8 m qochadi, park ichida qoladi. Ichida daraxt va fonus bo'lmaydi
const construction: ParkData['construction'] = {};
{
  const roadBuf = roadSurface ? turf.buffer(roadSurface, 0.8, { units: 'meters', steps: 4 }) as PolyFeature : null;
  const waterBuf = waterUnion ? turf.buffer(waterUnion, 1, { units: 'meters', steps: 4 }) as PolyFeature : null;
  for (const { f } of objects) {
    const bId = buildings.find((x) => x.name === nameOf(f) && JSON.stringify(x.poly) === JSON.stringify(toPoly(f.geometry.coordinates)))?.id;
    if (!bId || !CONSTRUCTION[bId]) continue;
    let z: PolyFeature | null = turf.buffer(f, CONSTRUCTION[bId].fenceMargin, { units: 'meters', steps: 2 }) as PolyFeature;
    z = minus(minus(z, roadBuf), waterBuf);
    // Qo'shni binolarga (masalan, Banya) tegmasin
    const others = unionAll(objects.filter((o) => o.f !== f && OBJECTS[nameOf(o.f)].kind === 'building')
      .map((o) => turf.buffer(o.f, 1.2, { units: 'meters', steps: 2 }) as PolyFeature));
    z = minus(z, others);
    if (z && apron) z = turf.intersect(turf.featureCollection([z, apron])) as PolyFeature | null;
    const parts = toMulti(z);
    const inside = parts.find((pp) => inPoly(toPoly(f.geometry.coordinates)[0][0], pp)) ?? parts[0];
    if (!inside) continue;
    // Yo'l bo'yidagi mayda tishlarni tekislaymiz (to'siq to'g'ri chiziq bo'lib tursin)
    const simple = turf.simplify(turf.polygon(inside.map((r) => r.map((p) => [p[0], p[1]]))), { tolerance: 0.6, highQuality: true });
    construction[bId] = { zone: [simple.geometry.coordinates[0].map(([x, y]) => [r2(x), r2(y)] as XY)] };
    console.log(`✓ Qurilish maydoni: ${bId} — to'siq ${Math.round(turf.length(turf.lineString(construction[bId].zone[0].map(unprojectXY)), { units: 'meters' }))} m`);
  }
}

// ---------- 4b. Parking ichi ----------
// Kontur, darvoza, piyoda kirish, bino, soyabon — data/parking-shape.geojson; o'lchamlar — config.ts → PARKING_LAYOUT
const parkingLayout: Record<string, ParkingLayout> = {};
for (const c of Object.values(construction)) blockerBoxes.push({ poly: c.zone, gap: 1, box: bbox(c.zone) });
const parkingTrees: [number, number, number][] = [];
const parkingLamps: XY[] = [];
for (const a of parking) {
  const cfg = PARKING_LAYOUT[a.name];
  if (!cfg) continue;
  const extras = parkingSrc.features.filter((f) => f.properties?.of === a.name);
  const one = (n: string) => extras.find((f) => nameOf(f) === n);
  const leftOf = (p: XY, q: XY): XY => {
    const L = Math.hypot(q[0] - p[0], q[1] - p[1]);
    return [-(q[1] - p[1]) / L, (q[0] - p[0]) / L];
  };
  /** a→b chiziq: chuqurlik chap tomonga. `inward` — chap tomon parking ichi bo'lsin (aks holda tashqari) */
  const orient = (f: Feature | undefined, inward: boolean): [XY, XY] | null => {
    if (f?.geometry.type !== 'LineString') return null;
    const c = (f.geometry as LineString).coordinates;
    let [p, q] = [P(c[0]), P(c[c.length - 1])];
    const n = leftOf(p, q);
    const m: XY = [(p[0] + q[0]) / 2 + n[0], (p[1] + q[1]) / 2 + n[1]];
    if (inPoly(m, a.poly) !== inward) [p, q] = [q, p];
    return [p, q];
  };
  const gateF = one('Darvoza'), pedF = one('Piyoda');
  const bld = orient(one('Bino'), false), can = orient(one('Soyabon'), true);
  const gate = gateF?.geometry.type === 'Point'
    ? {
      at: P((gateF.geometry as Point).coordinates),
      rot: Math.round(((90 - Number(gateF.properties?.bearing ?? 0)) * Math.PI / 180) * 1000) / 1000,
      width: Number(gateF.properties?.width ?? 8),
    }
    : null;
  const { layout, trees: t, lamps: l } = layoutParking({
    poly: a.poly,
    gate,
    ped: pedF?.geometry.type === 'Point' ? P((pedF.geometry as Point).coordinates) : null,
    building: bld ? { a: bld[0], b: bld[1], depth: Number(one('Bino')!.properties?.depth ?? 4.5), height: Number(one('Bino')!.properties?.height ?? 3.2) } : null,
    canopy: can ? { a: can[0], b: can[1], depth: Number(one('Soyabon')!.properties?.depth ?? 5.5) } : null,
    cfg,
  });
  parkingLayout[a.id] = layout;
  parkingTrees.push(...t);
  parkingLamps.push(...l);
  // Budka va bino ostida daraxt o'smasin
  if (layout.kiosk) {
    const [kx, ky] = layout.kiosk;
    const fp: Poly = [[[kx - 1.5, ky - 1.5], [kx + 1.5, ky - 1.5], [kx + 1.5, ky + 1.5], [kx - 1.5, ky + 1.5], [kx - 1.5, ky - 1.5]]];
    blockerBoxes.push({ poly: fp, gap: 1.5, box: bbox(fp) });
  }
  if (layout.building) {
    const { a: p, b: q, depth } = layout.building;
    const n = leftOf(p, q);
    const fp: Poly = [[p, q, [q[0] + n[0] * depth, q[1] + n[1] * depth], [p[0] + n[0] * depth, p[1] + n[1] * depth], p]];
    blockerBoxes.push({ poly: fp, gap: 2, box: bbox(fp) });
  }
  console.log(`✓ ${a.name}: ${layout.stalls.length} joy, ${layout.cars.length} mashina, ${layout.islands.length} orolcha, ` +
    `${layout.gate ? 'darvoza' : ''}${layout.kiosk ? ', budka' : ''}${layout.ped ? ', piyoda kirish' : ''}${layout.building ? ', bino' : ''}${layout.canopy ? ', soyabon' : ''}`);
}

// Daraxtlar: har to'r katakchasining o'z tasodifiy soni — biror joy o'zgarsa, boshqa joydagi daraxtlar siljimaydi
const cellRand = (i: number, j: number) => {
  let s = (Math.imul(i + 1000, 73856093) ^ Math.imul(j + 1000, 19349663) ^ 20261016) | 0;
  return () => {
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
};
blockerBoxes.push(...deck.map((poly) => ({ poly, gap: 0.5, box: bbox(poly) })));
const trees: [number, number, number][] = [];
const STEP = 12;
for (let x = bounds.minX, ci = 0; x < bounds.maxX; x += STEP, ci++) {
  for (let y = bounds.minY, cj = 0; y < bounds.maxY; y += STEP, cj++) {
    const cr = cellRand(ci, cj);
    const p: XY = [x + cr() * STEP * 0.9, y + cr() * STEP * 0.9];
    const size = 0.75 + cr() * 0.5;
    if (!inPoly(p, bog)) continue;
    let edge = Infinity;
    for (let i = 0; i < bog[0].length - 1; i++) edge = Math.min(edge, distToSeg(p, bog[0][i], bog[0][i + 1]));
    if (edge < 2) continue;
    const blocked = blockerBoxes.some(({ poly, gap, box }) =>
      p[0] > box.minX - gap && p[0] < box.maxX + gap && p[1] > box.minY - gap && p[1] < box.maxY + gap &&
      distToPoly(p, poly) < gap);
    if (!blocked) trees.push([r2(p[0]), r2(p[1]), r2(size)]);
  }
}
trees.push(...parkingTrees);
console.log(`✓ Daraxtlar: ${trees.length} (parking orolchalarida ${parkingTrees.length})`);

// ---------- 5b. Fonuslar ----------
// 1) data/lamps.geojson dagi chiziqlar: boshi va oxiri orasidagi yo'l grafdan topiladi, `count` yoki `spacing` bo'yicha qo'yiladi.
// 2) STREET_LAMP_ROADS.enabled bo'lsa — qolgan hamma yo'llar bo'ylab, har yo'lning bir tomonida, shu oraliqda.
// Fonus yo'l chetidan biroz tashqarida turadi; joy band bo'lsa yo'l bo'ylab suriladi.
const lamps: [number, number][] = [];
{
  const edgeOfPark = (p: XY) => {
    let m = Infinity;
    for (let i = 0; i < ground[0].length - 1; i++) m = Math.min(m, distToSeg(p, ground[0][i], ground[0][i + 1]));
    return m;
  };
  const blocked = (p: XY) =>
    !inPoly(p, ground) || edgeOfPark(p) < 0.5 ||
    roadPolys.some((poly) => distToPoly(p, poly) < 0.5) ||
    [...waterAreas, ...buildings, ...parking].some((a) => distToPoly(p, a.poly) < 1) ||
    Object.values(construction).some((c) => inPoly(p, c.zone) || distToPoly(p, c.zone) < 0.6) ||
    attractions.some((a) => Math.hypot(p[0] - a.at[0], p[1] - a.at[1]) < ATTRACTION_SIZES[a.size].footprint / 2 + 1) ||
    // Bolalar maydonchasi uskunalari, skameykalar va darvoza atrofida daraxt o'smaydi
    PLAYGROUND.items.some((q) => Math.hypot(p[0] - q[1], p[1] - q[2]) < 3.2) ||
    PLAYGROUND.benches.some((q) => Math.hypot(p[0] - q[0], p[1] - q[1]) < 1.8) ||
    PLAYGROUND.gates.some((q) => Math.hypot(p[0] - q[0], p[1] - q[1]) < 3) ||
    Math.hypot(p[0] - PLAYGROUND_RIDES.jeep.x, p[1] - PLAYGROUND_RIDES.jeep.y) < PLAYGROUND_RIDES.jeep.r + 1.8 ||
    Math.hypot(p[0] - PLAYGROUND_RIDES.carousel.x, p[1] - PLAYGROUND_RIDES.carousel.y) < PLAYGROUND_RIDES.carousel.r + 1.8 ||
    PLAYGROUND_RIDES.vehicles.some((q) => Math.hypot(p[0] - q[0], p[1] - q[1]) < 2.2);

  /** Chiziq bo'ylab yurish: uzunlik va `dist` metrdagi nuqta + chap normal */
  const walker = (line: XY[]) => {
    const cum = [0];
    for (let i = 1; i < line.length; i++) cum.push(cum[i - 1] + Math.hypot(line[i][0] - line[i - 1][0], line[i][1] - line[i - 1][1]));
    const total = cum[cum.length - 1];
    const at = (dist: number) => {
      const d = Math.min(Math.max(dist, 0), total);
      let i = 1;
      while (i < cum.length - 1 && cum[i] < d) i++;
      const [a, b] = [line[i - 1], line[i]];
      const len = Math.max(cum[i] - cum[i - 1], 1e-9);
      const k = (d - cum[i - 1]) / len;
      return { p: [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k] as XY, n: [-(b[1] - a[1]) / len, (b[0] - a[0]) / len] as XY };
    };
    return { total, at };
  };
  type Walk = ReturnType<typeof walker>;
  /** Berilgan tomonda (1 — chap, -1 — o'ng) yo'ldan chiqquncha surib bo'sh joy qidiradi */
  const spotOnSide = (w: Walk, dist: number, side: number): XY | null => {
    const { p, n } = w.at(dist);
    for (let off = 1.5; off <= 5; off += 0.25) {
      const q: XY = [p[0] + n[0] * off * side, p[1] + n[1] * off * side];
      if (!blocked(q)) return q;
    }
    return null;
  };
  /** Avval tanlangan tomonda yo'l bo'ylab ±6 m gacha siljitib, bo'lmasa ikkinchi tomonda */
  const spotNear = (w: Walk, dist: number, sides: number[]): XY | null => {
    for (const side of sides) for (const shift of [0, 2, -2, 4, -4, 6, -6]) {
      const q = spotOnSide(w, dist + shift, side);
      if (q) return q;
    }
    return null;
  };
  const tooClose = (q: XY, gap: number) => lamps.some(([x, y]) => Math.hypot(x - q[0], y - q[1]) < gap);

  // 1) Aniq belgilangan yo'llar
  if (fs.existsSync(LAMPS)) {
    const lampSrc: FeatureCollection = JSON.parse(fs.readFileSync(LAMPS, 'utf8'));
    const router = createRouter({ nodes, edges });
    const nearestEnd = (p: XY) => {
      const sn = router.snapToNetwork(p);
      return sn.t < 0.5 ? edges[sn.edge][0] : edges[sn.edge][1];
    };
    for (const f of lampSrc.features) {
      if (f.geometry.type !== 'LineString') continue;
      const way = f.geometry.coordinates.map((c) => nearestEnd(project(c)));
      const line: XY[] = [];
      for (let i = 0; i < way.length - 1; i++) line.push(...(router.between(way[i], way[i + 1])?.points ?? []));
      const w = walker(line);
      const count = Number(f.properties?.count) || 0;
      const spacing = count > 0 ? w.total / count : Number(f.properties?.spacing) || 16;
      // Park chegarasiga yaqin tomon birinchi
      const mid = w.at(w.total / 2);
      const sideScore = (s: number) => edgeOfPark([mid.p[0] + mid.n[0] * 3 * s, mid.p[1] + mid.n[1] * 3 * s]);
      const sides = [1, -1].sort((a, b) => sideScore(a) - sideScore(b));
      let placed = 0;
      for (let d = spacing / 2; d < w.total; d += spacing) {
        const q = spotNear(w, d, sides);
        if (q) { lamps.push([r2(q[0]), r2(q[1])]); placed++; }
      }
      console.log(`✓ Fonuslar: "${f.properties?.note ?? f.properties?.name}" — ${Math.round(w.total)} m yo'lga ${placed} ta (har ${spacing.toFixed(1)} m)`);
    }
  }

  // 2) Hamma yo'llar, bir tomonda
  if (STREET_LAMP_ROADS.enabled) {
    const { spacing, minGap } = STREET_LAMP_ROADS;
    const before = lamps.length;
    let length = 0;
    for (const l of groundLines) {
      const w = walker(l.geometry.coordinates.map(project));
      if (w.total < spacing * 0.5) continue; // juda qisqa bog'lovchi bo'laklar
      length += w.total;
      const n = Math.max(1, Math.round(w.total / spacing));
      const step = w.total / n;
      const ds = Array.from({ length: n }, (_, i) => step / 2 + i * step);
      // Tomon: qaysi tomonda ko'proq bo'sh joy bo'lsa, o'sha (yo'l bo'yi bir tomonda turadi)
      const score = (s: number) => ds.filter((d) => spotOnSide(w, d, s)).length;
      const side = score(1) >= score(-1) ? 1 : -1;
      for (const d of ds) {
        const q = spotNear(w, d, [side, -side]);
        if (q && !tooClose(q, minGap)) lamps.push([r2(q[0]), r2(q[1])]);
      }
    }
    console.log(`✓ Fonuslar: hamma yo'llar (${(length / 1000).toFixed(1)} km) bo'ylab yana ${lamps.length - before} ta, jami ${lamps.length}`);
  }
}

// Parking fonuslari (joylashuv bilan birga hisoblangan): boshqa fonusga juda yaqin bo'lsa tashlab ketiladi
{
  const before = lamps.length;
  for (const q of parkingLamps) {
    if (!lamps.some(([x, y]) => Math.hypot(x - q[0], y - q[1]) < 6)) lamps.push(q);
  }
  if (parkingLamps.length) console.log(`✓ Parking fonuslari: ${lamps.length - before} ta qo'shildi, jami ${lamps.length}`);
}

// ---------- 5c. Suv o'simliklari ----------
// data/water-plants.geojson dagi har bir hudud (Polygon) ichida: qirg'oq bo'ylab qamish to'plari (dog'-dog' bo'lib),
// suv yuzida nilufar to'dalari. Ko'prik va binolardan (rotonda) uzoqda.
const plants: ParkData['plants'] = { reeds: [], lilies: [] };
if (fs.existsSync(PLANTS)) {
  const P2 = WATER_PLANTS;
  const plantSrc: FeatureCollection = JSON.parse(fs.readFileSync(PLANTS, 'utf8'));
  const bridgeLines = lines.filter((l) => l.properties.name === 'Koprik').map((l) => l.geometry.coordinates.map(project));
  const nearBridge = (p: XY, gap: number) =>
    bridgeLines.some((bl) => bl.some((b, i) => i > 0 && distToSeg(p, bl[i - 1], b) < gap));
  const nearBuilding = (p: XY, gap: number) => buildings.some((b) => distToPoly(p, b.poly) < gap);
  const lerp = ([a, b]: [number, number], t: number) => a + (b - a) * t;
  // Qirg'oq bo'ylab 1D shovqin: qamish uzluksiz devor emas, to'p-to'p bo'lib o'sadi
  const hash = (i: number) => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
  const patch = (s: number) => {
    const i = Math.floor(s), f = s - i, u = f * f * (3 - 2 * f);
    return hash(i) * (1 - u) + hash(i + 1) * u;
  };

  for (const f of plantSrc.features) {
    if (f.geometry.type !== 'Polygon') continue;
    const region: Poly = f.geometry.coordinates.map((r) => r.map(project));
    const wantReeds = f.properties?.reeds !== false, wantLilies = f.properties?.lilies !== false;
    for (const w of waterAreas) {
      const touches = w.poly[0].some((p) => inPoly(p, region)) || region[0].some((p) => inPoly(p, w.poly));
      if (!touches) continue;
      const coping = WATER.styles[WATER.bodies[w.name] ?? 'pond'].coping;
      const inside = (p: XY) => inPoly(p, w.poly) && inPoly(p, region);
      const before = { r: plants.reeds.length, l: plants.lilies.length };

      if (wantReeds) {
        let arc0 = 0;
        for (const ring of w.poly) {
          for (let i = 0; i < ring.length - 1; i++) {
            const [a, b] = [ring[i], ring[i + 1]];
            const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
            if (len < 0.01) continue;
            // Suv tomonga qaragan normal
            let n: XY = [-(b[1] - a[1]) / len, (b[0] - a[0]) / len];
            const mid: XY = [(a[0] + b[0]) / 2 + n[0] * 0.5, (a[1] + b[1]) / 2 + n[1] * 0.5];
            if (!inPoly(mid, w.poly)) n = [-n[0], -n[1]];
            for (let t = rand() * P2.reedSpacing; t < len; t += P2.reedSpacing * (0.7 + rand() * 0.6)) {
              if (patch((arc0 + t) / 7) < 0.34) continue;
              const base: XY = [a[0] + ((b[0] - a[0]) * t) / len, a[1] + ((b[1] - a[1]) * t) / len];
              const rr = rand();
              const rows = rr < 0.2 ? 3 : rr < 0.65 ? 2 : 1;
              for (let k = 0; k < rows; k++) {
                const off = coping + 0.25 + k * (0.8 + rand() * 0.7) + rand() * 0.8;
                const q: XY = [base[0] + n[0] * off, base[1] + n[1] * off];
                if (!inside(q) || distToBoundary(q, w.poly) < coping + 0.15) continue;
                if (nearBridge(q, 3) || nearBuilding(q, 2)) continue;
                plants.reeds.push([r2(q[0]), r2(q[1]), r2(lerp(P2.reedHeight, rand()) * (k ? 0.85 : 1)), r2(rand() * Math.PI * 2)]);
              }
            }
            arc0 += len;
          }
        }
      }

      if (wantLilies) {
        const xs = region[0].map((p) => p[0]), ys = region[0].map((p) => p[1]);
        const box = { x0: Math.min(...xs), y0: Math.min(...ys), w: Math.max(...xs) - Math.min(...xs), h: Math.max(...ys) - Math.min(...ys) };
        const centers: XY[] = [];
        for (let tries = 0; centers.length < P2.lilyClusters && tries < 5000; tries++) {
          const q: XY = [box.x0 + rand() * box.w, box.y0 + rand() * box.h];
          if (!inside(q)) continue;
          const bd = distToBoundary(q, w.poly);
          if (bd < coping + 2.2 || bd > 16) continue;
          if (nearBridge(q, 5) || nearBuilding(q, 5) || centers.some((c) => Math.hypot(c[0] - q[0], c[1] - q[1]) < 9)) continue;
          centers.push(q);
        }
        for (const c of centers) {
          const want = Math.round(lerp(P2.lilyPerCluster, rand()));
          const spread = 1.4 + want * 0.18;
          for (let k = 0, got = 0; got < want && k < 400; k++) {
            const ang = rand() * Math.PI * 2, rad = spread * Math.sqrt(rand());
            const q: XY = [c[0] + Math.cos(ang) * rad, c[1] + Math.sin(ang) * rad];
            const r = lerp(P2.lilyRadius, rand());
            if (!inside(q) || distToBoundary(q, w.poly) < coping + r + 0.3) continue;
            if (nearBridge(q, 3) || nearBuilding(q, 2.5)) continue;
            if (plants.lilies.some(([x, y, rr]) => Math.hypot(x - q[0], y - q[1]) < rr + r + 0.04)) continue;
            if (plants.reeds.some(([x, y]) => Math.hypot(x - q[0], y - q[1]) < r + 0.5)) continue;
            const flower = rand() < P2.flowerShare ? (rand() < 0.6 ? 1 : 2) : 0;
            plants.lilies.push([r2(q[0]), r2(q[1]), r2(r), r2(rand() * Math.PI * 2), flower]);
            got++;
          }
        }
      }
      console.log(`✓ Suv o'simliklari: ${w.name} — ${plants.reeds.length - before.r} qamish to'pi, ` +
        `${plants.lilies.length - before.l} nilufar bargi (${plants.lilies.slice(before.l).filter((l) => l[4]).length} ta gulli)`);
    }
  }
}

// ---------- 5d. Basseyn bo'yi: soyabon va shezlonglar, bezaklar ----------
// Har basseyn chegarasi bo'ylab `spacing` oraliqda, `rows` masofalarda: soyabon va uning ostida ikkita shezlong (boshi suvdan teskari).
// Plitkadan chiqmaydi, yo'lak o'qidan (marshrut chizig'idan), ko'prik, bino, fonus va boshqa soyabonlardan uzoq turadi.
const poolside: ParkData['poolside'] = { umbrellas: [], loungers: [], sails: [] };
const poolFx: ParkData['poolFx'] = {};
{
  const fxOf = (name: string) =>
    (poolFx[name] ??= { jacuzzi: [], steps: [], band: [], line: [], stripes: false, playground: null });
  for (const f of poolSrc.features) {
    const name = nameOf(f), p = f.properties ?? {};
    const water = String(p.water ?? '');
    if (f.geometry.type === 'Point') {
      const at = P(f.geometry.coordinates);
      if (name === 'Jakuzi') fxOf(water).jacuzzi.push([at[0], at[1], Number(p.radius) || 2.5]);
      else if (name === 'Zina') fxOf(water).steps.push([at[0], at[1], Number(p.from) || 1.5, Number(p.to) || 4.5, Number(p.step) || 0.6]);
      else if (name === 'Mozaika' && p.kind === 'stripes') fxOf(water).stripes = true;
      else if (name === 'Suv_maydoni') fxOf(water).playground = [at[0], at[1], Number(p.bearing) || 0];
      else if (name === 'Yelkan') {
        const n = Number(p.count) || 4, size = Number(p.size) || 6;
        for (let k = 0; k < n; k++) {
          const c = k % 2, r = Math.floor(k / 2);
          poolside.sails.push([r2(at[0] + (c - 0.5) * size * 0.85), r2(at[1] + (r - (Math.ceil(n / 2) - 1) / 2) * size * 0.8), r2((k * 1.7) % Math.PI), size]);
        }
      }
    } else if (f.geometry.type === 'LineString' && name === 'Mozaika') {
      const pts = f.geometry.coordinates.map(P);
      if (p.kind === 'band') fxOf(water).band.push(pts);
      else fxOf(water).line.push(pts);
    }
  }

  const walkLines = lines.filter((l) => l.properties.name !== 'Koprik').map((l) => l.geometry.coordinates.map(project));
  const bridgeLines = lines.filter((l) => l.properties.name === 'Koprik').map((l) => l.geometry.coordinates.map(project));
  const nearLine = (p: XY, ls: XY[][], gap: number) => ls.some((l) => l.some((b, i) => i > 0 && distToSeg(p, l[i - 1], b) < gap));
  const inDeck = (p: XY, margin: number) => deck.some((poly) => inPoly(p, poly) && distToBoundary(p, poly) >= margin);
  const placed: XY[] = [];
  const free = (p: XY) =>
    inDeck(p, 1.1) &&
    !nearLine(p, walkLines, POOL_AREA.pathClearance) && !nearLine(p, bridgeLines, 3) &&
    waterAreas.every((a) => !inPoly(p, a.poly) && distToBoundary(p, a.poly) > 1.4) &&
    buildings.every((b) => distToPoly(p, b.poly) > 1.6) &&
    lamps.every(([x, y]) => Math.hypot(x - p[0], y - p[1]) > 1.7) &&
    placed.every((q) => Math.hypot(q[0] - p[0], q[1] - p[1]) > 1.2);

  for (const name of POOL_AREA.pools) {
    const area = waterAreas.find((a) => a.name === name);
    if (!area) continue;
    const coping = WATER.styles[WATER.bodies[name] ?? 'pond'].coping;
    const ring = area.poly[0];
    for (const row of POOL_AREA.rows) {
      let carry = POOL_AREA.spacing / 2;
      for (let i = 0; i < ring.length - 1; i++) {
        const [a, b] = [ring[i], ring[i + 1]];
        const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
        if (len < 1e-6) continue;
        const t: XY = [(b[0] - a[0]) / len, (b[1] - a[1]) / len];
        let n: XY = [t[1], -t[0]];
        const probe: XY = [(a[0] + b[0]) / 2 + n[0] * 0.3, (a[1] + b[1]) / 2 + n[1] * 0.3];
        if (inPoly(probe, area.poly)) n = [-n[0], -n[1]]; // tashqariga (suvdan teskari)
        for (let s = carry; s < len; s += POOL_AREA.spacing) {
          const e: XY = [a[0] + t[0] * s, a[1] + t[1] * s];
          const off = coping + row;
          const u: XY = [e[0] + n[0] * off, e[1] + n[1] * off];
          if (!free(u)) continue;
          placed.push(u);
          const rot = Math.atan2(n[1], n[0]);
          const color = rand() < 0.7 ? 0 : 1;
          for (const side of [-1, 1]) {
            const l: XY = [e[0] + n[0] * (off - 0.15) + t[0] * side * 0.55, e[1] + n[1] * (off - 0.15) + t[1] * side * 0.55];
            poolside.loungers.push([r2(l[0]), r2(l[1]), r2(rot), color]);
          }
        }
        carry = ((carry - len) % POOL_AREA.spacing + POOL_AREA.spacing) % POOL_AREA.spacing;
      }
    }
  }
  // Orol bari atrofida oq shezlonglar (fotodagidek): bar bilan suv orasida, ko'prik yo'nalishlari bo'sh qoladi
  for (const b of buildings) {
    if (BUILDING_LOOKS[b.id]?.facade !== 'bar') continue;
    const ring = b.poly[0].slice(0, -1);
    const cx = ring.reduce((s, p) => s + p[0], 0) / ring.length, cy = ring.reduce((s, p) => s + p[1], 0) / ring.length;
    const host = waterAreas.find((a) => a.poly.slice(1).some((h) => inPoly([cx, cy], [h])));
    const hole = host?.poly.slice(1).find((h) => inPoly([cx, cy], [h]));
    if (!host || !hole) continue;
    const rIsland = hole.reduce((s, p) => s + Math.hypot(p[0] - cx, p[1] - cy), 0) / hole.length;
    const coping = WATER.styles[WATER.bodies[host.name] ?? 'pond'].coping;
    const r = rIsland - coping - 1.05;
    const bridgeDirs = bridgeLines.flatMap((l) => [l[0], l[l.length - 1]])
      .filter((p) => Math.hypot(p[0] - cx, p[1] - cy) < rIsland + 3)
      .map((p) => Math.atan2(p[1] - cy, p[0] - cx));
    for (let k = 0; k < 16; k++) {
      const a = (k / 16) * Math.PI * 2;
      if (bridgeDirs.some((d) => Math.abs(Math.atan2(Math.sin(a - d), Math.cos(a - d))) < 0.42)) continue;
      poolside.loungers.push([r2(cx + Math.cos(a) * r), r2(cy + Math.sin(a) * r), r2(a + Math.PI), 2]);
    }
  }
  console.log(`✓ Basseyn bo'yi: ${poolside.umbrellas.length} soyabon, ${poolside.loungers.length} shezlong, ${poolside.sails.length} yelkan; ` +
    `bezaklar: ${Object.entries(poolFx).map(([k, v]) => `${k} (${v.jacuzzi.length} jakuzi, ${v.steps.length} zina, ${v.band.length + v.line.length} mozaika${v.stripes ? ', tasmalar' : ''}${v.playground ? ", o'yin maydoni" : ''})`).join(', ')}`);
}

// ---------- 6. Yozish ----------
const roadKm = lines.reduce((s, l) => s + turf.length(l, { units: 'kilometers' }), 0);
const data: ParkData = {
  bounds: { minX: r2(bounds.minX), minY: r2(bounds.minY), maxX: r2(bounds.maxX), maxY: r2(bounds.maxY) },
  ground,
  groundCut,
  water: waterAreas,
  // Basseyn plitkasi ustida alohida yo'lak chizilmaydi (fotodagidek bitta maydon); marshrut grafi o'zgarmaydi
  roads: deckFeature ? toMulti(minus(roadSurface, deckFeature)) : roadPolys,
  roadsDraft: toMulti(minus(draftOnly, deckFeature)),
  deck,
  poolside,
  poolFx,
  bridges: lines
    .filter((l) => l.properties.name === 'Koprik')
    .map((l, i) => ({ id: `bridge-${i + 1}`, line: l.geometry.coordinates.map(P), width: ROAD_WIDTH.Koprik })),
  parking,
  construction,
  parkingLayout,
  playgrounds,
  buildings,
  attractions,
  trees,
  lamps,
  plants,
  graph: { nodes: nodes.map(([x, y]) => [r2(x), r2(y)] as XY), edges },
  pois,
  stats: {
    roadKm: Math.round(roadKm * 10) / 10,
    areaHa: Math.round(turf.area(bogFeature) / 1000) / 10,
    objects: pois.filter((p) => p.category !== 'entrance').length,
  },
};
fs.writeFileSync(OUT, JSON.stringify(data));
console.log(`✓ ${path.relative(ROOT, OUT)} — ${(fs.statSync(OUT).size / 1024).toFixed(0)} KB`);

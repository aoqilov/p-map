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
import { pathToFileURL } from 'node:url';
import * as turf from '@turf/turf';
import type { Feature, FeatureCollection, Geometry, MultiPolygon, Point, Polygon, Position, LineString } from 'geojson';
import { ATTRACTION_MOVES, ATTRACTION_SIZES, BUILDING_OVERRIDES, EXTRA_BUILDINGS, FENCES, HEDGES, KASSA, PAVED_AREAS, REMOVED_ATTRACTIONS, REMOVED_BUILDINGS, TREE_GROVES, WATER_RIDES, type AttractionSize, type Category } from '../src/map/config';
import { project, unproject, type XY } from '../src/map/projection';
import type { Area, Attraction, Bridge, Building, MultiPoly, ParkData, Poi, Poly } from '../src/map/types';
import { distToBoundary, distToPoly, inPoly, segmentsCross, smoothLine } from '../src/map/geo';
import type { BuildingDef, PlanModelDef } from '../src/decor/define';
import type { AttractionPlaceDef } from '../src/attractions/define';

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
  /** Bino rangi (explication.py → NAME_AT) */
  color?: string;
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

/** Halqadagi eng yaqin nuqta */
const nearestOnRing = (p: XY, ring: XY[]): XY => {
  let best: XY = ring[0], bd = Infinity;
  for (let i = 0; i < ring.length - 1; i++) {
    const [a, b] = [ring[i], ring[i + 1]];
    const dx = b[0] - a[0], dy = b[1] - a[1], L = dx * dx + dy * dy || 1;
    const t = Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L));
    const q: XY = [a[0] + t * dx, a[1] + t * dy];
    const d = Math.hypot(q[0] - p[0], q[1] - p[1]);
    if (d < bd) { bd = d; best = q; }
  }
  return best;
};

// ---------- Chegara va yer ----------
const boundaryF = layer('boundary')[0] as Feature<Polygon>;
const ground: Poly = [toPoly(boundaryF.geometry.coordinates)[0]];
const bounds = bbox(ground);

// ---------- Bezak-binolar (src/decor/*/building.ts): planda yo'q, 3D modeli bor binolar (tibbiyot xonasi va h.k.) ----------
const DECOR_DIR = path.join(ROOT, 'src/decor');
const extraDefs: BuildingDef[] = [];
/** Plandagi mavjud binoga qo'yilgan modellar (hojatxona n7, n8): qutisi yashiriladi */
const planModels: PlanModelDef[] = [];
for (const dir of fs.readdirSync(DECOR_DIR).sort()) {
  const file = path.join(DECOR_DIR, dir, 'building.ts');
  if (!fs.existsSync(file)) continue;
  const mod = (await import(pathToFileURL(file).href)).default as BuildingDef | PlanModelDef | (BuildingDef | PlanModelDef)[];
  for (const d of [mod].flat()) {
    if ('plan' in d) planModels.push(d);
    else extraDefs.push(d);
  }
}
/** To'rtburchak iz: markaz, old yo'nalish (bearing), eni (old tomon bo'ylab) × chuqurligi */
const rectAround = (at: XY, bearing: number, width: number, depth: number): Poly => {
  const b = (bearing * Math.PI) / 180;
  const f: XY = [Math.sin(b), Math.cos(b)], r: XY = [Math.cos(b), -Math.sin(b)];
  const pt = (sx: number, sy: number): XY =>
    [r2(at[0] + r[0] * sx * width / 2 + f[0] * sy * depth / 2), r2(at[1] + r[1] * sx * width / 2 + f[1] * sy * depth / 2)];
  const ring = [pt(-1, -1), pt(1, -1), pt(1, 1), pt(-1, 1)];
  return [[...ring, ring[0]]];
};
/** Bino izi: to'rtburchak (yoki doira — shape: 'circle') */
const rectOf = (d: BuildingDef): Poly => {
  if (d.shape === 'circle') {
    const ring: XY[] = Array.from({ length: 32 }, (_, i) => {
      const a = (i / 32) * Math.PI * 2;
      return [r2(d.at[0] + Math.cos(a) * d.width / 2), r2(d.at[1] + Math.sin(a) * d.width / 2)];
    });
    return [[...ring, ring[0]]];
  }
  return rectAround(d.at, d.bearing, d.width, d.depth);
};

// ---------- Planda yo'q attraksionlar (src/attractions/*/place.ts): Ping pong va h.k. ----------
const ATTRACTIONS_DIR = path.join(ROOT, 'src/attractions');
const placedAttractions: AttractionPlaceDef[] = [];
for (const dir of fs.readdirSync(ATTRACTIONS_DIR).sort()) {
  const file = path.join(ATTRACTIONS_DIR, dir, 'place.ts');
  if (!fs.existsSync(file)) continue;
  placedAttractions.push(...[(await import(pathToFileURL(file).href)).default as AttractionPlaceDef | AttractionPlaceDef[]].flat());
}
const extraPolys = extraDefs.map(rectOf);
/** Yo'l plitkasi o'rniga qo'yilgan bezaklar (sharshara): izi plitkadan kesiladi, marshrut u orqali o'tmaydi */
const cutPolys = extraPolys.filter((_, i) => extraDefs[i].cutPaving);
const cutF: PolyFeature[] = cutPolys.map((pp) => turf.polygon([pp[0].map(unproject)]));
const inCut = (a: XY, b: XY) => cutPolys.some((pp) =>
  [0, 0.25, 0.5, 0.75, 1].some((t) => inPoly([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t], pp)));
/** Jonli devorlar (config/map.ts → HEDGES): ularni kesib o'tadigan yo'l qirrasi marshrutga kirmaydi */
const hedgeLines = HEDGES.map((h) => smoothLine(h.line, 3));
const crossesHedge = (a: XY, b: XY) => hedgeLines.some((l) => l.some((q, i) => i > 0 && segmentsCross(a, b, l[i - 1], q)));

// ---------- Suv: eng kattasi — Hovuz (baliqlar shu yerda), kanal — Ariq, sharqdagi basseynlar — Basseyn ----------
// Bezak-bino ostida qolgan suv (masalan, basseyn o'rniga tibbiyot xonasi) — olib tashlanadi
const waterF = layer('water').filter(isPoly).filter((f) => {
  const c = P(turf.centroid(f).geometry.coordinates);
  return !extraPolys.some((pp) => inPoly(c, pp));
});
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
// ---------- Suv attraksionlari (config/map.ts → WATER_RIDES): maydoncha ichida yer ostidagi halqa kanal va orol ----------
const rides = new Map<string, NonNullable<Attraction['ride']>>();
const rideWater: PolyFeature[] = [];
for (const f of layer('attraction').filter(isPoly)) {
  const cfg = f.properties.num ? WATER_RIDES[f.properties.num] : undefined;
  if (!cfg) continue;
  const inset = (m: number) => turf.buffer(f, -m, { units: 'meters', steps: 6 }) as PolyFeature | undefined;
  const outer = inset(cfg.rim), island = inset(cfg.rim + cfg.channel);
  const mid = inset(cfg.rim + cfg.channel / 2);
  if (!outer || !island || !mid) { console.warn(`⚠ Suv attraksioni ${f.properties.num}: maydoncha juda kichik`); continue; }
  const channel = minus(outer, island);
  if (!channel) continue;
  rideWater.push(channel);
  toMulti(channel).forEach((poly, k) => waterAreas.push({ id: `aqua-${f.properties.num}${k ? `-${k}` : ''}`, name: 'Aqua', poly }));
  // qayiqlar yo'li — kanal o'rtasidagi halqa (eng uzun qismi)
  const ring = toMulti(mid).map((pp) => pp[0]).sort((a, b) => b.length - a.length)[0];
  rides.set(f.properties.num!, { rim: toMulti(minus(f as PolyFeature, outer)), island: toMulti(island), path: ring, boats: cfg.boats });
}
const waterUnion = unionAll([...waterF, ...rideWater]);
const groundCut: MultiPoly = toMulti(minus(boundaryF as PolyFeature, waterUnion));

// ---------- Yo'l va maydonlar (plitka) ----------
const roadsF = minus(unionAll([...layer('paving'), ...layer('plaza')].filter(isPoly)), unionAll(cutF));
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
  if (p.layer === 'attraction' && p.num && REMOVED_ATTRACTIONS.includes(p.num)) return; // config/map.ts → REMOVED_ATTRACTIONS
  const at: XY = f.geometry.type === 'Point' ? P((f.geometry as Point).coordinates) : anchorOf(poly);
  switch (p.layer) {
    case 'building': {
      const h = p.height ?? 3.5;
      polys.forEach((pp, k) => buildings.push({ id: k ? `${id}-${k}` : id, name: p.name ?? 'Bino', poly: pp, height: h,
        ...(p.color ? { color: p.color } : {}) }));
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
      attractions.push({ id, name: p.name ?? 'Аттракцион', at, size, bearing: 0, height, num: p.num ?? null, footprint,
        ...(p.num && rides.has(p.num) ? { ride: rides.get(p.num) } : {}) });
      pending.push({ props: { ...p, category: p.category ?? 'fun' }, id, anchor: at, elevation: (height ?? ATTRACTION_SIZES[size].height) + 1 });
      break;
    }
    case 'fountain':
    case 'entrance':
      pending.push({ props: p, id, anchor: at, elevation: 0.5 });
      break;
  }
});

extraDefs.forEach((d, i) => {
  buildings.push({ id: d.id, name: d.name, poly: extraPolys[i], height: d.height, model: true });
  if (d.category) pending.push({ props: { layer: 'building', name: d.name, category: d.category }, id: d.id, anchor: d.at, elevation: d.height });
});
/** Ko'chirilgan plan binolari (PlanModelDef.move): marshrut ular orqali o'tmaydi */
const movedPolys: Poly[] = [];
const ringCenter = (ring: XY[]): XY => {
  let a = 0, cx = 0, cy = 0;
  for (let i = 0; i < ring.length - 1; i++) {
    const f = ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1];
    a += f; cx += (ring[i][0] + ring[i + 1][0]) * f; cy += (ring[i][1] + ring[i + 1][1]) * f;
  }
  return [cx / (3 * a), cy / (3 * a)];
};
for (const m of planModels) {
  const b = buildings.find((x) => x.id === m.plan);
  if (!b) { console.warn(`⚠ Model: plandagi "${m.plan}" bino topilmadi`); continue; }
  b.model = true;
  if (m.height) b.height = m.height;
  if (m.name) b.name = m.name;
  if (m.category && b.name !== 'Bino' && !pending.some((pe) => pe.id === m.plan))
    pending.push({ props: { layer: 'building', name: b.name, category: m.category }, id: m.plan, anchor: m.at, elevation: b.height });
  if (m.rect) {
    // plandagi notekis iz o'rniga bitta to'rtburchak (model izi); pin uning markaziga
    b.poly = rectAround(m.at, m.bearing, m.rect.width, m.rect.depth);
    for (const pe of pending) if (pe.id === m.plan) { pe.anchor = m.at; pe.elevation = b.height; }
    movedPolys.push(b.poly);
  } else if (m.move) {
    // izni model joyiga surish (shakli va burilishi o'zgarmaydi); pin ham shuncha siljiydi
    const c = ringCenter(b.poly[0]);
    const dx = m.at[0] - c[0], dy = m.at[1] - c[1];
    b.poly = b.poly.map((ring) => ring.map(([x, y]): XY => [r2(x + dx), r2(y + dy)]));
    for (const pe of pending) if (pe.id === m.plan) pe.anchor = [r2(pe.anchor[0] + dx), r2(pe.anchor[1] + dy)];
    movedPolys.push(b.poly);
  }
}
// #editor dagi oddiy binolar (config/map.ts → BUILDING_OVERRIDES, EXTRA_BUILDINGS): izlar shu yerda hisoblanadi (marshrut ular
// orqali o'tmaydi), binolar ro'yxatiga esa daraxtlardan keyin qo'shiladi — boshqa daraxtlar joyidan siljimasin
const overridePolys = new Map(Object.entries(BUILDING_OVERRIDES).map(([id, r]) => [id, rectAround(r.at, r.bearing, r.width, r.depth)]));
const extraBuildings: Building[] = EXTRA_BUILDINGS.map((e) => ({ id: e.id, name: e.name, poly: 'poly' in e ? [[...e.poly, e.poly[0]]] : rectAround(e.at, e.bearing, e.width, e.depth), height: e.height }));
for (const id of overridePolys.keys()) if (!buildings.some((b) => b.id === id)) console.warn(`⚠ BUILDING_OVERRIDES: plandagi "${id}" bino topilmadi`);
movedPolys.push(...overridePolys.values(), ...extraBuildings.map((b) => b.poly));
if (planModels.length) console.log(`✓ Plan binolariga model: ${planModels.map((m) => m.plan).join(', ')}`);
if (extraDefs.length) console.log(`✓ Bezak-binolar: ${extraDefs.map((d) => d.name).join(', ')}`);

/** Planda yo'q attraksionlar id (daraxtlar ulardan keyin alohida tozalanadi) */
const placedIds = new Set<string>();
// Planda yo'q attraksionlar: maydoncha izi — to'rtburchak; pin, qidiruv, to'siq va daraxtsiz zona — boshqa attraksionlardagidek
for (const a of placedAttractions) {
  const footprint = rectAround(a.at, a.bearing, a.width, a.depth);
  const id = a.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || `attraction-${attractions.length + 1}`;
  if (usedIds.has(id)) throw new Error(`Attraksion id takrorlandi: ${id} (${a.name})`);
  usedIds.add(id);
  placedIds.add(id);
  attractions.push({ id, name: a.name, at: a.at, size: sizeFor(2 * Math.sqrt(area(footprint) / Math.PI)), bearing: a.bearing, height: a.height,
    num: null, footprint });
  pending.push({ props: { layer: 'attraction', name: a.name, category: a.category ?? 'fun' }, id, anchor: a.at, elevation: a.height + 1 });
}
if (placedAttractions.length) console.log(`✓ Planda yo'q attraksionlar: ${placedAttractions.map((a) => a.name).join(', ')}`);

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
let hedgeCuts = 0;
for (const f of layer('path')) {
  const pts = (f.geometry as LineString).coordinates.map(P);
  for (let k = 0; k < pts.length - 1; k++) {
    if (inCut(pts[k], pts[k + 1])) continue; // sharshara o'rnidagi yo'l — marshrut yo'q
    if (crossesHedge(pts[k], pts[k + 1])) { hedgeCuts++; continue; } // buta orqali o'tmaydi
    if (movedPolys.some((pp) => [0, 0.25, 0.5, 0.75, 1].some((t) => inPoly([pts[k][0] + (pts[k + 1][0] - pts[k][0]) * t, pts[k][1] + (pts[k + 1][1] - pts[k][1]) * t], pp)))) continue; // ko'chirilgan bino ichidan o'tmaydi
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
if (HEDGES.length) console.log(`✓ Jonli devorlar: ${HEDGES.length} ta, marshrutdan ${hedgeCuts} qirra kesildi`);
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

// Kassalar (config.ts → KASSA): park metrlarida (`at` — 3D budka bilan), aniq koordinatada (`lonLat`) yoki plan raqami yonida (`near`)
for (const k of KASSA) {
  const base = k.near ? pois.find((p) => p.num === k.near) : null;
  const anchor: XY | null = k.at ?? (k.lonLat ? P(k.lonLat) : base ? [r2(base.anchor[0] + 3), r2(base.anchor[1] - 3)] : null);
  if (!anchor) { console.warn(`⚠ Kassa "${k.label}": joyi topilmadi (near: ${k.near})`); continue; }
  pois.push({ id: k.id, name: k.label, label: k.label, category: 'kassa', anchor, elevation: k.at ? r2(2.77 * (k.scale ?? 1) + 4.3) : 0.5, node: nearestNode(anchor),
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
  // planda yo'q attraksionlar bu yerda emas: ular daraxtlar yasalgandan keyin tozalanadi (boshqa daraxtlar siljimasin)
  ...attractions.filter((a) => !placedIds.has(a.id)).map((a) => ({ poly: a.footprint!, gap: 2.5 })),
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

// Qo'shimcha daraxtzorlar (config/map.ts → TREE_GROVES): o'z tasodifiy sonlari bilan — oddiy daraxtlar o'zgarmaydi
for (const grove of TREE_GROVES) {
  let gs = [...grove.id].reduce((h, ch) => (h * 31 + ch.charCodeAt(0)) | 0, 7);
  const grand = () => { gs = (gs * 16807 + 11) % 2147483647; if (gs <= 0) gs += 2147483646; return gs / 2147483647; };
  const [gx, gy] = grove.at;
  const near = lawns.filter((l) => { const b = bbox(l); return b.maxX > gx - grove.radius && b.minX < gx + grove.radius && b.maxY > gy - grove.radius && b.minY < gy + grove.radius; });
  let added = 0;
  for (let tries = 0; tries < 4000; tries++) {
    const ang = grand() * Math.PI * 2, rr = grove.radius * Math.sqrt(grand());
    const p: XY = [gx + Math.cos(ang) * rr, gy + Math.sin(ang) * rr];
    const lawn = near.find((l) => inPoly(p, l));
    if (!lawn || distToBoundary(p, lawn) < 1.4) continue;
    if (blockers.some((k) => p[0] > k.box.minX - k.gap && p[0] < k.box.maxX + k.gap && p[1] > k.box.minY - k.gap &&
      p[1] < k.box.maxY + k.gap && (inPoly(p, k.poly) || distToPoly(p, k.poly) < k.gap))) continue;
    if (trees.some((t) => Math.hypot(t[0] - p[0], t[1] - p[1]) < grove.spacing)) continue;
    trees.push([r2(p[0]), r2(p[1]), r2(grove.scale[0] + grand() * (grove.scale[1] - grove.scale[0]))]);
    added++;
  }
  console.log(`✓ Daraxtzor "${grove.id}": +${added} ta katta daraxt`);
}
// Planda yo'q attraksionlar (masalan, maysazordagi RC Park) ichidagi va chetidan 1 m gacha bo'lgan daraxtlar olib tashlanadi
{
  const placed = attractions.filter((a) => placedIds.has(a.id)).map((a) => ({ poly: a.footprint!, box: bbox(a.footprint!) }));
  const before = trees.length;
  for (let i = trees.length - 1; i >= 0; i--) {
    const p: XY = [trees[i][0], trees[i][1]];
    if (placed.some((k) => p[0] > k.box.minX - 1 && p[0] < k.box.maxX + 1 && p[1] > k.box.minY - 1 && p[1] < k.box.maxY + 1 &&
      (inPoly(p, k.poly) || distToPoly(p, k.poly) < 1))) trees.splice(i, 1);
  }
  if (before !== trees.length) console.log(`✓ Attraksion maydonchalaridan ${before - trees.length} ta daraxt olib tashlandi`);
}

// ---------- Qo'shimcha plitka (config/map.ts → PAVED_AREAS): daraxtlardan keyin — boshqa daraxtlar siljimasin ----------
let roadsOut = roads;
if (PAVED_AREAS.length) {
  // 0.4 m kengaytiriladi: chizilgan chegara mavjud plitkaga sal yetmasa ham, orada ingichka maysa bo'lagi qolmasin
  const pavedF: PolyFeature[] = PAVED_AREAS.map((a) =>
    (turf.buffer(turf.polygon([[...a.poly, a.poly[0]].map(unproject)]), 0.4, { units: 'meters', steps: 2 }) as PolyFeature));
  // bezak-binolar izi (cutPaving, masalan sharshara) qo'shimcha plitka ustida ham kesilgan bo'lsin
  roadsOut = toMulti(minus(unionAll([...(roadsF ? [roadsF] : []), ...pavedF]), unionAll(cutF)));
  // plitka ichida qolgan mayda maysa teshiklari (4 m² dan kichik) — yopiladi
  roadsOut = roadsOut.map((poly) => [poly[0], ...poly.slice(1).filter((hole) => area([hole]) >= 4)]);
  const paved = PAVED_AREAS.map((a) => { const poly: Poly = [[...a.poly, a.poly[0]]]; return { poly, box: bbox(poly) }; });
  const before = trees.length;
  for (let i = trees.length - 1; i >= 0; i--) {
    const p: XY = [trees[i][0], trees[i][1]];
    if (paved.some((k) => p[0] > k.box.minX - 1 && p[0] < k.box.maxX + 1 && p[1] > k.box.minY - 1 && p[1] < k.box.maxY + 1 &&
      (inPoly(p, k.poly) || distToPoly(p, k.poly) < 1))) trees.splice(i, 1);
  }
  console.log(`✓ Qo'shimcha plitka: ${PAVED_AREAS.map((a) => a.id).join(', ')} (${before - trees.length} ta daraxt olib tashlandi)`);
}

// ---------- #editor dagi oddiy binolar: izni almashtirish va yangilarini qo'shish, ostidagi daraxtlarni olib tashlash ----------
if (overridePolys.size || extraBuildings.length) {
  for (const [id, poly] of overridePolys) {
    const b = buildings.find((x) => x.id === id);
    if (!b) continue;
    b.poly = poly;
    const h = BUILDING_OVERRIDES[id].height;
    if (h) { b.height = h; for (const po of pois) if (po.id === id) po.elevation = h; } // pin bino tepasida
  }
  buildings.push(...extraBuildings);
  const polys = [...overridePolys.values(), ...extraBuildings.map((b) => b.poly)].map((poly) => ({ poly, box: bbox(poly) }));
  const before = trees.length;
  for (let i = trees.length - 1; i >= 0; i--) {
    const p: XY = [trees[i][0], trees[i][1]];
    if (polys.some((k) => p[0] > k.box.minX - 1.5 && p[0] < k.box.maxX + 1.5 && p[1] > k.box.minY - 1.5 && p[1] < k.box.maxY + 1.5 &&
      (inPoly(p, k.poly) || distToPoly(p, k.poly) < 1.5))) trees.splice(i, 1);
  }
  console.log(`✓ Oddiy binolar (#editor): ${overridePolys.size} ta o'zgartirildi, ${extraBuildings.length} ta qo'shildi` +
    (before !== trees.length ? `, ${before - trees.length} ta daraxt olib tashlandi` : ''));
}

// ---------- Olib tashlangan plan binolari (config/map.ts → REMOVED_BUILDINGS): daraxtlardan keyin — boshqa daraxtlar siljimasin ----------
if (REMOVED_BUILDINGS.length) {
  const gone = new Set(REMOVED_BUILDINGS);
  const isGone = (id: string) => gone.has(id) || [...gone].some((g) => id.startsWith(`${g}-`) && /^-\d+$/.test(id.slice(g.length)));
  for (const id of gone) if (!buildings.some((b) => b.id === id)) console.warn(`⚠ REMOVED_BUILDINGS: "${id}" topilmadi`);
  const before = buildings.length;
  for (let i = buildings.length - 1; i >= 0; i--) if (isGone(buildings[i].id)) buildings.splice(i, 1);
  for (let i = pois.length - 1; i >= 0; i--) if (isGone(pois[i].id)) pois.splice(i, 1);
  console.log(`✓ Olib tashlangan binolar: ${REMOVED_BUILDINGS.join(', ')} (${before - buildings.length} ta iz)`);
}

// ---------- Plandagi attraksionlarni surish (config/map.ts → ATTRACTION_MOVES): daraxtlardan keyin — boshqa daraxtlar siljimasin ----------
if (Object.keys(ATTRACTION_MOVES).length) {
  const moved: Poly[] = [];
  for (const [num, to] of Object.entries(ATTRACTION_MOVES)) {
    const a = attractions.find((x) => x.num === num);
    if (!a) { console.warn(`⚠ ATTRACTION_MOVES: №${num} attraksion topilmadi`); continue; }
    if (a.ride) { console.warn(`⚠ ATTRACTION_MOVES: №${num} — suv attraksioni, surilmaydi`); continue; }
    const dx = to[0] - a.at[0], dy = to[1] - a.at[1];
    a.at = [r2(to[0]), r2(to[1])];
    if (a.footprint) { a.footprint = a.footprint.map((ring) => ring.map(([x, y]): XY => [r2(x + dx), r2(y + dy)])); moved.push(a.footprint); }
    for (const po of pois) if (po.id === a.id) { po.anchor = [r2(po.anchor[0] + dx), r2(po.anchor[1] + dy)]; po.node = nearestNode(po.anchor); }
  }
  const polys = moved.map((poly) => ({ poly, box: bbox(poly) }));
  const before = trees.length;
  for (let i = trees.length - 1; i >= 0; i--) {
    const p: XY = [trees[i][0], trees[i][1]];
    if (polys.some((k) => p[0] > k.box.minX - 1 && p[0] < k.box.maxX + 1 && p[1] > k.box.minY - 1 && p[1] < k.box.maxY + 1 &&
      (inPoly(p, k.poly) || distToPoly(p, k.poly) < 1))) trees.splice(i, 1);
  }
  console.log(`✓ Surilgan attraksionlar: ${Object.keys(ATTRACTION_MOVES).map((n) => `№${n}`).join(', ')}` +
    (before !== trees.length ? ` (${before - trees.length} ta daraxt olib tashlandi)` : ''));
}

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
const SURFACE_ORDER = ['rubber', 'rubber_green', 'rubber_edge'] as const;
const surfaces: NonNullable<ParkData['surfaces']> = SURFACE_ORDER.flatMap((kind) =>
  layer('surface').filter((f) => (f.properties as { surface?: string }).surface === kind).flatMap(polysOf).map((poly) => ({ kind, poly })));
console.log(`✓ Yumshoq qoplama: ${surfaces.length} bo'lak`);
console.log(`✓ Fontanlar: ${fountains.length}, gulzorlar: ${beds.length}`);

// ---------- Panjaralar: maydoncha cheti bo'ylab, kirishlarda va qo'shni obyekt bilan umumiy chegarada uzilgan ----------
const fences: NonNullable<ParkData['fences']> = [];
{
  const deg = new Array(nodes.length).fill(0);
  for (const [a, b] of edges) { deg[a]++; deg[b]++; }
  const distSeg = (p: XY, a: XY, b: XY) => {
    const dx = b[0] - a[0], dy = b[1] - a[1], L = dx * dx + dy * dy || 1;
    const t = Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L));
    return Math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy);
  };
  const distRing = (p: XY, ring: XY[]) => Math.min(...ring.slice(1).map((q, i) => distSeg(p, ring[i], q)));
  for (const [num, cfg] of Object.entries(FENCES)) {
    const att = attractions.find((a) => a.num === num && a.footprint);
    const area = playgrounds.find((a) => a.id === `n${num.replace('.', '-')}`) ??
      (att ? { id: att.id, name: att.name, poly: att.footprint! } : undefined);
    if (!area) { console.warn(`⚠ Panjara ${num}: maydoncha topilmadi`); continue; }
    const ring = area.poly[0];
    const skipRings = (cfg.skip ?? []).flatMap((n) => attractions.filter((a) => a.num === n).map((a) => a.footprint![0]));
    // kirishlar: maydoncha tashqarisidagi, chegaraga yaqin yo'l uchlari (bitta qirrali tugunlar)
    const gates = nodes.filter((n, i) => deg[i] === 1 && comp[i] === mainComp && !inPoly(n, area.poly) && distRing(n, ring) < cfg.gateReach);
    const gatePts = [...gates, ...((cfg.gates ?? []) as XY[])].map((g) => nearestOnRing(g, ring));
    // chegarani 0.5 m qadam bilan yurib, panjara bo'ladigan nuqtalarni ketma-ket bo'laklarga yig'amiz
    const pts: { p: XY; on: boolean }[] = [];
    for (let i = 0; i < ring.length - 1; i++) {
      const [a, b] = [ring[i], ring[i + 1]];
      const n = Math.max(1, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / 0.5));
      for (let k = 0; k < n; k++) {
        const p: XY = [a[0] + ((b[0] - a[0]) * k) / n, a[1] + ((b[1] - a[1]) * k) / n];
        const on = !skipRings.some((r) => distRing(p, r) < 1.2) &&
          !gatePts.some((g) => Math.hypot(g[0] - p[0], g[1] - p[1]) < cfg.gateWidth / 2);
        pts.push({ p, on });
      }
    }
    // halqa: birinchi "on" bo'lmagan nuqtadan boshlaymiz, bo'laklar uzilmasin
    const start = Math.max(0, pts.findIndex((x) => !x.on));
    const lines: XY[][] = [];
    let cur: XY[] = [];
    for (let k = 0; k <= pts.length; k++) {
      const x = pts[(start + k) % pts.length];
      if (x.on) cur.push([r2(x.p[0]), r2(x.p[1])]);
      else { if (cur.length > 1) lines.push(cur); cur = []; }
    }
    if (cur.length > 1) lines.push(cur);
    fences.push({ id: `fence-${num}`, height: cfg.height, lines, ...(cfg.color ? { color: cfg.color } : {}) });
    console.log(`✓ Panjara ${num}: ${lines.length} bo'lak, ${Math.round(lines.reduce((s, l) => s + l.length * 0.5, 0))} m, ${gatePts.length} kirish`);
  }
}

// ---------- Natija ----------
const roadKm = edges.reduce((s, e) => s + e[2], 0) / 1000;
const data: ParkData = {
  bounds,
  ground,
  groundCut,
  water: waterAreas,
  roads: roadsOut,
  bridges,
  parking,
  playgrounds,
  buildings,
  attractions,
  trees,
  lamps,
  fountains,
  beds,
  surfaces,
  fences,
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

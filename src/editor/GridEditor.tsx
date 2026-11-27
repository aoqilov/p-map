// 2D setka tahrirlagich (faqat dev / demo: manzil oxiriga #editor). Fayllarga yozmaydi: hamma o'zgarish matn bo'lib chiqadi —
// uni nusxalab Claude'ga yuborasiz, u fayllarga qo'yadi (building.ts / place.ts / shape.json / config) va xaritani qayta yig'adi.
// Imkoniyatlar: bino/attraksionni ko'chirish, o'lchamini va burilishini o'zgartirish; yangi bino (to'rtburchak) va erkin shakl
// (plitka, terrasa, maysa...) chizish; mavjud shakllar (PAVED_AREAS, decor/*/shape.json) nuqtalarini sudrash; olib tashlashni belgilash.
import { useEffect, useMemo, useRef, useState } from 'react';
import parkJson from '../map/park.json';
import { ATTRACTION_SIZES, BUILDING_OVERRIDES, EXTRA_BUILDINGS, KASSA, PAVED_AREAS } from '../map/config';
import type { ParkData, Poly } from '../map/types';
import type { XY } from '../map/projection';
import type { BuildingDef, PlanModelDef } from '../decor/define';
import type { AttractionPlaceDef } from '../attractions/define';
import { ATTRACTIONS, ATTRACTIONS_BY_NAME } from '../attractions';
import './editor.css';

const park = parkJson as unknown as ParkData;

/** Iz: markaz, old yo'nalish (gradus), eni (old tomon bo'ylab) × chuqurligi, m — build-genplan dagi rectAround bilan bir xil */
interface Box { at: XY; bearing: number; width: number; depth: number; height?: number;
  /** Plandagi attraksion modeli qaragan yo'nalish (config.ts → bearing), gradus. Maydoncha (bearing) plandagidek qoladi — xaritada ham shunday */
  face?: number }
/** Yangi bino balandligi (standart), m */
const DEFAULT_H = 3.5;
type ItemKind = 'decor' | 'place' | 'plan' | 'attr' | 'new';
interface Item { key: string; id: string; name: string; source: string; kind: ItemKind; box: Box; circle?: boolean;
  /** Kassa budkasi: o'lchami qat'iy (faqat ko'chirish va burish) */
  kassa?: boolean }
interface Shape { key: string; id: string; name: string; source: string; kind: 'paved' | 'decor' | 'new'; poly: XY[]; purpose?: string }
/** Yangi chizilganlar */
interface Added { id: string; name: string; type: 'bino' | 'shakl' | 'kassa'; box?: Box; poly?: XY[]; purpose?: string }
interface Store { edits: Record<string, Box>; shapes: Record<string, XY[]>; added: Added[]; removed: string[] }
type Tool = 'select' | 'rect' | 'poly' | 'kassa';
/** Kassa budkasi izi (src/decor/kassa modeli korpusi), m */
const KASSA_BOX = { width: 1.36, depth: 0.96, height: 2.77 };
/** Kassa kattaligi (KASSA → scale, 1 — haqiqiy o'lcham) bo'yicha iz */
const kassaBox = (sc: number) => ({ width: r2(KASSA_BOX.width * sc), depth: r2(KASSA_BOX.depth * sc), height: r2(KASSA_BOX.height * sc) });
const kassaScale = (b: Box) => Math.round((b.width / KASSA_BOX.width) * 100) / 100;

const PURPOSES = ['plitka (yo\'l)', 'maysa', 'terrasa', 'bino izi', 'suv', 'boshqa'];

const rad = (d: number) => (d * Math.PI) / 180;
const axes = (b: number) => ({ r: [Math.cos(rad(b)), -Math.sin(rad(b))] as XY, f: [Math.sin(rad(b)), Math.cos(rad(b))] as XY });
const r2 = (v: number) => Math.round(v * 100) / 100;
const norm360 = (b: number) => r2(((b % 360) + 360) % 360);
const fmtPoly = (pl: XY[]) => `[${pl.map(([x, y]) => `[${x}, ${y}]`).join(', ')}]`;

function corners(bx: Box): XY[] {
  const { r, f } = axes(bx.bearing);
  const pt = (sx: number, sy: number): XY => [
    bx.at[0] + r[0] * sx * bx.width / 2 + f[0] * sy * bx.depth / 2,
    bx.at[1] + r[1] * sx * bx.width / 2 + f[1] * sy * bx.depth / 2,
  ];
  return [pt(-1, -1), pt(1, -1), pt(1, 1), pt(-1, 1)];
}

/** Berilgan burilishda iz atrofidagi to'rtburchak */
function fitBearing(ring: XY[], bearing: number): Box {
  const { r, f } = axes(bearing);
  let r0 = Infinity, r1 = -Infinity, f0 = Infinity, f1 = -Infinity;
  for (const [x, y] of ring) {
    const pr = x * r[0] + y * r[1], pf = x * f[0] + y * f[1];
    r0 = Math.min(r0, pr); r1 = Math.max(r1, pr); f0 = Math.min(f0, pf); f1 = Math.max(f1, pf);
  }
  const mr = (r0 + r1) / 2, mf = (f0 + f1) / 2;
  return { at: [r2(r[0] * mr + f[0] * mf), r2(r[1] * mr + f[1] * mf)], bearing: norm360(bearing), width: r2(r1 - r0), depth: r2(f1 - f0) };
}

/** Eng kichik yuzali to'rtburchak (qirralar yo'nalishlari bo'yicha) — plandagi notekis binolar uchun */
function fitMin(ring: XY[]): Box {
  let best: Box | null = null;
  for (let i = 0; i < ring.length - 1; i++) {
    const [x0, y0] = ring[i], [x1, y1] = ring[i + 1];
    if (Math.hypot(x1 - x0, y1 - y0) < 0.5) continue;
    const b = (Math.atan2(-(y1 - y0), x1 - x0) * 180) / Math.PI;
    const bx = fitBearing(ring, b);
    if (!best || bx.width * bx.depth < best.width * best.depth) best = bx;
  }
  return best ?? fitBearing(ring, 0);
}

const ringOf = (p: Poly) => p[0];

/** Plandagi attraksion modelining burilishi (config.ts → bearing), modeli yo'q bo'lsa — null */
const modelBearing = (a: { num?: string | null; name: string }) => {
  const d = (a.num ? ATTRACTIONS[a.num] : undefined) ?? ATTRACTIONS_BY_NAME[a.name];
  return d?.model ? d.bearing ?? 0 : null;
};

function collectItems(): Item[] {
  const items: Item[] = [];
  const used = new Set<string>();
  const decor = import.meta.glob<BuildingDef | PlanModelDef | (BuildingDef | PlanModelDef)[]>('../decor/*/building.ts', { eager: true, import: 'default' });
  for (const [path, mod] of Object.entries(decor)) {
    const arr = [mod].flat();
    const file = `src/decor/${path.split('/')[2]}/building.ts`;
    arr.forEach((d, i) => {
      const source = arr.length > 1 ? `${file} [${i}]` : file;
      if ('plan' in d) {
        const b = park.buildings.find((x) => x.id === d.plan);
        const box: Box = { ...(d.rect ? { at: d.at, bearing: d.bearing, ...d.rect } : b ? fitBearing(ringOf(b.poly), d.bearing) : { at: d.at, bearing: d.bearing, width: 5, depth: 5 }),
          height: d.height ?? b?.height ?? DEFAULT_H };
        items.push({ key: source, id: d.plan, name: d.name ?? b?.name ?? d.plan, source, kind: 'decor', box });
        used.add(d.plan);
      } else {
        items.push({ key: source, id: d.id, name: d.name, source, kind: 'decor', circle: d.shape === 'circle',
          box: { at: d.at, bearing: d.bearing, width: d.width, depth: d.shape === 'circle' ? d.width : d.depth, height: d.height } });
        used.add(d.id);
      }
    });
  }
  const places = import.meta.glob<AttractionPlaceDef | AttractionPlaceDef[]>('../attractions/*/place.ts', { eager: true, import: 'default' });
  const placeNames = new Set<string>();
  for (const [path, mod] of Object.entries(places)) {
    const arr = [mod].flat();
    const file = `src/attractions/${path.split('/')[2]}/place.ts`;
    arr.forEach((d, i) => {
      const source = arr.length > 1 ? `${file} [${i}]` : file;
      items.push({ key: source, id: d.name, name: d.name, source, kind: 'place', box: { at: d.at, bearing: d.bearing, width: d.width, depth: d.depth, height: d.height } });
      placeNames.add(d.name);
    });
  }
  // Kassa budkalari (config/kassa.ts → KASSA, `at` berilganlari): iz — budka korpusi (src/decor/kassa) × scale
  for (const k of KASSA) {
    if (!k.at) continue;
    items.push({ key: `kassa:${k.id}`, id: k.id, name: k.label, source: 'src/map/config/kassa.ts → KASSA (at, bearing, scale)', kind: 'decor',
      kassa: true, box: { at: k.at, bearing: k.bearing ?? 180, ...kassaBox(k.scale ?? 1) } });
  }
  for (const e of EXTRA_BUILDINGS) {
    items.push({ key: `extra:${e.id}`, id: e.id, name: e.name, source: 'src/map/config/map.ts → EXTRA_BUILDINGS', kind: 'plan',
      box: 'poly' in e ? { ...fitMin([...e.poly, e.poly[0]]), height: e.height } : { at: e.at, bearing: e.bearing, width: e.width, depth: e.depth, height: e.height } });
    used.add(e.id);
  }
  for (const b of park.buildings) {
    if (used.has(b.id)) continue;
    const o = BUILDING_OVERRIDES[b.id];
    items.push(o
      ? { key: `plan:${b.id}`, id: b.id, name: b.name, source: 'src/map/config/map.ts → BUILDING_OVERRIDES', kind: 'plan', box: { ...o, height: o.height ?? b.height } }
      : { key: `plan:${b.id}`, id: b.id, name: b.name, source: 'park.json (plandagi bino)', kind: 'plan', box: { ...fitMin(ringOf(b.poly)), height: b.height } });
  }
  for (const a of park.attractions) {
    if (placeNames.has(a.name) || !a.footprint) continue;
    items.push({ key: `attr:${a.id}`, id: a.id, name: a.name, source: `park.json (plandagi attraksion${a.num ? ` №${a.num}` : ''})${modelBearing(a) !== null ? ' + config.ts bearing' : ''}`, kind: 'attr',
      // maydoncha — plandagi shakli (xaritada burilmaydi), face — model qaragan yo'nalish (faqat model buriladi)
      box: { ...fitMin(ringOf(a.footprint)), ...(modelBearing(a) !== null ? { face: norm360(modelBearing(a)!) } : {}),
        height: a.height ?? ATTRACTION_SIZES[a.size].height } });
  }
  return items;
}

function collectShapes(): Shape[] {
  const shapes: Shape[] = PAVED_AREAS.map((a) => ({ key: `paved:${a.id}`, id: a.id, name: `Plitka: ${a.id}`, kind: 'paved' as const,
    source: 'src/map/config/map.ts → PAVED_AREAS', poly: a.poly.map(([x, y]) => [x, y] as XY), purpose: 'plitka (yo\'l)' }));
  const files = import.meta.glob<{ poly: [number, number][] }>('../decor/*/shape.json', { eager: true, import: 'default' });
  for (const [path, mod] of Object.entries(files)) {
    const dir = path.split('/')[2];
    shapes.push({ key: `shape:${dir}`, id: dir, name: `Shakl: ${dir}`, kind: 'decor' as const, source: `src/decor/${dir}/shape.json`,
      poly: mod.poly.map(([x, y]) => [x, y] as XY) });
  }
  return shapes;
}

const STORE = 'park-grid-editor';
const EMPTY: Store = { edits: {}, shapes: {}, added: [], removed: [] };
const loadStore = (): Store => {
  try {
    const raw = JSON.parse(localStorage.getItem(STORE) ?? '{}');
    if (raw && typeof raw === 'object' && 'edits' in raw) return { ...EMPTY, ...raw };
    return { ...EMPTY, edits: raw ?? {} }; // eski format: faqat edits
  } catch { return EMPTY; }
};
const saveStore = (s: Store) => {
  try { localStorage.setItem(STORE, JSON.stringify(s)); } catch { /* yo'q bo'lsa — mayli */ }
};
const sameBox = (a: Box, b: Box) => a.at[0] === b.at[0] && a.at[1] === b.at[1] && a.bearing === b.bearing && a.face === b.face && a.width === b.width && a.depth === b.depth &&
  (a.height ?? DEFAULT_H) === (b.height ?? DEFAULT_H);
/** Deyarli bir xil (0.08 m / 0.5° gacha farq — maydoncha shaklidan qayta hisoblashdagi xatolik; eng kichik qadam 0.1 m — u tushmaydi): eski yozuv tushadi */
const NEAR = 0.08;
const nearBox = (a: Box, b: Box) => Math.abs(a.at[0] - b.at[0]) <= NEAR && Math.abs(a.at[1] - b.at[1]) <= NEAR &&
  Math.abs(((a.bearing - b.bearing + 540) % 360) - 180) <= 0.5 && Math.abs((((a.face ?? 0) - (b.face ?? 0) + 540) % 360) - 180) <= 0.5 && Math.abs(a.width - b.width) <= NEAR && Math.abs(a.depth - b.depth) <= NEAR &&
  (a.height ?? DEFAULT_H) === (b.height ?? DEFAULT_H);
const samePoly = (a: XY[], b: XY[]) => a.length === b.length && a.every((q, i) => q[0] === b[i][0] && q[1] === b[i][1]);

/**
 * Fayllarga allaqachon qo'yilgan yozuvlarni olib tashlash: o'zgarish asl qiymatga (deyarli) teng, shakl o'zgarmagan,
 * olib tashlanadigan narsa endi yo'q, yangi bino / shakl xuddi shu joy va o'lcham bilan endi mavjud
 */
function cleanStore(s: Store, baseItems: Item[], baseShapes: Shape[]): Store {
  return {
    ...s,
    // eski yozuvlarda balandlik yo'q — asl qiymatdan olinadi
    edits: Object.fromEntries(Object.entries(s.edits)
      .map(([key, b]): [string, Box] => {
        const it = baseItems.find((i) => i.key === key);
        // eski yozuv (attraksion burilishi to'rtburchakning o'zida edi): u — model yo'nalishi, maydoncha plandagidek
        const old = it?.box.face !== undefined && b.face === undefined;
        return [key, { ...b, ...(old ? { face: b.bearing, bearing: it!.box.bearing, width: it!.box.width, depth: it!.box.depth } : {}), height: b.height ?? it?.box.height }];
      })
      .filter(([key, b]) => { const it = baseItems.find((i) => i.key === key); return it && !nearBox(b, it.box); })),
    shapes: Object.fromEntries(Object.entries(s.shapes).filter(([key, pl]) => { const sh = baseShapes.find((x) => x.key === key); return sh && !samePoly(pl, sh.poly); })),
    removed: s.removed.filter((k) => baseItems.some((i) => i.key === k) || baseShapes.some((x) => x.key === k)),
    added: s.added.filter((a) => (a.type !== 'shakl'
      ? !baseItems.some((i) => nearBox(i.box, { ...a.box!, height: a.box!.height ?? DEFAULT_H }))
      : !baseShapes.some((x) => samePoly(x.poly, a.poly!)))),
  };
}

type Drag =
  | { kind: 'pan'; sx: number; sy: number; cx: number; cy: number }
  | { kind: 'move'; start: XY; box: Box }
  | { kind: 'resize'; hx: number; hy: number; box: Box }
  | { kind: 'rotate'; box: Box }
  | { kind: 'vertex'; i: number }
  | { kind: 'shape-move'; start: XY; poly: XY[] }
  | { kind: 'draw-rect'; start: XY };

export default function GridEditor() {
  const baseItems = useMemo(collectItems, []);
  const baseShapes = useMemo(collectShapes, []);
  // fayllarga allaqachon qo'yilgan o'zgarishlar (asl qiymatga teng bo'lib qolgan) — ro'yxatdan tushadi
  const [store, setStore] = useState<Store>(() => cleanStore(loadStore(), baseItems, baseShapes));
  // fayllar o'zgarib, sahifa qayta yuklanmasdan yangilansa (Vite) — fayllarga qo'yilgan yozuvlar shu zahoti tushadi
  useEffect(() => setStore((s) => cleanStore(s, baseItems, baseShapes)), [baseItems, baseShapes]);
  const [tool, setTool] = useState<Tool>('select');
  const [sel, setSel] = useState<string | null>(null);
  const [selV, setSelV] = useState<number | null>(null);
  const [draftPoly, setDraftPoly] = useState<XY[]>([]);
  const [draftRect, setDraftRect] = useState<[XY, XY] | null>(null);
  const [hover, setHover] = useState<XY | null>(null);
  const [snap, setSnap] = useState(0.5);
  const [view, setView] = useState({ cx: -40, cy: 120, s: 5 });
  const [size, setSize] = useState({ w: 800, h: 600 });
  const [copied, setCopied] = useState(false);
  const [filter, setFilter] = useState('');
  const svgRef = useRef<SVGSVGElement>(null);
  const drag = useRef<Drag | null>(null);
  const pointers = useRef(new Map<number, XY>());
  const pinch = useRef<{ d: number; s: number } | null>(null);
  /** Fon surilganmi (unda bosish tanlovni bekor qilmaydi / nuqta qo'shmaydi) */
  const panned = useRef(false);

  useEffect(() => saveStore(store), [store]);
  useEffect(() => {
    const el = svgRef.current!;
    const ro = new ResizeObserver(() => setSize({ w: el.clientWidth, h: el.clientHeight }));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // ---------- ma'lumot: mavjud + yangi ----------
  const items: Item[] = useMemo(() => [...baseItems, ...store.added.filter((a) => a.type === 'bino').map((a) => ({
    key: `new:${a.id}`, id: a.id, name: a.name, source: 'YANGI bino', kind: 'new' as const, box: a.box!,
  })), ...store.added.filter((a) => a.type === 'kassa').map((a) => ({
    key: `new:${a.id}`, id: a.id, name: a.name, source: 'YANGI kassa', kind: 'new' as const, box: a.box!, kassa: true,
  }))], [baseItems, store.added]);
  const shapes: Shape[] = useMemo(() => [...baseShapes, ...store.added.filter((a) => a.type === 'shakl').map((a) => ({
    key: `new:${a.id}`, id: a.id, name: a.name, source: 'YANGI shakl', kind: 'new' as const, poly: a.poly!, purpose: a.purpose,
  }))], [baseShapes, store.added]);

  const boxOf = (it: Item) => (it.kind === 'new' ? it.box : store.edits[it.key] ?? it.box);
  const polyOf = (sh: Shape) => (sh.kind === 'new' ? sh.poly : store.shapes[sh.key] ?? sh.poly);
  const selItem = items.find((i) => i.key === sel) ?? null;
  const selShape = shapes.find((s) => s.key === sel) ?? null;
  const isRemoved = (key: string) => store.removed.includes(key);
  const updAdded = (id: string, patch: Partial<Added>) =>
    setStore((s) => ({ ...s, added: s.added.map((a) => (a.id === id ? { ...a, ...patch } : a)) }));

  const setBox = (it: Item, b: Box) => {
    // kassa — proporsiya saqlanadi: eni o'zgarsa shundan, aks holda chuqurligi / balandligidan kattalik (0.5–4×)
    const cur = boxOf(it);
    const sc = it.kassa ? Math.min(4, Math.max(0.5, b.width !== cur.width ? b.width / KASSA_BOX.width
      : b.depth !== cur.depth ? b.depth / KASSA_BOX.depth : (b.height ?? cur.height ?? KASSA_BOX.height) / KASSA_BOX.height)) : 1;
    const clean: Box = it.kassa
      ? { at: [r2(b.at[0]), r2(b.at[1])], bearing: norm360(b.bearing), ...kassaBox(Math.round(sc * 100) / 100) }
      : { at: [r2(b.at[0]), r2(b.at[1])], bearing: norm360(b.bearing), ...(b.face !== undefined ? { face: norm360(b.face) } : {}), width: r2(b.width), depth: r2(it.circle ? b.width : b.depth),
        height: r2(Math.max(0.5, b.height ?? DEFAULT_H)) };
    if (it.kind === 'new') { updAdded(it.id, { box: clean }); return; }
    setStore((s) => {
      const edits = { ...s.edits };
      if (sameBox(clean, it.box)) delete edits[it.key]; else edits[it.key] = clean;
      return { ...s, edits };
    });
  };
  const setPoly = (sh: Shape, pl: XY[]) => {
    const clean = pl.map(([x, y]) => [r2(x), r2(y)] as XY);
    if (sh.kind === 'new') { updAdded(sh.id, { poly: clean }); return; }
    setStore((s) => {
      const sp = { ...s.shapes };
      if (samePoly(clean, sh.poly)) delete sp[sh.key]; else sp[sh.key] = clean;
      return { ...s, shapes: sp };
    });
  };
  const toggleRemove = (key: string) =>
    setStore((s) => ({ ...s, removed: s.removed.includes(key) ? s.removed.filter((k) => k !== key) : [...s.removed, key] }));
  const deleteAdded = (id: string) => { setStore((s) => ({ ...s, added: s.added.filter((a) => a.id !== id) })); setSel(null); };
  const nextId = () => {
    let n = 1;
    while (store.added.some((a) => a.id === `yangi-${n}`) || baseItems.some((i) => i.id === `yangi-${n}`)) n++;
    return `yangi-${n}`;
  };
  /** Keyingi kassa raqami: mavjud va yangi "K-<n>" lardan eng kattasi + 1 */
  const nextKassaId = () => {
    const nums = [...baseItems.filter((i) => i.kassa).map((i) => i.id), ...store.added.filter((a) => a.type === 'kassa').map((a) => a.id)]
      .map((id) => /^K-(\d+)$/.exec(id)?.[1]).filter(Boolean).map(Number);
    return `K-${nums.length ? Math.max(...nums) + 1 : 1}`;
  };
  const placeKassa = (p: XY) => {
    const id = nextKassaId();
    setStore((s) => ({ ...s, added: [...s.added, { id, name: `Kassa ${id}`, type: 'kassa', box: { at: p, bearing: 180, ...KASSA_BOX } }] }));
    setTool('select');
    setSel(`new:${id}`);
  };

  // ---------- park metr ↔ ekran px (shimol — tepada) ----------
  const toScr = ([x, y]: XY): XY => [(x - view.cx) * view.s + size.w / 2, (view.cy - y) * view.s + size.h / 2];
  const toPark = (px: number, py: number): XY => [(px - size.w / 2) / view.s + view.cx, view.cy - (py - size.h / 2) / view.s];
  const evPark = (e: { clientX: number; clientY: number }): XY => {
    const rc = svgRef.current!.getBoundingClientRect();
    return toPark(e.clientX - rc.left, e.clientY - rc.top);
  };
  const sn = (v: number) => r2(Math.round(v / snap) * snap);
  const snapPt = (q: XY): XY => [sn(q[0]), sn(q[1])];
  const path = (ring: XY[], close = true) => ring.map((q, i) => `${i ? 'L' : 'M'}${toScr(q).map((v) => v.toFixed(1)).join(',')}`).join('') + (close ? 'Z' : '');
  const polyPath = (p: Poly) => p.map((r) => path(r)).join('');

  // ---------- chizishni yakunlash ----------
  const finishPoly = () => {
    if (draftPoly.length < 3) return;
    const id = nextId();
    setStore((s) => ({ ...s, added: [...s.added, { id, name: `Yangi shakl ${id.split('-')[1]}`, type: 'shakl', poly: draftPoly, purpose: PURPOSES[0] }] }));
    setDraftPoly([]);
    setTool('select');
    setSel(`new:${id}`);
  };
  const cancelDraw = () => { setDraftPoly([]); setDraftRect(null); setTool('select'); };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement).closest('input, textarea, select')) return;
      if (e.key === 'Escape') { if (tool !== 'select') cancelDraw(); else { setSel(null); setSelV(null); } }
      if (e.key === 'Enter' && tool === 'poly') finishPoly();
      if (e.key === 'Backspace' && tool === 'poly') { e.preventDefault(); setDraftPoly((d) => d.slice(0, -1)); }
      if ((e.key === 'Delete' || e.key === 'Backspace') && tool === 'select' && selShape && selV !== null) {
        const pl = polyOf(selShape);
        if (pl.length > 3) { setPoly(selShape, pl.filter((_, i) => i !== selV)); setSelV(null); }
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  // ---------- sichqoncha / barmoq ----------
  const onDown = (e: React.PointerEvent, d: Drag | null) => {
    e.stopPropagation();
    svgRef.current!.setPointerCapture(e.pointerId);
    pointers.current.set(e.pointerId, [e.clientX, e.clientY]);
    if (pointers.current.size === 2) {
      const [a, b] = [...pointers.current.values()];
      pinch.current = { d: Math.hypot(a[0] - b[0], a[1] - b[1]), s: view.s };
      drag.current = null;
      setDraftRect(null);
      return;
    }
    panned.current = false;
    if (!d && tool === 'rect') {
      const p = snapPt(evPark(e));
      drag.current = { kind: 'draw-rect', start: p };
      setDraftRect([p, p]);
      return;
    }
    drag.current = d ?? { kind: 'pan', sx: e.clientX, sy: e.clientY, cx: view.cx, cy: view.cy };
  };
  const onMove = (e: React.PointerEvent) => {
    if (tool === 'poly' || tool === 'kassa') setHover(snapPt(evPark(e)));
    if (!pointers.current.has(e.pointerId)) return;
    pointers.current.set(e.pointerId, [e.clientX, e.clientY]);
    if (pinch.current && pointers.current.size === 2) {
      const [a, b] = [...pointers.current.values()];
      const s = Math.min(60, Math.max(0.5, pinch.current.s * Math.hypot(a[0] - b[0], a[1] - b[1]) / pinch.current.d));
      setView((v) => ({ ...v, s }));
      return;
    }
    const d = drag.current;
    if (!d) return;
    if (d.kind === 'pan') {
      if (Math.hypot(e.clientX - d.sx, e.clientY - d.sy) > 4) panned.current = true;
      setView((v) => ({ ...v, cx: d.cx - (e.clientX - d.sx) / v.s, cy: d.cy + (e.clientY - d.sy) / v.s }));
      return;
    }
    const p = evPark(e);
    if (d.kind === 'draw-rect') { setDraftRect([d.start, snapPt(p)]); return; }
    if (d.kind === 'vertex' && selShape) {
      const pl = [...polyOf(selShape)];
      pl[d.i] = snapPt(p);
      setPoly(selShape, pl);
      return;
    }
    if (d.kind === 'shape-move' && selShape) {
      const dx = sn(p[0] - d.start[0]), dy = sn(p[1] - d.start[1]);
      setPoly(selShape, d.poly.map(([x, y]) => [x + dx, y + dy] as XY));
      return;
    }
    if (!selItem) return;
    if (d.kind === 'move') {
      setBox(selItem, { ...d.box, at: [sn(d.box.at[0] + p[0] - d.start[0]), sn(d.box.at[1] + p[1] - d.start[1])] });
    } else if (d.kind === 'rotate') {
      const a = (Math.atan2(p[0] - d.box.at[0], p[1] - d.box.at[1]) * 180) / Math.PI;
      const v = e.shiftKey ? Math.round(a / 15) * 15 : Math.round(a);
      setBox(selItem, d.box.face !== undefined ? { ...d.box, face: v } : { ...d.box, bearing: v });
    } else if (d.kind === 'resize') {
      // qarama-qarshi tomon joyida qoladi
      const { r, f } = axes(d.box.bearing);
      const lx = (p[0] - d.box.at[0]) * r[0] + (p[1] - d.box.at[1]) * r[1];
      const ly = (p[0] - d.box.at[0]) * f[0] + (p[1] - d.box.at[1]) * f[1];
      let w = d.box.width, dp = d.box.depth, cr = 0, cf = 0;
      if (d.hx) { const o = -d.hx * d.box.width / 2; w = Math.max(snap, sn((lx - o) * d.hx)); cr = o + d.hx * w / 2; }
      if (d.hy) { const o = -d.hy * d.box.depth / 2; dp = Math.max(snap, sn((ly - o) * d.hy)); cf = o + d.hy * dp / 2; }
      if (selItem.circle) { dp = w; cf = 0; cr = 0; }
      setBox(selItem, { ...d.box, width: w, depth: dp,
        at: [d.box.at[0] + r[0] * cr + f[0] * cf, d.box.at[1] + r[1] * cr + f[1] * cf] });
    }
  };
  const onUp = (e: React.PointerEvent) => {
    pointers.current.delete(e.pointerId);
    if (pointers.current.size < 2) pinch.current = null;
    const d = drag.current;
    drag.current = null;
    if (d?.kind === 'draw-rect' && draftRect) {
      const [a, b] = draftRect;
      const w = Math.abs(b[0] - a[0]), h = Math.abs(b[1] - a[1]);
      setDraftRect(null);
      panned.current = true; // ketidan keladigan click yangi binoning tanlovini bekor qilmasin
      if (w >= 1 && h >= 1) {
        const id = nextId();
        const box: Box = { at: [r2((a[0] + b[0]) / 2), r2((a[1] + b[1]) / 2)], bearing: 0, width: r2(w), depth: r2(h), height: DEFAULT_H };
        setStore((s) => ({ ...s, added: [...s.added, { id, name: `Yangi bino ${id.split('-')[1]}`, type: 'bino', box }] }));
        setTool('select');
        setSel(`new:${id}`);
      }
    }
  };
  const onClick = (e: React.MouseEvent) => {
    if (panned.current) return;
    if (tool === 'kassa') { placeKassa(snapPt(evPark(e))); return; }
    if (tool === 'poly') {
      const p = snapPt(evPark(e));
      if (draftPoly.length >= 3) {
        const f = toScr(draftPoly[0]), c = toScr(p);
        if (Math.hypot(f[0] - c[0], f[1] - c[1]) < 12) { finishPoly(); return; }
      }
      setDraftPoly((d) => [...d, p]);
      return;
    }
    if (tool === 'select' && !(e.target as Element).closest('.g-item, .g-shape, .g-h, .g-rot, .g-v')) { setSel(null); setSelV(null); }
  };
  const onWheel = (e: React.WheelEvent) => {
    const p = evPark(e);
    const s = Math.min(60, Math.max(0.5, view.s * Math.exp(-e.deltaY * 0.0015)));
    const rc = svgRef.current!.getBoundingClientRect();
    const px = e.clientX - rc.left, py = e.clientY - rc.top;
    setView({ s, cx: p[0] - (px - size.w / 2) / s, cy: p[1] + (py - size.h / 2) / s });
  };
  const focusAt = (c: XY, ext: number) =>
    setView((v) => ({ cx: c[0], cy: c[1], s: Math.max(v.s, Math.min(20, 0.5 * Math.min(size.w, size.h) / Math.max(ext, 1))) }));
  const focusItem = (it: Item) => { setTool('select'); setSel(it.key); setSelV(null); const b = boxOf(it); focusAt(b.at, Math.max(b.width, b.depth)); };
  const focusShape = (sh: Shape) => {
    setTool('select'); setSel(sh.key); setSelV(null);
    const pl = polyOf(sh);
    const xs = pl.map((q) => q[0]), ys = pl.map((q) => q[1]);
    focusAt([(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2], Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)));
  };

  // ---------- setka ----------
  const grid = useMemo(() => {
    const [x0, y1] = toPark(0, 0), [x1, y0] = toPark(size.w, size.h);
    const minor = view.s > 12 ? 1 : view.s > 3 ? 5 : 10;
    const major = minor * (minor === 1 ? 5 : 2);
    const lines: { d: string; major: boolean }[] = [];
    for (let x = Math.floor(x0 / minor) * minor; x <= x1; x += minor) {
      const sx = toScr([x, 0])[0];
      lines.push({ d: `M${sx},0V${size.h}`, major: Math.abs(x % major) < 1e-6 });
    }
    for (let y = Math.floor(y0 / minor) * minor; y <= y1; y += minor) {
      const sy = toScr([0, y])[1];
      lines.push({ d: `M0,${sy}H${size.w}`, major: Math.abs(y % major) < 1e-6 });
    }
    return { lines, minor };
    // toScr/toPark faqat view va size ga bog'liq
  }, [view, size]);

  // ---------- natija matni ----------
  const changedItems = baseItems.filter((it) => store.edits[it.key] && !isRemoved(it.key));
  const changedShapes = baseShapes.filter((sh) => store.shapes[sh.key] && !isRemoved(sh.key));
  const removedAll = [...baseItems.filter((it) => isRemoved(it.key)), ...baseShapes.filter((sh) => isRemoved(sh.key))];
  const total = changedItems.length + changedShapes.length + store.added.length + removedAll.length;
  const blocks: string[] = [];
  if (changedItems.length) blocks.push('== O\'ZGARTIRILDI ==\n' + changedItems.map((it) => {
    const b = store.edits[it.key], was = it.box;
    return `${it.id} — ${it.name}\n  fayl: ${it.source}\n  at: [${b.at[0]}, ${b.at[1]}], bearing: ${b.face ?? b.bearing}${b.face !== undefined ? ' (model)' : ''}, width: ${b.width}, depth: ${b.depth}, height: ${b.height ?? DEFAULT_H}${it.kassa ? `, scale: ${kassaScale(b)}` : ''}` +
      `\n  (oldin: at [${was.at[0]}, ${was.at[1]}], bearing ${was.face ?? was.bearing}, ${was.width} × ${was.depth}, balandligi ${was.height ?? DEFAULT_H})`;
  }).join('\n\n'));
  if (changedShapes.length) blocks.push('== SHAKL O\'ZGARDI ==\n' + changedShapes.map((sh) =>
    `${sh.id} — ${sh.name}\n  fayl: ${sh.source}\n  poly: ${fmtPoly(store.shapes[sh.key])}`).join('\n\n'));
  const newB = store.added.filter((a) => a.type === 'bino');
  if (newB.length) blocks.push('== YANGI BINO ==\n' + newB.map((a) =>
    `${a.id} — "${a.name}"\n  at: [${a.box!.at[0]}, ${a.box!.at[1]}], bearing: ${a.box!.bearing}, width: ${a.box!.width}, depth: ${a.box!.depth}, height: ${a.box!.height ?? DEFAULT_H}`).join('\n\n'));
  const newK = store.added.filter((a) => a.type === 'kassa');
  if (newK.length) blocks.push('== YANGI KASSA == (src/map/config/kassa.ts → KASSA)\n' + newK.map((a) =>
    `${a.id} — "${a.name}"\n  at: [${a.box!.at[0]}, ${a.box!.at[1]}], bearing: ${a.box!.bearing}, scale: ${kassaScale(a.box!)}`).join('\n\n'));
  const newS = store.added.filter((a) => a.type === 'shakl');
  if (newS.length) blocks.push('== YANGI SHAKL ==\n' + newS.map((a) =>
    `${a.id} — "${a.name}" (vazifasi: ${a.purpose ?? 'boshqa'})\n  poly: ${fmtPoly(a.poly!)}`).join('\n\n'));
  if (removedAll.length) blocks.push('== OLIB TASHLANSIN ==\n' + removedAll.map((x) => `${x.id} — ${x.name}\n  fayl: ${x.source}`).join('\n\n'));
  const text = blocks.join('\n\n');
  const copy = async () => {
    try { await navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1500); } catch { /* textarea'dan qo'lda */ }
  };

  // ---------- chizish yordamchilari ----------
  const sb = selItem ? boxOf(selItem) : null;
  const handles: { hx: number; hy: number }[] = [
    { hx: -1, hy: -1 }, { hx: 1, hy: -1 }, { hx: 1, hy: 1 }, { hx: -1, hy: 1 },
    { hx: 0, hy: -1 }, { hx: 1, hy: 0 }, { hx: 0, hy: 1 }, { hx: -1, hy: 0 },
  ];
  /** Model qaragan tomondagi nuqta (maydoncha chetigacha) */
  const facePt = (b: Box): XY => {
    const t = rad(b.face ?? b.bearing), l = Math.max(b.width, b.depth) / 2;
    return [b.at[0] + Math.sin(t) * l, b.at[1] + Math.cos(t) * l];
  };
  const local = (b: Box, lr: number, lf: number): XY => {
    const { r, f } = axes(b.bearing);
    return [b.at[0] + r[0] * lr + f[0] * lf, b.at[1] + r[1] * lr + f[1] * lf];
  };
  const q = filter.toLowerCase();
  const listItems = items.filter((it) => !q || `${it.id} ${it.name}`.toLowerCase().includes(q));
  const listShapes = shapes.filter((sh) => !q || `${sh.id} ${sh.name}`.toLowerCase().includes(q));
  const selPoly = selShape ? polyOf(selShape) : null;
  const selAdded = sel?.startsWith('new:') ? store.added.find((a) => `new:${a.id}` === sel) ?? null : null;

  const hint = tool === 'kassa'
    ? "Kassa qo'yish: xaritada kassa turadigan joyni bosing. Keyin uni ko'chirasiz, burasiz (sariq qirra — kassa oynasi) va kattaligini o'zgartirasiz. Esc — bekor."
    : tool === 'rect'
    ? 'Bino chizish: xaritada bir burchakdan qarama-qarshi burchakka sudrang. Keyin uni ko\'chirib, burib, o\'lchamini o\'zgartirasiz. Esc — bekor.'
    : tool === 'poly'
      ? 'Shakl chizish: nuqtama-nuqta bosing. Yakunlash — birinchi nuqtani bosing, Enter yoki "Tugatish". Backspace — oxirgi nuqtani o\'chirish, Esc — bekor. Xaritani surish mumkin.'
      : 'Tanlash: bino yoki shaklni bosing. Bo\'sh joyni sudrasangiz xarita suriladi, g\'ildirak — kattalashtirish.';

  return (
    <div className="ged">
      <svg ref={svgRef} className={`ged-map${tool !== 'select' ? ' drawing' : ''}`} onPointerDown={(e) => onDown(e, null)} onPointerMove={onMove}
        onPointerUp={onUp} onPointerCancel={onUp} onWheel={onWheel} onClick={onClick} onPointerLeave={() => setHover(null)}>
        <path d={path(park.ground[0])} className="g-ground" />
        <path d={park.roads.map(polyPath).join('')} className="g-road" />
        {park.water.map((w) => <path key={w.id} d={polyPath(w.poly)} className="g-water" />)}
        {park.playgrounds.map((p) => <path key={p.id} d={polyPath(p.poly)} className="g-play" />)}
        {grid.lines.map((l, i) => <path key={i} d={l.d} className={l.major ? 'g-grid g-major' : 'g-grid'} />)}
        {view.s > 2 && park.trees.map(([x, y, s], i) => {
          const [px, py] = toScr([x, y]);
          return <circle key={i} cx={px} cy={py} r={Math.max(1.5, s * 1.6 * view.s)} className="g-tree" />;
        })}
        {park.buildings.map((b) => <path key={b.id} d={polyPath(b.poly)} className="g-bld" />)}

        {/* shakllar (plitka maydonlari, terrasa, yangi chizilganlar) */}
        {shapes.map((sh) => {
          const pl = polyOf(sh);
          const on = sh.key === sel;
          return (
            <path key={sh.key} d={path(pl)}
              className={`g-shape${on ? ' on' : ''}${(sh.kind === 'new' || store.shapes[sh.key]) ? ' edited' : ''}${isRemoved(sh.key) ? ' removed' : ''}`}
              onPointerDown={(e) => { if (tool !== 'select') return; if (on) onDown(e, { kind: 'shape-move', start: evPark(e), poly: pl }); else { e.stopPropagation(); setSel(sh.key); setSelV(null); } }} />
          );
        })}

        {/* bino va attraksionlar */}
        {items.map((it) => {
          const b = boxOf(it);
          const on = it.key === sel;
          return (
            <g key={it.key} className={`g-item${on ? ' on' : ''}${it.kind === 'attr' ? ' attr' : ''}${it.kassa ? ' kassa' : ''}${(it.kind === 'new' || store.edits[it.key]) ? ' edited' : ''}${isRemoved(it.key) ? ' removed' : ''}`}
              onPointerDown={(e) => { if (tool !== 'select') return; if (on) onDown(e, { kind: 'move', start: evPark(e), box: b }); else { e.stopPropagation(); setSel(it.key); setSelV(null); } }}>
              {it.circle
                ? <circle cx={toScr(b.at)[0]} cy={toScr(b.at)[1]} r={b.width / 2 * view.s} />
                : <path d={path(corners(b))} />}
              {(on || view.s > 4) && (b.face !== undefined
                ? <path className="g-front" d={`M${toScr(b.at).join(',')}L${toScr(facePt(b)).join(',')}`} />
                : <path className="g-front" d={`M${toScr(local(b, -b.width / 2, b.depth / 2)).join(',')}L${toScr(local(b, b.width / 2, b.depth / 2)).join(',')}`} />)}
            </g>
          );
        })}

        {/* tanlangan bino: tutqichlar */}
        {tool === 'select' && selItem && sb && (() => {
          const front = toScr(sb.face !== undefined ? facePt(sb) : local(sb, 0, sb.depth / 2));
          const c = toScr(sb.at);
          const len = Math.hypot(front[0] - c[0], front[1] - c[1]) || 1;
          const rot: XY = [front[0] + (front[0] - c[0]) / len * 36, front[1] + (front[1] - c[1]) / len * 36];
          return (
            <g>
              {handles.filter((h) => !selItem.circle || (h.hx && !h.hy)).map((h) => {
                const [x, y] = toScr(local(sb, h.hx * sb.width / 2, h.hy * sb.depth / 2));
                return <rect key={`${h.hx}${h.hy}`} x={x - 7} y={y - 7} width={14} height={14} className={h.hx && h.hy ? 'g-h' : 'g-h edge'}
                  onPointerDown={(e) => onDown(e, { kind: 'resize', hx: h.hx, hy: h.hy, box: sb })} />;
              })}
              <line x1={front[0]} y1={front[1]} x2={rot[0]} y2={rot[1]} className="g-rotline" />
              <circle cx={rot[0]} cy={rot[1]} r={9} className="g-rot" onPointerDown={(e) => onDown(e, { kind: 'rotate', box: sb })} />
              <circle cx={c[0]} cy={c[1]} r={3} className="g-center" />
              <text x={c[0] + 8} y={c[1] - 8} className="g-coord">↕ {sb.height ?? DEFAULT_H} m</text>
            </g>
          );
        })()}

        {/* tanlangan shakl: nuqtalar (sudrash) va qirra o'rtalari (yangi nuqta qo'shish) */}
        {tool === 'select' && selShape && selPoly && (
          <g>
            {selPoly.map((a, i) => {
              const b = selPoly[(i + 1) % selPoly.length];
              const [mx, my] = toScr([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]);
              return <circle key={`m${i}`} cx={mx} cy={my} r={5} className="g-v mid"
                onPointerDown={(e) => {
                  const pl = [...selPoly];
                  pl.splice(i + 1, 0, [r2((a[0] + b[0]) / 2), r2((a[1] + b[1]) / 2)]);
                  setPoly(selShape, pl);
                  setSelV(i + 1);
                  onDown(e, { kind: 'vertex', i: i + 1 });
                }} />;
            })}
            {selPoly.map((v, i) => {
              const [x, y] = toScr(v);
              return <circle key={`v${i}`} cx={x} cy={y} r={7} className={`g-v${selV === i ? ' on' : ''}`}
                onPointerDown={(e) => { setSelV(i); onDown(e, { kind: 'vertex', i }); }} />;
            })}
          </g>
        )}

        {/* chizilayotgan narsa */}
        {draftRect && <path d={path([draftRect[0], [draftRect[1][0], draftRect[0][1]], draftRect[1], [draftRect[0][0], draftRect[1][1]]])} className="g-draft" />}
        {tool === 'poly' && draftPoly.length > 0 && (
          <g>
            <path d={path(hover ? [...draftPoly, hover] : draftPoly, false)} className="g-draft line" />
            {draftPoly.map((v, i) => { const [x, y] = toScr(v); return <circle key={i} cx={x} cy={y} r={i === 0 ? 8 : 5} className={i === 0 ? 'g-dv first' : 'g-dv'} />; })}
          </g>
        )}
        {tool !== 'select' && hover && <text x={toScr(hover)[0] + 12} y={toScr(hover)[1] - 10} className="g-coord">{hover[0]}, {hover[1]}</text>}
        <text x={12} y={size.h - 12} className="g-scale">setka: {grid.minor} m · {view.s.toFixed(1)} px/m</text>
      </svg>

      <aside className="ged-panel">
        <h1>2D setka tahrirlagich</h1>
        <div className="ged-tools">
          <button className={tool === 'select' ? 'on' : ''} onClick={cancelDraw}>☝ Tanlash</button>
          <button className={tool === 'rect' ? 'on' : ''} onClick={() => { setDraftPoly([]); setTool('rect'); setSel(null); }}>▭ Bino chizish</button>
          <button className={tool === 'poly' ? 'on' : ''} onClick={() => { setDraftRect(null); setTool('poly'); setSel(null); }}>✎ Shakl chizish</button>
          <button className={tool === 'kassa' ? 'on' : ''} onClick={() => { setDraftRect(null); setDraftPoly([]); setTool('kassa'); setSel(null); }}>🎫 Kassa qo'yish</button>
        </div>
        <p className="muted">{hint}</p>
        <label className="row">Qadam
          <select value={snap} onChange={(e) => setSnap(+e.target.value)}>
            {[0.1, 0.25, 0.5, 1].map((v) => <option key={v} value={v}>{v} m</option>)}
          </select>
        </label>

        {tool === 'poly' && (
          <section className="card">
            <div className="title">Shakl chizilmoqda — {draftPoly.length} nuqta</div>
            <div className="row">
              <button disabled={draftPoly.length < 3} onClick={finishPoly}>Tugatish</button>
              <button className="ghost" disabled={!draftPoly.length} onClick={() => setDraftPoly((d) => d.slice(0, -1))}>Oxirgi nuqtani o'chirish</button>
              <button className="ghost" onClick={cancelDraw}>Bekor qilish</button>
            </div>
          </section>
        )}

        {tool === 'select' && selItem && sb && (
          <section className="card">
            {selAdded ? (
              <label className="field">Nomi<input value={selAdded.name} onChange={(e) => updAdded(selAdded.id, { name: e.target.value })} /></label>
            ) : <div className="title">{selItem.name}</div>}
            <div className="muted small">{selItem.id} · {selItem.source}{isRemoved(selItem.key) ? ' · OLIB TASHLANADI' : ''}</div>
            <div className="fields">
              {([['X (sharq)', sb.at[0], (v: number) => ({ ...sb, at: [v, sb.at[1]] as XY })],
                ['Y (shimol)', sb.at[1], (v: number) => ({ ...sb, at: [sb.at[0], v] as XY })],
                [sb.face !== undefined ? 'Burilish ° (model)' : 'Burilish °', sb.face ?? sb.bearing,
                  (v: number) => (sb.face !== undefined ? { ...sb, face: v } : { ...sb, bearing: v })],
                ...(selItem.kassa ? [['Kattaligi ×', kassaScale(sb), (v: number) => ({ ...sb, ...kassaBox(v) })]] : [
                  ['Eni, m', sb.width, (v: number) => ({ ...sb, width: v })],
                  ...(selItem.circle ? [] : [['Chuqurligi, m', sb.depth, (v: number) => ({ ...sb, depth: v })]]),
                  ['Balandligi, m', sb.height ?? DEFAULT_H, (v: number) => ({ ...sb, height: v })],
                ]),
              ] as [string, number, (v: number) => Box][]).map(([label, val, mk]) => (
                <label key={label}>{label}
                  <input type="number" step={label.startsWith('Burilish') ? 1 : label.startsWith('Kattaligi') ? 0.1 : snap} value={val}
                    onChange={(e) => { const v = parseFloat(e.target.value); if (Number.isFinite(v)) setBox(selItem, mk(v)); }} />
                </label>
              ))}
            </div>
            <div className="row">
              {selAdded
                ? <button className="danger" onClick={() => deleteAdded(selAdded.id)}>O'chirish</button>
                : <>
                  {store.edits[selItem.key] && <button className="ghost" onClick={() => setStore((s) => { const edits = { ...s.edits }; delete edits[selItem.key]; return { ...s, edits }; })}>Asl holiga qaytarish</button>}
                  <button className={isRemoved(selItem.key) ? 'ghost' : 'danger'} onClick={() => toggleRemove(selItem.key)}>{isRemoved(selItem.key) ? 'Olib tashlashni bekor qilish' : 'Olib tashlash'}</button>
                </>}
            </div>
          </section>
        )}

        {tool === 'select' && selShape && selPoly && (
          <section className="card">
            {selAdded ? (
              <>
                <label className="field">Nomi<input value={selAdded.name} onChange={(e) => updAdded(selAdded.id, { name: e.target.value })} /></label>
                <label className="field">Vazifasi
                  <select value={selAdded.purpose ?? PURPOSES[0]} onChange={(e) => updAdded(selAdded.id, { purpose: e.target.value })}>
                    {PURPOSES.map((p) => <option key={p}>{p}</option>)}
                  </select>
                </label>
              </>
            ) : <div className="title">{selShape.name}</div>}
            <div className="muted small">{selShape.source} · {selPoly.length} nuqta{isRemoved(selShape.key) ? ' · OLIB TASHLANADI' : ''}</div>
            <p className="muted small">Oq nuqtani sudrang — joyi o'zgaradi. Qirra o'rtasidagi kichik nuqtani sudrang — yangi nuqta qo'shiladi. Shakl ichidan sudrang — butunlay ko'chadi.</p>
            {selV !== null && selPoly[selV] && (
              <div className="row small">Nuqta {selV + 1}: {selPoly[selV][0]}, {selPoly[selV][1]}
                <button className="ghost" disabled={selPoly.length <= 3} onClick={() => { setPoly(selShape, selPoly.filter((_, i) => i !== selV)); setSelV(null); }}>Nuqtani o'chirish</button>
              </div>
            )}
            <div className="row">
              {selAdded
                ? <button className="danger" onClick={() => deleteAdded(selAdded.id)}>O'chirish</button>
                : <>
                  {store.shapes[selShape.key] && <button className="ghost" onClick={() => setStore((s) => { const sp = { ...s.shapes }; delete sp[selShape.key]; return { ...s, shapes: sp }; })}>Asl holiga qaytarish</button>}
                  <button className={isRemoved(selShape.key) ? 'ghost' : 'danger'} onClick={() => toggleRemove(selShape.key)}>{isRemoved(selShape.key) ? 'Olib tashlashni bekor qilish' : 'Olib tashlash'}</button>
                </>}
            </div>
          </section>
        )}

        {tool === 'select' && !selItem && !selShape && <p className="muted">Hech narsa tanlanmagan.</p>}

        <section className="card">
          <div className="title">O'zgarishlar ({total})</div>
          {total ? (
            <>
              <textarea readOnly value={text} rows={Math.min(16, text.split('\n').length + 1)} onFocus={(e) => e.target.select()} />
              <div className="row">
                <button onClick={copy}>{copied ? 'Nusxalandi ✓' : 'Matnni nusxalash'}</button>
                <button className="ghost" onClick={() => { if (confirm('Barcha o\'zgarishlar o\'chirilsinmi?')) { setStore(EMPTY); setSel(null); } }}>Hammasini tozalash</button>
              </div>
              <p className="muted small">Shu matnni Claude'ga yuboring — u fayllarga qo'yib, xaritani qayta yig'adi. Yangi bino uchun foto ham qo'shing.</p>
            </>
          ) : <p className="muted small">Hali hech narsa o'zgartirilmagan.</p>}
        </section>

        <section className="card">
          <input className="ged-search" placeholder="Qidirish: nom yoki id" value={filter} onChange={(e) => setFilter(e.target.value)} />
          <ul className="ged-list">
            {listShapes.map((sh) => (
              <li key={sh.key} className={`${sh.key === sel ? 'on' : ''}${(sh.kind === 'new' || store.shapes[sh.key]) ? ' edited' : ''}${isRemoved(sh.key) ? ' removed' : ''}`} onClick={() => focusShape(sh)}>
                <span>◇ {sh.name}</span><span className="muted small">shakl</span>
              </li>
            ))}
            {listItems.map((it) => (
              <li key={it.key} className={`${it.key === sel ? 'on' : ''}${(it.kind === 'new' || store.edits[it.key]) ? ' edited' : ''}${isRemoved(it.key) ? ' removed' : ''}`} onClick={() => focusItem(it)}>
                <span>{it.kind === 'attr' ? '★ ' : ''}{it.name}</span><span className="muted small">{it.id}</span>
              </li>
            ))}
          </ul>
        </section>

        <details className="card help">
          <summary>Qo'llanma</summary>
          <ol>
            <li><b>Ko'chirish / o'lcham / burish.</b> "Tanlash" rejimida binoni bosing. Ichidan sudrang — ko'chadi; oq kvadratlar — o'lcham (qarama-qarshi tomon joyida qoladi); sariq doiracha — burish (Shift — 15° qadam). Qalin sariq qirra — old tomoni (eshigi).</li>
            <li><b>Yangi bino.</b> "▭ Bino chizish" → xaritada sudrab to'rtburchak chizing → nomini yozing, kerak bo'lsa burib to'g'rilang.</li>
            <li><b>Kassa.</b> "🎫 Kassa qo'yish" → kassa turadigan joyni bosing (nomi o'zi — K-6, K-7...). Keyin ko'chiring va sariq doiracha bilan buring: sariq qirra — kassa oynasi. Kattaligi — oq kvadratlar yoki "Kattaligi ×" maydoni (1 — haqiqiy budka; proporsiya saqlanadi).</li>
            <li><b>Erkin shakl</b> (plitka, maysa, terrasa...). "✎ Shakl chizish" → nuqtama-nuqta bosing → birinchi nuqtani bosib yoki Enter bilan yakunlang → nomi va vazifasini tanlang.</li>
            <li><b>Mavjud shakl</b> (◇ ro'yxatda: plitka maydonlari, terrasa). Bosing → nuqtalarni sudrang; qirra o'rtasidagi kichik nuqta — yangi nuqta; Delete — tanlangan nuqtani o'chirish.</li>
            <li><b>Olib tashlash.</b> Narsani tanlab "Olib tashlash" ni bosing (qizil chiziqli bo'lib qoladi). ★ — plandagi attraksionlar.</li>
            <li><b>Natija.</b> "Matnni nusxalash" → Claude'ga yuboring. O'zgarishlar brauzerda saqlanadi; fayllarga qo'yilgach ro'yxatdan o'zi tushadi.</li>
          </ol>
        </details>
      </aside>
    </div>
  );
}

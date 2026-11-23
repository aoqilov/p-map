/**
 * Parking ichki joylashuvi: chet bo'ylab joylar + ichkarida qo'sh qatorlar (orqama-orqa), daraxtli orolchalar,
 * mashinalar, fonuslar. Hammasi metrda (x — sharq, y — shimol), burchaklar radianda.
 *
 * Qoida: har bir joyning oldida `aisle` eni bo'sh yo'lak bo'lishi shart (mashina kira olsin) — shuning uchun
 * yo'laklar o'z-o'zidan hosil bo'ladi va hech bir joy berkilib qolmaydi.
 */
import type { XY } from '../src/map/projection';
import type { ParkingLayout, Poly } from '../src/map/types';
import { distToBoundary, inPoly } from '../src/map/geo';

export interface ParkingCfg {
  stall: [number, number];
  aisle: number;
  islandEvery: number;
  occupancy: number;
  lampEvery: number;
  seed: number;
  /** Ichki qatorlar yo'nalishi (kompas, gradus); berilmasa — avtomatik */
  rowBearing?: number;
}

export interface ParkingInput {
  poly: Poly;
  gate: ParkingLayout['gate'];
  ped: XY | null;
  building: ParkingLayout['building'];
  canopy: ParkingLayout['canopy'];
  cfg: ParkingCfg;
}

interface Rect { c: XY; u: XY; v: XY; hw: number; hd: number }

const add = (a: XY, b: XY, k = 1): XY => [a[0] + b[0] * k, a[1] + b[1] * k];
const dot = (a: XY, b: XY) => a[0] * b[0] + a[1] * b[1];
const r2 = (v: number) => Math.round(v * 100) / 100;
const r3 = (v: number) => Math.round(v * 1000) / 1000;

const corners = (r: Rect): XY[] => [
  add(add(r.c, r.u, -r.hw), r.v, -r.hd), add(add(r.c, r.u, r.hw), r.v, -r.hd),
  add(add(r.c, r.u, r.hw), r.v, r.hd), add(add(r.c, r.u, -r.hw), r.v, r.hd),
];

/** Ikki to'rtburchak kesishadimi (SAT). `pad` > 0 — chetma-chet tegib turishga ruxsat */
const overlap = (a: Rect, b: Rect, pad = 0.04) => {
  const d: XY = [b.c[0] - a.c[0], b.c[1] - a.c[1]];
  for (const ax of [a.u, a.v, b.u, b.v]) {
    const ra = a.hw * Math.abs(dot(a.u, ax)) + a.hd * Math.abs(dot(a.v, ax));
    const rb = b.hw * Math.abs(dot(b.u, ax)) + b.hd * Math.abs(dot(b.v, ax));
    if (Math.abs(dot(d, ax)) >= ra + rb - pad) return false;
  }
  return true;
};

const pointInRect = (p: XY, r: Rect, shrink = 0.05) => {
  const d: XY = [p[0] - r.c[0], p[1] - r.c[1]];
  return Math.abs(dot(d, r.u)) < r.hw - shrink && Math.abs(dot(d, r.v)) < r.hd - shrink;
};

/** Douglas–Peucker: egri chetlarni bir nechta to'g'ri bo'lakka aylantiradi */
function simplify(ring: XY[], eps: number): XY[] {
  const pts = ring.slice(0, -1);
  // Boshlang'ich nuqta — eng uzoq ikki nuqtadan biri (yopiq halqa uchun barqaror)
  let i0 = 0;
  pts.forEach((p, i) => { if (p[0] + p[1] < pts[i0][0] + pts[i0][1]) i0 = i; });
  const rot = [...pts.slice(i0), ...pts.slice(0, i0), pts[i0]];
  const keep = new Array(rot.length).fill(false);
  keep[0] = keep[rot.length - 1] = true;
  const segDist = (p: XY, a: XY, b: XY) => {
    const dx = b[0] - a[0], dy = b[1] - a[1], L = dx * dx + dy * dy;
    const t = L ? Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L)) : 0;
    return Math.hypot(p[0] - a[0] - dx * t, p[1] - a[1] - dy * t);
  };
  const rec = (s: number, e: number) => {
    let m = -1, md = eps;
    for (let i = s + 1; i < e; i++) { const d = segDist(rot[i], rot[s], rot[e]); if (d > md) { md = d; m = i; } }
    if (m >= 0) { keep[m] = true; rec(s, m); rec(m, e); }
  };
  // Yopiq halqa: eng uzoq nuqtani ham majburan qoldiramiz, aks holda hammasi bitta chiziqqa qisqaradi
  let far = 0;
  rot.forEach((p, i) => { if (Math.hypot(p[0] - rot[0][0], p[1] - rot[0][1]) > Math.hypot(rot[far][0] - rot[0][0], rot[far][1] - rot[0][1])) far = i; });
  keep[far] = true;
  rec(0, far); rec(far, rot.length - 1);
  return rot.filter((_, i) => keep[i]);
}

function rng(seed: number) {
  let s = seed | 0;
  return () => {
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function layoutParking(inp: ParkingInput) {
  const { poly, cfg } = inp;
  const [W, D] = cfg.stall;
  const A = cfg.aisle;
  const ring = poly[0];
  const verts = ring.slice(0, -1);

  // ---- Taqiqlangan joylar (mashina turmaydi, lekin yo'lak bo'lishi mumkin) ----
  const reserved: Rect[] = [];
  if (inp.gate) {
    const o: XY = [Math.cos(inp.gate.rot), Math.sin(inp.gate.rot)];
    const side: XY = [-o[1], o[0]];
    // Darvozadan ichkariga 16 m — kirish yo'lagi (strelkalar shu yerda)
    reserved.push({ c: add(inp.gate.at, o, -8), u: side, v: o, hw: inp.gate.width / 2 + 1.2, hd: 8.5 });
  }
  let pedDir: XY | null = null;
  if (inp.ped) {
    // Piyoda kirish: o'yiq tubidan ichkariga 7 m yo'lakcha (eng ochiq yo'nalishda)
    let best: XY = [0, 1], bd = -1;
    for (let k = 0; k < 32; k++) {
      const a = (k / 32) * Math.PI * 2, dir: XY = [Math.cos(a), Math.sin(a)];
      const q = add(inp.ped, dir, 4);
      if (!inPoly(q, poly)) continue;
      const d = distToBoundary(q, poly);
      if (d > bd) { bd = d; best = dir; }
    }
    pedDir = best;
    reserved.push({ c: add(inp.ped, best, 3), u: [-best[1], best[0]], v: best, hw: 1.6, hd: 4.2 });
  }

  const stalls: Rect[] = [];
  const strips: Rect[] = [];
  const islands: Rect[] = [];

  const insideLot = (r: Rect, inset: number) => {
    const cs = corners(r);
    const samples: XY[] = [r.c];
    for (let i = 0; i < 4; i++) {
      const a = cs[i], b = cs[(i + 1) % 4];
      for (const t of [0, 0.5]) samples.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]);
    }
    if (!samples.every((p) => inPoly(p, poly) && distToBoundary(p, poly) >= inset - 1e-6)) return false;
    return !verts.some((p) => pointInRect(p, r)); // o'yiq uchi to'rtburchakni teshib o'tmasin
  };
  const stripOf = (r: Rect): Rect => ({ c: add(r.c, r.v, r.hd + A / 2), u: r.u, v: r.v, hw: r.hw * 0.92, hd: A / 2 });
  /** Joy qo'yish mumkinmi: parking ichida, boshqa joy/orolcha/taqiqlangan joyga tegmaydi, oldidagi yo'lak ochiq */
  const canPlace = (r: Rect, extra: Rect[] = []) => {
    if (!insideLot(r, 0.25)) return false;
    const s = stripOf(r);
    if (!insideLot(s, 0)) return false;
    const solid = [...stalls, ...islands, ...extra];
    const lanes = [...strips, ...extra.map(stripOf)];
    if (solid.some((o) => overlap(o, r)) || reserved.some((o) => overlap(o, r)) || lanes.some((o) => overlap(o, r, 0.1))) return false;
    return !solid.some((o) => overlap(o, s, 0.1));
  };
  const place = (r: Rect) => { stalls.push(r); strips.push(stripOf(r)); };

  // ---- 1) Chet bo'ylab: chetga orqasi bilan, old tomoni ichkariga ----
  const edges = simplify(ring, 0.9);
  const inward = (a: XY, b: XY): XY => {
    const L = Math.hypot(b[0] - a[0], b[1] - a[1]);
    let n: XY = [-(b[1] - a[1]) / L, (b[0] - a[0]) / L];
    const m: XY = [(a[0] + b[0]) / 2 + n[0] * 0.6, (a[1] + b[1]) / 2 + n[1] * 0.6];
    if (!inPoly(m, poly)) n = [-n[0], -n[1]];
    return n;
  };
  // Soyabon ostidagi chet birinchi (u yerda albatta joy bo'lsin), keyin uzun chetlar — asosiy qatorlar tekis chiqadi
  const segD = (p: XY, a: XY, b: XY) => {
    const dx = b[0] - a[0], dy = b[1] - a[1], L = dx * dx + dy * dy;
    const t = L ? Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L)) : 0;
    return Math.hypot(p[0] - a[0] - dx * t, p[1] - a[1] - dy * t);
  };
  const canopyMid: XY | null = inp.canopy ? [(inp.canopy.a[0] + inp.canopy.b[0]) / 2, (inp.canopy.a[1] + inp.canopy.b[1]) / 2] : null;
  const prio = (e: { a: XY; b: XY; len: number }) => (canopyMid && segD(canopyMid, e.a, e.b) < 1.5 ? 1e6 : 0) + e.len;
  const edgeList = edges.slice(0, -1).map((a, i) => ({ a, b: edges[i + 1], len: Math.hypot(edges[i + 1][0] - a[0], edges[i + 1][1] - a[1]) }))
    .filter((e) => e.len >= W).sort((p, q) => prio(q) - prio(p));
  for (const { a, b, len } of edgeList) {
    const d: XY = [(b[0] - a[0]) / len, (b[1] - a[1]) / len];
    const n = inward(a, b);
    // Eng ko'p joy sig'adigan siljishni tanlaymiz
    // Soddalashtirilgan chet asl egri chetdan biroz farq qiladi — qatorni chetdan bir necha masofada sinab ko'ramiz
    let bestRow: Rect[] = [];
    for (const off of [0.3, 0.7, 1.1])
    for (const ph of [0, W / 4, W / 2, (3 * W) / 4]) {
      const row: Rect[] = [];
      for (let t = W / 2 + 0.15 + ph; t <= len - W / 2 - 0.15; t += W) {
        const r: Rect = { c: add(add(a, d, t), n, D / 2 + off), u: d, v: n, hw: W / 2, hd: D / 2 };
        if (canPlace(r, row)) row.push(r);
      }
      if (row.length > bestRow.length + (off > 0.3 ? 0 : -1)) bestRow = row;
    }
    bestRow.forEach(place);
  }

  // ---- 2) Ichkarida qo'sh qatorlar: eng ko'p joy beradigan yo'nalish va siljish ----
  const xs = verts.map((p) => p[0]), ys = verts.map((p) => p[1]);
  const cx = (Math.min(...xs) + Math.max(...xs)) / 2, cy = (Math.min(...ys) + Math.max(...ys)) / 2;
  const span = Math.hypot(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)) / 2 + 5;
  // Qator yo'nalishi: config da kompas burchagi berilgan bo'lsa — o'sha, aks holda eng uzun chetlar yo'nalishlaridan eng ko'p joy bergani
  const angles = cfg.rowBearing !== undefined ? [((90 - cfg.rowBearing) * Math.PI) / 180]
    : edgeList.slice(0, 4).map((e) => Math.atan2(e.b[1] - e.a[1], e.b[0] - e.a[0]));
  const pitch = 2 * D + A;
  type Slot = { line: number; j: number; pair: Rect[] };
  let best: { slots: Slot[]; dir: XY } = { slots: [], dir: [1, 0] };
  for (const ang of angles) {
    const dir: XY = [Math.cos(ang), Math.sin(ang)], perp: XY = [-dir[1], dir[0]];
    for (let ph = 0; ph < pitch; ph += pitch / 8) {
      for (const ph2 of [0, W / 3, (2 * W) / 3]) {
        const trial: Rect[] = [];
        const slots: Slot[] = [];
        for (let k = -Math.ceil(span / pitch); k <= Math.ceil(span / pitch); k++) {
          const off = k * pitch + ph;
          for (let j = -Math.ceil(span / W); j <= Math.ceil(span / W); j++) {
            const p = add(add([cx, cy], perp, off), dir, j * W + ph2);
            const pair: Rect[] = [];
            for (const sg of [1, -1]) {
              const v: XY = [perp[0] * sg, perp[1] * sg];
              const r: Rect = { c: add(p, v, D / 2), u: dir, v, hw: W / 2, hd: D / 2 };
              if (canPlace(r, trial)) { pair.push(r); trial.push(r); }
            }
            if (pair.length) slots.push({ line: k, j, pair });
          }
        }
        if (trial.length > best.slots.reduce((s, x) => s + x.pair.length, 0)) best = { slots, dir };
      }
    }
  }

  // Orolchalar: qator ichida har `islandEvery` joydan keyin bitta joy o'rniga daraxt; qator uchlarida kichik orolcha
  const lines = new Map<number, Slot[]>();
  for (const s of best.slots) lines.set(s.line, [...(lines.get(s.line) ?? []), s]);
  const islandTrees: [number, number, number][] = [];
  const lamps: XY[] = [];
  let islandNo = 0;
  for (const slots of lines.values()) {
    slots.sort((p, q) => p.j - q.j);
    // Uzluksiz bo'laklar (ikkala tomoni ham bor joylar)
    const runs: Slot[][] = [];
    for (const s of slots) {
      const last = runs[runs.length - 1];
      if (last && s.j === last[last.length - 1].j + 1) last.push(s); else runs.push([s]);
    }
    for (const run of runs) {
      const keep: Slot[] = [];
      run.forEach((s, i) => {
        const isIsland = s.pair.length === 2 && i > 1 && i < run.length - 2 && (i % (cfg.islandEvery + 1)) === cfg.islandEvery;
        if (!isIsland) { keep.push(s); return; }
        const c: XY = [(s.pair[0].c[0] + s.pair[1].c[0]) / 2, (s.pair[0].c[1] + s.pair[1].c[1]) / 2];
        islands.push({ c, u: s.pair[0].u, v: s.pair[0].v, hw: W / 2 - 0.15, hd: D - 0.25 });
        islandTrees.push([r2(c[0]), r2(c[1]), 0.95]);
        if (islandNo++ % cfg.lampEvery === 0) lamps.push(add(c, s.pair[0].v, D - 1.2));
      });
      keep.forEach((s) => s.pair.forEach(place));
      // Qator uchlari: qo'sh qator bo'lsa — bordyurli kichik orolcha va buta-daraxt
      if (run.length >= 4) {
        for (const [s, sg] of [[run[0], -1], [run[run.length - 1], 1]] as const) {
          if (s.pair.length < 2) continue;
          const c0: XY = [(s.pair[0].c[0] + s.pair[1].c[0]) / 2, (s.pair[0].c[1] + s.pair[1].c[1]) / 2];
          const cap: Rect = { c: add(c0, best.dir, sg * (W / 2 + 0.75)), u: best.dir, v: s.pair[0].v, hw: 0.6, hd: D - 0.6 };
          if (insideLot(cap, 0.3) && ![...stalls, ...islands, ...reserved].some((o) => overlap(o, cap)) &&
            !strips.some((o) => overlap(o, cap, 0.1))) {
            islands.push(cap);
            islandTrees.push([r2(cap.c[0]), r2(cap.c[1]), 0.7]);
          }
        }
      }
    }
  }

  // ---- 3) Chet bo'ylab fonuslar (parkingdan 1 m tashqarida, daraxtlar qatorida) ----
  {
    let carry = 0;
    for (let i = 0; i < ring.length - 1; i++) {
      const a = ring[i], b = ring[i + 1];
      const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
      if (len < 1e-6) continue;
      const n = inward(a, b);
      for (let t = 24 - carry; t < len; t += 24) {
        const q = add([a[0] + ((b[0] - a[0]) * t) / len, a[1] + ((b[1] - a[1]) * t) / len], n, -1.0);
        const nearGate = inp.gate && Math.hypot(q[0] - inp.gate.at[0], q[1] - inp.gate.at[1]) < 10;
        const nearPed = inp.ped && Math.hypot(q[0] - inp.ped[0], q[1] - inp.ped[1]) < 5;
        if (!nearGate && !nearPed) lamps.push(q);
      }
      carry = (carry + len) % 24;
    }
  }

  // ---- 4) Mashinalar ----
  const rand = rng(cfg.seed * 7919 + stalls.length);
  // Ranglar: oq, kumush, qora, kulrang, to'q ko'k, qizil, bej, to'q yashil
  const colorW = [0.3, 0.2, 0.2, 0.1, 0.08, 0.05, 0.04, 0.03];
  const pickColor = () => {
    let x = rand();
    for (let i = 0; i < colorW.length; i++) { if ((x -= colorW[i]) <= 0) return i; }
    return 0;
  };
  const cars: ParkingLayout['cars'] = [];
  for (const s of stalls) {
    if (rand() > cfg.occupancy) continue;
    const ang = Math.atan2(s.v[1], s.v[0]);
    const nose = rand() < 0.62 ? ang + Math.PI : ang; // ko'pchilik old tomoni bilan kiradi
    const p = add(add(s.c, s.v, (rand() - 0.5) * 0.35), s.u, (rand() - 0.5) * 0.25);
    cars.push([r2(p[0]), r2(p[1]), r3(nose + (rand() - 0.5) * 0.07), pickColor(), rand() < 0.3 ? 1 : 0]);
  }

  // ---- 5) Strelkalar: darvoza yo'lagida kirish va chiqish ----
  const arrows: ParkingLayout['arrows'] = [];
  if (inp.gate) {
    const o: XY = [Math.cos(inp.gate.rot), Math.sin(inp.gate.rot)], side: XY = [-o[1], o[0]];
    const q = inp.gate.width / 4;
    arrows.push([...add(add(inp.gate.at, o, -9), side, q).map(r2) as XY, r3(inp.gate.rot + Math.PI)]);
    arrows.push([...add(add(inp.gate.at, o, -9), side, -q).map(r2) as XY, r3(inp.gate.rot)]);
  }

  // ---- 6) Qorovul budkasi: darvoza yonida, parkingdan tashqarida (daraxtlar qatorida), joylardan uzoqroq tomonda ----
  let kiosk: ParkingLayout['kiosk'] = null;
  if (inp.gate) {
    const o: XY = [Math.cos(inp.gate.rot), Math.sin(inp.gate.rot)], side: XY = [-o[1], o[0]];
    let bestK: { p: XY; score: number } | null = null;
    for (const sg of [1, -1]) {
      for (const back of [3.5, 5, 6.5]) {
        const p = add(add(inp.gate.at, o, -back), side, sg * (inp.gate.width / 2 + 1.7));
        if (inPoly(p, poly) || distToBoundary(p, poly) < 1.3) continue;
        const score = Math.min(...stalls.map((s) => Math.hypot(s.c[0] - p[0], s.c[1] - p[1])));
        if (!bestK || score > bestK.score) bestK = { p, score };
      }
    }
    if (bestK) kiosk = [r2(bestK.p[0]), r2(bestK.p[1]), r3(inp.gate.rot)];
  }

  const asRot = (r: Rect) => r3(Math.atan2(r.v[1], r.v[0]));
  const layout: ParkingLayout = {
    stall: [W, D],
    stalls: stalls.map((s) => [r2(s.c[0]), r2(s.c[1]), asRot(s)]),
    cars,
    islands: islands.map((r) => [r2(r.c[0]), r2(r.c[1]), r3(Math.atan2(r.u[1], r.u[0])), r2(r.hw * 2), r2(r.hd * 2)]),
    arrows,
    gate: inp.gate,
    ped: inp.ped && pedDir ? { at: [r2(inp.ped[0]), r2(inp.ped[1])], rot: r3(Math.atan2(pedDir[1], pedDir[0])) } : null,
    kiosk,
    building: inp.building,
    canopy: inp.canopy,
  };
  return { layout, trees: islandTrees, lamps: lamps.map((p) => [r2(p[0]), r2(p[1])] as XY) };
}

// Parkingdagi harakat: vaqti-vaqti bilan darvozadan mashina kirib bo'sh joyga turadi, boshqasi joyidan chiqib ketadi.
// Yo'l topish: parking 0.5 m li to'rga bo'linadi (joylar, orolchalar va chet yaqini band), A* bilan yo'lak bo'ylab
// yo'l topiladi, keyin to'g'rilanadi va silliqlanadi. Hammasi metrda (x — sharq, y — shimol), burchaklar radianda.
import type { XY } from './projection';
import type { Area, ParkingLayout } from './types';

export interface TrafficCfg {
  /** Yangi mashina kelishi oralig'i, s (tasodifiy shu oraliqda) */
  arriveEvery: [number, number];
  /** Mashina ketishi oralig'i, s */
  departEvery: [number, number];
  /** Tezlik, m/s (oldinga / orqaga) */
  speed: number;
  reverseSpeed: number;
  /** Bir vaqtda harakatdagi mashinalar soni */
  maxMoving: number;
}

export interface Pose { x: number; y: number; h: number }

interface Leg { pts: XY[]; cum: number[]; reverse: boolean }

export interface Car {
  color: number;
  kind: number;
  /** Turgan (yoki borayotgan) joyi */
  stall: number | null;
  state: 'parked' | 'arriving' | 'departing' | 'gone';
  pose: Pose;
  legs: Leg[];
  leg: number;
  s: number;
  /** 0..1 — darvozada paydo bo'lish/yo'qolish uchun o'lcham */
  scale: number;
}

export interface Sim {
  T: number;
  cars: Car[];
  occupied: (number | null)[];
  nextArrive: number;
  nextDepart: number;
  /** Shlagbaum qo'llari: 0 — yopiq, 1 — ochiq (kirish, chiqish) */
  arms: [number, number];
}

const CELL = 0.5;

interface Nav { x0: number; y0: number; W: number; H: number; free: Uint8Array }

function rng(seed: number) {
  let s = seed | 0;
  return () => {
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Haydash mumkin bo'lgan katakchalar: parking ichida, chetdan 1.15 m, joy va orolchalardan ~1 m uzoqda */
function buildNav(area: Area, L: ParkingLayout): Nav {
  const ring = area.poly[0];
  const xs = ring.map((p) => p[0]), ys = ring.map((p) => p[1]);
  const x0 = Math.min(...xs) - 1, y0 = Math.min(...ys) - 1;
  const W = Math.ceil((Math.max(...xs) + 1 - x0) / CELL), H = Math.ceil((Math.max(...ys) + 1 - y0) / CELL);
  const free = new Uint8Array(W * H);
  // Ichki qism: har qator bo'yicha chegara kesishmalari orasini to'ldiramiz (tez, nuqta-ichida testisiz)
  for (let j = 0; j < H; j++) {
    const y = y0 + (j + 0.5) * CELL;
    const cross: number[] = [];
    for (const r of area.poly) {
      for (let k = 0; k < r.length - 1; k++) {
        const [a, b] = [r[k], r[k + 1]];
        if ((a[1] > y) !== (b[1] > y)) cross.push(a[0] + ((y - a[1]) * (b[0] - a[0])) / (b[1] - a[1]));
      }
    }
    cross.sort((p, q) => p - q);
    for (let k = 0; k + 1 < cross.length; k += 2) {
      for (let i = Math.max(0, Math.ceil((cross[k] - x0) / CELL - 0.5)); i < W && x0 + (i + 0.5) * CELL < cross[k + 1]; i++) free[j * W + i] = 1;
    }
  }
  // Chetdan 1.15 m ichkarigacha band: har bir qirra atrofidagi katakchalarni tekshiramiz
  const M = 1.15;
  for (const r of area.poly) {
    for (let k = 0; k < r.length - 1; k++) {
      const [a, b] = [r[k], r[k + 1]];
      const i0 = Math.max(0, Math.floor((Math.min(a[0], b[0]) - M - x0) / CELL)), i1 = Math.min(W - 1, Math.ceil((Math.max(a[0], b[0]) + M - x0) / CELL));
      const j0 = Math.max(0, Math.floor((Math.min(a[1], b[1]) - M - y0) / CELL)), j1 = Math.min(H - 1, Math.ceil((Math.max(a[1], b[1]) + M - y0) / CELL));
      const dx = b[0] - a[0], dy = b[1] - a[1], LL = dx * dx + dy * dy || 1;
      for (let j = j0; j <= j1; j++) {
        for (let i = i0; i <= i1; i++) {
          const px = x0 + (i + 0.5) * CELL - a[0], py = y0 + (j + 0.5) * CELL - a[1];
          const t = Math.max(0, Math.min(1, (px * dx + py * dy) / LL));
          if (Math.hypot(px - dx * t, py - dy * t) < M) free[j * W + i] = 0;
        }
      }
    }
  }
  // To'rtburchakni (markaz, yo'nalish, yarim o'lchamlar + zaxira) band qilish
  const block = (c: XY, ang: number, hw: number, hd: number) => {
    const v: XY = [Math.cos(ang), Math.sin(ang)], u: XY = [-v[1], v[0]];
    const r = Math.hypot(hw, hd);
    for (let j = Math.floor((c[1] - r - y0) / CELL); j <= Math.ceil((c[1] + r - y0) / CELL); j++) {
      for (let i = Math.floor((c[0] - r - x0) / CELL); i <= Math.ceil((c[0] + r - x0) / CELL); i++) {
        if (i < 0 || j < 0 || i >= W || j >= H) continue;
        const dx = x0 + (i + 0.5) * CELL - c[0], dy = y0 + (j + 0.5) * CELL - c[1];
        if (Math.abs(dx * u[0] + dy * u[1]) < hw && Math.abs(dx * v[0] + dy * v[1]) < hd) free[j * W + i] = 0;
      }
    }
  };
  const [SW, SD] = L.stall;
  for (const [x, y, r] of L.stalls) block([x, y], r, SW / 2 + 0.55, SD / 2 + 0.95);
  for (const [x, y, r, len, wid] of L.islands) block([x, y], r + Math.PI / 2, len / 2 + 1.0, wid / 2 + 1.0);
  return { x0, y0, W, H, free };
}

const cellOf = (n: Nav, p: XY) => [Math.floor((p[0] - n.x0) / CELL), Math.floor((p[1] - n.y0) / CELL)] as const;
const centerOf = (n: Nav, i: number, j: number): XY => [n.x0 + (i + 0.5) * CELL, n.y0 + (j + 0.5) * CELL];
const isFree = (n: Nav, i: number, j: number) => i >= 0 && j >= 0 && i < n.W && j < n.H && n.free[j * n.W + i] === 1;

/** Eng yaqin bo'sh katakcha (spiral bo'ylab) */
function snap(n: Nav, p: XY): [number, number] | null {
  const [ci, cj] = cellOf(n, p);
  for (let r = 0; r <= 10; r++) {
    let best: [number, number] | null = null, bd = Infinity;
    for (let j = cj - r; j <= cj + r; j++) {
      for (let i = ci - r; i <= ci + r; i++) {
        if (Math.max(Math.abs(i - ci), Math.abs(j - cj)) !== r || !isFree(n, i, j)) continue;
        const c = centerOf(n, i, j), d = Math.hypot(c[0] - p[0], c[1] - p[1]);
        if (d < bd) { bd = d; best = [i, j]; }
      }
    }
    if (best) return best;
  }
  return null;
}

/** To'g'ri chiziq bo'ylab hamma katakcha bo'shmi */
function lineFree(n: Nav, a: XY, b: XY) {
  const L = Math.hypot(b[0] - a[0], b[1] - a[1]);
  const k = Math.max(1, Math.ceil(L / (CELL * 0.5)));
  for (let t = 0; t <= k; t++) {
    const [i, j] = cellOf(n, [a[0] + ((b[0] - a[0]) * t) / k, a[1] + ((b[1] - a[1]) * t) / k]);
    if (!isFree(n, i, j)) return false;
  }
  return true;
}

/** A* (8 yo'nalish), keyin "ip tortish" bilan ortiqcha burilishlar olib tashlanadi */
function findPath(n: Nav, from: XY, to: XY): XY[] | null {
  const s = snap(n, from), g = snap(n, to);
  if (!s || !g) return null;
  const N = n.W * n.H, start = s[1] * n.W + s[0], goal = g[1] * n.W + g[0];
  const gs = new Float32Array(N).fill(Infinity), prev = new Int32Array(N).fill(-1), closed = new Uint8Array(N);
  const heap: number[] = [], f: number[] = [];
  const push = (id: number, fv: number) => {
    heap.push(id); f.push(fv);
    let i = heap.length - 1;
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (f[p] <= f[i]) break;
      [heap[p], heap[i]] = [heap[i], heap[p]]; [f[p], f[i]] = [f[i], f[p]]; i = p;
    }
  };
  const pop = () => {
    const top = heap[0], lastH = heap.pop()!, lastF = f.pop()!;
    if (heap.length) {
      heap[0] = lastH; f[0] = lastF;
      let i = 0;
      for (;;) {
        const l = i * 2 + 1, r = l + 1;
        let m = i;
        if (l < heap.length && f[l] < f[m]) m = l;
        if (r < heap.length && f[r] < f[m]) m = r;
        if (m === i) break;
        [heap[m], heap[i]] = [heap[i], heap[m]]; [f[m], f[i]] = [f[i], f[m]]; i = m;
      }
    }
    return top;
  };
  const hx = (id: number) => {
    const dx = Math.abs((id % n.W) - g[0]), dy = Math.abs(Math.floor(id / n.W) - g[1]);
    return Math.max(dx, dy) + 0.414 * Math.min(dx, dy);
  };
  gs[start] = 0;
  push(start, hx(start));
  const D8 = [[1, 0, 1], [-1, 0, 1], [0, 1, 1], [0, -1, 1], [1, 1, 1.414], [1, -1, 1.414], [-1, 1, 1.414], [-1, -1, 1.414]];
  while (heap.length) {
    const cur = pop();
    if (cur === goal) break;
    if (closed[cur]) continue;
    closed[cur] = 1;
    const ci = cur % n.W, cj = Math.floor(cur / n.W);
    for (const [di, dj, c] of D8) {
      const ni = ci + di, nj = cj + dj;
      if (!isFree(n, ni, nj)) continue;
      if (di && dj && (!isFree(n, ci + di, cj) || !isFree(n, ci, cj + dj))) continue; // burchakni kesmasin
      const id = nj * n.W + ni, ng = gs[cur] + c;
      if (ng < gs[id]) { gs[id] = ng; prev[id] = cur; push(id, ng + hx(id)); }
    }
  }
  if (prev[goal] < 0 && goal !== start) return null;
  const cells: XY[] = [];
  for (let id = goal; id >= 0; id = prev[id]) { cells.push(centerOf(n, id % n.W, Math.floor(id / n.W))); if (id === start) break; }
  cells.reverse();
  // Ip tortish: ko'rinib turgan eng uzoq nuqtaga to'g'ri boramiz
  const out: XY[] = [cells[0]];
  let k = 0;
  while (k < cells.length - 1) {
    let m = cells.length - 1;
    while (m > k + 1 && !lineFree(n, cells[k], cells[m])) m--;
    out.push(cells[m]);
    k = m;
  }
  return out;
}

/** Chaikin silliqlash (uchlari joyida), keyin har 0.25 m da teng bo'laklarga */
function smoothLeg(pts: XY[], reverse: boolean, iters = 3): Leg {
  let p = pts.filter((q, i) => i === 0 || Math.hypot(q[0] - pts[i - 1][0], q[1] - pts[i - 1][1]) > 0.05);
  for (let it = 0; it < iters && p.length > 2; it++) {
    const q: XY[] = [p[0]];
    for (let i = 0; i < p.length - 1; i++) {
      const a = p[i], b = p[i + 1];
      if (i > 0) q.push([a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25]);
      if (i < p.length - 2) q.push([a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75]);
    }
    q.push(p[p.length - 1]);
    p = q;
  }
  const cum = [0];
  for (let i = 1; i < p.length; i++) cum.push(cum[i - 1] + Math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]));
  return { pts: p, cum, reverse };
}

function sampleLeg(leg: Leg, s: number): { p: XY; t: XY } {
  const { pts, cum } = leg;
  const d = Math.min(Math.max(s, 0), cum[cum.length - 1]);
  let i = 1;
  while (i < cum.length - 1 && cum[i] < d) i++;
  const a = pts[i - 1], b = pts[i];
  const seg = Math.max(cum[i] - cum[i - 1], 1e-6), k = (d - cum[i - 1]) / seg;
  const p: XY = [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k];
  // Yo'nalish: ±0.6 m oraliqdagi o'rtacha (keskin burilish silliqroq)
  const lo = Math.max(d - 0.6, 0), hi = Math.min(d + 0.6, cum[cum.length - 1]);
  const pa = lo === d ? a : sampleRaw(leg, lo), pb = hi === d ? b : sampleRaw(leg, hi);
  const t: XY = [pb[0] - pa[0], pb[1] - pa[1]];
  return { p, t };
}
function sampleRaw(leg: Leg, d: number): XY {
  const { pts, cum } = leg;
  let i = 1;
  while (i < cum.length - 1 && cum[i] < d) i++;
  const a = pts[i - 1], b = pts[i], k = (d - cum[i - 1]) / Math.max(cum[i] - cum[i - 1], 1e-6);
  return [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k];
}

export interface Traffic {
  sim: Sim;
  step: (dt: number) => boolean;
  arrive: () => boolean;
  depart: () => boolean;
}

export function createTraffic(area: Area, L: ParkingLayout, cfg: TrafficCfg, seed = 1): Traffic | null {
  if (!L.gate) return null;
  const nav = buildNav(area, L);
  const rand = rng(seed * 4099 + L.stalls.length);
  const [SW, SD] = L.stall;
  void SW;
  const AISLE = 6;
  const o: XY = [Math.cos(L.gate.rot), Math.sin(L.gate.rot)], side: XY = [-o[1], o[0]];
  const q = L.gate.width / 4;
  // O'ng tomonlama harakat: kiruvchi +side bo'lakda, chiquvchi -side bo'lakda
  const lanePt = (sg: number, along: number): XY => [L.gate!.at[0] + o[0] * along + side[0] * q * sg, L.gate!.at[1] + o[1] * along + side[1] * q * sg];
  const barrier = lanePt(0, -2.4);

  const stallV = (i: number): XY => [Math.cos(L.stalls[i][2]), Math.sin(L.stalls[i][2])];
  const front = (i: number): XY => {
    const v = stallV(i), [x, y] = L.stalls[i];
    return [x + v[0] * (SD / 2 + AISLE / 2), y + v[1] * (SD / 2 + AISLE / 2)];
  };

  // Boshlang'ich mashinalar: har biri eng yaqin joyga biriktiriladi
  const occupied: (number | null)[] = L.stalls.map(() => null);
  const cars: Car[] = [];
  for (const [x, y, h, color, kind] of L.cars) {
    let bi = -1, bd = 2;
    L.stalls.forEach(([sx, sy], i) => { const d = Math.hypot(sx - x, sy - y); if (d < bd && occupied[i] === null) { bd = d; bi = i; } });
    cars.push({ color, kind, stall: bi >= 0 ? bi : null, state: 'parked', pose: { x, y, h }, legs: [], leg: 0, s: 0, scale: 1 });
    if (bi >= 0) occupied[bi] = cars.length - 1;
  }
  const sim: Sim = { T: 0, cars, occupied, nextArrive: 6 + rand() * 8, nextDepart: 14 + rand() * 10, arms: [0, 0] };
  // Bandlik boshlang'ich darajasi atrofida qoladi (kelgan va ketgan mashinalar soni muvozanatda)
  const target = occupied.filter((x) => x !== null).length / Math.max(occupied.length, 1);
  const between = ([a, b]: [number, number]) => a + rand() * (b - a);
  const moving = () => cars.filter((c) => c.state === 'arriving' || c.state === 'departing').length;
  const targeted = new Set<number>();

  const arrive = () => {
    const freeStalls = L.stalls.map((_, i) => i).filter((i) => occupied[i] === null && !targeted.has(i));
    for (let tries = 0; tries < 6 && freeStalls.length; tries++) {
      const k = Math.floor(rand() * freeStalls.length), si = freeStalls.splice(k, 1)[0];
      const gin = lanePt(1, -11), E = front(si);
      const path = findPath(nav, gin, E);
      if (!path) continue;
      const v = stallV(si), [sx, sy] = L.stalls[si];
      // Darvozadan kirib, yo'lak bo'ylab joy oldiga keladi, so'ng old tomoni bilan joyga kiradi
      const pts: XY[] = [lanePt(1, 1.5), lanePt(1, -4), gin, ...path.slice(1, -1), E,
        [sx + v[0] * (SD / 2 - 0.2), sy + v[1] * (SD / 2 - 0.2)], [sx - v[0] * 0.15, sy - v[1] * 0.15]];
      let idx = cars.findIndex((c) => c.state === 'gone');
      const car: Car = { color: Math.floor(rand() * 8), kind: rand() < 0.3 ? 1 : 0, stall: si, state: 'arriving',
        pose: { x: pts[0][0], y: pts[0][1], h: L.gate!.rot + Math.PI }, legs: [smoothLeg(pts, false)], leg: 0, s: 0, scale: 0 };
      if (idx < 0) { cars.push(car); idx = cars.length - 1; } else cars[idx] = car;
      targeted.add(si);
      return true;
    }
    return false;
  };

  const depart = () => {
    const parked = cars.map((c, i) => [c, i] as const).filter(([c]) => c.state === 'parked' && c.stall !== null);
    for (let tries = 0; tries < 6 && parked.length; tries++) {
      const k = Math.floor(rand() * parked.length), [car] = parked.splice(k, 1)[0];
      const si = car.stall!;
      const v = stallV(si), u: XY = [-v[1], v[0]], E = front(si);
      const gout = lanePt(-1, -11);
      const path = findPath(nav, E, gout);
      if (!path || path.length < 2) continue;
      // Chiqib ketish yo'nalishi: yo'lning boshidagi tomoni
      const look = path.find((p) => Math.hypot(p[0] - E[0], p[1] - E[1]) > 2.5) ?? path[path.length - 1];
      const sg = Math.sign((look[0] - E[0]) * u[0] + (look[1] - E[1]) * u[1]) || 1;
      const noseIn = Math.cos(car.pose.h - Math.atan2(-v[1], -v[0])) > 0;
      const start: XY = [car.pose.x, car.pose.y];
      const legs: Leg[] = [];
      let from: XY;
      if (noseIn) {
        // Orqaga chiqadi: dumi ketish yo'nalishiga teskari tomonga buriladi
        from = [E[0] - u[0] * sg * 2.6, E[1] - u[1] * sg * 2.6];
        legs.push(smoothLeg([start, [start[0] + v[0] * SD * 0.45, start[1] + v[1] * SD * 0.45], E, from], true, 2));
      } else {
        from = [E[0] + u[0] * sg * 2.6, E[1] + u[1] * sg * 2.6];
        legs.push(smoothLeg([start, [start[0] + v[0] * SD * 0.45, start[1] + v[1] * SD * 0.45], E, from], false, 2));
      }
      const rest = findPath(nav, from, gout) ?? path;
      legs.push(smoothLeg([from, ...rest.slice(1), gout, lanePt(-1, -4), lanePt(-1, 1.5)], false));
      car.state = 'departing'; car.legs = legs; car.leg = 0; car.s = 0;
      occupied[si] = null;
      car.stall = null;
      return true;
    }
    return false;
  };

  /** dt soniyaga suradi; biror narsa o'zgargan bo'lsa true */
  const step = (dt: number) => {
    sim.T += dt;
    let changed = false;
    const occ = occupied.filter((x) => x !== null).length / Math.max(occupied.length, 1);
    if (sim.T >= sim.nextArrive) {
      if (moving() < cfg.maxMoving && occ < target + 0.06) arrive();
      sim.nextArrive = sim.T + between(cfg.arriveEvery);
    }
    if (sim.T >= sim.nextDepart) {
      if (moving() < cfg.maxMoving && occ > target - 0.06) depart();
      sim.nextDepart = sim.T + between(cfg.departEvery);
    }
    let armIn = 0, armOut = 0;
    cars.forEach((car, idx) => {
      if (car.state !== 'arriving' && car.state !== 'departing') return;
      changed = true;
      const leg = car.legs[car.leg];
      const len = leg.cum[leg.cum.length - 1];
      const vmax = leg.reverse ? cfg.reverseSpeed : cfg.speed;
      // Joyidan qo'zg'alish va to'xtashda sekinlashadi
      const v = vmax * Math.min(1, 0.3 + car.s / 2.5, 0.2 + (len - car.s) / 3.5);
      car.s = Math.min(car.s + v * dt, len);
      const { p, t } = sampleLeg(leg, car.s);
      const tl = Math.hypot(t[0], t[1]);
      if (tl > 1e-4) {
        const h = Math.atan2(t[1], t[0]) + (leg.reverse ? Math.PI : 0);
        const dh = Math.atan2(Math.sin(h - car.pose.h), Math.cos(h - car.pose.h));
        car.pose.h += dh * Math.min(1, dt * 10);
      }
      car.pose.x = p[0]; car.pose.y = p[1];
      // Darvozada paydo bo'lish / yo'qolish: chegaradan tashqarida kichrayadi (tashqarida ko'cha yo'q)
      const along = (p[0] - L.gate!.at[0]) * o[0] + (p[1] - L.gate!.at[1]) * o[1];
      car.scale = Math.min(1, Math.max(0, (1.5 - along) / 3));
      const dBar = Math.hypot(p[0] - barrier[0], p[1] - barrier[1]);
      if (dBar < 9) { if (car.state === 'arriving') armIn = 1; else armOut = 1; }
      if (car.s >= len - 1e-3) {
        if (car.leg < car.legs.length - 1) { car.leg++; car.s = 0; return; }
        if (car.state === 'arriving') {
          car.state = 'parked';
          occupied[car.stall!] = idx;
          targeted.delete(car.stall!);
        } else {
          car.state = 'gone';
          car.scale = 0;
        }
      }
    });
    for (const [k, target] of [[0, armIn], [1, armOut]] as const) {
      const a = sim.arms[k], next = a + Math.sign(target - a) * Math.min(Math.abs(target - a), dt * 1.4);
      if (next !== a) { sim.arms[k] = next; changed = true; }
    }
    return changed;
  };

  return { sim, step, arrive, depart };
}

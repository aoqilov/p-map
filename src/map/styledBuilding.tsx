// Fotoga qarab qurilgan binolar (hozircha "More" majmuasi): oq ustunlar, yog'och friz va panellar,
// katta oynalar, naqshli oq panellar, past qiyalikli metall tom, tomdagi konditsionerlar va shamollatgichlar.
// Kechasi derazalar iliq rangda yonadi. Har bino — 3 ta draw call (devor, tom, detallar).
import { useEffect, useMemo } from 'react';
import * as THREE from 'three';
import type { ThreeEvent } from '@react-three/fiber';
import type { BuildingLook } from './config';
import { canvasTexture, mergeAll } from './modelKit';
import type { XY } from './projection';
import type { Palette } from './theme';
import type { Building } from './types';

const PPM = 64; // teksturada 1 m = 64 piksel
const MODULE = 4; // fasad moduli (ustun + oraliq + naqshli panel), m
const TILE_MODULES = 2; // tekstura 2 modulda takrorlanadi (ikkinchisi biroz boshqacha — bir xillik sezilmasin)
const PILASTER = 0.9; // oq ustun eni, m
const LATTICE = 0.7; // naqshli panel eni, m

export const w = (p: XY, h: number) => new THREE.Vector3(p[0], h, -p[1]);

// ---------------------------------------------------------------- teksturalar

/** Fasad qatlamlari (m): poydevor, 1-qavat, har yuqori qavat, yog'och friz, qopqoq */
function floorsLayout(H: number, floors: number) {
  const plinth = 0.35, ground = 3.05, frieze = 1.3, cap = 0.3;
  const upper = floors > 1 ? (H - plinth - ground - frieze - cap) / (floors - 1) : 0;
  return { plinth, ground, frieze, cap, upper: Math.max(upper, 1.6) };
}

export function woodSlats(g: CanvasRenderingContext2D, x: number, y: number, wpx: number, hpx: number, vertical: boolean, seed: number) {
  g.fillStyle = '#8d5a30';
  g.fillRect(x, y, wpx, hpx);
  const step = 0.11 * PPM;
  let s = seed;
  const rnd = () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
  for (let k = 0; k * step < (vertical ? wpx : hpx); k++) {
    const t = 0.85 + rnd() * 0.25;
    g.fillStyle = `rgb(${Math.round(141 * t)},${Math.round(90 * t)},${Math.round(48 * t)})`;
    if (vertical) g.fillRect(x + k * step, y, step - 1.5, hpx);
    else g.fillRect(x, y + k * step, wpx, step - 1.5);
  }
}

export function glass(g: CanvasRenderingContext2D, x: number, y: number, wpx: number, hpx: number) {
  const gr = g.createLinearGradient(0, y, 0, y + hpx);
  gr.addColorStop(0, '#1d2731');
  gr.addColorStop(1, '#3f4d59');
  g.fillStyle = gr;
  g.fillRect(x, y, wpx, hpx);
  // osmon aksi — qiya och tasma
  g.save();
  g.beginPath(); g.rect(x, y, wpx, hpx); g.clip();
  g.fillStyle = 'rgba(190,215,235,0.13)';
  g.beginPath();
  g.moveTo(x + wpx * 0.15, y + hpx); g.lineTo(x + wpx * 0.55, y); g.lineTo(x + wpx * 0.8, y); g.lineTo(x + wpx * 0.4, y + hpx);
  g.fill();
  g.restore();
}

/** Naqshli panel: oq fonda kesishgan romblar va nuqtalar (an'anaviy panjara uslubida) */
function lattice(g: CanvasRenderingContext2D, x: number, y: number, wpx: number, hpx: number) {
  g.fillStyle = '#eceae4';
  g.fillRect(x, y, wpx, hpx);
  g.save();
  g.beginPath(); g.rect(x + 3, y + 3, wpx - 6, hpx - 6); g.clip();
  g.strokeStyle = '#9da1a6';
  g.lineWidth = 2;
  const s = wpx / 2;
  for (let k = -hpx / s - 2; k < hpx / s + 4; k++) {
    g.beginPath(); g.moveTo(x, y + k * s); g.lineTo(x + wpx * 2, y + k * s + wpx * 2); g.stroke();
    g.beginPath(); g.moveTo(x + wpx, y + k * s); g.lineTo(x - wpx, y + k * s + wpx * 2); g.stroke();
  }
  g.fillStyle = '#8b9096';
  for (let k = 0; k < hpx / s + 1; k++) for (const fx of [0.5]) {
    g.beginPath(); g.arc(x + wpx * fx, y + k * s + s / 2, 2.4, 0, Math.PI * 2); g.fill();
  }
  g.restore();
  g.strokeStyle = '#c9c7c0'; g.lineWidth = 3;
  g.strokeRect(x + 1.5, y + 1.5, wpx - 3, hpx - 3);
}

/** Fasad va kechki derazalar niqobi (bir xil o'lchamda). Tekstura: eni TILE_MODULES×MODULE m, bo'yi H m */
function facadeTextures(look: BuildingLook) {
  const H = look.height;
  const L = floorsLayout(H, look.floors);
  const Wpx = TILE_MODULES * MODULE * PPM, Hpx = Math.round(H * PPM);
  const Y = (h: number) => Math.round((H - h) * PPM); // balandlik → canvas y (tepasi 0)
  const X = (m: number) => Math.round(m * PPM);
  const windows: { x: number; y: number; w: number; h: number; lit: number }[] = [];
  /** Oyna romlari — kechasi ham qora qolsin (yorug' oyna bo'laklarga bo'linib ko'rinadi) */
  const bars: [number, number, number, number][] = [];
  const bar = (g: CanvasRenderingContext2D, x: number, y: number, wpx: number, hpx: number) => { g.fillRect(x, y, wpx, hpx); bars.push([x, y, wpx, hpx]); };

  const facade = canvasTexture(Wpx, Hpx, (g) => {
    g.fillStyle = '#f2f1ec';
    g.fillRect(0, 0, Wpx, Hpx);
    g.fillStyle = '#5b5f65';
    g.fillRect(0, Y(L.plinth), Wpx, Hpx - Y(L.plinth)); // poydevor
    for (let m = 0; m < TILE_MODULES; m++) {
      const x0 = m * MODULE;
      const bayX = x0 + PILASTER, bayW = MODULE - PILASTER - (look.facade === 'more' ? LATTICE : 0);
      // Ustun: yon soyalar hajm beradi
      g.fillStyle = '#d8d6cf';
      g.fillRect(X(x0), 0, 3, Y(L.plinth));
      g.fillRect(X(x0 + PILASTER) - 4, 0, 4, Y(L.plinth));
      // 1-qavat: katta oyna, yog'och romlar, birinchi modulda eshik
      const gy0 = L.plinth, gy1 = L.plinth + L.ground;
      glass(g, X(bayX), Y(gy1), X(bayW), Y(gy0) - Y(gy1));
      windows.push({ x: X(bayX), y: Y(gy1), w: X(bayW), h: Y(gy0) - Y(gy1), lit: m === 0 ? 0.9 : 0.72 });
      g.fillStyle = '#7a4a26';
      for (const f of [0, 1 / 3, 2 / 3, 1]) bar(g, X(bayX + bayW * f) - 3, Y(gy1), 6, Y(gy0) - Y(gy1));
      bar(g, X(bayX), Y(gy0 + 2.45) - 3, X(bayW), 6); // transom
      if (m === 0) { g.fillStyle = 'rgba(10,14,18,0.55)'; g.fillRect(X(bayX + bayW / 3) + 3, Y(gy0 + 2.4), X(bayW / 3) - 6, Y(gy0) - Y(gy0 + 2.4)); }
      // Yuqori qavatlar
      for (let f = 1; f < look.floors; f++) {
        const fy0 = gy1 + (f - 1) * L.upper; // qavatlararo oq tasma
        const wy0 = fy0 + 0.42, wy1 = fy0 + L.upper;
        if (look.facade === 'more') {
          if ((m + f) % 2 === 1) {
            glass(g, X(bayX + 0.1), Y(wy1), X(bayW - 0.2), Y(wy0) - Y(wy1));
            g.fillStyle = '#7a4a26';
            bar(g, X(bayX + bayW / 2) - 3, Y(wy1), 6, Y(wy0) - Y(wy1));
            windows.push({ x: X(bayX + 0.1), y: Y(wy1), w: X(bayW - 0.2), h: Y(wy0) - Y(wy1), lit: m === 1 ? 0.7 : 0.2 });
          } else {
            woodSlats(g, X(bayX), Y(wy1), X(bayW), Y(wy0) - Y(wy1), true, 11 + m * 7 + f);
            glass(g, X(bayX + bayW * 0.62), Y(wy1 - 0.15), X(bayW * 0.28), Y(wy0 + 0.15) - Y(wy1 - 0.15));
            windows.push({ x: X(bayX + bayW * 0.62), y: Y(wy1 - 0.15), w: X(bayW * 0.28), h: Y(wy0 + 0.15) - Y(wy1 - 0.15), lit: 0.6 });
          }
        } else {
          // Yog'ochli variant: butun oraliq yog'och, ichida tor tik deraza
          woodSlats(g, X(bayX), Y(wy1), X(bayW), Y(wy0) - Y(wy1), true, 23 + m * 5 + f);
          for (const fx of [0.18, 0.62]) {
            glass(g, X(bayX + bayW * fx), Y(wy1 - 0.2), X(bayW * 0.2), Y(wy0 + 0.1) - Y(wy1 - 0.2));
            windows.push({ x: X(bayX + bayW * fx), y: Y(wy1 - 0.2), w: X(bayW * 0.2), h: Y(wy0 + 0.1) - Y(wy1 - 0.2), lit: fx < 0.5 ? 0.7 : 0.45 });
          }
        }
      }
      // Yog'och friz (tom ostidagi keng tasma)
      const fr0 = H - L.cap - L.frieze, fr1 = H - L.cap;
      woodSlats(g, X(bayX), Y(fr1), X(bayW), Y(fr0) - Y(fr1), false, 41 + m);
      // Naqshli panel
      if (look.facade === 'more') {
        const lx = x0 + MODULE - LATTICE;
        lattice(g, X(lx), Y(H - L.cap), X(LATTICE), Y(L.plinth) - Y(H - L.cap));
      }
    }
    g.fillStyle = '#e4e2dc';
    g.fillRect(0, Y(H) , Wpx, Y(H - L.cap) - Y(H)); // tepadagi qopqoq
    g.fillStyle = '#c9c7c0';
    g.fillRect(0, Y(H - L.cap) - 2, Wpx, 2);
  });

  // Kechki derazalar: fasad bilan bir xil o'lchamda, faqat oynalar yorug'
  const glow = canvasTexture(Wpx, Hpx, (g) => {
    g.fillStyle = '#000';
    g.fillRect(0, 0, Wpx, Hpx);
    for (const r of windows) {
      const v = Math.round(255 * r.lit);
      const gr = g.createLinearGradient(0, r.y, 0, r.y + r.h);
      gr.addColorStop(0, `rgb(${Math.round(v * 0.75)},${Math.round(v * 0.6)},${Math.round(v * 0.35)})`);
      gr.addColorStop(1, `rgb(${v},${Math.round(v * 0.82)},${Math.round(v * 0.55)})`);
      g.fillStyle = gr;
      g.fillRect(r.x + 3, r.y + 3, r.w - 6, r.h - 6);
    }
    g.fillStyle = '#000';
    for (const [x, y, bw, bh] of bars) g.fillRect(x, y, bw, bh);
  });
  for (const t of [facade, glow]) {
    t.wrapS = THREE.RepeatWrapping;
    t.wrapT = THREE.ClampToEdgeWrapping;
    t.repeat.set(1 / (TILE_MODULES * MODULE), 1 / H);
  }
  return { facade, glow };
}

/** Metall tom: tik choklar (standing seam) har 0.5 m da. UV metrda, 4×4 m da takrorlanadi */
function roofTexture() {
  const tex = canvasTexture(256, 256, (g, W, Hh) => {
    g.fillStyle = '#c3c6ca';
    g.fillRect(0, 0, W, Hh);
    for (let i = 0; i < 2500; i++) {
      const v = 180 + Math.random() * 40;
      g.fillStyle = `rgba(${v},${v + 2},${v + 5},0.35)`;
      g.fillRect(Math.random() * W, Math.random() * Hh, 2, 1);
    }
    const step = W / 8; // 0.5 m
    for (let k = 0; k < 8; k++) {
      g.fillStyle = '#e2e5e8'; g.fillRect(k * step, 0, 2, Hh);
      g.fillStyle = '#9da2a8'; g.fillRect(k * step + 2, 0, 1.5, Hh);
    }
  });
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(1 / 4, 1 / 4);
  return tex;
}

// Teksturalar bino turlari bo'yicha bir marta yaratiladi
const texCache = new Map<string, { facade: THREE.CanvasTexture; glow: THREE.CanvasTexture }>();
let roofTex: THREE.CanvasTexture | null = null;
const facadeFor = (look: BuildingLook) => {
  const key = `${look.facade}-${look.height}-${look.floors}`;
  if (!texCache.has(key)) texCache.set(key, facadeTextures(look));
  return texCache.get(key)!;
};

// ---------------------------------------------------------------- geometriya

export interface Buf { pos: number[]; nor: number[]; uv: number[] }
export const newBuf = (): Buf => ({ pos: [], nor: [], uv: [] });
export function tri(b: Buf, v: THREE.Vector3[], uv: number[][], up?: THREE.Vector3) {
  const n = new THREE.Vector3().crossVectors(v[1].clone().sub(v[0]), v[2].clone().sub(v[0])).normalize();
  let order = [0, 1, 2];
  if (up && n.dot(up) < 0) { order = [0, 2, 1]; n.negate(); }
  for (const k of order) { b.pos.push(v[k].x, v[k].y, v[k].z); b.nor.push(n.x, n.y, n.z); b.uv.push(uv[k][0], uv[k][1]); }
}
export const quad = (b: Buf, v: THREE.Vector3[], uv: number[][], up?: THREE.Vector3) => {
  tri(b, [v[0], v[1], v[2]], [uv[0], uv[1], uv[2]], up);
  tri(b, [v[0], v[2], v[3]], [uv[0], uv[2], uv[3]], up);
};
export const toGeom = (b: Buf) => {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(b.pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(b.nor, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(b.uv, 2));
  g.computeBoundingSphere();
  return g;
};

export function ringOf(b: Building): XY[] {
  const r = b.poly[0];
  const closed = r.length > 1 && r[0][0] === r[r.length - 1][0] && r[0][1] === r[r.length - 1][1];
  return closed ? r.slice(0, -1) : r;
}

/** Devorlar: har qirra alohida, u — metr (har devor oq ustun bilan boshlanib, oq ustun bilan tugaydi), v — balandlik */
function wallGeometry(ring: XY[], H: number) {
  const b = newBuf();
  let area = 0;
  for (let i = 0; i < ring.length; i++) { const p = ring[i], q = ring[(i + 1) % ring.length]; area += p[0] * q[1] - q[0] * p[1]; }
  const ccw = area > 0;
  for (let i = 0; i < ring.length; i++) {
    const p = ring[i], q = ring[(i + 1) % ring.length];
    const len = Math.hypot(q[0] - p[0], q[1] - p[1]);
    if (len < 0.05) continue;
    const n = Math.max(1, Math.round((len - PILASTER) / MODULE));
    const uEnd = n * MODULE + PILASTER; // devorga butun modullar sig'adi
    const dx = (q[0] - p[0]) / len, dy = (q[1] - p[1]) / len;
    const out = ccw ? new THREE.Vector3(dy, 0, dx) : new THREE.Vector3(-dy, 0, -dx); // dunyo: z = −y
    quad(b, [w(p, 0), w(q, 0), w(q, H), w(p, H)], [[0, 0], [uEnd, 0], [uEnd, H], [0, H]], out);
  }
  return toGeom(b);
}

interface RoofFrame { center: XY; a: XY; b: XY; hl: number; hw: number }

/** To'rtburchakmi? (4 burchak, burchaklar ~90°) — bo'lsa, o'qlari va o'lchamlari */
function rectFrame(ring: XY[]): RoofFrame | null {
  if (ring.length !== 4) return null;
  const e = ring.map((p, i) => { const q = ring[(i + 1) % 4]; return [q[0] - p[0], q[1] - p[1]] as XY; });
  const len = e.map((v) => Math.hypot(v[0], v[1]));
  for (let i = 0; i < 4; i++) {
    const j = (i + 1) % 4;
    if (Math.abs((e[i][0] * e[j][0] + e[i][1] * e[j][1]) / (len[i] * len[j])) > 0.12) return null;
  }
  const long = len[0] + len[2] >= len[1] + len[3] ? 0 : 1;
  const a: XY = [e[long][0] / len[long], e[long][1] / len[long]];
  const bv: XY = [-a[1], a[0]];
  const center: XY = [ring.reduce((s, p) => s + p[0], 0) / 4, ring.reduce((s, p) => s + p[1], 0) / 4];
  return { center, a, b: bv, hl: (len[long] + len[long + 2]) / 4, hw: (len[1 - long] + len[3 - long]) / 4 };
}

const OVERHANG = 0.45;

/** Past qiyalikli to'rt qiyali (hip) tom + chekka taxta, konditsionerlar, shamollatgichlar */
function hipRoof(f: RoofFrame, H: number, look: BuildingLook) {
  const t = Math.tan(THREE.MathUtils.degToRad(look.roofPitch)), cs = Math.cos(THREE.MathUtils.degToRad(look.roofPitch));
  const HL = f.hl + OVERHANG, HW = f.hw + OVERHANG;
  const eave = H - OVERHANG * t;
  const rl = Math.max(HL - HW, 0), ridge = eave + HW * t;
  /** Tom tekisligida: along — uzun o'q bo'ylab, across — ko'ndalang (m) → ma'lumot koordinatasi */
  const P = (along: number, across: number): XY =>
    [f.center[0] + f.a[0] * along + f.b[0] * across, f.center[1] + f.a[1] * along + f.b[1] * across];
  const C = (sa: number, sb: number) => w(P(sa * HL, sb * HW), eave);
  const R = (sa: number) => w(P(sa * rl, 0), ridge);
  const up = new THREE.Vector3(0, 1, 0);
  const roof = newBuf();
  for (const sb of [1, -1]) {
    // uzun qiya: u — tom bo'ylab, v — qiyalik bo'ylab yuqoriga (m)
    quad(roof, [C(1, sb), C(-1, sb), R(-1), R(1)], [[HL, 0], [-HL, 0], [-rl, HW / cs], [rl, HW / cs]], up);
  }
  for (const sa of [1, -1]) {
    tri(roof, [C(sa, -1), C(sa, 1), R(sa)], [[-HW, 0], [HW, 0], [0, (HL - rl) / cs]], up);
  }

  // Detallar: vertex rangli, bitta geometriya
  const parts: THREE.BufferGeometry[] = [];
  const colorize = (g: THREE.BufferGeometry, hex: string) => {
    const ng = g.index ? g.toNonIndexed() : g;
    if (ng !== g) g.dispose();
    ng.deleteAttribute('uv');
    const c = new THREE.Color(hex);
    ng.setAttribute('color', new THREE.Float32BufferAttribute(Array.from({ length: ng.attributes.position.count }, () => [c.r, c.g, c.b]).flat(), 3));
    parts.push(ng);
  };
  const yaw = Math.atan2(f.a[1], f.a[0]); // tom o'qi bo'ylab burilish: lokal +x → dunyoda (a.x, 0, −a.y)
  // Chekka taxta (fascia)
  const corners = [C(1, 1), C(-1, 1), C(-1, -1), C(1, -1)];
  for (let i = 0; i < 4; i++) {
    const p = corners[i], q = corners[(i + 1) % 4];
    const len = p.distanceTo(q), mid = p.clone().add(q).multiplyScalar(0.5);
    const g = new THREE.BoxGeometry(len + 0.1, 0.24, 0.08);
    g.rotateY(Math.atan2(-(q.z - p.z), q.x - p.x));
    g.translate(mid.x, eave - 0.1, mid.z);
    colorize(g, '#e9e8e4');
  }
  // Tizma qopqog'i
  if (rl > 0.1) {
    const g = new THREE.BoxGeometry(rl * 2 + 0.3, 0.12, 0.34);
    g.rotateY(yaw);
    const m = w(f.center, ridge + 0.03);
    g.translate(m.x, m.y, m.z);
    colorize(g, '#aeb2b7');
  }
  // Uchburchak shamollatgichlar (fotodagidek), har uzun qiyada bir necha
  const vents = Math.max(2, Math.round((rl * 2) / 11));
  for (const sb of [1, -1]) {
    for (let k = 0; k < vents; k++) {
      const along = rl * 2 * ((k + 0.5) / vents) - rl;
      const dFront = HW * 0.62, vh = 0.5, vw = 1.0, dBack = dFront - vh / t;
      const hF = ridge - dFront * t;
      const Fl = w(P(along - vw / 2, sb * dFront), hF), Fr = w(P(along + vw / 2, sb * dFront), hF);
      const Ft = w(P(along, sb * dFront), hF + vh), B = w(P(along, sb * Math.max(dBack, 0.2)), hF + vh);
      const vb = newBuf();
      tri(vb, [Fl, Fr, Ft], [[0, 0], [1, 0], [0.5, 1]]);
      tri(vb, [Fl, Ft, B], [[0, 0], [1, 0], [0.5, 1]], up);
      tri(vb, [Fr, B, Ft], [[0, 0], [1, 0], [0.5, 1]], up);
      const g = toGeom(vb);
      // old yuz to'q (panjara), yonlari tom rangida
      const c = new THREE.Color('#bfc3c8'), dark = new THREE.Color('#4a5058');
      g.setAttribute('color', new THREE.Float32BufferAttribute([0, 1, 2, 3, 4, 5, 6, 7, 8].map((i) => (i < 3 ? dark : c)).flatMap((cc) => [cc.r, cc.g, cc.b]), 3));
      g.deleteAttribute('uv');
      // old yuz har ikki tomondan ko'rinsin: normalini tashqariga (qiyalik pastiga) qaratamiz
      parts.push(g);
    }
  }
  // Konditsionerlar: uzun qiyalarda, bir-biriga yopishmasdan
  let s = Math.round(f.center[0] * 13 + f.center[1] * 7) | 1;
  const rnd = () => { s = (s * 16807) % 2147483647; if (s <= 0) s += 2147483646; return s / 2147483647; };
  const spots: XY[] = [];
  for (let tries = 0; spots.length < look.roofUnits && tries < 400; tries++) {
    const sb = rnd() < 0.5 ? 1 : -1;
    const d = 1.0 + rnd() * Math.max(HW - 2.4, 0.2); // tizmadan masofa
    const along = (rnd() * 2 - 1) * Math.max(rl + d - 1.2, 0.3);
    const xy = P(along, sb * d);
    if (spots.some((q) => Math.hypot(q[0] - xy[0], q[1] - xy[1]) < 1.8)) continue;
    spots.push(xy);
    const base = ridge - (d + 0.35) * t; // pastki (qiyalik pasti) cheti — tirqish qolmaydi
    const hgt = 0.62 + 0.7 * t;
    const g = new THREE.BoxGeometry(0.95, hgt, 0.68);
    g.rotateY(yaw);
    const c = w(xy, base + hgt / 2);
    g.translate(c.x, c.y, c.z);
    colorize(g, '#eceeef');
    const fan = new THREE.CylinderGeometry(0.22, 0.22, 0.04, 10);
    fan.translate(c.x, base + hgt + 0.02, c.z);
    colorize(fan, '#7d838a');
  }
  return { roof: toGeom(roof), details: mergeAll(parts), top: ridge + 0.1 };
}

function flatRoof(ring: XY[], H: number) {
  const shape = new THREE.Shape(ring.map(([x, y]) => new THREE.Vector2(x, y)));
  const g = new THREE.ShapeGeometry(shape, 1);
  g.rotateX(-Math.PI / 2);
  g.translate(0, H + 0.01, 0);
  // Detallar yo'q: bo'sh geometriya (vertex rangli material qora nuqta chizmasin)
  const empty = new THREE.BufferGeometry();
  empty.setAttribute('position', new THREE.Float32BufferAttribute([], 3));
  return { roof: g, details: empty, top: H };
}

/** Bino tepasi (pin balandligi uchun) */
export function styledTop(b: Building, look: BuildingLook) {
  const f = rectFrame(ringOf(b));
  if (!f) return look.height;
  const t = Math.tan(THREE.MathUtils.degToRad(look.roofPitch));
  return look.height - OVERHANG * t + (f.hw + OVERHANG) * t;
}

// ---------------------------------------------------------------- komponent

const isTap = (e: ThreeEvent<MouseEvent>) => e.delta < 6;

export function StyledBuilding({ b, look, pal, night, selected, onSelect }: {
  b: Building; look: BuildingLook; pal: Palette; night: boolean; selected: boolean; onSelect: (id: string) => void;
}) {
  const parts = useMemo(() => {
    const ring = ringOf(b);
    const frame = rectFrame(ring);
    const walls = wallGeometry(ring, look.height);
    const top = frame ? hipRoof(frame, look.height, look) : flatRoof(ring, look.height);
    return { walls, ...top };
  }, [b, look]);
  useEffect(() => () => { parts.walls.dispose(); parts.roof.dispose(); parts.details.dispose(); }, [parts]);
  const tex = facadeFor(look);
  const roof = (roofTex ??= roofTexture());
  const tint = selected ? pal.selected : night ? '#a3a8af' : '#ffffff'; // kechasi metall tom xiraroq
  // Oq suvoq soyada ham oppoq ko'rinsin (fotodagidek): devor rangi biroz 1 dan yuqori
  const wallTint = useMemo(() => (selected ? new THREE.Color(pal.selected) : new THREE.Color(1.18, 1.18, 1.18)), [selected, pal]);
  return (
    <group onClick={(e) => { if (!isTap(e)) return; e.stopPropagation(); onSelect(b.id); }}>
      <mesh geometry={parts.walls} castShadow receiveShadow>
        <meshStandardMaterial map={tex.facade} emissiveMap={tex.glow} emissive="#ffcf8a"
          emissiveIntensity={night ? 0.75 : 0} color={wallTint} roughness={0.8} />
      </mesh>
      <mesh geometry={parts.roof} castShadow receiveShadow>
        <meshStandardMaterial map={roof} color={tint} roughness={0.5} metalness={0.2} side={THREE.DoubleSide} />
      </mesh>
      <mesh geometry={parts.details} castShadow receiveShadow>
        <meshStandardMaterial vertexColors roughness={0.6} side={THREE.DoubleSide} />
      </mesh>
    </group>
  );
}

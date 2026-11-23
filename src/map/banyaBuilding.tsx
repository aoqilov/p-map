// Banya — fotoga qarab: 3 qavat, krem suvoq va to'q g'isht ustunlar, tor tik derazalar, yuqori qavat to'q ko'k
// plitka bilan qoplangan. Hovuzga qaragan dumaloq qismda tosh ustunlar, katta oynalar va oq egri balkonlar (gullari bilan).
// G'arbiy burchak oldida qizil g'ishtli kirish: "БАНЯ" yozuvi, oyna eshik, zinapoya. Tom tekis, ustida to'q qo'shimcha qavat.
// Kechasi derazalar, eshik va yozuv yonadi.
import { useEffect, useMemo } from 'react';
import * as THREE from 'three';
import type { ThreeEvent } from '@react-three/fiber';
import type { BuildingLook } from './config';
import { distToBoundary, inPoly } from './geo';
import { canvasTexture, mergeAll } from './modelKit';
import type { XY } from './projection';
import { newBuf, quad, ringOf, toGeom, w } from './styledBuilding';
import type { Palette } from './theme';
import type { Building } from './types';

const PPM = 48; // teksturada 1 m = 48 piksel
const MAIN = { module: 3.6, pier: 0.7 }; // asosiy fasad moduli: g'isht ustun + suvoq + deraza
const CURVE_MODULE = 3.0; // dumaloq qism moduli: tosh ustun + katta oyna
const DARK_FROM = 7.6; // shu balandlikdan yuqorisi to'q plitka
const ROOF_DROP = 0.45; // tekis tom parapetdan shuncha pastda
const TOWER_H = 7.9;

// ---------------------------------------------------------------- teksturalar

type Win = { x: number; y: number; w: number; h: number; lit: number };

function noise(g: CanvasRenderingContext2D, W: number, H: number, n: number, rgb: string, a = 0.18) {
  for (let i = 0; i < n; i++) {
    g.fillStyle = `rgba(${rgb},${a * Math.random()})`;
    g.fillRect(Math.random() * W, Math.random() * H, 2, 1);
  }
}

function bricks(g: CanvasRenderingContext2D, x: number, y: number, wpx: number, hpx: number, tones: string[], mortar: string) {
  g.fillStyle = mortar;
  g.fillRect(x, y, wpx, hpx);
  const bw = 0.25 * PPM, bh = 0.075 * PPM;
  g.save(); g.beginPath(); g.rect(x, y, wpx, hpx); g.clip();
  for (let r = 0; r * bh < hpx; r++) {
    for (let c = -1; c * bw < wpx; c++) {
      g.fillStyle = tones[(r * 7 + c * 3 + (r % 3)) % tones.length];
      g.fillRect(x + c * bw + (r % 2 ? bw / 2 : 0) + 0.6, y + r * bh + 0.6, bw - 1.2, bh - 1.2);
    }
  }
  g.restore();
}

function tealGlass(g: CanvasRenderingContext2D, x: number, y: number, wpx: number, hpx: number, dark = false) {
  const gr = g.createLinearGradient(0, y, 0, y + hpx);
  gr.addColorStop(0, dark ? '#1f2a31' : '#2c5560');
  gr.addColorStop(1, dark ? '#4a5a64' : '#6a9aa4');
  g.fillStyle = gr;
  g.fillRect(x, y, wpx, hpx);
  g.fillStyle = 'rgba(220,240,250,0.12)';
  g.beginPath(); g.moveTo(x + wpx * 0.2, y + hpx); g.lineTo(x + wpx * 0.7, y); g.lineTo(x + wpx * 0.9, y); g.lineTo(x + wpx * 0.4, y + hpx); g.fill();
  g.strokeStyle = '#2a2e33'; g.lineWidth = 2;
  g.strokeRect(x + 1, y + 1, wpx - 2, hpx - 2);
}

function darkTiles(g: CanvasRenderingContext2D, x: number, y: number, wpx: number, hpx: number) {
  g.fillStyle = '#2a3346';
  g.fillRect(x, y, wpx, hpx);
  const s = 0.6 * PPM;
  for (let i = 0; i * s < wpx + s; i++) for (let j = 0; j * s < hpx + s; j++) {
    const t = 0.92 + ((i * 13 + j * 7) % 5) * 0.03;
    g.fillStyle = `rgb(${Math.round(42 * t)},${Math.round(51 * t)},${Math.round(70 * t)})`;
    g.fillRect(x + i * s + 1, y + hpx - (j + 1) * s + 1, s - 2, s - 2);
  }
}

function finish(tex: THREE.CanvasTexture, tileW: number, tileH: number, clampV = true) {
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = clampV ? THREE.ClampToEdgeWrapping : THREE.RepeatWrapping;
  tex.repeat.set(1 / tileW, 1 / tileH);
  return tex;
}

function glowFrom(Wpx: number, Hpx: number, wins: Win[], bars: number[][] = [], extra?: (g: CanvasRenderingContext2D) => void) {
  return canvasTexture(Wpx, Hpx, (g) => {
    g.fillStyle = '#000'; g.fillRect(0, 0, Wpx, Hpx);
    for (const r of wins) {
      const v = Math.round(255 * r.lit);
      g.fillStyle = `rgb(${v},${Math.round(v * 0.8)},${Math.round(v * 0.52)})`;
      g.fillRect(r.x + 3, r.y + 3, r.w - 6, r.h - 6);
    }
    g.fillStyle = '#000';
    for (const [x, y, bw, bh] of bars) g.fillRect(x, y, bw, bh); // romlar kechasi ham qora
    extra?.(g);
  });
}

/** Asosiy fasad: 2 modul (7.2 m) da takrorlanadi */
function mainFacade(H: number) {
  const M = MAIN.module, T = 2, Wpx = Math.round(T * M * PPM), Hpx = Math.round(H * PPM);
  const Y = (h: number) => Math.round((H - h) * PPM), X = (m: number) => Math.round(m * PPM);
  const wins: Win[] = [];
  const bars: number[][] = [];
  const bar = (g: CanvasRenderingContext2D, x: number, y: number, bw: number, bh: number) => { g.fillRect(x, y, bw, bh); bars.push([x, y, bw, bh]); };
  const win = (g: CanvasRenderingContext2D, u: number, h0: number, ww: number, hh: number, lit: number, dark = false) => {
    tealGlass(g, X(u), Y(h0 + hh), X(ww), Y(h0) - Y(h0 + hh), dark);
    wins.push({ x: X(u), y: Y(h0 + hh), w: X(ww), h: Y(h0) - Y(h0 + hh), lit });
  };
  const facade = canvasTexture(Wpx, Hpx, (g) => {
    g.fillStyle = '#e6dfcf'; g.fillRect(0, 0, Wpx, Hpx);
    noise(g, Wpx, Hpx, 2500, '150,140,120');
    g.fillStyle = '#5b5f65'; g.fillRect(0, Y(0.35), Wpx, Hpx - Y(0.35));
    for (let m = 0; m < T; m++) {
      const x0 = m * M;
      bricks(g, X(x0), Y(DARK_FROM), X(MAIN.pier), Y(0.35) - Y(DARK_FROM), ['#5a4d43', '#4e433a', '#63564b', '#554940'], '#3a332d');
      if (m === 0) {
        win(g, x0 + 1.15, 0.6, 2.0, 3.0, 0.9);
        g.fillStyle = '#2a2e33'; bar(g, X(x0 + 2.15) - 2, Y(3.6), 4, Y(0.6) - Y(3.6)); bar(g, X(x0 + 1.15), Y(2.9) - 2, X(2.0), 4);
      } else {
        win(g, x0 + 1.3, 0.6, 1.25, 3.0, 0.75);
        g.fillStyle = '#8a5a34'; g.fillRect(X(x0 + 2.8), Y(3.6), X(0.45), Y(0.6) - Y(3.6)); // yog'och panel
      }
      win(g, x0 + 1.75, 4.6, 0.85, 2.5, m === 0 ? 0.65 : 0.25);
      if (m === 1) { g.fillStyle = '#8a5a34'; g.fillRect(X(x0 + 2.8), Y(7.1), X(0.4), Y(4.6) - Y(7.1)); }
    }
    darkTiles(g, 0, Y(H), Wpx, Y(DARK_FROM) - Y(H));
    for (let m = 0; m < T; m++) win(g, m * M + 1.8, 8.0, 0.75, 2.2, m === 0 ? 0.6 : 0.3, true);
    g.fillStyle = '#3c4659'; g.fillRect(0, Y(H), Wpx, Y(H - 0.15) - Y(H));
  });
  return { facade: finish(facade, T * M, H), glow: finish(glowFrom(Wpx, Hpx, wins, bars), T * M, H) };
}

/** Dumaloq qism: tosh ustunlar, har qavatda katta oyna, oq balkon tasmalari. 2 modul (6 m) da takrorlanadi */
function curveFacade(H: number) {
  const M = CURVE_MODULE, T = 2, Wpx = Math.round(T * M * PPM), Hpx = Math.round(H * PPM);
  const Y = (h: number) => Math.round((H - h) * PPM), X = (m: number) => Math.round(m * PPM);
  const wins: Win[] = [];
  const bars: number[][] = [];
  const floors: [number, number][] = [[0.35, 3.9], [4.35, 7.5], [7.95, H - 0.45]];
  const facade = canvasTexture(Wpx, Hpx, (g) => {
    g.fillStyle = '#9b9387'; g.fillRect(0, 0, Wpx, Hpx);
    g.strokeStyle = '#867e73'; g.lineWidth = 1.5;
    for (let r = 0; r * 0.3 * PPM < Hpx; r++) { // tosh qatorlari
      g.beginPath(); g.moveTo(0, r * 0.3 * PPM); g.lineTo(Wpx, r * 0.3 * PPM); g.stroke();
      for (let c = 0; c * 0.6 * PPM < Wpx; c++) {
        const xx = c * 0.6 * PPM + (r % 2 ? 0.3 * PPM : 0);
        g.beginPath(); g.moveTo(xx, r * 0.3 * PPM); g.lineTo(xx, (r + 1) * 0.3 * PPM); g.stroke();
      }
    }
    noise(g, Wpx, Hpx, 1500, '60,55,50');
    for (let m = 0; m < T; m++) {
      const x0 = m * M + 0.6;
      floors.forEach(([h0, h1], f) => {
        tealGlass(g, X(x0), Y(h1), X(M - 0.6), Y(h0) - Y(h1), true);
        g.fillStyle = '#2a2e33'; g.fillRect(X(x0 + (M - 0.6) / 2) - 2, Y(h1), 4, Y(h0) - Y(h1)); bars.push([X(x0 + (M - 0.6) / 2) - 2, Y(h1), 4, Y(h0) - Y(h1)]);
        wins.push({ x: X(x0), y: Y(h1), w: X(M - 0.6), h: Y(h0) - Y(h1), lit: [0.85, 0.55, 0.35][(f + m) % 3] });
      });
    }
    g.fillStyle = '#efede7';
    for (const [a, b] of [[3.9, 4.35], [7.5, 7.95], [H - 0.45, H]]) g.fillRect(0, Y(b), Wpx, Y(a) - Y(b));
    g.fillStyle = '#5b5f65'; g.fillRect(0, Y(0.35), Wpx, Hpx - Y(0.35));
  });
  return { facade: finish(facade, T * M, H), glow: finish(glowFrom(Wpx, Hpx, wins, bars), T * M, H) };
}

/** Qizil g'isht kirish: eshik va "БАНЯ" yozuvi. Tekstura butun old yuzaga (UV 0..1) */
function towerTextures(widthM: number) {
  const Wpx = Math.round(widthM * PPM), Hpx = Math.round(TOWER_H * PPM);
  const Y = (h: number) => Math.round((TOWER_H - h) * PPM), X = (m: number) => Math.round(m * PPM);
  const door = { x: X(widthM / 2 - 0.95), y: Y(2.9), w: X(1.9), h: Y(0) - Y(2.9) };
  const sign = { x: X(widthM / 2 - 1.35), y: Y(5.9), w: X(2.7), h: Y(4.7) - Y(5.9) };
  const text = (g: CanvasRenderingContext2D, color: string) => {
    g.fillStyle = color;
    g.font = `bold ${Math.round(0.72 * PPM)}px "DejaVu Sans", Arial, sans-serif`;
    g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillText('БАНЯ', sign.x + sign.w / 2, sign.y + sign.h / 2 + 1);
  };
  const map = canvasTexture(Wpx, Hpx, (g) => {
    bricks(g, 0, 0, Wpx, Hpx, ['#9a3a2a', '#a8452f', '#8c3324', '#b04b34', '#933828'], '#cdbfae');
    g.fillStyle = '#3b3a3a'; g.fillRect(0, 0, Wpx, Y(TOWER_H - 0.3));
    tealGlass(g, door.x, door.y, door.w, door.h, true);
    g.fillStyle = '#2a2e33'; g.fillRect(door.x + door.w / 2 - 2, door.y, 4, door.h); g.fillRect(door.x, door.y + door.h * 0.18, door.w, 4);
    g.fillStyle = '#262424'; g.fillRect(sign.x, sign.y, sign.w, sign.h);
    g.strokeStyle = '#8d8a85'; g.lineWidth = 2; g.strokeRect(sign.x + 2, sign.y + 2, sign.w - 4, sign.h - 4);
    text(g, '#f4f1ea');
  });
  const glow = canvasTexture(Wpx, Hpx, (g) => {
    g.fillStyle = '#000'; g.fillRect(0, 0, Wpx, Hpx);
    g.fillStyle = 'rgb(230,190,130)'; g.fillRect(door.x + 3, door.y + 3, door.w - 6, door.h - 6);
    text(g, '#fff4dc');
  });
  return { map, glow };
}

/** Qo'shimcha qavat: to'q plitka, har 4 m da tor deraza */
function penthouseTextures(h: number) {
  const Wpx = Math.round(4 * PPM), Hpx = Math.round(h * PPM);
  const Y = (v: number) => Math.round((h - v) * PPM), X = (m: number) => Math.round(m * PPM);
  const win: Win = { x: X(1.6), y: Y(2.6), w: X(0.75), h: Y(0.5) - Y(2.6), lit: 0.55 };
  const map = canvasTexture(Wpx, Hpx, (g) => {
    darkTiles(g, 0, 0, Wpx, Hpx);
    tealGlass(g, win.x, win.y, win.w, win.h, true);
    g.fillStyle = '#3c4659'; g.fillRect(0, 0, Wpx, X(0.15));
  });
  return { map: finish(map, 4, h), glow: finish(glowFrom(Wpx, Hpx, [win]), 4, h) };
}

function flatRoofTexture() {
  const tex = canvasTexture(128, 128, (g, W, H) => {
    g.fillStyle = '#8d9298'; g.fillRect(0, 0, W, H);
    noise(g, W, H, 900, '60,64,70', 0.25);
    g.fillStyle = '#7d8288';
    for (let k = 0; k < 4; k++) { g.fillRect(k * 32, 0, 1.5, H); g.fillRect(0, k * 32, W, 1.5); }
  });
  return finish(tex, 4, 4, false);
}

// ---------------------------------------------------------------- geometriya

const len2 = (a: XY, b: XY) => Math.hypot(b[0] - a[0], b[1] - a[1]);
const dirOf = (a: XY, b: XY) => Math.atan2(b[1] - a[1], b[0] - a[0]);
const angDiff = (a: number, b: number) => Math.atan2(Math.sin(b - a), Math.cos(b - a));

/** Vertex rangli bufer (balkonlar, zina, konditsionerlar) */
interface CBuf { pos: number[]; nor: number[]; col: number[] }
function cquad(b: CBuf, v: THREE.Vector3[], n: THREE.Vector3, hex: string) {
  const c = new THREE.Color(hex);
  const face = new THREE.Vector3().crossVectors(v[1].clone().sub(v[0]), v[2].clone().sub(v[0]));
  const order = face.dot(n) >= 0 ? [0, 1, 2, 0, 2, 3] : [0, 2, 1, 0, 3, 2];
  for (const k of order) { b.pos.push(v[k].x, v[k].y, v[k].z); b.nor.push(n.x, n.y, n.z); b.col.push(c.r, c.g, c.b); }
}
function cgeom(b: CBuf) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(b.pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(b.nor, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(b.col, 3));
  return g;
}
function cbox(sx: number, sy: number, sz: number, yaw: number, at: THREE.Vector3, hex: string) {
  const g = new THREE.BoxGeometry(sx, sy, sz).toNonIndexed();
  g.deleteAttribute('uv');
  g.rotateY(yaw);
  g.translate(at.x, at.y, at.z);
  const c = new THREE.Color(hex);
  g.setAttribute('color', new THREE.Float32BufferAttribute(Array.from({ length: g.attributes.position.count }, () => [c.r, c.g, c.b]).flat(), 3));
  return g;
}

/** Dumaloq qism: qisqa (<4.5 m), bir-biriga silliq ulangan qirralar ketma-ketligi (eng uzuni, ≥10 m) */
function curveRun(ring: XY[]) {
  const n = ring.length;
  const L = (i: number) => len2(ring[i], ring[(i + 1) % n]);
  const D = (i: number) => dirOf(ring[i], ring[(i + 1) % n]);
  let best: number[] = [], cur: number[] = [];
  const total = (r: number[]) => r.reduce((s, i) => s + L(i), 0);
  for (let i = 0; i < n; i++) {
    const short = L(i) < 4.5;
    if (short && (!cur.length || Math.abs(angDiff(D(cur[cur.length - 1]), D(i))) < THREE.MathUtils.degToRad(45))) cur.push(i);
    else { if (total(cur) > total(best)) best = cur; cur = short ? [i] : []; }
  }
  if (total(cur) > total(best)) best = cur;
  return total(best) >= 10 ? best : [];
}

function banyaParts(b: Building, look: BuildingLook) {
  const ring = ringOf(b);
  const n = ring.length, H = look.height;
  let area = 0;
  for (let i = 0; i < n; i++) { const p = ring[i], q = ring[(i + 1) % n]; area += p[0] * q[1] - q[0] * p[1]; }
  const ccw = area > 0;
  /** Qirraning tashqi normali (ma'lumot koordinatasida) */
  const outN = (i: number): XY => {
    const p = ring[i], q = ring[(i + 1) % n], l = len2(p, q) || 1;
    const dx = (q[0] - p[0]) / l, dy = (q[1] - p[1]) / l;
    return ccw ? [dy, -dx] : [-dy, dx];
  };
  const worldN = (v: XY) => new THREE.Vector3(v[0], 0, -v[1]);
  const run = look.balconies ? curveRun(ring) : [];
  const inRun = new Set(run);

  // Devorlar: asosiy (modulga moslangan) va dumaloq qism (uzluksiz)
  const mainB = newBuf(), curveB = newBuf();
  let uc = 0;
  for (let i = 0; i < n; i++) {
    const p = ring[i], q = ring[(i + 1) % n], L = len2(p, q);
    if (L < 0.05) continue;
    const nrm = worldN(outN(i));
    if (inRun.has(i)) {
      quad(curveB, [w(p, 0), w(q, 0), w(q, H), w(p, H)], [[uc, 0], [uc + L, 0], [uc + L, H], [uc, H]], nrm);
      uc += L;
    } else {
      const k = L >= MAIN.module * 0.75 ? Math.max(1, Math.round((L - MAIN.pier) / MAIN.module)) : 0;
      const uEnd = k ? k * MAIN.module + MAIN.pier : L;
      quad(mainB, [w(p, 0), w(q, 0), w(q, H), w(p, H)], [[0, 0], [uEnd, 0], [uEnd, H], [0, H]], nrm);
    }
  }

  const det: THREE.BufferGeometry[] = [];
  const cb: CBuf = { pos: [], nor: [], col: [] };
  const up = new THREE.Vector3(0, 1, 0), down = new THREE.Vector3(0, -1, 0);

  // Egri balkonlar: har qavat ustida plita + oq to'siq, 2-qavat to'sig'ida gullar; tepada karniz
  if (run.length) {
    const pts: XY[] = [...run.map((i) => ring[i]), ring[(run[run.length - 1] + 1) % n]];
    const normals = pts.map((_, k) => {
      const a = k > 0 ? outN(run[k - 1]) : null, c = k < run.length ? outN(run[k]) : null;
      if (!a) return c!;
      if (!c) return a;
      const mx = a[0] + c[0], my = a[1] + c[1], ml = Math.hypot(mx, my) || 1;
      const cosHalf = Math.max((mx / ml) * c[0] + (my / ml) * c[1], 0.5);
      return [mx / ml / cosHalf, my / ml / cosHalf] as XY;
    });
    const off = (k: number, d: number): XY => [pts[k][0] + normals[k][0] * d, pts[k][1] + normals[k][1] * d];
    const slab = (y: number, depth: number, t: number, parapet: number, planter: boolean) => {
      for (let k = 0; k < pts.length - 1; k++) {
        const a = pts[k], c = pts[k + 1], oa = off(k, depth), oc = off(k + 1, depth);
        const e = worldN(outN(run[k]));
        cquad(cb, [w(a, y + t), w(c, y + t), w(oc, y + t), w(oa, y + t)], up, '#f1efe9');
        cquad(cb, [w(a, y), w(c, y), w(oc, y), w(oa, y)], down, '#cfccc4');
        cquad(cb, [w(oa, y), w(oc, y), w(oc, y + t), w(oa, y + t)], e, '#f1efe9');
        if (parapet > 0) {
          const ia = off(k, depth - 0.12), ic = off(k + 1, depth - 0.12), top = y + t + parapet;
          cquad(cb, [w(oa, y + t), w(oc, y + t), w(oc, top), w(oa, top)], e, '#f3f1eb');
          cquad(cb, [w(ia, y + t), w(ic, y + t), w(ic, top), w(ia, top)], e.clone().negate(), '#e3e0d8');
          cquad(cb, [w(ia, top), w(ic, top), w(oc, top), w(oa, top)], up, '#f3f1eb');
          if (planter) {
            const pa = off(k, depth - 0.45), pc = off(k + 1, depth - 0.45), ph = top + 0.28;
            cquad(cb, [w(pa, top), w(pc, top), w(pc, ph), w(pa, ph)], e.clone().negate(), '#4f7a3a');
            cquad(cb, [w(pa, ph), w(pc, ph), w(ic, ph), w(ia, ph)], up, '#5d8c43');
          }
        }
      }
    };
    slab(3.9, 1.4, 0.3, 1.0, true);
    slab(7.5, 1.4, 0.3, 1.0, false);
    slab(H - 0.35, 0.7, 0.35, 0, false);
  }

  // Qizil g'isht kirish + zina
  let tower: THREE.BufferGeometry | null = null, towerWidth = 0;
  if (look.accentEdge !== undefined && look.accentEdge < n) {
    const i = look.accentEdge, p = ring[i], q = ring[(i + 1) % n], L = len2(p, q);
    towerWidth = Math.min(L * 0.84, 7);
    const o = outN(i), mid: XY = [(p[0] + q[0]) / 2 + o[0] * 0.15, (p[1] + q[1]) / 2 + o[1] * 0.15];
    const yaw = Math.atan2(o[0], -o[1]); // lokal +z → tashqi normal
    tower = new THREE.BoxGeometry(towerWidth, TOWER_H, 0.45);
    tower.rotateY(yaw);
    const c = w(mid, TOWER_H / 2);
    tower.translate(c.x, c.y, c.z);
    for (let s = 0; s < 3; s++) {
      const depth = 0.45 * (3 - s), h = 0.16 * (s + 1);
      const at: XY = [mid[0] + o[0] * (0.22 + depth / 2), mid[1] + o[1] * (0.22 + depth / 2)];
      det.push(cbox(3.4 - s * 0.3, h, depth, yaw, w(at, h / 2), s % 2 ? '#d6d1c7' : '#c8c2b7'));
    }
  }

  // Tom: parapetdan biroz pastda, devorlar ikki tomonlama — parapetning ichki tomoni ko'rinadi
  const shape = new THREE.Shape(ring.map(([x, y]) => new THREE.Vector2(x, y)));
  const roof = new THREE.ShapeGeometry(shape, 1);
  roof.rotateX(-Math.PI / 2);
  roof.translate(0, H - ROOF_DROP, 0);

  // Qo'shimcha qavat: eng uzun to'g'ri devor bo'ylab, ichkarida
  let pent: { walls: THREE.BufferGeometry; rect: XY[] } | null = null;
  if (look.penthouse) {
    const ph = look.penthouse;
    // ketma-ket deyarli bir yo'nalishdagi qirralarni birlashtiramiz
    let best = { start: 0, end: 0, len: 0 };
    for (let i = 0; i < n; i++) {
      let j = i, L = 0;
      while (j < i + n) {
        const a = ring[j % n], c = ring[(j + 1) % n];
        if (j > i && Math.abs(angDiff(dirOf(ring[i], ring[(i + 1) % n]), dirOf(a, c))) > THREE.MathUtils.degToRad(3)) break;
        L += len2(a, c); j++;
      }
      if (L > best.len) best = { start: i, end: j % n, len: L };
    }
    const A = ring[best.start], B = ring[best.end];
    const L = len2(A, B), ax = (B[0] - A[0]) / L, ay = (B[1] - A[1]) / L;
    const inv: XY = ccw ? [-ay, ax] : [ay, -ax]; // ichkariga
    let depth = ph.depth;
    /** Devor bo'ylab t metrda, ichkariga d metrda */
    const at = (t: number, d: number): XY => [A[0] + ax * t + inv[0] * d, A[1] + ay * t + inv[1] * d];
    const corners = (d: number): XY[] => [
      at(ph.inset, ph.setback), at(L - ph.inset, ph.setback), at(L - ph.inset, ph.setback + d), at(ph.inset, ph.setback + d),
    ];
    const ok = (r: XY[]) => r.every((p) => inPoly(p, b.poly) && distToBoundary(p, b.poly) > 1);
    let rect = corners(depth);
    for (let k = 0; k < 12 && !ok(rect); k++) rect = corners((depth *= 0.88));
    if (ok(rect)) {
      const pb = newBuf();
      const y0 = H - ROOF_DROP, y1 = H + ph.height;
      let rcc = 0;
      for (let k = 0; k < 4; k++) { const p = rect[k], q = rect[(k + 1) % 4]; rcc += p[0] * q[1] - q[0] * p[1]; }
      for (let k = 0; k < 4; k++) {
        const p = rect[k], q = rect[(k + 1) % 4], l = len2(p, q);
        const dx = (q[0] - p[0]) / l, dy = (q[1] - p[1]) / l;
        const nn = rcc > 0 ? new THREE.Vector3(dy, 0, dx) : new THREE.Vector3(-dy, 0, -dx);
        quad(pb, [w(p, y0), w(q, y0), w(q, y1), w(p, y1)], [[0, 0], [l, 0], [l, y1 - y0], [0, y1 - y0]], nn);
      }
      cquad(cb, [w(rect[0], y1), w(rect[1], y1), w(rect[2], y1), w(rect[3], y1)], up, '#555b64');
      pent = { walls: toGeom(pb), rect };
    }
  }

  // Tomdagi konditsionerlar
  let s = Math.round(ring[0][0] * 11 + ring[0][1] * 5) | 1;
  const rnd = () => { s = (s * 16807) % 2147483647; if (s <= 0) s += 2147483646; return s / 2147483647; };
  const xs = ring.map((p) => p[0]), ys = ring.map((p) => p[1]);
  const spots: XY[] = [];
  const inRect = (p: XY, r: XY[]) => inPoly(p, [[...r, r[0]]]);
  for (let k = 0; spots.length < look.roofUnits && k < 600; k++) {
    const p: XY = [Math.min(...xs) + rnd() * (Math.max(...xs) - Math.min(...xs)), Math.min(...ys) + rnd() * (Math.max(...ys) - Math.min(...ys))];
    if (!inPoly(p, b.poly) || distToBoundary(p, b.poly) < 1.8) continue;
    if (pent && (inRect(p, pent.rect) || pent.rect.some((c) => len2(c, p) < 1.5))) continue;
    if (spots.some((q) => len2(q, p) < 2.2)) continue;
    spots.push(p);
    const yaw = rnd() < 0.5 ? 0 : Math.PI / 2;
    det.push(cbox(1.0, 0.7, 0.7, yaw, w(p, H - ROOF_DROP + 0.35), '#eceeef'));
  }

  if (cb.pos.length) det.push(cgeom(cb));
  return {
    main: toGeom(mainB), curve: curveB.pos.length ? toGeom(curveB) : null, roof, tower, towerWidth,
    penthouse: pent?.walls ?? null, details: det.length ? mergeAll(det) : null,
  };
}

/** Banya tepasi (pin uchun) */
export const banyaTop = (look: BuildingLook) => look.height + (look.penthouse?.height ?? 0) + 0.5;

// ---------------------------------------------------------------- komponent

const isTap = (e: ThreeEvent<MouseEvent>) => e.delta < 6;
let roofTex: THREE.CanvasTexture | null = null;

export function BanyaBuilding({ b, look, pal, night, selected, onSelect }: {
  b: Building; look: BuildingLook; pal: Palette; night: boolean; selected: boolean; onSelect: (id: string) => void;
}) {
  const parts = useMemo(() => banyaParts(b, look), [b, look]);
  const tex = useMemo(() => ({
    main: mainFacade(look.height),
    curve: curveFacade(look.height),
    tower: parts.towerWidth ? towerTextures(parts.towerWidth) : null,
    pent: look.penthouse ? penthouseTextures(look.penthouse.height + ROOF_DROP) : null,
  }), [look, parts]);
  useEffect(() => () => {
    for (const g of [parts.main, parts.curve, parts.roof, parts.tower, parts.penthouse, parts.details]) g?.dispose();
    for (const t of [tex.main, tex.curve, tex.tower, tex.pent]) if (t) Object.values(t).forEach((x) => x.dispose());
  }, [parts, tex]);
  const roof = (roofTex ??= flatRoofTexture());
  const wallTint = useMemo(() => (selected ? new THREE.Color(pal.selected) : new THREE.Color(1.12, 1.12, 1.12)), [selected, pal]);
  const tint = selected ? pal.selected : night ? '#9da2a8' : '#ffffff';
  const glow = night ? 0.75 : 0;
  return (
    <group onClick={(e) => { if (!isTap(e)) return; e.stopPropagation(); onSelect(b.id); }}>
      <mesh geometry={parts.main} castShadow receiveShadow>
        <meshStandardMaterial map={tex.main.facade} emissiveMap={tex.main.glow} emissive="#ffcf8a" emissiveIntensity={glow}
          color={wallTint} roughness={0.85} side={THREE.DoubleSide} />
      </mesh>
      {parts.curve && (
        <mesh geometry={parts.curve} castShadow receiveShadow>
          <meshStandardMaterial map={tex.curve.facade} emissiveMap={tex.curve.glow} emissive="#ffcf8a" emissiveIntensity={glow}
            color={wallTint} roughness={0.8} side={THREE.DoubleSide} />
        </mesh>
      )}
      {parts.tower && tex.tower && (
        <mesh geometry={parts.tower} castShadow receiveShadow>
          <meshStandardMaterial map={tex.tower.map} emissiveMap={tex.tower.glow} emissive="#ffe2b0" emissiveIntensity={night ? 1 : 0}
            color={selected ? pal.selected : '#ffffff'} roughness={0.9} />
        </mesh>
      )}
      {parts.penthouse && tex.pent && (
        <mesh geometry={parts.penthouse} castShadow receiveShadow>
          <meshStandardMaterial map={tex.pent.map} emissiveMap={tex.pent.glow} emissive="#ffcf8a" emissiveIntensity={glow}
            color={wallTint} roughness={0.6} />
        </mesh>
      )}
      <mesh geometry={parts.roof} receiveShadow>
        <meshStandardMaterial map={roof} color={tint} roughness={0.9} />
      </mesh>
      {parts.details && (
        <mesh geometry={parts.details} castShadow receiveShadow>
          <meshStandardMaterial vertexColors roughness={0.7} side={THREE.DoubleSide} />
        </mesh>
      )}
    </group>
  );
}

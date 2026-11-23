// Katta bino — fotoga qarab: 5 qavatli savdo-ko'ngilochar markaz (~26 m).
// Old fasad (kanalga qaragan): chap burchakda butun bo'yi terrakota rang ustun-pilon, pastki 2 qavat — shisha vitrina,
// o'rtada 2.5 qavat balandlikdagi och plitkali keng tasma (kechasi — LED media-fasad: harakatlanuvchi ko'k-binafsha to'lqinlar),
// eng yuqori qavat — jigarrang ustunli shisha tasma, ustida qalin jigarrang karniz-soyabon. Markazda katta kulrang
// portal (ichkariga torayib boruvchi "voronka"). O'ng burchakdan bitta bo'lak shu uslubda yon tomonga o'tadi, qolgan
// yon tomonlar — har xil kulrang tik panellar. Tom tekis: konditsioner bloklari, chiqish qutilari, quyosh panellari.
// Belgilar (logotiplar) qo'yilmagan: pilon bo'sh — kerak bo'lsa, egasining logotip fayllari bilan qo'shiladi.
import { useEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame, type ThreeEvent } from '@react-three/fiber';
import { CONSTRUCTION, type BuildingLook } from './config';
import { ConstructionSite } from './constructionSite';
import { distToBoundary, inPoly } from './geo';
import { canvasTexture, mergeAll, prefersReducedMotion, useAmbientFrames } from './modelKit';
import type { XY } from './projection';
import { newBuf, quad, ringOf, toGeom, w, type Buf } from './styledBuilding';
import type { Palette } from './theme';
import type { Building, Poly } from './types';
import { Html } from '@react-three/drei';

// Balandliklar (m), fotodagi nisbatlardan: jami ~25.8 m
const H_GLASS = 8.6; // pastki vitrina (2 qavat + antresol)
const H_BAND = 19.3; // och tasma tepasi
const H_WALL = 23.3; // yuqori qavat shishasi tepasi = karniz osti
const H_TOP = 25.8; // karniz tepasi
const WRAP = 12; // old fasad uslubi yon tomonga shuncha metr o'tadi
const PYLON = { width: 8.8, out: 2.0 }; // karnizdan (1.6 m) oldinroq — fotodagidek pilon karnizni kesib o'tadi
const PORTAL = { at: 0.57, width: 17.5, inner: 9.3, height: 14, innerH: H_GLASS, depth: 2.6 };
const BROWN = '#6e4a3c', BROWN_DARK = '#4a3128', PARAPET = '#b8bbbf';

// ---------------------------------------------------------------- teksturalar

type Rect = [number, number, number, number]; // x, y, w, h (px)

function noise(g: CanvasRenderingContext2D, W: number, H: number, n: number, rgb: string, a = 0.15) {
  let s = 7;
  const r = () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
  for (let i = 0; i < n; i++) {
    g.fillStyle = `rgba(${rgb},${a * r()})`;
    g.fillRect(r() * W, r() * H, 2, 1);
  }
}

/** Fasad chizgichi: u (m, chapdan) va h (m, pastdan) → piksel */
function painter(Lm: number, Hm: number, ppm: number) {
  const Wpx = Math.max(64, Math.round(Lm * ppm)), Hpx = Math.round(Hm * ppm);
  const X = (u: number) => Math.round(u * ppm), Y = (h: number) => Math.round((Hm - h) * ppm);
  return { Wpx, Hpx, X, Y, ppm };
}
type Pn = ReturnType<typeof painter>;

/** Shisha vitrina: to'q ko'k-kulrang shisha, ingichka ramalar, qavat orasida to'q tasma; kechasi ichi iliq yonadi */
function curtain(g: CanvasRenderingContext2D, P: Pn, u0: number, u1: number, h0: number, h1: number, lit: Rect[], mull = 1.55, bars?: Rect[]) {
  const { X, Y } = P;
  const gr = g.createLinearGradient(0, Y(h1), 0, Y(h0));
  gr.addColorStop(0, '#3a4a5a'); gr.addColorStop(0.55, '#55687a'); gr.addColorStop(1, '#2b3846');
  g.fillStyle = gr;
  g.fillRect(X(u0), Y(h1), X(u1) - X(u0), Y(h0) - Y(h1));
  // osmon/daraxt aksi — qiya och tasmalar
  g.fillStyle = 'rgba(210,225,240,0.10)';
  for (let u = u0; u < u1; u += 7.3) {
    g.beginPath();
    g.moveTo(X(u), Y(h0)); g.lineTo(X(u + 2.5), Y(h1)); g.lineTo(X(u + 4.2), Y(h1)); g.lineTo(X(u + 1.7), Y(h0));
    g.fill();
  }
  lit.push([X(u0), Y(h1), X(u1) - X(u0), Y(h0) - Y(h1)]);
  g.fillStyle = '#1d242c';
  const n = Math.max(1, Math.round((u1 - u0) / mull));
  for (let k = 0; k <= n; k++) {
    const x = X(u0 + ((u1 - u0) * k) / n) - 1;
    g.fillRect(x, Y(h1), 2, Y(h0) - Y(h1));
    bars?.push([x, Y(h1), 2, Y(h0) - Y(h1)]);
  }
  g.fillRect(X(u0), Y(h1), X(u1) - X(u0), 2);
}

/** Vitrina (pastki 2 qavat): uch qator shisha, orasida plita tasmalari */
function storefront(g: CanvasRenderingContext2D, P: Pn, u0: number, u1: number, lit: Rect[], bars: Rect[]) {
  const { X, Y } = P;
  curtain(g, P, u0, u1, 0.3, 3.0, lit, 1.55, bars);
  curtain(g, P, u0, u1, 3.35, 5.7, lit, 1.55, bars);
  curtain(g, P, u0, u1, 6.05, H_GLASS, lit, 1.55, bars);
  g.fillStyle = '#20262d';
  for (const [a, b] of [[3.0, 3.35], [5.7, 6.05], [0, 0.3]]) {
    g.fillRect(X(u0), Y(b), X(u1) - X(u0), Y(a) - Y(b));
    bars.push([X(u0), Y(b), X(u1) - X(u0), Y(a) - Y(b)]);
  }
}

/** Och tasma: oq-krem plitalar (1.2 × 0.6 m), choklar ingichka */
function bandPanels(g: CanvasRenderingContext2D, P: Pn, u0: number, u1: number) {
  const { X, Y, ppm } = P;
  g.fillStyle = '#e9e6df';
  g.fillRect(X(u0), Y(H_BAND), X(u1) - X(u0), Y(H_GLASS) - Y(H_BAND));
  let s = 3;
  const r = () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
  for (let h = H_GLASS; h < H_BAND; h += 0.6) {
    for (let u = u0; u < u1; u += 1.2) {
      const t = 0.96 + r() * 0.05;
      g.fillStyle = `rgb(${Math.round(233 * t)},${Math.round(230 * t)},${Math.round(223 * t)})`;
      g.fillRect(X(u) + 1, Y(Math.min(h + 0.6, H_BAND)) + 1, Math.max(1, X(Math.min(u + 1.2, u1)) - X(u) - 1), Math.max(1, Math.round(0.6 * ppm) - 1));
    }
  }
  g.fillStyle = '#c9c4ba';
  g.fillRect(X(u0), Y(H_GLASS) - 2, X(u1) - X(u0), 3);
}

/** Yuqori qavat: shisha, har ~6 m da jigarrang ustun */
function topFloor(g: CanvasRenderingContext2D, P: Pn, u0: number, u1: number, lit: Rect[], bars: Rect[], terraceEnd = false) {
  const { X, Y } = P;
  const end = terraceEnd ? u1 - 4.2 : u1;
  curtain(g, P, u0, end, H_BAND + 0.15, H_WALL - 0.2, lit, 2.1, bars);
  if (terraceEnd) {
    // Burchakdagi ochiq terrasa: soya, gullar, shisha to'siq
    g.fillStyle = '#2a2622'; g.fillRect(X(end), Y(H_WALL), X(u1) - X(end), Y(H_BAND) - Y(H_WALL));
    g.fillStyle = '#3f6b36';
    for (let u = end + 0.4; u < u1 - 0.4; u += 1.1) { g.beginPath(); g.arc(X(u), Y(H_BAND + 1.0), 0.5 * P.ppm, 0, Math.PI * 2); g.fill(); }
    g.fillStyle = 'rgba(200,220,230,0.35)'; g.fillRect(X(end), Y(H_BAND + 1.1), X(u1) - X(end), Y(H_BAND) - Y(H_BAND + 1.1));
    lit.push([X(end), Y(H_WALL - 0.4), X(u1) - X(end), Y(H_BAND + 1.2) - Y(H_WALL - 0.4)]);
  }
  g.fillStyle = BROWN;
  const n = Math.max(1, Math.round((u1 - u0) / 6.2));
  for (let k = 0; k <= n; k++) {
    const u = u0 + ((u1 - u0) * k) / n;
    const x = X(u) - Math.round(0.3 * P.ppm);
    g.fillRect(x, Y(H_WALL), Math.round(0.6 * P.ppm), Y(H_BAND) - Y(H_WALL));
    bars.push([x, Y(H_WALL), Math.round(0.6 * P.ppm), Y(H_BAND) - Y(H_WALL)]);
  }
  g.fillStyle = '#d8d4cc'; g.fillRect(X(u0), Y(H_BAND + 0.15), X(u1) - X(u0), Y(H_BAND) - Y(H_BAND + 0.15));
}

/** Kulrang tik panellar (yon tomonlar): har xil kenglik va tusdagi bo'laklar, ba'zi joyda tor tik deraza */
function grayStripes(g: CanvasRenderingContext2D, P: Pn, u0: number, u1: number, h1: number, lit: Rect[], seed: number) {
  const { X, Y, ppm } = P;
  let s = seed;
  const r = () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
  const tones = ['#6c7076', '#7d8187', '#5b5f65', '#8e9298', '#666a70', '#a3a6aa'];
  for (let u = u0; u < u1;) {
    const wdt = Math.min(1.2 + Math.floor(r() * 3) * 1.2, u1 - u);
    g.fillStyle = tones[Math.floor(r() * tones.length)];
    g.fillRect(X(u), Y(h1), X(u + wdt) - X(u) + 1, Y(0) - Y(h1));
    if (r() < 0.22 && wdt >= 1.2) { // tor tik deraza
      const x0 = u + wdt / 2 - 0.35;
      g.fillStyle = '#34404c'; g.fillRect(X(x0), Y(h1 - 2.5), Math.round(0.7 * ppm), Y(2.5) - Y(h1 - 2.5));
      lit.push([X(x0), Y(h1 - 2.5), Math.round(0.7 * ppm), Y(2.5) - Y(h1 - 2.5)]);
    }
    u += wdt;
  }
  g.fillStyle = 'rgba(30,32,36,0.35)';
  for (let h = 1.2; h < h1; h += 1.2) g.fillRect(X(u0), Y(h), X(u1) - X(u0), 1);
  g.fillStyle = '#4c5056'; g.fillRect(X(u0), Y(0.4), X(u1) - X(u0), Y(0) - Y(0.4));
}

/** Kechasi: derazalar iliq yonadi, romlar qora; kulrang devorlar pastidan yoritgich nuri */
function glowCanvas(P: Pn, lit: Rect[], bars: Rect[], uplights: number[] = [], seed = 5) {
  return canvasTexture(P.Wpx, P.Hpx, (g) => {
    g.fillStyle = '#000'; g.fillRect(0, 0, P.Wpx, P.Hpx);
    let s = seed;
    const r = () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
    for (const [x, y, ww, hh] of lit) {
      // ichki yorug'lik notekis: bo'laklarga bo'lib, har biri o'z yorqinligida; tepasi (shift chiroqlari) yorqinroq
      const step = Math.max(8, Math.round(2.4 * P.ppm));
      for (let xx = x; xx < x + ww; xx += step) {
        const v = 0.35 + r() * 0.6, sw = Math.min(step, x + ww - xx);
        const gr = g.createLinearGradient(0, y, 0, y + hh);
        gr.addColorStop(0, `rgb(${Math.round(255 * v)},${Math.round(214 * v)},${Math.round(160 * v)})`);
        gr.addColorStop(1, `rgb(${Math.round(150 * v)},${Math.round(110 * v)},${Math.round(70 * v)})`);
        g.fillStyle = gr;
        g.fillRect(xx, y, sw, hh);
        // ichkaridagi odamlar va jihozlar — pastki qismida to'q siluetlar
        g.fillStyle = 'rgba(0,0,0,0.55)';
        for (let k = 0; k < 3; k++) if (r() < 0.5) g.fillRect(xx + r() * sw, y + hh * (0.55 + r() * 0.15), Math.max(2, P.ppm * (0.3 + r() * 0.6)), hh * 0.45);
      }
    }
    g.fillStyle = '#000';
    for (const [x, y, ww, hh] of bars) g.fillRect(x, y, ww, hh);
    for (const u of uplights) {
      const x = P.X(u), gr = g.createLinearGradient(0, P.Y(0), 0, P.Y(9));
      gr.addColorStop(0, 'rgba(255,214,160,0.55)'); gr.addColorStop(1, 'rgba(255,214,160,0)');
      g.fillStyle = gr;
      g.beginPath(); g.moveTo(x - 0.3 * P.ppm, P.Y(0)); g.lineTo(x - 1.4 * P.ppm, P.Y(9)); g.lineTo(x + 1.4 * P.ppm, P.Y(9)); g.lineTo(x + 0.3 * P.ppm, P.Y(0)); g.fill();
    }
  });
}

function asTex(t: THREE.CanvasTexture, Lm: number, Hm: number, repeatU = false) {
  t.wrapS = repeatU ? THREE.RepeatWrapping : THREE.ClampToEdgeWrapping;
  t.wrapT = THREE.ClampToEdgeWrapping;
  t.repeat.set(1 / Lm, 1 / Hm);
  return t;
}

/** Old fasad (bitta butun tekstura): pilon joyi, vitrina, och tasma, yuqori qavat (o'ng burchakda terrasa) */
function frontTextures(L: number) {
  const P = painter(L, H_WALL, 22);
  const lit: Rect[] = [], bars: Rect[] = [];
  const u0 = PYLON.width;
  const map = canvasTexture(P.Wpx, P.Hpx, (g) => {
    g.fillStyle = BROWN; g.fillRect(0, 0, P.Wpx, P.Hpx);
    storefront(g, P, u0, L, lit, bars);
    bandPanels(g, P, u0, L);
    topFloor(g, P, u0, L, lit, bars, true);
  });
  return { map: asTex(map, L, H_WALL), glow: asTex(glowCanvas(P, lit, bars), L, H_WALL) };
}

/** Yon tomon (o'ng): avval WRAP m old fasad uslubida, keyin kulrang panellar */
function sideTextures(L: number) {
  const P = painter(L, H_WALL, 16);
  const lit: Rect[] = [], bars: Rect[] = [];
  const wrap = Math.min(WRAP, L * 0.4);
  const ups: number[] = [];
  for (let u = wrap + 4; u < L - 2; u += 7) ups.push(u);
  const map = canvasTexture(P.Wpx, P.Hpx, (g) => {
    storefront(g, P, 0, wrap, lit, bars);
    bandPanels(g, P, 0, wrap);
    topFloor(g, P, 0, wrap, lit, bars);
    grayStripes(g, P, wrap, L, H_WALL, lit, 11);
    g.fillStyle = BROWN; g.fillRect(P.X(wrap) - 6, 0, 12, P.Hpx); // ikki uslub orasida jigarrang tik chiziq
  });
  return { map: asTex(map, L, H_WALL), glow: asTex(glowCanvas(P, lit, bars, ups, 9), L, H_WALL), wrap };
}

/** Qolgan kulrang devorlar: 24 m da takrorlanadi */
function grayTextures() {
  const T = 24, P = painter(T, H_WALL, 12);
  const lit: Rect[] = [];
  const map = canvasTexture(P.Wpx, P.Hpx, (g) => grayStripes(g, P, 0, T, H_WALL, lit, 21));
  return { map: asTex(map, T, H_WALL, true), glow: asTex(glowCanvas(P, lit, [], [5, 17], 13), T, H_WALL, true) };
}

/** Basseynlar tomoni: yuqori qavat shisha tasmasi davom etadi, pastda to'q panellar va keng tik oynalar; 16 m da takrorlanadi */
function poolSideTextures() {
  const T = 16, P = painter(T, H_WALL, 12);
  const lit: Rect[] = [], bars: Rect[] = [];
  const map = canvasTexture(P.Wpx, P.Hpx, (g) => {
    grayStripes(g, P, 0, T, H_BAND, lit, 31);
    topFloor(g, P, 0, T, lit, bars);
    curtain(g, P, 6, 9.6, 0.3, H_BAND - 0.8, lit, 1.2); // keng tik oyna (zinapoya)
  });
  return { map: asTex(map, T, H_WALL, true), glow: asTex(glowCanvas(P, lit, bars, [], 17), T, H_WALL, true) };
}

/** Pilon: terrakota panellar (1.2 × 2.4 m), choklari to'q */
function pylonTexture() {
  const P = painter(PYLON.width + PYLON.out * 2, H_TOP, 16);
  const map = canvasTexture(P.Wpx, P.Hpx, (g) => {
    g.fillStyle = BROWN; g.fillRect(0, 0, P.Wpx, P.Hpx);
    let s = 5;
    const r = () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
    for (let h = 0; h < H_TOP; h += 2.4) for (let u = 0; u < P.Wpx / P.ppm; u += 1.2) {
      const t = 0.92 + r() * 0.12;
      g.fillStyle = `rgb(${Math.round(118 * t)},${Math.round(80 * t)},${Math.round(64 * t)})`;
      g.fillRect(P.X(u) + 1, P.Y(h + 2.4) + 1, P.X(1.2) - 2, P.Y(0) - P.Y(2.4) - 2);
    }
    noise(g, P.Wpx, P.Hpx, 1500, '40,25,20', 0.12);
  });
  // Kechasi: pastdan yoritgich nuri
  const glow = canvasTexture(P.Wpx, P.Hpx, (g) => {
    g.fillStyle = '#000'; g.fillRect(0, 0, P.Wpx, P.Hpx);
    const gr = g.createLinearGradient(0, P.Y(0), 0, P.Y(14));
    gr.addColorStop(0, 'rgba(255,205,150,0.6)'); gr.addColorStop(1, 'rgba(255,205,150,0)');
    g.fillStyle = gr; g.fillRect(0, P.Y(14), P.Wpx, P.Y(0) - P.Y(14));
  });
  const L = PYLON.width + PYLON.out * 2;
  return { map: asTex(map, L, H_TOP, true), glow: asTex(glow, L, H_TOP, true) };
}

/** Portal: to'q kulrang tosh plitalar, gorizontal choklar */
function portalTexture() {
  const tex = canvasTexture(128, 128, (g, W, H) => {
    g.fillStyle = '#6a6e73'; g.fillRect(0, 0, W, H);
    for (let y = 0; y < H; y += 8) {
      for (let x = (y / 8) % 2 ? -16 : 0; x < W; x += 32) {
        const t = 0.9 + (((x * 7 + y * 3) % 11) / 11) * 0.18;
        g.fillStyle = `rgb(${Math.round(104 * t)},${Math.round(108 * t)},${Math.round(113 * t)})`;
        g.fillRect(x + 1, y + 1, 30, 6);
      }
    }
  });
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(1 / 4, 1 / 4);
  return tex;
}

function roofTexture() {
  const tex = canvasTexture(128, 128, (g, W, H) => {
    g.fillStyle = '#b7b9bb'; g.fillRect(0, 0, W, H);
    noise(g, W, H, 1200, '90,92,96', 0.22);
    g.fillStyle = 'rgba(120,122,126,0.5)';
    for (let k = 0; k < 4; k++) { g.fillRect(k * 32, 0, 1, H); g.fillRect(0, k * 32, W, 1); }
  });
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(1 / 8, 1 / 8);
  return tex;
}

// ---------------------------------------------------------------- geometriya

const len2 = (a: XY, b: XY) => Math.hypot(b[0] - a[0], b[1] - a[1]);
const dirOf = (a: XY, b: XY) => Math.atan2(b[1] - a[1], b[0] - a[0]);
const angDiff = (a: number, b: number) => Math.atan2(Math.sin(b - a), Math.cos(b - a));

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

type Kind = 'front' | 'side' | 'gray' | 'pool';

/** Lokal ramka: a nuqtadan, u — qirra bo'ylab, n — tashqariga */
function frameAt(a: XY, dir: number, out: XY) {
  const u: XY = [Math.cos(dir), Math.sin(dir)];
  return (s: number, t: number, h: number) => w([a[0] + u[0] * s + out[0] * t, a[1] + u[1] * s + out[1] * t], h);
}

function mallParts(b: Building, look: BuildingLook) {
  const ring = ringOf(b);
  const n = ring.length;
  let area = 0;
  for (let i = 0; i < n; i++) { const p = ring[i], q = ring[(i + 1) % n]; area += p[0] * q[1] - q[0] * p[1]; }
  const ccw = area > 0;
  const outN = (i: number): XY => {
    const p = ring[i], q = ring[(i + 1) % n], l = len2(p, q) || 1;
    const dx = (q[0] - p[0]) / l, dy = (q[1] - p[1]) / l;
    return ccw ? [dy, -dx] : [-dy, dx];
  };
  const D = (i: number) => dirOf(ring[i], ring[(i + 1) % n]);
  const Ln = (i: number) => len2(ring[i], ring[(i + 1) % n]);

  // Qirralar qatorlari (yo'nalish 12° dan kam o'zgarsa — bitta fasad)
  const f0 = look.frontEdge ?? 0;
  const order = Array.from({ length: n }, (_, k) => (f0 + k) % n);
  const runs: number[][] = [];
  for (const i of order) {
    const last = runs[runs.length - 1];
    if (last && Math.abs(angDiff(D(last[last.length - 1]), D(i))) < THREE.MathUtils.degToRad(12)) last.push(i);
    else runs.push([i]);
  }
  // Oxirgi qator old qatorning davomi bo'lsa (aylanib kelgan) — birlashtiramiz
  if (runs.length > 1 && Math.abs(angDiff(D(runs[runs.length - 1][runs[runs.length - 1].length - 1]), D(runs[0][0]))) < THREE.MathUtils.degToRad(12)) {
    runs[0] = [...runs.pop()!, ...runs[0]];
  }
  const kindOf = (ri: number): Kind => (ri === 0 ? 'front' : ri === 1 ? 'side' : ri === runs.length - 1 ? 'pool' : 'gray');

  // Devorlar: har tur alohida bufer, u — fasad qatori bo'ylab metr
  const bufs: Record<Kind, Buf> = { front: newBuf(), side: newBuf(), gray: newBuf(), pool: newBuf() };
  const runLen: Record<Kind, number> = { front: 0, side: 0, gray: 0, pool: 0 };
  let ug = 0;
  runs.forEach((run, ri) => {
    const kind = kindOf(ri);
    let u = kind === 'gray' || kind === 'pool' ? ug : 0;
    for (const i of run) {
      const p = ring[i], q = ring[(i + 1) % n], L = Ln(i);
      if (L < 0.05) continue;
      const nn = new THREE.Vector3(outN(i)[0], 0, -outN(i)[1]);
      quad(bufs[kind], [w(p, 0), w(q, 0), w(q, H_WALL), w(p, H_WALL)], [[u, 0], [u + L, 0], [u + L, H_WALL], [u, H_WALL]], nn);
      u += L;
    }
    if (kind === 'gray' || kind === 'pool') ug = u; else runLen[kind] = u;
  });

  const cb: CBuf = { pos: [], nor: [], col: [] };
  const det: THREE.BufferGeometry[] = [];
  const up = new THREE.Vector3(0, 1, 0), down = new THREE.Vector3(0, -1, 0);

  // Karniz: old/basseyn tomonida va yon tomonning old qismida qalin jigarrang soyabon (1.6 m chiqib turadi),
  // qolgan joyda ingichka och parapet. Har qirra o'z masofasiga suriladi, burchaklarda to'g'ri chiziqlar kesishadi
  const sideRun = runs[1] ?? [];
  const brownEdge = new Set<number>([...runs[0], ...(runs[runs.length - 1] ?? []), ...(sideRun.length ? [sideRun[0]] : [])]);
  const offs = ring.map((_, i) => (brownEdge.has(i) ? 1.6 : 0.3));
  const offRing: XY[] = ring.map((_, k) => {
    const i0 = (k - 1 + n) % n, i1 = k;
    const n0 = outN(i0), n1 = outN(i1);
    const a0: XY = [ring[i0][0] + n0[0] * offs[i0], ring[i0][1] + n0[1] * offs[i0]];
    const a1: XY = [ring[i1][0] + n1[0] * offs[i1], ring[i1][1] + n1[1] * offs[i1]];
    const d0: XY = [Math.cos(D(i0)), Math.sin(D(i0))], d1: XY = [Math.cos(D(i1)), Math.sin(D(i1))];
    const den = d0[0] * d1[1] - d0[1] * d1[0];
    if (Math.abs(den) < 1e-3) return [ring[k][0] + n1[0] * offs[i1], ring[k][1] + n1[1] * offs[i1]];
    const t = ((a1[0] - a0[0]) * d1[1] - (a1[1] - a0[1]) * d1[0]) / den;
    return [a0[0] + d0[0] * t, a0[1] + d0[1] * t];
  });
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    const nn = new THREE.Vector3(outN(i)[0], 0, -outN(i)[1]);
    const col = brownEdge.has(i) ? BROWN : PARAPET;
    cquad(cb, [w(offRing[i], H_WALL), w(offRing[j], H_WALL), w(offRing[j], H_TOP), w(offRing[i], H_TOP)], nn, col);
    // ostki tomoni (soffit) — pastdan qaraganda ko'rinadi
    cquad(cb, [w(ring[i], H_WALL), w(ring[j], H_WALL), w(offRing[j], H_WALL), w(offRing[i], H_WALL)], down, brownEdge.has(i) ? BROWN_DARK : '#8f9296');
    // parapet ichki tomoni va tepasi
    const inner = (k: number): XY => {
      const c: XY = [ring[k][0], ring[k][1]];
      return c;
    };
    cquad(cb, [w(offRing[i], H_TOP), w(offRing[j], H_TOP), w(inner(j), H_TOP), w(inner(i), H_TOP)], up, brownEdge.has(i) ? '#5c3d31' : '#a7aaae');
    cquad(cb, [w(inner(i), H_TOP - 0.5), w(inner(j), H_TOP - 0.5), w(inner(j), H_TOP), w(inner(i), H_TOP)], nn.clone().negate(), '#9a9ca0');
  }
  // Tom (parapetdan 0.5 m pastda)
  const roofShape = new THREE.Shape(ring.map(([x, y]) => new THREE.Vector2(x, y)));
  const roof = new THREE.ShapeGeometry(roofShape, 1);
  roof.rotateX(-Math.PI / 2);
  roof.translate(0, H_TOP - 0.5, 0);

  // Pilon: old fasadning boshida (chap burchak), butun bo'yi, oldinga chiqib turadi
  const front = runs[0];
  const fa = ring[front[0]], fDir = D(front[0]), fOut = outN(front[0]);
  const F = frameAt(fa, fDir, fOut);
  const pylonB = newBuf();
  {
    const s0 = -PYLON.out * 0.6, s1 = PYLON.width, t0 = -0.3, t1 = PYLON.out, h = H_TOP + 0.4;
    const nU = new THREE.Vector3(Math.cos(fDir), 0, -Math.sin(fDir)), nO = new THREE.Vector3(fOut[0], 0, -fOut[1]);
    const Wd = PYLON.width + PYLON.out * 2;
    quad(pylonB, [F(s0, t1, 0), F(s1, t1, 0), F(s1, t1, h), F(s0, t1, h)], [[0, 0], [s1 - s0, 0], [s1 - s0, h], [0, h]], nO); // old yuzi
    quad(pylonB, [F(s1, t0, 0), F(s1, t1, 0), F(s1, t1, h), F(s1, t0, h)], [[Wd - (t1 - t0), 0], [Wd, 0], [Wd, h], [Wd - (t1 - t0), h]], nU); // o'ng yon
    quad(pylonB, [F(s0, t1, 0), F(s0, t0 - 6, 0), F(s0, t0 - 6, h), F(s0, t1, h)], [[0, 0], [t1 - t0 + 6, 0], [t1 - t0 + 6, h], [0, h]], nU.clone().negate()); // chap yon (burchakni o'raydi)
    cquad(cb, [F(s0, t1, h), F(s1, t1, h), F(s1, t0 - 6, h), F(s0, t0 - 6, h)], up, BROWN_DARK);
  }

  // Portal: ikki oyoq (ichki cheti tik, tepasi qiya), qiya "voronka" peshtoq va tepa plita
  const portalB = newBuf();
  {
    const Lf = runLen.front, c = Lf * PORTAL.at, hw = PORTAL.width / 2, iw = PORTAL.inner / 2, d = PORTAL.depth;
    const H = PORTAL.height, ih = PORTAL.innerH;
    const nO = new THREE.Vector3(fOut[0], 0, -fOut[1]);
    const nU = new THREE.Vector3(Math.cos(fDir), 0, -Math.sin(fDir));
    const uvq = (a: number[], b2: number[], c2: number[], dd: number[]) => [a, b2, c2, dd];
    for (const sg of [-1, 1]) {
      const so = c + sg * hw, si = c + sg * iw;
      // old yuzi: (so,0) (si,0) (si,ih) (so,H)
      const fv = [F(so, d, 0), F(si, d, 0), F(si, d, ih), F(so, d, H)];
      quad(portalB, fv, uvq([so, 0], [si, 0], [si, ih], [so, H]), nO);
      // tashqi yon
      quad(portalB, [F(so, 0, 0), F(so, d, 0), F(so, d, H), F(so, 0, H)], [[0, 0], [d, 0], [d, H], [0, H]], nU.clone().multiplyScalar(sg));
      // ichki yon (tik)
      quad(portalB, [F(si, d, 0), F(si, 0, 0), F(si, 0, ih), F(si, d, ih)], [[0, 0], [d, 0], [d, ih], [0, ih]], nU.clone().multiplyScalar(-sg));
    }
    // Qiya peshtoq: old tepasi (to'liq eni, H) dan devordagi ichki ochiq joy tepasi (ih) gacha
    const lin = [F(c - hw, d, H), F(c + hw, d, H), F(c + iw, 0, ih), F(c - iw, 0, ih)];
    const ln = new THREE.Vector3().crossVectors(lin[1].clone().sub(lin[0]), lin[3].clone().sub(lin[0])).normalize();
    const lnDown = ln.y < 0 ? ln : ln.clone().negate();
    quad(portalB, lin, [[c - hw, 0], [c + hw, 0], [c + iw, 5.5], [c - iw, 5.5]], lnDown);
    // Oyoqlarning qiya tepasi bilan peshtoq orasidagi uchburchaklar (yon tomondan yopiq ko'rinsin)
    for (const sg of [-1, 1]) {
      const so = c + sg * hw, si = c + sg * iw;
      quad(portalB, [F(si, d, ih), F(si, 0, ih), F(si, 0, ih), F(so, d, H)], [[0, 0], [d, 0], [d, 0], [0, 4]], nU.clone().multiplyScalar(-sg));
    }
    // Tepa plita
    const top = [F(c - hw, 0, H), F(c + hw, 0, H), F(c + hw, d, H), F(c - hw, d, H)];
    cquad(cb, top, up, '#5d6166');
    cquad(cb, [F(c - hw, d, H - 0.01), F(c + hw, d, H - 0.01), F(c + hw, d, H + 0.25), F(c - hw, d, H + 0.25)], nO, '#55595e');
    cquad(cb, [F(c - hw, 0, H + 0.25), F(c + hw, 0, H + 0.25), F(c + hw, d, H + 0.25), F(c - hw, d, H + 0.25)], up, '#5d6166');
  }

  // Tom: chiqish qutilari, konditsioner guruhlari (old yarmida), quyosh panellari qatorlari (orqa yarmida)
  let s = 97;
  const rnd = () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
  const yRoof = H_TOP - 0.5;
  const inv = (p: XY) => { // tom nuqtasi → (u bo'ylab, ichkariga chuqurlik)
    const dx = p[0] - fa[0], dy = p[1] - fa[1];
    return [dx * Math.cos(fDir) + dy * Math.sin(fDir), -(dx * fOut[0] + dy * fOut[1])];
  };
  const at = (u: number, v: number): XY => [fa[0] + Math.cos(fDir) * u - fOut[0] * v, fa[1] + Math.sin(fDir) * u - fOut[1] * v];
  const okRoof = (p: XY, m: number) => inPoly(p, b.poly) && distToBoundary(p, b.poly) > m;
  const yaw = fDir; // rotateY(θ): lokal +X → ma'lumotda (cos θ, sin θ) — fasad bo'ylab
  const placed: { p: XY; r: number }[] = [];
  const free = (p: XY, r: number) => okRoof(p, r + 1.2) && placed.every((q) => len2(q.p, p) > q.r + r + 0.8);
  // chiqish/lift qutilari
  for (const [u, v, sx, sz] of [[14, 10, 7, 4.5], [34, 14, 5, 5], [24, 34, 6, 4], [46, 30, 4.5, 4.5]] as const) {
    const p = at(u, v);
    if (!free(p, Math.hypot(sx, sz) / 2)) continue;
    placed.push({ p, r: Math.hypot(sx, sz) / 2 });
    det.push(cbox(sx, 3.0, sz, yaw, w(p, yRoof + 1.5), '#c9cbcd'));
    det.push(cbox(sx + 0.3, 0.2, sz + 0.3, yaw, w(p, yRoof + 3.05), '#9fa2a6'));
  }
  // konditsioner bloklari: 3–6 tadan qator
  for (let k = 0; k < look.roofUnits; k++) {
    const u = 6 + rnd() * (runLen.front - 12), v = 5 + rnd() * 26;
    const p = at(u, v), cnt = 3 + Math.floor(rnd() * 4), r = cnt * 1.25;
    if (!free(p, r)) continue;
    placed.push({ p, r });
    for (let m = 0; m < cnt; m++) {
      const q = at(u + (m - (cnt - 1) / 2) * 2.3, v);
      det.push(cbox(2.0, 1.8, 2.6, yaw, w(q, yRoof + 0.9), '#e7e8ea'));
      det.push(cbox(1.3, 0.08, 1.3, yaw, w(q, yRoof + 1.83), '#3a3d42')); // fan panjarasi
    }
  }
  // quyosh panellari: fotodagidek katta bloklar — 2 qator yonma-yon (3.4 m), bloklar orasida 1.3 m o'tish joyi
  const sol: CBuf = { pos: [], nor: [], col: [] };
  const vs = ring.map(inv);
  const vMax = Math.max(...vs.map((x) => x[1]));
  const tilt = THREE.MathUtils.degToRad(10);
  const PW = 1.05, PD = 1.7;
  for (let v = 36; v < vMax - 3; v += 2 * PD + 1.3) {
    for (let u = 3; u < 120; u += PW) {
      if (Math.floor(u / 13) % 4 === 3) continue; // har 4-blokdan keyin keng o'tish joyi
      for (const dv of [0, PD]) {
        const vv = v + dv;
        const c0 = at(u, vv), c1 = at(u + PW, vv + PD);
        if (!okRoof(c0, 2.5) || !okRoof(c1, 2.5) || placed.some((q) => len2(q.p, c0) < q.r + 1.5 || len2(q.p, c1) < q.r + 1.5)) continue;
        const lo = yRoof + 0.3, hi = lo + PD * Math.sin(tilt);
        const v0 = w(at(u + 0.03, vv + PD), lo), v1 = w(at(u + PW - 0.03, vv + PD), lo), v2 = w(at(u + PW - 0.03, vv + 0.04), hi), v3 = w(at(u + 0.03, vv + 0.04), hi);
        const nrm = new THREE.Vector3().crossVectors(v1.clone().sub(v0), v3.clone().sub(v0)).normalize();
        cquad(sol, [v0, v1, v2, v3], nrm.y < 0 ? nrm.negate() : nrm, (Math.floor(u / PW) + (dv ? 1 : 0)) % 2 ? '#2a3d5c' : '#304667');
      }
    }
  }
  if (sol.pos.length) det.push(cgeom(sol));
  det.push(cgeom(cb));

  return {
    walls: { front: toGeom(bufs.front), side: toGeom(bufs.side), gray: toGeom(bufs.gray), pool: toGeom(bufs.pool) },
    runLen, roof, pylon: toGeom(pylonB), portal: toGeom(portalB), details: mergeAll(det),
  };
}

/** Bino tepasi (pin uchun): karniz + tomdagi qutilar */
export const mallTop = (look: BuildingLook, withYearSign = false) =>
  withYearSign ? look.height + YEAR_SIGN_TOP : look.height + 3.6;
/** Ochilish yili belgisining tepasi tomdan qancha balandda (pin undan yuqorida tursin) */
const YEAR_SIGN_TOP = 2.5 + 28 * 400 / 1024 + 2;

// ---------------------------------------------------------------- LED media-fasad (kechasi)

const LED_VERT = /* glsl */ `
varying vec2 vMallUv;
`;
const LED_FRAG = /* glsl */ `
varying vec2 vMallUv;
uniform float uTime;
uniform float uLed;
uniform vec2 uBandU;
float ledHash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
vec3 ledWaves(vec2 q) {
  // q: (u, h) metrda. Uch to'lqin tasmasi: ko'k → binafsha, sekin oqadi; atrofida uchqunlar
  vec3 acc = vec3(0.0);
  float mid = ${((H_GLASS + H_BAND) / 2).toFixed(2)};
  for (int i = 0; i < 3; i++) {
    float fi = float(i);
    float yc = mid + 2.6 * sin(q.x * 0.11 + uTime * 0.35 + fi * 1.7) + 1.1 * sin(q.x * 0.27 - uTime * 0.5 + fi * 2.3);
    float th = 0.32 + 0.22 * sin(q.x * 0.05 + fi * 1.3 + uTime * 0.2);
    float d = (q.y - yc) / th;
    float core = exp(-d * d);
    float halo = exp(-d * d * 0.08) * 0.25;
    vec3 c = mix(vec3(0.25, 0.75, 1.0), vec3(0.78, 0.38, 1.0), 0.5 + 0.5 * sin(q.x * 0.06 + fi * 1.3 + uTime * 0.25));
    acc += c * (core * (0.65 + 0.35 * sin(q.x * 0.6 + uTime * 1.2 + fi)) + halo);
    // uchqunlar
    vec2 cell = floor(vec2(q.x * 3.0, q.y * 3.0));
    float sp = step(0.985, ledHash(cell + fi * 17.0)) * exp(-abs(q.y - yc) * 0.9);
    acc += vec3(0.85, 0.9, 1.0) * sp * (0.5 + 0.5 * sin(uTime * 4.0 + ledHash(cell) * 6.28));
  }
  return acc;
}
`;

function withLed(mat: THREE.MeshStandardMaterial, u: { uTime: THREE.IUniform<number>; uLed: THREE.IUniform<number>; uBandU: THREE.IUniform<THREE.Vector2> }) {
  mat.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, u);
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', `#include <common>\n${LED_VERT}`)
      .replace('#include <uv_vertex>', '#include <uv_vertex>\n  vMallUv = uv;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', `#include <common>\n${LED_FRAG}`)
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
  if (uLed > 0.001 && vMallUv.y > ${(H_GLASS + 0.15).toFixed(2)} && vMallUv.y < ${(H_BAND - 0.1).toFixed(2)} && vMallUv.x > uBandU.x && vMallUv.x < uBandU.y) {
    diffuseColor.rgb *= 0.18; // ekran foni to'q ko'k (fotodagidek), to'lqinlar uning ustida yorqin
    totalEmissiveRadiance += (ledWaves(vMallUv) + vec3(0.03, 0.05, 0.15)) * uLed;
  }`);
  };
  mat.customProgramCacheKey = () => 'mall-led';
  return mat;
}

// ---------------------------------------------------------------- komponent

const isTap = (e: ThreeEvent<MouseEvent>) => e.delta < 6;

type MallProps = { b: Building; look: BuildingLook; pal: Palette; night: boolean; selected: boolean; onSelect: (id: string) => void };

/**
 * Katta bino. Qurilayotgan bo'lsa (config.ts → CONSTRUCTION) odatiy holda qurilish maydoni ko'rinadi;
 * `future` (pastki oynadagi "2027") — tayyor bino yerdan ko'tarilib chiqadi, ustida "Loyiha" yozuvi
 */
export function MallBuilding(props: MallProps & { construction?: { zone: Poly }; future?: boolean }) {
  const site = CONSTRUCTION[props.b.id];
  if (site?.display === 'finished') return <MallFinished {...props} rise={false} year={site.opens} />;
  if (site && props.construction && !props.future) {
    return <ConstructionSite {...props} zone={props.construction.zone} floorsBuilt={site.floorsBuilt} banner={site.banner} />;
  }
  return <MallFinished {...props} rise={!!(site && props.construction)} opens={site?.opens} />;
}

/**
 * Bino tepasidagi katta ochilish yili: doim kameraga qaragan yassi belgi. O'lchami metrda (yaqinlashganda kattalashadi),
 * lekin uzoqdan ham ekranda kamida `minPx` piksel eni bilan ko'rinadi
 */
const YEAR_SIGN = { width: 28, gap: 2.5, minPx: 84, minPxPhone: 66 };
const SIGN_ASPECT = 400 / 1024;
function yearTexture(text: string) {
  const W = 1024, H = 400;
  const tex = canvasTexture(W, H, (g) => {
    g.clearRect(0, 0, W, H);
    const r = 70, pad = 14;
    g.fillStyle = 'rgba(0,0,0,0.22)';
    g.beginPath(); g.roundRect(pad + 6, pad + 14, W - pad * 2 - 6, H - pad * 2 - 14, r); g.fill(); // soya
    g.fillStyle = '#facc15';
    g.beginPath(); g.roundRect(pad, pad, W - pad * 2 - 6, H - pad * 2 - 14, r); g.fill();
    g.lineWidth = 14; g.strokeStyle = '#ffffff'; g.stroke();
    g.fillStyle = '#1f2937';
    g.font = '800 270px "Unbounded", "Onest", system-ui, sans-serif';
    g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillText(text, W / 2 - 3, H / 2 - 2, W - 120);
  });
  tex.anisotropy = 8;
  return tex;
}

function YearSign({ base, text }: { base: THREE.Vector3; text: string }) {
  const tex = useMemo(() => yearTexture(text), [text]);
  // Unbounded shrifti keyinroq yuklansa — qayta chizamiz
  useEffect(() => {
    let alive = true;
    document.fonts?.ready.then(() => {
      if (!alive) return;
      const t = yearTexture(text), ctx = (tex.image as HTMLCanvasElement).getContext('2d')!;
      ctx.clearRect(0, 0, 1024, 400); ctx.drawImage(t.image as HTMLCanvasElement, 0, 0);
      tex.needsUpdate = true; t.dispose();
    });
    return () => { alive = false; tex.dispose(); };
  }, [tex, text]);
  const sprite = useRef<THREE.Sprite>(null!);
  const v = useMemo(() => new THREE.Vector3(), []);
  useFrame(({ camera, size }) => {
    const cam = camera as THREE.PerspectiveCamera, sp = sprite.current;
    if (!sp) return;
    const d = Math.max(1, v.copy(base).distanceTo(cam.position));
    const pxPerM = size.height / (2 * d * Math.tan(THREE.MathUtils.degToRad(cam.fov ?? 32) / 2));
    const minPx = size.width < 640 ? YEAR_SIGN.minPxPhone : YEAR_SIGN.minPx;
    const wM = Math.max(YEAR_SIGN.width, minPx / pxPerM), hM = wM * SIGN_ASPECT;
    sp.scale.set(wM, hM, 1);
    sp.position.set(base.x, base.y + YEAR_SIGN.gap + hM / 2, base.z); // pastki cheti tomdan biroz yuqorida
  });
  return (
    <sprite ref={sprite} position={base} scale={[YEAR_SIGN.width, YEAR_SIGN.width * SIGN_ASPECT, 1]} renderOrder={6}>
      <spriteMaterial map={tex} transparent depthWrite={false} toneMapped={false} fog={false} />
    </sprite>
  );
}

function MallFinished({ b, look, pal, night, selected, onSelect, rise, opens, year }: MallProps & { rise: boolean; opens?: string; year?: string }) {
  const parts = useMemo(() => mallParts(b, look), [b, look]);
  const tex = useMemo(() => {
    const side = sideTextures(parts.runLen.side || 20);
    return {
      front: frontTextures(parts.runLen.front || 40), side, gray: grayTextures(), pool: poolSideTextures(),
      pylon: pylonTexture(), portal: portalTexture(), roof: roofTexture(),
    };
  }, [parts]);
  const led = useMemo(() => ({
    front: { uTime: { value: 0 }, uLed: { value: 0 }, uBandU: { value: new THREE.Vector2(PYLON.width, 1e4) } },
    side: { uTime: { value: 0 }, uLed: { value: 0 }, uBandU: { value: new THREE.Vector2(-1, tex.side.wrap) } },
  }), [tex]);
  // Devorlar biroz yorqinroq (och plitka fotodagidek oq-krem ko'rinsin)
  // Tanlanganda butunlay bo'yalmaydi (katta bino — fasad ko'rinib tursin), faqat iliq tus oladi
  const tint = useMemo(() => new THREE.Color(1.12, 1.12, 1.12).lerp(new THREE.Color(pal.selected).multiplyScalar(1.15), selected ? 0.28 : 0), [selected, pal]);
  const mats = useMemo(() => {
    const m = (t: { map: THREE.Texture; glow: THREE.Texture }) =>
      new THREE.MeshStandardMaterial({ map: t.map, emissiveMap: t.glow, emissive: new THREE.Color('#ffd9a8'), roughness: 0.75, side: THREE.DoubleSide });
    return {
      front: withLed(m(tex.front), led.front),
      side: withLed(m(tex.side), led.side),
      gray: m(tex.gray), pool: m(tex.pool), pylon: m(tex.pylon),
    };
  }, [tex, led]);
  useEffect(() => {
    for (const k of ['front', 'side', 'gray', 'pool', 'pylon'] as const) {
      mats[k].color.copy(tint);
      mats[k].emissiveIntensity = night ? (k === 'pylon' ? 0.9 : 0.75) : 0;
    }
    led.front.uLed.value = led.side.uLed.value = night ? 1 : 0;
  }, [mats, led, tint, night]);
  useEffect(() => () => {
    for (const g of [...Object.values(parts.walls), parts.roof, parts.pylon, parts.portal, parts.details]) g.dispose();
    for (const t of Object.values(tex)) {
      if (t instanceof THREE.Texture) t.dispose();
      else Object.values(t).forEach((x) => { if (x instanceof THREE.Texture) x.dispose(); });
    }
    Object.values(mats).forEach((x) => x.dispose());
  }, [parts, tex, mats]);

  // LED to'lqinlari faqat kechasi harakatlanadi
  const animate = night && !prefersReducedMotion();
  useAmbientFrames(animate);
  const t0 = useRef(0);
  useFrame((_, dt) => {
    if (!animate) return;
    t0.current += Math.min(dt, 0.1);
    led.front.uTime.value = led.side.uTime.value = t0.current;
  });

  // Loyiha ko'rinishi: bino yerdan ko'tarilib chiqadi (1.2 s)
  const grow = useRef<THREE.Group>(null!);
  const riseT = useRef(rise && !prefersReducedMotion() ? 0 : 1);
  useEffect(() => { if (grow.current) grow.current.scale.y = Math.max(0.02, riseT.current); }, []);
  useFrame((st, dt) => {
    if (riseT.current >= 1) return;
    riseT.current = Math.min(1, riseT.current + Math.min(dt, 0.05) / 1.2);
    grow.current.scale.y = Math.max(0.02, 1 - Math.pow(1 - riseT.current, 3));
    st.invalidate();
  });
  const signAt = useMemo(() => {
    // Tomning o'rtasi (og'irlik markazi) ustida
    const ring = ringOf(b);
    let a2 = 0, cx = 0, cy = 0;
    for (let i = 0; i < ring.length; i++) {
      const p = ring[i], q = ring[(i + 1) % ring.length], f = p[0] * q[1] - q[0] * p[1];
      a2 += f; cx += (p[0] + q[0]) * f; cy += (p[1] + q[1]) * f;
    }
    return w([cx / (3 * a2), cy / (3 * a2)], H_TOP);
  }, [b]);
  const tagAt = useMemo(() => {
    // Old fasad o'rtasi, karniz ustida
    const ring = ringOf(b), f0 = look.frontEdge ?? 0, a = ring[f0], c = ring[(f0 + 2) % ring.length];
    return w([(a[0] + c[0]) / 2, (a[1] + c[1]) / 2], H_TOP + 3);
  }, [b, look]);

  return (
    <group ref={grow} onClick={(e) => { if (!isTap(e)) return; e.stopPropagation(); onSelect(b.id); }}>
      {rise && opens && (
        <Html position={tagAt} center zIndexRange={[30, 0]} style={{ pointerEvents: 'none' }}>
          <div className="future-tag">Loyiha · {opens}-yilda ochiladi</div>
        </Html>
      )}
      {year && <YearSign base={signAt} text={year} />}
      <mesh geometry={parts.walls.front} material={mats.front} castShadow receiveShadow />
      <mesh geometry={parts.walls.side} material={mats.side} castShadow receiveShadow />
      <mesh geometry={parts.walls.gray} material={mats.gray} castShadow receiveShadow />
      <mesh geometry={parts.walls.pool} material={mats.pool} castShadow receiveShadow />
      <mesh geometry={parts.pylon} material={mats.pylon} castShadow receiveShadow />
      <mesh geometry={parts.portal} castShadow receiveShadow>
        <meshStandardMaterial map={tex.portal} color={tint} roughness={0.85} side={THREE.DoubleSide} />
      </mesh>
      <mesh geometry={parts.roof} receiveShadow>
        <meshStandardMaterial map={tex.roof} color={night ? '#9da2a8' : selected ? tint : '#ffffff'} roughness={0.9} />
      </mesh>
      <mesh geometry={parts.details} castShadow receiveShadow>
        <meshStandardMaterial vertexColors roughness={0.7} side={THREE.DoubleSide} />
      </mesh>
    </group>
  );
}

// "Balicha massaj" — fotoga qarab: Banya va More binosi orasidagi bir qavatli oq bino.
// Pastda kafe ("Fastfood zona"): katta qora romli oynalar, tepasida chuqurchadagi yog'och panellar. Old tomon tepasida
// och kulrang tasma va katta qora harflar "БАЛИЙСКИЙ МАССАЖ НА МОРЕ" (kechasi yonadi). Tomida: travertin pol,
// orqa va yon tomonlarda oq panjara to'siq, katta bej chodir-soyabon (qiya, giperbolik mato), uning ostida ikkita massaj
// chodiri (parda, ichida massaj stoli), old tomonda somon soyabon. O'ng tomonda tomga ko'tariladigan po'lat zinapoya.
// Old tomonda — ayvon: rotang stullar, oq soyabonlar, yashil to'siq (o'rtasida o'tish joyi), axlat qutilari.
import { useEffect, useMemo } from 'react';
import * as THREE from 'three';
import type { ThreeEvent } from '@react-three/fiber';
import type { BuildingLook } from './config';
import { canvasTexture, colored, mergeAll, rod } from './modelKit';
import { travertineTexture } from './poolDecor';
import type { XY } from './projection';
import { newBuf, quad, ringOf, toGeom, w } from './styledBuilding';
import type { Palette } from './theme';
import type { Building } from './types';

const H = 4.4; // devor (tom poli) balandligi
const BAND = [4.4, 5.45] as const; // harfli tasma
const SCREEN_H = 1.9; // tomdagi panjara balandligi
const CANOPY = { FL: 9.4, FR: 6.9, BR: 9.6, BL: 7.1, over: 0.5, sag: 0.7 }; // chodir burchaklari balandligi (giperbolik mato)
const PPM = 48;

const isTap = (e: ThreeEvent<MouseEvent>) => e.delta < 6;

function rnd(seed: number) {
  let s = seed;
  return () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
}

/** Bino tepasi (pin uchun): chodirning eng baland burchagi */
export const massageTop = () => CANOPY.BR + 0.6;

// ---------------------------------------------------------------- teksturalar

type Rect = [number, number, number, number];

function stucco(g: CanvasRenderingContext2D, W: number, Hp: number) {
  g.fillStyle = '#f1ece3'; g.fillRect(0, 0, W, Hp);
  const r = rnd(9);
  for (let i = 0; i < W * Hp / 60; i++) {
    const v = 205 + r() * 40;
    g.fillStyle = `rgba(${v},${v - 6},${v - 16},0.25)`;
    g.fillRect(r() * W, r() * Hp, 2, 1);
  }
}

/** Fasad chizgichi: u (m) chapdan, h (m) pastdan */
function painter(Lm: number, Hm: number) {
  const Wpx = Math.round(Lm * PPM), Hpx = Math.round(Hm * PPM);
  return { Wpx, Hpx, X: (u: number) => Math.round(u * PPM), Y: (h: number) => Math.round((Hm - h) * PPM) };
}

/** Qora romli oyna guruhi: `panes` ta bo'lak; kechasi ichi iliq yonadi */
function glassGroup(g: CanvasRenderingContext2D, P: ReturnType<typeof painter>, u0: number, u1: number, h0: number, h1: number, panes: number, lit: Rect[], bars: Rect[]) {
  const { X, Y } = P;
  const gr = g.createLinearGradient(0, Y(h1), 0, Y(h0));
  gr.addColorStop(0, '#5d7182'); gr.addColorStop(0.5, '#8299a8'); gr.addColorStop(1, '#3f4d59');
  g.fillStyle = gr; g.fillRect(X(u0), Y(h1), X(u1) - X(u0), Y(h0) - Y(h1));
  // osmon va soyabon aksi
  g.fillStyle = 'rgba(240,244,246,0.22)';
  g.fillRect(X(u0), Y(h1 - 0.35), X(u1) - X(u0), Y(h1 - 1.0) - Y(h1 - 0.35));
  lit.push([X(u0), Y(h1), X(u1) - X(u0), Y(h0) - Y(h1)]);
  g.fillStyle = '#26292d';
  const fw = 5;
  for (let k = 0; k <= panes; k++) {
    const x = X(u0 + ((u1 - u0) * k) / panes) - fw / 2;
    g.fillRect(x, Y(h1), fw, Y(h0) - Y(h1)); bars.push([x, Y(h1), fw, Y(h0) - Y(h1)]);
  }
  for (const h of [h0, h1]) { g.fillRect(X(u0), Y(h) - fw / 2, X(u1) - X(u0), fw); bars.push([X(u0), Y(h) - fw / 2, X(u1) - X(u0), fw]); }
}

/** Devordagi chuqurcha: ichida tik yog'och taxtalar */
function woodRecess(g: CanvasRenderingContext2D, P: ReturnType<typeof painter>, u0: number, u1: number, h0: number, h1: number) {
  const { X, Y } = P;
  g.fillStyle = '#c9c1b4'; g.fillRect(X(u0) - 4, Y(h1) - 4, X(u1) - X(u0) + 8, Y(h0) - Y(h1) + 8); // soya cheti
  const r = rnd(Math.round(u0 * 31));
  for (let x = X(u0); x < X(u1); x += 7) {
    const v = 0.85 + r() * 0.25;
    g.fillStyle = `rgb(${Math.round(112 * v)},${Math.round(84 * v)},${Math.round(62 * v)})`;
    g.fillRect(x, Y(h1), 6, Y(h0) - Y(h1));
  }
}

function glowCanvas(P: ReturnType<typeof painter>, lit: Rect[], bars: Rect[]) {
  return canvasTexture(P.Wpx, P.Hpx, (g) => {
    g.fillStyle = '#000'; g.fillRect(0, 0, P.Wpx, P.Hpx);
    const r = rnd(5);
    for (const [x, y, ww, hh] of lit) {
      for (let xx = x; xx < x + ww; xx += 40) {
        const v = 0.55 + r() * 0.45;
        g.fillStyle = `rgb(${Math.round(255 * v)},${Math.round(208 * v)},${Math.round(150 * v)})`;
        g.fillRect(xx, y, Math.min(40, x + ww - xx), hh);
      }
    }
    g.fillStyle = '#000';
    for (const [x, y, ww, hh] of bars) g.fillRect(x, y, ww, hh);
  });
}

function asTex(t: THREE.CanvasTexture, Lm: number, Hm: number) {
  t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
  t.repeat.set(1 / Lm, 1 / Hm);
  return t;
}

/** Old fasad: chapdan o'ngga — 3 bo'lakli oyna, ustun, 2 bo'lak + eshik, ustun, 4 bo'lak; tepada yog'och chuqurchalar va lavha */
function frontTextures(L: number) {
  const P = painter(L, H), k = L / 18; // fotodagi nisbatlar 18 m eniga
  const lit: Rect[] = [], bars: Rect[] = [];
  const map = canvasTexture(P.Wpx, P.Hpx, (g) => {
    stucco(g, P.Wpx, P.Hpx);
    g.fillStyle = '#cfc8bb'; g.fillRect(0, P.Y(0.15), P.Wpx, P.Hpx - P.Y(0.15));
    glassGroup(g, P, 0.5 * k, 4.6 * k, 0.15, 2.85, 3, lit, bars);
    glassGroup(g, P, 6.0 * k, 8.2 * k, 0.15, 2.85, 2, lit, bars);
    glassGroup(g, P, 8.3 * k, 10.1 * k, 0.15, 2.85, 2, lit, bars); // eshik (ikki tavaqa)
    g.fillStyle = '#c4c9cc'; g.fillRect(P.X(9.15 * k) - 3, P.Y(1.6), 6, P.Y(1.0) - P.Y(1.6)); // tutqichlar
    glassGroup(g, P, 11.0 * k, 17.4 * k, 0.15, 2.85, 4, lit, bars);
    for (const [a, b] of [[1.0, 2.6], [5.0, 5.7], [6.4, 7.6], [11.5, 12.6]]) woodRecess(g, P, a * k, b * k, 3.05, 4.25);
    // "Fastfood zona" lavhasi
    const sx = P.X(13.0 * k), sy = P.Y(4.15), sw = P.X(2.4), sh = P.Y(3.1) - P.Y(4.15);
    g.fillStyle = '#1f2a3d'; g.fillRect(sx, sy, sw, sh);
    g.fillStyle = '#ffffff'; g.font = `600 ${Math.round(0.26 * PPM)}px "Onest", Arial, sans-serif`; g.textBaseline = 'middle';
    g.fillText('Fastfood', sx + 0.55 * PPM, sy + sh * 0.38);
    g.fillText('zona', sx + 0.55 * PPM, sy + sh * 0.7);
    g.strokeStyle = '#ffffff'; g.lineWidth = 2; g.strokeRect(sx + 0.15 * PPM, sy + sh * 0.25, 0.25 * PPM, sh * 0.5);
  });
  return { map: asTex(map, L, H), glow: asTex(glowCanvas(P, lit, bars), L, H) };
}

/** Yon va orqa devorlar: suvoq, bitta-ikkita oyna, yog'och chuqurcha */
function plainTextures(L: number, windows: [number, number][], door?: [number, number]) {
  const P = painter(L, H);
  const lit: Rect[] = [], bars: Rect[] = [];
  const map = canvasTexture(P.Wpx, P.Hpx, (g) => {
    stucco(g, P.Wpx, P.Hpx);
    g.fillStyle = '#cfc8bb'; g.fillRect(0, P.Y(0.15), P.Wpx, P.Hpx - P.Y(0.15));
    for (const [a, b] of windows) { glassGroup(g, P, a, b, 1.0, 2.85, 1, lit, bars); woodRecess(g, P, a, b, 3.05, 4.2); }
    if (door) {
      g.fillStyle = '#5a5f66'; g.fillRect(P.X(door[0]), P.Y(2.3), P.X(door[1]) - P.X(door[0]), P.Y(0.15) - P.Y(2.3));
      g.fillStyle = '#3a3e44'; g.fillRect(P.X((door[0] + door[1]) / 2) - 2, P.Y(2.3), 4, P.Y(0.15) - P.Y(2.3));
    }
  });
  return { map: asTex(map, L, H), glow: asTex(glowCanvas(P, lit, bars), L, H) };
}

/** Harfli tasma: och kulrang panel, katta qora harflar teng oraliqda; kechasi harflar yonadi */
function bandTextures(L: number, text: string) {
  const Hm = BAND[1] - BAND[0], Wpx = 2048, Hpx = Math.round((2048 * Hm) / L);
  const chars = [...text];
  const draw = (g: CanvasRenderingContext2D, glow: boolean) => {
    g.fillStyle = glow ? '#000' : '#d9dbdb'; g.fillRect(0, 0, Wpx, Hpx);
    if (!glow) { g.fillStyle = '#c3c6c7'; g.fillRect(0, Hpx - 4, Wpx, 4); g.fillRect(0, 0, Wpx, 3); }
    g.fillStyle = glow ? '#ffe9c4' : '#3a3b3d';
    g.font = `700 ${Math.round(Hpx * 0.62)}px "Onest", Arial, sans-serif`;
    g.textAlign = 'center'; g.textBaseline = 'middle';
    const step = Wpx / (chars.length + 1);
    chars.forEach((c, i) => g.fillText(c, step * (i + 1), Hpx * 0.54));
  };
  const map = canvasTexture(Wpx, Hpx, (g) => draw(g, false));
  const glow = canvasTexture(Wpx, Hpx, (g) => draw(g, true));
  for (const t of [map, glow]) t.anisotropy = 8;
  return { map, glow };
}

/** Oq panjara (romb katak), shaffof fon */
function latticeTexture() {
  const tex = canvasTexture(128, 128, (g, W, Hp) => {
    g.clearRect(0, 0, W, Hp);
    g.strokeStyle = '#f4f2ee'; g.lineWidth = 9;
    for (let k = -W; k <= W * 2; k += 32) {
      g.beginPath(); g.moveTo(k, 0); g.lineTo(k + Hp, Hp); g.stroke();
      g.beginPath(); g.moveTo(k, Hp); g.lineTo(k + Hp, 0); g.stroke();
    }
    g.strokeStyle = '#e8e4dc'; g.lineWidth = 10; g.strokeRect(0, 0, W, Hp);
  });
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(1 / 1.2, 1 / 1.2);
  return tex;
}

/** Parda: bej mato, tik burmalar */
function curtainTexture() {
  const tex = canvasTexture(64, 64, (g, W, Hp) => {
    for (let x = 0; x < W; x++) {
      const v = 0.86 + 0.14 * Math.cos((x / W) * Math.PI * 2 * 3);
      g.fillStyle = `rgb(${Math.round(240 * v)},${Math.round(224 * v)},${Math.round(200 * v)})`;
      g.fillRect(x, 0, 1, Hp);
    }
  });
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(1 / 0.6, 1);
  return tex;
}

/** Somon: radial tolalar */
function strawTexture() {
  const tex = canvasTexture(128, 32, (g, W, Hp) => {
    g.fillStyle = '#b48a52'; g.fillRect(0, 0, W, Hp);
    const r = rnd(4);
    for (let i = 0; i < 400; i++) {
      const v = 0.75 + r() * 0.4;
      g.fillStyle = `rgba(${Math.round(196 * v)},${Math.round(150 * v)},${Math.round(92 * v)},0.8)`;
      g.fillRect(r() * W, 0, 1, Hp);
    }
  });
  tex.wrapS = THREE.RepeatWrapping;
  return tex;
}

// ---------------------------------------------------------------- geometriya

/** Quti: lokal X o'qi ma'lumot koordinatasidagi `yaw` yo'nalishiga, markazi (p, y) */
function boxAt(sx: number, sy: number, sz: number, p: XY, y: number, yaw: number, hex: string) {
  const g = new THREE.BoxGeometry(sx, sy, sz);
  g.rotateY(yaw);
  g.translate(p[0], y, -p[1]);
  return colored(g, hex);
}

/** Rotang stul: o'tirg'ich, suyanchiq, oyoqlar (jigarrang) */
function chairAt(p: XY, face: number, out: THREE.BufferGeometry[]) {
  const c = Math.cos(face), s = Math.sin(face);
  const at = (a: number): XY => [p[0] - c * a, p[1] - s * a];
  out.push(boxAt(0.55, 0.08, 0.55, p, 0.44, face, '#5b4232'));
  out.push(boxAt(0.1, 0.5, 0.6, at(0.26), 0.72, face, '#4d382a'));
  out.push(boxAt(0.5, 0.44, 0.5, p, 0.22, face, '#3e2e23'));
}

function massageParts(b: Building, look: BuildingLook) {
  const ring = ringOf(b);
  const f0 = look.frontEdge ?? 0;
  // Old qirra FL→FR (tomoshabin chapdan o'ngga), keyin FR→BR, BR→BL, BL→FL
  const FL = ring[f0], FR = ring[(f0 + 1) % 4], BR = ring[(f0 + 2) % 4], BL = ring[(f0 + 3) % 4];
  const C: XY = [(FL[0] + FR[0] + BR[0] + BL[0]) / 4, (FL[1] + FR[1] + BR[1] + BL[1]) / 4];
  const W = Math.hypot(FL[0] - FR[0], FL[1] - FR[1]), Dp = Math.hypot(FL[0] - BL[0], FL[1] - BL[1]);
  const D: XY = [(FL[0] - FR[0]) / W, (FL[1] - FR[1]) / W]; // tomoshabinning chap tomoniga
  const N: XY = [(FL[0] - BL[0]) / Dp, (FL[1] - BL[1]) / Dp]; // oldinga
  const hw = W / 2, hd = Dp / 2, yawD = Math.atan2(D[1], D[0]);
  const L = (s: number, t: number): XY => [C[0] + D[0] * s + N[0] * t, C[1] + D[1] * s + N[1] * t];
  const Lw = (s: number, t: number, h: number) => w(L(s, t), h);
  const wn = (v: XY) => new THREE.Vector3(v[0], 0, -v[1]);

  // Devorlar: old, o'ng (zinapoya tomoni), orqa, chap — har biri o'z teksturasi bilan
  const walls = { front: newBuf(), right: newBuf(), back: newBuf(), left: newBuf() };
  const edges: [keyof typeof walls, XY, XY, XY][] = [
    ['front', FL, FR, N], ['right', FR, BR, [-D[0], -D[1]]], ['back', BR, BL, [-N[0], -N[1]]], ['left', BL, FL, D],
  ];
  for (const [k, p, q, n] of edges) {
    const len = Math.hypot(q[0] - p[0], q[1] - p[1]);
    quad(walls[k], [w(p, 0), w(q, 0), w(q, H), w(p, H)], [[0, 0], [len, 0], [len, H], [0, H]], wn(n));
  }

  // Tom poli (travertin) va parapet qirrasi
  const roofShape = new THREE.Shape([FL, FR, BR, BL].map(([x, y]) => new THREE.Vector2(x, y)));
  const roof = new THREE.ShapeGeometry(roofShape, 1);
  roof.rotateX(-Math.PI / 2);
  roof.translate(0, H + 0.02, 0);
  const solid: THREE.BufferGeometry[] = [];
  // tom chetidagi qopqoq (oq)
  for (const [, p, q, n] of edges) {
    const len = Math.hypot(q[0] - p[0], q[1] - p[1]);
    const mid: XY = [(p[0] + q[0]) / 2 - n[0] * 0.12, (p[1] + q[1]) / 2 - n[1] * 0.12];
    solid.push(boxAt(len + 0.1, 0.18, 0.28, mid, H + 0.09, Math.atan2(q[1] - p[1], q[0] - p[0]), '#e9e4da'));
  }

  // Harfli tasma: old devordan 6 sm oldinda
  const band = newBuf();
  {
    const a = L(hw + 0.1, hd + 0.08), c = L(-hw - 0.1, hd + 0.08), ln = W + 0.2;
    quad(band, [w(a, BAND[0]), w(c, BAND[0]), w(c, BAND[1]), w(a, BAND[1])], [[0, 0], [1, 0], [1, 1], [0, 1]], wn(N));
    solid.push(boxAt(ln, BAND[1] - BAND[0], 0.08, L(0, hd + 0.03), (BAND[0] + BAND[1]) / 2, yawD, '#c9cccd'));
  }

  // Tomdagi panjara to'siq: orqa va ikki yon, o'ng tomonda zinapoya kirishi uchun ochiq joy
  const lat = newBuf();
  const screen = (s0: number, t0: number, s1: number, t1: number, n: XY) => {
    const p = L(s0, t0), q = L(s1, t1), len = Math.hypot(q[0] - p[0], q[1] - p[1]);
    quad(lat, [w(p, H), w(q, H), w(q, H + SCREEN_H), w(p, H + SCREEN_H)], [[0, 0], [len, 0], [len, SCREEN_H], [0, SCREEN_H]], wn(n));
  };
  screen(-hw + 0.15, -hd + 0.15, hw - 0.15, -hd + 0.15, [-N[0], -N[1]]);
  screen(hw - 0.15, -hd + 0.15, hw - 0.15, hd - 0.4, D);
  screen(-hw + 0.15, hd - 0.4, -hw + 0.15, -hd + 3.0, [-D[0], -D[1]]); // o'ng: orqa tomondan 2.85 m ochiq (zinapoya)
  for (const [s, t] of [[-hw + 0.15, -hd + 0.15], [hw - 0.15, -hd + 0.15], [hw - 0.15, hd - 0.4], [-hw + 0.15, hd - 0.4], [-hw + 0.15, -hd + 3.0]]) {
    solid.push(boxAt(0.12, SCREEN_H + 0.05, 0.12, L(s, t), H + SCREEN_H / 2, yawD, '#e6e2da'));
  }
  // Old tomonda past oq to'siq (harfli tasma ortida)
  solid.push(boxAt(W - 0.3, 1.05, 0.15, L(0, hd - 0.25), H + 0.52, yawD, '#ece7de'));

  // Chodir-soyabon: giperbolik mato (qarama-qarshi burchaklari baland), 4 ustun
  const cg = new THREE.BufferGeometry();
  {
    const nS = 14, nT = 8, pos: number[] = [], idx: number[] = [], uv: number[] = [];
    const s0 = hw + CANOPY.over, t0 = hd + CANOPY.over;
    for (let j = 0; j <= nT; j++) for (let i = 0; i <= nS; i++) {
      const a = i / nS, bb = j / nT; // a: chap(0)→o'ng(1), bb: old(0)→orqa(1)
      const h = (1 - a) * (1 - bb) * CANOPY.FL + a * (1 - bb) * CANOPY.FR + a * bb * CANOPY.BR + (1 - a) * bb * CANOPY.BL
        - CANOPY.sag * Math.sin(Math.PI * a) * Math.sin(Math.PI * bb); // mato osilgan (tarang yelkan)
      const p = Lw(s0 - 2 * s0 * a, t0 - 2 * t0 * bb, h);
      pos.push(p.x, p.y, p.z); uv.push(a, bb);
    }
    for (let j = 0; j < nT; j++) for (let i = 0; i < nS; i++) {
      const k = j * (nS + 1) + i;
      idx.push(k, k + 1, k + nS + 1, k + 1, k + nS + 2, k + nS + 1);
    }
    cg.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    cg.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
    cg.setIndex(idx);
    cg.computeVertexNormals();
  }
  const posts: THREE.BufferGeometry[] = [];
  for (const [s, t, h] of [[hw - 0.2, hd - 0.2, CANOPY.FL], [-hw + 0.2, hd - 0.2, CANOPY.FR], [-hw + 0.2, -hd + 0.2, CANOPY.BR], [hw - 0.2, -hd + 0.2, CANOPY.BL]]) {
    posts.push(colored(rod(Lw(s, t, H), Lw(s * (1 + CANOPY.over / hw), t * (1 + CANOPY.over / hd), h - 0.1), 0.08, 6), '#4a4e54'));
  }
  // o'rtadagi ikki ustun (mato tarang tursin)
  for (const s of [-hw / 3, hw / 3]) posts.push(colored(rod(Lw(s, -hd + 0.25, H), Lw(s, -hd + 0.25, 7.6), 0.07, 6), '#4a4e54'));

  // Massaj chodirlari: 3×3 m, parda devorlar (oldi ochiq, pardalar bog'langan), qiya tom va kulrang tasma
  const curt = newBuf();
  const tentRoof: THREE.BufferGeometry[] = [];
  const tentIn: THREE.BufferGeometry[] = [];
  const TS = 3.0, TH = 2.3;
  for (const sc of [hw * 0.45, -hw * 0.45]) {
    const tc = -hd + 1.9;
    const corner = (a: number, c: number): XY => L(sc + a * TS / 2, tc + c * TS / 2);
    const side = (p: XY, q: XY, n: XY, u0 = 0) => {
      const len = Math.hypot(q[0] - p[0], q[1] - p[1]);
      quad(curt, [w(p, H), w(q, H), w(q, H + TH), w(p, H + TH)], [[u0, 0], [u0 + len, 0], [u0 + len, 1], [u0, 1]], wn(n));
    };
    side(corner(1, -1), corner(-1, -1), [-N[0], -N[1]]); // orqa
    side(corner(-1, -1), corner(-1, 1), [-D[0], -D[1]]);
    side(corner(1, 1), corner(1, -1), D);
    // old: chetlarda yig'ilgan pardalar (har biri 0.75 m)
    side(corner(1, 1), L(sc + TS / 2 - 0.55, tc + TS / 2), N);
    side(L(sc - TS / 2 + 0.55, tc + TS / 2), corner(-1, 1), N);
    // ichi: to'q matoli pol (kirish ochiq — ichi ko'rinsin)
    tentIn.push(boxAt(TS - 0.1, 0.02, TS - 0.1, L(sc, tc), H + 0.01, yawD, '#8a7a66'));
    // tom: piramida + kulrang tasma
    const pyr = new THREE.ConeGeometry(TS * 0.72, 0.9, 4, 1, true);
    pyr.rotateY(Math.PI / 4 + yawD);
    const pc = w(L(sc, tc), H + TH + 0.45);
    pyr.translate(pc.x, pc.y, pc.z);
    tentRoof.push(colored(pyr, '#6f6a62'));
    tentRoof.push(boxAt(TS + 0.08, 0.26, TS + 0.08, L(sc, tc), H + TH - 0.1, yawD, '#5f5b55'));
    // ichida massaj stoli
    tentIn.push(boxAt(1.9, 0.12, 0.72, L(sc, tc - 0.3), H + 0.78, yawD, '#6b3f2a'));
    tentIn.push(boxAt(1.6, 0.7, 0.5, L(sc, tc - 0.3), H + 0.36, yawD, '#2d2f33'));
  }
  // massaj kursisi (chodirlar orasida)
  tentIn.push(boxAt(0.5, 0.1, 0.45, L(0, -hd + 1.6), H + 0.6, yawD, '#202226'));
  tentIn.push(boxAt(0.12, 0.6, 0.12, L(0, -hd + 1.6), H + 0.3, yawD, '#8a9096'));

  // Somon soyabon: tom old tomonida
  const strawC = L(hw * 0.12, hd - 2.1);
  const straw = new THREE.ConeGeometry(2.2, 1.0, 18, 1, true);
  const sp = w(strawC, H + 2.75);
  straw.translate(sp.x, sp.y, sp.z);
  posts.push(colored(rod(w(strawC, H), w(strawC, H + 2.7), 0.06, 6), '#6b4a2e'));

  // Zinapoya: o'ng devor bo'ylab, oldidan 1.6 m oldinda boshlanib, orqa tomonda tomga chiqadi
  const stair: THREE.BufferGeometry[] = [];
  {
    const so = -hw - 0.85; // devordan 0.85 m tashqarida (eni 1.3 m)
    const tB = hd + 1.6, tT = -hd + 2.9, steps = 26;
    const rise = H / steps, run = (tB - tT) / steps;
    for (let k = 0; k < steps; k++) {
      const t = tB - run * (k + 0.5);
      stair.push(boxAt(1.3, 0.06, run + 0.04, L(so, t), rise * (k + 1) - 0.03, yawD, '#62676d'));
    }
    for (const ds of [-0.68, 0.68]) {
      // tetiva (qiya) va panjara
      stair.push(colored(rod(Lw(so + ds, tB, 0), Lw(so + ds, tT, H), 0.09, 4), '#3b3f45'));
      stair.push(colored(rod(Lw(so + ds, tB, 1.0), Lw(so + ds, tT, H + 1.0), 0.03, 4), '#3b3f45'));
      for (let k = 0; k <= 6; k++) {
        const t = tB + ((tT - tB) * k) / 6, h = (H * k) / 6;
        stair.push(colored(rod(Lw(so + ds, t, h), Lw(so + ds, t, h + 1.0), 0.025, 4), '#3b3f45'));
      }
    }
    // tepadagi maydoncha va pastdagi tayanch ustunlar
    stair.push(boxAt(1.5, 0.12, 1.6, L(so, tT - 0.8), H - 0.06, yawD, '#62676d'));
    for (const k of [0.33, 0.66]) stair.push(colored(rod(Lw(so, tB + (tT - tB) * k, 0), Lw(so, tB + (tT - tB) * k, H * k), 0.07, 4), '#3b3f45'));
  }

  // Ayvon: 2 qator × 3 stol (oq soyabon, 4 ta rotang stul), yashil to'siq (o'rtasi ochiq), axlat qutilari
  const patio: THREE.BufferGeometry[] = [];
  const umb: THREE.BufferGeometry[] = [];
  for (const t of [hd + 3.4, hd + 7.4]) for (const s of [-hw * 0.6, 0, hw * 0.6]) {
    const c = L(s, t);
    patio.push(boxAt(1.7, 0.06, 0.85, c, 0.74, yawD, '#3b3530'));
    patio.push(boxAt(0.1, 0.72, 0.1, c, 0.36, yawD, '#2c2825'));
    const face = yawD;
    for (const [ds, dt, f] of [[0.45, 0.75, face - Math.PI / 2], [-0.45, 0.75, face - Math.PI / 2], [0.45, -0.75, face + Math.PI / 2], [-0.45, -0.75, face + Math.PI / 2]] as const) {
      chairAt(L(s + ds, t + dt), f, patio);
    }
    // soyabon: ustun + kvadrat piramida (3 m)
    const top = w(c, 0);
    umb.push(colored(new THREE.CylinderGeometry(0.04, 0.04, 2.6, 5).translate(top.x, 1.3, top.z), '#d8dadc'));
    const cn = new THREE.ConeGeometry(2.1, 0.5, 4, 1, true).rotateY(Math.PI / 4 + yawD).translate(top.x, 2.62, top.z);
    const hem = new THREE.CylinderGeometry(2.1, 2.1, 0.16, 4, 1, true).rotateY(Math.PI / 4 + yawD).translate(top.x, 2.31, top.z);
    umb.push(colored(mergeAll([cn, hem]), '#f6f6f2'));
  }
  const hedge: THREE.BufferGeometry[] = [];
  for (const [s0, s1] of [[-hw + 0.5, -1.6], [1.6, hw - 0.5]]) {
    for (let s = s0; s < s1 - 0.01; s += 1.0) {
      const len = Math.min(1.0, s1 - s), v = 0.85 + ((Math.round(s * 7) % 5) / 5) * 0.25;
      const col = '#' + new THREE.Color(0.24 * v, 0.47 * v, 0.22 * v).getHexString();
      hedge.push(boxAt(len + 0.05, 1.1 + 0.15 * Math.sin(s * 3.1), 1.0, L(s + len / 2, hd + 10.2), 0.58, yawD, col));
    }
  }
  patio.push(boxAt(0.5, 0.9, 0.45, L(-2.3, hd + 10.2), 0.45, yawD, '#2d6fb8'));
  patio.push(boxAt(0.5, 0.9, 0.45, L(2.3, hd + 10.2), 0.45, yawD, '#c8372f'));

  return {
    walls: { front: toGeom(walls.front), right: toGeom(walls.right), back: toGeom(walls.back), left: toGeom(walls.left) },
    lens: { front: W, side: Dp }, roof, solid: mergeAll(solid), band: toGeom(band), lattice: toGeom(lat), canopy: cg,
    posts: mergeAll(posts), curtains: toGeom(curt), tentRoof: mergeAll(tentRoof), tentIn: mergeAll(tentIn), straw,
    stair: mergeAll(stair), patio: mergeAll(patio), umbrellas: mergeAll(umb), hedge: mergeAll(hedge),
  };
}

// ---------------------------------------------------------------- komponent

export function MassageBuilding({ b, look, pal, night, selected, onSelect }: {
  b: Building; look: BuildingLook; pal: Palette; night: boolean; selected: boolean; onSelect: (id: string) => void;
}) {
  const parts = useMemo(() => massageParts(b, look), [b, look]);
  const tex = useMemo(() => ({
    front: frontTextures(parts.lens.front),
    right: plainTextures(parts.lens.side, [], [parts.lens.side - 2.6, parts.lens.side - 1.6]),
    back: plainTextures(parts.lens.front, [[3.0, 4.6], [13.4, 15.0]], [8.6, 9.6]),
    left: plainTextures(parts.lens.side, [[2.6, 5.4]]),
    band: bandTextures(parts.lens.front + 0.2, 'БАЛИЙСКИЙ МАССАЖ НА МОРЕ'),
    lattice: latticeTexture(), curtain: curtainTexture(), straw: strawTexture(), roof: travertineTexture(),
  }), [parts]);
  useEffect(() => () => {
    for (const g of [...Object.values(parts.walls), parts.roof, parts.solid, parts.band, parts.lattice, parts.canopy, parts.posts,
      parts.curtains, parts.tentRoof, parts.tentIn, parts.straw, parts.stair, parts.patio, parts.umbrellas, parts.hedge]) g.dispose();
    for (const t of Object.values(tex)) {
      if (t instanceof THREE.Texture) t.dispose();
      else Object.values(t).forEach((x) => (x as THREE.Texture).dispose());
    }
  }, [parts, tex]);

  const tint = useMemo(() => new THREE.Color(1.06, 1.06, 1.06).lerp(new THREE.Color(pal.selected), selected ? 0.3 : 0), [selected, pal]);
  const glow = night ? 0.85 : 0;
  const wall = (t: { map: THREE.Texture; glow: THREE.Texture }) => (
    <meshStandardMaterial map={t.map} emissiveMap={t.glow} emissive="#ffd9a8" emissiveIntensity={glow} color={tint} roughness={0.85} />
  );
  return (
    <group onClick={(e) => { if (!isTap(e)) return; e.stopPropagation(); onSelect(b.id); }}>
      <mesh geometry={parts.walls.front} castShadow receiveShadow>{wall(tex.front)}</mesh>
      <mesh geometry={parts.walls.right} castShadow receiveShadow>{wall(tex.right)}</mesh>
      <mesh geometry={parts.walls.back} castShadow receiveShadow>{wall(tex.back)}</mesh>
      <mesh geometry={parts.walls.left} castShadow receiveShadow>{wall(tex.left)}</mesh>
      <mesh geometry={parts.roof} receiveShadow>
        <meshStandardMaterial map={tex.roof} color={night ? '#a7a39c' : '#ffffff'} roughness={0.9} />
      </mesh>
      <mesh geometry={parts.solid} castShadow receiveShadow>
        <meshStandardMaterial vertexColors color={tint} roughness={0.8} />
      </mesh>
      <mesh geometry={parts.band}>
        <meshStandardMaterial map={tex.band.map} emissiveMap={tex.band.glow} emissive="#ffffff" emissiveIntensity={night ? 1 : 0}
          roughness={0.5} metalness={0.2} polygonOffset polygonOffsetFactor={-1} />
      </mesh>
      <mesh geometry={parts.lattice} castShadow>
        <meshStandardMaterial map={tex.lattice} alphaTest={0.5} side={THREE.DoubleSide} roughness={0.8} />
      </mesh>
      <mesh geometry={parts.canopy} castShadow receiveShadow>
        <meshStandardMaterial color={night ? '#bdb2a0' : '#eadfc8'} emissive="#ffcf8a" emissiveIntensity={night ? 0.18 : 0}
          roughness={0.95} side={THREE.DoubleSide} />
      </mesh>
      <mesh geometry={parts.posts} castShadow>
        <meshStandardMaterial vertexColors roughness={0.6} metalness={0.3} />
      </mesh>
      <mesh geometry={parts.curtains} castShadow receiveShadow>
        <meshStandardMaterial map={tex.curtain} color="#fff6ea" roughness={0.95} side={THREE.DoubleSide}
          emissive="#ffcf8a" emissiveIntensity={night ? 0.22 : 0.06} />
      </mesh>
      <mesh geometry={parts.tentRoof} castShadow>
        <meshStandardMaterial vertexColors roughness={0.9} side={THREE.DoubleSide} />
      </mesh>
      <mesh geometry={parts.tentIn}>
        <meshStandardMaterial vertexColors roughness={0.8} />
      </mesh>
      <mesh geometry={parts.straw} castShadow>
        <meshStandardMaterial map={tex.straw} roughness={1} side={THREE.DoubleSide} />
      </mesh>
      <mesh geometry={parts.stair} castShadow receiveShadow>
        <meshStandardMaterial vertexColors roughness={0.6} metalness={0.3} />
      </mesh>
      <mesh geometry={parts.patio} castShadow receiveShadow>
        <meshStandardMaterial vertexColors roughness={0.85} />
      </mesh>
      <mesh geometry={parts.umbrellas} castShadow receiveShadow>
        <meshStandardMaterial vertexColors roughness={0.85} side={THREE.DoubleSide} />
      </mesh>
      <mesh geometry={parts.hedge} castShadow receiveShadow>
        <meshStandardMaterial vertexColors roughness={1} />
      </mesh>
    </group>
  );
}

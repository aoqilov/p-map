// Qurilish maydoni (config.ts → CONSTRUCTION): bino hali qurilmoqda — xaritada tayyor bino o'rniga shu ko'rinadi.
// Beton karkas (`floorsBuilt` qavat plita + ustunlar, tepasida keyingi qavat armaturasi va qolip), old fasadda havoza va
// yashil to'r, ichkarida minorali kran (sekin buriladi, yuk ko'taradi), atrofida to'siq va banner, tuproq maydon,
// vagonchalar va material taxlamlari. Kechasi kranda qizil ogohlantirish chiroqlari yonadi.
import { useEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame, type ThreeEvent } from '@react-three/fiber';
import type { BuildingLook } from './config';
import { distToBoundary, distToPoly, inPoly } from './geo';
import { extrude, polyToShape } from './geometry';
import { V, canvasTexture, colored, mergeAll, prefersReducedMotion, rod, useAmbientFrames } from './modelKit';
import type { XY } from './projection';
import { ringOf, w } from './styledBuilding';
import type { Palette } from './theme';
import type { Building, Poly } from './types';

/** Qavat balandligi (m) — tayyor binodagi vitrina qavatlari bilan bir xil */
export const FLOOR_H = 4.3;
const SLAB = 0.35;
const FENCE_H = 2.2;
const YELLOW = '#f0b400';

const len2 = (a: XY, b: XY) => Math.hypot(b[0] - a[0], b[1] - a[1]);
const dirOf = (a: XY, b: XY) => Math.atan2(b[1] - a[1], b[0] - a[0]);
const isTap = (e: ThreeEvent<MouseEvent>) => e.delta < 6;

function rnd(seed: number) {
  let s = seed;
  return () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
}

/** Qurilish maydoni tepasi (pin uchun) */
export const siteTop = (floorsBuilt: number) => floorsBuilt * FLOOR_H + 2.5;

// ---------------------------------------------------------------- teksturalar

function dirtTexture() {
  const tex = canvasTexture(256, 256, (g, W, H) => {
    g.fillStyle = '#a68e6c'; g.fillRect(0, 0, W, H);
    const r = rnd(3);
    for (let i = 0; i < 5000; i++) {
      const v = 120 + r() * 70;
      g.fillStyle = `rgba(${v},${v - 18},${v - 40},0.45)`;
      g.fillRect(r() * W, r() * H, 1 + r() * 2, 1 + r() * 2);
    }
    // texnika izlari
    g.strokeStyle = 'rgba(80,64,44,0.35)'; g.lineWidth = 5;
    for (let k = 0; k < 3; k++) {
      g.beginPath(); g.moveTo(0, 40 + k * 80); g.bezierCurveTo(90, 10 + k * 90, 170, 120 + k * 40, 256, 60 + k * 80); g.stroke();
    }
  });
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(1 / 10, 1 / 10);
  return tex;
}

/** To'siq: profillangan list (tik qovurg'alar), tepasida oq tasma; u — metr (1 m da takrorlanadi), v — balandlik */
function fenceTexture() {
  const tex = canvasTexture(64, 128, (g, W, H) => {
    for (let x = 0; x < W; x++) {
      const v = 0.86 + 0.14 * Math.cos((x / W) * Math.PI * 2 * 5);
      g.fillStyle = `rgb(${Math.round(44 * v)},${Math.round(104 * v)},${Math.round(80 * v)})`;
      g.fillRect(x, 0, 1, H);
    }
    g.fillStyle = '#eef0ec'; g.fillRect(0, 0, W, Math.round(H * 0.08));
    g.fillStyle = 'rgba(0,0,0,0.25)'; g.fillRect(0, H - 6, W, 6);
  });
  tex.wrapS = THREE.RepeatWrapping;
  tex.repeat.set(1, 1 / FENCE_H);
  return tex;
}

/** Banner: chapda to'q blokda "PLAY PORT", o'ngda ochilish yili va izoh */
function bannerTexture(text: string) {
  const [title, rest] = text.includes('·') ? text.split('·').map((x) => x.trim()) : [text, ''];
  return canvasTexture(1024, 160, (g, W, H) => {
    g.fillStyle = '#ffffff'; g.fillRect(0, 0, W, H);
    g.fillStyle = '#6e4a3c'; g.fillRect(0, 0, 380, H);
    g.fillStyle = '#ffffff';
    g.font = '700 70px "Unbounded", "Onest", system-ui, sans-serif';
    g.textBaseline = 'middle'; g.textAlign = 'center';
    g.fillText(title, 190, H / 2 + 4, 350);
    g.fillStyle = '#1d2733'; g.textAlign = 'left';
    g.font = '600 50px "Onest", system-ui, sans-serif';
    g.fillText(rest, 412, H / 2 - 22, 590);
    g.fillStyle = '#5d6b80';
    g.font = '500 30px "Onest", system-ui, sans-serif';
    g.fillText("Qurilish ishlari olib borilmoqda", 412, H / 2 + 36, 590);
    g.fillStyle = '#f0b400'; g.fillRect(0, H - 10, W, 10);
  });
}

/** Xavfsizlik to'ri: yarim shaffof yashil, mayda katak */
function netTexture() {
  const tex = canvasTexture(64, 64, (g, W, H) => {
    g.clearRect(0, 0, W, H);
    g.fillStyle = 'rgba(46,125,80,0.62)'; g.fillRect(0, 0, W, H);
    g.fillStyle = 'rgba(30,90,55,0.9)';
    for (let k = 0; k < W; k += 8) { g.fillRect(k, 0, 1, H); g.fillRect(0, k, W, 1); }
  });
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(1 / 2, 1 / 2);
  return tex;
}

// ---------------------------------------------------------------- geometriya

/** Lokal ramka: a nuqtadan, u — qirra bo'ylab, t — tashqariga, h — balandlik */
const frameAt = (a: XY, dir: number, out: XY) => (s: number, t: number, h: number) =>
  w([a[0] + Math.cos(dir) * s + out[0] * t, a[1] + Math.sin(dir) * s + out[1] * t], h);

/** Quti: lokal X o'qi ma'lumot koordinatasidagi `yaw` yo'nalishiga (rotateY(θ): +X → (cos θ, sin θ)), markazi (p, y) */
function boxAt(sx: number, sy: number, sz: number, p: XY, y: number, yaw: number, hex: string) {
  const g = new THREE.BoxGeometry(sx, sy, sz);
  g.rotateY(yaw);
  g.translate(p[0], y, -p[1]);
  return colored(g, hex);
}

function siteParts(b: Building, look: BuildingLook, zone: Poly, floorsBuilt: number) {
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
  const f0 = look.frontEdge ?? 0;
  const fa = ring[f0], fDir = dirOf(ring[f0], ring[(f0 + 1) % n]), fOut = outN(f0);
  // Old fasad qatori: yo'nalishi 12° dan kam o'zgaradigan qirralar
  const front: number[] = [f0];
  for (let k = 1; k < n; k++) {
    const i = (f0 + k) % n;
    const d = Math.atan2(Math.sin(dirOf(ring[i], ring[(i + 1) % n]) - fDir), Math.cos(dirOf(ring[i], ring[(i + 1) % n]) - fDir));
    if (Math.abs(d) < THREE.MathUtils.degToRad(12)) front.push(i); else break;
  }
  const frontLen = front.reduce((s, i) => s + len2(ring[i], ring[(i + 1) % n]), 0);
  const top = floorsBuilt * FLOOR_H;
  const r = rnd(41);

  // Plitalar (har qavat) — bitta geometriya
  const shape = polyToShape(b.poly);
  const slabs: THREE.BufferGeometry[] = [];
  for (let k = 0; k <= floorsBuilt; k++) {
    const g = extrude(shape, k === 0 ? 0.3 : SLAB);
    g.rotateX(-Math.PI / 2);
    g.translate(0, k === 0 ? 0 : k * FLOOR_H - SLAB, 0);
    slabs.push(g);
  }
  const slab = mergeAll(slabs);

  // Ustunlar: old fasadga parallel to'r (8.4 m) + chet bo'ylab; tepada keyingi qavat — bir qismida ustun, qolganida armatura
  const cols: THREE.BufferGeometry[] = [], rebar: THREE.BufferGeometry[] = [], form: THREE.BufferGeometry[] = [];
  const at = (u: number, v: number): XY => [fa[0] + Math.cos(fDir) * u - fOut[0] * v, fa[1] + Math.sin(fDir) * u - fOut[1] * v];
  const posts: XY[] = [];
  for (let u = 4.2; u < 140; u += 8.4) for (let v = 4.2; v < 140; v += 8.4) {
    const p = at(u, v);
    if (inPoly(p, b.poly) && distToBoundary(p, b.poly) > 1.5) posts.push(p);
  }
  for (let i = 0; i < n; i++) {
    const p = ring[i], q = ring[(i + 1) % n], L = len2(p, q), nn = outN(i);
    const k = Math.max(1, Math.round(L / 7.5));
    for (let j = 0; j <= k; j++) {
      const t = j / k, c: XY = [p[0] + (q[0] - p[0]) * t - nn[0] * 0.45, p[1] + (q[1] - p[1]) * t - nn[1] * 0.45];
      if (!posts.some((o) => len2(o, c) < 3)) posts.push(c);
    }
  }
  // Keyingi qavat front tomondagi yarmida boshlangan: ustunlar to'liq, qolip devorlari
  const nextU = frontLen * 0.55;
  for (const p of posts) {
    cols.push(boxAt(0.6, top, 0.6, p, top / 2, fDir, '#bdb9b0'));
    const dx = p[0] - fa[0], dy = p[1] - fa[1];
    const u = dx * Math.cos(fDir) + dy * Math.sin(fDir);
    if (u < nextU) {
      cols.push(boxAt(0.6, FLOOR_H - SLAB, 0.6, p, top + (FLOOR_H - SLAB) / 2, fDir, '#c8c4bb'));
    } else if (r() < 0.8) {
      // armatura chiqib turibdi (zang rang)
      for (const [ox, oz] of [[-0.2, -0.2], [0.2, -0.2], [-0.2, 0.2], [0.2, 0.2]]) {
        rebar.push(boxAt(0.05, 1.6, 0.05, [p[0] + ox, p[1] + oz], top + 0.8, 0, '#7b4a2c'));
      }
    }
  }
  // Qolip: keyingi qavat plitasi ostidagi sariq faner panellar (front yarmida, chetdan chetga emas — ishlar davom etmoqda)
  for (let u = 3; u < nextU - 2; u += 6.2) for (let v = 3; v < 60; v += 6.2) {
    const c = at(u + 3, v + 3);
    if (!inPoly(c, b.poly) || distToBoundary(c, b.poly) < 3.5 || r() < 0.08) continue;
    form.push(boxAt(5.8, 0.18, 5.8, c, top + FLOOR_H - SLAB - 0.09, fDir, '#c99b52'));
  }
  // Tepada material: armatura bog'lamlari, blok poddonlari
  for (let k = 0; k < 9; k++) {
    const c = at(nextU + 6 + r() * (frontLen - nextU), 6 + r() * 40);
    if (!inPoly(c, b.poly) || distToBoundary(c, b.poly) < 3) continue;
    form.push(r() < 0.5 ? boxAt(6, 0.4, 0.8, c, top + 0.2, fDir + r(), '#6d4630') : boxAt(1.2, 1.0, 1.2, c, top + 0.5, fDir, '#9a9690'));
  }

  // Havoza va to'r: old fasad bo'ylab, 1 m tashqarida, yuqori plitadan 1.2 m baland
  const scaf: THREE.BufferGeometry[] = [];
  const netPos: number[] = [], netUv: number[] = [];
  let uAcc = 0;
  for (const i of front) {
    const p = ring[i], q = ring[(i + 1) % n], L = len2(p, q), nn = outN(i), d = dirOf(p, q);
    const F = frameAt(p, d, nn);
    const H = top + FLOOR_H * 0.6;
    for (let s = 0; s <= L + 0.01; s += 2.5) for (const t of [0.6, 1.6]) scaf.push(colored(rod(F(s, t, 0), F(s, t, H), 0.04, 4), '#9aa0a6'));
    for (let h = 2; h <= H; h += 2) {
      for (const t of [0.6, 1.6]) scaf.push(colored(rod(F(0, t, h), F(L, t, h), 0.035, 4), '#9aa0a6'));
      scaf.push(boxAt(L, 0.05, 1.0, [(p[0] + q[0]) / 2 + nn[0] * 1.1, (p[1] + q[1]) / 2 + nn[1] * 1.1], h, d, '#8c6a43')); // taxta yo'lak
    }
    // To'r: havozaning tashqi tomoni, pastki 2.5 m ochiq
    const a0 = F(0, 1.75, 2.5), a1 = F(L, 1.75, 2.5), a2 = F(L, 1.75, H), a3 = F(0, 1.75, H);
    for (const [v, uu, hh] of [[a0, uAcc, 2.5], [a1, uAcc + L, 2.5], [a2, uAcc + L, H], [a0, uAcc, 2.5], [a2, uAcc + L, H], [a3, uAcc, H]] as const) {
      netPos.push(v.x, v.y, v.z); netUv.push(uu, hh);
    }
    uAcc += L;
  }
  const net = new THREE.BufferGeometry();
  net.setAttribute('position', new THREE.Float32BufferAttribute(netPos, 3));
  net.setAttribute('uv', new THREE.Float32BufferAttribute(netUv, 2));
  net.computeVertexNormals();

  // To'siq: hudud chegarasi bo'ylab tik tasma; u — yoy uzunligi
  const zr = zone[0].slice(0, zone[0][0][0] === zone[0][zone[0].length - 1][0] && zone[0][0][1] === zone[0][zone[0].length - 1][1] ? -1 : undefined);
  const fpos: number[] = [], fuv: number[] = [];
  let fu = 0;
  for (let i = 0; i < zr.length; i++) {
    const p = zr[i], q = zr[(i + 1) % zr.length], L = len2(p, q);
    const v = [w(p, 0), w(q, 0), w(q, FENCE_H), w(p, FENCE_H)];
    const uv = [[fu, 0], [fu + L, 0], [fu + L, FENCE_H], [fu, FENCE_H]];
    for (const k of [0, 1, 2, 0, 2, 3]) { fpos.push(v[k].x, v[k].y, v[k].z); fuv.push(uv[k][0], uv[k][1]); }
    fu += L;
  }
  const fence = new THREE.BufferGeometry();
  fence.setAttribute('position', new THREE.Float32BufferAttribute(fpos, 3));
  fence.setAttribute('uv', new THREE.Float32BufferAttribute(fuv, 2));
  fence.computeVertexNormals();
  // To'siq ustunlari har 3 m da
  const fposts: THREE.BufferGeometry[] = [];
  for (let i = 0; i < zr.length; i++) {
    const p = zr[i], q = zr[(i + 1) % zr.length], L = len2(p, q);
    for (let s = 0; s < L; s += 3) {
      const c: XY = [p[0] + ((q[0] - p[0]) * s) / L, p[1] + ((q[1] - p[1]) * s) / L];
      fposts.push(boxAt(0.1, FENCE_H + 0.1, 0.1, c, (FENCE_H + 0.1) / 2, 0, '#3b3f44'));
    }
  }

  // Bannerlar: old fasadga eng ko'p qaragan va parking tomonga qaragan to'siq qirralarida
  let zArea = 0;
  for (let i = 0; i < zr.length; i++) { const p = zr[i], q = zr[(i + 1) % zr.length]; zArea += p[0] * q[1] - q[0] * p[1]; }
  const zOut = (i: number): XY => {
    const p = zr[i], q = zr[(i + 1) % zr.length], l = len2(p, q) || 1;
    const dx = (q[0] - p[0]) / l, dy = (q[1] - p[1]) / l;
    return zArea > 0 ? [dy, -dx] : [-dy, dx];
  };
  const banners: { a: XY; b: XY; out: XY }[] = [];
  const BW = 14;
  for (const want of [fOut, [-Math.cos(fDir), -Math.sin(fDir)] as XY]) {
    let best = -1, bs = 0.6;
    for (let i = 0; i < zr.length; i++) {
      const L = len2(zr[i], zr[(i + 1) % zr.length]), o = zOut(i);
      const sc = o[0] * want[0] + o[1] * want[1];
      if (L >= BW + 2 && sc > bs) { bs = sc; best = i; }
    }
    if (best < 0) continue;
    const p = zr[best], q = zr[(best + 1) % zr.length], L = len2(p, q), o = zOut(best);
    const m = 0.5, s0 = (L - BW) / 2;
    const P = (s: number): XY => [p[0] + ((q[0] - p[0]) * s) / L + o[0] * 0.04, p[1] + ((q[1] - p[1]) * s) / L + o[1] * 0.04];
    banners.push({ a: P(s0), b: P(s0 + BW), out: o });
    void m;
  }
  const banner = new THREE.BufferGeometry();
  {
    const pos: number[] = [], uv: number[] = [], nor: number[] = [];
    for (const bn of banners) {
      const v = [w(bn.a, 0.1), w(bn.b, 0.1), w(bn.b, FENCE_H - 0.1), w(bn.a, FENCE_H - 0.1)];
      const t = [[0, 0], [1, 0], [1, 1], [0, 1]];
      // Matn tashqaridan to'g'ri o'qilishi uchun: a→b chap tomoni tashqariga qaramasa — teskari
      const d: XY = [bn.b[0] - bn.a[0], bn.b[1] - bn.a[1]];
      // (a, b, b tepa) uchburchagi a→b ning o'ng tomoniga qaraydi; tashqaridan qaralganda a chapda bo'lsin
      const rightIsOut = d[1] * bn.out[0] - d[0] * bn.out[1] > 0;
      const order = rightIsOut ? [0, 1, 2, 0, 2, 3] : [0, 2, 1, 0, 3, 2];
      const uvs = rightIsOut ? t : [[1, 0], [0, 0], [0, 1], [1, 1]];
      for (const k of order) { pos.push(v[k].x, v[k].y, v[k].z); uv.push(uvs[k][0], uvs[k][1]); nor.push(bn.out[0], 0, -bn.out[1]); }
    }
    banner.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    banner.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
    banner.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
  }

  // Vagonchalar va taxlamlar: bino bilan to'siq orasidagi bo'sh joyda
  const props: THREE.BufferGeometry[] = [];
  const placed: XY[] = [];
  const items = ['cabin', 'cabin', 'pallet', 'pallet', 'rebar', 'pallet', 'cabin', 'pallet'] as const;
  let it = 0;
  for (let i = 0; i < zr.length && it < items.length; i++) {
    const p = zr[i], q = zr[(i + 1) % zr.length], L = len2(p, q), o = zOut(i), d = dirOf(p, q);
    for (let s = 4; s < L - 4 && it < items.length; s += 7) {
      const kind = items[it];
      const half = kind === 'cabin' ? 1.4 : 0.8;
      const c: XY = [p[0] + ((q[0] - p[0]) * s) / L - o[0] * (half + 0.5), p[1] + ((q[1] - p[1]) * s) / L - o[1] * (half + 0.5)];
      if (!inPoly(c, zone) || inPoly(c, b.poly) || distToPoly(c, b.poly) < half + 0.6 || placed.some((x) => len2(x, c) < 9)) continue;
      // To'siq bo'ylab banner oldiga qo'ymaymiz
      if (banners.some((bn) => len2([(bn.a[0] + bn.b[0]) / 2, (bn.a[1] + bn.b[1]) / 2], c) < BW / 2 + 3)) continue;
      placed.push(c);
      if (kind === 'cabin') {
        props.push(boxAt(6, 2.5, 2.4, c, 1.35, d, '#f2f3f4'));
        props.push(boxAt(6.2, 0.15, 2.6, c, 2.65, d, '#2f5f9a'));
        const wv: XY = [Math.cos(d), Math.sin(d)];
        for (const k of [-1.6, 0.6]) props.push(boxAt(1.0, 0.8, 2.45, [c[0] + wv[0] * k, c[1] + wv[1] * k], 1.7, d, '#3c4a58'));
      } else if (kind === 'pallet') {
        for (const [dx, dy] of [[0, 0], [1.3, 0], [0, 1.3]]) props.push(boxAt(1.1, 1.0, 1.1, [c[0] + dx * 0.9, c[1] + dy * 0.9], 0.5, d, dx || dy ? '#a9a59e' : '#b9b5ae'));
      } else {
        for (let k = 0; k < 3; k++) props.push(boxAt(6, 0.3, 0.9, [c[0], c[1]], 0.15 + k * 0.32, d + k * 0.04, '#6b432c'));
      }
      it++;
    }
  }

  // Kran joyi: old fasaddan 16 m ichkarida, uzunligining 42 foizida
  let crane = at(frontLen * 0.42, 16);
  if (!inPoly(crane, b.poly) || distToBoundary(crane, b.poly) < 3) {
    const xs = ring.map((p) => p[0]), ys = ring.map((p) => p[1]);
    crane = [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2];
  }

  return {
    slab, cols: mergeAll(cols), rebar: rebar.length ? mergeAll(rebar) : null, form: form.length ? mergeAll(form) : null,
    scaf: mergeAll(scaf), net, fence, fposts: mergeAll(fposts), banner, props: props.length ? mergeAll(props) : null,
    crane, craneYaw: fDir, top,
  };
}

// ---------------------------------------------------------------- kran

const MAST = 2.0;
const JIB = 46;
const COUNTER = 14;

/** Minora (qo'zg'almas): to'rtta asosiy quvur va har 2.5 m da diagonal panjara */
function mastGeometry(H: number) {
  const parts: THREE.BufferGeometry[] = [];
  const h = MAST / 2;
  const c = [V(-h, 0, -h), V(h, 0, -h), V(h, 0, h), V(-h, 0, h)];
  for (const p of c) parts.push(rod(p, V(p.x, H, p.z), 0.09, 4));
  for (let y = 0; y < H - 0.1; y += 2.5) {
    const y1 = Math.min(y + 2.5, H);
    for (let k = 0; k < 4; k++) {
      const a = c[k], b = c[(k + 1) % 4];
      parts.push(rod(V(a.x, y, a.z), V(b.x, y1, b.z), 0.05, 3));
      parts.push(rod(V(a.x, y1, a.z), V(b.x, y1, b.z), 0.05, 3));
    }
  }
  parts.push(new THREE.BoxGeometry(4.5, 1.2, 4.5).translate(0, 0.6, 0)); // poydevor
  return colored(mergeAll(parts), YELLOW);
}

/** Aylanuvchi qism (lokal: strela +X bo'ylab): strela, qarama-qarshi strela, yuklar, kabina, cho'qqi va tortqilar */
function slewGeometry() {
  const parts: THREE.BufferGeometry[] = [];
  const y0 = 0.9, y1 = 2.6;
  // Strela: uchburchak kesimli panjara
  const chords = [[0, y0, -0.8], [0, y0, 0.8], [0, y1, 0]];
  for (const [, y, z] of chords) parts.push(rod(V(-1, y, z), V(JIB, y, z), 0.07, 4));
  for (let x = 0; x < JIB; x += 2.3) {
    const x1 = Math.min(x + 2.3, JIB);
    parts.push(rod(V(x, y0, -0.8), V(x1, y1, 0), 0.04, 3));
    parts.push(rod(V(x, y0, 0.8), V(x1, y1, 0), 0.04, 3));
    parts.push(rod(V(x1, y0, -0.8), V(x1, y0, 0.8), 0.04, 3));
  }
  // Qarama-qarshi strela: tekis platforma, panjara, beton yuklar
  parts.push(new THREE.BoxGeometry(COUNTER, 0.35, 1.8).translate(-COUNTER / 2, y0, 0));
  for (const z of [-0.9, 0.9]) parts.push(rod(V(-COUNTER, y0 + 1, z), V(0, y0 + 1, z), 0.04, 3));
  const yellow = colored(mergeAll(parts), YELLOW);
  const weights: THREE.BufferGeometry[] = [];
  for (let k = 0; k < 4; k++) weights.push(new THREE.BoxGeometry(0.75, 2.2, 2.0).translate(-COUNTER + 0.6 + k * 0.8, y0 + 1.3, 0));
  // Burilish qismi, kabina, cho'qqi (A-ramka) va tortqi arqonlar
  const head = [new THREE.BoxGeometry(2.6, 0.9, 2.6).translate(0, 0.45, 0)];
  const apex = V(0, 8.5, 0);
  const frame = [rod(V(-0.9, y1, -0.9), apex, 0.08, 4), rod(V(0.9, y1, 0.9), apex, 0.08, 4), rod(V(-0.9, y1, 0.9), apex, 0.08, 4), rod(V(0.9, y1, -0.9), apex, 0.08, 4)];
  const ties = [rod(apex, V(JIB * 0.55, y1, 0), 0.03, 3), rod(apex, V(JIB * 0.95, y1, 0), 0.03, 3), rod(apex, V(-COUNTER + 0.5, y0 + 0.3, 0), 0.035, 3)];
  const cab = new THREE.BoxGeometry(1.8, 2.0, 1.6).translate(1.6, -0.6, 1.9);
  const cabGlass = new THREE.BoxGeometry(1.82, 1.0, 1.62).translate(1.6, -0.3, 1.9);
  return mergeAll([
    yellow,
    colored(mergeAll(weights), '#9b9a96'),
    colored(mergeAll(head), '#3a3d42'),
    colored(mergeAll(frame), YELLOW),
    colored(mergeAll(ties), '#2d2f33'),
    colored(cab, '#f2f2f2'),
    colored(cabGlass, '#2b3b4c'),
  ]);
}

function hookGeometry() {
  const trolley = colored(new THREE.BoxGeometry(1.4, 0.5, 1.8), '#3a3d42');
  const block = colored(new THREE.BoxGeometry(0.7, 0.9, 0.5).translate(0, -0.45, 0), YELLOW);
  // Yuk: po'lat to'sinlar bog'lami, ikki strop bilan
  const load = mergeAll([
    colored(new THREE.BoxGeometry(7, 0.35, 0.9).translate(0, -3.1, 0), '#6b432c'),
    colored(new THREE.BoxGeometry(7, 0.35, 0.9).translate(0, -2.75, 0.05), '#73492f'),
    rod(V(0, -0.9, 0), V(-2.8, -2.6, 0), 0.03, 3), rod(V(0, -0.9, 0), V(2.8, -2.6, 0), 0.03, 3),
  ].map((g, i) => (i < 2 ? g : colored(g, '#2d2f33'))));
  return { trolley, block, load };
}

// ---------------------------------------------------------------- komponent

let texCache: { dirt: THREE.Texture; fence: THREE.Texture; net: THREE.Texture } | null = null;

export function ConstructionSite({ b, look, zone, floorsBuilt, banner, pal, night, selected, onSelect }: {
  b: Building; look: BuildingLook; zone: Poly; floorsBuilt: number; banner: string; pal: Palette; night: boolean;
  selected: boolean; onSelect: (id: string) => void;
}) {
  const parts = useMemo(() => siteParts(b, look, zone, floorsBuilt), [b, look, zone, floorsBuilt]);
  const crane = useMemo(() => {
    const mastH = parts.top + 30;
    return {
      mastH, mast: mastGeometry(mastH), slew: slewGeometry(), hook: hookGeometry(),
      cable: new THREE.CylinderGeometry(0.03, 0.03, 1, 3, 1).translate(0, -0.5, 0), // 0 dan −1 gacha: scale.y = uzunlik
    };
  }, [parts.top]);
  const ground = useMemo(() => {
    const g = new THREE.ShapeGeometry(polyToShape(zone), 1); // UV = x, y metrda
    g.rotateX(-Math.PI / 2);
    return g;
  }, [zone]);
  const tex = (texCache ??= { dirt: dirtTexture(), fence: fenceTexture(), net: netTexture() });
  const bannerTex = useMemo(() => bannerTexture(banner), [banner]);
  useEffect(() => () => {
    for (const g of [parts.slab, parts.cols, parts.rebar, parts.form, parts.scaf, parts.net, parts.fence, parts.fposts, parts.banner, parts.props, ground]) g?.dispose();
    for (const g of [crane.mast, crane.slew, crane.hook.trolley, crane.hook.block, crane.hook.load, crane.cable]) g.dispose();
    bannerTex.dispose();
  }, [parts, crane, ground, bannerTex]);

  // Kran: strela sekin u yoqdan bu yoqqa buriladi, aravacha yuradi, yuk ko'tariladi/tushadi
  const animate = !prefersReducedMotion();
  useAmbientFrames(animate);
  const slew = useRef<THREE.Group>(null!);
  const trolley = useRef<THREE.Group>(null!);
  const cable = useRef<THREE.Mesh>(null!);
  const hook = useRef<THREE.Group>(null!);
  const t = useRef(17);
  const pose = (time: number) => {
    const a = parts.craneYaw + 0.55 + 0.75 * Math.sin(time * 0.045) + 0.2 * Math.sin(time * 0.11);
    const r = 24 + 14 * Math.sin(time * 0.07 + 1.3);
    const drop = THREE.MathUtils.clamp(crane.mastH - parts.top - 8 + 6 * Math.sin(time * 0.09), 6, crane.mastH - 4);
    slew.current.rotation.y = a;
    trolley.current.position.x = r;
    cable.current.scale.y = drop;
    hook.current.position.y = -drop;
  };
  useEffect(() => { pose(t.current); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useFrame((_, dt) => {
    if (!animate) return;
    t.current += Math.min(dt, 0.1);
    pose(t.current);
  });

  // Tanlanganda iliq tus (butunlay bo'yalmaydi — karkas ko'rinib tursin)
  // Kechasi beton biroz to'qroq (boshqa binolar bilan bir xil yorug'likda ko'rinsin)
  const shade = (hex: string) => '#' + new THREE.Color(hex).multiply(new THREE.Color(night ? '#a3a8ae' : '#ffffff'))
    .lerp(new THREE.Color(pal.selected), selected ? 0.3 : 0).getHexString();
  const concrete = shade('#ffffff');
  const [cx, cy] = parts.crane;
  const lampMat = useMemo(() => new THREE.MeshBasicMaterial({ color: '#ff2a2a', toneMapped: false }), []);
  useEffect(() => () => lampMat.dispose(), [lampMat]);
  return (
    <group onClick={(e) => { if (!isTap(e)) return; e.stopPropagation(); onSelect(b.id); }}>
      <mesh geometry={ground} position-y={0.03} receiveShadow>
        <meshStandardMaterial map={tex.dirt} color={night ? '#8d8a85' : '#ffffff'} roughness={1} polygonOffset polygonOffsetFactor={-1} />
      </mesh>
      <mesh geometry={parts.slab} castShadow receiveShadow>
        <meshStandardMaterial color={shade('#c9c5bc')} roughness={0.95} />
      </mesh>
      <mesh geometry={parts.cols} castShadow receiveShadow>
        <meshStandardMaterial vertexColors color={concrete} roughness={0.95} />
      </mesh>
      {parts.rebar && (
        <mesh geometry={parts.rebar}>
          <meshStandardMaterial vertexColors roughness={0.8} />
        </mesh>
      )}
      {parts.form && (
        <mesh geometry={parts.form} castShadow receiveShadow>
          <meshStandardMaterial vertexColors roughness={0.85} />
        </mesh>
      )}
      <mesh geometry={parts.scaf} castShadow>
        <meshStandardMaterial vertexColors metalness={0.3} roughness={0.6} />
      </mesh>
      <mesh geometry={parts.net}>
        <meshStandardMaterial map={tex.net} transparent depthWrite={false} side={THREE.DoubleSide} roughness={0.9} />
      </mesh>
      <mesh geometry={parts.fence} castShadow receiveShadow>
        <meshStandardMaterial map={tex.fence} roughness={0.7} metalness={0.2} side={THREE.DoubleSide} />
      </mesh>
      <mesh geometry={parts.fposts}>
        <meshStandardMaterial vertexColors roughness={0.7} />
      </mesh>
      <mesh geometry={parts.banner}>
        <meshStandardMaterial map={bannerTex} roughness={0.8} emissiveMap={bannerTex} emissive="#ffffff" emissiveIntensity={night ? 0.35 : 0} />
      </mesh>
      {parts.props && (
        <mesh geometry={parts.props} castShadow receiveShadow>
          <meshStandardMaterial vertexColors roughness={0.75} />
        </mesh>
      )}
      {/* Kran */}
      <group position={[cx, 0, -cy]}>
        <mesh geometry={crane.mast} castShadow>
          <meshStandardMaterial vertexColors roughness={0.6} />
        </mesh>
        <group ref={slew} position-y={crane.mastH}>
          <mesh geometry={crane.slew} castShadow>
            <meshStandardMaterial vertexColors roughness={0.6} />
          </mesh>
          {/* Ogohlantirish chiroqlari (cho'qqi va strela uchi) */}
          <mesh position={[0, 8.7, 0]} material={lampMat}><sphereGeometry args={[0.35, 8, 6]} /></mesh>
          <mesh position={[JIB, 2.9, 0]} material={lampMat}><sphereGeometry args={[0.3, 8, 6]} /></mesh>
          <group ref={trolley} position-y={0.6}>
            <mesh geometry={crane.hook.trolley}>
              <meshStandardMaterial vertexColors roughness={0.6} />
            </mesh>
            {/* Arqon: uzunligi 1 m, scale.y bilan cho'ziladi */}
            <mesh ref={cable} geometry={crane.cable}>
              <meshStandardMaterial color="#25272b" />
            </mesh>
            <group ref={hook}>
              <mesh geometry={crane.hook.block} castShadow>
                <meshStandardMaterial vertexColors roughness={0.6} />
              </mesh>
              <mesh geometry={crane.hook.load} castShadow>
                <meshStandardMaterial vertexColors roughness={0.7} />
              </mesh>
            </group>
          </group>
        </group>
      </group>
    </group>
  );
}

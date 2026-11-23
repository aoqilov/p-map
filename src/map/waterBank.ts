// Suv qirg'og'i: chetidagi tosh (coping) va suvgacha tushadigan devor. Teksturalar ham shu yerda.
import * as THREE from 'three';
import { inPoly } from './geo';
import { canvasTexture } from './modelKit';
import type { XY } from './projection';
import type { Poly } from './types';

/**
 * Har bir halqa (tashqi chegara va orollar) uchun:
 *  - `coping`: suv chetidan `width` ichkariga kirgan tosh tasma (tepasi `top` balandlikda) + quruqlik tomondagi kichik yon devor
 *  - `wall`: tosh tasmaning suv tomonidagi chetidan `bottom` gacha tushadigan devor; pastki qismi nam (to'qroq) — vertex rang
 * UV metrda: u — qirg'oq bo'ylab, v — balandlik (devor) yoki 0..1 (tosh tasma eni).
 */
export function bankGeometry(poly: Poly, opts: { width: number; top: number; level: number; bottom: number }) {
  const { width, top, level, bottom } = opts;
  const cp = { pos: [] as number[], nor: [] as number[], uv: [] as number[] };
  const wl = { pos: [] as number[], nor: [] as number[], uv: [] as number[], col: [] as number[] };
  const w = (p: XY, y: number) => new THREE.Vector3(p[0], y, -p[1]);

  const quad = (
    buf: { pos: number[]; nor: number[]; uv: number[]; col?: number[] },
    v: THREE.Vector3[], n: THREE.Vector3, uvs: number[][], shade?: number[],
  ) => {
    const face = new THREE.Vector3().crossVectors(v[1].clone().sub(v[0]), v[2].clone().sub(v[0]));
    const order = face.dot(n) >= 0 ? [0, 1, 2, 0, 2, 3] : [0, 2, 1, 0, 3, 2];
    for (const k of order) {
      buf.pos.push(v[k].x, v[k].y, v[k].z);
      buf.nor.push(n.x, n.y, n.z);
      buf.uv.push(uvs[k][0], uvs[k][1]);
      if (buf.col && shade) buf.col.push(shade[k], shade[k], shade[k]);
    }
  };

  // Devor qatorlari: balandlik → rang ko'paytmasi (suv chizig'i atrofida nam, to'q tasma)
  const rows: [number, number][] = [[top, 1], [level + 0.16, 0.92], [level + 0.02, 0.6], [bottom, 0.5]];

  for (const raw of poly) {
    const closed = raw.length > 1 && raw[0][0] === raw[raw.length - 1][0] && raw[0][1] === raw[raw.length - 1][1];
    const ring = closed ? raw.slice(0, -1) : raw;
    const n = ring.length;
    if (n < 3) continue;
    const left = (a: XY, b: XY): XY => {
      const l = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
      return [-(b[1] - a[1]) / l, (b[0] - a[0]) / l];
    };
    // Suv chap tomondami? Eng uzun qirra o'rtasidan sinaymiz
    let bi = 0, bl = 0;
    for (let i = 0; i < n; i++) {
      const l = Math.hypot(ring[(i + 1) % n][0] - ring[i][0], ring[(i + 1) % n][1] - ring[i][1]);
      if (l > bl) { bl = l; bi = i; }
    }
    const nl = left(ring[bi], ring[(bi + 1) % n]);
    const probe: XY = [(ring[bi][0] + ring[(bi + 1) % n][0]) / 2 + nl[0] * 0.05, (ring[bi][1] + ring[(bi + 1) % n][1]) / 2 + nl[1] * 0.05];
    const s = inPoly(probe, poly) ? 1 : -1; // +1: suv chapda

    const inner: XY[] = ring.map((p, i) => {
      const n1 = left(ring[(i - 1 + n) % n], p), n2 = left(p, ring[(i + 1) % n]);
      let mx = n1[0] + n2[0], my = n1[1] + n2[1];
      const ml = Math.hypot(mx, my);
      if (ml < 1e-6) { mx = n2[0]; my = n2[1]; } else { mx /= ml; my /= ml; }
      const k = Math.min(1 / Math.max(mx * n2[0] + my * n2[1], 0.4), 2.5);
      return [p[0] + mx * width * k * s, p[1] + my * width * k * s];
    });

    let u = 0;
    for (let i = 0; i < n; i++) {
      const j = (i + 1) % n;
      const len = Math.hypot(ring[j][0] - ring[i][0], ring[j][1] - ring[i][1]);
      if (len < 1e-4) continue;
      const u1 = u + len;
      const e = left(ring[i], ring[j]);
      const toWater = new THREE.Vector3(e[0] * s, 0, -e[1] * s);
      // Tosh tasma tepasi
      quad(cp, [w(ring[i], top), w(ring[j], top), w(inner[j], top), w(inner[i], top)], new THREE.Vector3(0, 1, 0),
        [[u, 0], [u1, 0], [u1, 1], [u, 1]]);
      // Quruqlik tomondagi yon (yerdan tosh tepasigacha)
      quad(cp, [w(ring[i], -0.02), w(ring[j], -0.02), w(ring[j], top), w(ring[i], top)], toWater.clone().negate(),
        [[u, 0], [u1, 0], [u1, 1], [u, 1]]);
      // Suvga qaragan devor, qatorma-qator
      for (let r = 0; r < rows.length - 1; r++) {
        const [ya, ca] = rows[r], [yb, cb] = rows[r + 1];
        quad(wl, [w(inner[i], ya), w(inner[j], ya), w(inner[j], yb), w(inner[i], yb)], toWater,
          [[u, ya], [u1, ya], [u1, yb], [u, yb]], [ca, ca, cb, cb]);
      }
      u = u1;
    }
  }

  const make = (b: { pos: number[]; nor: number[]; uv: number[]; col?: number[] }) => {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(b.pos, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(b.nor, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(b.uv, 2));
    if (b.col) g.setAttribute('color', new THREE.Float32BufferAttribute(b.col, 3));
    g.computeBoundingSphere();
    return g;
  };
  return { coping: make(cp), wall: make(wl) };
}

/** Tosh devor: yotiq bloklar, qator-qator siljigan (UV metrda: 2.4 × 1.2 m da takrorlanadi) */
export function masonryTexture() {
  const tex = canvasTexture(256, 128, (g, w, h) => {
    g.fillStyle = 'rgb(105,105,105)'; // chok
    g.fillRect(0, 0, w, h);
    let seed = 11;
    const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
    const rowH = h / 4; // 0.3 m
    for (let r = 0; r < 4; r++) {
      let x = r % 2 ? -rowH * 1.1 : 0;
      while (x < w) {
        const bw = rowH * (1.4 + rnd() * 1.4);
        const v = 175 + rnd() * 60;
        g.fillStyle = `rgb(${v},${v * 0.98},${v * 0.95})`;
        // Takrorlanganda chok uzilmasin: chetdan chiqqan blokni boshida ham chizamiz
        for (const ox of [0, -w]) g.fillRect(x + ox + 1.5, r * rowH + 1.5, bw - 3, rowH - 3);
        x += bw;
      }
    }
    for (let i = 0; i < 1400; i++) { // dona-dona sirt
      const v = 120 + rnd() * 120;
      g.fillStyle = `rgba(${v},${v},${v},0.25)`;
      g.fillRect(rnd() * w, rnd() * h, 1, 1);
    }
  });
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(1 / 2.4, 1 / 1.2);
  return tex;
}

/** Basseyn devori: 25 sm li kafel (UV metrda: 1 × 1 m da takrorlanadi) */
export function tileTexture() {
  const tex = canvasTexture(128, 128, (g, w, h) => {
    g.fillStyle = 'rgb(200,206,210)'; // chok
    g.fillRect(0, 0, w, h);
    const t = w / 4;
    for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) {
      const v = 238 + ((i * 7 + j * 3) % 5) * 3;
      g.fillStyle = `rgb(${v},${v},${v})`;
      g.fillRect(i * t + 1.5, j * t + 1.5, t - 3, t - 3);
    }
  });
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  return tex;
}

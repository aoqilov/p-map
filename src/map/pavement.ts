// Yo'l qoplamasi: tosh plitka teksturasi va bordyur (yo'l cheti) geometriyasi
import * as THREE from 'three';
import { inPoly } from './geo';
import { canvasTexture } from './modelKit';
import type { XY } from './projection';
import type { MultiPoly } from './types';

/**
 * Tosh plitka (bruschatka): notekis shakldagi och kulrang toshlar, oralarida to'q chok.
 * Voronoi (Worley) usulida chiziladi va chetlari ulanadigan qilib qurilgan — choksiz takrorlanadi.
 * Toshlar yo'nalishsiz, shuning uchun egri yo'llarda ham tabiiy ko'rinadi.
 * Rangni material beradi (theme.ts → roadTop), tekstura uni toshma-tosh o'zgartiradi. UV = metr.
 */
export function stoneTexture() {
  const SIZE = 512;
  const GRID = 12; // bir takrorlanishda 12×12 tosh
  const TILE_M = 4; // takrorlanish o'lchami, m → tosh ~0.33 m
  const cs = SIZE / GRID;
  let seed = 7;
  const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  const sx: number[] = [], sy: number[] = [], tone: number[] = [], tint: number[] = [];
  for (let j = 0; j < GRID; j++) for (let i = 0; i < GRID; i++) {
    sx.push((i + 0.15 + rnd() * 0.7) * cs);
    sy.push((j + 0.15 + rnd() * 0.7) * cs);
    tone.push(0.8 + rnd() * 0.17); // har tosh o'z yorqinligida
    tint.push((rnd() - 0.5) * 0.025); // juda ozgina iliq/sovuq granit tusi
  }
  const tex = canvasTexture(SIZE, SIZE, (g) => {
    const img = g.createImageData(SIZE, SIZE);
    const d = img.data;
    const JOINT = 3.2; // chok qalinligi, px
    for (let y = 0; y < SIZE; y++) {
      for (let x = 0; x < SIZE; x++) {
        const cx = Math.floor(x / cs), cy = Math.floor(y / cs);
        let f1 = Infinity, f2 = Infinity, id = 0;
        for (let oy = -1; oy <= 1; oy++) for (let ox = -1; ox <= 1; ox++) {
          const gx = (cx + ox + GRID) % GRID, gy = (cy + oy + GRID) % GRID;
          const k = gy * GRID + gx;
          // halqa (tor) bo'ylab o'ralgan masofa — tekstura choksiz takrorlanadi
          let dx = sx[k] - x, dy = sy[k] - y;
          if (dx > SIZE / 2) dx -= SIZE; else if (dx < -SIZE / 2) dx += SIZE;
          if (dy > SIZE / 2) dy -= SIZE; else if (dy < -SIZE / 2) dy += SIZE;
          const dist = Math.hypot(dx, dy);
          if (dist < f1) { f2 = f1; f1 = dist; id = k; } else if (dist < f2) f2 = dist;
        }
        const edge = (f2 - f1) / 2; // eng yaqin chegaragacha masofa (px)
        const n = (Math.random() - 0.5) * 0.05;
        let r: number, gg: number, b: number;
        if (edge < JOINT) {
          const v = 0.42 + n; // chok
          r = v; gg = v; b = v * 1.02;
        } else {
          const bevel = Math.min(1, 0.86 + ((edge - JOINT) / 7) * 0.14); // tosh chetlari biroz to'qroq — hajm beradi
          const v = tone[id] * bevel + n;
          r = v * (1 + tint[id]); gg = v; b = v * (1 - tint[id]);
        }
        const o = (y * SIZE + x) * 4;
        d[o] = Math.min(255, r * 255); d[o + 1] = Math.min(255, gg * 255); d[o + 2] = Math.min(255, b * 255); d[o + 3] = 255;
      }
    }
    g.putImageData(img, 0, 0);
  });
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(1 / TILE_M, 1 / TILE_M);
  return tex;
}

/** Bordyur: och beton, har 1 m da ingichka chok (u — metrda) */
export function curbTexture() {
  const tex = canvasTexture(64, 16, (g, w, h) => {
    g.fillStyle = 'rgb(245,245,245)';
    g.fillRect(0, 0, w, h);
    for (let i = 0; i < 120; i++) {
      const v = 205 + Math.random() * 50;
      g.fillStyle = `rgb(${v},${v},${v})`;
      g.fillRect(Math.random() * w, Math.random() * h, 1, 1);
    }
    g.fillStyle = 'rgb(150,150,150)';
    g.fillRect(w - 2, 0, 2, h); // bloklar orasidagi chok
  });
  tex.wrapS = THREE.RepeatWrapping;
  return tex;
}

/**
 * Asfalt chegarasi bo'ylab bordyur: asfaltdan tashqarida (maysa tomonda), `width` eni, asfaltdan `height` baland.
 * Har bir halqada asfalt qaysi tomonda ekanini aniqlaymiz — tashqi chegarada ham, teshiklarda (kvartallarda) ham to'g'ri chiqadi.
 * Hammasi bitta BufferGeometry (bitta draw call).
 */
export function curbGeometry(roads: MultiPoly, opts: { width: number; height: number; base: number }) {
  const { width, height, base } = opts;
  const top = base + height;
  const pos: number[] = [], nor: number[] = [], uv: number[] = [];
  const w = (p: XY, y: number) => new THREE.Vector3(p[0], y, -p[1]);

  /** To'rtburchak: kerakli normal tomonga qaratib ikki uchburchak */
  const quad = (a: THREE.Vector3, b: THREE.Vector3, c: THREE.Vector3, d: THREE.Vector3, n: THREE.Vector3, uvs: number[][]) => {
    const face = new THREE.Vector3().crossVectors(b.clone().sub(a), c.clone().sub(a));
    const order = face.dot(n) >= 0 ? [0, 1, 2, 0, 2, 3] : [0, 2, 1, 0, 3, 2];
    const v = [a, b, c, d];
    for (const k of order) {
      pos.push(v[k].x, v[k].y, v[k].z);
      nor.push(n.x, n.y, n.z);
      uv.push(uvs[k][0], uvs[k][1]);
    }
  };

  for (const poly of roads) {
    for (const raw of poly) {
      const ring = raw.length > 1 && raw[0][0] === raw[raw.length - 1][0] && raw[0][1] === raw[raw.length - 1][1] ? raw.slice(0, -1) : raw;
      const n = ring.length;
      if (n < 3) continue;
      const leftNormal = (a: XY, b: XY): XY => {
        const l = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
        return [-(b[1] - a[1]) / l, (b[0] - a[0]) / l];
      };

      // Asfalt chap tomondami? Eng uzun qirraning o'rtasidan sinab ko'ramiz
      let bi = 0, bl = 0;
      for (let i = 0; i < n; i++) {
        const l = Math.hypot(ring[(i + 1) % n][0] - ring[i][0], ring[(i + 1) % n][1] - ring[i][1]);
        if (l > bl) { bl = l; bi = i; }
      }
      const [a0, b0] = [ring[bi], ring[(bi + 1) % n]];
      const nl = leftNormal(a0, b0);
      const mid: XY = [(a0[0] + b0[0]) / 2 + nl[0] * 0.05, (a0[1] + b0[1]) / 2 + nl[1] * 0.05];
      const s = inPoly(mid, poly) ? -1 : 1; // bordyur asfaltga qarama-qarshi tomonga

      // Tashqi chiziq: burchaklarda "miter" bilan surilgan (o'tkir burchakda cheklangan)
      const outer: XY[] = ring.map((p, i) => {
        const n1 = leftNormal(ring[(i - 1 + n) % n], p), n2 = leftNormal(p, ring[(i + 1) % n]);
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
        const out = new THREE.Vector3(outer[i][0] - ring[i][0], 0, -(outer[i][1] - ring[i][1])).normalize();
        // Tepa
        quad(w(ring[i], top), w(ring[j], top), w(outer[j], top), w(outer[i], top), new THREE.Vector3(0, 1, 0),
          [[u, 0], [u1, 0], [u1, 1], [u, 1]]);
        // Maysa tomoni (yerdan tepagacha)
        quad(w(outer[i], 0), w(outer[j], 0), w(outer[j], top), w(outer[i], top), out,
          [[u, 0], [u1, 0], [u1, 1], [u, 1]]);
        // Asfalt tomoni (asfalt sathidan tepagacha)
        quad(w(ring[i], base), w(ring[j], base), w(ring[j], top), w(ring[i], top), out.clone().negate(),
          [[u, 0], [u1, 0], [u1, 1], [u, 1]]);
        u = u1;
      }
    }
  }

  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.computeBoundingSphere();
  return g;
}

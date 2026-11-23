// Suv "maydoni" teksturasi: har bir piksel uchun qirg'oqqacha masofa (R) va oqim yo'nalishi (G, B).
// Shader shundan sayoz→chuqur rangni, qirg'oqdagi chiziqni va ariqdagi oqimni oladi.
// Brauzerda xarita ochilganda bir marta hisoblanadi (5 ta suv uchun jami ~15 ms), keyin GPU'da turadi.
import * as THREE from 'three';
import type { Poly } from './types';

/** R kanali: masofa + FIELD_OFFSET (qirg'oqdan tashqarida 2 m gacha manfiy masofa ham saqlanadi) */
export const FIELD_OFFSET = 2;

export interface WaterField {
  tex: THREE.DataTexture;
  /** Tekstura qoplagan to'rtburchak, metrda: [minX, minY, eni, bo'yi] */
  rect: [number, number, number, number];
  /** Suv ichidagi eng katta masofa, m */
  maxDist: number;
  /** R kanalidagi 1.0 = shuncha metr (maxDist + FIELD_OFFSET) */
  range: number;
}

export interface DistanceGrid {
  /** Ishorali masofa: suvda musbat (qirg'oqqacha), tashqarida manfiy (−FIELD_OFFSET gacha) */
  dist: Float32Array;
  inside: Uint8Array;
  W: number;
  H: number;
  cell: number;
  x0: number;
  y0: number;
  maxDist: number;
  /** Istalgan nuqtada masofa (bilinear), m */
  sample(x: number, y: number): number;
  /** Masofa gradienti — qirg'oqdan suv ichkarisiga qaragan birlik vektor */
  inward(x: number, y: number): [number, number];
}

/** Suv polygoni uchun masofa to'ri (CPU'da). Suv shaderi ham, baliqlar ham shundan foydalanadi */
export function distanceGrid(poly: Poly): DistanceGrid {
  const ring = poly[0];
  const xs = ring.map((p) => p[0]), ys = ring.map((p) => p[1]);
  const pad = 1;
  const x0 = Math.min(...xs) - pad, y0 = Math.min(...ys) - pad;
  const spanX = Math.max(...xs) + pad - x0, spanY = Math.max(...ys) + pad - y0;
  // Eng uzun tomoni ≤160 piksel (katta hovuzda ~0.8 m/piksel): masofa silliq o'zgaradi, GPU uni oraliqda aniq to'ldiradi.
  // Tashqi piksellarga manfiy masofa yoziladi, shunda qirg'oq chizig'i yirik to'rda ham aniq joyida chiqadi.
  const cell = Math.max(0.4, Math.max(spanX, spanY) / 160);
  const W = Math.ceil(spanX / cell), H = Math.ceil(spanY / cell);

  // Qirralar oldindan tekis massivlarga: ichki siklda obyekt yaratilmaydi, Math.hypot yo'q (u sekin) —
  // kvadrat masofa bilan ishlab, ildiz bir marta olinadi. Ichkarilik: barcha halqalar bo'yicha juft-toq qoida (orollar ham).
  const E: number[] = [];
  for (const r of poly) for (let e = 0; e < r.length - 1; e++) {
    const [ax, ay] = r[e], [bx, by] = r[e + 1];
    const dx = bx - ax, dy = by - ay, l2 = dx * dx + dy * dy;
    if (l2 > 1e-12) E.push(ax, ay, dx, dy, 1 / l2, by);
  }
  const edges = new Float64Array(E);
  const nE = edges.length / 6;

  const dist = new Float32Array(W * H);
  const inside = new Uint8Array(W * H);
  let maxDist = 0.01;
  for (let j = 0; j < H; j++) {
    const py = y0 + (j + 0.5) * cell;
    for (let i = 0; i < W; i++) {
      const px = x0 + (i + 0.5) * cell;
      let best = Infinity, odd = false;
      for (let e = 0; e < nE; e++) {
        const o = e * 6;
        const ax = edges[o], ay = edges[o + 1], dx = edges[o + 2], dy = edges[o + 3], by = edges[o + 5];
        let t = ((px - ax) * dx + (py - ay) * dy) * edges[o + 4];
        t = t < 0 ? 0 : t > 1 ? 1 : t;
        const qx = px - ax - t * dx, qy = py - ay - t * dy;
        const d2 = qx * qx + qy * qy;
        if (d2 < best) best = d2;
        if ((ay > py) !== (by > py) && px < (dx * (py - ay)) / dy + ax) odd = !odd;
      }
      const d = Math.sqrt(best), k = j * W + i;
      if (odd) {
        inside[k] = 1;
        dist[k] = d;
        if (d > maxDist) maxDist = d;
      } else {
        dist[k] = -Math.min(d, FIELD_OFFSET);
      }
    }
  }

  const sample = (x: number, y: number) => {
    const fx = (x - x0) / cell - 0.5, fy = (y - y0) / cell - 0.5;
    const i = Math.max(0, Math.min(W - 2, Math.floor(fx))), j = Math.max(0, Math.min(H - 2, Math.floor(fy)));
    const u = Math.max(0, Math.min(1, fx - i)), v = Math.max(0, Math.min(1, fy - j));
    const k = j * W + i;
    return (dist[k] * (1 - u) + dist[k + 1] * u) * (1 - v) + (dist[k + W] * (1 - u) + dist[k + W + 1] * u) * v;
  };
  const inward = (x: number, y: number): [number, number] => {
    const h = cell;
    const gx = sample(x + h, y) - sample(x - h, y), gy = sample(x, y + h) - sample(x, y - h);
    const l = Math.hypot(gx, gy) || 1;
    return [gx / l, gy / l];
  };
  return { dist, inside, W, H, cell, x0, y0, maxDist, sample, inward };
}

/**
 * @param flow — ariq uchun: oqim manbadan (shimoliy uch yoki `reverse` bo'lsa janubiy) quyi tomonga
 */
export function buildWaterField(poly: Poly, flow?: { reverse: boolean }): WaterField {
  const { dist, inside, W, H, cell, x0, y0, maxDist } = distanceGrid(poly);

  // Oqim: manbadan "suv yo'li bo'ylab" masofa (Dijkstra), uning gradienti — oqim yo'nalishi
  const fx = new Float32Array(W * H), fy = new Float32Array(W * H);
  if (flow) {
    let src = -1;
    for (let k = 0; k < W * H; k++) {
      if (!inside[k]) continue;
      if (src < 0) { src = k; continue; }
      const j = Math.floor(k / W), js = Math.floor(src / W);
      if (flow.reverse ? j < js : j > js) src = k;
    }
    const geo = geodesic(inside, W, H, src);
    for (let j = 0; j < H; j++) {
      for (let i = 0; i < W; i++) {
        const k = j * W + i;
        if (!inside[k]) continue;
        const g = (di: number, dj: number) => {
          const ii = i + di, jj = j + dj;
          return ii >= 0 && jj >= 0 && ii < W && jj < H && inside[jj * W + ii] ? geo[jj * W + ii] : geo[k];
        };
        fx[k] = g(1, 0) - g(-1, 0);
        fy[k] = g(0, 1) - g(0, -1);
      }
    }
    // Ikki marta tekislash — burilishlarda yo'nalish silliq o'zgarsin
    for (let pass = 0; pass < 2; pass++) {
      const ax = fx.slice(), ay = fy.slice();
      for (let j = 1; j < H - 1; j++) for (let i = 1; i < W - 1; i++) {
        const k = j * W + i;
        if (!inside[k]) continue;
        let sx = 0, sy = 0;
        for (let dj = -1; dj <= 1; dj++) for (let di = -1; di <= 1; di++) {
          const kk = k + dj * W + di;
          if (inside[kk]) { sx += ax[kk]; sy += ay[kk]; }
        }
        fx[k] = sx; fy[k] = sy;
      }
    }
  }

  const range = maxDist + FIELD_OFFSET;
  const data = new Uint8Array(W * H * 4);
  for (let k = 0; k < W * H; k++) {
    data[k * 4] = Math.round(((dist[k] + FIELD_OFFSET) / range) * 255);
    const l = Math.hypot(fx[k], fy[k]) || 1;
    data[k * 4 + 1] = Math.round((0.5 + 0.5 * (fx[k] / l)) * 255);
    data[k * 4 + 2] = Math.round((0.5 + 0.5 * (fy[k] / l)) * 255);
    data[k * 4 + 3] = 255;
  }
  const tex = new THREE.DataTexture(data, W, H, THREE.RGBAFormat);
  tex.minFilter = tex.magFilter = THREE.LinearFilter;
  tex.wrapS = tex.wrapT = THREE.ClampToEdgeWrapping;
  tex.needsUpdate = true;
  return { tex, rect: [x0, y0, W * cell, H * cell], maxDist, range };
}

/** 8 qo'shnili Dijkstra: ichki piksellar bo'ylab manbadan masofa (piksel birligida) */
function geodesic(inside: Uint8Array, W: number, H: number, src: number) {
  const d = new Float32Array(W * H).fill(Infinity);
  const heap: number[] = [];
  const push = (k: number) => {
    heap.push(k);
    let i = heap.length - 1;
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (d[heap[p]] <= d[heap[i]]) break;
      [heap[p], heap[i]] = [heap[i], heap[p]];
      i = p;
    }
  };
  const pop = () => {
    const top = heap[0], last = heap.pop()!;
    if (heap.length) {
      heap[0] = last;
      let i = 0;
      for (;;) {
        const l = 2 * i + 1, r = l + 1;
        let m = i;
        if (l < heap.length && d[heap[l]] < d[heap[m]]) m = l;
        if (r < heap.length && d[heap[r]] < d[heap[m]]) m = r;
        if (m === i) break;
        [heap[m], heap[i]] = [heap[i], heap[m]];
        i = m;
      }
    }
    return top;
  };
  d[src] = 0;
  push(src);
  const steps: [number, number, number][] = [
    [1, 0, 1], [-1, 0, 1], [0, 1, 1], [0, -1, 1], [1, 1, Math.SQRT2], [1, -1, Math.SQRT2], [-1, 1, Math.SQRT2], [-1, -1, Math.SQRT2],
  ];
  while (heap.length) {
    const k = pop();
    const i = k % W, j = Math.floor(k / W);
    for (const [di, dj, w] of steps) {
      const ii = i + di, jj = j + dj;
      if (ii < 0 || jj < 0 || ii >= W || jj >= H) continue;
      const kk = jj * W + ii;
      if (!inside[kk] || d[k] + w >= d[kk]) continue;
      d[kk] = d[k] + w;
      push(kk);
    }
  }
  for (let k = 0; k < W * H; k++) if (!Number.isFinite(d[k])) d[k] = 0;
  return d;
}

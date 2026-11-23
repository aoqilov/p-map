// Metrdagi tekis geometriya yordamchilari (build skript va brauzer uchun umumiy)
import type { XY } from './projection';
import type { Poly } from './types';

export function distToSeg(p: XY, a: XY, b: XY) {
  const dx = b[0] - a[0], dy = b[1] - a[1];
  const L = dx * dx + dy * dy;
  const t = L === 0 ? 0 : Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L));
  return Math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy);
}

/** Nuqtaning segmentdagi proyeksiyasi: t ∈ [0,1] va masofa */
export function projectOnSeg(p: XY, a: XY, b: XY) {
  const dx = b[0] - a[0], dy = b[1] - a[1];
  const L = dx * dx + dy * dy;
  const t = L === 0 ? 0 : Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L));
  const q: XY = [a[0] + t * dx, a[1] + t * dy];
  return { t, q, d: Math.hypot(p[0] - q[0], p[1] - q[1]) };
}

export function inRing(p: XY, ring: XY[]) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i], [xj, yj] = ring[j];
    if (yi > p[1] !== yj > p[1] && p[0] < ((xj - xi) * (p[1] - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

export const inPoly = (p: XY, poly: Poly) => inRing(p, poly[0]) && !poly.slice(1).some((h) => inRing(p, h));

/** Polygon chegarasigacha masofa — ichida ham, tashqarida ham (masalan, suvda qirg'oqqacha) */
export function distToBoundary(p: XY, poly: Poly) {
  let d = Infinity;
  for (const ring of poly) for (let i = 0; i < ring.length - 1; i++) d = Math.min(d, distToSeg(p, ring[i], ring[i + 1]));
  return d;
}

/** Polygon ichida bo'lsa 0, aks holda chegaragacha masofa */
export function distToPoly(p: XY, poly: Poly) {
  if (inPoly(p, poly)) return 0;
  let d = Infinity;
  for (const ring of poly) for (let i = 0; i < ring.length - 1; i++) d = Math.min(d, distToSeg(p, ring[i], ring[i + 1]));
  return d;
}

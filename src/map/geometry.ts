import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import type { XY } from './projection';
import type { MultiPoly, Poly } from './types';

// Koordinata tizimi: ma'lumot (x = sharq, y = shimol) → three.js (X = x, Y = balandlik, Z = -y).
// Shape'lar XY tekisligida quriladi va mesh `rotation-x={-Math.PI / 2}` bilan yotqiziladi:
// (x, y, 0) → (x, 0, -y), extrude chuqurligi esa yuqoriga (+Y) qaraydi.

export const toWorld = ([x, y]: XY, h = 0) => new THREE.Vector3(x, h, -y);

const v2 = (ring: XY[]) => {
  // Oxirgi nuqta birinchisini takrorlasa, olib tashlaymiz (three.js yopiq deb hisoblaydi)
  const pts = ring.map(([x, y]) => new THREE.Vector2(x, y));
  if (pts.length > 1 && pts[0].equals(pts[pts.length - 1])) pts.pop();
  return pts;
};

export function polyToShape(poly: Poly): THREE.Shape {
  const shape = new THREE.Shape(v2(poly[0]));
  shape.holes = poly.slice(1).map((h) => new THREE.Path(v2(h)));
  return shape;
}

export const multiToShapes = (m: MultiPoly) => m.map(polyToShape);

export function extrude(shapes: THREE.Shape | THREE.Shape[], depth: number) {
  return new THREE.ExtrudeGeometry(shapes, { depth, bevelEnabled: false, curveSegments: 1 });
}

export function flat(shapes: THREE.Shape | THREE.Shape[]) {
  return new THREE.ShapeGeometry(shapes, 1);
}

/** Bir xil materialli geometriyalarni bitta draw call'ga birlashtirish */
export function merge(geoms: THREE.BufferGeometry[], useGroups = false) {
  const merged = mergeGeometries(geoms, useGroups);
  geoms.forEach((g) => g.dispose());
  return merged;
}

/**
 * Ko'prik: har bir segment uchun taxta + ikki yon panjara + ustunchalar.
 * `pierLevel` berilsa — suv ustidagi joylarda taxta ostiga suvgacha tushadigan tayanch ustunlar (~5 m da bir juft).
 */
export function bridgeGeometry(line: XY[], width: number, deckY: number, pierLevel?: (p: XY) => number | null) {
  const deck: THREE.BufferGeometry[] = [];
  const rails: THREE.BufferGeometry[] = [];
  const DECK_H = 0.25, RAIL_H = 0.9, POST = 0.12;

  for (let i = 0; i < line.length - 1; i++) {
    const [x0, y0] = line[i], [x1, y1] = line[i + 1];
    const dx = x1 - x0, dy = y1 - y0;
    const len = Math.hypot(dx, dy);
    if (len < 0.01) continue;
    const angle = Math.atan2(dy, dx);
    const mid = toWorld([(x0 + x1) / 2, (y0 + y1) / 2]);
    // Perpendikulyar (ma'lumot koordinatasida), birlik vektor
    const nx = -dy / len, ny = dx / len;

    const place = (g: THREE.BufferGeometry, ox: number, oy: number, y: number) => {
      g.rotateY(angle);
      g.translate(mid.x + ox, y, mid.z - oy);
      return g;
    };

    deck.push(place(new THREE.BoxGeometry(len + 0.2, DECK_H, width), 0, 0, deckY + DECK_H / 2));
    for (const side of [-1, 1]) {
      const off = side * (width / 2 - POST / 2);
      rails.push(place(new THREE.BoxGeometry(len, 0.08, POST), nx * off, ny * off, deckY + DECK_H + RAIL_H));
      const posts = Math.max(2, Math.round(len / 1.5) + 1);
      for (let k = 0; k < posts; k++) {
        const t = k / (posts - 1) - 0.5;
        const p = new THREE.BoxGeometry(POST, RAIL_H, POST);
        p.translate(toWorld([dx * t + nx * off, dy * t + ny * off]).x + mid.x, deckY + DECK_H + RAIL_H / 2, toWorld([dx * t + nx * off, dy * t + ny * off]).z + mid.z);
        rails.push(p);
      }
    }
    if (pierLevel) {
      const n = Math.max(1, Math.round(len / 5));
      for (let k = 0; k <= n; k++) {
        const t = 0.06 + (k / n) * 0.88;
        for (const side of [-1, 1]) {
          const off = side * (width / 2 - 0.25);
          const at: XY = [x0 + dx * t + nx * off, y0 + dy * t + ny * off];
          const level = pierLevel(at);
          if (level === null) continue;
          const h = deckY - level + 0.1;
          const w = toWorld(at);
          rails.push(new THREE.BoxGeometry(0.22, h, 0.22).translate(w.x, level - 0.1 + h / 2, w.z));
        }
      }
    }
  }
  return { deck: merge(deck), rails: merge(rails) };
}

/**
 * Ekranda 1 metr necha piksel (ekran markazidagi yer nuqtasida). Ortografik kamerada bu zoom ning o'zi;
 * perspektivda — markazdagi yer nuqtasigacha masofa va ko'rish burchagidan.
 */
export function pxPerMeter(cam: THREE.Camera, viewportHeight: number) {
  if ((cam as THREE.OrthographicCamera).isOrthographicCamera) return (cam as THREE.OrthographicCamera).zoom;
  const p = cam as THREE.PerspectiveCamera;
  const dir = new THREE.Vector3(0, 0, -1).applyQuaternion(cam.quaternion);
  const t = dir.y < -1e-3 ? -cam.position.y / dir.y : 2000;
  return viewportHeight / 2 / (Math.min(t, 2000) * Math.tan(THREE.MathUtils.degToRad(p.fov) / 2));
}

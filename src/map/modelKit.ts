// Attraksion modellari uchun umumiy yordamchilar
import { useEffect } from 'react';
import * as THREE from 'three';
import { useThree } from '@react-three/fiber';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

export const V = (x: number, y: number, z: number) => new THREE.Vector3(x, y, z);
const UP = V(0, 1, 0);

/** Ikki nuqta orasidagi quvur */
export function rod(a: THREE.Vector3, b: THREE.Vector3, r: number, seg = 5) {
  const dir = b.clone().sub(a);
  const g = new THREE.CylinderGeometry(r, r, dir.length(), seg, 1);
  g.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(UP, dir.normalize()));
  g.translate((a.x + b.x) / 2, (a.y + b.y) / 2, (a.z + b.z) / 2);
  return g;
}

/** Geometriyaga bir xil vertex rang beradi (bir nechta rangli qismni bitta draw call'ga birlashtirish uchun) */
export function colored<T extends THREE.BufferGeometry>(g: T, hex: string): T {
  const c = new THREE.Color(hex);
  const n = g.attributes.position.count;
  const arr = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) arr.set([c.r, c.g, c.b], i * 3);
  g.setAttribute('color', new THREE.BufferAttribute(arr, 3));
  return g;
}

/** Aylana bo'ylab tashqariga qaragan holatga burish: lokal +Z → (cos a, 0, sin a) */
export const faceOutward = (a: number) => Math.PI / 2 - a;

/** Canvas'da chizilgan tekstura (tarmoq so'rovisiz) */
export function canvasTexture(w: number, h: number, draw: (ctx: CanvasRenderingContext2D, w: number, h: number) => void) {
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  draw(canvas.getContext('2d')!, w, h);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
}

export const prefersReducedMotion = () =>
  typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/**
 * Sahna "demand" rejimida (faqat o'zgarishda chiziladi). Doimiy animatsiya uchun
 * ~22 kadr/s da qayta chizishni so'raymiz — 60 emas, batareyani tejash uchun.
 */
export function useAmbientFrames(enabled: boolean, intervalMs = 45) {
  const invalidate = useThree((s) => s.invalidate);
  useEffect(() => {
    if (!enabled) return;
    let raf = 0;
    let last = 0;
    const loop = (t: number) => {
      if (t - last > intervalMs) {
        last = t;
        invalidate();
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [enabled, intervalMs, invalidate]);
}

/** Har xil turdagi geometriyalarni (indeksli va indekssiz) bitta geometriyaga birlashtirish */
export function mergeAll(geoms: THREE.BufferGeometry[]) {
  const flat = geoms.map((g) => {
    const out = g.index ? g.toNonIndexed() : g;
    if (out !== g) g.dispose();
    return out;
  });
  const merged = mergeGeometries(flat, false);
  flat.forEach((g) => g.dispose());
  return merged;
}

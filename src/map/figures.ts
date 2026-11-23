// Baliqlar chizadigan figuralar. Har bir figura — bir yoki bir nechta yopiq kontur,
// eni 1 ga keltirilgan, markazi (0, 0), y — yuqoriga (ekranda yoki shimolga).
// Yangi figura: config.ts → FISH.figures ga { shape: 'star' } yoki { svg: 'M … Z' } qo'shing.
import * as THREE from 'three';

export type Contour = [number, number][];
export type BuiltinShape = 'heart' | 'star' | 'circle';

export interface FishFigure {
  /** Ko'rsatish va fishShow('nomi') uchun */
  name: string;
  /** Tayyor shakl… */
  shape?: BuiltinShape;
  /** …yoki SVG <path d="…">: M L H V C S Q T Z buyruqlari (Figma → Copy as SVG). Yoy (A) qo'llanmaydi */
  svg?: string;
  /** Markaz [lon, lat]. Berilmasa — hovuzning eng keng joyi */
  at?: [number, number];
  /** Eni, m. Suvga sig'masa avtomatik kichraytiriladi */
  size: number;
  /**
   * true — ekranga qarab tik (yurak, harflar: o'qilishi uchun). false — suvda haqiqiy shakl,
   * xaritadagi boshqa dumaloq narsalar kabi har burchakdan bir xil ko'rinadi (aylana uchun standart).
   * Berilmasa: aylana — false, qolganlari — FISH.show.faceScreen
   */
  faceScreen?: boolean;
}

const loop = (n: number, f: (t: number) => [number, number]): Contour =>
  Array.from({ length: n }, (_, i) => f((i / n) * Math.PI * 2));

const BUILTIN: Record<BuiltinShape, () => Contour[]> = {
  // Klassik yurak egri chizig'i
  heart: () => [loop(240, (t) => [
    16 * Math.sin(t) ** 3,
    13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t),
  ])],
  star: () => [Array.from({ length: 10 }, (_, i): [number, number] => {
    const a = Math.PI / 2 + (i * Math.PI) / 5, r = i % 2 ? 0.42 : 1;
    return [Math.cos(a) * r, Math.sin(a) * r];
  })],
  circle: () => [loop(72, (t) => [Math.cos(t), Math.sin(t)])],
};

/** SVG path → konturlar (har bir M … Z bitta kontur). SVG'da y pastga qaraydi — aylantiramiz */
export function svgContours(d: string): Contour[] {
  const tokens = d.match(/[a-zA-Z]|-?\d*\.?\d+(?:e[-+]?\d+)?/g) ?? [];
  const out: Contour[] = [];
  let path: THREE.CurvePath<THREE.Vector2> | null = null;
  let cur = new THREE.Vector2(), start = new THREE.Vector2(), lastCtrl: THREE.Vector2 | null = null;
  let cmd = '', i = 0;
  const num = () => parseFloat(tokens[i++]);
  const flush = () => {
    if (path && path.curves.length) {
      const pts = path.getSpacedPoints(Math.max(32, Math.round(path.getLength() / 2)));
      out.push(pts.slice(0, -1).map((p) => [p.x, -p.y]));
    }
    path = null;
  };
  const add = (c: THREE.Curve<THREE.Vector2>) => { (path ??= new THREE.CurvePath()).add(c); };
  while (i < tokens.length) {
    if (/[a-zA-Z]/.test(tokens[i])) cmd = tokens[i++];
    const rel = cmd === cmd.toLowerCase();
    const P = (x: number, y: number) => (rel ? new THREE.Vector2(cur.x + x, cur.y + y) : new THREE.Vector2(x, y));
    switch (cmd.toUpperCase()) {
      case 'M': {
        flush();
        cur = P(num(), num()); start = cur.clone(); lastCtrl = null;
        cmd = rel ? 'l' : 'L'; // M dan keyingi juftlar — L
        break;
      }
      case 'L': { const p = P(num(), num()); add(new THREE.LineCurve(cur, p)); cur = p; lastCtrl = null; break; }
      case 'H': { const x = num(); const p = new THREE.Vector2(rel ? cur.x + x : x, cur.y); add(new THREE.LineCurve(cur, p)); cur = p; lastCtrl = null; break; }
      case 'V': { const y = num(); const p = new THREE.Vector2(cur.x, rel ? cur.y + y : y); add(new THREE.LineCurve(cur, p)); cur = p; lastCtrl = null; break; }
      case 'C': {
        const c1 = P(num(), num()), c2 = P(num(), num()), p = P(num(), num());
        add(new THREE.CubicBezierCurve(cur, c1, c2, p)); lastCtrl = c2; cur = p; break;
      }
      case 'S': {
        const c1 = lastCtrl ? cur.clone().multiplyScalar(2).sub(lastCtrl) : cur.clone();
        const c2 = P(num(), num()), p = P(num(), num());
        add(new THREE.CubicBezierCurve(cur, c1, c2, p)); lastCtrl = c2; cur = p; break;
      }
      case 'Q': {
        const c = P(num(), num()), p = P(num(), num());
        add(new THREE.QuadraticBezierCurve(cur, c, p)); lastCtrl = c; cur = p; break;
      }
      case 'T': {
        const c: THREE.Vector2 = lastCtrl ? cur.clone().multiplyScalar(2).sub(lastCtrl) : cur.clone();
        const p = P(num(), num());
        add(new THREE.QuadraticBezierCurve(cur, c, p)); lastCtrl = c; cur = p; break;
      }
      case 'Z': {
        if (cur.distanceTo(start) > 1e-6) add(new THREE.LineCurve(cur, start.clone()));
        cur = start.clone(); flush(); lastCtrl = null; cmd = ''; break;
      }
      default: i++; // A (yoy) va noma'lum buyruqlar — o'tkazib yuboriladi
    }
  }
  flush();
  return out;
}

/** Figura konturlari: markazi (0,0), eni 1 */
export function figureContours(f: FishFigure): Contour[] {
  const raw = f.svg ? svgContours(f.svg) : BUILTIN[f.shape ?? 'heart']();
  const all = raw.flat();
  if (!all.length) return figureContours({ ...f, svg: undefined, shape: 'heart' }); // SVG o'qilmasa — yurak
  const xs = all.map((p) => p[0]), ys = all.map((p) => p[1]);
  const cx = (Math.min(...xs) + Math.max(...xs)) / 2, cy = (Math.min(...ys) + Math.max(...ys)) / 2;
  const w = Math.max(...xs) - Math.min(...xs) || 1;
  return raw.map((c) => c.map(([x, y]) => [(x - cx) / w, (y - cy) / w] as [number, number]));
}

/** Kontur bo'ylab yurish: uzunlik, u ∈ [0,1) bo'yicha nuqta va urinma */
export function contourWalker(c: Contour) {
  const n = c.length;
  const cum = [0];
  for (let i = 0; i < n; i++) {
    const a = c[i], b = c[(i + 1) % n];
    cum.push(cum[i] + Math.hypot(b[0] - a[0], b[1] - a[1]));
  }
  const length = cum[n];
  const at = (u: number) => {
    const s = (((u % 1) + 1) % 1) * length;
    let lo = 0, hi = n;
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (cum[m] <= s) lo = m; else hi = m; }
    const a = c[lo], b = c[(lo + 1) % n];
    const seg = cum[lo + 1] - cum[lo] || 1;
    const k = (s - cum[lo]) / seg;
    const tx = (b[0] - a[0]) / seg, ty = (b[1] - a[1]) / seg;
    return { x: a[0] + (b[0] - a[0]) * k, y: a[1] + (b[1] - a[1]) * k, tx, ty };
  };
  return { length, at };
}

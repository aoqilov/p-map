import { useEffect, useLayoutEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { DROP_TOWER } from './config';
import { V, canvasTexture, colored, mergeAll, prefersReducedMotion, useAmbientFrames } from './modelKit';
import type { Palette } from './theme';

// Erkin tushish minorasi. Lokal koordinata: Y yuqoriga, zinapoya va eshik +Z tomonda.
// Sakkiz qirrali platforma, panjarali minora (pastdan qora → qizil → to'q sariq → sariq),
// minora atrofidagi halqa-kabina: ko'tariladi, tepada to'xtaydi, erkin tushadi va tormozlanadi.

const PLAT_H = 0.6;
const PLAT_R = 8.5; // sakkizburchak uchigacha
const APOTHEM = PLAT_R * Math.cos(Math.PI / 8);
const TOWER_BOTTOM = PLAT_H;
const TOWER_TOP = 52.6;
const DARK = '#2b3140';

export const DROP_TOWER_NATURAL = { height: 56.4, footprint: 2 * (APOTHEM + 1.8) };

/** Minora gradienti balandlik bo'yicha (0 — pastda, 1 — tepada) */
const STOPS: [number, string][] = [
  [0, '#16181d'], [0.42, '#2a1d22'], [0.55, '#c4161c'], [0.72, '#e3361b'], [0.86, '#f39a1b'], [1, '#f7d21e'],
];
function gradientAt(t: number, out: THREE.Color) {
  const c0 = new THREE.Color(), c1 = new THREE.Color();
  for (let i = 1; i < STOPS.length; i++) {
    if (t <= STOPS[i][0]) {
      const [a, ca] = STOPS[i - 1], [b, cb] = STOPS[i];
      return out.copy(c0.set(ca)).lerp(c1.set(cb), (t - a) / (b - a));
    }
  }
  return out.set(STOPS[STOPS.length - 1][1]);
}
/** Har bir uchga balandligiga qarab rang beradi (factor < 1 — to'qroq) */
function paintGradient(g: THREE.BufferGeometry, factor = 1) {
  const pos = g.attributes.position;
  const arr = new Float32Array(pos.count * 3);
  const c = new THREE.Color();
  for (let i = 0; i < pos.count; i++) {
    gradientAt(THREE.MathUtils.clamp((pos.getY(i) - TOWER_BOTTOM) / (TOWER_TOP - TOWER_BOTTOM), 0, 1), c).multiplyScalar(factor);
    arr.set([c.r, c.g, c.b], i * 3);
  }
  g.setAttribute('color', new THREE.BufferAttribute(arr, 3));
  return g;
}

/** Ikki nuqta orasidagi quvur, uzunasiga bir nechta bo'lak (gradient silliq chiqishi uchun) */
function strut(a: THREE.Vector3, b: THREE.Vector3, r: number, seg = 4, hseg = 1) {
  const dir = b.clone().sub(a);
  const g = new THREE.CylinderGeometry(r, r, dir.length(), seg, hseg);
  g.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(V(0, 1, 0), dir.normalize()));
  g.translate((a.x + b.x) / 2, (a.y + b.y) / 2, (a.z + b.z) / 2);
  return g;
}

/** Halqa-kabina balandligi vaqtga qarab (lokal metr, halqa ostidan) */
export function gondolaHeight(t: number) {
  const { restSeconds, climbSeconds, holdSeconds, freeFallShare } = DROP_TOWER;
  const low = PLAT_H + 1.7, high = TOWER_TOP - 6, span = high - low;
  const g = 9.81;
  const fall = span * freeFallShare;
  const tFall = Math.sqrt((2 * fall) / g);
  const v = g * tFall;
  const brakeDist = span - fall;
  const decel = (v * v) / (2 * brakeDist);
  const tBrake = v / decel;
  const cycle = restSeconds * 2 + climbSeconds + holdSeconds + tFall + tBrake;
  let s = t % cycle;
  if ((s -= restSeconds) < 0) return low;
  if (s < climbSeconds) { const k = s / climbSeconds; return low + span * k * k * (3 - 2 * k); }
  if ((s -= climbSeconds) < holdSeconds) return high;
  s -= holdSeconds;
  if (s < tFall) return high - 0.5 * g * s * s; // erkin tushish
  if ((s -= tFall) < tBrake) return high - fall - (v * s - 0.5 * decel * s * s); // magnit tormoz
  return low;
}

function buildTower() {
  const parts = { platform: [] as THREE.BufferGeometry[], fence: [] as THREE.BufferGeometry[], tower: [] as THREE.BufferGeometry[] };

  // --- Platforma: sakkiz qirrali, bir tomoni +Z ga qaragan ---
  parts.platform.push(colored(new THREE.CylinderGeometry(PLAT_R, PLAT_R + 0.15, PLAT_H, 8).rotateY(Math.PI / 8).translate(0, PLAT_H / 2, 0), '#3b4048'));
  const floor = new THREE.CircleGeometry(PLAT_R - 0.02, 8).rotateZ(Math.PI / 8).rotateX(-Math.PI / 2).translate(0, PLAT_H + 0.01, 0);

  // Zinapoya (+Z): uch pog'ona, qizil qadamlar
  for (let i = 0; i < 3; i++) {
    const top = PLAT_H * (3 - i) / 4;
    parts.platform.push(colored(new THREE.BoxGeometry(2.4, top, 0.55).translate(0, top / 2, APOTHEM + 0.275 + i * 0.55), i % 2 ? '#a92b27' : '#b5332e'));
  }
  // Operator budkasi (old o'ng burchakda)
  const booth = V(4.4, PLAT_H, APOTHEM - 2.2);
  parts.platform.push(colored(new THREE.BoxGeometry(1.8, 0.9, 1.8).translate(booth.x, booth.y + 0.45, booth.z), '#3a404c'));
  parts.platform.push(colored(new THREE.BoxGeometry(2.1, 0.16, 2.1).translate(booth.x, booth.y + 2.5, booth.z), '#5a616c'));
  for (const [dx, dz] of [[-0.85, -0.85], [0.85, -0.85], [-0.85, 0.85], [0.85, 0.85]]) {
    parts.platform.push(colored(new THREE.BoxGeometry(0.1, 1.55, 0.1).translate(booth.x + dx, booth.y + 1.65, booth.z + dz), '#3a404c'));
  }
  const glass = new THREE.BoxGeometry(1.7, 1.5, 1.7).translate(booth.x, booth.y + 1.65, booth.z);

  // Panjara platforma cheti bo'ylab (zinapoya oldida ochiq)
  const corners = Array.from({ length: 8 }, (_, k) => {
    const a = Math.PI / 2 + Math.PI / 8 + (k * Math.PI) / 4; // +Z tomoni tekis qirra bo'lishi uchun
    return V((PLAT_R - 0.2) * Math.cos(a), 0, (PLAT_R - 0.2) * Math.sin(a));
  });
  for (let k = 0; k < 8; k++) {
    const a = corners[k], b = corners[(k + 1) % 8];
    const len = a.distanceTo(b);
    const n = Math.max(2, Math.round(len / 1.3));
    const isFront = Math.abs((a.z + b.z) / 2 - (PLAT_R - 0.2) * Math.cos(Math.PI / 8)) < 0.5;
    for (let i = 0; i <= n; i++) {
      const p = a.clone().lerp(b, i / n);
      if (isFront && Math.abs(p.x) < 1.3) continue;
      parts.fence.push(new THREE.BoxGeometry(0.08, 1.1, 0.08).translate(p.x, PLAT_H + 0.55, p.z));
    }
    // Old tomonda eshik oralig'i (x ∈ [-1.3, 1.3]) qoldiriladi
    const [left, right] = a.x < b.x ? [a, b] : [b, a];
    const rails: [THREE.Vector3, THREE.Vector3][] = isFront
      ? [[left, V(-1.3, 0, left.z)], [V(1.3, 0, right.z), right]]
      : [[a, b]];
    for (const [p, q] of rails) {
      for (const y of [1.1, 0.55]) parts.fence.push(strut(V(p.x, PLAT_H + y, p.z), V(q.x, PLAT_H + y, q.z), y > 1 ? 0.045 : 0.03, 5));
    }
  }

  // --- Minora: 12 ta tik ustun, zigzag tirgaklar va halqalar; yuqoriga torayadi ---
  const N = 12, LEVEL = 1.6;
  const radiusAt = (y: number) => THREE.MathUtils.lerp(1.7, 1.15, (y - TOWER_BOTTOM) / (TOWER_TOP - TOWER_BOTTOM));
  const node = (i: number, y: number) => {
    const a = (i / N) * Math.PI * 2;
    const r = radiusAt(y);
    return V(r * Math.cos(a), y, r * Math.sin(a));
  };
  for (let i = 0; i < N; i++) parts.tower.push(strut(node(i, TOWER_BOTTOM), node(i, TOWER_TOP), 0.09, 5, 24));
  const levels = Math.floor((TOWER_TOP - TOWER_BOTTOM) / LEVEL);
  for (let k = 0; k < levels; k++) {
    const y0 = TOWER_BOTTOM + k * LEVEL, y1 = y0 + LEVEL;
    for (let i = 0; i < N; i++) {
      parts.tower.push(strut(node(i, y0), node(i + 1, y1), 0.035, 3));
      if (k % 2 === 0) parts.tower.push(strut(node(i, y0), node(i + 1, y0), 0.04, 3));
    }
  }
  const core = new THREE.CylinderGeometry(0.75, 0.95, TOWER_TOP - TOWER_BOTTOM, 12, 24).translate(0, (TOWER_TOP + TOWER_BOTTOM) / 2, 0);

  // Tepadagi sariq qalpoq
  const cap = mergeAll([
    new THREE.CylinderGeometry(1.5, 1.55, 1.6, 16).translate(0, TOWER_TOP + 0.8, 0),
    new THREE.TorusGeometry(1.58, 0.08, 4, 32).rotateX(Math.PI / 2).translate(0, TOWER_TOP + 1.6, 0),
    new THREE.SphereGeometry(1.5, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2).translate(0, TOWER_TOP + 1.6, 0),
    new THREE.ConeGeometry(0.12, 0.7, 8).translate(0, TOWER_TOP + 3.4, 0),
  ]);

  // --- Halqa-kabina (harakatlanadi): qizil halqa va tashqariga qaragan o'rindiqlar ---
  const ringShape = new THREE.Shape().absarc(0, 0, 3.4, 0, Math.PI * 2, false);
  ringShape.holes.push(new THREE.Path().absarc(0, 0, 2.0, 0, Math.PI * 2, true));
  const gondola: THREE.BufferGeometry[] = [
    colored(new THREE.ExtrudeGeometry(ringShape, { depth: 0.7, bevelEnabled: false, curveSegments: 32 }).rotateX(-Math.PI / 2), '#d0202a'),
  ];
  const SEATS = DROP_TOWER.seats;
  for (let i = 0; i < SEATS; i++) {
    const a = ((i + 0.5) / SEATS) * Math.PI * 2;
    const yaw = Math.PI / 2 - a; // lokal +Z → tashqariga
    const col = i % 2 ? '#f08a1c' : '#e0401c';
    const seat = [
      colored(new THREE.BoxGeometry(0.55, 1.0, 0.14).translate(0, -0.55, -0.12), col), // suyanchiq
      colored(new THREE.BoxGeometry(0.55, 0.12, 0.48).translate(0, -1.0, 0.12), col), // o'rindiq
      colored(new THREE.BoxGeometry(0.42, 0.28, 0.14).translate(0, 0.08, -0.12), col), // bosh tayanchi
      colored(new THREE.BoxGeometry(0.44, 0.62, 0.1).translate(0, -0.55, 0.12), '#1e2128'), // xavfsizlik kamari
    ];
    for (const g of seat) gondola.push(g.rotateY(yaw).translate(2.85 * Math.cos(a), 0, 2.85 * Math.sin(a)));
  }

  const floorTex = canvasTexture(512, 512, (g, w, h) => {
    g.fillStyle = '#8d949b';
    g.fillRect(0, 0, w, h);
    for (let i = 0; i < 1500; i++) { // beton donadorligi
      g.fillStyle = `rgba(0,0,0,${Math.random() * 0.06})`;
      g.fillRect(Math.random() * w, Math.random() * h, 2, 2);
    }
    g.strokeStyle = '#e8c21e';
    g.lineWidth = 7;
    const oct = (r: number) => {
      g.beginPath();
      for (let k = 0; k <= 8; k++) {
        const a = Math.PI / 8 + (k * Math.PI) / 4;
        const x = w / 2 + r * Math.cos(a), y = h / 2 + r * Math.sin(a);
        if (k) g.lineTo(x, y); else g.moveTo(x, y);
      }
      g.stroke();
    };
    oct(w * 0.43);
    g.setLineDash([16, 12]);
    oct(w * 0.3);
    g.setLineDash([]);
    for (let k = 0; k < 8; k++) { // xavfli hudud nurlari
      const a = (k * Math.PI) / 4;
      g.beginPath();
      g.moveTo(w / 2 + w * 0.3 * Math.cos(a), h / 2 + h * 0.3 * Math.sin(a));
      g.lineTo(w / 2 + w * 0.4 * Math.cos(a), h / 2 + h * 0.4 * Math.sin(a));
      g.stroke();
    }
  });

  return {
    platform: mergeAll(parts.platform),
    fence: mergeAll(parts.fence),
    floor,
    glass,
    tower: mergeAll([...parts.tower.map((g) => paintGradient(g)), paintGradient(core, 0.6)]),
    cap,
    gondola: mergeAll(gondola),
    floorTex,
  };
}

export function DropTower({ pal, selected }: { pal: Palette; selected: boolean }) {
  const t = useMemo(buildTower, []);
  useEffect(() => () => {
    Object.values(t).forEach((v) => (v instanceof THREE.BufferGeometry || v instanceof THREE.Texture) && v.dispose());
  }, [t]);

  const gondola = useRef<THREE.Group>(null!);
  const animate = DROP_TOWER.enabled && !prefersReducedMotion();
  useAmbientFrames(animate);

  useLayoutEffect(() => {
    gondola.current.position.y = gondolaHeight(animate ? performance.now() / 1000 : 0);
  }, [animate]);
  useFrame(() => {
    if (animate) gondola.current.position.y = gondolaHeight(performance.now() / 1000);
  });

  return (
    <group>
      <mesh geometry={t.platform} castShadow receiveShadow>
        <meshStandardMaterial vertexColors roughness={0.8} />
      </mesh>
      <mesh geometry={t.floor} receiveShadow>
        <meshStandardMaterial map={t.floorTex} color={selected ? pal.selected : '#ffffff'} roughness={0.9} />
      </mesh>
      <mesh geometry={t.fence} castShadow>
        <meshStandardMaterial color={DARK} roughness={0.6} metalness={0.3} />
      </mesh>
      <mesh geometry={t.glass}>
        <meshStandardMaterial color="#9cc7e6" transparent opacity={0.45} roughness={0.1} depthWrite={false} />
      </mesh>
      <mesh geometry={t.tower} castShadow>
        <meshStandardMaterial vertexColors roughness={0.5} metalness={0.25} />
      </mesh>
      <mesh geometry={t.cap} castShadow>
        <meshStandardMaterial color="#f2c414" roughness={0.35} metalness={0.4} />
      </mesh>
      <group ref={gondola}>
        <mesh geometry={t.gondola} castShadow>
          <meshStandardMaterial vertexColors roughness={0.5} />
        </mesh>
      </group>
    </group>
  );
}

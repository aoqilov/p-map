import { useEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { COASTER } from './config';
import { V, canvasTexture, colored, mergeAll, prefersReducedMotion, rod, useAmbientFrames } from './modelKit';
import type { Palette } from './theme';

// Mini amerikan tepaligi (bolalar uchun). Lokal koordinata: Y yuqoriga, zinapoya +Z tomonda, platforma uzunasi X bo'ylab.
// Trassa — sakkizsimon (Gerono lemniskatasi): bir tarmog'i baland, ikkinchisi past, markazda ustma-ust kesishadi.
// Parovoz va vagonlar trassa bo'ylab yuradi: tepada sekin, pastga tushganda tezlashadi (energiya saqlanishi).

const PLAT = 0.5; // platforma balandligi
const L = 22; // platforma uzunligi
const W = 14; // eni
const R = W / 2;
const HALF_STRAIGHT = L / 2 - R;
const A = 9; // trassa: X bo'ylab yarim uzunlik
const BZ = 4.6; // Z bo'ylab maksimal og'ish
const LOW = PLAT + 0.45; // relsning eng past nuqtasi
const LIFT = 3.6; // eng past va eng baland nuqta farqi
const GAUGE = 0.42; // rels markazdan masofasi
const RED = '#b3312b';
const STEEL = '#9aa0a6';

export const COASTER_NATURAL = { height: 6.0, footprint: L };

/** Trassa markaz chizig'i, t ∈ [0, 2π) */
function centerAt(t: number) {
  return V(A * Math.cos(t), LOW + (LIFT / 2) * (1 + Math.sin(t)), BZ * Math.sin(2 * t));
}

/** Uzunlik bo'yicha jadval: pozitsiya, yo'nalish va harakat vaqti */
function buildTrack() {
  const N = 1600;
  const pts: THREE.Vector3[] = [];
  for (let i = 0; i < N; i++) pts.push(centerAt((i / N) * Math.PI * 2));
  const s = new Float64Array(N + 1);
  for (let i = 1; i <= N; i++) s[i] = s[i - 1] + pts[i % N].distanceTo(pts[i - 1]);
  const length = s[N];

  // Tezlik: tepada `topSpeed`, pastda energiya bo'yicha tezlashadi (kichik "g" — bolalar attraksioni)
  const hTop = LOW + LIFT;
  const speedAt = (h: number) => Math.sqrt(COASTER.topSpeed ** 2 + 2 * COASTER.gravity * (hTop - h));
  const time = new Float64Array(N + 1);
  for (let i = 1; i <= N; i++) {
    const h = (pts[i % N].y + pts[i - 1].y) / 2;
    time[i] = time[i - 1] + (s[i] - s[i - 1]) / speedAt(h);
  }
  const lap = time[N];

  const search = (arr: Float64Array, v: number) => {
    let lo = 0, hi = N;
    while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (arr[mid] <= v) lo = mid; else hi = mid; }
    return lo;
  };
  /** Uzunlik bo'yicha nuqta va urinma */
  const at = (dist: number) => {
    const d = ((dist % length) + length) % length;
    const i = search(s, d);
    const k = (d - s[i]) / Math.max(s[i + 1] - s[i], 1e-9);
    const a = pts[i], b = pts[(i + 1) % N];
    return { p: a.clone().lerp(b, k), tan: b.clone().sub(a).normalize() };
  };
  /** Vaqt bo'yicha poyezd boshining uzunlikdagi o'rni */
  const distAtTime = (sec: number) => {
    const tt = ((sec % lap) + lap) % lap;
    const i = search(time, tt);
    const k = (tt - time[i]) / Math.max(time[i + 1] - time[i], 1e-9);
    return s[i] + k * (s[i + 1] - s[i]);
  };
  return { length, lap, at, distAtTime };
}

/** Urinma bo'yicha bazis: X — oldinga, Y — yuqoriga, Z — yon */
function frame(tan: THREE.Vector3) {
  const up = new THREE.Vector3(0, 1, 0);
  const u = up.clone().sub(tan.clone().multiplyScalar(tan.dot(up))).normalize();
  const side = new THREE.Vector3().crossVectors(tan, u).normalize();
  return { up: u, side, m: new THREE.Matrix4().makeBasis(tan, u, side) };
}

function locomotive() {
  const red = '#a8322b', dark = '#2a2522', brass = '#b8893c', cab = '#7a3a26';
  const parts: THREE.BufferGeometry[] = [
    colored(new THREE.BoxGeometry(1.55, 0.18, 0.78).translate(0, 0.24, 0), dark),
    colored(new THREE.CylinderGeometry(0.32, 0.32, 0.95, 16).rotateZ(Math.PI / 2).translate(0.25, 0.64, 0), red),
    colored(new THREE.CylinderGeometry(0.34, 0.34, 0.18, 16).rotateZ(Math.PI / 2).translate(0.78, 0.64, 0), '#3a3330'),
    colored(new THREE.CylinderGeometry(0.17, 0.11, 0.5, 12).translate(0.62, 1.12, 0), brass),
    colored(new THREE.CylinderGeometry(0.21, 0.17, 0.09, 12).translate(0.62, 1.41, 0), brass),
    colored(new THREE.SphereGeometry(0.15, 12, 8).translate(0.2, 0.96, 0), brass),
    colored(new THREE.CylinderGeometry(0.07, 0.07, 0.08, 10).rotateZ(Math.PI / 2).translate(0.9, 0.9, 0), brass),
    colored(new THREE.BoxGeometry(0.58, 0.78, 0.8).translate(-0.5, 0.72, 0), cab),
    colored(new THREE.BoxGeometry(0.32, 0.26, 0.82).translate(-0.5, 0.88, 0), dark),
    colored(new THREE.BoxGeometry(0.74, 0.07, 0.92).translate(-0.5, 1.14, 0), dark),
    colored(new THREE.BoxGeometry(0.22, 0.22, 0.72).rotateZ(0.6).translate(0.86, 0.24, 0), '#5a5f66'),
  ];
  for (const x of [-0.45, 0, 0.45]) for (const z of [-0.37, 0.37]) {
    parts.push(colored(new THREE.CylinderGeometry(0.17, 0.17, 0.08, 12).rotateX(Math.PI / 2).translate(x, 0.17, z), '#1d1a18'));
  }
  return mergeAll(parts);
}

function wagon() {
  const wood = '#7a4a2e', teal = '#2f8f87', dark = '#2a2522';
  const parts: THREE.BufferGeometry[] = [
    colored(new THREE.BoxGeometry(1.5, 0.15, 0.78).translate(0, 0.22, 0), dark),
    colored(new THREE.BoxGeometry(1.5, 0.5, 0.84).translate(0, 0.54, 0), wood),
    colored(new THREE.BoxGeometry(1.56, 0.05, 0.9).translate(0, 0.8, 0), '#5a3220'),
  ];
  for (const x of [-0.35, 0.38]) {
    parts.push(colored(new THREE.BoxGeometry(0.34, 0.12, 0.72).translate(x, 0.86, 0), teal));
    parts.push(colored(new THREE.BoxGeometry(0.1, 0.38, 0.72).translate(x - 0.2, 1.0, 0), teal));
  }
  for (const x of [-0.45, 0.45]) for (const z of [-0.37, 0.37]) {
    parts.push(colored(new THREE.CylinderGeometry(0.14, 0.14, 0.07, 12).rotateX(Math.PI / 2).translate(x, 0.15, z), '#1d1a18'));
  }
  return mergeAll(parts);
}

/** Stadion (to'g'ri to'rtburchak + yarim doiralar) chegara nuqtalari, inset — ichkariga surish */
function stadium(inset: number, steps = 24) {
  const r = R - inset;
  const out: THREE.Vector2[] = [];
  for (let i = 0; i <= steps; i++) { const a = -Math.PI / 2 + (i / steps) * Math.PI; out.push(new THREE.Vector2(HALF_STRAIGHT + r * Math.cos(a), r * Math.sin(a))); }
  for (let i = 0; i <= steps; i++) { const a = Math.PI / 2 + (i / steps) * Math.PI; out.push(new THREE.Vector2(-HALF_STRAIGHT + r * Math.cos(a), r * Math.sin(a))); }
  return out;
}

function buildCoaster() {
  const track = buildTrack();

  // --- Platforma (shakl XY da, keyin yotqiziladi: y → -z) ---
  const shape = new THREE.Shape(stadium(0));
  const base = colored(new THREE.ExtrudeGeometry(shape, { depth: PLAT, bevelEnabled: false, curveSegments: 1 }).rotateX(-Math.PI / 2), '#6f757c');
  const deck = new THREE.ShapeGeometry(shape).rotateX(-Math.PI / 2).translate(0, PLAT + 0.01, 0);
  const steps = mergeAll([0, 1].map((i) => {
    const top = PLAT * (2 - i) / 3;
    return new THREE.BoxGeometry(2.4, top, 0.5).translate(0, top / 2, R + 0.25 + i * 0.5);
  }));

  // --- Panjara: ustunlar, tutqich va to'r (zinapoya oldida eshik) ---
  const fencePts = stadium(0.25, 18).map((v) => V(v.x, PLAT, -v.y));
  const isGate = (p: THREE.Vector3) => p.z > R - 1 && Math.abs(p.x) < 1.3;
  const fence: THREE.BufferGeometry[] = [];
  const meshPos: number[] = [], meshUv: number[] = [];
  let u = 0;
  for (let i = 0; i < fencePts.length; i++) {
    const a = fencePts[i], b = fencePts[(i + 1) % fencePts.length];
    if (!isGate(a)) fence.push(rod(a, V(a.x, PLAT + 1.05, a.z), 0.035, 5));
    const len = a.distanceTo(b);
    if (isGate(a) || isGate(b) || len < 0.01) { u += len; continue; }
    fence.push(rod(V(a.x, PLAT + 1.05, a.z), V(b.x, PLAT + 1.05, b.z), 0.03, 4));
    const [u0, u1] = [u, u + len];
    meshPos.push(a.x, PLAT + 0.08, a.z, b.x, PLAT + 0.08, b.z, b.x, PLAT + 1.0, b.z, a.x, PLAT + 0.08, a.z, b.x, PLAT + 1.0, b.z, a.x, PLAT + 1.0, a.z);
    meshUv.push(u0, 0, u1, 0, u1, 1, u0, 0, u1, 1, u0, 1);
    u = u1;
  }
  const netting = new THREE.BufferGeometry();
  netting.setAttribute('position', new THREE.Float32BufferAttribute(meshPos, 3));
  netting.setAttribute('uv', new THREE.Float32BufferAttribute(meshUv, 2));
  netting.computeVertexNormals();

  // --- Trassa: ikki rels, pastki to'sin va shpallar ---
  const SAMPLES = 360;
  const left: THREE.Vector3[] = [], right: THREE.Vector3[] = [], spine: THREE.Vector3[] = [];
  for (let i = 0; i < SAMPLES; i++) {
    const { p, tan } = track.at((i / SAMPLES) * track.length);
    const f = frame(tan);
    left.push(p.clone().addScaledVector(f.side, GAUGE));
    right.push(p.clone().addScaledVector(f.side, -GAUGE));
    spine.push(p.clone().addScaledVector(f.up, -0.2));
  }
  const tube = (pts: THREE.Vector3[], r: number) => new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts, true), 480, r, 6, true);
  const rails = [tube(left, 0.055), tube(right, 0.055), tube(spine, 0.085)];
  const ties: THREE.BufferGeometry[] = [];
  for (let d = 0; d < track.length; d += 0.5) {
    const { p, tan } = track.at(d);
    const f = frame(tan);
    const g = new THREE.BoxGeometry(0.12, 0.06, 1.0).translate(0, -0.08, 0);
    g.applyMatrix4(f.m);
    g.translate(p.x, p.y, p.z);
    ties.push(g);
  }

  // --- Tayanchlar: ustun + ko'ndalang to'sin; balandida A-shaklli oyoqlar. Pastki tarmoq ustidan o'tmaydi ---
  const supports: THREE.BufferGeometry[] = [];
  const probe = Array.from({ length: 240 }, (_, i) => track.at((i / 240) * track.length).p);
  for (let d = 1; d < track.length; d += 2.3) {
    const { p, tan } = track.at(d);
    const bottom = p.y - 0.26;
    if (bottom - PLAT < 0.35) continue;
    const blocked = probe.some((q) => q.y < p.y - 1 && Math.hypot(q.x - p.x, q.z - p.z) < 1.6);
    if (blocked) continue;
    const f = frame(tan);
    const s = V(f.side.x, 0, f.side.z).normalize();
    supports.push(rod(V(p.x, PLAT, p.z), V(p.x, bottom, p.z), 0.09, 6));
    supports.push(rod(V(p.x, bottom, p.z).addScaledVector(s, -0.6), V(p.x, bottom, p.z).addScaledVector(s, 0.6), 0.06, 5));
    if (bottom - PLAT > 2.2) {
      for (const k of [-1, 1]) {
        supports.push(rod(V(p.x, bottom, p.z).addScaledVector(s, 0.55 * k), V(p.x, PLAT, p.z).addScaledVector(s, 1.4 * k), 0.06, 5));
      }
      const mid = PLAT + (bottom - PLAT) * 0.45;
      supports.push(rod(V(p.x, mid, p.z).addScaledVector(s, -1.0), V(p.x, mid, p.z).addScaledVector(s, 1.0), 0.045, 4));
    }
  }

  const deckTex = canvasTexture(128, 128, (g, w, h) => {
    g.fillStyle = '#9ca1a6';
    g.fillRect(0, 0, w, h);
    g.lineWidth = 3;
    for (let y = 0; y < h; y += 16) for (let x = 0; x < w; x += 16) { // "olmos" naqshli po'lat list
      const dx = (y / 16) % 2 ? 8 : 0;
      g.strokeStyle = 'rgba(255,255,255,0.35)';
      g.beginPath(); g.moveTo(x + dx + 2, y + 10); g.lineTo(x + dx + 10, y + 3); g.stroke();
      g.strokeStyle = 'rgba(0,0,0,0.18)';
      g.beginPath(); g.moveTo(x + dx + 3, y + 12); g.lineTo(x + dx + 11, y + 5); g.stroke();
    }
  });
  deckTex.wrapS = deckTex.wrapT = THREE.RepeatWrapping;
  deckTex.repeat.set(0.5, 0.5); // UV = metr → 2 m da bir naqsh

  const netTex = canvasTexture(64, 64, (g, w, h) => {
    g.clearRect(0, 0, w, h);
    g.strokeStyle = 'rgba(70,76,84,0.9)';
    g.lineWidth = 2;
    g.beginPath(); g.moveTo(0, 0); g.lineTo(w, h); g.moveTo(w, 0); g.lineTo(0, h); g.stroke();
    g.lineWidth = 4;
    g.strokeRect(0, 0, w, h);
  });
  netTex.wrapS = netTex.wrapT = THREE.RepeatWrapping;
  netTex.repeat.set(4, 6);

  return {
    track,
    base, deck, steps,
    fence: mergeAll(fence), netting,
    rails: mergeAll(rails), ties: mergeAll(ties), supports: mergeAll(supports),
    loco: locomotive(), wagon: wagon(),
    textures: [deckTex, netTex] as const,
  };
}

export function Coaster({ pal, selected }: { pal: Palette; selected: boolean }) {
  const c = useMemo(buildCoaster, []);
  useEffect(() => () => {
    Object.values(c).forEach((v) => v instanceof THREE.BufferGeometry && v.dispose());
    c.textures.forEach((t) => t.dispose());
  }, [c]);
  const [deckTex, netTex] = c.textures;

  const cars = useRef<THREE.Group[]>([]);
  const animate = COASTER.enabled && !prefersReducedMotion();
  useAmbientFrames(animate);

  const place = (sec: number) => {
    const head = c.track.distAtTime(sec);
    cars.current.forEach((g, i) => {
      if (!g) return;
      const { p, tan } = c.track.at(head - i * COASTER.carSpacing);
      g.quaternion.setFromRotationMatrix(frame(tan).m);
      g.position.copy(p).addScaledVector(frame(tan).up, 0.06);
    });
  };
  useEffect(() => place(animate ? performance.now() / 1000 : 3.2), [animate]); // eslint-disable-line react-hooks/exhaustive-deps
  useFrame(() => {
    if (animate) place(performance.now() / 1000);
  });

  return (
    <group>
      <mesh geometry={c.base} castShadow receiveShadow>
        <meshStandardMaterial vertexColors roughness={0.8} />
      </mesh>
      <mesh geometry={c.deck} receiveShadow>
        <meshStandardMaterial map={deckTex} color={selected ? pal.selected : '#ffffff'} roughness={0.6} metalness={0.3} />
      </mesh>
      <mesh geometry={c.steps} castShadow>
        <meshStandardMaterial color="#7d8288" roughness={0.7} />
      </mesh>
      <mesh geometry={c.fence}>
        <meshStandardMaterial color="#b9bec4" metalness={0.4} roughness={0.4} />
      </mesh>
      <mesh geometry={c.netting}>
        <meshStandardMaterial map={netTex} transparent alphaTest={0.3} side={THREE.DoubleSide} />
      </mesh>
      <mesh geometry={c.supports} castShadow>
        <meshStandardMaterial color={STEEL} metalness={0.4} roughness={0.45} />
      </mesh>
      <mesh geometry={c.rails} castShadow>
        <meshStandardMaterial color={RED} metalness={0.3} roughness={0.45} />
      </mesh>
      <mesh geometry={c.ties} castShadow>
        <meshStandardMaterial color="#8f2a25" roughness={0.6} />
      </mesh>
      {Array.from({ length: COASTER.cars + 1 }, (_, i) => (
        <group key={i} ref={(g) => { if (g) cars.current[i] = g; }}>
          <mesh geometry={i === 0 ? c.loco : c.wagon} castShadow>
            <meshStandardMaterial vertexColors roughness={0.5} metalness={0.15} />
          </mesh>
        </group>
      ))}
    </group>
  );
}

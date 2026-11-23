import { useEffect, useLayoutEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { GALLEON } from './config';
import { V, canvasTexture, colored, mergeAll, prefersReducedMotion, rod, useAmbientFrames } from './modelKit';
import type { Palette } from './theme';

// "Galleon" — qaroqchi kema-tebratgich. Lokal koordinata: Y yuqoriga, aylanish o'qi Z bo'ylab.
// Ikki qizil A-rama (z = ±ZS), ularning tepasida o'q va "GALLEON" yozuvi; kema ikki po'lat shtanga bilan osilgan
// va XY tekisligida tebranadi. Pastda panjarali platforma, zinapoya +Z tomonda. Yozuv ikkala tomonda o'qiladi.

const H = 15.5; // o'q balandligi
const L = 12.6; // o'qdan kema markazigacha
const ZS = 3.7; // A-ramalar z holati
const FOOT = 9.4; // A-rama oyoqlari orasidagi yarim masofa
const SHIP_HALF = 5.6;
const WALL_Z = 1.86;
const PLAT_TOP = 1.0;

export const GALLEON_NATURAL = { height: 21, footprint: 2 * (FOOT + 1) };

const RED = '#b3141c';
const DARK_RED = '#8e0f16';
const GOLD = '#dfae2c';
const WOOD = '#8a5a2b';
const STEEL = '#aeb4bb';

// Kema yon tomoni profili (x — uzunasiga, y — balandlik)
const top = (x: number) => (x >= 0 ? 0.1 + 1.9 * Math.pow(x / SHIP_HALF, 2.2) : 0.1 + 0.9 * Math.pow(-x / SHIP_HALF, 2));
const bot = (x: number) => -1.5 + 1.3 * Math.pow(Math.abs(x) / SHIP_HALF, 3);

/** Ikki egri chiziq (past/yuqori) orasidagi qirrani Z bo'ylab cho'zilgan qalinlikka aylantiradi */
function band(lo: (x: number) => number, hi: (x: number) => number, depth: number, z0: number, n = 28) {
  const s = new THREE.Shape();
  for (let i = 0; i <= n; i++) {
    const x = -SHIP_HALF + (2 * SHIP_HALF * i) / n;
    if (i) s.lineTo(x, hi(x)); else s.moveTo(x, hi(x));
  }
  for (let i = n; i >= 0; i--) {
    const x = -SHIP_HALF + (2 * SHIP_HALF * i) / n;
    s.lineTo(x, lo(x));
  }
  const g = new THREE.ExtrudeGeometry(s, { depth, bevelEnabled: false, curveSegments: 1 });
  g.translate(0, 0, z0);
  return g;
}

function signTexture() {
  return canvasTexture(1024, 420, (g, w, h) => {
    g.clearRect(0, 0, w, h);
    const cx = w / 2, cy = h + 50, R = 330;
    // Lampochkalar yoyi
    for (let k = -60; k <= 60; k += 4) {
      const a = (-90 + k) * (Math.PI / 180);
      for (const r of [R + 105, R - 100]) {
        g.fillStyle = '#ffe9a0';
        g.beginPath();
        g.arc(cx + r * Math.cos(a), cy + r * Math.sin(a), 6.5, 0, Math.PI * 2);
        g.fill();
      }
    }
    // Harflar yoy bo'ylab
    const text = 'GALLEON';
    g.font = '900 135px Georgia, "Times New Roman", serif';
    g.textAlign = 'center';
    g.textBaseline = 'middle';
    const span = 98;
    for (let i = 0; i < text.length; i++) {
      const k = -span / 2 + (span * i) / (text.length - 1);
      const a = (-90 + k) * (Math.PI / 180);
      g.save();
      g.translate(cx + R * Math.cos(a), cy + R * Math.sin(a));
      g.rotate(a + Math.PI / 2);
      g.lineJoin = 'round';
      g.lineWidth = 20;
      g.strokeStyle = '#fff6e0';
      g.strokeText(text[i], 0, 0);
      g.fillStyle = '#d4202a';
      g.fillText(text[i], 0, 0);
      g.restore();
    }
  });
}

function build() {
  const frame: THREE.BufferGeometry[] = [];
  const bulbs: THREE.BufferGeometry[] = [];
  const steel: THREE.BufferGeometry[] = [];
  const base: THREE.BufferGeometry[] = [];
  const fence: THREE.BufferGeometry[] = [];

  // ---- A-ramalar ----
  for (const sz of [-1, 1]) {
    const z = sz * ZS;
    for (const sx of [-1, 1]) {
      const foot = V(sx * FOOT, 0.2, z);
      const apex = V(sx * 0.5, H + 0.3, z);
      frame.push(colored(rod(foot, apex, 0.34, 6), RED));
      // tayanch plitasi
      frame.push(colored(new THREE.BoxGeometry(1.5, 0.3, 1.5).translate(foot.x, 0.15, z), DARK_RED));
      // lampochkalar (oyoq old yuzasi bo'ylab)
      const len = foot.distanceTo(apex);
      const n = Math.round(len / 0.85);
      for (let i = 1; i < n; i++) {
        const p = foot.clone().lerp(apex, i / n);
        bulbs.push(new THREE.SphereGeometry(0.15, 6, 4).translate(p.x, p.y, z + sz * 0.34));
      }
    }
    // pastki gorizontal to'sin va o'rta bog'lovchi
    frame.push(colored(new THREE.BoxGeometry(2 * FOOT, 0.3, 0.4).translate(0, 0.4, z), DARK_RED));
    // Yuqori qizil blok (o'q ustida)
  }
  frame.push(colored(new THREE.BoxGeometry(2.1, 1.5, 2 * ZS + 1.6).translate(0, H + 0.6, 0), RED));
  frame.push(colored(new THREE.BoxGeometry(1.4, 1.1, 2.8).translate(0, H + 1.9, 0), '#222831'));
  // Yozuv tayanchlari
  for (const sz of [-1, 1]) for (const sx of [-1, 1]) {
    frame.push(colored(rod(V(sx * 2.6, H + 1.2, sz * (ZS + 0.85)), V(sx * 2.6, H + 2.9, sz * (ZS + 0.85)), 0.07, 4), '#555c66'));
  }
  // O'q va gupchaklar
  steel.push(rod(V(0, H, -ZS - 1), V(0, H, ZS + 1), 0.2, 8));
  for (const sz of [-1, 1]) steel.push(new THREE.CylinderGeometry(0.55, 0.55, 0.3, 14).rotateX(Math.PI / 2).translate(0, H, sz * (ZS + 0.95)));

  // ---- Platforma ----
  base.push(colored(new THREE.BoxGeometry(14.8, PLAT_TOP - 0.1, 6.2).translate(0, (PLAT_TOP + 0.1) / 2 - 0.05, 0), '#a31820'));
  // zinapoya (+Z)
  for (let i = 0; i < 3; i++) {
    const h = (PLAT_TOP * (3 - i)) / 3.4;
    base.push(colored(new THREE.BoxGeometry(2.8, h, 0.5).translate(0, h / 2, 3.1 + 0.25 + i * 0.5), i % 2 ? '#8c9096' : '#a31820'));
  }
  // panjara
  const rail = (a: THREE.Vector3, b: THREE.Vector3) => {
    for (const y of [1.0, 0.5]) fence.push(rod(V(a.x, PLAT_TOP + y, a.z), V(b.x, PLAT_TOP + y, b.z), y > 0.9 ? 0.04 : 0.03, 4));
    const len = a.distanceTo(b);
    const n = Math.max(1, Math.round(len / 1.4));
    for (let i = 0; i <= n; i++) {
      const p = a.clone().lerp(b, i / n);
      fence.push(new THREE.BoxGeometry(0.07, 1.0, 0.07).translate(p.x, PLAT_TOP + 0.5, p.z));
    }
  };
  const X = 7.2, Zp = 3.0;
  rail(V(-X, 0, -Zp), V(X, 0, -Zp)); // orqa
  rail(V(-X, 0, -Zp), V(-X, 0, Zp)); // chap
  rail(V(X, 0, -Zp), V(X, 0, Zp)); // o'ng
  rail(V(-X, 0, Zp), V(-1.6, 0, Zp)); // old chap (zinapoya oralig'i ochiq)
  rail(V(1.6, 0, Zp), V(X, 0, Zp));

  return {
    frame: mergeAll(frame),
    bulbs: mergeAll(bulbs),
    steel: mergeAll(steel),
    base: mergeAll(base),
    fence: mergeAll(fence),
    slab: new THREE.BoxGeometry(14.8, 0.12, 6.2).translate(0, PLAT_TOP - 0.04, 0),
    sign: signTexture(),
    ...buildShip(),
  };
}

/** Kema (aylanish markazidan -L pastda quriladi) */
function buildShip() {
  const hull: THREE.BufferGeometry[] = [];
  const trim: THREE.BufferGeometry[] = [];
  const wood: THREE.BufferGeometry[] = [];
  const porthole: THREE.BufferGeometry[] = [];
  const dark: THREE.BufferGeometry[] = [];
  const hang: THREE.BufferGeometry[] = [];
  const Y = -L;

  for (const sz of [-1, 1]) {
    const z0 = sz * WALL_Z - 0.14;
    hull.push(colored(band(bot, top, 0.28, z0).translate(0, Y, 0), RED));
    trim.push(colored(band((x) => top(x) - 0.2, (x) => top(x) + 0.04, 0.42, sz * WALL_Z - 0.21).translate(0, Y, 0), GOLD));
    // iliq-yaltiroq pastki yo'l (ikkinchi oltin chiziq)
    trim.push(colored(band((x) => bot(x) + 0.5, (x) => bot(x) + 0.62, 0.34, sz * WALL_Z - 0.17).translate(0, Y, 0), GOLD));
    // illyuminatorlar
    for (let i = 0; i < 6; i++) {
      const x = -3.5 + i * 1.4;
      const y = Y + (bot(x) + top(x)) / 2 - 0.1;
      const zf = sz * (WALL_Z + 0.16);
      porthole.push(new THREE.TorusGeometry(0.2, 0.05, 5, 14).translate(x, y, zf));
      const d = new THREE.CircleGeometry(0.17, 12);
      if (sz < 0) d.rotateY(Math.PI);
      dark.push(d.translate(x, y, zf + sz * 0.005));
    }
    // osma shtangalar
    for (const sx of [-1, 1]) {
      const px = sx * 3.7;
      const py = Y + top(px) + 0.15;
      hang.push(rod(V(0, 0, sz * 2.35), V(px, py, sz * 2.35), 0.1, 6));
      hang.push(rod(V(px, py, sz * 2.35), V(px, py - 0.5, sz * WALL_Z), 0.1, 5));
    }
  }
  // kema pastki qismi (kil) — ikki devor orasi
  hull.push(colored(band(bot, (x) => bot(x) + 0.5, 3.74, -1.87).translate(0, Y, 0), DARK_RED));
  wood.push(colored(band((x) => bot(x) + 0.5, (x) => bot(x) + 0.58, 3.6, -1.8).translate(0, Y, 0), '#6b4220'));
  // ikki uchidagi yopqich
  for (const sx of [-1, 1]) {
    const x = sx * (SHIP_HALF - 0.08);
    hull.push(colored(new THREE.BoxGeometry(0.2, top(sx * SHIP_HALF) - bot(sx * SHIP_HALF), 3.74).translate(x, Y + (top(sx * SHIP_HALF) + bot(sx * SHIP_HALF)) / 2, 0), RED));
  }
  // o'rindiq qatorlari
  for (let i = 0; i < 7; i++) {
    const x = -3.6 + i * 1.2;
    const d = Y + bot(x) + 0.58;
    wood.push(colored(new THREE.BoxGeometry(0.52, 0.12, 3.1).translate(x, d + 0.45, 0), WOOD));
    wood.push(colored(new THREE.BoxGeometry(0.1, 0.6, 3.1).translate(x + 0.26, d + 0.85, 0), WOOD));
    for (const sz of [-1, 1]) wood.push(colored(new THREE.BoxGeometry(0.4, 0.45, 0.12).translate(x, d + 0.22, sz * 1.3), '#5c3a1c'));
  }
  // yon po'lat tutqichlar
  for (const sz of [-1, 1]) hang.push(rod(V(-3.6, Y + top(-3.6) + 0.55, sz * 1.65), V(3.6, Y + top(3.6) + 0.55, sz * 1.65), 0.04, 4));
  // kormadagi kayuta (ko'k tomli)
  wood.push(colored(new THREE.BoxGeometry(1.5, 1.1, 2.8).translate(-4.55, Y + bot(-4.55) + 0.58 + 0.55, 0), '#7a4a22'));
  wood.push(colored(new THREE.BoxGeometry(1.75, 0.22, 3.1).translate(-4.55, Y + bot(-4.55) + 0.58 + 1.2, 0), '#2f4f9a'));
  // machta (burun tomoni, egik)
  wood.push(colored(rod(V(4.9, Y + top(4.9), 0), V(6.8, Y + top(4.9) + 2.4, 0), 0.07, 5), '#5c3a1c'));

  return {
    hull: mergeAll(hull),
    trim: mergeAll(trim),
    wood: mergeAll(wood),
    porthole: mergeAll(porthole),
    dark: mergeAll(dark),
    hang: mergeAll(hang),
  };
}

/** Tebranish burchagi (radian), vaqtga qarab: tinch → tebranishni kuchaytirish → to'liq → sekinlashish */
export function swingAngle(t: number) {
  const { restSeconds, rampSeconds, holdSeconds, maxDegrees, periodSeconds } = GALLEON;
  const cycle = restSeconds + rampSeconds * 2 + holdSeconds;
  const s = t % cycle;
  const ease = (k: number) => k * k * (3 - 2 * k);
  let env = 0;
  if (s < restSeconds) env = 0;
  else if (s < restSeconds + rampSeconds) env = ease((s - restSeconds) / rampSeconds);
  else if (s < restSeconds + rampSeconds + holdSeconds) env = 1;
  else env = 1 - ease((s - restSeconds - rampSeconds - holdSeconds) / rampSeconds);
  return THREE.MathUtils.degToRad(maxDegrees) * env * Math.sin((2 * Math.PI * t) / periodSeconds);
}

export function Galleon({ pal, selected }: { pal: Palette; selected: boolean }) {
  const m = useMemo(build, []);
  useEffect(() => () => {
    Object.values(m).forEach((v) => (v instanceof THREE.BufferGeometry || v instanceof THREE.Texture) && v.dispose());
  }, [m]);

  const swing = useRef<THREE.Group>(null!);
  const animate = GALLEON.enabled && !prefersReducedMotion();
  useAmbientFrames(animate);
  // Ochilganda kema allaqachon yaxshi tebranib turgan fazada
  const t0 = useRef(performance.now() / 1000 - GALLEON.restSeconds - GALLEON.rampSeconds - 1);
  const angleNow = () => (animate ? swingAngle(performance.now() / 1000 - t0.current + GALLEON.restSeconds + GALLEON.rampSeconds + 1) : 0);

  useLayoutEffect(() => {
    swing.current.rotation.z = angleNow();
  }, [animate]);
  useFrame(() => {
    if (animate) swing.current.rotation.z = angleNow();
  });

  const signGeo = useMemo(() => new THREE.PlaneGeometry(8.2, 3.36), []);
  useEffect(() => () => signGeo.dispose(), [signGeo]);

  return (
    <group>
      <mesh geometry={m.base} castShadow receiveShadow>
        <meshStandardMaterial vertexColors roughness={0.8} />
      </mesh>
      <mesh geometry={m.slab} receiveShadow>
        <meshStandardMaterial color={selected ? pal.selected : '#8c9096'} roughness={0.9} />
      </mesh>
      <mesh geometry={m.fence} castShadow>
        <meshStandardMaterial color={STEEL} roughness={0.5} metalness={0.4} />
      </mesh>
      <mesh geometry={m.frame} castShadow>
        <meshStandardMaterial vertexColors roughness={0.55} metalness={0.2} />
      </mesh>
      <mesh geometry={m.steel} castShadow>
        <meshStandardMaterial color={STEEL} roughness={0.4} metalness={0.6} />
      </mesh>
      <mesh geometry={m.bulbs}>
        <meshBasicMaterial color="#ffe9a0" toneMapped={false} />
      </mesh>
      {[1, -1].map((s) => (
        <mesh key={s} geometry={signGeo} position={[0, H + 4.0, s * (ZS + 0.95)]} rotation-y={s > 0 ? 0 : Math.PI}>
          <meshBasicMaterial map={m.sign} transparent toneMapped={false} depthWrite={false} />
        </mesh>
      ))}
      <group ref={swing} position={[0, H, 0]}>
        <mesh geometry={m.hull} castShadow>
          <meshStandardMaterial vertexColors roughness={0.5} />
        </mesh>
        <mesh geometry={m.trim} castShadow>
          <meshStandardMaterial vertexColors roughness={0.35} metalness={0.4} />
        </mesh>
        <mesh geometry={m.wood} castShadow>
          <meshStandardMaterial vertexColors roughness={0.8} />
        </mesh>
        <mesh geometry={m.porthole}>
          <meshStandardMaterial color={GOLD} roughness={0.3} metalness={0.5} />
        </mesh>
        <mesh geometry={m.dark}>
          <meshStandardMaterial color="#1c120d" roughness={0.4} />
        </mesh>
        <mesh geometry={m.hang} castShadow>
          <meshStandardMaterial color={STEEL} roughness={0.4} metalness={0.6} />
        </mesh>
      </group>
    </group>
  );
}

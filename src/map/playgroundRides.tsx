import { useEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { PLAYGROUND_RIDES } from './config';
import { V, canvasTexture, colored, mergeAll, prefersReducedMotion, rod, useAmbientFrames } from './modelKit';

// Bolalar maydonchasidagi attraksionlar: jeep aylanma yo'li, otli karusel va 4 ta bolalar qurilish texnikasi.
// Boshqa chatda yasalgan modellar. Joylashuv va o'lcham `config.ts` dagi PLAYGROUND_RIDES da (xarita metrlarida).

const bx = (w: number, h: number, d: number, x: number, y: number, z: number, c: string) =>
  colored(new THREE.BoxGeometry(w, h, d).translate(x, y, z), c);
const cyl = (r1: number, r2: number, h: number, x: number, y: number, z: number, c: string, n = 10) =>
  colored(new THREE.CylinderGeometry(r1, r2, h, n).translate(x, y, z), c);
const sph = (r: number, x: number, y: number, z: number, c: string) =>
  colored(new THREE.SphereGeometry(r, 6, 5).translate(x, y, z), c);
const tube = (a: number[], b: number[], r: number, c: string) => colored(rod(V(a[0], a[1], a[2]), V(b[0], b[1], b[2]), r, 5), c);
const GOLD = '#d9a441';

// ---------------------------------------------------------------- Jeep attraksioni

function jeepBody(c: string) {
  const g: THREE.BufferGeometry[] = [
    bx(2.3, 0.42, 1.1, 0, 0.5, 0, c), bx(0.75, 0.3, 1.04, 0.8, 0.86, 0, c), bx(0.1, 0.34, 1.1, 1.2, 0.62, 0, '#16181b'),
    bx(0.9, 0.26, 1.12, -0.15, 0.84, 0, c), bx(0.5, 0.3, 1.1, -0.9, 0.8, 0, c),
    bx(0.5, 0.2, 0.4, -0.4, 0.72, 0.24, '#23282d'), bx(0.5, 0.2, 0.4, -0.4, 0.72, -0.24, '#23282d'),
    bx(0.12, 0.55, 1.0, 0.4, 1.2, 0, '#1c2025'),
    bx(0.9, 0.06, 0.06, -0.12, 1.5, 0.5, '#1c2025'), bx(0.9, 0.06, 0.06, -0.12, 1.5, -0.5, '#1c2025'),
    bx(0.06, 0.9, 0.06, -0.55, 1.05, 0.5, '#1c2025'), bx(0.06, 0.9, 0.06, -0.55, 1.05, -0.5, '#1c2025'),
    bx(0.06, 0.9, 0.06, 0.4, 1.05, 0.5, '#1c2025'), bx(0.06, 0.9, 0.06, 0.4, 1.05, -0.5, '#1c2025'),
    bx(0.06, 0.07, 1.0, -0.55, 1.5, 0, '#1c2025'), bx(0.14, 0.22, 1.2, -1.2, 0.38, 0, '#16181b'),
    sph(0.1, 1.22, 0.74, 0.38, '#fff3c4'), sph(0.1, 1.22, 0.74, -0.38, '#fff3c4'),
  ];
  for (const x of [-0.8, 0.8]) for (const z of [-0.66, 0.66]) {
    g.push(colored(new THREE.CylinderGeometry(0.34, 0.34, 0.24, 12).rotateX(Math.PI / 2).translate(x, 0.34, z), '#15171a'));
    g.push(colored(new THREE.CylinderGeometry(0.17, 0.17, 0.26, 8).rotateX(Math.PI / 2).translate(x, 0.34, z), '#b8bec6'));
  }
  g.push(bx(2.1, 0.05, 1.0, 0, 0.28, 0, '#2a2e33'));
  return mergeAll(g);
}

const JEEP_COLORS = ['#6fd23c', '#d9342b', '#2a86d6', '#e2552a', '#2a86d6', '#f2b01e'];

export function JeepRide() {
  const { x, y, r: R } = PLAYGROUND_RIDES.jeep;
  const m = useMemo(() => {
    const N = 12;
    const P = (k: number): [number, number] => [Math.cos(((k + 0.5) / N) * Math.PI * 2) * (R - 0.15), Math.sin(((k + 0.5) / N) * Math.PI * 2) * (R - 0.15)];
    const B = [
      colored(new THREE.CylinderGeometry(R, R + 0.05, 0.4, N).rotateY(Math.PI / N).translate(0, 0.2, 0), '#8d9298'),
      colored(new THREE.CylinderGeometry(R - 0.35, R - 0.35, 0.46, N).rotateY(Math.PI / N).translate(0, 0.23, 0), '#7b8086'),
      cyl(R * 0.62 + 0.9, R * 0.62 + 0.9, 0.5, 0, 0.25, 0, '#6a6f75', 36),
      cyl(R * 0.62 - 0.9, R * 0.62 - 0.9, 0.54, 0, 0.27, 0, '#8d9298', 36),
      bx(1.0, 0.55, 0.8, 0, 0.7, 0, '#6b6f75'),
    ];
    const M: THREE.BufferGeometry[] = [];
    for (let k = 0; k < N; k++) {
      const [ax, az] = P(k), [cx, cz] = P(k + 1);
      M.push(cyl(0.06, 0.06, 1.25, ax, 1.02, az, GOLD, 6), sph(0.1, ax, 1.68, az, GOLD));
      for (const h of [0.5, 1.52]) M.push(tube([ax, h, az], [cx, h, cz], 0.035, GOLD));
      const len = Math.hypot(cx - ax, cz - az), n = Math.max(2, Math.round(len / 0.26));
      for (let q = 1; q < n; q++) {
        const f = q / n;
        M.push(cyl(0.016, 0.016, 1.02, ax + (cx - ax) * f, 1.01, az + (cz - az) * f, GOLD, 4));
      }
    }
    return { cars: JEEP_COLORS.map(jeepBody), base: mergeAll(B), fence: mergeAll(M) };
  }, [R]);
  useEffect(() => () => { m.cars.forEach((c) => c.dispose()); m.base.dispose(); m.fence.dispose(); }, [m]);

  const refs = useRef<(THREE.Group | null)[]>([]);
  const ang = useRef(0);
  const animate = !prefersReducedMotion();
  useAmbientFrames(animate);
  useFrame(({ clock }, dt) => {
    if (animate) ang.current += Math.min(dt, 0.1) * 0.32;
    refs.current.forEach((g, k) => {
      if (!g) return;
      const a = ang.current + (k / 6) * Math.PI * 2, rr = R * 0.62;
      g.position.set(Math.cos(a) * rr, 0.5, -Math.sin(a) * rr);
      g.rotation.y = a - Math.PI / 2 + Math.PI;
      g.rotation.z = animate ? Math.sin(clock.elapsedTime * 1.8 + k) * 0.012 : 0;
    });
  });

  const s = (R / 4.8) * 0.88;
  return (
    <group position={[x, 0.02, -y]}>
      <mesh geometry={m.base} castShadow receiveShadow><meshStandardMaterial vertexColors roughness={0.85} /></mesh>
      <mesh geometry={m.fence} castShadow><meshStandardMaterial vertexColors roughness={0.4} metalness={0.5} /></mesh>
      {m.cars.map((g, k) => (
        <group key={k} ref={(q) => { refs.current[k] = q; }} scale={[s, s, s]}>
          <mesh geometry={g} castShadow receiveShadow><meshStandardMaterial vertexColors roughness={0.45} metalness={0.1} /></mesh>
        </group>
      ))}
    </group>
  );
}

// ---------------------------------------------------------------- Otli karusel

function horse(c: string, mane: string) {
  const g: THREE.BufferGeometry[] = [
    bx(0.95, 0.38, 0.34, 0, 1.0, 0, c), bx(0.36, 0.62, 0.3, 0.5, 1.3, 0, c).rotateZ(-0.45), bx(0.42, 0.26, 0.26, 0.78, 1.58, 0, c).rotateZ(-0.25),
    bx(0.36, 0.04, 0.26, 1.03, 1.48, 0, c), bx(0.12, 0.24, 0.1, 0.7, 1.78, 0.07, mane), bx(0.12, 0.24, 0.1, 0.7, 1.78, -0.07, mane),
    bx(0.3, 0.3, 0.06, 0.22, 1.43, 0, '#a52a2a'), bx(0.3, 0.06, 0.36, 0.16, 1.22, 0, '#a52a2a'),
    bx(0.22, 0.5, 0.06, -0.55, 1.05, 0, mane).rotateZ(0.5), bx(0.4, 0.12, 0.05, 0.38, 1.62, 0, mane),
  ];
  for (const [x, z] of [[0.34, 0.12], [0.34, -0.12], [-0.34, 0.12], [-0.34, -0.12]]) g.push(bx(0.1, 0.62, 0.1, x, 0.52, z, c), bx(0.12, 0.1, 0.12, x, 0.2, z, '#1a1a1a'));
  return mergeAll(g);
}
const HORSE_COLORS: [string, string][] = [['#c2622c', '#2a1a10'], ['#1d1d1f', '#cfcfcf'], ['#8a4a22', '#e0a43a'], ['#e9e6df', '#444'], ['#b8541e', '#e3a52f'],
  ['#2a2a2c', '#bbb'], ['#7b3d1c', '#2a1a10'], ['#cf6b2c', '#2a1a10'], ['#222', '#c7a24a'], ['#e9e6df', '#8a4a22']];

export function HorseCarousel() {
  const { x, y, r: R } = PLAYGROUND_RIDES.carousel;
  const m = useMemo(() => {
    const N = 8, Rg = R - 0.15, G = '#d6a23c';
    const P = (k: number): [number, number] => [Math.cos(((k + 0.5) / N) * Math.PI * 2) * Rg, Math.sin(((k + 0.5) / N) * Math.PI * 2) * Rg];
    const B = [
      colored(new THREE.CylinderGeometry(R, R + 0.04, 0.28, 8).rotateY(Math.PI / 8).translate(0, 0.14, 0), '#aeb3b8'),
      colored(new THREE.CylinderGeometry(R - 0.5, R - 0.4, 0.14, 8).rotateY(Math.PI / 8).translate(0, 0.35, 0), '#d9d3c4'),
    ];
    const M: THREE.BufferGeometry[] = [];
    for (let k = 0; k < N; k++) {
      const [ax, az] = P(k), [cx, cz] = P(k + 1);
      M.push(cyl(0.06, 0.06, 1.3, ax, 0.93, az, G, 6), sph(0.1, ax, 1.62, az, G));
      for (const h of [0.5, 1.5]) M.push(tube([ax, h, az], [cx, h, cz], 0.035, G));
      const len = Math.hypot(cx - ax, cz - az), n = Math.max(2, Math.round(len / 0.24));
      if (k !== 3) for (let q = 1; q < n; q++) {
        const f = q / n;
        M.push(cyl(0.016, 0.016, 1.0, ax + (cx - ax) * f, 1.0, az + (cz - az) * f, G, 4));
      }
    }
    const T: THREE.BufferGeometry[] = [
      cyl(0.55, 0.8, 0.12, 0, 0.42, 0, '#8a5a2a', 16), cyl(R * 0.82, R * 0.82, 0.1, 0, 0.4, 0, '#a77c4a', 16), cyl(0.5, 0.62, 3.1, 0, 1.95, 0, G),
      cyl(0.62, 0.5, 0.5, 0, 3.3, 0, '#b9852a'), cyl(R * 0.9, R * 0.9, 0.34, 0, 3.55, 0, '#e0b04a', 16), cyl(R * 0.95, R * 0.95, 0.12, 0, 3.35, 0, '#8a5a2a', 16),
      colored(new THREE.ConeGeometry(R * 0.9, 1.05, 16).translate(0, 4.25, 0), '#d9a23c'),
      colored(new THREE.SphereGeometry(0.14, 8, 6).translate(0, 4.85, 0), '#a8582a'), cyl(0.03, 0.03, 0.5, 0, 4.95, 0, '#d6a23c', 5),
    ];
    for (let k = 0; k < 16; k++) {
      const a = (k / 16) * Math.PI * 2;
      T.push(colored(new THREE.SphereGeometry(0.1, 6, 5).translate(Math.cos(a) * R * 0.9, 3.48, Math.sin(a) * R * 0.9), '#e9eef4'));
    }
    const poles = mergeAll(Array.from({ length: 10 }, (_, k) => {
      const a = (k / 10) * Math.PI * 2;
      return cyl(0.035, 0.035, 2.9, Math.cos(a) * R * 0.62, 1.9, Math.sin(a) * R * 0.62, '#c9ced4', 5);
    }));
    const tex = canvasTexture(512, 160, (c, w, h) => {
      const gr = c.createLinearGradient(0, 0, 0, h);
      gr.addColorStop(0, '#79c4e6'); gr.addColorStop(0.55, '#d6ecf2'); gr.addColorStop(0.56, '#2f7a58'); gr.addColorStop(1, '#1d4e3a');
      c.fillStyle = gr; c.fillRect(0, 0, w, h);
      c.fillStyle = '#5d6b78'; c.beginPath(); c.moveTo(60, 90); c.lineTo(190, 20); c.lineTo(270, 90); c.lineTo(340, 40); c.lineTo(460, 90); c.fill();
      c.fillStyle = '#f2f6f8'; c.beginPath(); c.moveTo(165, 36); c.lineTo(190, 20); c.lineTo(215, 40); c.lineTo(190, 34); c.fill();
      c.fillStyle = '#1c6e96'; c.fillRect(0, 100, w, 26);
      c.strokeStyle = '#e0b04a'; c.lineWidth = 14; c.strokeRect(5, 5, w - 10, h - 10);
    });
    return { base: mergeAll(B), fence: mergeAll(M), top: mergeAll(T), poles, horses: HORSE_COLORS.map(([c, mn]) => horse(c, mn)), tex, pan: new THREE.PlaneGeometry(R * 0.82, 0.32) };
  }, [R]);
  useEffect(() => () => {
    m.base.dispose(); m.fence.dispose(); m.top.dispose(); m.poles.dispose(); m.horses.forEach((h) => h.dispose()); m.tex.dispose(); m.pan.dispose();
  }, [m]);

  const rot = useRef<THREE.Group>(null!);
  const hs = useRef<(THREE.Group | null)[]>([]);
  const a0 = useRef(0);
  const animate = !prefersReducedMotion();
  useAmbientFrames(animate);
  useFrame(({ clock }, dt) => {
    if (!animate || !rot.current) return;
    a0.current += Math.min(dt, 0.1) * 0.55;
    rot.current.rotation.y = a0.current;
    hs.current.forEach((g, k) => { if (g) g.position.y = Math.sin(clock.elapsedTime * 1.6 + k * 1.3) * 0.14; });
  });

  return (
    <group position={[x, 0.02, -y]}>
      <mesh geometry={m.base} castShadow receiveShadow><meshStandardMaterial vertexColors roughness={0.8} /></mesh>
      <mesh geometry={m.fence} castShadow><meshStandardMaterial vertexColors roughness={0.4} metalness={0.5} /></mesh>
      <group ref={rot}>
        <mesh geometry={m.top} castShadow receiveShadow><meshStandardMaterial vertexColors roughness={0.5} metalness={0.35} /></mesh>
        <mesh geometry={m.poles} castShadow><meshStandardMaterial vertexColors roughness={0.3} metalness={0.7} /></mesh>
        {m.horses.map((g, k) => {
          const a = (k / 10) * Math.PI * 2, r = R * 0.62;
          return (
            <group key={k} position={[Math.cos(a) * r, 0, -Math.sin(a) * r]} rotation-y={a + Math.PI / 2}>
              <group ref={(q) => { hs.current[k] = q; }}>
                <mesh geometry={g} castShadow receiveShadow><meshStandardMaterial vertexColors roughness={0.55} /></mesh>
              </group>
            </group>
          );
        })}
        {Array.from({ length: 8 }, (_, k) => {
          const a = ((k + 0.5) / 8) * Math.PI * 2, rr = R * 0.9 * Math.cos(Math.PI / 16) * 0.97;
          return (
            <mesh key={k} geometry={m.pan} position={[Math.cos(a) * rr, 3.55, -Math.sin(a) * rr]} rotation-y={a - Math.PI / 2 + Math.PI}>
              <meshBasicMaterial map={m.tex} toneMapped={false} side={THREE.DoubleSide} />
            </mesh>
          );
        })}
      </group>
    </group>
  );
}

// ---------------------------------------------------------------- Bolalar qurilish texnikasi

const Y = '#f4b81e', YD = '#d99a12', K = '#17191c';
const wheel = (r: number, w: number, x: number, y: number, z: number, hub = Y) => [
  colored(new THREE.CylinderGeometry(r, r, w, 14).rotateX(Math.PI / 2).translate(x, y, z), K),
  colored(new THREE.CylinderGeometry(r * 0.55, r * 0.55, w + 0.03, 10).rotateX(Math.PI / 2).translate(x, y, z), hub),
];
const hubOnly = (r: number, w: number, x: number, y: number, z: number) => wheel(r, w, x, y, z).slice(1);
const glass = (w: number, h: number, d: number, x: number, y: number, z: number) => bx(w, h, d, x, y, z, '#1d2a36');

const VEHICLES: (() => THREE.BufferGeometry)[] = [
  // ekskavator
  () => mergeAll([
    bx(1.7, 0.34, 0.38, 0, 0.22, 0.55, '#4b3a86'), bx(1.7, 0.34, 0.38, 0, 0.22, -0.55, '#4b3a86'),
    ...hubOnly(0.2, 0.4, 0.78, 0.24, 0.55), ...hubOnly(0.2, 0.4, 0.78, 0.24, -0.55), ...hubOnly(0.2, 0.4, -0.78, 0.24, 0.55), ...hubOnly(0.2, 0.4, -0.78, 0.24, -0.55),
    bx(1.3, 0.5, 1.1, -0.1, 0.6, 0, Y), bx(0.8, 0.9, 0.95, -0.25, 1.3, 0, Y), glass(0.04, 0.55, 0.8, 0.16, 1.35, 0),
    glass(0.5, 0.55, 0.04, -0.25, 1.35, 0.49), glass(0.5, 0.55, 0.04, -0.25, 1.35, -0.49), bx(0.9, 0.06, 1.05, -0.25, 1.78, 0, YD),
    bx(0.36, 0.2, 0.02, -0.3, 0.62, 0.56, '#c4271f'), tube([0.4, 0.85, 0.2], [1.15, 1.45, 0.2], 0.07, Y), tube([0.4, 0.85, -0.2], [1.15, 1.45, -0.2], 0.07, Y),
    tube([1.15, 1.45, 0], [1.55, 0.7, 0], 0.06, Y), bx(0.14, 0.1, 0.5, 1.15, 1.45, 0, YD), bx(0.5, 0.34, 0.62, 1.65, 0.45, 0, Y), bx(0.2, 0.12, 0.62, 1.9, 0.28, 0, '#8a6a10'),
  ]),
  // old yuklagich
  () => mergeAll([
    bx(1.2, 0.5, 1.0, -0.35, 0.7, 0, Y), bx(0.7, 0.75, 0.92, -0.5, 1.3, 0, Y), glass(0.04, 0.5, 0.74, -0.14, 1.35, 0),
    glass(0.5, 0.5, 0.04, -0.5, 1.35, 0.47), glass(0.5, 0.5, 0.04, -0.5, 1.35, -0.47), bx(0.8, 0.06, 1.0, -0.5, 1.7, 0, YD), bx(0.62, 0.36, 0.9, 0.3, 0.86, 0, Y),
    ...wheel(0.38, 0.28, 0.62, 0.38, 0.66), ...wheel(0.38, 0.28, 0.62, 0.38, -0.66), ...wheel(0.38, 0.28, -0.62, 0.38, 0.66), ...wheel(0.38, 0.28, -0.62, 0.38, -0.66),
    tube([0.1, 0.9, 0.5], [1.0, 0.55, 0.6], 0.05, Y), tube([0.1, 0.9, -0.5], [1.0, 0.55, -0.6], 0.05, Y),
    bx(0.14, 0.5, 1.22, 1.12, 0.45, 0, '#5a3a8a'), bx(0.34, 0.04, 1.22, 1.25, 0.18, 0, '#cfd2d6'), bx(0.3, 0.4, 0.05, 1.15, 0.45, 0.62, Y), bx(0.3, 0.4, 0.05, 1.15, 0.45, -0.62, Y),
    bx(0.06, 0.08, 0.05, 1.3, 0.12, 0.5, '#cfd2d6'), bx(0.06, 0.08, 0.05, 1.3, 0.12, -0.5, '#cfd2d6'),
  ]),
  // yo'l katogi
  () => mergeAll([
    colored(new THREE.CylinderGeometry(0.46, 0.46, 0.62, 16).rotateX(Math.PI / 2).translate(0.85, 0.46, 0.34), '#aeb4ba'),
    colored(new THREE.CylinderGeometry(0.46, 0.46, 0.62, 16).rotateX(Math.PI / 2).translate(0.85, 0.46, -0.34), '#a1a8ae'), bx(0.18, 0.16, 1.34, 0.85, 0.46, 0, K),
    bx(0.18, 0.7, 0.1, 0.85, 0.7, 0.72, Y), bx(0.18, 0.7, 0.1, 0.85, 0.7, -0.72, Y), bx(1.1, 0.45, 0.9, -0.15, 0.8, 0, Y), bx(0.62, 0.38, 0.78, 0.5, 0.85, 0, Y),
    bx(0.4, 0.45, 0.5, -0.4, 1.2, 0, K), bx(0.5, 0.06, 0.85, -0.4, 1.85, 0, YD),
    tube([-0.1, 1.0, 0.4], [-0.1, 1.85, 0.4], 0.04, K), tube([-0.1, 1.0, -0.4], [-0.1, 1.85, -0.4], 0.04, K),
    tube([-0.65, 1.0, 0.4], [-0.65, 1.85, 0.4], 0.04, K), tube([-0.65, 1.0, -0.4], [-0.65, 1.85, -0.4], 0.04, K),
    ...wheel(0.45, 0.26, -0.55, 0.46, 0.7), ...wheel(0.45, 0.26, -0.55, 0.46, -0.7), bx(0.05, 0.1, 0.5, 1.08, 0.95, 0, '#c4271f'), bx(0.1, 0.1, 1.4, 1.15, 0.14, 0, '#c4271f'),
  ]),
  // samosval
  () => mergeAll([
    bx(1.9, 0.28, 0.82, 0, 0.45, 0, K), bx(0.8, 0.78, 1.0, 0.7, 1.0, 0, Y), glass(0.04, 0.34, 0.86, 1.1, 1.14, 0), bx(0.06, 0.34, 0.8, 1.12, 0.66, 0, K),
    bx(0.05, 0.1, 0.8, 1.13, 0.84, 0, '#c4271f'), sph(0.07, 1.12, 0.7, 0.38, '#ffffff'), sph(0.07, 1.12, 0.7, -0.38, '#ffffff'),
    bx(1.12, 0.12, 1.04, -0.55, 0.64, 0, YD), bx(1.12, 0.5, 0.08, -0.55, 0.92, 0.52, Y), bx(1.12, 0.5, 0.08, -0.55, 0.92, -0.52, Y), bx(0.08, 0.5, 1.04, -1.1, 0.92, 0, Y),
    bx(0.08, 0.62, 1.04, 0, 1.0, 0, Y), ...wheel(0.36, 0.28, 0.7, 0.36, 0.54), ...wheel(0.36, 0.28, 0.7, 0.36, -0.54), ...wheel(0.36, 0.28, -0.65, 0.36, 0.54), ...wheel(0.36, 0.28, -0.65, 0.36, -0.54),
    bx(0.25, 0.08, 0.9, 1.2, 0.28, 0, K),
  ]),
];

export function ConstructionVehicles() {
  const geos = useMemo(() => VEHICLES.map((f) => f()), []);
  useEffect(() => () => geos.forEach((g) => g.dispose()), [geos]);
  return (
    <>
      {PLAYGROUND_RIDES.vehicles.map(([x, y, a, t], k) => (
        <mesh key={k} geometry={geos[t]} position={[x, 0.02, -y]} rotation-y={a} scale={1.05} castShadow receiveShadow>
          <meshStandardMaterial vertexColors roughness={0.5} metalness={0.08} />
        </mesh>
      ))}
    </>
  );
}

import { useEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { canvasTexture, colored, mergeAll, useAmbientFrames } from './modelKit';

// Favora maydoni (pushti granit havza, o'rtada haykal, 9 ta suv oqimi, atrofida toshli halqalar va skameykalar)
// va unga tushuvchi 4 pog'onali sharshara. Koordinatalar xarita metrlarida: dunyoda (x, y) → (x, -y).

const CX = -78.3, CY = 119.9;
const A: [number, number] = [-104.0, 148.6]; // yo'llar tutashgan joy (sharshara boshi)
const B: [number, number] = [-85.4, 126.0]; // favora tomon
// [balandlik, chuqurlik, kenglik] — yuqoridan pastga
const TIERS: [number, number, number][] = [[3.2, 4.6, 5.2], [2.3, 4.6, 5.0], [1.5, 4.4, 4.6], [0.8, 4.2, 4.2]];

const ring = (r1: number, r0: number, y: number, h: number, n = 56) => {
  const s = new THREE.Shape().absarc(0, 0, r1, 0, Math.PI * 2, false);
  if (r0 > 0) s.holes.push(new THREE.Path().absarc(0, 0, r0, 0, Math.PI * 2, true));
  return new THREE.ExtrudeGeometry(s, { depth: h, bevelEnabled: false, curveSegments: n }).rotateX(-Math.PI / 2).translate(0, y, 0);
};

function waterMat(c: string, op = 0.85) {
  return new THREE.MeshStandardMaterial({ color: c, roughness: 0.12, metalness: 0.1, transparent: true, opacity: op });
}

function buildPlaza() {
  const bx = (w: number, h: number, d: number, x: number, y: number, z: number, c: string) => colored(new THREE.BoxGeometry(w, h, d).translate(x, y, z), c);
  const cy = (r1: number, r2: number, h: number, x: number, y: number, z: number, c: string, n = 12) => colored(new THREE.CylinderGeometry(r1, r2, h, n).translate(x, y, z), c);
  const y0 = 0.67;
  const statue = mergeAll([
    cy(1.05, 1.3, 0.9, 0, y0 + 0.45, 0, '#cdbba8'), cy(0.8, 1.05, 0.3, 0, y0 + 1.05, 0, '#d9c9b4'), cy(0.45, 0.6, 1.0, 0, y0 + 1.7, 0, '#e9dfcf'),
    cy(0.38, 0.3, 1.25, 0, y0 + 2.8, 0, '#efe7d8', 10),
    colored(new THREE.SphereGeometry(0.24, 10, 8).translate(0, y0 + 3.62, 0), '#efe7d8'),
    cy(0.1, 0.16, 0.5, 0.3, y0 + 4.05, 0, '#d8cfbe', 8), cy(0.1, 0.16, 0.5, -0.3, y0 + 4.05, 0, '#d8cfbe', 8),
    colored(new THREE.SphereGeometry(0.3, 10, 8).scale(1, 1.3, 1).translate(0, y0 + 4.45, 0), '#d8cfbe'),
  ]);
  const bench = () => mergeAll([
    bx(1.6, 0.07, 0.5, 0, 0.45, 0, '#9a6b44'), bx(1.6, 0.5, 0.06, -0.22, 0.78, 0, '#9a6b44').rotateZ(-0.12),
    bx(0.07, 0.45, 0.4, -0.65, 0.22, 0, '#3b4046'), bx(0.07, 0.45, 0.4, 0.65, 0.22, 0, '#3b4046'),
  ]);
  const benches = mergeAll([0, 1, 2, 3].map((k) => {
    const a = 0.1 + (k * Math.PI) / 2 + Math.PI / 4;
    return bench().rotateY(-a + Math.PI / 2 + Math.PI / 2).translate(Math.cos(a) * 7.3, 0.12, -Math.sin(a) * 7.3);
  }));
  return {
    pave1: ring(5.62, 5.55, 0.14, 0.02), pave2: ring(6.82, 6.75, 0.14, 0.02),
    rim: ring(4.75, 4.1, 0.12, 0.75), rimT: ring(4.75, 4.35, 0.87, 0.05),
    floor: ring(4.1, 0, 0.14, 0.04), water: ring(4.1, 0, 0.5, 0.06), disc: ring(7, 0, 0.1, 0.035),
    statue, benches, jet: new THREE.CylinderGeometry(0.03, 0.06, 1, 6).translate(0, 0.5, 0),
  };
}

function buildFall() {
  const dx = B[0] - A[0], dy = B[1] - A[1], L = Math.hypot(dx, dy), ang = Math.atan2(dy, dx);
  const tiers = TIERS.map(([h, d, w], k) => {
    const t = 0.1 + k * 0.2, x = A[0] + dx * t, y = A[1] + dy * t;
    return { h, d, w, x, y };
  });
  const RK = ['#7d7a70', '#8b8678', '#6e6b62', '#94907f'];
  let sd = 17; const rnd = () => ((sd = (sd * 16807) % 2147483647) / 2147483647);
  const blocks = tiers.map((t, k) => {
    const g: THREE.BufferGeometry[] = [colored(new THREE.BoxGeometry(t.d, t.h - 0.2, t.w).translate(0, (t.h - 0.2) / 2, 0), '#827d70'),
      colored(new THREE.BoxGeometry(t.d, 0.4, 0.34).translate(0, t.h + 0.03, t.w / 2 - 0.17), '#8f8a7b'),
      colored(new THREE.BoxGeometry(t.d, 0.4, 0.34).translate(0, t.h + 0.03, -t.w / 2 + 0.17), '#8f8a7b'),
      colored(new THREE.BoxGeometry(0.34, 0.4, t.w).translate(-t.d / 2 + 0.17, t.h + 0.03, 0), '#8f8a7b')];
    for (let q = 0; q < 9; q++) {
      const sz = 0.5 + rnd() * 0.55;
      g.push(colored(new THREE.IcosahedronGeometry(sz, 0).scale(1.2, 0.8, 1).translate(-t.d / 2 + rnd() * t.d, t.h * 0.4 * rnd() + sz * 0.5, (rnd() < 0.5 ? -1 : 1) * (t.w / 2 + 0.1 + rnd() * 0.5)), RK[(q + k) % 4]));
    }
    return mergeAll(g).rotateY(-ang).translate(t.x, 0, -t.y);
  });
  const waters = tiers.map((t) => new THREE.PlaneGeometry(t.d - 0.5, t.w - 0.7).rotateX(-Math.PI / 2).translate(0.1, t.h - 0.02, 0).rotateY(-ang).translate(t.x, 0, -t.y));
  const falls = tiers.map((t, k) => {
    const nh = k + 1 < tiers.length ? tiers[k + 1].h : 0.1, hh = t.h - nh + 0.15;
    const fx = t.x + Math.cos(ang) * (t.d / 2 + 0.03), fy = t.y + Math.sin(ang) * (t.d / 2 + 0.03);
    return { g: new THREE.PlaneGeometry(t.w - 0.8, hh).rotateY(Math.PI / 2).rotateY(-ang).translate(fx, nh - 0.1 + hh / 2, -fy), hh };
  });
  const last = tiers[tiers.length - 1];
  const bc: [number, number] = [last.x + Math.cos(ang) * (last.d / 2 + 2.6), last.y + Math.sin(ang) * (last.d / 2 + 2.6)];
  const brocks: THREE.BufferGeometry[] = [];
  for (let q = 0; q < 22; q++) {
    const an = (q / 22) * Math.PI * 2, r = 2.7 + rnd() * 0.5;
    brocks.push(colored(new THREE.IcosahedronGeometry(0.4 + rnd() * 0.55, 0).scale(1.1, 0.7, 1).translate(bc[0] + Math.cos(an) * r, 0.25, -(bc[1] + Math.sin(an) * r)), RK[q % 4]));
  }
  const tex = canvasTexture(64, 256, (c, w, h) => {
    c.fillStyle = '#9fd6ea'; c.fillRect(0, 0, w, h);
    for (let q = 0; q < 26; q++) { const x = rnd() * w, y = rnd() * h, l = 30 + rnd() * 60; c.fillStyle = 'rgba(255,255,255,.75)'; c.fillRect(x, y, 3, l); }
  });
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  return { blocks: mergeAll(blocks), waters, falls, bc, brocks: mergeAll(brocks), pool: ring(2.6, 0, 0.1, 0.04).translate(bc[0], 0, -bc[1]), tex, L };
}

export function Fountain() {
  const p = useMemo(buildPlaza, []);
  const f = useMemo(buildFall, []);
  const jets = useRef<(THREE.Mesh | null)[]>([]);
  const wm = useMemo(() => waterMat('#43b0c8', 0.9), []);
  const fm = useMemo(() => new THREE.MeshBasicMaterial({ map: f.tex, transparent: true, opacity: 0.8, side: THREE.DoubleSide }), [f]);
  useAmbientFrames(true);
  useEffect(() => () => {
    Object.values(p).forEach((g) => g.dispose()); f.blocks.dispose(); f.brocks.dispose(); f.pool.dispose(); f.waters.forEach((g) => g.dispose()); f.falls.forEach((x) => x.g.dispose()); f.tex.dispose(); wm.dispose(); fm.dispose();
  }, [p, f, wm, fm]);
  useFrame(({ clock }) => {
    const t = clock.elapsedTime;
    f.tex.offset.y = -t * 0.9;
    jets.current.forEach((m, k) => {
      if (!m) return;
      const s = 0.35 + 0.65 * (0.5 + 0.5 * Math.sin(t * 2.2 + k * 1.9));
      m.scale.y = (k === 0 ? 3.0 : 1.6) * s;
      (m.material as THREE.MeshBasicMaterial).opacity = 0.45 + 0.35 * s;
    });
  });
  const jetPos: [number, number][] = [[0, 0], ...Array.from({ length: 8 }, (_, k) => [Math.cos((k / 8) * 6.283) * 2.6, Math.sin((k / 8) * 6.283) * 2.6] as [number, number])];
  return (
    <group>
      <group position={[CX, 0, -CY]}>
        <mesh geometry={p.disc} receiveShadow><meshStandardMaterial color="#b8b1a3" roughness={1} /></mesh>
        <mesh geometry={p.pave1} receiveShadow><meshStandardMaterial color="#8a8174" roughness={1} /></mesh>
        <mesh geometry={p.pave2} receiveShadow><meshStandardMaterial color="#8a8174" roughness={1} /></mesh>
        <mesh geometry={p.rim} castShadow receiveShadow><meshStandardMaterial color="#a8645c" roughness={0.45} metalness={0.12} /></mesh>
        <mesh geometry={p.rimT} receiveShadow><meshStandardMaterial color="#c07a70" roughness={0.4} metalness={0.15} /></mesh>
        <mesh geometry={p.floor} receiveShadow><meshStandardMaterial color="#e9e4d6" roughness={0.9} /></mesh>
        <mesh geometry={p.water} material={wm} receiveShadow />
        <mesh geometry={p.statue} castShadow><meshStandardMaterial vertexColors roughness={0.7} /></mesh>
        {jetPos.map(([x, z], k) => (
          <mesh key={k} ref={(m) => { jets.current[k] = m; }} geometry={p.jet} position={[x, 0.55, z]}>
            <meshBasicMaterial color="#e6f6ff" transparent opacity={0.6} />
          </mesh>
        ))}
      </group>
      <mesh geometry={p.benches} position={[CX, 0, -CY]} castShadow><meshStandardMaterial vertexColors roughness={0.8} /></mesh>
      <mesh geometry={f.blocks} castShadow receiveShadow><meshStandardMaterial vertexColors roughness={0.9} /></mesh>
      {f.waters.map((g, i) => <mesh key={i} geometry={g} material={wm} />)}
      {f.falls.map((x, i) => <mesh key={i} geometry={x.g} material={fm} />)}
      <mesh geometry={f.pool} material={wm} />
      <mesh geometry={f.brocks} castShadow><meshStandardMaterial vertexColors roughness={0.9} /></mesh>
    </group>
  );
}

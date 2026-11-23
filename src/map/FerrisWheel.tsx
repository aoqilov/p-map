import { useEffect, useLayoutEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { FERRIS_WHEEL } from './config';
import { merge } from './geometry';
import { V, colored, prefersReducedMotion, rod, useAmbientFrames } from './modelKit';
import type { Palette } from './theme';

// Lokal koordinata: g'ildirak tekisligi = XY (Y yuqoriga), o'q = Z.
// Butun guruh Y atrofida burilib, o'q `axisBearing` yo'nalishiga qaratiladi.

const ring = (radius: number, tube: number, z: number) => {
  const g = new THREE.TorusGeometry(radius, tube, 6, 120);
  g.translate(0, 0, z);
  return g;
};

function buildWheel() {
  const { diameter, hubHeight: H, depth: D, cabins: N, pavilionRadius: PR } = FERRIS_WHEEL;
  const R = diameter / 2;
  const half = D / 2;

  // --- Aylanadigan qism (markaz 0,0,0 da) ---
  const rotor: THREE.BufferGeometry[] = [];
  const inner = R * 0.9;
  for (const z of [-half, half]) {
    rotor.push(ring(R, 0.22, z), ring(inner, 0.12, z));
  }
  for (let i = 0; i < N; i++) {
    const a = (i / N) * Math.PI * 2;
    const a2 = ((i + 0.5) / N) * Math.PI * 2;
    const p = (r: number, ang: number, z: number) => V(Math.cos(ang) * r, Math.sin(ang) * r, z);
    rotor.push(rod(p(R, a, -half), p(R, a, half), 0.1)); // gardishlar orasidagi to'sin
    for (const z of [-half, half]) {
      rotor.push(rod(p(R, a, z), p(inner, a2, z), 0.07)); // ferma diagonali
      rotor.push(rod(p(R, a2, z), p(inner, a2, z), 0.06));
      // Kesishgan tros-spitsalar: markazdan urinma bo'ylab ichki halqaga
      rotor.push(rod(p(1.1, a, z * 1.25), p(inner, a + 0.42, z), 0.035, 3));
    }
  }

  // --- Qo'zg'almas qism: tayanch oyoqlari, o'q, pavilon ---
  const frame: THREE.BufferGeometry[] = [];
  const spread = R * 0.55;
  const zb = half + 4;
  for (const side of [-1, 1]) {
    const top = V(0, H, side * (half + 0.9));
    const feet = [V(-spread, 0, side * zb), V(spread, 0, side * zb)];
    feet.forEach((f) => frame.push(rod(top, f, 0.32, 8)));
    const mid = (k: number) => feet.map((f) => top.clone().lerp(f, k));
    for (const k of [0.45, 0.8]) {
      const [l, r] = mid(k);
      frame.push(rod(l, r, 0.14, 6));
    }
  }
  // Ikki tomondagi oyoqlarni bog'lovchi ko'ndalang tirgaklar
  for (const sx of [-1, 1]) {
    for (const k of [0.55, 0.85]) {
      const a = V(0, H, -(half + 0.9)).lerp(V(sx * spread, 0, -zb), k);
      const b = V(0, H, half + 0.9).lerp(V(sx * spread, 0, zb), k);
      frame.push(rod(a, b, 0.12, 6));
    }
  }
  frame.push(rod(V(0, H, -(half + 1.2)), V(0, H, half + 1.2), 0.45, 12)); // o'q

  const hub = new THREE.CylinderGeometry(1.3, 1.3, D + 0.5, 20).rotateX(Math.PI / 2);

  const pavilionBody = new THREE.CylinderGeometry(PR, PR, 3.4, 48).translate(0, 1.7, 0);
  const pavilionGlass = new THREE.CylinderGeometry(PR + 0.06, PR + 0.06, 1.7, 48, 1, true).translate(0, 1.55, 0);
  const pavilionRoof = new THREE.CylinderGeometry(PR + 0.4, PR + 0.4, 0.35, 48).translate(0, 3.55, 0);

  // Kabina: sariq korpus + qora deraza tasmasi + oq tom (vertex rang bilan bitta geometriya)
  const cabin = merge([
    colored(new THREE.BoxGeometry(1.6, 1.9, 1.5), '#f7c21a'),
    colored(new THREE.BoxGeometry(1.66, 0.75, 1.56).translate(0, 0.2, 0), '#26303d'),
    colored(new THREE.BoxGeometry(1.25, 0.22, 1.2).translate(0, 1.06, 0), '#f4f6f9'),
  ]);

  return { rotor: merge(rotor), frame: merge(frame), hub, pavilionBody, pavilionGlass, pavilionRoof, cabin, R, H, N };
}

/** Modelning tabiiy (masshtabsiz) o'lchami — o'lcham sinfiga sig'dirish uchun */
export const FERRIS_WHEEL_NATURAL = {
  height: FERRIS_WHEEL.hubHeight + FERRIS_WHEEL.diameter / 2 + 1.3 + 1.1,
  footprint: FERRIS_WHEEL.diameter + 2 * 2.1,
};

/** Lokal markazda (0,0,0) quriladi; joylash, burish va masshtab — attractions.tsx dagi o'ram */
export function FerrisWheel({ pal, selected }: { pal: Palette; selected: boolean }) {
  const w = useMemo(buildWheel, []);
  useEffect(() => () => Object.values(w).forEach((g) => g instanceof THREE.BufferGeometry && g.dispose()), [w]);

  const rotor = useRef<THREE.Group>(null!);
  const cabins = useRef<THREE.InstancedMesh>(null!);

  const speed = FERRIS_WHEEL.secondsPerTurn > 0 ? (Math.PI * 2) / FERRIS_WHEEL.secondsPerTurn : 0;
  const spinning = speed > 0 && !prefersReducedMotion();
  const cabinRadius = w.R + 1.3; // kabinalar gardishdan tashqarida, doim tik holatda

  const place = (angle: number) => {
    const m = new THREE.Matrix4();
    for (let i = 0; i < w.N; i++) {
      const a = angle + (i / w.N) * Math.PI * 2;
      m.makeTranslation(Math.cos(a) * cabinRadius, w.H + Math.sin(a) * cabinRadius, 0);
      cabins.current.setMatrixAt(i, m);
    }
    cabins.current.instanceMatrix.needsUpdate = true;
    rotor.current.rotation.z = angle;
  };

  useLayoutEffect(() => place(0.1), []); // eslint-disable-line react-hooks/exhaustive-deps

  useAmbientFrames(spinning);

  useFrame(() => {
    if (spinning) place(-(performance.now() / 1000) * speed);
  });

  return (
    <group>
      <mesh geometry={w.frame} castShadow receiveShadow>
        <meshStandardMaterial color={pal.wheel} roughness={0.5} metalness={0.2} />
      </mesh>
      <group ref={rotor} position-y={w.H}>
        <mesh geometry={w.rotor} castShadow>
          <meshStandardMaterial color={pal.wheel} roughness={0.5} metalness={0.2} />
        </mesh>
        <mesh geometry={w.hub} castShadow>
          <meshStandardMaterial color={selected ? pal.selected : '#f7c21a'} roughness={0.4} />
        </mesh>
      </group>
      <instancedMesh ref={cabins} args={[w.cabin, undefined, w.N]} castShadow>
        <meshStandardMaterial vertexColors roughness={0.45} />
      </instancedMesh>
      <mesh geometry={w.pavilionBody} castShadow receiveShadow>
        <meshStandardMaterial color={pal.wheel} />
      </mesh>
      <mesh geometry={w.pavilionGlass}>
        <meshStandardMaterial color="#2a4560" roughness={0.15} metalness={0.3} side={THREE.DoubleSide} />
      </mesh>
      <mesh geometry={w.pavilionRoof} castShadow receiveShadow>
        <meshStandardMaterial color={selected ? pal.selected : pal.wheel} />
      </mesh>
    </group>
  );
}

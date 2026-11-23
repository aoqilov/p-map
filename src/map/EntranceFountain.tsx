// Gen plandagi fontanlar (masalan, 9 — mashina kirishidagi fontan) va gulzorlar.
// Fontan: sakkiz qirrali granit havza (plandagidek), suv, markazda pog'onali poydevor va suv oqimlari.
import { useEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { WATER } from './config';
import { extrude, polyToShape, toWorld } from './geometry';
import { colored, mergeAll, prefersReducedMotion, useAmbientFrames } from './modelKit';
import type { Palette } from './theme';
import type { ParkData } from './types';

const RIM_H = 0.55; // havza devori balandligi, m
const WATER_Y = 0.4;

/** Sakkiz qirrali halqa (tashqi r1, ichki r0), qirrasi plandagidek 22.5° ga burilgan */
function octRing(r1: number, r0: number, y: number, h: number) {
  const oct = (r: number) => Array.from({ length: 8 }, (_, k) => {
    const a = Math.PI / 8 + (k * Math.PI) / 4;
    return new THREE.Vector2(Math.cos(a) * r, Math.sin(a) * r);
  });
  const s = new THREE.Shape(oct(r1));
  if (r0 > 0) s.holes.push(new THREE.Path(oct(r0).reverse()));
  return new THREE.ExtrudeGeometry(s, { depth: h, bevelEnabled: false }).rotateX(-Math.PI / 2).translate(0, y, 0);
}

function buildFountain(r: number) {
  const cyl = (r1: number, r2: number, h: number, y: number, c: string, n = 16) =>
    colored(new THREE.CylinderGeometry(r1, r2, h, n).translate(0, y + h / 2, 0), c);
  const stone = mergeAll([
    colored(octRing(r, r - 0.45, 0, RIM_H), '#9c8f84'), // havza devori
    colored(octRing(r + 0.05, r - 0.5, RIM_H, 0.08), '#b9ada0'), // devor qopqog'i
    colored(octRing(r - 0.45, 0, 0, 0.1), '#6f7d86'), // havza tubi
    cyl(r * 0.24, r * 0.27, 0.55, 0, '#b3a596', 8), // markaziy poydevor (plandagi kichik sakkiz qirra)
    cyl(r * 0.14, r * 0.18, 0.5, 0.55, '#c8bcae', 8),
    cyl(r * 0.07, r * 0.1, 0.6, 1.05, '#d6ccbf', 12),
  ]);
  const water = new THREE.CircleGeometry(r - 0.45, 32).rotateX(-Math.PI / 2).translate(0, WATER_Y, 0);
  const jet = new THREE.CylinderGeometry(0.03, 0.07, 1, 6).translate(0, 0.5, 0);
  return { stone, water, jet };
}

function FountainView({ at, r }: { at: [number, number]; r: number }) {
  const g = useMemo(() => buildFountain(r), [r]);
  const animate = WATER.animate && !prefersReducedMotion();
  useAmbientFrames(animate);
  const jets = useRef<(THREE.Mesh | null)[]>([]);
  useEffect(() => () => { g.stone.dispose(); g.water.dispose(); g.jet.dispose(); }, [g]);
  useFrame(({ clock }) => {
    if (!animate) return;
    const t = clock.elapsedTime;
    jets.current.forEach((m, k) => {
      if (!m) return;
      const s = 0.55 + 0.45 * (0.5 + 0.5 * Math.sin(t * 2 + k * 1.7));
      m.scale.y = (k === 0 ? 4.2 : 1.9) * s;
    });
  });
  // Markaziy oqim + havza ichida aylana bo'ylab 8 ta oqim (poydevorga qarab)
  const jetPos: [number, number][] = [[0, 0], ...Array.from({ length: 8 }, (_, k) => {
    const a = (k / 8) * Math.PI * 2;
    return [Math.cos(a) * r * 0.62, Math.sin(a) * r * 0.62] as [number, number];
  })];
  return (
    <group position={toWorld(at)}>
      <mesh geometry={g.stone} castShadow receiveShadow><meshStandardMaterial vertexColors roughness={0.6} /></mesh>
      <mesh geometry={g.water} receiveShadow>
        <meshStandardMaterial color="#4fb3d1" roughness={0.1} metalness={0.1} transparent opacity={0.88} />
      </mesh>
      {jetPos.map(([x, y], k) => (
        <mesh key={k} ref={(m) => { jets.current[k] = m; }} geometry={g.jet}
          position={[x, k === 0 ? 1.65 : WATER_Y, -y]} scale-y={k === 0 ? 3 : 1.4}>
          <meshBasicMaterial color="#e8f7ff" transparent opacity={0.7} />
        </mesh>
      ))}
    </group>
  );
}

export function Fountains({ data }: { data: ParkData }) {
  return <>{(data.fountains ?? []).map((f) => <FountainView key={f.id} at={f.at} r={f.r} />)}</>;
}

/** Gulzorlar: past bordyurli tuproq + gullar (bitta geometriya, bitta draw call) */
export function FlowerBeds({ data, pal }: { data: ParkData; pal: Palette }) {
  const geom = useMemo(() => {
    const beds = data.beds ?? [];
    if (!beds.length) return null;
    return mergeAll(beds.map((poly) => colored(extrude(polyToShape(poly), 0.22), pal.flowerBed)));
  }, [data, pal]);
  useEffect(() => () => geom?.dispose(), [geom]);
  if (!geom) return null;
  return (
    <mesh geometry={geom} rotation-x={-Math.PI / 2} receiveShadow>
      <meshStandardMaterial vertexColors roughness={0.9} />
    </mesh>
  );
}

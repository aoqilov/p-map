import { useEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { colored, mergeAll, useAmbientFrames } from './modelKit';

// "Dam olish" fontani: to'q marmar havza, ustida 8 ta granit poydevor va shar, markazda va atrofida suv oqimlari,
// atrofida 4 ta sariq skameyka va 2 ta axlat qutisi. Xarita metrlarida (x, y) → dunyoda (x, -y).
export const DAM_FOUNTAIN_AT: [number, number] = [-19, 130];
const SC = 1.2, MARBLE = '#3e4044', MARBLE2 = '#4a4c50', GRANITE = '#8f8c82', YEL = '#d99a2b', DARK = '#1f2227';

const bx = (w: number, h: number, d: number, x: number, y: number, z: number, c: string, ry = 0) =>
  colored(new THREE.BoxGeometry(w, h, d).rotateY(ry).translate(x, y, z), c);

function build() {
  const NR = 40, g: THREE.BufferGeometry[] = [];
  for (let i = 0; i < NR; i++) {
    const a = ((i + 0.5) * Math.PI * 2) / NR;
    g.push(bx(0.93, 0.4, 2 * 3.98 * Math.sin(Math.PI / NR) + 0.03, Math.cos(a) * 3.515, 0.32, Math.sin(a) * 3.515, MARBLE, -a));
    g.push(bx(0.45, 0.18, 2 * 4.35 * Math.sin(Math.PI / NR) + 0.03, Math.cos(a) * 4.125, 0.21, Math.sin(a) * 4.125, MARBLE2, -a));
  }
  for (let k = 0; k < 8; k++) {
    const a = ((k + 0.5) * Math.PI * 2) / 8 + 0.1, x = Math.cos(a) * 3.5, z = Math.sin(a) * 3.5;
    g.push(bx(0.55, 0.48, 0.55, x, 0.76, z, GRANITE, -a), bx(0.63, 0.06, 0.63, x, 1.03, z, '#9a978c', -a));
    g.push(colored(new THREE.SphereGeometry(0.25, 14, 10).translate(x, 1.26, z), GRANITE));
  }
  g.push(colored(new THREE.CylinderGeometry(3.07, 3.07, 0.3, 48).translate(0, 0.2, 0), '#2e3a2c'));
  // skameykalar va axlat qutilari
  for (let k = 0; k < 4; k++) {
    const a = Math.PI / 4 + (k * Math.PI) / 2 + 0.35, r = 5.9, ry = Math.atan2(-Math.cos(a), -Math.sin(a));
    const parts = [
      bx(1.9, 0.05, 0.34, 0, 0.5, 0, YEL), bx(1.9, 0.34, 0.04, 0, 0.82, -0.26, YEL),
      bx(0.05, 0.5, 0.46, -0.88, 0.25, 0, DARK), bx(0.05, 0.5, 0.46, 0.88, 0.25, 0, DARK),
    ].map((p) => p.rotateY(ry).translate(Math.cos(a) * r, 0.14, Math.sin(a) * r));
    g.push(...parts);
  }
  [0.9, 3.5].forEach((a) => {
    const x = Math.cos(a) * 5.2, z = Math.sin(a) * 5.2;
    g.push(bx(0.38, 0.75, 0.38, x, 0.52, z, '#d9dde0'), bx(0.4, 0.08, 0.4, x, 0.94, z, '#8d949a'));
  });
  return mergeAll(g);
}

export function DamFountain() {
  const geo = useMemo(build, []);
  const water = useMemo(() => new THREE.CylinderGeometry(3.02, 3.02, 0.02, 48).translate(0, 0.37, 0), []);
  const jet = useMemo(() => new THREE.CylinderGeometry(0.03, 0.05, 1, 6).translate(0, 0.5, 0), []);
  const jets = useRef<(THREE.Mesh | null)[]>([]);
  useAmbientFrames(true);
  useEffect(() => () => { geo.dispose(); water.dispose(); jet.dispose(); }, [geo, water, jet]);
  useFrame(({ clock }) => {
    const t = clock.elapsedTime;
    jets.current.forEach((m, k) => {
      if (!m) return;
      const s = 0.5 + 0.5 * Math.sin(t * 2.4 + k * 1.3);
      m.scale.y = (k === 0 ? 1.4 : 0.8) * (0.55 + 0.45 * s);
    });
  });
  const pos: [number, number][] = [[0, 0], ...Array.from({ length: 6 }, (_, k) => [Math.cos(((k + 0.5) * Math.PI * 2) / 6) * 1.0, Math.sin(((k + 0.5) * Math.PI * 2) / 6) * 1.0] as [number, number])];
  return (
    <group position={[DAM_FOUNTAIN_AT[0], 0, -DAM_FOUNTAIN_AT[1]]} scale={SC}>
      <mesh geometry={geo} castShadow receiveShadow><meshStandardMaterial vertexColors roughness={0.5} metalness={0.1} /></mesh>
      <mesh geometry={water}><meshStandardMaterial color="#5f7a46" roughness={0.15} metalness={0.2} transparent opacity={0.92} /></mesh>
      {pos.map(([x, z], k) => (
        <mesh key={k} ref={(m) => { jets.current[k] = m; }} geometry={jet} position={[x, 0.38, z]}>
          <meshBasicMaterial color="#e6f6ff" transparent opacity={0.65} />
        </mesh>
      ))}
    </group>
  );
}

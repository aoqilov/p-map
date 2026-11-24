// Suv attraksioni (config/map.ts → WATER_RIDES), masalan 28 — "Водные гусеницы" (Aqua Lady Birds):
// plandagi maydoncha shaklida — chetida tosh yo'lak va panjara, yer ostidagi halqa kanal (suv — water.tsx, nomi 'Aqua'),
// o'rtada daraxtli orol, kanalda xonqizi qayiqchalar aylanib yuradi.
import { useEffect, useLayoutEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame, type ThreeEvent } from '@react-three/fiber';
import { WATER } from './config';
import { inPoly } from './geo';
import { extrude, multiToShapes, toWorld } from './geometry';
import { colored, mergeAll, prefersReducedMotion, useAmbientFrames } from './modelKit';
import type { XY } from './projection';
import type { Attraction, MultiPoly } from './types';
import { waterLevelOf } from './water';

/** Qayiqlar tezligi (m/s) va o'z o'qi atrofida aylanishi (rad/s) */
const BOAT_SPEED = 0.7;
const BOAT_SPIN = 0.35;
const BOAT_COLORS = ['#d7261e', '#f2c318', '#1f5fd1', '#2fae3a', '#d7261e', '#f2c318'];

/** Xonqizi qayiqcha: qizil/sariq/ko'k/yashil kosa, qora dog'lar, ichida ko'k o'rindiq, tepada qora qo'l to'sig'i */
function boatGeometry(color: string) {
  const parts: THREE.BufferGeometry[] = [];
  parts.push(colored(new THREE.SphereGeometry(0.85, 14, 8, 0, Math.PI * 2, 0, Math.PI / 2).scale(1, 0.75, 1).rotateX(Math.PI), color));
  parts.push(colored(new THREE.CylinderGeometry(0.86, 0.86, 0.22, 14).translate(0, 0.11, 0), color));
  parts.push(colored(new THREE.CylinderGeometry(0.66, 0.66, 0.06, 14).translate(0, 0.23, 0), '#1d4fb8'));
  parts.push(colored(new THREE.TorusGeometry(0.62, 0.03, 4, 16).rotateX(Math.PI / 2).translate(0, 0.62, 0), '#222326'));
  for (let k = 0; k < 4; k++) {
    const a = (k / 4) * Math.PI * 2;
    parts.push(colored(new THREE.CylinderGeometry(0.025, 0.025, 0.4, 5).translate(Math.cos(a) * 0.62, 0.42, Math.sin(a) * 0.62), '#222326'));
  }
  // qora dog'lar (kosa sirtida)
  for (let k = 0; k < 10; k++) {
    const a = (k / 10) * Math.PI * 2 + (k % 2) * 0.3;
    const y = k % 2 ? -0.12 : 0.05;
    const r = k % 2 ? 0.8 : 0.87;
    parts.push(colored(new THREE.SphereGeometry(0.09, 6, 4).scale(1, 1, 0.5).rotateY(-a + Math.PI / 2)
      .translate(Math.cos(a) * r, y, Math.sin(a) * r), '#111111'));
  }
  return mergeAll(parts);
}

/** Yopiq chiziq bo'ylab masofa → nuqta va yo'nalish */
function loop(path: XY[]) {
  const pts = path[0][0] === path[path.length - 1][0] && path[0][1] === path[path.length - 1][1] ? path.slice(0, -1) : path;
  const cum = [0];
  for (let i = 0; i < pts.length; i++) {
    const a = pts[i], b = pts[(i + 1) % pts.length];
    cum.push(cum[i] + Math.hypot(b[0] - a[0], b[1] - a[1]));
  }
  const total = cum[pts.length];
  const at = (s: number): XY => {
    const d = ((s % total) + total) % total;
    let i = 0;
    while (cum[i + 1] < d) i++;
    const a = pts[i], b = pts[(i + 1) % pts.length], t = (d - cum[i]) / (cum[i + 1] - cum[i] || 1);
    return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
  };
  return { at, total };
}

/** Orol daraxtlari: seed bilan, har safar bir xil */
function islandTrees(island: MultiPoly) {
  let seed = 2811;
  const rand = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  const out: [number, number, number][] = [];
  for (const poly of island) {
    const xs = poly[0].map((p) => p[0]), ys = poly[0].map((p) => p[1]);
    for (let x = Math.min(...xs) + 1; x < Math.max(...xs); x += 2.4) {
      for (let y = Math.min(...ys) + 1; y < Math.max(...ys); y += 2.4) {
        const p: XY = [x + (rand() - 0.5) * 1.6, y + (rand() - 0.5) * 1.6];
        if (inPoly(p, poly)) out.push([p[0], p[1], 0.8 + rand() * 0.6]);
      }
    }
  }
  return out;
}

export function WaterRide({ item, selected, onSelect }: {
  item: Attraction; selected: boolean; onSelect: (id: string) => void;
}) {
  const ride = item.ride!;
  const level = waterLevelOf('Aqua');
  const geo = useMemo(() => {
    // tosh yo'lak va orol (orol yerdan biroz baland, chetida tosh)
    const rim = extrude(multiToShapes(ride.rim), 0.14);
    const island = extrude(multiToShapes(ride.island), 0.3);
    // panjara: maydoncha cheti bo'ylab ustunlar va ikki qator to'siq
    const ring = item.footprint![0];
    const fence: THREE.BufferGeometry[] = [];
    for (let i = 0; i < ring.length - 1; i++) {
      const [a, b] = [ring[i], ring[i + 1]];
      const L = Math.hypot(b[0] - a[0], b[1] - a[1]);
      const ang = Math.atan2(b[1] - a[1], b[0] - a[0]);
      const mid = toWorld([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]);
      for (const h of [0.35, 1.0]) {
        fence.push(colored(new THREE.BoxGeometry(L, 0.04, 0.04).rotateY(ang).translate(mid.x, h, mid.z), '#4a3a2c'));
      }
      const n = Math.max(1, Math.round(L / 1.6));
      for (let k = 0; k < n; k++) {
        const p = toWorld([a[0] + ((b[0] - a[0]) * k) / n, a[1] + ((b[1] - a[1]) * k) / n]);
        fence.push(colored(new THREE.BoxGeometry(0.08, 1.15, 0.08).translate(p.x, 0.58, p.z), '#4a3a2c'));
      }
    }
    const boats = BOAT_COLORS.map(boatGeometry);
    return { rim, island, fence: mergeAll(fence), boats };
  }, [item, ride]);
  useEffect(() => () => { geo.rim.dispose(); geo.island.dispose(); geo.fence.dispose(); geo.boats.forEach((g) => g.dispose()); }, [geo]);

  const trees = useMemo(() => islandTrees(ride.island), [ride]);
  const trunkGeom = useMemo(() => new THREE.CylinderGeometry(0.12, 0.2, 2.2, 5).translate(0, 1.1, 0), []);
  const crownGeom = useMemo(() => new THREE.IcosahedronGeometry(1, 1), []);
  useEffect(() => () => { trunkGeom.dispose(); crownGeom.dispose(); }, [trunkGeom, crownGeom]);
  const trunks = useRef<THREE.InstancedMesh>(null!);
  const crowns = useRef<THREE.InstancedMesh>(null!);
  useLayoutEffect(() => {
    const m = new THREE.Matrix4(), q = new THREE.Quaternion(), c = new THREE.Color();
    trees.forEach(([x, y, s], i) => {
      const p = toWorld([x, y], 0.3);
      m.compose(p, q, new THREE.Vector3(s, s, s));
      trunks.current.setMatrixAt(i, m);
      m.compose(new THREE.Vector3(p.x, p.y + 2.6 * s, p.z), q, new THREE.Vector3(1.5 * s, 1.3 * s, 1.5 * s));
      crowns.current.setMatrixAt(i, m);
      crowns.current.setColorAt(i, c.set(['#3e7d2e', '#4f8f2f', '#5d9a35'][i % 3]));
    });
    trunks.current.instanceMatrix.needsUpdate = true;
    crowns.current.instanceMatrix.needsUpdate = true;
    if (crowns.current.instanceColor) crowns.current.instanceColor.needsUpdate = true;
  }, [trees]);

  // qayiqlar kanal o'rtasi bo'ylab teng oraliqda suzadi, o'z o'qi atrofida sekin aylanadi
  const track = useMemo(() => loop(ride.path), [ride]);
  const boats = useRef<(THREE.Mesh | null)[]>([]);
  const animate = WATER.animate && !prefersReducedMotion();
  useAmbientFrames(animate);
  const t = useRef(0);
  const place = () => {
    const n = ride.boats;
    for (let k = 0; k < n; k++) {
      const m = boats.current[k];
      if (!m) continue;
      const [x, y] = track.at(t.current * BOAT_SPEED + (k * track.total) / n);
      const w = toWorld([x, y], level + 0.12 + Math.sin(t.current * 1.6 + k) * 0.03);
      m.position.copy(w);
      m.rotation.y = t.current * BOAT_SPIN * (k % 2 ? 1 : -1) + k;
    }
  };
  useLayoutEffect(place); // eslint-disable-line react-hooks/exhaustive-deps
  useFrame((_, dt) => {
    if (!animate) return;
    t.current += Math.min(dt, 0.1);
    place();
  });

  const click = (e: ThreeEvent<MouseEvent>) => { if (e.delta >= 6) return; e.stopPropagation(); onSelect(item.id); };
  return (
    <group onClick={click}>
      <mesh geometry={geo.rim} rotation-x={-Math.PI / 2} receiveShadow>
        <meshStandardMaterial color={selected ? '#f2c66d' : '#b9b4aa'} roughness={0.9} />
      </mesh>
      <mesh geometry={geo.island} rotation-x={-Math.PI / 2} receiveShadow>
        <meshStandardMaterial attach="material-0" color="#4c6b2a" roughness={1} />
        <meshStandardMaterial attach="material-1" color="#5a5047" roughness={1} />
      </mesh>
      <mesh geometry={geo.fence} castShadow><meshStandardMaterial vertexColors roughness={0.8} /></mesh>
      <instancedMesh ref={trunks} args={[trunkGeom, undefined, trees.length]} castShadow>
        <meshStandardMaterial color="#6b5034" />
      </instancedMesh>
      <instancedMesh ref={crowns} args={[crownGeom, undefined, trees.length]} castShadow receiveShadow>
        <meshStandardMaterial flatShading roughness={0.9} />
      </instancedMesh>
      {Array.from({ length: ride.boats }, (_, k) => (
        <mesh key={k} ref={(m) => { boats.current[k] = m; }} geometry={geo.boats[k % geo.boats.length]} castShadow>
          <meshStandardMaterial vertexColors roughness={0.35} />
        </mesh>
      ))}
    </group>
  );
}

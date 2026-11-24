// Maydonchalar atrofidagi metall panjara (config/map.ts → FENCES, chiziqlar build:genplan da hisoblanadi).
// Ustunlar har ~2 m da, tepa va pastki to'siq, orasida tik chiviqlar. Hammasi instanced — telefonda 3 ta draw call.
import { useEffect, useLayoutEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import type { XY } from './projection';
import type { Palette } from './theme';
import type { ParkData } from './types';

const POST_EVERY = 2.0;   // ustunlar oralig'i, m
const BAR_EVERY = 0.14;   // tik chiviqlar oralig'i, m

interface Piece { pos: THREE.Vector3; rotY: number; scale: THREE.Vector3 }

function layout(fences: NonNullable<ParkData['fences']>) {
  const posts: Piece[] = [], rails: Piece[] = [], bars: Piece[] = [];
  const W = (p: XY, y: number) => new THREE.Vector3(p[0], y, -p[1]);
  for (const f of fences) {
    const h = f.height;
    for (const line of f.lines) {
      // chiziq uzunligi bo'yicha teng oraliqda nuqtalar
      const cum = [0];
      for (let i = 1; i < line.length; i++) cum.push(cum[i - 1] + Math.hypot(line[i][0] - line[i - 1][0], line[i][1] - line[i - 1][1]));
      const total = cum[cum.length - 1];
      if (total < 0.3) continue;
      const at = (d: number): XY => {
        let i = 1;
        while (i < cum.length - 1 && cum[i] < d) i++;
        const t = (d - cum[i - 1]) / (cum[i] - cum[i - 1] || 1);
        return [line[i - 1][0] + (line[i][0] - line[i - 1][0]) * t, line[i - 1][1] + (line[i][1] - line[i - 1][1]) * t];
      };
      const nPost = Math.max(1, Math.round(total / POST_EVERY));
      for (let k = 0; k <= nPost; k++) {
        const p = at((total * k) / nPost);
        posts.push({ pos: W(p, h / 2 + 0.05), rotY: 0, scale: new THREE.Vector3(1, h + 0.1, 1) });
        if (k === nPost) break;
        const q = at((total * (k + 1)) / nPost);
        const len = Math.hypot(q[0] - p[0], q[1] - p[1]);
        const rotY = Math.atan2(q[1] - p[1], q[0] - p[0]);
        const mid: XY = [(p[0] + q[0]) / 2, (p[1] + q[1]) / 2];
        for (const y of [0.12, h - 0.04]) rails.push({ pos: W(mid, y), rotY, scale: new THREE.Vector3(len, 1, 1) });
        const nBar = Math.max(1, Math.floor(len / BAR_EVERY));
        for (let j = 1; j < nBar; j++) {
          const t = j / nBar;
          bars.push({ pos: W([p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t], (0.12 + h - 0.04) / 2), rotY, scale: new THREE.Vector3(1, h - 0.16, 1) });
        }
      }
    }
  }
  return { posts, rails, bars };
}

function Instances({ items, geom, color }: { items: Piece[]; geom: THREE.BufferGeometry; color: string }) {
  const ref = useRef<THREE.InstancedMesh>(null!);
  useLayoutEffect(() => {
    const m = new THREE.Matrix4(), q = new THREE.Quaternion(), up = new THREE.Vector3(0, 1, 0);
    items.forEach((it, i) => {
      m.compose(it.pos, q.setFromAxisAngle(up, it.rotY), it.scale);
      ref.current.setMatrixAt(i, m);
    });
    ref.current.instanceMatrix.needsUpdate = true;
    ref.current.computeBoundingSphere();
  }, [items]);
  if (!items.length) return null;
  return (
    <instancedMesh ref={ref} args={[geom, undefined, items.length]} castShadow>
      <meshStandardMaterial color={color} roughness={0.6} metalness={0.2} />
    </instancedMesh>
  );
}

export function Fences({ data, pal }: { data: ParkData; pal: Palette }) {
  // rang bo'yicha guruhlar (har bir rang — 3 ta draw call)
  const groups = useMemo(() => {
    const by = new Map<'fence' | 'fenceYellow', NonNullable<ParkData['fences']>>();
    for (const f of data.fences ?? []) by.set(f.color ?? 'fence', [...(by.get(f.color ?? 'fence') ?? []), f]);
    return [...by.entries()].map(([color, fs]) => ({ color, parts: layout(fs) }));
  }, [data]);
  const geo = useMemo(() => ({
    post: new THREE.BoxGeometry(0.07, 1, 0.07),          // balandligi scale.y bilan
    rail: new THREE.BoxGeometry(1, 0.045, 0.045),        // uzunligi scale.x bilan (lokal X — chiziq bo'ylab)
    bar: new THREE.CylinderGeometry(0.012, 0.012, 1, 4), // balandligi scale.y bilan
  }), []);
  useEffect(() => () => { geo.post.dispose(); geo.rail.dispose(); geo.bar.dispose(); }, [geo]);
  return (
    <>
      {groups.map(({ color, parts }) => (
        <group key={color}>
          <Instances items={parts.posts} geom={geo.post} color={pal[color]} />
          <Instances items={parts.rails} geom={geo.rail} color={pal[color]} />
          <Instances items={parts.bars} geom={geo.bar} color={pal[color]} />
        </group>
      ))}
    </>
  );
}

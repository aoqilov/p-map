// Jonli devor — yashil buta to'siq (config/map.ts → HEDGES). Chiziq silliqlanadi, har ~0.7 m da kesim (profil) olinib,
// ular orasi to'ldiriladi: pastda tik, tepasi yumaloq, balandligi va eni ozgina notekis (kesilgan buta kabi).
// Daraxt tojlari kabi flat shading va barg ranglari. Har bir buta — bitta mesh (telefonda 1 draw call).
import { useEffect, useMemo } from 'react';
import * as THREE from 'three';
import { HEDGES, type HedgeDef } from './config';
import { smoothLine } from './geo';
import type { XY } from './projection';
import type { Palette } from './theme';

const STEP = 0.7; // kesimlar oralig'i, m

/** Chiziq bo'ylab teng oraliqdagi nuqtalar */
function resample(line: XY[], step: number): XY[] {
  const out: XY[] = [line[0]];
  let carry = 0;
  for (let i = 1; i < line.length; i++) {
    const [a, b] = [line[i - 1], line[i]];
    const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
    let d = step - carry;
    while (d < len) {
      out.push([a[0] + ((b[0] - a[0]) * d) / len, a[1] + ((b[1] - a[1]) * d) / len]);
      d += step;
    }
    carry = len - (d - step);
  }
  const last = line[line.length - 1];
  if (Math.hypot(last[0] - out[out.length - 1][0], last[1] - out[out.length - 1][1]) > step * 0.3) out.push(last);
  return out;
}

/** Kesim profili: [yon siljish (eni ulushi), balandlik ulushi] — pastdan chapdan o'ngga */
const PROFILE: [number, number][] = [[-0.92, 0], [-1, 0.3], [-0.95, 0.8], [-0.6, 0.97], [0, 1], [0.6, 0.97], [0.95, 0.8], [1, 0.3], [0.92, 0]];

function hedgeGeometry(h: HedgeDef, leaves: readonly string[]) {
  const pts = resample(smoothLine(h.line, 3), STEP);
  let seed = 9;
  const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  const pos: number[] = [], col: number[] = [], idx: number[] = [];
  const c = new THREE.Color(), c2 = new THREE.Color();
  const P = PROFILE.length;
  pts.forEach((p, i) => {
    const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)];
    const len = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
    const nx = -(b[1] - a[1]) / len, ny = (b[0] - a[0]) / len; // chiziqqa perpendikulyar
    const hh = h.height * (0.95 + rnd() * 0.07);
    const hw = (h.width / 2) * (0.9 + rnd() * 0.15);
    c.set(leaves[Math.floor(rnd() * leaves.length)]).lerp(c2.set(leaves[0]), 0.4);
    for (const [s, z] of PROFILE) {
      const top = z > 0.9 ? 1 + (rnd() - 0.5) * 0.06 : 1; // tepasi ozgina g'adir-budur
      pos.push(p[0] + nx * s * hw, z * hh * top, -(p[1] + ny * s * hw));
      const shade = 0.78 + 0.22 * z; // pasti to'qroq (soya)
      col.push(c.r * shade, c.g * shade, c.b * shade);
    }
    if (i === 0) return;
    const o0 = (i - 1) * P, o1 = i * P;
    for (let k = 0; k < P - 1; k++) idx.push(o0 + k, o1 + k, o1 + k + 1, o0 + k, o1 + k + 1, o0 + k + 1);
  });
  // uchlari: profil yuzasi (yelpig'ich)
  const n = pts.length;
  for (const [o, flip] of [[0, false], [(n - 1) * P, true]] as const) {
    for (let k = 1; k < P - 1; k++) idx.push(...(flip ? [o, o + k, o + k + 1] : [o, o + k + 1, o + k]));
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  g.setIndex(idx);
  const ng = g.toNonIndexed(); // flat shading — har bir yuz o'z normali bilan
  g.dispose();
  ng.computeVertexNormals();
  return ng;
}

export function Hedges({ pal }: { pal: Palette }) {
  const geoms = useMemo(() => HEDGES.map((h) => hedgeGeometry(h, pal.leaves)), [pal]);
  useEffect(() => () => geoms.forEach((g) => g.dispose()), [geoms]);
  return (
    <>
      {geoms.map((g, i) => (
        <mesh key={HEDGES[i].id} geometry={g} castShadow receiveShadow raycast={() => {}}>
          <meshStandardMaterial vertexColors flatShading roughness={0.95} side={THREE.DoubleSide} />
        </mesh>
      ))}
    </>
  );
}

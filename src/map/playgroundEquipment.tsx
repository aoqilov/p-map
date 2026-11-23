import { useEffect, useMemo } from 'react';
import * as THREE from 'three';
import { PLAYGROUND } from './config';
import { V, canvasTexture, colored, mergeAll, rod } from './modelKit';

// Bolalar maydonchasi (Playground): bolalar uskunalari, ota-onalar uchun skameykalar va kirish darvozasi.
// Boshqa chatda quyilgan modellar shu yerga ko'chirilgan. Lokal: Y yuqoriga, burchak — Y o'qi atrofida (radian).
// Joylashuv `config.ts` dagi PLAYGROUND da (2D reja sahifasidan olingan, xarita metrlarida).

const bx = (w: number, h: number, d: number, x: number, y: number, z: number, c: string) =>
  colored(new THREE.BoxGeometry(w, h, d).translate(x, y, z), c);
const cyl = (r1: number, r2: number, h: number, x: number, y: number, z: number, c: string, n = 10) =>
  colored(new THREE.CylinderGeometry(r1, r2, h, n).translate(x, y, z), c);
const sph = (r: number, x: number, y: number, z: number, c: string) =>
  colored(new THREE.SphereGeometry(r, 10, 8).translate(x, y, z), c);
const cone = (r: number, h: number, n: number, x: number, y: number, z: number, c: string) =>
  colored(new THREE.ConeGeometry(r, h, n).rotateY(n === 4 ? Math.PI / 4 : 0).translate(x, y, z), c);
const r3 = (a: number[], b: number[], r: number, c: string) => colored(rod(V(a[0], a[1], a[2]), V(b[0], b[1], b[2]), r, 5), c);

const BLUE = '#2f7fd0', YELLOW = '#e8c23a', RED = '#d9402e', STEEL = '#cfd4da', WOODC = '#9a6b44';
const SPRING_COLORS = ['#d9402e', '#2f7fd0', '#e8a32a', '#7fb83a'];

/** 0 belanchak · 1 slayd · 2 tebranma · 3 prujinali · 4 qum maydoni · 5 devor-narvon · 6 karusel */
const MODELS: Record<number, (ci: number) => THREE.BufferGeometry[]> = {
  0: () => {
    const g: THREE.BufferGeometry[] = [];
    for (const z of [-1.5, 1.5]) g.push(r3([-0.9, 0, z], [0, 2.3, z], 0.06, BLUE), r3([0.9, 0, z], [0, 2.3, z], 0.06, BLUE));
    g.push(r3([0, 2.3, -1.5], [0, 2.3, 1.5], 0.07, '#1f5fa8'));
    for (const z of [-0.55, 0.55]) {
      g.push(r3([0, 2.3, z], [0, 0.55, z - 0.18], 0.015, STEEL), r3([0, 2.3, z], [0, 0.55, z + 0.18], 0.015, STEEL), bx(0.5, 0.06, 0.42, 0, 0.5, z, '#f2b52a'));
    }
    return g;
  },
  1: () => {
    const g: THREE.BufferGeometry[] = [];
    for (const [x, z] of [[-0.6, -0.6], [-0.6, 0.6], [0.6, -0.6], [0.6, 0.6]]) g.push(r3([x, 0, z], [x, 1.6, z], 0.05, BLUE));
    g.push(bx(1.3, 0.08, 1.3, 0, 1.45, 0, YELLOW), cone(1.2, 0.8, 4, 0, 2.4, 0, RED));
    for (const z of [-0.6, 0.6]) g.push(r3([-0.6, 1.6, z], [-0.6, 2.0, z], 0.04, BLUE), r3([0.6, 1.6, z], [0.6, 2.0, z], 0.04, BLUE));
    g.push(bx(2.7, 0.08, 0.75, 0, 0, 0, '#e6483a').rotateZ(-0.52).translate(1.95, 0.78, 0));
    for (const z of [-0.38, 0.38]) g.push(bx(2.7, 0.2, 0.05, 0, 0, 0, '#c63a2c').rotateZ(-0.52).translate(1.95, 0.88, z));
    for (let k = 0; k < 4; k++) g.push(bx(0.06, 0.05, 0.5, -0.62, 0.25 + k * 0.33, 0, STEEL).translate(-0.1, 0, 0));
    return g;
  },
  2: () => [
    cyl(0.22, 0.32, 0.55, 0, 0.28, 0, BLUE),
    bx(3.2, 0.1, 0.34, 0, 0, 0, YELLOW).rotateZ(0.2).translate(0, 0.7, 0),
    bx(0.06, 0.3, 0.34, 1.5, 0, 0, RED).rotateZ(0.2).translate(0, 0.85, 0),
  ],
  3: (ci) => {
    const c = SPRING_COLORS[ci % 4];
    return [
      cyl(0.3, 0.3, 0.06, 0, 0.03, 0, '#555c64'), cyl(0.05, 0.05, 0.5, 0, 0.3, 0, '#8a929a', 6), sph(0.36, 0, 0.8, 0, c),
      colored(new THREE.BoxGeometry(0.16, 0.16, 0.5).translate(0.28, 0.95, 0), c), sph(0.18, 0.38, 1.02, 0, c), bx(0.5, 0.04, 0.04, 0, 1.12, 0, STEEL),
    ];
  },
  4: () => {
    const g: THREE.BufferGeometry[] = [];
    for (const z of [-1.5, 1.5]) g.push(bx(3.2, 0.35, 0.12, 0, 0.18, z, WOODC));
    for (const x of [-1.55, 1.55]) g.push(bx(0.12, 0.35, 3.0, x, 0.18, 0, WOODC));
    g.push(bx(2.9, 0.12, 2.9, 0, 0.1, 0, '#e3cf9a'), cone(0.3, 0.35, 6, 0.5, 0.35, 0.4, '#d9b878'));
    g.push(r3([-1.1, 0, -1.1], [-1.1, 2.3, -1.1], 0.05, BLUE), r3([1.1, 0, -1.1], [1.1, 2.3, -1.1], 0.05, BLUE),
      colored(new THREE.ConeGeometry(1.9, 0.45, 4).rotateY(Math.PI / 4).translate(0, 2.5, -1.1).scale(1, 1, 0.6), YELLOW));
    return g;
  },
  5: () => {
    const g: THREE.BufferGeometry[] = [];
    for (const x of [-1, 1]) for (const z of [-1, 1]) g.push(r3([x, 0, z], [x, 1.9, z], 0.05, BLUE));
    for (const h of [0.6, 1.2, 1.9]) {
      g.push(r3([-1, h, -1], [1, h, -1], 0.04, YELLOW), r3([-1, h, 1], [1, h, 1], 0.04, YELLOW), r3([-1, h, -1], [-1, h, 1], 0.04, YELLOW), r3([1, h, -1], [1, h, 1], 0.04, YELLOW));
    }
    g.push(bx(2.2, 0.08, 2.2, 0, 1.9, 0, RED), cone(1.7, 0.7, 4, 0, 2.3, 0, YELLOW), bx(0.1, 1.4, 0.1, 0, 1.2, 0, '#8a929a'));
    for (let k = 0; k < 5; k++) g.push(r3([1.05, 0.2 + k * 0.36, -0.5], [1.05, 0.2 + k * 0.36, 0.5], 0.03, STEEL));
    return g;
  },
  6: () => {
    const g: THREE.BufferGeometry[] = [cyl(1.45, 1.5, 0.14, 0, 0.34, 0, YELLOW, 18), cyl(0.08, 0.08, 2.2, 0, 1.2, 0, '#8a929a', 6), colored(new THREE.ConeGeometry(1.8, 0.8, 12).translate(0, 2.7, 0), RED)];
    for (let k = 0; k < 6; k++) {
      const a = (k / 6) * Math.PI * 2, x = Math.cos(a), z = Math.sin(a);
      g.push(r3([x, 0.4, z], [x, 2.3, z], 0.04, BLUE), sph(0.22, x, 0.7, z, [RED, BLUE, YELLOW][k % 3]), bx(0.3, 0.1, 0.3, x, 0.5, z, WOODC));
    }
    return g;
  },
};

function bench() {
  return [
    bx(1.7, 0.07, 0.5, 0, 0.45, 0, WOODC),
    bx(1.7, 0.5, 0.06, -0.22, 0.78, 0, WOODC).rotateZ(-0.12),
    bx(0.07, 0.45, 0.4, -0.7, 0.22, 0, '#3b4046'),
    bx(0.07, 0.45, 0.4, 0.7, 0.22, 0, '#3b4046'),
  ];
}

function gate() {
  const frame = mergeAll([
    bx(0.4, 2.9, 0.4, -1.7, 1.45, 0, BLUE), bx(0.4, 2.9, 0.4, 1.7, 1.45, 0, BLUE),
    bx(0.52, 0.14, 0.52, -1.7, 2.95, 0, YELLOW), bx(0.52, 0.14, 0.52, 1.7, 2.95, 0, YELLOW),
    bx(4.1, 0.12, 0.36, 0, 2.35, 0, YELLOW), bx(0.2, 0.2, 0.2, -1.7, 3.1, 0, RED), bx(0.2, 0.2, 0.2, 1.7, 3.1, 0, RED),
  ]);
  const tex = canvasTexture(512, 128, (c, w, h) => {
    c.fillStyle = BLUE; c.fillRect(0, 0, w, h);
    c.strokeStyle = '#fff'; c.lineWidth = 6; c.strokeRect(8, 8, w - 16, h - 16);
    c.fillStyle = '#fff'; c.font = '700 62px system-ui, sans-serif'; c.textAlign = 'center'; c.textBaseline = 'middle';
    c.fillText('PLAYGROUND', w / 2, h / 2 + 4);
  });
  return { frame, tex, plane: new THREE.PlaneGeometry(3.5, 0.88) };
}

/** Bolalar maydonchasi: uskunalar + skameykalar + darvoza */
export function PlaygroundEquipment() {
  const m = useMemo(() => {
    const place = (geoms: THREE.BufferGeometry[], x: number, y: number, a: number) =>
      mergeAll(geoms).rotateY(a).translate(x, 0.02, -y);
    const eq = mergeAll(PLAYGROUND.items.map(([t, x, y, a], i) => place(MODELS[t](i), x, y, a)));
    const bn = mergeAll(PLAYGROUND.benches.map(([x, y, a]) => place(bench(), x, y, a)));
    return { eq, bn, gates: PLAYGROUND.gates.map(() => gate()) };
  }, []);
  useEffect(() => () => {
    m.eq.dispose(); m.bn.dispose();
    m.gates.forEach((g) => { g.frame.dispose(); g.tex.dispose(); g.plane.dispose(); });
  }, [m]);

  return (
    <group>
      <mesh geometry={m.eq} castShadow receiveShadow>
        <meshStandardMaterial vertexColors roughness={0.7} side={THREE.DoubleSide} />
      </mesh>
      <mesh geometry={m.bn} castShadow receiveShadow>
        <meshStandardMaterial vertexColors roughness={0.85} side={THREE.DoubleSide} />
      </mesh>
      {PLAYGROUND.gates.map(([x, y, a], i) => (
        <group key={i} position={[x, 0.02, -y]} rotation-y={a}>
          <mesh geometry={m.gates[i].frame} castShadow receiveShadow>
            <meshStandardMaterial vertexColors roughness={0.6} />
          </mesh>
          <mesh geometry={m.gates[i].plane} position={[0, 2.72, 0.2]}>
            <meshBasicMaterial map={m.gates[i].tex} toneMapped={false} />
          </mesh>
          <mesh geometry={m.gates[i].plane} position={[0, 2.72, -0.2]} rotation-y={Math.PI}>
            <meshBasicMaterial map={m.gates[i].tex} toneMapped={false} />
          </mesh>
        </group>
      ))}
    </group>
  );
}

import { useEffect, useLayoutEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { CAROUSEL } from './config';
import { V, canvasTexture, colored, faceOutward, mergeAll, prefersReducedMotion, rod, useAmbientFrames } from './modelKit';
import type { Palette } from './theme';

// Lokal koordinata: Y yuqoriga, kirish eshigi +Z tomonda. Aylana bo'ylab nuqta: (R·cos a, y, R·sin a).
// Pastki asos va panjara qo'zg'almaydi; pol, otlar, ustun va tom birga aylanadi (yuqoridan qaraganda soat strelkasiga teskari).

const FLOOR = 0.55; // aylanadigan pol sathi
const CEIL = 4.4; // tom osti
const FRIEZE_TOP = 5.5;
const R_CANOPY = 6.0;
const R_FENCE = 6.65;
const GOLD = '#d6b25e';
const CREAM = '#f2e6c6';

export const CAROUSEL_NATURAL = { height: 9.3, footprint: 13.9 };

const ringPos = (r: number, a: number, y: number) => V(r * Math.cos(a), y, r * Math.sin(a));

/** ctx.roundRect eski Safari/Telegram webview'larda yo'q — o'zimiz chizamiz */
function roundRectPath(g: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  g.beginPath();
  g.moveTo(x + r, y);
  g.arcTo(x + w, y, x + w, y + h, r);
  g.arcTo(x + w, y + h, x, y + h, r);
  g.arcTo(x, y + h, x, y, r);
  g.arcTo(x, y, x + w, y, r);
  g.closePath();
}

/** Ot: oldinga +X, sakrash holatida (oldingi oyoqlari ko'tarilgan) */
function horseGeometry() {
  const body = '#f7f3ea', mane = '#d9b45a', saddle = '#d4a843', blanket = '#7a1f2b';
  const parts: THREE.BufferGeometry[] = [
    colored(new THREE.SphereGeometry(1, 14, 10).scale(0.6, 0.28, 0.21), body),
    colored(rod(V(0.33, 0.1, 0), V(0.62, 0.55, 0), 0.14, 8), body), // bo'yin
    colored(rod(V(0.57, 0.57, 0), V(0.93, 0.38, 0), 0.1, 8), body), // bosh
    colored(rod(V(0.27, 0.27, 0), V(0.53, 0.68, 0), 0.05, 5), mane), // yol
    colored(rod(V(-0.57, 0.08, 0), V(-0.82, -0.35, 0), 0.06, 5), mane), // dum
    colored(new THREE.BoxGeometry(0.5, 0.22, 0.45).translate(-0.04, 0.17, 0), blanket),
    colored(new THREE.BoxGeometry(0.42, 0.07, 0.47).translate(-0.04, 0.3, 0), saddle),
  ];
  for (const z of [-0.1, 0.1]) {
    parts.push(colored(rod(V(0.38, -0.12, z), V(0.62, -0.3, z), 0.05, 5), body));
    parts.push(colored(rod(V(0.62, -0.3, z), V(0.5, -0.52, z), 0.045, 5), body));
    parts.push(colored(rod(V(-0.4, -0.12, z), V(-0.56, -0.62, z), 0.055, 5), body));
  }
  return mergeAll(parts);
}

/** Arava: oldinga +X */
function chariotGeometry() {
  const red = '#7a1f2b';
  return mergeAll([
    colored(new THREE.BoxGeometry(1.25, 0.5, 0.85).translate(0, 0.25, 0), red),
    colored(new THREE.BoxGeometry(0.18, 0.6, 0.85).translate(-0.53, 0.8, 0), red),
    colored(new THREE.BoxGeometry(1.3, 0.06, 0.9).translate(0, 0.52, 0), GOLD),
    colored(new THREE.CylinderGeometry(0.26, 0.26, 0.86, 12).rotateX(Math.PI / 2).translate(0.55, 0.45, 0), GOLD),
  ]);
}

function buildCarousel() {
  const { outerHorses: NO, innerHorses: NI, chariots: NC } = CAROUSEL;

  // --- Qo'zg'almas qism ---
  const base = mergeAll([
    colored(new THREE.CylinderGeometry(6.95, 6.95, 0.12, 64).translate(0, 0.06, 0), '#e4dbc6'),
    colored(new THREE.CylinderGeometry(6.08, 6.12, 0.33, 64).translate(0, 0.12 + 0.165, 0), CREAM),
    colored(new THREE.TorusGeometry(6.1, 0.04, 4, 96).rotateX(Math.PI / 2).translate(0, 0.44, 0), GOLD),
    colored(new THREE.BoxGeometry(1.8, 0.18, 0.5).translate(0, 0.21, 6.35), CREAM), // zinapoya
  ]);

  const fence: THREE.BufferGeometry[] = [];
  const gap = THREE.MathUtils.degToRad(13);
  const front = Math.PI / 2;
  const posts: number[] = [];
  for (let d = 0; d < 360; d += 6) {
    const a = THREE.MathUtils.degToRad(d);
    const off = Math.abs(Math.atan2(Math.sin(a - front), Math.cos(a - front)));
    if (off >= gap) posts.push(a);
  }
  posts.forEach((a, i) => {
    fence.push(colored(new THREE.BoxGeometry(0.07, 0.95, 0.07).translate(R_FENCE * Math.cos(a), 0.12 + 0.475, R_FENCE * Math.sin(a)), CREAM));
    const b = posts[(i + 1) % posts.length];
    if (Math.abs(Math.atan2(Math.sin(b - a), Math.cos(b - a))) > THREE.MathUtils.degToRad(7)) return; // eshik oralig'i
    fence.push(colored(rod(ringPos(R_FENCE, a, 1.07), ringPos(R_FENCE, b, 1.07), 0.04, 5), GOLD));
    fence.push(colored(rod(ringPos(R_FENCE, a, 0.55), ringPos(R_FENCE, b, 0.55), 0.025, 4), CREAM));
  });
  for (const s of [-1, 1]) {
    const a = front + s * gap;
    fence.push(colored(new THREE.BoxGeometry(0.15, 1.15, 0.15).translate(R_FENCE * Math.cos(a), 0.12 + 0.575, R_FENCE * Math.sin(a)), GOLD));
    fence.push(colored(new THREE.SphereGeometry(0.11, 10, 8).translate(R_FENCE * Math.cos(a), 1.35, R_FENCE * Math.sin(a)), GOLD));
  }

  // --- Aylanadigan qism ---
  const floor = mergeAll([
    colored(new THREE.CylinderGeometry(5.95, 5.95, 0.1, 64).translate(0, FLOOR - 0.05, 0), '#8b5a32'),
    colored(new THREE.TorusGeometry(5.95, 0.045, 4, 96).rotateX(Math.PI / 2).translate(0, FLOOR, 0), GOLD),
    colored(new THREE.CylinderGeometry(1.75, 1.88, 0.2, 24).translate(0, FLOOR + 0.1, 0), GOLD), // ustun asosi
    colored(new THREE.CylinderGeometry(1.88, 1.75, 0.2, 24).translate(0, CEIL - 0.1, 0), GOLD), // ustun boshi
  ]);

  const columnH = CEIL - FLOOR;
  const column = new THREE.CylinderGeometry(1.62, 1.62, columnH - 0.4, 16, 1, true).translate(0, FLOOR + columnH / 2, 0);
  const ceiling = new THREE.RingGeometry(1.6, R_CANOPY, 48).rotateX(Math.PI / 2).translate(0, CEIL, 0);
  const frieze = new THREE.CylinderGeometry(R_CANOPY, R_CANOPY, FRIEZE_TOP - CEIL, 72, 1, true).translate(0, (CEIL + FRIEZE_TOP) / 2, 0);

  // Toj ustidagi oltin gerblar (frizdagi medalyonlar bilan bir chiziqda) va pastdagi tishli "parda"
  const shield = new THREE.Shape();
  shield.moveTo(-0.32, 0);
  shield.lineTo(0.32, 0);
  shield.lineTo(0.32, 0.4);
  shield.quadraticCurveTo(0.32, 0.72, 0, 0.8);
  shield.quadraticCurveTo(-0.32, 0.72, -0.32, 0.4);
  shield.closePath();
  const trim: THREE.BufferGeometry[] = [];
  for (let k = 0; k < 12; k++) {
    const a = (k * Math.PI) / 6;
    const p = ringPos(R_CANOPY, a, FRIEZE_TOP);
    const yaw = faceOutward(a);
    trim.push(colored(new THREE.ExtrudeGeometry(shield, { depth: 0.08, bevelEnabled: false }).translate(0, 0, -0.04).rotateY(yaw).translate(p.x, p.y, p.z), GOLD));
    trim.push(colored(new THREE.CircleGeometry(0.16, 16).translate(0, 0.42, 0.045).rotateY(yaw).translate(p.x, p.y, p.z), '#f0d6cf'));
  }
  const SCALLOPS = 48;
  for (let k = 0; k < SCALLOPS; k++) {
    const a = ((k + 0.5) / SCALLOPS) * Math.PI * 2;
    const p = ringPos(R_CANOPY + 0.03, a, CEIL);
    trim.push(colored(new THREE.CircleGeometry(0.33, 10, Math.PI, Math.PI).rotateY(faceOutward(a)).translate(p.x, p.y, p.z), k % 2 ? '#8fb5df' : CREAM));
  }

  // Chodir tom: ozgina botiq profil (Lathe)
  const roofProfile = [
    [R_CANOPY + 0.15, 0], [5.2, 0.5], [4.0, 1.08], [2.6, 1.68], [1.2, 2.25], [0.22, 2.7],
  ].map(([r, y]) => new THREE.Vector2(r, y));
  const roof = new THREE.LatheGeometry(roofProfile, 64).translate(0, FRIEZE_TOP, 0);
  const apex = FRIEZE_TOP + 2.7;
  const finial = mergeAll([
    new THREE.CylinderGeometry(0.12, 0.2, 0.35, 12).translate(0, apex + 0.17, 0),
    new THREE.SphereGeometry(0.2, 14, 10).translate(0, apex + 0.5, 0),
    new THREE.ConeGeometry(0.08, 0.55, 10).translate(0, apex + 0.95, 0),
  ]);

  // Ot va arava o'rinlari: tashqi halqa (aravalar shu yerda) va ichki halqa
  type Slot = { r: number; a: number; phase: number };
  const horseSlots: Slot[] = [];
  const chariotSlots: Slot[] = [];
  const chariotEvery = NC > 0 ? Math.floor(NO / NC) : Infinity;
  for (let i = 0; i < NO; i++) {
    const slot = { r: 4.75, a: (i / NO) * Math.PI * 2, phase: i * 1.7 };
    (i % chariotEvery === 0 && chariotSlots.length < NC ? chariotSlots : horseSlots).push(slot);
  }
  for (let j = 0; j < NI; j++) horseSlots.push({ r: 3.15, a: ((j + 0.5) / NI) * Math.PI * 2, phase: j * 2.3 + 0.8 });

  const poles = mergeAll(horseSlots.map((s) => rod(ringPos(s.r, s.a, FLOOR), ringPos(s.r, s.a, CEIL), 0.04, 6)));

  // Lampochkalar: friz pastida va tepasida, ustun boshida
  const bulbs: THREE.Vector3[] = [];
  for (let k = 0; k < 64; k++) {
    const a = (k / 64) * Math.PI * 2;
    bulbs.push(ringPos(R_CANOPY + 0.06, a, CEIL + 0.03), ringPos(R_CANOPY + 0.06, a, FRIEZE_TOP - 0.03));
  }
  for (let k = 0; k < 16; k++) bulbs.push(ringPos(1.92, (k / 16) * Math.PI * 2, CEIL - 0.2));

  // --- Teksturalar (canvas, tarmoqsiz) ---
  const friezeTex = canvasTexture(512, 180, (g, w, h) => {
    g.fillStyle = CREAM;
    g.fillRect(0, 0, w, h);
    g.fillStyle = '#cfa64b';
    g.fillRect(0, 0, w, 14);
    g.fillRect(0, h - 14, w, 14);
    const grad = g.createLinearGradient(0, 34, 0, 146);
    grad.addColorStop(0, '#c5dcf1');
    grad.addColorStop(1, '#93b8df');
    g.fillStyle = grad;
    roundRectPath(g, 64, 34, w - 128, 112, 18);
    g.fill();
    g.fillStyle = 'rgba(255,255,255,0.55)'; // bulutlar
    for (const [x, y, rx, ry] of [[150, 80, 46, 14], [260, 104, 60, 16], [372, 72, 40, 12]]) {
      g.beginPath();
      g.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2);
      g.fill();
    }
    g.lineWidth = 7;
    g.strokeStyle = '#c99a3b';
    roundRectPath(g, 64, 34, w - 128, 112, 18);
    g.stroke();
    g.fillStyle = '#d6b25e'; // segmentlar chegarasidagi medalyon (ikki yarmi qo'shilib butun bo'ladi)
    for (const x of [0, w]) {
      g.beginPath();
      g.arc(x, h / 2, 26, 0, Math.PI * 2);
      g.fill();
    }
  });
  friezeTex.wrapS = THREE.RepeatWrapping;
  friezeTex.repeat.set(12, 1);

  const roofTex = canvasTexture(1024, 64, (g, w, h) => {
    const n = 16;
    for (let i = 0; i < n; i++) {
      g.fillStyle = i % 2 ? '#f7f4ec' : '#9fc0e4';
      g.fillRect((i * w) / n, 0, w / n + 1, h);
      g.fillStyle = 'rgba(0,0,0,0.06)';
      g.fillRect(((i + 1) * w) / n - 3, 0, 3, h);
    }
  });

  const columnTex = canvasTexture(160, 400, (g, w, h) => {
    g.fillStyle = '#efe2bf';
    g.fillRect(0, 0, w, h);
    const grad = g.createLinearGradient(0, 60, 0, 340);
    grad.addColorStop(0, '#a9c7e8');
    grad.addColorStop(1, '#5f8fc9');
    g.fillStyle = grad;
    g.beginPath();
    g.moveTo(26, 340);
    g.lineTo(26, 120);
    g.arc(w / 2, 120, w / 2 - 26, Math.PI, 0);
    g.lineTo(w - 26, 340);
    g.closePath();
    g.fill();
    g.lineWidth = 6;
    g.strokeStyle = '#c99a3b';
    g.stroke();
    g.fillStyle = 'rgba(255,230,160,0.55)'; // ichki iliq yorug'lik
    g.fillRect(34, 300, w - 68, 34);
  });
  columnTex.wrapS = THREE.RepeatWrapping;
  columnTex.repeat.set(8, 1);

  return {
    base, fence: mergeAll(fence), floor, column, ceiling, frieze, trim: mergeAll(trim), roof, finial, poles,
    horse: horseGeometry(), chariot: chariotGeometry(), bulb: new THREE.IcosahedronGeometry(0.07, 0),
    horseSlots, chariotSlots, bulbs, textures: [friezeTex, roofTex, columnTex] as const,
  };
}

export function Carousel({ pal, selected }: { pal: Palette; selected: boolean }) {
  const c = useMemo(buildCarousel, []);
  useEffect(() => () => {
    Object.values(c).forEach((v) => v instanceof THREE.BufferGeometry && v.dispose());
    c.textures.forEach((t) => t.dispose());
  }, [c]);
  const [friezeTex, roofTex, columnTex] = c.textures;

  const rotor = useRef<THREE.Group>(null!);
  const horses = useRef<THREE.InstancedMesh>(null!);
  const chariots = useRef<THREE.InstancedMesh>(null!);
  const bulbs = useRef<THREE.InstancedMesh>(null!);

  const speed = CAROUSEL.secondsPerTurn > 0 ? (Math.PI * 2) / CAROUSEL.secondsPerTurn : 0;
  const spinning = speed > 0 && !prefersReducedMotion();
  useAmbientFrames(spinning);

  const m = useMemo(() => new THREE.Matrix4(), []);
  const q = useMemo(() => new THREE.Quaternion(), []);
  const one = useMemo(() => new THREE.Vector3(1, 1, 1), []);
  const Y = useMemo(() => new THREE.Vector3(0, 1, 0), []);

  // Otlar aylanish yo'nalishiga qarab turadi va yuqoriga-pastga chayqaladi
  const place = (t: number) => {
    rotor.current.rotation.y = t * speed;
    c.horseSlots.forEach((s, i) => {
      const bob = spinning ? Math.sin((t / CAROUSEL.bobSeconds) * Math.PI * 2 + s.phase) * 0.22 : 0;
      q.setFromAxisAngle(Y, Math.PI / 2 - s.a);
      m.compose(ringPos(s.r, s.a, FLOOR + 1.3 + bob), q, one);
      horses.current.setMatrixAt(i, m);
    });
    horses.current.instanceMatrix.needsUpdate = true;
  };

  useLayoutEffect(() => {
    c.chariotSlots.forEach((s, i) => {
      q.setFromAxisAngle(Y, Math.PI / 2 - s.a);
      chariots.current.setMatrixAt(i, m.compose(ringPos(s.r, s.a, FLOOR), q, one));
    });
    chariots.current.instanceMatrix.needsUpdate = true;
    c.bulbs.forEach((p, i) => bulbs.current.setMatrixAt(i, m.makeTranslation(p.x, p.y, p.z)));
    bulbs.current.instanceMatrix.needsUpdate = true;
    // Bir nechta otni jigarrang qilamiz (vertex rang × instance rang)
    const tint = new THREE.Color();
    c.horseSlots.forEach((_, i) => horses.current.setColorAt(i, tint.set(i % 5 === 2 ? '#c79a6e' : i % 7 === 4 ? '#b9bec7' : '#ffffff')));
    if (horses.current.instanceColor) horses.current.instanceColor.needsUpdate = true;
    place(spinning ? performance.now() / 1000 : 0.4);
  }, [c]); // eslint-disable-line react-hooks/exhaustive-deps

  useFrame(() => {
    if (spinning) place(performance.now() / 1000);
  });

  return (
    <group>
      <mesh geometry={c.base} receiveShadow castShadow>
        <meshStandardMaterial vertexColors roughness={0.7} />
      </mesh>
      <mesh geometry={c.fence} castShadow>
        <meshStandardMaterial vertexColors roughness={0.5} metalness={0.15} />
      </mesh>

      <group ref={rotor}>
        <mesh geometry={c.floor} receiveShadow>
          <meshStandardMaterial vertexColors roughness={0.6} />
        </mesh>
        <mesh geometry={c.column} castShadow>
          <meshStandardMaterial map={columnTex} side={THREE.DoubleSide} roughness={0.5} />
        </mesh>
        <mesh geometry={c.ceiling}>
          <meshStandardMaterial color="#d7e5f3" side={THREE.DoubleSide} />
        </mesh>
        <mesh geometry={c.poles}>
          <meshStandardMaterial color={GOLD} metalness={0.5} roughness={0.35} />
        </mesh>
        <instancedMesh ref={horses} args={[c.horse, undefined, c.horseSlots.length]} castShadow>
          <meshStandardMaterial vertexColors roughness={0.45} />
        </instancedMesh>
        <instancedMesh ref={chariots} args={[c.chariot, undefined, Math.max(1, c.chariotSlots.length)]} castShadow>
          <meshStandardMaterial vertexColors roughness={0.5} />
        </instancedMesh>
        <mesh geometry={c.frieze} castShadow>
          <meshStandardMaterial map={friezeTex} side={THREE.DoubleSide} roughness={0.55} />
        </mesh>
        <mesh geometry={c.trim} castShadow>
          <meshStandardMaterial vertexColors side={THREE.DoubleSide} metalness={0.25} roughness={0.45} />
        </mesh>
        <mesh geometry={c.roof} castShadow receiveShadow>
          <meshStandardMaterial map={roofTex} color={selected ? pal.selected : '#ffffff'} side={THREE.DoubleSide} roughness={0.8} />
        </mesh>
        <mesh geometry={c.finial} castShadow>
          <meshStandardMaterial color={GOLD} metalness={0.5} roughness={0.35} />
        </mesh>
        <instancedMesh ref={bulbs} args={[c.bulb, undefined, c.bulbs.length]}>
          <meshBasicMaterial color="#ffe8a3" toneMapped={false} />
        </instancedMesh>
      </group>
    </group>
  );
}

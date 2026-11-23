// "Море" basseynlar majmuasi (fotoga qarab): travertin plitka, soyabon va shezlonglar, yelkan soyabonlar,
// lagun orolidagi dumaloq tomli bar va metall halqa arkalar, bolalar basseynidagi suv o'yin maydoni.
// Ko'p takrorlanadigan narsalar InstancedMesh (soyabon 2, shezlong 2 draw call).
import { useEffect, useLayoutEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import type { ThreeEvent } from '@react-three/fiber';
import { V, canvasTexture, colored, mergeAll, rod } from './modelKit';
import { multiToShapes, toWorld } from './geometry';
import type { XY } from './projection';
import type { Palette } from './theme';
import type { Building, ParkData } from './types';
import { waterLevelAt } from './water';

const DECK_Y = 0.025;

// ---------------------------------------------------------------- plitka

/** Travertin: och bej, 60×40 sm plitalar, qatorma-qator siljigan (UV metrda, 4×4 m da takrorlanadi) */
export function travertineTexture() {
  const PPM = 64, M = 4, S = PPM * M;
  const tex = canvasTexture(S, S, (g) => {
    g.fillStyle = '#cfc2ab'; // chok
    g.fillRect(0, 0, S, S);
    let s = 3;
    const rnd = () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
    const tw = 0.6 * PPM, th = 0.4 * PPM;
    for (let r = 0; r * th < S; r++) {
      for (let c = -1; c * tw < S + tw; c++) {
        const x = c * tw + (r % 2 ? tw / 2 : 0), y = r * th;
        const v = 0.94 + rnd() * 0.08, warm = rnd() * 0.04;
        g.fillStyle = `rgb(${Math.round(236 * v)},${Math.round(225 * v * (1 - warm / 2))},${Math.round(205 * v * (1 - warm))})`;
        for (const ox of [0, -S, S]) g.fillRect(x + ox + 1.2, y + 1.2, tw - 2.4, th - 2.4);
      }
    }
    for (let i = 0; i < 2600; i++) { // travertin g'ovaklari
      const v = 170 + rnd() * 50;
      g.fillStyle = `rgba(${v},${v - 10},${v - 25},0.28)`;
      g.fillRect(rnd() * S, rnd() * S, 1 + rnd() * 2, 1);
    }
  });
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(1 / M, 1 / M);
  return tex;
}

export function PoolDeck({ data, pal }: { data: ParkData; pal: Palette }) {
  const geo = useMemo(() => {
    if (!data.deck.length) return null;
    const g = new THREE.ShapeGeometry(multiToShapes(data.deck), 1); // UV = x, y metrda
    g.rotateX(-Math.PI / 2);
    return g;
  }, [data]);
  const tex = useMemo(() => travertineTexture(), []);
  useEffect(() => () => { geo?.dispose(); tex.dispose(); }, [geo, tex]);
  if (!geo) return null;
  return (
    <mesh geometry={geo} position-y={DECK_Y} receiveShadow>
      <meshStandardMaterial map={tex} color={pal.deckTint} roughness={0.9} polygonOffset polygonOffsetFactor={-1} />
    </mesh>
  );
}

// ---------------------------------------------------------------- soyabon, shezlong, yelkan

function umbrellaGeometry() {
  const pole = mergeAll([
    new THREE.CylinderGeometry(0.035, 0.035, 2.55, 5).translate(0, 1.275, 0),
    new THREE.CylinderGeometry(0.22, 0.26, 0.08, 8).translate(0, 0.04, 0), // tagligi
  ]);
  // To'rtburchak soyabon: 4 qirrali piramida (2.5×2.5 m), cheti biroz pastga osilgan
  const canopy = mergeAll([
    new THREE.ConeGeometry(1.77, 0.48, 4, 1, true).rotateY(Math.PI / 4).translate(0, 2.55, 0),
    new THREE.CylinderGeometry(1.77, 1.77, 0.16, 4, 1, true).rotateY(Math.PI / 4).translate(0, 2.25, 0), // osilgan chet
  ]);
  return { pole, canopy };
}

function loungerGeometry() {
  // lokal +x — bosh tomoni (suvdan teskari)
  const frame = mergeAll([
    new THREE.BoxGeometry(1.95, 0.06, 0.66).translate(0, 0.3, 0),
    ...[-0.85, 0.85].flatMap((x) => [-0.28, 0.28].map((z) => new THREE.BoxGeometry(0.05, 0.3, 0.05).translate(x, 0.15, z))),
  ]);
  const back = new THREE.BoxGeometry(0.72, 0.07, 0.6);
  back.rotateZ(0.6); // suyanchiq ko'tarilgan
  back.translate(0.62, 0.58, 0);
  const cushion = mergeAll([new THREE.BoxGeometry(1.25, 0.08, 0.6).translate(-0.33, 0.37, 0), back]);
  return { frame, cushion };
}

function sailGeometry(sails: ParkData['poolside']['sails']) {
  const fabric: number[] = [], posts: THREE.BufferGeometry[] = [];
  for (const [x, y, rot, s] of sails) {
    const c = Math.cos(rot), sn = Math.sin(rot);
    const local: [number, number, number][] = [[-s / 2, -s / 2.6, 3.3], [s / 2, -s / 2.6, 2.7], [0, s / 2, 3.8]];
    const pts = local.map(([lx, ly, h]) => toWorld([x + lx * c - ly * sn, y + lx * sn + ly * c], h));
    // biroz egilgan mato: markazi pastroq (3 ta uchburchakka bo'lib)
    const mid = pts[0].clone().add(pts[1]).add(pts[2]).multiplyScalar(1 / 3).add(V(0, -0.35, 0));
    for (let k = 0; k < 3; k++) fabric.push(...pts[k].toArray(), ...pts[(k + 1) % 3].toArray(), ...mid.toArray());
    for (const p of pts) posts.push(rod(V(p.x, 0, p.z), V(p.x, p.y + 0.15, p.z), 0.06, 5));
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(fabric, 3));
  g.computeVertexNormals();
  return { fabric: g, posts: posts.length ? mergeAll(posts) : null };
}

export function Poolside({ data, pal }: { data: ParkData; pal: Palette }) {
  const { umbrellas, loungers, sails } = data.poolside;
  const geo = useMemo(() => ({ ...umbrellaGeometry(), ...loungerGeometry(), sail: sailGeometry(sails) }), [sails]);
  useEffect(() => () => {
    for (const g of [geo.pole, geo.canopy, geo.frame, geo.cushion, geo.sail.fabric, geo.sail.posts]) g?.dispose();
  }, [geo]);
  const poles = useRef<THREE.InstancedMesh>(null!);
  const canopies = useRef<THREE.InstancedMesh>(null!);
  const frames = useRef<THREE.InstancedMesh>(null!);
  const cushions = useRef<THREE.InstancedMesh>(null!);

  useLayoutEffect(() => {
    const m = new THREE.Matrix4(), q = new THREE.Quaternion(), one = V(1, 1, 1), up = V(0, 1, 0), c = new THREE.Color();
    umbrellas.forEach(([x, y, rot, kind], i) => {
      m.compose(toWorld([x, y], DECK_Y), q.setFromAxisAngle(up, rot), one);
      poles.current.setMatrixAt(i, m);
      canopies.current.setMatrixAt(i, m);
      canopies.current.setColorAt(i, c.set(kind ? pal.umbrellaRed : pal.umbrella));
    });
    loungers.forEach(([x, y, rot, kind], i) => {
      m.compose(toWorld([x, y], DECK_Y), q.setFromAxisAngle(up, rot), one);
      frames.current.setMatrixAt(i, m);
      cushions.current.setMatrixAt(i, m);
      cushions.current.setColorAt(i, c.set(pal.lounger[kind % pal.lounger.length]));
    });
    for (const r of [poles, canopies, frames, cushions]) {
      r.current.instanceMatrix.needsUpdate = true;
      if (r.current.instanceColor) r.current.instanceColor.needsUpdate = true;
      r.current.computeBoundingSphere();
    }
  }, [umbrellas, loungers, pal]);

  const nU = Math.max(umbrellas.length, 1), nL = Math.max(loungers.length, 1);
  return (
    <>
      <instancedMesh ref={poles} args={[geo.pole, undefined, nU]} count={umbrellas.length} castShadow>
        <meshStandardMaterial color="#c9cdd2" metalness={0.4} roughness={0.5} />
      </instancedMesh>
      <instancedMesh ref={canopies} args={[geo.canopy, undefined, nU]} count={umbrellas.length} castShadow receiveShadow>
        <meshStandardMaterial roughness={0.85} side={THREE.DoubleSide} />
      </instancedMesh>
      <instancedMesh ref={frames} args={[geo.frame, undefined, nL]} count={loungers.length} receiveShadow>
        <meshStandardMaterial color="#e9ecef" roughness={0.6} />
      </instancedMesh>
      <instancedMesh ref={cushions} args={[geo.cushion, undefined, nL]} count={loungers.length} castShadow receiveShadow>
        <meshStandardMaterial roughness={0.8} />
      </instancedMesh>
      {sails.length > 0 && (
        <>
          <mesh geometry={geo.sail.fabric} castShadow receiveShadow>
            <meshStandardMaterial color={pal.sail} roughness={0.9} side={THREE.DoubleSide} />
          </mesh>
          {geo.sail.posts && (
            <mesh geometry={geo.sail.posts} castShadow>
              <meshStandardMaterial color="#8d939a" metalness={0.4} roughness={0.5} />
            </mesh>
          )}
        </>
      )}
    </>
  );
}

// ---------------------------------------------------------------- orol bari va metall arkalar

function thatchTexture() {
  // Dumaloq tom: markazdan tarqaluvchi yog'och plankalar (UV — CylinderGeometry: u aylana bo'ylab)
  const tex = canvasTexture(256, 64, (g, W, H) => {
    g.fillStyle = '#6a4529'; g.fillRect(0, 0, W, H);
    for (let i = 0; i < 64; i++) {
      const v = 0.8 + ((i * 37) % 11) / 30;
      g.fillStyle = `rgb(${Math.round(110 * v)},${Math.round(72 * v)},${Math.round(42 * v)})`;
      g.fillRect(i * 4, 0, 3, H);
    }
  });
  tex.wrapS = THREE.RepeatWrapping;
  return tex;
}

const isTap = (e: ThreeEvent<MouseEvent>) => e.delta < 6;

/** Orol bari: yog'och-oyna dumaloq bino, keng dumaloq tom, atrofida bar peshtaxtasi; ustida kumushrang halqa arkalar */
export function IslandBar({ b, pal, selected, onSelect, night }: {
  b: Building; pal: Palette; selected: boolean; onSelect: (id: string) => void; night: boolean;
}) {
  const g = useMemo(() => {
    const ring = b.poly[0].slice(0, -1);
    const cx = ring.reduce((s, p) => s + p[0], 0) / ring.length, cy = ring.reduce((s, p) => s + p[1], 0) / ring.length;
    const R = ring.reduce((s, p) => s + Math.hypot(p[0] - cx, p[1] - cy), 0) / ring.length;
    const c = toWorld([cx, cy]);
    const rb = R * 0.42; // bar kichik — atrofida shezlonglarga joy qoladi
    const body = mergeAll([
      colored(new THREE.CylinderGeometry(rb, rb, 2.6, 24, 1, true).translate(0, 1.3, 0), '#7b5232'),
      colored(new THREE.CylinderGeometry(rb + 0.75, rb + 0.75, 1.1, 28, 1, true).translate(0, 0.55, 0), '#8a5c36'), // peshtaxta
      colored(new THREE.RingGeometry(rb, rb + 0.8, 28).rotateX(-Math.PI / 2).translate(0, 1.12, 0), '#e9e4da'), // peshtaxta usti
      ...Array.from({ length: 8 }, (_, k) => { // tom ustunlari
        const a = (k / 8) * Math.PI * 2;
        return colored(new THREE.CylinderGeometry(0.09, 0.09, 3.0, 6).translate(Math.cos(a) * (rb + 1.25), 1.5, Math.sin(a) * (rb + 1.25)), '#5b3c22');
      }),
    ]);
    body.translate(c.x, 0, c.z);
    const roof = new THREE.CylinderGeometry(0.3, rb + 1.75, 1.1, 32, 1, false).translate(c.x, 3.5, c.z);
    // Halqa arkalar: uchta katta halqa, har biri ikki qavat quvur (ferma kabi), turli burchakda
    const rings: THREE.BufferGeometry[] = [];
    const RR = R + 2.6;
    [0, 1.05, 2.1].forEach((yaw, k) => {
      for (const dr of [0, 0.38]) {
        const t = new THREE.TorusGeometry(RR - dr, 0.09, 5, 56);
        t.rotateX(k === 2 ? 0.25 : 0); // bittasi biroz qiya
        t.rotateY(yaw);
        t.translate(c.x, RR - 1.4, c.z); // pastki qismi yer ostida — kamar bo'lib ko'rinadi
        rings.push(t);
      }
    });
    // ferma bog'lovchilari: ikki halqa orasida kalta tayoqchalar
    [0, 1.05, 2.1].forEach((yaw, k) => {
      for (let i = 0; i < 28; i++) {
        const a = (i / 28) * Math.PI * 2;
        const p1 = V(Math.cos(a) * RR, Math.sin(a) * RR, 0), p2 = V(Math.cos(a) * (RR - 0.38), Math.sin(a) * (RR - 0.38), 0);
        const r = rod(p1, p2, 0.035, 3);
        r.rotateX(k === 2 ? 0.25 : 0); r.rotateY(yaw); r.translate(c.x, RR - 1.4, c.z);
        rings.push(r);
      }
    });
    return { body, roof, rings: mergeAll(rings), top: 4.2 };
  }, [b]);
  const tex = useMemo(() => thatchTexture(), []);
  useEffect(() => () => { g.body.dispose(); g.roof.dispose(); g.rings.dispose(); tex.dispose(); }, [g, tex]);
  return (
    <group onClick={(e) => { if (!isTap(e)) return; e.stopPropagation(); onSelect(b.id); }}>
      <mesh geometry={g.body} castShadow receiveShadow>
        <meshStandardMaterial vertexColors roughness={0.8} side={THREE.DoubleSide}
          color={selected ? pal.selected : '#ffffff'} emissive="#ffcf8a" emissiveIntensity={night ? 0.25 : 0} />
      </mesh>
      <mesh geometry={g.roof} castShadow receiveShadow>
        <meshStandardMaterial map={tex} color={selected ? pal.selected : '#ffffff'} roughness={0.9} />
      </mesh>
      <mesh geometry={g.rings} castShadow>
        <meshStandardMaterial color="#d7dbe0" metalness={0.75} roughness={0.3} />
      </mesh>
    </group>
  );
}

// ---------------------------------------------------------------- bolalar suv o'yin maydoni

/** Rangli minoralar, yashil qo'ziqorin, to'q sariq tekis va spiral tepalik, ko'k quvur tepalik. Lokal +z — bearing tomoni */
function playgroundGeometry() {
  const parts: THREE.BufferGeometry[] = [];
  const add = (g: THREE.BufferGeometry, hex: string) => parts.push(colored(g, hex));
  const box = (w: number, h: number, d: number, x: number, y: number, z: number, hex: string) =>
    add(new THREE.BoxGeometry(w, h, d).translate(x, y, z), hex);
  // Asosiy maydoncha: ustunlar va ikki qavat pol
  for (const [x, z] of [[-1.6, -1.2], [1.6, -1.2], [-1.6, 1.2], [1.6, 1.2], [0, -1.2], [0, 1.2]]) {
    add(new THREE.CylinderGeometry(0.09, 0.09, 3.2, 6).translate(x, 1.6, z), '#f2f2f2');
  }
  box(3.6, 0.15, 2.8, 0, 1.2, 0, '#2f9de0');
  box(1.8, 0.15, 2.6, -0.9, 2.3, 0, '#f2c230');
  // Minoracha tomlari
  box(1.4, 0.7, 1.4, -1.4, 3.55, -0.9, '#f5c518');
  add(new THREE.ConeGeometry(0.8, 0.9, 4).rotateY(Math.PI / 4).translate(-1.4, 4.35, -0.9), '#e8443a');
  add(new THREE.CylinderGeometry(0.55, 0.55, 0.9, 12).translate(1.3, 3.5, 0.8), '#f06fae');
  add(new THREE.ConeGeometry(0.65, 0.7, 12).translate(1.3, 4.3, 0.8), '#e8443a');
  box(1.1, 0.5, 1.1, 1.4, 3.2, -1.0, '#f5c518');
  // Suv chelagi (ag'dariladigan)
  add(new THREE.CylinderGeometry(0.45, 0.32, 0.6, 10).translate(0.2, 4.0, 0), '#e8443a');
  add(new THREE.CylinderGeometry(0.04, 0.04, 1.2, 4).translate(0.2, 3.3, 0), '#f2f2f2');
  // To'r panjaralar (yashil)
  box(3.6, 0.6, 0.06, 0, 1.6, -1.4, '#3fb25b');
  box(3.6, 0.6, 0.06, 0, 1.6, 1.4, '#3fb25b');
  // Yashil qo'ziqorin favvora (yonida)
  add(new THREE.CylinderGeometry(0.22, 0.3, 2.2, 10).translate(3.2, 1.1, -1.6), '#f2f2f2');
  add(new THREE.SphereGeometry(1.35, 18, 8, 0, Math.PI * 2, 0, Math.PI / 2).scale(1, 0.55, 1).translate(3.2, 2.15, -1.6), '#45b649');
  // To'q sariq tekis tepalik: 2.3 m dan suvgacha, +z tomonga 9 m
  const L = 9, h0 = 2.3, ang = Math.atan2(h0 - 0.1, L);
  const slide = new THREE.BoxGeometry(0.9, 0.12, Math.hypot(L, h0)).rotateX(ang).translate(-0.9, h0 / 2 + 0.05, 1.4 + L / 2);
  add(slide, '#f07a1c');
  for (const s of [-1, 1]) add(new THREE.BoxGeometry(0.1, 0.3, Math.hypot(L, h0)).rotateX(ang).translate(-0.9 + s * 0.45, h0 / 2 + 0.2, 1.4 + L / 2), '#e0661a');
  // To'q sariq spiral tepalik (−x tomonda)
  const helix = new THREE.CatmullRomCurve3(Array.from({ length: 30 }, (_, i) => {
    const t = i / 29, a = t * Math.PI * 2.2 + Math.PI / 2;
    return V(-3.6 + Math.cos(a) * 1.7, 3.0 - t * 2.8, 1.2 + Math.sin(a) * 1.7);
  }));
  add(new THREE.TubeGeometry(helix, 70, 0.42, 8, false), '#f07a1c');
  // Ko'k quvur tepalik (+x tomonda)
  const tube = new THREE.CatmullRomCurve3([V(1.6, 2.3, 0.6), V(2.8, 1.9, 1.6), V(3.4, 1.2, 3.2), V(2.6, 0.6, 4.6), V(1.5, 0.25, 5.2)]);
  add(new THREE.TubeGeometry(tube, 40, 0.38, 8, false), '#2f7fe0');
  // Suvdagi kichik o'yinchoqlar (favvoracha halqalari)
  for (const [x, z, hex] of [[2.6, 6.5, '#ffffff'], [-2.8, 6.0, '#ffffff'], [0.6, 7.8, '#ffffff']] as [number, number, string][]) {
    add(new THREE.TorusGeometry(0.45, 0.08, 6, 16).rotateX(Math.PI / 2).translate(x, 0.08, z), hex);
  }
  return mergeAll(parts);
}

export function KidsPlayground({ data }: { data: ParkData }) {
  const pg = useMemo(() => Object.values(data.poolFx).map((fx) => fx.playground).find(Boolean) ?? null, [data]);
  const geo = useMemo(() => (pg ? playgroundGeometry() : null), [pg]);
  useEffect(() => () => geo?.dispose(), [geo]);
  if (!pg || !geo) return null;
  const [x, y, bearing] = pg;
  const level = waterLevelAt([x, y] as XY, data.water) ?? 0;
  // bearing — shimoldan soat bo'yicha; lokal +z shu yo'nalishga
  const yaw = Math.PI - THREE.MathUtils.degToRad(bearing);
  return (
    <mesh geometry={geo} position={toWorld([x, y], level - 0.05)} rotation-y={yaw} castShadow receiveShadow>
      <meshStandardMaterial vertexColors roughness={0.55} />
    </mesh>
  );
}

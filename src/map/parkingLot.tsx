// Parking (fotoga qarab): asfalt, oq chiziqlar, bordyurli daraxt orolchalari, mashinalar, darvoza shlagbaumi,
// qorovul budkasi, yo'lak tepasidagi past bino va tomli soyabon. Joylashuv build-map da hisoblanadi (types.ts → ParkingLayout).
// Ko'p takrorlanadiganlar InstancedMesh: chiziqlar, orolchalar, mashinalar — har biri 1–2 draw call.
import { useEffect, useLayoutEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame, type ThreeEvent } from '@react-three/fiber';
import { V, canvasTexture, colored, mergeAll, prefersReducedMotion, useAmbientFrames } from './modelKit';
import { PARKING_TRAFFIC } from './config';
import { createTraffic, type Car } from './parkingTraffic';
import { extrude, polyToShape, toWorld } from './geometry';
import type { XY } from './projection';
import type { Palette } from './theme';
import type { Area, ParkData, ParkingLayout } from './types';

const LOT_TOP = 0.07; // asfalt sathi
const LINE_Y = LOT_TOP + 0.004;
const LIE_FLAT: [number, number, number] = [-Math.PI / 2, 0, 0];
const UP = V(0, 1, 0);
const isTap = (e: ThreeEvent<MouseEvent>) => e.delta < 6;

/** Mashina ranglari (layout dagi indeks): oq, kumush, qora, kulrang, to'q ko'k, qizil, bej, to'q yashil */
const CAR_COLORS = ['#f2f2ef', '#b9bdc2', '#1f2124', '#6c7077', '#25416f', '#a8262b', '#d4c4a2', '#2f4a3a'];

// ---------------------------------------------------------------- teksturalar

/** Och asfalt (fotodagidek kulrang-bej): mayda donador, ba'zi joyda dog'lar; UV metrda, 8×8 m da takrorlanadi */
function asphaltTexture() {
  const S = 256, M = 8;
  const tex = canvasTexture(S, S, (g) => {
    g.fillStyle = 'rgb(214,212,207)';
    g.fillRect(0, 0, S, S);
    let s = 11;
    const rnd = () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
    for (let i = 0; i < 9000; i++) {
      const v = 175 + rnd() * 70;
      g.fillStyle = `rgba(${v},${v - 2},${v - 6},0.5)`;
      g.fillRect(rnd() * S, rnd() * S, 1 + rnd(), 1 + rnd());
    }
    for (let i = 0; i < 7; i++) { // yamoq va moy dog'lari
      const x = rnd() * S, y = rnd() * S, r = 10 + rnd() * 26;
      const gr = g.createRadialGradient(x, y, 0, x, y, r);
      gr.addColorStop(0, 'rgba(120,118,112,0.22)');
      gr.addColorStop(1, 'rgba(120,118,112,0)');
      g.fillStyle = gr;
      for (const ox of [0, -S, S]) for (const oy of [0, -S, S]) g.fillRect(x - r + ox, y - r + oy, r * 2, r * 2);
    }
  });
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(1 / M, 1 / M);
  return tex;
}

/** To'lqinli metall tom: tom chetiga perpendikulyar qovurg'alar (u — metrda, 1 m da takrorlanadi) */
function metalTexture() {
  const tex = canvasTexture(64, 8, (g, w, h) => {
    for (let x = 0; x < w; x++) {
      const v = 200 + 40 * Math.cos((x / w) * Math.PI * 2 * 4);
      g.fillStyle = `rgb(${v},${v + 2},${v + 5})`;
      g.fillRect(x, 0, 1, h);
    }
  });
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  return tex;
}

// ---------------------------------------------------------------- geometriyalar

/** Past polili mashina: kuzov (bo'yoq), salon (tomi bo'yoq, oynalar to'q), g'ildiraklar. Old tomoni +X */
function carGeometry() {
  const prof = (pts: number[][], width: number) => {
    const g = new THREE.ExtrudeGeometry(new THREE.Shape(pts.map(([x, y]) => new THREE.Vector2(x, y))), { depth: width, bevelEnabled: false });
    g.translate(0, 0, -width / 2);
    return g;
  };
  const body = colored(prof([[-2.25, 0.28], [2.2, 0.28], [2.26, 0.46], [2.14, 0.72], [1.15, 0.84], [-1.95, 0.86], [-2.26, 0.7]], 1.8), '#ffffff');
  const cabin = prof([[-1.66, 0.82], [0.98, 0.82], [0.42, 1.36], [-1.26, 1.38]], 1.5);
  // Salon: faqat tekis tomi bo'yoq rangida, qolgani (oynalar) to'q
  {
    const n = cabin.attributes.normal, p = cabin.attributes.position;
    const col = new Float32Array(p.count * 3);
    const glass = new THREE.Color('#27313b'), paint = new THREE.Color('#ffffff');
    for (let i = 0; i < p.count; i++) (n.getY(i) > 0.97 ? paint : glass).toArray(col, i * 3);
    cabin.setAttribute('color', new THREE.BufferAttribute(col, 3));
  }
  const wheels = [-1.42, 1.42].flatMap((x) => [-0.8, 0.8].map((z) => {
    const w = new THREE.CylinderGeometry(0.33, 0.33, 0.24, 7, 1, true);
    w.rotateX(Math.PI / 2);
    w.translate(x, 0.33, z);
    return colored(w, '#121212');
  }));
  // Orqa chiroqlar (qizil) va old chiroqlar (och)
  const lamp = (x: number, z: number, hex: string) => colored(new THREE.BoxGeometry(0.06, 0.12, 0.34).translate(x, 0.62, z), hex);
  const lights = [lamp(-2.26, -0.6, '#b3121b'), lamp(-2.26, 0.6, '#b3121b'), lamp(2.2, -0.62, '#f3f0e2'), lamp(2.2, 0.62, '#f3f0e2')];
  return mergeAll([body, cabin, ...wheels, ...lights]);
}

/** Yassi strelka: +X tomonga, 3 m */
function arrowGeometry() {
  const s = new THREE.Shape([[-1.5, -0.17], [0.4, -0.17], [0.4, -0.5], [1.5, 0], [0.4, 0.5], [0.4, 0.17], [-1.5, 0.17]].map(([x, y]) => new THREE.Vector2(x, y)));
  const g = new THREE.ShapeGeometry(s);
  g.rotateX(-Math.PI / 2);
  return g;
}

/** Lokal koordinatada (s — a→b bo'ylab, t — chap tomonga) qurilgan geometriyani joyiga qo'yadi */
function placeLocal(g: THREE.BufferGeometry, a: XY, b: XY) {
  const ang = Math.atan2(b[1] - a[1], b[0] - a[0]);
  g.applyMatrix4(new THREE.Matrix4().makeRotationY(ang));
  g.translate(a[0], 0, -a[1]);
  return g;
}

/** Lokal to'rtburchak (s0..s1 × t0..t1), balandligi y0..y1 — ExtrudeGeometry, UV metrda (s, t) */
function localBox(s0: number, s1: number, t0: number, t1: number, y0: number, y1: number) {
  const g = extrude(new THREE.Shape([[s0, t0], [s1, t0], [s1, t1], [s0, t1]].map(([x, y]) => new THREE.Vector2(x, y))), y1 - y0);
  g.rotateX(-Math.PI / 2);
  g.translate(0, y0, 0);
  return g;
}

/** Yo'lak tepasidagi uzun past bino: devorlar, old tomonida derazalar va eshik, ikki rangli metall tom */
function buildingGeometry(bld: NonNullable<ParkingLayout['building']>) {
  const L = Math.hypot(bld.b[0] - bld.a[0], bld.b[1] - bld.a[1]);
  const { depth: d, height: h } = bld;
  const walls = colored(localBox(0, L, 0, d, 0, h), '#ffffff');
  const glass: THREE.BufferGeometry[] = [];
  for (let s = 1.4; s < L - 1; s += 2.3) {
    const door = Math.abs(s - L * 0.55) < 1.2;
    glass.push(door ? localBox(s - 0.5, s + 0.5, -0.04, 0.02, 0.05, 2.15) : localBox(s - 0.65, s + 0.65, -0.04, 0.02, 1.0, 2.05));
  }
  const cut = L * 0.62;
  const roofA = localBox(-0.3, cut, -0.45, d + 0.3, h, h + 0.12);
  const roofB = localBox(cut, L + 0.3, -0.45, d + 0.3, h + 0.02, h + 0.14);
  return {
    walls: placeLocal(walls, bld.a, bld.b),
    glass: placeLocal(mergeAll(glass), bld.a, bld.b),
    roofA: placeLocal(roofA, bld.a, bld.b),
    roofB: placeLocal(roofB, bld.a, bld.b),
  };
}

/** Tomli soyabon: orqa chetda (parking cheti) ustunlar, tom old tomonga qarab biroz ko'tarilgan */
function canopyGeometry(c: NonNullable<ParkingLayout['canopy']>) {
  const L = Math.hypot(c.b[0] - c.a[0], c.b[1] - c.a[1]);
  const posts: THREE.BufferGeometry[] = [];
  const n = Math.max(2, Math.round(L / 3.6) + 1);
  for (let i = 0; i < n; i++) {
    const s = 0.2 + ((L - 0.4) * i) / (n - 1);
    posts.push(localBox(s - 0.07, s + 0.07, 0.15, 0.29, 0, 2.8));
    posts.push(localBox(s - 0.05, s + 0.05, 0.22, c.depth * 0.55, 2.62, 2.74)); // tom ostidagi to'sin
  }
  const roof = new THREE.BoxGeometry(L + 0.4, 0.07, c.depth + 0.3);
  const slope = Math.atan2(0.35, c.depth);
  roof.rotateX(slope); // old tomoni (t katta, ya'ni -Z) balandroq
  roof.translate(L / 2, 2.82 + 0.17, -(c.depth / 2));
  // BoxGeometry UV: 0..1 — qovurg'alar metrda chiqishi uchun u ni uzunlikka ko'paytiramiz
  const uv = roof.attributes.uv as THREE.BufferAttribute;
  for (let i = 0; i < uv.count; i++) uv.setX(i, uv.getX(i) * (L + 0.4));
  return { posts: placeLocal(mergeAll(posts), c.a, c.b), roof: placeLocal(roof, c.a, c.b) };
}

/** Darvoza: ikki shlagbaum (qo'llari alohida — mashina yaqinlashganda ko'tariladi) va qorovul budkasi */
function gateGeometry(gate: NonNullable<ParkingLayout['gate']>, kiosk: ParkingLayout['kiosk']) {
  const o: XY = [Math.cos(gate.rot), Math.sin(gate.rot)], side: XY = [-o[1], o[0]];
  const base: XY = [gate.at[0] - o[0] * 2.4, gate.at[1] - o[1] * 2.4];
  const parts: THREE.BufferGeometry[] = [];
  const len = gate.width / 2 - 0.25;
  // Qo'l: lokal +X bo'ylab qizil-oq bo'laklar, sharniri nolda
  const armParts: THREE.BufferGeometry[] = [];
  for (let x = 0.2, k = 0; x < len; x += 0.5, k++) {
    const w = Math.min(0.5, len - x);
    armParts.push(colored(new THREE.BoxGeometry(w, 0.08, 0.08).translate(x + w / 2, 0, 0), k % 2 ? '#f4f4f4' : '#d0242b'));
  }
  const arm = mergeAll(armParts);
  /** 0 — kirish (+side bo'lak), 1 — chiqish */
  const arms = [1, -1].map((sg) => {
    const p: XY = [base[0] + side[0] * sg * (gate.width / 2 + 0.25), base[1] + side[1] * sg * (gate.width / 2 + 0.25)];
    const yaw = Math.atan2(-side[1] * sg, -side[0] * sg);
    parts.push(colored(new THREE.BoxGeometry(0.32, 1.0, 0.32).translate(0, 0.5, 0), '#e8b100')
      .applyMatrix4(new THREE.Matrix4().makeRotationY(yaw)).translate(p[0], LOT_TOP, -p[1]));
    return { pos: [p[0], LOT_TOP + 0.92, -p[1]] as [number, number, number], yaw };
  });
  let kioskGlass: THREE.BufferGeometry | null = null;
  if (kiosk) {
    const [kx, ky, kr] = kiosk;
    const walls = colored(new THREE.BoxGeometry(2.3, 2.5, 2.0).translate(0, 1.25, 0), '#f1f0ec');
    const roof = colored(new THREE.BoxGeometry(2.9, 0.16, 2.6).translate(0, 2.58, 0), '#6f777e');
    const m = new THREE.Matrix4().makeRotationY(kr).setPosition(kx, 0, -ky);
    parts.push(mergeAll([walls, roof]).applyMatrix4(m));
    kioskGlass = new THREE.BoxGeometry(2.34, 0.8, 2.04).translate(0, 1.55, 0).applyMatrix4(m);
  }
  return { solid: mergeAll(parts), kioskGlass, arm, arms };
}

/** Kechasi harakatdagi mashina oldidagi yorug'lik dog'i (oldinga cho'zilgan, uchi xira) */
function headlightTexture() {
  return canvasTexture(128, 64, (g, w, h) => {
    const gr = g.createRadialGradient(8, h / 2, 2, 8, h / 2, w);
    gr.addColorStop(0, 'rgba(255,236,190,0.9)');
    gr.addColorStop(0.45, 'rgba(255,226,170,0.35)');
    gr.addColorStop(1, 'rgba(255,220,160,0)');
    g.fillStyle = gr;
    g.beginPath(); g.moveTo(0, h * 0.38); g.lineTo(w, 0); g.lineTo(w, h); g.lineTo(0, h * 0.62); g.closePath(); g.fill();
  });
}

// ---------------------------------------------------------------- komponent

function ParkingLot({ area, layout, pal, night, selected, onSelect }: {
  area: Area; layout: ParkingLayout; pal: Palette; night: boolean; selected: boolean; onSelect: (id: string) => void;
}) {
  const [W, D] = layout.stall;
  const geo = useMemo(() => {
    const surface = extrude(polyToShape(area.poly), LOT_TOP);
    const line = new THREE.PlaneGeometry(D, 0.1).rotateX(-Math.PI / 2);
    const islandCurb = new THREE.BoxGeometry(1, 0.2, 1).translate(0, 0.1, 0);
    const islandGrass = new THREE.BoxGeometry(1, 0.24, 1).translate(0, 0.12, 0); // bordyurdan biroz baland — chetida beton halqa ko'rinadi
    const car = carGeometry();
    const arrow = arrowGeometry();
    // Chiroq dog'i: 1×1 tekislik, chap cheti mashina tumshug'ida (+X oldinga)
    const beam = new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2).translate(0.5, 0, 0);
    // Bordyur: chet bo'ylab past beton, darvoza va piyoda kirishda uzilgan
    const curbs: THREE.BufferGeometry[] = [];
    const ring = area.poly[0];
    const open = (p: XY) =>
      (layout.gate && Math.hypot(p[0] - layout.gate.at[0], p[1] - layout.gate.at[1]) < layout.gate.width * 1.6) ||
      (layout.ped && Math.hypot(p[0] - layout.ped.at[0], p[1] - layout.ped.at[1]) < 2.2);
    for (let i = 0; i < ring.length - 1; i++) {
      const a = ring[i], b = ring[i + 1];
      const L = Math.hypot(b[0] - a[0], b[1] - a[1]);
      if (L < 0.05 || open([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2])) continue;
      const g = new THREE.BoxGeometry(L + 0.2, 0.17, 0.22).translate(L / 2, LOT_TOP + 0.03, 0);
      curbs.push(placeLocal(g, a, b));
    }
    // Zebra: piyoda kirishdan ichkariga
    const zebra: THREE.BufferGeometry[] = [];
    if (layout.ped) {
      const { at, rot } = layout.ped;
      for (let k = 0; k < 5; k++) {
        const g = new THREE.PlaneGeometry(0.45, 2.6).rotateX(-Math.PI / 2).translate(1.0 + k * 0.9, LINE_Y, 0);
        g.applyMatrix4(new THREE.Matrix4().makeRotationY(rot));
        g.translate(at[0], 0, -at[1]);
        zebra.push(g);
      }
    }
    return {
      surface, line, islandCurb, islandGrass, car, arrow, beam,
      curb: curbs.length ? mergeAll(curbs) : null,
      zebra: zebra.length ? mergeAll(zebra) : null,
      building: layout.building ? buildingGeometry(layout.building) : null,
      canopy: layout.canopy ? canopyGeometry(layout.canopy) : null,
      gate: layout.gate ? gateGeometry(layout.gate, layout.kiosk) : null,
    };
  }, [area, layout, D]);
  const tex = useMemo(() => ({ asphalt: asphaltTexture(), metal: metalTexture(), beam: headlightTexture() }), []);
  useEffect(() => () => {
    const { building, canopy, gate, ...rest } = geo;
    for (const g of Object.values(rest)) (g as THREE.BufferGeometry | null)?.dispose();
    for (const g of [building?.walls, building?.glass, building?.roofA, building?.roofB, canopy?.posts, canopy?.roof, gate?.solid, gate?.kioskGlass, gate?.arm]) g?.dispose();
  }, [geo]);
  useEffect(() => () => { tex.asphalt.dispose(); tex.metal.dispose(); tex.beam.dispose(); }, [tex]);

  const lines = useRef<THREE.InstancedMesh>(null!);
  const curbs = useRef<THREE.InstancedMesh>(null!);
  const grass = useRef<THREE.InstancedMesh>(null!);
  const cars = useRef<THREE.InstancedMesh>(null!);
  const arrows = useRef<THREE.InstancedMesh>(null!);
  useLayoutEffect(() => {
    const m = new THREE.Matrix4(), q = new THREE.Quaternion(), s = V(1, 1, 1), c = new THREE.Color();
    // Har joyning ikki yon chizig'i (qo'shni joylarniki ustma-ust tushadi — sezilmaydi)
    layout.stalls.forEach(([x, y, r], i) => {
      const u: XY = [-Math.sin(r), Math.cos(r)];
      q.setFromAxisAngle(UP, r);
      for (const sg of [0, 1]) {
        const k = sg ? 1 : -1;
        m.compose(toWorld([x + u[0] * k * W / 2, y + u[1] * k * W / 2], LINE_Y), q, s);
        lines.current.setMatrixAt(i * 2 + sg, m);
      }
    });
    layout.islands.forEach(([x, y, r, len, wid], i) => {
      q.setFromAxisAngle(UP, r);
      m.compose(toWorld([x, y], LOT_TOP - 0.02), q, V(len, 1, wid));
      curbs.current.setMatrixAt(i, m);
      m.compose(toWorld([x, y], LOT_TOP - 0.02), q, V(Math.max(len - 0.36, 0.2), 1, Math.max(wid - 0.36, 0.2)));
      grass.current.setMatrixAt(i, m);
    });
    layout.arrows.forEach(([x, y, r], i) => {
      m.compose(toWorld([x, y], LINE_Y), q.setFromAxisAngle(UP, r), s);
      arrows.current.setMatrixAt(i, m);
    });
    for (const ref of [lines, curbs, grass, arrows]) {
      ref.current.instanceMatrix.needsUpdate = true;
      ref.current.computeBoundingSphere();
    }
    void c;
  }, [layout, W]);

  // ---- Mashinalar: turganlari va harakatdagilari bitta InstancedMesh da ----
  const animate = PARKING_TRAFFIC.enabled && !prefersReducedMotion();
  const traffic = useMemo(() => (animate ? createTraffic(area, layout, PARKING_TRAFFIC) : null), [animate, area, layout]);
  // Harakatsiz holat uchun ham bir xil ko'rinish: layout dagi mashinalar
  const staticCars = useMemo<Car[]>(() => layout.cars.map(([x, y, h, color, kind]) => (
    { color, kind, stall: null, state: 'parked', pose: { x, y, h }, legs: [], leg: 0, s: 0, scale: 1 })), [layout]);
  const capacity = Math.max(layout.stalls.length + PARKING_TRAFFIC.maxMoving + 2, layout.cars.length, 1);
  const beams = useRef<THREE.InstancedMesh>(null!);
  const armRefs = [useRef<THREE.Mesh>(null!), useRef<THREE.Mesh>(null!)];
  const colorOf = useRef<number[]>([]);
  const tmp = useMemo(() => ({ m: new THREE.Matrix4(), q: new THREE.Quaternion(), s: V(1, 1, 1), p: V(0, 0, 0), c: new THREE.Color() }), []);
  const writeCars = () => {
    const { m, q, s, p, c } = tmp;
    const list = traffic ? traffic.sim.cars : staticCars;
    const n = Math.min(list.length, capacity);
    let colors = false, nb = 0;
    for (let i = 0; i < n; i++) {
      const car = list[i];
      const k = car.state === 'gone' ? 0 : car.scale;
      q.setFromAxisAngle(UP, car.pose.h);
      m.compose(p.set(car.pose.x, LOT_TOP, -car.pose.y), q, car.kind ? s.set(1.03 * k, 1.14 * k, 1.07 * k) : s.set(k, k, k));
      cars.current.setMatrixAt(i, m);
      if (colorOf.current[i] !== car.color) {
        colorOf.current[i] = car.color;
        cars.current.setColorAt(i, c.set(CAR_COLORS[car.color % CAR_COLORS.length]));
        colors = true;
      }
      // Harakatdagi mashina oldidagi chiroq dog'i (faqat kechasi ko'rinadi)
      if ((car.state === 'arriving' || car.state === 'departing') && k > 0.2 && nb < PARKING_TRAFFIC.maxMoving + 2) {
        m.compose(p.set(car.pose.x + Math.cos(car.pose.h) * 2.1, LOT_TOP + 0.02, -(car.pose.y + Math.sin(car.pose.h) * 2.1)), q, s.set(7 * k, 1, 3.4 * k));
        beams.current.setMatrixAt(nb++, m);
      }
    }
    cars.current.count = n;
    cars.current.instanceMatrix.needsUpdate = true;
    if (colors && cars.current.instanceColor) cars.current.instanceColor.needsUpdate = true;
    beams.current.count = nb;
    beams.current.instanceMatrix.needsUpdate = true;
    if (traffic) armRefs.forEach((r, k) => { if (r.current) r.current.rotation.z = traffic.sim.arms[k] * 1.3; });
  };
  useLayoutEffect(() => {
    colorOf.current = [];
    writeCars();
    cars.current.computeBoundingSphere();
    // Harakatdagi mashina parking chegarasidan chiqmaydi — bounding sphere bir marta, butun parking bo'yicha
    const ring = area.poly[0];
    const xs = ring.map((p) => p[0]), ys = ring.map((p) => p[1]);
    const ctr = V((Math.min(...xs) + Math.max(...xs)) / 2, 1, -(Math.min(...ys) + Math.max(...ys)) / 2);
    const rad = Math.hypot(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)) / 2 + 8;
    cars.current.boundingSphere = new THREE.Sphere(ctr, rad);
    beams.current.boundingSphere = new THREE.Sphere(ctr.clone(), rad);
  }, [traffic, staticCars]); // eslint-disable-line react-hooks/exhaustive-deps

  useAmbientFrames(!!traffic);
  const paused = useRef(false); // faqat dev sinovlari uchun
  useEffect(() => {
    if (!import.meta.env.DEV || !traffic) return;
    (window as unknown as { __parking: unknown }).__parking = {
      traffic,
      advance: (sec: number) => { for (let t = 0; t < sec; t += 0.05) traffic.step(0.05); writeCars(); },
      pause: (on: boolean) => { paused.current = on; },
    };
  }, [traffic]); // eslint-disable-line react-hooks/exhaustive-deps
  useFrame((_, dt) => {
    if (!traffic || paused.current) return;
    // Sekin kadrda ham bir tekis: 0.05 s li qadamlar, oxirgi kadr 0.5 s dan oshsa — kesamiz
    let left = Math.min(dt, 0.5), changed = false;
    while (left > 1e-6) { const h = Math.min(left, 0.05); changed = traffic.step(h) || changed; left -= h; }
    if (changed) writeCars();
  });

  const lineColor = pal.parkingEdge;
  const glowGlass = night ? { emissive: '#ffcf8a', emissiveIntensity: 1.1 } : { emissive: '#000000', emissiveIntensity: 0 };
  const nS = Math.max(layout.stalls.length * 2, 1), nI = Math.max(layout.islands.length, 1);
  const nA = Math.max(layout.arrows.length, 1);
  return (
    <group userData={{ parking: area.id }}>
      <mesh geometry={geo.surface} rotation={LIE_FLAT} receiveShadow
        onClick={(e) => { if (!isTap(e)) return; e.stopPropagation(); onSelect(area.id); }}>
        <meshStandardMaterial attach="material-0" map={tex.asphalt} color={selected ? pal.selected : pal.parkingLot} roughness={0.95} />
        <meshStandardMaterial attach="material-1" color={pal.roadSide} roughness={0.95} />
      </mesh>
      {geo.curb && (
        <mesh geometry={geo.curb} receiveShadow>
          <meshStandardMaterial color={pal.curb} roughness={0.9} />
        </mesh>
      )}
      <instancedMesh ref={lines} args={[geo.line, undefined, nS]} count={layout.stalls.length * 2} receiveShadow>
        <meshStandardMaterial color={lineColor} roughness={0.8} polygonOffset polygonOffsetFactor={-2} />
      </instancedMesh>
      <instancedMesh ref={arrows} args={[geo.arrow, undefined, nA]} count={layout.arrows.length} receiveShadow>
        <meshStandardMaterial color={lineColor} roughness={0.8} polygonOffset polygonOffsetFactor={-2} />
      </instancedMesh>
      {geo.zebra && (
        <mesh geometry={geo.zebra} receiveShadow>
          <meshStandardMaterial color={lineColor} roughness={0.8} polygonOffset polygonOffsetFactor={-2} />
        </mesh>
      )}
      <instancedMesh ref={curbs} args={[geo.islandCurb, undefined, nI]} count={layout.islands.length} castShadow receiveShadow>
        <meshStandardMaterial color={pal.curb} roughness={0.9} />
      </instancedMesh>
      <instancedMesh ref={grass} args={[geo.islandGrass, undefined, nI]} count={layout.islands.length} receiveShadow>
        <meshStandardMaterial color={pal.groundTop} roughness={1} />
      </instancedMesh>
      <instancedMesh ref={cars} args={[geo.car, undefined, capacity]} castShadow receiveShadow frustumCulled={false}>
        <meshStandardMaterial vertexColors roughness={0.45} metalness={0.15} />
      </instancedMesh>
      <instancedMesh ref={beams} args={[geo.beam, undefined, PARKING_TRAFFIC.maxMoving + 2]} visible={night} renderOrder={4} frustumCulled={false}>
        <meshBasicMaterial map={tex.beam} transparent depthWrite={false} blending={THREE.AdditiveBlending} toneMapped={false} fog={false} />
      </instancedMesh>
      {geo.building && (
        <group>
          <mesh geometry={geo.building.walls} castShadow receiveShadow>
            <meshStandardMaterial vertexColors color="#ece6da" roughness={0.85} />
          </mesh>
          <mesh geometry={geo.building.glass}>
            <meshStandardMaterial color="#2c3a46" roughness={0.3} {...glowGlass} />
          </mesh>
          <mesh geometry={geo.building.roofA} castShadow receiveShadow>
            <meshStandardMaterial map={tex.metal} color="#9aa2a9" roughness={0.6} metalness={0.2} />
          </mesh>
          <mesh geometry={geo.building.roofB} castShadow receiveShadow>
            <meshStandardMaterial map={tex.metal} color="#c98a7c" roughness={0.65} metalness={0.1} />
          </mesh>
        </group>
      )}
      {geo.canopy && (
        <group>
          <mesh geometry={geo.canopy.posts} castShadow>
            <meshStandardMaterial color="#7d858c" roughness={0.6} metalness={0.3} />
          </mesh>
          <mesh geometry={geo.canopy.roof} castShadow receiveShadow>
            <meshStandardMaterial map={tex.metal} color="#8f989f" roughness={0.55} metalness={0.25} side={THREE.DoubleSide} />
          </mesh>
        </group>
      )}
      {geo.gate && (
        <group>
          <mesh geometry={geo.gate.solid} castShadow receiveShadow>
            <meshStandardMaterial vertexColors roughness={0.6} />
          </mesh>
          {geo.gate.arms.map((a, k) => (
            <group key={k} position={a.pos} rotation-y={a.yaw}>
              <mesh ref={armRefs[k]} geometry={geo.gate!.arm} castShadow>
                <meshStandardMaterial vertexColors roughness={0.6} />
              </mesh>
            </group>
          ))}
          {geo.gate.kioskGlass && (
            <mesh geometry={geo.gate.kioskGlass}>
              <meshStandardMaterial color="#2a3947" roughness={0.25} {...glowGlass} />
            </mesh>
          )}
        </group>
      )}
    </group>
  );
}

/** Joylashuvi bor parkinglar (config.ts → PARKING_LAYOUT). Qolganlari layers.tsx → Zones da oddiy maydon */
export function ParkingLots({ data, pal, night, selectedId, onSelect }: {
  data: ParkData; pal: Palette; night: boolean; selectedId: string | null; onSelect: (id: string) => void;
}) {
  return (
    <>
      {data.parking.map((a) => {
        const layout = data.parkingLayout?.[a.id];
        return layout
          ? <ParkingLot key={a.id} area={a} layout={layout} pal={pal} night={night} selected={a.id === selectedId} onSelect={onSelect} />
          : null;
      })}
    </>
  );
}

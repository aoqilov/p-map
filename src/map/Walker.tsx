// 3-shaxs yurish rejimi: parkda kichik odam (personaj) yuradi, kamera uning orqasidan kuzatadi.
// Boshqaruv: telefonda — joystik (ParkMap → Joystick), kompyuterda — WASD / strelkalar (Shift — yugurish).
// Ekranni bir barmoq/sichqoncha bilan sudrash — atrofga qarash (kamera personaj atrofida aylanadi), chimdish/g'ildirak — uzoq-yaqin.
// To'siqlar: park chegarasi, binolar, attraksion maydonchalari, suv (ko'priklar ustidan o'tsa bo'ladi).
import { useEffect, useLayoutEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
import { applyView, groundAt } from './mapGestures';
import type { ParkData, Poly } from './types';
import type { XY } from './projection';

/** Joystik holati: x — o'ngga, y — oldinga (−1..1) */
export interface WalkInput { x: number; y: number }
/** Personaj va kamera holati (rejimdan chiqqanda xarita kamerasi shu joydan davom etadi) */
export interface WalkPose { x: number; z: number; az: number; polar: number; dist: number }

const WALK_SPEED = 1.6;      // m/s (joystik o'rtacha)
const RUN_SPEED = 3.6;       // m/s (joystik oxirigacha yoki Shift)
const RADIUS = 0.3;          // personaj "tanasi" — to'siqqa shuncha yaqin kelmaydi
const EYE = 1.5;             // kamera qaraydigan balandlik (yelka)
const POLAR_MIN = THREE.MathUtils.degToRad(48), POLAR_MAX = THREE.MathUtils.degToRad(84);
const DIST_MIN = 4, DIST_MAX = 22;

// ---------- to'siqlar ----------
type Box = { x0: number; y0: number; x1: number; y1: number };
const bboxOf = (ring: XY[]): Box => {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const [x, y] of ring) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
  return { x0, y0, x1, y1 };
};
const inRing = (x: number, y: number, r: XY[]) => {
  let c = false;
  for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
    const [xi, yi] = r[i], [xj, yj] = r[j];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
  }
  return c;
};
const inPoly = (x: number, y: number, p: Poly) => inRing(x, y, p[0]) && !p.slice(1).some((h) => inRing(x, y, h));
const segDist = (x: number, y: number, a: XY, b: XY) => {
  const dx = b[0] - a[0], dy = b[1] - a[1], L = dx * dx + dy * dy || 1;
  const t = THREE.MathUtils.clamp(((x - a[0]) * dx + (y - a[1]) * dy) / L, 0, 1);
  return Math.hypot(x - a[0] - t * dx, y - a[1] - t * dy);
};

function useObstacles(data: ParkData) {
  return useMemo(() => {
    const solid = [
      ...data.buildings.map((b) => b.poly),
      ...data.attractions.filter((a) => a.footprint).map((a) => a.footprint!),
    ].map((p) => ({ p, b: bboxOf(p[0]) }));
    const water = data.water.map((w) => ({ p: w.poly, b: bboxOf(w.poly[0]) }));
    const hit = (list: { p: Poly; b: Box }[], x: number, y: number) =>
      list.some(({ p, b }) => x >= b.x0 && x <= b.x1 && y >= b.y0 && y <= b.y1 && inPoly(x, y, p));
    const onBridge = (x: number, y: number) =>
      data.bridges.some((br) => br.line.some((a, i) => i > 0 && segDist(x, y, br.line[i - 1], a) < br.width / 2));
    /** Park koordinatasidagi nuqta (x, y) yurib bo'lmaydigan joydami */
    const blocked = (x: number, y: number) =>
      !inPoly(x, y, data.ground) || hit(solid, x, y) || (hit(water, x, y) && !onBridge(x, y));
    return { blocked };
  }, [data]);
}

// ---------- personaj (oddiy low-poly odam) ----------
function makeCharacter(accent: string) {
  const g = new THREE.Group();
  const mat = (c: string) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.7 });
  const skin = mat('#f1c7a5'), pants = mat('#2c3a57'), shoe = mat('#1d1f24'), shirt = mat(accent), hair = mat('#3b2a1e');
  const add = (parent: THREE.Object3D, geo: THREE.BufferGeometry, m: THREE.Material, x: number, y: number, z: number) => {
    const mesh = new THREE.Mesh(geo, m);
    mesh.position.set(x, y, z);
    mesh.castShadow = true;
    parent.add(mesh);
    return mesh;
  };
  const legs: THREE.Group[] = [], arms: THREE.Group[] = [];
  for (const s of [-1, 1]) {
    const hip = new THREE.Group();
    hip.position.set(s * 0.1, 0.88, 0);
    add(hip, new THREE.BoxGeometry(0.15, 0.8, 0.17), pants, 0, -0.4, 0);
    add(hip, new THREE.BoxGeometry(0.16, 0.08, 0.27), shoe, 0, -0.84, 0.04);
    g.add(hip);
    legs.push(hip);
    const sh = new THREE.Group();
    sh.position.set(s * 0.27, 1.43, 0);
    add(sh, new THREE.BoxGeometry(0.11, 0.55, 0.12), shirt, 0, -0.26, 0);
    add(sh, new THREE.SphereGeometry(0.065, 8, 6), skin, 0, -0.58, 0);
    g.add(sh);
    arms.push(sh);
  }
  add(g, new THREE.BoxGeometry(0.44, 0.6, 0.25), shirt, 0, 1.17, 0);
  add(g, new THREE.CylinderGeometry(0.05, 0.06, 0.08, 8), skin, 0, 1.5, 0);
  const head = add(g, new THREE.SphereGeometry(0.14, 14, 10), skin, 0, 1.66, 0);
  head.scale.set(1, 1.08, 1);
  add(g, new THREE.SphereGeometry(0.15, 14, 8, 0, Math.PI * 2, 0, Math.PI / 2), hair, 0, 1.68, -0.01);
  // ko'rinishi uchun: oyoq ostida yarim shaffof halqa (xaritada uzoqdan ham topiladi)
  const ring = new THREE.Mesh(new THREE.RingGeometry(0.38, 0.5, 32),
    new THREE.MeshBasicMaterial({ color: accent, transparent: true, opacity: 0.55, depthWrite: false }));
  ring.rotation.x = -Math.PI / 2;
  ring.position.y = 0.03;
  g.add(ring);
  return { group: g, legs, arms };
}

export function Walker({ data, input, pose, accent }: {
  data: ParkData;
  input: React.MutableRefObject<WalkInput>;
  pose: React.MutableRefObject<WalkPose | null>;
  accent: string;
}) {
  const { camera, size, gl, invalidate } = useThree();
  const connected = useThree((s) => s.events.connected) as HTMLElement | undefined;
  const cam = camera as THREE.PerspectiveCamera;
  const { blocked } = useObstacles(data);
  const ch = useMemo(() => makeCharacter(accent), []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => () => {
    ch.group.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh) { m.geometry.dispose(); (m.material as THREE.Material).dispose(); }
    });
  }, [ch]);
  const st = useRef({ x: 0, y: 0, heading: 0, phase: 0, speed: 0, az: 0, polar: THREE.MathUtils.degToRad(66), dist: 11 });
  const keys = useRef(new Set<string>());

  // Paydo bo'lish: ekran markazidagi yer nuqtasida (bo'sh joy topilguncha spiral bo'ylab qidiradi); kamera yo'nalishi saqlanadi
  useLayoutEffect(() => {
    const g = groundAt(cam, size.width / 2, size.height / 2, size.width, size.height);
    let x = g ? g.x : 0, y = g ? -g.z : 0;
    if (blocked(x, y)) {
      outer: for (let r = 1.5; r < 120; r += 1.5) {
        for (let k = 0; k < 16; k++) {
          const a = (k / 16) * Math.PI * 2, nx = x + r * Math.cos(a), ny = y + r * Math.sin(a);
          if (!blocked(nx, ny)) { x = nx; y = ny; break outer; }
        }
      }
    }
    const f = new THREE.Vector3();
    cam.getWorldDirection(f);
    const az = Math.atan2(-f.x, -f.z);
    Object.assign(st.current, { x, y, heading: az + Math.PI, az });
    invalidate();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Klaviatura (qidiruv maydonida yozilayotgan bo'lsa — e'tiborsiz)
  useEffect(() => {
    const typing = (e: KeyboardEvent) => /^(INPUT|TEXTAREA|SELECT)$/.test((e.target as HTMLElement)?.tagName ?? '');
    const down = (e: KeyboardEvent) => { if (!typing(e)) keys.current.add(e.code); };
    const up = (e: KeyboardEvent) => keys.current.delete(e.code);
    const blur = () => keys.current.clear();
    window.addEventListener('keydown', down);
    window.addEventListener('keyup', up);
    window.addEventListener('blur', blur);
    return () => { window.removeEventListener('keydown', down); window.removeEventListener('keyup', up); window.removeEventListener('blur', blur); };
  }, []);

  // Atrofga qarash: sudrash — burilish va qiyalik, ikki barmoq — uzoq-yaqin, g'ildirak — uzoq-yaqin
  useEffect(() => {
    const host = connected ?? gl.domElement.parentElement ?? gl.domElement;
    const pts = new Map<number, { x: number; y: number }>();
    let pinch = 0;
    const down = (e: PointerEvent) => {
      pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (pts.size === 2) { const [a, b] = [...pts.values()]; pinch = Math.hypot(a.x - b.x, a.y - b.y); }
    };
    const move = (e: PointerEvent) => {
      const prev = pts.get(e.pointerId);
      if (!prev) return;
      const cur = { x: e.clientX, y: e.clientY };
      pts.set(e.pointerId, cur);
      const s = st.current;
      if (pts.size === 1) {
        s.az -= (cur.x - prev.x) * 0.007;
        s.polar = THREE.MathUtils.clamp(s.polar - (cur.y - prev.y) * 0.005, POLAR_MIN, POLAR_MAX);
      } else if (pts.size === 2) {
        const [a, b] = [...pts.values()];
        const d = Math.hypot(a.x - b.x, a.y - b.y);
        if (pinch > 0) s.dist = THREE.MathUtils.clamp(s.dist * (pinch / d), DIST_MIN, DIST_MAX);
        pinch = d;
      }
      invalidate();
    };
    const up = (e: PointerEvent) => { pts.delete(e.pointerId); pinch = 0; };
    const wheel = (e: WheelEvent) => {
      e.preventDefault();
      st.current.dist = THREE.MathUtils.clamp(st.current.dist * Math.exp(e.deltaY * 0.0015), DIST_MIN, DIST_MAX);
      invalidate();
    };
    host.addEventListener('pointerdown', down);
    host.addEventListener('pointermove', move);
    host.addEventListener('pointerup', up);
    host.addEventListener('pointercancel', up);
    host.addEventListener('wheel', wheel, { passive: false });
    return () => {
      host.removeEventListener('pointerdown', down);
      host.removeEventListener('pointermove', move);
      host.removeEventListener('pointerup', up);
      host.removeEventListener('pointercancel', up);
      host.removeEventListener('wheel', wheel);
    };
  }, [connected, gl, invalidate]);

  const view = useMemo(() => ({ tx: 0, tz: 0, dist: 7, polar: 1.2, az: 0 }), []);
  useFrame((_, frameDt) => {
    const dt = Math.min(frameDt, 0.1);
    const s = st.current, k = keys.current;
    // kiritish: joystik + klaviatura
    let ix = input.current.x + ((k.has('KeyD') || k.has('ArrowRight')) ? 1 : 0) - ((k.has('KeyA') || k.has('ArrowLeft')) ? 1 : 0);
    let iy = input.current.y + ((k.has('KeyW') || k.has('ArrowUp')) ? 1 : 0) - ((k.has('KeyS') || k.has('ArrowDown')) ? 1 : 0);
    const mag = Math.min(1, Math.hypot(ix, iy));
    if (mag > 1e-3) { const n = Math.hypot(ix, iy); ix = (ix / n) * mag; iy = (iy / n) * mag; }
    const run = k.has('ShiftLeft') || k.has('ShiftRight') || mag > 0.92;
    const target = mag < 0.05 ? 0 : (run ? RUN_SPEED : WALK_SPEED * Math.max(0.5, mag / 0.92));
    s.speed += (target - s.speed) * Math.min(1, dt * 8);

    if (mag >= 0.05) {
      // kameraga nisbatan: oldinga — kameradan uzoqlashish
      const fx = -Math.sin(s.az), fz = -Math.cos(s.az);       // dunyo XZ
      const rx = Math.cos(s.az), rz = -Math.sin(s.az);
      const wx = rx * ix + fx * iy, wz = rz * ix + fz * iy;
      const len = Math.hypot(wx, wz) || 1;
      const dx = wx / len, dz = wz / len;                       // birlik yo'nalish (dunyo)
      const want = Math.atan2(dx, dz);
      const dh = Math.atan2(Math.sin(want - s.heading), Math.cos(want - s.heading));
      s.heading += dh * Math.min(1, dt * 10);
      // park koordinatasi: x — sharq (dunyo x), y — shimol (−dunyo z)
      const step = s.speed * dt, px = dx * step, py = -dz * step;
      const free = (x: number, y: number) => !blocked(x, y) && !blocked(x + Math.sign(px) * RADIUS * Math.abs(dx), y + Math.sign(py) * RADIUS * Math.abs(dz));
      if (free(s.x + px, s.y + py)) { s.x += px; s.y += py; }
      else if (free(s.x + px, s.y)) s.x += px;               // devor bo'ylab sirpanish
      else if (free(s.x, s.y + py)) s.y += py;
      else s.speed = 0;
      // oldinga yurganda kamera asta personaj orqasiga o'tadi
      if (iy > 0.3) {
        const behind = s.heading + Math.PI;
        const da = Math.atan2(Math.sin(behind - s.az), Math.cos(behind - s.az));
        s.az += da * Math.min(1, dt * 0.9 * iy);
      }
    }
    // yurish animatsiyasi
    const moving = s.speed > 0.05;
    s.phase += dt * (moving ? 2.2 + s.speed * 2.2 : 0);
    const amp = moving ? Math.min(0.75, 0.25 + s.speed * 0.15) : 0;
    const sw = Math.sin(s.phase) * amp;
    ch.legs[0].rotation.x = sw;
    ch.legs[1].rotation.x = -sw;
    ch.arms[0].rotation.x = -sw * 0.8;
    ch.arms[1].rotation.x = sw * 0.8;
    ch.group.position.set(s.x, 0.04 + (moving ? Math.abs(Math.cos(s.phase)) * 0.04 : 0), -s.y);
    ch.group.rotation.y = s.heading;

    // kamera: personaj orqasida, yelka balandligiga qaraydi
    Object.assign(view, { tx: s.x, tz: -s.y, dist: s.dist, polar: s.polar, az: s.az });
    applyView(cam, view);
    cam.position.y += EYE;
    cam.updateMatrixWorld();
    pose.current = { x: s.x, z: -s.y, az: s.az, polar: s.polar, dist: s.dist };
    invalidate(); // yurish rejimida kadrlar uzluksiz
  });

  return <primitive object={ch.group} />;
}

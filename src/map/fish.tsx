// Hovuzdagi baliqlar (koi). Oddiy holatda to'da-to'da bo'lib erkin suzadi; har FISH.show.cycleSeconds da bir marta
// yig'ilib, figura (yurak va h.k.) konturi bo'ylab suzadi, keyin tarqaladi.
//
// Hammasi bitta InstancedMesh (1 draw call, ~3k uchburchak). Harakat CPU'da: 100 baliq uchun kadriga ~0.1–0.2 ms.
// Qirg'oqdan qochish suv shaderi ishlatadigan masofa to'ridan (waterField.ts) olinadi.
import { useEffect, useLayoutEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
import { pxPerMeter } from './geometry';
import { FISH, WATER } from './config';
import { contourWalker, figureContours, type FishFigure } from './figures';
import { inPoly } from './geo';
import { canvasTexture, prefersReducedMotion, useAmbientFrames } from './modelKit';
import { project, type XY } from './projection';
import type { Palette } from './theme';
import type { Area, ParkData } from './types';
import { waterLevelOf, waterStyleOf } from './water';
import { distanceGrid, type DistanceGrid } from './waterField';

// ---------------------------------------------------------------- tashqaridan boshqarish

let trigger: ((name?: string) => void) | null = null;

/** Figurani hozir ko'rsatish (masalan, adminkadagi tugmadan). Nom berilmasa — navbatdagisi */
export function fishShow(name?: string) {
  trigger?.(name);
}

// ---------------------------------------------------------------- model

/** Koi: ustidan qaralganda cho'ziq tana, ayri dum, ikki yon suzgich. Uzunligi 1 (+x — bosh), ~30 uchburchak */
function fishGeometry() {
  const pos: number[] = [], col: number[] = [];
  const tri = (a: number[], b: number[], c: number[], ca: number, cb: number, cc: number) => {
    pos.push(...a, ...b, ...c);
    col.push(ca, ca, ca, cb, cb, cb, cc, cc, cc);
  };
  // [x, yarim eni, bel balandligi] — koi to'ladi, boshi to'mtoq
  const S = [[0.5, 0, 0.02], [0.44, 0.08, 0.05], [0.3, 0.13, 0.075], [0.1, 0.145, 0.08], [-0.1, 0.115, 0.065], [-0.27, 0.06, 0.045], [-0.34, 0.03, 0.03]];
  for (let i = 0; i < S.length - 1; i++) {
    const [x0, w0, h0] = S[i], [x1, w1, h1] = S[i + 1];
    for (const s of [-1, 1]) {
      const r0 = [x0, h0, 0], r1 = [x1, h1, 0], e0 = [x0, 0, s * w0], e1 = [x1, 0, s * w1];
      tri(r0, e0, e1, 1.05, 0.85, 0.85);
      tri(r0, e1, r1, 1.05, 0.85, 1.05);
    }
  }
  const FIN = 1.3; // suzgichlar och, yarim shaffofdek
  const base = [-0.32, 0.02, 0], notch = [-0.44, 0.012, 0];
  tri(base, [-0.52, 0.012, -0.14], notch, 1.1, FIN, FIN);
  tri(base, notch, [-0.52, 0.012, 0.14], 1.1, FIN, FIN);
  for (const s of [-1, 1]) tri([0.25, 0.01, s * 0.09], [0.13, 0.01, s * 0.09], [0.12, 0.005, s * 0.21], FIN, FIN, FIN);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  g.computeVertexNormals();
  return g;
}

/**
 * Suvdagi iz: baliq ortida yumshoq och chiziq va ikki tomonga ochiladigan ingichka V-to'lqin.
 * Mayda baliqni uzoqdan ham ko'rinadigan qiladi (figura aniq o'qiladi); uzunligi tezlikka bog'liq.
 * Bitta to'rtburchak + canvas tekstura, qo'shiluvchi aralashma.
 */
const WAKE = { back: -1.7, front: 0.45, half: 0.75 };
function wakeGeometry() {
  const g = new THREE.PlaneGeometry(WAKE.front - WAKE.back, WAKE.half * 2).rotateX(-Math.PI / 2);
  g.translate((WAKE.front + WAKE.back) / 2, 0, 0);
  return g;
}
function wakeTexture() {
  const W = 256, H = 128;
  const tex = canvasTexture(W, H, (g) => {
    const img = g.createImageData(W, H);
    const smooth = (a: number, b: number, x: number) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
    // V-to'lqin uchi baliq boshi yonida (u≈0.9), orqaga qarab ochiladi
    const apex = 0.88;
    for (let j = 0; j < H; j++) for (let i = 0; i < W; i++) {
      const u = i / (W - 1), v = j / (H - 1) - 0.5; // u: 0 — orqa, 1 — old
      const fade = smooth(0, 0.55, u) * (1 - smooth(0.9, 1, u));
      const sig = 0.035 + (1 - u) * 0.1;
      const streak = Math.exp(-(v * v) / (2 * sig * sig)) * fade * 0.55;
      const spread = Math.max(apex - u, 0) * 0.5; // V qanotlari markazdan uzoqligi
      const dv = Math.abs(Math.abs(v) - spread);
      const wing = u < apex ? Math.exp(-(dv * dv) / (2 * 0.012 * 0.012)) * smooth(0, 0.5, u) * 0.45 : 0;
      const a = Math.min(1, streak + wing);
      const o = (j * W + i) * 4;
      img.data[o] = img.data[o + 1] = img.data[o + 2] = Math.round(a * 255);
      img.data[o + 3] = 255;
    }
    g.putImageData(img, 0, 0);
  });
  tex.colorSpace = THREE.NoColorSpace;
  return tex;
}

/** Dum likillashi: har baliqning o'z fazasi (aPhase), dumga tomon kuchayadi, bosh deyarli qimirlamaydi */
function fishMaterial() {
  const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.45, side: THREE.DoubleSide });
  mat.onBeforeCompile = (shader) => {
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nattribute float aPhase;')
      .replace('#include <begin_vertex>', `#include <begin_vertex>
  float fAlong = clamp(position.x + 0.5, 0.0, 1.0);
  float fTail = pow(1.0 - fAlong, 1.5);
  transformed.z += sin(aPhase - (1.0 - fAlong) * 4.0) * 0.11 * fTail;`);
  };
  return mat;
}

// ---------------------------------------------------------------- simulyatsiya

type Mode = 'free' | 'gather' | 'hold' | 'disperse';

interface Env {
  grid: DistanceGrid;
  /** Suv ichidagi binolar (rotonda) — doira bo'lib aylanib o'tiladi */
  obstacles: { x: number; y: number; r: number }[];
  /** Baliq qirg'oqqa shundan yaqin bormaydi (qirg'oq toshi + zaxira), m */
  margin: number;
  /** Erkin suzish uchun manzil nuqtalari (ochiq suv) */
  spots: XY[];
  /** Eng keng joy — figura markazi berilmasa */
  widest: XY;
}

interface Slot { walker: ReturnType<typeof contourWalker>; u0: number }

interface Sim {
  n: number;
  x: Float32Array; y: Float32Array; hd: Float32Array; sp: Float32Array;
  cruise: Float32Array; ph: Float32Array; size: Float32Array;
  school: Int32Array; offA: Float32Array; offB: Float32Array;
  leaders: number[]; targets: XY[];
  slot: Int32Array; slots: Slot[];
  mode: Mode; T: number; modeStart: number; nextShowAt: number; figIndex: number; pending: string | null;
}

function rng(seed: number) {
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = rng(20261023);
const lerp = ([a, b]: [number, number], t: number) => a + (b - a) * t;
const angDiff = (a: number, b: number) => Math.atan2(Math.sin(b - a), Math.cos(b - a));

function buildEnv(area: Area, data: ParkData): Env {
  const grid = distanceGrid(area.poly);
  const coping = WATER.styles[waterStyleOf(area.name)].coping;
  const margin = coping + 0.8;
  const obstacles = data.buildings
    .filter((b) => b.poly[0].some((p) => inPoly(p, area.poly)))
    .map((b) => {
      const ring = b.poly[0];
      const x = ring.reduce((s, p) => s + p[0], 0) / ring.length, y = ring.reduce((s, p) => s + p[1], 0) / ring.length;
      return { x, y, r: Math.max(...ring.map((p) => Math.hypot(p[0] - x, p[1] - y))) };
    });
  const spots: XY[] = [];
  let widest: XY = [0, 0], best = -Infinity;
  for (let j = 0; j < grid.H; j++) for (let i = 0; i < grid.W; i++) {
    const d = grid.dist[j * grid.W + i];
    const p: XY = [grid.x0 + (i + 0.5) * grid.cell, grid.y0 + (j + 0.5) * grid.cell];
    if (d < margin + 2.5 || obstacles.some((o) => Math.hypot(p[0] - o.x, p[1] - o.y) < o.r + 3)) continue;
    spots.push(p);
    if (d > best) { best = d; widest = p; }
  }
  return { grid, obstacles, margin, spots, widest };
}

function initSim(env: Env): Sim {
  const n = FISH.count;
  const s: Sim = {
    n,
    x: new Float32Array(n), y: new Float32Array(n), hd: new Float32Array(n), sp: new Float32Array(n),
    cruise: new Float32Array(n), ph: new Float32Array(n), size: new Float32Array(n),
    school: new Int32Array(n), offA: new Float32Array(n), offB: new Float32Array(n),
    leaders: [], targets: [], slot: new Int32Array(n).fill(-1), slots: [],
    mode: 'free', T: 0, modeStart: 0, nextShowAt: FISH.show.firstAfterSeconds, figIndex: 0, pending: null,
  };
  const pick = () => env.spots[Math.floor(rand() * env.spots.length)];
  for (let i = 0; i < n;) {
    const size = Math.round(lerp(FISH.schoolSize, rand()));
    const k = s.leaders.length;
    const [cx, cy] = pick();
    const speed = lerp(FISH.speed, rand());
    s.leaders.push(i);
    s.targets.push(pick());
    for (let m = 0; m < size && i < n; m++, i++) {
      s.school[i] = k;
      s.x[i] = cx + (rand() - 0.5) * 3; s.y[i] = cy + (rand() - 0.5) * 3;
      s.hd[i] = rand() * Math.PI * 2;
      s.cruise[i] = speed * (0.9 + rand() * 0.2);
      s.sp[i] = s.cruise[i];
      s.ph[i] = rand() * 10;
      s.size[i] = 0.8 + rand() * 0.4;
      s.offA[i] = -1 - rand() * 2.2; // to'da boshlig'idan orqada
      s.offB[i] = (rand() - 0.5) * 3; // yonida
    }
  }
  return s;
}

/** Figura boshlanishi: shakl, joy, yo'nalish, suvga sig'dirish, baliqlarni joylarga taqsimlash */
function startShow(s: Sim, env: Env, camera: THREE.Camera) {
  const figs = FISH.figures;
  if (!figs.length) return false;
  let fig: FishFigure | undefined = s.pending ? figs.find((f) => f.name === s.pending) : undefined;
  if (!fig) {
    s.figIndex = FISH.show.order === 'tasodifiy' ? Math.floor(rand() * figs.length) : s.figIndex % figs.length;
    fig = figs[s.figIndex];
    s.figIndex++;
  }
  s.pending = null;

  let center: XY = fig.at ? project(fig.at) : env.widest;
  if (env.grid.sample(center[0], center[1]) < env.margin + 3) center = env.widest;

  // Ekranga qarab: "o'ng" — kamera o'ng tomoni, "yuqori" — kameradan uzoqlashuvchi yo'nalish.
  // Ekranda vertikal masofa cos(qiyalik) marta qisqaradi — shunga cho'zamiz, shakl ekranda to'g'ri ko'rinsin
  let R: XY = [1, 0], U: XY = [0, 1], stretch = 1;
  const faceScreen = fig.faceScreen ?? (fig.shape === 'circle' && !fig.svg ? false : FISH.show.faceScreen);
  if (faceScreen) {
    const r = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion);
    const v = new THREE.Vector3(0, 0, 1).applyQuaternion(camera.quaternion);
    const rl = Math.hypot(r.x, r.z) || 1, vl = Math.hypot(v.x, v.z) || 1;
    R = [r.x / rl, -r.z / rl];
    U = [-v.x / vl, v.z / vl];
    stretch = 1 / Math.max(v.y, 0.4);
  }
  const contours = figureContours(fig);
  const place = (scale: number) => contours.map((c) => c.map(([fx, fy]): XY => [
    center[0] + (fx * R[0] + fy * U[0] * stretch) * scale,
    center[1] + (fx * R[1] + fy * U[1] * stretch) * scale,
  ]));
  const fits = (world: XY[][]) => world.every((c) => c.every(([x, y]) =>
    env.grid.sample(x, y) >= env.margin + 0.5 && env.obstacles.every((o) => Math.hypot(x - o.x, y - o.y) >= o.r + 1.2)));
  let scale = fig.size, world = place(scale);
  for (let k = 0; k < 14 && !fits(world); k++) world = place((scale *= 0.92));

  // Baliqlar konturlarga uzunligiga qarab bo'linadi
  const walkers = world.map((c) => contourWalker(c));
  const total = walkers.reduce((a, w) => a + w.length, 0);
  const counts = walkers.map((w) => Math.max(1, Math.round((w.length / total) * s.n)));
  while (counts.reduce((a, b) => a + b, 0) > s.n) counts[counts.indexOf(Math.max(...counts))]--;
  while (counts.reduce((a, b) => a + b, 0) < s.n) counts[counts.indexOf(Math.min(...counts))]++;
  s.slots = [];
  walkers.forEach((w, c) => { for (let k = 0; k < counts[c]; k++) s.slots.push({ walker: w, u0: k / counts[c] }); });

  // Eng yaqin juftlar birinchi: baliq o'ziga yaqin joyni oladi, yo'llar kam kesishadi
  const pairs: [number, number, number][] = [];
  s.slots.forEach((sl, j) => {
    const p = sl.walker.at(sl.u0);
    for (let i = 0; i < s.n; i++) pairs.push([Math.hypot(s.x[i] - p.x, s.y[i] - p.y), i, j]);
  });
  pairs.sort((a, b) => a[0] - b[0]);
  const fishFree = new Uint8Array(s.n).fill(1), slotFree = new Uint8Array(s.slots.length).fill(1);
  s.slot.fill(-1);
  for (const [, i, j] of pairs) if (fishFree[i] && slotFree[j]) { s.slot[i] = j; fishFree[i] = 0; slotFree[j] = 0; }
  return true;
}

/** Tarqalish: har to'daga yaqin atrofdan yangi manzil */
function startDisperse(s: Sim, env: Env) {
  s.leaders.forEach((l, k) => {
    const near = env.spots.filter((p) => Math.hypot(p[0] - s.x[l], p[1] - s.y[l]) < 30);
    const pool = near.length ? near : env.spots;
    s.targets[k] = pool[Math.floor(rand() * pool.length)];
  });
}

function step(s: Sim, env: Env, h: number, camera: THREE.Camera) {
  const cfg = FISH.show;
  s.T += h;
  // Bosqichlar
  if (s.mode === 'free' && s.T >= s.nextShowAt) {
    if (startShow(s, env, camera)) { s.mode = 'gather'; s.modeStart = s.T; }
    s.nextShowAt = s.T + cfg.cycleSeconds;
  } else if (s.mode === 'gather' && s.T - s.modeStart >= cfg.gatherSeconds) {
    s.mode = 'hold'; s.modeStart = s.T;
  } else if (s.mode === 'hold' && s.T - s.modeStart >= cfg.holdSeconds) {
    startDisperse(s, env); s.mode = 'disperse'; s.modeStart = s.T;
  } else if (s.mode === 'disperse' && s.T - s.modeStart >= cfg.disperseSeconds) {
    s.mode = 'free';
  }
  const mode = s.mode;
  const inShow = mode === 'gather' || mode === 'hold';
  const holdT = mode === 'hold' ? s.T - s.modeStart : 0;
  const left = mode === 'gather' ? Math.max(cfg.gatherSeconds - (s.T - s.modeStart), 0.4) : 0;
  const { grid, obstacles, margin } = env;

  for (let i = 0; i < s.n; i++) {
    const x = s.x[i], y = s.y[i];
    let vx = 0, vy = 0, maxSp = s.cruise[i], turn = 2.4, accel = 2.5;
    let tangent: { tx: number; ty: number } | null = null, slotPos: XY | null = null;

    if (inShow && s.slot[i] >= 0) {
      const sl = s.slots[s.slot[i]];
      const p = sl.walker.at(sl.u0 + (holdT * cfg.contourSpeed) / sl.walker.length);
      const dx = p.x - x, dy = p.y - y, d = Math.hypot(dx, dy);
      slotPos = [p.x, p.y];
      if (mode === 'gather' && d > 1.2) {
        // Vaqtida yetib borish uchun kerakli tezlik (uzoqdagilar shoshiladi)
        const need = Math.min(Math.max((d / left) * 1.15, s.cruise[i]), 9);
        vx = (dx / d) * need; vy = (dy / d) * need; maxSp = need; turn = 4; accel = 8;
      } else {
        const c = mode === 'hold' ? cfg.contourSpeed : 0.3;
        vx = p.tx * c + dx * 2; vy = p.ty * c + dy * 2;
        maxSp = cfg.contourSpeed + 3; turn = 7; accel = 10;
        tangent = p;
      }
    } else {
      // Erkin suzish: to'da boshlig'i manzilga, qolganlar boshliq orqasidan
      const k = s.school[i], l = s.leaders[k];
      let tx: number, ty: number;
      if (l === i) {
        [tx, ty] = s.targets[k];
        if (Math.hypot(tx - x, ty - y) < 4) {
          const near = env.spots.filter((p) => Math.hypot(p[0] - x, p[1] - y) < 45);
          const pool = near.length > 20 ? near : env.spots;
          s.targets[k] = pool[Math.floor(rand() * pool.length)];
        }
      } else {
        const c = Math.cos(s.hd[l]), sn = Math.sin(s.hd[l]);
        tx = s.x[l] + c * s.offA[i] - sn * s.offB[i];
        ty = s.y[l] + sn * s.offA[i] + c * s.offB[i];
      }
      const dx = tx - x, dy = ty - y, d = Math.hypot(dx, dy) || 1;
      const boost = mode === 'disperse' ? 1.6 : l === i ? 1 : Math.min(1 + Math.max(d - 1, 0) * 0.35, 1.9);
      maxSp = s.cruise[i] * boost;
      vx = (dx / d) * maxSp; vy = (dy / d) * maxSp;
      // Bir-biriga urilmaslik
      for (let j = 0; j < s.n; j++) {
        if (j === i) continue;
        const ex = x - s.x[j], ey = y - s.y[j], e2 = ex * ex + ey * ey;
        if (e2 < 0.81 && e2 > 1e-6) { const e = Math.sqrt(e2); vx += (ex / e) * (0.9 - e) * 3; vy += (ey / e) * (0.9 - e) * 3; }
      }
    }

    // Qirg'oq va rotondadan qochish (oldinga qarab)
    if (!tangent) {
      const sp = Math.max(s.sp[i], 0.5);
      const ax = x + Math.cos(s.hd[i]) * (1.2 + sp), ay = y + Math.sin(s.hd[i]) * (1.2 + sp);
      const da = grid.sample(ax, ay);
      if (da < margin + 1.5) {
        const [gx, gy] = grid.inward(ax, ay);
        const w = Math.min((margin + 1.5 - da) / 1.5, 2) * Math.max(maxSp, 1) * 1.5;
        vx += gx * w; vy += gy * w;
      }
      for (const o of obstacles) {
        const ox = ax - o.x, oy = ay - o.y, od = Math.hypot(ox, oy);
        if (od < o.r + 2.5) { const w = ((o.r + 2.5 - od) / 2.5) * Math.max(maxSp, 1) * 2; vx += (ox / od) * w; vy += (oy / od) * w; }
      }
    }

    // Burilish va tezlik
    const want = Math.hypot(vx, vy);
    if (want > 1e-4) {
      const dh = angDiff(s.hd[i], Math.atan2(vy, vx));
      s.hd[i] += Math.max(-turn * h, Math.min(turn * h, dh));
    }
    const target = Math.min(want, maxSp);
    s.sp[i] += Math.max(-accel * h, Math.min(accel * h, target - s.sp[i]));
    let nx = x + Math.cos(s.hd[i]) * s.sp[i] * h, ny = y + Math.sin(s.hd[i]) * s.sp[i] * h;

    // Figurada: joyiga yetgan baliq chiziqqa "yopishadi" — kontur toza ko'rinadi
    if (tangent && slotPos) {
      const k = Math.min(1, 6 * h);
      nx += (slotPos[0] - nx) * k; ny += (slotPos[1] - ny) * k;
      if (mode === 'hold') s.hd[i] += angDiff(s.hd[i], Math.atan2(tangent.ty, tangent.tx)) * Math.min(1, 5 * h);
    }

    // Qattiq chegara: qirg'oq toshiga chiqib ketmaydi
    const hard = margin - 0.5;
    const dn = grid.sample(nx, ny);
    if (dn < hard) { const [gx, gy] = grid.inward(nx, ny); nx += gx * (hard - dn); ny += gy * (hard - dn); }
    for (const o of obstacles) {
      const ox = nx - o.x, oy = ny - o.y, od = Math.hypot(ox, oy);
      if (od < o.r + 0.4) { nx = o.x + (ox / od) * (o.r + 0.4); ny = o.y + (oy / od) * (o.r + 0.4); }
    }
    s.x[i] = nx; s.y[i] = ny;
    s.ph[i] += Math.PI * 2 * (1.4 + s.sp[i] * 2.2) * h; // tezroq suzsa — dum tezroq
  }
}

// ---------------------------------------------------------------- komponent

export function Fish({ data, pal }: { data: ParkData; pal: Palette }) {
  const area = useMemo(() => data.water.find((w) => w.name === FISH.water), [data]);
  if (!FISH.enabled || !area) return null;
  return <FishSchool area={area} data={data} pal={pal} />;
}

function FishSchool({ area, data, pal }: { area: Area; data: ParkData; pal: Palette }) {
  const env = useMemo(() => buildEnv(area, data), [area, data]);
  const sim = useMemo(() => initSim(env), [env]);
  const geo = useMemo(() => {
    const g = fishGeometry();
    g.setAttribute('aPhase', new THREE.InstancedBufferAttribute(new Float32Array(FISH.count), 1));
    return g;
  }, []);
  const mat = useMemo(() => fishMaterial(), []);
  const wake = useMemo(() => {
    const map = wakeTexture();
    return {
      geo: wakeGeometry(), map,
      mat: new THREE.MeshBasicMaterial({ map, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false, fog: false }),
    };
  }, []);
  useEffect(() => () => { geo.dispose(); mat.dispose(); wake.geo.dispose(); wake.mat.dispose(); wake.map.dispose(); }, [geo, mat, wake]);
  const mesh = useRef<THREE.InstancedMesh>(null!);
  const wakes = useRef<THREE.InstancedMesh>(null!);
  const paused = useRef(false); // faqat dev sinovlari uchun
  const camera = useThree((st) => st.camera);
  const viewH = useThree((st) => st.size.height);
  const animate = !prefersReducedMotion();
  useAmbientFrames(animate);
  const level = waterLevelOf(area.name);

  useEffect(() => {
    trigger = (name) => { sim.pending = name ?? null; if (sim.mode === 'free' || sim.mode === 'disperse') sim.nextShowAt = sim.T; };
    // Faqat dev: konsoldan tekshirish va vaqtni oldinga surish (window.__fish.advance(10))
    if (import.meta.env.DEV) {
      (window as unknown as { __fish: unknown }).__fish = {
        sim, env,
        advance: (sec: number) => { for (let t = 0; t < sec; t += 0.05) step(sim, env, 0.05, camera); write(); },
        pause: (on: boolean) => { paused.current = on; },
      };
    }
    return () => { trigger = null; };
  }, [sim]); // eslint-disable-line react-hooks/exhaustive-deps

  const tmp = useMemo(() => ({ m: new THREE.Matrix4(), q: new THREE.Quaternion(), p: new THREE.Vector3(), s: new THREE.Vector3(), up: new THREE.Vector3(0, 1, 0) }), []);
  const write = () => {
    const { m, q, p, s, up } = tmp;
    const phase = geo.getAttribute('aPhase') as THREE.InstancedBufferAttribute;
    for (let i = 0; i < sim.n; i++) {
      const L = FISH.length * sim.size[i];
      q.setFromAxisAngle(up, sim.hd[i]);
      m.compose(p.set(sim.x[i], level + 0.006, -sim.y[i]), q, s.set(L, L, L));
      mesh.current.setMatrixAt(i, m);
      // Iz: tezlik oshsa uzunroq (yig'ilishda shoshilgan baliq uzun iz qoldiradi)
      m.compose(p.setY(level + 0.004), q, s.set(L * Math.min(0.7 + sim.sp[i] * 0.45, 3), 1, L));
      wakes.current.setMatrixAt(i, m);
      phase.setX(i, sim.ph[i]);
    }
    mesh.current.instanceMatrix.needsUpdate = true;
    wakes.current.instanceMatrix.needsUpdate = true;
    phase.needsUpdate = true;
  };

  useLayoutEffect(() => {
    const c = new THREE.Color();
    for (let i = 0; i < sim.n; i++) mesh.current.setColorAt(i, c.set(FISH.colors[Math.floor(rand() * FISH.colors.length)]));
    if (mesh.current.instanceColor) mesh.current.instanceColor.needsUpdate = true;
    write();
  }, [sim]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    mat.color.set(pal.fishTint);
    wake.mat.color.set(pal.fishWake);
  }, [mat, wake, pal]);

  useFrame((_, dt) => {
    // Iz uzoqdan kuchli (figura ko'rinsin), yaqinlashganda xiralashadi — baliqning o'zi ko'rinadi
    const z = pxPerMeter(camera, viewH);
    wake.mat.opacity = THREE.MathUtils.clamp(1 - Math.log2(Math.max(z, 1) / 8) * 0.35, 0.3, 1);
    if (!animate || paused.current) return;
    // Sekin qurilmada ham harakat bir tekis: kichik qadamlarga bo'lamiz (oxirgi kadr 0.5 s dan oshsa — kesamiz)
    const total = Math.min(dt, 0.5);
    const n = Math.max(1, Math.ceil(total / 0.05));
    for (let k = 0; k < n; k++) step(sim, env, total / n, camera);
    write();
  });

  return (
    <>
      <instancedMesh ref={wakes} args={[wake.geo, wake.mat, FISH.count]} frustumCulled={false} renderOrder={2} />
      <instancedMesh ref={mesh} args={[geo, mat, FISH.count]} frustumCulled={false} />
    </>
  );
}

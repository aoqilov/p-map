// Blender'da yasalgan attraksion modellari (.glb). Model haqiqiy o'lchamda (metr), markazi (0,0,0), Y — tepaga.
// Harakatlanadigan qismlar Blender'dagi obyekt nomi bilan topiladi:
//   rotor   — markaz atrofida aylanadi (bolalari ham u bilan birga aylanadi)
//   lift<N> — o'z joyida yuqoriga-pastga ko'tariladi (masalan, Air Race samolyotlari ustun bo'ylab)
//   spin<N> — o'z markazi atrofida aylanadi (masalan, Magic Bikes parraklari; Blender'da origin — parrak markazida)
//   swing<N> — origin (o'q) atrofida oldinga-orqaga tebranadi, o'q — model X bo'ylab (masalan, Happy Swing)
//   tilt<N> — origin (sharnir) atrofida ko'tariladi/tushadi, lokal Z o'qi atrofida (masalan, Windstar qo'llari);
//             uning bolasi hang<N> teskari buriladi — savat doim tik turadi
// Nom aniq solishtiriladi ('lift0', 'cabin12'): ko'p materialli tugunni three.js guruh + 'cabin0_1', 'cabin0_2' bo'laklari
// qilib yuklaydi — bo'laklar qayta harakatlantirilmasin.
//   wheel   — charxpalak g'ildiragi: o'z gorizontal o'qi (lokal Z) atrofida aylanadi;
//             uning bolalari cabin<N> teskari buriladi — kabinalar doim tik osilib turadi
//   car<N>  — trassa bo'ylab yuradi (anim.follow, masalan Speady coaster poyezdi; trassa — model.py yozgan track.json)
// Tezlik va balandlik config.ts da (masalan, AIR_RACE). Tanlangan holat pin bilan ko'rsatiladi.
import { useLayoutEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import { prefersReducedMotion, useAmbientFrames } from './modelKit';
import type { ModelProps } from './attractions';

export interface GltfAnimation {
  /** Bir aylanish, soniya. 0 — aylanmaydi */
  secondsPerTurn?: number;
  /**
   * `lift*` qismlarining ko'tarilishi (meters: 0 — o'chiq). Sikl: pastda turadi → silliq ko'tariladi → tepada turadi →
   * silliq tushadi. `stagger` — har bir keyingi qism shuncha soniya kech ko'tariladi (0 — hammasi birga)
   */
  lift?: { meters: number; seconds: number; stagger?: number };
  /** `car*` qismlari trassa bo'ylab yuradi */
  follow?: FollowAnimation;
  /** `spin*` qismlari o'z o'qi (tik) atrofida aylanadi: daqiqasiga aylanishlar soni (0 — to'xtagan) */
  spin?: { rpm: number };
  /**
   * `swing*` qismlari tebranadi (arg'imchoq): eng katta burchak (gradus), bir tebranish (oldinga-orqaga) soniya,
   * seans sikli soniya — tinch turadi → asta kuchayadi → eng balandda tebranadi → sekinlashib to'xtaydi. degrees: 0 — o'chiq
   */
  swing?: {
    degrees: number; period: number; cycle: number; stagger?: number;
    /** Doimiy og'ish, gradus (aylanuvchi arg'imchoq o'rindiqlari tashqariga og'adi — markazdan qochma kuch) */
    lean?: number;
  };
  /**
   * `tilt*` qo'llari ko'tariladi: necha gradus, sikl soniya (pastda turish → ko'tarilish → tepada turish → tushish),
   * stagger — har bir keyingi qo'l necha soniya kech (0 — hammasi birga). degrees: 0 — o'chiq
   */
  tilt?: { degrees: number; seconds: number; stagger?: number };
  /** `wheel` g'ildiragi aylanadi (kabinalar tik qoladi): bir aylanish necha soniyada. 0 — to'xtagan */
  wheel?: { secondsPerTurn: number };
}

/** Yopiq chiziq bo'ylab masofa → nuqta (oldindan hisoblangan uzunliklar bilan) */
function trackSampler(points: number[][]) {
  const n = points.length;
  const cum = [0];
  for (let i = 0; i < n; i++) {
    const a = points[i], b = points[(i + 1) % n];
    cum.push(cum[i] + Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]));
  }
  const total = cum[n];
  const ys = points.map((p) => p[1]);
  const at = (s: number, out: THREE.Vector3) => {
    const d = ((s % total) + total) % total;
    let lo = 0, hi = n;
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (cum[m] <= d) lo = m; else hi = m; }
    const a = points[lo], b = points[(lo + 1) % n];
    const t = (d - cum[lo]) / (cum[lo + 1] - cum[lo] || 1);
    return out.set(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t);
  };
  return { at, total, yMin: Math.min(...ys), yMax: Math.max(...ys) };
}

/** Trassa (model.py → track.json): o'rta chiziq glTF koordinatalarida, vagonlar va bekat joyi */
export interface TrackData {
  closed: boolean;
  points: number[][];
  /** Vagon tuguni nomi va parovozdan orqaga masofasi, m */
  cars: { name: string; offset: number }[];
  /** Bekat: trassa boshidan masofa, m (poyezd shu yerda to'xtaydi) */
  station: number;
}

export interface FollowAnimation {
  track: TrackData;
  /** Tezlik, m/s: eng past joyda `max`, eng baland joyda `min` (tepaga sekin chiqadi, pastga tez tushadi) */
  speed: { min: number; max: number };
  /** Bekatda turish, soniya (0 — to'xtamaydi) */
  dwell?: number;
}

export interface GltfOptions {
  url: string;
  /** Animatsiya sozlamalari — har kadrda o'qiladi, shuning uchun config.ts dagi obyektni to'g'ridan-to'g'ri bering */
  anim?: GltfAnimation;
}

const smooth = (x: number) => x * x * (3 - 2 * x);
const X_AXIS = new THREE.Vector3(1, 0, 0);
const tmpQ = new THREE.Quaternion();
/** Ko'tarilish dasturi, u ∈ [0, 1) sikl ulushi → balandlik ulushi 0..1: 20% pastda, 30% ko'tarilish, 20% tepada, 30% tushish */
function liftProgram(u: number) {
  const v = u < 0 ? u + 1 : u;
  if (v < 0.2) return 0;
  if (v < 0.5) return smooth((v - 0.2) / 0.3);
  if (v < 0.7) return 1;
  return 1 - smooth((v - 0.7) / 0.3);
}

/** .glb modelidan attraksion komponenti yasaydi (ATTRACTION_MODELS ga qo'shish uchun) */
export function gltfModel({ url, anim = {} }: GltfOptions) {
  function Model(_: ModelProps) {
    const { scene } = useGLTF(url);
    // Har bir nusxa o'z ierarxiyasiga ega bo'lsin (geometriya va materiallar umumiy qoladi)
    const root = useMemo(() => {
      const r = scene.clone(true);
      r.traverse((o) => {
        const m = o as THREE.Mesh;
        if (!m.isMesh) return;
        // shaffof qismlar (masalan, avtodromning oq tomi) soya tashlamaydi va chuqurlikni yozmaydi
        const transparent = (Array.isArray(m.material) ? m.material : [m.material]).some((x) => x.transparent);
        if (transparent) (Array.isArray(m.material) ? m.material : [m.material]).forEach((x) => { if (x.transparent) x.depthWrite = false; });
        m.castShadow = !transparent;
        m.receiveShadow = true;
      });
      return r;
    }, [scene]);
    useModelAnimation(root, anim);
    return <primitive object={root} />;
  }
  Model.preload = () => useGLTF.preload(url);
  return Model;
}

/**
 * Model qismlarini nomi bo'yicha topib harakatlantiradi (yuqoridagi nom qoidalari). Bitta .glb ichidagi bir nechta
 * jihozni alohida-alohida harakatlantirish uchun ham ishlatiladi (masalan, bolalar maydonchasi — har bir jihoz nusxasiga).
 */
export function useModelAnimation(root: THREE.Object3D, anim: GltfAnimation) {
    const parts = useMemo(() => {
      const lifts: { node: THREE.Object3D; y0: number }[] = [];
      const spinners: THREE.Object3D[] = [];
      const swingers: { node: THREE.Object3D; q0: THREE.Quaternion }[] = [];
      const tilts: { node: THREE.Object3D; z0: number; hang: THREE.Object3D | null; h0: number }[] = [];
      root.traverse((o) => {
        if (/^lift\d+$/.test(o.name)) lifts.push({ node: o, y0: o.position.y });
        if (/^spin\d+$/.test(o.name)) spinners.push(o);
        if (/^swing\d+$/.test(o.name)) swingers.push({ node: o, q0: o.quaternion.clone() });
        if (/^tilt\d+$/.test(o.name)) {
          const hang = o.children.find((c) => /^hang\d+$/.test(c.name)) ?? null;
          tilts.push({ node: o, z0: o.rotation.z, hang, h0: hang?.rotation.z ?? 0 });
        }
      });
      const cars = (anim.follow?.track.cars ?? [])
        .map((c) => ({ node: root.getObjectByName(c.name), offset: c.offset }))
        .filter((c): c is { node: THREE.Object3D; offset: number } => !!c.node);
      return { rotor: root.getObjectByName('rotor') ?? null, lifts, cars, spinners, swingers, tilts,
        wheel: root.getObjectByName('wheel') ?? null,
        cabins: (() => { const c: THREE.Object3D[] = []; root.traverse((o) => { if (/^cabin\d+$/.test(o.name)) c.push(o); }); return c; })() };
    }, [root]);
    const track = useMemo(() => (anim.follow ? trackSampler(anim.follow.track.points) : null), []);
    // Poyezd holati: trassa bo'ylab masofa va bekatda qolgan turish vaqti
    const train = useRef({ s: anim.follow?.track.station ?? 0, wait: anim.follow?.dwell ?? 0 });
    const tmp = useMemo(() => ({ p: new THREE.Vector3(), a: new THREE.Vector3(), b: new THREE.Vector3() }), []);
    const placeCars = (s: number) => {
      if (!track) return;
      for (const { node, offset } of parts.cars) {
        const d = s - offset;
        track.at(d, tmp.p);
        track.at(d + 0.4, tmp.a).sub(track.at(d - 0.4, tmp.b)).normalize();
        node.position.copy(tmp.p);
        // yo'nalish: gorizontal burilish (Y atrofida) va qiyalik (lokal Z atrofida); vagon lokal +X ga qaragan
        node.rotation.set(0, Math.atan2(-tmp.a.z, tmp.a.x), Math.asin(THREE.MathUtils.clamp(tmp.a.y, -1, 1)), 'YZX');
      }
    };
    // Animatsiya o'chiq bo'lsa ham vagonlar trassada (bekatda) tursin
    useLayoutEffect(() => placeCars(train.current.s), [parts]); // eslint-disable-line react-hooks/exhaustive-deps

    const spins = (anim.secondsPerTurn ?? 0) > 0 && !!parts.rotor;
    const lifts = (anim.lift?.meters ?? 0) > 0 && parts.lifts.length > 0;
    const follows = !!track && parts.cars.length > 0 && (anim.follow?.speed.max ?? 0) > 0;
    const props = (anim.spin?.rpm ?? 0) > 0 && parts.spinners.length > 0;
    const swings = ((anim.swing?.degrees ?? 0) > 0 || (anim.swing?.lean ?? 0) > 0) && parts.swingers.length > 0;
    const tilting = (anim.tilt?.degrees ?? 0) > 0 && parts.tilts.length > 0;
    const wheeling = (anim.wheel?.secondsPerTurn ?? 0) > 0 && !!parts.wheel;
    const animate = (spins || lifts || follows || props || swings || tilting || wheeling) && !prefersReducedMotion();
    useAmbientFrames(animate);

    const t = useRef(0);
    useFrame((_, frameDt) => {
      let dt = frameDt;
      if (!animate) return;
      dt = Math.min(dt, 0.1); // fon tabidan qaytganda sakrab ketmasin
      t.current += dt;
      if (spins && parts.rotor) parts.rotor.rotation.y = ((t.current * Math.PI * 2) / anim.secondsPerTurn!) % (Math.PI * 2);
      if (lifts && anim.lift) {
        const { meters, seconds, stagger = 0 } = anim.lift;
        parts.lifts.forEach(({ node, y0 }, i) => {
          node.position.y = y0 + meters * liftProgram(((t.current - i * stagger) / seconds) % 1);
        });
      }
      if (swings && anim.swing) {
        const { degrees, period, cycle, stagger = 0 } = anim.swing;
        // tebranish kuchi seans bo'yicha o'zgaradi (liftProgram: tinch → kuchayish → eng katta → so'nish); cycle: 0 — doim
        const amp = THREE.MathUtils.degToRad(degrees) * (cycle > 0 ? liftProgram((t.current / cycle) % 1) : 1);
        const lean = THREE.MathUtils.degToRad(anim.swing.lean ?? 0);
        // o'z lokal X o'qi atrofida (boshlang'ich burilish saqlanadi — aylana bo'ylab turgan o'rindiqlar ham to'g'ri og'adi)
        parts.swingers.forEach(({ node, q0 }, i) => {
          const ang = lean + amp * Math.sin(((t.current - i * stagger) * Math.PI * 2) / period);
          node.quaternion.copy(q0).multiply(tmpQ.setFromAxisAngle(X_AXIS, ang));
        });
      }
      if (tilting && anim.tilt) {
        const { degrees, seconds, stagger = 0 } = anim.tilt;
        const max = THREE.MathUtils.degToRad(degrees);
        parts.tilts.forEach(({ node, z0, hang, h0 }, i) => {
          const a = max * liftProgram(((t.current - i * stagger) / seconds) % 1);
          node.rotation.z = z0 + a;
          if (hang) hang.rotation.z = h0 - a;
        });
      }
      if (wheeling && anim.wheel && parts.wheel) {
        const a = ((t.current * Math.PI * 2) / anim.wheel.secondsPerTurn) % (Math.PI * 2);
        parts.wheel.rotation.z = a;
        for (const c of parts.cabins) c.rotation.z = -a;
      }
      if (props && anim.spin) {
        const da = (anim.spin.rpm / 60) * Math.PI * 2 * dt;
        for (const n of parts.spinners) n.rotation.y = (n.rotation.y + da) % (Math.PI * 2);
      }
      if (follows && track && anim.follow) {
        const tr = train.current, f = anim.follow;
        if (tr.wait > 0) tr.wait -= dt;
        else {
          // balandlikka qarab tezlik: pastda max, tepada min
          track.at(tr.s, tmp.p);
          const k = (tmp.p.y - track.yMin) / (track.yMax - track.yMin || 1);
          const before = tr.s % track.total;
          tr.s += (f.speed.max + (f.speed.min - f.speed.max) * k) * dt;
          const after = tr.s % track.total;
          const st = f.track.station;
          // bekatdan o'tdi — to'xtaydi
          if ((f.dwell ?? 0) > 0 && (before < st ? after >= st || after < before : after >= st && after < before)) {
            tr.s = st;
            tr.wait = f.dwell!;
          }
          if (tr.s > track.total * 1000) tr.s %= track.total;
        }
        placeCars(tr.s);
      }
    });
}

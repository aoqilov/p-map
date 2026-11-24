import { useEffect, useImperativeHandle, useMemo, useRef, forwardRef } from 'react';
import * as THREE from 'three';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Bridges, Buildings, Ground, Pins, Roads, RouteLine, Trees, Zones } from './layers';
import { Water, WaterPlants } from './water';
import { Fish } from './fish';
import { Attractions, attractionTop } from './attractions';
import { UserMarker } from './UserMarker';
import { StreetLamps } from './StreetLamps';
import { FlowerBeds, Fountains } from './EntranceFountain';
import { RubberSurfaces } from './RubberSurface';
import { Fences } from './Fences';
import { PlaygroundEquipment } from './PlaygroundEquipment';
import { Decor } from './Decor';
import { Walker, type WalkInput, type WalkPose } from './Walker';
import type { UserFix } from './useUserLocation';
import { PALETTE, useThemeName } from './theme';
import { RENDER } from './config';
import { toWorld } from './geometry';
import { MapGestures, applyView, groundAt, type Limits, type View } from './mapGestures';
import type { XY } from './projection';
import type { ParkData, Poi } from './types';

/**
 * Boshlang'ich ko'rinish (ochilganda va "Butun parkni ko'rsatish" bosilganda — doim shu): vertikaldan 49°, kamera parkning
 * shimoli-g'arbida turib janubi-sharqqa qaraydi — kirishlar pastda, basseynlar va 1-parking tepada (mijoz tanlagan burchak)
 */
export const HOME_VIEW = { polar: 49, azimuth: 234 } as const;
/**
 * Tor (portret telefon) ekran: park uzun o'qi (kirish → basseynlar) ekranga tik tushadi va qiyalik kamroq —
 * park ekranni to'ldiradi. Tartib o'sha: kirishlar pastda, basseynlar tepada
 */
export const HOME_VIEW_NARROW = { polar: 36, azimuth: 205 } as const;
const NARROW_PX = 640;
const POLAR = THREE.MathUtils.degToRad(HOME_VIEW.polar);
/** Ekran kengligiga qarab boshlang'ich burchaklar (radian) */
const homeAngles = (width: number) => {
  const h = width < NARROW_PX ? HOME_VIEW_NARROW : HOME_VIEW;
  return { polar: THREE.MathUtils.degToRad(h.polar), az: THREE.MathUtils.degToRad(h.azimuth) };
};
/** Perspektiv kamera ko'rish burchagi (tor — odatiy burchakda ortografikka yaqin, pastdan esa haqiqiy perspektiva) */
const FOV = 32;
/** Qiyalik chegarasi: 0 — tepadan, 80° — yerga yaqin; kamera yerdan kamida 1.7 m (odam ko'zi balandligi) */
const MAX_POLAR = THREE.MathUtils.degToRad(80);
const MIN_HEIGHT = 1.7;
const ANIM_SECONDS = 0.6;
/** Boshlang'ich ko'rinish o'lchami (ko'rinadigan maydonga nisbatan) va hisobga olinadigan pastki joy (filtr qatori, px) — doim bir xil */
const HOME_FILL = 1.05;
const HOME_BOTTOM = 68;

/** Qiyalik tugmasi uchun tayyor burchaklar */
export const TILT_PRESETS = [
  { id: 'top', label: 'tepadan', polar: 0 },
  { id: 'default', label: 'odatiy', polar: HOME_VIEW.polar },
  { id: 'low', label: 'pastdan', polar: 74 },
] as const;

export interface ViewInfo {
  /** Gorizontal burilish (gradus, boshlang'ich ko'rinishga nisbatan emas — shimoldan) */
  azimuth: number;
  /** Qiyalik: 0 — tepadan, 80 — yerga yaqin (gradus) */
  polar: number;
  /** Boshlang'ich burilish va qiyalikdan farq qiladimi (kompas ko'rinishi uchun) */
  rotated: boolean;
}

export interface MapApi {
  zoomBy(factor: number): void;
  /** Butun parkni ko'rsatish (boshlang'ich burchak bilan) */
  reset(): void;
  /** Nuqtani ko'rinadigan maydon markaziga olib kelish */
  flyTo(p: XY, zoomFactor?: number): void;
  /** Nuqtalar to'plamini (masalan, marshrutni) ekranga sig'dirish */
  fitTo(points: XY[]): void;
  /** Zoomni o'zgartirmasdan nuqtaga silliq surish (joylashuvni kuzatish rejimi) */
  panTo(p: XY): void;
  /** Qiyalikni o'zgartirish (gradus: 0 — tepadan, 80 — yerga yaqin) */
  setTilt(polarDeg: number): void;
  /** Burilish va qiyalikni boshlang'ich holatga qaytarish (kompas) */
  resetRotation(): void;
  /** Ekran (xarita konteyneri) markazidagi yer nuqtasi — park koordinatasi, metr (pritsel uchun) */
  pointAtCenter(): XY | null;
}

/** Xarita ustidagi UI panellari egallagan joy (px) — kamera shu joydan tashqarini ko'rinadigan maydon deb hisoblaydi */
export interface Insets {
  top: number;
  bottom: number;
  right: number;
}

export interface ParkSceneProps {
  data: ParkData;
  pois: Poi[];
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  route: XY[] | null;
  showTrees: boolean;
  insets: Insets;
  /** Fonus chiroqlari yoqilganmi (default: config.ts → STREET_LAMP.lightsOn) */
  lampsLit?: boolean;
  /** Mijozning joyi (faqat park ichida bo'lsa beriladi) */
  user: UserFix | null;
  /** Foydalanuvchi xaritani qo'lda sura boshladi — kuzatish rejimini o'chirish uchun */
  onUserInteract?: () => void;
  /** Burilish/qiyalik o'zgardi (kompas va qiyalik tugmasi uchun) */
  onViewChange?: (v: ViewInfo) => void;
  /** 3-shaxs yurish rejimi (berilsa — personaj paydo bo'ladi, kamera uning orqasidan): joystik holati va rang */
  walk?: { input: React.MutableRefObject<WalkInput>; accent: string } | null;
}

const reducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;

type Anim = { from: View; to: View; t: number };

const CameraRig = forwardRef<MapApi, {
  data: ParkData; insetsRef: React.MutableRefObject<Insets>; onUserInteract?: () => void; onViewChange?: (v: ViewInfo) => void; fogColor: string;
  walking: boolean; walkPose: React.MutableRefObject<WalkPose | null>;
}>(function CameraRig({ data, insetsRef, onUserInteract, onViewChange, fogColor, walking, walkPose }, ref) {
  // Panellar o'lchami ref orqali: Canvas ichidagi komponent kechroq yangilanadi, ref esa doim hozirgi qiymatda
  const insets = insetsRef.current;
  const { camera, size, invalidate, gl, scene } = useThree();
  // Imo-ishoralar Canvas konteynerida tinglanadi: pin (HTML) ustidan ham surish va zoom ishlaydi
  const connected = useThree((st) => st.events.connected) as HTMLElement | undefined;
  const internal = useThree((st) => st.internal);
  const cam = camera as THREE.PerspectiveCamera;
  const fitDist = useRef(600);
  const anim = useRef<Anim | null>(null);
  const ctl = useRef<MapGestures | null>(null);
  const interactRef = useRef(onUserInteract);
  interactRef.current = onUserInteract;
  const viewRef = useRef(onViewChange);
  viewRef.current = onViewChange;
  /** Foydalanuvchi xaritani qo'lda surgan bo'lsa, o'lcham o'zgarganda ko'rinishni tashlab yubormaymiz */
  const touched = useRef(false);

  const { minX, minY, maxX, maxY } = data.bounds;

  const limits = (): Limits => ({
    minDist: 6,
    maxDist: fitDist.current * 1.5,
    minPolar: 0,
    maxPolar: MAX_POLAR,
    // Butun park ko'rinadigan uzoqlikda ko'pi bilan ~62°, to'rt baravar yaqinda — 80° gacha
    maxPolarAt: (d) => THREE.MathUtils.lerp(MAX_POLAR, THREE.MathUtils.degToRad(62),
      THREE.MathUtils.clamp(Math.log(d / (fitDist.current / 4)) / Math.log(4), 0, 1)),
    minHeight: MIN_HEIGHT,
    bounds: { minX, maxX, minZ: -maxY, maxZ: -minY },
  });

  // Tuman: uzoq joylar fon rangiga singib ketadi (pastdan qaraganda ufq ko'rinadi, parkdan tashqari bo'shliq bilinmaydi)
  const fog = useMemo(() => new THREE.Fog(fogColor, 400, 3000), []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { fog.color.set(fogColor); invalidate(); }, [fog, fogColor, invalidate]);
  useEffect(() => { scene.fog = fog; return () => { scene.fog = null; }; }, [scene, fog]);
  const updateFog = (v: View) => {
    fog.near = Math.max(v.dist * 1.7, 160);
    fog.far = Math.max(v.dist * 5, 650);
  };

  const lastInfo = useRef('');
  const emitView = (v: View) => {
    updateFog(v);
    const info: ViewInfo = {
      azimuth: Math.round(THREE.MathUtils.radToDeg(v.az)),
      polar: Math.round(THREE.MathUtils.radToDeg(v.polar)),
      rotated: (() => {
        const h = homeAngles(size.width);
        return Math.abs(Math.atan2(Math.sin(v.az - h.az), Math.cos(v.az - h.az))) > 0.035 || Math.abs(v.polar - h.polar) > 0.035;
      })(),
    };
    const key = `${info.azimuth}|${info.polar}|${info.rotated}`;
    if (key !== lastInfo.current) { lastInfo.current = key; viewRef.current?.(info); }
  };

  /** Ko'rinadigan maydon (UI panellaridan tashqari) — ekran px */
  const visibleRect = (right = insetsRef.current.right, ins = insetsRef.current) => {
    const x1 = Math.max(200, size.width - right), y0 = ins.top, y1 = Math.max(y0 + 200, size.height - ins.bottom);
    return { cx: x1 / 2, cy: (y0 + y1) / 2, w: x1, h: y1 - y0 };
  };

  const probe = () => {
    const c = cam.clone();
    c.aspect = size.width / size.height;
    c.updateProjectionMatrix();
    return c;
  };

  /** Ko'rinishni nuqta `p` (yerda) ko'rinadigan maydon markazida turadigan qilib siljitish */
  const centerOn = (v: View, p: THREE.Vector3, right = insetsRef.current.right) => {
    const pc = probe(), r = visibleRect(right);
    const out = { ...v, tx: p.x, tz: p.z };
    for (let k = 0; k < 3; k++) {
      applyView(pc, out);
      const g = groundAt(pc, r.cx, r.cy, size.width, size.height);
      if (!g) break;
      out.tx += p.x - g.x;
      out.tz += p.z - g.z;
    }
    return out;
  };

  /** Nuqtalar (va baland attraksion tepalari) ko'rinadigan maydonga sig'adigan masofa va markaz */
  /** pad: ko'rinadigan maydonning qancha qismini egallasin; [eniga, bo'yiga] alohida ham berish mumkin */
  const computeFit = (pts: XY[], polar: number, az: number, pad: number | [number, number], right = insetsRef.current.right,
    tops: [XY, number][] = [], ins = insetsRef.current) => {
    const pc = probe(), r = visibleRect(right, ins);
    const [padW, padH] = typeof pad === 'number' ? [pad, pad] : pad;
    const world: THREE.Vector3[] = [];
    for (const p of pts) for (const h of [0, 10]) world.push(toWorld(p, h));
    for (const [p, h] of tops) world.push(toWorld(p, h));
    let x0 = Infinity, x1 = -Infinity, z0 = Infinity, z1 = -Infinity;
    for (const w of world) { x0 = Math.min(x0, w.x); x1 = Math.max(x1, w.x); z0 = Math.min(z0, w.z); z1 = Math.max(z1, w.z); }
    let v: View = { tx: (x0 + x1) / 2, tz: (z0 + z1) / 2, dist: 500, polar, az };
    const v3 = new THREE.Vector3();
    const box = (vv: View) => {
      applyView(pc, vv);
      let a = Infinity, b = -Infinity, c = Infinity, d = -Infinity, behind = false;
      for (const w of world) {
        v3.copy(w).project(pc);
        if (v3.z > 1) behind = true;
        const sx = (v3.x + 1) / 2 * size.width, sy = (1 - v3.y) / 2 * size.height;
        a = Math.min(a, sx); b = Math.max(b, sx); c = Math.min(c, sy); d = Math.max(d, sy);
      }
      return { w: b - a, h: d - c, cx: (a + b) / 2, cy: (c + d) / 2, behind };
    };
    for (let it = 0; it < 4; it++) {
      let lo = 5, hi = 30000;
      for (let k = 0; k < 36; k++) {
        const mid = Math.sqrt(lo * hi), bx = box({ ...v, dist: mid });
        if (!bx.behind && bx.w <= r.w * padW && bx.h <= r.h * padH) hi = mid; else lo = mid;
      }
      v.dist = hi;
      const bx = box(v);
      const gB = groundAt(pc, bx.cx, bx.cy, size.width, size.height), gR = groundAt(pc, r.cx, r.cy, size.width, size.height);
      if (!gB || !gR) break;
      v = { ...v, tx: v.tx + gB.x - gR.x, tz: v.tz + gB.z - gR.z };
    }
    return v;
  };

  const animateTo = (to: View) => {
    const c = ctl.current;
    if (!c) return;
    if (reducedMotion()) {
      c.set(to);
    } else {
      anim.current = { from: { ...c.view }, to, t: 0 };
    }
    invalidate();
  };

  /**
   * Boshlang'ich ko'rinish — doim bir xil: pastki oyna (tanlangan obyekt) ochiq bo'lsa ham hisobga olinmaydi,
   * faqat yuqori panel va pastdagi filtr qatori. Keng ekranda o'ng ustun hisobga olinmaydi (park kattaroq ko'rinadi).
   * HOME_FILL > 1: park chetlari panellar ostiga biroz kiradi (mijoz tanlagan o'lcham). Tor telefon ekranida esa eniga
   * to'liq sig'adi — chetlari kesilib qolmasin
   */
  const homeView = () => {
    const tops = data.attractions.map((a) => [a.at, attractionTop(a)] as [XY, number]);
    const ins = insetsRef.current;
    // Tor ekranda (telefon) park eniga to'liq sig'sin va o'ng ustun uni yopib qo'ymasin
    const narrow = size.width < NARROW_PX;
    const h = homeAngles(size.width);
    const v = computeFit(data.ground[0], h.polar, h.az, narrow ? [0.99, HOME_FILL] : HOME_FILL, narrow ? ins.right : 0, tops,
      { ...ins, bottom: HOME_BOTTOM });
    fitDist.current = v.dist;
    return v;
  };

  // Imo-ishoralar boshqaruvchisi (bir marta)
  useEffect(() => {
    const home = homeView();
    const host = connected ?? gl.domElement.parentElement ?? gl.domElement;
    const c = new MapGestures(cam, host, limits, {
      change: () => { emitView(c.view); invalidate(); },
      start: () => { touched.current = true; anim.current = null; interactRef.current?.(); },
      zoomTap: (x, y) => {
        // Ikki marta tegish: shu nuqtaga 2 baravar yaqinlashish (silliq)
        const rc = host.getBoundingClientRect();
        const g = groundAt(cam, x, y, rc.width, rc.height, c.view.dist * 8 + 400);
        const f = 0.5, v = c.view, d1 = Math.max(v.dist * f, 6), k = d1 / v.dist;
        animateTo(g ? { ...v, tx: g.x + (v.tx - g.x) * k, tz: g.z + (v.tz - g.z) * k, dist: d1 } : { ...v, dist: d1 });
      },
    }, home);
    ctl.current = c;
    // Kursor "qo'l" bo'lishi uchun: R3F bosish hodisasi bor obyektlar (bino, suv, attraksion, parking) ustidami
    const hoverRay = new THREE.Raycaster();
    c.hoverTest = (x, y) => {
      const rc = host.getBoundingClientRect(), objs = internal.interaction;
      if (!objs.length) return false;
      hoverRay.setFromCamera(new THREE.Vector2((x / rc.width) * 2 - 1, -(y / rc.height) * 2 + 1), cam);
      return objs.some((o) => o.visible && hoverRay.intersectObject(o, true).length > 0);
    };
    c.set(home);
    if (import.meta.env.DEV) (window as unknown as { __view: unknown }).__view = c;
    return () => { c.dispose(); ctl.current = null; };
  }, [cam, gl, connected]); // eslint-disable-line react-hooks/exhaustive-deps

  // Yurish rejimi: xarita imo-ishoralari o'chadi (kamerani Walker boshqaradi). Chiqishda — personaj turgan joydan
  // xarita ko'rinishiga silliq uzoqlashamiz
  useEffect(() => {
    const c = ctl.current;
    if (!c) return;
    if (walking) {
      anim.current = null;
      c.setEnabled(false);
      return;
    }
    c.setEnabled(true);
    const p = walkPose.current;
    if (!p) return;
    walkPose.current = null;
    touched.current = true;
    c.set({ tx: p.x, tz: p.z, dist: p.dist, polar: p.polar, az: p.az });
    animateTo({ ...c.view, dist: 70, polar: Math.min(c.view.polar, POLAR) });
  }, [walking]); // eslint-disable-line react-hooks/exhaustive-deps

  // Birinchi ochilish va o'lcham/panel o'zgarishi: foydalanuvchi hali tegmagan bo'lsa — parkni sig'diramiz
  useEffect(() => {
    const home = homeView();
    if (!touched.current && ctl.current) ctl.current.set(home);
    else ctl.current?.set({}); // chegaralar (maxDist) yangilansin
    invalidate();
  }, [size.width, size.height, insets.top, insets.bottom, insets.right]); // eslint-disable-line react-hooks/exhaustive-deps

  useFrame((_, dt) => {
    const a = anim.current, c = ctl.current;
    if (!a || !c) return;
    // Sekin qurilmada ham animatsiya cho'zilib ketmasin
    a.t = Math.min(1, a.t + Math.min(dt, 1 / 15) / ANIM_SECONDS);
    const k = 1 - Math.pow(1 - a.t, 3);
    const lerp = THREE.MathUtils.lerp;
    const dAz = Math.atan2(Math.sin(a.to.az - a.from.az), Math.cos(a.to.az - a.from.az));
    c.set({
      tx: lerp(a.from.tx, a.to.tx, k),
      tz: lerp(a.from.tz, a.to.tz, k),
      dist: Math.exp(lerp(Math.log(a.from.dist), Math.log(a.to.dist), k)), // masofa logarifmik — zoom bir tekis seziladi
      polar: lerp(a.from.polar, a.to.polar, k),
      az: a.from.az + dAz * k,
    });
    if (a.t >= 1) anim.current = null;
    invalidate();
  });

  useImperativeHandle(ref, () => ({
    zoomBy(f) {
      touched.current = true;
      const c = ctl.current;
      if (!c) return;
      // Ko'rinadigan maydon markazi atrofida
      const r = visibleRect();
      const g = groundAt(cam, r.cx, r.cy, size.width, size.height);
      const v = c.view, L = limits(), d1 = THREE.MathUtils.clamp(v.dist / f, Math.max(L.minDist, L.minHeight), L.maxDist), k = d1 / v.dist;
      animateTo(g ? { ...v, tx: g.x + (v.tx - g.x) * k, tz: g.z + (v.tz - g.z) * k, dist: d1 } : { ...v, dist: d1 });
    },
    reset() {
      touched.current = false;
      animateTo(homeView());
    },
    flyTo(p, zoomFactor = 3) {
      touched.current = true;
      const c = ctl.current;
      if (!c) return;
      const dist = Math.max(Math.min(c.view.dist, fitDist.current / zoomFactor), limits().minDist);
      animateTo(centerOn({ ...c.view, dist }, toWorld(p)));
    },
    panTo(p) {
      touched.current = true;
      const c = ctl.current;
      if (!c) return;
      animateTo(centerOn({ ...c.view }, toWorld(p)));
    },
    fitTo(points) {
      touched.current = true;
      const c = ctl.current;
      if (!c) return;
      // Marshrutni ko'rsatishda qiyalik juda katta bo'lsa, biroz tiklaymiz — yo'l butunligicha ko'rinsin
      const v = computeFit(points, Math.min(c.view.polar, POLAR), c.view.az, 0.85);
      animateTo({ ...v, dist: THREE.MathUtils.clamp(v.dist, limits().minDist, fitDist.current) });
    },
    setTilt(deg) {
      touched.current = true;
      const c = ctl.current;
      if (!c) return;
      const polar = THREE.MathUtils.degToRad(deg);
      // Markaz o'zgarmasin; pastdan qaraganda kamera yerga juda yaqin bo'lmasin — kerak bo'lsa biroz uzoqlashamiz
      const minD = MIN_HEIGHT / Math.max(Math.cos(polar), 0.05) * 1.6;
      // "Pastdan" ko'rinish uzoqdan ma'nosiz (park chiziq bo'lib qoladi) — biroz yaqinlashamiz
      const maxD = polar > THREE.MathUtils.degToRad(60) ? fitDist.current / 2.5 : Infinity;
      animateTo({ ...c.view, polar, dist: THREE.MathUtils.clamp(c.view.dist, Math.min(minD, fitDist.current), maxD) });
    },
    pointAtCenter() {
      const g = groundAt(cam, size.width / 2, size.height / 2, size.width, size.height);
      return g ? [Math.round(g.x * 100) / 100, Math.round(-g.z * 100) / 100] : null;
    },
    resetRotation() {
      touched.current = true;
      const c = ctl.current;
      if (!c) return;
      const h = homeAngles(size.width);
      animateTo({ ...c.view, az: h.az, polar: h.polar });
    },
  }));

  return null;
});

/**
 * Soyalarni har kadrda emas, sekundiga `hz` marta yangilash. Kamera surilganda soya o'zgarmaydi,
 * faqat harakatlanuvchi attraksionlar va daraxtlarni yoqib-o'chirish uni o'zgartiradi.
 * Oxirgi o'zgarish yangilanishlar orasiga tushib qolsa, taymer yana bitta kadr so'raydi — soya eskirib qolmaydi.
 */
function ShadowThrottle({ hz }: { hz: number }) {
  const gl = useThree((s) => s.gl);
  const invalidate = useThree((s) => s.invalidate);
  const last = useRef(-Infinity);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (hz <= 0) return;
    gl.shadowMap.autoUpdate = false;
    gl.shadowMap.needsUpdate = true;
    return () => {
      gl.shadowMap.autoUpdate = true;
      if (timer.current) clearTimeout(timer.current);
    };
  }, [gl, hz]);
  useFrame((st) => {
    if (hz <= 0) return;
    const t = st.clock.elapsedTime, step = 1 / hz;
    if (t - last.current >= step) {
      gl.shadowMap.needsUpdate = true;
      last.current = t;
    } else if (!timer.current) {
      timer.current = setTimeout(() => { timer.current = null; invalidate(); }, (step - (t - last.current)) * 1000 + 5);
    }
  });
  return null;
}

/** Faqat dev rejimda: konsoldan sahnani tekshirish uchun window.__three */
function DevExpose() {
  const state = useThree();
  useEffect(() => { (window as unknown as { __three: unknown }).__three = state; }, [state]);
  return null;
}

export const ParkScene = forwardRef<MapApi, ParkSceneProps>(function ParkScene(props, ref) {
  const { data, pois, selectedId, onSelect, route, showTrees, insets, user, onUserInteract, onViewChange, lampsLit = true } = props;
  const walkPose = useRef<WalkPose | null>(null);
  const insetsRef = useRef(insets);
  insetsRef.current = insets;
  const theme = useThemeName();
  const pal = PALETTE[theme];
  const select = (id: string) => onSelect(id);
  const span = Math.max(data.bounds.maxX - data.bounds.minX, data.bounds.maxY - data.bounds.minY);
  // Attraksion pini modelning haqiqiy tepasida turadi (sinf chegarasida emas)
  const pinPois = useMemo(() => pois.map((p) => {
    const a = data.attractions.find((x) => x.id === p.id);
    return a ? { ...p, elevation: attractionTop(a) + 1 } : p;
  }), [pois, data]);
  const mid = toWorld([(data.bounds.minX + data.bounds.maxX) / 2, (data.bounds.minY + data.bounds.maxY) / 2]);

  return (
    <Canvas
      flat
      shadows
      frameloop="demand"
      dpr={[1, 2]}
      camera={{ fov: FOV, position: [300, 300, 300], near: 1, far: 6000 }}
      // Faqat xaritaning o'ziga bosilganda tanlov bekor bo'ladi (pin — HTML, unga bosish bu yerga yetib kelmasin)
      onPointerMissed={(e) => { if ((e.target as HTMLElement | null)?.tagName === 'CANVAS') onSelect(null); }}
    >
      <color attach="background" args={[pal.base]} />
      <hemisphereLight args={[0xffffff, theme === 'dark' ? 0x223040 : 0xb9c7d6, theme === 'dark' ? 1.1 : 1.6]} />
      <directionalLight
        position={[mid.x - 180, 320, mid.z + 140]}
        intensity={theme === 'dark' ? 1.4 : 2.2}
        castShadow
        shadow-mapSize={[2048, 2048]}
        shadow-bias={-0.0004}
        shadow-normalBias={0.04}
      >
        <orthographicCamera attach="shadow-camera" args={[-span / 1.6, span / 1.6, span / 1.6, -span / 1.6, 1, 1200]} />
      </directionalLight>

      <Ground data={data} pal={pal} />
      <Zones data={data} pal={pal} selectedId={selectedId} onSelect={select} />
      <Water data={data} pal={pal} selectedId={selectedId} onSelect={select} night={theme === 'dark'} lampsLit={lampsLit} />
      <WaterPlants data={data} pal={pal} />
      <Fish data={data} pal={pal} />
      <Roads data={data} pal={pal} />
      <FlowerBeds data={data} pal={pal} />
      <RubberSurfaces data={data} pal={pal} />
      <Fences data={data} pal={pal} />
      <PlaygroundEquipment />
      <Decor pal={pal} lamps={data.lamps} night={theme === 'dark'} lampsLit={lampsLit} />
      <Fountains data={data} />
      <Bridges data={data} pal={pal} />
      <Buildings data={data} pal={pal} selectedId={selectedId} onSelect={select} />
      <Attractions items={data.attractions} pal={pal} selectedId={selectedId} onSelect={select} />
      {showTrees && <Trees data={data} pal={pal} />}
      <StreetLamps data={data} night={theme === 'dark'} lit={lampsLit} />
      {route && <RouteLine points={route} data={data} pal={pal} />}
      <Pins pois={pinPois} selectedId={selectedId} onSelect={select} showLabels={false} />

      {user && <UserMarker fix={user} />}

      <CameraRig ref={ref} data={data} insetsRef={insetsRef} onUserInteract={onUserInteract} onViewChange={onViewChange} fogColor={pal.base}
        walking={!!props.walk} walkPose={walkPose} />
      {props.walk && <Walker data={data} input={props.walk.input} pose={walkPose} accent={props.walk.accent} />}
      <ShadowThrottle hz={RENDER.shadowUpdatesPerSecond} />
      {import.meta.env.DEV && <DevExpose />}
    </Canvas>
  );
});

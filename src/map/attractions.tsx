import { Suspense, useEffect, useMemo, type ComponentType } from 'react';
import * as THREE from 'three';
import { Edges } from '@react-three/drei';
import type { ThreeEvent } from '@react-three/fiber';
import { AIR_RACE, ATTRACTION_SIZES } from './config';
import { Carousel, CAROUSEL_NATURAL } from './Carousel';
import { Coaster, COASTER_NATURAL } from './Coaster';
import { DropTower, DROP_TOWER_NATURAL } from './DropTower';
import { FerrisWheel, FERRIS_WHEEL_NATURAL } from './FerrisWheel';
import { Galleon, GALLEON_NATURAL } from './Galleon';
import { extrude, polyToShape, toWorld } from './geometry';
import type { Palette } from './theme';
import type { Attraction } from './types';
import { gltfModel } from './GltfModel';
import airRaceUrl from './models/air_race.glb?url';

export interface ModelProps {
  pal: Palette;
  selected: boolean;
}

interface ModelEntry {
  component: ComponentType<ModelProps>;
  /** Model qurilgan tabiiy o'lcham (metr): balandligi va eng keng tomoni */
  natural: { height: number; footprint: number };
  /** Model haqiqiy o'lchamda (Blender, metr) — o'lcham sinfiga cho'zilmaydi, masshtab 1 */
  realSize?: boolean;
  /** Xaritadagi o'lcham, metr (config.ts dan, har chizishda o'qiladi): eni va balandligi alohida o'zgaradi */
  size?: { width: number; height: number };
}

/**
 * Kalit: gen plan raqami ('#21', '#26.1') yoki eski GeoJSON `name`. Yangi attraksion (masalan, Blender modeli):
 * model komponentini yozing va shu yerga `'#<raqam>': { component, natural }` qilib qo'shing — quti o'rniga model chiqadi.
 * Har bir model lokal (0,0,0) markazda quriladi, old tomoni lokal +Z ga qaraydi.
 */
export const ATTRACTION_MODELS: Record<string, ModelEntry> = {
  Charxpalak: { component: FerrisWheel, natural: FERRIS_WHEEL_NATURAL },
  Karusel: { component: Carousel, natural: CAROUSEL_NATURAL },
  Erkin_tushish: { component: DropTower, natural: DROP_TOWER_NATURAL },
  Amerikan_tepaligi: { component: Coaster, natural: COASTER_NATURAL },
  Galleon: { component: Galleon, natural: GALLEON_NATURAL },
  Cars: { component: () => null, natural: { height: 1, footprint: 1 } },
  Merry_go_round: { component: () => null, natural: { height: 1, footprint: 1 } },
  Excavator: { component: () => null, natural: { height: 1, footprint: 1 } },
  Aqua_Lady_Birds: { component: () => null, natural: { height: 1, footprint: 1 } },

  // ---- Blender modellari (blender/*.py → src/map/models/*.glb), gen plan raqami bilan ----
  '#24': { component: gltfModel({ url: airRaceUrl, anim: AIR_RACE }), natural: { height: 6.0, footprint: 9.7 }, realSize: true, size: AIR_RACE.size },
};

/**
 * Attraksion modeli: avval gen plan raqami bo'yicha ('#47' — Колесо обозрения), keyin nomi bo'yicha (eski xarita).
 * Topilmasa — plandagi maydoncha shaklidagi quti (AttractionBox).
 */
export const modelFor = (item: Pick<Attraction, 'name' | 'num'>): ModelEntry | undefined =>
  (item.num ? ATTRACTION_MODELS[`#${item.num}`] : undefined) ?? ATTRACTION_MODELS[item.name];

/** Model o'z proporsiyasini saqlab, o'lcham sinfining "qutisi"ga sig'diriladigan masshtab */
/** Masshtab: [gorizontal, tik]. `size` berilgan bo'lsa — shu o'lchamga, aks holda bir xil (fitScale) */
export function modelScale(entry: ModelEntry, item: Pick<Attraction, 'size' | 'height'>): [number, number] {
  if (entry.size) return [entry.size.width / entry.natural.footprint, entry.size.height / entry.natural.height];
  const s = fitScale(entry, item);
  return [s, s];
}

export function fitScale(entry: ModelEntry, item: Pick<Attraction, 'size' | 'height'>) {
  if (entry.realSize) return 1;
  const box = ATTRACTION_SIZES[item.size];
  const maxHeight = item.height ?? box.height; // GeoJSON'dagi `height` sinf balandligini almashtiradi
  return Math.min(maxHeight / entry.natural.height, box.footprint / entry.natural.footprint);
}

/**
 * Modeli hali yo'q attraksion (gen plandan) — plandagi maydoncha shaklidagi quti. Balandligi o'lcham sinfiga qarab;
 * eksplikatsiyada aniq balandlik berilgan bo'lsa (Twist tower H=38 m) — o'sha.
 */
const BOX_HEIGHT: Record<number, number> = { 1: 2.5, 2: 4, 3: 6, 4: 9 };
export const boxHeight = (item: Pick<Attraction, 'size' | 'height'>) => item.height ?? BOX_HEIGHT[item.size] ?? 4;

/** Attraksion egallagan doira radiusi, metr (daraxtlarni olib tashlash uchun) */
export function attractionRadius(item: Attraction) {
  const entry = modelFor(item);
  if (entry) return (entry.natural.footprint / 2) * modelScale(entry, item)[0];
  if (!item.footprint) return 0;
  return Math.max(...item.footprint[0].map(([x, y]) => Math.hypot(x - item.at[0], y - item.at[1])));
}

/** Attraksionning xaritadagi haqiqiy balandligi (kamera sig'dirish uchun) */
export function attractionTop(item: Attraction) {
  const entry = modelFor(item);
  if (entry) return entry.natural.height * modelScale(entry, item)[1];
  return item.footprint ? boxHeight(item) : 0;
}

/** Modeli bor attraksion ostidagi maydoncha (plandagi pushti shakl) — plitka rangida, yerdan biroz baland */
function AttractionPad({ item, pal }: { item: Attraction; pal: Palette }) {
  const geom = useMemo(() => extrude(polyToShape(item.footprint!), 0.1), [item]);
  useEffect(() => () => geom.dispose(), [geom]);
  return (
    <mesh geometry={geom} rotation-x={-Math.PI / 2} receiveShadow>
      <meshStandardMaterial color={pal.padTop} roughness={0.9} />
    </mesh>
  );
}

/** Vaqtinchalik quti: Blender modeli ATTRACTION_MODELS ga qo'shilguncha */
function AttractionBox({ item, pal, selected, onSelect }: {
  item: Attraction; pal: Palette; selected: boolean; onSelect: (id: string) => void;
}) {
  const h = boxHeight(item);
  const geom = useMemo(() => extrude(polyToShape(item.footprint!), h), [item, h]);
  useEffect(() => () => geom.dispose(), [geom]);
  return (
    <mesh geometry={geom} rotation-x={-Math.PI / 2} castShadow receiveShadow
      onClick={(e) => { if (e.delta >= 6) return; e.stopPropagation(); onSelect(item.id); }}>
      <meshStandardMaterial color={selected ? pal.selected : pal.attractionBox} transparent opacity={0.82} roughness={0.7} />
      <Edges color={pal.attractionBoxEdge} threshold={20} />
    </mesh>
  );
}

function AttractionView({ item, pal, selected, onSelect }: {
  item: Attraction; pal: Palette; selected: boolean; onSelect: (id: string) => void;
}) {
  const entry = modelFor(item);
  if (!entry) return item.footprint ? <AttractionBox item={item} pal={pal} selected={selected} onSelect={onSelect} /> : null;
  const Model = entry.component;
  // bearing: old tomon yo'nalishi (shimoldan soat strelkasi bo'yicha). Lokal +Z → ma'lumotdagi (sin b, cos b)
  const yaw = Math.PI - THREE.MathUtils.degToRad(item.bearing);
  const click = (e: ThreeEvent<MouseEvent>) => {
    if (e.delta >= 6) return; // sudrash paytida tanlab qo'ymaslik uchun
    e.stopPropagation();
    onSelect(item.id);
  };
  const [sx, sy] = modelScale(entry, item);
  // .glb yuklanguncha — plandagi quti ko'rinib turadi
  const fallback = item.footprint ? <AttractionBox item={item} pal={pal} selected={selected} onSelect={onSelect} /> : null;
  return (
    <Suspense fallback={fallback}>
      {item.footprint && <AttractionPad item={item} pal={pal} />}
      <group position={toWorld(item.at)} rotation-y={yaw} scale={[sx, sy, sx]} onClick={click}>
        <Model pal={pal} selected={selected} />
      </group>
    </Suspense>
  );
}

export function Attractions({ items, pal, selectedId, onSelect }: {
  items: Attraction[]; pal: Palette; selectedId: string | null; onSelect: (id: string) => void;
}) {
  return (
    <>
      {items.map((a) => (
        <AttractionView key={a.id} item={a} pal={pal} selected={a.id === selectedId} onSelect={onSelect} />
      ))}
    </>
  );
}

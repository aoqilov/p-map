import { Suspense, useEffect, useMemo, type ComponentType } from 'react';
import * as THREE from 'three';
import { Edges } from '@react-three/drei';
import type { ThreeEvent } from '@react-three/fiber';
import { ATTRACTIONS } from '../attractions';
import type { AttractionDef } from '../attractions/define';
import { extrude, polyToShape, toWorld } from './geometry';
import { gltfModel } from './GltfModel';
import { WaterRide } from './WaterRide';
import type { Palette } from './theme';
import type { Attraction } from './types';

export interface ModelProps {
  pal: Palette;
  selected: boolean;
}

/** Modeli bor attraksion sozlamasi (src/attractions/<raqam>-<nom>/config.ts). Yo'q bo'lsa — plandagi quti */
const defFor = (item: Pick<Attraction, 'num'>): (AttractionDef & { model: NonNullable<AttractionDef['model']> }) | undefined => {
  const d = item.num ? ATTRACTIONS[item.num] : undefined;
  return d?.model ? (d as AttractionDef & { model: NonNullable<AttractionDef['model']> }) : undefined;
};

/** .glb komponentlari: har bir model uchun bir marta yasaladi */
const components = new Map<string, ComponentType<ModelProps>>();
const componentFor = (d: AttractionDef & { model: NonNullable<AttractionDef['model']> }) => {
  let c = components.get(d.model.url);
  if (!c) components.set(d.model.url, (c = gltfModel({ url: d.model.url, anim: d.anim })));
  return c;
};

/** Maydoncha markazi (yuza bo'yicha og'irlik markazi) — model shu yerga qo'yiladi; maydoncha yo'q bo'lsa pin nuqtasi */
function centerOf(item: Attraction): [number, number] {
  const ring = item.footprint?.[0];
  if (!ring || ring.length < 4) return item.at;
  let a = 0, cx = 0, cy = 0;
  for (let i = 0; i < ring.length - 1; i++) {
    const f = ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1];
    a += f; cx += (ring[i][0] + ring[i + 1][0]) * f; cy += (ring[i][1] + ring[i + 1][1]) * f;
  }
  return Math.abs(a) < 1e-6 ? item.at : [cx / (3 * a), cy / (3 * a)];
}

/** Masshtab [gorizontal, tik]: `size` berilgan bo'lsa — shu o'lchamga, aks holda asl o'lcham (1) */
function modelScale(d: AttractionDef & { model: NonNullable<AttractionDef['model']> }): [number, number] {
  if (!d.size) return [1, 1];
  return [d.size.width / d.model.natural.width, d.size.height / d.model.natural.height];
}

/**
 * Modeli hali yo'q attraksion (gen plandan) — plandagi maydoncha shaklidagi quti. Balandligi o'lcham sinfiga qarab;
 * eksplikatsiyada aniq balandlik berilgan bo'lsa (Twist tower H=38 m) — o'sha.
 */
const BOX_HEIGHT: Record<number, number> = { 1: 2.5, 2: 4, 3: 6, 4: 9 };
export const boxHeight = (item: Pick<Attraction, 'size' | 'height'>) => item.height ?? BOX_HEIGHT[item.size] ?? 4;

/** Attraksion egallagan doira radiusi, metr (daraxtlarni olib tashlash uchun) */
export function attractionRadius(item: Attraction) {
  if (item.ride) return 0; // suv attraksioni: atrofdagi daraxtlarni o'chirmaymiz (maydoncha chetida panjara)
  const d = defFor(item);
  if (d) return (d.size?.width ?? d.model.natural.width) / 2;
  if (!item.footprint) return 0;
  return Math.max(...item.footprint[0].map(([x, y]) => Math.hypot(x - item.at[0], y - item.at[1])));
}

/** Attraksionning xaritadagi haqiqiy balandligi (kamera sig'dirish uchun) */
export function attractionTop(item: Attraction) {
  if (item.ride) return 4.5; // orol daraxtlari
  const d = defFor(item);
  if (d) return d.size?.height ?? d.model.natural.height;
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

/** Vaqtinchalik quti: attraksion papkasiga model.glb qo'shilguncha */
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
  if (item.ride) return <WaterRide item={item} selected={selected} onSelect={onSelect} />;
  const d = defFor(item);
  if (!d) return item.footprint ? <AttractionBox item={item} pal={pal} selected={selected} onSelect={onSelect} /> : null;
  const Model = componentFor(d);
  // bearing: old tomon yo'nalishi (shimoldan soat strelkasi bo'yicha). Lokal +Z → ma'lumotdagi (sin b, cos b)
  const yaw = Math.PI - THREE.MathUtils.degToRad(d.bearing ?? item.bearing);
  const click = (e: ThreeEvent<MouseEvent>) => {
    if (e.delta >= 6) return; // sudrash paytida tanlab qo'ymaslik uchun
    e.stopPropagation();
    onSelect(item.id);
  };
  const [sx, sy] = modelScale(d);
  // .glb yuklanguncha — plandagi quti ko'rinib turadi
  const fallback = item.footprint ? <AttractionBox item={item} pal={pal} selected={selected} onSelect={onSelect} /> : null;
  return (
    <Suspense fallback={fallback}>
      {item.footprint && <AttractionPad item={item} pal={pal} />}
      <group position={toWorld(centerOf(item))} rotation-y={yaw} scale={[sx, sy, sx]} onClick={click}>
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

import { useEffect, useLayoutEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { Edges, Html, Line } from '@react-three/drei';
import type { ThreeEvent } from '@react-three/fiber';
import { bridgeGeometry, extrude, multiToShapes, polyToShape, toWorld } from './geometry';
import type { XY } from './projection';
import type { Palette } from './theme';
import type { Area, Building, ParkData, Poi } from './types';
import { PAVEMENT, type Category } from './config';
import { liveOf, shortLabel, statusLine } from '../api/live';
import { curbGeometry, curbTexture, stoneTexture } from './pavement';
import { attractionRadius } from './attractions';
import { waterLevelAt, waterLevelUnder } from './water';
import { DECOR, decorClearRadius } from '../decor';

const LIE_FLAT: [number, number, number] = [-Math.PI / 2, 0, 0];

/** Geometriya o'zgarganda yoki komponent o'chganda GPU xotirasini bo'shatish */
function useDisposable<T extends THREE.BufferGeometry>(make: () => T, deps: unknown[]): T {
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const g = useMemo(make, deps);
  useEffect(() => () => g.dispose(), [g]);
  return g;
}

/** Sudrash (pan) paytida tasodifan tanlab qo'ymaslik uchun */
const isTap = (e: ThreeEvent<MouseEvent>) => e.delta < 6;

export function Ground({ data, pal }: { data: ParkData; pal: Palette }) {
  // Suv o'rni kesib olingan plita: suv sathi yerdan pastda, teshik devorini water.tsx dagi qirg'oq yopadi
  const geom = useDisposable(() => extrude(multiToShapes(data.groundCut.length ? data.groundCut : [data.ground]), 1.5), [data]);
  return (
    <>
      <mesh rotation={LIE_FLAT} position-y={-1.5} receiveShadow>
        <planeGeometry args={[4000, 4000]} />
        <meshStandardMaterial color={pal.base} />
      </mesh>
      <mesh geometry={geom} rotation={LIE_FLAT} position-y={-1.5} receiveShadow castShadow>
        <meshStandardMaterial attach="material-0" color={pal.groundTop} />
        <meshStandardMaterial attach="material-1" color={pal.groundSide} />
      </mesh>
    </>
  );
}

interface Selectable {
  selectedId: string | null;
  onSelect: (id: string) => void;
}

const ROAD_TOP = 0.12; // asfalt sathi

export function Roads({ data, pal }: { data: ParkData; pal: Palette }) {
  const surface = useDisposable(() => extrude(multiToShapes(data.roads), ROAD_TOP), [data]);
  const curb = useDisposable(
    () => curbGeometry(data.roads, { width: PAVEMENT.curbWidth, height: PAVEMENT.curbHeight, base: ROAD_TOP }),
    [data],
  );
  const tex = useMemo(() => ({ stone: stoneTexture(), curb: curbTexture() }), []);
  useEffect(() => () => { tex.stone.dispose(); tex.curb.dispose(); }, [tex]);
  return (
    <>
      <mesh geometry={surface} rotation={LIE_FLAT} position-y={0} receiveShadow>
        <meshStandardMaterial attach="material-0" map={tex.stone} color={pal.roadTop} roughness={0.9} />
        <meshStandardMaterial attach="material-1" color={pal.roadSide} roughness={0.95} />
      </mesh>
      <mesh geometry={curb} receiveShadow>
        <meshStandardMaterial map={tex.curb} color={pal.curb} roughness={0.85} />
      </mesh>
    </>
  );
}

const DECK_Y = 0.35;

export function Bridges({ data, pal }: { data: ParkData; pal: Palette }) {
  const geoms = useMemo(
    () => data.bridges.map((b) => bridgeGeometry(b.line, b.width, DECK_Y, (p) => waterLevelAt(p, data.water))),
    [data],
  );
  useEffect(() => () => geoms.forEach((g) => { g.deck.dispose(); g.rails.dispose(); }), [geoms]);
  return (
    <>
      {geoms.map((g, i) => (
        <group key={data.bridges[i].id}>
          <mesh geometry={g.deck} castShadow receiveShadow>
            <meshStandardMaterial color={pal.bridge} roughness={0.8} />
          </mesh>
          <mesh geometry={g.rails} castShadow>
            <meshStandardMaterial color={pal.rail} roughness={0.8} />
          </mesh>
        </group>
      ))}
    </>
  );
}

function Zone({ area, color, edge, depth, selected, pal, onSelect }: {
  area: Area; color: string; edge: string; depth: number; selected: boolean; pal: Palette; onSelect: (id: string) => void;
}) {
  const geom = useDisposable(() => extrude(polyToShape(area.poly), depth), [area, depth]);
  return (
    <mesh geometry={geom} rotation={LIE_FLAT} receiveShadow
      onClick={(e) => { if (!isTap(e)) return; e.stopPropagation(); onSelect(area.id); }}>
      <meshStandardMaterial color={selected ? pal.selected : color} />
      <Edges color={edge} threshold={20} />
    </mesh>
  );
}

export function Zones({ data, pal, selectedId, onSelect }: { data: ParkData; pal: Palette } & Selectable) {
  return (
    <>
      {data.parking.map((a) => (
        <Zone key={a.id} area={a} color={pal.parking} edge={pal.parkingEdge} depth={0.07} pal={pal}
          selected={a.id === selectedId} onSelect={onSelect} />
      ))}
      {data.playgrounds.map((a) => (
        <Zone key={a.id} area={a} color={pal.playground} edge={pal.roadSide} depth={0.06} pal={pal}
          selected={a.id === selectedId} onSelect={onSelect} />
      ))}
    </>
  );
}

function BuildingMesh({ b, pal, selected, onSelect, base }: {
  b: Building; pal: Palette; selected: boolean; onSelect: (id: string) => void; base: number;
}) {
  // Suv ichidagi bino (rotonda) suv sathidan boshlanadi — ostida bo'shliq qolmaydi
  const geom = useDisposable(() => extrude(polyToShape(b.poly), b.height - base), [b, base]);
  // 3D modeli bor bino (src/decor/*/building.ts): quti ko'rinmaydi, faqat bosish uchun turadi
  if (b.model) return (
    <mesh geometry={geom} rotation={LIE_FLAT} position-y={base}
      onClick={(e) => { if (!isTap(e)) return; e.stopPropagation(); onSelect(b.id); }}>
      <meshBasicMaterial visible={false} />
    </mesh>
  );
  return (
    <mesh geometry={geom} rotation={LIE_FLAT} position-y={base} castShadow receiveShadow
      onClick={(e) => { if (!isTap(e)) return; e.stopPropagation(); onSelect(b.id); }}>
      <meshStandardMaterial attach="material-0" color={selected ? pal.selected : b.color ?? pal.roof} />
      <meshStandardMaterial attach="material-1" color={selected ? pal.selected : b.color ?? pal.wall} />
      <Edges color={pal.edge} threshold={25} />
    </mesh>
  );
}

export function Buildings({ data, pal, selectedId, onSelect }: { data: ParkData; pal: Palette } & Selectable) {
  // Suv ichidagi bino suv sathidan boshlanadi — ostida bo'shliq qolmaydi
  const bases = useMemo(() => data.buildings.map((b) => {
    const level = waterLevelUnder(b.poly, data.water);
    return level === null ? 0 : level - 0.1;
  }), [data]);
  return (
    <>
      {data.buildings.map((b, i) => (
        <BuildingMesh key={b.id} b={b} pal={pal} selected={b.id === selectedId} onSelect={onSelect} base={bases[i]} />
      ))}
    </>
  );
}

export function Trees({ data, pal }: { data: ParkData; pal: Palette }) {
  const trunks = useRef<THREE.InstancedMesh>(null!);
  const crowns = useRef<THREE.InstancedMesh>(null!);
  // Attraksion platformalari ostida daraxt qolmasin (haqiqiy o'lcham faqat brauzerda ma'lum)
  const trees = useMemo(() => {
    const zones = [
      ...data.attractions.map((a) => ({ at: a.at, r: attractionRadius(a) + 1.5 })),
      ...DECOR.map((d) => ({ at: d.at, r: decorClearRadius(d) })), // bezaklar (Eyfel minorasi va h.k.)
    ];
    return data.trees.filter(([x, y]) => zones.every((z) => Math.hypot(x - z.at[0], y - z.at[1]) > z.r));
  }, [data]);
  const count = trees.length;
  const trunkGeom = useDisposable(() => new THREE.CylinderGeometry(0.16, 0.24, 1.8, 6).translate(0, 0.9, 0), []);
  const crownGeom = useDisposable(() => new THREE.IcosahedronGeometry(1, 1), []);

  useLayoutEffect(() => {
    const m = new THREE.Matrix4();
    const q = new THREE.Quaternion();
    const c = new THREE.Color();
    trees.forEach(([x, y, s], i) => {
      const p = toWorld([x, y]);
      m.compose(p, q, new THREE.Vector3(s, s, s));
      trunks.current.setMatrixAt(i, m);
      m.compose(new THREE.Vector3(p.x, 1.8 * s + 1.3 * s, p.z), q, new THREE.Vector3(1.6 * s, 2 * s, 1.6 * s));
      crowns.current.setMatrixAt(i, m);
      crowns.current.setColorAt(i, c.set(pal.leaves[i % pal.leaves.length]));
    });
    trunks.current.instanceMatrix.needsUpdate = true;
    crowns.current.instanceMatrix.needsUpdate = true;
    if (crowns.current.instanceColor) crowns.current.instanceColor.needsUpdate = true;
  }, [trees, pal]);

  return (
    <>
      <instancedMesh ref={trunks} args={[trunkGeom, undefined, count]} castShadow>
        <meshStandardMaterial color={pal.trunk} />
      </instancedMesh>
      <instancedMesh ref={crowns} args={[crownGeom, undefined, count]} castShadow receiveShadow>
        <meshStandardMaterial flatShading roughness={0.9} />
      </instancedMesh>
    </>
  );
}

/** Marshrut chizig'i: oq "g'ilof" + rangli o'zak; ko'prik ustidagi tugunlar ko'tarib chiziladi */
export function RouteLine({ points, data, pal }: { points: XY[]; data: ParkData; pal: Palette }) {
  const world = useMemo(() => {
    const segs = data.bridges.flatMap((b) => b.line.slice(1).map((p, i) => [b.line[i], p] as const));
    const onBridge = ([x, y]: XY) => segs.some(([a, b]) => {
      const dx = b[0] - a[0], dy = b[1] - a[1];
      const L = dx * dx + dy * dy || 1;
      const t = Math.max(0, Math.min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / L));
      return Math.hypot(x - a[0] - t * dx, y - a[1] - t * dy) < 0.3;
    });
    return points.map((p) => toWorld(p, onBridge(p) ? DECK_Y + 0.45 : 0.4));
  }, [points, data]);

  if (world.length < 2) return null;
  const [first, last] = [world[0], world[world.length - 1]];
  return (
    <>
      <Line points={world} color="#ffffff" lineWidth={11} depthTest={false} renderOrder={10} />
      <Line points={world} color={pal.route} lineWidth={6} depthTest={false} renderOrder={11} />
      {[first, last].map((p, i) => (
        <mesh key={i} position={[p.x, p.y + 0.05, p.z]} rotation={LIE_FLAT} renderOrder={12}>
          <circleGeometry args={[i === 0 ? 2.2 : 2.6, 24]} />
          <meshBasicMaterial color={i === 0 ? '#ffffff' : pal.route} depthTest={false} />
        </mesh>
      ))}
    </>
  );
}


const ICONS: Record<Category, string> = {
  services: 'M12 5v14M5 12h14',
  fun: 'M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8L3.5 9.7l5.9-.9z',
  buildings: 'M5 20V8l7-4 7 4v12M9 20v-5h6v5',
  parking: 'M8 20V4h5.5a4.5 4.5 0 010 9H8',
  entrance: 'M10 5l7 7-7 7M4 12h13',
  kassa: 'M4 8a2 2 0 002-2h12a2 2 0 002 2v2a2 2 0 000 4v2a2 2 0 00-2 2H6a2 2 0 00-2-2v-2a2 2 0 000-4zM10 6v12',
};

export function Pins({ pois, selectedId, onSelect, showLabels }: {
  pois: Poi[]; selectedId: string | null; onSelect: (id: string) => void; showLabels: boolean;
}) {
  return (
    <>
      {pois.map((p) => {
        const active = p.id === selectedId;
        const live = liveOf(p.num);
        return (
          <Html key={p.id} position={toWorld(p.anchor, p.elevation + 1)} zIndexRange={active ? [60, 50] : [40, 0]}
            style={{ pointerEvents: 'none' }}>
            <button type="button"
              className={`pin pin--${p.category}${live ? ` pin--${live.status}` : ''}${active ? ' is-active' : ''}`}
              onClick={(e) => { e.stopPropagation(); onSelect(p.id); }}
              aria-label={live ? `${p.label}. ${statusLine(live)}` : p.label} aria-pressed={active}>
              <span className="pin__body">
                <span className="pin__icon">
                  <svg viewBox="0 0 24 24" aria-hidden="true"><path d={ICONS[p.category]} /></svg>
                </span>
                {live && (
                  <span className="pin__status" aria-hidden="true">
                    {live.status === 'stopped' && <svg viewBox="0 0 10 10"><path d="M3.6 2.6v4.8M6.4 2.6v4.8" /></svg>}
                  </span>
                )}
              </span>
              {(active || showLabels) && (
                <span className="pin__card">
                  <strong>{shortLabel(p.label)}</strong>
                  {live && <span className="pin__line"><i aria-hidden="true" />{statusLine(live)}</span>}
                </span>
              )}
            </button>
          </Html>
        );
      })}
    </>
  );
}

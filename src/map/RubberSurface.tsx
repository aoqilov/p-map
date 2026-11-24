// Bolalar maydonchasining yumshoq qoplamasi (EPDM rezina granula): gen plandagi ranglar bo'yicha —
// to'q sariq asos, to'q yashil halqalar va yo'laklar, qizil chetlar. Har bir qatlam oldingisidan biroz baland (ustma-ust
// tushganda "tirqishmasin"). Tekstura — canvas'da chizilgan mayda granulalar, rasm fayli yo'q.
import { useEffect, useMemo } from 'react';
import * as THREE from 'three';
import { extrude, polyToShape } from './geometry';
import { canvasTexture } from './modelKit';
import type { Palette } from './theme';
import type { ParkData } from './types';

/** Qatlam: yerdan balandligi (m) va rang kaliti (theme.ts) */
const LAYERS = {
  rubber: { top: 0.07, color: 'rubber' },
  rubber_green: { top: 0.09, color: 'rubberGreen' },
  rubber_edge: { top: 0.11, color: 'rubberEdge' },
} as const;
/** Tekstura bir marta takrorlanadigan masofa, m */
const TILE = 1.5;

function granuleTexture() {
  let seed = 7;
  const rand = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  const tex = canvasTexture(256, 256, (c, w, h) => {
    c.fillStyle = '#e6e6e6';
    c.fillRect(0, 0, w, h);
    for (let i = 0; i < 4200; i++) {
      const v = 175 + Math.floor(rand() * 80);
      c.fillStyle = `rgb(${v},${v},${v})`;
      const s = 1 + rand() * 2.2;
      c.fillRect(rand() * w, rand() * h, s, s);
    }
  });
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(1 / TILE, 1 / TILE);
  return tex;
}

export function RubberSurfaces({ data, pal }: { data: ParkData; pal: Palette }) {
  const tex = useMemo(granuleTexture, []);
  const geoms = useMemo(() => (Object.keys(LAYERS) as (keyof typeof LAYERS)[]).map((kind) => {
    const polys = (data.surfaces ?? []).filter((s) => s.kind === kind).map((s) => polyToShape(s.poly));
    return { kind, geom: polys.length ? extrude(polys, LAYERS[kind].top) : null };
  }), [data]);
  useEffect(() => () => { tex.dispose(); geoms.forEach((g) => g.geom?.dispose()); }, [tex, geoms]);
  return (
    <>
      {geoms.map(({ kind, geom }) => geom && (
        <mesh key={kind} geometry={geom} rotation-x={-Math.PI / 2} receiveShadow>
          <meshStandardMaterial attach="material-0" map={tex} color={pal[LAYERS[kind].color]} roughness={0.95} />
          <meshStandardMaterial attach="material-1" color={pal[LAYERS[kind].color]} roughness={0.95} />
        </mesh>
      ))}
    </>
  );
}

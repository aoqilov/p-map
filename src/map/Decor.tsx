// Bezaklar (src/decor/*/config.ts): attraksion emas — faqat 3D model, bosilmaydi, pin yo'q.
import { Suspense, useEffect, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { Billboard, useGLTF, useTexture } from '@react-three/drei';
import { DECOR, decorScale } from '../decor';
import type { DecorDef } from '../decor/define';
import { toWorld } from './geometry';
import { prefersReducedMotion, useAmbientFrames } from './modelKit';
import { WATER } from './config';
import type { Palette } from './theme';
import { WaterSurfaces, type WaterSurfaceDef } from './water';

/** Suv uchun sahna ma'lumotlari (hovuz shaderi: ranglar, fonus aksi) */
interface DecorEnv { pal: Palette; lamps: [number, number][]; night: boolean; lampsLit: boolean }

/** Model koordinatasi (Blender X, Y) → park koordinatasi: bezak joyi, burilishi va masshtabi bilan */
function modelToPark(d: DecorDef, sx: number) {
  const yaw = Math.PI - THREE.MathUtils.degToRad(d.bearing ?? 0);
  const c = Math.cos(yaw), s = Math.sin(yaw);
  return ([x, y]: [number, number]): [number, number] => {
    // glTF: (x, z = -y); Y o'qi atrofida yaw ga burish; dunyo (X, Z) → park (X, -Z)
    const lx = x * sx, lz = -y * sx;
    return [d.at[0] + lx * c + lz * s, d.at[1] - (-lx * s + lz * c)];
  };
}

function DecorModel({ d, env }: { d: DecorDef; env: DecorEnv }) {
  const { scene } = useGLTF(d.model.url);
  const root = useMemo(() => {
    const r = scene.clone(true);
    r.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      m.castShadow = true;
      m.receiveShadow = true;
      m.raycast = () => {}; // bosilmaydi — ostidagi obyektlarni tanlashga xalal bermasin
      const mname = (m.material as THREE.Material).name;
      if (mname === d.flow?.material) m.castShadow = false; // suv pardasi soya tashlamaydi
      if (mname === d.water?.material) m.visible = false;   // o'rniga hovuz suvi (WaterSurfaces)
    });
    return r;
  }, [scene]);
  const [sx, sy] = decorScale(d);
  const surfaces = useMemo<WaterSurfaceDef[]>(() => {
    if (!d.water) return [];
    const toPark = modelToPark(d, sx);
    return d.water.basins.map((b, i) => {
      const ring = b.poly.map(toPark);
      return { id: `${d.name}-suv-${i}`, poly: [[...ring, ring[0]]], level: b.z * sy };
    });
  }, [d, sx, sy]);
  // bearing: old tomon (Blender'da -Y) yo'nalishi, attraksionlardagi kabi
  const yaw = Math.PI - THREE.MathUtils.degToRad(d.bearing ?? 0);
  return (
    <>
      <group position={toWorld(d.at)} rotation-y={yaw} scale={[sx, sy, sx]}>
        <primitive object={root} />
      </group>
      {d.flow && <DecorFlow root={root} flow={d.flow} />}
      {surfaces.length > 0 && <WaterSurfaces surfaces={surfaces} style={d.water?.style ?? 'pond'} {...env} />}
      {d.card && (
        <Suspense fallback={null}>
          <DecorCard d={d} card={d.card} top={d.model.natural.height * sy} />
        </Suspense>
      )}
    </>
  );
}

const noRaycast = () => {};

/** Oqayotgan suv tekshurasi: oq-havorang tik chiziqlar (shaffoflik bilan), V bo'ylab takrorlanadi */
function flowTexture() {
  const W = 64, H = 128;
  const cv = document.createElement('canvas');
  cv.width = W;
  cv.height = H;
  const g = cv.getContext('2d')!;
  g.fillStyle = 'rgba(200,230,250,0.55)';
  g.fillRect(0, 0, W, H);
  let seed = 11;
  const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  for (let i = 0; i < 70; i++) {
    const x = rnd() * W, y = rnd() * H, w = 1 + rnd() * 3, h = 14 + rnd() * 40;
    g.fillStyle = `rgba(255,255,255,${0.35 + rnd() * 0.5})`;
    g.fillRect(x, y, w, h);
    if (y + h > H) g.fillRect(x, y - H, w, h); // tikuvsiz takrorlanish
  }
  const t = new THREE.CanvasTexture(cv);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

/** Sharshara: `flow.material` nomli materialga tekstura qo'yib, uni pastga suradi (suv oqimi) */
function DecorFlow({ root, flow }: { root: THREE.Object3D; flow: NonNullable<DecorDef['flow']> }) {
  const tex = useMemo(flowTexture, []);
  useEffect(() => {
    root.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      const mat = m.material as THREE.MeshStandardMaterial;
      if (mat.name !== flow.material) return;
      mat.map = tex;
      mat.color.set('#ffffff');
      mat.transparent = true;
      mat.opacity = 1;
      mat.depthWrite = false;
      mat.side = THREE.DoubleSide;
      mat.needsUpdate = true;
    });
    return () => tex.dispose();
  }, [root, flow.material, tex]);
  const animate = WATER.animate && !prefersReducedMotion();
  useAmbientFrames(animate);
  // glTF da V teskari: tekstura siljishi oshsa, chiziqlar pastga oqadi
  useFrame((_, dt) => { if (animate) tex.offset.y = (tex.offset.y + flow.speed * Math.min(dt, 0.1)) % 1; });
  return null;
}

/** Model tepasidagi karta: Billboard — xarita aylantirilsa ham, egilsa ham doim kameraga qaragan */
function DecorCard({ d, card, top }: { d: DecorDef; card: NonNullable<DecorDef['card']>; top: number }) {
  const tex = useTexture(card.url);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return (
    <Billboard position={toWorld(d.at, top + card.lift + card.height / 2)}>
      <mesh raycast={noRaycast}>
        <planeGeometry args={[card.width, card.height]} />
        <meshBasicMaterial map={tex} transparent toneMapped={false} side={THREE.DoubleSide} />
      </mesh>
    </Billboard>
  );
}

export function Decor(env: DecorEnv) {
  return (
    <>
      {DECOR.map((d, i) => (
        <Suspense key={`${d.name}-${i}`} fallback={null}>
          <DecorModel d={d} env={env} />
        </Suspense>
      ))}
    </>
  );
}

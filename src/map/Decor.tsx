// Bezaklar (src/decor/*/config.ts): attraksion emas — faqat 3D model, bosilmaydi, pin yo'q.
import { Suspense, useMemo } from 'react';
import * as THREE from 'three';
import { useGLTF } from '@react-three/drei';
import { DECOR, decorScale } from '../decor';
import type { DecorDef } from '../decor/define';
import { toWorld } from './geometry';

function DecorModel({ d }: { d: DecorDef }) {
  const { scene } = useGLTF(d.model.url);
  const root = useMemo(() => {
    const r = scene.clone(true);
    r.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      m.castShadow = true;
      m.receiveShadow = true;
      m.raycast = () => {}; // bosilmaydi — ostidagi obyektlarni tanlashga xalal bermasin
    });
    return r;
  }, [scene]);
  const [sx, sy] = decorScale(d);
  // bearing: old tomon (Blender'da -Y) yo'nalishi, attraksionlardagi kabi
  const yaw = Math.PI - THREE.MathUtils.degToRad(d.bearing ?? 0);
  return (
    <group position={toWorld(d.at)} rotation-y={yaw} scale={[sx, sy, sx]}>
      <primitive object={root} />
    </group>
  );
}

export function Decor() {
  return (
    <>
      {DECOR.map((d) => (
        <Suspense key={d.name} fallback={null}>
          <DecorModel d={d} />
        </Suspense>
      ))}
    </>
  );
}

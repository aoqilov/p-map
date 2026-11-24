// Bolalar maydonchasi (30) jihozlari: bitta .glb dan har bir jihoz (item_<nom>) nusxalanib, layout.json dagi joyiga
// qo'yiladi. Jihozlar alohida pin emas — maydoncha bitta pin bilan qoladi. Harakat — useModelAnimation (GltfModel.tsx).
import { Suspense, useMemo } from 'react';
import * as THREE from 'three';
import { useGLTF } from '@react-three/drei';
import { PLAYGROUND_ANIM, PLAYGROUND_ITEMS, PLAYGROUND_MODEL, type PlaygroundItem } from '../attractions/30-detskaya-ploshchadka/equipment';
import { useModelAnimation } from './GltfModel';
import { toWorld } from './geometry';

/** Rezina qoplama ustida (RubberSurface: eng yuqori qatlam ~0.11 m) */
const GROUND_Y = 0.07;

function Item({ src, item }: { src: THREE.Object3D; item: PlaygroundItem }) {
  const root = useMemo(() => {
    const r = src.clone(true);
    r.position.set(0, 0, 0); // Blender'da ko'rish uchun yonma-yon terilgan — xaritada joyi layout.json dan
    r.traverse((o) => { if ((o as THREE.Mesh).isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    return r;
  }, [src]);
  useModelAnimation(root, PLAYGROUND_ANIM[item.name] ?? {});
  return (
    <group position={toWorld([item.x, item.y], GROUND_Y)} rotation-y={THREE.MathUtils.degToRad(item.rot)}>
      <primitive object={root} />
    </group>
  );
}

function Items() {
  const { scene } = useGLTF(PLAYGROUND_MODEL);
  const nodes = useMemo(() => new Map(scene.children.map((c) => [c.name, c])), [scene]);
  return (
    <>
      {PLAYGROUND_ITEMS.map((it, i) => {
        const src = nodes.get(`item_${it.name}`);
        // bir xil jihoz bir necha marta bo'lishi mumkin (masalan, soya daraxtlari)
        return src ? <Item key={`${it.name}-${i}`} src={src} item={it} /> : null;
      })}
    </>
  );
}

export function PlaygroundEquipment() {
  return (
    <Suspense fallback={null}>
      <Items />
    </Suspense>
  );
}

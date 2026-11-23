import { useEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { Html } from '@react-three/drei';
import { useFrame, useThree } from '@react-three/fiber';
import type { UserFix } from './useUserLocation';

const BLUE = '#2f80ff';

/** "Siz shu yerdasiz": ko'k nuqta (DOM, CSS puls), aniqlik doirasi va yo'nalish yelpig'ichi (WebGL) */
export function UserMarker({ fix }: { fix: UserFix }) {
  const group = useRef<THREE.Group>(null!);
  const accuracy = useRef<THREE.Group>(null!);
  const heading = useRef<THREE.Group>(null!);
  const invalidate = useThree((s) => s.invalidate);
  const shown = useRef<THREE.Vector3 | null>(null);
  const target = useMemo(() => new THREE.Vector3(fix.xy[0], 0, -fix.xy[1]), [fix]);

  const wedge = useMemo(() => {
    const s = new THREE.Shape();
    s.moveTo(0, 0);
    s.absarc(0, 0, 9, Math.PI / 2 - 0.45, Math.PI / 2 + 0.45, false);
    s.lineTo(0, 0);
    return new THREE.ShapeGeometry(s, 12);
  }, []);
  useEffect(() => () => wedge.dispose(), [wedge]);

  // Yangi o'lchov kelganda nuqta sakramasdan, silliq siljiydi
  useEffect(() => {
    if (!shown.current) shown.current = target.clone();
    invalidate();
  }, [target, invalidate]);

  useFrame((_, dt) => {
    const cur = shown.current;
    if (!cur) return;
    const k = 1 - Math.exp(-Math.min(dt, 0.1) / 0.25);
    cur.lerp(target, k);
    group.current.position.copy(cur);
    const r = THREE.MathUtils.clamp(fix.accuracy ?? 10, 3, 80);
    accuracy.current.scale.setScalar(r);
    heading.current.visible = fix.heading !== null;
    heading.current.rotation.y = -THREE.MathUtils.degToRad(fix.heading ?? 0);
    if (cur.distanceToSquared(target) > 0.0025) invalidate();
  });

  return (
    <group ref={group}>
      <group ref={accuracy} position-y={0.3}>
        <mesh rotation-x={-Math.PI / 2} renderOrder={5}>
          <circleGeometry args={[1, 48]} />
          <meshBasicMaterial color={BLUE} transparent opacity={0.14} depthWrite={false} />
        </mesh>
        <mesh rotation-x={-Math.PI / 2} renderOrder={5}>
          <ringGeometry args={[0.96, 1, 64]} />
          <meshBasicMaterial color={BLUE} transparent opacity={0.45} depthWrite={false} />
        </mesh>
      </group>
      <group ref={heading} position-y={0.35}>
        <mesh geometry={wedge} rotation-x={-Math.PI / 2} renderOrder={6}>
          <meshBasicMaterial color={BLUE} transparent opacity={0.35} depthWrite={false} />
        </mesh>
      </group>
      <Html position={[0, 0.5, 0]} center zIndexRange={[80, 70]} style={{ pointerEvents: 'none' }}>
        <span className="me-dot" aria-label="Siz shu yerdasiz" />
      </Html>
    </group>
  );
}

import { useEffect, useLayoutEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
import { STREET_LAMP } from './config';
import { V, canvasTexture, mergeAll, rod } from './modelKit';
import { toWorld } from './geometry';
import type { ParkData } from './types';

// Klassik park fonusi: sakkiz qirrali asos, ingichka ustun ikki halqa bilan, olti qirrali shisha fonus va uchli tom.
// Hammasi InstancedMesh — fonus soni ko'paysa ham 4 ta draw call.
// Yorug'lik haqiqiy chiroq (PointLight) emas: yerdagi iliq doira va fonus atrofidagi nur — telefon uchun yengil.

export const LANTERN_Y = 3.8; // shisha markazi (suvdagi aks ham shu balandlikdan hisoblanadi)

export function lampGeometry() {
  // Fonuslar ko'p (100+), shuning uchun har biri ~250 uchburchak: segmentlar minimal, mayda detallar yo'q
  const body = mergeAll([
    new THREE.CylinderGeometry(0.27, 0.29, 0.18, 8).translate(0, 0.09, 0), // plita (yo'l sathidan baland)
    new THREE.CylinderGeometry(0.15, 0.26, 0.36, 8).translate(0, 0.36, 0), // qo'ng'iroqsimon asos
    new THREE.CylinderGeometry(0.055, 0.07, 2.9, 6).translate(0, 1.99, 0), // ustun
    ...[1.35, 2.4].map((y) => new THREE.CylinderGeometry(0.095, 0.095, 0.16, 8).translate(0, y, 0)), // bezak halqalari
    new THREE.CylinderGeometry(0.11, 0.06, 0.16, 8).translate(0, 3.47, 0), // kapitel
    new THREE.CylinderGeometry(0.15, 0.13, 0.06, 6).translate(0, 3.56, 0), // fonus tagi
    ...Array.from({ length: 6 }, (_, k) => { // olti qirra ramkasi (yuqoriga kengayadi)
      const a = (k / 6) * Math.PI * 2;
      return rod(V(0.15 * Math.sin(a), 3.58, 0.15 * Math.cos(a)), V(0.245 * Math.sin(a), 4.06, 0.245 * Math.cos(a)), 0.014, 3);
    }),
    new THREE.CylinderGeometry(0.27, 0.26, 0.06, 6).translate(0, 4.09, 0), // yuqori halqa
    new THREE.ConeGeometry(0.33, 0.32, 6).translate(0, 4.28, 0), // tom
    new THREE.ConeGeometry(0.035, 0.18, 4).translate(0, 4.52, 0), // uchi
  ]);
  const glass = new THREE.CylinderGeometry(0.235, 0.145, 0.48, 6, 1, false).translate(0, 3.82, 0);
  return { body, glass };
}

const glowTexture = () =>
  canvasTexture(128, 128, (g, w, h) => {
    const grad = g.createRadialGradient(w / 2, h / 2, 0, w / 2, h / 2, w / 2);
    grad.addColorStop(0, 'rgba(255,236,190,1)');
    grad.addColorStop(0.25, 'rgba(255,214,150,0.55)');
    grad.addColorStop(1, 'rgba(255,200,120,0)');
    g.fillStyle = grad;
    g.fillRect(0, 0, w, h);
  });

/** lit=false — fonuslar turadi, lekin chiroqlari o'chiq (shisha to'q, yerda yorug'lik va nur yo'q) */
export function StreetLamps({ data, night, lit = true }: { data: ParkData; night: boolean; lit?: boolean }) {
  const lamps = data.lamps;
  const geo = useMemo(() => {
    const g = lampGeometry();
    const pool = new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2);
    const halo = new THREE.BufferGeometry().setAttribute(
      'position',
      new THREE.Float32BufferAttribute(lamps.flatMap(([x, y]) => [x, LANTERN_Y, -y]), 3),
    );
    return { ...g, pool, halo, tex: glowTexture() };
  }, [lamps]);
  useEffect(() => () => {
    [geo.body, geo.glass, geo.pool, geo.halo].forEach((g) => g.dispose());
    geo.tex.dispose();
  }, [geo]);

  const body = useRef<THREE.InstancedMesh>(null!);
  const glass = useRef<THREE.InstancedMesh>(null!);
  const pools = useRef<THREE.InstancedMesh>(null!);
  const haloMat = useRef<THREE.PointsMaterial>(null!);
  const camera = useThree((s) => s.camera);

  useLayoutEffect(() => {
    const m = new THREE.Matrix4();
    const q = new THREE.Quaternion();
    const one = new THREE.Vector3(1, 1, 1);
    const r = STREET_LAMP.lightRadius * 2;
    lamps.forEach(([x, y], i) => {
      q.setFromAxisAngle(V(0, 1, 0), (i * 1.3) % (Math.PI / 3)); // olti qirra bir xil qaramasin
      m.compose(toWorld([x, y]), q, one);
      body.current.setMatrixAt(i, m);
      glass.current.setMatrixAt(i, m);
      pools.current.setMatrixAt(i, m.makeScale(r, 1, r).setPosition(x, 0.14, -y));
    });
    [body, glass, pools].forEach((ref) => (ref.current.instanceMatrix.needsUpdate = true));
  }, [lamps]);

  // Nur (Points): perspektiv kamerada masofaga qarab o'zi kichrayadi (sizeAttenuation) — o'lchami metrda saqlanadi.
  // Ortografik kamerada esa piksel o'lchamini zoomga qarab yangilaymiz
  const ortho = (camera as THREE.OrthographicCamera).isOrthographicCamera === true;
  const haloSize = ortho ? 10 : (STREET_LAMP.haloRadius * 2) / Math.tan(THREE.MathUtils.degToRad((camera as THREE.PerspectiveCamera).fov) / 2);
  useFrame(() => {
    if (!ortho) return;
    const zoom = (camera as THREE.OrthographicCamera).zoom;
    const size = STREET_LAMP.haloRadius * 2 * zoom;
    if (haloMat.current && Math.abs(haloMat.current.size - size) > 0.5) haloMat.current.size = size;
  });

  if (!lamps.length) return null;
  const strength = night ? 1 : STREET_LAMP.dayStrength;

  return (
    <group>
      <instancedMesh ref={body} args={[geo.body, undefined, lamps.length]}>
        <meshStandardMaterial color="#1d2024" metalness={0.55} roughness={0.4} />
      </instancedMesh>
      <instancedMesh ref={glass} args={[geo.glass, undefined, lamps.length]}>
        <meshBasicMaterial color={lit ? STREET_LAMP.color : STREET_LAMP.offGlass} toneMapped={false} />
      </instancedMesh>
      <instancedMesh ref={pools} args={[geo.pool, undefined, lamps.length]} renderOrder={4} visible={lit}>
        <meshBasicMaterial map={geo.tex} color={STREET_LAMP.color} transparent opacity={0.75 * strength}
          blending={THREE.AdditiveBlending} depthWrite={false} toneMapped={false} fog={false} />
      </instancedMesh>
      <points geometry={geo.halo} renderOrder={7} visible={lit}>
        <pointsMaterial ref={haloMat} map={geo.tex} color={STREET_LAMP.color} size={haloSize} sizeAttenuation={!ortho}
          transparent opacity={0.9 * strength} blending={THREE.AdditiveBlending} depthWrite={false} toneMapped={false} fog={false} />
      </points>
    </group>
  );
}

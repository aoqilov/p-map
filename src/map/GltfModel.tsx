// Blender'da yasalgan attraksion modellari (.glb). Model haqiqiy o'lchamda (metr), markazi (0,0,0), Y — tepaga.
// Harakatlanadigan qismlar Blender'dagi obyekt nomi bilan topiladi:
//   rotor   — markaz atrofida aylanadi (bolalari ham u bilan birga aylanadi)
//   lift<N> — o'z joyida yuqoriga-pastga ko'tariladi (masalan, Air Race samolyotlari ustun bo'ylab)
// Tezlik va balandlik config.ts da (masalan, AIR_RACE). Tanlangan holat pin bilan ko'rsatiladi.
import { useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import { prefersReducedMotion, useAmbientFrames } from './modelKit';
import type { ModelProps } from './attractions';

export interface GltfAnimation {
  /** Bir aylanish, soniya. 0 — aylanmaydi */
  secondsPerTurn?: number;
  /**
   * `lift*` qismlarining ko'tarilishi (meters: 0 — o'chiq). Sikl: pastda turadi → silliq ko'tariladi → tepada turadi →
   * silliq tushadi. `stagger` — har bir keyingi qism shuncha soniya kech ko'tariladi (0 — hammasi birga)
   */
  lift?: { meters: number; seconds: number; stagger?: number };
}

export interface GltfOptions {
  url: string;
  /** Animatsiya sozlamalari — har kadrda o'qiladi, shuning uchun config.ts dagi obyektni to'g'ridan-to'g'ri bering */
  anim?: GltfAnimation;
}

const smooth = (x: number) => x * x * (3 - 2 * x);
/** Ko'tarilish dasturi, u ∈ [0, 1) sikl ulushi → balandlik ulushi 0..1: 20% pastda, 30% ko'tarilish, 20% tepada, 30% tushish */
function liftProgram(u: number) {
  const v = u < 0 ? u + 1 : u;
  if (v < 0.2) return 0;
  if (v < 0.5) return smooth((v - 0.2) / 0.3);
  if (v < 0.7) return 1;
  return 1 - smooth((v - 0.7) / 0.3);
}

/** .glb modelidan attraksion komponenti yasaydi (ATTRACTION_MODELS ga qo'shish uchun) */
export function gltfModel({ url, anim = {} }: GltfOptions) {
  function Model(_: ModelProps) {
    const { scene } = useGLTF(url);
    // Har bir nusxa o'z ierarxiyasiga ega bo'lsin (geometriya va materiallar umumiy qoladi)
    const root = useMemo(() => {
      const r = scene.clone(true);
      r.traverse((o) => {
        if ((o as THREE.Mesh).isMesh) { o.castShadow = true; o.receiveShadow = true; }
      });
      return r;
    }, [scene]);
    const parts = useMemo(() => {
      const lifts: { node: THREE.Object3D; y0: number }[] = [];
      root.traverse((o) => { if (/^lift\d*/.test(o.name)) lifts.push({ node: o, y0: o.position.y }); });
      return { rotor: root.getObjectByName('rotor') ?? null, lifts };
    }, [root]);

    const spins = (anim.secondsPerTurn ?? 0) > 0 && !!parts.rotor;
    const lifts = (anim.lift?.meters ?? 0) > 0 && parts.lifts.length > 0;
    const animate = (spins || lifts) && !prefersReducedMotion();
    useAmbientFrames(animate);

    const t = useRef(0);
    useFrame((_, dt) => {
      if (!animate) return;
      t.current += Math.min(dt, 0.1); // fon tabidan qaytganda sakrab ketmasin
      if (spins && parts.rotor) parts.rotor.rotation.y = ((t.current * Math.PI * 2) / anim.secondsPerTurn!) % (Math.PI * 2);
      if (lifts && anim.lift) {
        const { meters, seconds, stagger = 0 } = anim.lift;
        parts.lifts.forEach(({ node, y0 }, i) => {
          node.position.y = y0 + meters * liftProgram(((t.current - i * stagger) / seconds) % 1);
        });
      }
    });
    return <primitive object={root} />;
  }
  Model.preload = () => useGLTF.preload(url);
  return Model;
}

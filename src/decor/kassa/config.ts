import { KASSA } from '../../map/config/kassa';
import { defineDecor } from '../define';
import modelUrl from './model.glb?url';

/** Tepadagi katta raqam kartasi (masalan, "K-5"): qora fon, oq hoshiya, sariq raqam — xarita aylansa ham doim ko'ruvchiga qaragan */
const cardSvg = (id: string) => `data:image/svg+xml;charset=utf-8,${encodeURIComponent(
  `<svg xmlns="http://www.w3.org/2000/svg" width="512" height="320" viewBox="0 0 512 320">
  <rect x="10" y="10" width="492" height="300" rx="56" fill="#2b2b2d" stroke="#ffffff" stroke-width="16"/>
  <text x="256" y="92" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="64" font-weight="800" fill="#ffffff" letter-spacing="8">KASSA</text>
  <text x="256" y="272" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="190" font-weight="800" fill="#ffc20e">${id}</text>
</svg>`)}`;

/**
 * Kassa budkasi — fotosurat bo'yicha (attraction-images-park/kasa.png): krem plastik budka, qiya qirrali, old tomonda
 * ramkali kassa oynasi (ichida e'lonlar), QR stikerlar, tepasida qora "КАССА / GAZNA" belgisi (kechasi yonadi).
 * Ustida katta raqam kartasi (id, masalan "K-5") — har tomondan ko'rinadi.
 * Joylari — src/map/config/kassa.ts → KASSA (`at` berilganlari; pin ham o'sha yerdan). Model: model.py → model.glb.
 */
export default defineDecor(KASSA.filter((k) => k.at).map((k) => ({
  name: `Kassa ${k.id}`,
  at: k.at!,
  /** Oyna qaragan yo'nalish (berilmasa — janub) */
  bearing: k.bearing ?? 180,
  /** Asl o'lcham: 1.44 × 1.16 m (belgi bilan), balandligi 2.77 m */
  model: { url: modelUrl, natural: { width: 1.44, height: 2.77 } },
  /** Kattaligi — KASSA → scale (proporsiya saqlanadi) */
  ...(k.scale && k.scale !== 1 ? { size: { width: 1.44 * k.scale, height: 2.77 * k.scale } } : {}),
  /** Raqam kartasi: o'lchami, m va budka tepasidan balandligi */
  card: { url: cardSvg(k.id), width: 5.6, height: 3.5, lift: 0.6 },
  clearRadius: 1.5,
})));

// Ona va bola xonasi — xaritadagi bino (pin, qidiruv, "Xizmatlar" bo'limi, yurish rejimida to'siq).
// Shu fayldan `npm run build:genplan` park.json ga bino qo'shadi; ko'rinishi — shu papkadagi 3D model (config.ts).
import type { BuildingDef } from '../define';

export default {
  id: 'ona-bola-xonasi',
  name: 'Ona va bola xonasi',
  category: 'services',
  /** Markazi — park koordinatasi, metr (tibbiyot xonasi yonidagi maydon, pritsel: 39.4, 130.9) */
  at: [38.98, 130.7],
  /** Eshigi qaragan yo'nalish, gradus: janubi-g'arb — maydon tomonga */
  bearing: 233,
  /** Eni (old tomon bo'ylab) × chuqurligi, metr */
  width: 9,
  depth: 6.5,
  height: 4.8,
} satisfies BuildingDef;

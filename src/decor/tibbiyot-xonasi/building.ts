// Tibbiyot xonasi — xaritadagi bino (pin, qidiruv, "Xizmatlar" bo'limi, yurish rejimida to'siq).
// Shu fayldan `npm run build:genplan` park.json ga bino qo'shadi; ko'rinishi — shu papkadagi 3D model (config.ts).
// Avval shu joyda basseyn bo'lgan — bino ostida qolgan suv xaritadan olib tashlanadi.
import type { BuildingDef } from '../define';

export default {
  id: 'tibbiyot-xonasi',
  name: 'Tibbiyot xonasi',
  category: 'services',
  /** Markazi — park koordinatasi, metr (sobiq basseyn markazi) */
  at: [47.37, 135.39],
  /** Eshigi qaragan yo'nalish, gradus: shimoli-sharq — daryo bo'yidagi yo'lak */
  bearing: 53,
  /** Eni (old tomon bo'ylab) × chuqurligi, metr — sobiq basseyn o'lchami */
  width: 17.1,
  depth: 6.4,
  height: 5.2,
} satisfies BuildingDef;

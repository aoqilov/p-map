// Oqqushlar haykali — dam olish maskani (gulzor, haykal, skameykalar). Xaritadagi "bino": pin, qidiruv, "Dam olish" bo'limi,
// yurishda to'siq — faqat oval gulzor (skameykalar atrofidagi plitkada). Ko'rinishi — config.ts dagi 3D model.
// O'zgartirgach: npm run build:genplan
import type { BuildingDef } from '../define';

export default {
  id: 'oqqush-haykali',
  name: 'Oqqushlar haykali',
  category: 'fun',
  /** Gulzor markazi — park koordinatasi, metr */
  at: [-80.5, 202],
  /** Oqqushlar qaragan yo'nalish, gradus (#editor da burish mumkin) */
  bearing: 152,
  /** Oval gulzor: eni × chuqurligi, m (model.py → A, B — 2 × yarim o'qlari) */
  width: 10,
  depth: 9.5,
  /** Oqqush qanotlari tepasigacha */
  height: 3.9,
} satisfies BuildingDef;

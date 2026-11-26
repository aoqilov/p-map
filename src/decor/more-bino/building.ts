// "Море — Водный комплекс" (planda More_Bino): plandagi ikki bino o'z joyida qoladi (to'siq, bosish),
// faqat qutisi o'rniga shu papkadagi 3D model chiziladi (config.ts). O'zgartirgach: npm run build:genplan
import type { PlanModelDef } from '../define';

export default [
  /** Katta blok (62.9 × 14.5 m) — basseyn; kirishi g'arbga, kanal bo'yidagi yo'lakka. Pin — "Dam olish" bo'limida */
  { plan: 'building-136', at: [98.5, -86.69], bearing: 297.3, height: 9.5, name: 'Море — Водный комплекс (basseyn)', category: 'fun' },
  /** 2-blok (19.3 × 10.3 m), katta blokning shimoli-sharqida; eshigi yo'q (yashirin), pin chiqmaydi */
  { plan: 'building-137', at: [118.68, -44.99], bearing: 296.3, height: 9.5, name: 'Море — Водный комплекс (2-blok)' },
] satisfies PlanModelDef[];

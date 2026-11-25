// Merry Go Round — otli karusel — planda yo'q attraksion: joyi shu yerda. `npm run build:genplan` uni park.json ga attraksion sifatida
// qo'shadi (pin, qidiruv, tanlash, yurishda to'siq). Ko'rinishi — shu papkadagi 3D model (config.ts). Fayl faqat ma'lumot.
import type { AttractionPlaceDef } from '../define';

export default {
  /** Xaritadagi nomi — config.ts dagi planName bilan bir xil */
  name: 'Merry Go Round',
  /** Markazi — park koordinatasi, metr. Detskaya ploshchadka (30) panjarasi bo'ylab, Speedway bilan bolalar mashinalari orasida (diametri 8.4 m) */
  at: [10.29, 119.35],
  /** Old tomoni (kirish) — shimoli-g'arbga, yo'lakka. Uchala attraksion bir chiziqda, panjaraga parallel */
  bearing: 314.46,
  /** Maydoncha izi: eni (panjara bo'ylab) × chuqurligi, metr */
  width: 8.6,
  depth: 8.6,
  /** Eng baland joyi, metr */
  height: 5.9,
} satisfies AttractionPlaceDef;

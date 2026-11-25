// Speedway — bolalar jiplari oval yo'lda (6 ta jip) — planda yo'q attraksion: joyi shu yerda. `npm run build:genplan` uni park.json ga attraksion sifatida
// qo'shadi (pin, qidiruv, tanlash, yurishda to'siq). Ko'rinishi — shu papkadagi 3D model (config.ts). Fayl faqat ma'lumot.
import type { AttractionPlaceDef } from '../define';

export default {
  /** Xaritadagi nomi — config.ts dagi planName bilan bir xil */
  name: 'Speedway',
  /** Markazi — park koordinatasi, metr. Detskaya ploshchadka (30) shimoli-g'arbiy panjarasi bo'ylab, qatorning shimoli-sharqiy chetida (diametri 9.6 m) */
  at: [16.72, 127.05],
  /** Old tomoni (kirish) — shimoli-g'arbga, yo'lakka. Uchala attraksion bir chiziqda, panjaraga parallel */
  bearing: 314.46,
  /** Maydoncha izi: eni (panjara bo'ylab) × chuqurligi, metr */
  width: 9.8,
  depth: 9.8,
  /** Eng baland joyi, metr */
  height: 1.6,
} satisfies AttractionPlaceDef;

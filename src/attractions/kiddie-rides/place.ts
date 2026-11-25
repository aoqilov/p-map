// Kiddie Rides — 6 ta tanga bilan ishlaydigan bolalar mashinasi — planda yo'q attraksion: joyi shu yerda. `npm run build:genplan` uni park.json ga attraksion sifatida
// qo'shadi (pin, qidiruv, tanlash, yurishda to'siq). Ko'rinishi — shu papkadagi 3D model (config.ts). Fayl faqat ma'lumot.
import type { AttractionPlaceDef } from '../define';

export default {
  /** Xaritadagi nomi — config.ts dagi planName bilan bir xil */
  name: 'Kiddie Rides',
  /** Markazi — park koordinatasi, metr. Detskaya ploshchadka (30) panjarasi yonida, Vodnye gusenitsy (28) tomondagi chetida; mashinalar panjara bo'ylab bir qatorda */
  at: [6.91, 109.64],
  /** Old tomoni (kirish) — shimoli-g'arbga, yo'lakka. Uchala attraksion bir chiziqda, panjaraga parallel */
  bearing: 314.46,
  /** Maydoncha izi: eni (panjara bo'ylab) × chuqurligi, metr */
  width: 9.2,
  depth: 3.0,
  /** Eng baland joyi, metr */
  height: 1.75,
} satisfies AttractionPlaceDef;

// RC Park — planda yo'q attraksion: joyi shu yerda. `npm run build:genplan` uni park.json ga attraksion sifatida qo'shadi
// (pin, qidiruv, tanlash, yurishda to'siq); maydoncha ichidagi daraxtlar olib tashlanadi (boshqa daraxtlar joyida qoladi).
// Ko'rinishi — shu papkadagi 3D model (config.ts). Fayl faqat ma'lumot (.glb import qilinmaydi).
import type { AttractionPlaceDef } from '../define';

export default {
  /** Xaritadagi nomi — config.ts dagi planName bilan bir xil */
  name: 'RC Park',
  /**
   * Markazi — park koordinatasi, metr: Koleso obozreniya (47) g'arbidagi katta maysazorning shimoli-g'arbiy burchagi
   * (foydalanuvchi chizgan bino va ochiq zona; shimolda yo'l, g'arbda park chetidagi yo'l — ikkalasidan ~1 m ichkarida)
   */
  at: [-86.84, -16.26],
  /** Old tomoni (bino, kirish) — shimoliy yo'lga (yo'lga parallel) */
  bearing: 336,
  /** Maydoncha: eni (yo'l bo'ylab) × chuqurligi, metr */
  width: 32.5,
  depth: 24.8,
  /** Eng baland joyi (bino tomidagi pult antennasi), metr */
  height: 8.8,
} satisfies AttractionPlaceDef;

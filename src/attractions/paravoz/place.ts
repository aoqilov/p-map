// Paravoz — planda yo'q attraksion (relssiz park poyezdi): joyi shu yerda. `npm run build:genplan` uni park.json ga
// attraksion sifatida qo'shadi (pin, qidiruv, tanlash, yurishda to'siq). Ko'rinishi — shu papkadagi 3D model (config.ts).
import type { AttractionPlaceDef } from '../define';

export default {
  /** Xaritadagi nomi — config.ts dagi planName bilan bir xil */
  name: 'Paravoz',
  /**
   * Poyezd o'rtasi — park koordinatasi, metr (pritsel: -29.8, 82.6). Водные гусеницы (28) g'arbiy uchi bilan maysazor
   * orasidagi yo'lakda, yo'lak bo'ylab; Baby Car yo'lidan ~1.5 m chetda (pritseldan 3 m shimoli-sharqda)
   */
  at: [-28.57, 85.51],
  /** Lokomotiv oldi — janubi-g'arbga, chorraha tomonga; poyezd yo'lak bo'ylab (shimoli-sharq – janubi-g'arb) */
  bearing: 221.3,
  /** Maydoncha: eni × uzunligi (lokomotiv + 3 vagon), metr */
  width: 1.8,
  depth: 12.4,
  /** Eng baland joyi (vagon tomidagi ustqurma), metr */
  height: 2.6,
} satisfies AttractionPlaceDef;

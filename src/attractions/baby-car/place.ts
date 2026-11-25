// Baby Car — planda yo'q attraksion (ijara bolalar elektromashinalari): joyi shu yerda. `npm run build:genplan` uni park.json ga
// attraksion sifatida qo'shadi (pin, qidiruv, tanlash, yurishda to'siq). Ko'rinishi — shu papkadagi 3D model (config.ts).
import type { AttractionPlaceDef } from '../define';

export default {
  /** Xaritadagi nomi — config.ts dagi planName bilan bir xil */
  name: 'Baby Car',
  /** Markazi — park koordinatasi, metr (pritsel: -44.3, 79.9): maysazor chetidan ~1 m, yo'lak tomonda */
  at: [-44.2, 80.0],
  /** Mashinalar oldi — yo'lakka (shimoli-sharq); orqasi maysazor chetiga, qator chet bo'ylab (janubi-sharq – shimoli-g'arb) */
  bearing: 41.8,
  /** Maydoncha: eni (qator bo'ylab) × chuqurligi, metr */
  width: 4.4,
  depth: 1.7,
  /** Eng baland joyi (bagi ramasi), metr */
  height: 1.4,
} satisfies AttractionPlaceDef;

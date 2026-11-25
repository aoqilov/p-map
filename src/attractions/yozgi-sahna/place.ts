// Yozgi sahna (dam olish maskani) — planda yo'q attraksion: joyi shu yerda. `npm run build:genplan` uni park.json ga
// attraksion sifatida qo'shadi (pin, qidiruv, tanlash, yurishda to'siq). Ko'rinishi — shu papkadagi 3D model (config.ts).
// Oldidagi skameykalar — alohida bezak: src/decor/sahna-skameykalari. Fayl faqat ma'lumot (.glb import qilinmaydi).
import type { AttractionPlaceDef } from '../define';

export default {
  /** Xaritadagi nomi — config.ts dagi planName bilan bir xil */
  name: 'Yozgi sahna',
  /** Maydoncha markazi — park koordinatasi, metr (pritsel: 15.4, 170.8; maysazorlardan ~1 m uzoqda) */
  at: [15.6, 171.4],
  /** Sahna old tomoni — janubi-g'arbga, skameykalar tomonga */
  bearing: 223,
  /** Maydoncha izi: eni (old tomon bo'ylab) × chuqurligi, metr — model shunga sig'adi (17.5 × 8.1 m) */
  width: 18,
  depth: 9,
  /** Soyabon tepasi, metr */
  height: 6.8,
} satisfies AttractionPlaceDef;

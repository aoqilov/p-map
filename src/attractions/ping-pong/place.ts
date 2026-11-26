// Ping pong — planda yo'q attraksion: joyi shu yerda beriladi. `npm run build:genplan` uni park.json ga attraksion sifatida
// qo'shadi (pin, qidiruv, tanlash, yurishda to'siq). Ko'rinishi — shu papkadagi 3D model (config.ts).
// Fayl faqat ma'lumot: Node (build-genplan) ham, brauzer ham o'qiydi — shuning uchun bu yerda .glb import qilinmaydi.
import type { AttractionPlaceDef } from '../define';

export default {
  /** Xaritadagi nomi — config.ts dagi planName bilan bir xil */
  name: 'Ping pong',
  /** To'rtala stolning o'rtasi — park koordinatasi, metr (2D setka tahrirlagichda tanlangan) */
  at: [-40.5, 171.5],
  /** Stollarning uzun tomoni qaragan yo'nalish, gradus (140 — janubi-sharq). Qator unga perpendikulyar: shimoli-sharq – janubi-g'arb */
  bearing: 140,
  /** Maydoncha: qator bo'ylab eni (4 stol: 3 × 5 m + 1.84 m + chetlari) va stol uzun tomoni bo'ylab chuqurligi, metr */
  width: 19,
  depth: 4.8,
  /** Stol balandligi (to'r ustunlari bilan, plita ustida) — pin va yuklanguncha ko'rinadigan quti uchun, metr */
  height: 1.12,
} satisfies AttractionPlaceDef;

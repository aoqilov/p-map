import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';

/**
 * 29 — Аттракцион "Junior jet 6". Model: model.py (Blender skripti) → model.glb
 * Asl o'lcham: supa diametri 8.6 m, balandligi 5.5 m. Plandagi doira diametri ~7.3 m
 * (planda doira ikki bo'lakka bo'lingan edi — explication.py → MERGE_PADS bitta doiraga birlashtiradi).
 */
export default defineAttraction({
  num: '29',
  name: 'Junior jet 6',
  model: { url: modelUrl, natural: { width: 8.6, height: 5.5 } },
  /**
   * Xaritadagi o'lchami, metr. width — supa diametri, height — balandligi.
   * Nisbatni saqlang (height = width × 5.5 / 8.6), aks holda model cho'ziladi. Asl o'lchami uchun — shu qatorni o'chiring
   */
  size: { width: 7.3, height: 4.7 },
  /** Kirish/chiqish (yashil yozuvlar) — janub. Aylana maydonchada faqat kirish tomoni muhim */
  bearing: 180,
  anim: {
    /** Ustun va samolyotlar aylanishi, bir aylanish soniyada (0 — to'xtagan) */
    secondsPerTurn: 9,
    /**
     * Samolyotlar ko'tariladi: necha gradus, sikl soniya (pastda → ko'tarilish → tepada → tushish),
     * stagger — har bir keyingi samolyot necha soniya kech (0 — hammasi birga). degrees: 0 — o'chiq
     */
    tilt: { degrees: 30, seconds: 10, stagger: 1.7 },
  },
});

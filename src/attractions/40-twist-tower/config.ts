import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';

/**
 * 40 — Аттракцион "Twist tower" (Drop'N'Twist). Model: model.py (Blender skripti) → model.glb
 * Asl o'lcham: supa diametri 8.7 m, balandligi 23.9 m (gumbaz bilan). Plandagi doira diametri ~9 m.
 */
export default defineAttraction({
  num: '40',
  name: 'Twist tower',
  model: { url: modelUrl, natural: { width: 8.74, height: 23.85 } },
  /**
   * Xaritadagi o'lchami, metr. width — supa diametri, height — balandligi.
   * Nisbatni saqlang (height = width × 23.85 / 8.74), aks holda model cho'ziladi. Asl o'lchami uchun — shu qatorni o'chiring
   */
  size: { width: 19.0, height: 34.56 },
  /** Zina (panjaradagi ochiq joy) — janub tomonda */
  bearing: 180,
  anim: {
    /**
     * O'rindiqli halqa minora bo'ylab ko'tariladi: necha metr, sikl soniya (pastda turish → ko'tarilish → tepada →
     * tushish). meters: 0 — o'chiq
     */
    lift: { meters: 15, seconds: 30 },
    /** Halqa aylanishi (ko'tarilayotganda ham): daqiqasiga aylanish */
    spin: { rpm: 5 },
  },
});

import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';

/**
 * 34 — Аттракцион "Swing 20" (barokko uslubidagi zanjirli karusel). Model: model.py (Blender skripti) → model.glb
 * Asl o'lcham: panjara diametri 9.8 m, balandligi 6.1 m. Plandagi doira diametri ~8.4 m.
 */
export default defineAttraction({
  num: '34',
  name: 'Swing 20',
  model: { url: modelUrl, natural: { width: 9.8, height: 6.1 } },
  /**
   * Xaritadagi o'lchami, metr. width — panjara diametri, height — balandligi.
   * Nisbatni saqlang (height = width × 6.1 / 9.8), aks holda model cho'ziladi. Asl o'lchami uchun — shu qatorni o'chiring
   */
  size: { width: 8.4, height: 5.2 },
  /** Kirish (panjaradagi ochiq joy) — janub */
  bearing: 180,
  anim: {
    /** Soyabon va o'rindiqlar aylanishi, bir aylanish soniyada (0 — to'xtagan) */
    secondsPerTurn: 8,
    /** O'rindiqlar tashqariga og'adi (lean, gradus) va yengil tebranadi (degrees, period). lean > 20 — panjaraga yetadi */
    swing: { degrees: 3, period: 2.4, cycle: 0, stagger: 0.3, lean: 15 },
  },
});

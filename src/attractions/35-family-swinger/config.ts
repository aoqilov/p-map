import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';

/**
 * 35 — Аттракцион "Family swinger" (savatchali zanjirli karusel). Model: model.py (Blender skripti) → model.glb
 * Asl o'lcham: soyabon diametri 9.3 m, balandligi 8.7 m. Plandagi doira diametri ~16 m — savatlar aylanganda
 * tashqariga uchib chiqadi, shuning uchun soyabon doiradan ancha kichik.
 */
export default defineAttraction({
  num: '35',
  name: 'Family swinger',
  model: { url: modelUrl, natural: { width: 9.3, height: 8.7 } },
  /**
   * Xaritadagi o'lchami, metr. width — soyabon diametri, height — balandligi.
   * Nisbatni saqlang (height = width × 8.7 / 9.3), aks holda model cho'ziladi. Asl o'lchami uchun — shu qatorni o'chiring
   */
  size: { width: 11.0, height: 10.3 },
  bearing: 180,
  anim: {
    /** Soyabon va savatlar aylanishi, bir aylanish soniyada (0 — to'xtagan) */
    secondsPerTurn: 7,
    /** Savatlar tashqariga og'adi (lean, gradus) va yengil tebranadi (degrees, period) */
    swing: { degrees: 3, period: 2.6, cycle: 0, stagger: 0.3, lean: 22 },
  },
});

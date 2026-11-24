import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';

/**
 * 25 — Аттракцион "Slide M 350" (ko'p yo'lakli to'lqinli tepalik). Model: model.py (Blender skripti) → model.glb
 * Asl o'lcham: 37.1 × 6.6 m, start maydonchasi 8.5 m, chiroqlar bilan 11.85 m. Plandagi maydoncha ~37.7 × 6.0 m.
 */
export default defineAttraction({
  num: '25',
  name: 'Slide M 350',
  model: { url: modelUrl, natural: { width: 37.1, height: 11.85 } },
  /**
   * Xaritadagi o'lchami, metr. width — uzunligi, height — balandligi (chiroqlar bilan).
   * Nisbatni saqlang (height = width × 11.85 / 37.1), aks holda model cho'ziladi. Asl o'lchami uchun — shu qatorni o'chiring
   */
  size: { width: 37.1, height: 11.85 },
  /**
   * Tushish uchi qaragan yo'nalish: 202 — janubi-janubi-g'arb (start minorasi shimoliy uchida, Galleon tomonda).
   * Teskari kerak bo'lsa — 22
   */
  bearing: 202,
});

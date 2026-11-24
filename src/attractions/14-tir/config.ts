import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';

/**
 * 14 — Тир (otish joyi), "Wild West" uslubidagi yog'och bino. Model: model.py (Blender skripti) → model.glb
 * Genplan'da bino edi — 3D model qo'yish uchun explication.py da attraksion qilingan (PAD_AT — plandagi bino o'rni).
 * Asl o'lcham: 8.9 × 7.5 m (shag'al, pandus, temir yo'l bilan), balandligi 4.5 m. Plandagi maydoncha ~7.0 × 6.7 m.
 */
export default defineAttraction({
  num: '14',
  name: 'Тир',
  model: { url: modelUrl, natural: { width: 8.9, height: 4.5 } },
  /**
   * Xaritadagi o'lchami, metr. width — eng keng tomoni, height — balandligi.
   * Nisbatni saqlang (height = width × 4.5 / 8.9), aks holda model cho'ziladi. Asl o'lchami uchun — shu qatorni o'chiring
   */
  size: { width: 9.5, height: 4.8 },
  /**
   * Old tomoni ("TIR" peshtoq, pandus) — yon yo'lka tomonga (shimoli-sharq). Uzun fasad yo'lka bo'ylab turadi.
   * Maydoncha ~45° burilgan kvadrat: boshqa tomonga qaratish uchun 134, 224 yoki 314 (karusel tomoni)
   */
  bearing: 44,
});

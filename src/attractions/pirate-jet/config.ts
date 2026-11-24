import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';

/**
 * Pirate jet — planda raqamsiz attraksion (plandagi nomi bo'yicha bog'lanadi). Model: model.py → model.glb
 * Asl o'lcham: diametri 9.3 m, balandligi 5.4 m (qaroqchi shlyapasi bilan). Plandagi doira diametri ~9.0 m.
 */
export default defineAttraction({
  /** Plandagi nomi (park.json → attractions[].name); gen plan raqami berilsa — `num` ga o'tkazing */
  planName: 'Pirate jet',
  name: 'Pirate jet',
  model: { url: modelUrl, natural: { width: 9.3, height: 5.4 } },
  /**
   * Xaritadagi o'lchami, metr. width — diametri, height — balandligi.
   * Nisbatni saqlang (height = width × 5.4 / 9.3), aks holda model cho'ziladi. Asl o'lchami uchun — shu qatorni o'chiring
   */
  size: { width: 9.0, height: 5.2 },
  /** Qaroqchi qaragan tomon — janub (aylana maydonchada faqat haykal yo'nalishi muhim) */
  bearing: 180,
  anim: {
    /** Kemachalar aylanishi, bir aylanish soniyada (0 — to'xtagan) */
    secondsPerTurn: 10,
    /** Kemachalar ko'tarilib-tushadi: gradus, sikl soniya, stagger — har bir keyingisi necha soniya kech */
    tilt: { degrees: 22, seconds: 9, stagger: 1.5 },
  },
});

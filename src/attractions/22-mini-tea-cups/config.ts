import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';

/**
 * 22 — Аттракцион "Mini tea cups". Model: model.py (Blender skripti) → model.glb
 * Asl o'lcham: panjara diametri 8.2 m, balandligi 3.1 m (choynak). Plandagi doira diametri ~10 m.
 */
export default defineAttraction({
  num: '22',
  name: 'Mini tea cups',
  model: { url: modelUrl, natural: { width: 8.2, height: 3.1 } },
  /**
   * Xaritadagi o'lchami, metr. width — panjara diametri, height — balandligi.
   * Nisbatni saqlang (height = width × 3.1 / 8.2), aks holda model cho'ziladi. Asl o'lchami uchun — shu qatorni o'chiring
   */
  size: { width: 10.0, height: 5.8 },
  /** Kirish/chiqish (yashil yozuvlar) — janub. Aylana maydonchada faqat kirish tomoni muhim */
  bearing: 180,
  anim: {
    /** Disk bir aylanishi necha soniyada (0 — aylanmaydi) */
    secondsPerTurn: 10,
    /** Piyolalar o'z o'qi atrofida: daqiqasiga aylanish (0 — to'xtagan) */
    spin: { rpm: 14 },
  },
});

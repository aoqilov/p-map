import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';

/**
 * 38 — Аттракцион "Galleon 42" (tebranuvchi kema). Model: model.py (Blender skripti) → model.glb
 * Asl o'lcham: 21.6 × 8.9 m (oyoqlar orasi × zinalar bilan), balandligi 17.5 m ("GALLEON" yozuvi bilan).
 * Plandagi maydoncha ~22 × 9.5 m.
 */
export default defineAttraction({
  num: '38',
  name: 'Galleon 42',
  model: { url: modelUrl, natural: { width: 21.6, height: 17.5 } },
  /**
   * Xaritadagi o'lchami, metr. width — oyoqlar orasi (kema tebranadigan yo'nalish), height — balandligi.
   * Nisbatni saqlang (height = width × 17.5 / 21.6), aks holda model cho'ziladi. Asl o'lchami uchun — shu qatorni o'chiring
   */
  size: { width: 21.6, height: 17.5 },
  /**
   * Kema burni qaragan yo'nalish (uzun o'qi plandagi maydoncha bo'ylab, ~47°/227°). 227 da zinalar va yozuv —
   * shimoli-g'arbga (charxpalak tomonga); teskari tomonga kerak bo'lsa — 47
   */
  bearing: 227,
  anim: {
    /**
     * Kema tebranishi: eng katta og'ish (gradus), bir tebranish (oldinga-orqaga) soniya, seans soniya
     * (tinch turadi → asta kuchayadi → eng baland → sekinlashib to'xtaydi). degrees: 0 — o'chiq
     */
    swing: { degrees: 60, period: 6.5, cycle: 50 },
  },
});

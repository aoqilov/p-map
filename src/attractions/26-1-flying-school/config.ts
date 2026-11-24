import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';

/**
 * 26.1 — Аттракцион "Flying school". Model: model.py (Blender skripti) → model.glb
 * Asl o'lcham: supa 8.4 × 7.0 m, balandligi 7.2 m. Plandagi maydoncha 6.0 × 5.0 m (nisbati bir xil — 6 : 5).
 */
export default defineAttraction({
  num: '26.1',
  name: 'Flying school',
  model: { url: modelUrl, natural: { width: 8.4, height: 7.2 } },
  /**
   * Xaritadagi o'lchami, metr. width — supaning uzun tomoni, height — balandligi.
   * Nisbatni saqlang (height = width × 7.2 / 8.4), aks holda model cho'ziladi. Asl o'lchami uchun — shu qatorni o'chiring
   */
  size: { width: 7.0, height: 6.1 },
  /** Old tomoni (kirish/chiqish, pult) — janubga; uzun o'qi plandagi maydoncha bo'ylab (~76°). Teskari bo'lsa — 346 */
  bearing: 166,
  anim: {
    /**
     * Samolyotlar: eng katta og'ish (gradus), bir tebranish soniya, seans soniya (tinch → kuchayadi → so'nadi).
     * stagger — ikkinchi samolyot shuncha soniya kech (period / 2 — qarama-qarshi tebranadi)
     */
    swing: { degrees: 50, period: 5, cycle: 40, stagger: 2.5 },
  },
});

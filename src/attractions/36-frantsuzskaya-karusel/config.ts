import { defineAttraction } from "../define";
import modelUrl from "./model.glb?url";

/**
 * 36 — Аттракцион "Французская карусель" (Central carousel) — park ramzi. Model: model.py (Blender skripti) → model.glb
 * Asl o'lcham: panjara diametri 15.2 m, balandligi 7.9 m (shpil bilan). Plandagi doira diametri ~15 m.
 */
export default defineAttraction({
  num: "36",
  name: "Central carousel",
  model: { url: modelUrl, natural: { width: 15.2, height: 7.9 } },
  /**
   * Xaritadagi o'lchami, metr. width — panjara diametri, height — balandligi (shpil uchigacha).
   * Nisbatni saqlang (height = width × 7.9 / 15.2), aks holda model cho'ziladi. Asl o'lchami uchun — shu qatorni o'chiring
   */
  size: { width: 23.0, height: 12.8 },
  /** Zinapoya (panjaradagi ochiq joy) — janub */
  bearing: 180,
  anim: {
    /** Karusel bir aylanishi necha soniyada (0 — aylanmaydi). Soat strelkasiga teskari */
    secondsPerTurn: 16,
    /**
     * Otlar ko'tarilib-tushadi: metr, sikl soniya. Otlar 3 guruhda (lift0..2) — stagger: har bir keyingi guruh
     * necha soniya kech (seconds / 3 — navbatma-navbat). meters: 0 — o'chiq
     */
    lift: { meters: 0.3, seconds: 4.5, stagger: 1.5 },
  },
});

// 30 — Детская площадка: jihozlar modeli, joylashuvi va animatsiyasi.
// Model: equipment.py (Blender) → equipment.glb (ichida item_<nom> tugunlari). Joylashuv: layout.json
// (scripts/genplan/playground_layout.py yaratadi, qo'lda ham o'zgartirsa bo'ladi).
import type { GltfAnimation } from "../../map/GltfModel";
import layout from "./layout.json";
import modelUrl from "./equipment.glb?url";

export const PLAYGROUND_MODEL = modelUrl;

export interface PlaygroundItem {
  name: string;
  /** Park metrlari: x — sharq, y — shimol */
  x: number;
  y: number;
  /** Burilish, gradus (soat teskarisiga) */
  rot: number;
}

export const PLAYGROUND_ITEMS = layout.items as PlaygroundItem[];

/** Jihoz nomi → animatsiya (qiymatlarni o'zgartirsangiz, xarita darhol yangilanadi). Ro'yxatda yo'qlari qimirlamaydi */
export const PLAYGROUND_ANIM: Record<string, GltfAnimation> = {
  /** Aylanuvchi platforma: daqiqasiga aylanish */
  spinning_platform: { spin: { rpm: 9 } },
  /** Arqon konus */
  spinning_cone: { spin: { rpm: 6 } },
  /** Ikki savatli arg'imchoq: og'ish (gradus), bir tebranish (s), seans (0 — doim), stagger — ikkinchisi necha soniya kech */
  nest_swing: { swing: { degrees: 28, period: 3.2, cycle: 0, stagger: 1.1 } },
  /** Qo'sh arg'imchoq (seesaw): ikkalasi navbat bilan */
  seesaw: { swing: { degrees: 14, period: 2.6, cycle: 0, stagger: 1.3 } },
  /** Prujinali o'yinchoqlar: yengil chayqalish */
  spring_rider: { swing: { degrees: 9, period: 1.6, cycle: 0, stagger: 0.5 } },
};

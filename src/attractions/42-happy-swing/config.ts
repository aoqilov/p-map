import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';

/**
 * 42 — Аттракцион "Happy swing". Model: model.py (Blender skripti) → model.glb
 * Planda shakli chizilmagan — maydoncha 6 × 6 m standart (yozuv nuqtasida).
 */
export default defineAttraction({
  num: '42',
  name: 'Happy Swing',
  model: { url: modelUrl, natural: { width: 4.8, height: 6.2 } },
  /** Old tomoni (o'rindiqlar qaragan) — janub; arg'imchoq shimol–janub bo'ylab tebranadi */
  bearing: 180,
  anim: {
    /**
     * Arg'imchoq: eng katta og'ish (gradus), bir tebranish (oldinga-orqaga) necha soniya, seans necha soniya.
     * Seans: tinch turadi → asta kuchayadi → eng katta tebranish → sekinlashib to'xtaydi. degrees: 0 — o'chiq
     */
    swing: { degrees: 55, period: 4.5, cycle: 40 },
  },
});

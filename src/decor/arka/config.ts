import { defineDecor } from '../define';
import modelUrl from './model.glb?url';

/**
 * Arka — sharshara boshidagi yarim aylana g'isht arkada (5 ta uchli ravoq, panjara, tosh pol).
 * Botiq (old) tomoni maydonga, orqasi sharsharaga. Model: model.py → model.glb. Asl o'lcham: eni ~10.6 m, balandligi 5.47 m. Pin va to'siq yo'q (faqat bezak).
 */
export default defineDecor({
  name: 'Arka',
  /** Yoy o'rtasi (orqa devor) — sharshara boshidan 0.6 m maydon tomonda (pritsel: -104.7, 144.3) */
  at: [-104.51, 144.94],
  model: { url: modelUrl, natural: { width: 10.6, height: 5.47 } },
  /** Old tomoni — maydonga (sharsharaga teskari: 136.8 + 180) */
  bearing: 316.8,
});

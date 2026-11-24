import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';

/**
 * 41 — Аттракцион "Jumping star 6" (Jumpin' Star). Model: model.py (Blender skripti) → model.glb
 * Maydonchasi plandagi 41 yozuvidan ~28 m g'arbda (scripts/genplan/explication.py → PAD_AT).
 */
export default defineAttraction({
  num: '41',
  name: "Jumpin' Star",
  model: { url: modelUrl, natural: { width: 4.8, height: 10.5 } },
  /** Old tomoni (o'rindiqlar) shimolga — eng yaqin yo'l shu tomonda, maydoncha qirralariga ham mos */
  bearing: 0,
  anim: {
    /**
     * O'rindiqli arava minora bo'ylab ko'tariladi: necha metr, to'liq sikl necha soniya
     * (pastda turish → ko'tarilish → tepada turish → tushish). meters: 0 — o'chiq
     */
    lift: { meters: 3.2, seconds: 9 },
  },
});

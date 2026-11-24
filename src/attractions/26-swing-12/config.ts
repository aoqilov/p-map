import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';

/**
 * 26 — Аттракцион "Swing 12" (daraxt-arg'imchoq). Model: model.py (Blender skripti) → model.glb
 * Planda shakli 6 × 6 m standart maydoncha; plandagi aylana belgisi (nomsiz bino) olib tashlangan — explication.py → DROP_AT.
 */
export default defineAttraction({
  num: '26',
  name: 'Swing 12',
  model: { url: modelUrl, natural: { width: 6.0, height: 4.7 } },
  /** Kirish (panjaradagi ochiq joy) — janub */
  bearing: 180,
  anim: {
    /** Toj va o'rindiqlar aylanishi, bir aylanish soniyada (0 — to'xtagan) */
    secondsPerTurn: 7,
    /** O'rindiqlar tashqariga og'adi (lean, gradus) va yengil tebranadi (degrees, period) */
    swing: { degrees: 4, period: 2.2, cycle: 0, stagger: 0.4, lean: 18 },
  },
});

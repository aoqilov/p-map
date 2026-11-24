import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';

/**
 * 33 — Аттракцион "Gameland" (o'yin zali binosi). Model: model.py (Blender skripti) → model.glb
 * Plandagi nomsiz bino (23.9 × 10.7 m) shu raqamga bog'langan — explication.py → PAD_AT.
 */
export default defineAttraction({
  num: '33',
  name: 'Gameland',
  model: { url: modelUrl, natural: { width: 24.1, height: 8.4 } },
  /**
   * Kirish ("GAMELAND" fronton, eshik) — qisqa tomonda. 78 — sharqi (plandagi 33 yozuvi shu tomonda),
   * 258 — g'arb (coaster tomonga). Uzun o'qi plandagi bino bo'ylab
   */
  bearing: 258,
});

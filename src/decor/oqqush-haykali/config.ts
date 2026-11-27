import { defineDecor } from '../define';
import building from './building';
import modelUrl from './model.glb?url';

/**
 * Oqqushlar haykali — fotosuratlar bo'yicha: oval gulzor (magnoliya, paporotnik, lilyalar), to'q kulrang postament,
 * oq to'lqinsimon ko'pik ustida ikki oq oqqush (biri qanotlarini yoygan); orqasida skameykalar va axlat qutilari.
 * Joyi, burilishi, izi va pin — building.ts da. Model: model.py → model.glb.
 * Model origin — gulzor markazi; skameykalar gulzor chetidan tashqarida, orqa tomonda (+Y).
 */
export default defineDecor({
  name: building.name,
  at: building.at,
  bearing: building.bearing,
  /** Asl o'lcham: skameykalar bilan eni 11.06 m, balandligi 3.88 m */
  model: { url: modelUrl, natural: { width: 11.06, height: 3.88 } },
  clearRadius: 0,
});

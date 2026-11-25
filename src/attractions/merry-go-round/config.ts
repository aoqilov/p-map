import { defineAttraction } from '../define';
import place from './place';
import modelUrl from './model.glb?url';

/**
 * Merry Go Round — planda raqamsiz attraksion: tilla rang otli karusel (toj, rangli panellar, 12 ta ot, panjara).
 * Rasm: attraction-images-park/Merry_Go_Round.png. Joyi va maydoncha izi — place.ts (o'zgartirgach: npm run build:genplan).
 * Model: model.py → model.glb. Asl o'lcham: diametri 8.4 m, balandligi 5.9 m (shpil bilan).
 */
export default defineAttraction({
  planName: place.name,
  name: place.name,
  model: { url: modelUrl, natural: { width: 8.4, height: 5.9 } },
  /** Kirish — yo'lak tomonda (place.ts) */
  bearing: place.bearing,
  anim: {
    /** Bir aylanish, soniya */
    secondsPerTurn: 14,
    /** Otlar 3 guruhda navbat bilan ko'tarilib-tushadi: metr, sikl soniya, guruhlar orasidagi kechikish */
    lift: { meters: 0.25, seconds: 4.2, stagger: 1.4 },
  },
});

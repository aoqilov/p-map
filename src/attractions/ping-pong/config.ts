import { defineAttraction } from '../define';
import place from './place';
import modelUrl from './model.glb?url';

/**
 * Ping pong — planda raqamsiz attraksion (plandagi nomi bo'yicha bog'lanadi): to'rtta beton stol tennisi stoli yonma-yon,
 * yashil maydonchada. Joyi, burilishi va maydoncha izi — place.ts da (o'zgartirgach: npm run build:genplan).
 * Model: model.py (Blender skripti) → model.glb. Asl o'lcham: 18.9 × 4.7 m, balandligi 1.12 m.
 */
export default defineAttraction({
  /** Plandagi nomi (park.json → attractions[].name) — place.ts dagi nom */
  planName: place.name,
  name: place.name,
  model: { url: modelUrl, natural: { width: 18.9, height: 1.12 } },
  /** Stollarning uzun tomoni qaragan yo'nalish (place.ts) */
  bearing: place.bearing,
});

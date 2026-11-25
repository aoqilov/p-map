import { defineAttraction } from '../define';
import place from './place';
import modelUrl from './model.glb?url';

/**
 * Yozgi sahna (dam olish maskani) — planda raqamsiz attraksion (plandagi nomi bo'yicha bog'lanadi): oq bandshell,
 * oltin rozetkali soyabon, LED ekran, ikki yonida qanotlar va zinapoyalar. Oldidagi skameykalar — src/decor/sahna-skameykalari.
 * Joyi, burilishi va maydoncha izi — place.ts da (o'zgartirgach: npm run build:genplan).
 * Model: model.py (Blender skripti) → model.glb. Asl o'lcham: eni 17.5 m, chuqurligi 8.1 m, balandligi 6.8 m.
 */
export default defineAttraction({
  /** Plandagi nomi (park.json → attractions[].name) — place.ts dagi nom */
  planName: place.name,
  name: place.name,
  model: { url: modelUrl, natural: { width: 17.5, height: 6.8 } },
  /** Old tomoni (place.ts) */
  bearing: place.bearing,
});

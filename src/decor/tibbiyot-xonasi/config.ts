import { defineDecor } from '../define';
import building from './building';
import modelUrl from './model.glb?url';

/**
 * Tibbiyot xonasi — sobiq basseyn o'rnidagi oq bino (qizil xoch, pandus).
 * Joyi, burilishi va xaritadagi izi — building.ts da (pin, qidiruv va to'siq ham shundan; o'zgartirgach: npm run build:genplan).
 * Model: model.py (Blender skripti) → model.glb. Asl o'lcham: eni 17.1 m, balandligi 5.17 m.
 */
export default defineDecor({
  name: building.name,
  at: building.at,
  bearing: building.bearing,
  model: { url: modelUrl, natural: { width: 17.1, height: 5.17 } },
});

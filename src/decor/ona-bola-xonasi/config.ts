import { defineDecor } from '../define';
import building from './building';
import modelUrl from './model.glb?url';

/**
 * Ona va bola xonasi — yashil uycha (ona va bola belgisi, aravacha uchun pandus).
 * Joyi, burilishi va xaritadagi izi — building.ts da (pin, qidiruv va to'siq ham shundan; o'zgartirgach: npm run build:genplan).
 * Model: model.py (Blender skripti) → model.glb. Asl o'lcham: eni 9.0 m, balandligi 4.71 m.
 */
export default defineDecor({
  name: building.name,
  at: building.at,
  bearing: building.bearing,
  model: { url: modelUrl, natural: { width: 9.0, height: 4.71 } },
});

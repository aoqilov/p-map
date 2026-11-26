import { defineDecor } from '../define';
import place from './building';
import modelUrl from './model.glb?url';

/**
 * Кафе "Замок эльфов" — fotosurat bo'yicha: shisha pavilon, tepasida kulrang beton quti, zang-sariq metall fermali
 * yog'och soyabon, old va chap tomonda bannerli to'siq. Joyi va izi — building.ts da. Model: model.py → model.glb.
 */
export default defineDecor({
  name: 'Кафе "Замок эльфов"',
  at: place.at,
  bearing: place.bearing,
  /** Asl o'lcham: 19 × 10 m (izga aynan teng), balandligi 7.04 m */
  model: { url: modelUrl, natural: { width: 19, height: 7.04 } },
  clearRadius: 0,
});

import { defineDecor } from '../define';
import building from './building';
import modelUrl from './model.glb?url';

/**
 * Eski sharshara — foydalanuvchi fotosurati bo'yicha: yarim doira granit bordyur, mozaika kosa (bronza baliqlar),
 * orqada pog'onali qoyalar va ikkita yotgan bronza kiyik. Joyi — building.ts da. Model: model.py → model.glb.
 * Sharshara to'xtatilgan: suv yo'q, kosa ichi quruq tuproq va o't.
 */
export default defineDecor({
  name: building.name,
  at: building.at,
  bearing: building.bearing,
  /** Asl o'lcham: eng keng joyi 13.7 m, balandligi 4.04 m */
  model: { url: modelUrl, natural: { width: 13.7, height: 4.04 } },
  /** Xaritada izga moslab kattalashtirilgan (eni 17 m → ×1.24, chuqurligi ~14 m); bo'yi biroz kamroq (×1.11), kiyiklar cho'zilib ketmasin */
  size: { width: building.width, height: building.height },
  clearRadius: 0,
});

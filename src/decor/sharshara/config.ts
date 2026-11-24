import { defineDecor } from '../define';
import basins from './basins.json';
import building from './building';
import modelUrl from './model.glb?url';

/**
 * Sharshara — tekis yerdagi tosh pog'onali kaskad (relyef yo'q). Joyi va yo'nalishi — building.ts da.
 * Model: model.py → model.glb (`fall` — suv pardalari pastga oqadi; `water` — hovuzchalar, hovuz suvi shaderi bilan; Decor.tsx). Asl o'lcham: 7 × 22.4 m, ~2 m.
 */
export default defineDecor({
  name: building.name,
  at: building.at,
  bearing: building.bearing,
  model: { url: modelUrl, natural: { width: 22.4, height: 2.38 } },
  /** Suv pardalari oqimi: tekstura tezligi (m/s) */
  flow: { material: 'fall', speed: 0.9 },
  /** Hovuzchalardagi suv — katta hovuz bilan bir xil ko'rinishda (to'lqin, ko'pik, yaltiroq) */
  water: { material: 'water', basins: basins as { poly: [number, number][]; z: number }[] },
});

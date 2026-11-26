import { defineDecor } from '../define';
import place from './building';
import modelUrl from './model.glb?url';

/**
 * "EASY Box — casual food" — fotosurat bo'yicha: tosh plitkali devorlar, katta oynalar, shingl tom, uchta g'ishtli
 * mansard, qora "EASY Box" peshtaxtasi (kechasi yonadi), firuza osma belgi; oldida skameykalar va axlat qutilari.
 * Joyi — building.ts da. Model: model.py → model.glb (asl o'lchamda).
 */
export default defineDecor({
  name: place.name,
  at: place.at,
  bearing: place.bearing,
  /** Asl o'lcham: 13.15 m (osma belgi bilan), balandligi 6.85 m */
  model: { url: modelUrl, natural: { width: 13.15, height: 6.85 } },
  clearRadius: 0,
});

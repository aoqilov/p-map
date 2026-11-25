import { defineDecor } from '../define';
import places from './building';
import modelUrl from './model.glb?url';

/**
 * Burger uychasi — ertak do'kon-uycha (rasm: foydalanuvchi fotosuratlari). Plandagi binolar joyida (building.ts).
 * Model: model.py → model.glb (umumiy bo'laklar — ../domik_kit.py). Asl o'lcham: 4.0 × 3.6 m, balandligi 6.4 m.
 */
const W = 4.0, D = 3.6, H = 6.4;

/** Plandagi bino izi: [old tomon eni, chuqurligi], m — model shunga sig'adigan qilib kichraytiriladi */
const FOOTPRINT: Record<string, [number, number]> = {
  'n70': [4.22, 3.32],
  'n71': [2.73, 3.39],
};

// Planda ikki marta chizilgan bino (bir joyda) — model bitta
const unique = places.filter((p, i) => places.findIndex((q) => q.at[0] === p.at[0] && q.at[1] === p.at[1]) === i);

export default defineDecor(unique.map((pl) => {
  const [fw, fd] = FOOTPRINT[pl.plan];
  const s = Math.min(fw / W, fd / D);
  return {
    name: `Burger uychasi ${pl.plan}`,
    at: pl.at,
    bearing: pl.bearing,
    model: { url: modelUrl, natural: { width: W, height: H } },
    size: { width: W * s, height: H * s },
    clearRadius: 0,
  };
}));

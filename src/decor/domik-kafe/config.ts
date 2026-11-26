import { defineDecor } from '../define';
import places from './building';
import modelUrl from './model.glb?url';

/**
 * Kafe uychasi — ertak do'kon-uycha (rasm: foydalanuvchi fotosuratlari). Plandagi binolar joyida (building.ts).
 * Model: model.py → model.glb (umumiy bo'laklar — ../domik_kit.py). Asl o'lcham: 4.0 × 3.6 m, balandligi 5.65 m.
 */
const W = 4.0, D = 3.6, H = 5.65;

/** Plandagi bino izi: [old tomon eni, chuqurligi], m — model shunga sig'adigan qilib kichraytiriladi */
const FOOTPRINT: Record<string, [number, number]> = {
  'n69-1': [3.23, 3.32],
  'n69-2': [3.25, 3.33],
};

// Planda ikki marta chizilgan bino (bir joyda) — model bitta
const unique = places.filter((p, i) => places.findIndex((q) => q.at[0] === p.at[0] && q.at[1] === p.at[1]) === i);

export default defineDecor(unique.map((pl) => {
  // izi to'rtburchak qilib berilgan bo'lsa (#editor) — shu o'lcham, bo'lmasa — plandagi
  const [fw, fd] = 'rect' in pl && pl.rect ? [pl.rect.width, pl.rect.depth] : FOOTPRINT[pl.plan];
  const s = Math.min(fw / W, fd / D);
  return {
    name: `Kafe uychasi ${pl.plan}`,
    at: pl.at,
    bearing: pl.bearing,
    model: { url: modelUrl, natural: { width: W, height: H } },
    size: { width: W * s, height: H * s },
    clearRadius: 0,
  };
}));

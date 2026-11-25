import { defineDecor } from '../define';
import type { XY } from '../../map/projection';
import modelUrl from './model.glb?url';

/**
 * Yozgi sahna oldidagi skameykalar — suyanchiqli yog'och skameykalar (cho'yan oyoqli), qatorlab, sahnaga qaragan.
 * Sahna — attraksion: src/attractions/yozgi-sahna. Bitta model (model.py → model.glb), har bir skameyka — nusxa.
 * Asl o'lcham: uzunligi 3.0 m, balandligi 0.98 m. Pin va to'siq yo'q: yurish rejimida skameykalar orasidan o'tib bo'ladi.
 */

/** Skameykalar maydonining o'rtasi — park koordinatasi, metr (foydalanuvchi chizgan joy, sahnadan ~12 m janubi-g'arbda) */
const CENTER: XY = [0.2, 156.9];
/** O'tirganlar qaraydigan yo'nalish — sahnaga (shimoli-sharq), gradus */
const BEARING = 43;
/** Qatorlar soni va oralig'i (old qatordan orqaga), m */
const ROWS = 5;
const ROW_GAP = 2.0;
/** Qatordagi skameykalar o'rni (o'rtadan, qator bo'ylab), m: o'rtada va chetlarda ~1.6 m o'tish yo'li */
const COLS = [-6.9, -2.3, 2.3, 6.9];

const b = (BEARING * Math.PI) / 180;
const FWD: XY = [Math.sin(b), Math.cos(b)];       // sahnaga tomon
const SIDE: XY = [Math.cos(b), -Math.sin(b)];     // qator bo'ylab
const r2 = (v: number) => Math.round(v * 100) / 100;

export default defineDecor(
  Array.from({ length: ROWS }, (_, row) => COLS.map((c, col) => {
    const f = ((ROWS - 1) / 2 - row) * ROW_GAP; // 0-qator — sahnaga eng yaqin
    return {
      name: `Skameyka ${row + 1}-${col + 1}`,
      at: [r2(CENTER[0] + FWD[0] * f + SIDE[0] * c), r2(CENTER[1] + FWD[1] * f + SIDE[1] * c)] as XY,
      bearing: BEARING,
      model: { url: modelUrl, natural: { width: 3.0, height: 0.98 } },
      /** Atrofidagi daraxtlar o'chmasin (skameykalar daraxt ostida ham turishi mumkin) */
      clearRadius: 0,
    };
  })).flat(),
);

import { defineDecor, type DecorDef } from '../define';
import basins from './basins.json';
import building from './building';
import modelUrl from './model.glb?url';
import benchUrl from '../sahna-skameykalari/model.glb?url';

/**
 * Sharli fontan va atrofidagi dam olish joyi: granit havza (keng o'tiriladigan qirra, 8 ta postament ustida sharlar,
 * kichik favvoralar) va maydon chetida 4 ta skameyka (sahna skameykasi modeli). Joyi va to'siq — building.ts.
 * Atrofidagi katta daraxtlar — config/map.ts → TREE_GROVES. Model: model.py → model.glb. Asl o'lcham: diametri 10.1 m, balandligi 1.66 m.
 */
const fountain: DecorDef = {
  name: building.name,
  at: building.at,
  bearing: building.bearing,
  model: { url: modelUrl, natural: { width: 10.1, height: 1.66 } },
  /** Favvoralar — oqim teksturasi */
  flow: { material: 'jet', speed: 1.2 },
  /** Havza suvi — hovuz kabi (yashilroq) */
  water: { material: 'water', basins: basins as { poly: [number, number][]; z: number }[] },
};

/** Skameykalar: maydon markazidan masofasi, m va qaysi tomonlarda (gradus) — maysazorlar oldida, diagonal yo'laklar ochiq */
const BENCH_R = 6.9;
const BENCH_SIDES = [0, 90, 180, 270];

const benches: DecorDef[] = BENCH_SIDES.map((deg) => {
  const a = (deg * Math.PI) / 180;
  return {
    name: `Fontan skameykasi ${deg}`,
    at: [Math.round((building.at[0] + Math.sin(a) * BENCH_R) * 100) / 100, Math.round((building.at[1] + Math.cos(a) * BENCH_R) * 100) / 100],
    /** Fontanga qaragan */
    bearing: (deg + 180) % 360,
    model: { url: benchUrl, natural: { width: 3.0, height: 0.98 } },
    clearRadius: 0,
  };
});

export default defineDecor([fountain, ...benches]);

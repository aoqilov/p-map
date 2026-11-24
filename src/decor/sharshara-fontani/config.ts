import { defineDecor } from "../define";
import basins from "./basins.json";
import building from "./building";
import modelUrl from "./model.glb?url";

/**
 * Sharshara ostidagi fontan: qizil granit havza, o'rtada qirrali ustun ustida savat ko'targan ayol haykali, 12 ta suv yoyi,
 * maydon chetida 4 ta skameyka (burchaklari — model.py → BENCHES). Joyi — building.ts.
 * Model: model.py → model.glb. Asl o'lcham: skameykalar bilan 19 m, havza 10.4 m, balandligi 4.9 m.
 */
export default defineDecor({
  name: building.name,
  at: building.at,
  bearing: building.bearing,
  model: { url: modelUrl, natural: { width: 30, height: 14.91 } },
  size: { width: 39.0, height: 14.91 },
  /** Suv yoylari — pastga oqadi */
  flow: { material: "jet", speed: 1.6 },
  /** Havza suvi — basseyn kabi och (tubi och plitka) */
  water: {
    material: "water",
    basins: basins as { poly: [number, number][]; z: number }[],
    style: "pool",
  },
});

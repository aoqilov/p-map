// Sharshara ostidagi fontan — aylana maydon o'rtasida (pritsel: -82.4, 120.1). Havza — yurish rejimida to'siq (doira),
// pin yo'q. O'zgartirgach: npm run build:genplan
import type { BuildingDef } from "../define";

export default {
  id: "sharshara-fontani",
  name: "Fontan",
  /** Markazi — 2D setka tahrirlagichda tanlangan */
  at: [-79.5, 119.5],
  /** Model koordinatasi park bilan bir xil (+X — sharq, +Y — shimol) bo'lishi uchun 180 */
  bearing: 180,
  /** Havza diametri, metr (doira iz) */
  width: 15.4,
  depth: 15.4,
  shape: "circle",
  height: 14.91,
} satisfies BuildingDef;

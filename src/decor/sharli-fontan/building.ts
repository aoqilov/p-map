// Sharli fontan — dumaloq maydon o'rtasida (pritsel: -20.8, 129.9; maydon radiusi ~8.4 m, to'rt diagonal yo'lak).
// Havza — yurish rejimida to'siq (doira), pin yo'q. O'zgartirgach: npm run build:genplan
import type { BuildingDef } from '../define';

export default {
  id: 'sharli-fontan',
  name: 'Sharli fontan',
  /** Maydon markazi, metr */
  at: [-20.9, 129.95],
  /** Doira — burilish ahamiyatsiz; sharlar diagonal yo'laklardan siljigan holda turadi */
  bearing: 0,
  /** Havza tashqi diametri, metr */
  width: 10.1,
  depth: 10.1,
  shape: 'circle',
  height: 1.66,
} satisfies BuildingDef;

// Burger uychasi — plandagi "Французский домик" binolariga model (nomi va pin plandagidek, quti chizilmaydi).
// Uychalar plandagi joyidan ~3.3 m Детская площадка panjarasiga surilgan (orqasi panjaradan 1.2 m), eshigi — teskari,
// janubi-g'arbdagi katta maydonga. move: true — bino izi, pin va to'siq ham `at` ga ko'chadi. O'zgartirgach: npm run build:genplan
import type { PlanModelDef } from '../define';

export default [
  /** n70 */
  { plan: 'n70', at: [7.89, 46.59], bearing: 224.0, move: true },
  /** n71 */
  { plan: 'n71', at: [-3.62, 57.82], bearing: 224.8, move: true },
] satisfies PlanModelDef[];

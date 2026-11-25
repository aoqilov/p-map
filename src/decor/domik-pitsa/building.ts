// Pitsa uychasi — plandagi "Французский домик" binolariga model (nomi va pin plandagidek, quti chizilmaydi).
// Uychalar plandagi joyidan ~3.3 m Детская площадка panjarasiga surilgan (orqasi panjaradan 1.2 m), eshigi — teskari,
// janubi-g'arbdagi katta maydonga. move: true — bino izi, pin va to'siq ham `at` ga ko'chadi. O'zgartirgach: npm run build:genplan
import type { PlanModelDef } from '../define';

export default [
  /** n68-2 — eng keng uycha (5.9 × 3.4 m) */
  { plan: 'n68-2', at: [2.17, 52.08], bearing: 225.1, move: true },
] satisfies PlanModelDef[];

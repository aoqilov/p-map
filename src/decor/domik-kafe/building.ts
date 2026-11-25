// Kafe uychasi — plandagi "Французский домик" binolariga model (nomi va pin plandagidek, quti chizilmaydi).
// Uychalar plandagi joyidan ~3.3 m Детская площадка panjarasiga surilgan (orqasi panjaradan 1.2 m), eshigi — teskari,
// janubi-g'arbdagi katta maydonga. move: true — bino izi, pin va to'siq ham `at` ga ko'chadi. O'zgartirgach: npm run build:genplan
import type { PlanModelDef } from '../define';

export default [
  /** n69-1 — planda ikki marta chizilgan (n69-1-2), model bitta */
  { plan: 'n69-1', at: [-8.09, 62.23], bearing: 225.2, move: true },
  { plan: 'n69-1-2', at: [-8.09, 62.23], bearing: 225.2, move: true },
  /** n69-2 */
  { plan: 'n69-2', at: [11.39, 43.16], bearing: 224.6, move: true },
  /** n67 — boshqalardan janubda, alohida: joyida qoladi, faqat burilgan */
  { plan: 'n67', at: [7.65, 23.89], bearing: 65.7 },
] satisfies PlanModelDef[];

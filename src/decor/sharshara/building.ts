// Sharshara — plandagi yo'l o'rnida (kengligi ~7 m): izi yo'l plitkasidan kesiladi (ostida maysa), marshrut u orqali o'tmaydi,
// yurish rejimida to'siq. Pin yo'q (category berilmagan). O'zgartirgach: npm run build:genplan
// Foydalanuvchi belgilagan chiziq: (-104.1, 144.5) — boshi (eng baland pog'ona) → (-88.8, 128.2) — pastki hovuzcha.
import type { BuildingDef } from '../define';

export default {
  id: 'sharshara',
  name: 'Sharshara',
  /** Markazi — chiziq o'rtasi */
  at: [-96.45, 136.35],
  /** Suv oqib boradigan tomon (pastki hovuzcha), gradus. Teskari bo'lsin desangiz: 316.8 */
  bearing: 136.8,
  /** Eni × uzunligi, metr (eni — plandagi yo'ldan biroz keng, chetlarida plitka qolmasin) */
  width: 8,
  depth: 22.4,
  height: 2.0,
  cutPaving: true,
} satisfies BuildingDef;

// Eski sharshara — "Замок эльфов" kafesi yonidagi qoyali fontan (kiyik haykallari bilan). Planda bu yerda yo'l plitkasi
// chizilgan, aslida yo'l yo'q: izi plitkadan kesiladi (ostida maysa), marshrut o'tmaydi, yurishda to'siq. Pin yo'q.
// Joyi — foydalanuvchi skrinshotda belgilagan to'rtburchak (ikki ingichka maysa bo'lagi orasidagi yarim doira). O'zgartirgach: npm run build:genplan
import type { BuildingDef } from '../define';

export default {
  id: 'eski-sharshara',
  name: 'Eski sharshara',
  /** Markazi — park koordinatasi, metr */
  at: [-61.63, 166.71],
  /** Old tomoni (granit bordyur yoyi) — janubi-sharq, maydonga qaragan; orqasi (qoyalar) — shimoli-g'arbdagi to'g'ri yo'lak */
  bearing: 148,
  /** Eni × chuqurligi, metr (2D setka tahrirlagichda tanlangan; model.py asl o'lchami 13.7 × 11.5 — config.ts da kattalashtiriladi) */
  width: 17,
  depth: 14,
  /** O'ngdagi kiyik shoxi tepasigacha */
  height: 4.5,
  cutPaving: true,
} satisfies BuildingDef;

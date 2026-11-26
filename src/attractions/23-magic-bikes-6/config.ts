import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';

/** 23 — Аттракцион "Magic bikes 6". Model: model.py (Blender skripti) → model.glb */
export default defineAttraction({
  num: '23',
  name: 'Magic Bikes',
  model: { url: modelUrl, natural: { width: 9.0, height: 8.2 } },
  /** Old tomoni (kirish, yozuvlar) — shimol. Aylana maydonchada yo'nalish muhim emas */
  /** #editor da tanlangan (oldin 0) */
  bearing: 179,
  anim: {
    /** Bir aylanish necha soniyada (0 — aylanmaydi) */
    secondsPerTurn: 12,
    /** Savatlar yengil ko'tariladi: metr, sikl soniya, stagger — har biri necha soniya kech (0 — birga) */
    lift: { meters: 0.8, seconds: 10, stagger: 0 },
    /** Qo'l uchidagi parraklar: daqiqasiga aylanish (0 — to'xtagan) */
    spin: { rpm: 40 },
  },
});

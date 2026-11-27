import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';

/** 24 — Аттракцион "Air race 2 seats". Model: model.py (Blender skripti) → model.glb */
export default defineAttraction({
  num: '24',
  name: 'Air Race',
  model: { url: modelUrl, natural: { width: 9.7, height: 6.0 } },
  /** Xaritadagi o'lchami, metr. Asl: 9.7 × 6.0 — nisbatni saqlasangiz, shakli buzilmaydi */
  size: { width: 15.7, height: 16.0 },
  /** Model qaragan yo'nalish, gradus (#editor) */
  bearing: 54,
  anim: {
    /** Bir aylanish necha soniyada (0 — aylanmaydi). Haqiqiy attraksion ~8–10 s */
    secondsPerTurn: 9,
    /**
     * Samolyotlar ustun bo'ylab ko'tariladi: necha metr, to'liq sikl necha soniya (pastda turish → ko'tarilish → tepada
     * turish → tushish), stagger — har bir keyingi samolyot necha soniya kech (0 — hammasi birga). meters: 0 — o'chiq
     */
    lift: { meters: 1.2, seconds: 14, stagger: 0 },
  },
});

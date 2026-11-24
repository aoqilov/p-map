import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';

/** 37 — Аттракцион "Space Jet" (planda: "Mini jet 6"). Model: model.py (Blender skripti) → model.glb */
export default defineAttraction({
  num: '37',
  name: 'Space Jet',
  model: { url: modelUrl, natural: { width:10.0, height: 8.5 } },
  /** Kirish (panjaradagi ochiq joy) — janub. Aylana maydonchada yo'nalish muhim emas */
  bearing: 180,
  anim: {
    /** Bir aylanish necha soniyada (0 — aylanmaydi) */
    secondsPerTurn: 10,
    /**
     * 6 ta qo'l mashinalarni ko'taradi: necha gradus, sikl soniya (pastda → ko'tarilish → tepada → tushish),
     * stagger — har bir keyingi qo'l necha soniya kech (0 — hammasi birga). degrees: 0 — o'chiq
     */
    tilt: { degrees: 38, seconds: 12, stagger: 0 },
  },
});

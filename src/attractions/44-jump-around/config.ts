import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';

/** 44 — Аттракцион "Jump around". Model: model.py (Blender skripti) → model.glb */
export default defineAttraction({
  num: '44',
  name: 'Jump Around',
  model: { url: modelUrl, natural: { width: 9.2, height: 7.6 } },
  /** Kirish (panjaradagi ochiq joy) — janub. Aylana maydonchada yo'nalish muhim emas */
  bearing: 180,
  anim: {
    /** Bir aylanish necha soniyada (0 — aylanmaydi) */
    secondsPerTurn: 9,
    /**
     * Jiplar sakraydi: necha metr, bitta sakrash sikli soniya, stagger — har bir keyingi jip necha soniya kech
     * (navbat bilan "to'lqin" bo'lib sakraydi; 0 — hammasi birga). meters: 0 — o'chiq
     */
    lift: { meters: 0.55, seconds: 2.4, stagger: 0.4 },
  },
});

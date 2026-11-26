import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';

/**
 * 31 — Аттракцион "Mini Crazy Mill". Model: model.py (Blender skripti) → model.glb
 * Planda shakli 6 × 6 m standart maydoncha; plandagi aylana belgisi olib tashlangan — explication.py → DROP_AT.
 */
export default defineAttraction({
  num: '31',
  name: 'Mini Crazy Mill',
  model: { url: modelUrl, natural: { width: 5.5, height: 4.4 } },
  /** Kirish (panjaradagi ochiq joy) va kulgili yuz — g'arbga, yo'l tomonga */
  /** #editor da tanlangan (oldin 270) */
  bearing: 254,
  anim: {
    /** Disk va transportlar markaziy tegirmon atrofida aylanadi, soniya (0 — to'xtagan) */
    secondsPerTurn: 10,
    /** Transportlar yengil sakraydi: metr, sikl, stagger — navbat bilan */
    lift: { meters: 0.25, seconds: 2.2, stagger: 0.7 },
  },
});

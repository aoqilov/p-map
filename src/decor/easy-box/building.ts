// "EASY Box — casual food" kafesi (planda building-131, "Bino"): plandagi kvadrat iz (13 × 12.8 m) o'z joyida,
// qutisi o'rniga shu papkadagi 3D model (config.ts). Pin — "Xizmatlar" bo'limida. O'zgartirgach: npm run build:genplan
import type { PlanModelDef } from '../define';

export default {
  plan: 'building-131',
  /** Iz markazi — park koordinatasi, metr */
  at: [-12.06, 39.99],
  /** Old tomoni (oynalar, peshtaxta, skameykalar) — shimoli-sharq */
  bearing: 45,
  /** Plandagi iz bilan bir xil to'rtburchak (old tomon bo'ylab × chuqurligi) */
  rect: { width: 13, depth: 12.8 },
  /** Mansard tomi tepasigacha */
  height: 6.9,
  name: 'EASY Box — casual food',
  category: 'services',
} satisfies PlanModelDef;

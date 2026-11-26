// Кафе "Замок эльфов" (planda n13): plandagi notekis sariq iz o'rniga bitta to'rtburchak pavilon (rect) —
// markazi foydalanuvchi ko'rsatgan nuqtada. Ko'rinishi — shu papkadagi 3D model (config.ts). O'zgartirgach: npm run build:genplan
import type { PlanModelDef } from '../define';

export default {
  plan: 'n13',
  /** Pavilon markazi — park koordinatasi, metr (pritsel) */
  at: [-66.2, 136.5],
  /** Old tomoni (banner, shisha fasad) — janubi-sharq, plazaga qaragan; plandagi iz qirrasi bilan parallel */
  bearing: 132,
  /** Soyabon chetigacha: 22 × 14 m (model.py dagi W × D) */
  rect: { width: 22, depth: 14 },
  /** Beton quti tepasigacha */
  height: 7,
} satisfies PlanModelDef;

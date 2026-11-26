// Кафе "Замок эльфов" (planda n13): plandagi notekis sariq iz o'rniga bitta to'rtburchak pavilon (rect) —
// joyi va o'lchami 2D setka tahrirlagichda (#editor) tanlangan. Ko'rinishi — shu papkadagi 3D model (config.ts). O'zgartirgach: npm run build:genplan
import type { PlanModelDef } from '../define';

export default {
  plan: 'n13',
  /** Pavilon markazi — park koordinatasi, metr (2D setka tahrirlagichda tanlangan) */
  at: [-78.4, 147.15],
  /** Old tomoni (banner, shisha fasad) — janubi-sharq, plazaga qaragan; plandagi iz qirrasi bilan parallel */
  bearing: 138,
  /** Soyabon chetigacha: 19 × 10 m (model.py dagi W × D) */
  rect: { width: 19, depth: 10 },
  /** Beton quti tepasigacha */
  height: 7,
} satisfies PlanModelDef;

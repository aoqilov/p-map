// "The Бани Тельмана" (planda Bani → building-127): plandagi bino o'z joyida qoladi (to'siq, bosish),
// qutisi o'rniga shu papkadagi 3D model chiziladi (config.ts). O'zgartirgach: npm run build:genplan
import type { PlanModelDef } from '../define';

export default {
  plan: 'building-127',
  /** Iz markazi (centroid) — model.py shu nuqtaga nisbatan quriladi */
  at: [145.99, -144.0],
  /** 180 — model o'qlari park o'qlari bilan bir xil (X — sharq, Y — shimol): iz park.json dan aynan olinadi */
  bearing: 180,
  /** To'q minora tepasigacha */
  height: 17.5,
  name: 'The Бани Тельмана',
  category: 'fun',
} satisfies PlanModelDef;

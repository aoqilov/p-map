// Hojatxonalar (Общественный туалет, planda 7 va 8) — plandagi binolar o'z joyida qoladi (nomi, pin, "Xizmatlar", to'siq),
// faqat qutisi o'rniga shu papkadagi 3D model chiziladi (config.ts). O'zgartirgach: npm run build:genplan
import type { PlanModelDef } from '../define';

export default [
  /** 7 — tibbiyot xonasi yonida; eshiklari shimoli-g'arbga, maydon tomonga */
  { plan: 'n7', at: [58.87, 120.25], bearing: 230.8 },
  /** 8 — g'arbiy qism; eshiklari sharqqa, asosiy yo'lakka */
  { plan: 'n8', at: [-69.7, -47.02], bearing: 76.9 },
] satisfies PlanModelDef[];

import type { TrackData } from '../../map/GltfModel';
import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';
import track from './track.json';

/**
 * 32 — Аттракцион "3 Loops Coaster" (planda: "Spining coaster"; maydonchasi planda bino rangida — explication.py → PAD_AT).
 * Model va trassa: model.py → model.glb + track.json
 * Xonqizi vagonlar: bekat → ko'tarilish → 3 aylanali spiral → qaytish.
 */
export default defineAttraction({
  num: '32',
  name: '3 Loops Coaster',
  model: { url: modelUrl, natural: { width: 24.5, height: 5.8 } },
  /** Bekat va zina — g'arbga (yo'l tomonga), uzun o'qi maydoncha bo'ylab (~109°) */
  bearing: 251,
  /** Maydoncha 35 × 13.7 m — eni sig'ishi uchun proporsional kichraytirilgan (asl 24.5 × 15.8, balandligi 5.8) */
  size: { width: 21.3, height: 5.05 },
  anim: {
    follow: {
      track: track as TrackData,
      /** Tezlik, m/s: pastda max, eng baland joyda min */
      speed: { min: 2.0, max: 5.5 },
      /** Bekatda turish, soniya */
      dwell: 5,
    },
  },
});

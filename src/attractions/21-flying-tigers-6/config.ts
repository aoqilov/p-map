import type { TrackData } from '../../map/GltfModel';
import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';
import track from './track.json';

/**
 * 21 — Аттракцион "Flying tigers 6". Model va oval yo'l: model.py → model.glb + track.json
 * Planda shakli chizilmagan — yozuv nuqtasida, 3 Loops Coaster (32) bilan parallel, undan ~2.6 m narida.
 */
export default defineAttraction({
  num: '21',
  name: 'Flying Tigers',
  model: { url: modelUrl, natural: { width: 10.0, height: 4.9 } },
  /** Kirish — coaster'ga teskari tomonga (janubi-g'arb); uzun o'qi coaster bilan parallel (~109°) */
  bearing: 251,
  anim: {
    follow: {
      track: track as TrackData,
      /** Samolyotlar oval bo'ylab tekis tezlikda uchadi, m/s */
      speed: { min: 1.6, max: 1.6 },
      dwell: 0,
    },
  },
});

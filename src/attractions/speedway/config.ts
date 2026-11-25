import type { TrackData } from '../../map/GltfModel';
import { defineAttraction } from '../define';
import place from './place';
import modelUrl from './model.glb?url';
import track from './track.json';

/**
 * Speedway — planda raqamsiz attraksion: 12 qirrali supada oval yo'l, 6 ta bolalar jipi aylanib yuradi, tilla rang panjara.
 * Rasm: attraction-images-park/Speedway.png. Joyi va maydoncha izi — place.ts (o'zgartirgach: npm run build:genplan).
 * Model va jiplar yo'li: model.py → model.glb + track.json. Asl o'lcham: diametri 9.6 m, balandligi 1.6 m.
 */
export default defineAttraction({
  planName: place.name,
  name: place.name,
  model: { url: modelUrl, natural: { width: 9.6, height: 1.6 } },
  /** Kirish (panjaradagi ochiq joy) — yo'lak tomonda (place.ts) */
  bearing: place.bearing,
  anim: {
    follow: {
      track: track as TrackData,
      /** Jiplar tezligi, m/s (oval ~15 m — bir aylanish ~12 s) */
      speed: { min: 1.3, max: 1.3 },
      dwell: 0,
    },
  },
});

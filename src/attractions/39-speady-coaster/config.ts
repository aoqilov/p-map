import type { TrackData } from '../../map/GltfModel';
import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';
import track from './track.json';

/** 39 — Аттракцион "Speady coaster". Model va trassa: model.py (Blender skripti) → model.glb + track.json */
export default defineAttraction({
  num: '39',
  name: 'Speady Coaster',
  model: { url: modelUrl, natural: { width: 30, height: 4.5 } },
  /** Old tomoni (bekat, zina) shimoli-sharqqa — park ichidagi asosiy yo'l tomonga; uzun o'qi maydonchaga mos */
  bearing: 62,
  anim: {
    follow: {
      track: track as TrackData,
      /** Tezlik, m/s: pastda max, eng baland joyda min. Haqiqiy bolalar coaster'i ~5–8 m/s */
      speed: { min: 2.2, max: 6.5 },
      /** Bekatda turish, soniya (0 — to'xtamaydi) */
      dwell: 4,
    },
  },
});

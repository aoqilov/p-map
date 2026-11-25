import { defineAttraction } from '../define';
import place from './place';
import modelUrl from './model.glb?url';

/**
 * Paravoz — planda raqamsiz attraksion: relssiz park poyezdi (lokomotiv va 3 vagon, qora-to'q qizil, tilla bezakli).
 * Rasm: attraction-images-park/paravoz.png. Joyi va maydoncha izi — place.ts (o'zgartirgach: npm run build:genplan).
 * Model: model.py → model.glb. Asl o'lcham: uzunligi 12.2 m, eni 1.6 m, balandligi 2.6 m.
 */
export default defineAttraction({
  planName: place.name,
  name: place.name,
  /** width — eng keng joyi (bu yerda uzunligi) */
  model: { url: modelUrl, natural: { width: 12.2, height: 2.6 } },
  /** Lokomotiv oldi (place.ts) */
  bearing: place.bearing,
});

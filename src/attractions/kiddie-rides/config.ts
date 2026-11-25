import { defineAttraction } from '../define';
import place from './place';
import modelUrl from './model.glb?url';

/**
 * Kiddie Rides — planda raqamsiz attraksion: 6 ta tanga bilan ishlaydigan bolalar mashinasi bir qatorda (Smurf samolyoti,
 * Hello Kitty mashinasi, ekskavator, yuklagich, yo'l katogi, samosval). Rasmlar: attraction-images-park/payloader.png,
 * Screenshot_1.png. Joyi va maydoncha izi — place.ts (o'zgartirgach: npm run build:genplan).
 * Model: model.py → model.glb. Asl o'lcham: 9.1 × 2.9 m, balandligi 1.75 m.
 */
export default defineAttraction({
  planName: place.name,
  name: place.name,
  model: { url: modelUrl, natural: { width: 9.1, height: 1.75 } },
  /** Mashinalar oldi — yo'lakka (place.ts) */
  bearing: place.bearing,
  anim: {
    /** Mashinalar oldinga-orqaga tebranadi (tanga tashlanganda): gradus, bir tebranish soniya, seans soniya, kechikish */
    swing: { degrees: 5, period: 1.4, cycle: 16, stagger: 2.3 },
  },
});

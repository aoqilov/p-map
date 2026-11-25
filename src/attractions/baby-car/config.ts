import type { TourAnimation } from '../../map/GltfModel';
import { defineAttraction } from '../define';
import place from './place';
import modelUrl from './model.glb?url';
import tours from './tours.json';

/**
 * Baby Car — planda raqamsiz attraksion: park bo'ylab aylanib yurish uchun ijara bolalar elektromashinalari, maysazor chetida
 * yonma-yon (sariq sport mashina, qizil bagi, to'q sariq-oq bagi). Rasm: attraction-images-park/Baby_Car.png.
 * Mashinalar navbat bilan bittadan sayrga chiqadi: yo'lak bo'ylab Французская карусель (36) oldigacha borib, qaytib keladi
 * va joyiga orqasi bilan kiradi (yo'llar — model.py → tours.json). Joyi va maydoncha izi — place.ts (o'zgartirgach:
 * npm run build:genplan). Model: model.py → model.glb. Asl o'lcham: 4.0 × 1.6 m, balandligi 1.9 m (lavha bilan).
 */
export default defineAttraction({
  planName: place.name,
  name: place.name,
  model: { url: modelUrl, natural: { width: 4.0, height: 1.9 } },
  /** Mashinalar oldi — yo'lakka (place.ts) */
  bearing: place.bearing,
  anim: {
    tour: {
      tours: tours as TourAnimation['tours'],
      /** Yurish tezligi, m/s (~7 km/soat): bir aylanish (~210 m) ~1.7 daqiqa */
      speed: 2.0,
      /** Joyiga orqasi bilan kirish tezligi, m/s */
      reverseSpeed: 0.6,
      /** Bir mashina qaytgach, keyingisi jo'nagunicha, soniya */
      pause: 4,
    },
  },
});

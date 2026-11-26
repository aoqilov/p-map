import { defineDecor } from '../define';
import place from './building';
import modelUrl from './model.glb?url';

/**
 * The Бани Тельмана (Городские общественные бани) — fotolar bo'yicha: g'arbiy dumaloq burchak qizil g'isht ("БАНИ ТЕЛЬМАНА",
 * shisha kirish, yelpig'ich zinapoya; g'arbiy devorda 2-kirish "ГОРОДСКИЕ ОБЩЕСТВЕННЫЕ БАНИ"), baland oq fasad va to'q panelli 4-qavat + minora, sharqqa past qanot — basseyn
 * tomonda S-shakl egri lodjiyalar. Izi — plandagi bino (park.json, building-127). Model: model.py → model.glb (asl o'lchamda).
 */
export default defineDecor({
  name: place.name,
  at: place.at,
  bearing: place.bearing,
  /** Asl o'lcham: eng keng joyi 69.7 m (g'arbiy kirish portali bilan), balandligi 17.8 m (minora bilan) */
  model: { url: modelUrl, natural: { width: 69.7, height: 17.8 } },
  clearRadius: 0,
});

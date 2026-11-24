import { defineDecor } from '../define';
import places from './building';
import cardUrl from './card.svg?url';
import modelUrl from './model.glb?url';

/**
 * Hojatxona — oq bino jigarrang sokolda (erkaklar, ayollar, nogironlar eshiklari). Ikkala plan binosiga bir xil model.
 * Joyi va burilishi — building.ts da. Model: model.py → model.glb. Asl o'lcham: 10 × 10 m, balandligi 4.31 m.
 * Tepasida WC kartasi (card.svg): xarita aylansa ham doim ko'ruvchiga qaragan.
 */
export default defineDecor(places.map((pl) => ({
  name: `Hojatxona ${pl.plan}`,
  at: pl.at,
  /** Burilish — building.ts dagi `bearing` (har bir hojatxona uchun alohida) */
  bearing: pl.bearing,
  model: { url: modelUrl, natural: { width: 10, height: 4.31 } },
  /** Karta o'lchami (m) va tomdan balandligi */
  card: { url: cardUrl, width: 3.2, height: 2.4, lift: 1.2 },
})));

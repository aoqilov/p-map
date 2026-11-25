import type { TrackData } from '../../map/GltfModel';
import { defineAttraction } from '../define';
import place from './place';
import modelUrl from './model.glb?url';
import track from './track.json';

/**
 * RC Park — planda raqamsiz attraksion: RC do'kon-bino ("RC PARK" yozuvi, tomida katta RC mashina va katta pult) va haydovchilar supasi, rally treki
 * (4 ta RC mashina aylanib yuradi), cho'l zonasi (qum tepaliklari, kaktuslar), o'rmon/crawler zonasi (qoyalar, yog'ochlar,
 * ko'prik, archalar), atrofida panjara. Joyi va maydoncha izi — place.ts (o'zgartirgach: npm run build:genplan).
 * Model va mashinalar yo'li: model.py → model.glb + track.json. Asl o'lcham: 32.4 × 24.7 m, balandligi 8.8 m (tomdagi pult antennasi).
 */
export default defineAttraction({
  planName: place.name,
  name: place.name,
  /**
   * width — bu yerda ataylab maydonchaning qisqa tomoni (24.8 m): xarita attraksion atrofidagi daraxtlarni shu diametrli doira
   * bo'yicha o'chiradi, uzun tomon (32.5 m) olinsa maysazordagi qo'shni daraxtlar ham ketardi. Maydoncha ichidagilarni
   * build:genplan o'zi olib tashlaydi. Model masshtablanmaydi (size yo'q)
   */
  model: { url: modelUrl, natural: { width: 24.8, height: 8.8 } },
  /** Bino va kirish — shimoliy yo'lga (place.ts) */
  bearing: place.bearing,
  anim: {
    follow: {
      track: track as TrackData,
      /** RC mashinalar tezligi, m/s: tepalikka sekin chiqadi, pastga tez tushadi */
      speed: { min: 2.2, max: 3.2 },
      dwell: 0,
    },
  },
});

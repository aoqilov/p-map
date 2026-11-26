import { defineDecor } from '../define';
import places from './building';
import blok1Url from './blok1.glb?url';
import blok2Url from './blok2.glb?url';

/**
 * "Море — Водный комплекс" — bej shtukaturka, pilyastrlar, baland to'q oynalar, jigarrang yog'och panellar,
 * kirish ustida "MOPE" peshtaxtasi, granit zinapoya (foydalanuvchi fotosuratlari bo'yicha). Ikki blok — bir xil uslubda.
 * Joyi va burilishi — building.ts da. Model: model.py → blok1.glb, blok2.glb (asl o'lchamda, cho'zilmaydi).
 */
const [b1, b2] = places;

export default defineDecor([
  {
    name: 'Море (katta blok)',
    at: b1.at,
    bearing: b1.bearing,
    /** Asl o'lcham: 63.5 m (pilyastrlar bilan), balandligi 9.48 m (tomdagi bloklar bilan) */
    model: { url: blok1Url, natural: { width: 63.5, height: 9.48 } },
    clearRadius: 0,
  },
  {
    name: 'Море (2-blok)',
    at: b2.at,
    bearing: b2.bearing,
    /** Asl o'lcham: 19.9 m, balandligi 9.48 m */
    model: { url: blok2Url, natural: { width: 19.9, height: 9.48 } },
    clearRadius: 0,
  },
]);

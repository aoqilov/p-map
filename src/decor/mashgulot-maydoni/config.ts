import { defineDecor } from '../define';
import modelUrl from './model.glb?url';
import shape from './shape.json';

/** Shakl nuqtalarining o'rtachasi — model.py dagi origin bilan bir xil (0.01 m gacha yaxlitlangan) */
const r2 = (v: number) => Math.round(v * 100) / 100;
const at: [number, number] = [r2(shape.poly.reduce((s, q) => s + q[0], 0) / shape.poly.length),
  r2(shape.poly.reduce((s, q) => s + q[1], 0) / shape.poly.length)];

/**
 * Mashg'ulot (workout) maydoni — fotosuratlar bo'yicha: bordo rezina qoplama, o'rtasida to'q yashil yo'lak, sariq ustunli
 * turnik va rukoxod majmualari, shved devorlari, qora brusyalar; sharqda mural devor, shimolda reklama bannerlari,
 * yo'lka tomonida skameykalar va axlat qutilari. Avval #editor da "yangi-7" bino izi sifatida chizilgan joyda.
 * Shakli — shape.json (#editor da tahrirlanadi, keyin model.py qayta ishga tushiriladi).
 * To'siq emas: odamlar ichidan o'tadi (building.ts yo'q).
 */
export default defineDecor({
  name: "Mashg'ulot maydoni",
  at,
  /** 180 — model o'qlari park o'qlari bilan bir xil (X — sharq, Y — shimol) */
  bearing: 180,
  /** Asl o'lcham: eng uzun joyi 39.9 m, balandligi 4.61 m (fonar ustuni) */
  model: { url: modelUrl, natural: { width: 39.9, height: 4.61 } },
  clearRadius: 0,
});

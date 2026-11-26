import { defineDecor } from '../define';
import modelUrl from './model.glb?url';
import shape from './shape.json';

/** Shakl nuqtalarining o'rtachasi — model.py dagi origin bilan bir xil (0.01 m gacha yaxlitlangan) */
const r2 = (v: number) => Math.round(v * 100) / 100;
const at: [number, number] = [r2(shape.poly.reduce((s, q) => s + q[0], 0) / shape.poly.length),
  r2(shape.poly.reduce((s, q) => s + q[1], 0) / shape.poly.length)];

/**
 * "EASY Box" kafesining tashqi o'tirish zonasi — fotosurat bo'yicha: granit supa, yog'och tuvaklar (butalar bilan),
 * stollar, rattan stullar, oq-krem kvadrat soyabonlar; kirish oldida skameykalar va axlat qutilari.
 * Shakli — shape.json (EASY Box janubi-sharqiy devori bo'ylab; #editor da tahrirlanadi, keyin model.py qayta ishga tushiriladi).
 * To'siq emas: odamlar ichidan o'tadi (building.ts yo'q).
 */
export default defineDecor({
  name: 'EASY Box terrasasi',
  at,
  /** 180 — model o'qlari park o'qlari bilan bir xil (X — sharq, Y — shimol) */
  bearing: 180,
  /** Asl o'lcham: eng keng joyi 15.0 m, balandligi 2.97 m (soyabon tepasi) */
  model: { url: modelUrl, natural: { width: 15.0, height: 2.97 } },
  clearRadius: 0,
});

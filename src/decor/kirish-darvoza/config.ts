import { defineDecor } from '../define';
import modelUrl from './model.glb?url';

/**
 * Kirish darvozasi — "Central Park" sirk uslubidagi darvoza: 4 ta chiziqli chodir tom, peshtoqda yozuvli taxta va ot
 * bo'rtmalari, qizil parda gulchambarlari, oltin ustunlarda oq otlar, chetlarida oltin panjara va romb naqshli devorchalar.
 * Yozuvni o'chirish: model.py → SIGN_TEXT = ''. Model: model.py → model.glb. Asl o'lcham: eni 16.8 m, balandligi 9.4 m.
 * Pin va to'siq yo'q (o'rtadagi ikki oraliqdan o'tiladi).
 */
export default defineDecor({
  name: 'Kirish darvozasi',
  /** Bosh kirish yo'lagi, fontan oldida (pritsel) */
  at: [-187.7, 225.2],
  model: { url: modelUrl, natural: { width: 16.8, height: 9.38 } },
  /** Old tomoni — fontan tomonga (kiruvchilar yuzma-yuz ko'radi) */
  bearing: 311.7,
});

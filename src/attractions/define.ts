// Attraksion sozlamasi: har bir attraksion o'z papkasida (src/attractions/<raqam>-<nom>/config.ts).
// Bu yerda faqat xaritadagi KO'RINISH: model, o'lcham, animatsiya. Narx, cheklov, ish vaqti, rasm — keyin backend API'dan
// keladi va gen plan raqami (`num`) orqali bog'lanadi.
import type { GltfAnimation } from '../map/GltfModel';
import type { Category } from '../map/config/ui';
import type { XY } from '../map/projection';

export interface AttractionDef {
  /** Gen plan raqami ('24', '26.1') — xaritadagi joyi va backend bilan bog'lanish kaliti. Raqamsiz bo'lsa — `planName` */
  num?: string;
  /**
   * Planda raqami yo'q attraksion (masalan, "Pirate jet", "Батут") — plandagi nomi bo'yicha topiladi (park.json → name).
   * `num` bo'lsa, u ustun
   */
  planName?: string;
  /** Qisqa nom (dasturchi uchun; xaritada plandagi nom ko'rinadi) */
  name: string;
  /**
   * Blender modeli (papkadagi model.glb): `import url from './model.glb?url'`.
   * natural — modelning asl o'lchami, metr (width — eng keng joyi, height — balandligi). Berilmasa — plandagi pushti quti.
   */
  model?: { url: string; natural: { width: number; height: number } };
  /**
   * Old tomoni qaragan yo'nalish, gradus: shimoldan soat strelkasi bo'yicha (0 — shimol, 90 — sharq).
   * Modelning old tomoni — Blender'da -Y. Berilmasa — 0
   */
  bearing?: number;
  /** Xaritadagi o'lchami, metr (berilmasa — asl o'lcham). Nisbat o'zgarsa, model cho'ziladi */
  size?: { width: number; height: number };
  /** Animatsiya (Blender'dagi `rotor` va `lift*` qismlari). Qiymatlar har kadrda o'qiladi */
  anim?: GltfAnimation;
}

export const defineAttraction = (d: AttractionDef) => d;

/**
 * Planda yo'q attraksion (masalan, Ping pong): papkadagi `place.ts` — shu tur. `npm run build:genplan` uni park.json ga
 * attraksion sifatida qo'shadi: maydoncha izi, pin, qidiruv, yurishda to'siq, atrofida daraxt chiqmaydi.
 * Ko'rinishi — config.ts dagi 3D model (`planName` shu `name` bilan bir xil bo'lishi kerak). Fayl faqat ma'lumot (.glb import qilinmaydi).
 */
export interface AttractionPlaceDef {
  /** Xaritadagi nomi (pin, qidiruv); config.ts → planName bilan bir xil */
  name: string;
  /** Maydoncha markazi — park koordinatasi, metr (xaritadagi pritsel) */
  at: XY;
  /** Old tomoni qaragan yo'nalish, gradus (0 — shimol, 90 — sharq); config.ts da qayta yozilmaydi */
  bearing: number;
  /** Maydoncha izi: old tomon bo'ylab eni va chuqurligi, metr */
  width: number;
  depth: number;
  /** Eng baland joyi, metr (pin shu balandlik ustida; model yuklanguncha shu balandlikda quti) */
  height: number;
  /** Xarita bo'limi (berilmasa — 'fun') */
  category?: Category;
}

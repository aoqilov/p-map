// Attraksion sozlamasi: har bir attraksion o'z papkasida (src/attractions/<raqam>-<nom>/config.ts).
// Bu yerda faqat xaritadagi KO'RINISH: model, o'lcham, animatsiya. Narx, cheklov, ish vaqti, rasm — keyin backend API'dan
// keladi va gen plan raqami (`num`) orqali bog'lanadi.
import type { GltfAnimation } from '../map/GltfModel';

export interface AttractionDef {
  /** Gen plan raqami ('24', '26.1') — xaritadagi joyi va backend bilan bog'lanish kaliti */
  num: string;
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

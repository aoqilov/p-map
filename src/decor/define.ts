// Bezaklar (dekor): attraksion emas — pin, maydoncha, tanlash yo'q. Faqat xaritadagi 3D model (masalan, Eyfel minorasi).
// Har bir bezak o'z papkasida: src/decor/<nom>/config.ts (+ model.py → model.glb). index.ts avtomatik yig'adi.
// Koordinatani xaritadagi "pritsel" tugmasi bilan oling (park metrlari: x — sharq, y — shimol).
import type { XY } from '../map/projection';

export interface DecorDef {
  /** Qisqa nom (dasturchi uchun) */
  name: string;
  /** Joyi — park koordinatasi, metr (pritsel ko'rsatgan qiymat) */
  at: XY;
  /** Blender modeli: `import url from './model.glb?url'`; natural — asl o'lchami (width — eng keng joyi, height — balandligi) */
  model: { url: string; natural: { width: number; height: number } };
  /** Xaritadagi o'lchami, metr (berilmasa — asl o'lcham). Nisbat o'zgarsa, model cho'ziladi */
  size?: { width: number; height: number };
  /** Old tomoni qaragan yo'nalish, gradus (0 — shimol, 90 — sharq). Modelning old tomoni — Blender'da -Y */
  bearing?: number;
  /** Atrofidagi daraxtlarni olib tashlash radiusi, m (berilmasa — eni / 2 + 1.5) */
  clearRadius?: number;
}

export const defineDecor = (d: DecorDef) => d;

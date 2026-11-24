// Bezaklar (dekor): attraksion emas — faqat xaritadagi 3D model (masalan, Eyfel minorasi). Bino bo'lsa (tibbiyot xonasi),
// papkada building.ts ham bo'ladi — u xaritaga pin, qidiruv va to'siq qo'shadi (pastdagi BuildingDef).
// Har bir bezak o'z papkasida: src/decor/<nom>/config.ts (+ model.py → model.glb). index.ts avtomatik yig'adi.
// Koordinatani xaritadagi "pritsel" tugmasi bilan oling (park metrlari: x — sharq, y — shimol).
import type { XY } from '../map/projection';
import type { Category } from '../map/config/ui';
import type { WaterStyle } from '../map/config/map';

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
  /**
   * Tepasidagi karta (rasm, masalan WC belgisi): xarita qanday aylantirilmasin, doim ko'ruvchiga qaragan turadi.
   * url — `import url from './card.svg?url'`; width/height — o'lchami, m; lift — model tepasidan pastki chetigacha, m
   */
  card?: { url: string; width: number; height: number; lift: number };
  /** Oqayotgan suv (sharshara): shu nomdagi materialga chiziqli tekstura qo'yilib, UV bo'ylab pastga suriladi */
  flow?: { material: string; speed: number };
  /**
   * Model ichidagi suv hovuz kabi ko'rinsin (style: 'pond' — hovuz, standart; 'pool' — basseyn, och firuza): `material` nomli qismlar yashiriladi, o'rniga hovuz suvi shaderi chiziladi.
   * basins — model koordinatasidagi konturlar (Blender X, Y, metr) va suv sathi z (model.py → basins.json)
   */
  water?: { material: string; basins: { poly: [number, number][]; z: number }[]; style?: WaterStyle };
}

/** Bitta bezak yoki bir xil modelning bir necha nusxasi (masalan, ikki hojatxona) */
export const defineDecor = <T extends DecorDef | DecorDef[]>(d: T) => d;

/**
 * Bezak — bino bo'lsa (tibbiyot xonasi, ona va bola xonasi): papkadagi `building.ts`.
 * `npm run build:genplan` uni park.json ga bino sifatida qo'shadi: pin, qidiruv, bo'lim, yurishda to'siq, daraxt chiqmaydi.
 * Bino qutisi chizilmaydi (ko'rinishi — config.ts dagi 3D model), lekin bosilganda tanlanadi.
 * Ostida qolgan suv (masalan, basseyn) xaritadan olib tashlanadi.
 */
export interface BuildingDef {
  /** park.json dagi id (pin, tanlov) */
  id: string;
  name: string;
  /** Xarita bo'limi — pin va qidiruv (berilmasa — pin yo'q, faqat model va to'siq) */
  category?: Category;
  /** Markazi — park koordinatasi, metr */
  at: XY;
  /** Old tomoni (eshigi) qaragan yo'nalish, gradus (0 — shimol, 90 — sharq) */
  bearing: number;
  /** Eni (old tomon bo'ylab) va chuqurligi, metr — xaritadagi to'rtburchak izi */
  width: number;
  depth: number;
  /** Balandligi, metr (pin shu balandlik ustida) */
  height: number;
  /** Iz shakli: 'rect' (standart) yoki 'circle' — diametri width (fontan havzasi) */
  shape?: 'rect' | 'circle';
  /** Plandagi yo'l ustiga qo'yilgan (sharshara): izi yo'l plitkasidan kesiladi, marshrut u orqali o'tmaydi */
  cutPaving?: boolean;
}

/**
 * Plandagi mavjud binoga model qo'yish (masalan, hojatxonalar n7, n8): `building.ts` da shu tur (yoki massiv).
 * Bino plandagidek qoladi (nomi, pin, to'siq), faqat qutisi chizilmaydi. at/bearing — config.ts dagi model joyi uchun.
 */
export interface PlanModelDef {
  /** park.json dagi bino id (n7 — plandagi 7-raqam) */
  plan: string;
  /** Bino markazi, metr */
  at: XY;
  /** Eshigi qaragan yo'nalish, gradus */
  bearing: number;
}

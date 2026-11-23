import type { AttractionSize, Category } from './config';
import type { XY } from './projection';

/** Polygon: [tashqi halqa, ...teshiklar], koordinatalar metrda */
export type Poly = XY[][];
export type MultiPoly = Poly[];

export interface Building {
  id: string;
  name: string;
  poly: Poly;
  height: number;
}

export interface Area {
  id: string;
  name: string;
  poly: Poly;
}

export interface Attraction {
  id: string;
  name: string;
  at: XY;
  /** O'lcham sinfi 1–4 (config.ts → ATTRACTION_SIZES) */
  size: AttractionSize;
  /** Old tomoni qaragan yo'nalish, shimoldan soat strelkasi bo'yicha (gradus) */
  bearing: number;
  /** Sinf balandligini almashtirish (metr), masalan baland minora uchun; null — sinf chegarasi */
  height: number | null;
  /** Gen plan eksplikatsiyasidagi raqam (masalan "21", "26.1") */
  num?: string | null;
  /** Plandagi maydoncha shakli — modeli yo'q attraksion shu shakldagi quti bo'lib chiziladi */
  footprint?: Poly | null;
}

export interface PoolFx {
  /** Jakuzi: [x, y, radius] */
  jacuzzi: [number, number, number][];
  /** Zina (konsentrik yoylar): [x, y, ichki radius, tashqi radius, pog'ona] */
  steps: [number, number, number, number, number][];
  /** Tubidagi to'q tasma (sayoz/chuqur chegarasi), siniq chiziq */
  band: XY[][];
  /** Oq bezak chiziqlari */
  line: XY[][];
  /** Tubida qiya to'q ko'k tasmalar (to'g'ri burchakli basseyn) */
  stripes: boolean;
  /** Bolalar suv o'yin maydoni: [x, y, bearing] */
  playground: [number, number, number] | null;
}

export interface Bridge {
  id: string;
  line: XY[];
  width: number;
}

export interface Poi {
  id: string;
  name: string;
  label: string;
  category: Category;
  /** Pin turadigan nuqta */
  anchor: XY;
  /** Pin balandligi (bino tepasi) */
  elevation: number;
  /** Marshrut grafidagi eng yaqin tugun */
  node: number;
  /** Gen plan raqami */
  num?: string | null;
  /** Kassa: ish vaqti va qo'shimcha ma'lumot (config.ts → KASSA) */
  hours?: string;
  info?: string;
}

export interface ParkData {
  bounds: { minX: number; minY: number; maxX: number; maxY: number };
  ground: Poly;
  /** Yer plitasi suv o'rnida teshik bilan (suv yerdan pastda turadi; orollar alohida bo'lak) */
  groundCut: MultiPoly;
  water: Area[];
  roads: MultiPoly;
  bridges: Bridge[];
  parking: Area[];
  playgrounds: Area[];
  buildings: Building[];
  attractions: Attraction[];
  /** [x, y, o'lcham] */
  trees: [number, number, number][];
  /** Gen plandagi fontanlar: markaz va sakkiz qirrali havza radiusi (m) */
  fountains?: { id: string; num: string | null; at: XY; r: number }[];
  /** Gulzorlar (gen plandagi to'q sariq konturlar) */
  beds?: Poly[];
  /** Ko'cha fonuslari [x, y] (yo'l chetlari bo'ylab, build:genplan) */
  lamps: [number, number][];
  /** Basseyn tubi bezaklari: suv nomi → bezaklar (ixtiyoriy, hozircha gen planda yo'q) */
  poolFx?: Record<string, PoolFx>;
  /** Suv o'simliklari: qamish va nilufar (ixtiyoriy, hozircha gen planda yo'q) */
  plants?: {
    /** [x, y, o'lcham, burilish (rad)] */
    reeds: [number, number, number, number][];
    /** [x, y, radius, burilish (rad), gul: 0 yo'q / 1 pushti / 2 oq] */
    lilies: [number, number, number, number, number][];
  };
  graph: { nodes: XY[]; edges: [number, number, number][] };
  pois: Poi[];
  stats: { roadKm: number; areaHa: number; objects: number };
}

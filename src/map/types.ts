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

/** Parking ichi (data/parking-shape.geojson + config.ts → PARKING_LAYOUT). Burchaklar radianda, x o'qidan soat teskarisiga */
export interface ParkingLayout {
  /** Joy o'lchami: [eni, chuqurligi] */
  stall: [number, number];
  /** Joylar: [x, y, burilish] — burilish: orqa chetdan yo'lakka qarab */
  stalls: [number, number, number][];
  /** Mashinalar: [x, y, burilish (old tomoni), rang indeksi, tur: 0 sedan / 1 krossover] */
  cars: [number, number, number, number, number][];
  /** Daraxtli orolchalar (bordyurli to'rtburchak): [x, y, burilish, uzunligi, eni] */
  islands: [number, number, number, number, number][];
  /** Yo'nalish strelkalari (asfaltda): [x, y, burilish] */
  arrows: [number, number, number][];
  /** Avtomobil darvozasi: chegara nuqtasi, tashqariga qaragan burilish, eni */
  gate: { at: XY; rot: number; width: number } | null;
  /** Piyoda kirish: yo'l parkingga tushadigan nuqta va ichkariga qaragan burilish (zebra shu yo'nalishda) */
  ped: { at: XY; rot: number } | null;
  /** Darvoza yonidagi qorovul budkasi: [x, y, burilish] */
  kiosk: [number, number, number] | null;
  /** Yo'lak tepasidagi bino: old cheti a→b, chuqurligi tashqariga, balandligi */
  building: { a: XY; b: XY; depth: number; height: number } | null;
  /** Tomli soyabon: old cheti a→b (parking chetida), chuqurligi ichkariga */
  canopy: { a: XY; b: XY; depth: number } | null;
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
  /** 'genplan' — gen plandan qurilgan (eski qo'lda joylangan bezaklar chizilmaydi); yo'q — eski map.geojson */
  source?: 'genplan';
  bounds: { minX: number; minY: number; maxX: number; maxY: number };
  ground: Poly;
  /** Yer plitasi suv o'rnida teshik bilan (suv yerdan pastda turadi; orollar alohida bo'lak) */
  groundCut: MultiPoly;
  water: Area[];
  roads: MultiPoly;
  /** Taxminiy chizilgan yo'llar (roads-draft.geojson) — faqat ajratib ko'rsatish uchun */
  roadsDraft: MultiPoly;
  bridges: Bridge[];
  parking: Area[];
  /** Qurilayotgan bino id → to'siq bilan o'ralgan hudud (config.ts → CONSTRUCTION) */
  construction: Record<string, { zone: Poly }>;
  /** Parking id → ichki joylashuv (faqat config.ts → PARKING_LAYOUT dagilar) */
  parkingLayout: Record<string, ParkingLayout>;
  playgrounds: Area[];
  buildings: Building[];
  attractions: Attraction[];
  /** [x, y, o'lcham] */
  trees: [number, number, number][];
  /** Gen plandagi fontanlar: markaz va sakkiz qirrali havza radiusi (m) */
  fountains?: { id: string; num: string | null; at: XY; r: number }[];
  /** Gulzorlar (gen plandagi to'q sariq konturlar) */
  beds?: Poly[];
  /** Ko'cha fonuslari [x, y] (data/lamps.geojson dan) */
  lamps: [number, number][];
  /** Basseynlar atrofidagi plitka (travertin), suv o'rni teshik */
  deck: MultiPoly;
  /** Basseyn bo'yi: soyabon, shezlong, yelkan soyabonlar */
  poolside: {
    /** [x, y, burilish (rad), tur: 0 — oq, 1 — qizil] */
    umbrellas: [number, number, number, number][];
    /** [x, y, burilish (rad, bosh tomoni), rang indeksi] */
    loungers: [number, number, number, number][];
    /** [x, y, burilish (rad), o'lcham (m)] */
    sails: [number, number, number, number][];
  };
  /** Basseyn bezaklari (data/pools-shape.geojson): GeoJSON nomi → bezaklar */
  poolFx: Record<string, PoolFx>;
  /** Suv o'simliklari (data/water-plants.geojson hududida) */
  plants: {
    /** [x, y, o'lcham, burilish (rad)] */
    reeds: [number, number, number, number][];
    /** [x, y, radius, burilish (rad), gul: 0 yo'q / 1 pushti / 2 oq] */
    lilies: [number, number, number, number, number][];
  };
  graph: { nodes: XY[]; edges: [number, number, number][] };
  pois: Poi[];
  stats: { roadKm: number; areaHa: number; objects: number };
}

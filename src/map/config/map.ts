// Xarita sahnasi: attraksion o'lcham sinflari, fonuslar, yo'l qoplamasi, suv, baliqlar, render, joylashuv
import type { FishFigure } from '../figures';
import type { XY } from '../projection';

/**
 * Attraksion o'lcham sinflari. Model o'z proporsiyasini saqlagan holda shu "quti" ichiga sig'diriladi:
 * balandligi `height` dan, eng keng tomoni `footprint` dan oshmaydi (metr).
 * GeoJSON'da: { "name": "...", "size": 3, "bearing": 90 }
 */
export const ATTRACTION_SIZES = {
  4: {
    height: 38,
    footprint: 34,
    note: "Eng katta: charxpalak, katta amerikan tepaligi",
  },
  3: {
    height: 20,
    footprint: 24,
    note: "Katta: erkin tushish minorasi, katta qayiq-arg'imchoq, katta karusel",
  },
  2: {
    height: 10,
    footprint: 14,
    note: "O'rta: karusel, arg'imchoqli aylanma, avtodrom",
  },
  1: {
    height: 5,
    footprint: 7,
    note: "Kichik: bolalar attraksionlari, batut, mini karusel",
  },
} as const;

export type AttractionSize = keyof typeof ATTRACTION_SIZES;

/** Ko'cha fonuslari (joylari data/lamps.geojson da: yo'l bo'ylab chiziq + `spacing`) */
export const STREET_LAMP = {
  /** Xarita ochilganda chiroqlar yoqilganmi (foydalanuvchi tugma bilan o'zgartira oladi) */
  lightsOn: true,
  /** Chiroq rangi — iliq oq-sariq */
  color: "#ffe3a6",
  /** O'chiq chiroq shishasi rangi */
  offGlass: "#3f4652",
  /** Yerdagi yorug' doira radiusi, m */
  lightRadius: 5.5,
  /** Fonus atrofidagi nur radiusi, m */
  haloRadius: 1.1,
  /** Kunduzgi (yorug' mavzu) yorug'lik kuchi; qorong'i mavzuda 1 */
  dayStrength: 0.25,
};

/** Yo'l qoplamasi: asfalt va bordyur (fotodagi kabi). Bordyur xaritada ko'rinishi uchun biroz kattalashtirilgan */
export const PAVEMENT = {
  /** Bordyur eni, m (haqiqiysi ~0.15) */
  curbWidth: 0.25,
  /** Bordyurning asfaltdan balandligi, m (haqiqiysi ~0.12) */
  curbHeight: 0.15,
};

/**
 * Suv. Har bir suv obyekti (OBJECTS dagi kind: 'water') shu uslublardan biriga tegishli:
 *  - pond  — tabiiy hovuz: tosh qirg'oq, sayozda yashil-firuza, o'rtasi to'q ko'k
 *  - canal — ariq: tor, chuqurroq, suv oqim yo'nalishida siljiydi
 *  - pool  — basseyn: ochiq firuza, tagida kafel, oq chet
 * `level` — suv sathi yerdan qancha pastda (m, xaritada ko'rinishi uchun biroz kattalashtirilgan),
 * `coping` — qirg'oq toshining eni (m), `copingTop` — uning yerdan balandligi.
 */
export type WaterStyle = "pond" | "canal" | "pool";

export const WATER = {
  /** To'lqin animatsiyasi. false — suv jim turadi (kadr chizilmaydi, batareya tejaladi) */
  animate: true,
  /** Kechasi (qorong'i mavzu) yoqilgan fonuslar suvda aks etadi */
  lampReflections: true,
  styles: {
    pond: { level: -0.6, coping: 0.35, copingTop: 0.06 },
    canal: { level: -0.7, coping: 0.25, copingTop: 0.05 },
    pool: { level: -0.28, coping: 0.55, copingTop: 0.12 },
  } satisfies Record<
    WaterStyle,
    { level: number; coping: number; copingTop: number }
  >,
  /** GeoJSON nomi → uslub. Ro'yxatda bo'lmagan suv — 'pond' */
  bodies: {
    Hovuz: "pond",
    Ariq: "canal",
    Basseyn: "pool",
    Basseyn_Kv: "pool",
    Basseyn_D: "pool",
    Aqua: "canal", // suv attraksionlari kanali (WATER_RIDES) — chuqur, oqimli
  } as Record<string, WaterStyle>,
  /** Ariq oqimi: tezlik (m/s) va yo'nalish (false — shimoliy uchidan janubga, true — teskari) */
  canalFlow: { speed: 0.55, reverse: false },
};

/**
 * Baliqlar. Oddiy holatda to'da-to'da bo'lib hovuz bo'ylab erkin suzadi.
 * Har `cycleSeconds` da bir marta yig'ilib, `figures` dagi shaklni kontur bo'ylab suzib chizadi, keyin tarqaladi.
 * Qo'lda chaqirish: import { fishShow } from './map/fish'; fishShow('yurak').
 */
export const FISH = {
  enabled: true,
  /** Qaysi suvda (GeoJSON nomi) */
  water: "Hovuz",
  /** Baliqlar soni. Figura konturi shular bilan chiziladi: 140 ta ~40 m lik yurakni zich chizadi */
  count: 140,
  /** Baliq uzunligi, m (haqiqiy koi 0.3–0.7; xaritada ko'rinishi uchun biroz katta) */
  length: 0.8,
  /** Oddiy suzish tezligi, m/s */
  speed: [0.6, 1.2] as [number, number],
  /** Bitta to'dada nechta baliq */
  schoolSize: [3, 7] as [number, number],
  /** Koi ranglari (har baliqqa tasodifan) */
  colors: [
    "#ff7a1a",
    "#ff7a1a",
    "#ff6a10",
    "#f0482a",
    "#f0482a",
    "#ffc533",
    "#ffb020",
    "#f7f1e6",
    "#ff9a4d",
  ],
  show: {
    /** Bir figuradan keyingisigacha, soniya (boshlanishdan boshlanishgacha) */
    cycleSeconds: 50,
    /** Yig'ilish: baliqlar figuradagi o'z joyiga suzib boradi */
    gatherSeconds: 8,
    /** Figura turishi */
    holdSeconds: 15,
    /** Tarqalish */
    disperseSeconds: 4,
    /** Xarita ochilgandan keyin birinchi figura qachon boshlanadi, soniya */
    firstAfterSeconds: 20,
    /** Figura chizig'i bo'ylab suzish tezligi, m/s */
    contourSpeed: 1.2,
    /** true — figura har doim ekranga qarab tik turadi (xarita aylantirilsa ham); false — shimolga qotirilgan */
    faceScreen: true,
    /** 'navbat' — ro'yxat tartibida, 'tasodifiy' */
    order: "navbat" as "navbat" | "tasodifiy",
  },
  /** Figuralar. shape: 'heart' | 'star' | 'circle', yoki svg: 'M … Z'. at — [lon, lat] markaz, size — eni (m) */
  figures: [
    { name: "aylana", shape: "circle", at: [69.2982223, 41.3110829], size: 38 },
    // { name: 'yurak', shape: 'heart', at: [69.2982223, 41.3110829], size: 38 },
  ] as FishFigure[],
};

/** Chizish sozlamalari (tezlik uchun) */
export const RENDER = {
  /**
   * Soyalar sekundiga necha marta qayta chiziladi. Soya xaritasi sahnani yana bir marta chizish demak (~10% kadr),
   * harakatlanuvchi soyalar esa sekin (charxpalak, karusel) — 5 marta yetarli. 0 — har kadrda (eski usul).
   */
  shadowUpdatesPerSecond: 5,
};

/** Mijoz joylashuvi */
export const LOCATION = {
  /** Park chegarasidan shuncha metr tashqarida bo'lsa ham "ichida" deb hisoblaymiz (GPS xatosi uchun) */
  insideMarginMeters: 30,
  /** Telegram LocationManager bir martalik joy beradi — shu oraliqda qayta so'raymiz */
  telegramPollMs: 2000,
  /** Simulyatsiyada yurish tezligi, m/s (haqiqiy piyoda ~1.3; demo tezroq bo'lishi uchun) */
  simulationSpeed: 3.5,
};

/** Piyoda tezligi, m/s — marshrut vaqtini hisoblash uchun */
export const WALK_SPEED = 1.2;

/**
 * Suv attraksionlari: plandagi maydoncha ichida yer ostiga chuqurlashtirilgan halqa kanal, o'rtada daraxtli orol,
 * kanalda qayiqchalar aylanib yuradi. Kalit — gen plan raqami. O'lchamlar metrda:
 * rim — chetdagi tosh yo'lak, channel — kanal eni, boats — qayiqlar soni. O'zgartirsangiz: npm run build:genplan
 */
export const WATER_RIDES: Record<string, { rim: number; channel: number; boats: number }> = {
  '28': { rim: 1.2, channel: 3.4, boats: 6 }, // Водные гусеницы (Aqua Lady Birds)
};

/**
 * Maydoncha yoki attraksion atrofidagi panjara (ограждение), plandagi shakl cheti bo'ylab. Kalit — gen plan raqami. Kirishlar avtomatik: maydonchaga kelib
 * tugaydigan yo'l uchlari (chegaradan `gateReach` m ichida) — shu joyda `gateWidth` m ochiq qoladi.
 * `skip` — shu raqamli obyekt bilan umumiy chegarada panjara qo'yilmaydi (u yerda boshqa obyektning panjarasi bor).
 */
/**
 * Jonli devor — yashil buta to'siq (Hedges.tsx). `line` — o'rta chizig'i, park metrlari [x, y] (qo'lda chizilgan chiziq:
 * xaritada silliqlanadi). Yurish rejimida to'siq, marshrut undan o'tmaydi (o'zgartirgach: npm run build:genplan).
 */
export interface HedgeDef { id: string; height: number; width: number; line: XY[] }
export const HEDGES: HedgeDef[] = [
  {
    // Shimoliy chegara: chap maysazor uchini aylanib, uzun maysa yo'lagi shimolidan yozgi sahna ortigacha, park chegarasigacha
    id: 'shimoliy-buta',
    height: 3,
    width: 1.2,
    line: [
      [-54.25, 198.34], [-51.65, 195.36], [-50.39, 192.16], [-48.81, 191.1], [-46.3, 192.14], [-43.7, 194.57],
      [-38.36, 193.78], [-31.66, 192.49], [-22.02, 191.05], [-9.4, 188.95], [4.63, 187.17], [20.6, 185.89],
      [35.22, 185.35], [45.0, 185.2],
    ],
  },
];

/**
 * Qo'shimcha daraxtzor: `at` atrofidagi `radius` m ichidagi maysazorlarga zichroq va kattaroq daraxtlar (build:genplan).
 * Oddiy daraxtlar o'zgarmaydi — bular ustiga qo'shiladi. spacing — daraxtlar orasidagi eng kam masofa, m;
 * scale — o'lcham oralig'i (oddiy daraxtlar 0.8–1.3).
 */
export const TREE_GROVES: { id: string; at: XY; radius: number; spacing: number; scale: [number, number] }[] = [
  // Sharli fontan atrofidagi to'rt maysazor (src/decor/sharli-fontan) — katta soyali daraxtlar
  { id: 'sharli-fontan', at: [-20.9, 129.95], radius: 24, spacing: 3.9, scale: [1.3, 1.75] },
];

export const FENCES: Record<string, {
  height: number; gateWidth: number; gateReach: number; skip?: string[];
  /** Rang kaliti (theme.ts): 'fence' — to'q yashil, 'fenceYellow' — sariq */
  color?: 'fence' | 'fenceYellow';
  /** Qo'shimcha kirishlar, park metrlari [x, y] (masalan, bekat zinasi qarshisida) — chegaradagi eng yaqin nuqtada ochiladi */
  gates?: [number, number][];
}> = {
  '30': { height: 1.0, gateWidth: 2.4, gateReach: 5, skip: ['28'] }, // Детская площадка
  '32': { height: 1.1, gateWidth: 2.2, gateReach: 6, color: 'fenceYellow', gates: [[56.0, 86.5]] }, // 3 Loops Coaster — zina qarshisida kirish
};

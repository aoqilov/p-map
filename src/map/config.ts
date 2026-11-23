// Barcha sozlamalar bir joyda: GeoJSON'dagi `name` → obyekt turi, nomi, balandligi, kategoriyasi.
// Yangi obyekt qo'shsangiz, shu yerga bitta qator qo'shing.
import type { FishFigure } from "./figures";

export type Kind =
  | "ground"
  | "road"
  | "bridge"
  | "plaza"
  | "water"
  | "building"
  | "parking"
  | "playground"
  | "attraction";
export type Category =
  | "services"
  | "fun"
  | "buildings"
  | "parking"
  | "entrance"
  | "kassa";

/** Yo'l kengligi, metrda (to'liq kenglik, yarmi emas). Sputnikdan o'lchab aniqlashtiring. */
export const ROAD_WIDTH: Record<string, number> = {
  Kirish_yoli: 6,
  Kirish_2: 4,
  Ichkaridagi_yol: 3,
  Koprik: 2.5,
};

/** Uzilgan yo'l uchini shu masofagacha (metr) eng yaqin yo'lga yopishtiramiz. */
export const SNAP_METERS = 4;

interface ObjectDef {
  kind: Exclude<Kind, "road" | "bridge" | "plaza">;
  label: string;
  category?: Category;
  /** Faqat binolar uchun, metrda */
  height?: number;
}

export const OBJECTS: Record<string, ObjectDef> = {
  Bog: { kind: "ground", label: "Bog'" },

  Hovuz: { kind: "water", label: "Hovuz", category: "fun" },
  Ariq: { kind: "water", label: "Ariq" },
  Basseyn: { kind: "water", label: "Basseyn", category: "fun" },
  Basseyn_Kv: { kind: "water", label: "Kvadrat basseyn", category: "fun" },
  Basseyn_D: { kind: "water", label: "Bolalar basseyni", category: "fun" },

  Parking_1: { kind: "parking", label: "1-parking", category: "parking" },
  Parking_3: { kind: "parking", label: "3-parking", category: "parking" },
  Bolalar_maydonchasi: {
    kind: "playground",
    label: "Bolalar maydonchasi",
    category: "fun",
  },

  Tualet: {
    kind: "building",
    label: "Hojatxona",
    category: "services",
    height: 3.2,
  },
  Tualet_2: {
    kind: "building",
    label: "Hojatxona 2",
    category: "services",
    height: 3.2,
  },
  Med_Punkt: {
    kind: "building",
    label: "Tibbiyot punkti",
    category: "services",
    height: 3.4,
  },
  Ona_Bola_Xonasi: {
    kind: "building",
    label: "Ona va bola xonasi",
    category: "services",
    height: 3.4,
  },

  GameLand: { kind: "building", label: "GameLand", category: "fun", height: 5 },
  Rotonda: { kind: "building", label: "Rotonda", category: "fun", height: 4.5 },
  More_Rotonda: {
    kind: "building",
    label: "Orol rotondasi",
    category: "fun",
    height: 4,
  },
  Bani: { kind: "building", label: "Banya", category: "fun", height: 6 },

  "Ariston Park": {
    kind: "building",
    label: "Ariston Park",
    category: "buildings",
    height: 7,
  },
  DAR: { kind: "building", label: "DAR", category: "buildings", height: 6 },
  Bino_1: {
    kind: "building",
    label: "1-bino",
    category: "buildings",
    height: 4.5,
  },
  Bino_2: {
    kind: "building",
    label: "2-bino",
    category: "buildings",
    height: 4,
  },
  Bino_Katta: {
    kind: "building",
    label: "Play Port 2027",
    category: "buildings",
    height: 26,
  },
  // data/extra-objects.geojson dan
  Massaj: {
    kind: "building",
    label: "Bali massaji",
    category: "fun",
    height: 5.6,
  },
  More_Bino: {
    kind: "building",
    label: "More binosi",
    category: "buildings",
    height: 5.5,
  },

  // Attraksionlar — GeoJSON'da Point sifatida turadi, o'lchami `size` (1–4) xususiyatida
  Charxpalak: { kind: "attraction", label: "Charxpalak", category: "fun" },
  Karusel: { kind: "attraction", label: "Karusel", category: "fun" },
  Erkin_tushish: {
    kind: "attraction",
    label: "Erkin tushish minorasi",
    category: "fun",
  },
  Amerikan_tepaligi: {
    kind: "attraction",
    label: "Mini amerikan tepaligi",
    category: "fun",
  },
  Galleon: { kind: "attraction", label: "Galleon", category: "fun" },
  Cars: { kind: "attraction", label: "Cars", category: "fun" },
  Merry_go_round: {
    kind: "attraction",
    label: "Merry-go-round",
    category: "fun",
  },
  Excavator: { kind: "attraction", label: "Excavator", category: "fun" },
  Aqua_Lady_Birds: {
    kind: "attraction",
    label: "Aqua Lady Birds",
    category: "fun",
  },
};

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

/** `bearing` berilmasa: attraksion old tomoni shu yo'nalishga qaraydi (shimoldan soat strelkasi bo'yicha, gradus) */
export const DEFAULT_BEARING = 156;

/** Charxpalak modelining tabiiy o'lchamlari (metr). Xaritadagi o'lchami `size` sinfi bilan belgilanadi. */
export const FERRIS_WHEEL = {
  diameter: 30,
  /** G'ildirak markazining yerdan balandligi */
  hubHeight: 21.2,
  /** Ikki gardish orasidagi masofa (o'q bo'ylab) */
  depth: 2.6,
  cabins: 32,
  /** Bir aylanish necha soniyada (0 — aylanmaydi) */
  secondsPerTurn: 120,
  pavilionRadius: 6.5,
};

/** GeoJSON'da nuqta sifatida yo'q, lekin xaritada kerak bo'lgan joylar (kirishlar). Feature indeksidan olinadi. */
export const ENTRANCES = [
  { id: "entrance-main", label: "Asosiy kirish", fromFeature: 0 },
  { id: "entrance-2", label: "2-kirish", fromFeature: 33 },
];

export const CATEGORY_LABEL: Record<Category, string> = {
  services: "Xizmatlar",
  fun: "Dam olish",
  buildings: "Binolar",
  parking: "Parking",
  entrance: "Kirish",
  kassa: "Kassa",
};

/**
 * Kassalar (chipta sotish joylari). Gen planda yo'q — shu yerga qo'shing, keyin `npm run build:genplan`.
 * Joyi: `near` — plan raqami (kassa shu obyekt yonida, masalan '53' — Главный вход) yoki aniq `lonLat`.
 * Masalan: { id: 'kassa-1', label: 'Asosiy kassa', near: '53', hours: '10:00–23:00', info: 'Kattalar 50 000, bolalar 30 000' }
 */
export const KASSA: {
  id: string;
  label: string;
  near?: string;
  lonLat?: [number, number];
  hours?: string;
  info?: string;
}[] = [];

/**
 * Yuqoridagi menyu tablari. Tab bosilsa: xaritada faqat shu bo'lim pinlari, pastda ro'yxati ochiladi.
 * `attractions` — attraksionlar va bolalar maydonchalari (dam olish bo'limidagi fontan, teatr kirmaydi).
 */
export type MenuTab = "attractions" | "kassa" | "services" | "parking";
export const MENU_TABS: { id: MenuTab; label: string }[] = [
  { id: "attractions", label: "Attraksionlar" },
  { id: "kassa", label: "Kassa" },
  { id: "services", label: "Xizmatlar" },
  { id: "parking", label: "Parking va kirish" },
];

/**
 * Xarita ikki joyda ishlaydi. Har bir rejimda qaysi funksiyalar yoqilganini shu yerda belgilang.
 * Komponentga `features` prop orqali alohida ham o'zgartirish mumkin.
 */
export type MapMode = "miniapp" | "admin";

export interface MapFeatures {
  /** "Mening joyim" tugmasi, ko'k nuqta, joyimdan marshrut */
  location: boolean;
  /** Joylashuv yo'q bo'lganda "Simulyatsiya" tugmasi — faqat sinov va demo uchun */
  simulation: boolean;
  /** Taxminiy chizilgan yo'llarni to'q sariq rangda ajratib ko'rsatish va izoh */
  draftRoads: boolean;
}

/**
 * Xaritadagi pinlar (metkalar). "Hammasi" filtrida faqat shu toifalar ko'rinadi (ko'k pinlar — xizmatlar, dam olish,
 * binolar — ko'rinmaydi). Qurilayotgan bino (kran belgisi) ham ko'rinadi. Pastdagi toifa tugmasi bosilsa yoki obyekt
 * tanlansa (bino ustiga bosish, qidiruv), o'sha pinlar chiqadi. Hammasi ko'rinsin desangiz: ['services', 'fun', 'buildings', 'parking', 'entrance'].
 */
export const PINS = {
  alwaysShow: ["parking", "entrance"] as Category[],
  /** Qurilish maydoni ko'rsatilayotgan binoning kran pini (CONSTRUCTION → display: 'site' bo'lganda) */
  showConstruction: true,
};

export const MODE_FEATURES: Record<MapMode, MapFeatures> = {
  miniapp: { location: true, simulation: false, draftRoads: false },
  admin: { location: false, simulation: false, draftRoads: true },
};

/**
 * Air Race (gen plan № 24, Blender modeli: blender/air_race.py). Qiymatlarni o'zgartirsangiz, xarita darhol yangilanadi.
 * Hammasini to'xtatish: secondsPerTurn: 0 va lift.meters: 0. Telefonda "harakatni kamaytirish" yoqilgan bo'lsa — o'zi to'xtaydi.
 */
export const AIR_RACE = {
  /**
   * Xaritadagi o'lchami, metr: width — diametri (samolyot qanotlari uchigacha), height — balandligi (minora uchigacha).
   * Modelning asl o'lchami: 9.7 × 6.0. Ikkalasini bir xil nisbatda o'zgartirsangiz, shakli buzilmaydi.
   */
  size: { width: 15.7, height: 16.0 },
  /** Bir aylanish necha soniyada (0 — aylanmaydi). Haqiqiy attraksion ~8–10 s */
  secondsPerTurn: 9,
  /**
   * Samolyotlar ustun bo'ylab ko'tariladi: necha metr, to'liq sikl necha soniya (pastda turish → ko'tarilish → tepada
   * turish → tushish), stagger — har bir keyingi samolyot necha soniya kech (0 — hammasi birga). meters: 0 — o'chiq
   */
  lift: { meters: 1.2, seconds: 14, stagger: 0 },
};

/** Karusel: aylanish va otlar soni */
export const CAROUSEL = {
  /** Bir aylanish necha soniyada (0 — aylanmaydi) */
  secondsPerTurn: 14,
  /** Otning bir marta ko'tarilib-tushishi, soniya */
  bobSeconds: 2.6,
  /** Tashqi halqadagi o'rinlar (aravalar ham shu yerda) va ichki halqadagi otlar */
  outerHorses: 12,
  innerHorses: 8,
  chariots: 2,
};

/** Galleon (qaroqchi kema): tebranish sikli. Sikl = rest + 2·ramp + hold (soniya) */
export const GALLEON = {
  /** false — kema tik turadi */
  enabled: true,
  restSeconds: 4,
  rampSeconds: 14,
  holdSeconds: 12,
  maxDegrees: 52,
  /** Bitta to'liq tebranish davri */
  periodSeconds: 5.4,
};

/** Erkin tushish minorasi: kabina sikli (soniya) */
export const DROP_TOWER = {
  /** false — kabina pastda turadi */
  enabled: true,
  restSeconds: 3,
  climbSeconds: 9,
  holdSeconds: 2,
  /** Balandlikning qancha qismi erkin tushish, qolgani tormozlash */
  freeFallShare: 0.65,
  seats: 16,
};

/** Mini amerikan tepaligi: poyezd harakati */
export const COASTER = {
  /** false — poyezd joyida turadi */
  enabled: true,
  /** Eng baland nuqtadagi tezlik, m/s; pastda energiya bo'yicha tezlashadi */
  topSpeed: 2.5,
  /** "Tortishish" — kichikroq qiymat bolalar attraksioniga mos sekinroq tushish beradi */
  gravity: 5,
  /** Parovozdan keyingi vagonlar soni va ular orasidagi masofa (m) */
  cars: 3,
  carSpacing: 1.85,
};

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

/** Hamma yo'llar bo'ylab fonus (har yo'lning bir tomonida). data/lamps.geojson dagi yo'llar ham saqlanadi. */
export const STREET_LAMP_ROADS = {
  enabled: true,
  /** Oraliq, m (g'arbiy yo'ldagi 10 ta fonus bilan bir xil ≈ 33 m) */
  spacing: 33,
  /** Ikki fonus bundan yaqin bo'lsa (chorrahalarda), ikkinchisi qo'yilmaydi */
  minGap: 14,
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
  } as Record<string, WaterStyle>,
  /** Ariq oqimi: tezlik (m/s) va yo'nalish (false — shimoliy uchidan janubga, true — teskari) */
  canalFlow: { speed: 0.55, reverse: false },
};

/**
 * Basseynlar majmuasi ("Море", fotoga qarab). Shakllar va bezaklar: data/pools-shape.geojson
 * (lagun va bolalar basseyni konturi, jakuzi, zina, mozaika, suv o'yin maydoni, yelkan soyabonlar).
 */
export const POOL_AREA = {
  /** Plitka shu basseynlarni bitta umumiy maydon bo'lib o'raydi (fotodagidek), maysa va daraxtlar o'rniga */
  pools: ["Basseyn", "Basseyn_Kv", "Basseyn_D"],
  /** Basseynlar tashqi chegarasidan tashqariga, m */
  margin: 8.5,
  /** Soyabon qatorlari: suv chetidan masofa (m) */
  rows: [2.4],
  /** Bir qatorda soyabonlar oralig'i, m */
  spacing: 1.5,
  /** Qizil soyabonlar ulushi (qolgani oq) */
  redShare: 0.08,
  /** Soyabon yo'lakdan (marshrut chizig'idan) kamida shuncha uzoqda — o'tish joyi ochiq qolsin, m */
  pathClearance: 1.9,
};

/**
 * Parking ichki joylashuvi (fotoga qarab). Kontur, darvoza, piyoda kirish, bino va soyabon — data/parking-shape.geojson da.
 * Ro'yxatda yo'q parkinglar oddiy kulrang maydon bo'lib qoladi.
 */
export const PARKING_LAYOUT: Record<
  string,
  {
    /** Bitta joy: eni × chuqurligi, m */
    stall: [number, number];
    /** Mashina o'tadigan yo'lak eni, m */
    aisle: number;
    /** Ichki qo'sh qatorda har nechta joydan keyin daraxtli orolcha */
    islandEvery: number;
    /** Band joylar ulushi (mashinalar) */
    occupancy: number;
    /** Orolchalardagi fonuslar: har nechinchi orolchada */
    lampEvery: number;
    seed: number;
    /** Ichki qatorlar yo'nalishi (kompas, gradus); berilmasa — eng ko'p joy sig'adigani avtomatik tanlanadi */
    rowBearing?: number;
  }
> = {
  // Fotodagidek: ichki qatorlar g'arbiy chetga parallel, o'rtada daraxtli orolchalar
  Parking_1: {
    stall: [2.5, 5],
    aisle: 6,
    islandEvery: 5,
    occupancy: 0.72,
    lampEvery: 2,
    seed: 7,
    rowBearing: 166,
  },
};

/**
 * Parkingdagi harakat (joylashuvi bor parkinglarda): vaqti-vaqti bilan darvozadan mashina kirib bo'sh joyga turadi,
 * boshqasi joyidan (orqaga yoki oldinga) chiqib ketadi; shlagbaum ko'tariladi. "Harakatni kamaytirish" yoqilgan bo'lsa o'chadi.
 */
export const PARKING_TRAFFIC = {
  enabled: true,
  /** Yangi mashina kelishi oralig'i, s */
  arriveEvery: [14, 30] as [number, number],
  /** Mashina ketishi oralig'i, s */
  departEvery: [14, 30] as [number, number],
  /** Tezlik, m/s: oldinga (~11 km/soat) va orqaga */
  speed: 3.2,
  reverseSpeed: 1.3,
  /** Bir vaqtda harakatdagi mashinalar */
  maxMoving: 2,
};

/** Qamish va nilufar (joyi data/water-plants.geojson dagi hudud ichida) */
export const WATER_PLANTS = {
  /** Qirg'oq bo'ylab qamish to'pi oralig'i, m (bo'shliqlar shovqin bilan o'zi chiqadi) */
  reedSpacing: 0.85,
  /** Qamish balandligi, m */
  reedHeight: [1.5, 2.4] as [number, number],
  /** Nilufar to'dalari soni (hudud ichida) va har to'dadagi barglar */
  lilyClusters: 9,
  lilyPerCluster: [6, 14] as [number, number],
  /** Barg radiusi, m (haqiqiysi 0.1–0.3; xaritada ko'rinishi uchun kattaroq) */
  lilyRadius: [0.32, 0.6] as [number, number],
  /** Barglarning qanchasida gul bor */
  flowerShare: 0.18,
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

/**
 * Binolarning haqiqiy ko'rinishi (fotoga qarab). Ro'yxatda yo'q binolar oddiy ko'k quti bo'lib qoladi.
 * Kalit — bino id si (nomi + tartib raqami: GeoJSON'dagi ikkinchi More_Bino → 'more-bino-2').
 *  - facade: 'more' — oq ustunlar, yog'och friz, katta oynalar, naqshli oq panellar
 *            'moreWood' — yog'och panellar ko'proq, tor tik derazalar
 *  - floors: qavatlar soni, height: devor balandligi (m), roofPitch: tom qiyaligi (gradus)
 *  - roofUnits: tomdagi konditsionerlar soni (taxminan)
 * Faqat to'rtburchak binolarga qiya tom quriladi, boshqa shakllarga — tekis tom.
 */
export interface BuildingLook {
  facade: "more" | "moreWood" | "banya" | "bar" | "mall" | "massage";
  floors: number;
  height: number;
  roofPitch: number;
  roofUnits: number;
  /** Banya: qizil g'ishtli kirish ("БАНЯ" yozuvi, eshik, zina) — polygonning nechanchi qirrasida (0 dan) */
  accentEdge?: number;
  /** Banya: dumaloq qismdagi egri balkonlar */
  balconies?: boolean;
  /** Tekis tomdagi qo'shimcha qavat: eng uzun devordan `setback` m ichkarida, chuqurligi `depth`, chetlardan `inset` */
  penthouse?: { setback: number; depth: number; inset: number; height: number };
  /** Katta bino (mall): old fasad (pilon va portal) shu qirradan boshlanadi (polygon qirrasi, 0 dan) */
  frontEdge?: number;
}
export const BUILDING_LOOKS: Record<string, BuildingLook> = {
  "more-bino-1": {
    facade: "more",
    floors: 2,
    height: 7.6,
    roofPitch: 12,
    roofUnits: 12,
  },
  "more-bino-2": {
    facade: "moreWood",
    floors: 2,
    height: 7.6,
    roofPitch: 12,
    roofUnits: 4,
  },
  // Banya: hovuzga qaragan fasadda dumaloq balkonli qism va qizil g'isht kirish (12-qirra — g'arbiy burchak oldi)
  "bani-1": {
    facade: "banya",
    floors: 3,
    height: 11,
    roofPitch: 0,
    roofUnits: 8,
    accentEdge: 12,
    balconies: true,
    penthouse: { setback: 2, depth: 11, inset: 6, height: 3.2 },
  },
  // Lagun orolidagi bar: dumaloq yog'och tom, peshtaxta, ustida kumushrang halqa arkalar (fotodagidek)
  "more-rotonda-1": {
    facade: "bar",
    floors: 1,
    height: 3,
    roofPitch: 0,
    roofUnits: 0,
  },
  // Katta bino: 5 qavat (~26 m). Old fasad kanalga qaragan (0-qirra — shimoliy burchakdan): chapda pilon, markazda portal
  "bino-katta-1": {
    facade: "mall",
    floors: 5,
    height: 25.8,
    roofPitch: 0,
    roofUnits: 14,
    frontEdge: 0,
  },
  // Balicha massaj: 1 qavat kafe ("Fastfood zona"), tomida chodir ostida massaj kabinalari; old tomoni basseynlarga qaragan
  "massaj-1": {
    facade: "massage",
    floors: 1,
    height: 4.4,
    roofPitch: 0,
    roofUnits: 0,
    frontEdge: 0,
  },
};

/**
 * Qurilayotgan binolar. Xaritada odatiy holda qurilish maydoni ko'rinadi: beton karkas (`floorsBuilt` qavat), minorali kran,
 * to'siq va banner. Bino tanlanganda pastki oynada "Hozir / 2027" almashtirgichi bor: "2027" — tayyor bino (loyiha).
 * Bino ochilganda shu ro'yxatdan o'chirib, `npm run build:map` qiling — xaritada tayyor bino qoladi.
 */
export const CONSTRUCTION: Record<
  string,
  {
    /** Ochilish yili (pastki oynada, qidiruvda va bannerda) */
    opens: string;
    /** Hozir nechta qavat karkasi ko'tarilgan */
    floorsBuilt: number;
    /** To'siq binodan shuncha metr tashqarida (yo'l va suvga yetmaydi) */
    fenceMargin: number;
    /** Bannerdagi yozuv */
    banner: string;
    /**
     * Xaritada nima ko'rinadi: 'finished' — tayyor bino, tepasida katta ochilish yili ("2027");
     * 'site' — qurilish maydoni (karkas, kran, to'siq), pastki oynada "Hozir / 2027" almashtirgichi bilan
     */
    display: "finished" | "site";
  }
> = {
  "bino-katta-1": {
    opens: "2027",
    floorsBuilt: 3,
    fenceMargin: 4.5,
    banner: "PLAY PORT · 2027-yilda ochiladi",
    display: "finished",
  },
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
 * Bolalar maydonchasi (Playground) joylashuvi — 2D reja sahifasidan (xarita metrlarida: x — sharq, y — shimol).
 * items: [tur, x, y, burchak(rad)] · turlar: 0 belanchak, 1 slayd, 2 tebranma, 3 prujinali, 4 qum maydoni, 5 devor-narvon, 6 karusel
 * benches/gates: [x, y, burchak]
 */
export const PLAYGROUND = {
  items: [
    [6, 28.5, 72.5, -1.38],
    [0, 14, 92.5, 0.17],
    [1, 6, 71.5, 1.34],
    [5, 1.04, 86.99, -0.2],
    [4, 26.04, 120.99, 3.39],
    [2, 11, 68.5, 1.76],
    [0, 14, 88.5, 0.25],
    [1, 33.04, 58.99, -1.84],
    [5, 30, 83, 2.99],
    [4, -4.96, 64.99, -1.84],
    [6, 4.04, 56.99, 3.31],
    [3, 11, 73, 0.54],
    [6, 23.5, 88.5, 0],
    [6, 39.5, 80.5, 0],
    [2, 39.5, 68, 0],
    [2, 40.5, 65.5, 0],
    [5, 23, 56.5, 0],
    [4, 15.5, 55.5, 3.14],
    [1, 13, 98.5, 1.83],
  ] as [number, number, number, number][],
  benches: [
    [15.5, 82.5, 4.32],
    [11.5, 64, 7.2],
    [15.5, 66, 3.8],
    [10, 61.5, 4.07],
    [20, 74, 6.42],
    [27, 98, 3.54],
    [30.5, 101, 4.07],
    [22.5, 97, 6.42],
    [24, 75.5, 3.78],
    [21, 67, 9.56],
    [15, 102.5, 5.26],
    [18, 99, 5.41],
    [8, 79, 4.34],
    [5.5, 89, 3.92],
    [0, 80.5, 6.63],
    [25.06, 116.49, 7.64],
    [16.5, 75.5, 2.43],
    [10.39, 83.19, 7.46],
    [29.5, 60, 8.06],
    [26, 65, 5.53],
    [26, 78, 7.65],
    [15, 78.5, 8.02],
    [17, 84.5, 0.79],
    [20.5, 85.5, 0],
    [24, 84.5, -0.79],
    [25.5, 82, -1.31],
  ] as [number, number, number][],
  gates: [[37.02, 91.9, -1.44]] as [number, number, number][],
};

/** Bolalar maydonchasidagi attraksionlar (xarita metrlarida): jeep aylanma yo'li, otli karusel (r — platforma radiusi), texnikalar [x, y, burchak(rad), tur 0–3] */
export const PLAYGROUND_RIDES = {
  jeep: { x: 21, y: 129.5, r: 4.58 },
  carousel: { x: 13.5, y: 123.5, r: 3.7 },
  vehicles: [
    [10.5, 115, -3.9, 0],
    [9, 113.5, -3.9, 1],
    [7.5, 112, -3.9, 2],
    [6, 110.5, -3.9, 3],
  ] as [number, number, number, number][],
};

// Interfeys: kategoriyalar, menyu tablari, pinlar, rejimlar (mijoz mini-app / adminka)

export type Category =
  | "services"
  | "fun"
  | "buildings"
  | "parking"
  | "entrance"
  | "kassa";

export const CATEGORY_LABEL: Record<Category, string> = {
  services: "Xizmatlar",
  fun: "Dam olish",
  buildings: "Binolar",
  parking: "Parking",
  entrance: "Kirish",
  kassa: "Kassa",
};

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
}

/**
 * Xaritadagi pinlar (metkalar). "Hammasi" filtrida faqat shu toifalar ko'rinadi (ko'k pinlar — xizmatlar, dam olish,
 * binolar — ko'rinmaydi). Yuqoridagi tab bosilsa yoki obyekt
 * tanlansa (bino ustiga bosish, qidiruv), o'sha pinlar chiqadi. Hammasi ko'rinsin desangiz: ['services', 'fun', 'buildings', 'parking', 'entrance'].
 */
export const PINS = {
  alwaysShow: ["parking", "entrance"] as Category[],
};

export const MODE_FEATURES: Record<MapMode, MapFeatures> = {
  miniapp: { location: true, simulation: false },
  admin: { location: false, simulation: false },
};

// Kassalar (chipta sotish joylari) — gen planda yo'q, shu yerda qo'lda belgilanadi

/**
 * Kassalar (chipta sotish joylari). Gen planda yo'q — shu yerga qo'shing, keyin `npm run build:genplan`.
 * Joyi: `at` — park koordinatasi, metr (#editor / pritsel; shu joyda 3D kassa budkasi ham chiqadi — src/decor/kassa),
 * yoki `near` — plan raqami (kassa shu obyekt yonida, masalan '53' — Главный вход), yoki aniq `lonLat` (bu ikkisida model yo'q).
 * Masalan: { id: 'kassa-1', label: 'Asosiy kassa', at: [12.5, -40], bearing: 180, hours: '10:00–23:00', info: 'Kattalar 50 000' }
 */
export const KASSA: {
  id: string;
  label: string;
  /** Budka joyi — park koordinatasi, metr [x — sharq, y — shimol] */
  at?: [number, number];
  /** Budka oynasi qaragan yo'nalish, gradus (0 — shimol, 90 — sharq) */
  bearing?: number;
  /** Budka kattaligi (1 — haqiqiy o'lcham 1.36 × 0.96 m, 2 — ikki barobar; proporsiya saqlanadi) */
  scale?: number;
  near?: string;
  lonLat?: [number, number];
  hours?: string;
  info?: string;
}[] = [
  /** EASY Box yonidagi uzun bino (building-132) oldida; oynasi shimoli-sharqqa; 2.21× kattalikda (#editor) */
  { id: 'K-5', label: 'Kassa K-5', at: [-19.03, 49.09], bearing: 43, scale: 2.21 },
  { id: 'K-8', label: 'Kassa K-8', at: [62, 48], bearing: 255, scale: 2.21 },
  { id: 'K-2', label: 'Kassa K-2', at: [57, 6.5], bearing: 272, scale: 2.21 },
  { id: 'K-1', label: 'Kassa K-1', at: [45.5, 62.5], bearing: 61, scale: 2.21 },
  { id: 'K-6', label: 'Kassa K-6', at: [-52.78, 25.85], bearing: 230, scale: 3.31 },
  { id: 'K-3', label: 'Kassa K-3', at: [-39.5, -96.5], bearing: 125, scale: 2.21 },
  { id: 'K-4', label: 'Kassa K-4', at: [-105.5, 112], bearing: 303, scale: 2.21 },
  { id: 'K-7', label: 'Kassa K-7', at: [34, -98], bearing: 297, scale: 2.21 },
];

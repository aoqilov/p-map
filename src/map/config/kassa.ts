// Kassalar (chipta sotish joylari) — gen planda yo'q, shu yerda qo'lda belgilanadi

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

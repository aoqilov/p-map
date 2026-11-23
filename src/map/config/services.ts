// Servislar (hojatxona, kafe, tibbiyot va h.k.) — gen plan raqami bo'yicha ko'rinish sozlamalari.
// Ish vaqti, menyu va boshqa ma'lumotlar keyin backend API'dan keladi (plan raqami — `num` orqali bog'lanadi).
import type { Category } from './ui';

export interface ServiceDef {
  /** Xaritadagi nomi (berilmasa — plandagi nom) */
  label?: string;
  /** Boshqa bo'limga o'tkazish (masalan, kafe → 'services') */
  category?: Category;
  /** Xaritada ko'rsatilmasin (masalan, transformator podstansiyasi) */
  hidden?: boolean;
}

/** Kalit — gen plan raqami ('7', '13', '68.1'). Keyin `npm run build:genplan` */
export const SERVICES: Record<string, ServiceDef> = {};

// Barcha attraksionlar: har bir papkadagi config.ts avtomatik yig'iladi (yangi papka qo'shsangiz, shu yerga yozish shart emas).
import type { AttractionDef } from './define';

const modules = import.meta.glob<AttractionDef>('./*/config.ts', { eager: true, import: 'default' });

/** Gen plan raqami → sozlama */
export const ATTRACTIONS: Record<string, AttractionDef> = Object.fromEntries(
  Object.values(modules).filter((d) => d.num).map((d) => [d.num!, d]),
);

/** Raqamsiz attraksionlar: plandagi nomi → sozlama (define.ts → planName) */
export const ATTRACTIONS_BY_NAME: Record<string, AttractionDef> = Object.fromEntries(
  Object.values(modules).filter((d) => !d.num && d.planName).map((d) => [d.planName!, d]),
);

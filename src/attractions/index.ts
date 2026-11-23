// Barcha attraksionlar: har bir papkadagi config.ts avtomatik yig'iladi (yangi papka qo'shsangiz, shu yerga yozish shart emas).
import type { AttractionDef } from './define';

const modules = import.meta.glob<AttractionDef>('./*/config.ts', { eager: true, import: 'default' });

/** Gen plan raqami → sozlama */
export const ATTRACTIONS: Record<string, AttractionDef> = Object.fromEntries(
  Object.values(modules).map((d) => [d.num, d]),
);

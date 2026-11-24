// Barcha bezaklar: har bir papkadagi config.ts avtomatik yig'iladi (yangi papka qo'shsangiz, shu yerga yozish shart emas).
import type { DecorDef } from './define';

const modules = import.meta.glob<DecorDef>('./*/config.ts', { eager: true, import: 'default' });

export const DECOR: DecorDef[] = Object.values(modules);

/** Xaritadagi o'lcham masshtabi [gorizontal, tik] */
export const decorScale = (d: DecorDef): [number, number] =>
  d.size ? [d.size.width / d.model.natural.width, d.size.height / d.model.natural.height] : [1, 1];

/** Bezak atrofida daraxt bo'lmasin — radius, m */
export const decorClearRadius = (d: DecorDef) => d.clearRadius ?? (d.size?.width ?? d.model.natural.width) / 2 + 1.5;

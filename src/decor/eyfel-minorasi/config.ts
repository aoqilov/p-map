import { defineDecor } from '../define';
import modelUrl from './model.glb?url';

/**
 * Eyfel minorasi — bezak (attraksion emas: pin, tanlash yo'q). Model: model.py (Blender skripti) → model.glb
 * Asl o'lcham: asosi 6.8 m (tosh maydoncha bilan), balandligi 13 m (antenna uchigacha).
 */
export default defineDecor({
  name: 'Eyfel minorasi',
  /** Joyi — park koordinatasi, metr (xaritadagi pritsel) */
  at: [36.2, -33.2],
  model: { url: modelUrl, natural: { width: 6.8, height: 13.0 } },
  /**
   * Xaritadagi o'lchami, metr. width — asosi (maydoncha bilan), height — balandligi.
   * Nisbatni saqlang (height = width × 13 / 6.8), aks holda model cho'ziladi. Asl o'lchami uchun — shu qatorni o'chiring
   */
  size: { width: 11.8, height: 25.0 },
  /** Burilish, gradus (kvadrat asos — 0..90 oralig'ida ma'noli) */
  bearing: 
  65,
});

import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';

/**
 * VR-9D Cinema — planda raqamsiz (avvalgi "Батут" o'rnida; nomi — explication.py → RENAME_UNNAMED).
 * Model: model.py (Blender skripti) → model.glb
 * Asl o'lcham: sahna 9 × 9 m, balandligi 2.9 m. Plandagi maydoncha ~11 × 11 m (45° burilgan kvadrat).
 */
export default defineAttraction({
  /** Plandagi nomi (park.json → attractions[].name) */
  planName: 'VR-9D Cinema',
  name: 'VR-9D Cinema',
  model: { url: modelUrl, natural: { width: 9.0, height: 2.93 } },
  /**
   * Xaritadagi o'lchami, metr. width — sahna tomoni, height — balandligi.
   * Nisbatni saqlang (height = width × 2.93 / 9), aks holda model cho'ziladi. Asl o'lchami uchun — shu qatorni o'chiring
   */
  size: { width: 10.5, height: 3.42 },
  /** Monitor va kabina burni qaragan tomon. Kvadrat maydoncha 45° burilgan: 45, 135, 225 yoki 315 */
  bearing: 315,
  anim: {
    /** Kabina (harakat platformasi) oldinga-orqaga chayqaladi: gradus, bir tebranish soniya, seans soniya */
    swing: { degrees: 6, period: 2.8, cycle: 24 },
  },
});

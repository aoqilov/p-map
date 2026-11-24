import type { TrackData } from '../../map/GltfModel';
import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';
import track from './track.json';

/**
 * 43 — Аттракцион "Cyclon" (spiral coaster). Model va trassa: model.py (Blender skripti) → model.glb + track.json
 * Asl o'lcham: 37.4 × 13.6 m, balandligi 7.6 m. Plandagi maydoncha ~40 × 15 m.
 * Bekat — suv tomondagi uzun tomonda, maydonchaning bir uchida (kirish pandusi shu chetda), spiral — ikkinchi uchida
 * (model.py → MIRROR). Chiqish zinasi — bekatning spiral tomondagi uchida (yo'lovchilar uzun tomon bo'ylab chiqadi).
 */
export default defineAttraction({
  num: '43',
  name: 'Cyclon',
  model: { url: modelUrl, natural: { width: 37.4, height: 7.6 } },
  /**
   * Xaritadagi o'lchami, metr. width — uzun tomoni, height — balandligi.
   * Nisbatni saqlang (height = width × 7.6 / 37.4), aks holda model cho'ziladi. Asl o'lchami uchun — shu qatorni o'chiring
   */
  size: { width: 37.4, height: 7.6 },
  /** Old tomoni (bekat) — g'arbi-shimoli-g'arb, suv tomonga; uzun o'qi plandagi maydoncha bo'ylab (~28°) */
  bearing: 298,
  anim: {
    follow: {
      track: track as TrackData,
      /** Tezlik, m/s: pastda max, eng baland joyda min (ko'tarilishda sekin, spiraldan tez tushadi) */
      speed: { min: 1.6, max: 6.0 },
      /** Bekatda turish (yo'lovchi tushib-chiqishi), soniya */
      dwell: 6,
      /**
       * Vagonlar ulanmagan: har biri o'zi yuradi, bekatda navbat bilan bittadan jo'naydi.
       * gap — oldindagi vagongacha eng kichik masofa, m (vagon uzunligi ~2.5 m)
       */
      independent: { gap: 2.8 },
    },
  },
});

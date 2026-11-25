import { defineDecor } from '../define';
import chapUrl from './chap.glb?url';
import ongUrl from './ong.glb?url';

/**
 * Arkali yo'lak — metall arkalar tunneli, sariq chiroqchalar bilan zich o'ralgan, ikki uchida "soat" kirish arkasi
 * (rasm: foydalanuvchi fotosuratlari). Ikki joyda, ikkalasining kirishi ham chorrahaga qaragan. Bezak: pin va to'siq yo'q,
 * tunnel ichidan yurib o'tiladi. Model: model.py → chap.glb, ong.glb (har biri o'z yo'lagi uzunligi va enida).
 */
export default defineDecor([
  {
    name: "Arkali yo'lak (Водные гусеницы yonida)",
    /** Yo'lak o'rtasi: Paravoz orqasidan (1.6 m keyin) shimoli-sharqqa, Водные гусеницы bilan maysazor orasida */
    at: [-17.92, 98.48],
    /** Kirish — janubi-g'arbga (chorraha, paravoz tomonga) */
    bearing: 221.3,
    /** Asl o'lcham: uzunligi 18 m (eni 5.3 m, kirish arkasi bilan 6.5 m), balandligi 4.4 m */
    model: { url: chapUrl, natural: { width: 18.1, height: 4.44 } },
    clearRadius: 0,
  },
  {
    name: "Arkali yo'lak (Windstarz oldida)",
    /** Yo'lak o'rtasi: chorrahadan janubi-g'arbga, ikki maysazor orasidagi to'g'ri yo'lak */
    at: [-47.87, 64.44],
    /** Kirish — shimoli-sharqqa (chorraha tomonga) */
    bearing: 41.0,
    /** Asl o'lcham: uzunligi 22 m (eni 4.8 m, kirish arkasi bilan 6 m), balandligi 4.2 m */
    model: { url: ongUrl, natural: { width: 22.1, height: 4.19 } },
    clearRadius: 0,
  },
]);

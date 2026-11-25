import { defineAttraction } from "../define";
import modelUrl from "./model.glb?url";

/** 27 — Аттракцион "Windstarz" (Windstar). Model: model.py (Blender skripti) → model.glb */
export default defineAttraction({
  num: "27",
  name: "Windstar",
  model: { url: modelUrl, natural: { width: 16.8, height: 9.6 } },
  /** Kirish (panjaradagi ochiq joy) — janub. Aylana maydonchada yo'nalish muhim emas */
  bearing: 110,
  size: { height: 15.6, width: 22.8 },
  anim: {
    /** Bir aylanish necha soniyada (0 — aylanmaydi) */
    secondsPerTurn: 8,

    /**
     * 6 ta qo'l ko'tariladi: necha gradus, sikl soniya (pastda turish → ko'tarilish → tepada turish → tushish),
     * stagger — har bir keyingi qo'l necha soniya kech (0 — hammasi birga). degrees: 0 — o'chiq
     */
    tilt: { degrees: 40, seconds: 16, stagger: 0 },
  },
});

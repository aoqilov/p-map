import type { TrackData } from "../../map/GltfModel";
import { defineAttraction } from "../define";
import modelUrl from "./model.glb?url";
import track from "./track.json";

/** 45 — Аттракцион "Автодром". Model va mashinalar yo'li: model.py → model.glb + track.json (maydoncha 28 × 16 m) */
export default defineAttraction({
  num: "45",
  name: "Avtodrom",
  model: { url: modelUrl, natural: { width: 28.0, height: 9.6 } },
  /** Old tomoni (panjara, pandus) — janub; uzun o'qi plandagi maydoncha bo'ylab */
  bearing: 166,
  anim: {
    follow: {
      track: track as TrackData,
      /** Mashinalar arena bo'ylab aylanib yuradi, m/s */
      speed: { min: 1.8, max: 1.8 },
      dwell: 0,
    },
  },
});

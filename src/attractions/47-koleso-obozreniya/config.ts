import { defineAttraction } from '../define';
import modelUrl from './model.glb?url';

/** 47 — Аттракцион "Колесо обозрения" (charxpalak). Model: model.py (Blender skripti) → model.glb */
export default defineAttraction({
  num: '47',
  name: 'Koleso obozreniya',
  model: { url: modelUrl, natural: { width: 35.2, height: 37.8 } },
  /** G'ildirak yuzi (pavilyon eshigi, "GO" belgisi) — shu yo'nalishga qaraydi: 156° — janubi-sharq, bosh kirish tomonga */
  bearing: 156,
  anim: {
    /** G'ildirakning bir aylanishi necha soniyada (haqiqiysi ~10–15 daqiqa; xaritada ko'rinsin deb tezroq). 0 — to'xtagan */
    wheel: { secondsPerTurn: 120 },
  },
});

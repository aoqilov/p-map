// Suv: yerdan pastda turgan sath, tosh qirg'oq, jonli sirt (to'lqin, rang, yaltiroq, oqim, kafel, fonus aksi)
// va suv o'simliklari (qamish, nilufar).
//
// Sirt — oddiy MeshStandardMaterial (sahna yorug'ligi va soyalar o'zi ishlaydi), shaderiga onBeforeCompile bilan
// to'lqin normali, rang va yaltiroq qo'shilgan. Haqiqiy aks ettirish (sahnani ikki marta chizish) yo'q — telefon uchun yengil.
import { useEffect, useLayoutEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame, type ThreeEvent } from '@react-three/fiber';
import { STREET_LAMP, WATER, type WaterStyle } from './config';
import { distToPoly, inPoly } from './geo';
import { flat, polyToShape } from './geometry';
import { prefersReducedMotion, useAmbientFrames } from './modelKit';
import { curbTexture } from './pavement';
import { LANTERN_Y } from './StreetLamps';
import type { Palette } from './theme';
import type { Area, ParkData, PoolFx, Poly } from './types';
import { FIELD_OFFSET, buildWaterField } from './waterField';
import { bankGeometry, masonryTexture, tileTexture } from './waterBank';
import type { XY } from './projection';

const LIE_FLAT: [number, number, number] = [-Math.PI / 2, 0, 0];
/** Quyosh yo'nalishi — ParkScene dagi directionalLight bilan bir xil */
const SUN_DIR = new THREE.Vector3(-180, 320, 140).normalize();

export const waterStyleOf = (name: string): WaterStyle => WATER.bodies[name] ?? 'pond';
export const waterLevelOf = (name: string) => WATER.styles[waterStyleOf(name)].level;

/** Polygon (masalan, bino) suv ichida tursa — o'sha suv sathi, aks holda null */
export function waterLevelUnder(poly: Poly, water: Area[]): number | null {
  let level: number | null = null;
  for (const w of water) {
    if (poly[0].some((p) => inPoly(p, w.poly))) level = Math.min(level ?? 0, waterLevelOf(w.name));
  }
  return level;
}

/** Nuqta qaysi suv ustida bo'lsa — o'sha sath, aks holda null */
export function waterLevelAt(p: XY, water: Area[]): number | null {
  const w = water.find((a) => inPoly(p, a.poly));
  return w ? waterLevelOf(w.name) : null;
}

// ---------------------------------------------------------------- shader

const FRAG_HEAD = /* glsl */ `
varying vec3 vWaterW;
uniform float uTime;
uniform sampler2D uField;
uniform vec4 uFieldRect;
uniform float uFieldRange;
uniform float uFieldOffset;
uniform float uCoping;
uniform float uDepthRange;
uniform vec3 uShallow;
uniform vec3 uDeep;
uniform vec3 uRim;
uniform vec3 uSky;
uniform vec3 uGlintColor;
uniform float uGlint;
uniform vec3 uSunDir;
uniform float uSelect;
uniform vec3 uSelectColor;
uniform float uFlowSpeed;
uniform float uLampOn;
uniform float uLampH;
uniform vec3 uLampColor;
#if LAMP_COUNT > 0
uniform vec2 uLamps[LAMP_COUNT];
#endif
// Basseyn bezaklari (data/pools-shape.geojson): jakuzi, zina, tubidagi tasma va chiziqlar, qiya mozaika
uniform vec3 uFxDeep;
uniform vec3 uFxTeal;
#ifdef JAC_COUNT
uniform vec3 uJac[JAC_COUNT];       // x, y, radius
#endif
#ifdef STEP_COUNT
uniform vec4 uSteps[STEP_COUNT];    // x, y, ichki va tashqi radius
uniform float uStepSize[STEP_COUNT];
#endif
#ifdef BAND_N
uniform vec2 uBand[BAND_N];
#endif
#ifdef LINE_N
uniform vec2 uLine[LINE_N];
#endif
#ifdef WATER_STRIPES
uniform vec4 uFrame;                // markaz, uzun o'q
uniform vec2 uFrameSize;            // yarim uzunlik, yarim en
#endif

vec3 wN;
vec3 wAlbedo;
vec3 wEmit;

float wHash(vec2 p) {
  vec3 p3 = fract(vec3(p.xyx) * 0.1031);
  p3 += dot(p3, p3.yzx + 33.33);
  return fract((p3.x + p3.y) * p3.z);
}
// Qiymatli shovqin va uning hosilalari: (qiymat, d/dx, d/dy)
vec3 wNoise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  vec2 du = 6.0 * f * (1.0 - f);
  float a = wHash(i);
  float b = wHash(i + vec2(1.0, 0.0));
  float c = wHash(i + vec2(0.0, 1.0));
  float d = wHash(i + vec2(1.0, 1.0));
  float k1 = b - a, k2 = c - a, k4 = a - b - c + d;
  return vec3(a + k1 * u.x + k2 * u.y + k4 * u.x * u.y, du * vec2(k1 + k4 * u.y, k2 + k4 * u.x));
}
// Bitta to'lqin qatlami. Piksel to'lqindan katta bo'lsa (uzoqdan) — so'nadi, aks holda "qum" bo'lib miltillaydi.
// To'liq so'ngan qatlam umuman hisoblanmaydi: uzoqdan qaralganda GPU deyarli faqat katta to'lqinni hisoblaydi
vec3 wOct(vec2 p, float freq, vec2 dir, float speed, float amp, float px) {
  float lod = 1.0 - smoothstep(0.16, 0.42, px * freq);
  if (lod <= 0.0) return vec3(0.0);
  vec3 n = wNoise(p * freq + dir * (speed * freq * uTime));
  return vec3(n.x - 0.5, n.yz * freq) * amp * lod;
}
vec3 wRipples(vec2 p, float px) {
  vec3 h = wOct(p, 0.07, vec2(0.6, 0.8), 0.25, 1.0, px);         // katta, sekin tolqin (~14 m)
  h += wOct(p + 17.0, 0.24, vec2(0.8, 0.6), 0.35, 0.34, px);     // o'rta (~4 m), ikki yo'nalishda kesishadi
  h += wOct(p + 41.0, 0.24, vec2(-0.6, 0.8), 0.3, 0.34, px);
  h += wOct(p + 7.0, 0.65, vec2(0.3, -0.95), 0.5, 0.12, px);     // mayda jimirlash (~1.5 m)
  h += wOct(p + 3.0, 0.65, vec2(-0.9, -0.4), 0.45, 0.12, px);
  return h;
}

// Siniq chiziqqacha masofa va qaysi tomonda ekani (chap +1 / o'ng −1)
#define POLY_DIST(NAME, ARR, N) float NAME(vec2 p, out float side) { \
  float best = 1e9; side = 1.0; \
  for (int i = 0; i < N - 1; i++) { \
    vec2 a = ARR[i], ab = ARR[i + 1] - ARR[i]; \
    float t = clamp(dot(p - a, ab) / dot(ab, ab), 0.0, 1.0); \
    float d = length(p - a - ab * t); \
    if (d < best) { best = d; side = sign(ab.x * (p.y - a.y) - ab.y * (p.x - a.x)); } \
  } \
  return best; }
#ifdef BAND_N
POLY_DIST(bandDist, uBand, BAND_N)
#endif
#ifdef LINE_N
POLY_DIST(lineDist, uLine, LINE_N)
#endif

void waterSurface() {
  vec2 p = vec2(vWaterW.x, -vWaterW.z);           // metr (x — sharq, y — shimol)
  vec2 fw = fwidth(p);
  float px = max(max(fw.x, fw.y), 1e-4);          // bir piksel necha metr
  vec4 fld = texture2D(uField, (p - uFieldRect.xy) / uFieldRect.zw);
  float shore = max(fld.r * uFieldRange - uFieldOffset - uCoping, 0.0); // ko'rinadigan suv chetidan masofa, m

  vec3 h;
#ifdef WATER_FLOW
  // Oqim xaritasi: ikki faza navbatma-navbat, shunda shovqin cho'zilib ketmaydi
  vec2 fl = fld.gb * 2.0 - 1.0;
  float cyc = 3.0;
  float ph0 = fract(uTime / cyc);
  float ph1 = fract(uTime / cyc + 0.5);
  float wa = 1.0 - abs(2.0 * ph0 - 1.0);
  vec3 ha = wRipples(p - fl * uFlowSpeed * ph0 * cyc, px);
  vec3 hb = wRipples(p - fl * uFlowSpeed * ph1 * cyc + vec2(5.3, 2.9), px);
  h = mix(hb, ha, wa) * 1.3;
#else
  h = wRipples(p, px);
#endif
  wN = normalize(vec3(-h.y * 0.9, 1.0, h.z * 0.9));

  // Sayoz → chuqur
  vec3 col = mix(uShallow, uDeep, smoothstep(0.0, uDepthRange, shore));
  col *= 1.0 + 0.14 * h.x;

  // Kameraga yo'nalish: perspektivda har nuqtadan alohida (pastdan qaraganda uzoq suv osmonni ko'proq aks ettiradi)
  vec3 V = isOrthographic ? normalize(vec3(viewMatrix[0][2], viewMatrix[1][2], viewMatrix[2][2])) : normalize(cameraPosition - vWaterW);
  // Osmon aksi: kameraga qaragan to'lqin yonbag'ri baland (och) osmonni, narigisi qirg'oqdagi daraxtlarni "ko'radi"
  vec2 vh = normalize(V.xz + vec2(1e-5));
  float toward = dot(vec2(wN.x, wN.z), vh);
  col = mix(col, uSky, clamp(0.08 + toward * 1.5, 0.0, 0.26));
  float caus = 0.0;
#ifdef WATER_POOL
  // Tagidagi kafel suv orqali biroz "sinib" ko'rinadi, ustida quyosh to'rlari (kaustika)
  if (px < 0.3) { // uzoqdan kafel va kaustika ko'rinmaydi — hisoblamaymiz
    vec2 q = p + vec2(wN.x, -wN.z) * 0.35;
    vec2 g = abs(fract(q / 0.5) - 0.5);
    float gw = fw.x / 0.5; // hosila shart ichida emas, tashqarida olingan (fwidth shart ichida aniqlanmagan)
    float line = smoothstep(0.455 - gw, 0.475, max(g.x, g.y));
    col = mix(col, col * 1.2 + 0.04, line * 0.5 * (1.0 - smoothstep(0.06, 0.16, px)));
    float c1 = wNoise(q * 0.9 + vec2(0.13, 0.07) * uTime).x;
    float c2 = wNoise(q * 1.1 + 13.0 - vec2(0.09, 0.12) * uTime).x;
    caus = pow(1.0 - abs(c1 - c2), 12.0) * (1.0 - smoothstep(0.08, 0.3, px));
  }
#endif
#ifdef WATER_FLOW
  // Oqim bo'ylab cho'zilgan och izlar
  if (px < 0.6) {
    vec2 fd = normalize(fl + vec2(1e-4));
    vec2 sq = vec2(dot(p, fd), dot(p, vec2(-fd.y, fd.x)));
    float st = wNoise(vec2(sq.x * 0.22 - uTime * uFlowSpeed * 0.22, sq.y * 1.4)).x;
    col = mix(col, uRim, smoothstep(0.7, 0.92, st) * 0.22 * (1.0 - smoothstep(0.2, 0.6, px)));
  }
#endif

  // Basseyn tubidagi bezaklar: suv orqali biroz "sinib" ko'rinadi
  vec2 q2 = p + vec2(wN.x, -wN.z) * 0.3;
#ifdef WATER_STRIPES
  {
    // To'g'ri burchakli basseyn: ikkita qiya to'q tasma, ularda har uchinchi kvadrat firuza
    vec2 d = q2 - uFrame.xy, A = uFrame.zw, B = vec2(-A.y, A.x);
    float u = dot(d, A), v = dot(d, B);
    float s = (u + v) * 0.7071, t = (u - v) * 0.7071;
    float S0 = uFrameSize.x * 0.45, bw = 1.55;
    float inB = max(1.0 - smoothstep(bw, bw + 0.08 + px, abs(s - S0)), 1.0 - smoothstep(bw, bw + 0.08 + px, abs(s + S0)));
    float teal = step(2.0, mod(floor(t / 3.1), 3.0));
    col = mix(col, mix(uFxDeep, uFxTeal, teal), inB * 0.6);
  }
#endif
#ifdef BAND_N
  {
    // Sayoz va chuqur qism orasidagi to'q tasma; tasmaning janubi (o'ng tomoni) sayoz — ochroq
    float side;
    float d = bandDist(q2, side);
    if (side < 0.0) col = mix(col, col * 1.1 + vec3(0.02, 0.07, 0.07), 0.75);
    col = mix(col, uFxDeep, (1.0 - smoothstep(0.42, 0.62 + px, d)) * 0.8);
  }
#endif
#ifdef LINE_N
  {
    float side;
    float d = lineDist(q2, side);
    col = mix(col, vec3(0.93, 0.97, 1.0), (1.0 - smoothstep(0.06, 0.13 + px, d)) * 0.6 * (1.0 - smoothstep(0.12, 0.45, px)));
  }
#endif
#ifdef STEP_COUNT
  for (int i = 0; i < STEP_COUNT; i++) {
    // Zina: konsentrik pog'onalar, chetlari och chiziq, o'zi sayoz (ochroq)
    float r = length(q2 - uSteps[i].xy);
    if (r < uSteps[i].w) {
      float f = (r - uSteps[i].z) / uStepSize[i];
      float edge = 1.0 - smoothstep(0.0, 0.18 + px / uStepSize[i], min(fract(f), 1.0 - fract(f)));
      float on = step(-0.5, f);
      col = mix(col, col * 1.12 + 0.04, 0.6 * on);
      col = mix(col, uRim, edge * 0.5 * on);
    }
  }
#endif
#ifdef JAC_COUNT
  for (int i = 0; i < JAC_COUNT; i++) {
    // Jakuzi: oq devorcha (halqa), ichida ochroq suv va to'xtovsiz pufakchalar
    float R = uJac[i].z;
    float r = length(p - uJac[i].xy);
    if (r < R + 0.4) {
      float rim = 1.0 - smoothstep(0.1, 0.22 + px, abs(r - R));
      float inside = 1.0 - smoothstep(R - 0.25, R, r);
      float b1 = wNoise(p * 3.2 + vec2(uTime * 0.9, -uTime * 0.7)).x;
      float b2 = wNoise(p * 5.5 - vec2(uTime * 1.3, uTime * 0.5)).x;
      float bub = smoothstep(0.58, 0.88, b1 * 0.6 + b2 * 0.5) * inside * (1.0 - smoothstep(0.12, 0.45, px));
      col = mix(col, col * 1.15 + vec3(0.05, 0.08, 0.08), inside * 0.55);
      col = mix(col, vec3(0.95, 0.98, 1.0), max(rim * 0.85, bub * 0.75));
    }
  }
#endif

  // Qirg'oq bo'yidagi och chiziq (devorga urilgan mayda to'lqin)
  float foam = 1.0 - smoothstep(0.0, 0.3 + px * 0.8, shore);
  foam *= 0.6 + 0.4 * sin(uTime * 1.4 + (p.x + p.y) * 0.9);
  col = mix(col, uRim, foam * 0.55);

  col = mix(col, uSelectColor, uSelect * 0.55);
  wAlbedo = col;

  // Quyosh yaltirog'i: mayda to'lqinchalarning quyoshga qaragan yonbag'irlarida, uchqun-uchqun
  wEmit = uRim * caus * 0.2 * uGlint;
  if (px < 0.9) {
    vec3 hg = wOct(p + 29.0, 1.5, vec2(0.7, -0.7), 0.6, 0.06, px);
    vec3 nG = normalize(vec3(-(h.y + hg.y) * 0.9, 1.0, (h.z + hg.z) * 0.9));
    vec3 Hh = normalize(uSunDir + V);
    vec3 Hg = normalize(mix(Hh, vec3(0.0, 1.0, 0.0), 0.62));
    float sp = pow(max(dot(nG, Hg), 0.0), 1600.0);
    wEmit += uGlintColor * sp * uGlint * 1.8 * (1.0 - smoothstep(0.3, 0.9, px));
  }

#if LAMP_COUNT > 0
  // Fonus aksi: suvdan qaytgan nur fonus shishasiga tegsa — yorug' iz. To'lqin uni silkitib, cho'zib turadi
  if (uLampOn > 0.001) {
    vec3 nR = normalize(mix(vec3(0.0, 1.0, 0.0), wN, 0.3));
    vec3 R = reflect(-V, nR);
    float t = uLampH / max(R.y, 0.1);
    vec2 hit = vWaterW.xz + R.xz * t;
    vec2 hd = normalize(V.xz + vec2(1e-5));
    vec2 hq = vec2(-hd.y, hd.x);
    float sum = 0.0;
    for (int i = 0; i < LAMP_COUNT; i++) {
      vec2 d = hit - uLamps[i];
      float a = dot(d, hd), c = dot(d, hq);
      sum += exp(-c * c * 4.0 - a * a * 0.3);
    }
    float shimmer = 0.75 + 0.25 * sin(uTime * 3.0 + p.x * 2.1 + p.y * 1.7);
    wEmit += uLampColor * min(sum, 1.5) * uLampOn * shimmer;
  }
#endif
}
`;

interface WaterUniforms {
  [k: string]: THREE.IUniform;
  uTime: THREE.IUniform<number>;
  uShallow: THREE.IUniform<THREE.Color>;
  uDeep: THREE.IUniform<THREE.Color>;
  uRim: THREE.IUniform<THREE.Color>;
  uSky: THREE.IUniform<THREE.Color>;
  uGlintColor: THREE.IUniform<THREE.Color>;
  uGlint: THREE.IUniform<number>;
  uSelect: THREE.IUniform<number>;
  uSelectColor: THREE.IUniform<THREE.Color>;
  uLampOn: THREE.IUniform<number>;
  uFxDeep: THREE.IUniform<THREE.Color>;
  uFxTeal: THREE.IUniform<THREE.Color>;
}

/** To'rtburchak basseyn o'qlari (qiya mozaika uchun): markaz, uzun o'q, yarim o'lchamlar */
function rectFrameOf(poly: Poly) {
  const r = poly[0].slice(0, -1);
  if (r.length !== 4) return null;
  const e = r.map((p, i) => { const q = r[(i + 1) % 4]; return [q[0] - p[0], q[1] - p[1]]; });
  const len = e.map(([x, y]) => Math.hypot(x, y));
  const k = len[0] + len[2] >= len[1] + len[3] ? 0 : 1;
  const cx = r.reduce((s, p) => s + p[0], 0) / 4, cy = r.reduce((s, p) => s + p[1], 0) / 4;
  return { c: [cx, cy], a: [e[k][0] / len[k], e[k][1] / len[k]], hl: (len[k] + len[k + 2]) / 4, hw: (len[1 - k] + len[3 - k]) / 4 };
}

function makeWaterMaterial(area: Area, style: WaterStyle, lamps: [number, number][], time: THREE.IUniform<number>, fx?: PoolFx) {
  const s = WATER.styles[style];
  const field = buildWaterField(area.poly, style === 'canal' ? { reverse: WATER.canalFlow.reverse } : undefined);
  // Fonus aksi faqat suv bo'yidagi fonuslar uchun (kamera aylanishi mumkin — har tomonga ~9 m)
  const near = lamps.filter((l) => distToPoly(l, area.poly) < 9).slice(0, 32);
  const uniforms: WaterUniforms = {
    uTime: time,
    uField: { value: field.tex },
    uFieldRect: { value: new THREE.Vector4(...field.rect) },
    uFieldRange: { value: field.range },
    uFieldOffset: { value: FIELD_OFFSET },
    uCoping: { value: s.coping },
    uDepthRange: {
      value: style === 'pool' ? Math.min(field.maxDist * 0.7, 4) : style === 'canal' ? field.maxDist : Math.min(field.maxDist * 0.85, 14),
    },
    uShallow: { value: new THREE.Color() },
    uDeep: { value: new THREE.Color() },
    uRim: { value: new THREE.Color() },
    uSky: { value: new THREE.Color() },
    uGlintColor: { value: new THREE.Color() },
    uGlint: { value: 1 },
    uSunDir: { value: SUN_DIR },
    uSelect: { value: 0 },
    uSelectColor: { value: new THREE.Color() },
    uFlowSpeed: { value: WATER.canalFlow.speed },
    uLampOn: { value: 0 },
    uLampH: { value: LANTERN_Y - s.level },
    uLampColor: { value: new THREE.Color(STREET_LAMP.color) },
    uLamps: { value: near.map(([x, y]) => new THREE.Vector2(x, -y)) },
    uFxDeep: { value: new THREE.Color() },
    uFxTeal: { value: new THREE.Color() },
  };
  // Basseyn bezaklari — faqat borlari shaderga kiradi (har biri alohida define)
  const defs: Record<string, string | number> = {
    LAMP_COUNT: near.length,
    ...(style === 'pool' ? { WATER_POOL: '' } : {}),
    ...(style === 'canal' ? { WATER_FLOW: '' } : {}),
  };
  const jac = fx?.jacuzzi.slice(0, 8) ?? [];
  if (jac.length) { defs.JAC_COUNT = jac.length; uniforms.uJac = { value: jac.map(([x, y, r]) => new THREE.Vector3(x, y, r)) }; }
  const steps = fx?.steps.slice(0, 4) ?? [];
  if (steps.length) {
    defs.STEP_COUNT = steps.length;
    uniforms.uSteps = { value: steps.map(([x, y, a, b]) => new THREE.Vector4(x, y, a, b)) };
    uniforms.uStepSize = { value: steps.map((st) => st[4]) };
  }
  const band = fx?.band[0]?.slice(0, 24) ?? [];
  if (band.length > 1) { defs.BAND_N = band.length; uniforms.uBand = { value: band.map(([x, y]) => new THREE.Vector2(x, y)) }; }
  const line = fx?.line[0]?.slice(0, 24) ?? [];
  if (line.length > 1) { defs.LINE_N = line.length; uniforms.uLine = { value: line.map(([x, y]) => new THREE.Vector2(x, y)) }; }
  const frame = fx?.stripes ? rectFrameOf(area.poly) : null;
  if (frame) {
    defs.WATER_STRIPES = '';
    uniforms.uFrame = { value: new THREE.Vector4(frame.c[0], frame.c[1], frame.a[0], frame.a[1]) };
    uniforms.uFrameSize = { value: new THREE.Vector2(frame.hl, frame.hw) };
  }
  const mat = new THREE.MeshStandardMaterial({ roughness: 0.32, metalness: 0 });
  mat.defines = defs;
  mat.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vWaterW;')
      .replace('#include <project_vertex>', '#include <project_vertex>\n  vWaterW = (modelMatrix * vec4(transformed, 1.0)).xyz;');
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>\n${FRAG_HEAD}`)
      .replace('#include <color_fragment>', '#include <color_fragment>\n  waterSurface();\n  diffuseColor.rgb = wAlbedo;')
      .replace('#include <normal_fragment_maps>', '#include <normal_fragment_maps>\n  normal = normalize((viewMatrix * vec4(wN, 0.0)).xyz);')
      .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n  totalEmissiveRadiance += wEmit;');
  };
  return { mat, uniforms, field };
}

const isTap = (e: ThreeEvent<MouseEvent>) => e.delta < 6;

function WaterBody({ area, pal, selected, onSelect, lamps, time, lampOn, night, tex, fx }: {
  area: Area; pal: Palette; selected: boolean; onSelect: (id: string) => void; lamps: [number, number][]; fx?: PoolFx;
  time: THREE.IUniform<number>; lampOn: boolean; night: boolean;
  tex: { curb: THREE.Texture; masonry: THREE.Texture; tile: THREE.Texture };
}) {
  const style = waterStyleOf(area.name);
  const s = WATER.styles[style];
  const surface = useMemo(() => flat(polyToShape(area.poly)), [area]);
  const bank = useMemo(() => bankGeometry(area.poly, { width: s.coping, top: s.copingTop, level: s.level, bottom: s.level - 0.15 }), [area, s]);
  const water = useMemo(() => makeWaterMaterial(area, style, lamps, time, fx), [area, style, lamps, time, fx]);
  useEffect(() => () => {
    surface.dispose(); bank.coping.dispose(); bank.wall.dispose();
    water.mat.dispose(); water.field.tex.dispose();
  }, [surface, bank, water]);

  // Mavzu, tanlash va fonuslar o'zgarganda faqat uniformlar yangilanadi (shader qayta yig'ilmaydi)
  useLayoutEffect(() => {
    const c = pal.water[style];
    const u = water.uniforms;
    u.uShallow.value.set(c.shallow);
    u.uDeep.value.set(c.deep);
    u.uRim.value.set(c.rim);
    u.uSky.value.set(pal.waterSky);
    u.uGlintColor.value.set(pal.glint);
    u.uGlint.value = night ? 0.12 : 1;
    u.uSelect.value = selected ? 1 : 0;
    u.uSelectColor.value.set(pal.selected);
    u.uLampOn.value = lampOn ? 1 : 0;
    u.uFxDeep.value.set(pal.poolMosaic);
    u.uFxTeal.value.set(pal.poolMosaicTeal);
  }, [pal, style, water, selected, lampOn, night]);

  const c = pal.water[style];
  return (
    <group>
      <mesh geometry={surface} material={water.mat} rotation={LIE_FLAT} position-y={s.level} receiveShadow
        onClick={(e) => { if (!isTap(e)) return; e.stopPropagation(); onSelect(area.id); }} />
      <mesh geometry={bank.coping} receiveShadow castShadow>
        <meshStandardMaterial map={tex.curb} color={c.coping} roughness={0.85} />
      </mesh>
      <mesh geometry={bank.wall} receiveShadow castShadow>
        <meshStandardMaterial map={style === 'pool' ? tex.tile : tex.masonry} color={c.wall} vertexColors roughness={0.9} />
      </mesh>
    </group>
  );
}

export function Water({ data, pal, selectedId, onSelect, night, lampsLit }: {
  data: ParkData; pal: Palette; selectedId: string | null; onSelect: (id: string) => void; night: boolean; lampsLit: boolean;
}) {
  const time = useMemo<THREE.IUniform<number>>(() => ({ value: 0 }), []);
  const tex = useMemo(() => ({ curb: curbTexture(), masonry: masonryTexture(), tile: tileTexture() }), []);
  useEffect(() => () => Object.values(tex).forEach((t) => t.dispose()), [tex]);
  const animate = WATER.animate && !prefersReducedMotion();
  useAmbientFrames(animate);
  useFrame((st) => { if (animate) time.value = st.clock.elapsedTime; });
  const lampOn = WATER.lampReflections && night && lampsLit;
  return (
    <>
      {data.water.map((a) => (
        <WaterBody key={a.id} area={a} pal={pal} selected={a.id === selectedId} onSelect={onSelect}
          lamps={data.lamps} time={time} lampOn={lampOn} night={night} tex={tex} fx={data.poolFx?.[a.name]} />
      ))}
    </>
  );
}

// ---------------------------------------------------------------- o'simliklar

/** Bitta qamish to'pi: egilgan barglar + 3 ta qo'g'a (jigarrang boshcha). Balandligi 1 (instance bo'yicha cho'ziladi) */
function reedClumpGeometry() {
  const pos: number[] = [], col: number[] = [];
  let seed = 5;
  const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  const tri = (a: number[], b: number[], c: number[], ca: number[], cb: number[], cc: number[]) => {
    pos.push(...a, ...b, ...c);
    col.push(...ca, ...cb, ...cc);
  };
  const BASE = [0.24, 0.36, 0.13], TIP = [0.62, 0.72, 0.3], DRY = [0.66, 0.58, 0.33];

  const blade = (ang: number, r0: number, h: number, lean: number, w0: number, dry: boolean) => {
    const dx = Math.cos(ang), dz = Math.sin(ang);
    const px = -dz, pz = dx; // eni yo'nalishi
    const T = [0, 0.35, 0.7, 1];
    const pts = T.map((t) => {
      const off = r0 + lean * Math.pow(t, 1.7);
      const w = w0 * Math.pow(1 - t, 0.7) * 0.5;
      const cx = dx * off, cz = dz * off, y = h * t;
      return { l: [cx - px * w, y, cz - pz * w], r: [cx + px * w, y, cz + pz * w] };
    });
    const tip = dry ? DRY : TIP;
    const shade = (t: number) => BASE.map((b, k) => b + (tip[k] - b) * t);
    for (let k = 0; k < T.length - 1; k++) {
      const [a, b] = [pts[k], pts[k + 1]];
      const [ca, cb] = [shade(T[k]), shade(T[k + 1])];
      tri(a.l, a.r, b.r, ca, ca, cb);
      if (k < T.length - 2) tri(a.l, b.r, b.l, ca, cb, cb);
    }
  };
  // Xaritada ko'rinishi uchun barglar haqiqiysidan kengroq (~15 sm), to'p esa yarim metrcha
  for (let k = 0; k < 16; k++) {
    blade((k / 16) * Math.PI * 2 + rnd() * 0.6, 0.03 + rnd() * 0.2, 0.55 + rnd() * 0.45, 0.14 + rnd() * 0.32, 0.13 + rnd() * 0.07, rnd() < 0.2);
  }
  const geoms: THREE.BufferGeometry[] = [];
  const g0 = new THREE.BufferGeometry();
  g0.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g0.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  geoms.push(g0);
  // Qo'g'a: ingichka poya + jigarrang boshcha
  for (let k = 0; k < 3; k++) {
    const a = rnd() * Math.PI * 2, r = 0.05 + rnd() * 0.1, top = 0.95 + rnd() * 0.12;
    const x = Math.cos(a) * r, z = Math.sin(a) * r;
    const stem = new THREE.CylinderGeometry(0.012, 0.018, top, 4, 1, true).translate(x, top / 2, z);
    const head = new THREE.CylinderGeometry(0.055, 0.055, 0.13, 6, 1, true).translate(x, top - 0.1, z);
    const spike = new THREE.ConeGeometry(0.012, 0.07, 4).translate(x, top + 0.0, z);
    for (const [g, c] of [[stem, [0.36, 0.45, 0.2]], [head, [0.36, 0.22, 0.12]], [spike, [0.5, 0.45, 0.3]]] as const) {
      const ng = g.toNonIndexed();
      g.dispose();
      ng.deleteAttribute('uv');
      ng.deleteAttribute('normal');
      const n = ng.attributes.position.count;
      ng.setAttribute('color', new THREE.Float32BufferAttribute(Array.from({ length: n }, () => c).flat(), 3));
      geoms.push(ng);
    }
  }
  const merged = mergeSimple(geoms);
  merged.computeVertexNormals();
  return merged;
}

function mergeSimple(geoms: THREE.BufferGeometry[]) {
  const pos: number[] = [], col: number[] = [];
  for (const g of geoms) {
    pos.push(...(g.attributes.position.array as Float32Array));
    col.push(...(g.attributes.color.array as Float32Array));
    g.dispose();
  }
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  out.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  return out;
}

/** Nilufar bargi: kesigi bor doira, chetlari biroz ko'tarilgan (radius 1) */
function lilyPadGeometry() {
  const notch = 0.42;
  const g = new THREE.CircleGeometry(1, 18, notch / 2, Math.PI * 2 - notch).rotateX(-Math.PI / 2);
  const p = g.attributes.position;
  const col: number[] = [];
  for (let i = 0; i < p.count; i++) {
    const r2 = p.getX(i) ** 2 + p.getZ(i) ** 2;
    p.setY(i, 0.03 * r2);
    const v = 1.08 - 0.25 * r2;
    col.push(v, v, v);
  }
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  g.computeVertexNormals();
  return g;
}

/** Nilufar guli: ikki qavat gulbarg + sariq o'rta (diametri ~0.4 m) */
function lilyFlowerGeometry() {
  const pos: number[] = [], col: number[] = [];
  const petal = (ang: number, len: number, tilt: number, w: number, y0: number) => {
    const dx = Math.cos(ang), dz = Math.sin(ang), px = -dz, pz = dx;
    const ct = Math.cos(tilt), st = Math.sin(tilt);
    const B = [dx * 0.02, y0, dz * 0.02];
    const M = [dx * (0.02 + len * 0.5 * ct), y0 + len * 0.5 * st, dz * (0.02 + len * 0.5 * ct)];
    const T = [dx * (0.02 + len * ct), y0 + len * st, dz * (0.02 + len * ct)];
    const L = [M[0] - px * w, M[1], M[2] - pz * w], R = [M[0] + px * w, M[1], M[2] + pz * w];
    pos.push(...B, ...R, ...T, ...B, ...T, ...L);
    col.push(0.9, 0.9, 0.9, 1, 1, 1, 1, 1, 1, 0.9, 0.9, 0.9, 1, 1, 1, 1, 1, 1);
  };
  for (let k = 0; k < 8; k++) petal((k / 8) * Math.PI * 2, 0.19, 0.35, 0.055, 0.0);
  for (let k = 0; k < 6; k++) petal((k / 6 + 0.08) * Math.PI * 2, 0.13, 0.95, 0.045, 0.02);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  const center = new THREE.CylinderGeometry(0.035, 0.045, 0.06, 6).translate(0, 0.04, 0).toNonIndexed();
  center.deleteAttribute('uv');
  center.deleteAttribute('normal');
  center.setAttribute('color', new THREE.Float32BufferAttribute(
    Array.from({ length: center.attributes.position.count }, () => [1, 0.8, 0.22]).flat(), 3));
  const merged = mergeSimple([g, center]);
  merged.computeVertexNormals();
  return merged;
}

/** Qamish shamolda tebranadi: balandlikka qarab (tagi joyida, uchi ko'proq) */
function swayMaterial(time: THREE.IUniform<number>) {
  const mat = new THREE.MeshStandardMaterial({ vertexColors: true, side: THREE.DoubleSide, roughness: 0.85 });
  mat.onBeforeCompile = (shader) => {
    shader.uniforms.uTime = time;
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nuniform float uTime;')
      .replace('#include <begin_vertex>', `#include <begin_vertex>
  #ifdef USE_INSTANCING
  vec2 iph = vec2(instanceMatrix[3].x, instanceMatrix[3].z);
  #else
  vec2 iph = vec2(0.0);
  #endif
  float sh = max(transformed.y, 0.0);
  float sw = sin(uTime * 1.6 + iph.x * 0.35 + iph.y * 0.27) + 0.45 * sin(uTime * 2.7 + iph.x * 0.9 - iph.y * 0.5);
  transformed.x += sw * 0.07 * sh * sh;
  transformed.z += sw * 0.035 * sh * sh;`);
  };
  return mat;
}

export function WaterPlants({ data, pal }: { data: ParkData; pal: Palette }) {
  const { reeds, lilies } = data.plants;
  const flowers = useMemo(() => lilies.filter((l) => l[4] > 0), [lilies]);
  const time = useMemo<THREE.IUniform<number>>(() => ({ value: 0 }), []);
  const geo = useMemo(() => ({ reed: reedClumpGeometry(), pad: lilyPadGeometry(), flower: lilyFlowerGeometry() }), []);
  const reedMat = useMemo(() => swayMaterial(time), [time]);
  useEffect(() => () => { Object.values(geo).forEach((g) => g.dispose()); reedMat.dispose(); }, [geo, reedMat]);
  const animate = WATER.animate && !prefersReducedMotion();
  useFrame((st) => { if (animate) time.value = st.clock.elapsedTime; });

  const reedRef = useRef<THREE.InstancedMesh>(null!);
  const padRef = useRef<THREE.InstancedMesh>(null!);
  const flowerRef = useRef<THREE.InstancedMesh>(null!);

  useLayoutEffect(() => {
    const m = new THREE.Matrix4(), q = new THREE.Quaternion(), up = new THREE.Vector3(0, 1, 0), c = new THREE.Color();
    const level = (x: number, y: number) => waterLevelAt([x, y], data.water) ?? 0;
    reeds.forEach(([x, y, h, rot], i) => {
      const s = 0.9 + ((h * 7.3) % 0.3);
      m.compose(new THREE.Vector3(x, level(x, y) - 0.05, -y), q.setFromAxisAngle(up, rot), new THREE.Vector3(s, h, s));
      reedRef.current.setMatrixAt(i, m);
    });
    lilies.forEach(([x, y, r, rot], i) => {
      m.compose(new THREE.Vector3(x, level(x, y) + 0.012, -y), q.setFromAxisAngle(up, rot), new THREE.Vector3(r, 1, r));
      padRef.current.setMatrixAt(i, m);
      padRef.current.setColorAt(i, c.set(pal.lily[i % pal.lily.length]));
    });
    flowers.forEach(([x, y, r, rot, kind], i) => {
      // Gul bargning kesigiga qarama-qarshi tomonida
      const ox = -Math.cos(rot) * r * 0.25, oz = Math.sin(rot) * r * 0.25;
      const s = 0.85 + (r - 0.3) * 0.6;
      m.compose(new THREE.Vector3(x + ox, level(x, y) + 0.03, -y + oz), q.setFromAxisAngle(up, rot * 2.1), new THREE.Vector3(s, s, s));
      flowerRef.current.setMatrixAt(i, m);
      flowerRef.current.setColorAt(i, c.set(kind === 1 ? '#f6a8c8' : '#fbf8f3'));
    });
    for (const ref of [reedRef, padRef, flowerRef]) {
      ref.current.instanceMatrix.needsUpdate = true;
      if (ref.current.instanceColor) ref.current.instanceColor.needsUpdate = true;
      ref.current.computeBoundingSphere();
    }
  }, [reeds, lilies, flowers, pal, data.water]);

  useEffect(() => { reedMat.color.set(pal.plantTint); }, [reedMat, pal]);

  return (
    <>
      <instancedMesh ref={reedRef} args={[geo.reed, reedMat, Math.max(reeds.length, 1)]} count={reeds.length} />
      <instancedMesh ref={padRef} args={[geo.pad, undefined, Math.max(lilies.length, 1)]} count={lilies.length} receiveShadow>
        <meshStandardMaterial vertexColors roughness={0.6} color={pal.plantTint} />
      </instancedMesh>
      <instancedMesh ref={flowerRef} args={[geo.flower, undefined, Math.max(flowers.length, 1)]} count={flowers.length}>
        <meshStandardMaterial vertexColors roughness={0.7} side={THREE.DoubleSide} color={pal.plantTint} />
      </instancedMesh>
    </>
  );
}

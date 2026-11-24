// Xarita kamerasi va imo-ishoralar (Google Maps uslubida). MapControls o'rniga — mobil uchun burash va qiyalatish bilan.
//
// Ko'rinish (View): kamera yerdagi `target` nuqtaga qaraydi, undan `dist` metr uzoqda, vertikaldan `polar` burchakda
// (0 — tepadan, ~80° — yerga yaqin), `az` — gorizontal burilish. Dunyo koordinatasi: X — sharq, Y — balandlik, Z — janub.
//
// Sensorli ekran: 1 barmoq — surish (inersiya bilan), 2 barmoq — chimdish (zoom), burash (aylantirish), birga tepaga/pastga
// surish (qiyalatish); ikki marta tegish — yaqinlashtirish. Sichqoncha: chap — surish, o'ng (yoki Ctrl/Shift + chap) —
// aylantirish va qiyalatish, g'ildirak — kursor tomonga zoom, ikki marta bosish — yaqinlashtirish.
import * as THREE from 'three';

export interface View { tx: number; tz: number; dist: number; polar: number; az: number }

export interface Limits {
  minDist: number;
  maxDist: number;
  minPolar: number;
  maxPolar: number;
  /** Uzoqlikka qarab qiyalik chegarasi (uzoqdan juda qiya qaralsa, park ingichka chiziq bo'lib qoladi) */
  maxPolarAt?: (dist: number) => number;
  /** Kamera yerdan kamida shuncha balandda (m) */
  minHeight: number;
  /** Markaz (target) chegarasi, dunyo koordinatasida */
  bounds: { minX: number; maxX: number; minZ: number; maxZ: number };
}

const clamp = THREE.MathUtils.clamp;
const wrap = (a: number) => Math.atan2(Math.sin(a), Math.cos(a));

/** Kamerani ko'rinishga qo'yish. near/far masofaga qarab — uzoqdan qaraganda ham qatlamlar bir-biriga "tirqishmaydi" */
export function applyView(cam: THREE.PerspectiveCamera, v: View) {
  const sp = Math.sin(v.polar), cp = Math.cos(v.polar), sa = Math.sin(v.az), ca = Math.cos(v.az);
  cam.position.set(v.tx + v.dist * sp * sa, v.dist * cp, v.tz + v.dist * sp * ca);
  // Bazis to'g'ridan-to'g'ri: tepadan qaraganda ham (polar = 0) lookAt kabi aynimaydi
  const f = new THREE.Vector3(-sp * sa, -cp, -sp * ca);
  const r = new THREE.Vector3(ca, 0, -sa);
  const u = new THREE.Vector3().crossVectors(r, f);
  cam.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(r, u, f.negate()));
  const near = clamp(v.dist * 0.03, 0.2, 25);
  const far = v.dist * 14 + 3000;
  if (Math.abs(cam.near - near) > 1e-3 || cam.far !== far) {
    cam.near = near;
    cam.far = far;
    cam.updateProjectionMatrix();
  }
  cam.updateMatrixWorld();
}

const ray = new THREE.Raycaster();
const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
/** Ekran nuqtasi (CSS px, element ichida) ostidagi yer nuqtasi; ufqdan yuqori yoki juda uzoq bo'lsa — null */
export function groundAt(cam: THREE.PerspectiveCamera, x: number, y: number, w: number, h: number, maxDist = Infinity) {
  ray.setFromCamera(new THREE.Vector2((x / w) * 2 - 1, -((y / h) * 2 - 1)), cam);
  const hit = ray.ray.intersectPlane(plane, new THREE.Vector3());
  if (!hit || hit.distanceTo(cam.position) > maxDist) return null;
  return hit;
}

type P = { x: number; y: number };

/** Sichqoncha kursori holati (konteynerning data-cursor atributi, ko'rinishi styles.css da) */
export type MapCursor = 'grab' | 'grabbing' | 'rotate' | 'tilt' | 'zoom-in' | 'zoom-out' | 'pointer';

export class MapGestures {
  view: View;
  private ptrs = new Map<number, P & { type: string }>();
  private captured = new Set<number>();
  private mode: 'none' | 'pan' | 'orbit' | 'two' = 'none';
  private anchor: THREE.Vector3 | null = null;
  private last: P = { x: 0, y: 0 };
  private two: { a: P; b: P; s0a: P; s0b: P; kind: 'undecided' | 'tilt' | 'transform' } | null = null;
  private vel = { x: 0, z: 0 };
  private lastMoveT = 0;
  private fling = 0;
  private lastTap = { t: 0, x: 0, y: 0 };
  private downAt = { t: 0, x: 0, y: 0 };
  // Kursor: joyiga (bosiladigan obyekt ustida — qo'l) va qilinayotgan ishga (surish, aylantirish, qiyalatish, zoom) qarab
  private mouseDrag = false;
  private hoverPos: P | null = null;
  private hoverHit = false;
  private hoverAt = 0;
  private modKey = false;
  private zoomCur: { dir: number; until: number } | null = null;
  private cursorTimer: ReturnType<typeof setTimeout> | undefined;
  private orbitAxis: 'rotate' | 'tilt' = 'rotate';
  private orbitAcc = { x: 0, y: 0 };
  /** Ekran nuqtasida bosiladigan obyekt bormi (kursor "qo'l" bo'lishi uchun) */
  hoverTest: ((x: number, y: number) => boolean) | null = null;
  /** O'chiq bo'lsa (masalan, 3-shaxs yurish rejimi) — imo-ishoralarni tinglamaydi */
  private enabled = true;
  setEnabled(on: boolean) {
    if (on === this.enabled) return;
    this.enabled = on;
    this.ptrs.clear();
    this.captured.clear();
    this.mode = 'none';
    this.two = null;
    this.mouseDrag = false;
    cancelAnimationFrame(this.fling);
    this.refreshCursor();
  }

  constructor(
    private cam: THREE.PerspectiveCamera,
    private dom: HTMLElement,
    private limits: () => Limits,
    private cb: { change: () => void; start: () => void; zoomTap: (x: number, y: number) => void },
    view: View,
  ) {
    this.view = { ...view };
    dom.style.touchAction = 'none';
    dom.addEventListener('pointerdown', this.onDown);
    dom.addEventListener('pointermove', this.onMove);
    dom.addEventListener('pointerup', this.onUp);
    dom.addEventListener('pointercancel', this.onUp);
    dom.addEventListener('wheel', this.onWheel, { passive: false });
    dom.addEventListener('contextmenu', this.onContext);
    dom.addEventListener('dblclick', this.onDbl);
    dom.addEventListener('pointerleave', this.onLeave);
    window.addEventListener('keydown', this.onKey);
    window.addEventListener('keyup', this.onKey);
    window.addEventListener('blur', this.onBlur);
    this.refreshCursor();
  }

  dispose() {
    const d = this.dom;
    d.removeEventListener('pointerdown', this.onDown);
    d.removeEventListener('pointermove', this.onMove);
    d.removeEventListener('pointerup', this.onUp);
    d.removeEventListener('pointercancel', this.onUp);
    d.removeEventListener('wheel', this.onWheel);
    d.removeEventListener('contextmenu', this.onContext);
    d.removeEventListener('dblclick', this.onDbl);
    d.removeEventListener('pointerleave', this.onLeave);
    window.removeEventListener('keydown', this.onKey);
    window.removeEventListener('keyup', this.onKey);
    window.removeEventListener('blur', this.onBlur);
    cancelAnimationFrame(this.fling);
    clearTimeout(this.cursorTimer);
    delete d.dataset.cursor;
  }

  // ---- Kursor ----
  private refreshCursor() {
    let c: MapCursor = 'grab';
    if (this.mouseDrag && this.mode === 'pan') c = 'grabbing';
    else if (this.mouseDrag && this.mode === 'orbit') c = this.orbitAxis;
    else if (this.zoomCur && performance.now() < this.zoomCur.until) c = this.zoomCur.dir > 0 ? 'zoom-in' : 'zoom-out';
    else if (this.modKey && this.hoverPos) c = 'rotate'; // Ctrl/Shift bosib turilsa — sudrash aylantirishini ko'rsatamiz
    else if (this.hoverHit) c = 'pointer';
    if (this.dom.dataset.cursor !== c) this.dom.dataset.cursor = c;
  }
  private testHover(p: P, force = false) {
    const now = performance.now();
    if (!force && now - this.hoverAt < 60) return; // raycast har harakatda emas
    this.hoverAt = now;
    this.hoverHit = !!this.hoverTest?.(p.x, p.y);
  }
  private onLeave = () => { this.hoverPos = null; this.hoverHit = false; this.refreshCursor(); };
  private onKey = (e: KeyboardEvent) => {
    const m = e.ctrlKey || e.metaKey || e.shiftKey;
    if (m !== this.modKey) { this.modKey = m; this.refreshCursor(); }
  };
  private onBlur = () => { this.modKey = false; this.refreshCursor(); };

  /** Ko'rinishni o'rnatish (chegaralar bilan) */
  set(v: Partial<View>, notify = true) {
    Object.assign(this.view, v);
    this.clampView();
    applyView(this.cam, this.view);
    if (notify) this.cb.change();
  }

  get busy() { return this.ptrs.size > 0; }

  private clampView() {
    const L = this.limits(), v = this.view;
    v.dist = clamp(v.dist, Math.max(L.minDist, L.minHeight), L.maxDist);
    // Yaqindan pastdan qaraganda kamera yerga kirib ketmasin
    const maxP = Math.min(L.maxPolar, L.maxPolarAt ? L.maxPolarAt(v.dist) : Infinity, Math.acos(clamp(L.minHeight / v.dist, 0, 1)));
    v.polar = clamp(v.polar, L.minPolar, Math.max(L.minPolar, maxP));
    v.az = wrap(v.az);
    v.tx = clamp(v.tx, L.bounds.minX, L.bounds.maxX);
    v.tz = clamp(v.tz, L.bounds.minZ, L.bounds.maxZ);
  }

  private rect() { return this.dom.getBoundingClientRect(); }
  private local(e: { clientX: number; clientY: number }): P {
    const r = this.rect();
    return { x: e.clientX - r.left, y: e.clientY - r.top };
  }
  private ground(p: P) {
    const r = this.rect();
    return groundAt(this.cam, p.x, p.y, r.width, r.height, this.view.dist * 8 + 400);
  }

  /** Yer nuqtasi `g` atrofida masshtab: g ekranda joyida qoladi */
  zoomAbout(g: THREE.Vector3 | null, f: number) {
    const v = this.view, L = this.limits();
    const d1 = clamp(v.dist * f, Math.max(L.minDist, L.minHeight), L.maxDist);
    const k = d1 / v.dist;
    if (g) { v.tx = g.x + (v.tx - g.x) * k; v.tz = g.z + (v.tz - g.z) * k; }
    v.dist = d1;
    this.set({});
  }

  /** Yer nuqtasi `g` atrofida vertikal o'q bo'yicha burish */
  private rotateAbout(g: THREE.Vector3 | null, ang: number) {
    const v = this.view;
    if (g) {
      const c = Math.cos(ang), s = Math.sin(ang);
      const dx = v.tx - g.x, dz = v.tz - g.z;
      v.tx = g.x + dx * c + dz * s;
      v.tz = g.z - dx * s + dz * c;
    }
    v.az += ang;
  }

  /** Ekrandagi `from` ostidagi yer nuqtasi `to` ostiga o'tsin (surish) */
  private panScreen(from: THREE.Vector3 | null, to: P) {
    if (!from) return;
    const g = this.ground(to);
    if (!g) return;
    let dx = from.x - g.x, dz = from.z - g.z;
    const m = Math.hypot(dx, dz), lim = this.view.dist * 0.8;
    if (m > lim) { dx *= lim / m; dz *= lim / m; } // ufq yaqinida keskin sakramasin
    this.view.tx += dx;
    this.view.tz += dz;
    const now = performance.now(), dt = Math.max((now - this.lastMoveT) / 1000, 1 / 120);
    // Inersiya uchun tezlik (silliqlangan)
    this.vel.x = this.vel.x * 0.6 + (dx / dt) * 0.4;
    this.vel.z = this.vel.z * 0.6 + (dz / dt) * 0.4;
    this.lastMoveT = now;
  }

  private onContext = (e: Event) => e.preventDefault();

  private onDown = (e: PointerEvent) => {
    if (!this.enabled) return;
    cancelAnimationFrame(this.fling);
    const p = this.local(e);
    this.ptrs.set(e.pointerId, { ...p, type: e.pointerType });
    this.cb.start();
    if (this.ptrs.size === 1) {
      this.downAt = { t: performance.now(), ...p };
      const orbit = e.pointerType === 'mouse' && (e.button === 2 || e.ctrlKey || e.metaKey || e.shiftKey);
      this.beginOne(p, orbit ? 'orbit' : 'pan');
      this.mouseDrag = e.pointerType === 'mouse';
      this.orbitAxis = 'rotate';
      this.orbitAcc = { x: 0, y: 0 };
      this.refreshCursor();
    } else if (this.ptrs.size === 2) {
      const [a, b] = [...this.ptrs.values()];
      this.two = { a: { ...a }, b: { ...b }, s0a: { ...a }, s0b: { ...b }, kind: 'undecided' };
      this.mode = 'two';
    }
  };

  private beginOne(p: P, mode: 'pan' | 'orbit') {
    this.mode = mode;
    this.last = p;
    this.anchor = mode === 'pan' ? this.ground(p) : null;
    this.vel = { x: 0, z: 0 };
    this.lastMoveT = performance.now();
  }

  private onMove = (e: PointerEvent) => {
    if (!this.enabled) return;
    const old = this.ptrs.get(e.pointerId);
    if (!old) {
      // Tugmasiz harakat (sichqoncha): ostida bosiladigan obyekt bo'lsa — qo'l kursor
      if (e.pointerType === 'mouse') {
        this.hoverPos = this.local(e);
        this.modKey = e.ctrlKey || e.metaKey || e.shiftKey;
        this.testHover(this.hoverPos);
        this.refreshCursor();
      }
      return;
    }
    const p = this.local(e);
    this.ptrs.set(e.pointerId, { ...p, type: old.type });
    const v = this.view;
    // Sudrash boshlangandagina ushlab olamiz: oddiy bosish pin tugmasiga "click" bo'lib yetib borsin
    if (!this.captured.has(e.pointerId) && Math.hypot(p.x - old.x, p.y - old.y) + Math.hypot(p.x - this.downAt.x, p.y - this.downAt.y) > 4) {
      this.captured.add(e.pointerId);
      try { this.dom.setPointerCapture(e.pointerId); } catch { /* sintetik hodisalar */ }
    }

    if (this.mode === 'pan') {
      this.panScreen(this.anchor, p);
      this.set({});
    } else if (this.mode === 'orbit') {
      const dx = p.x - this.last.x, dy = p.y - this.last.y;
      this.last = p;
      // Kursor: asosan chapga-o'ngga — aylantirish, tepaga-pastga — qiyalatish
      this.orbitAcc = { x: this.orbitAcc.x * 0.8 + Math.abs(dx), y: this.orbitAcc.y * 0.8 + Math.abs(dy) };
      const axis = this.orbitAcc.y > this.orbitAcc.x * 1.3 ? 'tilt' : this.orbitAcc.x > this.orbitAcc.y * 1.3 ? 'rotate' : this.orbitAxis;
      if (axis !== this.orbitAxis) { this.orbitAxis = axis; this.refreshCursor(); }
      // Ekran markazi atrofida: o'ngga — soat yo'nalishida, tepaga — ko'proq qiya (yerga yaqin)
      const r = this.rect();
      this.rotateAbout(this.ground({ x: r.width / 2, y: r.height / 2 }), dx * 0.006);
      v.polar -= dy * 0.005;
      this.set({});
    } else if (this.mode === 'two' && this.two && this.ptrs.size >= 2) {
      const [a, b] = [...this.ptrs.values()];
      const t = this.two;
      if (t.kind === 'undecided') {
        const da = { x: a.x - t.s0a.x, y: a.y - t.s0a.y }, db = { x: b.x - t.s0b.x, y: b.y - t.s0b.y };
        const moved = Math.hypot(da.x, da.y) + Math.hypot(db.x, db.y);
        if (moved > 14) {
          const sep0 = Math.hypot(t.s0a.x - t.s0b.x, t.s0a.y - t.s0b.y), sep1 = Math.hypot(a.x - b.x, a.y - b.y);
          const vertical = Math.abs(da.y) > 1.6 * Math.abs(da.x) && Math.abs(db.y) > 1.6 * Math.abs(db.x) &&
            Math.sign(da.y) === Math.sign(db.y) && Math.abs(sep1 - sep0) < 0.35 * moved;
          t.kind = vertical ? 'tilt' : 'transform';
          // Qaror qabul qilinguncha bo'lgan harakat ham hisobga olinsin (burash/qiyalik "yo'qolmasin")
          t.a = { ...t.s0a };
          t.b = { ...t.s0b };
        }
      }
      if (t.kind === 'tilt') {
        const dy = ((a.y - t.a.y) + (b.y - t.b.y)) / 2;
        v.polar -= dy * 0.0055; // barmoqlar tepaga — yerga yaqinroq (ko'proq qiya)
        this.set({});
      } else if (t.kind === 'transform') {
        const m0 = { x: (t.a.x + t.b.x) / 2, y: (t.a.y + t.b.y) / 2 }, m1 = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
        // 1) surish: barmoqlar o'rtasi ostidagi nuqta ular bilan birga yuradi
        this.panScreen(this.ground(m0), m1);
        this.set({}, false);
        const g = this.ground(m1);
        // 2) burash
        const ang = wrap(Math.atan2(b.y - a.y, b.x - a.x) - Math.atan2(t.b.y - t.a.y, t.b.x - t.a.x));
        this.rotateAbout(g, ang);
        // 3) chimdish
        const s0 = Math.hypot(t.b.x - t.a.x, t.b.y - t.a.y), s1 = Math.hypot(b.x - a.x, b.y - a.y);
        if (s1 > 4 && s0 > 4) this.zoomAbout(g, s0 / s1);
        else this.set({});
      }
      t.a = { ...a };
      t.b = { ...b };
    }
  };

  private onUp = (e: PointerEvent) => {
    if (!this.enabled) { this.ptrs.delete(e.pointerId); return; }
    const had = this.ptrs.get(e.pointerId);
    this.ptrs.delete(e.pointerId);
    if (this.captured.delete(e.pointerId)) { try { this.dom.releasePointerCapture(e.pointerId); } catch { /* */ } }
    if (!had) return;
    if (this.ptrs.size === 1) {
      // Ikkinchi barmoq ko'tarildi — qolgani bilan surishni davom ettiramiz (sakramasdan)
      const [rest] = [...this.ptrs.values()];
      this.two = null;
      this.beginOne(rest, 'pan');
      return;
    }
    if (this.ptrs.size > 0) return;
    const p = this.local(e);
    // Sensorli ekranda ikki marta tegish — yaqinlashtirish (sichqonchada dblclick bor)
    const now = performance.now();
    const tap = now - this.downAt.t < 260 && Math.hypot(p.x - this.downAt.x, p.y - this.downAt.y) < 10;
    if (tap && had.type !== 'mouse') {
      if (now - this.lastTap.t < 320 && Math.hypot(p.x - this.lastTap.x, p.y - this.lastTap.y) < 30) {
        this.lastTap.t = 0;
        this.cb.zoomTap(p.x, p.y);
      } else this.lastTap = { t: now, x: p.x, y: p.y };
    }
    // Inersiya: tez surib qo'yib yuborilsa, xarita biroz sirpanib to'xtaydi
    if (this.mode === 'pan' && now - this.lastMoveT < 60 && Math.hypot(this.vel.x, this.vel.z) > this.view.dist * 0.15) {
      let prev = now;
      const step = (t: number) => {
        const dt = Math.min((t - prev) / 1000, 0.05);
        prev = t;
        const k = Math.exp(-dt / 0.32);
        this.vel.x *= k; this.vel.z *= k;
        this.set({ tx: this.view.tx + this.vel.x * dt, tz: this.view.tz + this.vel.z * dt });
        if (Math.hypot(this.vel.x, this.vel.z) > this.view.dist * 0.02) this.fling = requestAnimationFrame(step);
      };
      this.fling = requestAnimationFrame(step);
    }
    this.mode = 'none';
    this.two = null;
    if (had.type === 'mouse') {
      this.mouseDrag = false;
      this.hoverPos = p;
      this.testHover(p, true);
      this.refreshCursor();
    }
  };

  private onWheel = (e: WheelEvent) => {
    if (!this.enabled) return;
    e.preventDefault();
    cancelAnimationFrame(this.fling);
    this.cb.start();
    const dy = e.deltaMode === 1 ? e.deltaY * 40 : e.deltaMode === 2 ? e.deltaY * 800 : e.deltaY;
    // Kursor qisqa vaqt "lupa +/−" bo'lib turadi
    this.zoomCur = { dir: dy < 0 ? 1 : -1, until: performance.now() + 380 };
    this.refreshCursor();
    clearTimeout(this.cursorTimer);
    this.cursorTimer = setTimeout(() => { this.zoomCur = null; if (this.hoverPos) this.testHover(this.hoverPos, true); this.refreshCursor(); }, 400);
    // Trackpad chimdishi brauzerda ctrl+wheel bo'lib keladi — u ham zoom
    this.zoomAbout(this.ground(this.local(e)), Math.exp(clamp(dy, -200, 200) * (e.ctrlKey ? 0.01 : 0.0018)));
  };

  private onDbl = (e: MouseEvent) => {
    if (!this.enabled) return;
    const p = this.local(e);
    this.cb.zoomTap(p.x, p.y);
  };
}

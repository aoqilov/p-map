import { useCallback, useEffect, useRef, useState } from 'react';
import { LOCATION } from './config';
import { project, type XY } from './projection';

export type LocationStatus = 'off' | 'locating' | 'active' | 'denied' | 'unavailable' | 'error';
export type LocationSource = 'gps' | 'telegram' | 'simulation';

export interface UserFix {
  /** Park markaziga nisbatan metr */
  xy: XY;
  /** Aniqlik radiusi, metr */
  accuracy: number | null;
  /** Harakat yo'nalishi, shimoldan soat strelkasi bo'yicha (gradus); turganda null */
  heading: number | null;
  time: number;
  source: LocationSource;
}

// --- Telegram Mini Apps: WebApp.LocationManager (Bot API 8.0+) ---
interface TgLocationData {
  latitude: number;
  longitude: number;
  course: number | null;
  horizontal_accuracy: number | null;
}
interface TgLocationManager {
  isInited: boolean;
  isLocationAvailable: boolean;
  isAccessGranted: boolean;
  init(cb?: () => void): TgLocationManager;
  getLocation(cb: (data: TgLocationData | null) => void): TgLocationManager;
  openSettings(): TgLocationManager;
}
interface TgWebApp {
  LocationManager?: TgLocationManager;
  isVersionAtLeast?(version: string): boolean;
}

/** Telegram ichida ochilgan va LocationManager mavjud bo'lsa — uni qaytaradi */
export function telegramLocation(): TgLocationManager | null {
  const wa = (window as unknown as { Telegram?: { WebApp?: TgWebApp } }).Telegram?.WebApp;
  return wa?.LocationManager && wa.isVersionAtLeast?.('8.0') ? wa.LocationManager : null;
}

/**
 * Mijoz joylashuvini kuzatish.
 * - Telegram'da: LocationManager.getLocation (bir martalik) — LOCATION.telegramPollMs da qayta so'raladi
 * - Brauzerda: navigator.geolocation.watchPosition (HTTPS talab qilinadi)
 * - Simulyatsiya: berilgan yo'l bo'ylab yurish (sinov va demo uchun)
 * Koordinatalar hech qayerga yuborilmaydi, faqat qurilmada ishlatiladi.
 */
export function useUserLocation() {
  const [status, setStatus] = useState<LocationStatus>('off');
  const [fix, setFix] = useState<UserFix | null>(null);
  const stopRef = useRef<() => void>(() => {});

  const accept = useCallback((f: UserFix) => {
    setFix(f);
    setStatus('active');
  }, []);

  const stop = useCallback(() => {
    stopRef.current();
    stopRef.current = () => {};
    setFix(null);
    setStatus('off');
  }, []);

  const start = useCallback(() => {
    stopRef.current();
    setFix(null);
    setStatus('locating');

    const tg = telegramLocation();
    if (tg) {
      let cancelled = false;
      let timer = 0;
      const poll = () =>
        tg.getLocation((d) => {
          if (cancelled) return;
          if (!d) {
            setStatus(tg.isLocationAvailable ? 'denied' : 'unavailable');
            return;
          }
          accept({
            xy: project([d.longitude, d.latitude]),
            accuracy: d.horizontal_accuracy,
            heading: d.course,
            time: Date.now(),
            source: 'telegram',
          });
          timer = window.setTimeout(poll, LOCATION.telegramPollMs);
        });
      if (tg.isInited) poll();
      else tg.init(poll);
      stopRef.current = () => {
        cancelled = true;
        clearTimeout(timer);
      };
      return;
    }

    if (!('geolocation' in navigator)) {
      setStatus('unavailable');
      return;
    }
    const id = navigator.geolocation.watchPosition(
      (p) =>
        accept({
          xy: project([p.coords.longitude, p.coords.latitude]),
          accuracy: p.coords.accuracy,
          heading: p.coords.heading !== null && Number.isFinite(p.coords.heading) ? p.coords.heading : null,
          time: p.timestamp,
          source: 'gps',
        }),
      (e) => {
        // TIMEOUT'da kuzatuv davom etadi, keyingi muvaffaqiyatli o'lchov holatni 'active' qiladi
        if (e.code === e.PERMISSION_DENIED) setStatus('denied');
        else if (e.code === e.POSITION_UNAVAILABLE) setStatus('unavailable');
        else setStatus((s) => (s === 'active' ? s : 'error'));
      },
      { enableHighAccuracy: true, maximumAge: 2000, timeout: 20000 },
    );
    stopRef.current = () => navigator.geolocation.clearWatch(id);
  }, [accept]);

  /** Berilgan yo'l bo'ylab yurishni taqlid qilish (aylanib qaytadi) */
  const simulate = useCallback(
    (path: XY[]) => {
      stopRef.current();
      if (path.length < 2) return;
      const cum = [0];
      for (let i = 1; i < path.length; i++) {
        cum.push(cum[i - 1] + Math.hypot(path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1]));
      }
      const total = cum[cum.length - 1];
      const t0 = performance.now();
      let timer = 0;
      const tick = () => {
        const s = (((performance.now() - t0) / 1000) * LOCATION.simulationSpeed) % total;
        let i = 1;
        while (i < cum.length - 1 && cum[i] < s) i++;
        const [a, b] = [path[i - 1], path[i]];
        const k = (s - cum[i - 1]) / Math.max(cum[i] - cum[i - 1], 1e-6);
        const jitter = () => (Math.random() - 0.5) * 2; // GPS "titrashi" ±1 m
        accept({
          xy: [a[0] + (b[0] - a[0]) * k + jitter(), a[1] + (b[1] - a[1]) * k + jitter()],
          accuracy: 5 + Math.random() * 3,
          heading: ((Math.atan2(b[0] - a[0], b[1] - a[1]) * 180) / Math.PI + 360) % 360,
          time: Date.now(),
          source: 'simulation',
        });
        timer = window.setTimeout(tick, 1000);
      };
      tick();
      stopRef.current = () => clearTimeout(timer);
    },
    [accept],
  );

  useEffect(() => () => stopRef.current(), []);

  return { status, fix, start, stop, simulate };
}

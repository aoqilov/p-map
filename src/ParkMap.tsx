import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import parkJson from './map/park.json';
import { HOME_VIEW, ParkScene, TILT_PRESETS, type MapApi, type ViewInfo } from './map/ParkScene';
import { createRouter } from './map/route';
import { CATEGORY_LABEL, LOCATION, MENU_TABS, MODE_FEATURES, PINS, STREET_LAMP, WALK_SPEED, type MapFeatures, type MapMode, type MenuTab } from './map/config';
import { distToPoly } from './map/geo';
import type { XY } from './map/projection';
import type { ParkData, Poi } from './map/types';
import { telegramLocation, useUserLocation } from './map/useUserLocation';

const data = parkJson as unknown as ParkData;
const router = createRouter(data.graph);
const TAB_ICONS: Record<MenuTab, string> = {
  attractions: 'M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8L3.5 9.7l5.9-.9z',
  kassa: 'M4 8a2 2 0 002-2h12a2 2 0 002 2v2a2 2 0 000 4v2a2 2 0 00-2 2H6a2 2 0 00-2-2v-2a2 2 0 000-4zM10 6v12',
  services: 'M12 5v14M5 12h14',
  parking: 'M8 20V4h5.5a4.5 4.5 0 010 9H8',
};
/** Attraksionlar tabi: attraksionlar va bolalar maydonchalari */
const FUN_IDS = new Set([...data.attractions.map((a) => a.id), ...data.playgrounds.map((a) => a.id)]);
const numKey = (p: Poi) => (p.num ? parseFloat(p.num) : 1e6);
/** Tab → shu bo'limdagi joylar (ro'yxat tartibida) */
function tabItems(tab: MenuTab): Poi[] {
  const by = (f: (p: Poi) => boolean) => data.pois.filter(f);
  switch (tab) {
    case 'attractions': return by((p) => FUN_IDS.has(p.id)).sort((a, b) => numKey(a) - numKey(b) || a.label.localeCompare(b.label));
    case 'kassa': return by((p) => p.category === 'kassa');
    case 'services': return by((p) => p.category === 'services').sort((a, b) => a.label.localeCompare(b.label));
    case 'parking': return [...by((p) => p.category === 'entrance'), ...by((p) => p.category === 'parking')];
  }
}
const TAB_ITEMS = Object.fromEntries(MENU_TABS.map((t) => [t.id, tabItems(t.id)])) as Record<MenuTab, Poi[]>;
/** Marshrut boshlanadigan joylar: kirishlar, keyin parkinglar (ma'lumotdan) */
const START_IDS = [
  ...data.pois.filter((p) => p.category === 'entrance'),
  ...data.pois.filter((p) => p.category === 'parking'),
].map((p) => p.id);
const ME = 'me';
/** O'ngdagi asboblar ustuni kengligi + chekka (px) */
const TOOLS_INSET = 72;

/** Sensorli ekran (barmoq) — +/− o'rniga chimdish, bir martalik imo-ishora maslahati */
const isTouch = () => typeof window !== 'undefined' && window.matchMedia('(pointer: coarse)').matches;
const HINT_KEY = 'park-map:gesture-hint';

/** Telegram mini-app: xaritani tepaga/pastga surganda ilova yopilib ketmasin (Bot API 7.7+) */
function lockTelegramSwipes() {
  const wa = (window as unknown as { Telegram?: { WebApp?: { disableVerticalSwipes?: () => void; isVersionAtLeast?: (v: string) => boolean } } }).Telegram?.WebApp;
  if (wa?.disableVerticalSwipes && wa.isVersionAtLeast?.('7.7')) wa.disableVerticalSwipes();
}

/** Qiyalik: hozirgi burchakka eng yaqin tayyor holat */
const tiltIndex = (polar: number) => {
  let bi = 0;
  TILT_PRESETS.forEach((t, i) => { if (Math.abs(t.polar - polar) < Math.abs(TILT_PRESETS[bi].polar - polar)) bi = i; });
  return bi;
};

const fmtMeters = (m: number) => (m >= 1000 ? `${(m / 1000).toFixed(1)} km` : `${Math.round(m / 10) * 10} m`);
const fmtMinutes = (m: number) => `${Math.max(1, Math.round(m / WALK_SPEED / 60))} daq`;

/** Simulyatsiya uchun yo'l: kirish → charxpalak → hovuz → kirish (grafdagi haqiqiy yo'llar bo'ylab) */
function simulationPath(byId: Map<string, Poi>): XY[] {
  // Eski xaritada: kirish → charxpalak → hovuz; gen planda: kirish → eng baland attraksion → kirish
  const legacy = ['entrance-main', 'charxpalak-1', 'hovuz-1', 'entrance-main'];
  const top = [...data.attractions].sort((a, b) => b.size - a.size)[0]?.id;
  const stops = (legacy.every((id) => byId.has(id)) ? legacy : [START_IDS[0], top, START_IDS[0]])
    .map((id) => (id ? byId.get(id)?.node : undefined))
    .filter((n): n is number => n !== undefined);
  const path: XY[] = [];
  for (let i = 0; i < stops.length - 1; i++) path.push(...(router.between(stops[i], stops[i + 1])?.points ?? []));
  return path;
}

function useElementHeight<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [h, setH] = useState(0);
  useLayoutEffect(() => {
    if (!ref.current) return;
    const ro = new ResizeObserver(([e]) => setH(Math.round(e.borderBoxSize?.[0]?.blockSize ?? e.contentRect.height)));
    ro.observe(ref.current);
    return () => ro.disconnect();
  }, []);
  return [ref, h] as const;
}

export interface ParkMapProps {
  /** 'miniapp' — mijozlar uchun, 'admin' — adminka uchun (config.ts → MODE_FEATURES) */
  mode: MapMode;
  /** Rejim sozlamalarini alohida o'zgartirish, masalan { simulation: true } */
  features?: Partial<MapFeatures>;
}

export default function ParkMap({ mode, features }: ParkMapProps) {
  const f: MapFeatures = { ...MODE_FEATURES[mode], ...features };
  const map = useRef<MapApi>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  // Yuqoridagi menyu tabi: tanlansa — xaritada faqat shu bo'lim pinlari, pastda ro'yxati
  const [tab, setTab] = useState<MenuTab | null>(null);
  const [query, setQuery] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);
  const [fromId, setFromId] = useState(START_IDS[0]);
  const [showRoute, setShowRoute] = useState(false);
  const [showTrees, setShowTrees] = useState(true);
  const [lampsLit, setLampsLit] = useState(STREET_LAMP.lightsOn);
  const [follow, setFollow] = useState(false);
  const [toastHidden, setToastHidden] = useState(false);
  const [view, setView] = useState<ViewInfo>({ ...HOME_VIEW, rotated: false });
  const [hint, setHint] = useState(false);
  useEffect(() => {
    lockTelegramSwipes();
    if (!isTouch()) return;
    let seen = true;
    try { seen = localStorage.getItem(HINT_KEY) === '1'; } catch { /* maxfiy rejim */ }
    if (seen) return;
    setHint(true);
    try { localStorage.setItem(HINT_KEY, '1'); } catch { /* */ } // bir marta ko'rsatiladi
    const t = setTimeout(() => setHint(false), 6000);
    return () => clearTimeout(t);
  }, []);
  const closeHint = () => setHint(false);
  const loc = useUserLocation();
  // Rejimda joylashuv o'chirilgan bo'lsa (masalan, adminka), kuzatuvni to'xtatamiz
  const locationEnabled = f.location;
  useEffect(() => {
    if (!locationEnabled) loc.stop();
  }, [locationEnabled]); // eslint-disable-line react-hooks/exhaustive-deps
  const [topRef, topH] = useElementHeight<HTMLDivElement>();
  const [bottomRef, bottomH] = useElementHeight<HTMLDivElement>();

  const byId = useMemo(() => new Map(data.pois.map((p) => [p.id, p])), []);
  const selected = selectedId ? byId.get(selectedId) ?? null : null;

  // Mijoz park ichidami? (GPS xatosi uchun chegaradan LOCATION.insideMarginMeters gacha ruxsat)
  const outsideBy = loc.fix ? distToPoly(loc.fix.xy, data.ground) : null;
  const inside = outsideBy !== null && outsideBy <= LOCATION.insideMarginMeters;
  const me = loc.status === 'active' && inside ? loc.fix : null;

  const starts = [
    ...(me ? [{ id: ME, label: 'Mening joyim' }] : []),
    ...START_IDS.map((id) => byId.get(id)).filter((p): p is Poi => !!p),
  ];

  // Joylashuv paydo bo'lganda marshrut boshi avtomatik "Mening joyim" bo'ladi
  const hasMe = !!me;
  useEffect(() => {
    if (hasMe) setFromId(ME);
    else setFromId((id) => (id === ME ? START_IDS[0] : id));
  }, [hasMe]);

  const visiblePois = useMemo(
    () => {
      const inTab = tab ? new Set(TAB_ITEMS[tab].map((p) => p.id)) : null;
      return data.pois.filter((p) => p.id === selectedId || p.category === 'entrance' ||
        (inTab ? inTab.has(p.id) : PINS.alwaysShow.includes(p.category)));
    },
    [tab, selectedId],
  );

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return data.pois.filter((p) => p.label.toLowerCase().includes(q)).slice(0, 6);
  }, [query]);

  // Marshrut. "Mening joyim"dan bo'lsa, har yangi GPS o'lchovida qayta hisoblanadi (Dijkstra ~1 ms)
  const route = useMemo(() => {
    if (!selected) return null;
    if (fromId === ME) return me ? router.fromPoint(me.xy, selected.node) : null;
    const from = byId.get(fromId);
    if (!from || from.id === selected.id) return null;
    return router.between(from.node, selected.node);
  }, [selected, fromId, byId, me]);
  const arrived = fromId === ME && !!route && route.meters < 12;

  const select = useCallback((id: string | null) => {
    setSelectedId(id);
    setShowRoute(false);
    if (id) setFollow(false);
  }, []);

  // Tanlangan obyektga uchish. bottomH ham kuzatiladi: pastki oyna ochilgach balandligi o'zgaradi
  // va obyekt oyna ostida qolmasligi uchun markaz qayta hisoblanadi.
  useEffect(() => {
    if (selected && !showRoute && !follow) map.current?.flyTo(selected.anchor, 2.6);
  }, [selected, bottomH]); // eslint-disable-line react-hooks/exhaustive-deps

  // Kuzatish rejimi: birinchi o'lchovda yaqinlashtirib uchadi, keyin har o'lchovda kamerani suradi
  const firstFix = useRef(true);
  useEffect(() => {
    if (!me) { firstFix.current = true; return; }
    if (!follow) return;
    if (firstFix.current) map.current?.flyTo(me.xy, 3);
    else map.current?.panTo(me.xy);
    firstFix.current = false;
  }, [me, follow]);

  const onLocate = () => {
    setToastHidden(false);
    if (loc.status === 'active' && inside) {
      if (follow) { loc.stop(); setFollow(false); } // uchinchi bosish — o'chirish
      else { setFollow(true); firstFix.current = true; }
      return;
    }
    if (loc.status === 'active' || loc.status === 'locating') { loc.stop(); setFollow(false); return; }
    setFollow(true);
    loc.start();
  };

  const startSimulation = () => {
    setToastHidden(false);
    setFollow(true);
    loc.simulate(simulationPath(byId));
  };

  const locateLabel = loc.status === 'off' ? "Mening joyimni ko'rsatish"
    : loc.status === 'active' && inside && follow ? "Joylashuvni o'chirish"
    : loc.status === 'active' && inside ? 'Mening joyimga qaytish'
    : "Joylashuvni o'chirish";

  const tg = telegramLocation();
  const simulating = loc.fix?.source === 'simulation';
  const toast = toastHidden ? null
    : loc.status === 'locating' ? { text: 'Joylashuv aniqlanmoqda…', sim: f.simulation, settings: false }
    : loc.status === 'denied' ? {
        text: tg ? "Joylashuvga ruxsat berilmagan. Telegram sozlamalaridan ruxsat bering." : "Joylashuvga ruxsat berilmagan. Brauzer yoki telefon sozlamalaridan ruxsat bering.",
        sim: f.simulation, settings: !!tg }
    : loc.status === 'unavailable' || loc.status === 'error' ? { text: "Joylashuvni aniqlab bo'lmadi. GPS yoqilganini tekshiring.", sim: f.simulation, settings: false }
    : loc.status === 'active' && !inside && outsideBy !== null ? {
        text: `Siz parkdan ${fmtMeters(outsideBy)} uzoqdasiz. Park hududiga kirganingizda joyingiz xaritada ko'rinadi.`,
        sim: f.simulation, settings: false }
    : simulating ? { text: "Simulyatsiya: park bo'ylab yurish", sim: false, settings: false, stop: true }
    : null;

  // Esc — tanlovni bekor qilish
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') { setSearchOpen(false); select(null); } };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [select]);

  const pickResult = (p: Poi) => {
    setQuery('');
    setSearchOpen(false);
    if (tab && !TAB_ITEMS[tab].some((x) => x.id === p.id)) setTab(null);
    select(p.id);
  };

  return (
    <div className="app">
      <div className="map" aria-label="Park xaritasi, 3D ko'rinish">
        <ParkScene
          ref={map}
          data={data}
          pois={visiblePois}
          selectedId={selectedId}
          onSelect={select}
          route={showRoute && route ? route.points : null}
          showTrees={showTrees}
          lampsLit={lampsLit}
          insets={{ top: topH + 8, bottom: bottomH + 8, right: TOOLS_INSET }}
          user={me}
          onUserInteract={() => setFollow(false)}
          onViewChange={setView}
        />
      </div>

      <div className="top gutter" ref={topRef}>
        <header className="bar">
          <div className="brand">
            <span className="brand__mark" aria-hidden="true">
              <svg viewBox="0 0 24 24"><path d="M12 3c3.5 3 5 6 5 9a5 5 0 01-10 0c0-3 1.5-6 5-9zM12 17v4" /></svg>
            </span>
            <div className="brand__text">
              <span className="brand__name">Park xaritasi</span>
              <span className="brand__sub">Toshkent · 41.312° N</span>
            </div>
          </div>
          <div className="search">
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5" /><path d="M16 16l4 4" /></svg>
            <input
              id="search"
              type="search"
              placeholder="Qidirish: hojatxona, basseyn…"
              value={query}
              autoComplete="off"
              onChange={(e) => { setQuery(e.target.value); setSearchOpen(true); }}
              onFocus={() => setSearchOpen(true)}
              onKeyDown={(e) => { if (e.key === 'Enter' && results[0]) pickResult(results[0]); }}
              aria-label="Obyekt qidirish"
            />
            {searchOpen && results.length > 0 && (
              <ul className="results" role="listbox">
                {results.map((p) => (
                  <li key={p.id}>
                    <button type="button" onClick={() => pickResult(p)}>
                      <span>{p.label}</span>
                      <small>{CATEGORY_LABEL[p.category]}</small>
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {searchOpen && query.trim() && results.length === 0 && (
              <div className="results results--empty">“{query}” topilmadi</div>
            )}
          </div>
        </header>

        <nav className="tabs" aria-label="Bo'limlar">
          {MENU_TABS.map((t) => (
            <button key={t.id} type="button" aria-pressed={tab === t.id} className={`tab${tab === t.id ? ' is-on' : ''}`}
              onClick={() => { select(null); setTab((cur) => (cur === t.id ? null : t.id)); }}>
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d={TAB_ICONS[t.id]} /></svg>
              {t.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="tools" role="toolbar" aria-label="Xarita boshqaruvi">
        {f.location && (
          <button type="button" onClick={onLocate} aria-label={locateLabel} title={locateLabel}
            className={`locate${loc.status === 'locating' ? ' is-busy' : ''}${me ? ' is-on' : ''}${me && follow ? ' is-follow' : ''}`}>
            {me && follow ? (
              <svg viewBox="0 0 24 24"><path className="fill" d="M12 3l7 18-7-4-7 4z" /></svg>
            ) : (
              <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="6" /><path d="M12 2v4M12 18v4M2 12h4M18 12h4" />{me && <circle className="fill" cx="12" cy="12" r="2.4" />}</svg>
            )}
          </button>
        )}
        <button type="button" className="zoom" onClick={() => map.current?.zoomBy(1.5)} aria-label="Yaqinlashtirish">
          <svg viewBox="0 0 24 24"><path d="M12 6v12M6 12h12" /></svg>
        </button>
        <button type="button" className="zoom" onClick={() => map.current?.zoomBy(1 / 1.5)} aria-label="Uzoqlashtirish">
          <svg viewBox="0 0 24 24"><path d="M6 12h12" /></svg>
        </button>
        {(() => {
          // Qiyalik: tepadan → odatiy → pastdan (barmoq bilan ham: ikki barmoqni tepaga/pastga surish)
          const cur = TILT_PRESETS[tiltIndex(view.polar)], next = TILT_PRESETS[(tiltIndex(view.polar) + 1) % TILT_PRESETS.length];
          const label = `Ko'rish burchagi: ${cur.label}. Bosing — ${next.label}`;
          const eye = cur.id === 'top' ? [12, 4] : cur.id === 'default' ? [5, 6] : [3, 14];
          return (
            <button type="button" className="tilt" onClick={() => map.current?.setTilt(next.polar)} aria-label={label}
              title={`${label}. Kompyuterda: o'ng tugma bilan sudrang`}>
              <svg viewBox="0 0 24 24">
                <path d="M3 20h18" />
                <path className="dash" d={`M${eye[0]} ${eye[1]}L${cur.id === 'top' ? 12 : 16} 19`} />
                <circle className="fill" cx={eye[0]} cy={eye[1]} r="2.3" />
              </svg>
            </button>
          );
        })()}
        {view.rotated && (
          <button type="button" className="compass" onClick={() => map.current?.resetRotation()}
            aria-label="Burilish va qiyalikni tiklash" title="Burilish va qiyalikni tiklash">
            <svg viewBox="0 0 24 24" style={{ transform: `rotate(${view.azimuth}deg)` }}>
              <path className="north" d="M12 3l3.2 9h-6.4z" />
              <path d="M8.8 12h6.4L12 21z" />
            </svg>
          </button>
        )}
        <button type="button" onClick={() => map.current?.reset()} aria-label="Butun parkni ko'rsatish">
          <svg viewBox="0 0 24 24"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5" /></svg>
        </button>
        <button type="button" className={showTrees ? 'is-on' : ''} onClick={() => setShowTrees((v) => !v)}
          aria-pressed={showTrees} aria-label="Daraxtlar">
          <svg viewBox="0 0 24 24"><path d="M12 3l5 7h-3l4 6H6l4-6H7zM12 16v5" /></svg>
        </button>
        {data.lamps.length > 0 && (
          <button type="button" className={lampsLit ? 'is-on' : ''} onClick={() => setLampsLit((v) => !v)}
            aria-pressed={lampsLit} aria-label={lampsLit ? "Fonus chiroqlarini o'chirish" : 'Fonus chiroqlarini yoqish'}
            title={lampsLit ? "Fonus chiroqlarini o'chirish" : 'Fonus chiroqlarini yoqish'}>
            <svg viewBox="0 0 24 24"><path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.6 10.8c.7.6 1.1 1.3 1.1 2.2h5c0-.9.4-1.6 1.1-2.2A6 6 0 0 0 12 3z" /></svg>
          </button>
        )}
      </div>

      {hint && (
        <button type="button" className="gesture-hint" onClick={closeHint}>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 13V5.5a1.5 1.5 0 013 0V12M11 11.5V4.5a1.5 1.5 0 013 0v7M14 11.5V6a1.5 1.5 0 013 0v8a6 6 0 01-6 6h-.5a6 6 0 01-5.2-3L3.8 14a1.5 1.5 0 012.6-1.5L8 15" /></svg>
          <span>Ikki barmoq: burab aylantiring, birga tepaga surib qiyalating</span>
        </button>
      )}

      <div className="bottom gutter" ref={bottomRef}>
        {toast && (
          <div className="toast" role="status">
            <span>{toast.text}</span>
            <div className="toast__actions">
              {toast.settings && <button type="button" onClick={() => tg?.openSettings()}>Sozlamalar</button>}
              {toast.sim && <button type="button" onClick={startSimulation}>Simulyatsiya</button>}
              {'stop' in toast && <button type="button" onClick={() => { loc.stop(); setFollow(false); }}>To'xtatish</button>}
              {loc.status !== 'locating' && !('stop' in toast) && (
                <button type="button" className="toast__close" onClick={() => setToastHidden(true)} aria-label="Yopish">
                  <svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18" /></svg>
                </button>
              )}
            </div>
          </div>
        )}
        {selected ? (
          <section className="sheet" aria-live="polite">
            <div className="sheet__head">
              <div>
                <span className={`chip chip--${selected.category}`}>{CATEGORY_LABEL[selected.category]}</span>
                <h2>{selected.label}</h2>
                {(selected.hours || selected.info) && (
                  <p className="sheet__info">{[selected.hours && `Ish vaqti: ${selected.hours}`, selected.info].filter(Boolean).join(' · ')}</p>
                )}
              </div>
              <button type="button" className="icon-btn" onClick={() => select(null)} aria-label="Yopish">
                <svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18" /></svg>
              </button>
            </div>

            <div className="trip">
              <label className="trip__from" htmlFor="from">
                <span>Qayerdan</span>
                <select id="from" value={fromId} onChange={(e) => setFromId(e.target.value)}>
                  {starts.map((s) => <option key={s.id} value={s.id}>{s.label}</option>)}
                </select>
              </label>
              <div className="trip__dist">
                {arrived ? (
                  <><strong>Yetib keldingiz</strong><span>shu yerdasiz</span></>
                ) : route ? (
                  <>
                    <strong>{fmtMeters(route.meters)}</strong>
                    <span>piyoda ~{fmtMinutes(route.meters)}</span>
                  </>
                ) : (
                  <span>{fromId === selected.id ? 'Siz shu yerdasiz' : "Yo'l topilmadi"}</span>
                )}
              </div>
            </div>

            <button type="button" className="primary" disabled={!route}
              onClick={() => {
                setShowRoute((v) => !v);
                if (!showRoute && route) {
                  setFollow(false);
                  map.current?.fitTo([...route.points, selected.anchor]);
                }
              }}>
              {showRoute ? "Yo'lni yashirish" : "Yo'lni ko'rsatish"}
            </button>
          </section>
        ) : (
          <>
            {tab && (
              <section className="list" aria-label={MENU_TABS.find((t) => t.id === tab)!.label}>
                <div className="list__head">
                  <h2>{MENU_TABS.find((t) => t.id === tab)!.label}</h2>
                  <button type="button" className="icon-btn" onClick={() => setTab(null)} aria-label="Yopish">
                    <svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18" /></svg>
                  </button>
                </div>
                {TAB_ITEMS[tab].length === 0 ? (
                  <p className="list__empty">{tab === 'kassa' ? "Kassalar joyi va ish vaqti tez orada qo'shiladi." : "Hozircha ro'yxat bo'sh."}</p>
                ) : (
                  <ul>
                    {TAB_ITEMS[tab].map((p) => (
                      <li key={p.id}>
                        <button type="button" onClick={() => select(p.id)}>
                          {p.num && <span className="list__num">{p.num}</span>}
                          <span className="list__label">{p.label}</span>
                          {p.hours && <small>{p.hours}</small>}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            )}
          </>
        )}
      </div>
    </div>
  );
}

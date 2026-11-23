// Attraksionlarning jonli holati (status). HOZIRCHA SOXTA MA'LUMOT — pin dizaynini ko'rish uchun.
// Backend tayyor bo'lganda shu fayl API so'roviga almashtiriladi (kalit — gen plan raqami `num`).

export type LiveStatus = 'open' | 'stopped' | 'closed';

export interface LiveInfo {
  status: LiveStatus;
  /** Navbat, daqiqa (faqat ochiq bo'lsa) */
  queueMin?: number;
  /** Qisqa izoh: sabab yoki qachon ochilishi */
  note?: string;
}

const MOCK: Record<string, LiveInfo> = {
  '21': { status: 'open', queueMin: 10 },
  '22': { status: 'open', queueMin: 0 },
  '24': { status: 'open', queueMin: 5 },
  '27': { status: 'stopped', note: "Texnik ko'rik · 16:00 gacha" },
  '35': { status: 'open', queueMin: 15 },
  '36': { status: 'closed', note: '10:00 da ochiladi' },
  '38': { status: 'open', queueMin: 3 },
  '39': { status: 'stopped', note: "Kuchli shamol" },
  '43': { status: 'closed', note: 'Mavsum tugadi' },
  '47': { status: 'open', queueMin: 20 },
};

export const liveOf = (num: string | null | undefined): LiveInfo | null => (num ? MOCK[num] ?? null : null);

export const STATUS_LABEL: Record<LiveStatus, string> = {
  open: 'Ochiq',
  stopped: "Vaqtincha to'xtatilgan",
  closed: 'Yopiq',
};

/** Pin va pastki oynadagi status qatori: "Ochiq · navbat 5 daq" */
export function statusLine(l: LiveInfo) {
  if (l.status === 'open') return l.queueMin ? `${STATUS_LABEL.open} · navbat ${l.queueMin} daq` : `${STATUS_LABEL.open} · navbat yo'q`;
  return l.note ? `${STATUS_LABEL[l.status]} · ${l.note}` : STATUS_LABEL[l.status];
}

/** Pin kartochkasi uchun qisqa nom: 'Аттракцион "Air race 2 seats"' → 'Air race 2 seats' */
export const shortLabel = (label: string) =>
  label.replace(/^Аттракци[оo]н\s*/u, '').replace(/^"(.*)"$/u, '$1').replace(/^"([^"]*)"\s*/u, '$1 ').trim() || label;

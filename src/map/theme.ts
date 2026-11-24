import { useEffect, useState } from 'react';

export type ThemeName = 'light' | 'dark';

/** 3D sahna ranglari. UI ranglari styles.css dagi tokenlarda. */
export const PALETTE = {
  light: {
    base: '#e7ecf3',
    // Maysa: qorong'i rejimdagi bilan bir xil to'q yashil — telefon (odatda yorug' rejim) va kompyuter (adminka) bir xil ko'rinsin
    groundTop: '#3c5a3f',
    groundSide: '#a88f6c',
    // Suv: sayoz (qirg'oq bo'yi) → chuqur (o'rtasi), qirg'oqdagi och chiziq, qirg'oq toshi va devori
    water: {
      pond: { shallow: '#62ad9c', deep: '#2b6fa6', rim: '#e3f3ee', coping: '#b9b4aa', wall: '#958b7d' },
      canal: { shallow: '#6aa58c', deep: '#2f7593', rim: '#e0f0e8', coping: '#b9b4aa', wall: '#8f8475' },
      pool: { shallow: '#8ee3ed', deep: '#2aaed3', rim: '#f4fdff', coping: '#f4f4f1', wall: '#c4ecf2' },
    },
    waterSky: '#d2eaf8', // suvda aks etgan osmon
    glint: '#fffaf0',
    plantTint: '#ffffff', // qamish ranglari modelda; bu — umumiy yorqinlik
    fishTint: '#eef6f7', // baliq suv ostida: rangi biroz suvga singadi
    fishWake: '#9fb3bd', // baliq ortidagi och iz (qo'shiluvchi — qanchalik och bo'lsa, shunchalik kuchli)
    lily: ['#4f8a3a', '#5e9a45', '#3f7a35', '#6aa04c'],
    // Basseynlar majmuasi
    deckTint: '#ffffff', // travertin plitka (rangi teksturada)
    umbrella: '#f7f7f4',
    umbrellaRed: '#d8343a',
    lounger: ['#1f5fae', '#14a3ad', '#f2f1ec'],
    sail: '#eadcc0',
    poolMosaic: '#1d55b0', // basseyn tubidagi to'q tasmalar
    poolMosaicTeal: '#279c98',
    roadTop: '#f6f4ef', // tosh plitka: tekstura bilan ~#d2d1cd
    roadSide: '#8e8b86',
    curb: '#9a9da1', // bordyur: plitkadan to'qroq, yo'l cheti ko'rinsin
    draft: '#f59e0b',
    parking: '#a6a29c',
    parkingLot: '#cbc7bf', // joylashuvli parking asfalti (tekstura bilan ~#aaa6a0, fotodagidek och)
    parkingEdge: '#ffffff',
    playground: '#f3c58a',
    wall: '#2f66db',
    roof: '#6f9bf2',
    edge: '#1f4bb0',
    selected: '#f59e0b',
    bridge: '#b9875a',
    rail: '#7b5434',
    trunk: '#8a6a4a',
    leaves: ['#4f9f50', '#3f8c46', '#6bb35a'],
    route: '#f97316',
    attractionBox: '#f08cb4', // modeli hali yo'q attraksion qutisi (gen plandagi pushti maydoncha)
    attractionBoxEdge: '#b4457a',
    flowerBed: '#d8607f', // gulzor (gullar)
    padTop: '#d9d6cf', // modeli bor attraksion ostidagi maydoncha
    rubber: '#ec7a32', // bolalar maydonchasi yumshoq qoplamasi (plandagi to'q sariq)
    rubberGreen: '#2f7a45',
    rubberEdge: '#c0362f',
    fence: '#2c5e3f', // maydoncha panjarasi (to'q yashil metall)
    fenceYellow: '#e0b21c', // attraksion panjarasi (sariq)
    wheel: '#f1f4f8',
  },
  dark: {
    base: '#0e1522',
    groundTop: '#3c5a3f',
    groundSide: '#4b3d2c',
    water: {
      pond: { shallow: '#2c5f5c', deep: '#163d66', rim: '#6f9fa2', coping: '#77736b', wall: '#544c42' },
      canal: { shallow: '#2d5a52', deep: '#18415e', rim: '#6a9893', coping: '#77736b', wall: '#4f483f' },
      pool: { shallow: '#2f9cb1', deep: '#116c91', rim: '#8ad8e6', coping: '#b6b9bd', wall: '#5f9aa6' },
    },
    waterSky: '#2c4b72',
    glint: '#d6e6ff',
    plantTint: '#b4bfae',
    fishTint: '#c4ccd4',
    fishWake: '#5d7186',
    lily: ['#3b6e2e', '#467a36', '#30622a', '#517f3b'],
    deckTint: '#b7b1a8',
    umbrella: '#c9ccd0',
    umbrellaRed: '#a8282c',
    lounger: ['#1a4a85', '#127f87', '#bfc2c6'],
    sail: '#b8ad97',
    poolMosaic: '#123e86',
    poolMosaicTeal: '#1b706d',
    roadTop: '#c4c1bb', // kechasi ham och: ~#a6a49f
    roadSide: '#5c5a56',
    curb: '#6d7075',
    draft: '#fbbf24',
    parking: '#6c6964',
    parkingLot: '#807c76',
    parkingEdge: '#c6ccd6',
    playground: '#b98a52',
    wall: '#2a55b8',
    roof: '#5c86e0',
    edge: '#9db8f5',
    selected: '#fbbf24',
    bridge: '#9c7350',
    rail: '#d9b48c',
    trunk: '#6d533a',
    leaves: ['#3f7d44', '#356f3b', '#4f8f48'],
    route: '#fb923c',
    attractionBox: '#c46a92',
    attractionBoxEdge: '#f3a9c9',
    flowerBed: '#a84a63',
    padTop: '#a9a6a0',
    rubber: '#b85e28',
    rubberGreen: '#255f37',
    rubberEdge: '#962b25',
    fence: '#4f8a63',
    fenceYellow: '#c99d17',
    wheel: '#cdd5e1',
  },
} as const;

export type Palette = (typeof PALETTE)[ThemeName];

/** data-theme atributi (aniq tanlov) yoki tizim sozlamasi */
export function useThemeName(): ThemeName {
  const read = (): ThemeName => {
    const attr = document.documentElement.getAttribute('data-theme');
    if (attr === 'light' || attr === 'dark') return attr;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  };
  const [name, setName] = useState<ThemeName>(read);
  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const update = () => setName(read());
    mq.addEventListener('change', update);
    const mo = new MutationObserver(update);
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => {
      mq.removeEventListener('change', update);
      mo.disconnect();
    };
  }, []);
  return name;
}

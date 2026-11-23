# Park xaritasi (3D)

`map.geojson` asosida qurilgan izometrik 3D park xaritasi: yo'llar haqiqiy kenglikda chiziladi, kesishmalar tekis qo'shiladi, obyektdan obyektgacha piyoda yo'l topiladi.

Stack: React 18 + TypeScript + Vite, three.js / react-three-fiber / drei. Ma'lumot Node + Turf bilan oldindan qayta ishlanadi.

## Ishga tushirish

```bash
npm install
npm run build:map   # data/*.geojson → src/map/park.json
npm run dev         # http://localhost:5173
npm run build       # production build → dist/
npm run build:demo  # hammasi bitta HTML faylda → dist-demo/index.html
```

`map.geojson` o'zgarsa, `npm run build:map` ni qayta ishga tushiring.

## Gen plan asosida xarita (asosiy manba)

Xarita endi `yana-reference/Ген планТэльмана  2025 Цвет.pdf` (AutoCAD vektor PDF, 1:500) dan quriladi:

```bash
pip install pypdfium2 shapely numpy      # bir marta
npm run extract:genplan   # PDF → data/genplan/genplan.geojson
npm run build:genplan     # genplan.geojson → src/map/park.json
npm run dev
```

- **Koordinatalar** — `scripts/genplan/georef.json`. Masshtab plandagi 7 ta radius yozuvidan olingan: 1 pt = 0,1247 m (1:500, 1/√2 ga kichraytirib chop etilgan). Burilish va siljish eski yo'llarga moslangan va sputnik bilan tekshirilgan (basseynlar ~1 m aniqlikda).
- **Turlar plandagi rangdan** aniqlanadi (`extract.py` → `COLOR_KIND`): maysa, suv, bino, attraksion (pushti), bolalar maydoni, maydon. Yo'l va maydonlar = chegara − hamma rangli shakllar.
- **Chegara** — plandagi qalin qizil chiziq (yer uchastkasi).
- **Obyektlar** — plandagi qizil raqamlar eksplikatsiya bilan bog'lanadi (`scripts/genplan/explication.py`, nomlar plandagidek).
- **Marshrut** — yo'l yuzasining markaz chiziqlari (medial o'q) bo'ylab.
- Planda faqat ingichka chiziq bilan chizilgan mavjud binolar (Аристон, Дар, More binosi...), kanal va ko'priklar eski `data/map.geojson` dan olinadi.
- **Attraksionlar hozircha pushti quti** (plandagi maydoncha shaklida). Blender modeli tayyor bo'lsa, `src/map/attractions.tsx` → `ATTRACTION_MODELS` ga plan raqami bilan qo'shing, masalan `'#47': { component: Wheel, natural: {...} }` — quti o'rniga model chiqadi.
- `park.json` da `source: 'genplan'` bo'lsa, eski xaritaga qo'lda joylangan bezaklar (fontanlar, oqqush, bolalar maydoni jihozlari) chizilmaydi.
- Eski jarayon (`npm run build:map`) o'zgarmagan.
- **Menyu tablari** (qidiruv ostida): Attraksionlar · Kassa · Xizmatlar · Parking va kirish — `config.ts` → `MENU_TABS`. Tab bosilsa xaritada faqat shu bo'lim pinlari, pastda ro'yxati chiqadi.
- **Kassalar** gen planda yo'q: `config.ts` → `KASSA` ga qo'shing (joyi — plan raqami `near` yoki `lonLat`, ish vaqti, narx), keyin `npm run build:genplan`.
- **Telefonda boshlang'ich ko'rinish** (`ParkScene.tsx` → `HOME_VIEW_NARROW`, 36° / 205°): park uzun o'qi ekranga tik tushadi va ekranni to'ldiradi; kompyuterda — `HOME_VIEW` (49° / 234°).

## Qanday ishlaydi

```
data/map.geojson ─┐
data/roads-draft.geojson ─┴─> scripts/build-map.ts ─> src/map/park.json ─> React + three.js
```

`scripts/build-map.ts` quyidagilarni bajaradi:

1. **Snap.** Yo'l uchi boshqa yo'ldan `SNAP_METERS` (4 m) ichida bo'lsa, unga yopishtiriladi. Uzoqroq uchlar konsolda chiqadi: ular kirish, parking yoki bino eshigi bo'lsa normal.
2. **Yo'l yuzasi.** Har bir chiziq `ROAD_WIDTH` bo'yicha metrda buffer qilinadi, aylana maydonchalar bilan birlashtiriladi (union) va suv kesib tashlanadi. Natijada bitta toza yuza chiqadi, kesishmalarda ustma-ust tushish bo'lmaydi.
3. **Graf.** Chiziqlar kesishgan har bir joyga tugun qo'yiladi va marshrut uchun graf quriladi. Konsolda `1 komponent` deb chiqishi kerak: bu hamma yo'llar bir-biriga ulangan degani.
4. **Daraxtlar.** Yo'l, bino va suvdan bo'sh joylarga sochiladi (seed bilan, har safar bir xil natija).

Brauzerda Turf yo'q: hamma hisob build paytida bajariladi, brauzer tayyor JSON'ni (~75 KB) o'qiydi.

## Fayllar

| Fayl | Vazifasi |
|---|---|
| `src/map/config.ts` | **Asosiy sozlamalar**: obyekt nomlari, turi, balandligi, kategoriyasi, yo'l kengliklari |
| `src/map/theme.ts` | 3D sahna ranglari (yorug' va qorong'i rejim) |
| `src/map/ParkScene.tsx` | Canvas, kamera, chegaralar, `MapApi` (flyTo, fitTo, zoom, qiyalik, kompas) |
| `src/map/mapGestures.ts` | Kamera va imo-ishoralar: surish, chimdish, burash, qiyalatish (mobil va sichqoncha) |
| `src/map/layers.tsx` | Qatlamlar: yer, yo'l, ko'prik, bino, daraxt, marshrut, pinlar |
| `src/map/water.tsx`, `waterField.ts`, `waterBank.ts` | Suv: shader, qirg'oq, qamish va nilufar |
| `src/map/fish.tsx`, `figures.ts` | Baliqlar: harakat, figura sikli, figuralar (aylana, yurak, yulduz, SVG) |
| `src/map/styledBuilding.tsx`, `banyaBuilding.tsx`, `mallBuilding.tsx`, `massageBuilding.tsx`, `constructionSite.tsx` | Fotoga qarab qurilgan binolar (More, Banya, Katta bino): fasad, tom, kechki derazalar, LED media-fasad |
| `src/map/poolDecor.tsx`, `data/pools-shape.geojson` | Basseynlar majmuasi: plitka, soyabon, shezlong, orol bari, bolalar o'yin maydoni; basseyn shakllari va bezaklari |
| `src/map/parkingLot.tsx`, `parkingTraffic.ts`, `scripts/parking-layout.ts`, `data/parking-shape.geojson` | 1-parking (fotoga qarab): kontur, joylar, mashinalar va ularning harakati, orolchalar, darvoza, budka, bino, soyabon |
| `src/map/route.ts` | Dijkstra (binary heap) |
| `src/map/projection.ts` | lon/lat ↔ metr. GPS nuqtani xaritaga qo'yish uchun `project()` |
| `src/ParkMap.tsx`, `src/styles.css` | Asosiy komponent va UI: qidiruv, filtrlar, pastki oyna, joylashuv |

## Taxminiy yo'llar

`data/roads-draft.geojson` faylida 4 ta yo'lni **taxminan** chizib qo'ydim, chunki asl faylda ular yo'q edi:

- D1: ariq uchini aylanib o'tadigan yo'l
- D2: Basseyn atrofidagi aylana yo'l (ikkala ko'prik shunga ulanadi)
- D3: Kichik basseyn yonidan Basseynga tushadigan yo'l
- D4: ko'prikdan 1-parking piyoda kirishiga tushadigan qisqa yo'l (fotodagidek)

Xaritada ular to'q sariq rangda ajratib ko'rsatiladi. Ularni geojson.io'da ochib, haqiqiy joyiga moslang yoki o'chirib, o'rniga asl `map.geojson` ga to'g'ri yo'llarni chizing. Keyin `npm run build:map` ni ishga tushiring.

## Attraksionlar

Attraksion GeoJSON'da `Point` bo'lib turadi:

```json
{ "type": "Feature",
  "properties": { "name": "Charxpalak", "size": 4, "bearing": 156 },
  "geometry": { "type": "Point", "coordinates": [69.298192998, 41.312255507] } }
```

- `size` — o'lcham sinfi (`config.ts` → `ATTRACTION_SIZES`). Model o'z proporsiyasini saqlab, sinf "qutisi"ga sig'diriladi:

  | size | Balandligi | Eni | Misol |
  |---|---|---|---|
  | 4 | ≤ 38 m | ≤ 34 m | charxpalak |
  | 3 | ≤ 20 m | ≤ 24 m | erkin tushish minorasi, qayiq-arg'imchoq |
  | 2 | ≤ 10 m | ≤ 14 m | karusel, avtodrom |
  | 1 | ≤ 5 m | ≤ 7 m | bolalar attraksionlari, batut |

  Ma'lumot uchun: kichik aylana maydonchalar ⌀ ~17 m (2-sinf sig'adi), o'rtalari ⌀ ~29 m (3-sinf), eng kattasi ⌀ ~33 m (4-sinf).
- `height` (ixtiyoriy) — sinf balandligini almashtiradi, metrda. Baland va ingichka attraksionlar uchun: masalan, minora `size: 4, height: 55`. Eni baribir sinf chegarasidan oshmaydi.
- `bearing` — old tomoni qaragan yo'nalish, shimoldan soat strelkasi bo'yicha (gradus). Berilmasa 156°.

Har bir attraksion modeli `src/map/` dagi alohida komponent (masalan, `FerrisWheel.tsx`). Model lokal (0,0,0) markazda quriladi va `attractions.tsx` dagi `ATTRACTION_MODELS` ro'yxatiga qo'shiladi. Joylash, burish va masshtabni o'ram komponent o'zi bajaradi.

Hozirgi modellar:

| Nomi | size | Fayl | Animatsiya (`config.ts`) |
|---|---|---|---|
| Charxpalak | 4 | `FerrisWheel.tsx` | `FERRIS_WHEEL.secondsPerTurn`: g'ildirak aylanadi, kabinalar tik turadi |
| Karusel | 2 | `Carousel.tsx` | `CAROUSEL.secondsPerTurn`: pol va tom aylanadi, otlar ko'tarilib-tushadi (`bobSeconds`) |
| Erkin tushish minorasi (`Erkin_tushish`) | 4, `height: 55` | `DropTower.tsx` | `DROP_TOWER`: kabina ko'tariladi, tepada to'xtaydi, erkin tushadi va tormozlanadi |
| Mini amerikan tepaligi (`Amerikan_tepaligi`) | 3 | `Coaster.tsx` | `COASTER`: parovoz va 3 vagon sakkizsimon trassada yuradi, tepada sekinlashib, pastda tezlashadi |

`secondsPerTurn: 0` qilsangiz, attraksion to'xtaydi. Hamma attraksion to'xtagan bo'lsa, xarita faqat harakat bo'lganda chiziladi va batareya tejaladi. Animatsiyalar ~22 kadr/s da ishlaydi va `prefers-reduced-motion` yoqilgan bo'lsa o'chadi.

Modellar tashqi 3D fayllarsiz, kod bilan quriladi. Bezaklar (friz, chodir yo'llari, ustun derazalari) canvas'da chizilgan teksturalar.

## Pinlar (metkalar)

"Hammasi" filtrida faqat parkinglar, kirishlar va qurilayotgan bino (kran belgisi) pinlari ko'rinadi. Ko'k pinlar (xizmatlar, dam olish, binolar) ko'rinmaydi. Obyektni topish uchun:
- 3D model ustiga bosish (bino, suv, attraksion) — pastki oyna ochiladi va shu obyektning pini chiqadi;
- qidiruv;
- pastdagi toifa tugmasi ("Xizmatlar", "Dam olish", "Binolar") — o'sha toifaning pinlari chiqadi.

Sozlama: `config.ts` → `PINS.alwaysShow`. Hammasi ko'rinsin desangiz, unga barcha toifalarni yozing.

## Xaritani boshqarish (mobil va kompyuter)

Kamera perspektivli. Boshlang'ich ko'rinishda (qiyalik 49°, kamera shimoli-g'arbdan qaraydi: kirishlar pastda, basseynlar va 1-parking tepada) butun park ekranni to'ldiradi. Ochilganda ham, "Butun parkni ko'rsatish" bosilganda ham doim aynan shu holat chiqadi: pastki oyna ochiq bo'lsa ham o'lchami o'zgarmaydi (`ParkScene.tsx` → `HOME_VIEW`, `HOME_FILL`). Telefonda (tor ekran) park eniga to'liq sig'adi. Xaritani tepadan (0°) to yerga yaqin holatgacha (80°) qiyalatsa bo'ladi. Pastdan qaraganda uzoq joylar tumanga singib, ufq bo'lib ko'rinadi. Kamera yerdan 1.7 m (odam ko'zi balandligi) dan pastga tushmaydi. Butun park ko'rinadigan uzoqlikda qiyalik ko'pi bilan ~62°, yaqinlashgan sari 80° gacha ochiladi: uzoqdan juda qiya qaralsa, park ingichka chiziq bo'lib qoladi.

| Amal | Telefon | Kompyuter |
|---|---|---|
| Surish | bir barmoq (qo'yib yuborganda biroz sirpanadi) | chap tugma bilan sudrash |
| Yaqinlashtirish | ikki barmoq bilan chimdish yoki ikki marta tegish | g'ildirak (kursor tomonga), ikki marta bosish, +/− |
| Aylantirish | ikki barmoqni burash | o'ng tugma (yoki Ctrl/Shift + chap) bilan chapga/o'ngga |
| Qiyalatish (yerdan/osmondan) | ikki barmoqni birga tepaga/pastga surish | o'ng tugma bilan tepaga/pastga |

Tugmalar:
- **Qiyalik tugmasi** — tepadan (0°) → odatiy (49°) → pastdan (74°). "Pastdan"ga o'tganda, uzoqda bo'lsa, biroz yaqinlashadi.
- **Kompas** — xarita aylantirilganda yoki qiyalatilganda chiqadi, ignasi shimolni ko'rsatadi. Bosilsa, boshlang'ich burilish va qiyalikka qaytadi.
- Telefonda (sensorli ekranda) +/− tugmalari yashiriladi, tugmalar 44 px bo'ladi. Birinchi ochilganda bir marta "Ikki barmoq: burab aylantiring, birga tepaga surib qiyalating" maslahati chiqadi.
- Telegram mini-app'da vertikal svayp o'chiriladi (`disableVerticalSwipes`, Bot API 7.7+). Aks holda xaritani pastga surganda ilova yopilib qolardi.

**Kursor** (kompyuterda) joyiga va qilinayotgan ishga qarab o'zgaradi (`mapGestures.ts` → konteynerning `data-cursor` atributi, ko'rinishi `styles.css` da):

| Holat | Kursor |
|---|---|
| Xarita ustida | ochiq qo'l (`grab`) |
| Bosiladigan obyekt (bino, suv, attraksion, parking) yoki pin ustida | barmoq (`pointer`) |
| Surish paytida | yumilgan qo'l (`grabbing`) |
| O'ng tugma bilan chapga-o'ngga — aylantirish; Ctrl/Shift bosib turilganda ham | aylana strelka |
| O'ng tugma bilan tepaga-pastga — qiyalatish | tik ikki tomonlama strelka |
| G'ildirak bilan yaqinlashtirish / uzoqlashtirish | lupa + / − (qisqa vaqt) |

Sudrash paytida pin ustidan o'tilsa ham kursor o'zgarmaydi. Obyekt ustidami — R3F bosish hodisasi bor obyektlarga raycast bilan aniqlanadi (har 60 ms da ko'pi bilan bir marta).

Imo-ishoralar Canvas konteynerida tinglanadi, shuning uchun pin ustidan ham surish va zoom ishlaydi. Pinga oddiy bosish esa tanlovni ochadi. `MapApi` ga `setTilt(gradus)` va `resetRotation()` qo'shildi, `ParkScene` ning `onViewChange` propi burilish va qiyalikni beradi.

## Yo'l qoplamasi: tosh plitka va bordyur

Yo'llar och kulrang tosh plitkadan (bruschatka), chetlarida bordyur bor (`pavement.ts`).

- **Tosh plitka:** notekis shakldagi toshlar, oralarida to'q choklar. Canvas'da Voronoi usulida chiziladi, alohida rasm fayli yo'q. Tekstura choksiz takrorlanadi (4 m da), toshlar yo'nalishsiz, shuning uchun egri yo'llarda ham tabiiy ko'rinadi. Bitta tosh ~33 sm. Uzoqdan ular bir tekis och kulrang rangga qo'shilib ketadi, yaqinlashtirganda alohida toshlar ko'rinadi.
- **Bordyur:** asfaltning butun chegarasi bo'ylab avtomatik quriladi: chorrahalar, aylana maydonchalar, kvartallar ichi va suv bo'yi ham. U plitkadan tashqarida, maysa tomonda turadi, shuning uchun yo'l kengligi o'zgarmaydi. Har 1 m da chok bor. Butun bordyur bitta geometriyadan iborat (~11k uchburchak, 1 ta draw call).
- **O'lcham:** `config.ts` → `PAVEMENT` (`curbWidth` 0.25 m, `curbHeight` 0.15 m). Haqiqiy bordyurdan biroz katta, xaritada ko'rinishi uchun.
- **Ranglar** (`theme.ts`): `roadTop` — plitka rangi; tekstura uni har bir tosh uchun ozgina o'zgartiradi. Yorug' mavzuda `#f6f4ef` (natija ~#d2d1cd), qorong'i mavzuda `#c4c1bb`. Bordyur plitkadan to'qroq (`#9a9da1` / `#6d7075`), shunda yo'l cheti aniq ko'rinadi. Parking asfalt rangida qoldi.

## Suv: hovuz, ariq va basseynlar

Suv endi yerdan pastda turadi: yer plitasidan suv o'rni kesib olingan (`build:map` → `groundCut`), chetida tosh qirg'oq bor. Sirti jonli: to'lqin, rang va yaltiroq bor (`water.tsx`, `waterField.ts`, `waterBank.ts`).

Uchta uslub bor (`config.ts` → `WATER.bodies`):

| Uslub | Obyekt | Ko'rinishi |
|---|---|---|
| `pond` | Hovuz | Qirg'oq bo'yi sayoz va yashil-firuza, o'rtasi to'q ko'k. Qirg'og'i tosh devor, suv chizig'i atrofida nam (to'q) tasma bor |
| `canal` | Ariq | Tor va chuqurroq. Suv oqim yo'nalishida siljiydi, oqim bo'ylab och izlar ko'rinadi |
| `pool` | Basseyn, Basseyn_Kv, Basseyn_D | Ochiq firuza rang, tagidagi kafel suv orqali biroz "sinib" ko'rinadi, ustida quyosh to'rlari (kaustika) bor. Cheti oq tosh |

- **Chuqurlik.** `WATER.styles` da: `level` — suv sathi yerdan qancha pastda (hovuz −0.6 m, ariq −0.7 m, basseyn −0.28 m), `coping` — qirg'oq toshining eni, `copingTop` — uning balandligi. Xaritada ko'rinishi uchun haqiqiysidan biroz chuqurroq qilingan.
- **Sayozdan chuqurga rang.** Brauzer ochilganda har bir suv uchun "qirg'oqqacha masofa" teksturasi bir marta hisoblanadi: 5 ta suv uchun jami ~15 ms (2 yadroli serverda o'lchangan, telefonda biroz ko'proq). Tekstura yirik to'rda (eng uzun tomoni ≤160 piksel), GPU oraliqni silliq to'ldiradi. Rang shunga qarab o'zgaradi, qirg'oq bo'yida ingichka och chiziq chiqadi.
- **To'lqin.** Bir necha qatlam shovqin bir-birini kesib, har xil yo'nalishda sekin suzadi. To'lqin yonbag'irlari osmonni aks ettiradi, quyoshga qaraganlari uchqun-uchqun yaltiraydi. Uzoqdan qaralganda mayda to'lqinlar o'zi so'nadi, shuning uchun suv "qum" bo'lib miltillamaydi. To'liq so'ngan qatlamlar, kafel va kaustika esa umuman hisoblanmaydi. Animatsiya attraksionlar bilan bir xil ~22 kadr/s da ishlaydi. `WATER.animate: false` bo'lsa yoki `prefers-reduced-motion` yoqilgan bo'lsa, suv jim turadi.
- **Ariq oqimi.** Yo'nalish ariqning shimoliy uchidan janubga qarab avtomatik topiladi. Teskari bo'lsa, `WATER.canalFlow.reverse: true` qiling. Tezlik `canalFlow.speed` da.
- **Fonus aksi.** Kechasi (qorong'i mavzuda) yoqilgan fonuslar suvda tik, silkinib turgan yorug' iz bo'lib aks etadi. Iz kamera burchagiga qarab o'z joyini topadi, xaritani aylantirsangiz ham to'g'ri chiqadi. Fonus chiroqlari o'chirilsa, aks ham yo'qoladi. Kerak bo'lmasa, `WATER.lampReflections: false` qiling.
- **Suv ichidagi binolar** (Rotonda) suv sathidan boshlanadi, ostida bo'shliq qolmaydi. **Ko'priklar** ostiga suvgacha tushadigan tayanch ustunlar qo'shildi (~5 m da bir juft).
- **Ranglar** `theme.ts` → `water` (har uslub uchun `shallow`, `deep`, `rim`, `coping`, `wall`), `waterSky` va `glint` da, yorug' va qorong'i mavzu uchun alohida.

Haqiqiy aks ettirish (three.js `Water`) ishlatilmadi: u sahnani har kadrda ikki marta chizadi va telefonda sekinlashadi. Bu yerda hammasi bitta shader ichida hisoblanadi. Suv sirti oddiy `MeshStandardMaterial`, shuning uchun sahna yorug'ligi va soyalar (rotonda, ko'prik, daraxtlar) unga ham tushadi.

### Qamish va nilufar

Joyi `data/water-plants.geojson` da, bitta `Polygon`: hozir hovuzning uchli (g'arbiy) qismi, skrinshotda qizil bilan belgilangan joy.

```json
{ "type": "Feature",
  "properties": { "name": "Suv_osimliklari", "reeds": true, "lilies": true },
  "geometry": { "type": "Polygon", "coordinates": [[ … ]] } }
```

- **Qamish.** Hudud ichidagi qirg'oq bo'ylab, toshdan biroz narida to'p-to'p bo'lib o'sadi. Uzluksiz devor emas, orasida bo'shliqlar bor, ba'zi joyda 2–3 qator. Har to'pda 16 ta egilgan barg va 3 ta qo'g'a (jigarrang boshcha) bor, shamolda sekin tebranadi. Hozir 318 ta to'p.
- **Nilufar.** Qirg'oqdan 2.5 m dan uzoqda 9 ta to'da, har birida 6–14 ta barg, barglarning ~18 foizida pushti yoki oq gul. Hozir 93 ta barg, 13 tasi gulli.
- Ko'prik va rotondaga yaqin joyga qo'yilmaydi. Joylashuv seed bilan qilinadi, har safar bir xil chiqadi.
- **Sozlamalar** `config.ts` → `WATER_PLANTS` da: oraliq, balandlik, to'dalar soni, barg o'lchami, gullar ulushi. Boshqa joyga ham qo'shish uchun geojson.io'da yangi `Polygon` chizib, shu faylga qo'shing. Faqat qamish kerak bo'lsa `"lilies": false` qiling, faqat nilufar kerak bo'lsa `"reeds": false`. Keyin `npm run build:map` ni ishga tushiring.
- Hammasi `InstancedMesh` (3 ta draw call). Bitta qamish to'pi 164 uchburchak, 318 ta to'p jami ~52k. Soya tashlamaydi.

### Tezlik: suv qanchalik og'ir

To'lqinning o'zi to'liq GPU'da hisoblanadi. CPU har kadrda faqat bitta raqamni (vaqtni) yangilaydi.

O'lchov dasturiy GPU'da (SwiftShader) qilingan. Shuning uchun faqat foizlar ma'noli, o'lchov xatosi ±5% atrofida:

| Holat | Jonli suv oddiy suvga nisbatan |
|---|---|
| Butun park ko'rinishi | +3–4% kadr vaqti |
| Hovuz ekranni to'ldirganda | +15–17% |

Batareyani asosan suv emas, xaritaning doim qayta chizilishi yeydi (~22 kadr/s, attraksionlar va suv harakati uchun). Uni to'xtatish uchun `WATER.animate: false` va attraksionlarda `secondsPerTurn: 0` / `enabled: false` qiling.

## Fotoga qarab qurilgan binolar (More, Banya)

"More binosi 1", "More binosi 2" (`styledBuilding.tsx`) va "Banya" (`banyaBuilding.tsx`) haqiqiy fotosuratlarga qarab qurilgan. Qolgan binolar oddiy ko'k quti bo'lib qolgan.

### More binolari

- **Fasad.** 2 qavat, devor balandligi 7.6 m. Har 4 m da qaytariladigan modul:
  - oq suvoq ustun;
  - 1-qavatda yog'och romli katta oyna (bitta modulda eshik);
  - 2-qavatda navbatma-navbat katta oyna yoki tor derazali yog'och panel;
  - tom ostida keng yog'och friz;
  - yonida naqshli oq panel.

  2-bino `moreWood` variantida: yuqori qavati to'liq yog'och, ichida tor tik derazalar. Har devor butun modullarga moslanadi va oq ustun bilan boshlanib, oq ustun bilan tugaydi.
- **Tom.** Past qiyalikli (12°), to'rt tomonga qiya, kulrang metall: har 0.5 m da tik choklar, chetida oq taxta, tizmasida qopqoq. Tomda konditsionerlar (1-binoda 12 ta, 2-binoda 4 ta) va fotodagidek kichik uchburchak shamollatgichlar bor.
- **Kechasi** 1-qavat (restoran) va yuqori derazalarning bir qismi iliq rangda yonadi, romlar qora qolib, oynani bo'laklarga bo'ladi.
- **Tanlansa** boshqa binolar kabi to'q sariq rangga kiradi, pin tom tizmasi ustida turadi.
- **Teksturalar** canvas'da chiziladi, tashqi rasm fayli yo'q. Har bino 3 ta draw call: devor, tom, detallar.

### Banya

Hovuzga (dumaloq basseyn) qaragan shimoliy fasadi fotodagidek:

- **Asosiy fasad.** 3 qavat, 11 m. Krem suvoq, har 3.6 m da to'q g'isht ustun, tor tik derazalar va yog'och panellar. Yuqori qavat (7.6 m dan yuqori) to'q ko'k kvadrat plitka bilan qoplangan.
- **Dumaloq qism.** Fasaddagi yarim doira bo'rtiq avtomatik topiladi: qisqa, silliq ulangan qirralar ketma-ketligi. Unda tosh ustunlar va har qavatda katta oyna bor. Har qavat ustida oq egri balkon bor, 2-qavat to'sig'i ustida gullar o'sadi, tepasida oq karniz.
- **Kirish.** G'arbiy burchak oldidagi bo'lak qizil g'ishtdan, ustida "БАНЯ" yozuvi, oyna eshik va 3 pog'onali zina. Qaysi qirrada turishi `accentEdge` da (hozir 12).
- **Tom.** Tekis, kulrang, parapetdan biroz pastda. Ustida to'q plitkali qo'shimcha qavat bor (`penthouse`, 3.2 m): eng uzun janubiy devor bo'ylab, binoning ichida qoladigan qilib o'lchanadi. Yana 8 ta konditsioner.
- **Kechasi** derazalar, eshik va "БАНЯ" yozuvi yonadi.
- 6 ta draw call: 2 xil fasad, kirish, qo'shimcha qavat, tom, detallar.

Boshqa binoni ham shunday qilish uchun `config.ts` → `BUILDING_LOOKS` ga uning id sini qo'shing:

```ts
'dar-1': { facade: 'more', floors: 2, height: 7.6, roofPitch: 12, roofUnits: 6 },
```

Qiya tom faqat to'rtburchak binolarga quriladi, boshqa shakllarga tekis tom qo'yiladi. Boshqa uslubdagi bino uchun (masalan, oyna fasad) fotosini yuboring, yangi `facade` turi qo'shiladi.

### Bali massaji

Banya va More binosi orasidagi uchburchak maydonda (asl `map.geojson` da yo'q edi). U `data/extra-objects.geojson` da turadi: `Massaj` — bino konturi, `Plitka` — maysa o'rniga travertin plitka bo'ladigan maydon (basseyn plitkasiga qo'shiladi). Model `massageBuilding.tsx` da, sozlamasi `BUILDING_LOOKS['massaj-1']`.

- Bir qavatli oq bino (~18 × 8 m, 4.4 m). Pastda kafe: katta qora romli oynalar, ikki tavaqali eshik, tepasida yog'och chuqurchalar, "Fastfood zona" lavhasi.
- Old tomon tepasida och kulrang tasma va katta qora harflar "БАЛИЙСКИЙ МАССАЖ НА МОРЕ", kechasi harflar yonadi.
- Tomida travertin pol, orqa va yon tomonlarda oq panjara, katta bej chodir-soyabon (qiya, tarang mato), uning ostida ikkita massaj chodiri (parda, ichida massaj stoli), orasida massaj kursisi, oldinda somon soyabon. O'ng tomonda tomga chiqadigan po'lat zinapoya.
- Old tomonda ayvon: 6 ta stol, rotang stullar, oq soyabonlar, o'rtasida o'tish joyi bor yashil to'siq, axlat qutilari.
- Maydonda maysa va daraxt yo'q, hammasi plitka. Plitka endi har bir binoning devorigacha boradi (avval 0.6 m maysa tasmasi qolardi).

### Katta bino

5 qavatli savdo-ko'ngilochar markaz, balandligi ~26 m (avval 10 m edi). `mallBuilding.tsx`, sozlamasi `config.ts` → `BUILDING_LOOKS['bino-katta-1']`.

- **Old fasad** kanalga qaragan (`frontEdge: 0` — polygonning shimoliy burchagidan boshlanadigan qirra). Chap burchakda butun bo'yi terrakota rang pilon, u karnizdan oldinga chiqib turadi. Pastda 3 qator shisha vitrina (~8.6 m), o'rtada och plitkali keng tasma, eng yuqorida jigarrang ustunli shisha qavat, o'ng burchakda gulli terrasa. Ustida qalin jigarrang karniz.
- **Portal** markazda: ikki kulrang tosh oyoq va ichkariga torayib boruvchi qiya peshtoq ("voronka"), ichida vitrina ko'rinadi.
- **Yon tomonlar:** parking tomonida old fasad uslubi 12 m o'tadi, keyin har xil kulrang tik panellar va tor derazalar. Basseynlar tomonida yuqori shisha qavat davom etadi, pastda kulrang panellar.
- **Tom** tekis: chiqish/lift qutilari, konditsioner bloklari qatorlari, orqa yarmida quyosh panellari bloklari.
- **Kechasi** derazalar notekis iliq yonadi (ichida siluetlar bor), pilon va kulrang devorlar pastdan yoritiladi. O'rtadagi och tasma LED media-fasadga aylanadi: ko'k-binafsha to'lqinlar va uchqunlar sekin oqadi (shaderda, qo'shimcha geometriyasiz). "Harakatni kamaytirish" yoqilgan bo'lsa, to'lqinlar to'xtab turadi.
- Logotiplar qo'yilmagan, pilon bo'sh. Rasmiy logotip fayllari bo'lsa, pilonga qo'shsa bo'ladi.

#### Qurilmoqda: Play Port 2027

Hozir xaritada **tayyor bino** ko'rsatiladi (`config.ts` → `CONSTRUCTION['bino-katta-1'].display: 'finished'`). Tomining ustida katta sariq "2027" belgisi turadi: u doim kameraga qaraydi, yaqinlashganda kattalashadi, uzoqdan ham ekranda kamida ~84 px (telefonda ~66 px) bo'lib ko'rinadi. Bu bino uchun pin chiqmaydi, uning o'rnida shu belgi turadi. Bino tanlanganda pastki oynada "Qurilmoqda" belgisi va "2027-yilda ochilishi rejalashtirilgan" izohi chiqadi.

`display: 'site'` qilinsa, quyida tasvirlangan qurilish maydoni ko'rinishiga qaytadi.


Bino 2027-yilda ochilishi rejalashtirilgan, shuning uchun xaritada odatiy holda **qurilish maydoni** ko'rinadi (`constructionSite.tsx`, sozlamasi `config.ts` → `CONSTRUCTION`):

- 3 qavat beton karkas: plitalar va ustunlar. Tepada keyingi qavat boshlangan: front yarmida ustunlar va qolip, qolganida armatura chiqib turibdi.
- Old fasadda havoza va yashil xavfsizlik to'ri.
- Ichkarida minorali kran: strela sekin buriladi, aravacha yuradi, yuk ko'tariladi va tushadi. Kechasi cho'qqisida va strela uchida qizil chiroqlar yonadi.
- Atrofida to'siq (bino + 4.5 m, yo'l, suv va qo'shni binolarga tegmaydi), kanal va parking tomonida "PLAY PORT · 2027-yilda ochiladi" banneri. Ichi tuproq, vagonchalar va material taxlamlari bor. To'siq ichida daraxt va fonus yo'q.
- Pin belgisi — kran, nomi "Play Port 2027". Qidiruvda "Qurilmoqda · 2027" deb chiqadi. Marshrut eng yaqin yo'lgacha, ya'ni to'siq oldigacha boradi.
- Bino tanlanganda pastki oynada "Qurilmoqda" belgisi, izoh va **"Hozir / 2027"** almashtirgichi chiqadi. "2027" bosilsa, tayyor bino yerdan ko'tarilib chiqadi, ustida "Loyiha · 2027-yilda ochiladi" yozuvi turadi. Boshqa obyekt tanlansa yoki oyna yopilsa, yana "Hozir" bo'ladi.

Qurilish bosqichi o'zgarsa, `floorsBuilt` ni o'zgartiring. Bino ochilganda `CONSTRUCTION` dan uning qatorini o'chirib, `npm run build:map` qiling: xaritada tayyor bino qoladi, to'siq olib tashlanadi, daraxtlar qaytadi. Nomini ham `OBJECTS.Bino_Katta.label` da o'zgartirish mumkin.

## Basseynlar majmuasi ("Море")

Uchala basseyn fotosuratlarga qarab qilingan (`poolDecor.tsx`, suv bezaklari `water.tsx` shaderida). Shakl va bezaklar `data/pools-shape.geojson` da turadi. Asl `map.geojson` o'zgarmagan: shu fayldagi `Polygon` shu nomdagi suvning konturini almashtiradi. geojson.io'da ochib tahrirlab, `npm run build:map` ni ishga tushirsangiz bo'ladi.

| Basseyn | Ko'rinishi |
|---|---|
| **Lagun** (`Basseyn`) | Egri-bugri shakl: shimolda ikki bo'lak, sharqda plitka yarim oroli, janubda 4 ta yarim doira jakuzi (oq devorcha, ichida to'xtovsiz pufakchalar). G'arbda konsentrik zina. Tubida sayoz va chuqur qismni ajratuvchi to'q ko'k tasma (janubi sayoz, ochroq) va oq bezak chizig'i. Orol va ikkala ko'prik joyida |
| **Orol bari** (`More_Rotonda`) | Kichik dumaloq yog'och bar: peshtaxta, keng yog'och tom, ustunlar. Ustida uchta katta kumushrang halqa arka (ikki qavat quvur, ferma kabi), atrofida 10 ta oq shezlong |
| **To'g'ri burchakli** (`Basseyn_Kv`) | Tubida ikkita qiya to'q ko'k tasma, har uchinchi kvadrati firuza |
| **Bolalar basseyni** (`Basseyn_D`) | Tomchi shakl, keng tomoni lagunga qaragan. Keng tomonida rangli suv o'yin maydoni: minorachalar, ag'dariladigan chelak, yashil qo'ziqorin, to'q sariq tekis va spiral tepalik, ko'k quvur tepalik. Yonida 4 ta bej yelkan soyabon |

- **Plitka.** Uchala basseyn bitta umumiy travertin maydon ichida, maysa va daraxtlar o'rnida. Maydon basseynlarni o'rab olgan qavariq shakl, chetga 8.5 m zaxira bilan (`config.ts` → `POOL_AREA.margin`). Binolar o'rni teshik, faqat orol bari plitka ustida turadi. Maydon ichida alohida yo'lak chizilmaydi, lekin marshrut grafi o'zgarmagan: marshrut plitka ustidan o'tadi.
- **Soyabon va shezlonglar.** Har basseyn chegarasi bo'ylab ikki qatorda (suv chetidan 2.4 va 6.8 m, `POOL_AREA.rows`), har 3.4 m da qo'yilgan. Har soyabon ostida ikkita shezlong turadi, boshi suvdan teskari. Soyabonlar oq, ~8 foizi qizil (`redShare`), fotodagi Coca-Cola yozuvi qo'yilmagan. Shezlonglar ko'k va firuza. Marshrut chizig'iga (`pathClearance` 1.9 m), ko'prik, bino, fonus va bir-biriga yaqin qo'yilmaydi. Hozir 106 ta soyabon, 222 ta shezlong.
- **Lagun pini** endi orol ustiga emas, suv ustiga tushadi: markazi polygon ichida bo'lmasa, chegaradan eng uzoq nuqta olinadi.
- **Daraxtlar** endi har to'r katakchasining o'z tasodifiy soni bilan joylashadi: biror joy o'zgarsa, boshqa joydagi daraxtlar siljimaydi. Bu o'zgarish tufayli daraxtlar bir marta yangi joyga tushdi.

**Tezlik:** soyabon, shezlong, yelkan, o'yin maydoni, bar va plitka jami ~11 draw call va ~30k uchburchak. Suv bezaklari shaderda hisoblanadi. Uzoqdan pufakchalar va oq chiziq hisoblanmaydi, faqat ular bor basseynlarda bor.

## 1-parking (fotoga qarab)

Kontur fotodagi qizil chiziq bo'yicha qayta chizilgan (asl `map.geojson` dagi romb o'zgarmagan). U `data/parking-shape.geojson` da turadi: shu fayldagi `Parking_1` Polygon shu nomdagi parking konturini almashtiradi. Faylda yana `of: "Parking_1"` xossali to'rtta element bor:

| Nomi | Turi | Nima |
|---|---|---|
| `Darvoza` | Point (`bearing`, `width`) | Avtomobil kirish-chiqishi: janubi-sharqiy ko'chaga, fotodagi strelkalar joyida. Ikki shlagbaum (kirishdagisi ko'tarilgan), yonida qorovul budkasi, asfaltda kirish/chiqish strelkalari |
| `Piyoda` | Point | Piyoda kirish: o'yiq tubi. Ko'prikdan keladigan yo'l (D4) shu yerga tushadi, ichkarida zebra. Parkingga marshrut shu nuqtada tugaydi |
| `Bino` | LineString (`depth`, `height`) | Yo'lak tepasidagi uzun past bino: old tomonida derazalar va eshik, ikki rangli metall tom (kulrang va qizg'ish), kechasi derazalar yonadi |
| `Soyabon` | LineString (`depth`) | Yo'lakning g'arbiy chetidagi tomli soyabon, ostida 4 ta joy |

Shakli fotodagidek: g'arbiy va janubi-g'arbiy cheti devor bo'ylab uzun diagonal, shimolida daraxtlar ortida Ichkaridagi yo'l, o'rtasida o'yiq (daraxtlar, piyoda kirish), shimoli-sharqda budkagacha tor yo'lak, sharqida daraxtlar bo'ylab zinapoya va darvoza. Fotoda parking xaritadagi bog' chegarasidan biroz tashqariga chiqadi; bu yerda u chegara ichiga sig'dirilgan (chetida 4.5 m daraxt va fonus qatori).

**Joylashuv** `npm run build:map` da hisoblanadi (`scripts/parking-layout.ts`, sozlamalari `config.ts` → `PARKING_LAYOUT`):

- Har joy 2.5 × 5 m, oldida kamida 6 m bo'sh yo'lak bo'lishi shart. Shuning uchun yo'laklar o'z-o'zidan hosil bo'ladi va hech bir joy berkilib qolmaydi.
- Avval chet bo'ylab qatorlar qo'yiladi (orqasi chetga, soyabon osti birinchi), keyin ichkarida orqama-orqa qo'sh qatorlar. Ichki qatorlar fotodagidek g'arbiy chetga parallel (`rowBearing: 166`). Bu qiymat olib tashlansa, eng ko'p joy sig'adigan yo'nalish avtomatik tanlanadi.
- Ichki qatorda har 5 joydan keyin bordyurli daraxt orolchasi (`islandEvery`), qator uchlarida kichik orolcha. Har ikkinchi orolchada fonus bor, chet bo'ylab parkingdan 1 m tashqarida har 24 m da fonus turadi.
- Joylarning ~72 foizida mashina turadi (`occupancy`). Ranglar oq, kumush, qora, kulrang, to'q ko'k, qizil, bej va yashil, ~30 foizi krossover.
- Hozir 156 joy, 105 mashina, 6 orolcha, 13 fonus (yo'ldagi fonusga 6 m dan yaqini qo'shilmaydi).

**Harakat** (`src/map/parkingTraffic.ts`, sozlamalari `config.ts` → `PARKING_TRAFFIC`):

- Har 14–30 soniyada darvozadan bitta mashina kiradi, yo'lak bo'ylab bo'sh joyga borib, old tomoni bilan turadi. Shunday oraliqda boshqa bir mashina joyidan chiqib ketadi: old tomoni bilan turgan bo'lsa orqaga chiqib buriladi, keyin darvozaga boradi. Bandlik boshlang'ich daraja (~67 foiz) atrofida qoladi.
- Bir vaqtda ko'pi bilan 2 ta mashina harakatda (`maxMoving`), tezligi ~11 km/soat, orqaga sekinroq. Joyidan qo'zg'alishda va to'xtashda sekinlashadi.
- O'ng tomonlama harakat: kiruvchi va chiquvchi o'z bo'lagida. Mashina yaqinlashganda o'sha bo'lakdagi shlagbaum ko'tariladi, o'tib ketgach tushadi. Darvoza tashqarisida ko'cha yo'q, shuning uchun mashina chegarada paydo bo'ladi va yo'qoladi.
- Kechasi harakatdagi mashina oldida chiroq yorug'i ko'rinadi.
- Yo'l topish: parking 0.5 m li to'rga bo'linadi (joylar, orolchalar va chetga yaqin joy band), A* bilan yo'l topiladi, to'g'rilanadi va silliqlanadi. To'r bir marta ~20 ms da quriladi, bitta yo'l ~2 ms da topiladi, har kadrda simulyatsiya ~0.01 ms.
- "Harakatni kamaytirish" (prefers-reduced-motion) yoqilgan bo'lsa yoki `enabled: false` bo'lsa, mashinalar turgan joyida qoladi.

**Tezlik:** parking jami 19 mesh va ~16.5k uchburchak (sahnaning ~6 foizi). Chiziqlar, orolchalar va mashinalar InstancedMesh: turgan va harakatdagi hamma mashinalar bitta draw call.

## Baliqlar va figuralar

Hovuzda 140 ta mayda koi baliq bor: to'q sariq, qizil, tilla va oq rangli (`fish.tsx`, `figures.ts`). Adminkada ham, mini-appda ham ko'rinadi.

- **Oddiy holat.** Baliqlar 3–7 tadan to'da bo'lib erkin suzadi. Boshliq yangi joyni tanlaydi, qolganlari uning ortidan boradi. Bir-biriga urilmaydi, qirg'oq toshi, qamish va rotondadan aylanib o'tadi, nilufar barglari ostidan o'tib ketadi. Dumi tezlikka qarab likillaydi, ortida mayda V-to'lqin izi qoladi.
- **Figura sikli** (`FISH.show`), har 50 soniyada bir marta:

  | Bosqich | Davomiyligi | Nima bo'ladi |
  |---|---|---|
  | Erkin suzish | 23 s | To'da-to'da suzish |
  | Yig'ilish | 8 s | Har bir baliq figuradagi o'z joyiga shoshiladi: uzoqdagilar tezroq suzadi, izi uzunroq bo'ladi |
  | Figura | 15 s | Baliqlar kontur bo'ylab bir tomonga suzib turadi, shakl jonli ko'rinadi |
  | Tarqalish | 4 s | To'dalar yaqin atrofga tarqaladi |

  Birinchi figura xarita ochilgandan 20 soniya keyin boshlanadi (`firstAfterSeconds`).
- **Hozirgi figura — aylana.** U siz belgilagan joyda, hovuzning keng sharqiy qismida turadi, diametri 38 m. Suvda haqiqiy doira bo'lib chiziladi. Shuning uchun xaritadagi dumaloq maydoncha va basseynlar kabi ekranda biroz yassi (oval) ko'rinadi va xarita qaysi tomonga aylantirilsa ham bir xil turadi.
- **Ekranga qaratish** (`faceScreen`). Yurak, yulduz, harflar kabi "tik" figuralar standart holda ekranga qarab turadi: xarita aylantirilsa ham yonboshlab qolmaydi. Ekranda vertikal masofa qisqarib ko'rinadi, shunga moslab shakl cho'zilgan. Yo'nalish figura boshlanganda bir marta olinadi. Figura ko'rsatilayotganda xarita burilsa, keyingi ko'rsatuvgacha shu holicha qoladi. Aylanaga bu kerak emas, uning standarti `faceScreen: false`. Har figuraga alohida berish mumkin.
- **Sig'dirish.** Figura suvga sig'masa yoki rotondaga tegsa, avtomatik kichraytiriladi.
- **Uzoqdan ko'rinishi.** Baliqlar mayda, shuning uchun uzoqdan figurani asosan ularning izi chizadi: suvda och chiziq paydo bo'ladi. Yaqinlashganda iz xiralashadi va baliqlarning o'zi ko'rinadi.

### Yangi figura qo'shish

`config.ts` → `FISH.figures` ro'yxatiga bitta qator qo'shing:

```ts
figures: [
  { name: 'aylana', shape: 'circle', at: [69.2982223, 41.3110829], size: 38 },   // hozirgi
  { name: 'yurak', shape: 'heart', at: [69.2982223, 41.3110829], size: 38 },
  { name: 'yulduz', shape: 'star', size: 34 },                        // at berilmasa — hovuzning eng keng joyi
  { name: 'tomchi', svg: 'M50 0 C 50 30, 90 50, 90 75 C 90 98, 70 110, 50 110 C 30 110, 10 98, 10 75 C 10 50, 50 30, 50 0 Z', size: 30 },
],
```

- `shape` — tayyor shakllar: `heart`, `star`, `circle`.
- `svg` — istalgan kontur: Figma'da shaklni tanlab "Copy as SVG" qiling va `<path d="…">` ichidagi qatorni qo'ying. Bir nechta kontur (masalan, harflar) bo'lsa, baliqlar ular orasida uzunligiga qarab bo'linadi. Yoy (`A`) buyrug'i qo'llanmaydi: Figma'da "Flatten" qilsangiz, yoylar egri chiziqqa aylanadi. Ochiq chiziq avtomatik yopiladi. SVG o'qilmasa, o'rniga yurak chiziladi.
- `order: 'navbat'` — ro'yxat tartibida, `'tasodifiy'` — har safar tasodifan.

Figurani istalgan paytda qo'lda chaqirish ham mumkin, masalan adminkadagi tugmadan yoki bayramda:

```ts
import { fishShow } from './map/fish';
fishShow('aylana');   // nom berilmasa — navbatdagisi
```

### Tezlik

| | Qiymat |
|---|---|
| CPU | 140 baliq uchun bir qadam ~0.17 ms (kadriga ~1 qadam) |
| GPU | 2 draw call (baliqlar + izlar), ~5k uchburchak |

Sekin qurilmada ham harakat bir tekis qoladi, chunki vaqt 0.05 s lik qadamlarga bo'lib hisoblanadi. Yig'ilish ham o'z vaqtida tugaydi. Hammasini o'chirish uchun `FISH.enabled: false` qiling. `prefers-reduced-motion` yoqilgan bo'lsa, baliqlar joyida turadi.

## Soyalar

Soya xaritasini chizish kadrning ~10–17% ini oladi. Kamera surilganda soya o'zgarmaydi, harakatlanuvchi soyalar esa sekin (charxpalak, karusel). Shuning uchun soyalar har kadrda emas, sekundiga 5 marta yangilanadi: `config.ts` → `RENDER.shadowUpdatesPerSecond`. Bu kadr vaqtini ~8–13% qisqartiradi. `0` qilsangiz, eski usulda har kadrda yangilanadi.

Daraxtlarni yoqib-o'chirish kabi o'zgarishlarda soya ko'pi bilan 0.2 s ichida yangilanadi. Xarita jim turgan bo'lsa ham, oxirgi o'zgarish uchun alohida kadr chiziladi.

## Ko'cha fonuslari

Fonuslar `data/lamps.geojson` dagi chiziqlar bo'yicha qo'yiladi. Har bir `LineString` ning boshi va oxiri (va oraliq nuqtalari) yo'l grafiga yopishtiriladi. Orasidagi yo'l topilgach, fonuslar shu yo'l bo'ylab qo'yiladi: `count` — yo'l uzunligiga teng taqsimlangan fonuslar soni, yoki `spacing` — har necha metrda bittadan. Chorraha yoki band joyga to'g'ri kelsa, fonus yo'l bo'ylab bir necha metr suriladi. Fonus yo'l chetidan biroz tashqarida, park chegarasi tomonda bo'ladi. Joy band bo'lsa (boshqa yo'l, bino, suv yoki attraksion), qarama-qarshi tomonga o'tadi.

```json
{ "type": "Feature", "properties": { "name": "Fonus", "count": 10 },
  "geometry": { "type": "LineString", "coordinates": [[69.296555, 41.314266], [69.297608, 41.311425]] } }
```

Bundan tashqari `config.ts` → `STREET_LAMP_ROADS` yoqilgan: **parkdagi hamma yo'llar** bo'ylab, har bir yo'lning bir tomonida, ≈33 m da bitta fonus turadi (hozir jami 130 ta). Tomon har yo'l uchun o'zi tanlanadi: qaysi tomonda bo'sh joy ko'p bo'lsa, o'sha. Chorrahalarda bir-biriga 14 m dan yaqin kelgan fonuslarning ikkinchisi qo'yilmaydi (`minGap`). Faqat tanlangan yo'llarni yoritish kerak bo'lsa, `enabled: false` qiling.

**Chiroqlarni o'chirish.** Fonuslar joyida qoladi, faqat chiroqlari o'chadi: shisha to'q rangga kiradi, yerdagi yorug'lik va nur yo'qoladi.
- Foydalanuvchi o'ngdagi ustundagi lampochka tugmasi bilan yoqib-o'chiradi.
- Xarita ochilgandagi holat `config.ts` → `STREET_LAMP.lightsOn` da (`false` — o'chiq holda ochiladi).
- Komponentga to'g'ridan-to'g'ri: `<ParkScene lampsLit={false} … />`.

Yangi yo'lni yoritish uchun geojson.io'da o'sha yo'lning boshi va oxirini bog'lovchi chiziq chizib, shu faylga qo'shing va `npm run build:map` ni ishga tushiring. Chiziqni aniq yo'l ustidan chizish shart emas.

Model (`StreetLamps.tsx`): sakkiz qirrali asos, ikki halqali ustun, olti qirrali shisha fonus, uchli tom. Hammasi `InstancedMesh`, shuning uchun fonus soni ko'paysa ham 4 ta draw call bo'ladi. Bitta fonus ~350 uchburchak, soya tashlamaydi: 130 ta fonus jami ~45k uchburchak.

Yorug'lik haqiqiy `PointLight` emas. Yerda iliq doira va fonus atrofida nur chiziladi, chunki o'nlab real chiroq telefonni sekinlashtiradi. Qorong'i mavzuda yorug'lik to'liq kuchda, yorug' mavzuda xira (`STREET_LAMP.dayStrength`). Rang va o'lchamlar `config.ts` dagi `STREET_LAMP` bo'limida.

## Mijoz joylashuvi ("Siz shu yerdasiz")

Faqat `mode="miniapp"` da ishlaydi. O'ngdagi ustunning eng tepasidagi tugma bosilganda:

1. Joylashuvga ruxsat so'raladi va ko'k nuqta, aniqlik doirasi hamda harakat yo'nalishi chiziladi. Nuqta yangi o'lchovga sakramasdan, silliq siljiydi.
2. Kamera mijozni kuzatib boradi. Xaritani qo'lda sursa, kuzatish to'xtaydi. Tugmani yana bossa, joyiga qaytadi. Uchinchi bosish joylashuvni o'chiradi.
3. Marshrutdagi "Qayerdan" ro'yxatida **"Mening joyim"** paydo bo'ladi. Yo'l mijozning eng yaqin yo'lga chiqadigan nuqtasidan hisoblanadi va u yurgan sari masofa yangilanib boradi. 12 m ichiga kelsa, "Yetib keldingiz" deb chiqadi.
4. Mijoz parkdan tashqarida bo'lsa (`LOCATION.insideMarginMeters`, 30 m), nuqta chizilmaydi. Buning o'rniga "Siz parkdan 1.4 km uzoqdasiz" degan xabar chiqadi.

Manbani kod o'zi tanlaydi (`src/map/useUserLocation.ts`):

| Qayerda ochilgan | Usul |
|---|---|
| Telegram Mini App (Bot API 8.0+) | `Telegram.WebApp.LocationManager.getLocation()`. Bu bir martalik so'rov, shuning uchun har 2 soniyada qayta chaqiriladi. Ruxsat yo'q bo'lsa, "Sozlamalar" tugmasi `openSettings()` ni ochadi |
| Oddiy brauzer | `navigator.geolocation.watchPosition`. **HTTPS kerak**, localhost'da ham ishlaydi |

Telegram'da ishlashi uchun sahifaga `https://telegram.org/js/telegram-web-app.js` skripti ulangan bo'lishi kerak. Mini app'larda u odatda ulangan bo'ladi.

Koordinatalar hech qayerga yuborilmaydi va faqat qurilmada ishlatiladi.

**Simulyatsiya.** Joylashuv yo'q yoki mijoz parkdan tashqarida bo'lsa, "Simulyatsiya" tugmasi chiqadi. U kirish → charxpalak → hovuz → kirish yo'li bo'ylab yurishni taqlid qiladi. Ofisda turib sinash uchun qulay. Bu tugma faqat `features={{ simulation: true }}` berilganda chiqadi. Dev va demo build'larida u yoqilgan, production'da o'chiq.

## Ikki rejim: mini-app va adminka

Bitta komponent ikki joyda ishlatiladi:

```tsx
import ParkMap from './ParkMap';
import './styles.css';

// Mini-app (mijozlar)
<ParkMap mode="miniapp" />

// Adminka
<ParkMap mode="admin" />
```

Har bir rejimda qaysi funksiya yoqilgani `config.ts` → `MODE_FEATURES` da belgilanadi:

| Funksiya | miniapp | admin |
|---|---|---|
| `location`: "Mening joyim", ko'k nuqta, joyimdan marshrut | ✓ | — |
| `draftRoads`: taxminiy yo'llarni ajratib ko'rsatish | — | ✓ |
| `simulation`: joylashuv simulyatsiyasi (sinov uchun) | — | — |

Bitta joyda alohida o'zgartirish ham mumkin: `<ParkMap mode="miniapp" features={{ simulation: true }} />`.

Shu loyihani alohida ishga tushirganda (`npm run dev`) mini-app rejimi ochiladi. Manzil oxiriga `#admin` qo'shsangiz, adminka rejimiga o'tadi.

## park-mini-app ga ulash

1. `src/map/`, `src/ParkMap.tsx`, `src/styles.css` va `scripts/build-map.ts` ni loyihangizga ko'chiring. `data/` papkasini ham ko'chiring yoki skriptdagi yo'lni o'zgartiring.
2. Paketlar: `npm i three @react-three/fiber @react-three/drei` va `npm i -D @turf/turf tsx @types/three @types/geojson`.
3. `package.json` ga `"build:map": "tsx scripts/build-map.ts"` qo'shing.
4. Xarita sahifasida `<ParkMap mode="miniapp" />` (adminkada `mode="admin"`) ni to'liq ekranli konteynerga qo'ying. Konteyner balandligi bo'lishi kerak, masalan `position: fixed; inset: 0`.

`styles.css` dagi `html`, `body`, `#root` qoidalari to'liq ekranli alohida sahifa uchun yozilgan. Loyihangizda boshqa sahifalar ham bo'lsa, ularni `.app` konteyneriga ko'chiring.

## E'tibor bering
- **Html pinlar** z-index oladi, shuning uchun xarita konteyneriga `isolation: isolate` kerak (`.map` da bor). Aks holda pinlar UI panellar ustiga chiqib qoladi.
- **`frameloop="demand"`**: sahna faqat o'zgarish bo'lganda chiziladi, telefonda batareyani tejaydi. Sahnani o'zingiz o'zgartirsangiz, `invalidate()` ni chaqiring.
- **Koordinatalar** park markaziga nisbatan metrda. Xom Mercator qiymatlarini three.js ga bermang, float32 aniqligi yetmaydi va sahna titraydi.
- **Bundle** ~310 KB gzip (asosan three.js). Xarita alohida sahifada bo'lsa, `React.lazy` bilan alohida chunk qiling.

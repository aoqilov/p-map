# Park xaritasi (3D)

Toshkent, Markaziy bog' (Тельман parki) uchun 3D xarita: gen plan PDF'idan aniq qurilgan yo'llar va hududlar, obyektdan obyektgacha piyoda yo'l, mijoz joylashuvi, Blender'da yasalgan attraksion modellari. Asosan telefonda (Telegram mini-app) ishlaydi.

Stack: React 18 + TypeScript + Vite, three.js / react-three-fiber / drei. Ma'lumot oldindan qayta ishlanadi (Python + Node), brauzer tayyor `park.json` ni o'qiydi.

## Ishga tushirish

```bash
npm install
pip install pypdfium2 shapely numpy   # bir marta (gen plan ajratish uchun)
npm run extract:genplan   # PDF → data/genplan/genplan.geojson
npm run build:genplan     # genplan.geojson + config → src/map/park.json
npm run dev               # http://localhost:5173
npm run build             # production → dist/
npm run build:demo        # hammasi bitta HTML faylda → dist-demo/index.html
```

## Papkalar

```
yana-reference/            gen plan PDF'lari (asosiy manba)
scripts/
  genplan/                 PDF → GeoJSON (Python): extract.py, explication.py (73 obyekt), georef.json (koordinata)
  build-genplan.ts         GeoJSON → src/map/park.json (marshrut grafi, daraxtlar, fonuslar, pinlar)
data/genplan/
  genplan.geojson          oraliq natija (geojson.io'da ochsa bo'ladi)
  existing.geojson         planda faqat ingichka chiziq bilan chizilgan mavjud binolar, Salor kanali, ko'priklar
src/
  ParkMap.tsx, styles.css  interfeys: qidiruv, tablar, ro'yxat, pastki oyna
  map/
    config/                sozlamalar: map.ts (sahna), ui.ts (tablar, pinlar, rejimlar), kassa.ts, services.ts
    park.json              tayyor ma'lumot (~190 KB) — qo'lda o'zgartirilmaydi
    ParkScene.tsx          3D sahna, kamera, boshlang'ich ko'rinish
    layers.tsx             yer, yo'l, bino, daraxt, pinlar, marshrut chizig'i
    attractions.tsx        attraksionlar: model yoki plandagi pushti quti
    GltfModel.tsx          .glb yuklash va animatsiya (rotor, lift*)
    EntranceFountain.tsx   fontanlar va gulzorlar
    water.tsx, fish.tsx    suv, baliqlar
  attractions/             HAR BIR ATTRAKSION ALOHIDA PAPKADA (pastga qarang)
```

## Gen plan: PDF dan xaritaga

Xarita endi `yana-reference/Ген планТэльмана  2025 Цвет.pdf` (AutoCAD vektor PDF, 1:500) dan quriladi:

- **Koordinatalar** — `scripts/genplan/georef.json`. Masshtab plandagi 7 ta radius yozuvidan olingan: 1 pt = 0,1247 m (1:500, 1/√2 ga kichraytirib chop etilgan). Burilish va siljish eski yo'llarga moslangan va sputnik bilan tekshirilgan (basseynlar ~1 m aniqlikda).
- **Turlar plandagi rangdan** aniqlanadi (`extract.py` → `COLOR_KIND`): maysa, suv, bino, attraksion (pushti), bolalar maydoni, maydon. Yo'l va maydonlar = chegara − hamma rangli shakllar.
- **Chegara** — plandagi qalin qizil chiziq (yer uchastkasi).
- **Obyektlar** — plandagi qizil raqamlar eksplikatsiya bilan bog'lanadi (`scripts/genplan/explication.py`, nomlar plandagidek).
- **Marshrut** — yo'l yuzasining markaz chiziqlari (medial o'q) bo'ylab.
- Planda faqat ingichka chiziq bilan chizilgan mavjud binolar (Аристон, Дар, More binosi...), Salor kanali va ko'priklar — `data/genplan/existing.geojson` dan.

## Attraksionlar

Har bir attraksion — `src/attractions/<raqam>-<nom>/` papkasi. Raqam — gen plan eksplikatsiyasidagi raqam (xaritadagi joyi shu bo'yicha topiladi):

```
src/attractions/24-air-race/
  config.ts     model, o'lcham, animatsiya
  model.py      Blender skripti (modelni yasaydi)
  model.blend   Blender'da ochib ko'rish / tahrirlash uchun
  model.glb     xaritaga ulanadigan model
```

- Papkadagi `config.ts` avtomatik yig'iladi (`src/attractions/index.ts`), ro'yxatga qo'lda yozish shart emas.
- `config.ts` da `model` bo'lmasa — xaritada plandagi maydoncha shaklidagi **pushti quti**.
- Narx, yosh/bo'y cheklovi, ish vaqti, rasm — config'da emas: keyin backend API'dan keladi va plan raqami (`num`) orqali bog'lanadi.

**Yangi model qo'shish:**

1. Papkaga `model.py` (namuna: `24-air-race/model.py`) va uni ishga tushirish:
   `blender -b --factory-startup -P src/attractions/<papka>/model.py` → `model.glb`, `model.blend`, `preview.png`.
   Yoki modelni Blender'da qo'lda yasab, `model.glb` qilib eksport qiling (File → Export → glTF 2.0).
2. `config.ts` ga:
   ```ts
   import modelUrl from './model.glb?url';
   export default defineAttraction({
     num: '24', name: 'Air Race',
     model: { url: modelUrl, natural: { width: 9.7, height: 6.0 } }, // asl o'lcham, metr
     size: { width: 9.7, height: 6.0 },                              // xaritadagi o'lcham (ixtiyoriy)
     anim: { secondsPerTurn: 9, lift: { meters: 1.2, seconds: 14, stagger: 0 } },
   });
   ```

**Model qoidalari** (xarita kodi shularga tayanadi):

| Blender'dagi obyekt nomi | Xaritada |
|---|---|
| `rotor` | markaz atrofida aylanadi (`anim.secondsPerTurn`); bolalari ham u bilan birga |
| `lift0`, `lift1`… | yuqoriga-pastga ko'tariladi (`anim.lift`): pastda turish → ko'tarilish → tepada turish → tushish |
| boshqa nomlar | qimirlamaydi |

- Model haqiqiy o'lchamda (metr), markazi (0, 0, 0), Z — tepaga (Blender). Telefon uchun: ~10 ming uchburchakdan kam, ≤ 400 KB.
- Metallik qismlarni 0.3 dan oshirmang — xaritada atrof-muhit aksi yo'q, yuqori metallik qora ko'rinadi.
- Animatsiya ~22 kadr/s; telefonda "harakatni kamaytirish" yoqilgan bo'lsa — to'xtaydi.

## Menyu, kassa va servislar

- **Tablar** (qidiruv ostida): Attraksionlar · Kassa · Xizmatlar · Parking va kirish — `src/map/config/ui.ts` → `MENU_TABS`. Tab bosilsa xaritada faqat shu bo'lim pinlari, pastda ro'yxati.
- **Kassalar** gen planda yo'q: `src/map/config/kassa.ts` → `KASSA` (joyi: plan raqami `near` yoki `lonLat`), keyin `npm run build:genplan`.
- **Servislar** (hojatxona, kafe...): `src/map/config/services.ts` → `SERVICES` (plan raqami bo'yicha nom, bo'lim, yashirish).
- **Telefonda boshlang'ich ko'rinish** — `ParkScene.tsx` → `HOME_VIEW_NARROW` (36° / 205°): park uzun o'qi ekranga tik tushadi; kompyuterda — `HOME_VIEW` (49° / 234°).

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
- **O'lcham:** `config/map.ts` → `PAVEMENT` (`curbWidth` 0.25 m, `curbHeight` 0.15 m). Haqiqiy bordyurdan biroz katta, xaritada ko'rinishi uchun.
- **Ranglar** (`theme.ts`): `roadTop` — plitka rangi; tekstura uni har bir tosh uchun ozgina o'zgartiradi. Yorug' mavzuda `#f6f4ef` (natija ~#d2d1cd), qorong'i mavzuda `#c4c1bb`. Bordyur plitkadan to'qroq (`#9a9da1` / `#6d7075`), shunda yo'l cheti aniq ko'rinadi. Parking asfalt rangida qoldi.

## Suv: hovuz, ariq va basseynlar

Suv endi yerdan pastda turadi: yer plitasidan suv o'rni kesib olingan (`build:genplan` → `groundCut`), chetida tosh qirg'oq bor. Sirti jonli: to'lqin, rang va yaltiroq bor (`water.tsx`, `waterField.ts`, `waterBank.ts`).

Uchta uslub bor (`config/map.ts` → `WATER.bodies`):

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

Kod bor (`water.tsx` → `WaterPlants`), lekin gen plan xaritasida hozircha o'simliklar yo'q (`park.json` → `plants` bo'sh). Kerak bo'lsa, `build-genplan.ts` da hudud berib qo'shiladi.

### Tezlik: suv qanchalik og'ir

To'lqinning o'zi to'liq GPU'da hisoblanadi. CPU har kadrda faqat bitta raqamni (vaqtni) yangilaydi.

O'lchov dasturiy GPU'da (SwiftShader) qilingan. Shuning uchun faqat foizlar ma'noli, o'lchov xatosi ±5% atrofida:

| Holat | Jonli suv oddiy suvga nisbatan |
|---|---|
| Butun park ko'rinishi | +3–4% kadr vaqti |
| Hovuz ekranni to'ldirganda | +15–17% |

Batareyani asosan suv emas, xaritaning doim qayta chizilishi yeydi (~22 kadr/s, attraksionlar va suv harakati uchun). Uni to'xtatish uchun `WATER.animate: false` va attraksionlarda `secondsPerTurn: 0` / `enabled: false` qiling.

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

`config/map.ts` → `FISH.figures` ro'yxatiga bitta qator qo'shing:

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

Soya xaritasini chizish kadrning ~10–17% ini oladi. Kamera surilganda soya o'zgarmaydi, harakatlanuvchi soyalar esa sekin (charxpalak, karusel). Shuning uchun soyalar har kadrda emas, sekundiga 5 marta yangilanadi: `config/map.ts` → `RENDER.shadowUpdatesPerSecond`. Bu kadr vaqtini ~8–13% qisqartiradi. `0` qilsangiz, eski usulda har kadrda yangilanadi.

Daraxtlarni yoqib-o'chirish kabi o'zgarishlarda soya ko'pi bilan 0.2 s ichida yangilanadi. Xarita jim turgan bo'lsa ham, oxirgi o'zgarish uchun alohida kadr chiziladi.

## Ko'cha fonuslari

Fonuslar avtomatik qo'yiladi (`build-genplan.ts` → `LAMP_EVERY`): yo'l markaz chiziqlari bo'ylab har ~30 m da, yo'lning eng yaqin chetiga, maysa tomonga 0.4 m. Keng maydon o'rtasiga (chetdan 6 m dan uzoq) va suvga qo'yilmaydi, bir-biriga 15 m dan yaqin kelganlari tashlab yuboriladi. Hozir ~130 ta.

**Chiroqlarni o'chirish.** Fonuslar joyida qoladi, faqat chiroqlari o'chadi: shisha to'q rangga kiradi, yerdagi yorug'lik va nur yo'qoladi.
- Foydalanuvchi o'ngdagi ustundagi lampochka tugmasi bilan yoqib-o'chiradi.
- Xarita ochilgandagi holat `config/map.ts` → `STREET_LAMP.lightsOn` da (`false` — o'chiq holda ochiladi).
- Komponentga to'g'ridan-to'g'ri: `<ParkScene lampsLit={false} … />`.

Model (`StreetLamps.tsx`): sakkiz qirrali asos, ikki halqali ustun, olti qirrali shisha fonus, uchli tom. Hammasi `InstancedMesh`, shuning uchun fonus soni ko'paysa ham 4 ta draw call bo'ladi. Bitta fonus ~350 uchburchak, soya tashlamaydi: 130 ta fonus jami ~45k uchburchak.

Yorug'lik haqiqiy `PointLight` emas. Yerda iliq doira va fonus atrofida nur chiziladi, chunki o'nlab real chiroq telefonni sekinlashtiradi. Qorong'i mavzuda yorug'lik to'liq kuchda, yorug' mavzuda xira (`STREET_LAMP.dayStrength`). Rang va o'lchamlar `config/map.ts` dagi `STREET_LAMP` bo'limida.

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

Har bir rejimda qaysi funksiya yoqilgani `config/ui.ts` → `MODE_FEATURES` da belgilanadi:

| Funksiya | miniapp | admin |
|---|---|---|
| `location`: "Mening joyim", ko'k nuqta, joyimdan marshrut | ✓ | — |
| `simulation`: joylashuv simulyatsiyasi (sinov uchun) | — | — |

Bitta joyda alohida o'zgartirish ham mumkin: `<ParkMap mode="miniapp" features={{ simulation: true }} />`.

Shu loyihani alohida ishga tushirganda (`npm run dev`) mini-app rejimi ochiladi. Manzil oxiriga `#admin` qo'shsangiz, adminka rejimiga o'tadi.

## park-mini-app ga ulash

1. `src/map/`, `src/attractions/`, `src/ParkMap.tsx`, `src/styles.css` ni loyihangizga ko'chiring. Xarita ma'lumoti (`src/map/park.json`) shu loyihada yangilanadi — ko'chirilgan loyihaga faqat tayyor `park.json` kerak.
2. Paketlar: `npm i three @react-three/fiber @react-three/drei` va `npm i -D @types/three`. Vite kerak (`import.meta.glob`, `?url` importlari).
3. Xarita sahifasida `<ParkMap mode="miniapp" />` (adminkada `mode="admin"`) ni to'liq ekranli konteynerga qo'ying. Konteyner balandligi bo'lishi kerak, masalan `position: fixed; inset: 0`.

`styles.css` dagi `html`, `body`, `#root` qoidalari to'liq ekranli alohida sahifa uchun yozilgan. Loyihangizda boshqa sahifalar ham bo'lsa, ularni `.app` konteyneriga ko'chiring.

## E'tibor bering
- **Html pinlar** z-index oladi, shuning uchun xarita konteyneriga `isolation: isolate` kerak (`.map` da bor). Aks holda pinlar UI panellar ustiga chiqib qoladi.
- **`frameloop="demand"`**: sahna faqat o'zgarish bo'lganda chiziladi, telefonda batareyani tejaydi. Sahnani o'zingiz o'zgartirsangiz, `invalidate()` ni chaqiring.
- **Koordinatalar** park markaziga nisbatan metrda. Xom Mercator qiymatlarini three.js ga bermang, float32 aniqligi yetmaydi va sahna titraydi.
- **Bundle** ~310 KB gzip (asosan three.js). Xarita alohida sahifada bo'lsa, `React.lazy` bilan alohida chunk qiling.


"""Gen plan eksplikatsiyasi (PDF dagi jadval): raqam → (nomi, turi, kategoriya).

Nomlar plandagidek, tarjimasiz. Turlar:
  building   — bino (balandligi bilan chiziladi)
  attraction — attraksion (hozircha quti; keyin Blender modeli bilan almashtiriladi)
  playground — bolalar maydoni / labirint (yer sathida)
  fountain   — fontan (hozircha past quti)
  parking    — avtostoyanka
  entrance   — kirish / darvoza
Kategoriyalar src/map/config.ts → Category bilan bir xil.
"""

E = {
    '1': ('Здание администрации парка', 'building', 'buildings'),
    '2': ('Ресторан "Аристон-парк"', 'building', 'buildings'),
    '3': ('Ресторан "Дар"', 'building', 'buildings'),
    '4': ('Водопроводная насосная станция', 'building', None),
    '5': ('Трансформаторная подстанция', 'building', None),
    '6': ('Трансформаторная подстанция', 'building', None),
    '7': ('Общественный туалет (промывной)', 'building', 'services'),
    '8': ('Общественный туалет (промывной)', 'building', 'services'),
    '9': ('Фонтан', 'fountain', 'fun'),
    '10.1': ('Фонтан', 'fountain', 'fun'),
    '10.2': ('Фонтан "Беседка"', 'fountain', 'fun'),
    '11': ('Фонтан "Каскад"', 'fountain', 'fun'),
    '12': ('Кафе на 10 мест', 'building', 'services'),
    '13': ('Кафе "Замок эльфов"', 'building', 'services'),
    '14': ('Тир', 'attraction', 'fun'),  # bino, lekin 3D model bilan (src/attractions/14-tir) — attraksion sifatida
    '15': ('Кафе на 10 мест', 'building', 'services'),
    '16': ('Домик "Шляпника"', 'building', 'services'),
    '17': ('"Сладкий домик"', 'building', 'services'),
    '18': ('Чoйхона', 'building', 'services'),
    '19': ('"Пряничный домик"', 'building', 'services'),
    '20': ('Кафе "Шоколадная фабрика"', 'building', 'services'),
    '21': ('Аттракцион "Flying tigers 6"', 'attraction', 'fun'),
    '22': ('Аттракцион "Mini tea cups"', 'attraction', 'fun'),
    '23': ('Аттракцион "Magic bikes 6"', 'attraction', 'fun'),
    '24': ('Аттракцион "Air race 2 seats"', 'attraction', 'fun'),
    '25': ('Аттракцион "Slide M 350"', 'attraction', 'fun'),
    '26': ('Аттракцион "Swing 12"', 'attraction', 'fun'),
    '26.1': ('Аттракцион "Flying school"', 'attraction', 'fun'),
    '27': ('Аттракцион "Windstarz"', 'attraction', 'fun'),
    '28': ('Аттракцион "Водные гусеницы"', 'attraction', 'fun'),
    '29': ('Аттракцион "Junior jet 6"', 'attraction', 'fun'),
    '30': ('Детская площадка', 'playground', 'fun'),
    '31': ('Аттракцион "Mini Crazy Mill"', 'attraction', 'fun'),
    '32': ('Аттракцион "3 Loops Coaster"', 'attraction', 'fun'),  # planda: "Spining coaster"
    '33': ('Аттракцион "Gameland"', 'attraction', 'fun'),
    '34': ('Аттракцион "Swing 20"', 'attraction', 'fun'),
    '35': ('Аттракцион "Family swinger"', 'attraction', 'fun'),
    '36': ('Аттракцион "Французская карусель"', 'attraction', 'fun'),
    '37': ('Аттракцион "Space Jet"', 'attraction', 'fun'),  # planda: "Mini jet 6" (Ground loading)
    '38': ('Аттракцион "Galleon 42"', 'attraction', 'fun'),
    '39': ('Аттракцион "Speady coaster"', 'attraction', 'fun'),
    '40': ('Аттракцион "Twist tower"', 'attraction', 'fun'),
    '41': ('Аттракцион "Jumping star 6"', 'attraction', 'fun'),
    '42': ('Аттракцион "Happy swing"', 'attraction', 'fun'),
    '43': ('Аттракцион "Cyclon"', 'attraction', 'fun'),
    '44': ('Аттракцион "Jump around"', 'attraction', 'fun'),
    '45': ('Аттракцион "Автодром"', 'attraction', 'fun'),
    '46': ('Аттракцион "Автодром"', 'attraction', 'fun'),
    '47': ('Аттракцион "Колесо обозрения"', 'attraction', 'fun'),
    '48': ('Здание фудкортов (2 эт.)', 'building', 'services'),
    '49': ('Развлекательный центр', 'building', 'buildings'),
    '50': ('Автостоянка на 367 машины', 'parking', 'parking'),
    '51': ('Автостоянка на 60 машин', 'parking', 'parking'),
    '52': ('Магазин сувениров', 'building', 'services'),
    '53': ('Главный вход', 'entrance', 'entrance'),
    '54': ('Аквапарк', 'building', 'fun'),
    '55': ('Детский лабиринт', 'playground', 'fun'),
    '56': ('Проходная', 'entrance', 'entrance'),
    '57': ('Кафе "Алиса в стране чудес" c летней посадкой', 'building', 'services'),
    '58': ('Кафе "Cладкий мир" c летней посадкой', 'building', 'services'),
    '59': ('"Домик ведьмы" (магазин)', 'building', 'services'),
    '60': ('"Домик хоббита"', 'building', 'services'),
    '61': ('Шатер для проведения мероприятий', 'building', 'fun'),
    '62': ('"Зеленый" театр', 'building', 'fun'),
    '63': ('"Арка"-вход в зону "Музей"', 'entrance', 'fun'),
    '64': ('Арт-объект "Колокольчик"', 'fountain', 'fun'),
    '65': ('Кафе "Cafe de France"', 'building', 'services'),
    '66': ('Французский домик', 'building', 'services'),
    '67': ('Французский домик', 'building', 'services'),
    '68.1': ('Французский домик', 'building', 'services'),
    '68.2': ('Французский домик', 'building', 'services'),
    '69.1': ('Французский домик', 'building', 'services'),
    '69.2': ('Французский домик', 'building', 'services'),
    '70': ('Французский домик', 'building', 'services'),
    '71': ('Французский домик', 'building', 'services'),
    '72': ('Торговый киоск "Choko"', 'building', 'services'),
    '73': ('Веревочный городок', 'playground', 'fun'),
}

# Raqam yozuvi o'z maydonchasidan uzoqda turgan obyektlar: raqam → maydoncha ichidagi nuqta (park metrlari, x sharq, y shimol).
# Joyida tekshirilgan (foydalanuvchi ko'rsatgan). Shu nuqtadagi rangli maydoncha shu raqamga beriladi.
PAD_AT = {
    '41': (-86.95, 47.67),  # Jumping star 6 — yozuv maydonchadan ~28 m sharqda
    '32': (64.0, 85.0),     # 3 Loops Coaster — maydonchasi planda bino rangida chizilgan (21 × 35 m)
    '33': (74.0, 55.0),     # Gameland — bino (26 × 15 m), planda nomsiz bino rangida
    '14': (55.8, -24.3),    # Тир — plandagi 14 yozuvi tor binoga tushgan; haqiqiy tir — 9.7 × 9.8 m bino
}

# Planda attraksionning o'zi (masalan, aylana belgisi) nomsiz bino bo'lib chiqqan joylar — o'rniga 3D model qo'yiladi,
# shu nuqtadagi nomsiz shakl xaritaga chiqmaydi (park metrlari)
DROP_AT = [
    (49.6, 97.8),  # 26 — Swing 12 maydonchasidagi aylana
    (51.4, 90.6),  # 31 — Mini Crazy Mill maydonchasidagi aylana
]

# Planda chiziqlar bilan bo'laklarga bo'lingan bitta attraksion maydonchasi: raqam → qo'shiladigan nomsiz bo'laklar ichidagi
# nuqtalar (park metrlari). Bo'laklarni o'rab oluvchi eng kichik doira olinadi
MERGE_PADS = {
    '29': [(61.07, 14.86)],  # Junior jet 6 — doiraning shimoliy qismi alohida "Аттракцион" bo'lib chiqqan
}

# Obyektlar orasidagi tor plitka oraliq birinchisiga qo'shiladi: (qaysi raqamga, qaysi raqam bilan oraliq, eng katta eni m)
MERGE_GAPS = [
    ('30', '28', 3.0),  # Детская площадка ↔ Водные гусеницы: oraliq maydoncha hududi, asfalt emas
]

# Planda nomsiz chizilgan binolar: shu nuqtadagi bino nom, kategoriya (pin chiqadi) va rang oladi (park metrlari).
# Rang — xaritadagi devor/tom rangi (berilmasa — oddiy bino rangi). Raqamli bino (PAD_AT) shu yerdan faqat rang oladi
NAME_AT: dict[tuple[float, float], tuple[str, str, str]] = {
    # (x, y): ('Nomi', 'kategoriya', '#rang'),
}

# Raqamsiz attraksion maydonchalari: plandagi yozuv → haqiqiy nomi (attraksion almashgan bo'lsa).
# None — attraksion yo'q: xaritaga chiqmaydi, pin yo'q, o'rni yo'l plitasi bo'ladi
RENAME_UNNAMED = {
    'Батут': 'VR-9D Cinema',  # batut olib tashlangan, o'rnida VR-9D kinoteatr (src/attractions/vr-9d-cinema)
    'Башня SKY TOWER': None,  # olib tashlangan
}

# Bino balandligi (m), qolganlari — HEIGHT_DEFAULT
HEIGHT = {'1': 7, '2': 7, '3': 6, '48': 8, '49': 18, '54': 8, '65': 7, '13': 6, '61': 6}
HEIGHT_DEFAULT = 3.5

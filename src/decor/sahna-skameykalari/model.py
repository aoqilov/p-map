"""
Sahna oldidagi skameyka — suyanchiqli park skameykasi: sariq-to'q sariq yog'och reykalar (o'tirg'ich 3 ta, suyanchiq 2 ta),
3 ta qora cho'yan oyoq (old oyoq egilgan, orqa oyoq suyanchiqqa ko'tariladi). Rasm: foydalanuvchi fotosurati.
Xaritada 20 nusxa (config.ts), yozgi sahnaga qaragan.

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/decor/sahna-skameykalari/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png

Old tomoni (o'tirgan odam qaraydigan tomon) — Blender'da -Y, suyanchiq +Y da. Markaz — (0, 0); oyoqlari z = 0.12 da
(yo'l plitkasi yuzasi). Asl o'lcham: uzunligi 3.0 m, chuqurligi ~0.6 m, balandligi ~0.98 m (yerdan).
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from blender_kit import Kit  # noqa: E402

PALETTE = {'wood': (0.7, 0.33, 0.06), 'wood_d': (0.55, 0.24, 0.04), 'iron': (0.03, 0.03, 0.035)}
k = Kit(PALETTE)
p = []

L = 3.0            # uzunligi
SEAT_Z = 0.45      # o'tirg'ich balandligi
LEGS = (-1.3, 0.0, 1.3)

# o'tirg'ich: 3 ta reyka, suyanchiq: 2 ta reyka (biroz orqaga qiya)
for i, y in enumerate((-0.17, -0.04, 0.09)):
    p.append(k.box((L, 0.11, 0.04), (0, y, SEAT_Z), 'wood' if i % 2 == 0 else 'wood_d'))
for z, y in ((0.6, 0.2), (0.77, 0.24)):
    p.append(k.box((L, 0.04, 0.12), (0, y, z), 'wood', rot=(-0.17, 0, 0)))

# cho'yan oyoqlar: old oyoq (pastda oldga egilgan), orqa oyoq suyanchiq tepasigacha, o'tirg'ich osti, tovonlar
for x in LEGS:
    p.append(k.beam((x, -0.2, SEAT_Z - 0.02), (x, -0.24, 0.12), 0.05, 0.04, 'iron'))
    p.append(k.beam((x, -0.24, 0.12), (x, -0.3, 0.0), 0.05, 0.04, 'iron'))
    p.append(k.beam((x, 0.14, 0.0), (x, 0.12, SEAT_Z), 0.05, 0.04, 'iron'))
    p.append(k.beam((x, 0.12, SEAT_Z), (x, 0.28, 0.85), 0.05, 0.04, 'iron'))
    p.append(k.box((0.05, 0.38, 0.04), (x, -0.04, SEAT_Z - 0.04), 'iron'))
    p.append(k.box((0.09, 0.1, 0.02), (x, -0.3, 0.01), 'iron'))
    p.append(k.box((0.09, 0.1, 0.02), (x, 0.14, 0.01), 'iron'))

# Yo'l plitkasi yuzasi 0.12 m (layers.tsx → ROAD_TOP): skameyka plitka ustida tursin, oyoqlari ichiga botmasin
for ob in p:
    ob.location.z += 0.12

k.finish('SKAMEYKA', p, HERE, [('preview.png', (2.2, -2.6, 1.5), (0, 0, 0.4))])

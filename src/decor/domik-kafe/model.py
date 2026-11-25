"""
Kafe uychasi — ertak do'kon-uycha (rasm: foydalanuvchi fotosurati, chapdagi g'ishtli uychalar): qizil-jigarrang g'isht,
burchaklarda oq hoshiya, pastda ravoqli deraza va ravoqli eshik, oq karniz, old tomonda oq hoshiyali uchburchak fronton
(ichida kichik deraza), jigarrang tom, pushti dumaloq lavha, devor chirog'i.

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/decor/domik-kafe/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png

Old tomoni — Blender'da -Y. Asl o'lcham: 4.0 × 3.6 m, balandligi ~5.6 m.
Xaritada plandagi bino iziga moslab kichraytiriladi (config.ts → size).
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from blender_kit import Kit  # noqa: E402
from domik_kit import DomikKit, PALETTE, GLOW  # noqa: E402

k = Kit(PALETTE, glow=GLOW)
d = DomikKit(k)

W, D, H = 4.0, 3.6, 4.0
Y = -D / 2

d.block(W, D, H, mat='brick')
for s in (-1, 1):                                                       # burchak hoshiyalari (oq "toshlar")
    for i in range(6):
        d.add(k.box((0.24 if i % 2 else 0.16, 0.06, 0.32), (s * (W / 2 - 0.1), Y - 0.02, 0.7 + i * 0.55), 'white'))
d.arch(-0.85, 0.7, 1.0, 1.7, Y - 0.01, fill='glass')
d.arch(0.95, 0.45, 0.85, 2.1, Y - 0.01, fill='door')
d.panel(-0.85, 0.5, 1.2, 0.15, Y - 0.01, 'white')                       # deraza tokchasi
d.band(-W / 2, W / 2, 2.85, Y, h=0.14)
d.arch(-0.85, 3.1, 0.45, 0.75, Y, fill='glass', frame_w=0.07)
d.arch(0.95, 3.1, 0.45, 0.75, Y, fill='glass', frame_w=0.07)
d.band(-W / 2, W / 2, H - 0.06, Y, h=0.16)
RISE = 1.5
d.gable_roof(W, D, H, RISE, ridge_along='y', over=0.25, gable_mat='plaster')
d.window_rect(0, H + 0.3, 0.45, 0.55, Y, fill='glass')
d.round_sign(1.75, 2.6, Y, r=0.34, mat='sign_p')
d.wall_lamp(0.1, 2.2, Y)

k.finish('DOMIK-KAFE', d.p, HERE, [('preview.png', (5.5, -11.0, 5.0), (0, 0, 2.6))])

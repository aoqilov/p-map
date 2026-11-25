"""
Burger uychasi — ertak do'kon-uycha (rasm: foydalanuvchi fotosurati, "Telman's burgers"): sariq g'ishtli fasad, chapda oq
suvoqli qism va ravoqli derazada burger plakati, o'ngda to'q g'ishtli qism va ingichka ravoqli derazalar, o'rtada ravoqli
jigarrang eshik, tepada ravoqli deraza, old tomonda tik uchli fronton va jigarrang tom (chetida chiroqchalar),
qizil dumaloq lavha, devor chirog'i.

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/decor/domik-burger/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png

Old tomoni — Blender'da -Y. Asl o'lcham: 4.0 × 3.6 m, balandligi ~6.3 m.
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

W, D, H, FL = 4.0, 3.6, 4.4, 2.6
Y = -D / 2

d.block(W, D, H, mat='brick_y')
# ---------- fasad bo'laklari: chapda oq suvoq, o'ngda to'q g'isht ----------
d.panel(-1.45, 0.45, 1.1, H - 0.45, Y, 'plaster')
d.panel(1.55, 0.45, 0.9, H - 0.45, Y, 'brick')
for i in range(7):                                                      # sariq g'isht qatorlari (yo'l-yo'l)
    d.add(k.box((1.85, 0.02, 0.03), (0.05, Y - 0.015, 0.7 + i * 0.5), 'orange'))
d.arch(-1.45, 0.75, 0.75, 1.55, Y - 0.01, fill='poster_y')               # burger plakati
d.arch(0.35, 0.45, 0.8, 2.05, Y - 0.01, fill='door')
d.window_rect(0.95, 0.9, 0.3, 0.9, Y - 0.01, fill='poster')
for x in (1.35, 1.75):
    d.arch(x, 1.0, 0.26, 1.2, Y - 0.01, fill='glass', frame_w=0.06, mullion=False)
d.band(-W / 2, W / 2, FL, Y, h=0.14)
# ---------- 2-qavat ----------
d.arch(0.35, FL + 0.35, 0.55, 1.1, Y, fill='glass')
d.arch(-1.45, FL + 0.4, 0.5, 0.95, Y, fill='glass')
for x in (1.35, 1.75):
    d.arch(x, FL + 0.4, 0.24, 1.0, Y, fill='glass', frame_w=0.05, mullion=False)
d.band(-W / 2, W / 2, H - 0.06, Y, h=0.14)
# ---------- tik fronton va tom, chetida chiroqchalar ----------
RISE = 1.85
d.gable_roof(W, D, H, RISE, ridge_along='y', over=0.3, gable_mat='plaster')
for i in range(9):
    t = i / 8
    for s in (-1, 1):
        d.add(k.ball(0.04, (s * (W / 2 + 0.25) * (1 - t), Y - 0.35, H - 0.05 + RISE * t), 'lamp', sub=1))
d.arch(0, H + 0.25, 0.4, 0.75, Y, fill='glass', frame_w=0.07)
d.round_sign(-0.55, 3.2, Y, r=0.4)
d.wall_lamp(1.0, 2.25, Y)

k.finish('DOMIK-BURGER', d.p, HERE, [('preview.png', (5.5, -11.0, 5.0), (0, 0, 2.8))])

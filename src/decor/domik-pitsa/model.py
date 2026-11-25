"""
Pitsa uychasi — ertak do'kon-uycha (rasm: foydalanuvchi fotosurati, park ichidagi pitsa do'koni): g'ishtli ikki qavatli
fasad, pastda oq ustunchalar orasida to'q sariq panellar, uchta ravoqli derazada qizil pitsa plakatlari va ravoqli eshik,
tepada ikki ravoqli deraza va oq balyustrada, ikki burchakda oq-to'q sariq minoracha (ustunchali ayvoncha, jigarrang konus
tom), minorada qizil dumaloq lavha, devor chiroqlari, jigarrang past tom.

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/decor/domik-pitsa/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png

Old tomoni — Blender'da -Y. Asl o'lcham: asosiy blok 6.0 × 3.6 m (minoralar bilan eni ~7.3 m), balandligi ~6.6 m.
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

W, D, H, FL = 6.0, 3.6, 4.6, 2.6        # eni, chuqurligi, devor balandligi, 1-qavat tepasi
Y = -D / 2

d.block(W, D, H)
# ---------- 1-qavat: oq ustunchalar, to'q sariq panellar, ravoqli plakat-derazalar, eshik ----------
d.panel(0, 0.45, W - 0.1, FL - 0.45, Y, 'plaster')
for x in (-2.65, -1.25, 0.15, 1.45, 2.75):
    d.pilaster(x, 0.45, FL, Y, w=0.18)
for x in (-1.95, -0.55):
    d.panel(x, 0.5, 0.95, 0.45, Y - 0.005, 'orange')
d.panel(0.8, 0.5, 1.0, 1.95, Y - 0.005, 'orange')
for x in (-1.95, -0.55):
    d.arch(x, 1.05, 0.78, 1.4, Y - 0.01, fill='poster')
d.arch(2.1, 0.45, 0.95, 2.05, Y - 0.01, fill='door')
d.panel(2.1, 0.75, 0.55, 1.2, Y - 0.08, 'poster')                     # eshik oynasidagi plakat
d.band(-W / 2, W / 2, FL, Y, h=0.16)
# ---------- 2-qavat: ravoqli derazalar, oq to'rtburchak bezaklar, balyustrada ----------
for x in (-1.6, -0.2):
    d.arch(x, FL + 0.4, 0.62, 1.15, Y, fill='glass')
for x in (-2.35, -0.9, 0.55):
    for i in range(4):
        d.add(k.box((0.22 if i % 2 else 0.14, 0.05, 0.18), (x, Y - 0.02, FL + 0.35 + i * 0.3), 'white'))
d.add(k.box((1.6, 0.25, 0.1), (1.6, Y - 0.12, FL + 0.15), 'white'),
      k.box((1.6, 0.25, 0.1), (1.6, Y - 0.12, FL + 1.05), 'white'))
for i in range(6):
    d.add(k.cyl(0.06, 0.8, (0.95 + i * 0.26, Y - 0.12, FL + 0.6), 'white', segs=6, r2=0.04))
d.band(-W / 2, W / 2, H - 0.08, Y, h=0.18)
d.flat_roof(W, D, H)
# ---------- minorachalar (chapda kichik, o'ngda katta) ----------
d.tower(-W / 2 + 0.05, Y + 0.25, 0.5, 4.5)
d.tower(W / 2 + 0.1, Y + 0.35, 0.72, 5.1)
d.round_sign(-W / 2 + 0.05, 3.0, Y - 0.2, r=0.36)
for x in (-1.25, 1.45):
    d.wall_lamp(x, 2.25, Y)

k.finish('DOMIK-PITSA', d.p, HERE, [('preview.png', (6.5, -13.0, 5.5), (0, 0, 2.8))])

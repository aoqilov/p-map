"""
Ping pong — to'rtta ochiq havodagi beton stol tennisi stoli yonma-yon, rezina qoplamali maydonchada.
Rasm: foydalanuvchi skrinshoti (4 ta stol qatori), joyi — place.ts.

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/ping-pong/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png, preview_top.png

Tuzilish (bitta `base` obyekt, animatsiyasiz): yassi yashil maydoncha plitasi (xaritadagi maydoncha izidan 5 sm kichik —
shu iz ostidagi plitka bilan chegaralanadi), ustida 4 ta bir xil stol. Har bir stol standart o'lchamda (2.74 × 1.525 m,
tepa yuzasi 0.76 m): ko'k tepa va oq chiziqlar (chet, o'rta), ikki uchida beton tayanch (poydevor va bel bilan),
o'rtada po'lat to'r (ustida oq lenta, ikki ustun), stol ustida ikki raketka va to'p.
Stollarning uzun tomoni — Blender'da Y o'qi bo'ylab (o'yinchilar ±Y uchlarida), qator — X bo'ylab, markaz — (0, 0).
Asl o'lcham: 18.9 × 4.7 m, balandligi ~1.12 m (plita ustidagi to'r ustunlari bilan).
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'decor'))
from blender_kit import Kit  # noqa: E402

PALETTE = {
    'court': (0.07, 0.22, 0.1),
    'top': (0.07, 0.27, 0.58), 'line': (0.95, 0.95, 0.93), 'concrete': (0.64, 0.63, 0.6), 'concrete_d': (0.5, 0.49, 0.47),
    'net': (0.16, 0.18, 0.21), 'steel': (0.58, 0.6, 0.62), 'ball': (1.0, 0.55, 0.12),
    'rubber_r': (0.78, 0.12, 0.13), 'rubber_k': (0.09, 0.09, 0.1), 'wood': (0.72, 0.5, 0.3),
}
k = Kit(PALETTE)
p = []

# ====================== o'lchamlar (metr) ======================
PAD_W, PAD_D = 19.0, 4.8    # xaritadagi maydoncha izi (place.ts → width, depth); plita undan 0.1 m kichik
SLAB_T = 0.18               # plita qalinligi: yo'l yuzasi 0.12 m (layers.tsx → ROAD_TOP), plita shundan 6 sm baland — aks holda titraydi
COUNT, GAP = 4, 5.0         # stollar soni va o'qlari orasidagi masofa (m)

L, W = 2.74, 1.525          # stol: uzunligi (Y) × eni (X)
H = 0.76                    # tepa yuzasi balandligi
T = 0.05                    # tepa plita qalinligi
LINE_T = 0.003              # chiziq qalinligi (tepa yuzasidan chiqib turadi)
NET_H = 0.1525              # to'r balandligi
NET_L = 1.83                # to'r uzunligi (stol eni + har tomondan 15.25 sm)

# ---------- maydoncha plitasi ----------
p.append(k.box((PAD_W - 0.1, PAD_D - 0.1, SLAB_T), (0, 0, SLAB_T / 2), 'court'))

OX = 0.0                    # hozir yasalayotgan stolning X dagi o'rni


def box(size, loc, mat, rot=(0, 0, 0)):
    """Stolning mahalliy koordinatasidagi quti → plita ustidagi shu stol o'rniga"""
    return k.box(size, (loc[0] + OX, loc[1], loc[2] + SLAB_T), mat, rot)


def table():
    # ---------- tepa plita va oq chiziqlar ----------
    p.append(box((W, L, T), (0, 0, H - T / 2), 'top'))
    zl = H + LINE_T / 2
    for sx in (-1, 1):                                              # yon chiziqlar (uzun tomonlar)
        p.append(box((0.02, L, LINE_T), (sx * (W / 2 - 0.01), 0, zl), 'line'))
    for sy in (-1, 1):                                              # oxirgi chiziqlar (qisqa tomonlar)
        p.append(box((W - 0.04, 0.02, LINE_T), (0, sy * (L / 2 - 0.01), zl), 'line'))
    p.append(box((0.012, L - 0.04, LINE_T), (0, 0, zl), 'line'))    # o'rta chiziq (juftlik o'yini uchun)

    # ---------- beton tayanchlar: ikki uchida tik plita, poydevor va ularni tutashtiruvchi bel ----------
    LEG_Y, FOOT_T = 1.0, 0.05
    for sy in (-1, 1):
        p.append(box((1.4, 0.5, FOOT_T), (0, sy * LEG_Y, FOOT_T / 2), 'concrete_d'))                              # poydevor
        p.append(box((1.2, 0.14, H - T - FOOT_T), (0, sy * LEG_Y, FOOT_T + (H - T - FOOT_T) / 2), 'concrete'))   # tik plita
    p.append(box((0.22, 2 * LEG_Y, 0.14), (0, 0, FOOT_T + 0.07), 'concrete_d'))                                  # bel

    # ---------- to'r: po'lat plastina, ustida oq lenta, ikki chetida ustun ----------
    p.append(box((NET_L - 0.04, 0.008, NET_H), (0, 0, H + NET_H / 2), 'net'))
    p.append(box((NET_L - 0.04, 0.014, 0.016), (0, 0, H + NET_H - 0.006), 'line'))
    post_x = NET_L / 2 - 0.015                                      # ustun markazi (stol chetidan ~0.14 m tashqarida)
    z0, z1 = H - 0.055, H + NET_H + 0.03
    for sx in (-1, 1):
        p.append(box((0.03, 0.045, z1 - z0), (sx * post_x, 0, (z0 + z1) / 2), 'steel'))                           # ustun
        arm = post_x + 0.015 - (W / 2 - 0.04)                                                                     # tepa plita chetidan ustungacha
        p.append(box((arm, 0.05, 0.03), (sx * ((post_x + 0.015 + W / 2 - 0.04) / 2), 0, H - 0.04), 'steel'))     # mahkamlagich qo'l

    # ---------- ustida: ikki raketka va to'p ----------
    def paddle(x, y, ang, rubber):
        """Raketka stol ustida yotibdi: g'ildirak (aylana) + yog'och dasta. ang — Z atrofida burilish (rad)"""
        z = H + LINE_T + 0.006
        p.append(k.cyl(0.075, 0.012, (x + OX, y, z + SLAB_T), rubber, segs=18))
        d = 0.075 + 0.045                                           # blade markazidan dasta markazigacha
        p.append(box((0.026, 0.09, 0.016), (x + math.sin(ang) * d, y - math.cos(ang) * d, z), 'wood', rot=(0, 0, ang)))

    paddle(-0.34, -0.8, 0.35, 'rubber_r')
    paddle(0.30, 0.78, math.pi - 0.25, 'rubber_k')
    p.append(k.ball(0.02, (0.12 + OX, -0.45, H + LINE_T + 0.02 + SLAB_T), 'ball', sub=1))


for i in range(COUNT):
    OX = (i - (COUNT - 1) / 2) * GAP
    table()

k.finish('PING-PONG', p, HERE, [
    ('preview.png', (11.0, -13.0, 9.0), (0, 0, 0.5)),
    ('preview_top.png', (0.01, -3.0, 22.0), (0, 0, 0.5)),
])

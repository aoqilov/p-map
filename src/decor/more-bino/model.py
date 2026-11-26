"""
"Море — Водный комплекс" binolari (planda More_Bino: building-136 — katta blok, building-137 — 2-blok).
Tashqi ko'rinishi — foydalanuvchi fotosuratlari bo'yicha: och bej (shtukaturka) devor, granit sokol, keng chiqib turgan
pilyastrlar, ular orasida baland to'q (ko'kish-kulrang) oynalar, oynalar o'rtasida va tepasida jigarrang yog'och
panellar, ba'zi oraliqlarda oq naqshli (panjara) panellar. Katta blokda old tomon o'rtasida ikki juft shisha eshik (qora ramka),
tepasida jigarrang yog'och peshtaxta: "MOPE" (O — to'q sariq), granit zinapoya, yonlarida butalar, axlat qutisi.
2-blok — shu uslubdagi yopiq quti: eshigi, peshtaxtasi va zinapoyasi yo'q (yashirin eshik orqali kiriladi).

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/decor/more-bino/model.py [-- <preview_papka>]
Natija shu papkada: blok1.blend/.glb, blok2.blend/.glb, preview_blok1.png, preview_blok2.png

Old tomoni (kirish) — Blender'da -Y, eni (X) — bino uzunligi bo'ylab. Origin — bino izining markazi.
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from blender_kit import Kit  # noqa: E402

PALETTE = {
    'wall': (0.86, 0.82, 0.75), 'wall_l': (0.9, 0.87, 0.81), 'granite': (0.52, 0.53, 0.54), 'granite_d': (0.42, 0.43, 0.44),
    'glass': (0.2, 0.27, 0.31), 'frame': (0.1, 0.11, 0.12), 'wood': (0.38, 0.22, 0.13), 'wood_d': (0.27, 0.15, 0.09),
    'lattice': (0.93, 0.93, 0.92), 'roof': (0.45, 0.45, 0.46), 'unit': (0.62, 0.63, 0.64),
    'sign_w': (0.97, 0.96, 0.93), 'sign_o': (0.96, 0.6, 0.15), 'leaf': (0.2, 0.42, 0.18), 'bin': (0.2, 0.24, 0.27),
}

H = 8.4          # devor tepasi (parapet ostigacha)
PL = 0.6         # granit sokol / kirish maydonchasi balandligi
PIL = 1.0        # pilyastr eni
PIL_OUT = 0.28   # pilyastr chiqishi
BAY = 3.0        # oraliq (deraza) eni — mo'ljal
Z_BAND = (4.2, 4.75)   # o'rtadagi yog'och band
Z_TOP = H - 1.05       # tepadagi yog'och panel pastki cheti


def build(name, W, D, main=True):
    k = Kit(PALETTE)
    bpy_mat = k.mats
    bpy_mat['glass'].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.12
    bpy_mat['glass'].node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = 0.3
    for g in ('sign_w', 'sign_o'):  # kechasi peshtaxta yonib turadi
        b = bpy_mat[g].node_tree.nodes['Principled BSDF']
        b.inputs['Emission Color'].default_value = (*PALETTE[g], 1)
        b.inputs['Emission Strength'].default_value = 1.0
    p = []

    # ---------- tomonlar: (o'rta nuqta, tangens, tashqi normal, uzunlik) ----------
    FACES = {
        'front': ((0, -D / 2), (1, 0), (0, -1), W),
        'back': ((0, D / 2), (-1, 0), (0, 1), W),
        'left': ((-W / 2, 0), (0, -1), (-1, 0), D),
        'right': ((W / 2, 0), (0, 1), (1, 0), D),
    }

    def fbox(face, u, off, z0, z1, su, so, mat):
        """Tomon koordinatasida quti: u — tomon bo'ylab markaz, off — devordan tashqariga (markaz), z0..z1 — balandlik"""
        (cx, cy), (tx, ty), (nx, ny), _ = FACES[face]
        x, y = cx + tx * u + nx * off, cy + ty * u + ny * off
        size = (su, so, z1 - z0) if tx else (so, su, z1 - z0)
        return k.box(size, (x, y, (z0 + z1) / 2), mat)

    # ---------- korpus, sokol, tom, parapet ----------
    p.append(k.box((W, D, H - PL), (0, 0, (H + PL) / 2), 'wall'))
    p.append(k.box((W + 0.12, D + 0.12, PL), (0, 0, PL / 2), 'granite'))
    PAR = 0.45
    for face, (_, _, _, L) in FACES.items():  # parapet (biroz chiqib turgan qopqoq bilan)
        p.append(fbox(face, 0, -0.15, H, H + PAR, L, 0.3, 'wall'))
        p.append(fbox(face, 0, -0.12, H + PAR, H + PAR + 0.08, L + 0.1, 0.42, 'wall_l'))
    p.append(k.box((W - 0.6, D - 0.6, 0.06), (0, 0, H + 0.03), 'roof'))
    # tomdagi konditsioner bloklari, ventilyatsiya qutilari
    for i in range(max(2, int(W // 12))):
        x = -W / 2 + 4 + i * (W - 8) / max(1, max(2, int(W // 12)) - 1)
        p.append(k.box((2.2, 1.4, 1.0), (x, D / 4, H + 0.5), 'unit'))
        p.append(k.cyl(0.45, 0.08, (x, D / 4, H + 1.04), 'granite_d', segs=12))

    # ---------- oraliq (deraza) turlari ----------
    def window_bay(face, u, bw, lattice=False):
        r = []
        g = 0.02  # oyna devordan biroz oldinda
        r.append(fbox(face, u, g, PL + 0.1, Z_BAND[0], bw - 0.3, 0.04, 'glass'))
        r.append(fbox(face, u, 0.06, Z_BAND[0], Z_BAND[1], bw - 0.1, 0.12, 'wood'))           # o'rtadagi yog'och band
        if lattice:  # tepasi — oq naqshli panjara panel (ichkariga botgan tirqishda)
            r.append(fbox(face, u, g, Z_BAND[1], H - 0.3, bw - 0.3, 0.04, 'glass'))
            lw, lz0, lz1 = min(1.3, bw - 0.8), Z_BAND[1] + 0.35, H - 0.6
            r.append(fbox(face, u, 0.05, lz0, lz1, lw, 0.05, 'lattice'))
            # rombsimon naqsh: diagonal chiziqlar
            step = 0.42
            n = int((lz1 - lz0) / step)
            for i in range(n):
                zc = lz0 + (i + 0.5) * (lz1 - lz0) / n
                for j in (-1, 0, 1):
                    uu = u + j * lw / 3
                    for s in (-1, 1):
                        (cx, cy), (tx, ty), (nx, ny), _ = FACES[face]
                        a = (uu - 0.18, zc - s * 0.18)
                        b2 = (uu + 0.18, zc + s * 0.18)
                        pa = (cx + tx * a[0] + nx * 0.09, cy + ty * a[0] + ny * 0.09, a[1])
                        pb = (cx + tx * b2[0] + nx * 0.09, cy + ty * b2[0] + ny * 0.09, b2[1])
                        r.append(k.beam(pa, pb, 0.05, 0.04, 'granite'))
            for s in (-1, 1):  # panel ramkasi (yon chiziqlar)
                r.append(fbox(face, u + s * lw / 2, 0.08, lz0, lz1, 0.06, 0.06, 'wall_l'))
        else:
            r.append(fbox(face, u, g, Z_BAND[1], Z_TOP, bw - 0.3, 0.04, 'glass'))
            r.append(fbox(face, u, 0.06, Z_TOP, H - 0.25, bw - 0.1, 0.12, 'wood'))           # tepadagi yog'och panel
            for i in range(4):  # yog'och reykalar (gorizontal chiziqlar)
                z = Z_TOP + 0.15 + i * (H - 0.25 - Z_TOP - 0.3) / 3
                r.append(fbox(face, u, 0.13, z - 0.015, z + 0.015, bw - 0.12, 0.03, 'wood_d'))
        # deraza ramkasi: o'rtada tik ustuncha (qora)
        r.append(fbox(face, u, 0.05, PL + 0.1, Z_BAND[0], 0.06, 0.05, 'frame'))
        return r

    def door_bay(face, u, bw):
        r = []
        DT = 3.4  # eshik tepasi
        for s in (-1, 1):  # ikki tabaqali shisha eshik
            uu = u + s * (bw - 0.4) / 4
            r.append(fbox(face, uu, 0.02, PL, DT, (bw - 0.4) / 2 - 0.08, 0.04, 'glass'))
            ww = (bw - 0.4) / 2
            for z0, z1 in ((PL, PL + 0.08), (DT - 0.08, DT)):
                r.append(fbox(face, uu, 0.06, z0, z1, ww, 0.08, 'frame'))
            for e in (-1, 1):
                r.append(fbox(face, uu + e * ww / 2, 0.06, PL, DT, 0.08, 0.08, 'frame'))
            r.append(fbox(face, u + s * 0.12, 0.14, PL + 0.6, PL + 2.0, 0.04, 0.05, 'frame'))  # uzun tutqich
            # eshik oynasidagi oq "MOPE" yozuvi (logotip)
            r.append(fbox(face, uu, 0.045, PL + 0.95, PL + 1.3, ww * 0.6, 0.01, 'lattice'))
        r.append(fbox(face, u, 0.02, DT, Z_BAND[0], bw - 0.3, 0.04, 'glass'))
        r.append(fbox(face, u, 0.1, DT + 0.05, Z_BAND[1] - 0.05, bw - 0.1, 0.2, 'wood'))      # eshik usti yog'och
        r.append(fbox(face, u, 0.3, Z_BAND[1] - 0.4, Z_BAND[1] - 0.2, 0.3, 0.2, 'frame'))       # chiroq
        r.append(fbox(face, u, 0.02, Z_BAND[1], Z_TOP, bw - 0.3, 0.04, 'glass'))
        r.append(fbox(face, u, 0.06, Z_TOP, H - 0.25, bw - 0.1, 0.12, 'wood'))
        return r

    # ---------- tomonlar: pilyastrlar va oraliqlar ----------
    for face, (_, _, _, L) in FACES.items():
        n = max(1, round((L - PIL) / (BAY + PIL)))
        entrance = main and face == 'front'  # 2-blokda eshik yo'q (ichkaridan, yashirin eshik orqali kiriladi)
        if entrance and main and n % 2:
            n += 1  # asosiy blok: o'rtada pilyastr, ikki yonida eshik
        bw = (L - PIL * (n + 1)) / n
        doors = set()
        if entrance:
            doors = {n // 2 - 1, n // 2} if n % 2 == 0 else {n // 2}
        for i in range(n + 1):  # pilyastrlar (burchaklarda ham)
            u = -L / 2 + PIL / 2 + i * (bw + PIL)
            p.append(fbox(face, u, PIL_OUT / 2, PL, H, PIL, PIL_OUT, 'wall'))
            p.append(fbox(face, u, PIL_OUT / 2 + 0.02, 0, PL + 0.25, PIL + 0.06, PIL_OUT + 0.06, 'granite'))  # granit tagi
        for i in range(n):
            u = -L / 2 + PIL + bw / 2 + i * (bw + PIL)
            if i in doors:
                p.extend(door_bay(face, u, bw))
            else:
                # chetdagi va har to'rtinchi oraliq — naqshli panel
                lattice = i in (0, n - 1) if face in ('front', 'back') and n > 3 else (i % 2 == 1 and n > 2)
                p.extend(window_bay(face, u, bw, lattice))

    # ---------- kirish: peshtaxta, zinapoya, butalar (faqat katta blokda) ----------
    if main:
        entrance_parts(k, p, D)

    k.finish(f'MORE-{name.upper()}', p, HERE, [
        (f'preview_{name}.png', (-W * 0.35, -D / 2 - max(16, W * 0.45), 10), (0, -D / 2, 3.5)),
        (f'preview_{name}_front.png', (0, -D / 2 - 17, 3.0), (0, -D / 2, 4.5)),
    ], name=name)


def entrance_parts(k, p, D, main=True):
    YF = -D / 2
    SW, SH = (7.2, 2.0) if main else (5.0, 1.5)       # peshtaxta eni, balandligi
    sz0 = H - SH + 0.55
    p.append(k.box((SW, 0.5, SH), (0, YF - 0.25, sz0 + SH / 2), 'wood'))
    for i in range(int(SW / 0.18)):  # tik yog'och reykalar
        x = -SW / 2 + 0.09 + i * 0.18
        p.append(k.box((0.06, 0.04, SH - 0.1), (x, YF - 0.52, sz0 + SH / 2), 'wood_d'))
    # "MOPE" (lotin harflari kirillcha МОРЕ bilan bir xil ko'rinadi), O — to'q sariq
    size = SH * 0.55
    letters = [('M', 'sign_w'), ('O', 'sign_o'), ('P', 'sign_w'), ('E', 'sign_w')]
    obs, widths = [], []
    for ch, mat in letters:
        ob = k.text(ch, size, (0, YF - 0.58, sz0 + SH * 0.6), mat, depth=0.06)
        xs = [v.co.x for v in ob.data.vertices]
        obs.append((ob, min(xs), max(xs)))
        widths.append(max(xs) - min(xs))
    gap = size * 0.1
    total = sum(widths) + gap * (len(obs) - 1)
    x = -total / 2
    for ob, x0, x1 in obs:
        ob.location.x = x - x0
        x += (x1 - x0) + gap
        p.append(ob)
    sub = k.text('водный комплекс', size * 0.26, (0, YF - 0.58, sz0 + SH * 0.2), 'sign_w', depth=0.03)
    if len(sub.data.vertices):
        p.append(sub)

    # granit zinapoya: kirish maydonchasi (sokol balandligida) + 3 pog'ona
    EW = 9.5 if main else 6.0
    LAND = 1.2
    p.append(k.box((EW, LAND, PL), (0, YF - LAND / 2, PL / 2), 'granite'))
    for i in range(3):
        h = PL * (3 - i) / 3
        d = LAND + 0.45 * (i + 1)
        p.append(k.box((EW + 1.2 * (i + 1), 0.45, h), (0, YF - d + 0.225, h / 2), 'granite_d' if i % 2 else 'granite'))
    # butalar (kirish yonlarida, devor bo'ylab) va axlat qutisi
    for s in (-1, 1):
        for j in range(3 if main else 2):
            x = s * (EW / 2 + 1.6 + j * 1.5)
            p.append(k.ball(0.95 - j * 0.12, (x, YF - 0.9, 0.85 - j * 0.08), 'leaf', sub=1, scale=(1, 0.8, 1.15)))
    p.append(k.box((1.1, 0.6, 1.0), (EW / 2 - 0.9, YF - LAND + 0.35, PL + 0.5), 'bin'))


# building-136 (katta blok): 62.85 × 14.5 m; building-137 (2-blok): 19.25 × 10.3 m
build('blok1', 62.85, 14.5, main=True)
build('blok2', 19.25, 10.3, main=False)

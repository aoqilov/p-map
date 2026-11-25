"""
Arkali yo'lak — metall arkalar tunneli, sariq chiroqchalar bilan zich o'ralgan (rasm: foydalanuvchi fotosuratlari, park
ichidagi "soat" arkali yo'lak). Ikki uchida katta kirish arkasi: kumush quvur, ustida soat raqamlari (VIII…IV, tepada
XII — havorang, qolganlari tilla) va gajak bezaklar. Orasida har ~1.3 m da yarim aylana arka (oyoqlari past), ular
uzunasiga quvurlar bilan bog'langan; har bir arka va uzunasiga quvurlar bo'ylab zich sariq chiroqchalar (archa
chiroqlari kabi, kechasi yonadi).

Ishga tushirish (loyiha ildizidan):
    blender -b --factory-startup -P src/decor/arkali-yolak/model.py [-- <preview_papka>]
Natija shu papkada: chap.glb/.blend (Водные гусеницы yonidagi, 18 × 5.3 m), ong.glb/.blend (Windstarz oldidagi,
22 × 4.8 m), preview_chap.png, preview_ong.png

Tunnel bo'yi — Blender'da Y o'qi bo'ylab, kirish (oldi) — -Y. Oyoqlari yo'l plitkasi ustida (z = 0.12).
"""
import math
import sys
from pathlib import Path

import bmesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from blender_kit import Kit  # noqa: E402

PALETTE = {
    'metal': (0.78, 0.8, 0.82), 'metal_d': (0.55, 0.57, 0.6), 'gold': (0.95, 0.62, 0.08), 'teal': (0.05, 0.55, 0.6),
    'ink': (0.02, 0.02, 0.02), 'bulb': (1.0, 0.72, 0.18), 'base': (0.35, 0.36, 0.38),
}
G = 0.12                    # yo'l plitkasi yuzasi
LEG = 0.55                  # arka oyog'i (tik qismi) balandligi
STEP = 1.3                  # arkalar oralig'i, m
BULB = 0.3                  # chiroqchalar oralig'i, m
NUMS = ['VIII', 'IX', 'X', 'XI', 'XII', 'I', 'II', 'III', 'IV']


def build(name, L, W):
    k = Kit(PALETTE, glow=('bulb',))
    p = []
    R = W / 2

    def bulb(x, y, z, r=0.065):
        """Kichik chiroqcha (oktaedr — 8 uchburchak, telefon uchun yengil)"""
        bm = bmesh.new()
        vs = [bm.verts.new(v) for v in ((x + r, y, z), (x - r, y, z), (x, y + r, z), (x, y - r, z), (x, y, z + r), (x, y, z - r))]
        for a, b in ((0, 2), (2, 1), (1, 3), (3, 0)):
            bm.faces.new([vs[a], vs[b], vs[4]])
            bm.faces.new([vs[b], vs[a], vs[5]])
        p.append(k.obj('bulb', bm, 'bulb'))

    def arc_pts(r, n, z0):
        """Yarim aylana (XZ tekislik): oyoq tepasidan boshlab, chapdan o'ngga"""
        return [(-r * math.cos(math.pi * i / n), z0 + r * math.sin(math.pi * i / n)) for i in range(n + 1)]

    def hoop(y, r, tube, mat, lights=True, z_leg=LEG):
        """Bitta arka: ikki tik oyoq + yarim aylana, chiroqchalar bilan"""
        z0 = G + z_leg
        for s in (-1, 1):
            p.append(k.cyl(tube, z_leg, (s * r, y, G + z_leg / 2), mat, segs=6))
            p.append(k.box((0.16, 0.16, 0.04), (s * r, y, G + 0.02), 'base'))
        pts = arc_pts(r, 12, z0)
        for a, b in zip(pts, pts[1:]):
            p.append(k.beam((a[0], y, a[1]), (b[0], y, b[1]), tube * 2, tube * 2, mat))
        if lights:
            arc_len = math.pi * r
            n = max(4, int(arc_len / BULB))
            for i in range(n + 1):
                a = math.pi * i / n
                bulb(-r * math.cos(a), y, z0 + r * math.sin(a))
            for s in (-1, 1):
                for j in range(1, int(z_leg / BULB) + 1):
                    bulb(s * r, y, G + j * BULB)

    # ---------- tunnel arkalari ----------
    n_hoops = max(2, round((L - 1.6) / STEP))
    y0, y1 = -L / 2 + 0.8, L / 2 - 0.8
    ys = [y0 + (y1 - y0) * i / n_hoops for i in range(n_hoops + 1)]
    for y in ys:
        hoop(y, R, 0.025, 'metal')
    # uzunasiga quvurlar (tepada, ikki yonda yuqorida va pastda) va ular bo'ylab chiroqchalar
    for ang in (90, 50, 130, 15, 165):
        a = math.radians(ang)
        x, z = -R * math.cos(a), G + LEG + R * math.sin(a)
        p.append(k.beam((x, y0, z), (x, y1, z), 0.035, 0.035, 'metal_d'))
        for j in range(int((y1 - y0) / 0.4) + 1):
            bulb(x, y0 + j * 0.4 + 0.2, z - 0.06)
    for s in (-1, 1):                                                   # pastki panjara chizig'i
        p.append(k.beam((s * R, y0, G + 0.45), (s * R, y1, G + 0.45), 0.03, 0.03, 'metal_d'))

    # ---------- ikki uchidagi katta "soat" kirish arkalari ----------
    for end in (-1, 1):
        y = end * (L / 2 - 0.15)
        RO = R + 0.35
        hoop(y, RO, 0.05, 'metal', lights=True, z_leg=LEG + 0.2)
        hoop(y + end * 0.12, RO - 0.12, 0.03, 'metal', lights=False, z_leg=LEG + 0.2)
        z0 = G + LEG + 0.2
        face = end * 0.09                                               # lavhalar tashqariga qaragan
        for i, num in enumerate(NUMS):
            a = math.pi * (0.06 + 0.88 * i / (len(NUMS) - 1))
            x, z = -(RO + 0.05) * math.cos(a), z0 + (RO + 0.05) * math.sin(a)
            col = 'teal' if num == 'XII' else 'gold'
            ob = k.cyl(0.24, 0.05, (0, 0, 0), col, segs=8, rot=(math.pi / 2, 0, 0))
            ob.location = (x, y + face, z)
            p.append(ob)
            p.append(k.text(num, 0.17 if len(num) < 4 else 0.13, (x, y + face * 1.45, z), 'ink',
                            face='-Y' if end < 0 else '+Y', depth=0.02))
        # tepasidagi gajak bezaklar (egilgan quvurlar)
        for s in (-1, 1):
            pts = [(s * 0.4, z0 + RO + 0.15), (s * 1.0, z0 + RO + 0.55), (s * 1.6, z0 + RO + 0.35), (s * 1.35, z0 + RO + 0.1),
                   (s * 1.05, z0 + RO + 0.25)]
            for a, b in zip(pts, pts[1:]):
                p.append(k.beam((a[0], y, a[1]), (b[0], y, b[1]), 0.04, 0.04, 'metal'))
            p.append(k.beam((s * 0.15, y, z0 + RO + 0.05), (s * 0.4, y, z0 + RO + 0.15), 0.04, 0.04, 'metal'))
            for a, b in zip(pts, pts[1:]):
                for t in (0.33, 0.66):
                    bulb(a[0] + (b[0] - a[0]) * t, y, a[1] + (b[1] - a[1]) * t)

    k.finish(f'ARKALI-YOLAK-{name.upper()}', p, HERE, [
        (f'preview_{name}.png', (W * 0.9, -L / 2 - 6.5, 3.2), (0, -L / 2 + 3, 1.8)),
    ], name=name)


build('chap', 18.0, 5.3)
build('ong', 22.0, 4.8)

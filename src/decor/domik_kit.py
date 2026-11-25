"""
Ertak uychalari (domik-pitsa, domik-burger, domik-kafe) uchun umumiy Blender bo'laklari: g'ishtli devor, ravoqli deraza va
eshik, qiya tom, minoracha, dumaloq lavha, devor chirog'i. Rasm: foydalanuvchi fotosuratlari (park ichidagi do'kon-uychalar).

    from domik_kit import DomikKit, PALETTE
    d = DomikKit(Kit(PALETTE))

O'qlar: old tomon — -Y, tepa — +Z, metr. Devorlar old yuzasi y = -D/2.
"""
import math

PALETTE = {
    'brick': (0.42, 0.13, 0.05), 'brick_d': (0.2, 0.04, 0.04), 'brick_y': (0.85, 0.55, 0.16), 'plaster': (0.85, 0.78, 0.62),
    'white': (0.9, 0.9, 0.88), 'orange': (0.85, 0.3, 0.05), 'roof': (0.2, 0.07, 0.03), 'roof_d': (0.12, 0.04, 0.02),
    'door': (0.25, 0.08, 0.03), 'glass': (0.06, 0.07, 0.08), 'poster': (0.8, 0.06, 0.03), 'poster_y': (0.95, 0.6, 0.05),
    'sign_r': (0.75, 0.03, 0.03), 'sign_p': (0.75, 0.1, 0.45), 'sign_w': (0.95, 0.95, 0.95), 'iron': (0.04, 0.04, 0.04),
    'lamp': (1.0, 0.85, 0.55), 'stripe': (0.08, 0.08, 0.08), 'plant': (0.12, 0.4, 0.08), 'wood': (0.45, 0.2, 0.06),
}
GLOW = ('lamp',)


class DomikKit:
    def __init__(self, k):
        self.k = k
        self.p = []

    def add(self, *objs):
        self.p.extend(objs)

    # ---------- devorlar ----------
    def block(self, w, d, h, cx=0.0, cy=0.0, z0=0.0, mat='brick', sokol=0.45):
        """To'rtburchak bino qismi: g'isht sokol (to'q) + devor"""
        k = self.k
        self.add(k.box((w + 0.06, d + 0.06, sokol), (cx, cy, z0 + sokol / 2), 'brick_d'),
                 k.box((w, d, h - sokol), (cx, cy, z0 + sokol + (h - sokol) / 2), mat))

    def band(self, x0, x1, z, y, h=0.12, mat='white', depth=0.06):
        """Old yuzadagi gorizontal oq hoshiya (karniz chizig'i)"""
        self.add(self.k.box((x1 - x0, depth, h), ((x0 + x1) / 2, y - depth / 2 + 0.01, z), mat))

    def pilaster(self, x, z0, z1, y, w=0.16, mat='white', depth=0.06):
        self.add(self.k.box((w, depth, z1 - z0), (x, y - depth / 2 + 0.01, (z0 + z1) / 2), mat))

    def panel(self, x, z0, w, h, y, mat='orange'):
        """Devordagi rangli tekis panel (fasad bezagi)"""
        self.add(self.k.box((w, 0.03, h), (x, y - 0.01, z0 + h / 2), mat))

    # ---------- ravoqli deraza / eshik ----------
    @staticmethod
    def arch_pts(x, z0, w, h, n=8):
        r = w / 2
        zs = z0 + h - r
        pts = [(x - r, z0), (x + r, z0)]
        for i in range(n + 1):
            a = math.pi * i / n
            pts.append((x + r * math.cos(a), zs + r * math.sin(a)))
        return pts

    def arch(self, x, z0, w, h, y, fill='glass', frame='white', frame_w=0.1, mullion=True):
        """Ravoqli teshik: oq hoshiya, ichi (oyna, plakat yoki eshik), o'rtada tik/yotiq romlar"""
        k = self.k
        self.add(k.prism_y(self.arch_pts(x, z0 - frame_w, w + 2 * frame_w, h + 2 * frame_w), y - 0.04, y + 0.02, frame))
        self.add(k.prism_y(self.arch_pts(x, z0, w, h), y - 0.06, y - 0.03, fill))
        if mullion:
            self.add(k.box((0.04, 0.03, h - w / 2), (x, y - 0.075, z0 + (h - w / 2) / 2), 'door' if fill != 'door' else 'glass'),
                     k.box((w, 0.03, 0.04), (x, y - 0.075, z0 + h - w / 2), 'door' if fill != 'door' else 'glass'))

    def window_rect(self, x, z0, w, h, y, fill='glass'):
        k = self.k
        self.add(k.box((w + 0.16, 0.05, h + 0.16), (x, y - 0.02, z0 + h / 2), 'white'),
                 k.box((w, 0.04, h), (x, y - 0.05, z0 + h / 2), fill))

    # ---------- tomlar ----------
    def gable_roof(self, w, d, z0, rise, cy=0.0, ridge_along='y', over=0.25, gable_mat='brick'):
        """Ikki nishabli tom. ridge_along='y' — tizma oldidan orqaga (old tomonda uchburchak fronton)"""
        k = self.k
        if ridge_along == 'y':
            # ikki qiya plita (ichi bo'sh — old tomondagi fronton ko'rinib turadi)
            ang = math.atan2(rise, w / 2)
            L = math.hypot(w / 2, rise) + over
            for s in (-1, 1):
                cx = s * (math.cos(ang) * L / 2 - 0.02)
                cz = z0 + rise - math.sin(ang) * L / 2 + 0.07
                self.add(k.box((L, d + 2 * over, 0.12), (cx, cy, cz), 'roof', rot=(0, s * ang, 0)))
            self.add(k.box((0.14, d + 2 * over + 0.02, 0.1), (0, cy, z0 + rise + 0.1), 'roof_d'))   # tizma
            tri = [(-w / 2, z0), (w / 2, z0), (0, z0 + rise)]
            self.add(k.prism_y(tri, cy - d / 2 + 0.01, cy + d / 2 - 0.01, gable_mat))
            # oq fronton hoshiyasi (old)
            for s in (-1, 1):
                self.add(k.beam((s * (w / 2 + 0.05), cy - d / 2 - 0.08, z0 - 0.02), (0, cy - d / 2 - 0.08, z0 + rise), 0.12, 0.08, 'white'))
        else:
            hd = d / 2 + over
            prof = [(cy - hd, z0 - 0.05), (cy + hd, z0 - 0.05), (cy, z0 + rise + 0.08)]
            self.add(k.prism_x(prof, -w / 2 - over, w / 2 + over, 'roof'))
            tri = [(cy - d / 2, z0), (cy + d / 2, z0), (cy, z0 + rise)]
            self.add(k.prism_x(tri, -w / 2 + 0.01, w / 2 - 0.01, gable_mat))

    def flat_roof(self, w, d, z, cy=0.0, over=0.3):
        k = self.k
        self.add(k.box((w + 2 * over, d + 2 * over, 0.14), (0, cy, z + 0.07), 'roof'),
                 k.box((w + 2 * over + 0.06, d + 2 * over + 0.06, 0.06), (0, cy, z + 0.03), 'white'))
        # past qiya tom (jigarrang)
        self.add(k.cyl((min(w, d) / 2 + over) * 1.41, 0.6, (0, cy, z + 0.44), 'roof', segs=4, rot=(0, 0, math.pi / 4), r2=0.2))

    # ---------- minoracha ----------
    def tower(self, x, y, r, h, cap=True):
        """Oq-to'q sariq silindr minora, tepasida ustunchali ayvoncha va konus tom"""
        k = self.k
        self.add(k.cyl(r + 0.04, 0.45, (x, y, 0.225), 'brick_d', segs=16))
        self.add(k.cyl(r, h * 0.55, (x, y, h * 0.275), 'plaster', segs=16))
        self.add(k.cyl(r + 0.03, 0.1, (x, y, h * 0.55), 'white', segs=16))
        self.add(k.cyl(r, h * 0.18, (x, y, h * 0.64), 'orange', segs=16))
        self.add(k.cyl(r + 0.06, 0.1, (x, y, h * 0.74), 'white', segs=16))
        self.add(k.cyl(r * 0.8, h * 0.2, (x, y, h * 0.84), 'plaster', segs=16))
        if cap:
            for i in range(6):                                      # ayvoncha ustunchalari
                a = 2 * math.pi * i / 6
                self.add(k.cyl(0.05, 0.6, (x + (r + 0.02) * math.cos(a), y + (r + 0.02) * math.sin(a), h + 0.3), 'white', segs=6))
            self.add(k.cyl(r + 0.1, 0.08, (x, y, h + 0.62), 'white', segs=16))
            self.add(k.cyl(r + 0.25, 0.9, (x, y, h + 1.1), 'roof', segs=8, r2=0.02))

    # ---------- lavha, chiroq, gulzor ----------
    def round_sign(self, x, z, y, r=0.38, mat='sign_r', inner='sign_w'):
        """Devordan chiqib turgan dumaloq lavha (ikki tomonli), qora temir kronshteyn bilan"""
        k = self.k
        out = 0.55
        self.add(k.beam((x, y, z + r + 0.08), (x, y - out - r, z + r + 0.08), 0.04, 0.04, 'iron'),
                 k.cyl(r, 0.08, (x, y - out, z), mat, segs=20, rot=(0, math.pi / 2, 0)),
                 k.cyl(r * 0.55, 0.1, (x, y - out, z), inner, segs=16, rot=(0, math.pi / 2, 0)))

    def wall_lamp(self, x, z, y):
        k = self.k
        self.add(k.box((0.05, 0.2, 0.05), (x, y - 0.1, z + 0.15), 'iron'),
                 k.box((0.14, 0.14, 0.22), (x, y - 0.22, z), 'lamp'),
                 k.cyl(0.11, 0.08, (x, y - 0.22, z + 0.15), 'iron', segs=4, rot=(0, 0, math.pi / 4), r2=0.02))

    def planter(self, x, y, w, d):
        """Oq-qora yo'l-yo'l gulzor (oldida), ustida yashil butalar"""
        k = self.k
        self.add(k.box((w, d, 0.42), (x, y, 0.21), 'white'))
        n = max(2, int(w / 0.25))
        for i in range(n):
            if i % 2 == 0:
                self.add(k.box((w / n, d + 0.02, 0.4), (x - w / 2 + (i + 0.5) * w / n, y, 0.2), 'stripe'))
        self.add(k.box((w - 0.06, d - 0.06, 0.06), (x, y, 0.45), 'wood'))
        for i in range(max(2, int(w / 0.5))):
            self.add(k.ball(0.2, (x - w / 2 + 0.3 + i * (w - 0.6) / max(1, int(w / 0.5) - 1), y, 0.55), 'plant', sub=1))

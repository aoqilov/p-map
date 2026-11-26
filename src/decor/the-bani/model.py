"""
"The Бани Тельмана" (Городские общественные бани; planda Bani → park.json dagi building-127) — foydalanuvchi fotosuratlari bo'yicha.
Izi — plandagi bino aynan o'zi (src/map/park.json dan o'qiladi): config bearing 180 → Blender X = sharq, Y = shimol,
origin — iz markazi. Basseynlar — shimolda; fotolar basseyn tomondan (janubga qarab) olingan: o'ngda — g'arb.

Tuzilish:
  - g'arbiy dumaloq burchak — qizil g'isht (3 qavat), chetlarida to'q kulrang g'isht hoshiya, "БАНИ / ТЕЛЬМАНА" lavhasi,
    pastda egri shisha kirish va yelpig'ichsimon granit zinapoya
  - g'arbiy qism (burchakdan sharqqa ~14 m gacha): oq 3 qavat (10.5 m) — tor oyna ustunlari, kulrang tosh-g'isht
    chiziqlar, jigarrang tik panellar; g'arbiy yon devorda tik "БАНИ" lavhasi va 2-kirish — bir qavatli shisha portal
    ("ГОРОДСКИЕ ОБЩЕСТВЕННЫЕ БАНИ" lavhasi, rang-barang g'isht tasma)
  - ustida to'q ko'k-qora kvadrat panelli 4-qavat (14 m, burchakni ham aylanadi) va 5-qavatgacha to'q minora (17.5 m)
  - past qanot (sharqqa, 2 qavat, 8.9 m): basseyn tomonda S-shakl egri lodjiyalar — oq qalin bandlar, kulrang g'isht
    orqa devor va ustunlar, balkonda gul qutilari; orqasida ichkariga surilgan to'q qavat va kichik to'q hajm;
    sharqiy uchida oq tik qovurg'alar

Ishga tushirish (loyiha ildizidan, park.json yig'ilgandan keyin):
    blender -b --factory-startup -P src/decor/the-bani/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png, preview_corner.png, preview_loggia.png, preview_west.png
"""
import json
import math
import sys
from pathlib import Path

import bmesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from blender_kit import Kit  # noqa: E402

PLAN_ID = 'building-127'

PALETTE = {
    'wall': (0.91, 0.9, 0.86), 'wall_l': (0.96, 0.95, 0.93), 'granite': (0.5, 0.51, 0.52), 'granite_d': (0.4, 0.41, 0.42),
    'glass': (0.17, 0.25, 0.3), 'frame': (0.14, 0.15, 0.17), 'frame_w': (0.92, 0.92, 0.9),
    'stone': (0.5, 0.48, 0.45), 'stone_d': (0.38, 0.37, 0.36), 'dark': (0.1, 0.12, 0.17), 'dark_l': (0.2, 0.23, 0.3),
    'brick': (0.5, 0.17, 0.13), 'brick_l': (0.6, 0.27, 0.2), 'brick_d': (0.25, 0.25, 0.27), 'wood': (0.48, 0.3, 0.17),
    'roof': (0.46, 0.46, 0.47), 'navy': (0.1, 0.16, 0.3), 'sign_w': (0.97, 0.97, 0.97), 'leaf': (0.22, 0.45, 0.2), 'pot': (0.62, 0.36, 0.2),
}
k = Kit(PALETTE)
_glass = k.mats['glass'].node_tree.nodes['Principled BSDF']
_glass.inputs['Roughness'].default_value = 0.12
_glass.inputs['Metallic'].default_value = 0.3
_sw = k.mats['sign_w'].node_tree.nodes['Principled BSDF']   # kechasi yozuvlar yonib turadi
_sw.inputs['Emission Color'].default_value = (*PALETTE['sign_w'], 1)
_sw.inputs['Emission Strength'].default_value = 1.0
p = []

PL = 0.5                    # granit sokol
FL_T = (0.0, 3.5, 7.0)      # baland qism qavatlari
WH = 10.5                   # baland oq qism tepasi
FL_L = (0.0, 4.4)           # past qanot qavatlari
LH = 8.9                    # past qanot tepasi
DH = 14.0                   # to'q 4-qavat tepasi
TT = 17.5                   # to'q minora tepasi
LD = 2.6                    # lodjiya chuqurligi
WHITE_LEN = 14.0            # g'isht burchakdan sharqqa baland oq fasad uzunligi

# ---------- iz: park.json → markazga nisbatan, CCW ----------
park = json.loads((HERE.parent.parent / 'map' / 'park.json').read_text(encoding='utf-8'))
ring = next(b for b in park['buildings'] if b['id'] == PLAN_ID)['poly'][0]
if ring[0] == ring[-1]:
    ring = ring[:-1]


def area2(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))


def centroid(pts):
    a = cx = cy = 0.0
    for i in range(len(pts)):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
        f = x0 * y1 - x1 * y0
        a += f
        cx += (x0 + x1) * f
        cy += (y0 + y1) * f
    return cx / (3 * a), cy / (3 * a)


CX, CY = centroid(ring)
print(f'BANI centroid at=[{CX:.2f}, {CY:.2f}]')
P = [(x - CX, y - CY) for x, y in ring]
if area2(P) < 0:
    P.reverse()
N = len(P)


def seg_of(pts, t):
    """a, b, uzunlik, yo'nalish, tashqi normal (CCW ko'pburchak)"""
    (x0, y0), (x1, y1) = pts[t], pts[(t + 1) % len(pts)]
    L = math.hypot(x1 - x0, y1 - y0) or 1e-9
    return (x0, y0), (x1, y1), L, ((x1 - x0) / L, (y1 - y0) / L), ((y1 - y0) / L, -(x1 - x0) / L)


def seg(t):
    return seg_of(P, t)


# dumaloq burchaklar: ketma-ket ≥4 ta qisqa qirra
short = [seg(i)[2] < 1.7 for i in range(N)]
runs, i = [], 0
while i < N:
    if short[i]:
        j = i
        while j < N and short[j]:
            j += 1
        if j - i >= 4:
            runs.append(list(range(i, j)))
        i = j
    else:
        i += 1
arc_of = {t: r for r in runs for t in r}

# bino o'qi: eng uzun qirra bo'ylab, g'arbdan sharqqa; NX — shimol (basseyn) tomon
longest = max(range(N), key=lambda t: seg(t)[2])
AX = seg(longest)[3]
if AX[0] < 0:
    AX = (-AX[0], -AX[1])
NX = (-AX[1], AX[0])
rot_ax = math.atan2(AX[1], AX[0])


def u_of(q):
    return q[0] * AX[0] + q[1] * AX[1]


def v_of(q):
    return q[0] * NX[0] + q[1] * NX[1]


def lerp(a, b, f):
    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)


def along(a, b, dist):
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    return lerp(a, b, dist / L)


ARC1 = min(runs, key=lambda r: sum(u_of(P[t]) for t in r) / len(r))    # g'arbiy — g'isht burchak
ARC2 = max(runs, key=lambda r: sum(u_of(P[t]) for t in r) / len(r))    # sharqiy qanot burchagi (lodjiyalar aylanadi)
north = [t for t in range(N) if t not in arc_of and seg(t)[2] > 10 and seg(t)[4][0] * NX[0] + seg(t)[4][1] * NX[1] > 0.7]
CD = min(north, key=lambda t: u_of(seg(t)[0]) + u_of(seg(t)[1]))    # g'arbiy qism shimoliy fasadi (CCW: D → C)
FG = max(north, key=lambda t: u_of(seg(t)[0]) + u_of(seg(t)[1]))    # sharqiy qanot shimoliy fasadi (G → F)
D, C = P[CD], P[(CD + 1) % N]
G, F = P[FG], P[(FG + 1) % N]
S = along(C, D, WHITE_LEN)           # baland oq fasad shu yerda tugaydi, lodjiyalar boshlanadi
G2 = along(G, F, 2.0)                # lodjiyalar sharqiy uchidan 2 m oldin tugaydi
uS = u_of(S)


# ---------- geometriya yordamchilari ----------
def offset(pts, d):
    """Yopiq ko'pburchakni tashqariga d ga surish (miter, cheklangan)"""
    out, n = [], len(pts)
    for t in range(n):
        (ax, ay), (bx, by), (cx, cy) = pts[t - 1], pts[t], pts[(t + 1) % n]
        def nrm(px, py, qx, qy):
            L = math.hypot(qx - px, qy - py) or 1
            return ((qy - py) / L, -(qx - px) / L)
        n1, n2 = nrm(ax, ay, bx, by), nrm(bx, by, cx, cy)
        m = max(1 + n1[0] * n2[0] + n1[1] * n2[1], 0.25)
        out.append((bx + (n1[0] + n2[0]) / m * d, by + (n1[1] + n2[1]) / m * d))
    return out


def offset_line(pts, d):
    """Ochiq chiziqni o'ng tomonga (CCW izda — tashqariga) d ga surish; manfiy d — ichkariga"""
    out, n = [], len(pts)
    for t in range(n):
        ns = []
        pairs = ([(pts[t - 1], pts[t])] if t > 0 else []) + ([(pts[t], pts[t + 1])] if t < n - 1 else [])
        for a, b in pairs:
            L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
            ns.append(((b[1] - a[1]) / L, -(b[0] - a[0]) / L))
        nx, ny = sum(q[0] for q in ns), sum(q[1] for q in ns)
        m = max((nx * nx + ny * ny) / len(ns) ** 2, 0.3) * len(ns)
        out.append((pts[t][0] + nx / m * d, pts[t][1] + ny / m * d))
    return out


def chaikin(pts, it):
    for _ in range(it):
        q = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            q += [lerp(a, b, 0.25), lerp(a, b, 0.75)]
        q.append(pts[-1])
        pts = q
    return pts


def resample(pts, step):
    L = [0.0]
    for a, b in zip(pts, pts[1:]):
        L.append(L[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    n = max(2, round(L[-1] / step))
    out, j = [], 0
    for i in range(n + 1):
        s = L[-1] * i / n
        while j < len(L) - 2 and L[j + 1] < s:
            j += 1
        f = (s - L[j]) / ((L[j + 1] - L[j]) or 1)
        out.append(lerp(pts[j], pts[j + 1], min(1, max(0, f))))
    return out


def clip_hp(pts, fn):
    """Ko'pburchakning fn(q) >= 0 qismi (Sutherland–Hodgman)"""
    res, n = [], len(pts)
    for t in range(n):
        a, b = pts[t], pts[(t + 1) % n]
        fa, fb = fn(a), fn(b)
        if fa >= 0:
            res.append(a)
        if (fa >= 0) != (fb >= 0):
            res.append(lerp(a, b, fa / (fa - fb)))
    return res


def prism(pts, z0, z1, mat):
    bm = bmesh.new()
    lo = [bm.verts.new((x, y, z0)) for x, y in pts]
    hi = [bm.verts.new((x, y, z1)) for x, y in pts]
    bm.faces.new(lo[::-1])
    bm.faces.new(hi)
    n = len(pts)
    for t in range(n):
        bm.faces.new([lo[t], lo[(t + 1) % n], hi[(t + 1) % n], hi[t]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return k.obj('prism', bm, mat)


def strip(line_a, line_b, z0, z1, mat):
    """Ikki chiziq orasidagi egri plita (balkon, zinapoya): har bo'lagi alohida to'rtburchak — botiq ko'pburchak
    uchburchaklashda buzilmasin"""
    bm = bmesh.new()
    lo_a = [bm.verts.new((x, y, z0)) for x, y in line_a]
    hi_a = [bm.verts.new((x, y, z1)) for x, y in line_a]
    lo_b = [bm.verts.new((x, y, z0)) for x, y in line_b]
    hi_b = [bm.verts.new((x, y, z1)) for x, y in line_b]
    n = len(line_a)
    for i in range(n - 1):
        bm.faces.new([hi_a[i], hi_a[i + 1], hi_b[i + 1], hi_b[i]])
        bm.faces.new([lo_a[i], lo_b[i], lo_b[i + 1], lo_a[i + 1]])
        bm.faces.new([lo_a[i], lo_a[i + 1], hi_a[i + 1], hi_a[i]])
        bm.faces.new([lo_b[i], hi_b[i], hi_b[i + 1], lo_b[i + 1]])
    for i in (0, n - 1):
        bm.faces.new([lo_a[i], hi_a[i], hi_b[i], lo_b[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return k.obj('strip', bm, mat)


def ebox(a, d, nrm, u, off, z0, z1, alongw, thick, mat):
    """Qirra bo'ylab quti: a — qirra boshi, u — undan masofa, off — devordan tashqariga (markaz)"""
    x = a[0] + d[0] * u + nrm[0] * off
    y = a[1] + d[1] * u + nrm[1] * off
    return k.box((alongw, thick, z1 - z0), (x, y, (z0 + z1) / 2), mat, rot=(0, 0, math.atan2(d[1], d[0])))


def facing_text(s, size, a, d, nrm, u, off, z, mat, depth=0.04):
    ob = k.text(s, size, (0, 0, 0), mat, depth=depth)
    ob.rotation_euler = (math.pi / 2, 0, math.atan2(nrm[0], -nrm[1]))
    ob.location = (a[0] + d[0] * u + nrm[0] * off, a[1] + d[1] * u + nrm[1] * off, z)
    return ob


def window(a, d, nrm, u, w, z0, z1, frame='frame', mull=True):
    r = [ebox(a, d, nrm, u, 0.03, z0, z1, w, 0.05, 'glass'),
         ebox(a, d, nrm, u, 0.07, z0 - 0.07, z0, w + 0.16, 0.14, frame),
         ebox(a, d, nrm, u, 0.05, z1, z1 + 0.06, w + 0.1, 0.08, frame)]
    for s in (-1, 1):
        r.append(ebox(a, d, nrm, u + s * w / 2, 0.05, z0, z1, 0.06, 0.08, frame))
    if mull and w > 1.4:
        r.append(ebox(a, d, nrm, u, 0.05, z0, z1, 0.05, 0.07, frame))
    return r


# ---------- lodjiyalar chizig'i: G2 → F → sharqiy burchak → E → D → S (silliqlangan S-egri) ----------
path = [G2]
t = (FG + 1) % N
while True:
    path.append(P[t])
    if t == CD:
        break
    t = (t + 1) % N
path.append(S)
FRONT = resample(chaikin(path, 3), 1.5)          # balkonlar old cheti
BACK = offset_line(FRONT, -LD)                   # lodjiya orqa devori

# bino devori izi: C ... G (g'arbiy burchak, g'arbiy va janubiy, sharqiy tomonlar) + G2 + orqa devor + S
P2 = []
t = (CD + 1) % N
while True:
    P2.append(P[t])
    if t == FG:
        break
    t = (t + 1) % N
P2 += [G2] + BACK + [S]
if area2(P2) < 0:
    raise SystemExit('P2 yo\'nalishi buzildi')
TALL = clip_hp(P2, lambda q: uS - u_of(q))
LOW = clip_hp(P2, lambda q: u_of(q) - uS)

# ---------- korpus, tomlar ----------
p.append(prism(offset(P2, 0.08), 0, PL, 'granite'))
p.append(prism(TALL, PL, WH, 'wall'))
p.append(prism(LOW, PL, LH, 'wall'))
p.append(prism(LOW, LH - 0.01, LH + 0.04, 'roof'))   # offset botiq izda o'zini kesadi — iz o'zi
DARK_W = offset(TALL, 0.06)
p.append(prism(DARK_W, WH, DH, 'dark'))
p.append(prism(offset(TALL, -0.45), DH, DH + 0.06, 'roof'))
vC = v_of(C)
uG = u_of(G)
DARK_E = clip_hp(clip_hp(LOW, lambda q: (uG - 8) - u_of(q)), lambda q: (vC - LD - 1.2) - v_of(q))
p.append(prism(DARK_E, LH, 13.0, 'dark'))
p.append(prism(offset(DARK_E, -0.4), 13.0, 13.06, 'roof'))


def is_cut(pts, t, u0):
    a, b, *_ = seg_of(pts, t)
    return abs(u_of(a) - u0) < 0.05 and abs(u_of(b) - u0) < 0.05


# to'q qismlar: parapet, kvadrat panel choklari, tasma oynalar
for poly, z0, z1 in ((DARK_W, WH, DH), (DARK_E, LH, 13.0)):
    for t in range(len(poly)):
        a, b, L, d, nrm = seg_of(poly, t)
        if L < 0.05:
            continue
        p.append(ebox(a, d, nrm, L / 2, -0.1, z1, z1 + 0.45, L + 0.2, 0.25, 'dark_l'))
        if L < 2.5:
            continue
        nj = int(L / 1.5)
        for j in range(1, nj):
            p.append(ebox(a, d, nrm, j * L / nj, 0.02, z0, z1, 0.05, 0.03, 'dark_l'))
        for z in (z0 + 1.4, z0 + 2.9):
            if z < z1 - 0.3:
                p.append(ebox(a, d, nrm, L / 2, 0.02, z - 0.03, z + 0.03, L, 0.03, 'dark_l'))
        if L > 5 and not (poly is DARK_W and abs(u_of(a) - uS) < 0.2 and abs(u_of(b) - uS) < 0.2):
            nw = int(L / 4.5)
            for j in range(nw):
                p.append(ebox(a, d, nrm, (j + 0.5) * L / nw, 0.04, z0 + 0.6, z0 + 2.6, 2.2, 0.04, 'glass'))
# oq parapetlar (past qanot tomi; lodjiyalar ustida — oq band, quyida)
for t in range(len(LOW)):
    a, b, L, d, nrm = seg_of(LOW, t)
    if L < 0.05 or is_cut(LOW, t, uS):
        continue
    mid = lerp(a, b, 0.5)
    if any(math.hypot(mid[0] - q[0], mid[1] - q[1]) < 0.9 for q in BACK):
        continue
    p.append(ebox(a, d, nrm, L / 2, -0.12, LH, LH + 0.5, L + 0.25, 0.3, 'wall_l'))


# ---------- to'q minora va kichik hajm ----------
def top_box(u, w, dd, v_front, z0, z1, win_u=None):
    v = v_front - dd / 2
    cx, cy = AX[0] * u + NX[0] * v, AX[1] * u + NX[1] * v
    r = [k.box((w, dd, z1 - z0), (cx, cy, (z0 + z1) / 2), 'dark', rot=(0, 0, rot_ax)),
         k.box((w + 0.2, dd + 0.2, 0.3), (cx, cy, z1 + 0.15), 'dark_l', rot=(0, 0, rot_ax))]
    fy = v_front + 0.02
    nj = int(w / 1.5)
    for j in range(1, nj):
        uu = u - w / 2 + j * w / nj
        r.append(k.box((0.05, 0.03, z1 - z0), (AX[0] * uu + NX[0] * fy, AX[1] * uu + NX[1] * fy, (z0 + z1) / 2), 'dark_l',
                       rot=(0, 0, rot_ax)))
    if win_u is not None:   # old tomonda tik oyna ustuni
        uu = u + win_u
        for zz in ((z0 + 0.5, z0 + 1.6), (z1 - 1.9, z1 - 0.5)):
            r.append(k.box((1.1, 0.05, zz[1] - zz[0]), (AX[0] * uu + NX[0] * (fy + 0.01), AX[1] * uu + NX[1] * (fy + 0.01),
                                                       (zz[0] + zz[1]) / 2), 'glass', rot=(0, 0, rot_ax)))
    return r


uC = u_of(C)
p.extend(top_box(uC + 7.0, 10.0, 9.0, vC - 0.4, DH, TT, win_u=-2.0))     # g'isht burchak yonidagi baland to'q minora
p.extend(top_box(uS + 4.0, 7.0, 5.0, vC - LD - 2.0, 13.0, 15.6))         # lodjiyalar orqasidagi kichik hajm

# ---------- g'isht burchak (ARC1): qizil g'isht, hoshiyalar, lavha, egri shisha kirish, zinapoya ----------
BR_EXT = 2.0     # g'isht qo'shni devorlarga ham o'tadi
CS = seg_of(P2, len(P2) - 1)                     # S → C qirrasi (baland oq fasad)
iB = (ARC1[-1] + 1) % N
B, A_ = P[iB], P[(iB + 1) % N]
BA = (B, A_, math.hypot(A_[0] - B[0], A_[1] - B[1]), None, None)
corner = [along(C, S, BR_EXT), C] + [P[(t + 1) % N] for t in ARC1[:-1]] + [B, along(B, A_, BR_EXT)]
for a0, a1 in zip(corner, corner[1:]):
    L = math.hypot(a1[0] - a0[0], a1[1] - a0[1])
    d = ((a1[0] - a0[0]) / L, (a1[1] - a0[1]) / L)
    nrm = (d[1], -d[0])
    p.append(ebox(a0, d, nrm, L / 2, 0.12, 0, WH, L + 0.12, 0.26, 'brick'))
    for j in range(int(WH / 0.6)):   # g'isht qatorlari (och choklar)
        p.append(ebox(a0, d, nrm, L / 2, 0.255, 0.3 + j * 0.6, 0.32 + j * 0.6, L + 0.1, 0.012, 'brick_l'))
for a0, a1 in ((corner[0], corner[1]), (corner[-1], corner[-2])):   # chetlarida to'q kulrang g'isht hoshiya
    L = math.hypot(a1[0] - a0[0], a1[1] - a0[1])
    d = ((a1[0] - a0[0]) / L, (a1[1] - a0[1]) / L)
    sgn = 1 if a0 is corner[0] else -1
    nrm = (d[1], -d[0]) if sgn > 0 else (-d[1], d[0])
    p.append(ebox(a0, d, nrm, 0.25, 0.16, 0, WH, 0.55, 0.34, 'brick_d'))
# shisha kirish (yoy bo'ylab, pastda) va eshik
arc_pts = [C] + [P[(t + 1) % N] for t in ARC1[:-1]] + [B]
mid_i = len(arc_pts) // 2
for i, (a0, a1) in enumerate(zip(arc_pts, arc_pts[1:])):
    L = math.hypot(a1[0] - a0[0], a1[1] - a0[1])
    d = ((a1[0] - a0[0]) / L, (a1[1] - a0[1]) / L)
    nrm = (d[1], -d[0])
    p.append(ebox(a0, d, nrm, L / 2, 0.27, PL, 4.3, L + 0.05, 0.04, 'glass'))
    p.append(ebox(a0, d, nrm, 0, 0.3, PL, 4.3, 0.08, 0.08, 'frame'))
    for z in (PL, 2.9, 4.3):
        p.append(ebox(a0, d, nrm, L / 2, 0.3, z - 0.05, z + 0.05, L + 0.05, 0.08, 'frame'))
    if i == mid_i - 1:
        p.append(ebox(a0, d, nrm, L / 2, 0.3, PL, 2.85, L * 0.9, 0.03, 'dark_l'))   # ikki tabaqali eshik
        p.append(ebox(a0, d, nrm, L / 2, 0.34, PL + 0.8, PL + 1.9, 0.04, 0.04, 'frame_w'))
a0, a1 = arc_pts[mid_i - 1], arc_pts[mid_i]
L = math.hypot(a1[0] - a0[0], a1[1] - a0[1])
d = ((a1[0] - a0[0]) / L, (a1[1] - a0[1]) / L)
nrm = (d[1], -d[0])
# lavha: qora ramka ichida "БАНИ", pastida oq tasmada "ТЕЛЬМАНА"
p.append(ebox(a0, d, nrm, L / 2, 0.34, 5.5, 7.9, 3.4, 0.14, 'frame'))
p.append(ebox(a0, d, nrm, L / 2, 0.42, 6.15, 7.75, 3.1, 0.04, 'dark'))
p.append(facing_text('БАНИ', 1.05, a0, d, nrm, L / 2, 0.46, 6.95, 'sign_w', depth=0.05))
p.append(ebox(a0, d, nrm, L / 2, 0.42, 5.6, 6.05, 2.4, 0.04, 'sign_w'))
p.append(facing_text('ТЕЛЬМАНА', 0.3, a0, d, nrm, L / 2, 0.46, 5.82, 'frame', depth=0.03))
# yelpig'ichsimon granit zinapoya (burchakni aylanib)
steps_line = [along(C, S, 1.2)] + arc_pts + [along(B, A_, 1.2)]
for j in range(3):
    inner = offset_line(steps_line, 0.3 + 0.55 * j)
    outer = offset_line(steps_line, 0.85 + 0.55 * j)
    p.append(strip(outer, inner, 0, PL * (3 - j) / 3, 'granite_d' if j % 2 else 'granite'))


# ---------- baland oq fasad (S → C): tor oyna ustunlari, tosh chiziqlar, jigarrang panellar ----------
a, b, L, d, nrm = CS                      # a = S, b = C; u — S dan
def from_c(x):
    return L - x


for x in (3.3, 7.4, 11.2):                # oyna ustunlari (3 qavat)
    for z in FL_T:
        p.extend(window(a, d, nrm, from_c(x), 1.3, max(z + 0.7, PL + 0.3), z + 2.9, 'frame_w'))
for x, w in ((4.9, 0.9), (9.0, 1.1), (12.9, 0.9)):   # kulrang tosh-g'isht chiziqlar
    p.append(ebox(a, d, nrm, from_c(x), 0.1, PL, WH, w, 0.2, 'stone'))
    for j in range(int((WH - PL) / 0.6)):
        p.append(ebox(a, d, nrm, from_c(x), 0.205, PL + 0.3 + j * 0.6, PL + 0.32 + j * 0.6, w, 0.01, 'stone_d'))
for x in (5.95, 10.15):                    # jigarrang tik panellar
    p.append(ebox(a, d, nrm, from_c(x), 0.08, 3.9, 9.9, 0.55, 0.12, 'wood'))
    p.append(ebox(a, d, nrm, from_c(x), 0.08, 0.9, 3.0, 0.55, 0.12, 'wood'))

# ---------- g'arbiy yon devor (B → A): tik "БАНИ" lavhasi, oynalar, tosh chiziqlar ----------
a, b, L, d, nrm = B, A_, BA[2], ((A_[0] - B[0]) / BA[2], (A_[1] - B[1]) / BA[2]), None
nrm = (d[1], -d[0])
p.append(ebox(a, d, nrm, 3.2, 0.1, 6.0, 10.2, 1.15, 0.16, 'frame'))
for j, ch in enumerate('БАНИ'):
    p.append(facing_text(ch, 0.72, a, d, nrm, 3.2, 0.2, 9.55 - j * 0.98, 'sign_w', depth=0.04))
PU, PW, PO, PH = 9.6, 5.6, 1.7, 4.2     # 2-kirish portali: markazi (B dan), eni, chiqishi, balandligi
for x in (5.2, 8.2, 11.0):
    if x < L - 0.8:
        for z in FL_T:
            if z == 0 and abs(x - PU) < PW / 2:   # pastki qavat — portal ortida
                continue
            p.extend(window(a, d, nrm, x, 1.3, max(z + 0.7, PL + 0.3), z + 2.9, 'frame_w'))
for x in (6.7, 9.6):
    if x < L - 0.5:
        z0 = PH if abs(x - PU) < PW / 2 else PL
        p.append(ebox(a, d, nrm, x, 0.1, z0, WH, 0.9, 0.2, 'stone'))

# 2-kirish: "ГОРОДСКИЕ ОБЩЕСТВЕННЫЕ БАНИ" — bir qavatli shisha portal (qora ramkali vitraj, o'rtada ikki tabaqali eshik va
# tepasida fortochka, yonlarida granit sokol, ustida rang-barang g'isht tasma va to'q ko'k lavha)
GB = 3.15     # g'isht tasma pastki cheti
p.append(ebox(a, d, nrm, PU, PO / 2, 0, PH, PW, PO, 'wall'))                       # portal korpusi
p.append(ebox(a, d, nrm, PU, PO / 2, GB, PH, PW + 0.2, PO + 0.15, 'brick_l'))     # g'isht tasma
for j in range(4):   # rang-barang g'isht: och/to'q qatorlar
    z = GB + 0.12 + j * 0.24
    p.append(ebox(a, d, nrm, PU, PO + 0.08, z, z + 0.1, PW + 0.2, 0.02, 'pot' if j % 2 else 'stone'))
p.append(ebox(a, d, nrm, PU, PO + 0.12, GB + 0.25, PH - 0.2, PW - 0.5, 0.06, 'navy'))
p.append(facing_text('ГОРОДСКИЕ ОБЩЕСТВЕННЫЕ БАНИ', 0.27, a, d, nrm, PU, PO + 0.17, (GB + PH) / 2 + 0.02, 'sign_w', depth=0.03))
# old tomon vitraj
p.append(ebox(a, d, nrm, PU, PO + 0.01, PL, GB, PW - 0.2, 0.04, 'glass'))
for s in (-1, 1):   # yonlarida granit sokol (pastki 0.9 m)
    p.append(ebox(a, d, nrm, PU + s * (PW / 2 - 0.85), PO + 0.04, 0, 0.9, 1.5, 0.1, 'granite'))
for x in (-PW / 2 + 0.1, -1.0, -0.55, 0.55, 1.0, PW / 2 - 0.1):   # tik ramkalar
    p.append(ebox(a, d, nrm, PU + x, PO + 0.06, PL, GB, 0.08, 0.08, 'frame'))
for z in (PL, 1.75, GB - 0.05):   # gorizontal ramkalar
    p.append(ebox(a, d, nrm, PU, PO + 0.06, z, z + 0.07, PW - 0.2, 0.08, 'frame'))
p.append(ebox(a, d, nrm, PU, PO + 0.06, 2.45, 2.52, 2.0, 0.08, 'frame'))           # eshik ustidagi fortochka
p.append(ebox(a, d, nrm, PU, PO + 0.05, PL, 2.45, 1.95, 0.03, 'dark_l'))           # ikki tabaqali eshik
p.append(ebox(a, d, nrm, PU, PO + 0.08, PL, 2.45, 0.05, 0.05, 'frame'))
for s in (-1, 1):
    p.append(ebox(a, d, nrm, PU + s * 0.12, PO + 0.1, 1.2, 1.5, 0.04, 0.04, 'frame_w'))   # tutqichlar
    p.append(ebox(a, d, nrm, PU + s * (PW / 2 + 0.45), PO + 0.3, 0, 0.75, 0.25, 0.25, 'granite_d'))   # urna
# yon tomonlar: vitraj (portal chuqurligi bo'ylab)
for s in (-1, 1):
    side_a = (a[0] + d[0] * (PU + s * PW / 2), a[1] + d[1] * (PU + s * PW / 2))
    sd = (nrm[0], nrm[1])
    sn = (s * d[0], s * d[1])
    p.append(ebox(side_a, sd, sn, PO / 2, 0.01, PL, GB, PO - 0.3, 0.04, 'glass'))
    p.append(ebox(side_a, sd, sn, PO / 2, 0.04, PL, PL + 0.07, PO - 0.3, 0.06, 'frame'))
# kirish oldidagi granit maydoncha (bir pog'ona)
p.append(ebox(a, d, nrm, PU, PO + 0.6, 0, 0.18, PW + 1.0, 1.2, 'granite'))

# ---------- qolgan tomonlar (janub, sharq): oyna to'ri; sharqiy uchida oq tik qovurg'alar ----------
special = set(ARC1) | set(ARC2) | {CD, FG, iB}
t = (CD + 1) % N
for t in range(N):
    if t in special or t in arc_of:
        continue
    a, b, L, d, nrm = seg(t)
    if L < 2.5:
        continue
    if nrm[0] * NX[0] + nrm[1] * NX[1] > 0.7:    # shimolga qaragan (lodjiyalar zonasi — alohida)
        continue
    east = nrm[0] * AX[0] + nrm[1] * AX[1] > 0.7
    nw = int(L / 3.2)
    if nw < 1:
        continue
    step = L / nw
    for j in range(nw):
        u = (j + 0.5) * step
        q = (a[0] + d[0] * u, a[1] + d[1] * u)
        tall = u_of(q) < uS
        if east and u > L - 6:
            continue
        for z in (FL_T if tall else FL_L):
            zz1 = z + (2.9 if tall else 3.5)
            p.extend(window(a, d, nrm, u, 1.8, max(z + 0.8, PL + 0.3), zz1))
        if j % 3 == 2 and j < nw - 1:
            p.append(ebox(a, d, nrm, (j + 1) * step, 0.1, PL, WH if tall else LH, 0.9, 0.2, 'stone'))
    if east:   # sharqiy uchida (shimol tomonda) oq tik qovurg'alar
        for j in range(6):
            p.append(ebox(a, d, nrm, L - 0.6 - j * 0.9, 0.3, PL, LH - 0.2, 0.18, 0.6, 'wall_l'))

# ---------- egri lodjiyalar (basseyn tomonda) ----------
# orqa devor: kulrang g'isht qoplama, har qavatda oynalar (oq ramka)
for i, (a0, a1) in enumerate(zip(BACK, BACK[1:])):
    L = math.hypot(a1[0] - a0[0], a1[1] - a0[1])
    if L < 0.05:
        continue
    d = ((a1[0] - a0[0]) / L, (a1[1] - a0[1]) / L)
    nrm = (d[1], -d[0])
    p.append(ebox(a0, d, nrm, L / 2, 0.015, PL, LH - 0.4, L + 0.06, 0.03, 'stone'))
    for z in (1.6, 2.8, 6.0, 7.2):
        p.append(ebox(a0, d, nrm, L / 2, 0.033, z, z + 0.02, L + 0.06, 0.01, 'stone_d'))
    if i % 2 == 0:
        for z in FL_L:
            p.extend(window(a0, d, nrm, L / 2, min(1.25, L - 0.1), max(z + 0.6, PL + 0.2), z + 3.4, 'frame_w', mull=False))
# balkon plitasi va tom: oq qalin bandlar (old cheti egri)
INNER = offset_line(BACK, 0.05)
p.append(strip(FRONT, INNER, FL_L[1] - 0.2, FL_L[1] + 0.15, 'wall_l'))
p.append(strip(FRONT, INNER, LH - 0.35, LH + 0.12, 'roof'))   # past qanot tomidan biroz baland (ustma-ust tushmasin)
OUT = offset_line(FRONT, 0.12)
IN_ = offset_line(FRONT, -0.22)
p.append(strip(OUT, IN_, FL_L[1] - 0.45, FL_L[1] + 1.0, 'wall_l'))    # 1-balkon to'sig'i (yaxlit oq)
p.append(strip(OUT, IN_, LH - 0.85, LH + 0.45, 'wall_l'))             # tomdagi oq band
# tosh-g'isht ustunlar (old chiziqda)
for fu in (0.03, 0.3, 0.6, 0.86):
    i = min(len(FRONT) - 2, int(fu * (len(FRONT) - 1)))
    a0, a1 = FRONT[i], FRONT[i + 1]
    L = math.hypot(a1[0] - a0[0], a1[1] - a0[1])
    d = ((a1[0] - a0[0]) / L, (a1[1] - a0[1]) / L)
    nrm = (d[1], -d[0])
    p.append(ebox(a0, d, nrm, 0, -0.55, 0, LH - 0.85, 1.0, 0.95, 'stone'))
    for j in range(int((LH - 0.85) / 0.6)):
        for s in (-1, 1):
            p.append(ebox(a0, d, nrm, s * 0.505, -0.55, 0.3 + j * 0.6, 0.32 + j * 0.6, 0.01, 0.95, 'stone_d'))
# 1-balkondagi gul qutilari (sharqiy qismida)
for fu in (0.08, 0.14, 0.2, 0.26):
    i = int(fu * (len(FRONT) - 1))
    a0, a1 = FRONT[i], FRONT[i + 1]
    L = math.hypot(a1[0] - a0[0], a1[1] - a0[1])
    d = ((a1[0] - a0[0]) / L, (a1[1] - a0[1]) / L)
    nrm = (d[1], -d[0])
    p.append(ebox(a0, d, nrm, L / 2, -0.6, FL_L[1] + 0.15, FL_L[1] + 0.6, L * 0.95, 0.55, 'pot'))
    c = (a0[0] + d[0] * L / 2 - nrm[0] * 0.6, a0[1] + d[1] * L / 2 - nrm[1] * 0.6)
    p.append(k.ball(0.45, (c[0], c[1], FL_L[1] + 0.85), 'leaf', sub=1, scale=(1.6, 0.9, 0.8)))

# ---------- preview ----------
cm = arc_pts[mid_i]
fm = FRONT[len(FRONT) // 2]
wd = ((A_[0] - B[0]) / BA[2], (A_[1] - B[1]) / BA[2])
wn = (wd[1], -wd[0])
pm = (B[0] + wd[0] * PU, B[1] + wd[1] * PU)     # 2-kirish markazi
k.finish('BANI', p, HERE, [
    ('preview.png', (NX[0] * 48 + AX[0] * 12, NX[1] * 48 + AX[1] * 12, 24), (u_of(C) * AX[0] * 0.3, u_of(C) * AX[1] * 0.3, 5)),
    ('preview_corner.png', (cm[0] + NX[0] * 13 - AX[0] * 8, cm[1] + NX[1] * 13 - AX[1] * 8, 5), (cm[0], cm[1], 5)),
    ('preview_loggia.png', (fm[0] + NX[0] * 20 - AX[0] * 4, fm[1] + NX[1] * 20 - AX[1] * 4, 3.5), (fm[0], fm[1], 5)),
    ('preview_west.png', (pm[0] + wn[0] * 11 + wd[0] * 3, pm[1] + wn[1] * 11 + wd[1] * 3, 3.2), (pm[0], pm[1], 3.2)),
])

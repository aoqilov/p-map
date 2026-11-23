"""Gen plan PDF → GeoJSON uchun umumiy yordamchilar (pdf o'qish, koordinata almashtirish)."""
import ctypes, json, math
from collections import defaultdict
from pathlib import Path

import pypdfium2 as pdfium
import pypdfium2.raw as raw
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
from shapely import affinity

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / 'yana-reference' / 'Ген планТэльмана  2025 Цвет.pdf'
GEOREF = ROOT / 'scripts' / 'genplan' / 'georef.json'
OUT_DIR = ROOT / 'data' / 'genplan'

# Projection — src/map/projection.ts bilan bir xil bo'lishi shart
ORIGIN_LON, ORIGIN_LAT = 69.29866, 41.31233
KX = 111_320 * math.cos(math.radians(ORIGIN_LAT))
KY = 110_540


def _rgb(fn, o):
    r, g, b, a = (ctypes.c_uint() for _ in range(4))
    fn(o, r, g, b, a)
    return (r.value, g.value, b.value)


def read_pdf(path=PDF):
    """Sahifadagi to'ldirilgan shakllar (rang → poligonlar), chiziqlar va matnlar (PDF pt koordinatalarida)."""
    page = pdfium.PdfDocument(str(path))[0]
    tp = page.get_textpage()
    fills, strokes, texts = defaultdict(list), defaultdict(list), []
    for obj in page.get_objects(max_depth=5):
        o = obj.raw
        if obj.type == raw.FPDF_PAGEOBJ_TEXT:
            n = raw.FPDFTextObj_GetText(o, tp.raw, None, 0)
            buf = (ctypes.c_ushort * (n + 1))()
            raw.FPDFTextObj_GetText(o, tp.raw, buf, n * 2)
            t = bytes(buf)[: n * 2].decode('utf-16-le', errors='replace').rstrip('\x00').strip()
            l, b, r, tt = (ctypes.c_float() for _ in range(4))
            raw.FPDFPageObj_GetBounds(o, l, b, r, tt)
            texts.append(dict(t=t, x=(l.value + r.value) / 2, y=(b.value + tt.value) / 2,
                              h=tt.value - b.value, c=_rgb(raw.FPDFPageObj_GetFillColor, o)))
            continue
        if obj.type != raw.FPDF_PAGEOBJ_PATH:
            continue
        m = raw.FS_MATRIX(); raw.FPDFPageObj_GetMatrix(o, m)
        fm, st = ctypes.c_int(), ctypes.c_int(); raw.FPDFPath_GetDrawMode(o, fm, st)
        rings, cur = [], []
        for i in range(raw.FPDFPath_CountSegments(o)):
            s = raw.FPDFPath_GetPathSegment(o, i)
            x, y = ctypes.c_float(), ctypes.c_float(); raw.FPDFPathSegment_GetPoint(s, x, y)
            p = (m.a * x.value + m.c * y.value + m.e, m.b * x.value + m.d * y.value + m.f)
            if raw.FPDFPathSegment_GetType(s) == raw.FPDF_SEGMENT_MOVETO and cur:
                rings.append(cur); cur = []
            cur.append(p)
            if raw.FPDFPathSegment_GetClose(s):
                rings.append(cur); cur = []
        if cur:
            rings.append(cur)
        if fm.value:
            c = _rgb(raw.FPDFPageObj_GetFillColor, o)
            for ring in rings:
                if len(ring) >= 3:
                    pl = Polygon(ring).buffer(0)
                    if not pl.is_empty:
                        fills[c].append(pl)
        elif st.value:
            c = _rgb(raw.FPDFPageObj_GetStrokeColor, o)
            w = ctypes.c_float(); raw.FPDFPageObj_GetStrokeWidth(o, w)
            for ring in rings:
                if len(ring) >= 2:
                    strokes[(c, round(w.value, 1))].append(LineString(ring))
    merged = {c: unary_union(p).buffer(0.3).buffer(-0.3) for c, p in fills.items()}
    return merged, dict(strokes), texts, page.get_size()


def load_georef():
    return json.loads(GEOREF.read_text())


def pt_to_m(geom, g):
    """PDF pt → park metrlari (x sharq, y shimol; ORIGIN atrofida)."""
    th, tx, ty, mpp = g['th'], g['tx'], g['ty'], g['mpp']
    c, s = math.cos(-th), math.sin(-th)
    # m = Rot(-th) * (pt - t) * mpp
    return affinity.affine_transform(geom, [c * mpp, -s * mpp, s * mpp, c * mpp,
                                            -(c * tx - s * ty) * mpp, -(s * tx + c * ty) * mpp])


def m_to_pt(geom, g):
    th, tx, ty, mpp = g['th'], g['tx'], g['ty'], g['mpp']
    c, s = math.cos(th), math.sin(th)
    k = 1 / mpp
    return affinity.affine_transform(geom, [c * k, -s * k, s * k, c * k, tx, ty])


def m_to_lonlat(geom):
    return affinity.affine_transform(geom, [1 / KX, 0, 0, 1 / KY, ORIGIN_LON, ORIGIN_LAT])


def lonlat_to_m(geom):
    return affinity.affine_transform(geom, [KX, 0, 0, KY, -ORIGIN_LON * KX, -ORIGIN_LAT * KY])

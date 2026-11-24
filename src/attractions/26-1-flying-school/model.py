"""
26.1 — Аттракцион "Flying school". Low-poly model, rasm: attraction-images-park/Flying_School.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/26-1-flying-school/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png

Tuzilish (xarita kodi shu nomlarga tayanadi, src/map/GltfModel.tsx):
    base          — qimirlamaydigan qism: tosh supa, oltin panjara (kirish/chiqish), ko'k A-ramkalar (teshikli,
                    chiroqchali), tepadagi to'sin, bulutli "FLYING SCHOOL" peshtoqi, boshqaruv pulti
    swing0, swing1 — samolyot-kabinalar osma qo'llari bilan: tepadagi o'q atrofida oldinga-orqaga tebranadi.
                    Origin — o'q markazida, o'q — Blender X bo'ylab (samolyot burni -Y ga qaragan).
Asl o'lcham metrda: supa 8.4 × 7.0 m, balandligi ~6.7 m (peshtoq bilan). Uzun o'qi — X, old tomoni — Blender'da -Y.
Xaritada `size` bilan plandagi maydonchaga sig'diriladi (nisbat 8.4 : 7.0 = 6 : 5 — plandagi bilan bir xil).
"""
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Euler, Vector

HERE = Path(__file__).resolve().parent
OUT_GLB = HERE / 'model.glb'
OUT_BLEND = HERE / 'model.blend'
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PREVIEW_DIR = Path(argv[0]) if argv else HERE

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

PALETTE = {
    'stone': (0.42, 0.41, 0.4), 'paver': (0.5, 0.49, 0.47), 'gold': (0.85, 0.6, 0.15), 'blue': (0.12, 0.42, 0.85),
    'navy': (0.08, 0.2, 0.55), 'sky': (0.45, 0.72, 0.95), 'cloud': (0.93, 0.96, 1.0), 'yellow': (0.98, 0.8, 0.08),
    'orange': (0.98, 0.45, 0.05), 'red': (0.85, 0.1, 0.08), 'green': (0.2, 0.7, 0.25), 'pink': (0.85, 0.3, 0.55),
    'purple': (0.5, 0.3, 0.8), 'steel': (0.65, 0.66, 0.68), 'beige': (0.9, 0.88, 0.8), 'white': (0.97, 0.97, 0.97),
    'sign': (0.15, 0.6, 0.25),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.5
    if name in ('gold', 'steel'):
        bsdf.inputs['Metallic'].default_value = 0.3  # xaritada atrof-muhit aksi yo'q — yuqori metallik qoraygan ko'rinadi
    m.diffuse_color = (*rgb, 1)
    MATS[name] = m


def new_obj(name, bm, mat):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(MATS[mat])
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob


def box(size, loc, mat, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return new_obj('box', bm, mat)


def cyl(r, h, loc, mat, segs=10, rot=(0, 0, 0), r2=None):
    """Silindr/konus: markazi loc, o'qi Z (rot bilan buriladi)"""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return new_obj('cyl', bm, mat)


def ball(r, loc, mat):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return new_obj('ball', bm, mat)


def beam(a, b, w, d, mat):
    """a→b to'sin, kesimi w × d"""
    a, b = Vector(a), Vector(b)
    v = b - a
    ob = box((v.length, w, d), (0, 0, 0), mat)
    ob.rotation_euler = v.to_track_quat('X', 'Z').to_euler()
    ob.location = (a + b) / 2
    return ob


def prism(pts, z0, z1, mat):
    """XY ko'pburchak → z0..z1 prizma"""
    bm = bmesh.new()
    bot = [bm.verts.new((x, y, z0)) for x, y in pts]
    top = [bm.verts.new((x, y, z1)) for x, y in pts]
    bm.faces.new(bot[::-1])
    bm.faces.new(top)
    n = len(pts)
    for k in range(n):
        bm.faces.new([bot[k], bot[(k + 1) % n], top[(k + 1) % n], top[k]])
    return new_obj('prism', bm, mat)


def plate_yz(pts, x, t, mat):
    """YZ tekislikdagi ko'pburchak → X bo'yicha qalinligi t plastina"""
    bm = bmesh.new()
    a = [bm.verts.new((x - t / 2, y, z)) for y, z in pts]
    b = [bm.verts.new((x + t / 2, y, z)) for y, z in pts]
    bm.faces.new(a[::-1])
    bm.faces.new(b)
    n = len(pts)
    for k in range(n):
        bm.faces.new([a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return new_obj('plate', bm, mat)


def cut_holes(ob, x, holes):
    """Boolean bilan dumaloq teshiklar (o'qi X bo'ylab, plastina x da)"""
    for (y, z, r) in holes:
        c = cyl(r, 2.0, (x, y, z), 'blue', 16, (0, math.pi / 2, 0))
        mod = ob.modifiers.new('hole', 'BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = c
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(c, do_unlink=True)


def join(name, objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return ob


# ---------- BASE ----------
W, D = 8.4, 7.0          # supa (X × Y)
CH = 1.1                 # old burchaklar qirqimi
H0 = 0.4                 # supa balandligi
p = []
outline = [(-W / 2 + CH, -D / 2), (W / 2 - CH, -D / 2), (W / 2, -D / 2 + CH), (W / 2, D / 2), (-W / 2, D / 2),
           (-W / 2, -D / 2 + CH)]
p.append(prism(outline, 0, H0 - 0.03, 'stone'))
inset = 0.15
inner = [(-W / 2 + CH + inset * 0.4, -D / 2 + inset), (W / 2 - CH - inset * 0.4, -D / 2 + inset),
         (W / 2 - inset, -D / 2 + CH + inset * 0.4), (W / 2 - inset, D / 2 - inset), (-W / 2 + inset, D / 2 - inset),
         (-W / 2 + inset, -D / 2 + CH + inset * 0.4)]
p.append(prism(inner, H0 - 0.03, H0, 'paver'))

# oltin panjara: supa cheti bo'ylab, oldinda (-Y) kirish va chiqish ochiq
FH = 1.0
GAPS = [(-1.5, -0.5), (0.5, 1.5)]   # old tomondagi ochiq joylar (X oralig'i): chiqish, kirish
fence = [(x * 0.94, y * 0.94) for x, y in outline]
for k in range(len(fence)):
    a, b = Vector((*fence[k], 0)), Vector((*fence[(k + 1) % len(fence)], 0))
    L = (b - a).length
    n = max(2, round(L / 0.22))
    front = abs(a.y - b.y) < 1e-6 and a.y < 0
    segs = [(0.0, 1.0)]
    if front:  # old tomon: kirish/chiqish oraliqlarini qoldirib, bo'laklarga bo'linadi
        xs = sorted([a.x, b.x])
        cuts, cur = [], xs[0]
        for g0, g1 in GAPS:
            cuts.append((cur, g0))
            cur = g1
        cuts.append((cur, xs[1]))
        segs = [((c0 - a.x) / (b.x - a.x), (c1 - a.x) / (b.x - a.x)) for c0, c1 in cuts]
    for t0, t1 in segs:
        if t1 < t0:
            t0, t1 = t1, t0
        pa, pb = a.lerp(b, t0), a.lerp(b, t1)
        for z in (H0 + 0.12, H0 + FH - 0.05):
            p.append(beam((pa.x, pa.y, z), (pb.x, pb.y, z), 0.04, 0.04, 'gold'))
        m = max(1, round((pb - pa).length / 0.22))
        for i in range(m + 1):
            q = pa.lerp(pb, i / m)
            if i in (0, m):  # ustun, tepasida shar
                p.append(box((0.08, 0.08, FH + 0.1), (q.x, q.y, H0 + (FH + 0.1) / 2), 'gold'))
                p.append(ball(0.07, (q.x, q.y, H0 + FH + 0.14), 'gold'))
            else:
                p.append(box((0.025, 0.025, FH - 0.1), (q.x, q.y, H0 + 0.08 + (FH - 0.1) / 2), 'gold'))
# yashil yozuvlar: CHIQISH / KIRISH (ochiq joylar yonida)
for gx in (-1.95, 0.0):
    p.append(box((0.7, 0.03, 0.35), (gx, -D / 2 * 0.94 - 0.04, H0 + 0.6), 'sign'))
    p.append(box((0.5, 0.035, 0.05), (gx, -D / 2 * 0.94 - 0.045, H0 + 0.66), 'white'))
    p.append(box((0.4, 0.035, 0.04), (gx, -D / 2 * 0.94 - 0.045, H0 + 0.55), 'white'))

# ko'k A-ramkalar (YZ tekislikda trapetsiya, ichida 3 teshik), chetida rangli chiroqchalar
FX = 3.2                 # ramkalar X bo'yicha
BEAM_Z = 5.4             # tepadagi to'sin markazi
PIVOT_Z = 5.05           # tebranish o'qi
LIGHTS = ['red', 'yellow', 'green', 'white', 'orange']
for sx in (-1, 1):
    x = sx * FX
    shape = [(-1.6, H0), (1.6, H0), (0.35, BEAM_Z + 0.2), (-0.35, BEAM_Z + 0.2)]
    fr = plate_yz(shape, x, 0.28, 'blue')
    bpy.ops.object.select_all(action='DESELECT')
    cut_holes(fr, x, [(0, 1.35, 0.42), (0, 2.45, 0.36), (0, 3.45, 0.28)])
    p.append(fr)
    p.append(box((0.6, 3.6, 0.08), (x, 0, H0 + 0.04), 'navy'))          # tayanch plitasi
    for sy in (-1, 1):  # qiya qirralar bo'ylab chiroqchalar (ikki tomonda)
        a = Vector((x, sy * 1.6, H0 + 0.25))
        b = Vector((x, sy * 0.38, BEAM_Z))
        for k in range(14):
            q = a.lerp(b, (k + 0.5) / 14)
            for side in (-1, 1):
                p.append(ball(0.05, (x + side * 0.15, q.y - sy * 0.12, q.z), LIGHTS[k % 5]))
    # gul naqshi (sariq) ramka yuzida
    p.append(box((0.3, 0.18, 0.18), (x, -0.9, 3.0), 'orange', (0.6, 0, 0)))
# tepadagi to'sin va o'q podshipniklari
p.append(box((2 * FX + 0.3, 0.5, 0.4), (0, 0, BEAM_Z), 'blue'))
SWING_X = (-1.35, 1.35)
for sx in SWING_X:
    for dx in (-0.45, 0.45):
        p.append(box((0.08, 0.35, 0.45), (sx + dx, 0, PIVOT_Z + 0.05), 'navy'))
    p.append(cyl(0.06, 1.0, (sx, 0, PIVOT_Z), 'steel', 8, (0, math.pi / 2, 0)))

# bulutli peshtoq: ko'k taxta, oq bulutlar, "FLYING SCHOOL" (sariq harflar o'rnida bloklar), samolyotcha
SZ = BEAM_Z + 0.2
p.append(box((7.0, 0.2, 1.0), (0, 0, SZ + 0.6), 'sky'))
for k in range(15):  # bulut "puflari" — taxta cheti bo'ylab yassi disklar (o'rtasi ko'k qoladi)
    t = k / 14
    x = -3.5 + 7.0 * t
    for z, r in ((SZ + 0.08, 0.2 + 0.05 * (k % 3)), (SZ + 1.12, 0.18 + 0.06 * ((k + 1) % 3))):
        p.append(cyl(r, 0.16, (x, 0, z), 'cloud', 10, (math.pi / 2, 0, 0)))
for z in (SZ + 0.4, SZ + 0.8):
    for sx in (-1, 1):
        p.append(cyl(0.3, 0.16, (sx * 3.55, 0, z), 'cloud', 10, (math.pi / 2, 0, 0)))
text = 'FLYING SCHOOL'
for k, ch in enumerate(text):
    if ch == ' ':
        continue
    x = -2.9 + k * 0.38
    h = 0.5 if k in (0, 7) else 0.4
    for sy in (-1, 1):
        p.append(box((0.3, 0.06, h), (x, sy * 0.15, SZ + 0.6), 'yellow'))
        p.append(box((0.34, 0.04, h + 0.06), (x, sy * 0.12, SZ + 0.6), 'green'))   # yashil hoshiya
# rangli strelkalar (konuslar) peshtoq tepasida
for x, col in ((-1.8, 'pink'), (0.6, 'purple'), (2.6, 'green')):
    p.append(cyl(0.18, 0.4, (x, 0, SZ + 1.4), col, 6, (0, 0.4, 0), 0.0))
# samolyotcha o'ng chetda: tana, qanot, parrak
p.append(cyl(0.2, 1.0, (2.7, -0.15, SZ + 0.45), 'orange', 10, (0, math.pi / 2, 0), 0.12))
p.append(box((0.3, 0.06, 0.9), (2.8, -0.2, SZ + 0.45), 'yellow'))
p.append(cyl(0.3, 0.05, (2.15, -0.15, SZ + 0.45), 'sky', 8, (0, math.pi / 2, 0)))

# boshqaruv pulti: o'ng old burchakda
PX, PY = 3.3, -1.9
p.append(box((0.55, 0.45, 1.1), (PX, PY, H0 + 0.55), 'beige'))
for k, col in enumerate(('red', 'green', 'yellow', 'red', 'orange')):
    p.append(cyl(0.035, 0.03, (PX - 0.18 + (k % 3) * 0.18, PY - 0.08 + (k // 3) * 0.14, H0 + 1.11), col, 8))
base = join('base', p)

# ---------- SWING0/1: samolyot-kabinalar (o'q atrofida tebranadi) ----------
BODY_Z = 1.15            # tana markazi balandligi (tinch holatda)
BL, BR = 2.5, 0.55       # tana uzunligi (Y), radiusi
swings = []
for n, sx in enumerate(SWING_X):
    q = []
    # osma qo'llar: o'qdan tananing oldi va orqasiga V-shaklda (ikki yonida)
    for dx in (-0.38, 0.38):
        for sy in (-1, 1):
            q.append(beam((sx + dx * 0.6, 0, PIVOT_Z), (sx + dx, sy * 0.85, BODY_Z + 0.35), 0.12, 0.12, 'blue'))
        q.append(beam((sx + dx, -0.85, BODY_Z + 0.35), (sx + dx, 0.85, BODY_Z + 0.35), 0.1, 0.1, 'blue'))
    q.append(cyl(0.13, 0.85, (sx, 0, PIVOT_Z), 'navy', 10, (0, math.pi / 2, 0)))
    # tana: Y bo'ylab silindr (burni -Y), pastida sariq-to'q sariq tasma
    body = cyl(BR, BL, (sx, 0, BODY_Z), 'blue', 12, (math.pi / 2, 0, 0))
    body.scale = (1.0, 1.0, 1.0)
    q.append(body)
    q.append(cyl(BR + 0.02, BL - 0.3, (sx, 0, BODY_Z - 0.18), 'yellow', 12, (math.pi / 2, 0, 0)))
    q.append(box((1.0, BL - 0.2, 0.3), (sx, 0, BODY_Z - 0.38), 'orange'))
    # ochiq kabina: tepada to'q ko'k o'rindiqlar (ikki qator) va kumush tutqichlar
    for yy in (-0.45, 0.45):
        q.append(box((0.8, 0.7, 0.2), (sx, yy, BODY_Z + 0.48), 'navy'))
        q.append(box((0.8, 0.1, 0.4), (sx, yy + 0.33, BODY_Z + 0.65), 'navy'))
        q.append(cyl(0.025, 0.85, (sx, yy - 0.3, BODY_Z + 0.85), 'steel', 6, (0, math.pi / 2, 0)))
    # burun: rangli disk (sariq "nurlar") va yashil parrak
    q.append(cyl(BR * 0.92, 0.08, (sx, -BL / 2 - 0.04, BODY_Z), 'navy', 12, (math.pi / 2, 0, 0)))
    for k in range(8):
        a = k * math.pi / 4
        q.append(box((0.1, 0.04, 0.12), (sx + 0.3 * math.cos(a), -BL / 2 - 0.1, BODY_Z + 0.3 * math.sin(a)),
                     'yellow' if k % 2 else 'red', (0, a, 0)))
    q.append(cyl(0.1, 0.12, (sx, -BL / 2 - 0.14, BODY_Z), 'red', 8, (math.pi / 2, 0, 0)))
    q.append(box((1.1, 0.04, 0.14), (sx, -BL / 2 - 0.2, BODY_Z), 'green', (0, 0.7, 0)))
    # qanotchalar (pushti) yonlarda, dumda tik suzgich va qizil-sariq gorizontal dum
    for side in (-1, 1):
        q.append(box((0.45, 0.6, 0.07), (sx + side * (BR + 0.2), -0.2, BODY_Z - 0.05), 'pink'))
    q.append(box((0.12, 0.35, 0.55), (sx, BL / 2 - 0.2, BODY_Z + 0.75), 'yellow'))
    q.append(box((0.9, 0.25, 0.08), (sx, BL / 2 - 0.2, BODY_Z + 1.02), 'red'))
    q.append(cyl(0.05, 0.12, (sx, BL / 2 - 0.2, BODY_Z + 1.1), 'yellow', 6))
    sw = join(f'swing{n}', q)
    # Origin — o'q markaziga: tebranish shu nuqta atrofida
    bpy.ops.object.select_all(action='DESELECT')
    sw.select_set(True)
    bpy.context.view_layer.objects.active = sw
    scene.cursor.location = (sx, 0, PIVOT_Z)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    swings.append(sw)

tris = sum(len(pg.vertices) - 2 for o in scene.objects if o.type == 'MESH' for pg in o.data.polygons)
top = max((o.matrix_world @ v.co).z for o in scene.objects if o.type == 'MESH' for v in o.data.vertices)
print(f'FLYING_SCHOOL tris={tris} top={top:.2f}')

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'FLYING_SCHOOL glb={OUT_GLB.stat().st_size // 1024} KB')

# ---------- Preview (kabinalar qarama-qarshi tebrangan holatda) ----------
swings[0].rotation_euler = (math.radians(-35), 0, 0)
swings[1].rotation_euler = (math.radians(20), 0, 0)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.location = (9.5, -12.5, 7.5)
cam.rotation_euler = (Vector((0, 0, 2.8)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 900, 900
world = bpy.data.worlds.new('w')
world.color = (0.93, 0.95, 0.98)
scene.world = world
scene.render.filepath = str(PREVIEW_DIR / 'preview.png')
bpy.ops.render.render(write_still=True)
print('FLYING_SCHOOL preview', scene.render.filepath)

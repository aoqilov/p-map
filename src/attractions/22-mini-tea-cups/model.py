"""
22 — Аттракцион "Mini tea cups". Low-poly model, rasm: attraction-images-park/Midi_Tea_Cup.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/22-mini-tea-cups/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png

Tuzilish (xarita kodi shu nomlarga tayanadi, src/map/GltfModel.tsx):
    base       — qimirlamaydigan qism: to'q ko'k supa, oltin panjara (old tomonda kirish/chiqish, yashil yozuvlar),
                 markazdagi choynak (rangli bo'yoq oqimlari) tagkursisi bilan
    rotor      — aylanadigan ko'k disk va likopchalar (markaz atrofida)
    spin0..5   — piyolalar (rotor bolalari): o'z o'qi atrofida aylanadi, origin — piyola markazida
Asl o'lcham metrda: panjara diametri ~8.1 m, balandligi ~3.6 m (choynak). Old tomoni — Blender'da -Y.
Xaritada `size` bilan plandagi doiraga (diametri ~10 m) sig'diriladi.
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
    'navy': (0.07, 0.14, 0.32), 'deck': (0.12, 0.24, 0.5), 'gold': (0.85, 0.6, 0.15), 'porcelain': (0.96, 0.96, 0.95),
    'inner': (0.86, 0.87, 0.88), 'purple': (0.45, 0.15, 0.7), 'yellow': (0.98, 0.8, 0.08), 'blue': (0.1, 0.45, 0.8),
    'teal': (0.1, 0.55, 0.75), 'green': (0.25, 0.65, 0.12), 'red': (0.88, 0.08, 0.08), 'pink': (0.92, 0.25, 0.6),
    'steel': (0.65, 0.66, 0.68), 'sign': (0.15, 0.6, 0.25), 'white': (0.97, 0.97, 0.97),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.3 if name in ('porcelain', 'inner') else 0.5
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


def cyl(r, h, loc, mat, segs=12, rot=(0, 0, 0), r2=None):
    """Silindr/konus: markazi loc, o'qi Z (rot bilan buriladi); r — pastki, r2 — ustki radius"""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return new_obj('cyl', bm, mat)


def ball(r, loc, mat, scale=(1, 1, 1), sub=2):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return new_obj('ball', bm, mat)


def beam(a, b, w, d, mat):
    a, b = Vector(a), Vector(b)
    v = b - a
    ob = box((v.length, w, d), (0, 0, 0), mat)
    ob.rotation_euler = v.to_track_quat('X', 'Z').to_euler()
    ob.location = (a + b) / 2
    return ob


def torus(major, minor, loc, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=12, minor_segments=5,
                                     location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.data.materials.append(MATS[mat])
    return ob


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


def hollow_cup(r0, r1, h, wall, segs=20):
    """Ichi bo'sh piyola: tashqi devor (porcelain) va ichki devor + tag (inner) — ikki obyekt.
    Ichki yuzalar ichkariga qaragan (three.js orqa yuzalarni chizmaydi)"""
    bm = bmesh.new()
    ring = lambda r, z: [bm.verts.new((r * math.cos(2 * math.pi * i / segs), r * math.sin(2 * math.pi * i / segs), z))
                         for i in range(segs)]
    ob_, ot_, it_ = ring(r0, 0), ring(r1, h), ring(r1 - wall, h)
    bm.faces.new(ob_[::-1])
    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new([ob_[i], ob_[j], ot_[j], ot_[i]])     # tashqi devor
        bm.faces.new([ot_[i], ot_[j], it_[j], it_[i]])     # gardish usti
    outer = new_obj('cup_out', bm, 'porcelain')
    bm = bmesh.new()
    it2, ib2 = ring(r1 - wall, h), ring(r0 - wall, wall)
    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new([it2[i], it2[j], ib2[j], ib2[i]])    # ichki devor (ichkariga)
    bm.faces.new(ib2)                                      # ichki tag (tepaga)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)            # ochiq idish: recalc tashqariga buradi — teskari qilamiz
    inner = new_obj('cup_in', bm, 'inner')
    return [outer, inner]


def band(r0, r1, z0, z1, mat, segs=20):
    """Ochiq halqa (qopqoqsiz konus yuzasi) — bo'yoq gardishi"""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=segs, radius1=r0, radius2=r1, depth=z1 - z0)
    bmesh.ops.translate(bm, vec=(0, 0, (z0 + z1) / 2), verts=bm.verts)
    return new_obj('band', bm, mat)


def drips(cx, cy, z, r, mat, n, seed, out=0.0):
    """Bo'yoq oqimlari: z balandlikdagi halqa (radius r) ostidan turli uzunlikda osilgan 'tomchilar'"""
    res = []
    for k in range(n):
        a = 2 * math.pi * k / n
        ln = 0.08 + 0.16 * (((k * 7 + seed) * 37) % 10) / 10
        x, y = cx + (r + out) * math.cos(a), cy + (r + out) * math.sin(a)
        res.append(box((0.06, 0.03, ln), (x, y, z - ln / 2), mat, (0, 0, a + math.pi / 2)))
        res.append(ball(0.035, (x, y, z - ln), mat, sub=1))
    return res


# ---------- BASE ----------
R_DECK = 3.7             # supa radiusi
H0 = 0.45                # supa balandligi
p = []
p.append(cyl(R_DECK, H0, (0, 0, H0 / 2), 'navy', 32))

# oltin panjara (doira, 20 ta bo'lak), old tomonda (-Y) ikkita ochiq joy: chiqish va kirish
RF, FH, NS = 4.05, 0.95, 20
GAP_SEGS = {14, 16}      # -Y atrofidagi bo'laklar (a = -90° ≈ 15-bo'lak)
for k in range(NS):
    a0, a1 = 2 * math.pi * k / NS, 2 * math.pi * (k + 1) / NS
    pa = Vector((RF * math.cos(a0), RF * math.sin(a0), 0))
    pb = Vector((RF * math.cos(a1), RF * math.sin(a1), 0))
    p.append(box((0.09, 0.09, FH + 0.1), (pa.x, pa.y, (FH + 0.1) / 2), 'gold'))
    p.append(ball(0.06, (pa.x, pa.y, FH + 0.14), 'gold', sub=1))
    if k in GAP_SEGS:
        continue
    for z in (0.12, FH - 0.05):
        p.append(beam((pa.x, pa.y, z), (pb.x, pb.y, z), 0.035, 0.035, 'gold'))
    for i in range(1, 6):
        q = pa.lerp(pb, i / 6)
        p.append(box((0.025, 0.025, FH - 0.12), (q.x, q.y, 0.09 + (FH - 0.12) / 2), 'gold'))
# yashil yozuvlar: CHIQISH / KIRISH — ochiq joylar orasidagi bo'lakda (-Y)
for k in (15,):
    am = 2 * math.pi * (k + 0.5) / NS
    for off in (-0.35, 0.35):
        a = am + off / RF
        x, y = (RF + 0.03) * math.cos(a), (RF + 0.03) * math.sin(a)
        p.append(box((0.55, 0.03, 0.28), (x, y, 0.62), 'sign', (0, 0, a + math.pi / 2)))
        p.append(box((0.4, 0.035, 0.04), (x * 1.002, y * 1.002, 0.66), 'white', (0, 0, a + math.pi / 2)))

# markazdagi choynak: tagkursi (rangli halqa bilan), qorni, bo'yni, qopqog'i, jo'mragi, dastasi
PZ = H0 + 0.95           # tagkursi tepasi
p.append(cyl(0.5, 0.95, (0, 0, H0 + 0.475), 'porcelain', 16))
p.append(cyl(0.52, 0.1, (0, 0, PZ - 0.05), 'green', 16))
p.append(cyl(0.5, 0.05, (0, 0, PZ - 0.12), 'pink', 16))
p.append(ball(0.55, (0, 0, PZ + 0.5), 'porcelain', (1, 1, 1.05)))
p.append(cyl(0.48, 0.5, (0, 0, PZ + 1.05), 'pink', 16, r2=0.28))           # bo'yin — pushti bo'yoq
p.append(cyl(0.3, 0.1, (0, 0, PZ + 1.35), 'yellow', 16))                   # sariq gardish
p.append(cyl(0.3, 0.14, (0, 0, PZ + 1.47), 'green', 16, r2=0.12))          # qopqoq
p.append(ball(0.08, (0, 0, PZ + 1.6), 'pink', sub=1))
p.extend(drips(0, 0, PZ + 0.85, 0.5, 'pink', 10, 1, 0.02))
p.extend(drips(0, 0, PZ + 0.75, 0.54, 'yellow', 8, 4, 0.02))
p.extend(drips(0, 0, PZ + 0.6, 0.56, 'green', 6, 7, 0.01))
p.append(cyl(0.1, 1.0, (0.62, 0, PZ + 0.75), 'porcelain', 8, (0, math.radians(40), 0), 0.05))     # jo'mrak
p.append(torus(0.38, 0.06, (-0.55, 0, PZ + 0.8), 'porcelain', (math.pi / 2, 0, 0)))             # dasta
base = join('base', p)

# ---------- ROTOR: aylanadigan disk va likopchalar ----------
R_CUP = 2.45             # piyolalar markazi radiusi
CUPS = ['purple', 'yellow', 'blue', 'teal', 'red', 'green']
DZ = H0 + 0.04
q = [cyl(R_DECK - 0.1, 0.08, (0, 0, DZ), 'deck', 32)]
for k in range(6):  # disk bo'laklari chiziqlari
    a = k * math.pi / 3 + math.pi / 6
    q.append(box((R_DECK - 0.75, 0.03, 0.01), ((0.55 + (R_DECK - 0.75) / 2) * math.cos(a),
                                                 (0.55 + (R_DECK - 0.75) / 2) * math.sin(a), DZ + 0.045),
                 'navy', (0, 0, a)))
for k in range(6):
    a = k * math.pi / 3
    x, y = R_CUP * math.cos(a), R_CUP * math.sin(a)
    q.append(cyl(0.72, 0.08, (x, y, DZ + 0.08), 'porcelain', 20, r2=0.95))   # likopcha
rotor = join('rotor', q)

# ---------- SPIN0..5: piyolalar ----------
SZ0 = DZ + 0.12          # piyola tagi
CH = 0.85                # piyola balandligi
for k, col in enumerate(CUPS):
    a = k * math.pi / 3
    g = hollow_cup(0.42, 0.72, CH, 0.05)                                     # ichi bo'sh piyola
    g.append(band(0.677, 0.725, CH - 0.2, CH - 0.005, col))                  # rangli bo'yoq gardishi (tashqarida)
    g.append(cyl(0.5, 0.25, (0, 0, 0.2), 'inner', 16))                       # ichidagi o'rindiq (aylana)
    g.extend(drips(0, 0, CH - 0.2, 0.66, col, 12, k * 3, 0.03))
    g.append(torus(0.2, 0.05, (0.78, 0, CH * 0.55), 'porcelain', (math.pi / 2, 0, 0)))   # dasta
    g.append(cyl(0.18, 0.05, (0, 0, CH * 0.55), 'steel', 10))                # rul (o'rtada)
    g.append(cyl(0.03, 0.5, (0, 0, CH * 0.3), 'steel', 6))
    g.append(beam((-0.45, -0.35, CH - 0.05), (-0.45, 0.35, CH - 0.05), 0.04, 0.04, 'steel'))   # tutqich
    cup = join(f'spin{k}', g)
    cup.location = (R_CUP * math.cos(a), R_CUP * math.sin(a), SZ0)
    cup.rotation_euler = (0, 0, a * 1.7)
    cup.parent = rotor

objs = [o for o in scene.objects if o.type == 'MESH']
tris = sum(len(pg.vertices) - 2 for o in objs for pg in o.data.polygons)
top = max((o.matrix_world @ v.co).z for o in objs for v in o.data.vertices)
xmax = max(abs((o.matrix_world @ v.co).x) for o in objs for v in o.data.vertices)
print(f'TEA_CUPS tris={tris} top={top:.2f} width={2 * xmax:.2f} objects={[o.name for o in objs]}')

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'TEA_CUPS glb={OUT_GLB.stat().st_size // 1024} KB')

# ---------- Preview ----------
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.location = (7.5, -10.5, 6.5)
cam.rotation_euler = (Vector((0, 0, 1.0)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
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
print('TEA_CUPS preview', scene.render.filepath)

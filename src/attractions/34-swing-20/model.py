"""
34 — Аттракцион "Swing 20" (barokko uslubidagi zanjirli karusel). Low-poly model, rasm: attraction-images-park/Swing_Baroque.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/34-swing-20/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png

Tuzilish (xarita kodi: src/map/GltfModel.tsx):
    base        — qimirlamaydigan qism: sakkiz qirrali kumush supa, oltin panjara (old tomonda kirish),
                  ustunning pastki qismi (qizil tagkursi, krem "ko'za", oltin naqshlar, chiroqchali qizil halqa)
    rotor       — aylanadigan qism: ustun yuqorisi (rasmli panellar), soyabon (osti ko'k rasmli, qizil chiroqli
                  gardish, tepada krem toj — oltin chig'anoqlar va jingalaklar)
    swing0..19  — zanjirli qizil-oq o'rindiqlar (rotor bolalari): origin — ilgakda, lokal +Y — tashqariga;
                  kod ularni tashqariga og'diradi (markazdan qochma kuch) — lokal X o'qi atrofida
Asl o'lcham metrda: panjara diametri ~9.8 m, balandligi ~5.6 m. Old tomoni — Blender'da -Y.
Xaritada `size` bilan plandagi doiraga (diametri ~8.4 m) sig'diriladi.
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
    'plate': (0.72, 0.73, 0.75), 'plate_side': (0.5, 0.51, 0.53), 'gold': (0.8, 0.58, 0.18), 'cream': (0.95, 0.88, 0.7),
    'red': (0.62, 0.06, 0.08), 'bulb': (1.0, 0.98, 0.92), 'sky': (0.5, 0.72, 0.9), 'steel': (0.7, 0.71, 0.73),
    'seat': (0.7, 0.08, 0.1), 'white': (0.97, 0.97, 0.97),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.5
    if name in ('gold', 'steel', 'plate'):
        bsdf.inputs['Metallic'].default_value = 0.3  # xaritada atrof-muhit aksi yo'q — yuqori metallik qoraygan ko'rinadi
    if name == 'bulb':
        bsdf.inputs['Emission Color'].default_value = (1.0, 0.95, 0.8, 1)
        bsdf.inputs['Emission Strength'].default_value = 0.6
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
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return new_obj('cyl', bm, mat)


def ball(r, loc, mat, sub=1):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return new_obj('ball', bm, mat)


def beam(a, b, w, d, mat):
    a, b = Vector(a), Vector(b)
    v = b - a
    ob = box((v.length, w, d), (0, 0, 0), mat)
    ob.rotation_euler = v.to_track_quat('X', 'Z').to_euler()
    ob.location = (a + b) / 2
    return ob


def lathe(profile, mat, segs=24, cap_bottom=True, cap_top=True):
    """Aylanish jismi: profile — [(radius, z), ...] pastdan tepaga"""
    bm = bmesh.new()
    rings = [[bm.verts.new((r * math.cos(2 * math.pi * i / segs), r * math.sin(2 * math.pi * i / segs), z))
              for i in range(segs)] for r, z in profile]
    for a, b in zip(rings, rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            bm.faces.new([a[i], a[j], b[j], b[i]])
    if cap_bottom:
        bm.faces.new(rings[0][::-1])
    if cap_top:
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return new_obj('lathe', bm, mat)


def ring_of(n, r, z, fn, phase=0.0):
    """n ta element r radiusda, z balandlikda; fn(x, y, z, a) → obyekt"""
    return [fn(r * math.cos(phase + 2 * math.pi * k / n), r * math.sin(phase + 2 * math.pi * k / n), z,
               phase + 2 * math.pi * k / n) for k in range(n)]


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
R_DECK, H0 = 4.5, 0.3
p = []
p.append(cyl(R_DECK, H0, (0, 0, H0 / 2), 'plate_side', 8, (0, 0, math.pi / 8)))
p.append(cyl(R_DECK - 0.05, 0.02, (0, 0, H0 + 0.01), 'plate', 8, (0, 0, math.pi / 8)))

# oltin panjara: 16 qirrali, old tomonda (-Y) bitta ochiq bo'lak — kirish
RF, FH, NS = 4.9, 1.0, 16
GAP = 12                 # -Y dagi bo'lak (a = 270° ± 11°)
for k in range(NS):
    a0 = 2 * math.pi * (k - 0.5) / NS
    a1 = 2 * math.pi * (k + 0.5) / NS
    pa = Vector((RF * math.cos(a0), RF * math.sin(a0), 0))
    pb = Vector((RF * math.cos(a1), RF * math.sin(a1), 0))
    p.append(box((0.1, 0.1, FH + 0.08), (pa.x, pa.y, (FH + 0.08) / 2), 'gold'))
    p.append(box((0.22, 0.22, 0.03), (pa.x, pa.y, 0.015), 'plate_side'))
    p.append(ball(0.06, (pa.x, pa.y, FH + 0.13), 'gold'))
    if k == GAP:
        continue
    for z in (0.12, FH - 0.05):
        p.append(beam((pa.x, pa.y, z), (pb.x, pb.y, z), 0.035, 0.035, 'gold'))
    for i in range(1, 9):
        q = pa.lerp(pb, i / 9)
        p.append(box((0.025, 0.025, FH - 0.12), (q.x, q.y, 0.09 + (FH - 0.12) / 2), 'gold'))

# ustun pastki qismi: qizil tagkursi → krem "ko'za" → bo'yin → chiroqchali qizil halqa
Z0 = H0
p.append(cyl(1.05, 0.3, (0, 0, Z0 + 0.15), 'red', 24))
p.append(lathe([(0.95, Z0 + 0.3), (1.08, Z0 + 0.7), (1.12, Z0 + 1.1), (1.0, Z0 + 1.5), (0.78, Z0 + 1.8),
                (0.72, Z0 + 2.0)], 'cream'))
for k in range(8):  # oltin tik naqshlar (jingalak "barglar")
    a = 2 * math.pi * k / 8 + math.pi / 8
    for z, r, h in ((Z0 + 0.75, 1.1, 0.7), (Z0 + 1.35, 1.06, 0.4)):
        p.append(box((0.06, 0.1, h), (r * math.cos(a), r * math.sin(a), z), 'gold', (0, 0, a)))
    p.append(ball(0.09, (1.08 * math.cos(a), 1.08 * math.sin(a), Z0 + 1.6), 'gold'))
RING_Z = Z0 + 2.05
p.append(cyl(0.92, 0.14, (0, 0, RING_Z), 'red', 24))
p.extend(ring_of(20, 0.93, RING_Z, lambda x, y, z, a: ball(0.045, (x, y, z), 'bulb')))
base = join('base', p)

# ---------- ROTOR: ustun yuqorisi va soyabon ----------
q = []
UZ = RING_Z + 0.07
q.append(lathe([(0.78, UZ), (0.8, UZ + 0.3), (0.95, UZ + 0.8), (1.25, UZ + 1.25)], 'cream'))
for k in range(8):  # rasmli panellar va qizil qovurg'alar
    a = 2 * math.pi * k / 8
    q.append(box((0.04, 0.42, 0.55), (0.9 * math.cos(a), 0.9 * math.sin(a), UZ + 0.62), 'sky', (0, -0.3, a)))
    a2 = a + math.pi / 8
    q.append(beam((0.8 * math.cos(a2), 0.8 * math.sin(a2), UZ + 0.1), (1.24 * math.cos(a2), 1.24 * math.sin(a2), UZ + 1.22),
                  0.08, 0.08, 'red'))
q.extend(ring_of(16, 1.28, UZ + 1.25, lambda x, y, z, a: ball(0.045, (x, y, z), 'bulb')))
# soyabon osti: ko'tarilgan konus (krem), rasmli ko'k panellar, qizil radial qovurg'alar
CZ0, CZ1 = UZ + 1.25, UZ + 2.05      # soyabon ichki va tashqi cheti balandligi
R_C = 3.85
q.append(lathe([(1.25, CZ0), (R_C, CZ1)], 'cream', 32, False, False))
q.append(lathe([(1.25, CZ0 + 0.06), (R_C, CZ1 + 0.06)], 'cream', 32, False, False))
NP = 10
for k in range(NP):
    a = 2 * math.pi * k / NP
    rm = (1.25 + R_C) / 2 + 0.2
    zm = CZ0 + (CZ1 - CZ0) * (rm - 1.25) / (R_C - 1.25) - 0.03
    tilt = math.atan2(CZ1 - CZ0, R_C - 1.25)
    q.append(box((1.3, 0.85, 0.02), (rm * math.cos(a), rm * math.sin(a), zm), 'sky', (0, -tilt, a)))
    a2 = a + math.pi / NP
    q.append(beam((1.25 * math.cos(a2), 1.25 * math.sin(a2), CZ0 - 0.04), (R_C * math.cos(a2), R_C * math.sin(a2), CZ1 - 0.04),
                  0.09, 0.07, 'red'))
# qizil gardish chiroqchalar bilan
RIM_Z = CZ1 + 0.05
q.append(lathe([(R_C, RIM_Z - 0.12), (R_C + 0.08, RIM_Z - 0.1), (R_C + 0.08, RIM_Z + 0.12), (R_C, RIM_Z + 0.14)], 'red', 40,
               False, False))
q.extend(ring_of(40, R_C + 0.1, RIM_Z, lambda x, y, z, a: ball(0.05, (x, y, z), 'bulb')))
# krem toj: tik devor, ustida oltin chig'anoqlar va jingalaklar, tepa qopqoq
TZ0, TZ1 = RIM_Z + 0.14, RIM_Z + 0.8
q.append(lathe([(R_C - 0.05, TZ0), (R_C - 0.05, TZ1)], 'cream', 40, False, False))
q.append(lathe([(R_C - 0.05, TZ1), (R_C - 0.6, TZ1 + 0.15), (1.0, TZ1 + 0.45), (0.0, TZ1 + 0.55)], 'cream', 32, False, False))
q.append(cyl(R_C, 0.04, (0, 0, TZ0 + 0.02), 'gold', 40))                          # pastki oltin chiziq
for k in range(10):
    a = 2 * math.pi * k / 10
    x, y = (R_C - 0.02) * math.cos(a), (R_C - 0.02) * math.sin(a)
    # chig'anoq: yarim disk (tashqariga qaragan), ustida qirralar
    q.append(cyl(0.32, 0.06, (x, y, TZ1 - 0.02), 'gold', 10, (math.pi / 2, 0, a + math.pi / 2)))
    for f in (-0.18, 0.0, 0.18):
        q.append(box((0.05, 0.03, 0.3), (x + f * -math.sin(a) + 0.03 * math.cos(a), y + f * math.cos(a) + 0.03 * math.sin(a),
                                         TZ1 + 0.05), 'gold', (0, 0, a + math.pi / 2)))
    # jingalaklar (chig'anoqlar orasida): ikki halqa
    b = a + math.pi / 10
    for dz, s in ((0.38, -1), (0.38, 1)):
        bx, by = (R_C + 0.01) * math.cos(b), (R_C + 0.01) * math.sin(b)
        t = Vector((-math.sin(b), math.cos(b), 0)) * 0.22 * s
        bpy.ops.mesh.primitive_torus_add(major_radius=0.13, minor_radius=0.03, major_segments=10, minor_segments=4,
                                         location=(bx + t.x, by + t.y, TZ0 + dz), rotation=(math.pi / 2, 0, b + math.pi / 2))
        tor = bpy.context.active_object
        tor.data.materials.append(MATS['gold'])
        q.append(tor)
    q.append(beam((R_C * math.cos(b - 0.12), R_C * math.sin(b - 0.12), TZ0 + 0.18),
                  (R_C * math.cos(b + 0.12), R_C * math.sin(b + 0.12), TZ0 + 0.18), 0.04, 0.04, 'gold'))
q.append(ball(0.15, (0, 0, TZ1 + 0.62), 'gold'))
rotor = join('rotor', q)

# ---------- O'rindiqlar: zanjir + qizil-oq o'rindiq; lokal +Y — tashqariga, ilgakda origin ----------
N = 20
R_HOOK = R_C - 0.3
Z_HOOK = CZ1 - 0.25
SEAT_Z = H0 + 0.75
L = SEAT_Z - Z_HOOK      # manfiy: ilgakdan o'rindiqqacha
for k in range(N):
    a = 2 * math.pi * k / N
    s = []
    for side in (-0.22, 0.22):
        for dy in (-0.15, 0.15):
            s.append(beam((side * 0.4, 0, 0), (side, dy, L + 0.42), 0.02, 0.02, 'steel'))
    s.append(box((0.5, 0.44, 0.1), (0, 0, L + 0.03), 'seat'))                     # qizil tag
    s.append(box((0.5, 0.42, 0.04), (0, 0, L + 0.1), 'white'))                    # oq o'rindiq
    s.append(box((0.5, 0.06, 0.38), (0, -0.21, L + 0.25), 'white'))               # suyanchiq
    for sx in (-0.25, 0.25):
        s.append(box((0.04, 0.44, 0.2), (sx, 0, L + 0.15), 'seat'))
    s.append(beam((-0.22, 0.2, L + 0.36), (0.22, 0.2, L + 0.36), 0.025, 0.025, 'steel'))  # tutqich zanjiri
    s.append(beam((0, 0.22, L + 0.1), (0, 0.22, L - 0.3), 0.02, 0.02, 'steel'))          # oyoq zanjiri
    sw = join(f'swing{k}', s)
    sw.rotation_euler = (0, 0, a - math.pi / 2)
    sw.location = (math.cos(a) * R_HOOK, math.sin(a) * R_HOOK, Z_HOOK)
    sw.parent = rotor

objs = [o for o in scene.objects if o.type == 'MESH']
tris = sum(len(pg.vertices) - 2 for o in objs for pg in o.data.polygons)
top = max((o.matrix_world @ v.co).z for o in objs for v in o.data.vertices)
xmax = max(abs((o.matrix_world @ v.co).x) for o in objs for v in o.data.vertices)
print(f'SWING20 tris={tris} top={top:.2f} width={2 * xmax:.2f}')

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'SWING20 glb={OUT_GLB.stat().st_size // 1024} KB')

# ---------- Preview (o'rindiqlar aylanishda tashqariga og'gan holatda) ----------
for o in objs:
    if o.name.startswith('swing'):
        o.rotation_euler.x = math.radians(25)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.location = (9.0, -12.5, 6.5)
cam.rotation_euler = (Vector((0, 0, 2.4)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
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
print('SWING20 preview', scene.render.filepath)

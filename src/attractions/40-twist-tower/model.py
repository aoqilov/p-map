"""
40 — Аттракцион "Twist tower" (Drop'N'Twist). Rasm: attraction-images-park/Drop_N_Twist.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/40-twist-tower/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png (va preview_seats.png)

Tuzilish (xarita kodi: src/map/GltfModel.tsx):
    base   — qimirlamaydigan qism: 12 qirrali supa (sariq belgilar), to'q ko'k panjara, zina, operator budkasi,
             panjarali minora (8 ustun, X-bog'lovchilar; rangi pastdan tepaga: qora → qizil → to'q sariq → sariq,
             ustunlar bo'ylab chiroqchalar), tepada sariq gumbaz
    lift0  — o'rindiqli halqa minora bo'ylab ko'tariladi/tushadi (anim.lift)
    spin0  — lift0 ning bolasi: qizil halqa va 16 o'rindiq (tashqariga qaragan, yelka tutqichlari) — aylanadi (anim.spin)
Asl o'lcham metrda: supa diametri ~9 m, balandligi ~23 m.
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

# minora rang tasmalari (pastdan tepaga)
BANDS = [(0.0, (0.12, 0.12, 0.14)), (0.35, (0.2, 0.08, 0.08)), (0.5, (0.72, 0.08, 0.06)), (0.68, (0.92, 0.3, 0.05)),
         (0.83, (0.98, 0.55, 0.05)), (0.93, (0.99, 0.82, 0.1))]
PALETTE = {
    'deck': (0.42, 0.43, 0.45), 'deck_side': (0.12, 0.15, 0.25), 'fence': (0.12, 0.15, 0.25), 'yellow': (0.98, 0.78, 0.1),
    'steel': (0.6, 0.62, 0.64), 'ring_red': (0.78, 0.06, 0.06), 'seat_red': (0.9, 0.15, 0.08), 'seat_or': (0.98, 0.5, 0.06),
    'black': (0.08, 0.08, 0.09), 'glass': (0.6, 0.7, 0.75), 'white': (0.95, 0.95, 0.95), 'bulb': (1.0, 0.92, 0.7),
    'gold': (0.98, 0.82, 0.15),
}
for i, (_, rgb) in enumerate(BANDS):
    PALETTE[f'band{i}'] = rgb
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.45
    if name.startswith('band') or name == 'steel':
        bsdf.inputs['Metallic'].default_value = 0.25  # xaritada atrof-muhit aksi yo'q — yuqori metallik qoraygan ko'rinadi
    if name == 'bulb':
        bsdf.inputs['Emission Color'].default_value = (*rgb, 1)
        bsdf.inputs['Emission Strength'].default_value = 1.3
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


def ball(r, loc, mat, sub=1, scale=(1, 1, 1)):
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


def lathe(profile, mat, segs=48):
    """Aylanish yuzasi: profil yuqoriga/tashqariga yursa — normal tashqariga/pastga"""
    bm = bmesh.new()
    rings = [[bm.verts.new((r * math.cos(2 * math.pi * i / segs), r * math.sin(2 * math.pi * i / segs), z)) for i in range(segs)]
             for r, z in profile]
    for a, b in zip(rings, rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            bm.faces.new([a[i], a[j], b[j], b[i]])
    return new_obj('lathe', bm, mat)


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
    ob.data.shade_smooth()
    ob.data.set_sharp_from_angle(angle=math.radians(50))
    return ob


def band_mat(t):
    """Balandlik ulushi t (0..1) → minora rang tasmasi"""
    k = 0
    for i, (t0, _) in enumerate(BANDS):
        if t >= t0:
            k = i
    return f'band{k}'


# ====================== BASE ======================
NP = 12
R_DECK, H0 = 4.45, 0.55
HALF = math.pi / NP
p = [cyl(R_DECK, H0, (0, 0, H0 / 2), 'deck_side', NP, (0, 0, HALF)),
     cyl(R_DECK - 0.04, 0.03, (0, 0, H0 + 0.015), 'deck', NP, (0, 0, HALF))]
# sariq belgilar: ichki sakkiz qirra va radial chiziqlar
for k in range(8):
    a0, a1 = 2 * math.pi * k / 8 + math.pi / 8, 2 * math.pi * (k + 1) / 8 + math.pi / 8
    for r in (2.6, 3.4):
        p.append(beam((r * math.cos(a0), r * math.sin(a0), H0 + 0.035), (r * math.cos(a1), r * math.sin(a1), H0 + 0.035), 0.07,
                      0.01, 'yellow'))
    a = 2 * math.pi * k / 8
    p.append(beam((2.6 * math.cos(a), 2.6 * math.sin(a), H0 + 0.035), (3.4 * math.cos(a), 3.4 * math.sin(a), H0 + 0.035), 0.06,
                  0.01, 'yellow'))
    p.append(box((0.35, 0.35, 0.01), (3.0 * math.cos(a + math.pi / 8), 3.0 * math.sin(a + math.pi / 8), H0 + 0.035), 'yellow',
                 (0, 0, a)))
# panjara (12 qirra), old tomonda (-Y) zina uchun ochiq joy; zina; operator budkasi
RF = R_DECK - 0.12
GAP_K = 9                         # -Y ga yaqin qirra (zina)
for k in range(NP):
    a0, a1 = 2 * math.pi * k / NP + HALF * 0, 2 * math.pi * (k + 1) / NP
    pa = Vector((RF * math.cos(a0 - HALF + HALF), RF * math.sin(a0), 0))
    pa = Vector((RF * math.cos(a0), RF * math.sin(a0), H0))
    pb = Vector((RF * math.cos(a1), RF * math.sin(a1), H0))
    p.append(box((0.08, 0.08, 1.1), (pa.x, pa.y, H0 + 0.55), 'fence'))
    if k == GAP_K:
        continue
    for z in (0.1, 1.05):
        p.append(beam(pa + Vector((0, 0, z)), pb + Vector((0, 0, z)), 0.05, 0.05, 'fence'))
    for i in range(1, 12):
        c = pa.lerp(pb, i / 12)
        p.append(box((0.025, 0.025, 0.95), (c.x, c.y, H0 + 0.58), 'fence'))
ag = 2 * math.pi * (GAP_K + 0.5) / NP
gx, gy = (R_DECK + 0.6) * math.cos(ag), (R_DECK + 0.6) * math.sin(ag)
for k in range(4):     # zina pog'onalari (supadan tashqariga)
    r = R_DECK + 0.15 + k * 0.3
    h = H0 * (4 - k) / 5
    p.append(box((0.32, 1.2, h), (r * math.cos(ag), r * math.sin(ag), h / 2), 'deck_side', (0, 0, ag)))
    p.append(box((0.32, 1.2, 0.02), (r * math.cos(ag), r * math.sin(ag), h), 'deck', (0, 0, ag)))
for s in (-1, 1):
    t = Vector((-math.sin(ag), math.cos(ag), 0)) * 0.6 * s
    n = Vector((math.cos(ag), math.sin(ag), 0))
    p.append(beam(n * (R_DECK - 0.1) + t + Vector((0, 0, H0 + 1.0)), n * (R_DECK + 1.2) + t + Vector((0, 0, 1.0)), 0.04, 0.04,
                  'fence'))
    p.append(box((0.05, 0.05, 1.0), tuple(n * (R_DECK + 1.2) + t + Vector((0, 0, 0.5))), 'fence'))
ab = 2 * math.pi * 7.5 / NP     # operator budkasi (old-o'ngda)
bc = Vector((3.4 * math.cos(ab), 3.4 * math.sin(ab), H0))
p.append(box((1.0, 1.0, 1.9), (bc.x, bc.y, H0 + 0.95), 'fence', (0, 0, ab)))
p.append(box((1.02, 0.8, 0.8), (bc.x, bc.y, H0 + 1.4), 'glass', (0, 0, ab)))
p.append(box((1.15, 1.15, 0.1), (bc.x, bc.y, H0 + 1.95), 'black', (0, 0, ab)))
p.append(box((0.6, 0.02, 0.5), (bc.x + 0.51 * math.cos(ab), bc.y + 0.51 * math.sin(ab), H0 + 0.6), 'white', (0, 0, ab + math.pi / 2)))

# minora: 8 ustun (sakkiz qirra), har segmentda halqa va X-bog'lovchilar; ustunlarda chiroqchalar
TOWER_H = 21.5
R0, R1 = 0.95, 0.62
NSEG = 16
NPOST = 8
p.append(cyl(1.25, 0.4, (0, 0, H0 + 0.2), 'black', 16))
z0 = H0 + 0.4


def post_xy(k, z):
    t = (z - z0) / (TOWER_H - z0)
    r = R0 + (R1 - R0) * t
    a = 2 * math.pi * k / NPOST + math.pi / NPOST
    return Vector((r * math.cos(a), r * math.sin(a), z))


zs = [z0 + (TOWER_H - z0) * i / NSEG for i in range(NSEG + 1)]
for i in range(NSEG):
    za, zb = zs[i], zs[i + 1]
    mat = band_mat((za + zb) / 2 / TOWER_H)
    for k in range(NPOST):
        a0, a1 = post_xy(k, za), post_xy(k, zb)
        p.append(beam(a0, a1, 0.13, 0.13, mat))                        # ustun
        b0, b1 = post_xy((k + 1) % NPOST, za), post_xy((k + 1) % NPOST, zb)
        p.append(beam(a0, b1, 0.05, 0.05, mat))                        # X-bog'lovchi
        p.append(beam(b0, a1, 0.05, 0.05, mat))
        p.append(beam(a1, b1, 0.07, 0.07, mat))                        # halqa
        if k % 2 == 0:                                                   # chiroqchalar (har ikkinchi ustunda)
            for j in range(3):
                c = a0.lerp(a1, (j + 0.5) / 3)
                n = Vector((c.x, c.y, 0)).normalized()
                p.append(ball(0.04, tuple(c + n * 0.09), 'bulb'))
# ichki "o'zak" (qora quvur) — halqa yo'naltirgichi
p.append(cyl(0.38, TOWER_H - z0, (0, 0, (z0 + TOWER_H) / 2), 'black', 12))
# tepa: sariq gumbaz (ustunchalar, qopqoq, shar)
TZ = TOWER_H
p.append(cyl(R1 + 0.15, 0.15, (0, 0, TZ + 0.07), 'gold', 16))
for k in range(8):
    a = 2 * math.pi * k / 8
    p.append(cyl(0.05, 0.9, (0.7 * math.cos(a), 0.7 * math.sin(a), TZ + 0.6), 'gold', 8))
p.append(cyl(0.82, 0.12, (0, 0, TZ + 1.08), 'gold', 16))
p.append(lathe([(0.8, TZ + 1.14), (0.65, TZ + 1.5), (0.35, TZ + 1.72), (0.0, TZ + 1.8)], 'gold', 16))
p.append(ball(0.14, (0, 0, TZ + 1.9), 'gold'))
p.append(cyl(0.03, 0.4, (0, 0, TZ + 2.15), 'gold', 6, r2=0.0))
base = join('base', p)

# ====================== LIFT0 → SPIN0: o'rindiqli halqa ======================
lift = bpy.data.objects.new('lift0', None)
scene.collection.objects.link(lift)
RING_Z = H0 + 2.25            # qizil halqa markazi (pastki holatda)
s = []
R_RING = 1.75
s.append(lathe([(R_RING, RING_Z - 0.28), (R_RING + 0.05, RING_Z - 0.2), (R_RING + 0.05, RING_Z + 0.2), (R_RING, RING_Z + 0.28)],
               'ring_red', 48))
s.append(lathe([(1.0, RING_Z + 0.28), (R_RING, RING_Z + 0.28)], 'ring_red', 48))     # ustki yuza
s.append(lathe([(R_RING, RING_Z - 0.28), (1.0, RING_Z - 0.28)], 'ring_red', 48))     # pastki yuza
s.append(lathe([(1.0, RING_Z - 0.28), (1.0, RING_Z + 0.28)][::-1], 'black', 24))     # ichki devor
for k in range(12):   # halqadagi chiroqchalar va boltlar
    a = 2 * math.pi * k / 12
    s.append(ball(0.05, ((R_RING + 0.06) * math.cos(a), (R_RING + 0.06) * math.sin(a), RING_Z), 'bulb'))
    s.append(cyl(0.04, 0.03, (1.4 * math.cos(a), 1.4 * math.sin(a), RING_Z + 0.3), 'steel', 6))
NSEAT = 16
SEAT_R = 1.75
for k in range(NSEAT):
    a = 2 * math.pi * k / NSEAT
    n = Vector((math.cos(a), math.sin(a), 0))
    t = Vector((-math.sin(a), math.cos(a), 0))
    col = 'seat_red' if k % 2 == 0 else 'seat_or'
    base_c = n * SEAT_R + Vector((0, 0, H0 + 0.95))
    rot = (0, 0, a)
    s.append(box((0.12, 0.5, 1.0), tuple(base_c + n * -0.12 + Vector((0, 0, 0.55))), 'black', rot))    # suyanchiq ramasi
    s.append(box((0.14, 0.46, 0.9), tuple(base_c + n * -0.05 + Vector((0, 0, 0.55))), col, rot))      # suyanchiq
    s.append(box((0.42, 0.46, 0.12), tuple(base_c + n * 0.15 + Vector((0, 0, 0.06))), col, rot))      # o'tirg'ich
    s.append(box((0.1, 0.5, 0.5), tuple(base_c + n * -0.02 + Vector((0, 0, 1.1))), 'black', rot))     # bosh suyanchig'i
    for side in (-1, 1):                                                                                 # yelka tutqichi
        s.append(beam(base_c + t * (side * 0.17) + n * 0.02 + Vector((0, 0, 1.0)),
                      base_c + t * (side * 0.15) + n * 0.32 + Vector((0, 0, 0.45)), 0.06, 0.06, 'black'))
    s.append(box((0.08, 0.3, 0.2), tuple(base_c + n * 0.35 + Vector((0, 0, 0.35))), 'black', rot))
    s.append(box((0.3, 0.36, 0.04), tuple(base_c + n * 0.42 + Vector((0, 0, -0.38))), 'yellow', rot))  # oyoq tirgagi
    s.append(beam(base_c + n * 0.15 + Vector((0, 0, -0.05)), base_c + n * 0.42 + Vector((0, 0, -0.36)), 0.05, 0.05, 'steel'))
    s.append(beam(n * 1.05 + Vector((0, 0, RING_Z - 0.25)), base_c + n * -0.12 + Vector((0, 0, 1.05)), 0.07, 0.07, 'black'))
spin = join('spin0', s)
spin.parent = lift

objs = [o for o in scene.objects if o.type == 'MESH']
tris = sum(len(pg.vertices) - 2 for o in objs for pg in o.data.polygons)
bpy.context.view_layer.update()
allv = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
print(f'TWIST tris={tris} width={max(v.x for v in allv) - min(v.x for v in allv):.2f} top={max(v.z for v in allv):.2f}')

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'TWIST glb={OUT_GLB.stat().st_size // 1024} KB')

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 800, 1100
world = bpy.data.worlds.new('w')
world.color = (0.95, 0.96, 0.97)
scene.world = world
for fname, loc, tgt in (('preview.png', (15.0, -22.0, 12.0), (0, 0, 10.5)),
                        ('preview_seats.png', (4.5, -6.5, 3.5), (0, 0, 2.0))):
    cam.location = loc
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(PREVIEW_DIR / fname)
    bpy.ops.render.render(write_still=True)
    print('TWIST preview', scene.render.filepath)

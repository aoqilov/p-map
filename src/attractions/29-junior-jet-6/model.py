"""
29 — Аттракцион "Junior jet 6". Low-poly model, rasm: attraction-images-park/Junior_Jet.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/29-junior-jet-6/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png

Tuzilish (xarita kodi: src/map/GltfModel.tsx):
    base       — qimirlamaydigan qism: kulrang dumaloq supa, oltin panjara (old tomonda kirish/chiqish, yashil yozuvlar),
                 ko'k sakkiz qirrali poydevor (oynachali)
    rotor      — aylanadigan qism: ko'k ustun (chiroqchali), sariq-qizil "kapsula", qizil gumbaz, flyuger
    arm0..5    — qo'l uyasi (bo'sh tugun, rotor bolasi): sharnir joyi va qo'l yo'nalishi
    tilt0..5   — sariq qo'llar va gidravlik tirgaklar (arm bolasi): origin — sharnirda, ko'tariladi/tushadi
    hang0..5   — samolyotchalar (tilt bolasi): doim gorizontal turadi, burni aylanish yo'nalishiga qaragan
Asl o'lcham metrda: panjara diametri ~9.1 m, balandligi ~5.3 m (flyuger bilan). Old tomoni — Blender'da -Y.
Xaritada `size` bilan plandagi doiraga (diametri ~7.3 m) sig'diriladi.
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
    'deck': (0.6, 0.61, 0.62), 'deck_side': (0.45, 0.46, 0.47), 'gold': (0.82, 0.6, 0.18), 'blue': (0.12, 0.38, 0.8),
    'glass': (0.6, 0.85, 0.92), 'white': (0.96, 0.96, 0.96), 'yellow': (0.98, 0.8, 0.08), 'red': (0.85, 0.08, 0.08),
    'green': (0.2, 0.65, 0.2), 'dark': (0.1, 0.1, 0.12), 'steel': (0.65, 0.66, 0.68), 'sign': (0.15, 0.6, 0.25),
    'orange': (0.98, 0.45, 0.05),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.45
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
R_DECK, H0 = 4.3, 0.25
p = []
p.append(cyl(R_DECK, H0, (0, 0, H0 / 2), 'deck_side', 40))
p.append(cyl(R_DECK - 0.08, 0.02, (0, 0, H0 + 0.01), 'deck', 40))

# oltin panjara (18 bo'lak), old tomonda (-Y) ikkita ochiq joy: chiqish va kirish, orasida yozuvlar
RF, FH, NS = 4.15, 0.9, 18
GAPS = {12, 14}          # 13-bo'lak markazi ≈ 270° (-Y)
for k in range(NS):
    a0, a1 = 2 * math.pi * (k - 0.5) / NS, 2 * math.pi * (k + 0.5) / NS
    pa = Vector((RF * math.cos(a0), RF * math.sin(a0), H0))
    pb = Vector((RF * math.cos(a1), RF * math.sin(a1), H0))
    p.append(box((0.08, 0.08, FH + 0.08), (pa.x, pa.y, H0 + (FH + 0.08) / 2), 'gold'))
    p.append(ball(0.055, (pa.x, pa.y, H0 + FH + 0.12), 'gold'))
    if k in GAPS:
        continue
    for z in (0.1, FH - 0.05):
        p.append(beam((pa.x, pa.y, H0 + z), (pb.x, pb.y, H0 + z), 0.035, 0.035, 'gold'))
    for i in range(1, 7):
        q = pa.lerp(pb, i / 7)
        p.append(box((0.025, 0.025, FH - 0.1), (q.x, q.y, H0 + 0.08 + (FH - 0.1) / 2), 'gold'))
am = 2 * math.pi * 13 / NS
for off in (-0.33, 0.33):  # CHIQISH / KIRISH yozuvlari
    a = am + off / RF
    x, y = (RF + 0.04) * math.cos(a), (RF + 0.04) * math.sin(a)
    p.append(box((0.5, 0.03, 0.25), (x, y, H0 + 0.58), 'sign', (0, 0, a + math.pi / 2)))
    p.append(box((0.36, 0.035, 0.035), (x * 1.002, y * 1.002, H0 + 0.62), 'white', (0, 0, a + math.pi / 2)))

# ko'k sakkiz qirrali poydevor, yonlarida oynachalar (oq ramkali)
PB_R, PB_H = 1.05, 0.9
p.append(cyl(PB_R, PB_H, (0, 0, H0 + PB_H / 2), 'blue', 8, (0, 0, math.pi / 8), r2=0.85))
for k in range(8):
    a = 2 * math.pi * k / 8
    r = (PB_R + 0.85) / 2 * math.cos(math.pi / 8) + 0.01
    p.append(box((0.03, 0.5, 0.42), (r * math.cos(a), r * math.sin(a), H0 + 0.45), 'white', (0, -0.2, a)))
    p.append(box((0.035, 0.4, 0.32), ((r + 0.01) * math.cos(a), (r + 0.01) * math.sin(a), H0 + 0.45), 'glass', (0, -0.2, a)))
base = join('base', p)

# ---------- ROTOR: ustun, kapsula, gumbaz, flyuger ----------
COL_Z0 = H0 + PB_H
CAP_Z = 3.4              # kapsula pasti
q = [cyl(0.32, CAP_Z - COL_Z0, (0, 0, (COL_Z0 + CAP_Z) / 2), 'blue', 8, (0, 0, math.pi / 8))]
q.append(cyl(0.55, 0.15, (0, 0, COL_Z0 + 0.1), 'blue', 8, (0, 0, math.pi / 8)))     # sharnirlar halqasi
DOTS = ['red', 'yellow', 'green', 'white', 'orange']
for k in range(8):
    a = 2 * math.pi * k / 8
    for j in range(8):
        z = COL_Z0 + 0.35 + j * 0.24
        q.append(ball(0.035, (0.31 * math.cos(a), 0.31 * math.sin(a), z), DOTS[(j + k) % 5]))
# kapsula: sariq pastki halqa, qizil ustki halqa (chiroqchalar), qora qopqoq, qizil gumbaz
q.append(cyl(0.75, 0.3, (0, 0, CAP_Z + 0.15), 'yellow', 8, (0, 0, math.pi / 8), r2=0.9))
q.append(cyl(0.9, 0.38, (0, 0, CAP_Z + 0.49), 'red', 8, (0, 0, math.pi / 8)))
q.append(cyl(0.9, 0.08, (0, 0, CAP_Z + 0.68), 'yellow', 8, (0, 0, math.pi / 8)))
for k in range(8):
    a = 2 * math.pi * k / 8
    r = 0.9 * math.cos(math.pi / 8) + 0.02
    for j in range(3):
        t = Vector((-math.sin(a), math.cos(a), 0)) * (j - 1) * 0.15
        q.append(ball(0.04, (r * math.cos(a) + t.x, r * math.sin(a) + t.y, CAP_Z + 0.52), DOTS[(j + k) % 5]))
    q.append(cyl(0.06, 0.03, ((r - 0.12) * math.cos(a), (r - 0.12) * math.sin(a), CAP_Z + 0.2), 'white', 8,
                 (math.pi / 2, 0, a + math.pi / 2)))
q.append(cyl(0.6, 0.06, (0, 0, CAP_Z + 0.75), 'dark', 8, (0, 0, math.pi / 8)))
q.append(ball(0.42, (0, 0, CAP_Z + 0.78), 'red', 2, (1, 1, 0.75)))
VZ = CAP_Z + 1.1
q.append(cyl(0.025, 1.0, (0, 0, VZ + 0.4), 'white', 6))
for a in (0.0, math.pi / 2):
    for s in (-1, 1):
        x, y = s * 0.35 * math.cos(a), s * 0.35 * math.sin(a)
        q.append(beam((0, 0, VZ + 0.25), (x, y, VZ + 0.25), 0.025, 0.025, 'white'))
        q.append(ball(0.07, (x, y, VZ + 0.25), 'yellow'))
q.append(box((0.5, 0.03, 0.08), (0, 0, VZ + 0.7), 'blue'))                       # flyuger strelkasi
q.append(box((0.12, 0.03, 0.18), (-0.25, 0, VZ + 0.7), 'blue', (0, 0.3, 0)))
q.append(cyl(0.07, 0.15, (0.28, 0, VZ + 0.7), 'blue', 4, (0, math.pi / 2, 0), r2=0.0))
q.append(ball(0.08, (0, 0, VZ + 0.92), 'yellow'))
rotor = join('rotor', q)

# ---------- Qo'llar va samolyotlar ----------
HINGE_R, HINGE_Z = 0.5, COL_Z0 + 0.1
ARM_L = 2.1
REST = math.radians(6)   # tinch holatda qo'l uchi biroz pastda
PLANES = [('red', 'yellow'), ('green', 'yellow'), ('blue', 'red'), ('red', 'white'), ('green', 'yellow'),
          ('yellow', 'red')]


def plane(body, wing):
    """Samolyot: lokal +Y — burun (aylanish yo'nalishi), +X — tashqariga; origin — qo'l uchida"""
    g = []
    cx = 0.45            # tana markazi (qo'l uchidan tashqariga)
    BZ = 0.15
    g.append(cyl(0.38, 1.4, (cx, 0.05, BZ), body, 12, (-math.pi / 2, 0, 0), r2=0.3))      # tana
    g.append(cyl(0.3, 0.45, (cx, 0.95, BZ), body, 12, (-math.pi / 2, 0, 0), r2=0.12))     # burun konusi
    g.append(cyl(0.38, 0.5, (cx, -0.85, BZ + 0.04), body, 12, (math.pi / 2, 0, 0), r2=0.12))   # dum qismi
    g.append(box((0.5, 0.7, 0.08), (cx, 0.05, BZ + 0.33), 'dark'))                        # ochiq kabina
    g.append(box((0.52, 0.06, 0.18), (cx, 0.42, BZ + 0.4), 'glass', (0.4, 0, 0)))         # oyna
    g.append(box((1.7, 0.55, 0.06), (cx, 0.25, BZ - 0.08), wing))                        # qanotlar (radial)
    for s in (-1, 1):  # qanot uchidagi oq yulduzcha o'rnida
        g.append(box((0.18, 0.18, 0.07), (cx + s * 0.65, 0.25, BZ - 0.08), 'white', (0, 0, math.pi / 4)))
    g.append(box((0.06, 0.35, 0.42), (cx, -1.0, BZ + 0.32), wing))                       # tik suzgich
    g.append(box((0.8, 0.28, 0.05), (cx, -1.0, BZ + 0.1), wing))                         # gorizontal dum
    g.append(cyl(0.09, 0.12, (cx, 1.2, BZ), 'red', 8, (-math.pi / 2, 0, 0), r2=0.04))    # parrak markazi
    g.append(box((0.08, 0.04, 0.75), (cx, 1.22, BZ), 'dark', (0, 0.5, 0)))               # parrak
    g.append(cyl(0.035, 0.25, (cx, 0.45, BZ - 0.3), 'dark', 6))                          # g'ildirak oyog'i
    g.append(cyl(0.08, 0.06, (cx, 0.45, BZ - 0.42), 'dark', 8, (0, math.pi / 2, 0)))
    return g


for n in range(6):
    yaw = n * math.pi / 3 + math.pi / 6
    arm = bpy.data.objects.new(f'arm{n}', None)
    scene.collection.objects.link(arm)
    arm.parent = rotor
    arm.location = (math.cos(yaw) * HINGE_R, math.sin(yaw) * HINGE_R, HINGE_Z)
    arm.rotation_euler = (0, 0, yaw)

    # tilt<n>: ikki parallel sariq to'sin (lokal +X bo'ylab), sharnir, qora gidravlik tirgak
    t = []
    for dz in (0.0, 0.32):
        t.append(box((ARM_L, 0.12, 0.12), (ARM_L / 2, 0, dz), 'yellow'))
    for k in range(4):
        x = 0.3 + k * (ARM_L - 0.5) / 3
        t.append(box((0.08, 0.1, 0.32), (x, 0, 0.16), 'yellow'))
    t.append(cyl(0.12, 0.3, (0, 0, 0), 'dark', 8, (math.pi / 2, 0, 0)))
    t.append(beam((1.2, 0, 0.32), (-0.15, 0, 1.6), 0.09, 0.09, 'dark'))            # gidravlik tirgak
    t.append(beam((0.2, 0, 1.25), (-0.15, 0, 1.6), 0.05, 0.05, 'steel'))
    tilt = join(f'tilt{n}', t)
    tilt.parent = arm
    tilt.location = (0, 0, 0)
    tilt.rotation_euler = (0, REST, 0)   # Blender'da +Y atrofida musbat burchak — uchi pastga

    hang = join(f'hang{n}', plane(*PLANES[n]))
    hang.parent = tilt
    hang.location = (ARM_L, 0, 0.1)
    hang.rotation_euler = (0, -REST, 0)  # qo'l og'ishini qaytaradi — samolyot gorizontal

objs = [o for o in scene.objects if o.type == 'MESH']
tris = sum(len(pg.vertices) - 2 for o in objs for pg in o.data.polygons)
bpy.context.view_layer.update()
top = max((o.matrix_world @ v.co).z for o in objs for v in o.data.vertices)
xmax = max(abs((o.matrix_world @ v.co).x) for o in objs for v in o.data.vertices)
print(f'JUNIOR_JET tris={tris} top={top:.2f} width={2 * xmax:.2f}')

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'JUNIOR_JET glb={OUT_GLB.stat().st_size // 1024} KB')

# ---------- Preview (ikki qo'l ko'tarilgan) ----------
for o in objs:
    if o.name in ('tilt1', 'tilt4'):
        o.rotation_euler.y = REST - math.radians(30)
        o.children[0].rotation_euler.y = -(REST - math.radians(30))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.location = (7.5, -10.0, 6.5)
cam.rotation_euler = (Vector((0, 0, 1.6)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
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
print('JUNIOR_JET preview', scene.render.filepath)

"""
27 — Аттракцион "Windstarz" (Windstar). Low-poly model, rasm: attraction-images-park/Windstar_Z.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/27-windstarz/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png

Tuzilish (xarita kodi shu nomlarga tayanadi, src/map/GltfModel.tsx):
    base       — qimirlamaydigan qism: dumaloq maydon (qizil-oq chet), panjara, yo'l-yo'l konus
    rotor      — aylanadigan qism: ko'k ustun, "WINDSTAR" halqasi, gumbaz, sariq yoylar, "W"
    arm0..5    — qo'l uyasi (bo'sh tugun, rotor bolasi): qo'l yo'nalishi
    tilt0..5   — sariq qo'l (arm bolasi): origin — sharnirda, ko'tariladi/tushadi (lokal Z atrofida)
    hang0..5   — qo'l uchidagi ikki o'rindiqli savatlar va soyabonlar (tilt bolasi): doim tik turadi
Asl o'lcham metrda: diametri ~16.8 m, balandligi ~9.6 m.
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
    'red': (0.85, 0.07, 0.07), 'white': (0.95, 0.95, 0.95), 'blue': (0.06, 0.2, 0.62), 'yellow': (0.98, 0.72, 0.08),
    'orange': (0.96, 0.55, 0.1), 'floor': (0.28, 0.28, 0.3), 'fence': (0.55, 0.57, 0.6), 'steel': (0.75, 0.76, 0.78),
    'c_red': (0.95, 0.15, 0.12), 'c_blue': (0.1, 0.35, 0.9), 'c_yellow': (0.98, 0.78, 0.35),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.45
    if name == 'steel':
        bsdf.inputs['Metallic'].default_value = 0.3  # xaritada atrof-muhit aksi yo'q — yuqori metallik qoraygan ko'rinadi
    m.diffuse_color = (*rgb, 1)
    MATS[name] = m


def new_obj(name, bm, mats):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(MATS[m])
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob


def box(name, size, loc, mat, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return new_obj(name, bm, [mat])


def cyl(name, r, h, loc, mat, segs=10, rot=(0, 0, 0), r2=None):
    """Silindr: markazi loc, o'qi Z (rot bilan buriladi)"""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return new_obj(name, bm, [mat])


def lathe(name, profile, segs, mat_of, mats):
    """Aylanma jism: profile [(radius, z), ...] pastdan tepaga; mat_of(i, k) — material indeksi"""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r < 1e-6:
            v = bm.verts.new((0, 0, z))
            rings.append([v] * segs)
        else:
            rings.append([bm.verts.new((r * math.cos(2 * math.pi * k / segs), r * math.sin(2 * math.pi * k / segs), z))
                          for k in range(segs)])
    for i in range(len(profile) - 1):
        for k in range(segs):
            k2 = (k + 1) % segs
            vs = []
            for v in (rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]):
                if v not in vs:
                    vs.append(v)
            if len(vs) >= 3:
                bm.faces.new(vs).material_index = mat_of(i, k)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return new_obj(name, bm, mats)


def beam(name, a, b, w, d, mat):
    a, b = Vector(a), Vector(b)
    v = b - a
    ob = box(name, (v.length, w, d), (0, 0, 0), mat)
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
R, H0 = 8.4, 0.35
p = []
# dumaloq maydon: chetida qizil-oq bo'laklar, usti to'q kulrang
p.append(lathe('rim', [(R, 0), (R, H0), (R - 0.01, H0)], 32, lambda i, k: k % 2, ['red', 'white']))
p.append(lathe('floor', [(R - 0.01, H0), (0, H0)], 32, lambda i, k: 0, ['floor']))
# panjara: ustunlar va ikki qator to'siq (oldida kirish)
FH = 1.05
for k in range(32):
    a0, a1 = 2 * math.pi * k / 32, 2 * math.pi * (k + 1) / 32
    if abs(((a0 + a1) / 2) - 3 * math.pi / 2) < 0.15:  # janub (old) — kirish
        continue
    r = R - 0.2
    x0, y0, x1, y1 = r * math.cos(a0), r * math.sin(a0), r * math.cos(a1), r * math.sin(a1)
    p.append(cyl('post', 0.03, FH, (x0, y0, H0 + FH / 2), 'fence', 6))
    for z in (H0 + 0.1, H0 + FH / 2, H0 + FH - 0.03):
        p.append(beam('rail', (x0, y0, z), (x1, y1, z), 0.03, 0.03, 'fence'))
# markaziy konus: qizil-oq tik yo'llar, pastida qizil-oq halqa
p.append(lathe('cone_ring', [(3.3, H0), (3.3, H0 + 0.12), (2.6, H0 + 0.12)], 24, lambda i, k: k % 2, ['red', 'white']))
p.append(lathe('cone', [(2.5, H0 + 0.12), (1.9, 1.5), (1.25, 2.9), (1.05, 3.3), (0, 3.3)], 20,
               lambda i, k: k % 2, ['red', 'white']))
base = join('base', p)

# ---------- ROTOR: ustun, halqa, gumbaz, yoylar ----------
HINGE_Z, HINGE_R = 4.4, 1.35
q = []
q.append(cyl('column', 0.85, 2.6, (0, 0, 3.3 + 1.3), 'blue', 12))
q.append(cyl('drum', 1.05, 0.9, (0, 0, HINGE_Z), 'yellow', 12))            # sharnirlar o'rnatilgan baraban
q.append(lathe('bowl', [(0.85, 5.3), (1.5, 5.9), (1.85, 6.4), (0, 6.4)], 16, lambda i, k: 0, ['yellow']))
q.append(lathe('band', [(1.9, 6.35), (1.9, 6.85), (1.85, 6.85)], 24, lambda i, k: 0 if k % 4 else 1, ['red', 'yellow']))
q.append(lathe('dome', [(1.55, 6.85), (1.5, 7.3), (1.25, 7.75), (0.8, 8.1), (0, 8.25)], 16, lambda i, k: 0, ['blue']))
for k in range(4):  # sariq yoylar gumbaz ustida
    a = k * math.pi / 4
    pts = [(math.cos(t) * 1.75, math.sin(t) * 1.75 + 6.85) for t in [math.pi * j / 10 for j in range(11)]]
    for (u0, z0), (u1, z1) in zip(pts[:-1], pts[1:]):
        q.append(beam('arch', (u0 * math.cos(a), u0 * math.sin(a), z0), (u1 * math.cos(a), u1 * math.sin(a), z1),
                      0.16, 0.12, 'yellow'))
q.append(cyl('crown', 0.25, 0.35, (0, 0, 8.75), 'orange', 10))
q.append(box('W', (0.7, 0.12, 0.6), (0, 0, 9.25), 'red'))
for k in range(6):  # "WINDSTAR" halqasidagi yulduz belgilari
    a = k * math.pi / 3 + math.pi / 6
    q.append(box('star', (0.3, 0.06, 0.3), (math.cos(a) * 1.93, math.sin(a) * 1.93, 6.6), 'yellow', (0, 0, a + math.pi / 2)))
rotor = join('rotor', q)

# ---------- Qo'llar ----------
ARM_L = 5.0
REST = math.radians(28)     # tinch holatda qo'l pastga shuncha og'gan
CANOPY_COLS = ['c_red', 'c_blue', 'c_yellow']


def double_seat(name_, loc, yaw):
    """Ikki o'rindiqli qizil savat, markazi loc, old tomoni yaw yo'nalishida"""
    s = []
    for off in (-0.3, 0.3):
        x = loc[0] + math.cos(yaw + math.pi / 2) * off
        y = loc[1] + math.sin(yaw + math.pi / 2) * off
        s.append(box(name_ + 'pan', (0.45, 0.45, 0.08), (x, y, loc[2]), 'red', (0, 0, yaw)))
        s.append(box(name_ + 'back', (0.08, 0.45, 0.55), (x - math.cos(yaw) * 0.22, y - math.sin(yaw) * 0.22, loc[2] + 0.28),
                     'red', (0, 0, yaw)))
    s.append(box(name_ + 'frame', (0.5, 1.2, 0.05), (loc[0], loc[1], loc[2] - 0.08), 'steel', (0, 0, yaw)))
    return s


for n in range(6):
    yaw = n * math.pi / 3
    # arm<n>: bo'sh tugun — sharnir joyi va qo'l yo'nalishi (rotor bolasi)
    arm = bpy.data.objects.new(f'arm{n}', None)
    scene.collection.objects.link(arm)
    arm.parent = rotor
    arm.location = (math.cos(yaw) * HINGE_R, math.sin(yaw) * HINGE_R, HINGE_Z)
    arm.rotation_euler = (0, 0, yaw)

    # tilt<n>: qo'l lokal +X bo'ylab, origin — sharnirda
    t = [box('beam', (ARM_L, 0.28, 0.32), (ARM_L / 2, 0, 0), 'yellow')]
    t.append(cyl('hinge', 0.32, 0.5, (0, 0, 0), 'red', 10, (math.pi / 2, 0, 0)))
    t.append(cyl('disc', 0.55, 0.1, (0.6, 0.0, 0.0), 'orange', 12, (math.pi / 2, 0, 0)))
    t.append(beam('ram', (0.25, 0, -0.8), (1.6, 0, -0.15), 0.12, 0.12, 'blue'))   # gidravlik tirgak
    for k in range(6):  # chiroqchalar
        t.append(box('dot', (0.06, 0.3, 0.06), (0.8 + k * 0.7, 0, 0.19), 'white'))
    tilt = join(f'tilt{n}', t)
    tilt.parent = arm
    tilt.location = (0, 0, 0)
    tilt.rotation_euler = (0, REST, 0)   # Blender'da +Y atrofida musbat burchak — uchi pastga

    # hang<n>: qo'l uchida, tik turadi; ko'ndalang to'sin, ikki ustun, soyabonlar, savatlar
    h = [box('cross', (0.14, 2.6, 0.14), (0, 0, 0), 'yellow')]
    for side in (-1, 1):
        y = side * 1.2
        h.append(cyl('pole', 0.04, 3.0, (0, y, -0.6), 'steel', 6))
        # soyabon: 4 bo'lakli qiya kvadrat (piramida)
        col = CANOPY_COLS[(n * 2 + (side > 0)) % 3]
        bm = bmesh.new()
        c = bm.verts.new((0, y, 1.25))
        cs = [bm.verts.new((dx * 1.05, y + dy * 1.05, 0.95)) for dx, dy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
        for k in range(4):
            bm.faces.new([c, cs[k], cs[(k + 1) % 4]])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        h.append(new_obj('canopy', bm, [col]))
        h.extend(double_seat('seat', (0, y, -1.75), 0.0))
    hang = join(f'hang{n}', h)
    hang.parent = tilt
    hang.location = (ARM_L, 0, 0)
    hang.rotation_euler = (0, -REST, 0)  # qo'l og'ishini qaytaradi — savat tik

tris = sum(len(pg.vertices) - 2 for o in scene.objects if o.type == 'MESH' for pg in o.data.polygons)
print(f'WINDSTAR tris={tris}')

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'WINDSTAR glb={OUT_GLB.stat().st_size // 1024} KB')

# ---------- Preview ----------
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.location = (15, -21, 14)
cam.rotation_euler = (Vector((0, 0, 3.5)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 1000, 900
world = bpy.data.worlds.new('w')
world.color = (0.93, 0.95, 0.98)
scene.world = world
scene.render.filepath = str(PREVIEW_DIR / 'preview.png')
bpy.ops.render.render(write_still=True)
print('WINDSTAR preview', scene.render.filepath)

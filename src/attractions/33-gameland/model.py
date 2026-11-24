"""
33 — Аттракцион "Gameland" (o'yin zali binosi). Rasmlar: attraction-images-park/gameland2.png, gameland3.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/33-gameland/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png

Tuzilish: base — butun bino (qimirlamaydi). Plandagi bino shakli 23.9 × 10.7 m — uzun o'qi Blender Y bo'ylab,
kirish (frontondagi "GAMELAND" yozuvi, eshik, afishalar) — qisqa tomonda, -Y (old). Balandligi ~7.6 m.
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
    'navy': (0.07, 0.12, 0.42), 'navy2': (0.1, 0.17, 0.52), 'orange': (0.85, 0.3, 0.05), 'roof': (0.36, 0.39, 0.43),
    'ridge': (0.28, 0.3, 0.33), 'concrete': (0.78, 0.76, 0.72), 'black': (0.03, 0.03, 0.04), 'poster': (0.06, 0.2, 0.16),
    'yellow': (0.98, 0.85, 0.1), 'glow': (1.0, 0.45, 0.1),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.6
    if name in ('glow', 'yellow'):
        bsdf.inputs['Emission Color'].default_value = (*rgb, 1)
        bsdf.inputs['Emission Strength'].default_value = 0.6 if name == 'glow' else 0.3
    m.diffuse_color = (*rgb, 1)
    MATS[name] = m


def obj(bm, mat):
    me = bpy.data.meshes.new('m')
    bm.to_mesh(me)
    bm.free()
    me.materials.append(MATS[mat])
    ob = bpy.data.objects.new('o', me)
    scene.collection.objects.link(ob)
    return ob


def box(size, loc, mat, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return obj(bm, mat)


def poly_prism(pts_xz, y0, y1, mat):
    """XZ tekislikdagi ko'pburchak (frontonlar), Y bo'ylab y0..y1 qalinlikda"""
    bm = bmesh.new()
    a = [bm.verts.new((x, y0, z)) for x, z in pts_xz]
    b = [bm.verts.new((x, y1, z)) for x, z in pts_xz]
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    n = len(pts_xz)
    for k in range(n):
        bm.faces.new([a[k], b[k], b[(k + 1) % n], a[(k + 1) % n]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj(bm, mat)


def cyl(r, h, loc, mat, segs=20, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=h)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return obj(bm, mat)


# ---------- O'lchamlar (plandagi shakl: 10.7 × 23.9 m) ----------
W, L = 10.7, 23.9
WALL_W, WALL_L = W - 1.6, L - 1.6    # devorlar — beton yo'lak ichida
H = 4.3                              # devor balandligi
OV = 0.9                             # tom karnizi chiqishi
RIDGE = 3.0                          # kulrang qiya tomning devordan baland qismi
p = []
# beton yo'lak (apron)
p.append(box((W, L, 0.15), (0, 0, 0.075), 'concrete'))
# devorlar va tik qovurg'alar (gofrirovka)
p.append(box((WALL_W, WALL_L, H), (0, 0, 0.15 + H / 2), 'navy'))
for sx in (-1, 1):
    n = int(WALL_L / 0.45)
    for k in range(n):
        y = -WALL_L / 2 + 0.22 + k * 0.45
        p.append(box((0.06, 0.12, H - 0.1), (sx * (WALL_W / 2 + 0.03), y, 0.15 + H / 2), 'navy2'))
    # to'q sariq ustunlar (karniz tayanchlari) har ~4.5 m da
    for k in range(6):
        y = -WALL_L / 2 + 0.6 + k * (WALL_L - 1.2) / 5
        p.append(box((0.22, 0.22, H), (sx * (WALL_W / 2 + OV - 0.15), y, 0.15 + H / 2), 'orange'))
# to'q sariq karniz (tekis "qobiq", butun bino atrofida) — qalin chet
TZ = 0.15 + H
p.append(box((WALL_W + 2 * OV, WALL_L + 2 * OV, 0.75), (0, 0, TZ + 0.2), 'orange'))
# kulrang ikki qiyali tom (qiya yuzlar), tizma to'sini
half = (WALL_W - 0.6) / 2
pitch = math.atan2(RIDGE, half)
slope = math.hypot(half, RIDGE)
for sx in (-1, 1):
    p.append(box((slope, WALL_L - 0.4, 0.12), (sx * half / 2, 0, TZ + 0.55 + RIDGE / 2), 'roof', (0, sx * pitch, 0)))
    # qiya yuzdagi chiziqlar (profil list)
    for k in range(10):
        y = -WALL_L / 2 + 0.8 + k * (WALL_L - 1.6) / 9
        p.append(box((slope, 0.06, 0.04), (sx * half / 2, y, TZ + 0.63 + RIDGE / 2), 'ridge', (0, sx * pitch, 0)))
p.append(box((0.3, WALL_L - 0.2, 0.25), (0, 0, TZ + 0.6 + RIDGE), 'ridge'))
# frontonlar (old va orqa uchburchak — ko'k)
for sy, front in ((-1, True), (1, False)):
    y = sy * (WALL_L / 2 + 0.02)
    p.append(poly_prism([(-half - 0.2, TZ + 0.55), (half + 0.2, TZ + 0.55), (0, TZ + 0.55 + RIDGE + 0.1)], y - 0.05 * sy, y + 0.05 * sy, 'navy'))
# old (-Y) fasad: katta ko'k uchburchak panel (yerdan tomgacha), to'q sariq doira, GAMELAND, eshik, afishalar
FY = -WALL_L / 2 - 0.12
p.append(poly_prism([(-3.3, 0.15), (3.3, 0.15), (0, TZ + 0.55 + RIDGE + 0.4)], FY - 0.08, FY + 0.08, 'navy2'))
p.append(cyl(0.95, 0.12, (0, FY - 0.12, TZ + 1.6), 'orange', 24, (math.pi / 2, 0, 0)))
p.append(cyl(0.8, 0.13, (0, FY - 0.13, TZ + 1.6), 'navy', 24, (math.pi / 2, 0, 0)))
for k in range(8):  # "GAMELAND" — yonib turgan to'q sariq harflar o'rnida bloklar
    p.append(box((0.32, 0.06, 0.45), (-1.3 + k * 0.37, FY - 0.17, 3.45), 'glow'))
# eshik: to'q sariq rom, qora o'rta
p.append(box((1.9, 0.1, 2.9), (0, FY - 0.15, 0.15 + 1.45), 'orange'))
p.append(box((1.5, 0.12, 2.6), (0, FY - 0.18, 0.15 + 1.3), 'black'))
# afishalar: to'q yashil fonda sariq "GAME LAND"
for sx in (-1, 1):
    x = sx * 2.0
    p.append(box((1.3, 0.08, 2.0), (x, FY - 0.15, 1.5), 'poster'))
    for row, z in enumerate((2.05, 1.7)):
        p.append(box((0.95, 0.09, 0.22), (x, FY - 0.17, z), 'yellow'))
    for k in range(5):
        p.append(box((1.1, 0.09, 0.03), (x, FY - 0.17, 0.75 + k * 0.12), 'navy2'))

bpy.ops.object.select_all(action='DESELECT')
for o in p:
    o.select_set(True)
bpy.context.view_layer.objects.active = p[0]
bpy.ops.object.join()
base = bpy.context.view_layer.objects.active
base.name = base.data.name = 'base'
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

tris = sum(len(pg.vertices) - 2 for pg in base.data.polygons)
print(f'GAMELAND tris={tris} size={base.dimensions.x:.1f}x{base.dimensions.y:.1f}x{base.dimensions.z:.1f}')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'GAMELAND glb={OUT_GLB.stat().st_size // 1024} KB')

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.location = (14, -26, 12)
cam.rotation_euler = (Vector((0, -3, 3)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 1000, 800
world = bpy.data.worlds.new('w')
world.color = (0.93, 0.95, 0.98)
scene.world = world
scene.render.filepath = str(PREVIEW_DIR / 'preview.png')
bpy.ops.render.render(write_still=True)
print('GAMELAND preview', scene.render.filepath)

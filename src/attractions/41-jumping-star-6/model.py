"""
41 — Аттракцион "Jumping star 6" (Jumpin' Star). Low-poly model, rasm: attraction-images-park/jumping.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/41-jumping-star-6/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png

Tuzilish (xarita kodi shu nomlarga tayanadi, src/map/GltfModel.tsx):
    base  — qimirlamaydigan qism: poydevor, panjara, minora, yulduzlar, chiroq yoylari, fonus
    lift0 — 6 o'rindiqli arava: minora bo'ylab ko'tarilib-tushadi
Asl o'lcham metrda: poydevor 4.8 × 4.8 m, balandligi ~10 m. Old tomoni (o'rindiqlar qaragan) — Blender'da -Y.
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

# ---------- Materiallar ----------
PALETTE = {
    'yellow': (0.98, 0.72, 0.05), 'gold': (0.85, 0.62, 0.18), 'red': (0.85, 0.06, 0.06), 'orange': (0.98, 0.35, 0.04),
    'blue': (0.06, 0.18, 0.62), 'pink': (0.95, 0.45, 0.75), 'purple': (0.55, 0.2, 0.85), 'deck': (0.72, 0.62, 0.45),
    'soil': (0.36, 0.25, 0.16), 'dark': (0.12, 0.11, 0.1), 'glass': (0.95, 0.85, 0.55),
}
GLOW = {'pink', 'purple', 'glass'}  # chiroq yoylari va fonus — biroz o'zidan yorug'lik chiqaradi
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.5
    if name == 'gold':
        bsdf.inputs['Metallic'].default_value = 0.3  # xaritada atrof-muhit aksi yo'q — yuqori metallik qoraygan ko'rinadi
    if name in GLOW:
        bsdf.inputs['Emission Color'].default_value = (*rgb, 1)
        bsdf.inputs['Emission Strength'].default_value = 0.6
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


def cyl(name, r, h, loc, mat, segs=8):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=h)
    bmesh.ops.translate(bm, vec=(loc[0], loc[1], loc[2] + h / 2), verts=bm.verts)
    return new_obj(name, bm, [mat])


def star(name, r_out, depth, loc, mat, r_in_k=0.45, rot_y=0.0):
    """Besh qirrali yulduz, XZ tekisligida tik turadi (old tomoni -Y), qalinligi depth"""
    pts = []
    for k in range(10):
        a = math.pi / 2 + k * math.pi / 5
        r = r_out if k % 2 == 0 else r_out * r_in_k
        pts.append((r * math.cos(a), r * math.sin(a)))
    bm = bmesh.new()
    front = [bm.verts.new((x, -depth / 2, z)) for x, z in pts]
    back = [bm.verts.new((x, depth / 2, z)) for x, z in pts]
    c_f, c_b = bm.verts.new((0, -depth / 2, 0)), bm.verts.new((0, depth / 2, 0))
    for k in range(10):
        k2 = (k + 1) % 10
        bm.faces.new([c_f, front[k2], front[k]])
        bm.faces.new([c_b, back[k], back[k2]])
        bm.faces.new([front[k], front[k2], back[k2], back[k]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler((0, rot_y, 0), 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return new_obj(name, bm, [mat])


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
S = 4.8            # poydevor tomoni
H0 = 0.4           # poydevor balandligi (tuproq + pol)
TOWER_Y = 0.9      # minora markazi (orqa tomonga surilgan)
TOWER_H = 7.6      # minora balandligi poydevordan
p = []
p.append(box('soil', (S, S, H0 - 0.06), (0, 0, (H0 - 0.06) / 2), 'soil'))
p.append(box('deck', (S - 0.08, S - 0.08, 0.06), (0, 0, H0 - 0.03), 'deck'))

# Panjara: oltin rang ustun va to'siqlar, ko'k burchak ustunlari; old tomonda kirish ochiq
FH = 1.05
edge = S / 2 - 0.12
sides = [((-edge, -edge), (edge, -edge)), ((edge, -edge), (edge, edge)), ((-edge, edge), (-edge, -edge))]
for (x0, y0), (x1, y1) in sides:
    L = math.hypot(x1 - x0, y1 - y0)
    ang = math.atan2(y1 - y0, x1 - x0)
    n = int(L / 0.16)
    gap = (x0 == -edge and y0 == -edge and y1 == -edge)  # old tomon: o'rtada 1.2 m kirish
    for k in range(n + 1):
        t = k / n
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        if gap and abs(x) < 0.6:
            continue
        p.append(cyl('bar', 0.018, FH, (x, y, H0), 'gold', 5))
    for z in (H0 + 0.08, H0 + FH - 0.02):
        if gap:
            for sx in (-1, 1):
                seg = (L / 2 - 0.6)
                p.append(box('rail', (seg, 0.04, 0.04), (sx * (0.6 + seg / 2), y0, z), 'gold'))
        else:
            p.append(box('rail', (L, 0.04, 0.04), ((x0 + x1) / 2, (y0 + y1) / 2, z), 'gold', (0, 0, ang)))
for x in (-edge, edge):
    for y in (-edge, edge):
        p.append(box('cpost', (0.09, 0.09, FH + 0.06), (x, y, H0 + (FH + 0.06) / 2), 'blue'))
for sx in (-0.6, 0.6):  # kirish ustunlari
    p.append(box('gpost', (0.08, 0.08, FH + 0.06), (sx, -edge, H0 + (FH + 0.06) / 2), 'blue'))

# Minora: sariq, old yuzida ko'k yulduzchalar; tepasida qopqoq
p.append(box('tower', (0.75, 0.6, TOWER_H), (0, TOWER_Y, H0 + TOWER_H / 2), 'yellow'))
p.append(box('rail_l', (0.08, 0.1, TOWER_H - 0.6), (-0.3, TOWER_Y - 0.33, H0 + TOWER_H / 2), 'gold'))
p.append(box('rail_r', (0.08, 0.1, TOWER_H - 0.6), (0.3, TOWER_Y - 0.33, H0 + TOWER_H / 2), 'gold'))
p.append(box('cap', (0.95, 0.8, 0.35), (0, TOWER_Y, H0 + TOWER_H + 0.17), 'yellow'))
for k, z in enumerate([2.2, 3.1, 4.0, 4.9, 5.8, 6.7]):
    p.append(star('tstar', 0.09, 0.02, ((-0.12 if k % 2 else 0.12), TOWER_Y - 0.31, H0 + z), 'blue'))

# Ikki yonda S-shaklidagi chiroq yoylari (pastdan tepaga rang o'zgaradi) va yulduzlar
ARC_COLS = ['blue', 'purple', 'pink', 'pink', 'purple', 'blue', 'purple', 'pink']
for side in (-1, 1):
    for k in range(16):
        t = k / 15
        z = H0 + 2.4 + t * 3.9
        x = side * (0.62 + 0.28 * math.sin(t * math.pi * 1.5))
        col = ARC_COLS[k % len(ARC_COLS)] if side < 0 else ['orange', 'pink', 'purple', 'pink'][k % 4]
        p.append(box('arc', (0.16, 0.16, 0.3), (x, TOWER_Y - 0.15, z), col, (0, side * 0.25 * math.cos(t * math.pi * 1.5), 0)))
    for k, z in enumerate([2.2, 4.1, 6.4]):
        col = 'pink' if (side < 0 and k != 2) else 'yellow'
        p.append(star('sstar', 0.32, 0.08, (side * (0.95 + 0.1 * (k % 2)), TOWER_Y - 0.2, H0 + z), col))

# Tepadagi katta yulduz: qizil chet + sariq yulduz va "JUMPIN' STAR" o'rnida rangli chiroqlar qatori
TOP = H0 + TOWER_H + 1.25
p.append(star('bigstar_back', 1.25, 0.12, (0, TOWER_Y + 0.02, TOP), 'red'))
p.append(star('bigstar', 1.1, 0.16, (0, TOWER_Y - 0.02, TOP), 'yellow'))
for k, col in enumerate(['red', 'orange', 'pink', 'blue', 'purple', 'red']):
    p.append(box('sign', (0.2, 0.06, 0.24), (-0.55 + k * 0.22, TOWER_Y - 0.14, TOP + 0.15), col))
for k, col in enumerate(['orange', 'red', 'red', 'orange']):
    p.append(box('sign2', (0.2, 0.06, 0.22), (-0.33 + k * 0.22, TOWER_Y - 0.14, TOP - 0.2), col))

# Fonus (o'ng old burchakda) va boshqaruv qutisi
p.append(cyl('lamp_pole', 0.03, 1.9, (edge - 0.25, -edge + 0.9, H0), 'dark', 6))
p.append(box('lamp_arm', (0.3, 0.03, 0.03), (edge - 0.37, -edge + 0.9, H0 + 1.9), 'dark'))
p.append(cyl('lamp', 0.1, 0.25, (edge - 0.5, -edge + 0.9, H0 + 1.6), 'glass', 6))
p.append(box('ctrl', (0.3, 0.35, 0.9), (edge - 0.35, 0.1, H0 + 0.45), 'blue'))
p.append(box('ctrl_top', (0.31, 0.36, 0.12), (edge - 0.35, 0.1, H0 + 0.96), 'red'))

base = join('base', p)

# ---------- LIFT0: 6 o'rindiqli arava (pastki holatda) ----------
q = []
CZ = H0 + 0.55  # arava o'rindig'i balandligi pastda
q.append(box('panel', (3.3, 0.35, 1.0), (0, TOWER_Y - 0.55, CZ + 0.2), 'blue'))
q.append(box('panel_top', (3.4, 0.4, 0.14), (0, TOWER_Y - 0.55, CZ + 0.76), 'red'))
for k in range(6):  # tepadagi uchburchak "toj" bezaklari
    q.append(box('crown', (0.22, 0.05, 0.22), (-1.4 + k * 0.56, TOWER_Y - 0.74, CZ + 0.92), 'yellow', (0, math.pi / 4, 0)))
SEAT_COLS = ['yellow', 'orange', 'red', 'red', 'orange', 'yellow']
for k, col in enumerate(SEAT_COLS):
    x = -1.32 + k * 0.53
    q.append(box('seat', (0.44, 0.42, 0.09), (x, TOWER_Y - 0.95, CZ - 0.05), col))     # o'tirgich
    q.append(box('back', (0.44, 0.09, 0.72), (x, TOWER_Y - 0.78, CZ + 0.3), col))     # suyanchiq
    q.append(box('bar', (0.4, 0.03, 0.03), (x, TOWER_Y - 1.17, CZ + 0.2), 'gold'))    # qo'l to'sig'i
q.append(box('frame', (0.9, 0.35, 1.3), (0, TOWER_Y - 0.35, CZ + 0.15), 'yellow'))  # minoraga ilinadigan qism
lift = join('lift0', q)

tris = sum(len(pg.vertices) - 2 for o in scene.objects if o.type == 'MESH' for pg in o.data.polygons)
top = max(o.location.z + o.dimensions.z for o in (base, lift))
print(f'JUMPING_STAR tris={tris} size={base.dimensions.x:.2f}x{base.dimensions.y:.2f}x{base.dimensions.z:.2f}')

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'JUMPING_STAR glb={OUT_GLB.stat().st_size // 1024} KB')

# ---------- Preview render ----------
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.location = (9.5, -11.5, 8.0)
cam.rotation_euler = (Vector((0, 0.3, 4.6)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 800, 1000
world = bpy.data.worlds.new('w')
world.color = (0.93, 0.95, 0.98)
scene.world = world
scene.render.filepath = str(PREVIEW_DIR / 'preview.png')
bpy.ops.render.render(write_still=True)
print('JUMPING_STAR preview', scene.render.filepath)

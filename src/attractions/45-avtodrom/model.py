"""
45 — Аттракцион "Автодром" (bamper-mashinalar). Namuna: foydalanuvchi skrinshoti (tomli arena, yo'l-yo'l chodir cheti).

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/45-avtodrom/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, track.json, preview.png

Tuzilish (xarita kodi: src/map/GltfModel.tsx):
    base       — beton supa, qora arena (bortli), ustunlar, kulrang tom, ko'k-oq-qizil chodir cheti, chiroqlar,
                 ship to'ri (tok tarmog'i), sariq panjara; kirish — orqa (+Y) uzun tomonning +X chetida, zinali
    car0..car7 — bamper-mashinalar (sariq va ko'k gumbazli, orqasida tok ustuni): track.json dagi oval bo'ylab
Asl o'lcham: 28 × 16 m (plandagi maydoncha), balandligi ~5.2 m. Uzun o'qi — X, old tomoni (zina) — Blender'da -Y.
"""
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Euler, Vector

HERE = Path(__file__).resolve().parent
OUT_GLB = HERE / 'model.glb'
OUT_BLEND = HERE / 'model.blend'
OUT_TRACK = HERE / 'track.json'
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PREVIEW_DIR = Path(argv[0]) if argv else HERE

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

PALETTE = {
    'concrete': (0.66, 0.65, 0.62), 'floor': (0.06, 0.06, 0.07), 'rubber': (0.08, 0.08, 0.09), 'roof': (0.96, 0.97, 0.98),
    'steel': (0.65, 0.66, 0.68), 'blue': (0.1, 0.2, 0.62), 'white': (0.95, 0.95, 0.95), 'red': (0.62, 0.08, 0.08),
    'gold': (0.78, 0.58, 0.15), 'yellow': (0.92, 0.68, 0.05), 'navy': (0.08, 0.15, 0.5), 'black': (0.03, 0.03, 0.04),
    'bulb': (1.0, 0.95, 0.8), 'stripe': (0.9, 0.62, 0.05),
}
ROOF_ALPHA = 0.45
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.5
    if name in ('steel', 'gold'):
        bsdf.inputs['Metallic'].default_value = 0.3  # xaritada atrof-muhit aksi yo'q — yuqori metallik qoraygan ko'rinadi
    if name == 'bulb':
        bsdf.inputs['Emission Color'].default_value = (*rgb, 1)
        bsdf.inputs['Emission Strength'].default_value = 1.2
    if name == 'roof':  # oq shaffof tom (polikarbonat) — ichidagi arena ko'rinib turadi
        bsdf.inputs['Alpha'].default_value = ROOF_ALPHA
        m.surface_render_method = 'BLENDED'
    m.diffuse_color = (*rgb, ROOF_ALPHA if name == 'roof' else 1)
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


def cyl(r, h, loc, mat, segs=10, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=h)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return obj(bm, mat)


def dome(r, loc, mat, scale=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=6, radius=r)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-4], context='VERTS')
    bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return obj(bm, mat)


def tube(a, b, r, mat, segs=6):
    a, b = Vector(a), Vector(b)
    v = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=segs, radius1=r, radius2=r, depth=v.length)
    ob = obj(bm, mat)
    ob.rotation_euler = v.to_track_quat('Z', 'Y').to_euler()
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


W, D = 28.0, 16.0
AW, AD = 21.0, 11.5      # arena (qora pol)
AX, AY = 1.6, 0.6        # arena markazi (chapda zina va budka uchun joy)
FZ = 0.55                # arena poli balandligi
H = 4.6                  # tom osti balandligi

p = []
p.append(box((W, D, 0.15), (0, 0, 0.075), 'concrete'))
p.append(box((AW + 0.6, AD + 0.6, FZ - 0.15), (AX, AY, 0.15 + (FZ - 0.15) / 2), 'concrete'))
p.append(box((AW, AD, 0.04), (AX, AY, FZ), 'floor'))
# bort (rezina bamper) arena cheti bo'ylab, ustida sariq chiziq
for (sx, sy, lx, ly) in ((0, -1, AW, 0.25), (0, 1, AW, 0.25), (-1, 0, 0.25, AD), (1, 0, 0.25, AD)):
    x = AX + sx * AW / 2
    y = AY + sy * AD / 2
    p.append(box((lx, ly, 0.35), (x, y, FZ + 0.17), 'rubber'))
    p.append(box((lx + 0.01, ly + 0.01, 0.05), (x, y, FZ + 0.3), 'stripe'))
# ustunlar (kumush) va kulrang tom
cols_x = [AX - AW / 2 + k * AW / 4 for k in range(5)]
GATE_X1 = AX + AW / 2 - 0.6   # kirish: orqa uzun tomon, +X chetida
GATE_X0 = GATE_X1 - 2.4
for x in cols_x:
    for sy in (-1, 1):
        p.append(cyl(0.12, H, (x, AY + sy * (AD / 2 + 0.35), FZ + H / 2), 'steel', 8))
RW, RD = AW + 2.0, AD + 2.0
p.append(box((RW, RD, 0.2), (AX, AY, FZ + H + 0.1), 'roof'))
# tomning qiya ustki qismi (past piramida)
bm = bmesh.new()
c = [bm.verts.new((AX + sx * RW / 2, AY + sy * RD / 2, FZ + H + 0.2)) for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
t = [bm.verts.new((AX + sx * RW / 4, AY + sy * 0.3, FZ + H + 1.0)) for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
for k in range(4):
    bm.faces.new([c[k], c[(k + 1) % 4], t[(k + 1) % 4], t[k]])
bm.faces.new(t)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
p.append(obj(bm, 'roof'))
# chodir cheti (valans): ko'k-oq-qizil-oq yo'llar, pastki qirrasi tishli, ostida chiroqlar
STR = ['blue', 'white', 'red', 'white']
VH = 0.75
for sy, lx, ly in ((-1, RW, 0), (1, RW, 0), (-1, 0, RD), (1, 0, RD)):
    along_x = lx > 0
    L = lx if along_x else ly
    n = int(L / 0.85)
    for k in range(n):
        u = -L / 2 + (k + 0.5) * L / n
        x = AX + (u if along_x else sy * RW / 2)
        y = AY + (sy * RD / 2 if along_x else u)
        size = (L / n, 0.06, VH) if along_x else (0.06, L / n, VH)
        p.append(box(size, (x, y, FZ + H - VH / 2 + 0.1), STR[k % 4]))
        tooth = (L / n * 0.5, 0.07, 0.18) if along_x else (0.07, L / n * 0.5, 0.18)
        p.append(box(tooth, (x, y, FZ + H - VH - 0.0), 'black'))
        p.append(cyl(0.06, 0.06, (x, y, FZ + H - VH - 0.15), 'bulb', 6))
# ship ostidagi tok to'ri (kulrang panjara)
for k in range(9):
    x = AX - AW / 2 + k * AW / 8
    p.append(tube((x, AY - AD / 2, FZ + H - 0.1), (x, AY + AD / 2, FZ + H - 0.1), 0.025, 'steel', 4))
for k in range(6):
    y = AY - AD / 2 + k * AD / 5
    p.append(tube((AX - AW / 2, y, FZ + H - 0.1), (AX + AW / 2, y, FZ + H - 0.1), 0.025, 'steel', 4))
# sariq panjara (arena atrofida, old tomonda kirish ochiq), chapdagi pandus va zina
FH = 0.95
fence_pts = [(AX - AW / 2 - 0.5, AY - AD / 2 - 0.5), (AX + AW / 2 + 0.5, AY - AD / 2 - 0.5),
             (AX + AW / 2 + 0.5, AY + AD / 2 + 0.5), (AX - AW / 2 - 0.5, AY + AD / 2 + 0.5)]
for i in range(4):
    (ax, ay), (bx, by) = fence_pts[i], fence_pts[(i + 1) % 4]
    L = math.hypot(bx - ax, by - ay)
    n = int(L / 2.0)
    for j in range(n + 1):
        tt = j / n
        x, y = ax + (bx - ax) * tt, ay + (by - ay) * tt
        if i == 2 and GATE_X0 < x < GATE_X1:  # orqa (+Y, Gameland tomoni) uzun tomonning +X chetida kirish
            continue
        p.append(tube((x, y, FZ), (x, y, FZ + FH), 0.03, 'gold', 6))
    for z in (FZ + 0.4, FZ + FH):
        if i == 2:  # (ax > bx) — kirish oralig'ini o'tkazib yuboramiz
            p.append(tube((ax, ay, z), (GATE_X1, ay, z), 0.025, 'gold', 4))
            p.append(tube((GATE_X0, ay, z), (bx, by, z), 0.025, 'gold', 4))
        else:
            p.append(tube((ax, ay, z), (bx, by, z), 0.025, 'gold', 4))
# kirish zinasi: orqa yo'lakdan (beton, z=0.15) arena sathiga, kirish oralig'ida
GY = AY + AD / 2 + 0.5
steps = 3
for k in range(steps):
    z = 0.15 + (FZ - 0.15) * (k + 1) / steps
    p.append(box((GATE_X1 - GATE_X0, 0.3, z - 0.15), ((GATE_X0 + GATE_X1) / 2, GY + 0.9 - k * 0.3, 0.15 + (z - 0.15) / 2), 'concrete'))
for x in (GATE_X0, GATE_X1):
    p.append(tube((x, GY, FZ), (x, GY, FZ + FH + 0.15), 0.04, 'gold', 6))
    p.append(tube((x, GY + 1.0, 0.15), (x, GY, FZ + 0.1), 0.025, 'gold', 4))
base = join('base', p)

# ---------- Mashinalar va trassa (arena ichidagi oval) ----------
SA, RO = AW / 2 - 3.5, AD / 2 - 2.0


def oval(step=0.2):
    pts = []
    n = int(2 * SA / step)
    pts += [(-SA + 2 * SA * i / n, -RO) for i in range(n)]
    n = int(math.pi * RO / step)
    pts += [(SA + RO * math.cos(-math.pi / 2 + math.pi * i / n), RO * math.sin(-math.pi / 2 + math.pi * i / n)) for i in range(n)]
    n = int(2 * SA / step)
    pts += [(SA - 2 * SA * i / n, RO) for i in range(n)]
    n = int(math.pi * RO / step)
    pts += [(-SA + RO * math.cos(math.pi / 2 + math.pi * i / n), RO * math.sin(math.pi / 2 + math.pi * i / n)) for i in range(n)]
    return [(AX + x, AY + y) for x, y in pts]


cars = []
for k in range(8):
    col = 'yellow' if k % 2 == 0 else 'blue'
    q = [box((1.9, 1.2, 0.28), (0, 0, 0.2), 'rubber')]                    # rezina bamper
    q.append(dome(0.85, (0.0, 0, 0.32), col, (1.15, 0.75, 0.6)))           # gumbazli kuzov
    q.append(box((0.6, 0.6, 0.35), (-0.2, 0, 0.6), 'black'))               # o'rindiq
    q.append(cyl(0.12, 0.04, (0.35, 0, 0.75), 'black', 8, (0, 0.6, 0)))     # rul
    q.append(tube((-0.75, 0, 0.5), (-0.75, 0, FZ + H - 0.15 - FZ), 0.025, 'black', 4))  # tok ustuni
    for sx in (-0.5, 0.0, 0.5):
        q.append(box((0.08, 1.22, 0.03), (sx, 0, 0.36), 'black'))          # kuzovdagi chiziqlar
    c = join(f'car{k}', q)
    cars.append(c)
op = oval()
L_track = sum(math.dist(a, b) for a, b in zip(op, op[1:] + op[:1]))
spacing = L_track / len(cars)
cum = [0.0]
for a, b in zip(op, op[1:] + op[:1]):
    cum.append(cum[-1] + math.dist(a, b))
for k, c in enumerate(cars):  # preview uchun joylashtirish
    s = (L_track - k * spacing) % L_track
    i = max(j for j in range(len(op)) if cum[j] <= s)
    a, b = op[i], op[(i + 1) % len(op)]
    c.location = (a[0], a[1], FZ + 0.02)
    c.rotation_euler = (0, 0, math.atan2(b[1] - a[1], b[0] - a[0]))
OUT_TRACK.write_text(json.dumps({
    'closed': True,
    'points': [[round(x, 3), round(FZ + 0.02, 3), round(-y, 3)] for x, y in op],
    'cars': [{'name': c.name, 'offset': round(k * spacing, 3)} for k, c in enumerate(cars)],
    'station': 0,
}, separators=(',', ':')))

tris = sum(len(pg.vertices) - 2 for o in scene.objects if o.type == 'MESH' for pg in o.data.polygons)
print(f'AVTODROM tris={tris} track={L_track:.1f}m')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
for c in cars:  # eksportda mashinalar boshlang'ich holatda (kod joylaydi)
    pass
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'AVTODROM glb={OUT_GLB.stat().st_size // 1024} KB')

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.location = (16, -30, 15)
cam.rotation_euler = (Vector((0, 0, 1.5)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 1100, 750
world = bpy.data.worlds.new('w')
world.color = (0.93, 0.95, 0.98)
scene.world = world
scene.render.filepath = str(PREVIEW_DIR / 'preview.png')
bpy.ops.render.render(write_still=True)
print('AVTODROM preview', scene.render.filepath)

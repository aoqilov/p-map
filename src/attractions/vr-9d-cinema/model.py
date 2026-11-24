"""
VR-9D Cinema — planda raqamsiz (avvalgi "Батут" o'rnida). Rasm: foydalanuvchi skrinshoti (qora-ko'k VR harakat platformasi).

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/vr-9d-cinema/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png (va preview_close.png)

Tuzilish (xarita kodi: src/map/GltfModel.tsx):
    base    — qimirlamaydigan qism: kvadrat sahna (to'q pol, chetlarida ko'k LED), platforma tagi (zina, panjara, LED),
              oldida katta monitor (ekrani o'rindiqlarga qaragan, kosmik rasm; orqasida "VR 9D" yozuvi), to'siq ustunchalar
    swing0  — kabina (harakat platformasi): burchakli kapot (ko'k chiziqlar, sariq strelkalar), yonlarida "dvigatellar"
              (yonib turgan ko'k ramkalar), 6 o'rindiq (2 qator), tutqichlardagi ko'k tugmalar, orqada qanot va yon ekran.
              Origin — platforma o'qida (o'q — Blender X): oldinga-orqaga yengil chayqaladi
Joylashuv: kabina burni va monitor — -Y (old tomon). Asl o'lcham: sahna 9 × 9 m, balandligi ~2.9 m.
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
    'floor': (0.12, 0.13, 0.15), 'floor_line': (0.2, 0.21, 0.24), 'body': (0.13, 0.14, 0.16), 'body2': (0.2, 0.21, 0.23),
    'panel': (0.28, 0.29, 0.31), 'seat': (0.06, 0.06, 0.07), 'cyan': (0.1, 0.85, 1.0), 'yellow': (1.0, 0.8, 0.1),
    'steel': (0.55, 0.57, 0.6), 'grate': (0.35, 0.37, 0.4), 'screen': (0.05, 0.12, 0.35), 'space1': (0.45, 0.2, 0.85),
    'space2': (0.1, 0.6, 1.0), 'star': (0.95, 0.95, 1.0), 'black': (0.04, 0.04, 0.05),
}
EMISSIVE = {'cyan': 2.0, 'yellow': 1.2, 'screen': 0.6, 'space1': 1.2, 'space2': 1.4, 'star': 1.5}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.35
    if name in ('body', 'body2', 'panel', 'steel'):
        bsdf.inputs['Metallic'].default_value = 0.3  # xaritada atrof-muhit aksi yo'q — yuqori metallik qoraygan ko'rinadi
    if name in EMISSIVE:
        bsdf.inputs['Emission Color'].default_value = (*rgb, 1)
        bsdf.inputs['Emission Strength'].default_value = EMISSIVE[name]
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


def prism_yz(pts, x0, x1, mat):
    """YZ ko'pburchak (profil) → X bo'yicha x0..x1 prizma (kapot shakli uchun)"""
    bm = bmesh.new()
    a = [bm.verts.new((x0, y, z)) for y, z in pts]
    b = [bm.verts.new((x1, y, z)) for y, z in pts]
    bm.faces.new(a)
    bm.faces.new(b[::-1])
    n = len(pts)
    for k in range(n):
        bm.faces.new([a[(k + 1) % n], a[k], b[k], b[(k + 1) % n]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return new_obj('prism', bm, mat)


def frame_rect(cx, cy, cz, w, h, t, mat, axis='Y', depth=0.03):
    """To'rtburchak ramka (yonib turgan chiziq): Y o'qiga perpendikulyar tekislikda (XZ) yoki X ga (YZ)"""
    res = []
    if axis == 'Y':
        res.append(box((w, depth, t), (cx, cy, cz + h / 2), mat))
        res.append(box((w, depth, t), (cx, cy, cz - h / 2), mat))
        res.append(box((t, depth, h), (cx - w / 2, cy, cz), mat))
        res.append(box((t, depth, h), (cx + w / 2, cy, cz), mat))
    else:
        res.append(box((depth, w, t), (cx, cy, cz + h / 2), mat))
        res.append(box((depth, w, t), (cx, cy, cz - h / 2), mat))
        res.append(box((depth, t, h), (cx, cy - w / 2, cz), mat))
        res.append(box((depth, t, h), (cx, cy + w / 2, cz), mat))
    return res


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
    ob.data.set_sharp_from_angle(angle=math.radians(40))
    return ob


# ====================== BASE ======================
S = 9.0                  # sahna tomoni
H0 = 0.12
p = [box((S, S, H0), (0, 0, H0 / 2), 'floor')]
for k in range(1, 9):    # pol plitalari choklari
    c = -S / 2 + k * S / 9
    p.append(box((S - 0.1, 0.02, 0.005), (0, c, H0 + 0.002), 'floor_line'))
    p.append(box((0.02, S - 0.1, 0.005), (c, 0, H0 + 0.002), 'floor_line'))
for sx in (-1, 1):       # chetdagi ko'k LED tasma
    p.append(box((0.06, S, 0.05), (sx * (S / 2 - 0.03), 0, H0 + 0.01), 'cyan'))
    p.append(box((S, 0.06, 0.05), (0, sx * (S / 2 - 0.03), H0 + 0.01), 'cyan'))
# to'siq: burchaklarda va chetlarda ustunchalar, orasida qora tasma (old tomonda ochiq)
for i in range(7):
    for side in ('l', 'r', 'b'):
        t = -S / 2 + 0.4 + i * (S - 0.8) / 6
        x, y = {'l': (-S / 2 + 0.4, t), 'r': (S / 2 - 0.4, t), 'b': (t, S / 2 - 0.4)}[side]
        p.append(cyl(0.05, 0.95, (x, y, H0 + 0.475), 'steel', 8))
        p.append(cyl(0.14, 0.04, (x, y, H0 + 0.02), 'steel', 10))
        p.append(cyl(0.06, 0.05, (x, y, H0 + 0.97), 'cyan', 8))
for a, b in (((-S / 2 + 0.4, -S / 2 + 0.4), (-S / 2 + 0.4, S / 2 - 0.4)), ((S / 2 - 0.4, -S / 2 + 0.4), (S / 2 - 0.4, S / 2 - 0.4)),
             ((-S / 2 + 0.4, S / 2 - 0.4), (S / 2 - 0.4, S / 2 - 0.4))):
    p.append(beam((a[0], a[1], H0 + 0.85), (b[0], b[1], H0 + 0.85), 0.02, 0.08, 'black'))

# platforma tagi (harakatsiz): qora quti, LED chiziq, zina (orqa-chapda), panjara
PL = (2.9, 3.6, 0.45)
PY = 0.6                 # platforma markazi (Y)
p.append(box(PL, (0, PY, H0 + PL[2] / 2), 'body'))
p.append(box((PL[0] + 0.04, PL[1] + 0.04, 0.04), (0, PY, H0 + PL[2] - 0.05), 'cyan'))
for k in range(6):
    p.append(box((0.04, 0.3, 0.12), (PL[0] / 2 + 0.01, PY - 1.4 + k * 0.56, H0 + 0.2), 'panel'))
p.append(box((1.6, 0.25, 0.04), (0, PY + PL[1] / 2 + 0.01, H0 + 0.2), 'cyan'))
SX, SY = -PL[0] / 2 - 0.55, PY + 1.1          # zina (chap tomonda, orqaroqda)
for k in range(3):
    h = H0 + (k + 1) * PL[2] / 3
    p.append(box((0.3, 1.0, h - H0), (SX + 0.3 - k * 0.0 + (2 - k) * -0.0 + (k - 1) * 0.3 - 0.3, SY, H0 + (h - H0) / 2), 'grate'))
for k in range(3):
    p.append(box((0.3, 1.0, 0.02), (SX - 0.3 + k * 0.3, SY, H0 + (k + 1) * PL[2] / 3 + 0.01), 'cyan'))
for y in (SY - 0.5, SY + 0.5):
    p.append(beam((SX - 0.45, y, H0 + 0.95), (SX + 0.45, y, H0 + PL[2] + 0.95), 0.05, 0.05, 'steel'))
    for x, z in ((SX - 0.45, H0), (SX + 0.45, H0 + PL[2])):
        p.append(box((0.05, 0.05, 0.95), (x, y, z + 0.475), 'steel'))

# monitor (oldida, -Y): ikki oyoq, katta ekran (o'rindiqlarga qaragan), orqasida "VR 9D"
MY = -3.3
MW, MH, MZ = 3.2, 1.8, 1.95            # ekran eni, bo'yi, markaz balandligi
for x in (-1.1, 1.1):
    p.append(box((0.14, 0.14, MZ - 0.2), (x, MY - 0.12, H0 + (MZ - 0.2) / 2), 'body2'))
    p.append(box((0.6, 0.6, 0.05), (x, MY - 0.12, H0 + 0.03), 'body2'))
p.append(box((MW + 0.16, 0.16, MH + 0.16), (0, MY - 0.12, MZ), 'black'))
p.append(box((MW, 0.03, MH), (0, MY - 0.03, MZ), 'screen'))
# ekrandagi rasm: kosmos — sayyora, tumanlik, yulduzlar, kosmik kema siluetlari
p.append(cyl(0.38, 0.02, (-0.8, MY - 0.01, MZ + 0.25), 'space1', 24, (math.pi / 2, 0, 0)))
p.append(cyl(0.55, 0.015, (-0.8, MY - 0.005, MZ + 0.25), 'space2', 24, (math.pi / 2, 0, 0), 0.5))
p.append(box((1.2, 0.02, 0.06), (0.6, MY - 0.01, MZ - 0.3), 'space2', (0, 0.25, 0)))
p.append(box((0.5, 0.02, 0.18), (0.8, MY - 0.012, MZ + 0.2), 'space1', (0, -0.3, 0)))
for k in range(18):
    x = -MW / 2 + 0.15 + ((k * 0.67) % (MW - 0.3))
    z = MZ - MH / 2 + 0.12 + ((k * 0.41) % (MH - 0.25))
    p.append(box((0.03, 0.02, 0.03), (x, MY - 0.015, z), 'star'))
for k in range(4):        # pastki "interfeys" chiziqlari
    p.append(box((0.5, 0.02, 0.025), (-1.2 + k * 0.8, MY - 0.015, MZ - MH / 2 + 0.12), 'cyan'))
p.extend(frame_rect(0, MY - 0.035, MZ, MW + 0.05, MH + 0.05, 0.03, 'cyan', 'Y', 0.02))
# orqa tomoni (yo'lka tarafdan ko'rinadi): ko'k ramka va "VR 9D" harflari
BY = MY - 0.21
p.extend(frame_rect(0, BY, MZ, MW - 0.2, MH - 0.2, 0.05, 'cyan', 'Y', 0.02))
FONT = {
    'V': ['10001', '10001', '10001', '10001', '01010', '01010', '00100'],
    'R': ['11110', '10001', '10001', '11110', '10100', '10010', '10001'],
    '9': ['01110', '10001', '10001', '01111', '00001', '00010', '01100'],
    'D': ['11100', '10010', '10001', '10001', '10001', '10010', '11100'],
}
txt, px = 'VR 9D', 0.07
cx0 = (len(txt) * 6 - 1) * px / 2
for i, ch in enumerate(txt):
    if ch == ' ':
        continue
    for r, row in enumerate(FONT[ch]):
        for c, bit in enumerate(row):
            if bit == '1':
                # -Y tomondan (yo'lkadan) qaraganda chapdan o'ngga = +X yo'nalishi
                x = -cx0 + (i * 6 + c) * px + px / 2
                p.append(box((px * 0.9, 0.02, px * 0.9), (x, BY - 0.01, MZ + 0.25 - r * px), 'cyan'))
base = join('base', p)

# ====================== SWING0: kabina ======================
PZ = H0 + PL[2]          # platforma usti
PIV = Vector((0, PY, PZ + 0.25))
q = []
q.append(box((2.7, 3.4, 0.35), (0, PY, PZ + 0.25), 'body2'))                          # rama
# kapot (oldda): burchakli profil, Y bo'ylab
hood = [(-1.75, PZ + 0.35), (-1.75, PZ + 0.85), (-1.45, PZ + 1.15), (-0.55, PZ + 1.25), (-0.35, PZ + 1.0),
        (-0.35, PZ + 0.35)]
q.append(prism_yz([(PY + y, z) for y, z in hood], -1.05, 1.05, 'body'))
for side in (-1, 1):     # kapot yon qiyaliklari va chiziqlari
    q.append(box((0.04, 1.2, 0.05), (side * 0.75, PY - 1.0, PZ + 1.22), 'cyan'))
    q.append(box((0.3, 0.04, 0.1), (side * 0.55, PY - 1.77, PZ + 0.62), 'yellow', (0, side * 0.6, 0)))
for k in range(3):
    q.append(box((1.2 - k * 0.2, 0.05, 0.04), (0, PY - 1.35 + k * 0.25, PZ + 1.2 + k * 0.02), 'cyan', (0.2, 0, 0)))
q.append(box((1.6, 0.04, 0.35), (0, PY - 1.77, PZ + 0.55), 'panel'))                 # old panjara
for k in range(6):
    q.append(box((0.04, 0.05, 0.28), (-0.6 + k * 0.24, PY - 1.8, PZ + 0.55), 'black'))
# "dvigatellar": yonlarida, old yuzida yonib turgan ichma-ich ramkalar
for side in (-1, 1):
    ex, ey = side * 1.3, PY - 0.7
    q.append(box((0.6, 1.2, 0.8), (ex, ey, PZ + 0.75), 'body'))
    q.append(box((0.64, 0.2, 0.84), (ex, ey - 0.55, PZ + 0.75), 'body2'))
    for k, (w, h) in enumerate(((0.5, 0.66), (0.36, 0.5), (0.22, 0.34))):
        q.extend(frame_rect(ex, ey - 0.66 - 0.005 * k, PZ + 0.75, w, h, 0.035, 'cyan', 'Y', 0.02))
    q.append(box((0.04, 0.6, 0.06), (ex + side * 0.31, ey, PZ + 1.0), 'yellow'))
# o'rindiqlar: 2 qator × 3 (qora, baland suyanchiq, bosh joyida ko'k chiroq)
for r, y in enumerate((PY + 0.1, PY + 1.05)):
    zs = PZ + 0.45 + r * 0.25             # orqa qator balandroq (amfiteatr)
    if r == 1:
        q.append(box((2.5, 0.9, 0.25), (0, y, PZ + 0.5), 'body2'))
    for x in (-0.75, 0.0, 0.75):
        q.append(box((0.6, 0.6, 0.18), (x, y, zs + 0.12), 'seat'))
        q.append(box((0.6, 0.15, 0.85), (x, y + 0.3, zs + 0.55), 'seat', (-0.15, 0, 0)))
        q.append(box((0.42, 0.12, 0.22), (x, y + 0.36, zs + 1.05), 'seat', (-0.15, 0, 0)))
        q.append(box((0.3, 0.02, 0.04), (x, y + 0.29, zs + 1.08), 'cyan', (-0.15, 0, 0)))
        for s in (-1, 1):                 # tutqichlar va ko'k tugmalar
            q.append(box((0.08, 0.5, 0.08), (x + s * 0.34, y - 0.02, zs + 0.38), 'body2'))
            q.append(cyl(0.035, 0.04, (x + s * 0.34, y - 0.22, zs + 0.43), 'cyan', 10))
    q.append(box((2.5, 0.04, 0.04), (0, y - 0.32, PZ + 0.42 + r * 0.25), 'cyan'))
# orqadagi qanot (dron shaklida) va yon ekran
WY = PY + 1.55
q.append(box((0.12, 0.12, 0.95), (0, WY, PZ + 1.6), 'body2'))
q.append(box((2.0, 0.35, 0.06), (0, WY, PZ + 2.1), 'body'))
for s in (-1, 1):
    q.append(box((0.6, 0.25, 0.05), (s * 1.05, WY - 0.1, PZ + 2.16), 'body', (0, s * -0.25, 0)))
    q.append(box((1.5, 0.04, 0.03), (s * 0.55, WY - 0.18, PZ + 2.14), 'cyan', (0, 0, 0)))
q.append(box((0.35, 0.6, 0.12), (0, WY + 0.05, PZ + 2.2), 'body2'))
q.append(box((0.12, 0.7, 1.2), (-1.4, PY + 1.15, PZ + 1.3), 'body'))                 # yon ekran (chapda)
q.extend(frame_rect(-1.47, PY + 1.15, PZ + 1.3, 0.6, 1.05, 0.03, 'cyan', 'X', 0.02))
swing = join('swing0', q)
bpy.ops.object.select_all(action='DESELECT')
swing.select_set(True)
bpy.context.view_layer.objects.active = swing
scene.cursor.location = PIV
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

objs = [o for o in scene.objects if o.type == 'MESH']
tris = sum(len(pg.vertices) - 2 for o in objs for pg in o.data.polygons)
bpy.context.view_layer.update()
top = max((o.matrix_world @ v.co).z for o in objs for v in o.data.vertices)
print(f'VR9D tris={tris} top={top:.2f}')

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'VR9D glb={OUT_GLB.stat().st_size // 1024} KB')

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 1000, 900
world = bpy.data.worlds.new('w')
world.color = (0.9, 0.92, 0.95)
scene.world = world
for fname, loc, tgt in (('preview.png', (7.5, -9.0, 6.0), (0, -0.5, 1.0)),
                        ('preview_close.png', (3.2, 4.5, 3.2), (0, -1.5, 1.4))):
    cam.location = loc
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(PREVIEW_DIR / fname)
    bpy.ops.render.render(write_still=True)
    print('VR9D preview', scene.render.filepath)

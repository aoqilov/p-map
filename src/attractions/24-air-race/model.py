"""
24 — Аттракцион "Air race 2 seats". Low-poly model, rasm: attraction-images-park/Air_Race.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/24-air-race/model.py [-- <preview_papka>]
Natija shu papkada:
    model.blend — Blender'da ochib ko'rish/tahrirlash uchun
    model.glb   — xaritaga ulanadigan model (config.ts shuni import qiladi)
    preview.png, preview_seat.png — tekshirish uchun render

Tuzilish (xarita kodi shu nomlarga tayanadi, src/map/GltfModel.tsx):
    base     — qimirlamaydigan qism: shaxmat naqshli sakkiz qirrali poydevor va konus
    rotor    — aylanadigan qism: markaz, minora, 6 ta qo'l, ustunlar
    lift0..5 — samolyot-o'rindiqlar (rotor bolalari): ustun bo'ylab ko'tariladi
Asl o'lcham metrda: diametri 9.7 m, balandligi 6.0 m (xaritadagi o'lcham — config.ts → size).
"""
import math
import sys
from pathlib import Path

import bmesh
import bpy

HERE = Path(__file__).resolve().parent
OUT_GLB = HERE / 'model.glb'
OUT_BLEND = HERE / 'model.blend'
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PREVIEW_DIR = Path(argv[0]) if argv else HERE

# ---------- Sahnani tozalash ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- Materiallar ----------
PALETTE = {
    'white': (0.92, 0.92, 0.90), 'black': (0.04, 0.04, 0.05), 'blue': (0.04, 0.09, 0.42),
    'red': (0.75, 0.03, 0.03), 'yellow': (0.95, 0.70, 0.02), 'orange': (0.95, 0.25, 0.03),
    'green': (0.35, 0.75, 0.08), 'silver': (0.65, 0.66, 0.68), 'dark': (0.12, 0.12, 0.14),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.45 if name in ('blue', 'red', 'yellow', 'orange', 'green') else 0.6
    if name == 'silver':
        bsdf.inputs['Metallic'].default_value = 0.3  # xaritada atrof-muhit aksi yo'q — yuqori metallik qoraygan ko'rinadi
    m.diffuse_color = (*rgb, 1)  # Workbench preview uchun
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


def lathe(name, profile, segs, mat_of, mats, phase=0.0):
    """Aylanma jism: profile [(radius, z), ...] pastdan tepaga; mat_of(i, k) — material indeksi."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r < 1e-6:
            v = bm.verts.new((0, 0, z))
            rings.append([v] * segs)
        else:
            rings.append([bm.verts.new((r * math.cos(phase + 2 * math.pi * k / segs),
                                        r * math.sin(phase + 2 * math.pi * k / segs), z)) for k in range(segs)])
    for i in range(len(profile) - 1):
        a, b = rings[i], rings[i + 1]
        for k in range(segs):
            k2 = (k + 1) % segs
            vs = [a[k], a[k2], b[k2], b[k]]
            uniq = []
            for v in vs:
                if v not in uniq:
                    uniq.append(v)
            if len(uniq) < 3:
                continue
            f = bm.faces.new(uniq)
            f.material_index = mat_of(i, k)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return new_obj(name, bm, mats)


def box(name, size, loc, mat, rot_z=0.0, rot=None):
    """Quti: o'lchami size, markazi loc; rot_z — Z atrofida burilish, rot — (rx, ry, rz) to'liq burilish"""
    from mathutils import Euler
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    m = Euler(rot if rot else (0, 0, rot_z), 'XYZ').to_matrix()
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=m)
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return new_obj(name, bm, [mat])


def torus(name, major, minor, loc, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=12, minor_segments=5,
                                     location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(MATS[mat])
    return ob


def _cyl(name, r, h, loc, mat, segs, r2):
    """Silindr (r2 berilsa — kesik konus), asosi loc da"""
    ob = lathe(name, [(0, 0), (r, 0), (r2 if r2 is not None else r, h), (0, h)], segs, lambda i, k: 0, [mat])
    ob.location = loc
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


# ---------- BASE: shaxmat poydevor (sakkiz qirra) va konus ----------
BASE_R, BASE_H = 4.0, 0.35
checker2 = lambda i, k: (i + k) % 2  # 0 — oq, 1 — qora
base = lathe('base_plate', [(0, 0), (BASE_R, 0), (BASE_R, BASE_H), (2.75, BASE_H), (1.5, BASE_H), (0, BASE_H)], 16,
             lambda i, k: (0 if i == 0 else (k + i) % 2), ['white', 'black'], phase=math.pi / 16)
cone = lathe('base_cone', [(1.35, BASE_H), (1.2, 0.95), (1.05, 1.55), (0.9, 2.15), (0.8, 2.5), (0, 2.5)], 12,
             lambda i, k: (k + i) % 2, ['white', 'black'])
base = join('base', [base, cone])

# ---------- ROTOR ----------
parts = []
HUB_Z = 2.5
# Markaz: ko'k "samolyot tanasi" disk + qizil tumshuq
parts.append(lathe('hub', [(0, HUB_Z), (0.95, HUB_Z), (1.25, HUB_Z + 0.25), (0.9, HUB_Z + 0.55), (0, HUB_Z + 0.6)], 12,
                   lambda i, k: 0, ['blue']))
nose = lathe('nose', [(0, 0), (0.28, 0), (0.18, 0.35), (0, 0.45)], 8, lambda i, k: 0, ['red'])
nose.rotation_euler = (0, math.pi / 2, 0)
nose.location = (1.2, 0, HUB_Z + 0.3)
parts.append(nose)
# Minora: oq-qizil yo'l-yo'l konus
SPIRE = [(0.62, HUB_Z + 0.55), (0.55, 3.5), (0.47, 4.0), (0.39, 4.5), (0.3, 5.0), (0.2, 5.5), (0.1, 5.95), (0, 6.05)]
parts.append(lathe('spire', SPIRE, 10, lambda i, k: i % 2, ['white', 'red']))
# Minorani o'rab chiqadigan ko'k spiral (kichik bo'laklardan)
for j in range(28):
    u = j / 27
    z = HUB_Z + 0.8 + u * 2.4
    r = 0.6 - u * 0.33 + 0.06
    ang = u * math.pi * 3.2
    parts.append(box('helix', (0.12, 0.26, 0.1), (r * math.cos(ang), r * math.sin(ang), z), 'blue', ang))
parts.append(_cyl('mast', 0.03, 0.55, (0, 0, 6.0), 'silver', 6, None))
for a in (0, math.pi / 2):  # tepadagi kichik parrak
    parts.append(box('prop_top', (0.9, 0.06, 0.03), (0, 0, 6.5), 'white', a))

ARM_R = 4.3  # qo'l uzunligi (markazdan ustungacha)
SEAT_COLORS = ['orange', 'green', 'yellow', 'orange', 'green', 'red']
for n in range(6):
    a = math.pi / 6 + n * math.pi / 3
    ca, sa = math.cos(a), math.sin(a)
    # qo'l (gorizontal to'sin)
    parts.append(box(f'arm{n}', (ARM_R, 0.22, 0.26), (ca * ARM_R / 2, sa * ARM_R / 2, HUB_Z + 0.15), 'blue', a))
    # ustun va qizil qalpoq
    # qo'l yon tomonidagi sariq "AIR RACE" chizig'i
    for side in (-1, 1):
        ox, oy = -sa * 0.115 * side, ca * 0.115 * side
        parts.append(box(f'stripe{n}', (ARM_R * 0.55, 0.01, 0.09), (ca * ARM_R * 0.55 + ox, sa * ARM_R * 0.55 + oy, HUB_Z + 0.15), 'yellow', a))
    parts.append(box(f'post{n}', (0.2, 0.2, 3.45), (ca * ARM_R, sa * ARM_R, 2.27), 'blue', a))
    parts.append(box(f'cap{n}', (0.34, 0.3, 0.3), (ca * ARM_R, sa * ARM_R, 4.08), 'red', a))
    parts.append(box(f'tip{n}', (0.7, 0.18, 0.18), (ca * (ARM_R + 0.2), sa * (ARM_R + 0.2), HUB_Z + 0.15), 'blue', a))

rotor = join('rotor', parts)

# ---------- Samolyot-o'rindiqlar ----------
# Har biri alohida `lift<n>` obyekti, `rotor`ning bolasi: rotor bilan aylanadi, kodda ustun bo'ylab ko'tariladi.
# Lokal o'qlar: +X — tashqariga (markazdan), +Y — harakat yo'nalishi (samolyot burni), Z — tepaga. (0,0) — samolyot markazi.
Z0 = 0.55  # qanot sathi
POST_X = -0.55  # ustun samolyot markazidan shuncha ichkarida


def gondola(n, col):
    p = []
    blade_col = 'yellow' if col not in ('yellow', 'green') else 'red'
    # korpus: aylanma jism, burni +Y ga
    body = lathe(f'fus{n}', [(0, -1.05), (0.1, -1.0), (0.2, -0.55), (0.23, 0.1), (0.2, 0.6), (0.13, 0.88), (0, 0.92)], 10,
                 lambda i, k: 0, [col])
    body.rotation_euler = (-math.pi / 2, 0, 0)
    body.location = (0, 0, Z0)
    p.append(body)
    # qanot (uchlari dumaloq) va ustidagi metall panjara (oyoq qo'yish joyi)
    p.append(box(f'wing{n}', (2.3, 0.62, 0.06), (0, 0.15, Z0), col))
    for sx in (-1.15, 1.15):
        p.append(_cyl(f'wtip{n}', 0.31, 0.06, (sx, 0.15, Z0 - 0.03), col, 10, None))
    p.append(box(f'grate{n}', (1.25, 0.42, 0.02), (0, 0.28, Z0 + 0.04), 'silver'))
    # dum: gorizontal va tik stabilizator
    p.append(box(f'stab{n}', (0.95, 0.28, 0.04), (0, -0.9, Z0 + 0.08), col))
    p.append(box(f'fin{n}', (0.04, 0.32, 0.38), (0, -0.92, Z0 + 0.27), col, rot=(0.25, 0, 0)))
    # parrak: kumush konus + ikki parrak
    sp = lathe(f'spin{n}', [(0, 0), (0.14, 0), (0.08, 0.18), (0, 0.24)], 8, lambda i, k: 0, ['silver'])
    sp.rotation_euler = (-math.pi / 2, 0, 0)
    sp.location = (0, 0.9, Z0)
    p.append(sp)
    p.append(box(f'blade{n}', (0.9, 0.035, 0.1), (0, 1.0, Z0), blade_col, rot=(0, 0.5, 0)))  # ikki qanotli parrak
    # ikki "kovsh" o'rindiq
    for sx in (-0.3, 0.3):
        p.append(_cyl(f'ped{n}', 0.06, 0.26, (sx, -0.12, Z0 + 0.03), 'silver', 6, None))  # tayanch
        p.append(box(f'pan{n}', (0.44, 0.44, 0.1), (sx, -0.1, Z0 + 0.34), col))  # o'tirgich
        for bx_ in (-0.2, 0.2):  # yon tayanchlar
            p.append(box(f'bol{n}', (0.07, 0.42, 0.16), (sx + bx_, -0.1, Z0 + 0.45), col))
        # suyanchiq: o'rta va ikki yon qanot (kovsh shakli), biroz orqaga qiya
        p.append(box(f'back{n}', (0.3, 0.08, 0.8), (sx, -0.33, Z0 + 0.78), col, rot=(-0.18, 0, 0)))
        for side in (-1, 1):
            p.append(box(f'wing_b{n}', (0.12, 0.08, 0.74), (sx + side * 0.2, -0.28, Z0 + 0.76), col,
                         rot=(-0.18, 0, side * 0.6)))
        # tepadagi qora ushlagich halqasi va kumush qo'l to'sig'i
        p.append(torus(f'head{n}', 0.13, 0.03, (sx, -0.42, Z0 + 1.24), 'black', rot=(math.pi / 2 - 0.18, 0, 0)))
        p.append(box(f'lap{n}', (0.38, 0.03, 0.03), (sx, 0.12, Z0 + 0.62), 'silver'))
        for lx in (-0.17, 0.17):
            p.append(box(f'lapr{n}', (0.025, 0.025, 0.22), (sx + lx, 0.12, Z0 + 0.5), 'silver'))
    # ustunga mahkamlagich: ustunni o'rab turuvchi gilza va samolyotga tutashtiruvchi to'sin
    p.append(box(f'sleeve{n}', (0.3, 0.3, 0.6), (POST_X, 0, Z0 + 0.35), 'blue'))
    p.append(box(f'brk{n}', (0.45, 0.14, 0.14), (POST_X / 2 - 0.05, -0.1, Z0 + 0.12), 'blue'))
    g = join(f'lift{n}', p)
    return g


for n in range(6):
    a = math.pi / 6 + n * math.pi / 3
    g = gondola(n, SEAT_COLORS[n])
    r = ARM_R - POST_X
    g.location = (math.cos(a) * r, math.sin(a) * r, 0)
    g.rotation_euler = (0, 0, a)  # lokal +X → tashqariga
    g.parent = rotor


# ---------- Tekshiruv ----------
tris = sum(len(p.vertices) - 2 for o in scene.objects if o.type == 'MESH' for p in o.data.polygons)
dims = [max(o.dimensions[i] for o in (base, rotor)) for i in range(3)]
print(f'AIR_RACE tris={tris} size={dims[0]:.2f}x{dims[1]:.2f}x{max(o.location.z + o.dimensions.z for o in (base, rotor)):.2f}')

# ---------- Saqlash va eksport ----------
OUT_GLB.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'AIR_RACE glb={OUT_GLB.stat().st_size // 1024} KB')

# ---------- Preview render (Workbench — tez, GPU shart emas) ----------
cam_data = bpy.data.cameras.new('cam')
cam_data.lens = 50
cam = bpy.data.objects.new('cam', cam_data)
scene.collection.objects.link(cam)
cam.location = (15.5, -15.5, 10.5)
direction = __import__('mathutils').Vector((0, 0, 2.6)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 1000, 900
scene.render.film_transparent = False
world = bpy.data.worlds.new('w')
world.color = (0.93, 0.95, 0.98)
scene.world = world
scene.render.filepath = str(PREVIEW_DIR / 'preview.png')
bpy.ops.render.render(write_still=True)
print('AIR_RACE preview', scene.render.filepath)

# Yaqin ko'rinish: bitta samolyot-o'rindiq (tekshirish uchun)
a0 = math.pi / 6
gx, gy = math.cos(a0) * (ARM_R + 0.55), math.sin(a0) * (ARM_R + 0.55)
cam.location = (gx + 3.2, gy - 2.6, 2.4)
cam.rotation_euler = (__import__('mathutils').Vector((gx, gy, 0.9)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.render.filepath = str(PREVIEW_DIR / 'preview_seat.png')
bpy.ops.render.render(write_still=True)

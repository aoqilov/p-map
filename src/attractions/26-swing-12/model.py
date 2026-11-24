"""
26 — Аттракцион "Swing 12" (daraxt-arg'imchoq). Rasm: attraction-images-park/Swing.png

Ishga tushirish (Blender oynasiz, loyiha ildizidan):
    blender -b --factory-startup -P src/attractions/26-swing-12/model.py [-- <preview_papka>]
Natija shu papkada: model.blend, model.glb, preview.png

Tuzilish (xarita kodi: src/map/GltfModel.tsx):
    base       — qimirlamaydigan qism: sakkiz qirrali yashil supa, oltin panjara, jigarrang tana pastki qismi
    rotor      — aylanadigan qism: tana yuqorisi, yashil toj (barg qirrali, oq chiroqchalar, qizil mevalar)
    swing0..11 — zanjirli oq o'rindiqlar (rotor bolalari): origin — ilgakda, kod ularni tashqariga og'diradi
                 (aylanishdagi markazdan qochma kuch) — swing animatsiyasi lokal X o'qi atrofida
Asl o'lcham metrda: diametri ~6 m, balandligi ~4.6 m.
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
    'grass': (0.12, 0.5, 0.12), 'leaf': (0.35, 0.68, 0.08), 'leaf2': (0.62, 0.8, 0.12), 'dark': (0.08, 0.38, 0.08),
    'bark': (0.42, 0.24, 0.1), 'bark2': (0.55, 0.32, 0.14), 'gold': (0.82, 0.64, 0.25), 'white': (0.95, 0.95, 0.93),
    'red': (0.8, 0.05, 0.05), 'steel': (0.6, 0.61, 0.63), 'floor': (0.82, 0.82, 0.8),
}
MATS = {}
for name, rgb in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.5
    if name in ('gold', 'steel'):
        bsdf.inputs['Metallic'].default_value = 0.3  # xaritada atrof-muhit aksi yo'q — yuqori metallik qoraygan ko'rinadi
    m.diffuse_color = (*rgb, 1)
    MATS[name] = m


def obj(bm, mats):
    me = bpy.data.meshes.new('m')
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(MATS[m])
    ob = bpy.data.objects.new('o', me)
    scene.collection.objects.link(ob)
    return ob


def box(size, loc, mat, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return obj(bm, [mat])


def sphere(r, loc, mat, segs=8):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=max(4, segs // 2), radius=r)
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return obj(bm, [mat])


def tube(a, b, r, mat, segs=6):
    a, b = Vector(a), Vector(b)
    v = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=segs, radius1=r, radius2=r, depth=v.length)
    ob = obj(bm, [mat])
    ob.rotation_euler = v.to_track_quat('Z', 'Y').to_euler()
    ob.location = (a + b) / 2
    return ob


def lathe(profile, segs, mats, mat_of, phase=0.0, wobble=None):
    """Aylanma jism; wobble(i, k) — radius ko'paytiruvchisi (to'lqinli qirralar uchun)"""
    bm = bmesh.new()
    rings = []
    for i, (r, z) in enumerate(profile):
        if r < 1e-6:
            v = bm.verts.new((0, 0, z))
            rings.append([v] * segs)
        else:
            ring = []
            for k in range(segs):
                a = phase + 2 * math.pi * k / segs
                rr = r * (wobble(i, k) if wobble else 1)
                ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z)))
            rings.append(ring)
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
    return obj(bm, mats)


def join(name, objs, origin=(0, 0, 0)):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    scene.cursor.location = origin
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return ob


# ---------- BASE ----------
R_FENCE, R_DECK = 2.95, 2.45
p = []
p.append(lathe([(R_FENCE + 0.05, 0), (R_FENCE + 0.05, 0.08), (0, 0.08)], 8, ['floor'], lambda i, k: 0, math.pi / 8))
p.append(lathe([(R_DECK, 0.08), (R_DECK, 0.3), (0, 0.3)], 8, ['grass'], lambda i, k: 0, math.pi / 8))
FH = 1.0
for k in range(8):
    a0, a1 = math.pi / 8 + k * math.pi / 4, math.pi / 8 + (k + 1) * math.pi / 4
    x0, y0, x1, y1 = R_FENCE * math.cos(a0), R_FENCE * math.sin(a0), R_FENCE * math.cos(a1), R_FENCE * math.sin(a1)
    p.append(tube((x0, y0, 0.08), (x0, y0, 0.08 + FH + 0.1), 0.04, 'gold', 6))
    p.append(sphere(0.06, (x0, y0, 0.08 + FH + 0.14), 'gold', 6))
    if k == 5:  # janub — kirish
        continue
    for z in (0.18, 0.08 + FH):
        p.append(tube((x0, y0, z), (x1, y1, z), 0.022, 'gold', 5))
    for j in range(1, 10):
        t = j / 10
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        p.append(tube((x, y, 0.18), (x, y, 0.08 + FH), 0.011, 'gold', 4))
# tananing pastki qismi (ildizlari yoyilgan), halqa
roots = lambda i, k: 1.0 + (0.35 if (k % 4 == 0 and i == 0) else 0.0)
p.append(lathe([(0.95, 0.3), (0.72, 0.6), (0.58, 1.1), (0.55, 1.5)], 16, ['bark', 'bark2'], lambda i, k: k % 2, wobble=roots))
p.append(lathe([(0.66, 1.15), (0.66, 1.45), (0.6, 1.45)], 16, ['bark2'], lambda i, k: 0))
base = join('base', p)

# ---------- ROTOR: tananing yuqorisi va toj ----------
q = []
q.append(lathe([(0.55, 1.5), (0.5, 2.3), (0.62, 2.9), (0.9, 3.25)], 14, ['bark', 'bark2'], lambda i, k: (k // 2) % 2))
# toj: gumbaz, pastki cheti barg qirrali (to'lqinli), ikki xil yashil
crown = [(2.55, 3.1), (2.7, 3.35), (2.6, 3.75), (2.2, 4.15), (1.5, 4.45), (0.7, 4.6), (0, 4.62)]
zig = lambda i, k: (1.0 + (0.07 if k % 2 else -0.04)) if i <= 1 else 1.0
q.append(lathe(crown, 32, ['leaf', 'leaf2', 'dark'], lambda i, k: 2 if i == 0 else (0 if (k // 4 + i) % 2 else 1), wobble=zig))
q.append(lathe([(2.55, 3.1), (0.9, 3.15), (0, 3.2)], 32, ['dark'], lambda i, k: 0))   # tojning osti
# oq chiroqchalar (toj sirtida qatorlar) va qizil mevalar
for row, (r, z) in enumerate([(2.68, 3.55), (2.4, 3.98), (1.85, 4.32), (1.1, 4.52)]):
    n = [24, 20, 16, 10][row]
    for k in range(n):
        a = 2 * math.pi * (k + 0.5 * (row % 2)) / n
        q.append(sphere(0.06, (math.cos(a) * r, math.sin(a) * r, z + 0.05), 'white', 6))
        if row < 2 and k % 2 == 0:
            q.append(sphere(0.045, (math.cos(a + 0.12) * (r + 0.02), math.sin(a + 0.12) * (r + 0.02), z - 0.15), 'red', 4))
# osmalar uchun ko'ndalang qo'llar (toj ostida)
N = 12
R_HOOK, Z_HOOK = 2.2, 3.05
for k in range(N):
    a = 2 * math.pi * k / N
    q.append(tube((math.cos(a) * 0.9, math.sin(a) * 0.9, Z_HOOK + 0.05), (math.cos(a) * R_HOOK, math.sin(a) * R_HOOK, Z_HOOK + 0.05),
                  0.035, 'steel', 5))
rotor = join('rotor', q)

# ---------- O'rindiqlar: zanjir + oq o'rindiq; lokal +Y — tashqariga (radial), ilgakda origin ----------
SEAT_Z = 0.75
for k in range(N):
    a = 2 * math.pi * k / N
    s = []
    for side in (-0.2, 0.2):
        for dy in (-0.12, 0.12):
            s.append(tube((side * 0.3, 0, 0), (side, dy, SEAT_Z - Z_HOOK + 0.35), 0.012, 'steel', 3))
    s.append(box((0.46, 0.4, 0.06), (0, 0, SEAT_Z - Z_HOOK + 0.02), 'white'))
    s.append(box((0.46, 0.06, 0.36), (0, -0.2, SEAT_Z - Z_HOOK + 0.2), 'white'))
    for sx in (-0.23, 0.23):
        s.append(box((0.04, 0.4, 0.18), (sx, 0, SEAT_Z - Z_HOOK + 0.12), 'white'))
    s.append(tube((-0.2, 0.2, SEAT_Z - Z_HOOK + 0.3), (0.2, 0.2, SEAT_Z - Z_HOOK + 0.3), 0.015, 'steel', 4))
    sw = join(f'swing{k}', s)
    # lokal: +Y tashqariga — Z atrofida (a - 90°) buramiz; ilgak (R_HOOK, Z_HOOK) da
    sw.rotation_euler = (0, 0, a - math.pi / 2)
    sw.location = (math.cos(a) * R_HOOK, math.sin(a) * R_HOOK, Z_HOOK)
    sw.parent = rotor

tris = sum(len(pg.vertices) - 2 for o in scene.objects if o.type == 'MESH' for pg in o.data.polygons)
print(f'SWING tris={tris}')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', export_apply=True, export_yup=True)
print(f'SWING glb={OUT_GLB.stat().st_size // 1024} KB')

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.location = (6.5, -8.5, 5.0)
cam.rotation_euler = (Vector((0, 0, 2.1)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
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
print('SWING preview', scene.render.filepath)

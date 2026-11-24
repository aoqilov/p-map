"""Bolalar maydonchasi jihozlari uchun umumiy Blender yordamchilari (equipment.py shu yerdan import qiladi)."""
import math

import bmesh
import bpy
from mathutils import Euler, Vector

PALETTE = {
    'wood': (0.82, 0.72, 0.55), 'post': (0.72, 0.6, 0.45), 'deck': (0.55, 0.5, 0.45), 'brown': (0.28, 0.16, 0.12),
    'dark': (0.14, 0.13, 0.13), 'steel': (0.72, 0.73, 0.75), 'blue': (0.1, 0.32, 0.78), 'navy': (0.06, 0.15, 0.45),
    'sky': (0.2, 0.55, 0.9), 'red': (0.82, 0.1, 0.08), 'yellow': (0.98, 0.75, 0.05), 'orange': (0.98, 0.45, 0.06),
    'green': (0.12, 0.55, 0.22), 'lime': (0.45, 0.75, 0.15), 'teal': (0.05, 0.55, 0.55), 'purple': (0.45, 0.2, 0.7),
    'pink': (0.92, 0.35, 0.65), 'white': (0.93, 0.93, 0.92), 'beige': (0.82, 0.76, 0.66), 'rope': (0.55, 0.15, 0.12),
    'black': (0.05, 0.05, 0.06), 'gray': (0.55, 0.56, 0.58),
}
MATS = {}


def init_materials():
    for name, rgb in PALETTE.items():
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Base Color'].default_value = (*rgb, 1)
        bsdf.inputs['Roughness'].default_value = 0.5
        if name == 'steel':
            bsdf.inputs['Metallic'].default_value = 0.3  # xaritada atrof-muhit aksi yo'q — yuqori metallik qoraygan ko'rinadi
        m.diffuse_color = (*rgb, 1)
        MATS[name] = m


def _obj(name, bm, mats):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(MATS[m])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def box(size, loc, mat, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return _obj('box', bm, [mat])


def cyl(r, h, loc, mat, segs=10, rot=(0, 0, 0), r2=None, caps=True):
    """Silindr/konus: markazi loc, o'qi Z (rot bilan buriladi)"""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return _obj('cyl', bm, [mat])


def tube(a, b, r, mat, segs=6):
    """a→b quvur"""
    a, b = Vector(a), Vector(b)
    v = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=segs, radius1=r, radius2=r, depth=v.length)
    ob = _obj('tube', bm, [mat])
    ob.rotation_euler = v.to_track_quat('Z', 'Y').to_euler()
    ob.location = (a + b) / 2
    return ob


def sphere(r, loc, mat, segs=10):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=max(4, segs // 2), radius=r)
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    return _obj('sph', bm, [mat])


def lathe(profile, segs, mat, loc=(0, 0, 0), mats=None, mat_of=None):
    """Aylanma jism: profile [(radius, z)] pastdan tepaga"""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r < 1e-6:
            v = bm.verts.new((loc[0], loc[1], loc[2] + z))
            rings.append([v] * segs)
        else:
            rings.append([bm.verts.new((loc[0] + r * math.cos(2 * math.pi * k / segs),
                                        loc[1] + r * math.sin(2 * math.pi * k / segs), loc[2] + z)) for k in range(segs)])
    for i in range(len(profile) - 1):
        for k in range(segs):
            k2 = (k + 1) % segs
            vs = []
            for v in (rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]):
                if v not in vs:
                    vs.append(v)
            if len(vs) >= 3:
                f = bm.faces.new(vs)
                if mat_of:
                    f.material_index = mat_of(i, k)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj('lathe', bm, mats or [mat])


def pyramid_roof(w, d, h, loc, mat, overhang=0.15):
    """To'rt qiyali tom: asos w×d, balandligi h, markazi loc (asos sathi)"""
    x, y, z = loc
    hw, hd = w / 2 + overhang, d / 2 + overhang
    bm = bmesh.new()
    c = [bm.verts.new((x + sx * hw, y + sy * hd, z)) for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    top = bm.verts.new((x, y, z + h))
    for k in range(4):
        bm.faces.new([c[k], c[(k + 1) % 4], top])
    bm.faces.new(list(reversed(c)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj('roof', bm, [mat])


def leaf_roof(r, loc, mat, n=6, droop=0.45):
    """Palma barglari kabi tom: n ta egilgan uchburchak barg markazdan tashqariga"""
    x, y, z = loc
    bm = bmesh.new()
    top = bm.verts.new((x, y, z + 0.35))
    for k in range(n):
        a = 2 * math.pi * k / n
        a1, a2 = a - math.pi / n * 0.85, a + math.pi / n * 0.85
        mid = bm.verts.new((x + math.cos(a) * r * 0.55, y + math.sin(a) * r * 0.55, z + 0.15))
        tip = bm.verts.new((x + math.cos(a) * r, y + math.sin(a) * r, z - droop))
        l = bm.verts.new((x + math.cos(a1) * r * 0.6, y + math.sin(a1) * r * 0.6, z - droop * 0.3))
        rr = bm.verts.new((x + math.cos(a2) * r * 0.6, y + math.sin(a2) * r * 0.6, z - droop * 0.3))
        bm.faces.new([top, l, mid])
        bm.faces.new([top, mid, rr])
        bm.faces.new([l, tip, mid])
        bm.faces.new([mid, tip, rr])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj('leaf', bm, [mat])


def chute(pts, width, mat, wall=0.28):
    """Ochiq tarnov (to'g'ri yoki to'lqinli tepalik): pts — o'rta chiziq [(x,y,z)], U-kesim"""
    bm = bmesh.new()
    prof = [(-width / 2, wall), (-width / 2, 0), (width / 2, 0), (width / 2, wall)]
    rows = []
    for i, p in enumerate(pts):
        a = Vector(pts[max(0, i - 1)])
        b = Vector(pts[min(len(pts) - 1, i + 1)])
        t = (b - a).normalized()
        side = Vector((-t.y, t.x, 0)).normalized()
        rows.append([bm.verts.new(Vector(p) + side * sx + Vector((0, 0, sz))) for sx, sz in prof])
    for i in range(len(rows) - 1):
        for k in range(len(prof) - 1):
            bm.faces.new([rows[i][k], rows[i][k + 1], rows[i + 1][k + 1], rows[i + 1][k]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = _obj('chute', bm, [mat])
    mod = ob.modifiers.new('solid', 'SOLIDIFY')
    mod.thickness = 0.04
    return ob


def curve_tube(pts, r, mat, segs=10):
    """Egri yopiq quvur (tunnel-tepalik): pts [(x,y,z)]"""
    cu = bpy.data.curves.new('ct', 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = r
    cu.bevel_resolution = max(1, segs // 4)
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for i, (x, y, z) in enumerate(pts):
        sp.points[i].co = (x, y, z, 1)
    ob = bpy.data.objects.new('ct', cu)
    bpy.context.scene.collection.objects.link(ob)
    cu.materials.append(MATS[mat])
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target='MESH')
    return bpy.context.view_layer.objects.active


def spiral(cx, cy, r, z0, z1, turns, start=0.0, n=40):
    """Spiral nuqtalar (pastga tushuvchi slayd uchun): z0 tepada, z1 pastda"""
    return [(cx + r * math.cos(start + 2 * math.pi * turns * i / n), cy + r * math.sin(start + 2 * math.pi * turns * i / n),
             z0 + (z1 - z0) * i / n) for i in range(n + 1)]


def net(a, b, c, d, nu, nv, mat, r=0.015):
    """To'r: a-b-c-d to'rtburchak ichida nu × nv katak (arqon)"""
    A, B, C, D = map(Vector, (a, b, c, d))
    out = []
    for i in range(nu + 1):
        t = i / nu
        out.append(tube(A.lerp(B, t), D.lerp(C, t), r, mat, 4))
    for j in range(nv + 1):
        t = j / nv
        out.append(tube(A.lerp(D, t), B.lerp(C, t), r, mat, 4))
    return out


def ladder(x, y, z0, z1, w, yaw, mat, rung_mat=None):
    out = []
    c, s = math.cos(yaw), math.sin(yaw)
    for sx in (-w / 2, w / 2):
        out.append(tube((x + c * sx, y + s * sx, z0), (x + c * sx, y + s * sx, z1), 0.035, mat, 6))
    n = int((z1 - z0) / 0.3)
    for k in range(1, n + 1):
        z = z0 + k * 0.3
        out.append(tube((x - c * w / 2, y - s * w / 2, z), (x + c * w / 2, y + s * w / 2, z), 0.025, rung_mat or mat, 5))
    return out


def stairs(x0, y0, z1, run_dir, width, mat, rail_mat):
    """Zina: (x0,y0) pastki uchi, z1 tepasi, run_dir — tepaga yo'nalish (radian)"""
    out = []
    steps = max(3, int(z1 / 0.25))
    c, s = math.cos(run_dir), math.sin(run_dir)
    for k in range(steps):
        z = (k + 1) * z1 / steps
        out.append(box((0.3, width, 0.05), (x0 + c * k * 0.3, y0 + s * k * 0.3, z), mat, (0, 0, run_dir)))
    L = steps * 0.3
    for sd in (-1, 1):
        ox, oy = -s * width / 2 * sd, c * width / 2 * sd
        out.append(tube((x0 + ox, y0 + oy, 0.9), (x0 + c * L + ox, y0 + s * L + oy, z1 + 0.9), 0.03, rail_mat, 6))
        out.append(tube((x0 + ox, y0 + oy, 0), (x0 + ox, y0 + oy, 0.9), 0.03, rail_mat, 6))
    return out


def platform(x, y, z, w, d, posts_mat, deck_mat, post_h_extra=0.0, rails=True, rail_mat='steel', open_sides=()):
    """Maydoncha: 4 ustun (z+extra gacha), pol z sathida, atrofida to'siq ('n','s','e','w' — ochiq tomonlar)"""
    out = [box((w, d, 0.08), (x, y, z), deck_mat)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            out.append(box((0.12, 0.12, z + post_h_extra), (x + sx * w / 2, y + sy * d / 2, (z + post_h_extra) / 2), posts_mat))
    if rails:
        sides = {'s': ((x - w / 2, y - d / 2), (x + w / 2, y - d / 2)), 'n': ((x - w / 2, y + d / 2), (x + w / 2, y + d / 2)),
                 'w': ((x - w / 2, y - d / 2), (x - w / 2, y + d / 2)), 'e': ((x + w / 2, y - d / 2), (x + w / 2, y + d / 2))}
        for k, ((ax, ay), (bx, by)) in sides.items():
            if k in open_sides:
                continue
            out.append(tube((ax, ay, z + 0.8), (bx, by, z + 0.8), 0.03, rail_mat, 6))
            n = max(2, int(math.hypot(bx - ax, by - ay) / 0.2))
            for j in range(1, n):
                t = j / n
                out.append(box((0.025, 0.025, 0.75), (ax + (bx - ax) * t, ay + (by - ay) * t, z + 0.42), rail_mat))
    return out


def join(name, objs, origin=(0, 0, 0)):
    """Obyektlarni bittaga birlashtiradi; origin — shu nuqta (animatsiya o'qi uchun)"""
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    for o in objs:
        for m in list(o.modifiers):
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.context.scene.cursor.location = origin
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return ob


def empty(name, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.location = loc
    return e

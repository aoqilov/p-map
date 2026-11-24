"""
Bezak-binolar uchun umumiy Blender yordamchilari (src/decor/*/model.py dan import qilinadi).

    import sys; sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from blender_kit import Kit
    k = Kit(PALETTE)          # sahna tozalanadi, materiallar yaratiladi
    parts = [k.box(...), k.text(...)]
    k.finish('base', parts, HERE, cams)   # bitta obyekt → model.blend, model.glb, preview*.png

O'qlar: old tomon — Blender'da -Y, tepa — +Z, metr.
"""
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Euler, Vector


class Kit:
    def __init__(self, palette, glow=(), glass=(), glass_alpha=0.35):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self.scene = bpy.context.scene
        self.mats = {}
        for name, rgb in palette.items():
            m = bpy.data.materials.new(name)
            m.use_nodes = True
            bsdf = m.node_tree.nodes.get('Principled BSDF')
            bsdf.inputs['Base Color'].default_value = (*rgb, 1)
            bsdf.inputs['Roughness'].default_value = 0.15 if name in glass else 0.7
            if name in glass:
                bsdf.inputs['Alpha'].default_value = glass_alpha
            if name in glow:  # kechasi yonib turadigan belgilar
                bsdf.inputs['Emission Color'].default_value = (*rgb, 1)
                bsdf.inputs['Emission Strength'].default_value = 1.2
            m.diffuse_color = (*rgb, glass_alpha if name in glass else 1)
            self.mats[name] = m

    # ---------- primitivlar ----------
    def obj(self, name, bm, mat):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(self.mats[mat])
        ob = bpy.data.objects.new(name, me)
        self.scene.collection.objects.link(ob)
        return ob

    def box(self, size, loc, mat, rot=(0, 0, 0)):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=size, verts=bm.verts)
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
        bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
        return self.obj('box', bm, mat)

    def cyl(self, r, h, loc, mat, segs=12, rot=(0, 0, 0), r2=None):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Euler(rot, 'XYZ').to_matrix())
        bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
        return self.obj('cyl', bm, mat)

    def ball(self, r, loc, mat, sub=1, scale=(1, 1, 1)):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
        bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
        bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
        return self.obj('ball', bm, mat)

    def beam(self, a, b, w, d, mat):
        a, b = Vector(a), Vector(b)
        v = b - a
        ob = self.box((v.length, w, d), (0, 0, 0), mat)
        ob.rotation_euler = v.to_track_quat('X', 'Z').to_euler()
        ob.location = (a + b) / 2
        return ob

    def prism_x(self, pts, x0, x1, mat):
        """YZ tekislikdagi ko'pburchak (profil) → X bo'yicha x0..x1 prizma (tom, pandus)"""
        bm = bmesh.new()
        a = [bm.verts.new((x0, y, z)) for y, z in pts]
        b = [bm.verts.new((x1, y, z)) for y, z in pts]
        bm.faces.new(a)
        bm.faces.new(b[::-1])
        n = len(pts)
        for i in range(n):
            bm.faces.new([a[(i + 1) % n], a[i], b[i], b[(i + 1) % n]])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        return self.obj('prism', bm, mat)

    def prism_y(self, pts, y0, y1, mat):
        """XZ tekislikdagi ko'pburchak → Y bo'yicha y0..y1 prizma (old tomondagi shakllar: peshtoq, uchburchak frontón)"""
        bm = bmesh.new()
        a = [bm.verts.new((x, y0, z)) for x, z in pts]
        b = [bm.verts.new((x, y1, z)) for x, z in pts]
        bm.faces.new(a)
        bm.faces.new(b[::-1])
        n = len(pts)
        for i in range(n):
            bm.faces.new([a[(i + 1) % n], a[i], b[i], b[(i + 1) % n]])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        return self.obj('prism', bm, mat)

    def disc_y(self, r, y, z, x, t, mat, segs=24):
        """Old tomonga (−Y) qaragan yassi doira (belgi, dumaloq deraza)"""
        return self.cyl(r, t, (x, y, z), mat, segs=segs, rot=(math.pi / 2, 0, 0))

    def text(self, s, size, loc, mat, face='-Y', depth=0.03):
        """Yozuv (Blender shrifti → mesh). face: qaysi tomonga qaragan ('-Y' old, '+Y' orqa, '-X', '+X')"""
        cu = bpy.data.curves.new('txt', 'FONT')
        cu.body = s
        cu.size = size
        cu.extrude = depth / 2
        cu.align_x = 'CENTER'
        cu.align_y = 'CENTER'
        cu.resolution_u = 3
        ob = bpy.data.objects.new('txt', cu)
        self.scene.collection.objects.link(ob)
        rz = {'-Y': 0, '+Y': math.pi, '-X': -math.pi / 2, '+X': math.pi / 2}[face]
        ob.rotation_euler = (math.pi / 2, 0, rz)
        ob.location = loc
        bpy.ops.object.select_all(action='DESELECT')
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.convert(target='MESH')
        ob = bpy.context.view_layer.objects.active
        ob.data.materials.clear()
        ob.data.materials.append(self.mats[mat])
        return ob

    def frame_y(self, cx, y, cz, w, h, t, mat, depth=0.06):
        """XZ tekislikdagi to'rtburchak ramka (deraza, eshik)"""
        return [self.box((w + t, depth, t), (cx, y, cz + h / 2), mat), self.box((w + t, depth, t), (cx, y, cz - h / 2), mat),
                self.box((t, depth, h), (cx - w / 2, y, cz), mat), self.box((t, depth, h), (cx + w / 2, y, cz), mat)]

    def frame_x(self, x, cy, cz, w, h, t, mat, depth=0.06):
        """YZ tekislikdagi ramka (yon devordagi deraza)"""
        return [self.box((depth, w + t, t), (x, cy, cz + h / 2), mat), self.box((depth, w + t, t), (x, cy, cz - h / 2), mat),
                self.box((depth, t, h), (x, cy - w / 2, cz), mat), self.box((depth, t, h), (x, cy + w / 2, cz), mat)]

    # ---------- yakun ----------
    def join(self, name, objs):
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

    def finish(self, tag, parts, here: Path, cams):
        """Bitta `base` obyekt → model.blend, model.glb; Workbench preview(lar). cams: [(fayl, kamera joyi, qaragan nuqta)]"""
        argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
        preview_dir = Path(argv[0]) if argv else here
        base = self.join('base', parts)
        tris = sum(len(pg.vertices) - 2 for pg in base.data.polygons)
        xs = [v.co.x for v in base.data.vertices]
        ys = [v.co.y for v in base.data.vertices]
        zs = [v.co.z for v in base.data.vertices]
        print(f'{tag} tris={tris} x={min(xs):.2f}..{max(xs):.2f} y={min(ys):.2f}..{max(ys):.2f} top={max(zs):.2f}')
        bpy.ops.wm.save_as_mainfile(filepath=str(here / 'model.blend'))
        bpy.ops.export_scene.gltf(filepath=str(here / 'model.glb'), export_format='GLB', export_apply=True, export_yup=True)
        print(f'{tag} glb={(here / "model.glb").stat().st_size // 1024} KB')

        scene = self.scene
        cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
        scene.collection.objects.link(cam)
        scene.camera = cam
        scene.render.engine = 'BLENDER_WORKBENCH'
        scene.display.shading.light = 'STUDIO'
        scene.display.shading.color_type = 'MATERIAL'
        scene.display.shading.show_shadows = True
        scene.display.shading.show_cavity = True
        scene.render.resolution_x, scene.render.resolution_y = 1100, 800
        world = bpy.data.worlds.new('w')
        world.color = (0.9, 0.92, 0.95)
        scene.world = world
        for fname, loc, tgt in cams:
            cam.location = loc
            cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
            scene.render.filepath = str(preview_dir / fname)
            bpy.ops.render.render(write_still=True)
            print(tag, 'preview', scene.render.filepath)

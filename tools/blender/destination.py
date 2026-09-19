"""The three destination worlds. Artistic interpretations of a region's character, not reconstructions
of real sites: no named landmark is copied.

    blender --factory-startup --background --python tools/blender/destination.py -- world=alula|najd|aseer mode=preview|all aspect=land|port
"""
import bpy, bmesh, math, os, sys, random
sys.path.insert(0, os.path.dirname(__file__))
import common as C, worlds as W
from mathutils import Vector, noise

A = C.args()
WORLD = A.get("world", "alula"); MODE = A.get("mode", "preview"); ASPECT = A.get("aspect", "land")
s = C.reset()
leaf = C.leaf_material(); bark = C.bark_material()
PORT = ASPECT == "port"
res = (1440, 2560) if PORT else (2560, 1440)


def flat(name, color, rough=0.8, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    if emit: b.inputs["Emission Color"].default_value = (*color, 1); b.inputs["Emission Strength"].default_value = emit
    return m


def box(name, loc, size, mat, taper=0.0, rot=0.0):
    """A wall mass; taper leans the faces inwards towards the top (battered earth walls, stone towers)."""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        k = 1 - taper * (v.co.z + 0.5)
        v.co = Vector((v.co.x * size[0] * k, v.co.y * size[1] * k, (v.co.z + 0.5) * size[2]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    o = C.link(bpy.data.objects.new(name, me)); o.location = loc; o.rotation_euler = (0, 0, math.radians(rot))
    return o


def blob(name, loc, radius, mat, seed=1, squash=0.8, detail=3, rough=0.35):
    """A noisy ball: shrubs, tree crowns, cloud cores."""
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=detail, radius=1.0)
    for v in bm.verts:
        n = noise.fractal(v.co * 1.7 + Vector((seed, seed * 2, 0)), 1.0, 2.0, 3)
        v.co *= 1 + rough * n
        v.co.z *= squash
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    me.materials.append(mat)
    o = C.link(bpy.data.objects.new(name, me)); o.location = loc; o.scale = (radius,) * 3
    return o


def near_fronds(spots):
    for i, (loc, rot) in enumerate(spots):
        me = C.frond_mesh(f"NearFrond{i}", length=3.4, leaflets=70, droop=1.2, seed=70 + i, leaflet_len=0.7, mat=leaf)
        o = C.link(bpy.data.objects.new(f"NearFrond{i}", me)); o.location = loc; o.rotation_euler = [math.radians(r) for r in rot]; o.pass_index = 1


# =================================================================== ALULA: a sandstone valley at the end of the day
def alula():
    sun = math.radians(-58)
    C.sky("qwantani_late_afternoon_puresky_4k.hdr", sun, strength=0.95, sun_strength=8.5, sun_color=(1.0, 0.70, 0.42), sun_angle=1.2, sun_el=math.radians(11))
    rock = W.strata_material("Sandstone", "sandstone_cracks", scale=0.05, light=(0.74, 0.47, 0.30), dark=(0.36, 0.18, 0.11), band=0.13)   # natural cracked sandstone (the wall texture is masonry)
    sand = W.sand_material(tint=(1.0, 0.74, 0.50))

    def h(x, y):
        valley = 1 - math.exp(-(x / 85) ** 2)
        return 7 * C.fbm(x, y, 160, 3, 4.0) * valley + 2.4 * abs(C.fbm(x + 0.4 * y, y, 40, 3, 9.0)) * (0.3 + valley) + 0.25 * C.fbm(x, y, 8, 2, 1.0)
    C.terrain("Ground", size=(1100, 1500), center=(0, 640), res=(300, 420), height=h, mat=sand)
    # the valley walls step back into the distance on both sides; the way between them is the destination
    for i, (x, y, r, hh, sq, seed) in enumerate([(-150, 150, 55, 150, (1.0, 1.6), 31), (165, 210, 60, 175, (1.0, 1.5), 33), (-200, 330, 80, 200, (1.1, 1.3), 35), (215, 430, 90, 185, (1.2, 1.2), 37),
                                                 (-230, 560, 110, 210, (1.3, 1.0), 39), (120, 700, 70, 240, (0.9, 0.9), 41), (300, 820, 130, 180, (1.5, 0.9), 43), (-60, 1050, 150, 160, (1.8, 0.8), 45), (-420, 900, 140, 150, (1.6, 0.9), 47)]):
        W.butte(f"Wall{i}", (x, y, -5), radius=r, height=hh, seed=seed, mat=rock, squash=sq, ledges=7, talus=0.26, flute=0.26)
    # a free-standing weathered tower in the open, the kind of form wind leaves behind
    W.butte("Tower", (-18, 300, -2), radius=15, height=82, seed=51, mat=rock, squash=(1.0, 0.8), ledges=9, talus=0.2, flute=0.32, top_noise=0.12)
    rnd = random.Random(5)
    for i in range(16):
        x = rnd.uniform(-46, 40); y = rnd.uniform(60, 250)
        C.palm(f"Palm{i}", (x, y, h(x, y) - 0.2), height=rnd.uniform(7.5, 12), fronds=28, seed=200 + i, leaf=leaf, bark=bark)
    boulder = C.load_scan("namaqualand_boulder_04"); blocks = C.load_scan("namaqualand_boulder_02")
    for t_ in (boulder, blocks): C.warm_scan_material(t_, tint=(0.62, 0.42, 0.30), amount=0.25, value=0.62, sat=0.55)
    C.place(boulder, (-5.2, 9, 0.9), rot=(0, 0, 30), scale=1.7); C.place(blocks, (5.5, 7.5, 0.4), rot=(0, 0, -60), scale=1.5); C.place(blocks, (-2.5, 15, 0.2), rot=(0, 0, 100), scale=0.7)
    for i in range(40):
        x = rnd.uniform(-50, 50); y = rnd.uniform(14, 150)
        C.place(rnd.choice((blocks, boulder)), (x, y, h(x, y)), rot=(rnd.uniform(-20, 20), rnd.uniform(-20, 20), rnd.uniform(0, 360)), scale=rnd.uniform(0.08, 0.5), name=f"Stone{i}")
    near_fronds([((-4.6, 6.5, 6.2), (-38, 10, -50)), ((-5.2, 7.5, 7.0), (-55, -6, -20))] if not PORT else [((-3.2, 6.5, 8.2), (-40, 10, -50)), ((3.4, 7.0, 8.6), (-46, -8, 48))])
    C.haze(size=(2600, 3000, 90), center=(0, 1500, 40), density=0.0011, color=(1.0, 0.80, 0.58), anisotropy=0.75)
    C.haze(size=(2600, 3000, 300), center=(0, 1500, 240), density=0.00012, color=(0.95, 0.88, 0.82), anisotropy=0.6)
    return (Vector((0.6, 0, 1.8)), Vector((10, 300, 34 if not PORT else 58)), 24 if not PORT else 20, -0.75)


# =================================================================== NAJD: an earth-built courtyard, palms behind the walls
def najd():
    sun = math.radians(-66)
    C.sky("kloppenheim_06_puresky_4k.hdr", sun, strength=0.85, sun_strength=8.0, sun_color=(1.0, 0.74, 0.50), sun_angle=1.0, sun_el=math.radians(26))
    mud = C.pbr("Mud", "clay_plaster", scale=0.22, tint=(0.80, 0.58, 0.40))
    mud2 = C.pbr("Mud2", "clay_plaster", scale=0.31, tint=(0.70, 0.49, 0.33))
    earth = C.pbr("Earth", "dry_ground_rocks", scale=0.30, tint=(0.95, 0.78, 0.60), triplanar=False)
    gyps = flat("Gypsum", (0.92, 0.88, 0.80), 0.7); dark = flat("Void", (0.02, 0.015, 0.01), 1.0)
    wood = flat("Wood", (0.16, 0.09, 0.05), 0.6); paint = [flat("PaintR", (0.55, 0.12, 0.08)), flat("PaintG", (0.10, 0.30, 0.18)), flat("PaintY", (0.80, 0.58, 0.16))]
    C.terrain("Ground", size=(500, 700), center=(0, 250), res=(140, 200), height=lambda x, y: 0.05 * C.fbm(x, y, 3, 2, 1.0), mat=earth)

    def house(x, y, w, d, hh, rot=0, m=mud, door=False, seed=1):
        rnd = random.Random(seed)
        body = box(f"House{seed}", (x, y, 0), (w, d, hh), m, taper=0.07, rot=rot)
        k = 1 - 0.07
        # gypsum band under the parapet, then the stepped triangular crenellations along the top
        band = box(f"Band{seed}", (0, 0, hh - 1.0), (w * k + 0.06, d * k + 0.06, 0.28), gyps); band.parent = body
        nb = max(4, int(w / 0.75))
        for i in range(nb):
            be = box(f"Be{seed}_{i}", ((i + 0.5) / nb * w * k - w * k / 2, -d * k / 2 - 0.16, hh - 1.55), (0.13, 0.36, 0.13), wood); be.parent = body
        n = max(3, int(w / 0.9))
        for i in range(n):
            for side in (-1, 1):
                for step in range(3):
                    c = box(f"Cr{seed}_{i}_{side}_{step}", ((i + 0.5) / n * w * k - w * k / 2, side * (d * k / 2 - 0.14), hh + step * 0.2), (w * k / n * (0.78 - step * 0.26), 0.28, 0.2), m); c.parent = body
        # rows of small triangular vents, read as dark triangles on the face turned to the yard
        rows = 2 if hh > 6 else 1
        for r in range(rows):
            cnt = max(2, int(w / 1.6))
            for i in range(cnt):
                bmv = bmesh.new(); a_, b_, c_ = bmv.verts.new((-0.16, 0, 0)), bmv.verts.new((0.16, 0, 0)), bmv.verts.new((0, 0, 0.30)); bmv.faces.new((a_, b_, c_))
                me = bpy.data.meshes.new("Vent"); bmv.to_mesh(me); bmv.free(); me.materials.append(dark)
                v = C.link(bpy.data.objects.new(f"Vent{seed}_{r}_{i}", me)); v.parent = body
                v.location = ((i + 0.5) / cnt * w * 0.8 - w * 0.4, -d / 2 * (1 - 0.07 * (hh - 2.2 - r * 0.9) / hh) - 0.02, hh - 2.2 - r * 0.9)
        if door:
            dr = box(f"Door{seed}", (0, -d / 2 - 0.03, 0), (1.25, 0.10, 2.35), wood); dr.parent = body
            for j in range(3):
                for i2 in range(2):
                    p = box(f"Pn{seed}_{j}_{i2}", ((i2 - 0.5) * 0.52, -d / 2 - 0.10, 0.35 + j * 0.62), (0.40, 0.04, 0.44), rnd.choice(paint)); p.parent = body
            fr = box(f"Frame{seed}", (0, -d / 2 - 0.01, 0), (1.6, 0.08, 2.62), gyps); fr.parent = body
        return body
    # the yard: houses around an open court, a lane leading away between them
    house(-10.5, 19, 11, 8, 8.2, rot=14, door=True, seed=1); house(11.5, 22, 10, 9, 10.8, rot=-12, m=mud2, door=True, seed=2)
    house(-1, 44, 12, 9, 13.5, rot=3, m=mud2, door=True, seed=3); house(15, 48, 9, 9, 9.0, rot=-5, seed=4); house(-17, 42, 9, 9, 7.4, rot=10, seed=5)
    house(-24, 16, 8, 12, 6.4, rot=80, seed=6); house(25, 18, 8, 12, 7.2, rot=-82, m=mud, seed=7); house(4, 72, 18, 10, 9.0, seed=8); house(-26, 70, 12, 10, 11.0, rot=5, m=mud2, seed=9)
    # a low yard wall with a gap, and the doorway we look through: its jambs and lintel frame the picture, in shade
    jw = 2.1 if not PORT else 1.5
    box("JambL", (-jw - 1.2, 3.2, 0), (2.4, 1.4, 7), mud2); box("JambR", (jw + 1.2, 3.2, 0), (2.4, 1.4, 7), mud2); box("Lintel", (0, 3.2, 4.4 if not PORT else 6.2), (2 * jw + 5, 1.4, 3), mud2)
    for i in range(7): box(f"Beam{i}", (-jw + i * (2 * jw / 6), 3.2, (4.4 if not PORT else 6.2) - 0.16), (0.16, 1.8, 0.16), wood)
    rnd = random.Random(8)
    for i, (x, y) in enumerate([(-3.5, 27), (4.5, 31), (-19, 30), (21, 33), (8, 58), (-9, 60), (24, 62), (-30, 52), (34, 50), (-4, 92), (14, 98), (-38, 100), (40, 90)]):
        C.palm(f"Palm{i}", (x, y, 0), height=rnd.uniform(9, 14), fronds=28, seed=300 + i, leaf=leaf, bark=bark)
    # far off in the haze: a few plain contemporary towers. Generic forms, not portraits of real buildings
    glass = flat("Glass", (0.42, 0.50, 0.56), 0.25)
    for i, (x, y, w, hh) in enumerate([(-120, 1500, 46, 300), (40, 1700, 60, 380), (170, 1600, 40, 240), (-260, 1800, 70, 210), (300, 1900, 54, 330)]):
        box(f"Tower{i}", (x, y, 0), (w, w, hh), glass, taper=0.35 if i % 2 else 0.1)
    near_fronds([((3.0, 6.4, 5.4), (-42, -8, 58))] if not PORT else [((2.4, 6.4, 7.0), (-42, -8, 58)), ((-2.6, 6.0, 7.4), (-50, 8, -52))])
    C.haze(size=(3000, 3400, 120), center=(0, 1700, 55), density=0.00065, color=(1.0, 0.86, 0.68), anisotropy=0.7)
    bl = bpy.data.lights.new("Bounce", "AREA"); bl.energy = 900; bl.color = (1.0, 0.74, 0.5); bl.size = 8
    bo = C.link(bpy.data.objects.new("Bounce", bl)); bo.location = (0, 9, 0.5); bo.rotation_euler = (math.radians(-100), 0, 0); bo.visible_camera = False
    return (Vector((0.4, -1.2, 1.7)), Vector((0.5, 60, 6.5 if not PORT else 11)), 22 if not PORT else 19, -0.55)


# =================================================================== ASEER: green ridges, terraces and cloud in the valleys
def aseer():
    sun = math.radians(-40)
    C.sky("kloofendal_48d_partly_cloudy_puresky_4k.hdr", sun, strength=0.9, sun_strength=5.5, sun_color=(1.0, 0.84, 0.66), sun_angle=1.6, sun_el=math.radians(24))
    rockm = C.pbr("Rock", "worn_rock_natural_01", scale=0.05, tint=(0.80, 0.70, 0.58))
    nt = rockm.node_tree; bsdf = nt.nodes["Principled BSDF"]
    # slopes turn green where they are not too steep: grass and low scrub over the rock
    src = bsdf.inputs["Base Color"].links[0].from_socket
    geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Normal"], sep.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.05; nz.inputs["Detail"].default_value = 6
    addn = nt.nodes.new("ShaderNodeMath"); addn.operation = "ADD"; nt.links.new(sep.outputs["Z"], addn.inputs[0]); nt.links.new(nz.outputs["Fac"], addn.inputs[1])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].position = 1.02; ramp.color_ramp.elements[1].position = 1.22
    nt.links.new(addn.outputs[0], ramp.inputs["Fac"])
    gcol = nt.nodes.new("ShaderNodeValToRGB"); gcol.color_ramp.elements[0].color = (0.05, 0.11, 0.04, 1); gcol.color_ramp.elements[1].color = (0.20, 0.30, 0.09, 1)
    gn = nt.nodes.new("ShaderNodeTexNoise"); gn.inputs["Scale"].default_value = 0.6; gn.inputs["Detail"].default_value = 8; nt.links.new(gn.outputs["Fac"], gcol.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; nt.links.new(ramp.outputs["Color"], mix.inputs["Factor"]); nt.links.new(src, mix.inputs["A"]); nt.links.new(gcol.outputs["Color"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])

    def h(x, y):
        ridge = 1 - abs(C.fbm(x, y, 520, 4, 3.0)) * 2.0
        base = 230 * ridge * min(1.0, max(0.0, (y - 40) / 500)) + 60 * C.fbm(x, y, 160, 4, 8.0) + 9 * C.fbm(x, y, 38, 3, 2.0)
        drop = -46 * math.exp(-((y - 150) / 120) ** 2) * math.exp(-((x - 20) / 170) ** 2)          # the valley we look across
        z = base + drop - 0.10 * max(0.0, y - 30)
        if 30 < y < 330 and z > -60: z = math.floor(z / 3.2) * 3.2 * 0.75 + z * 0.25                # farmed terraces on the near slopes
        near = math.exp(-(y / 26) ** 2) * math.exp(-(x / 40) ** 2)
        return z * (1 - near) + 0.4 * C.fbm(x, y, 5, 2, 1.0) * near
    C.terrain("Ground", size=(2600, 3000), center=(0, 1380), res=(420, 480), height=h, mat=rockm)
    green = flat("Juniper", (0.035, 0.085, 0.035), 0.9); green2 = flat("Scrub", (0.10, 0.17, 0.06), 0.9)
    rnd = random.Random(12)
    # junipers: five shared shapes (three stacked noisy crowns), scattered by the hundred so they read as cover, not as objects
    lib = []
    for v in range(5):
        parts = [blob(f"JP{v}_{q}", (0, 0, 0.6 + q * 0.85), 1.0 - q * 0.26, green if v % 2 else green2, seed=v * 7 + q, squash=1.25, detail=2, rough=0.5) for q in range(3)]
        bpy.ops.object.select_all(action="DESELECT")
        for o_ in parts: o_.select_set(True)
        bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join(); t_ = bpy.context.view_layer.objects.active
        for c_ in list(t_.users_collection): c_.objects.unlink(t_)
        lib.append(t_)
    for i in range(1500):
        x = rnd.uniform(-420, 420); y = rnd.uniform(16, 900); z = h(x, y)
        if h(x + 2, y) - z > 2.4 or z < -55: continue                                                # not on cliffs, not under the cloud
        C.place(rnd.choice(lib), (x, y, z - 0.2), rot=(0, 0, rnd.uniform(0, 360)), scale=rnd.uniform(1.1, 2.6), name=f"Tree{i}")
    # tower houses of stone and earth: tapered, small white-framed windows, a pale band at the crown
    stone = C.pbr("Stone", "rock_wall_08", scale=0.5, tint=(0.70, 0.62, 0.52)); white = flat("Lime", (0.93, 0.92, 0.88), 0.7); void = flat("Void", (0.02, 0.02, 0.02), 1)
    for k, (x, y, w, hh, rot) in enumerate([(-13, 34, 7.5, 15, 14), (-3, 43, 6.5, 19, -8), (8, 38, 7, 13, 22), (-25, 50, 6, 12, -15), (20, 52, 6, 16, 8)]):
        z = h(x, y) - 0.6
        b = box(f"Qasaba{k}", (x, y, z), (w, w, hh), stone, taper=0.16, rot=rot)
        crown = box(f"Crown{k}", (0, 0, hh - 1.1), (w * 0.86, w * 0.86, 0.5), white); crown.parent = b
        for fl in range(int(hh // 3.4)):
            for i in range(2):
                zz = 2.4 + fl * 3.3; kk = 1 - 0.16 * zz / hh
                fr = box(f"WinF{k}_{fl}_{i}", ((i - 0.5) * w * 0.42 * kk, -w / 2 * kk - 0.03, zz), (0.95, 0.10, 1.25), white); fr.parent = b
                wn = box(f"Win{k}_{fl}_{i}", ((i - 0.5) * w * 0.42 * kk, -w / 2 * kk - 0.09, zz + 0.16), (0.55, 0.06, 0.9), void); wn.parent = b
    # dry-stone wall and rock at our feet
    boulder = C.load_scan("namaqualand_boulder_04"); blocks = C.load_scan("namaqualand_boulder_02")
    for i in range(22): C.place(blocks, (-9 + i * 0.95 + rnd.uniform(-0.2, 0.2), 7.5 + 0.05 * i + rnd.uniform(-0.2, 0.2), 0.25), rot=(rnd.uniform(-10, 10), 0, rnd.uniform(0, 360)), scale=rnd.uniform(0.45, 0.7), name=f"WallStone{i}")
    C.place(boulder, (-7.5, 5.2, 0.7), rot=(0, 0, 60), scale=1.5)
    for i in range(9): blob(f"NearShrub{i}", (rnd.uniform(-11, 11), rnd.uniform(5, 13), 0.5), rnd.uniform(0.6, 1.3), green2, seed=900 + i, detail=3)
    # cloud lying in the valleys: a wide slab of uneven vapour, thickest low down
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 1100, -62)); cl = bpy.context.object; cl.name = "HazeCloud"; cl.scale = (3000, 2100, 110)
    cm = bpy.data.materials.new("Cloud"); cm.use_nodes = True; cnt = cm.node_tree; cnt.nodes.clear()
    vol = cnt.nodes.new("ShaderNodeVolumePrincipled"); out = cnt.nodes.new("ShaderNodeOutputMaterial"); vol.inputs["Color"].default_value = (0.95, 0.96, 0.98, 1); vol.inputs["Anisotropy"].default_value = 0.35
    n1 = cnt.nodes.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = 3.2; n1.inputs["Detail"].default_value = 7; n1.inputs["Roughness"].default_value = 0.62
    tc = cnt.nodes.new("ShaderNodeTexCoord"); cnt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    sepz = cnt.nodes.new("ShaderNodeSeparateXYZ"); cnt.links.new(tc.outputs["Object"], sepz.inputs[0])
    low = cnt.nodes.new("ShaderNodeMapRange"); low.inputs["From Min"].default_value = -0.5; low.inputs["From Max"].default_value = 0.5; low.inputs["To Min"].default_value = 1.0; low.inputs["To Max"].default_value = 0.0; cnt.links.new(sepz.outputs["Z"], low.inputs["Value"])
    rmp = cnt.nodes.new("ShaderNodeValToRGB"); rmp.color_ramp.elements[0].position = 0.50; rmp.color_ramp.elements[1].position = 0.70; cnt.links.new(n1.outputs["Fac"], rmp.inputs["Fac"])
    mul = cnt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; cnt.links.new(rmp.outputs["Color"], mul.inputs[0]); cnt.links.new(low.outputs["Result"], mul.inputs[1])
    dens = cnt.nodes.new("ShaderNodeMath"); dens.operation = "MULTIPLY"; dens.inputs[1].default_value = 0.05; cnt.links.new(mul.outputs[0], dens.inputs[0])
    cnt.links.new(dens.outputs[0], vol.inputs["Density"]); cnt.links.new(vol.outputs["Volume"], out.inputs["Volume"]); cl.data.materials.append(cm); cl.visible_shadow = False
    C.haze(size=(4000, 4200, 500), center=(0, 2000, 150), density=0.00028, color=(0.80, 0.86, 0.92), anisotropy=0.5)
    return (Vector((0.5, 0, 2.4)), Vector((-4, 200, -4 if not PORT else 30)), 25 if not PORT else 20, -0.35)


p, look, lens, ev = {"alula": alula, "najd": najd, "aseer": aseer}[WORLD]()
C.camera(p, look, lens=lens)
s.view_settings.exposure = float(A.get("ev", ev))
base = os.path.join(C.ROOT, "renders", WORLD); os.makedirs(base, exist_ok=True)
if MODE == "preview":
    C.render(os.path.join(base, f"preview-{ASPECT}.png"), (res[0] * 3 // 8, res[1] * 3 // 8), samples=40)
else:
    C.render(os.path.join(base, f"{ASPECT}-still0.png"), res, samples=160)
    C.render(os.path.join(base, f"{ASPECT}-data0.png"), res, data=True)

"""Procedural large-scale pieces shared by the worlds: sandstone buttes, dunes, sand and rock materials."""
import bpy, bmesh, math, random
from mathutils import Vector, noise
import common as C


def strata_material(name="Sandstone", tex="red_sandstone_wall", scale=0.045, light=(0.86, 0.58, 0.38), dark=(0.42, 0.22, 0.13), band=0.11):
    """Photographed sandstone, modulated by horizontal colour beds so big forms read as layered rock."""
    m = C.pbr(name, tex, scale=scale)
    nt = m.node_tree; bsdf = nt.nodes["Principled BSDF"]
    src = bsdf.inputs["Base Color"].links[0].from_socket
    geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.02; nz.inputs["Detail"].default_value = 3
    add = nt.nodes.new("ShaderNodeMath"); add.operation = "MULTIPLY_ADD"; add.inputs[1].default_value = band; add.inputs[2].default_value = 0
    warp = nt.nodes.new("ShaderNodeMath"); warp.operation = "ADD"
    wave = nt.nodes.new("ShaderNodeTexNoise"); wave.noise_dimensions = "1D"; wave.inputs["Scale"].default_value = 1.0; wave.inputs["Detail"].default_value = 6; wave.inputs["Roughness"].default_value = 0.7
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].position = 0.3; ramp.color_ramp.elements[0].color = (*dark, 1); ramp.color_ramp.elements[1].position = 0.72; ramp.color_ramp.elements[1].color = (*light, 1)
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "OVERLAY"; mix.inputs["Factor"].default_value = 0.85
    nt.links.new(geo.outputs["Position"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], add.inputs[0])
    nt.links.new(geo.outputs["Position"], nz.inputs["Vector"]); nt.links.new(add.outputs[0], warp.inputs[0]); nt.links.new(nz.outputs["Fac"], warp.inputs[1])
    nt.links.new(warp.outputs[0], wave.inputs["W"]); nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(src, mix.inputs["A"]); nt.links.new(ramp.outputs["Color"], mix.inputs["B"]); nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    # beds also catch light: a gentle bump from the same signal
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.5; bump.inputs["Distance"].default_value = 1.5
    nt.links.new(wave.outputs["Fac"], bump.inputs["Height"])
    if bsdf.inputs["Normal"].links: nt.links.new(bsdf.inputs["Normal"].links[0].from_socket, bump.inputs["Normal"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def butte(name, loc, radius=40, height=110, seed=1, mat=None, squash=(1.0, 1.0), talus=0.30, flute=0.16, ledges=6, top_noise=0.06, seg=160, rings=90):
    """A free-standing sandstone mass: talus skirt, fluted vertical walls broken by ledges, weathered cap.
    An artistic form in the spirit of north-western Arabian sandstone country, not a copy of a named landmark."""
    rnd = random.Random(seed); s = seed * 13.37
    bm = bmesh.new(); grid = []
    ledge_z = sorted(rnd.uniform(0.32, 0.92) for _ in range(ledges))
    for k in range(rings + 1):
        v = k / rings; z = height * v
        if v < talus:                                   # skirt of fallen sand and rock
            prof = 1.0 + (1 - v / talus) ** 1.6 * 0.95
        else:
            prof = 1.0 - 0.10 * ((v - talus) / (1 - talus)) ** 2
            for lz in ledge_z:
                if v > lz: prof -= 0.035 + 0.03 * noise.noise(Vector((lz * 9, s, 0)))
        row = []
        for i in range(seg):
            th = 2 * math.pi * i / seg
            foot = 1 + 0.30 * noise.noise(Vector((math.cos(th) * 0.9 + s, math.sin(th) * 0.9, 0.0))) + 0.12 * noise.noise(Vector((math.cos(th) * 2.6, math.sin(th) * 2.6 + s, 1.0)))
            wall = 0 if v < talus else 1
            fl = flute * wall * noise.fractal(Vector((math.cos(th) * 5.5, math.sin(th) * 5.5, v * 0.55 + s)), 1.0, 2.0, 4)
            crumble = 0.05 * noise.noise(Vector((math.cos(th) * 14, math.sin(th) * 14, v * 11 + s)))
            r = radius * prof * foot * (1 + fl + crumble)
            zz = z + (height * top_noise * noise.noise(Vector((math.cos(th) * 2 + s, math.sin(th) * 2, 3.0))) if v > 0.97 else 0)
            row.append(bm.verts.new((math.cos(th) * r * squash[0], math.sin(th) * r * squash[1], zz)))
        grid.append(row)
    for k in range(rings):
        for i in range(seg):
            bm.faces.new((grid[k][i], grid[k][(i + 1) % seg], grid[k + 1][(i + 1) % seg], grid[k + 1][i]))
    cap = bm.verts.new((0, 0, height * (1 + 0.02)))
    for i in range(seg): bm.faces.new((grid[rings][i], grid[rings][(i + 1) % seg], cap))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    if mat: me.materials.append(mat)
    ob = C.link(bpy.data.objects.new(name, me)); ob.location = loc; ob.rotation_euler = (0, 0, rnd.uniform(0, 6.28))
    return ob


def sand_material(name="Sand", tex="sand_01", scale=0.22, tint=(1.0, 0.80, 0.58)):
    m = C.pbr(name, tex, scale=scale, tint=tint, triplanar=False)
    nt = m.node_tree; bsdf = nt.nodes["Principled BSDF"]
    # wind ripples as bump, stronger on open ground
    w = nt.nodes.new("ShaderNodeTexWave"); w.inputs["Scale"].default_value = 2.2; w.inputs["Distortion"].default_value = 6; w.inputs["Detail"].default_value = 2
    tc = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tc.outputs["Object"], w.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.22; bump.inputs["Distance"].default_value = 0.05
    nt.links.new(w.outputs["Fac"], bump.inputs["Height"])
    if bsdf.inputs["Normal"].links: nt.links.new(bsdf.inputs["Normal"].links[0].from_socket, bump.inputs["Normal"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.85
    return m


def passage(name, y0=-16.0, y1=17.0, half_width=3.4, height=7.6, seed=2, mat=None, seg=200, rows=240):
    """The inside of a rock threshold: an irregular arched way through bedded sandstone, seen only from within.
    Bedding is made by displacing with noise that is stretched flat, so ledges and overhangs run horizontally."""
    s = seed * 7.13
    bm = bmesh.new(); grid = []
    for j in range(rows + 1):
        v = j / rows; y = y0 + (y1 - y0) * v
        w = half_width * (1 + 0.22 * noise.noise(Vector((y * 0.11, s, 0))) + 0.35 * (1 - v) ** 2)     # a little wider behind the viewer
        h = height * (1 + 0.18 * noise.noise(Vector((y * 0.09, s + 4, 1))))
        cx = 0.9 * noise.noise(Vector((y * 0.07, s + 9, 2)))
        mouth = max(0.0, (v - 0.80) / 0.20)                                                        # the mouth flares and breaks up
        row = []
        for i in range(seg + 1):
            u = i / seg; ph = math.pi * u
            x = cx + w * math.cos(ph) * (1 + 0.25 * mouth); z = h * (math.sin(ph) ** 0.62) * (1 + 0.35 * mouth)
            p = Vector((x, y, z))
            n = Vector((math.cos(ph), 0, math.sin(ph) * 0.9)).normalized()                         # outward from the void
            # flat-lying beds: a slow warp of height, turned into rounded shelves (hard bed out, soft bed in)
            zw = p.z * 0.95 + 1.1 * noise.noise(Vector((p.x * 0.10 + s, p.y * 0.10, p.z * 0.05)))
            ft = zw - math.floor(zw)
            shelf = (ft * ft * (3 - 2 * ft)) if ft < 0.5 else 1 - ((ft - 0.5) * 2) ** 3 * 0.0 - 0.0
            shelf = math.sin(ft * math.pi) ** 0.55                                                  # 0 at bed planes, 1 mid-bed
            thick = 0.5 + 0.5 * noise.noise(Vector((math.floor(zw) * 3.7 + s, 0, 0)))               # each bed weathers differently
            block = noise.noise(Vector((p.x * 0.22, p.y * 0.22 + s, p.z * 0.18)))                   # big alcoves and buttresses
            fine = noise.fractal(Vector((p.x * 0.9 + s, p.y * 0.9, p.z * 2.4)), 1.0, 2.0, 3)
            d = 0.75 * shelf * (0.35 + thick) + 1.25 * block + 0.10 * fine + mouth * 1.6 * noise.noise(Vector((u * 7 + s, y * 0.4, 5)))
            row.append(bm.verts.new(p + n * d))
        grid.append(row)
    for j in range(rows):
        for i in range(seg):
            bm.faces.new((grid[j][i + 1], grid[j][i], grid[j + 1][i], grid[j + 1][i + 1]))
    # close the back so no sky leaks in from behind the viewer
    back = bm.verts.new((0, y0 - 1, height * 0.4))
    for i in range(seg): bm.faces.new((grid[0][i], grid[0][i + 1], back))
    for _ in range(2): bmesh.ops.smooth_vert(bm, verts=bm.verts, factor=0.5)               # wind-worn, not shattered
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    if mat: me.materials.append(mat)
    return C.link(bpy.data.objects.new(name, me))

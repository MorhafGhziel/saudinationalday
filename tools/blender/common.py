"""Shared scene-building helpers for the «حكايتنا واحدة» worlds (Blender 5.2, Cycles, headless).

Every world is built from CC0 Poly Haven scans (see ASSETS.md) plus procedural palms, terrain and haze
made here. Nothing is hand-modelled in the UI, so every render can be reproduced from these scripts.
"""
import bpy, bmesh, math, os, random, sys
from mathutils import Vector, Matrix, Euler, noise

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "assets-src", "polyhaven")


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return dict(x.split("=", 1) for x in a if "=" in x)


# ------------------------------------------------------------------ scene / render setup
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
    s.cycles.device = "GPU"
    s.cycles.use_adaptive_sampling = True
    s.cycles.adaptive_threshold = 0.02
    s.cycles.use_denoising = True
    s.cycles.denoiser = "OPTIX"
    s.cycles.max_bounces = 6
    s.cycles.volume_bounces = 1
    s.cycles.volume_step_rate = 2.0
    s.cycles.use_auto_tile = False     # this PC has no page file: keep peak memory low
    s.render.film_transparent = False
    s.view_settings.view_transform = "AgX"
    s.view_settings.look = "AgX - Medium High Contrast"
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_depth = "16"
    s.world = bpy.data.worlds.new("World")
    return s


def collection(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def link(obj, col=None):
    (col or bpy.context.scene.collection).objects.link(obj)
    return obj


# ------------------------------------------------------------------ sky
def sun_direction(path):
    """Brightest spot of an equirect HDRI, as (azimuth, elevation) in radians, Blender world mapping."""
    img = bpy.data.images.load(path)
    small = img.copy()
    small.scale(512, 256)
    px = list(small.pixels)
    best, bi = -1.0, 0
    for i in range(0, len(px), 4):
        l = px[i] + px[i + 1] + px[i + 2]
        if l > best:
            best, bi = l, i // 4
    x, y = bi % 512, bi // 512
    u, v = (x + 0.5) / 512, (y + 0.5) / 256
    bpy.data.images.remove(small)
    az = (u - 0.5) * 2 * math.pi          # angle around Z, 0 at -Y in Blender's equirect mapping
    el = (v - 0.5) * math.pi
    return img, az, el


def sky(hdr_name, sun_az_target, strength=1.0, sun_strength=3.0, sun_color=(1.0, 0.82, 0.62), sun_angle=1.2, sun_el=None):
    """HDRI world rotated so its sun sits at sun_az_target (radians, 0 = +Y, positive = towards +X),
    plus a matching Sun lamp for crisp shadows and light shafts."""
    w = bpy.context.scene.world
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    img, az, el = sun_direction(os.path.join(SRC, "hdris", hdr_name))
    tex = nt.nodes.new("ShaderNodeTexEnvironment"); tex.image = img
    mp = nt.nodes.new("ShaderNodeMapping"); tc = nt.nodes.new("ShaderNodeTexCoord")
    bg = nt.nodes.new("ShaderNodeBackground"); out = nt.nodes.new("ShaderNodeOutputWorld")
    bg.inputs["Strength"].default_value = strength
    # Blender maps equirect u = atan2(dir.y, -dir.x) / 2pi + 0.5, so the photographed sun starts at:
    dir0 = Vector((-math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
    az0 = math.atan2(dir0.x, dir0.y)          # my convention: 0 = +Y, positive towards +X (clockwise from above)
    # the Mapping node turns the lookup vector, so the picture turns the other way: clockwise azimuth grows by +rot
    rot = sun_az_target - az0
    mp.inputs["Rotation"].default_value = (0, 0, rot)
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], bg.inputs["Color"]); nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    if sun_el is not None: el = sun_el   # a lower lamp than the photographed sun, for longer shadows
    sun_dir = Vector((math.sin(sun_az_target) * math.cos(el), math.cos(sun_az_target) * math.cos(el), math.sin(el)))
    lamp = bpy.data.lights.new("Sun", "SUN"); lamp.energy = sun_strength; lamp.color = sun_color; lamp.angle = math.radians(sun_angle)
    ob = link(bpy.data.objects.new("Sun", lamp))
    ob.rotation_euler = (-sun_dir).to_track_quat("-Z", "Y").to_euler()
    return sun_dir, el


def haze(size=(900, 1400, 260), center=(0, 500, 120), density=0.0022, color=(0.95, 0.86, 0.74), anisotropy=0.55):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    ob = bpy.context.object; ob.name = "Haze"; ob.scale = size
    m = bpy.data.materials.new("Haze"); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    vol = nt.nodes.new("ShaderNodeVolumeScatter"); out = nt.nodes.new("ShaderNodeOutputMaterial")
    vol.inputs["Color"].default_value = (*color, 1); vol.inputs["Density"].default_value = density; vol.inputs["Anisotropy"].default_value = anisotropy
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    ob.data.materials.append(m)
    ob.visible_shadow = False
    return ob


# ------------------------------------------------------------------ scans
def load_scan(name):
    """Imports a Poly Haven glTF once and returns its mesh objects joined into one template object."""
    d = os.path.join(SRC, "models", name)
    f = [x for x in os.listdir(d) if x.endswith(".gltf")][0]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(d, f))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    extras = [o.name for o in new if o.type != "MESH"]  # by name: joined objects stop existing
    for o in meshes:
        o.matrix_world = o.matrix_world.copy(); o.parent = None
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1: bpy.ops.object.join()
    t = bpy.context.view_layer.objects.active; t.name = "T_" + name
    for n in extras:
        if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n])
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    for c in list(t.users_collection): c.objects.unlink(t)
    return t


def place(template, loc, rot=(0, 0, 0), scale=1.0, col=None, name=None):
    o = template.copy()  # shares mesh data: cheap instances
    o.name = name or template.name[2:]
    o.location = loc; o.rotation_euler = Euler([math.radians(r) for r in rot]); o.scale = (scale,) * 3 if isinstance(scale, (int, float)) else scale
    return link(o, col)


def warm_scan_material(template, tint=(0.80, 0.52, 0.33), amount=0.55, value=1.0, rough_add=0.0, sat=1.08):
    """Pushes a scan's albedo towards warm sandstone without hiding its photographed detail."""
    for slot in template.material_slots:
        m = slot.material
        if not m or not m.use_nodes: continue
        nt = m.node_tree
        bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if not bsdf or not bsdf.inputs["Base Color"].links: continue
        src = bsdf.inputs["Base Color"].links[0].from_socket
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "OVERLAY"
        mix.inputs["Factor"].default_value = amount; mix.inputs["B"].default_value = (*tint, 1)
        hsv = nt.nodes.new("ShaderNodeHueSaturation"); hsv.inputs["Value"].default_value = value; hsv.inputs["Saturation"].default_value = sat
        nt.links.new(src, mix.inputs["A"]); nt.links.new(mix.outputs["Result"], hsv.inputs["Color"]); nt.links.new(hsv.outputs["Color"], bsdf.inputs["Base Color"])


# ------------------------------------------------------------------ materials from texture sets
def pbr(name, tex, scale=1.0, tint=None, bump=0.35, disp=0.0, triplanar=True):
    d = os.path.join(SRC, "textures", tex)
    fs = os.listdir(d)
    pick = lambda k: next((os.path.join(d, f) for f in fs if k in f.lower()), None)
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])

    def img(path, cs):
        n = nt.nodes.new("ShaderNodeTexImage"); n.image = bpy.data.images.load(path); n.image.colorspace_settings.name = cs
        if triplanar: n.projection = "BOX"; n.projection_blend = 0.35
        nt.links.new(mp.outputs["Vector"], n.inputs["Vector"]); return n

    c = img(pick("diff"), "sRGB"); col = c.outputs["Color"]
    if tint:
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.inputs["Factor"].default_value = 1
        mix.inputs["B"].default_value = (*tint, 1); nt.links.new(col, mix.inputs["A"]); col = mix.outputs["Result"]
    nt.links.new(col, bsdf.inputs["Base Color"])
    if pick("rough"): nt.links.new(img(pick("rough"), "Non-Color").outputs["Color"], bsdf.inputs["Roughness"])
    if pick("nor_gl"):
        nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 1.0
        nt.links.new(img(pick("nor_gl"), "Non-Color").outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return m


# ------------------------------------------------------------------ terrain
def terrain(name, size=(700, 1100), center=(0, 420), res=(360, 560), height=None, mat=None):
    """Grid displaced by a height function h(x, y) in metres."""
    bm = bmesh.new()
    nx, ny = res
    verts = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = center[0] + (i / nx - 0.5) * size[0]; y = center[1] + (j / ny - 0.5) * size[1]
            verts.append(bm.verts.new((x, y, height(x, y) if height else 0)))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            bm.faces.new((verts[a], verts[a + 1], verts[a + nx + 2], verts[a + nx + 1]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = link(bpy.data.objects.new(name, me))
    if mat: me.materials.append(mat)
    return ob


def fbm(x, y, scale, octaves=4, seed=0.0):
    return noise.fractal(Vector((x / scale + seed, y / scale - seed, seed)), 1.0, 2.0, octaves, noise_basis="PERLIN_ORIGINAL")


# ------------------------------------------------------------------ date palm
def leaf_material(name="Frond", base=(0.10, 0.19, 0.06), back=(0.42, 0.50, 0.12)):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    pr = nt.nodes.new("ShaderNodeBsdfPrincipled"); pr.inputs["Base Color"].default_value = (*base, 1); pr.inputs["Roughness"].default_value = 0.42
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent"); tr.inputs["Color"].default_value = (*back, 1)
    mx = nt.nodes.new("ShaderNodeMixShader"); mx.inputs["Fac"].default_value = 0.42
    nt.links.new(pr.outputs["BSDF"], mx.inputs[1]); nt.links.new(tr.outputs["BSDF"], mx.inputs[2]); nt.links.new(mx.outputs["Shader"], out.inputs["Surface"])
    return m


def frond_mesh(name, length=3.2, leaflets=62, droop=0.9, seed=1, leaflet_len=0.62, mat=None):
    """One pinnate date-palm frond along +Y from the origin: an arching rachis with paired, folded leaflets."""
    rnd = random.Random(seed)
    bm = bmesh.new()

    def spine(t):  # arch up, then droop under its own weight
        y = length * (t - 0.10 * droop * t * t * t)
        z = length * (0.30 * t - droop * 0.62 * t * t)
        return Vector((0, y, z))

    # rachis: a thin tapering triangular tube
    rings = 22; prev = None
    for k in range(rings + 1):
        t = k / rings; p = spine(t); r = 0.022 * (1 - 0.85 * t) + 0.003
        ring = [bm.verts.new(p + Vector((math.cos(a) * r, 0, math.sin(a) * r))) for a in (math.pi / 2, math.pi * 7 / 6, math.pi * 11 / 6)]
        if prev:
            for q in range(3): bm.faces.new((prev[q], prev[(q + 1) % 3], ring[(q + 1) % 3], ring[q]))
        prev = ring
    for k in range(leaflets):
        t = 0.10 + 0.90 * (k + 0.5) / leaflets
        p = spine(t); tan = (spine(min(1, t + 0.01)) - spine(max(0, t - 0.01))).normalized()
        L = leaflet_len * (0.55 + 0.75 * math.sin(math.pi * min(1, t * 1.15)) ** 0.8) * (0.85 + 0.3 * rnd.random())
        for side in (-1, 1):
            ang = math.radians(48 - 22 * t + rnd.uniform(-7, 7))            # leaflets sweep forward towards the tip
            d = (Vector((side * math.cos(ang), 0, 0)) + tan * math.sin(ang)).normalized()
            d.z -= 0.18 + 0.5 * rnd.random() * droop * 0.5                    # and hang a little
            d.normalize()
            up = tan.cross(d).normalized() * side
            w = 0.020 + 0.012 * rnd.random()
            fold = up * (-w * 0.55)
            seg = 5; rowL = rowC = rowR = None
            for s in range(seg + 1):
                u = s / seg
                c = p + d * (L * u) + Vector((0, 0, -0.10 * L * u * u))       # slight curl down along the blade
                ww = w * (math.sin(math.pi * min(1.0, 0.12 + u * 0.88)) ** 0.7) * (1 - 0.15 * u)
                side_v = tan * ww
                vl, vc, vr = bm.verts.new(c - side_v), bm.verts.new(c + fold * (1 - u)), bm.verts.new(c + side_v)
                if rowL:
                    bm.faces.new((rowL, rowC, vc, vl)); bm.faces.new((rowC, rowR, vr, vc))
                rowL, rowC, rowR = vl, vc, vr
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for poly in me.polygons: poly.use_smooth = True
    if mat: me.materials.append(mat)
    return me


def bark_material():
    m = bpy.data.materials.new("Bark"); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 9; n.inputs["Detail"].default_value = 8
    w = nt.nodes.new("ShaderNodeTexWave"); w.wave_type = "BANDS"; w.bands_direction = "Z"; w.inputs["Scale"].default_value = 7; w.inputs["Distortion"].default_value = 3.5
    r = nt.nodes.new("ShaderNodeValToRGB"); r.color_ramp.elements[0].color = (0.05, 0.035, 0.025, 1); r.color_ramp.elements[1].color = (0.30, 0.22, 0.15, 1)
    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MULTIPLY"
    nt.links.new(n.outputs["Fac"], mx.inputs[0]); nt.links.new(w.outputs["Fac"], mx.inputs[1]); nt.links.new(mx.outputs[0], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.9
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.9; bump.inputs["Distance"].default_value = 0.08
    nt.links.new(w.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


_FRONDS = {}


def frond_library(leaf, count=7):
    """A few frond shapes, young and old, shared by every palm as linked mesh data (keeps host memory low)."""
    key = leaf.name
    if key not in _FRONDS:
        rnd = random.Random(99)
        young = [frond_mesh(f"FrondY{i}", length=rnd.uniform(3.0, 4.2), leaflets=54, droop=rnd.uniform(0.55, 1.05), seed=500 + i, mat=leaf) for i in range(count)]
        old = [frond_mesh(f"FrondO{i}", length=rnd.uniform(3.0, 4.0), leaflets=48, droop=rnd.uniform(1.25, 1.7), seed=600 + i, mat=leaf) for i in range(4)]
        _FRONDS[key] = (young, old)
    return _FRONDS[key]


def palm(name, loc, height=8.0, fronds=34, seed=1, leaf=None, bark=None, col=None, lean=0.06, pass_index=1):
    """A date palm: leaning tapered trunk, a crown of arching fronds, a skirt of older drooping ones."""
    rnd = random.Random(seed)
    root = link(bpy.data.objects.new(name, None), col); root.location = loc; root.rotation_euler = (0, 0, rnd.uniform(0, 6.28))
    # trunk
    bm = bmesh.new(); rings = 26; seg = 12; prev = None
    lx = rnd.uniform(-lean, lean) * height; ly = rnd.uniform(-lean, lean) * height
    for k in range(rings + 1):
        t = k / rings; c = Vector((lx * t * t, ly * t * t, height * t)); r = (0.30 - 0.10 * t) * (1 + 0.06 * math.sin(k * 2.1)) + (0.10 if k < 2 else 0)
        ring = [bm.verts.new(c + Vector((math.cos(a) * r, math.sin(a) * r, 0))) for a in [2 * math.pi * q / seg for q in range(seg)]]
        if prev:
            for q in range(seg): bm.faces.new((prev[q], prev[(q + 1) % seg], ring[(q + 1) % seg], ring[q]))
        prev = ring
    me = bpy.data.meshes.new(name + "_trunk"); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    if bark: me.materials.append(bark)
    tr = link(bpy.data.objects.new(name + "_trunk", me), col); tr.parent = root
    top = Vector((lx, ly, height))
    for k in range(fronds):
        old = k >= fronds * 0.72
        young_lib, old_lib = frond_library(leaf)
        me = rnd.choice(old_lib if old else young_lib)
        f = link(bpy.data.objects.new(f"{name}_f{k}", me), col); f.parent = root; f.location = top; f.pass_index = pass_index; sc = rnd.uniform(0.85, 1.12); f.scale = (sc, sc, sc)
        az = k * 2.39996 + rnd.uniform(-0.3, 0.3)
        pitch = math.radians(rnd.uniform(-35, -5) if old else rnd.uniform(8, 62))
        f.rotation_euler = Euler((pitch, 0, az), "ZYX") if False else (Matrix.Rotation(az, 4, "Z") @ Matrix.Rotation(pitch, 4, "X")).to_euler()
    return root


# ------------------------------------------------------------------ camera
def camera(loc, look, lens=26, sensor=36, dof=None):
    cam = bpy.data.cameras.new("Cam"); cam.lens = lens; cam.sensor_width = sensor; cam.clip_start = 0.05; cam.clip_end = 4000
    ob = link(bpy.data.objects.new("Cam", cam)); ob.location = loc
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    if dof: cam.dof.use_dof = True; cam.dof.focus_distance = dof[0]; cam.dof.aperture_fstop = dof[1]
    bpy.context.scene.camera = ob
    return ob


# ------------------------------------------------------------------ data pass (depth + masks) via material override
def data_material(near=0.6):
    """R: inverse depth (near / distance, 1 = at the lens, 0 = infinitely far). G: palm mask (pass_index 1)."""
    m = bpy.data.materials.new("DATA"); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
    cd = nt.nodes.new("ShaderNodeCameraData")
    div = nt.nodes.new("ShaderNodeMath"); div.operation = "DIVIDE"; div.inputs[0].default_value = near; div.use_clamp = True
    nt.links.new(cd.outputs["View Distance"], div.inputs[1])
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    eq = nt.nodes.new("ShaderNodeMath"); eq.operation = "COMPARE"; eq.inputs[1].default_value = 1; eq.inputs[2].default_value = 0.1
    nt.links.new(oi.outputs["Object Index"], eq.inputs[0])
    comb = nt.nodes.new("ShaderNodeCombineColor")
    nt.links.new(div.outputs[0], comb.inputs[0]); nt.links.new(eq.outputs[0], comb.inputs[1])
    nt.links.new(comb.outputs["Color"], em.inputs["Color"]); nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m


def render(path, res, samples=96, data=False):
    if os.path.exists(path) and os.path.getsize(path) > 20000 and "preview" not in path and "-t0" not in path:
        print("SKIP", path); return            # resumable: a finished file is never rendered twice
    s = bpy.context.scene
    s.render.resolution_x, s.render.resolution_y = res; s.render.resolution_percentage = 100
    s.render.filepath = path
    vl = bpy.context.view_layer
    hidden = []
    if data:
        vl.material_override = data_material()
        s.cycles.samples = 8; s.cycles.use_denoising = False; s.cycles.use_adaptive_sampling = False
        s.view_settings.view_transform = "Raw"; s.view_settings.look = "None"
        s.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0
        for o in bpy.data.objects:
            if o.name.startswith("Haze") or o.type == "LIGHT": o.hide_render = True; hidden.append(o)
        s.cycles.filter_width = 0.01
    else:
        s.cycles.samples = samples
    bpy.ops.render.render(write_still=True)
    print("RENDERED", path)


def mem(tag):
    """Private bytes of this process, in MB (Windows). Used to find what makes a scene heavy."""
    import ctypes
    from ctypes import wintypes
    class PMC(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [(n, ctypes.c_size_t) for n in ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage", "PrivateUsage")]
    c = PMC(); c.cb = ctypes.sizeof(PMC)
    ctypes.windll.kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    ctypes.windll.psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
    ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(c), c.cb)
    print(f"MEM {tag}: {c.PrivateUsage / 1048576:.0f} MB", flush=True)

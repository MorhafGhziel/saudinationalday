"""The opening world: a shaded sandstone threshold with palm fronds overhead, looking out onto sand,
a palm grove and a distant sandstone mass in late light.

    blender --background --python tools/blender/opening.py -- mode=preview|still|data|seq aspect=land|port t=0..1 out=<file or folder>

t moves the camera along the entrance path (0 = at the threshold, 1 = out in the open).
"""
import bpy, math, os, sys, random
sys.path.insert(0, os.path.dirname(__file__))
import common as C, worlds as W
from mathutils import Vector

A = C.args()
MODE = A.get("mode", "preview"); ASPECT = A.get("aspect", "land"); T = float(A.get("t", 0))
OUT = A.get("out", os.path.join(C.ROOT, "renders", "opening"))

s = C.reset()
SUN_AZ = math.radians(-68)                    # sun ahead and to the left: back-light, long shadows towards the lens
sun_dir, sun_el = C.sky("qwantani_late_afternoon_puresky_4k.hdr", SUN_AZ, strength=1.0, sun_strength=7.5, sun_color=(1.0, 0.74, 0.48), sun_angle=1.4, sun_el=math.radians(17))

C.mem("sky")
rock = W.strata_material("Sandstone", "red_sandstone_wall", scale=0.035)
sand = W.sand_material()
leaf = C.leaf_material(); bark = C.bark_material()

# ------------------------------------------------------------------ ground: open sand, low dunes, a worn way out of the passage
def ground_h(x, y):
    dunes = 9.0 * C.fbm(x, y, 150, 3, 2.0) + 3.2 * abs(C.fbm(x + 0.5 * y, y, 46, 3, 7.0)) + 0.5 * C.fbm(x, y, 11, 2, 3.0)
    way = math.exp(-((x + 0.10 * y) / 11) ** 2)                      # flatter along the line of sight
    near = min(1.0, max(0.0, (y - 4) / 60))
    return dunes * near * (1 - 0.65 * way) + 0.06 * C.fbm(x, y, 3, 2, 1.0)

C.terrain("Ground", size=(900, 1300), center=(0, 560), res=(300, 430), height=ground_h, mat=sand)

C.mem("ground")
# ------------------------------------------------------------------ the threshold: scanned strata rock, in shade, framing the view
face1 = C.load_scan("rock_face_01"); face2 = C.load_scan("rock_face_02"); cliff = C.load_scan("namaqualand_cliff_01"); boulder = C.load_scan("namaqualand_boulder_04"); blocks = C.load_scan("namaqualand_boulder_02")
for t_, amt in ((face1, 0.6), (face2, 0.6), (cliff, 0.7), (boulder, 0.55), (blocks, 0.6)):
    C.warm_scan_material(t_, tint=(0.78, 0.47, 0.28), amount=amt)

# the way through the rock: a sculpted, bedded passage (solid, so the frame is always closed and dark)
near_rock = W.strata_material("SandstoneNear", "sandstone_cracks", scale=0.42, band=1.05, light=(0.62, 0.40, 0.26), dark=(0.26, 0.14, 0.09))
W.passage("Passage", y0=-14.0, y1=17.0, half_width=4.7, height=9.6, mat=near_rock, seg=340, rows=420)
# floor stones and a boulder to step past
C.place(boulder, (-3.9, 8.5, 0.5), rot=(0, 0, 40), scale=1.15, name="Boulder")
C.place(blocks, (3.6, 6.2, 0.35), rot=(0, 0, -25), scale=1.3, name="Blocks")
C.place(blocks, (-2.9, 2.2, 0.2), rot=(0, 0, 130), scale=0.8, name="Blocks2")
C.place(boulder, (9.5, 30, 0.6), rot=(0, 0, 200), scale=1.8, name="BoulderOut")
C.place(blocks, (-13, 36, 0.4), rot=(0, 0, 80), scale=2.2, name="BlocksOut")
sr = random.Random(3)
for i in range(46):
    x = sr.uniform(-40, 40); y = sr.uniform(18, 120)
    C.place(sr.choice((blocks, boulder)), (x, y, ground_h(x, y)), rot=(sr.uniform(-20, 20), sr.uniform(-20, 20), sr.uniform(0, 360)), scale=sr.uniform(0.08, 0.42), name=f"Stone{i}")

C.mem("threshold")
# ------------------------------------------------------------------ fronds leaning into frame from above (close to the lens)
rnd = random.Random(7)
for i, (loc, rot) in enumerate([((-3.4, 9.5, 5.6), (-28, 12, -58)), ((-3.9, 10.5, 6.2), (-40, -8, -28)), ((-2.9, 9.0, 6.6), (-52, 6, -80)), ((4.2, 8.5, 5.2), (-30, -10, 62)), ((4.6, 9.6, 6.0), (-46, 8, 34)), ((3.6, 7.6, 6.6), (-58, 0, 84)), ((-4.2, 12.0, 7.0), (-60, 0, -10))]):
    me = C.frond_mesh(f"NearFrond{i}", length=3.3, leaflets=70, droop=1.15 + 0.2 * rnd.random(), seed=40 + i, leaflet_len=0.7, mat=leaf)
    o = C.link(bpy.data.objects.new(f"NearFrond{i}", me)); o.location = loc; o.rotation_euler = [math.radians(r) for r in rot]; o.pass_index = 1

C.mem("fronds")
# ------------------------------------------------------------------ the grove in the middle ground
grove = [(-13, 38, 10.5), (-19, 46, 8), (-16, 62, 9.5), (-9, 74, 11), (-22, 80, 8.5), (-4, 92, 10), (-28, 98, 12), (-13, 110, 9), (14, 72, 11.5), (19, 84, 8.5), (24, 104, 9), (-36, 126, 11), (4, 132, 10), (30, 140, 12), (-52, 150, 10), (-44, 176, 11), (10, 190, 9.5), (44, 205, 12), (-70, 230, 10), (-8, 250, 11)]
for i, (x, y, h) in enumerate(grove):
    C.palm(f"Palm{i}", (x, y, ground_h(x, y) - 0.2), height=h, fronds=30, seed=11 + i, leaf=leaf, bark=bark)

C.mem("grove")
# ------------------------------------------------------------------ the destination and its companions, far off in the haze
W.butte("Destination", (-90, 640, -4), radius=92, height=165, seed=3, mat=rock, squash=(1.35, 0.8), ledges=8, talus=0.34, flute=0.27)
W.butte("DestinationC", (-5, 690, -4), radius=58, height=112, seed=21, mat=rock, squash=(1.2, 0.9), ledges=6, talus=0.36, flute=0.24)
W.butte("DestinationD", (-190, 655, -4), radius=64, height=132, seed=27, mat=rock, squash=(1.1, 0.9), ledges=7, talus=0.33, flute=0.25)
W.butte("DestinationB", (-275, 720, -4), radius=40, height=120, seed=5, mat=rock, squash=(0.9, 1.0), ledges=5)
W.butte("FarL", (-380, 900, -6), radius=120, height=150, seed=8, mat=rock, squash=(1.6, 0.8), ledges=5, flute=0.10)
W.butte("FarR", (300, 860, -6), radius=110, height=170, seed=9, mat=rock, squash=(1.5, 0.9), ledges=6, flute=0.12)
W.butte("FarR2", (560, 1040, -6), radius=140, height=120, seed=12, mat=rock, squash=(1.8, 0.8), ledges=4, flute=0.08)
W.butte("MidR", (150, 330, -3), radius=30, height=62, seed=15, mat=rock, squash=(1.2, 0.9), ledges=4)

# ground-hugging air: thick low down, clear above, so the sky keeps its colour and far rock fades from the base up
C.haze(size=(2400, 2600, 70), center=(0, 1320, 30), density=0.00060, color=(1.0, 0.86, 0.70), anisotropy=0.72)
C.haze(size=(2400, 2600, 260), center=(0, 1340, 200), density=0.00010, color=(0.92, 0.90, 0.88), anisotropy=0.6).name = "HazeHigh"
# thicker air in the passage mouth so the sun draws shafts past the rock
# bounce from the sunlit sand, cheated a little so the shaded rock keeps its texture
bl = bpy.data.lights.new("Bounce", "AREA"); bl.energy = 650; bl.color = (1.0, 0.70, 0.44); bl.size = 9; bl.size_y = 5; bl.shape = "RECTANGLE"
bo = C.link(bpy.data.objects.new("Bounce", bl)); bo.location = (0, 21, 0.6); bo.rotation_euler = (math.radians(-104), 0, 0); bo.visible_camera = False
C.haze(size=(60, 44, 24), center=(0, 40, 11), density=0.0040, color=(1.0, 0.84, 0.66), anisotropy=0.75).name = "HazeNear"

C.mem("buttes+haze")
# ------------------------------------------------------------------ camera path: through the threshold and out
def ease(t): return t * t * t * (t * (t * 6 - 15) + 10)
if ASPECT == "port":
    p0, p1 = Vector((0.4, -5.0, 1.75)), Vector((-2.0, 44, 2.8)); look0, look1 = Vector((-5, 90, 14)), Vector((-36, 400, 52)); lens = 20
    res = (1440, 2560)
else:
    p0, p1 = Vector((2.4, -3.5, 1.75)), Vector((-2.0, 44, 2.8)); look0, look1 = Vector((7, 90, 9)), Vector((-20, 400, 40)); lens = 24
    res = (2560, 1440)
cam = C.camera(p0.lerp(p1, T), look0.lerp(look1, T), lens=lens)
s.view_settings.exposure = float(A.get("ev", -0.45))

if MODE == "preview":
    C.render(OUT + f"-{ASPECT}-t{int(T * 100):03d}.png", (res[0] * 3 // 8, res[1] * 3 // 8), samples=40)
elif MODE == "still":
    C.render(OUT + f"-{ASPECT}.png", res, samples=int(A.get("spp", 160)))
elif MODE == "data":
    C.render(OUT + f"-{ASPECT}-data.png", res, data=True)
elif MODE == "seq":
    n = int(A.get("frames", 48)); scale = float(A.get("scale", 0.625))
    for k in range(n):
        t = k / (n - 1)
        cam.location = p0.lerp(p1, t); cam.rotation_euler = (look0.lerp(look1, t) - cam.location).to_track_quat("-Z", "Y").to_euler()
        C.render(os.path.join(OUT, f"{ASPECT}-{k:03d}.png"), (int(res[0] * scale), int(res[1] * scale)), samples=int(A.get("spp", 64)))
elif MODE == "top":
    # layout check: orthographic plan of the threshold, lintel and haze hidden, camera marked by a red cone
    for o in bpy.data.objects:
        if o.name.startswith(("Haze", "Lintel")): o.hide_render = True
    bpy.ops.mesh.primitive_cone_add(radius1=0.5, depth=2.0, location=p0 + Vector((0, 0, 14)), rotation=(math.radians(-90), 0, 0))
    mk = bpy.context.object; mm = bpy.data.materials.new("mk"); mm.use_nodes = True; mm.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1, 0, 0, 1); mm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 30; mk.data.materials.append(mm)
    cd = bpy.data.cameras.new("Top"); cd.type = "ORTHO"; cd.ortho_scale = float(A.get("span", 60)); cd.clip_end = 500
    co = C.link(bpy.data.objects.new("Top", cd)); co.location = (0, float(A.get("cy", 14)), 120); co.rotation_euler = (0, 0, 0); s.camera = co
    C.render(OUT + "-top.png", (900, 900), samples=16)
elif MODE == "side":
    for o in bpy.data.objects:
        if o.name.startswith(("Haze", "WallR")): o.hide_render = True
    cd = bpy.data.cameras.new("Side"); cd.type = "ORTHO"; cd.ortho_scale = float(A.get("span", 60)); cd.clip_end = 500
    co = C.link(bpy.data.objects.new("Side", cd)); co.location = (150, float(A.get("cy", 14)), 8); co.rotation_euler = (math.radians(90), 0, math.radians(90)); s.camera = co
    C.render(OUT + "-side.png", (900, 500), samples=16)
elif MODE == "all":
    # one scene build, every output for this aspect: opening still, the walk-through, then the data passes (they change scene state, so last)
    base = os.path.join(C.ROOT, "renders", "opening"); os.makedirs(base, exist_ok=True)
    n = int(A.get("frames", 36)); scale = float(A.get("scale", 0.625))
    def at(t):
        cam.location = p0.lerp(p1, t); cam.rotation_euler = (look0.lerp(look1, t) - cam.location).to_track_quat("-Z", "Y").to_euler()
    at(0); C.render(os.path.join(base, f"{ASPECT}-still0.png"), res, samples=160)
    at(1); C.render(os.path.join(base, f"{ASPECT}-still1.png"), res, samples=160)
    for k in range(n):
        at(k / (n - 1)); C.render(os.path.join(base, "seq", f"{ASPECT}-{k:03d}.png"), (int(res[0] * scale), int(res[1] * scale)), samples=72)
    at(0); C.render(os.path.join(base, f"{ASPECT}-data0.png"), res, data=True)
    at(1); C.render(os.path.join(base, f"{ASPECT}-data1.png"), res, data=True)
elif MODE == "walk":
    # the walk as video frames: the ease is baked in, so the browser only has to play a normal 30 fps video
    base = os.path.join(C.ROOT, "renders", "opening", "walk"); os.makedirs(base, exist_ok=True)
    n = int(A.get("frames", 105)); size = (1280, 720) if ASPECT == "land" else (720, 1280)
    for k in range(n):
        t = ease(k / (n - 1))
        cam.location = p0.lerp(p1, t); cam.rotation_euler = (look0.lerp(look1, t) - cam.location).to_track_quat("-Z", "Y").to_euler()
        C.render(os.path.join(base, f"{ASPECT}-{k:03d}.png"), size, samples=56)

"""Renders each downloaded scan from the front, the side and above, with its size, so scenes can be composed knowingly.

    blender --background --python tools/blender/preview_scans.py -- out=<folder>
"""
import bpy, math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import common as C
from mathutils import Vector

a = C.args(); out = a.get("out", os.path.join(C.ROOT, "renders", "scans")); os.makedirs(out, exist_ok=True)
names = sorted(os.listdir(os.path.join(C.SRC, "models")))
for name in names:
    s = C.reset()
    s.view_settings.look = "None"
    C.sky("kloofendal_48d_partly_cloudy_puresky_4k.hdr" if os.path.exists(os.path.join(C.SRC, "hdris", "kloofendal_48d_partly_cloudy_puresky_4k.hdr")) else os.listdir(os.path.join(C.SRC, "hdris"))[0], math.radians(-50), strength=1.0, sun_strength=3)
    t = C.load_scan(name); C.link(t)
    d = t.dimensions; r = max(d) * 1.2
    print("SCAN", name, "dims", [round(x, 2) for x in d])
    for view, loc in (("front", (0, -r * 1.4, r * 0.25)), ("side", (r * 1.4, 0, r * 0.25)), ("top", (0, -0.01, r * 1.8))):
        C.camera(loc, (0, 0, 0), lens=35)
        C.render(os.path.join(out, f"{name}-{view}.png"), (480, 360), samples=24)

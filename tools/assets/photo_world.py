"""Builds a destination world from a real, freely licensed photograph (see ASSETS.md for each credit).

For each place it writes, straight into public/worlds/<id>/:
  land-still0.webp (+ -sm)   16:9 crop, gently graded to sit with the other worlds
  port-still0.webp (+ -sm)   9:16 crop around the subject, used on phones and for the poster
  land-data0.png, port-data0.png   R = sqrt(inverse depth), G = 0

A photograph has no depth pass, so depth is estimated from the picture's own structure: the sky is found
by colour and set to "infinitely far"; the ground recedes either towards the horizon line or, for a lane
in one-point perspective, towards its vanishing point. It is an approximation, kept smooth, and the view
only ever shifts by a few pixels, so it reads as depth without showing seams.

    uv run --python 3.12 --with pillow --with numpy --with scipy python tools/assets/photo_world.py
"""
import json, os, time, urllib.error, urllib.request
import numpy as np
from PIL import Image, ImageEnhance
from scipy.ndimage import gaussian_filter, binary_opening, binary_closing

root = os.path.join(os.path.dirname(__file__), "..", "..")
src = os.path.join(root, "assets-src", "commons")
cands = json.load(open(os.path.join(src, "candidates.json"), encoding="utf8"))

# pick = preview name from candidates.json; land_y / port_x = where the crop sits (0..1); depth = how the ground recedes
WORLDS = {
    "najd": {"pick": "najd-08.jpg", "land_y": 0.30, "port_x": 0.66, "depth": ("vanish", 0.665, 0.50), "warm": 1.04},
    "alula": {"pick": "alula-01.jpg", "land_y": 0.55, "port_x": 0.54, "depth": ("horizon", 0.74), "warm": 1.02},
    "jeddah": {"pick": "jeddah-06.jpg", "land_y": 0.30, "port_x": 0.50, "depth": ("horizon", 0.12), "warm": 1.02},
    "makkah": {"pick": "makkah-04.jpg", "land_y": 0.40, "port_x": 0.50, "depth": ("horizon", 0.55), "warm": 1.02},
    "madinah": {"pick": "madinah-08.jpg", "land_y": 0.0, "port_x": 0.42, "depth": ("horizon", 0.50), "warm": 1.0},
    "sharqiyah": {"pick": "sharqiyah-04.jpg", "land_y": 0.50, "port_x": 0.62, "depth": ("horizon", 0.50), "warm": 1.0},
    "aseer": {"pick": "aseer-02.jpg", "land_y": 0.18, "port_x": 0.50, "depth": ("horizon", 0.30), "warm": 1.0},
}


def fetch(c):
    dest = os.path.join(src, "full-" + c["preview"])
    if not os.path.exists(dest):
        req = urllib.request.Request(c["url"], headers={"User-Agent": "hekayatna-national-day/1.0 (independent studio project)"})
        for attempt in range(6):                       # be a polite client: wait between files, back off when asked to
            time.sleep(6 + attempt * 20)
            try:
                blob = urllib.request.urlopen(req).read()   # read fully first, so a failed download never leaves an empty file behind
                open(dest, "wb").write(blob); break
            except urllib.error.HTTPError as e:
                if e.code != 429 or attempt == 5: raise
                print("  rate limited, waiting", flush=True)
    return Image.open(dest).convert("RGB")


def sky_mask(a):
    """Blue or bright-and-colourless pixels that connect to the top of the frame."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = 0.3 * r + 0.6 * g + 0.1 * b
    blue = (b > r * 1.08) & (b > 0.35)
    cloud = (lum > 0.72) & (np.abs(r - b) < 0.10)
    m = binary_closing(binary_opening(blue | cloud, iterations=2), iterations=3)
    m[:10] = m[10]                                        # morphology erodes the frame edge: restore the top rows
    # keep only what is reachable from the top edge, column by column (a roof or a wall stops the sky)
    out = np.zeros_like(m)
    for x in range(m.shape[1]):
        col = m[:, x]; stop = np.argmax(~col) if (~col).any() else len(col)
        out[:stop, x] = True
    return out


def depth(a, spec):
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); yy /= h; xx /= w
    sky = sky_mask(a)
    if spec[0] == "horizon":
        hz = spec[1]
        d = np.clip((yy - hz) / (1 - hz), 0, 1) ** 1.35 * 0.78 + 0.04          # near at our feet, far at the horizon
    else:
        vx, vy = spec[1], spec[2]
        dist = np.sqrt(((xx - vx) * 1.25) ** 2 + (yy - vy) ** 2)
        d = np.clip(dist / 0.62, 0, 1) ** 0.85 * 0.80 + 0.04                   # everything recedes towards the end of the lane
    d[sky] = 0.0
    return gaussian_filter(d, sigma=max(3, w // 260))


def grade(im, warm):
    im = ImageEnhance.Contrast(im).enhance(1.06)
    im = ImageEnhance.Color(im).enhance(0.94)
    a = np.asarray(im).astype(np.float32) / 255
    a[..., 0] *= warm; a[..., 2] /= warm
    a = np.clip(a, 0, 1) ** 1.04
    return Image.fromarray((a * 255 + 0.5).astype(np.uint8))


def save(im, dmap, out, name):
    im.save(os.path.join(out, f"{name}-still0.webp"), "WEBP", quality=88, method=6)
    im.resize((im.width * 5 // 8, im.height * 5 // 8), Image.LANCZOS).save(os.path.join(out, f"{name}-still0-sm.webp"), "WEBP", quality=84, method=6)
    r = (np.sqrt(np.clip(dmap, 0, 1)) * 255 + 0.5).astype(np.uint8)
    rgb = np.stack([r, np.zeros_like(r), np.zeros_like(r)], -1)
    Image.fromarray(rgb, "RGB").resize((im.width // 2, im.height // 2), Image.BILINEAR).save(os.path.join(out, f"{name}-data0.png"), optimize=True)


credits = {}
for place, cfg in WORLDS.items():
    c = next(x for x in cands[place] if x["preview"] == cfg["pick"])
    full = grade(fetch(c), cfg["warm"])
    W, H = full.size
    out = os.path.join(root, "public", "worlds", place); os.makedirs(out, exist_ok=True)
    full_d = depth(np.asarray(full).astype(np.float32) / 255, cfg["depth"])
    # landscape 16:9
    ch = int(W * 9 / 16); y0 = int((H - ch) * cfg["land_y"])
    land = full.crop((0, y0, W, y0 + ch)).resize((2560, 1440), Image.LANCZOS)
    land_d = np.asarray(Image.fromarray((full_d[y0:y0 + ch] * 65535).astype(np.uint16)).resize((2560, 1440), Image.BILINEAR)).astype(np.float32) / 65535
    save(land, land_d, out, "land")
    # portrait 9:16 around the subject
    cw = int(H * 9 / 16); x0 = int(np.clip(W * cfg["port_x"] - cw / 2, 0, W - cw))
    port = full.crop((x0, 0, x0 + cw, H)).resize((1440, 2560), Image.LANCZOS)
    port_d = np.asarray(Image.fromarray((full_d[:, x0:x0 + cw] * 65535).astype(np.uint16)).resize((1440, 2560), Image.BILINEAR)).astype(np.float32) / 65535
    save(port, port_d, out, "port")
    credits[place] = {"title": c["title"], "author": c["author"], "licence": c["licence"], "page": c["page"]}
    print(place, c["title"], "|", c["author"], "|", c["licence"], "| sky share", round(float((full_d < 0.01).mean()), 2))
json.dump(credits, open(os.path.join(src, "used.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)

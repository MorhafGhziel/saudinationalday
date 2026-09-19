"""Turns Blender renders into web assets under public/worlds/<world>/.

  colour  -> WebP (quality 88)
  data    -> 8-bit PNG: R = sqrt(inverse depth) (more precision in the middle distance), G = frond mask
  seq     -> WebP frames (quality 80)

    uv run --python 3.12 --with pillow --with numpy python tools/assets/pack.py opening
"""
import glob, os, sys
import numpy as np
from PIL import Image

root = os.path.join(os.path.dirname(__file__), "..", "..")
world = sys.argv[1]
src = os.path.join(root, "renders", world)
out = os.path.join(root, "public", "worlds", world)
os.makedirs(out, exist_ok=True)


def data(path, dest):
    a = np.asarray(Image.open(path))
    if a.dtype != np.uint16:
        a = a.astype(np.uint16) * 257
    a = a.astype(np.float32) / 65535.0
    r = np.sqrt(np.clip(a[..., 0], 0, 1)); g = np.clip(a[..., 1], 0, 1)
    rgb = np.stack([r, g, np.zeros_like(r)], -1)
    im = Image.fromarray((rgb * 255 + 0.5).astype(np.uint8), "RGB")
    im.resize((im.width // 2, im.height // 2), Image.BILINEAR).save(dest, optimize=True)      # depth does not need full resolution, and softer depth hides parallax seams


for f in sorted(glob.glob(os.path.join(src, "*-still*.png"))):
    name = os.path.basename(f).replace(".png", ".webp")
    im = Image.open(f).convert("RGB")
    im.save(os.path.join(out, name), "WEBP", quality=88, method=6)
    im.resize((im.width * 5 // 8, im.height * 5 // 8), Image.LANCZOS).save(os.path.join(out, name.replace(".webp", "-sm.webp")), "WEBP", quality=84, method=6)   # phones and lite tier
    print("colour", name)
for f in sorted(glob.glob(os.path.join(src, "*-data*.png"))):
    data(f, os.path.join(out, os.path.basename(f)))
    print("data", os.path.basename(f))


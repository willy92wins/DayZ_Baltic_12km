"""Project the 48 m water-tile grid (pieces.json: tile_m 48, origins at 24 + 48k) on the lake level into a capture,
to see whether the band edges of BALTIC-018 follow the tiles. Camera model as tools/playtest/tide_views_v30.py."""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

cap, out = Path(sys.argv[1]), Path(sys.argv[2])
cam = np.array([float(v) for v in sys.argv[3].split(',')])
look = np.array([float(v) for v in sys.argv[4].split(',')])
level, vfov = float(sys.argv[5]), float(sys.argv[6])
im = Image.open(cap).convert('RGB')
W, HH = im.size
f = (look - cam) / np.linalg.norm(look - cam)
right = np.array([f[2], 0.0, -f[0]])
right /= np.linalg.norm(right)
up = np.cross(right, f)
up = up if up[1] > 0 else -up
t2 = math.tan(math.radians(vfov) / 2)


def proj(p):
    v = p - cam
    zc = v @ f
    ok = zc > 1.0
    u = W / 2 + (v @ right) / np.where(ok, zc, 1) / (t2 * W / HH) * (W / 2)
    w = HH / 2 - (v @ up) / np.where(ok, zc, 1) / t2 * (HH / 2)
    return np.column_stack([u, w]), ok


d = ImageDraw.Draw(im)
x0, x1 = 0, 1400
z0, z1 = 300, 2200
for gx in range(0, 1440, 48):
    zs = np.linspace(z0, z1, 400)
    p = np.column_stack([np.full_like(zs, gx), np.full_like(zs, level), zs])
    uv, ok = proj(p)
    pts = [tuple(q) for q, k in zip(uv, ok) if k and -50 < q[0] < W + 50 and -50 < q[1] < HH + 50]
    if len(pts) > 1:
        d.line(pts, fill=(255, 0, 0), width=1)
for gz in range(0, 2400, 48):
    xs = np.linspace(x0, x1, 400)
    p = np.column_stack([xs, np.full_like(xs, level), np.full_like(xs, gz)])
    uv, ok = proj(p)
    pts = [tuple(q) for q, k in zip(uv, ok) if k and -50 < q[0] < W + 50 and -50 < q[1] < HH + 50]
    if len(pts) > 1:
        d.line(pts, fill=(255, 0, 0), width=1)
im.save(out, quality=90)
print(out, im.size)

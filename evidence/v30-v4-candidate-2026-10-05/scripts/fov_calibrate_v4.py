"""Vertical FOV check for the 05-10 window size (1273x701 client): same method as fov_calibrate.py (EDGE1 waterline
per column cast onto the terrain; the right FOV puts the hits on the sea-level contour), on the v4 terrain."""
import math
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees'
                   r'\codex-handoff-review-74f290\tools\terrain')
from v30_common import tri_sample  # noqa: E402

with np.load('E:/DayZ-Baltic-Build/v30-v4/coast/terrain_coast.npz') as d:
    H = d['heights'].astype(np.float64)
cam = np.array([2061.0, 35.8, 7341.0])
look = np.array([2091.0, 0.8, 7371.0])
f = (look - cam) / np.linalg.norm(look - cam)
right = np.array([f[2], 0.0, -f[0]])
right /= np.linalg.norm(right)
up = np.cross(right, f)
if up[1] < 0:
    up = -up

for name, sea in (('032804_222', 0.650), ('032757_963', 0.850)):
    img = np.asarray(Image.open(f'E:/DayZ-Baltic-Build/v30-v4/views/shots/capture_20261005_{name}.jpg')
                     .convert('RGB')).astype(np.float64)
    HH, W = img.shape[:2]
    R, G, B = img[..., 0], img[..., 1], img[..., 2]
    landish = (G > B + 4) & (G > R)
    obs = []
    y0, y1 = int(900 / 1080 * HH), int(200 / 1080 * HH)
    for x in range(int(80 / 1920 * W), int(1880 / 1920 * W), max(1, int(40 / 1920 * W))):
        col = landish[:, x]
        for y in range(y0, y1, -1):
            if col[y - 4:y].all():
                obs.append((x, y))
                break
    obs = np.array(obs, dtype=np.float64)

    def cast(px, py, vfov):
        t = math.tan(vfov / 2)
        dvec = f + right * ((px - W / 2) / (W / 2)) * t * W / HH + up * ((HH / 2 - py) / (HH / 2)) * t
        dvec /= np.linalg.norm(dvec)
        ts = np.arange(1.0, 1500, 0.25)
        p = cam[None, :] + ts[:, None] * dvec[None, :]
        ter = tri_sample(H, p[:, 0], p[:, 2])
        k = np.nonzero(p[:, 1] <= np.maximum(ter, sea))[0]
        return None if k.size == 0 else p[k[0]]

    print(name, 'sea', sea, 'size', W, HH, 'observed waterline points', len(obs))
    best = None
    for deg in np.arange(60, 78.01, 1.0):
        errs = []
        for px, py in obs:
            hit = cast(px, py, math.radians(deg))
            if hit is not None:
                errs.append(abs(tri_sample(H, [hit[0]], [hit[2]])[0] - sea))
        m = float(np.median(errs)) if errs else float('nan')
        best = (m, deg) if best is None or m < best[0] else best
        print(f'  vfov {deg:4.1f}: median |terrain - sea| {m:6.3f} m over {len(errs)} columns')
    print('  best', best)

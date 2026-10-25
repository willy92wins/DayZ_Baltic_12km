"""Prototype: land-cover classes at 1 m as build_surface_v30.py picks them today (nearest 6 m vertex of the 5 x 5
majority raster, at coordinates warped by smooth noise) against a smooth pick (each class's one-hot raster blurred with a
Gaussian of SIGMA vertices, bilinear at the same warped coordinates, then the strongest class). Same palette, no water,
roads or shading, so only the class boundaries differ. Usage: landcover_proto.py TERRAIN.npz OUT.png SIGMA x0 z0 x1 z1"""
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

sys.path.insert(0, r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees'
                   r'\codex-handoff-review-74f290\tools\terrain')
import build_surface_v30 as bs  # noqa: E402

terrain, out, sigma = sys.argv[1], sys.argv[2], float(sys.argv[3])
x0, z0, x1, z1 = (float(v) for v in sys.argv[4:8])
bs.load(terrain)
G, noise, LAND = bs.G, bs.noise, bs.LAND
X, Z = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(z1, z0, -1.0) - 0.5)
wx = 6.0 * noise(X, Z, 23.0, "wx") + 2.0 * noise(X, Z, 7.0, "wz")
wz = 6.0 * noise(X, Z, 23.0, "wz") + 2.0 * noise(X, Z, 7.0, "wx")
# today: nearest vertex
lr = np.clip(np.rint((12282 - (Z + wz)) / 6).astype(int), 0, 2047)
lc = np.clip(np.rint((X + wx) / 6).astype(int), 0, 2047)
near = G["wc"][lr, lc]
# smooth: blurred one-hot fields, bilinear
classes = np.array(sorted(LAND))
fr, fc = (12282 - (Z + wz)) / 6, (X + wx) / 6
r0 = np.clip(np.floor(fr).astype(int), 0, 2046)
c0 = np.clip(np.floor(fc).astype(int), 0, 2046)
tr, tc = np.clip(fr - r0, 0, 1), np.clip(fc - c0, 0, 1)
pr0, pr1 = max(r0.min() - 8, 0), min(r0.max() + 10, 2048)
pc0, pc1 = max(c0.min() - 8, 0), min(c0.max() + 10, 2048)
sub = G["wc"][pr0:pr1, pc0:pc1]
best, bestv = np.zeros(X.shape, np.uint8), np.full(X.shape, -1.0)
for k in classes:
    f = gaussian_filter((sub == k).astype(np.float32), sigma) if sigma > 0 else (sub == k).astype(np.float32)
    rr, cc = r0 - pr0, c0 - pc0
    v = (f[rr, cc] * (1 - tr) * (1 - tc) + f[rr, cc + 1] * (1 - tr) * tc + f[rr + 1, cc] * tr * (1 - tc)
         + f[rr + 1, cc + 1] * tr * tc)
    m = v > bestv
    best[m], bestv[m] = k, v[m]
pal = {k: np.array(col) * 3 for k, (_, col) in LAND.items()}
img = np.zeros(X.shape + (2,) + (3,), np.uint8)
a = np.zeros(X.shape + (3,))
b = np.zeros(X.shape + (3,))
for k, col in pal.items():
    a[near == k] = col
    b[best == k] = col
both = np.concatenate([np.clip(a, 0, 255), np.full((X.shape[0], 8, 3), 255.0), np.clip(b, 0, 255)], axis=1)
Image.fromarray(both.astype(np.uint8), 'RGB').resize((both.shape[1] * 2, both.shape[0] * 2), Image.NEAREST).save(out)
print('changed share', float((near != best).mean()))

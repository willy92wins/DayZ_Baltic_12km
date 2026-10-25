"""Plot a flowing-water shore window (contours within 15 m of the water): vertex classes, the exact 24 m corridor, the smoothed outline, and the engine
waterline (native triangles with NW-SE diagonals; per-vertex level of the nearest flowing water) before and after
profile_rivers_v30. Usage: plot_river_shore.py BEFORE.npz AFTER.npz X0 Z0 SIZE OUT.png [TITLE]"""
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.tri as mtri  # noqa: E402
import numpy as np  # noqa: E402
from scipy import ndimage  # noqa: E402

sys.path.insert(0, r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290\tools\terrain')
from finish_shores_v30 import protect_corridors  # noqa: E402
from v30_common import cell_planes  # noqa: E402

p0, p1, x0, z0, size, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), sys.argv[6]
title = sys.argv[7] if len(sys.argv) > 7 else ''
t0, t1 = np.load(p0), np.load(p1)
cls, lev = t0['cls'], t0['level'].astype(float)
flow = np.isin(cls, (3, 5, 6)) & (lev > 0.80)
exact, _, _, _ = protect_corridors(cell_planes(cls, lev))
c0, c1 = int(x0 / 6), int((x0 + size) / 6) + 1
r0, r1 = int((12282 - z0 - size) / 6), int((12282 - z0) / 6) + 1
g = 20
R0, R1, C0, C1 = max(r0 - g, 0), r1 + g, max(c0 - g, 0), c1 + g
F = flow[R0:R1, C0:C1]
_, (ir, ic) = ndimage.distance_transform_edt(~F, return_indices=True)
lnear = lev[R0:R1, C0:C1][ir, ic]
base = np.where(F, -ndimage.distance_transform_edt(F), ndimage.distance_transform_edt(~F)) * 6.0
smooth = np.clip(ndimage.gaussian_filter(base, 2.0), base - 4.0, base + 4.0)
crop = (slice(r0 - R0, r1 - R0), slice(c0 - C0, c1 - C0))
W = (slice(r0, r1), slice(c0, c1))
rr, cc = np.mgrid[r0:r1, c0:c1]
X, Z = cc * 6.0, 12282.0 - rr * 6.0
nr, nc = X.shape
idx = np.arange(nr * nc).reshape(nr, nc)
tris = []
for r in range(nr - 1):
    for c in range(nc - 1):
        a, b, d, e = idx[r, c], idx[r, c + 1], idx[r + 1, c], idx[r + 1, c + 1]
        tris += [[a, b, e], [a, d, e]]   # NW-SE diagonal (r, c)-(r + 1, c + 1)
tri = mtri.Triangulation(X.ravel(), Z.ravel(), np.array(tris))
L = lnear[crop]
Wall = cls[R0:R1, C0:C1] > 0
dall, (jr, jc) = ndimage.distance_transform_edt(~Wall, sampling=6.0, return_indices=True)
# the waterline of flowing water only: within 15 m, where the nearest water vertex is flowing
shore = ((dall <= 15.0) & F[jr, jc])[crop]
fig, ax = plt.subplots(figsize=(10, 10))
wet, fix = flow[W], exact[W]
ax.scatter(X[wet & ~fix], Z[wet & ~fix], s=6, c='#3b6ea5', label='agua que fluye')
ax.scatter(X[wet & fix], Z[wet & fix], s=6, c='#17becf', label='corredor fijo de 24 m')
ax.scatter(X[~wet], Z[~wet], s=6, c='#8a8a5a', label='tierra / otra')
ax.tricontour(tri, np.where(shore, (t0['heights'][W].astype(float) - L), 10.0).ravel(), levels=[0], colors='#d62728', linewidths=1.6)
ax.tricontour(tri, np.where(shore, (t1['heights'][W].astype(float) - L), 10.0).ravel(), levels=[0], colors='#1f77b4', linewidths=1.6)
ax.contour(X, Z, smooth[crop], levels=[0], colors='#2ca02c', linewidths=1.0, linestyles='--')
ax.plot([], [], c='#d62728', label='orilla antes (motor)')
ax.plot([], [], c='#1f77b4', label='orilla después (motor)')
ax.plot([], [], c='#2ca02c', ls='--', label='contorno suavizado')
ax.set_aspect('equal')
ax.legend(loc='upper right', fontsize=9)
ax.set_title(title or f'ventana {size:.0f} m en x {x0:.0f}, z {z0:.0f}')
fig.savefig(out, dpi=90, bbox_inches='tight')
print(out)

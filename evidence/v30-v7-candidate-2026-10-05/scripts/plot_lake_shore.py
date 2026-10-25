"""Plot a lake shore window: vertex classes, the smoothed outline, and the engine waterline (native triangles with
NW-SE diagonals) before and after profile_lakes_v30. Usage: plot_lake_shore.py BODY_ID X0 Z0 SIZE OUT.png"""
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.tri as mtri  # noqa: E402
import numpy as np  # noqa: E402
from scipy import ndimage  # noqa: E402

sys.path.insert(0, r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290\tools\terrain')
from relevel_bodies_v30 import label_bodies  # noqa: E402

body, x0, z0, size, out = int(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
t0 = np.load('E:/DayZ-Baltic-Build/v30-v6/causeway/terrain_causeway.npz')
t1 = np.load('E:/DayZ-Baltic-Build/v30-v7/lakes/terrain_lakes.npz')
cls, lev = t0['cls'], t0['level'].astype(float)
ids = label_bodies(cls, lev)
B = ids == body
L = float(np.median(lev[B]))
c0, c1 = int(x0 / 6), int((x0 + size) / 6) + 1
r0, r1 = int((12282 - z0 - size) / 6), int((12282 - z0) / 6) + 1
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
# smoothed outline as the tool builds it (whole-body window, then cropped)
g = 20
R0, R1, C0, C1 = max(r0 - g, 0), r1 + g, max(c0 - g, 0), c1 + g
Bw = ids[R0:R1, C0:C1] == body
base = np.where(Bw, -ndimage.distance_transform_edt(Bw), ndimage.distance_transform_edt(~Bw)) * 6.0
smooth = ndimage.gaussian_filter(base, 2.0)
smooth = np.clip(smooth, base - 4.0, base + 4.0)[r0 - R0:r0 - R0 + nr, c0 - C0:c0 - C0 + nc]
fig, ax = plt.subplots(figsize=(10, 10))
wet = B[W]
ax.scatter(X[wet], Z[wet], s=6, c='#3b6ea5', label='agua del lago')
ax.scatter(X[~wet], Z[~wet], s=6, c='#8a8a5a', label='tierra / otra')
ax.tricontour(tri, (t0['heights'][W].astype(float) - L).ravel(), levels=[0], colors='#d62728', linewidths=1.6)
ax.tricontour(tri, (t1['heights'][W].astype(float) - L).ravel(), levels=[0], colors='#1f77b4', linewidths=1.6)
ax.contour(X, Z, smooth, levels=[0], colors='#2ca02c', linewidths=1.0, linestyles='--')
ax.plot([], [], c='#d62728', label='orilla v6 (motor)')
ax.plot([], [], c='#1f77b4', label='orilla v7 (motor)')
ax.plot([], [], c='#2ca02c', ls='--', label='contorno suavizado')
ax.set_aspect('equal')
ax.legend(loc='upper right', fontsize=9)
ax.set_title(f'cuerpo {body}, agua a {L:.2f} m, ventana {size:.0f} m')
fig.savefig(out, dpi=90, bbox_inches='tight')
print(out)

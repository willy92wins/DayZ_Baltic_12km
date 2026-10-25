import numpy as np, json
from scipy.ndimage import distance_transform_edt
rng = np.random.default_rng(20261013)
fp = np.load("E:/DayZ-Baltic-Build/v31-pond-layer-20261013/fp-p0/footprint.npz"); plane = fp["plane"].astype(float); field = fp["field"]
H = np.load("E:/DayZ-Baltic-Build/v31-ev103-sills-cones-20261012/terrain-ev103.npz")["heights"].astype(float)
wx0, wx1, wz0, wz1 = 7776, 10224, 8976, 11040
r0, r1, c0, c1 = int((12282 - wz1) / 6), int((12282 - wz0) / 6), int(wx0 / 6), int(wx1 / 6)
inwin = np.zeros(plane.shape, bool); inwin[r0:r1, c0:c1] = True
fpm = np.isfinite(plane)
nw, ne, sw, se = H[:-1, :-1], H[:-1, 1:], H[1:, :-1], H[1:, 1:]
cmax = np.maximum.reduce([nw, ne, sw, se]); cmin = np.minimum.reduce([nw, ne, sw, se])
pts = []
def add(kind, cells, n, extra=None):
    if len(cells) == 0: return
    idx = rng.choice(len(cells), size=min(n, len(cells)), replace=False)
    for k in idx:
        r, c = cells[k]
        x, z = 6 * c + 4, 12282 - 6 * r - 2           # centroid of native triangle A (NW, NE, SE)
        h = (nw[r, c] + ne[r, c] + se[r, c]) / 3
        pts.append(dict(id=f"{kind}_{len(pts)}", kind=kind, x=float(x), z=float(z), plane=float(plane[r, c]) if fpm[r, c] else None, h=float(h)))
wet = np.argwhere(fpm & inwin & (cmax < plane - 0.10))
add("wet", wet, 60)
bur = np.argwhere(fpm & inwin & (cmin >= plane + 0.05))
add("buried", bur, 40)
d = distance_transform_edt(~fpm) * 6.0
for dist in (3, 6, 9, 12):
    ring = np.argwhere(~fpm & inwin & (np.abs(d - dist) < 3) & (cmin > 0.95))
    add(f"out{dist}", ring, 30)
with open("BalticPondLayerProbeV1.BalticTrial/points.csv", "w", newline="\n") as f:
    for i, p in enumerate(pts):
        f.write(f"{i};{p['x']:.6f} 0 {p['z']:.6f}\n")
json.dump(pts, open("probe_points.json", "w"), indent=1)
from collections import Counter
print(len(pts), Counter(p["kind"] for p in pts))

"""Server probe points for the full-map v31 layer: wet / buried / outside samples over the whole map plus every lagoon
centre. Usage: probe_points_map.py <footprint.npz> <terrain.npz> <lagoons-report.json> <points.csv> <points.json>"""
import json, sys
import numpy as np
from scipy.ndimage import distance_transform_edt
fp_path, t_path, lag_path, csv_path, json_path = sys.argv[1:6]
rng = np.random.default_rng(20261013)
fp = np.load(fp_path); plane = fp["plane"].astype(float)
H = np.load(t_path)["heights"].astype(float)
fpm = np.isfinite(plane)
nw, ne, sw, se = H[:-1, :-1], H[:-1, 1:], H[1:, :-1], H[1:, 1:]
cmax = np.maximum.reduce([nw, ne, sw, se]); cmin = np.minimum.reduce([nw, ne, sw, se])
pts = []
def add(kind, cells, n):
    idx = rng.choice(len(cells), size=min(n, len(cells)), replace=False)
    for k in idx:
        r, c = cells[k]
        pts.append(dict(id=len(pts), kind=kind, x=float(6 * c + 4), z=float(12282 - 6 * r - 2), plane=float(plane[r, c]) if fpm[r, c] else None))
add("wet", np.argwhere(fpm & (cmax < plane - 0.10)), 100)
add("buried", np.argwhere(fpm & (cmin >= plane + 0.05)), 60)
d = distance_transform_edt(~fpm) * 6.0
for dist in (6, 9, 12):
    add(f"out{dist}", np.argwhere(~fpm & (np.abs(d - dist) < 3) & (cmin > 0.95)), 30)
for l in json.load(open(lag_path))["lagoons"]:
    pts.append(dict(id=len(pts), kind="lagoon", x=float(l["x"]), z=float(l["z"]), plane=float(l["level"])))
with open(csv_path, "w", newline="\n") as f:
    for p in pts:
        f.write(f"{p['id']};{p['x']:.6f} 0 {p['z']:.6f}\n")
json.dump(pts, open(json_path, "w"), indent=1)
from collections import Counter
print(len(pts), Counter(p["kind"] for p in pts))

import json, sys
import numpy as np
from shapely import STRtree, points as shp_points
from shapely.geometry import Polygon
sys.path[:0] = [r"C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts", r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290\tools\terrain"]
from odol_reader import ODOL
from wrp0wzd import read
P = "E:/DayZ-Baltic-Build/v31-pond-layer-20261013"
rep = json.load(open(f"{P}/p0/stage-report.json")); wx0, wx1, wz0, wz1 = rep["window"]
fp = np.load(f"{P}/fp-p0/footprint.npz"); plane = fp["plane"].astype(float); vis = fp["visible"]
base = np.isfinite(np.load("E:/DayZ-Baltic-Build/v30-shore-sdf-20261011/cover-level-ev98.npy"))
temp = f"{P}/p0/water/temp/baltic_water_v30"
w0 = read("E:/DayZ-Baltic-Build/v31-ev103-sills-cones-20261012/stage/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp")
dropped = {d["id"] for d in rep["dropped_list"]}
polys, ids = [], []
cache = {}
for o in w0["objects"]:
    if o["id"] not in dropped: continue
    name = o["name"].split("\\")[-1]
    if name not in cache: cache[name] = ODOL.from_file(f"{temp}/{name}")
    od = cache[name]; road = min(od.lods, key=lambda l: abs(l.resolution - 3e15))
    v = np.array([(p.x, p.y, p.z) for p in road.vertices]) + np.array(o["matrix"][9:12])
    for f in road.faces:
        polys.append(Polygon(v[list(f.vertex_indices)][:, [0, 2]])); ids.append(o["id"])
tree = STRtree(polys)
cells = []
for r in range(int((12282 - wz1 - 96) / 6), int((12282 - wz0 + 96) / 6)):
    for c in range(int((wx0 - 96) / 6), int((wx1 + 96) / 6)):
        inwin = 6*c >= wx0 and 6*c+6 <= wx1 and 12282-6*r-6 >= wz0 and 12282-6*r <= wz1
        if not inwin and (base[r, c] or np.isfinite(plane[r, c])):
            pts = shp_points([6*c+4, 6*c+2], [12282-6*r-2, 12282-6*r-4])
            hit = len(tree.query(pts, predicate="within")[0]) > 0
            if hit: cells.append((r, c, bool(vis[r, c]), bool(np.isfinite(plane[r, c]))))
print("frame cells covered by DROPPED records:", len(cells), "visible:", sum(c[2] for c in cells), "in new footprint:", sum(c[3] for c in cells))
print("max distance outside window (m):", max(max(wx0 - 6*c, 6*c + 6 - wx1, wz0 - (12282-6*r-6) if 12282-6*r-6 < wz0 else 0, (12282-6*r) - wz1) for r, c, _, _ in cells) if cells else 0)

"""Rasterize the physical footprint of every kept EV98 pond piece into a per-cell plane level (NaN = no piece)."""
import sys, hashlib, numpy as np, shapely
from shapely.geometry import Polygon
from rasterio.features import rasterize
from affine import Affine
sys.path.insert(0, r"C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/tools/terrain")
sys.path.insert(0, r"C:/Users/guill/.claude/skills/dayz-p3d-debinarizer/scripts")
from wrp0wzd import read
from odol_reader import ODOL
B = "E:/DayZ-Baltic-Build/v30-pond-sea-separation-20261011-b"
M = "E:/DayZ-Baltic-Build/v30-global-contour-pass-20261009/package/water/temp/baltic_water_v30/"
w = read(B + "/stage/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp")
cache, items = {}, []
for o in w["objects"]:
    n = o["name"].lower()
    if not n.startswith("baltic_water_v30"): continue
    m = n.split("\\")[-1]
    if m not in cache:
        od = ODOL.from_file(M + m); road = min(od.lods, key=lambda l: abs(l.resolution - 3e15))
        rv = np.array([(v.x, v.y, v.z) for v in road.vertices])
        cache[m] = (rv[:, 1].mean(), shapely.union_all([Polygon(rv[list(f.vertex_indices)][:, [0, 2]]) for f in road.faces]))
    y, poly = cache[m]; pos = o["matrix"][9:12]
    items.append((shapely.affinity.translate(poly, pos[0], pos[2]), y + pos[1]))
T = Affine(6, 0, 0, 0, -6, 12282)
lev = np.full((2047, 2047), np.nan, np.float32)
# write highest level last so overlaps keep the max plane
for s, y in sorted(items, key=lambda t: t[1]):
    m = rasterize([(s, 1)], out_shape=(2047, 2047), transform=T, fill=0, dtype="uint8").astype(bool) if False else None
order = sorted(range(len(items)), key=lambda i: items[i][1])
idx = rasterize(((items[i][0], k + 1) for k, i in enumerate(order)), out_shape=(2047, 2047), transform=T, fill=0, dtype="uint32")
levels = np.array([np.nan] + [items[i][1] for i in order], np.float64)
lev = levels[idx].astype(np.float32)
np.save("E:/DayZ-Baltic-Build/v30-shore-sdf-20261011/cover-level-ev98.npy", lev)
print("covered cells", int(np.isfinite(lev).sum()), "pieces", len(items), "level range", np.nanmin(lev), np.nanmax(lev))

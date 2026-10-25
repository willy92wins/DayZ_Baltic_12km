"""Independent check of EV98: union of kept pond-piece footprints vs sub-clear wet beds, and navigable draft."""
import sys, numpy as np, shapely
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
z = np.load(B + "/terrain-ev98.npz"); H, W, C, L = z["heights"], z["water"] | (z["cls"] > 0), z["cls"], z["level"]
assert np.array_equal(w["heights"], H[::-1])
cache, shapes, lv = {}, [], []
for o in w["objects"]:
    n = o["name"].lower()
    if not n.startswith("baltic_water_v30"): continue
    m = n.split("\\")[-1]
    if m not in cache:
        od = ODOL.from_file(M + m); road = min(od.lods, key=lambda l: abs(l.resolution - 3e15))
        rv = np.array([(v.x, v.y, v.z) for v in road.vertices])
        cache[m] = (rv[:, 1].mean(), shapely.union_all([Polygon(rv[list(f.vertex_indices)][:, [0, 2]]) for f in road.faces]))
    y, poly = cache[m]; pos = o["matrix"][9:12]
    shapes.append(shapely.affinity.translate(poly, pos[0], pos[2])); lv.append(y + pos[1])
lv = np.array(lv); print("pieces", len(lv), "min level", lv.min().round(3), "pieces below 0.95", int((lv < 0.95).sum()))
cov = rasterize(((s, 1) for s in shapes), out_shape=(2047, 2047), transform=Affine(6, 0, 0, 0, -6, 12282), fill=0, dtype="uint8") > 0
corner = np.zeros((2048, 2048), bool)
for dr in (0, 1):
    for dc in (0, 1):
        corner[dr:dr + 2047, dc:dc + 2047] |= cov
bad = corner & W & (H < 1.0)
rr, cc = np.nonzero(bad)
print("wet sub-clear vertices under a kept pond piece:", int(bad.sum()))
if bad.any(): print(" sample (x,z,bed):", [(int(c*6), int((2047-r)*6), round(float(H[r, c]), 2)) for r, c in list(zip(rr, cc))[:10]])
nav = (C == 3) & corner & W & np.isfinite(L)
d = L[nav] - H[nav]; print("navigable under pieces: vertices", int(nav.sum()), "min draft %.3f" % d.min(), "below 0.95:", int((d < 0.95 - 1e-4).sum()))

"""Seam check (dam_gates_v31 G1 a+b, no dam) on every near-contact site of census_near.py, on a terrain + footprint.
Usage: census_seams.py <terrain.npz> <footprint.npz> <census-near.json> <out.json>"""
import json, os, sys
import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "tools", "water"))
from dam_gates_v31 import raster, PX, SEAM_R, EDGE_TOL, TIDES, N8

tp, fpp, cp, outp = sys.argv[1:5]
H = np.load(tp)["heights"].astype(np.float64); fp = np.load(fpp)
plane = fp["plane"].astype(np.float64); field = fp["field"]
rows = []
for s in json.load(open(cp))["list"]:
    x0, x1, z0, z1 = s["x"] - 40, s["x"] + 40, s["z"] - 40, s["z"] + 40
    X, Z, T, cov, P, F, pond = raster(H, plane, field, x0, x1, z0, z1)
    res = dict(id=s["id"], x=s["x"], z=s["z"], kind=s["kind"], ev102_raised=s["ev102_raised"], contact_cells_8=s["contact_cells_8"])
    for L in TIDES:
        sea = (~cov) & (T < L)
        adj = pond & binary_dilation(sea, N8)
        expo = np.zeros(X.shape, bool)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr or dc:
                    nu = np.roll(np.roll(~cov, -dr, 0), -dc, 1); nT = np.roll(np.roll(T, -dr, 0), -dc, 1)
                    expo |= pond & nu & (nT < P - EDGE_TOL)
        expo[[0, -1], :] = False; expo[:, [0, -1]] = False
        dsea = distance_transform_edt(~sea) * PX if sea.any() else np.full(X.shape, np.inf)
        gap = float(dsea[pond].min()) if pond.any() and sea.any() else None
        res[f"tide_{L}"] = dict(adjacent_px=int(adj.sum()), exposed_near_sea_px=int((expo & (dsea <= SEAM_R)).sum()),
                                min_gap_m=None if gap is None else round(gap, 2))
    res["seam"] = any(res[f"tide_{L}"]["adjacent_px"] or res[f"tide_{L}"]["exposed_near_sea_px"] for L in TIDES)
    rows.append(res)
    print(res["id"], res["kind"], s["x"], s["z"], "sill" if s["ev102_raised"] else "-", "SEAM" if res["seam"] else "ok",
          [(res[f"tide_{L}"]["adjacent_px"], res[f"tide_{L}"]["exposed_near_sea_px"], res[f"tide_{L}"]["min_gap_m"]) for L in TIDES])
json.dump(dict(terrain=tp, footprint=fpp, sites=rows, seams=sum(r["seam"] for r in rows)), open(outp, "w", newline="\n"), indent=1)

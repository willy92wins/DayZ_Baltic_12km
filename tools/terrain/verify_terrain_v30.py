"""Offline gates for terrain V30 other than roads (roads: verify_roads_v30.py).

water_depth  every water vertex at least 0.10 m below its level (sea 0.75 m), Narva zone excluded (V29 exact)
banks        every land vertex within 8.5 m of water at least 0.05 m above the nearest water level (shores are
             slopes from the smooth outline; the plane edge must still lie under land)
land_floor   every land vertex >= 1.40 m (the sea, 0.5-1.0 m with tide, never floods land), except the beach strip
             along the smoothed coast (terrain mask 'beach'), which must stay >= 0.80 m; with --low-water-bank-min
             M a land vertex 8-adjacent to inland water (classes 2, 3, 5, 6, 7, level > 0.80 m) whose level is
             under 1.35 m passes at max(level + 0.05, M) instead (the highest such adjacent level)
slopes       land triangles (all three corners land) <= 35 degrees (+0.01 for float32: V29 itself is capped at
             35.000x in the Narva zone); triangles touching water reported, not gated
bed_floor    no vertex below -12.0 m, V29's deepest sea floor (a bed is cut, never dug as a pit)
pieces       every cell a pond piece covers (v30_common.cell_planes): water corners >= 0.02 m under the plane, land
             corners >= 0.00 m over it, outside the 600 m Narva zone
narva        heights within 480 m of the bridge centre identical to V29 (ASC ed6cdaa5)
Usage: verify_terrain_v30.py <terrain.npz> [--json out.json] [--sea-cut 0.80] [--low-water-bank-min M]
                             (pond planes above the sea cut)
"""
import json
import hashlib
import os
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v30_common import cell_planes  # noqa: E402

R = r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev"
NARVA = (2417.1428225906, 6889.8850822322)
G = {"depth_min_m": 0.10, "bank_radius_m": 8.5, "bank_min_m": 0.05, "land_floor_m": 1.40, "beach_floor_m": 0.80, "slope_max_deg": 35.0, "slope_tol_deg": 0.01, "bed_floor_m": -12.0,
     "narva_radius_m": 480.0, "narva_zone_excluded_m": 600.0}


def main():
    t = np.load(sys.argv[1])
    h = t["heights"].astype(float)
    cls, level = t["cls"], t["level"].astype(float)
    water = cls > 0
    n = h.shape[0]
    c, r = np.meshgrid(np.arange(n), np.arange(n))
    dn = np.hypot(c * 6.0 - NARVA[0], 12282 - r * 6.0 - NARVA[1])
    out = {}
    zone = dn <= G["narva_zone_excluded_m"]
    m = water & ~zone
    depth = level[m] - h[m]
    out["water_depth"] = {"vertices": int(m.sum()), "fail": int((depth < G["depth_min_m"]).sum()),
                          "min_m": round(float(depth.min()), 3),
                          "by_class_fail": {int(k): int(((level - h) < G["depth_min_m"])[m & (cls == k)].sum()) for k in range(1, 8)}}
    dist, idx = distance_transform_edt(~water, sampling=6.0, return_indices=True)
    near_lv = level[idx[0], idx[1]]
    b = (~water) & (dist <= G["bank_radius_m"]) & ~zone
    over = h[b] - near_lv[b]
    out["banks"] = {"vertices": int(b.sum()), "fail": int((over < G["bank_min_m"]).sum()), "min_m": round(float(over.min()), 3)}
    land = ~water
    sea_cut = float(sys.argv[sys.argv.index("--sea-cut") + 1]) if "--sea-cut" in sys.argv else 0.80
    lw_min = float(sys.argv[sys.argv.index("--low-water-bank-min") + 1]) if "--low-water-bank-min" in sys.argv else None
    plane = cell_planes(cls, level, sea_cut=sea_cut)
    czone = zone[:-1, :-1] | zone[:-1, 1:] | zone[1:, :-1] | zone[1:, 1:]
    pw = pl = 0
    for dr in (0, 1):
        for dc in (0, 1):
            hc = h[dr:dr + n - 1, dc:dc + n - 1]
            wc = water[dr:dr + n - 1, dc:dc + n - 1]
            ok = np.isfinite(plane) & ~czone
            with np.errstate(invalid="ignore"):
                pw += int((ok & wc & (hc > plane - 0.02)).sum())
                pl += int((ok & ~wc & (hc < plane)).sum())
    out["pieces"] = {"cells": int((np.isfinite(plane) & ~czone).sum()), "water_corner_fail": pw, "land_corner_fail": pl,
                     "fail": pw + pl}
    out["bed_floor"] = {"fail": int((h < G["bed_floor_m"] - 1e-6).sum()), "min_m": round(float(h.min()), 3)}
    beach = t["beach"] if "beach" in t.files else np.zeros_like(land)
    inland = land & ~zone & ~beach
    under = inland & (h < G["land_floor_m"] - 1e-6)
    fail_lf, elig, lwb = int(under.sum()), np.zeros_like(inland), {}
    if lw_min is not None:
        # very low inland water: a bank vertex 8-adjacent to it passes at max(adjacent level + 0.05, M)
        iw = np.isin(cls, (2, 3, 5, 6, 7)) & (level > 0.80) & (level + G["bank_min_m"] < G["land_floor_m"])
        pad = np.pad(np.where(iw, level, -np.inf), 1, constant_values=-np.inf)
        best = np.full(h.shape, -np.inf)
        for dr in (0, 1, 2):
            for dc in (0, 1, 2):
                if (dr, dc) != (1, 1):
                    best = np.fmax(best, pad[dr:dr + n, dc:dc + n])
        elig = inland & (best > -np.inf)
        f = int((elig & (h < np.maximum(best + G["bank_min_m"], lw_min) - 1e-6)).sum())
        lwb = {"low_water_bank": {"vertices": int(elig.sum()), "fail": f}}
        fail_lf = int((under & ~elig).sum()) + f
    out["land_floor"] = {"vertices": int(inland.sum()), "fail": fail_lf,
                         "min_m": round(float(h[inland].min()), 3),
                         "beach_vertices": int(beach.sum()),
                         "beach_fail": int((h[beach] < G["beach_floor_m"] - 1e-6).sum()), **lwb}
    nw, ne, sw, se = h[:-1, :-1], h[:-1, 1:], h[1:, :-1], h[1:, 1:]
    au = np.degrees(np.arctan(np.hypot((ne - nw) / 6, (se - ne) / 6)))
    al = np.degrees(np.arctan(np.hypot((sw - nw) / 6, (se - sw) / 6)))
    lnw, lne, lsw, lse = land[:-1, :-1], land[:-1, 1:], land[1:, :-1], land[1:, 1:]
    mu, ml = lnw & lne & lse, lnw & lsw & lse
    su, sl = (lnw | lne | lse) & ~mu, (lnw | lsw | lse) & ~ml
    land_ang = np.r_[au[mu], al[ml]]
    shore_ang = np.r_[au[su], al[sl]]
    out["slopes"] = {"land_triangles": int(land_ang.size), "fail": int((land_ang > G["slope_max_deg"] + G["slope_tol_deg"]).sum()),
                     "within_tolerance": int(((land_ang > G["slope_max_deg"]) & (land_ang <= G["slope_max_deg"] + G["slope_tol_deg"])).sum()),
                     "max_deg": round(float(land_ang.max()), 2),
                     "shore_triangles_over_35": int((shore_ang > G["slope_max_deg"]).sum()),
                     "shore_max_deg": round(float(shore_ang.max()), 2)}
    with rasterio.open(os.path.join(R, "tests", "regional_road_network_v29", "baltic_road_network_v29.asc")) as ds:
        v29 = ds.read(1).astype("float32")
    nz = dn <= G["narva_radius_m"]
    out["narva"] = {"vertices": int(nz.sum()), "identical": bool(np.array_equal(t["heights"][nz], v29[nz])),
                    "max_diff_m": float(np.abs(t["heights"][nz] - v29[nz]).max())}
    gates = [out["water_depth"]["fail"], out["banks"]["fail"], out["land_floor"]["fail"], out["land_floor"]["beach_fail"],
             out["slopes"]["fail"], out["pieces"]["fail"],
             out["bed_floor"]["fail"]]
    out["status"] = "PASS" if all(g == 0 for g in gates) and out["narva"]["identical"] else "FAIL"
    out["limits"] = dict(G, sea_cut_m=sea_cut)
    out['terrain_sha256'] = hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest()
    out['sources'] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (
        Path(__file__), Path(cell_planes.__code__.co_filename),
        Path(R) / 'tests/regional_road_network_v29/baltic_road_network_v29.asc')}
    print(json.dumps(out, indent=1))
    if "--json" in sys.argv:
        with open(sys.argv[sys.argv.index("--json") + 1], "wb") as f:
            f.write(json.dumps(out, indent=1).encode("utf-8"))


if __name__ == "__main__":
    main()

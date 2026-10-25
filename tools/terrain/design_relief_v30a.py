"""Relief V30, option A (moderate): V29 character kept, seams removed, plains in the real lowlands.

1. Codex's relief pipeline (reproduced exactly by design_relief_v30.v2_uplift/v3_project) is re-run with Codex's
   own factor and controls, minus the SPB rectangle, the reserve mask (which holds the study ellipse) and the
   wetlands. Hills then continue where the old protection left straight and elliptical walls.
2. H1 = V29 + (R_seamless - R_old), applied outside the envelope of engineered water, Narva and map edges.
3. H = base + g * (H1 - base): g = 1 in the high cores, ~0.25 in plains (real lowlands, wetlands, real reserve
   polygons, floodplains), ~0.6 elsewhere, all fields smooth and following the real large-scale elevation.
4. Slope cap 0.48 per axis with the envelope fixed, as Codex's v3.
Needs <b_dir>/relief_v30.npz from design_relief_v30.py (high, plain, big and envelope fields).
"""
import json
import os
import sys

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, gaussian_filter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from design_relief_v30 import R, ease, v2_uplift, v3_project  # noqa: E402

B_DIR, OUT = sys.argv[1], sys.argv[2]
P = {"g_plain": 0.25, "g_mid": 0.6, "plain_cut": [1.5, 3.0], "ease_m": 100, "dry_floor_m": 1.4, "slope_cap_per_axis_m": 2.88}
os.makedirs(OUT, exist_ok=True)


def main():
    b = np.load(os.path.join(B_DIR, "relief_v30.npz"))
    v1 = np.load(os.path.join(R, "tests", "regional_outline_v1", "reference.npz"))
    v3 = np.load(os.path.join(R, "tests", "regional_outline_v3", "reference.npz"))
    v29 = b["v29"].astype("float64")
    base = v1["base"]
    with rasterio.open(os.path.join(R, "source", "baltic_physical_2048_6m.asc")) as ds:
        physical = ds.read(1)
    n = base.shape[0]
    x, z = np.meshgrid(np.arange(n) * 6., 12282 - np.arange(n) * 6.)
    a = np.exp(-.5 * (((x - 5900) / 1700) ** 2 + ((z - 7950) / 1500) ** 2))
    bb = np.exp(-.5 * (((x - 4500) / 1700) ** 2 + ((z - 1100) / 1550) ** 2))
    macro = gaussian_filter(np.maximum(physical, 0).astype("float64"), 9)
    controls = v1["controls"] & ~(v1["spb"] | v1["reserve"] | v1["wetlands"])
    # Keep every control that is also hydrology, Narva or a road: only the area protections are dropped.
    controls |= v1["water"] | v1["narva"] | v1["road_core"] | (x < 24) | (x > 12258) | (z < 24) | (z > 12258)
    seamless = v3_project(v2_uplift(macro * (5 + 15 * a + 19 * bb), base, controls), base).astype("float64")
    envelope = b["envelope"]
    w = ease(distance_transform_edt(~envelope, sampling=6.0) / P["ease_m"])
    h1 = v29 + (seamless - v3["candidate"].astype("float64")) * w
    h1[envelope] = v29[envelope]

    high, plain_b, big = b["high"].astype("float64"), b["plain"].astype("float64"), b["big"].astype("float64")
    lowland = 1 - ease((big - P["plain_cut"][0]) / (P["plain_cut"][1] - P["plain_cut"][0]))
    plain = np.maximum(plain_b, lowland) * (1 - high)
    g = np.clip(high + (1 - high) * (plain * P["g_plain"] + (1 - plain) * P["g_mid"]), 0, 1)
    g = 1 - w * (1 - g)
    base64 = base.astype("float64")
    new = base64 + g * (h1 - base64)
    new[envelope] = v29[envelope]
    dry = (v29 >= P["dry_floor_m"]) & ~envelope
    new[dry] = np.maximum(new[dry], P["dry_floor_m"])

    cap = P["slope_cap_per_axis_m"]
    xcost = np.maximum(cap, np.abs(np.diff(v29, axis=1)))
    ycost = np.maximum(cap, np.abs(np.diff(v29, axis=0)))
    floor = np.where(dry, P["dry_floor_m"], -np.inf)
    for _ in range(512):
        nh = new.copy()
        nh[:, 1:] = np.minimum(nh[:, 1:], new[:, :-1] + xcost)
        nh[:, :-1] = np.minimum(nh[:, :-1], new[:, 1:] + xcost)
        nh[1:, :] = np.minimum(nh[1:, :], new[:-1, :] + ycost)
        nh[:-1, :] = np.minimum(nh[:-1, :], new[1:, :] + ycost)
        nh = np.maximum(nh, floor)
        nh[envelope] = v29[envelope]
        delta = float(np.max(np.abs(new - nh)))
        new = nh
        if delta < 1e-4:
            break
    else:
        raise ValueError("slope cap did not converge")
    assert np.array_equal(new[envelope], v29[envelope]) and np.isfinite(new).all()

    def slope(h):
        gy, gx = np.gradient(h, 6.0)
        return np.degrees(np.arctan(np.hypot(gx, gy)))

    s29, snew = slope(v29), slope(new)
    land = v29 > 1.0
    band = lambda s, x0, x1: round(float(s[(z > 8100) & (z < 9100) & (x > x0) & (x < x1)].mean()), 2)
    stats = {"params": P,
             "height_max": [round(float(v29.max()), 2), round(float(new.max()), 2)],
             "height_land_mean": [round(float(v29[land].mean()), 2), round(float(new[land].mean()), 2)],
             "slope_land_pct_over_v29_new": {f">{t}deg": [round(100 * float((s29[land] > t).mean()), 1), round(100 * float((snew[land] > t).mean()), 1)] for t in (5, 10, 15, 20, 25, 30)},
             "slope_land_median_deg": [round(float(np.median(s29[land])), 2), round(float(np.median(snew[land])), 2)],
             "flat_lt2deg_pct": [round(100 * float((s29[land] < 2).mean()), 1), round(100 * float((snew[land] < 2).mean()), 1)],
             "x6250_edge_slope_west_east": [[band(s29, 5900, 6150), band(s29, 6250, 6500)], [band(snew, 5900, 6150), band(snew, 6250, 6500)]]}
    np.savez_compressed(os.path.join(OUT, "relief_v30.npz"), new=new.astype("float32"), v29=b["v29"], f_old=b["f_old"],
                        f_new=g.astype("float32"), envelope=envelope, high=b["high"], plain=plain.astype("float32"))
    with open(os.path.join(OUT, "relief_v30_stats.json"), "wb") as f:
        f.write(json.dumps(stats, indent=1, ensure_ascii=False).encode("utf-8"))
    print(json.dumps({k: v for k, v in stats.items() if k != "params"}, ensure_ascii=False))


if __name__ == "__main__":
    main()

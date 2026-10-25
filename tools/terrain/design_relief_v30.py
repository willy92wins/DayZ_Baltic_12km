"""Relief V30 design: Codex's regional relief pipeline re-run with a natural exaggeration field.

Codex's relief (tests/regional_outline_v3) = base + uplift, built by
  v2  tools/navigation/prepare_relief_envelope.py: target = gauss(physical, 9) * F_old, uplift capped by a
      0.6-grade toe curve from the controls, smoothed (sigma 4);
  v3  tools/navigation/limit_regional_slopes.py: projection to 0.48 per-axis grade, never below base.
This script re-implements both steps, checks they reproduce v3 exactly with Codex's inputs, then runs them with
  F_new     follows real topography: high cores keep F_old, lowlands ~x1.2, mid elevations up to ~x2.8,
            plains (SPB lowland, real reserve polygons, wetlands, floodplains) ~x1.1;
  controls  water support, Narva, map edges and major roads only (no SPB rectangle, reserve ellipse or wetlands).
Design heights = V29 + (R_new - R_old) * w, with w = 0 inside the water/Narva/edge envelope and a 200 m ease out,
so every engineered water, shore and bridge height of V29 stays exact. Road bands are re-graded in phase 2.
"""
import json
import os
import sys

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt, gaussian_filter

R = r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev"
sys.path.insert(0, os.path.join(R, "tools", "navigation"))
from prepare_regional_outline import features, raster  # noqa: E402  Codex's own mask helpers
from geo_common import tb_geometry  # noqa: E402
from shapely import make_valid  # noqa: E402
from shapely.geometry import shape  # noqa: E402

OUT = sys.argv[1]
PARAMS = {
    "large_scale_sigma_px": 50,
    "lowland_to_mid": [1.0, 4.0],
    "factor_lowland": 1.2,
    "factor_mid": 2.8,
    "high_core_factor": [7.0, 16.0],
    "high_core_elevation": [3.0, 6.0],
    "core_factor": 10.0,                 # V29 high zones peak at ~25-55 m, rarely 107 m: x10 keeps that order
    "valley_grade": 0.30,                # Codex used 0.60 with a 36 m toe: V-shaped trenches
    "valley_toe_m": 60.0,
    "plain_factor": 1.1,
    "plain_sigma_px": 70,
    "floodplain_m": 150,
    "control_pond_min_m2": 300,
    "control_waterway_min_m": 600,
    "control_waterway_buffer_m": 12,
    "envelope_water_m": 30,
    "narva_radius_m": 480,
    "edge_m": 24,
    "ease_m": 100,
    "dry_floor_m": 1.4,
    "slope_cap_per_axis_m": 2.88,
}
os.makedirs(OUT, exist_ok=True)


def ease(t):
    t = np.clip(t, 0, 1)
    return t * t * t * (10 + t * (-15 + 6 * t))


def smoothstep(v, lo, hi):
    return ease((v - lo) / (hi - lo))


def v2_uplift(target, base, controls, grade=.60, toe=36.0):
    """tools/navigation/prepare_relief_envelope.py, main(), uplift and candidate lines (grade/toe as parameters)."""
    distance = distance_transform_edt(~controls, sampling=6)
    cap = grade * (distance - toe * (1 - np.exp(-distance / toe)))
    requested = np.maximum(0, target - base)
    uplift = np.minimum(gaussian_filter(np.minimum(requested, cap), 4), cap)
    candidate = base.copy()
    active = (uplift >= .001) & ~controls
    candidate[active] = np.round(base[active] + uplift[active], 4).astype("float32")
    return candidate


def v3_project(candidate, base):
    """tools/navigation/limit_regional_slopes.py, main(), projection loop."""
    h = candidate.copy()
    xcost = np.maximum(2.88, np.abs(np.diff(base, axis=1)))
    ycost = np.maximum(2.88, np.abs(np.diff(base, axis=0)))
    for _ in range(256):
        nh = h.copy()
        nh[:, 1:] = np.minimum(nh[:, 1:], h[:, :-1] + xcost)
        nh[:, :-1] = np.minimum(nh[:, :-1], h[:, 1:] + xcost)
        nh[1:, :] = np.minimum(nh[1:, :], h[:-1, :] + ycost)
        nh[:-1, :] = np.minimum(nh[:-1, :], h[1:, :] + ycost)
        np.maximum(nh, base, out=nh)
        diff = float(np.max(h - nh))
        h = nh
        if diff < .0001:
            return h
    raise ValueError("projection did not converge")


def main():
    P = PARAMS
    v1 = np.load(os.path.join(R, "tests", "regional_outline_v1", "reference.npz"))
    v3 = np.load(os.path.join(R, "tests", "regional_outline_v3", "reference.npz"))
    v33 = np.load(os.path.join(R, "tests", "regional_outline_smoothing_v33", "reference.npz"))
    base = v1["base"]
    with rasterio.open(os.path.join(R, "source", "baltic_physical_2048_6m.asc")) as ds:
        physical = ds.read(1)
    with rasterio.open(os.path.join(R, "tests", "regional_road_network_v29", "baltic_road_network_v29.asc")) as ds:
        v29 = ds.read(1).astype("float64")
    with rasterio.open(os.path.join(R, "derived", "gis", "worldcover_2021_3857.tif")) as ds:
        cover = ds.read(1)
    n = base.shape[0]
    x, z = np.meshgrid(np.arange(n) * 6., 12282 - np.arange(n) * 6.)
    a = np.exp(-.5 * (((x - 5900) / 1700) ** 2 + ((z - 7950) / 1500) ** 2))
    b = np.exp(-.5 * (((x - 4500) / 1700) ** 2 + ((z - 1100) / 1550) ** 2))
    f_old = 5 + 15 * a + 19 * b
    macro = gaussian_filter(np.maximum(physical, 0).astype("float64"), 9)

    # 1. Reproduce Codex's relief with Codex's inputs.
    check = v3_project(v2_uplift(macro * f_old, base, v1["controls"]), base)
    repro = float(np.max(np.abs(check - v3["candidate"])))
    print("reproduction max |diff| vs tests/regional_outline_v3:", repro, flush=True)
    assert repro < 1e-3, "pipeline does not reproduce Codex's v3 relief"

    # 2. Natural factor field.
    land = ~v1["water"] & (physical > 0)
    wgt = gaussian_filter(land.astype(float), P["large_scale_sigma_px"])
    big = gaussian_filter(np.where(land, physical, 0.0).astype("float64"), P["large_scale_sigma_px"]) / np.maximum(wgt, 1e-6)
    f_mid = P["factor_lowland"] + (P["factor_mid"] - P["factor_lowland"]) * smoothstep(big, *P["lowland_to_mid"])
    high = smoothstep(f_old, *P["high_core_factor"]) * smoothstep(big, *P["high_core_elevation"])
    f_new = high * P["core_factor"] + (1 - high) * f_mid
    feats = json.load(open(os.path.join(R, "evidence", "regional-outline-v1", "reserve_wgs84.geojson"), encoding="utf-8"))["features"]
    reserve = raster([make_valid(tb_geometry(shape(f["geometry"]))) for f in feats])
    rivers = v33["fairway_support"] | v33["bank_support"] | (v33["wet"] & ~v33["ocean"])
    flood = binary_dilation(rivers, iterations=int(P["floodplain_m"] / 6))
    plain_raw = (v1["spb"] & (big < 2.5)) | reserve | v1["wetlands"] | flood
    plain = ease(np.clip(gaussian_filter(plain_raw.astype(float), P["plain_sigma_px"]) * 1.6, 0, 1)) * (1 - high)
    f_new = f_new * (1 - plain) + P["plain_factor"] * plain

    # 3. New controls: only water that exists or is planned (built water, OSM ponds >= 300 m2, waterways >= 600 m),
    #    Narva and map edges. Major roads stop being controls: phase 2 re-grades them on the new relief.
    built = v33["wet"] | v33["ocean"] | v33["islands"] | v33["fairway_support"] | v33["bank_support"]
    ponds = [g for g in (make_valid(tb_geometry(shape(f["geometry"]))) for f in features("water"))
             if g.area >= P["control_pond_min_m2"]]
    lines = [tb_geometry(shape(f["geometry"])) for f in features("rivers")]
    lines = [g.buffer(P["control_waterway_buffer_m"]) for g in lines if g.length >= P["control_waterway_min_m"]]
    planned = raster(ponds) | raster(lines)
    edges = (x < 24) | (x > 12258) | (z < 24) | (z > 12258)
    controls = binary_dilation(built | planned, iterations=3) | v1["narva"] | edges
    relief_new = v3_project(v2_uplift(macro * f_new, base, controls, P["valley_grade"], P["valley_toe_m"]), base).astype("float64")
    d = relief_new - v3["candidate"].astype("float64")

    # 4. Apply the relief difference to V29 outside the envelope of engineered water, Narva and edges.
    water_env = binary_dilation(built, iterations=int(P["envelope_water_m"] / 6))
    fit = json.load(open(os.path.join(R, "evidence", "narva", "evidence", "narva-fit.json"), encoding="utf-8"))
    cx, cz = fit["bridge_centre_tb"]
    narva = (x - (cx - 200000)) ** 2 + (z - cz) ** 2 <= P["narva_radius_m"] ** 2
    envelope = water_env | narva | edges
    w = ease(distance_transform_edt(~envelope, sampling=6.0) / P["ease_m"])
    new = v29 + d * w
    new[envelope] = v29[envelope]
    dry = (v29 >= P["dry_floor_m"]) & ~envelope
    new[dry] = np.maximum(new[dry], P["dry_floor_m"])

    # 5. Slope cap as in tools/navigation/limit_regional_slopes.py, with envelope heights held fixed.
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

    np.savez_compressed(os.path.join(OUT, "relief_v30.npz"), new=new.astype("float32"), v29=v29.astype("float32"),
                        f_old=f_old.astype("float32"), f_new=f_new.astype("float32"), high=high.astype("float32"),
                        plain=plain.astype("float32"), big=big.astype("float32"), d=d.astype("float32"),
                        envelope=envelope, controls_new=controls, reserve=reserve)

    def slope(hm):
        gy, gx = np.gradient(hm, 6.0)
        return np.degrees(np.arctan(np.hypot(gx, gy)))

    s29, snew = slope(v29), slope(new)
    land29 = v29 > 1.0
    band = lambda s, x0, x1: round(float(s[(z > 8100) & (z < 9100) & (x > x0) & (x < x1)].mean()), 2)
    stats = {
        "params": P, "reproduction_max_abs_m": repro,
        "envelope_cells_pct": round(100 * float(envelope.mean()), 2),
        "changed_cells_pct": round(100 * float((np.abs(new - v29) > 0.01).mean()), 2),
        "height_max": [round(float(v29.max()), 2), round(float(new.max()), 2)],
        "height_land_mean": [round(float(v29[land29].mean()), 2), round(float(new[land29].mean()), 2)],
        "slope_land_pct_over_v29_new": {f">{t}deg": [round(100 * float((s29[land29] > t).mean()), 1),
                                                     round(100 * float((snew[land29] > t).mean()), 1)] for t in (5, 10, 15, 20, 25, 30)},
        "slope_land_median_deg": [round(float(np.median(s29[land29])), 2), round(float(np.median(snew[land29])), 2)],
        "x6250_edge_slope_west_east_v29": [band(s29, 5900, 6150), band(s29, 6250, 6500)],
        "x6250_edge_slope_west_east_new": [band(snew, 5900, 6150), band(snew, 6250, 6500)],
        "flat_lt2deg_pct": [round(100 * float((s29[land29] < 2).mean()), 1), round(100 * float((snew[land29] < 2).mean()), 1)],
    }
    with open(os.path.join(OUT, "relief_v30_stats.json"), "wb") as f:
        f.write(json.dumps(stats, indent=1, ensure_ascii=False).encode("utf-8"))
    print(json.dumps(stats, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()

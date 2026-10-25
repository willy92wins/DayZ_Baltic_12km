"""EV97: one global smoothing pass over dry land to round the faceted planes and creases (Guillermo, 2026-10-11).

Method: normalized Gaussian convolution over dry vertices only (water beds never pull banks down), blended in
with a ramp away from frozen geometry (road reserve, platforms, the Narva bridge pilot). Floors keep every dry
vertex out of the water and out of the shore-texture band: H >= min(H_old, nearest water level + 0.30) near
water, and H >= min(H_old, 1.60) everywhere (land floor decided 2026-10-05). Wet vertices are untouched.
Usage: smooth_dry_relief.py <in.npz> <out.npz> <sigma_cells> [--report out.json]
"""
import json, sys
import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, minimum_filter

SHORE_BAND = 0.30
LAND_FLOOR = 1.60
RAMP_CELLS = 4.0


def metrics(H, dry):
    """Crease metrics on interior dry vertices (all 8 neighbours dry): bend angle between consecutive 6 m segments."""
    interior = dry.copy()
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            interior &= np.roll(np.roll(dry, dr, 0), dc, 1)
    interior[:2] = interior[-2:] = False
    interior[:, :2] = interior[:, -2:] = False
    bends = []
    for axis in (0, 1):
        a1 = np.degrees(np.arctan((H - np.roll(H, 1, axis)) / 6.0))
        a2 = np.degrees(np.arctan((np.roll(H, -1, axis) - H) / 6.0))
        bends.append(np.abs(a2 - a1))
    bend = np.maximum(*bends)
    gy, gx = np.gradient(H, 6.0)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    nb = np.full(H.shape, np.inf)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr or dc:
                nb = np.minimum(nb, np.roll(np.roll(H, dr, 0), dc, 1))
    q = lambda a, p: [round(float(v), 3) for v in np.quantile(a[interior], p)]
    return dict(interior_vertices=int(interior.sum()), slope_deg_q50_90_99_999_max=q(slope, [.5, .9, .99, .999, 1]),
                bend_deg_q90_99_999_max=q(bend, [.9, .99, .999, 1]),
                bend_gt_10=int((bend > 10)[interior].sum()), bend_gt_20=int((bend > 20)[interior].sum()),
                bend_gt_30=int((bend > 30)[interior].sum()), strict_dry_minima=int(((H < nb) & interior).sum()))


def main():
    src, dst, sigma = sys.argv[1], sys.argv[2], float(sys.argv[3])
    report_path = sys.argv[5] if len(sys.argv) > 5 and sys.argv[4] == "--report" else None
    z = np.load(src)
    arrays = {k: z[k].copy() for k in z.files}
    H = arrays["heights"].astype(np.float64)
    W = arrays["water"] | (arrays["cls"] > 0)
    dry = ~W
    frozen = arrays["reserve"] | arrays["platform"] | arrays["narva"]
    # nearest water level for every vertex (sea counts at its own level array value or 1.0 when undefined)
    lvl = np.where(np.isfinite(arrays["level"]), arrays["level"], 1.0).astype(np.float64)
    dist_w, idx = distance_transform_edt(~W, return_indices=True)
    near_lvl = lvl[idx[0], idx[1]]
    # smoothing weight: 0 on frozen and wet vertices, ramps to 1 over RAMP_CELLS
    ramp = np.clip(distance_transform_edt(~frozen) / RAMP_CELLS, 0, 1)
    w = np.where(dry, ramp, 0.0)
    num = gaussian_filter(np.where(dry, H, 0.0), sigma, mode="nearest")
    den = gaussian_filter(dry.astype(np.float64), sigma, mode="nearest")
    Hs = np.where(den > 1e-6, num / np.maximum(den, 1e-6), H)
    Hn = H + w * (Hs - H)
    floor_shore = np.minimum(H, near_lvl + SHORE_BAND + 1e-3)
    floor_land = np.minimum(H, LAND_FLOOR)
    Hn = np.where(dry, np.maximum(Hn, np.maximum(floor_shore, floor_land)), H)
    Hn = Hn.astype(np.float32)
    assert np.array_equal(Hn[~dry], arrays["heights"][~dry])
    assert np.array_equal(Hn[frozen], arrays["heights"][frozen])
    before, after = metrics(H, dry), metrics(Hn.astype(np.float64), dry)
    flooded = int((dry & (Hn < near_lvl + 0.05) & ~(H < near_lvl + 0.05)).sum())
    new_shore = int((dry & (dist_w * 6.0 <= 15.0) & (Hn < near_lvl + SHORE_BAND) & ~(H < near_lvl + SHORE_BAND)).sum())
    d = np.abs(Hn.astype(np.float64) - H)
    rep = dict(schema="ev97-dry-relief-smoothing.v1", sigma_cells=sigma, sigma_m=sigma * 6, ramp_cells=RAMP_CELLS,
               changed_vertices=int((d > 0).sum()), change_m_q50_99_max=[round(float(v), 3) for v in np.quantile(d[d > 0], [.5, .99, 1])],
               newly_flooded=flooded, new_shore_band=new_shore, before=before, after=after,
               max_height_before=round(float(H[dry].max()), 2), max_height_after=round(float(Hn[dry].max()), 2))
    arrays["heights"] = Hn
    np.savez(dst, **arrays)
    print(json.dumps(rep, indent=1))
    if report_path:
        open(report_path, "w").write(json.dumps(rep, indent=1))
    assert flooded == 0 and new_shore == 0


if __name__ == "__main__":
    main()

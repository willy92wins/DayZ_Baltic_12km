"""Navigable channels V3: natural course along the validated boat fairways, width 30-60 m from the real relative width.

Axis   evidence/regional-foundation-v1/fairways-main-game.json (boat routes with a 24 m clear channel).
Width  real compressed width from OSM river polygons, measured on transects every 6 m; mapped per river from its
       own 10th-90th percentile onto 30-60 m, widened in bends, smoothed, then irregular banks (+-1.5 m).
Output <out>/navigable.geojson and <out>/navigable_samples.npz.
"""
import json
import os
import sys

import numpy as np
from scipy.ndimage import gaussian_filter1d, median_filter
from shapely import STRtree
from shapely.geometry import LineString, Point, shape
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from water_common import EV, merge_lines, normals, read_shp, resample, ribbon, save_geojson, smooth_noise  # noqa: E402

OUT = sys.argv[1]
P = {"step_m": 6.0, "w_min": 30.0, "w_max": 60.0, "clear_channel_m": 24.0, "transect_half_m": 90.0,
     "bend_gain_m": 10.0, "bend_radius_ref_m": 120.0, "smooth_m": 120.0, "bank_noise_m": 1.5, "bank_noise_sigma_m": 40.0}
os.makedirs(OUT, exist_ok=True)


def real_width(pts, nrm, polys, tree):
    """Length of the OSM river cross-section through each sample (nearest piece if the sample is outside)."""
    h = P["transect_half_m"]
    out = np.zeros(len(pts))
    for i, (p, n) in enumerate(zip(pts, nrm)):
        tr = LineString([p - n * h, p + n * h])
        hits = tree.query(tr)
        if len(hits) == 0:
            continue
        inter = unary_union([polys[j].intersection(tr) for j in hits])
        segs = list(inter.geoms) if hasattr(inter, "geoms") else [inter]
        segs = [s for s in segs if s.length > 0]
        if not segs:
            continue
        pt = Point(p)
        out[i] = min(segs, key=lambda s: s.distance(pt)).length
    return out


def main():
    rng = np.random.default_rng(20261002)
    fair = json.load(open(os.path.join(EV, "fairways-main-game.json"), encoding="utf-8"))["features"]
    rivers = {}
    for f in fair:
        rivers.setdefault(f["properties"]["river"], []).append(shape(f["geometry"]))
    polys = [g for g, rec in read_shp("water", {"river", "canal"})]
    tree = STRtree(polys)
    feats, samples, report = [], {}, {}
    for river, lines in rivers.items():
        parts = []
        for line in merge_lines(lines):
            s, pts = resample(line, P["step_m"])
            nrm, tan = normals(pts, smooth=7)
            w_real = median_filter(real_width(pts, nrm, polys, tree), size=min(11, len(pts) | 1), mode="nearest")
            parts.append((line, s, pts, nrm, tan, w_real))
        allw = np.concatenate([p[5] for p in parts])
        allw = allw[allw > 0]
        lo, hi = np.percentile(allw, [10, 90]) if len(allw) > 10 else (0.0, 1.0)
        for k, (line, s, pts, nrm, tan, w_real) in enumerate(parts):
            valid = w_real > 0
            rel = np.clip((w_real - lo) / max(hi - lo, 1e-6), 0, 1)
            rel[~valid] = np.median(np.clip((allw - lo) / max(hi - lo, 1e-6), 0, 1)) if len(allw) else 0.5
            if line.length < 60:
                rel[:] = np.median(rel)
            ang = np.unwrap(np.arctan2(tan[:, 1], tan[:, 0]))
            curv = np.abs(np.gradient(gaussian_filter1d(ang, 5), s)) if len(s) > 2 else np.zeros(len(s))  # rad per metre
            bend = np.clip(curv * P["bend_radius_ref_m"], 0, 1)
            w = P["w_min"] + (P["w_max"] - P["w_min"]) * rel + P["bend_gain_m"] * bend
            w = np.clip(gaussian_filter1d(w, P["smooth_m"] / P["step_m"]), P["w_min"], P["w_max"])
            sig = P["bank_noise_sigma_m"] / P["step_m"]
            left = w / 2 + P["bank_noise_m"] * smooth_noise(len(w), sig, rng)
            right = w / 2 + P["bank_noise_m"] * smooth_noise(len(w), sig, rng)
            left = np.maximum(left, P["clear_channel_m"] / 2 + 2)
            right = np.maximum(right, P["clear_channel_m"] / 2 + 2)
            poly = ribbon(pts, left, right)
            key = f"{river}_{k}"
            feats.append((poly, {"id": key, "class": "navigable", "river": river, "length_m": round(line.length, 1),
                                 "width_min_m": round(float((left + right).min()), 1), "width_median_m": round(float(np.median(left + right)), 1),
                                 "width_max_m": round(float((left + right).max()), 1), "real_width_median_m": round(float(np.median(w_real[valid])) if valid.any() else 0, 1)}))
            samples[key] = np.column_stack([s, pts, left, right, w_real])
            report[key] = feats[-1][1]
    save_geojson(os.path.join(OUT, "navigable.geojson"), feats)
    np.savez_compressed(os.path.join(OUT, "navigable_samples.npz"), **samples)
    with open(os.path.join(OUT, "navigable_report.json"), "wb") as f:
        f.write(json.dumps({"params": P, "channels": report}, indent=1, ensure_ascii=False).encode("utf-8"))
    for k, v in report.items():
        print(k, v["length_m"], "m  width", v["width_min_m"], v["width_median_m"], v["width_max_m"], " real median", v["real_width_median_m"])


if __name__ == "__main__":
    main()

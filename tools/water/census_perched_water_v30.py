#!/usr/bin/env python3.11
"""Census of perched (diked) standing water bodies on a DayZ terrain grid.

Finds every lake/pond whose water level sits above the natural ground ring
around it, reports how perched it is, how high its dike is, and where it is.

Written by GLM-5.3-Flash (GX10 lane F, 04-10); receiver changes: the class
count uses minlength=8 (a body of lake vertices only raised IndexError), the
map colours are an (n, 3) array (np.full with the vector shape failed) and the
self-test now draws the map too, and OUTDIR is checked before the computation.

CLI:
    python census_perched_water_v30.py --terrain T.npz --out OUTDIR \
        [--ring-in 12] [--ring-out 36] [--perched-min 0.30] [--dike-min 0.50]
    python census_perched_water_v30.py --selftest --out OUTDIR
"""

import argparse
import csv
import hashlib
import json
import math
import os
import sys
import time

import numpy as np
from scipy import ndimage

import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg

STRUCT8 = np.ones((3, 3), dtype=int)
STANDING_CLASSES = (2, 7)
MIN_VERTICES = 4
GRID_H = GRID_W = 2048
VERTEX_M = 6.0
Z0 = 12282.0

HIST_EDGES = np.array(
    [-np.inf, -1.0, -0.5, 0.0, 0.3, 0.6, 1.0, 1.5, 2.0, np.inf], dtype=np.float64
)


# ----------------------------------------------------------------------------
# Core computation (shared by the real run and the self-test)
# ----------------------------------------------------------------------------

def find_bodies(cls, heights, level, ring_in, ring_out, perched_min, dike_min):
    """Return (bodies, perched_vertex).

    bodies: list of dicts with raw (unrounded) float values.
    perched_vertex: float32 (H, W), perched_m at each standing vertex else -inf.
    """
    cls = np.asarray(cls)
    heights = np.asarray(heights)
    level = np.asarray(level)
    standing = (cls == 2) | (cls == 7)
    rounded = np.round(level.astype(np.float64) * 100.0) / 100.0

    perched_vertex = np.full(cls.shape, -np.inf, dtype=np.float32)
    bodies = []
    body_id = 0

    if not standing.any():
        return bodies, perched_vertex

    rows = np.flatnonzero(standing.any(axis=1))
    cols = np.flatnonzero(standing.any(axis=0))
    r0g, r1g = rows[0], rows[-1] + 1
    c0g, c1g = cols[0], cols[-1] + 1

    standing_s = standing[r0g:r1g, c0g:c1g]
    rounded_s = rounded[r0g:r1g, c0g:c1g]

    pad_v = int(math.ceil(ring_out / VERTEX_M)) + 2

    for lvl in np.unique(rounded_s[standing_s]):
        mask_s = standing_s & (rounded_s == lvl)
        labels_s, n = ndimage.label(mask_s, structure=STRUCT8)
        if n == 0:
            continue
        counts = np.bincount(labels_s.ravel())
        for i in range(1, n + 1):
            if counts[i] < MIN_VERTICES:
                continue
            rr_s, cc_s = np.nonzero(labels_s == i)
            rr = rr_s + r0g
            cc = cc_s + c0g
            body_id += 1
            bodies.append(
                _body_stats(
                    body_id, cls, heights, level, rr, cc,
                    ring_in, ring_out, perched_min, dike_min, pad_v,
                    perched_vertex,
                )
            )
    return bodies, perched_vertex


def _body_stats(body_id, cls, heights, level, rr, cc, ring_in, ring_out,
                perched_min, dike_min, pad_v, perched_vertex):
    lv = level[rr, cc].astype(np.float64)
    L = float(np.median(lv))
    counts = np.bincount(cls[rr, cc], minlength=8)
    klass = "lake" if counts[2] >= counts[7] else "pond"

    r0 = max(0, int(rr.min()) - pad_v)
    r1 = min(GRID_H, int(rr.max()) + 1 + pad_v)
    c0 = max(0, int(cc.min()) - pad_v)
    c1 = min(GRID_W, int(cc.max()) + 1 + pad_v)

    B_win = np.zeros((r1 - r0, c1 - c0), dtype=bool)
    B_win[rr - r0, cc - c0] = True
    cls_w = cls[r0:r1, c0:c1]
    hts_w = heights[r0:r1, c0:c1].astype(np.float64)
    land_w = cls_w == 0

    # Bank: land vertices 8-adjacent to the body.
    bank_w = ndimage.binary_dilation(B_win, structure=STRUCT8) & ~B_win & land_w

    # Natural ground ring via EDT on the window only.
    dist = ndimage.distance_transform_edt(~B_win, sampling=VERTEX_M)
    ring_w = land_w & (dist > ring_in) & (dist <= ring_out)

    body_h = heights[rr, cc].astype(np.float64)
    bank_h = hts_w[bank_w]
    ring_h = hts_w[ring_w]

    bed_median = float(np.median(body_h))
    bank_median = float(np.median(bank_h)) if bank_h.size else None
    bank_max = float(np.max(bank_h)) if bank_h.size else None
    ring_median = float(np.median(ring_h)) if ring_h.size else None
    ring_p25 = float(np.percentile(ring_h, 25)) if ring_h.size else None
    ring_vertices = int(ring_h.size)

    perched_m = L - ring_median if ring_median is not None else float("nan")
    dike_m = (
        bank_median - ring_median
        if bank_median is not None and ring_median is not None
        else float("nan")
    )

    perched_vertex[rr, cc] = np.float32(perched_m)

    return {
        "id": body_id,
        "class": klass,
        "vertices": int(rr.size),
        "area_m2": float(rr.size) * VERTEX_M * VERTEX_M,
        "level_m": L,
        "cx": float(VERTEX_M * cc.mean()),
        "cz": float(Z0 - VERTEX_M * rr.mean()),
        "bed_median_m": bed_median,
        "bank_median_m": bank_median,
        "bank_max_m": bank_max,
        "ring_median_m": ring_median,
        "ring_p25_m": ring_p25,
        "ring_vertices": ring_vertices,
        "perched_m": perched_m,
        "dike_m": dike_m,
        "perched": bool(perched_m > perched_min),
        "diked": bool(dike_m > dike_min),
    }


# ----------------------------------------------------------------------------
# Output helpers
# ----------------------------------------------------------------------------

def _clean(v):
    if v is None:
        return None
    f = float(v)
    if math.isnan(f) or math.isinf(f):
        return None
    return round(f, 3)


def body_out(b):
    return {
        "id": b["id"],
        "class": b["class"],
        "vertices": b["vertices"],
        "area_m2": round(b["area_m2"], 3),
        "level_m": _clean(b["level_m"]),
        "centroid_xz": [_clean(b["cx"]), _clean(b["cz"])],
        "bed_median_m": _clean(b["bed_median_m"]),
        "bank_median_m": _clean(b["bank_median_m"]),
        "bank_max_m": _clean(b["bank_max_m"]),
        "ring_median_m": _clean(b["ring_median_m"]),
        "ring_p25_m": _clean(b["ring_p25_m"]),
        "ring_vertices": b["ring_vertices"],
        "perched_m": _clean(b["perched_m"]),
        "dike_m": _clean(b["dike_m"]),
        "perched": b["perched"],
        "diked": b["diked"],
    }


def _class_totals(bodies, flag):
    sel = [b for b in bodies if b[flag]]
    return {
        "count": len(sel),
        "area_m2": round(sum(b["area_m2"] for b in sel), 3),
        "lake": {
            "count": sum(1 for b in sel if b["class"] == "lake"),
            "area_m2": round(
                sum(b["area_m2"] for b in sel if b["class"] == "lake"), 3
            ),
        },
        "pond": {
            "count": sum(1 for b in sel if b["class"] == "pond"),
            "area_m2": round(
                sum(b["area_m2"] for b in sel if b["class"] == "pond"), 3
            ),
        },
    }


def make_census(bodies, params, terrain_name, sha, seconds):
    vals = np.array(
        [b["perched_m"] for b in bodies
         if not (isinstance(b["perched_m"], float) and math.isnan(b["perched_m"]))],
        dtype=np.float64,
    )
    if vals.size:
        counts, _ = np.histogram(vals, bins=HIST_EDGES)
        counts = [int(c) for c in counts]
    else:
        counts = [0] * (len(HIST_EDGES) - 1)

    edges_out = []
    for e in HIST_EDGES:
        if np.isinf(e):
            edges_out.append("-inf" if e < 0 else "inf")
        else:
            edges_out.append(float(e))

    perched = [b for b in bodies if b["perched"]]
    perched.sort(key=lambda b: b["perched_m"] * b["area_m2"], reverse=True)

    return {
        "terrain": terrain_name,
        "terrain_sha256": sha,
        "params": {
            "ring_in_m": params["ring_in_m"],
            "ring_out_m": params["ring_out_m"],
            "perched_min_m": params["perched_min_m"],
            "dike_min_m": params["dike_min_m"],
            "min_vertices": MIN_VERTICES,
        },
        "totals": {
            "bodies": len(bodies),
            "perched": _class_totals(bodies, "perched"),
            "diked": _class_totals(bodies, "diked"),
        },
        "perched_m_histogram": {"edges": edges_out, "counts": counts},
        "top": [body_out(b) for b in perched[:40]],
        "seconds": round(seconds, 3),
    }


CSV_FIELDS = [
    "id", "class", "vertices", "area_m2", "level_m", "x", "z",
    "bed_median_m", "bank_median_m", "bank_max_m", "ring_median_m",
    "ring_p25_m", "ring_vertices", "perched_m", "dike_m", "perched", "diked",
]


def write_csv(path, bodies):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(CSV_FIELDS)
        for b in bodies:
            o = body_out(b)
            w.writerow([
                o["id"], o["class"], o["vertices"], o["area_m2"], o["level_m"],
                o["centroid_xz"][0], o["centroid_xz"][1],
                o["bed_median_m"], o["bank_median_m"], o["bank_max_m"],
                o["ring_median_m"], o["ring_p25_m"], o["ring_vertices"],
                o["perched_m"], o["dike_m"], o["perched"], o["diked"],
            ])


def write_map(path, cls, heights, perched_vertex):
    h, w = heights.shape
    grey = (np.clip(heights.astype(np.float64), 0.0, 12.0) / 12.0 * 255.0)
    grey = grey.astype(np.uint8)

    standing = perched_vertex > -np.inf
    water_ns = (cls >= 1) & (cls <= 6) & ~standing

    def block_max(a):
        return a.reshape(h // 2, 2, w // 2, 2).max(axis=(1, 3))

    gm = block_max(grey)
    wm = block_max(water_ns.astype(np.uint8))
    pv = block_max(perched_vertex)

    rgb = np.repeat(gm[:, :, None], 3, axis=2)
    rgb[wm > 0] = (30, 30, 140)  # non-standing water: dark blue

    m = pv > -np.inf
    v = pv[m]
    col = np.empty((v.size, 3), dtype=np.uint8)
    col[:] = (120, 180, 255)                                 # <= 0 / NaN
    col[(v > 0.0) & (v <= 0.3)] = (0, 220, 220)              # cyan
    col[(v > 0.3) & (v <= 1.0)] = (255, 220, 0)              # yellow
    col[v > 1.0] = (255, 40, 40)                             # red
    rgb[m] = col

    mpimg.imsave(path, rgb)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_terrain(path):
    data = np.load(path)
    return data["heights"], data["cls"], data["level"]


def real_run(args):
    t0 = time.time()
    heights, cls, level = load_terrain(args.terrain)
    bodies, perched_vertex = find_bodies(
        cls, heights, level,
        args.ring_in, args.ring_out, args.perched_min, args.dike_min,
    )
    seconds = time.time() - t0
    params = {
        "ring_in_m": args.ring_in,
        "ring_out_m": args.ring_out,
        "perched_min_m": args.perched_min,
        "dike_min_m": args.dike_min,
    }
    census = make_census(bodies, params, args.terrain, sha256_file(args.terrain),
                         seconds)
    os.makedirs(args.out)  # fails if OUTDIR exists
    with open(os.path.join(args.out, "census.json"), "w", encoding="utf-8") as f:
        json.dump(census, f, indent=1)
    write_csv(os.path.join(args.out, "bodies.csv"), bodies)
    write_map(os.path.join(args.out, "map.png"), cls, heights, perched_vertex)
    print(
        "bodies=%d perched=%d diked=%d seconds=%.1f"
        % (
            census["totals"]["bodies"],
            census["totals"]["perched"]["count"],
            census["totals"]["diked"]["count"],
            seconds,
        )
    )


# ----------------------------------------------------------------------------
# Self-test
# ----------------------------------------------------------------------------

def selftest(args):
    t0 = time.time()
    heights = np.full((GRID_H, GRID_W), 3.0, dtype=np.float32)
    cls = np.zeros((GRID_H, GRID_W), dtype=np.uint8)
    level = np.full((GRID_H, GRID_W), np.nan, dtype=np.float32)

    # Lake A: 10x10 at level 4.2, bed 3.5, bank ring at 4.55.
    cls[1000:1010, 1000:1010] = 2
    level[1000:1010, 1000:1010] = 4.2
    heights[1000:1010, 1000:1010] = 3.5
    heights[999:1011, 999:1011] = 4.55  # overwrite interior again below
    heights[1000:1010, 1000:1010] = 3.5

    # Pond B: 5x5 at level 2.8, bed 2.0, natural ground 3.0 around it.
    cls[1100:1105, 1100:1105] = 7
    level[1100:1105, 1100:1105] = 2.8
    heights[1100:1105, 1100:1105] = 2.0

    bodies, perched_vertex = find_bodies(cls, heights, level, 12.0, 36.0, 0.30, 0.50)

    assert len(bodies) == 2, "expected exactly 2 bodies, got %d" % len(bodies)
    a = next(b for b in bodies if b["vertices"] == 100)
    b = next(b for b in bodies if b["vertices"] == 25)

    assert a["class"] == "lake"
    assert abs(a["area_m2"] - 3600.0) < 1e-6
    assert abs(a["perched_m"] - 1.2) < 1e-6, a["perched_m"]
    assert abs(a["dike_m"] - 1.55) < 1e-6, a["dike_m"]
    assert a["perched"] and a["diked"]

    assert b["class"] == "pond"
    assert abs(b["perched_m"] - (-0.2)) < 1e-6, b["perched_m"]
    assert not b["perched"] and not b["diked"]

    seconds = time.time() - t0
    params = {
        "ring_in_m": 12.0, "ring_out_m": 36.0,
        "perched_min_m": 0.30, "dike_min_m": 0.50,
    }
    sha = hashlib.sha256(heights.tobytes()).hexdigest()
    census = make_census(bodies, params, "synthetic", sha, seconds)
    os.makedirs(args.out)  # fails if OUTDIR exists
    with open(os.path.join(args.out, "census.json"), "w", encoding="utf-8") as f:
        json.dump(census, f, indent=1)
    write_map(os.path.join(args.out, "map.png"), cls, heights, perched_vertex)

    print("SELFTEST PASS")


def main():
    p = argparse.ArgumentParser(
        description="Census of perched standing water bodies."
    )
    p.add_argument("--terrain", help="path to terrain .npz")
    p.add_argument("--out", required=True, help="output directory (must not exist)")
    p.add_argument("--ring-in", type=float, default=12.0)
    p.add_argument("--ring-out", type=float, default=36.0)
    p.add_argument("--perched-min", type=float, default=0.30)
    p.add_argument("--dike-min", type=float, default=0.50)
    p.add_argument("--selftest", action="store_true")
    args = p.parse_args()
    if os.path.exists(args.out):
        p.error("output directory already exists: %s" % args.out)

    if args.selftest:
        selftest(args)
    else:
        if not args.terrain:
            p.error("--terrain is required unless --selftest is given")
        real_run(args)


if __name__ == "__main__":
    main()

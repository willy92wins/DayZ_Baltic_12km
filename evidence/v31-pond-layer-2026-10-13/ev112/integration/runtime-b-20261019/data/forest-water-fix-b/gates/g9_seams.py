"""G9 seams: the computation tiles must not show (EV112: "sectorise only for computation, never visibly").

Usage: python -I g9_seams.py <records.json> <tile_m> <out.json> [--region x0,z0,x1,z1]
         [--compare other.json --compare-tile T2]
A) Density at the tile borders. Border lines: x = k T and z = 12288 - k T (the placer's tiles start at the map's
   north-west corner), map edges excluded. For trees, bushes, dead wood and reeds, the WRP positions in the bands
   0-2, 2-4, 4-6 and 6-10 m from a border line are counted per unit of band area and divided by the same density in
   the 10-40 m band around the same lines (the same land): r = density(band) / density(10-40 m). Band area in a
   T x T tile with the distance to its nearest side: (T - 2a)^2 - (T - 2b)^2 for [a, b). A seam shows as a
   narrow step or dip next to the line. Rule: |r - 1| <= max(0.03, 4 sqrt(1/n_band + 1/n_ref x w_band/w_ref)) for
   trees and bushes in every band (dead wood and reeds reported). The same ratios around control lines shifted by
   T / 2 are reported for scale.
B) Hard spacing rules of the placer, map-wide (any pair closer than the rule is a defect; at a seam it means the two
   tiles did not see each other): tree-tree 0.7 m (broadleaf-broadleaf 0.45 m), bush-bush 0.28 m, bush-tree 0.52 m,
   dead-dead 0.77 m, reed-reed 1.75 m, reed-tree 2.21 m (WRP positions, 1e-6 m tolerance). Rule: 0 pairs.
C) Partition invariance (with --compare): another run of the same seed, region and calibration with another tile size.
   Instances are matched by model and matrix (exact), 20 m inside the region (a region run keeps an instance by its
   sample point, the comparison selects by WRP position; a fallen trunk's bounding centre lies metres away). Rule: >= 99 % of the instances identical, and every
   difference within 40 m (halo + chain) of a border of either tiling.
Prints PASS or FAIL last."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gcfg  # noqa: E402
import glib  # noqa: E402

MAP = gcfg.MAP
BANDS = [(0, 2), (2, 4), (4, 6), (6, 10)]
GROUPS = {"trees": (0, 1), "bush": (2,), "dead": (3,), "reed": (4,)}


def line_dist(x, z, T, off, region):
    """Distance to the nearest border line of a grid of step T offset by off (vertical x = kT + off, horizontal
    z = MAP - (kT + off)), lines on the map edges excluded; lines outside region ignored."""
    x0, z0, x1, z1 = region
    xs = np.arange(off, MAP, T, dtype=float)
    xs = xs[(xs > max(x0, 0)) & (xs < min(x1, MAP))]
    zs = MAP - np.arange(off, MAP, T, dtype=float)
    zs = zs[(zs > max(z0, 0)) & (zs < min(z1, MAP))]
    d = np.full(len(x), np.inf)
    if xs.size:
        i = np.clip(np.searchsorted(xs, x), 1, xs.size) if xs.size > 1 else np.zeros(len(x), int)
        d = np.minimum(d, np.minimum(np.abs(x - xs[np.clip(i - 1, 0, xs.size - 1)]), np.abs(x - xs[np.clip(i, 0, xs.size - 1)])))
    if zs.size:
        zs = np.sort(zs)
        i = np.clip(np.searchsorted(zs, z), 1, zs.size) if zs.size > 1 else np.zeros(len(z), int)
        d = np.minimum(d, np.minimum(np.abs(z - zs[np.clip(i - 1, 0, zs.size - 1)]), np.abs(z - zs[np.clip(i, 0, zs.size - 1)])))
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records")
    ap.add_argument("tile", type=float)
    ap.add_argument("out")
    ap.add_argument("--region", default=f"0,0,{MAP},{MAP}")
    ap.add_argument("--compare")
    ap.add_argument("--compare-tile", type=float)
    a = ap.parse_args()
    region = [float(v) for v in a.region.split(",")]
    bb = tuple(region) if a.region != f"0,0,{MAP},{MAP}" else None
    MR = glib.MapRecords(a.records, bb)
    T = a.tile
    x, z, fam = MR.x, MR.z, MR.fam
    ins = (x >= region[0] + 15) & (x < region[2] - 15) & (z >= region[1] + 15) & (z < region[3] - 15)
    dr = line_dist(x, z, T, 0.0, region)
    dp = line_dist(x, z, T, T / 2, region)
    res = {"tile_m": T, "region": region, "A": {}, "B": {}}
    ok = True
    for g, fs in GROUPS.items():
        sel = np.isin(fam, fs) & ins
        rows = []
        for lo, hi in BANDS:
            row = {"band_m": [lo, hi]}
            for lab, dd in (("border", dr), ("control", dp)):
                nb = int(((dd >= lo) & (dd < hi) & sel).sum())
                nref = int(((dd >= 10) & (dd < 40) & sel).sum())
                ab, aref = (T - 2 * lo) ** 2 - (T - 2 * hi) ** 2, (T - 20) ** 2 - (T - 80) ** 2
                r = (nb / ab) / (nref / aref) if nref else None
                tol = max(0.03, 4 * np.sqrt(1 / max(nb, 1) + 1 / max(nref, 1)))
                row[lab] = {"n_band": nb, "n_ref_10_40": nref, "ratio": None if r is None else round(r, 4), "tolerance": round(float(tol), 4)}
            rb = row["border"]
            good = rb["ratio"] is not None and abs(rb["ratio"] - 1) <= rb["tolerance"]
            row["status"] = "PASS" if good else ("EMPTY" if rb["n_band"] + rb["n_ref_10_40"] == 0 else "FAIL")
            if g in ("trees", "bush"):
                ok &= bool(good) or row["status"] == "EMPTY"
            rows.append(row)
        res["A"][g] = rows
    # B: hard spacing
    P = np.c_[x, z]
    tree = np.isin(fam, (0, 1))
    rules = []
    kt = cKDTree(P[tree])
    pairs = kt.query_pairs(0.7, output_type="ndarray")
    ti = np.flatnonzero(tree)
    if len(pairs):
        f1, f2 = fam[ti[pairs[:, 0]]], fam[ti[pairs[:, 1]]]
        dd = np.hypot(*(P[ti[pairs[:, 0]]] - P[ti[pairs[:, 1]]]).T)
        bad = np.where((f1 == 1) & (f2 == 1), dd < 0.45 - 1e-6, dd < 0.7 - 1e-6)
        bp = pairs[bad]
    else:
        bp = np.zeros((0, 2), int)
    rules.append(("tree-tree 0.7 (broadleaf pairs 0.45)", ti[bp[:, 0]] if len(bp) else np.zeros(0, int)))
    for name, fa, fb, r in (("bush-bush", 2, 2, 0.28), ("dead-dead", 3, 3, 0.77), ("reed-reed", 4, 4, 1.75)):
        s = np.flatnonzero(fam == fa)
        pr = cKDTree(P[s]).query_pairs(r - 1e-6, output_type="ndarray") if s.size > 1 else np.zeros((0, 2), int)
        rules.append((f"{name} {r}", s[pr[:, 0]] if len(pr) else np.zeros(0, int)))
    for name, fa, r in (("bush-tree", 2, 0.52), ("reed-tree", 4, 2.21)):
        s = np.flatnonzero(fam == fa)
        d_ = kt.query(P[s], distance_upper_bound=r)[0] if s.size and tree.any() else np.full(s.size, np.inf)
        rules.append((f"{name} {r}", s[d_ < r - 1e-6]))
    for name, idx in rules:
        n_ = int(len(idx))
        ok &= n_ == 0
        near = int((dr[idx] < 10).sum()) if n_ else 0
        res["B"][name] = {"violations": n_, "within_10m_of_a_border": near}
    if a.compare:
        ib = (region[0] + 20, region[1] + 20, region[2] - 20, region[3] - 20)   # the region run keeps instances by sample
        MR = glib.MapRecords(a.records, ib)                                     # point; WRP positions differ by the bounding
        MO = glib.MapRecords(a.compare, ib)                                     # centre offset: compare 20 m inside it
        key = lambda M, k: (M.names[k], tuple(np.round(M.m[k], 9)))  # noqa: E731
        sa = {key(MR, k) for k in range(MR.n)}
        sb = {key(MO, k) for k in range(MO.n)}
        only_a = sa - sb
        only_b = sb - sa
        same = len(sa & sb)
        share = same / max(len(sa | sb), 1)
        diffs = np.array([[v[1][9], v[1][11]] for v in list(only_a) + list(only_b)], float).reshape(-1, 2)
        if len(diffs):
            d1 = line_dist(diffs[:, 0], diffs[:, 1], T, 0.0, region)
            d2 = line_dist(diffs[:, 0], diffs[:, 1], a.compare_tile, 0.0, region)
            far = int((np.minimum(d1, d2) > 40).sum())
            dmax = float(np.minimum(d1, d2).max())
        else:
            far, dmax = 0, 0.0
        good = share >= 0.99 and far == 0
        ok &= good
        res["C"] = {"instances_a": MR.n, "instances_b": MO.n, "identical": same, "identical_share": round(share, 6),
                    "only_a": len(only_a), "only_b": len(only_b), "differences_beyond_40m_of_a_border": far,
                    "largest_difference_distance_to_a_border_m": round(dmax, 2), "status": "PASS" if good else "FAIL"}
    Path(a.out).write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(res, indent=1))
    print(f"G9 {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

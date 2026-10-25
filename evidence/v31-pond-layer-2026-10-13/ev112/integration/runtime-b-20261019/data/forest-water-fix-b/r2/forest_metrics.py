"""Shared vegetation measurements, used unchanged on Livonia windows (reference bands) and on Baltic sectors (gates).

Canopy mask (as forest-livonia/analyze.py:13-27): trees (conifer + broadleaf) counted on a 5 m raster, density in a
20 m disc per ha, mask = density >= 60/ha, 4-connected components >= 0.5 ha kept, holes < 100 m2 filled.
Contexts (analyze.py:76-81): interior sd >= 25 m, edge -10 <= sd < 25 m, open sd < -10 m, riparian = land within 25 m
of water (overrides); water cells are no context.
Rasters are indexed [row = (z - z0) / 5, col = (x - x0) / 5] (row 0 = south edge of the raster).
v2 (EV111 review 1): texture-relative edge bins (TEX_BINS) on the signed distance to the forest-floor surface, an edge
reference that does not depend on the generated trees: the surface is sampled every 12.5 m (Livonia: enoch_surf.npy
ids 6/7, Baltic: shipped mask slot 1), the nearest sample fills each 5 m cell, sd = EDT x 5 m (inside > 0). Species
TVD over the union of observed and reference models (mass outside the reference counts in full). The edge bins
(canopy and texture) leave out the riparian context (land within 25 m of water), which G2 judges on its own.
"""
import numpy as np
from scipy import ndimage

FAM = ["conifer", "broadleaf", "bush", "dead", "reed", "herb"]
CTX = ["interior", "edge", "riparian", "open"]
CS = 5.0
A = CS * CS / 1e4
EDGE_BINS = [(-20.0, -5.0), (5.0, 15.0), (15.0, 25.0), (25.0, 1e9)]
EDGE_NAMES = ["out_-20_-5", "in_5_15", "in_15_25", "in_25_up"]
TEX_BINS = [(-40.0, -25.0), (-25.0, -10.0), (-10.0, 0.0), (0.0, 15.0), (15.0, 25.0), (25.0, 1e9)]
TEX_NAMES = ["out_-40_-25", "out_-25_-10", "out_-10_0", "in_0_15", "in_15_25", "in_25_up"]
TEX_SAMPLE = 12.5


def surface_sd(forest):
    """Signed distance (m) to the forest surface on a 5 m raster: EDT x 5, positive inside."""
    return np.where(forest, ndimage.distance_transform_edt(forest), -ndimage.distance_transform_edt(~forest)) * CS


def canopy(tx, tz, x0, z0, n_r, n_c):
    r = np.floor((tz - z0) / CS).astype(int)
    c = np.floor((tx - x0) / CS).astype(int)
    ok = (r >= 0) & (r < n_r) & (c >= 0) & (c < n_c)
    cnt = np.bincount(r[ok] * n_c + c[ok], minlength=n_r * n_c).reshape(n_r, n_c).astype(float)
    k = int(20.0 / CS)
    yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
    disc = ((xx * CS) ** 2 + (yy * CS) ** 2 <= 400.0).astype(float)
    D = ndimage.convolve(cnt, disc, mode="constant") / (disc.sum() * CS * CS / 1e4)
    fm = D >= 60
    lab, n = ndimage.label(fm)
    if n:
        sizes = ndimage.sum(np.ones_like(D), lab, index=np.arange(1, n + 1)) * CS * CS
        keep = np.zeros(n + 1, bool)
        keep[1:] = sizes >= 5000
        fm = keep[lab]
    holes = ndimage.binary_fill_holes(fm) & ~fm
    hl, hn = ndimage.label(holes)
    if hn:
        hs = ndimage.sum(np.ones_like(D), hl, index=np.arange(1, hn + 1)) * CS * CS
        small = np.zeros(hn + 1, bool)
        small[1:] = hs < 100
        fm = fm | small[hl]
    return fm, D


def contexts(fm, water):
    land = ~water
    sd = np.where(fm, ndimage.distance_transform_edt(fm), -ndimage.distance_transform_edt(~fm)) * CS
    dw = ndimage.distance_transform_edt(~water) * CS if water.any() else np.full(water.shape, 1e9)
    ctx = np.full(fm.shape, -1, np.int8)
    ctx[land & (sd >= 25)] = 0
    ctx[land & (sd < 25) & (sd >= -10)] = 1
    ctx[land & (sd < -10)] = 3
    ctx[land & (dw <= 25)] = 2
    return ctx, sd, dw


def measure(p, cells, model_info=None):
    """p: dict of point arrays (fam, ctx, sd, nn, model, solitary, size) restricted to the analysed area.
    cells: dict of cell arrays (ctx, sd, land, forest_surface optional, canopy) restricted to the analysed area."""
    out = {"area_ha": {}, "density": {}, "share": {}, "nn": {}, "edge": {}, "species": {}, "trees": {}}
    fam, ctx = p["fam"], p["ctx"]
    tree = (fam == 0) | (fam == 1)
    for k, cn in enumerate(CTX):
        a = float((cells["ctx"] == k).sum() * A)
        out["area_ha"][cn] = a
        s = ctx == k
        n_all = int(s.sum())
        out["density"][cn] = {FAM[i]: (float(((fam == i) & s).sum()) / a if a > 0 else None) for i in range(6)}
        out["density"][cn]["trees"] = float((tree & s).sum()) / a if a > 0 else None
        out["share"][cn] = {FAM[i]: (float(((fam == i) & s).sum()) / n_all if n_all else None) for i in range(6)}
        nt = int((tree & s).sum())
        out["trees"][cn] = {"n": nt,
                            "broadleaf_share": float(((fam == 1) & s).sum()) / nt if nt else None,
                            "solitary_share": float((tree & s & p["solitary"]).sum()) / nt if nt else None,
                            "size3_share": float((tree & s & (p["size"] == 3)).sum()) / nt if nt else None}
        out["species"][cn] = {}
        for i in range(5):
            m = p["model"][(fam == i) & s]
            u, c = np.unique(m, return_counts=True)
            out["species"][cn][FAM[i]] = {str(a_): int(b_) for a_, b_ in zip(u, c)}
    for i in range(5):
        r = p["nn"][fam == i]
        r = r[np.isfinite(r)]
        out["nn"][FAM[i]] = {"n": int(r.size), "p5": float(np.percentile(r, 5)) if r.size >= 20 else None,
                             "p50": float(np.percentile(r, 50)) if r.size >= 20 else None}
    land = cells["land"]
    for (lo, hi), nm in zip(EDGE_BINS, EDGE_NAMES):
        a = float((land & (cells["ctx"] != 2) & (cells["sd"] >= lo) & (cells["sd"] < hi)).sum() * A)
        s = (p["sd"] >= lo) & (p["sd"] < hi) & (p["ctx"] >= 0) & (p["ctx"] != 2)
        nt, nb = int((tree & s).sum()), int(((fam == 2) & s).sum())
        out["edge"][nm] = {"area_ha": a, "trees_per_ha": nt / a if a > 0 else None, "bush_per_ha": nb / a if a > 0 else None,
                           "bush_share": nb / (nt + nb) if nt + nb else None,
                           "broadleaf_share_trees": float(((fam == 1) & s).sum()) / nt if nt else None}
    e = out["edge"]
    ref_t, ref_b = e["in_25_up"]["trees_per_ha"], e["in_25_up"]["bush_per_ha"]
    out["edge_gradient"] = {
        "trees_out_over_in": (e["out_-20_-5"]["trees_per_ha"] / ref_t) if ref_t and e["out_-20_-5"]["trees_per_ha"] is not None else None,
        "trees_5_15_over_in": (e["in_5_15"]["trees_per_ha"] / ref_t) if ref_t and e["in_5_15"]["trees_per_ha"] is not None else None,
        "bush_5_15_over_in": (e["in_5_15"]["bush_per_ha"] / ref_b) if ref_b and e["in_5_15"]["bush_per_ha"] is not None else None}
    if "tex_sd" in cells:
        tsd = cells["tex_sd"]
        out["tex_edge"] = {}
        for (lo, hi), nm in zip(TEX_BINS, TEX_NAMES):
            a = float((land & (cells["ctx"] != 2) & (tsd >= lo) & (tsd < hi)).sum() * A)
            s = (p["tex_sd"] >= lo) & (p["tex_sd"] < hi) & (p["ctx"] >= 0) & (p["ctx"] != 2)
            nt, nb = int((tree & s).sum()), int(((fam == 2) & s).sum())
            out["tex_edge"][nm] = {"area_ha": a, "trees_per_ha": nt / a if a > 0 else None, "bush_per_ha": nb / a if a > 0 else None,
                                   "bush_share": nb / (nt + nb) if nt + nb else None}
        t_ = out["tex_edge"]
        ti = t_["in_25_up"]["trees_per_ha"]

        def ratio(k):
            v = t_[k]["trees_per_ha"]
            return v / ti if ti and v is not None else None
        out["tex_gradient"] = {"trees_out10_over_in25": ratio("out_-10_0"), "trees_out25_over_in25": ratio("out_-25_-10"),
                               "trees_in15_over_in25": ratio("in_0_15")}
    can = cells["canopy"]
    out["canopy_frac"] = float(can[land].mean()) if land.any() else None
    if "forest_surface" in cells:
        fs = cells["forest_surface"]
        out["agreement"] = {"surface_in_canopy": float((fs & can & land).sum() / max(1, (fs & land).sum())),
                            "canopy_on_surface": float((fs & can & land).sum() / max(1, (can & land).sum()))}
    return out


def nn_same_family(x, z, fam):
    from scipy.spatial import cKDTree
    nn = np.full(len(x), np.nan)
    for i in range(6):
        s = np.flatnonzero(fam == i)
        if s.size < 2:
            continue
        d, _ = cKDTree(np.c_[x[s], z[s]]).query(np.c_[x[s], z[s]], k=2)
        nn[s] = d[:, 1]
    return nn


def tvd(counts, ref):
    """Total variation distance between a model-count dict and a reference weight dict, over the union of their keys
    (observed mass on models absent from the reference counts in full; v2, EV111 review 1)."""
    keys = sorted(set(ref) | {k for k, v in counts.items() if v})
    a = np.array([counts.get(k, 0) for k in keys], float)
    b = np.array([ref.get(k, 0) for k in keys], float)
    if a.sum() == 0 or b.sum() == 0:
        return None
    return float(0.5 * np.abs(a / a.sum() - b / b.sum()).sum())

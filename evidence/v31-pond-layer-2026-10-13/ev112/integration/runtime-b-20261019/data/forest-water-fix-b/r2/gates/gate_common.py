"""Shared loaders for the EV111 forest gates. Inputs are read from the files, never from the placer's report.
v2 (EV111 review 1): texture-relative edge profile per sector (forest_metrics.TEX_BINS) with the Livonia sampling of the
surface (12.5 m points, nearest to each 5 m cell, EDT on a raster padded by TEX_PAD m); species TVD judged whenever the
context/family has >= 50 observed instances, over the union of observed and reference models.
v3 (EV111 bog, 2026-10-16): the strict contract is back (g2_g3.py: 0 metrics outside the Livonia envelope, no tolerance
file). The OSM wetland (the bog of the v3 placer) is left out of G2/G3: Livonia has no raised bog, so its window bands
describe forest, edge, riparian and open land, not a bog; G7 (g7_bog.py) judges the bog against stated design bands.
A 5 m cell is bog when >= 50 % of its 25 one-metre sub-samples have the bilinear osm_wetland vertex fraction >= 0.5
(the placer's definition, re-derived here from layers.npz); bog cells leave the analysis area, so their points and
their area leave every G2/G3 metric.
r2 (EV111 review 1, open moss clearings in the bog rim): the cells within BOG_MARGIN_M = 25 m of a bog cell leave G2/G3
too (v3 shipped 0). The canopy contexts are still computed from every tree; once the bog rim is open, the canopy edge
lies on the bog boundary, and with the bog cells left out only its forest half is measured, while every Livonia window
measures both halves of its edges. Measured on the r2 development records (scratchpad ev111-fix, runs m5-*): with 0 m
the r2 pilot fails G2 in both sectors (A density.edge.trees 165.1 > 125.7) and 10 of 12 seeds fail G2 (9 of them in A);
the v3 records of the same seeds failed 3 of 12. With 25 m the r2 and v3 records of seeds 20261016 and 1-6 get the same
G2/G3 verdicts (identical values on 20261016, 1 and 2; small shifts of the canopy contexts on 3-6). Cost: A judges fewer
metrics (G2 28 instead of 44, G3 7 instead of 18). G7 judges that margin (ring: forest 0-25 m outside the bog, contrast
and transition)."""
import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import forest_metrics as FMx  # noqa: E402

sys.path.insert(0, str(HERE.parent.parent / 'gates'))
import gcfg as FINAL
import kit_water_consumer as KIT_WATER
E = Path("E:/DayZ-Baltic-Build/v31-pond-layer-20261013")
TERRAIN = FINAL.TERRAIN
FOOTPRINT = FINAL.FOOTPRINT
STAGE_WRP = FINAL.STAGE_WRP
REFERENCE = FINAL.REFERENCE
LAYERS = FINAL.LAYERS
BOG_MARGIN_M = 25.0                     # r2 (see the docstring); v3 shipped 0.0
PREFIXES = {"G2": ("density.", "share.", "trees.", "nn.", "tvd.", "agreement."),
            "G3": ("edge.", "edge_gradient.", "tex_edge.", "tex_gradient.")}
SECTORS = FINAL.SECTORS
PBO = FINAL.PBO
LAYER_DIRS = FINAL.LAYER_DIRS
N, ZTOP = 2048, 12282
INSET = 50.0
TEX_PAD = 100.0
WT_TOOL_DIR = FINAL.TOOL_DIR


def sha256(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_records(path):
    return json.loads(Path(path).read_text(encoding="ascii"))


def h_planar(H, x, z):
    c = np.clip(np.asarray(x, float) / 6.0, 0, N - 1.000001)
    r = np.clip((ZTOP - np.asarray(z, float)) / 6.0, 0, N - 1.000001)
    c0, r0 = np.floor(c).astype(int), np.floor(r).astype(int)
    fc, fr = c - c0, r - r0
    nw, ne, sw, se = H[r0, c0], H[r0, c0 + 1], H[r0 + 1, c0], H[r0 + 1, c0 + 1]
    return np.where(fc >= fr, nw + fc * (ne - nw) + fr * (se - ne), nw + fr * (sw - nw) + fc * (se - sw))


def in_poly(px, pz, poly):
    poly = np.asarray(poly, float)
    ins = np.zeros(np.shape(px), bool)
    for (xa, za), (xb, zb) in zip(poly, np.roll(poly, -1, axis=0)):
        cond = (za > pz) != (zb > pz)
        xi = xa + (pz - za) * (xb - xa) / np.where(zb == za, 1e-12, zb - za)
        ins ^= cond & (px < xi)
    return ins


def poly_edge_dist(px, pz, poly):
    poly = np.asarray(poly, float)
    d = np.full(np.shape(px), np.inf)
    for (xa, za), (xb, zb) in zip(poly, np.roll(poly, -1, axis=0)):
        ex, ez = xb - xa, zb - za
        t = np.clip(((px - xa) * ex + (pz - za) * ez) / max(ex * ex + ez * ez, 1e-12), 0, 1)
        d = np.minimum(d, np.hypot(px - xa - t * ex, pz - za - t * ez))
    return d


_WETLAND = None


def wetland_fraction(x, z):
    """Bilinear OSM wetland vertex fraction (layers.npz osm_wetland; vertex (r, c) at x = 6c, z = ZTOP - 6r)."""
    global _WETLAND
    if _WETLAND is None:
        _WETLAND = np.load(LAYERS)["osm_wetland"].astype(np.float64)
    V = _WETLAND
    c = np.clip(np.asarray(x, float) / 6.0, 0, N - 1.000001)
    r = np.clip((ZTOP - np.asarray(z, float)) / 6.0, 0, N - 1.000001)
    c0, r0 = np.floor(c).astype(int), np.floor(r).astype(int)
    fc, fr = c - c0, r - r0
    return (1 - fr) * ((1 - fc) * V[r0, c0] + fc * V[r0, c0 + 1]) + fr * ((1 - fc) * V[r0 + 1, c0] + fc * V[r0 + 1, c0 + 1])


def bog_cells(x0, z0, n_r, n_c):
    """Bog 5 m cells (row 0 = south): >= 50 % of the 25 one-metre sub-samples with a wetland fraction >= 0.5."""
    off = np.arange(5) + 0.5
    cx = x0 + np.arange(n_c)[None, :, None, None] * 5 + off[None, None, None, :]
    cz = z0 + np.arange(n_r)[:, None, None, None] * 5 + off[None, None, :, None]
    cx, cz = np.broadcast_to(cx, (n_r, n_c, 5, 5)), np.broadcast_to(cz, (n_r, n_c, 5, 5))
    return (wetland_fraction(cx, cz) >= 0.5).mean(axis=(2, 3)) >= 0.5


def texture_sd(mask, x0, z0, n_r, n_c):
    """Signed distance (m) to the shipped forest-floor texture on the sector's 5 m raster (row 0 = south), sampled as
    Livonia's enoch_surf: surface at the 12.5 m points, the nearest point fills each 5 m cell, EDT x 5 m."""
    k = int(TEX_PAD / FMx.CS)
    ccx = x0 - TEX_PAD + (np.arange(n_c + 2 * k) + 0.5) * FMx.CS
    ccz = z0 - TEX_PAD + (np.arange(n_r + 2 * k) + 0.5) * FMx.CS
    sx = np.rint(ccx / FMx.TEX_SAMPLE) * FMx.TEX_SAMPLE
    sz = np.rint(ccz / FMx.TEX_SAMPLE) * FMx.TEX_SAMPLE
    X0, X1 = int(np.floor(sx.min())) - 1, int(np.ceil(sx.max())) + 2
    Z0, Z1 = int(np.floor(sz.min())) - 2, int(np.ceil(sz.max())) + 1
    slot = mask.compose(X0, Z0, X1, Z1)                                   # row 0 = north (z just below Z1)
    jj = np.floor(sx - X0).astype(int)
    ii = np.floor(Z1 - sz).astype(int)
    forest = slot[ii][:, jj] == 1                                         # rows follow ccz: row 0 = south
    return FMx.surface_sd(forest)[k:k + n_r, k:k + n_c]


def sector_measure(records, ref, sec, H, plane, forest_surface_fn=None, mask=None, exclude_bog=True):
    """Canopy contexts and the shared measurement for one sector (analysis area = polygon inset by INSET m, minus the
    bog cells unless exclude_bog is False)."""
    poly = np.asarray(sec["polygon_xz"], float)
    models = ref["models"]
    fam_of = {nm: FMx.FAM.index(m["family"]) for nm, m in models.items()}
    P = np.array([r["matrix"][9:12] for r in records], float) if records else np.zeros((0, 3))
    names = np.array([r["model"] for r in records], object)
    x, z = P[:, 0], P[:, 2]
    sel = in_poly(x, z, poly)
    x, z, names = x[sel], z[sel], names[sel]
    fam = np.array([fam_of.get(nm, 5) for nm in names], int)
    x0, z0 = float(np.floor(poly[:, 0].min())), float(np.floor(poly[:, 1].min()))
    n_c = int(np.ceil((poly[:, 0].max() - x0) / FMx.CS))
    n_r = int(np.ceil((poly[:, 1].max() - z0) / FMx.CS))
    tree = (fam == 0) | (fam == 1)
    fm, _ = FMx.canopy(x[tree], z[tree], x0, z0, n_r, n_c)
    # water at 5 m: share of 25 sub-samples (1 m) that are visible water (h < pond plane or h < 0.75) >= 0.5
    off = np.arange(5) + 0.5
    cx = x0 + np.arange(n_c)[None, :, None, None] * 5 + off[None, None, None, :]
    cz = z0 + np.arange(n_r)[:, None, None, None] * 5 + off[None, None, :, None]
    cx, cz = np.broadcast_to(cx, (n_r, n_c, 5, 5)), np.broadcast_to(cz, (n_r, n_c, 5, 5))
    h = h_planar(H, cx, cz)
    rr = np.clip(np.floor((ZTOP - cz) / 6).astype(int), 0, N - 2)
    cc = np.clip(np.floor(cx / 6).astype(int), 0, N - 2)
    pl = plane[rr, cc]
    wet = (np.isfinite(pl) & (h < np.nan_to_num(pl, nan=-1e9))) | (h < 0.75)
    wet |= KIT_WATER.sample(cx, cz)  # staged water proxies omitted by the pond footprint
    water = wet.mean(axis=(2, 3)) >= 0.5
    ctx, sd, _ = FMx.contexts(fm, water)
    ccx = x0 + (np.arange(n_c) + 0.5) * 5
    ccz = z0 + (np.arange(n_r) + 0.5) * 5
    GX, GZ = np.meshgrid(ccx, ccz)
    area = in_poly(GX, GZ, poly) & (poly_edge_dist(GX, GZ, poly) >= INSET)
    bogc = bog_cells(x0, z0, n_r, n_c)
    if BOG_MARGIN_M > 0 and bogc.any():
        bogc = bogc | (ndimage.distance_transform_edt(~bogc) * FMx.CS <= BOG_MARGIN_M)
    bog_excluded_ha = float((area & bogc).sum() * FMx.A)
    if exclude_bog:
        area &= ~bogc
    r_pt = np.clip(np.floor((z - z0) / 5).astype(int), 0, n_r - 1)
    c_pt = np.clip(np.floor((x - x0) / 5).astype(int), 0, n_c - 1)
    pin = area[r_pt, c_pt]
    tsd = texture_sd(mask, x0, z0, n_r, n_c) if mask is not None else None
    nn = FMx.nn_same_family(x, z, fam)
    sol = np.array([models[nm]["solitary"] if nm in models else False for nm in names], bool)
    size = np.array([models[nm]["size"] if nm in models else 0 for nm in names], int)
    p = {"fam": fam[pin], "ctx": ctx[r_pt, c_pt][pin], "sd": sd[r_pt, c_pt][pin], "nn": nn[pin], "model": names[pin],
         "solitary": sol[pin], "size": size[pin]}
    if tsd is not None:
        p["tex_sd"] = tsd[r_pt, c_pt][pin]
    cells = {"ctx": np.where(area, ctx, -1), "sd": sd[area], "land": (~water)[area], "canopy": fm[area]}
    cells_ctx = np.where(area, ctx, -1)
    cells = {"ctx": cells_ctx[area], "sd": sd[area], "land": (~water)[area], "canopy": fm[area]}
    if tsd is not None:
        cells["tex_sd"] = tsd[area]
    if forest_surface_fn is not None:
        cells["forest_surface"] = forest_surface_fn(x0, z0, n_r, n_c)[area]
    m = FMx.measure(p, cells)
    m["tvd"] = {cn: {FMx.FAM[i]: (FMx.tvd(m["species"][cn][FMx.FAM[i]], ref["species_reference"][cn][FMx.FAM[i]])
                                  if sum(m["species"][cn][FMx.FAM[i]].values()) >= 50 else None)
                     for i in range(5)} for cn in FMx.CTX}
    m["n_points_analysed"] = int(pin.sum())
    m["analysis_area_ha"] = float(area.sum() * FMx.A)
    m["unknown_models"] = int(sum(1 for nm in names if nm not in models))
    m["bog_excluded_ha"] = bog_excluded_ha if exclude_bog else 0.0
    return m, {"fm": fm, "ctx": ctx, "sd": sd, "water": water, "area": area, "x0": x0, "z0": z0, "tex_sd": tsd, "bog": bogc}


def texture_mask():
    sys.path.insert(0, str(WT_TOOL_DIR))
    import forest_v31 as T  # texture composition only (the mask under test is the vegetation, not the texture)
    return T.Mask(PBO, LAYER_DIRS)


def texture_forest_fn():
    sys.path.insert(0, str(WT_TOOL_DIR))
    import forest_v31 as T  # texture composition only (the mask under test is the vegetation, not the texture)
    mk = T.Mask(PBO, LAYER_DIRS)

    def f(x0, z0, n_r, n_c):
        X0, Z0 = int(x0), int(z0)
        slot = mk.compose(X0, Z0, X0 + n_c * 5, Z0 + n_r * 5)      # row 0 = north
        s = (slot == 1).reshape(n_r, 5, n_c, 5).mean(axis=(1, 3)) >= 0.5
        return s[::-1]                                               # row 0 = south
    return f


def metric_table(m, ref):
    """Flatten a measurement into {metric: value} with the same names as the reference bands."""
    out = {}
    min_area = ref["windows"]["min_context_area_ha"]
    for cn in FMx.CTX:
        if m["area_ha"][cn] < min_area[cn]:
            continue
        for f_ in FMx.FAM[:5] + ["trees"]:
            out[f"density.{cn}.{f_}"] = m["density"][cn][f_]
        for f_ in FMx.FAM[:5]:
            out[f"share.{cn}.{f_}"] = m["share"][cn][f_]
        if m["trees"][cn]["n"] >= 50:
            for k_ in ("broadleaf_share", "solitary_share", "size3_share"):
                out[f"trees.{cn}.{k_}"] = m["trees"][cn][k_]
        for f_ in FMx.FAM[:5]:
            if m["tvd"][cn][f_] is not None:
                out[f"tvd.{cn}.{f_}"] = m["tvd"][cn][f_]
    for f_ in FMx.FAM[:5]:
        if m["nn"][f_]["n"] >= 100:
            out[f"nn.{f_}.p5"] = m["nn"][f_]["p5"]
            out[f"nn.{f_}.p50"] = m["nn"][f_]["p50"]
    for nm in FMx.EDGE_NAMES:
        if m["edge"][nm]["area_ha"] >= ref["windows"]["edge_bin_min_area_ha"]:
            for k_ in ("trees_per_ha", "bush_per_ha", "bush_share", "broadleaf_share_trees"):
                out[f"edge.{nm}.{k_}"] = m["edge"][nm][k_]
    if m["edge"]["in_5_15"]["area_ha"] >= 2 and m["edge"]["out_-20_-5"]["area_ha"] >= 2:
        for k_ in ("trees_out_over_in", "trees_5_15_over_in", "bush_5_15_over_in"):
            out[f"edge_gradient.{k_}"] = m["edge_gradient"][k_]
    if "tex_edge" in m:
        tmin = ref["windows"]["tex_bin_min_area_ha"]
        te = m["tex_edge"]
        for nm in FMx.TEX_NAMES:
            if te[nm]["area_ha"] >= tmin:
                for k_ in ("trees_per_ha", "bush_per_ha", "bush_share"):
                    out[f"tex_edge.{nm}.{k_}"] = te[nm][k_]
        for k_, b_ in (("trees_out10_over_in25", "out_-10_0"), ("trees_out25_over_in25", "out_-25_-10"), ("trees_in15_over_in25", "in_0_15")):
            if te[b_]["area_ha"] >= tmin and te["in_25_up"]["area_ha"] >= tmin:
                out[f"tex_gradient.{k_}"] = m["tex_gradient"][k_]
    if "agreement" in m:
        out["agreement.surface_in_canopy"] = m["agreement"]["surface_in_canopy"]
        out["agreement.canopy_on_surface"] = m["agreement"]["canopy_on_surface"]
    return out


def excess(v, lo, hi, width):
    """Distance of v outside [lo, hi] in units of the band width (0 inside)."""
    d = (lo - v) if v < lo else ((v - hi) if v > hi else 0.0)
    return float(d / max(width, 1e-12))


def judge(values, ref, prefixes, one_sided=None):
    """Envelope rule per metric: within [min, max] of the comparable Livonia windows; tvd.* only <= max and
    agreement.* only >= min. A metric without a band (n < 10 windows) is reported as NO_BAND and not judged.
    v3 (EV111 review 1): the v2 [p10, p90] exception for two canopy edge metrics is gone (the texture-relative bins
    carry the edge contract now). v3: the gate passes with 0 failed metrics (g2_g3.py, strict contract)."""
    rows, ok = [], True
    for k, v in sorted(values.items()):
        if not k.startswith(prefixes):
            continue
        b = ref["bands"].get(k, {})
        if "min" not in b or v is None:
            rows.append((k, v, None, None, "NO_BAND"))
            continue
        lo, hi = b["min"], b["max"]
        if k.startswith("tvd."):
            lo = -np.inf
        if k.startswith("agreement."):
            hi = np.inf
        good = lo <= v <= hi
        ok &= bool(good)
        ex = excess(v, lo, hi, b["max"] - b["min"])
        central = b["p10"] <= v <= b["p90"]
        rows.append((k, v, lo, hi, ("PASS" if good else f"FAIL excess {ex:.3f}") + ("" if central else " (outside p10-p90)")))
    return ok, rows

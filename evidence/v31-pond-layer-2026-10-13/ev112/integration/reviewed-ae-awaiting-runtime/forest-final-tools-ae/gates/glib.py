"""Shared measurement for the EV112 map-wide forest gates.

Windows: 1 km squares on a 500 m step from the map's south-west corner (x0, z0 in 0, 500, ..., 11000 and 11288), 576
windows, as Livonia's 26 x 26 grid of 576. The canopy, contexts and nearest neighbours of a window are computed with
the instances within MARGIN m around it (Livonia measured them on the whole map), the metrics over the window's cells
minus the bog and its 25 m margin (r2 contract, gate_common.BOG_MARGIN_M). Metric names, bands and the judge are the
EV111 r2 ones (scripts-v3r2/gates/gate_common.py metric_table, judge; forest_metrics.py)."""
import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import gcfg  # noqa: E402
import recio  # noqa: E402

sys.path.insert(0, str(gcfg.R2_GATES))
sys.path.insert(0, str(gcfg.R2_GATES.parent))
import forest_metrics as FMx  # noqa: E402
import gate_common as GC  # noqa: E402

MARGIN = 100.0
NB = 2458
WIN_X0 = sorted(set(range(0, 11001, 500)) | {11288})


class MapRecords:
    def __init__(self, path, bbox=None):
        self.ref = json.loads(gcfg.REFERENCE.read_text(encoding="utf-8"))
        mods = self.ref["models"]
        self.models, self.midx, self.m, self.keys_ok = recio.load_records(path, bbox)
        known = np.array([nm in mods for nm in self.models] + [False], bool)
        mi = np.where(self.midx < len(self.models), self.midx, len(self.models))
        self.known = known[mi]
        fam_of = np.array([FMx.FAM.index(mods[nm]["family"]) if nm in mods else 5 for nm in self.models] + [5], int)
        sol_of = np.array([bool(mods[nm]["solitary"]) if nm in mods else False for nm in self.models] + [False])
        size_of = np.array([int(mods[nm]["size"]) if nm in mods else 0 for nm in self.models] + [0])
        pine_of = np.array([(mods[nm]["genus"] or "") == "pinussylvestris" if nm in mods else False for nm in self.models] + [False])
        self.fam, self.sol, self.size, self.pine = fam_of[mi], sol_of[mi], size_of[mi], pine_of[mi]
        self.names = np.array(self.models + ["?"], object)[mi]
        self.x, self.z = self.m[:, 9], self.m[:, 11]
        self.tree = (self.fam == 0) | (self.fam == 1)
        self.n = len(self.x)
        # 250 m buckets for window selection
        self.bk = (np.clip(self.z // 250, 0, 49).astype(int) * 50 + np.clip(self.x // 250, 0, 49).astype(int))
        self.order = np.argsort(self.bk, kind="stable")
        self.starts = np.searchsorted(self.bk[self.order], np.arange(2501))

    def select(self, x0, z0, x1, z1):
        bx0, bx1 = int(max(0, x0 // 250)), int(min(49, (x1 - 1e-9) // 250))
        bz0, bz1 = int(max(0, z0 // 250)), int(min(49, (z1 - 1e-9) // 250))
        ids = [self.order[self.starts[b]:self.starts[b + 1]] for bz in range(bz0, bz1 + 1) for b in range(bz * 50 + bx0, bz * 50 + bx1 + 1)]
        ids = np.concatenate(ids) if ids else np.zeros(0, int)
        k = (self.x[ids] >= x0) & (self.x[ids] < x1) & (self.z[ids] >= z0) & (self.z[ids] < z1)
        return np.sort(ids[k])


class Rasters:
    def __init__(self, d):
        d = Path(d)
        g = np.load(d / "g5m.npz")
        for k in g.files:
            setattr(self, k, g[k])
        self.dir = d

    def big(self, name):
        return np.load(self.dir / f"{name}.npy", mmap_mode="r")


def contexts_safe(fm, water):
    """forest_metrics.contexts with a defined distance when the raster is all canopy or has none (scipy's EDT
    measures to a phantom corner when there is no background pixel)."""
    land = ~water
    if fm.all():
        sd = np.full(fm.shape, 1e3)
    elif not fm.any():
        sd = np.full(fm.shape, -1e3)
    else:
        sd = np.where(fm, ndimage.distance_transform_edt(fm), -ndimage.distance_transform_edt(~fm)) * FMx.CS
    dw = ndimage.distance_transform_edt(~water) * FMx.CS if water.any() else np.full(water.shape, 1e9)
    ctx = np.full(fm.shape, -1, np.int8)
    ctx[land & (sd >= 25)] = 0
    ctx[land & (sd < 25) & (sd >= -10)] = 1
    ctx[land & (sd < -10)] = 3
    ctx[land & (dw <= 25)] = 2
    return ctx, sd


def window_measure(R, MR, x0, z0, size=1000.0, exclude_bog=True):
    """G2/G3 measurement of one window: (metrics dict from forest_metrics.measure, comparable flag, info)."""
    ref = MR.ref
    c0, r0, n = int(x0 // 5), int(z0 // 5), int(size // 5)
    k = int(MARGIN // 5)
    a0, a1, b0, b1 = r0 - k, r0 + n + k, c0 - k, c0 + n + k
    X0, Z0 = b0 * 5.0, a0 * 5.0
    ids = MR.select(X0, Z0, b1 * 5.0, a1 * 5.0)
    x, z, fam = MR.x[ids], MR.z[ids], MR.fam[ids]
    tree = (fam == 0) | (fam == 1)
    nr, nc = a1 - a0, b1 - b0
    fm, _ = FMx.canopy(x[tree], z[tree], X0, Z0, nr, nc)

    def crop(arr, fill):
        o = np.full((nr, nc), fill, arr.dtype)
        aa0, aa1, bb0, bb1 = max(a0, 0), min(a1, NB), max(b0, 0), min(b1, NB)
        o[aa0 - a0:aa1 - a0, bb0 - b0:bb1 - b0] = arr[aa0:aa1, bb0:bb1]
        return o
    water = crop(R.water, True)
    ctx, sd = contexts_safe(fm, water)
    tsd, texm, bogm = crop(R.tsd, np.float32(-1e3)), crop(R.tex_major, False), crop(R.bogm, False)
    win = np.zeros((nr, nc), bool)
    win[k:k + n, k:k + n] = True
    area = win & (~bogm if exclude_bog else True)
    rp = np.clip(np.floor((z - Z0) / 5).astype(int), 0, nr - 1)
    cp = np.clip(np.floor((x - X0) / 5).astype(int), 0, nc - 1)
    pin = area[rp, cp]
    nn = FMx.nn_same_family(x, z, fam)
    p = {"fam": fam[pin], "ctx": ctx[rp, cp][pin], "sd": sd[rp, cp][pin], "nn": nn[pin], "model": MR.names[ids][pin],
         "solitary": MR.sol[ids][pin], "size": MR.size[ids][pin], "tex_sd": tsd[rp, cp][pin]}
    cells = {"ctx": ctx[area], "sd": sd[area], "land": (~water)[area], "canopy": fm[area], "tex_sd": tsd[area],
             "forest_surface": texm[area]}
    m = FMx.measure(p, cells)
    m["tvd"] = {cn: {FMx.FAM[i]: (FMx.tvd(m["species"][cn][FMx.FAM[i]], ref["species_reference"][cn][FMx.FAM[i]])
                                  if sum(m["species"][cn][FMx.FAM[i]].values()) >= 50 else None)
                     for i in range(5)} for cn in FMx.CTX}
    land_frac = float((~water)[win].mean())
    canopy_frac = float(fm[win][~water[win]].mean()) if (~water[win]).any() else 0.0
    cx_, tx_ = cells["ctx"], cells["forest_surface"]
    on_tex = {str(k_): (float(tx_[cx_ == k_].mean()) if (cx_ == k_).any() else None) for k_ in range(4)}
    info = {"x0": x0, "z0": z0, "land_frac": land_frac, "canopy_frac": canopy_frac, "ctx_on_texture": on_tex,
            "analysis_ha": float(area.sum() * 25 / 1e4), "bog_excluded_ha": float((win & bogm).sum() * 25 / 1e4),
            "n_points": int(pin.sum()), "unknown_models": int((~MR.known[ids][pin]).sum())}
    return m, land_frac >= 0.9 and canopy_frac >= 0.5, info


def agreement_maps(R, MR):
    """Global 5 m maps of the agreement gate: forest-floor land cells, tree-free (no tree within 10 m) cells, tree
    count per cell, far land (tsd < -40 m, > 25 m from water, not bog + 25 m margin)."""
    ff = R.tex_samp & ~R.water & ~R.narva & ~R.kit & ~R.bridge
    rr, cc = np.nonzero(ff)
    tx, tz = MR.x[MR.tree], MR.z[MR.tree]
    free = np.zeros(ff.shape, bool)
    if len(tx):
        d = cKDTree(np.c_[tx, tz]).query(np.c_[(cc + 0.5) * 5, (rr + 0.5) * 5], distance_upper_bound=11.0)[0]
        free[rr, cc] = d > 10.0
    else:
        free = ff.copy()
    cnt = np.zeros(ff.shape)
    rp = np.clip(np.floor(tz / 5).astype(int), 0, NB - 1)
    cp = np.clip(np.floor(tx / 5).astype(int), 0, NB - 1)
    np.add.at(cnt, (rp, cp), 1)
    far = ~R.water & (R.tsd < -40) & (R.dw > 25) & ~R.bogm & ~R.narva
    return ff, free, cnt, far


def agreement_window(ff, free, cnt, far, x0, z0, size=1000.0):
    c0, r0, n = int(x0 // 5), int(z0 // 5), int(size // 5)
    sl = (slice(r0, r0 + n), slice(c0, c0 + n))
    nf, nfar = int(ff[sl].sum()), int(far[sl].sum())
    res = {"x0": x0, "z0": z0, "forest_ha": nf * 25 / 1e4, "far_ha": nfar * 25 / 1e4}
    if nf:
        fr = free[sl]
        res["free10"] = float(fr.sum()) / nf
        lab, k = ndimage.label(fr, structure=np.ones((3, 3)))
        if k:
            sz = ndimage.sum(np.ones(fr.shape), lab, index=np.arange(1, k + 1))
            keep = np.zeros(k + 1, bool)
            keep[1:] = sz >= 16
            res["patch10_400"] = float(keep[lab].sum()) / nf
            res["max_patch_m2"] = float(sz.max()) * 25.0
            big = int(np.argmax(sz)) + 1
            yy, xx = np.nonzero(lab == big)
            res["max_patch_xz"] = [round(x0 + (xx.mean() + 0.5) * 5, 1), round(z0 + (yy.mean() + 0.5) * 5, 1)]
        else:
            res["patch10_400"] = 0.0
            res["max_patch_m2"] = 0.0
    if nfar:
        res["far_trees_ha"] = float(cnt[sl][far[sl]].sum()) / (nfar * 25 / 1e4)
    return res

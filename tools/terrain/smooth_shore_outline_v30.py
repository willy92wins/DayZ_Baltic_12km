"""Smoother shore outline for the shore fit, and a narrower shallow margin in Narva (Guillermo, 04-10, view 9).

1. Narva margin: inside the Narva mask, navigable vertices shallower than --margin-depth and within --margin-width of
   land become land at level + --bank-margin (never on platforms, reserves or beach, never inside the 24 m channel
   corridor: vertices deeper than 2.9 m and their 8-neighbours stay). Then the Narva shelf: navigable beds within
   30 m of land go down to a bank profile, 0.4 m deep at 6 m from land and --shelf-depth at 18 m (platforms,
   reserves and beach stay).
2. Outline: the zero contour of the input sd (the design outline the shore fit targets), with the new Narva land
   taken as outside, smoothed along its length with a Gaussian (--sigma m; --sigma-narva inside the Narva mask),
   each point moving at most --max-shift m. Closed lines wrap; open lines keep their ends.
3. sd: distance to the smoothed lines on every vertex where the input sd is finite (and on the new land), sign from
   the class of the output (water negative, land positive), as the builder signs it. A vertex whose nearest
   smoothed line is farther than its input distance + max shift + 1 m (outline cut by the map border or the sea
   mask) keeps its input distance.
Output <out>/terrain_shape.npz, <out>/sd_shape.npz and <out>/report.json (shift percentiles, turning before/after).
Usage: smooth_shore_outline_v30.py --terrain IN.npz --sd SD.npz --out OUTDIR [--sigma 12] [--sigma-narva 18]
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import contourpy
import numpy as np
import shapely
from scipy import ndimage
from scipy.ndimage import gaussian_filter1d

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v30_common import N, grid_xz  # noqa: E402

STRUCT8 = np.ones((3, 3), dtype=int)
STEP = 1.5


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def resample(ln, step=STEP):
    seg = np.linalg.norm(np.diff(ln, axis=0), axis=1)
    s = np.r_[0, np.cumsum(seg)]
    if s[-1] < 2 * step:
        return ln, s[-1]
    q = np.linspace(0, s[-1], max(int(s[-1] / step) + 1, 3))
    return np.column_stack([np.interp(q, s, ln[:, 0]), np.interp(q, s, ln[:, 1])]), s[-1]


def smooth_line(ln, sig_at, max_shift):
    """Arc-length Gaussian with a per-point sigma (metres): blend of two fixed-sigma passes by the local sigma."""
    closed = np.allclose(ln[0], ln[-1])
    p, length = resample(ln[:-1] if closed else ln)
    if length < 3 * STEP or len(p) < 4:
        return ln
    if closed:
        p = p[:-1] if np.allclose(p[0], p[-1]) else p
    sig = sig_at(p)
    mode = 'wrap' if closed else 'nearest'
    out = np.empty_like(p)
    lo, hi = sig.min(), sig.max()
    a = np.column_stack([gaussian_filter1d(p[:, k], lo / STEP, mode=mode) for k in (0, 1)])
    b = a if hi - lo < 0.5 else np.column_stack([gaussian_filter1d(p[:, k], hi / STEP, mode=mode) for k in (0, 1)])
    w = ((sig - lo) / (hi - lo))[:, None] if hi - lo >= 0.5 else np.zeros((len(p), 1))
    out[:] = (1 - w) * a + w * b
    if not closed:                                  # keep the ends: blend back over two sigmas
        s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
        k = np.clip(np.minimum(s, s[-1] - s) / (2 * np.maximum(sig, 1e-3)), 0, 1)[:, None]
        out = k * out + (1 - k) * p
    d = out - p
    n = np.linalg.norm(d, axis=1, keepdims=True)
    out = p + d * np.minimum(1.0, max_shift / np.maximum(n, 1e-9))
    if closed:
        out = np.vstack([out, out[:1]])
    return out


def turn_p95(lines, scale=12.0):
    vals = []
    for ln in lines:
        seg = np.linalg.norm(np.diff(ln, axis=0), axis=1)
        s = np.r_[0, np.cumsum(seg)]
        if s[-1] < 4 * scale:
            continue
        q = np.arange(0, s[-1], scale)
        p = np.column_stack([np.interp(q, s, ln[:, 0]), np.interp(q, s, ln[:, 1])])
        d = np.diff(p, axis=0)
        a = np.degrees(np.arctan2(d[:, 1], d[:, 0]))
        vals.append(np.abs((np.diff(a) + 180) % 360 - 180))
    v = np.concatenate(vals) if vals else np.array([np.nan])
    return {'p50': round(float(np.percentile(v, 50)), 1), 'p95': round(float(np.percentile(v, 95)), 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--terrain', type=Path, required=True)
    ap.add_argument('--sd', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--sigma', type=float, default=12.0)
    ap.add_argument('--sigma-narva', type=float, default=18.0)
    ap.add_argument('--max-shift', type=float, default=4.0)
    ap.add_argument('--margin-depth', type=float, default=0.6)
    ap.add_argument('--margin-width', type=float, default=12.0)
    ap.add_argument('--bank-margin', type=float, default=0.10)
    ap.add_argument('--shelf-depth', type=float, default=3.0)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    t = dict(np.load(a.terrain))
    h = t['heights'].astype(np.float64)
    cls = t['cls'].copy()
    level = t['level'].astype(np.float64)
    sd0 = np.load(a.sd)['sd'].astype(np.float64)
    protected = t['platform'] | t['reserve'] | t['beach']
    narva = t['narva']
    x, z = grid_xz()
    rep = {'inputs': {'terrain': str(a.terrain), 'terrain_sha256': sha(a.terrain), 'sd': str(a.sd),
                      'sd_sha256': sha(a.sd)}, 'params': {k: v for k, v in vars(a).items() if k not in ('terrain', 'sd', 'out')}}

    # 1. Narva shallow margin to land.
    nav = cls == 3
    depth = np.where(nav, level - h, np.nan)
    corridor = ndimage.binary_dilation(nav & (depth > 2.9), structure=STRUCT8)
    dist_land = ndimage.distance_transform_edt(cls > 0) * 6.0
    margin = narva & nav & (depth < a.margin_depth) & (dist_land <= a.margin_width) & ~protected & ~corridor
    lvl_m = level[margin]
    h[margin] = np.maximum(h[margin], lvl_m + a.bank_margin)
    cls[margin] = 0
    level[margin] = np.nan
    rep['narva_margin'] = {'vertices_to_land': int(margin.sum()),
                           'raise_max_m': round(float((h - t['heights'])[margin].max()), 3) if margin.any() else 0}
    # 1b. Narva shelf: the light 1-2 m deep band along the bank reads as flooded meadow (view 9). The bed goes down to
    # a steeper bank profile, 0.4 m deep at the first wet vertex (6 m from land) and the corridor depth 18 m out.
    nav = cls == 3
    dist_land = ndimage.distance_transform_edt(cls > 0) * 6.0
    prof = np.minimum(a.shelf_depth, 0.4 + (a.shelf_depth - 0.4) * (dist_land - 6.0) / 12.0)
    # (deepening never harms the 24 m corridor, so its neighbours are allowed here)
    shelf = narva & nav & (dist_land <= 30.0) & ~protected & (h > level - prof + 1e-6)
    deep = np.where(shelf, (h - (level - prof)), 0.0)
    h[shelf] = (level - prof)[shelf]
    rep['narva_shelf'] = {'vertices_deepened': int(shelf.sum()),
                          'deepen_max_m': round(float(deep.max()), 3) if shelf.any() else 0,
                          'deepen_median_m': round(float(np.median(deep[shelf])), 3) if shelf.any() else 0}

    # 2. Outline: zero contour of sd with the new land outside, smoothed along its length.
    sd_tmp = sd0.copy()
    sd_tmp[margin] = np.where(np.isfinite(sd_tmp[margin]), np.maximum(sd_tmp[margin], 3.0), 3.0)
    gen = contourpy.contour_generator(x=np.arange(N) * 6.0, y=12282.0 - np.arange(N) * 6.0,
                                      z=np.ma.masked_invalid(sd_tmp), line_type=contourpy.LineType.Separate)
    lines = [ln for ln in gen.lines(0.0) if len(ln) >= 3]

    def sig_at(p):
        cc = np.clip(np.rint(p[:, 0] / 6).astype(int), 0, N - 1)
        rr = np.clip(np.rint((12282 - p[:, 1]) / 6).astype(int), 0, N - 1)
        return np.where(narva[rr, cc], a.sigma_narva, a.sigma)

    smooth = [smooth_line(ln, sig_at, a.max_shift) for ln in lines]
    shifts = []
    for ln, sm in zip(lines, smooth):
        if len(sm) != len(ln):
            p, _ = resample(ln[:-1] if np.allclose(ln[0], ln[-1]) else ln)
            k = min(len(p), len(sm))
            shifts.append(np.linalg.norm(sm[:k] - p[:k], axis=1))
    sh = np.concatenate(shifts) if shifts else np.array([0.0])
    rep['outline'] = {'lines': len(lines), 'shift_m_p50_p95_max': [round(float(np.percentile(sh, 50)), 2),
                                                                    round(float(np.percentile(sh, 95)), 2),
                                                                    round(float(sh.max()), 2)],
                      'turn_deg_per_12m_before': turn_p95(lines), 'turn_deg_per_12m_after': turn_p95(smooth)}

    # 3. sd to the smoothed lines, signed by the output class.
    segs = np.concatenate([np.stack([s[:-1], s[1:]], axis=1) for s in smooth if len(s) >= 2])
    tree = shapely.STRtree(shapely.linestrings(segs))
    sup = np.isfinite(sd0) | margin
    _, dist = tree.query_nearest(shapely.points(x[sup], z[sup]), return_distance=True, all_matches=False)
    # Where the input outline has no zero contour on the map (lakes cut by the map border, inland water against the
    # sea mask) the nearest smoothed line lies far away: those vertices keep their input distance.
    d0 = np.abs(sd0[sup])
    far = np.isfinite(d0) & (dist > d0 + a.max_shift + 1.0)
    dist = np.where(far, d0, dist)
    wet_out = cls > 0
    sd = np.full((N, N), np.nan, dtype=np.float32)
    sd[sup] = np.where(wet_out[sup], -dist, dist)
    rep['sd_kept_input_distance'] = int(far.sum())
    disagree = sup & np.isfinite(sd0) & (np.sign(sd0) != np.sign(sd)) & (sd0 != 0)
    rep['sd'] = {'support_vertices': int(sup.sum()), 'sign_changed_vs_input': int(disagree.sum()),
                 'abs_change_m_p50_p95': [round(float(np.percentile(np.abs(sd - sd0)[sup & np.isfinite(sd0)], q)), 2)
                                          for q in (50, 95)]}
    out = dict(t)
    out['heights'] = h.astype(t['heights'].dtype)
    out['cls'] = cls
    out['level'] = level.astype(t['level'].dtype)
    out['water'] = cls > 0
    np.savez_compressed(a.out / 'terrain_shape.npz', **out)
    np.savez_compressed(a.out / 'sd_shape.npz', sd=sd)
    rep['outputs'] = {'terrain_sha256': sha(a.out / 'terrain_shape.npz'), 'sd_sha256': sha(a.out / 'sd_shape.npz')}
    (a.out / 'report.json').write_text(json.dumps(rep, indent=1), encoding='utf-8')
    print(json.dumps({k: v for k, v in rep.items() if k != 'inputs'}, indent=1))


if __name__ == '__main__':
    main()

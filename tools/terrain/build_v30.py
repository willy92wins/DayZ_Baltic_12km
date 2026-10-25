"""Build terrain V30 (offline, vertex grid) from relief V30 and water V30. Phases approved by Guillermo on 2026-10-02.

Steps, in order:
 1 dimples   high zones: fill closed depressions that hold no water (Guillermo asked to fill them).
 2 excess    V29 water the new design drops: Laplace fill from the surrounding land.
 3 valleys   ridges across rivers, streams and navigable reaches are lowered to a natural valley envelope.
 4 roads     Codex's graded chains re-graded on the new terrain: smooth profile (grade <= 6 %, junctions shared),
             flat platform for every vertex whose triangles touch the 8 m band, 30-degree cut and fill to terrain.
             Stations within 10 m of water are bridge or ford reserves.
 5 water     beds carved below each level (depth grows from the bank); banks and land kept above water.
 6 Narva     within 480 m of the bridge centre V29 stays exact; 480-600 m blends back.
 7 slopes    per-axis cap 2.88 m (34.2 deg) by lowering, with water, road platforms and Narva fixed.
Output: <out>/terrain_v30.npz (heights float32 and masks), <out>/build_v30.json.
"""
import json
import os
import sys

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt, gaussian_filter, grey_erosion
from scipy.sparse import diags, identity
from scipy.sparse.linalg import spsolve
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v30_common import N, R, cell_planes, grid_xz, tri_sample, vertex_plane_bounds  # noqa: E402

sys.path.insert(0, os.path.join(R, "tools", "navigation"))
from verify_roads_v30 import road_chains  # noqa: E402  (scratchpad copy shares the name)

V30, OUT = sys.argv[1], sys.argv[2]
P = {
    "dimple_min_m": 0.2, "dimple_water_clear_m": 30.0, "high_min": 0.3,
    "valley_deg": {3: 14.0, 5: 18.0, 6: 22.0}, "valley_reach_m": 150.0, "valley_freeboard_m": 0.35,
    "road_reserve_water_m": 10.0, "road_alpha": 4.0e5, "road_grade_max": 0.058, "road_curvature_max": 0.001, "road_grade_per_radius": 0.002, "road_grade_per_radius_tight": 0.0005, "road_tight_radius_m": 16.0, "road_turn_window_m": 6.0,
    "road_couple_m": 25.0, "road_couple_tol_m": 0.002, "road_admm_iters": 3000, "road_admm_eps": 2e-5,
    "road_dense_m": 0.125, "road_platform_m": 12.6, "road_slope_deg": 30.0, "road_reach_m": 70.0,
    "depth_max": {1: 2.0, 2: 2.0, 3: 3.0, 5: 1.2, 6: 0.5, 7: 1.2}, "bank_radius_m": 8.5, "delta_bed": -2.5, "bed_edge_m": 0.15, "bed_gain_per_m": 0.45,
    "bank_margin_m": 0.35, "dry_floor_m": 1.4, "shore_slope": 0.12, "shore_min_depth_m": 0.10, "shore_max_depth_m": 1.2, "shore_freeboard_m": 0.06,
    "shore_reach_m": 12.0, "beach_slope": 0.15, "beach_freeboard_m": 0.10, "beach_floor_m": 0.80, "piece_depth_m": 0.05, "piece_freeboard_m": 0.03,
    "narva_radius_m": 480.0, "narva_blend_m": 120.0, "slope_cap_m": 2.88,
}
NARVA = np.array([2417.1428225906, 6889.8850822322])
os.makedirs(OUT, exist_ok=True)


def ease(t):
    t = np.clip(t, 0, 1)
    return t * t * t * (10 + t * (-15 + 6 * t))


def fill_depressions(h, seeds):
    """Morphological reconstruction by erosion: fills closed depressions; seeds keep their height."""
    big = h.max() + 1.0
    f = np.where(seeds, h, big)
    for _ in range(20000):
        nf = np.maximum(h, grey_erosion(f, size=(3, 3)))
        nf[seeds] = h[seeds]
        if np.array_equal(nf, f):
            return f
        f = nf
    raise ValueError("depression filling did not converge")


def laplace_fill(h, mask, iters=3000):
    """Harmonic fill of mask from its boundary (Jacobi on a nearest-value start)."""
    _, idx = distance_transform_edt(mask, return_indices=True)
    out = h.copy()
    out[mask] = h[idx[0], idx[1]][mask]
    ys, xs = np.nonzero(binary_dilation(mask, iterations=2))
    y0, y1, x0, x1 = max(ys.min() - 2, 0), min(ys.max() + 3, N), max(xs.min() - 2, 0), min(xs.max() + 3, N)
    sub, m = out[y0:y1, x0:x1], mask[y0:y1, x0:x1]
    for _ in range(iters):
        avg = 0.25 * (np.roll(sub, 1, 0) + np.roll(sub, -1, 0) + np.roll(sub, 1, 1) + np.roll(sub, -1, 1))
        sub[m] = avg[m]
    out[y0:y1, x0:x1] = sub
    return out


def admm_qp(p, q, a, lo, hi, eq):
    """min 1/2 x'Px + q'x  s.t. lo <= Ax <= hi (OSQP's ADMM: relaxation 1.6, rho x1e3 on equality rows, adaptive rho)."""
    from scipy.sparse.linalg import splu
    n, m = p.shape[0], a.shape[0]
    sigma, alpha = 1e-6, 1.6
    scale = float(p.diagonal().mean())
    rho = 0.1 * scale
    at = a.T.tocsr()
    x, z, y = np.zeros(n), np.zeros(m), np.zeros(m)
    log = []

    def factor(r):
        rv = np.where(eq, 1e3 * r, r)
        return splu((p + sigma * identity(n) + at @ diags(rv) @ a).tocsc()), rv

    lu, rv = factor(rho)
    for it in range(1, P["road_admm_iters"] + 1):
        xt = lu.solve(sigma * x - q + at @ (rv * z - y))
        zt = a @ xt
        x = alpha * xt + (1 - alpha) * x
        zr = alpha * zt + (1 - alpha) * z
        zn = np.clip(zr + y / rv, lo, hi)
        y = y + rv * (zr - zn)
        z = zn
        if it % 25 == 0:
            ax = a @ x
            rp = float(np.abs(ax - z).max())
            px = p @ x
            aty = at @ y
            rd = float(np.abs(px + q + aty).max())
            log.append([it, rp, rd, rho])
            if it % 100 == 0:
                print("admm", it, f"{rp:.2e}", f"{rd:.2e}", f"{rho:.2e}", flush=True)
            if rp < P["road_admm_eps"] and rd < 1e-3 * max(np.abs(q).max(), 1.0):
                break
            if it % 200 == 0:
                np_ = rp / max(np.abs(ax).max(), np.abs(z).max(), 1e-9)
                nd = rd / max(np.abs(px).max(), np.abs(aty).max(), np.abs(q).max(), 1e-9)
                new = rho * np.sqrt(np_ / max(nd, 1e-12))
                if new > 5 * rho or new < rho / 5:
                    rho = float(np.clip(new, 1e-6 * scale, 1e6 * scale))
                    lu, rv = factor(rho)
    return x, log


def polish(base, rhs0, cmat, lo, hi, eq, x0):
    """Exact finish: rows near their bounds after ADMM are held there as stiff penalties; equality rows always."""
    span = np.where(np.isfinite(hi - lo), np.minimum(hi - lo, 1.0), 1.0)
    val = cmat @ x0
    side = np.where(val > hi - 0.02 * span, 1, np.where(val < lo + 0.02 * span, -1, 0)).astype(np.int8)
    side[eq] = 2
    tol = 1e-3 * span
    wpen = 1e8
    log = []
    prof = x0
    escalated = False
    for it in range(30):
        act = np.flatnonzero(side)
        ca = cmat[act]
        bnd = np.where(side[act] == 2, 0.0, np.where(side[act] > 0, hi[act], lo[act]))
        prof = spsolve((base + wpen * (ca.T @ ca)).tocsc(), rhs0 + wpen * (ca.T @ bnd))
        val = cmat @ prof
        add_hi = (side == 0) & (val > hi + tol)
        add_lo = (side == 0) & (val < lo - tol)
        rel = np.zeros_like(add_hi)
        if it % 3 == 2:
            rel = ((side == 1) & (val < hi - 10 * tol)) | ((side == -1) & (val > lo + 10 * tol))
        log.append([it, int(len(act)), int(add_hi.sum() + add_lo.sum()), int(rel.sum())])
        print("polish", log[-1], flush=True)
        if not add_hi.any() and not add_lo.any() and not rel.any():
            held = side != 0
            over = np.maximum(val - hi, lo - val)[held & ~eq]
            if not escalated and over.size and over.max() > 1e-4:
                wpen *= 100.0
                escalated = True
                continue
            break
        side[add_hi] = 1
        side[add_lo] = -1
        side[rel] = 0
    return prof, log


def road_profiles(h, water, v29, report):
    """Profiles for the whole network as one quadratic programme, solved by a primal active set.

    Variables: one height per 1 m station; chain ends at the same point share one variable (junctions).
    Objective: terrain (smoothed) at dry stations, nothing at bridge/ford reserves, V29 near the Narva bridge;
    second differences along each chain; equal heights between each station and the nearest station of every
    other chain within 25 m (their 12.6 m platforms touch, so both must describe one surface).
    Constraints: grade <= road_grade_max and curvature <= road_curvature_max outside the Narva zone, height >=
    the dry floor. Violated rows enter the active set as stiff penalties; rows the solution leaves are released.
    """
    from scipy.sparse import coo_matrix, vstack as svstack
    chains = road_chains()
    wd = distance_transform_edt(~water) * 6
    var_of_end, coords, chain_vars, chain_glim = {}, [], [], []

    def var(xy, key=None):
        if key is not None and key in var_of_end:
            return var_of_end[key]
        coords.append(xy)
        idx = len(coords) - 1
        if key is not None:
            var_of_end[key] = idx
        return idx

    for c in chains:
        if len(c) < 2:
            continue
        station = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]
        if station[-1] <= 0:
            continue
        s = np.linspace(0, station[-1], max(2, int(np.ceil(station[-1])) + 1))
        q = np.column_stack([np.interp(s, station, c[:, d]) for d in (0, 1)])
        ids = [var(q[0], tuple(np.round(q[0], 1)))] + [var(p) for p in q[1:-1]] + [var(q[-1], tuple(np.round(q[-1], 1)))]
        w = P["road_turn_window_m"]
        qa = np.column_stack([np.interp(np.clip(s - w, 0, station[-1]), station, c[:, d]) for d in (0, 1)])
        qb = np.column_stack([np.interp(np.clip(s + w, 0, station[-1]), station, c[:, d]) for d in (0, 1)])
        u, v = q - qa, qb - q
        nu, nv = np.linalg.norm(u, axis=1), np.linalg.norm(v, axis=1)
        ok = (nu > 0.5) & (nv > 0.5)
        cosang = np.where(ok, (u * v).sum(1) / np.maximum(nu * nv, 1e-9), 1.0)
        turn = np.arccos(np.clip(cosang, -1, 1))
        radius = np.where(turn > 1e-6, w / np.maximum(turn, 1e-6), 1e9)
        chain_vars.append((np.asarray(ids), np.diff(s)))
        # Bends tighter than the platform half-width fan the inside vertices over many stations: keep them flat.
        per_r = np.where(radius >= P["road_tight_radius_m"], P["road_grade_per_radius"], P["road_grade_per_radius_tight"])
        chain_glim.append(np.minimum(P["road_grade_max"], per_r * radius))
    xy = np.asarray(coords)
    n = len(xy)
    chains_of = [[] for _ in range(n)]
    for k, (ids, _) in enumerate(chain_vars):
        for i in ids[1:-1]:
            chains_of[i] = [k]
        for i in (ids[0], ids[-1]):
            if k not in chains_of[i]:
                chains_of[i].append(k)
    owner = np.array([cs[0] for cs in chains_of])
    shared = np.array([len(cs) > 1 for cs in chains_of])

    # Coupling: station <-> nearest station of each other chain within road_couple_m.
    pairs = cKDTree(xy).query_pairs(r=P["road_couple_m"], output_type="ndarray")
    if len(pairs):
        keep = np.array([not (set(chains_of[a]) & set(chains_of[b])) for a, b in pairs])
        pairs = pairs[keep]
    dist = np.hypot(*(xy[pairs[:, 0]] - xy[pairs[:, 1]]).T)
    a = np.r_[pairs[:, 0], pairs[:, 1]]
    b = np.r_[pairs[:, 1], pairs[:, 0]]
    d = np.r_[dist, dist]
    order = np.lexsort((d, owner[b], a))
    a, b, d = a[order], b[order], d[order]
    first = np.r_[True, (a[1:] != a[:-1]) | (owner[b][1:] != owner[b][:-1])] if len(a) else np.zeros(0, bool)
    cpl = np.unique(np.sort(np.column_stack([a[first], b[first]]), axis=1), axis=0) if len(a) else np.zeros((0, 2), int)
    report["road_coupled_pairs"] = int(len(cpl))
    report["road_shared_ends"] = int(shared.sum())

    hs = gaussian_filter(h, 1.5)
    t = tri_sample(hs, xy[:, 0], xy[:, 1])
    rr = np.clip(np.rint((12282 - xy[:, 1]) / 6).astype(int), 0, N - 1)
    cc = np.clip(np.rint(xy[:, 0] / 6).astype(int), 0, N - 1)
    dry = wd[rr, cc] > P["road_reserve_water_m"]
    dn = np.hypot(xy[:, 0] - NARVA[0], xy[:, 1] - NARVA[1])
    near_narva = dn <= P["narva_radius_m"] + P["narva_blend_m"]
    v29s = tri_sample(v29, xy[:, 0], xy[:, 1])
    causeway = ~dry & ~near_narva & (v29s >= 1.0)
    target = np.where(near_narva, v29s, np.where(causeway, np.maximum(v29s, P["dry_floor_m"] + 0.1),
                                                np.maximum(t, P["dry_floor_m"] + 0.1)))
    weight = np.where(near_narva, 1e4, np.where(causeway, 0.5, dry.astype(float))) + 1e-6
    report["road_causeway_stations"] = int(causeway.sum())

    ri, ci, vals = [], [], []
    g_rows, g_lim, k_rows, k_lim = [], [], [], []
    r = 0
    free = dn > P["narva_radius_m"] + P["narva_blend_m"] + 10.0
    for (ids, ds), glim in zip(chain_vars, chain_glim):
        for k in range(len(ids) - 2):
            ri += [r, r, r]
            ci += [ids[k], ids[k + 1], ids[k + 2]]
            vals += [1.0, -2.0, 1.0]
            r += 1
            if free[ids[k]] and free[ids[k + 1]] and free[ids[k + 2]]:
                k_rows.append((ids[k], ids[k + 1], ids[k + 2]))
                k_lim.append(P["road_curvature_max"] * (0.5 * (ds[k] + ds[k + 1])) ** 2)
        for k in range(len(ids) - 1):
            if free[ids[k]] and free[ids[k + 1]]:
                g_rows.append((ids[k], ids[k + 1]))
                g_lim.append(min(glim[k], glim[k + 1]) * ds[k])
    d2 = coo_matrix((vals, (ri, ci)), shape=(r, n)).tocsr()
    m = len(cpl)
    cp = coo_matrix((np.r_[np.ones(m), -np.ones(m)], (np.r_[np.arange(m), np.arange(m)], np.r_[cpl[:, 0], cpl[:, 1]])),
                    shape=(m, n)).tocsr()
    base = (diags(weight) + P["road_alpha"] * (d2.T @ d2)).tocsr()
    rhs0 = weight * target

    # Constraint rows C x in [lo, hi]: grades, curvatures, dry floor.
    g_rows, k_rows = np.asarray(g_rows), np.asarray(k_rows)
    ng, nk = len(g_rows), len(k_rows)
    gm = coo_matrix((np.r_[-np.ones(ng), np.ones(ng)], (np.r_[np.arange(ng), np.arange(ng)], np.r_[g_rows[:, 0], g_rows[:, 1]])),
                    shape=(ng, n))
    km = coo_matrix((np.r_[np.ones(nk), -2 * np.ones(nk), np.ones(nk)],
                     (np.r_[np.arange(nk), np.arange(nk), np.arange(nk)], np.r_[k_rows[:, 0], k_rows[:, 1], k_rows[:, 2]])),
                    shape=(nk, n))
    fl = np.flatnonzero(~near_narva)
    fm = coo_matrix((np.ones(len(fl)), (np.arange(len(fl)), fl)), shape=(len(fl), n))
    cmat = svstack([gm, km, fm, cp]).tocsr()
    lo = np.r_[-np.asarray(g_lim), -np.asarray(k_lim), np.full(len(fl), P["dry_floor_m"] + 0.05), np.full(m, -P["road_couple_tol_m"])]
    hi = np.r_[np.asarray(g_lim), np.asarray(k_lim), np.full(len(fl), 1e9), np.full(m, P["road_couple_tol_m"])]
    eq = np.r_[np.zeros(ng + nk + len(fl), bool), np.ones(m, bool)]
    prof, log = admm_qp(base, -rhs0, cmat, lo, hi, eq=eq)
    prof, plog = polish(base, rhs0, cmat, lo, hi, eq, prof)
    report["road_polish_log"] = plog
    val = cmat @ prof
    over = np.maximum(val - hi, lo - val)
    report["road_admm_log"] = log[-4:]
    report["road_admm_iterations"] = log[-1][0]
    report["road_violation_max"] = {"grade_m": round(float(over[:ng].max()), 5),
                                    "curvature_m": round(float(over[ng:ng + nk].max()), 6),
                                    "floor_m": round(float(over[ng + nk:ng + nk + len(fl)].max()), 4),
                                    "coupling_m": round(float(over[ng + nk + len(fl):].max()), 5) if m else 0.0}
    seg_len = np.concatenate([ds for ids, ds in chain_vars])[np.concatenate(
        [[free[ids[k]] and free[ids[k + 1]] for k in range(len(ids) - 1)] for ids, _ in chain_vars])]
    report["road_grade_limited_by_bends"] = int((np.asarray(g_lim) < P["road_grade_max"] * seg_len - 1e-9).sum())
    report["road_profile_grade_max"] = round(float((np.abs(prof[g_rows[:, 1]] - prof[g_rows[:, 0]]) / seg_len).max()), 4)
    report["road_coupling_mismatch_max_m"] = round(float(np.abs(prof[cpl[:, 0]] - prof[cpl[:, 1]]).max()), 4) if m else 0.0
    report["road_chains"] = len(chain_vars)
    report["road_stations"] = int(n)

    # Dense centre lines (every <= road_dense_m) for the platform: linear profile between stations.
    dx, dz, dp = [], [], []
    for ids, ds in chain_vars:
        k = np.maximum(np.ceil(ds / P["road_dense_m"]).astype(int), 1)
        seg = np.repeat(np.arange(len(ds)), k)
        frac = np.concatenate([np.arange(v) / v for v in k])
        a0, a1 = ids[seg], ids[seg + 1]
        dx.append(xy[a0, 0] + frac * (xy[a1, 0] - xy[a0, 0]))
        dz.append(xy[a0, 1] + frac * (xy[a1, 1] - xy[a0, 1]))
        dp.append(prof[a0] + frac * (prof[a1] - prof[a0]))
        dx.append(xy[ids[-1:], 0])
        dz.append(xy[ids[-1:], 1])
        dp.append(prof[ids[-1:]])
    dense = np.column_stack([np.concatenate(dx), np.concatenate(dz)])
    np.savez(os.path.join(OUT, "road_v30_profile.npz"), xy=xy, prof=prof, owner=owner, dry=dry, target=target,
             couple=cpl, chain_ids=np.concatenate([ids for ids, _ in chain_vars]),
             chain_len=np.array([len(ids) for ids, _ in chain_vars]))
    return dense, np.concatenate(dp), xy[~dry]


def pre_roads(h, high, w, water, cls, level, rep):
    """Steps 1-3 (dimples, dropped V29 water, valley envelopes); cached because the road step is iterated."""
    # 1. Dimples in the high zones.
    near_water = binary_dilation(water | w["excess"], iterations=int(P["dimple_water_clear_m"] / 6))
    zone = (high > P["high_min"]) & ~near_water
    filled = fill_depressions(h, ~zone)
    dimple = zone & (filled - h > P["dimple_min_m"])
    h = h + np.where(dimple, filled - h, 0.0)
    region = binary_dilation(dimple, iterations=2) & zone
    h[region] = gaussian_filter(h, 1.0)[region]  # round off the flat spill surface
    rep["dimple_vertices"] = int(dimple.sum())

    # 2. V29 water that the new design drops.
    excess = w["excess"]
    if excess.any():
        h = laplace_fill(h, excess)
        floor = np.maximum(P["dry_floor_m"], np.nan_to_num(w["level_near"].astype(float), nan=0.0) + P["bank_margin_m"])
        h[excess] = np.maximum(h[excess], floor[excess])
    rep["excess_filled_vertices"] = int(excess.sum())

    # 3. Valley envelopes beside rivers, streams and navigable reaches.
    dist_w, idx = distance_transform_edt(~water, sampling=6.0, return_indices=True)
    near_cls = cls[idx[0], idx[1]]
    near_lv = level[idx[0], idx[1]]
    lowered = 0
    for code, deg in P["valley_deg"].items():
        m = (~water) & (near_cls == code) & (dist_w <= P["valley_reach_m"]) & np.isfinite(near_lv)
        env = near_lv + P["valley_freeboard_m"] + dist_w * np.tan(np.radians(deg))
        cut = m & (h > env)
        h[cut] = env[cut]
        lowered += int(cut.sum())
    rep["valley_lowered_vertices"] = lowered
    return h


def main():
    rep = {"params": {k: (v if not isinstance(v, dict) else {str(a): b for a, b in v.items()}) for k, v in P.items()}}
    relief = np.load(os.path.join(R, "tests", "relief_v30", "relief_v30_mix.npz"))
    h = relief["new"].astype("float64")
    high = relief["high"].astype("float64")
    w = np.load(os.path.join(V30, "water_v30.npz"))
    cls, level = w["cls"], w["level"].astype("float64")
    water = cls > 0
    with rasterio.open(os.path.join(R, "tests", "regional_road_network_v29", "baltic_road_network_v29.asc")) as ds:
        v29 = ds.read(1).astype("float64")
    x, z = grid_xz()

    pre = os.path.join(OUT, "pre_roads_v30.npz")
    if "--reuse-pre" in sys.argv and os.path.exists(pre):
        cached = np.load(pre)
        h = cached["h"]
        rep.update(json.loads(str(cached["rep"])))
    else:
        h = pre_roads(h, high, w, water, cls, level, rep)
        np.savez(pre, h=h, rep=json.dumps({k: v for k, v in rep.items() if k != "params"}))
    dist_w, idx = distance_transform_edt(~water, sampling=6.0, return_indices=True)
    near_lv = level[idx[0], idx[1]]

    # 4. Roads.
    pts, prof, reserve_pts = road_profiles(h, water, v29, rep)
    tree = cKDTree(pts)
    print('platform', len(pts), flush=True)
    land = ~water
    sel = np.flatnonzero(land.ravel())
    dist, j = tree.query(np.column_stack([x.ravel()[sel], z.ravel()[sel]]), distance_upper_bound=P["road_platform_m"] + P["road_reach_m"])
    hit = np.isfinite(dist)
    flat_h = h.ravel().copy()
    platform = np.zeros(N * N, dtype=bool)
    sel_hit, d_hit, ph = sel[hit], dist[hit], prof[j[hit]]
    plat = d_hit <= P["road_platform_m"]
    flat_h[sel_hit[plat]] = ph[plat]
    platform[sel_hit[plat]] = True
    emb = ~plat
    tanv = np.tan(np.radians(P["road_slope_deg"]))
    lim = (d_hit[emb] - P["road_platform_m"]) * tanv
    orig = flat_h[sel_hit[emb]]
    flat_h[sel_hit[emb]] = ph[emb] + np.clip(orig - ph[emb], -lim, lim)
    h = flat_h.reshape(N, N)
    platform = platform.reshape(N, N)
    reserve = np.zeros((N, N), dtype=bool)
    if len(reserve_pts):
        rr = np.clip(np.rint((12282 - reserve_pts[:, 1]) / 6).astype(int), 0, N - 1)
        cc = np.clip(np.rint(reserve_pts[:, 0] / 6).astype(int), 0, N - 1)
        reserve[rr, cc] = True
        reserve = binary_dilation(reserve, iterations=2)
    rep["road_platform_vertices"] = int(platform.sum())
    rep["road_reserve_vertices"] = int(reserve.sum())

    # 5. Water beds and banks.
    edge = np.maximum(w["dist_bank"].astype(float) - 6.0, 0.0)
    for code, dmax in P["depth_max"].items():
        if code == 1:
            continue
        gain = 1.0 if code in (2, 3) else P["bed_gain_per_m"]  # navigable and lakes: full depth from the first interior vertex
        depth = P["bed_edge_m"] + gain * edge
        m = cls == code
        bed = level - np.minimum(depth, dmax)
        h[m] = np.minimum(h[m], bed[m])
    depth = P["bed_edge_m"] + P["bed_gain_per_m"] * edge
    m = cls == 1  # sea: keep the deeper existing sea floor, only the shallow fringe is cut (at most 2 m deep)
    h[m] = np.minimum(h[m], level[m] - np.minimum(depth[m], P["depth_max"][1]))
    m = cls == 4
    h[m] = np.minimum(h[m], np.maximum(P["delta_bed"], level[m] - depth[m]))
    # Smooth shores along inland outlines (signed distance sd, + on land); the fixed bank stays for the sea.
    sd = w["sd"].astype(float)
    shaped = np.isfinite(sd) & (np.abs(np.nan_to_num(sd, nan=1e9)) <= P["shore_reach_m"])
    wet_in = shaped & water
    shore_depth = np.clip(P["shore_slope"] * np.abs(sd[wet_in]), P["shore_min_depth_m"], P["shore_max_depth_m"])
    h[wet_in] = np.minimum(h[wet_in], level[wet_in] - shore_depth)
    shore_land = shaped & ~water & np.isfinite(near_lv)
    shore_floor = near_lv + P["shore_freeboard_m"] + P["shore_slope"] * np.clip(np.nan_to_num(sd, nan=0.0), 0, None)
    h[shore_land] = np.maximum(h[shore_land], shore_floor[shore_land])
    # Smooth sea coast (sd_sea, + on land): sea bed below the coast, beach rising to the dry floor.
    sds = w["sd_sea"].astype(float)
    coast = np.isfinite(sds) & (np.abs(np.nan_to_num(sds, nan=1e9)) <= P["shore_reach_m"])
    m = coast & (cls == 1)
    h[m] = np.minimum(h[m], level[m] - np.clip(P["beach_slope"] * np.abs(sds[m]), 0.15, 2.0))
    beach_floor = 0.75 + P["beach_freeboard_m"] + P["beach_slope"] * np.clip(np.nan_to_num(sds, nan=0.0), 0, None)
    beach = coast & ~water & (beach_floor < P["dry_floor_m"])
    shaped = shaped | (coast & ~water)
    bank = (~water) & (dist_w <= P["bank_radius_m"]) & np.isfinite(near_lv) & ~shaped
    h[bank] = np.maximum(h[bank], near_lv[bank] + P["bank_margin_m"])
    dry = ~water
    land_floor = np.where(beach, beach_floor, P["dry_floor_m"])
    h[dry] = np.maximum(h[dry], land_floor[dry])
    rep["beach_vertices"] = int(beach.sum())
    rep["bank_vertices"] = int(bank.sum())

    # 5b. Consistency with the pond pieces (v30_common.cell_planes): water corners under every adjacent plane,
    #     land corners over it, so a plane never ends in the open and never hides under its own bed.
    plane = cell_planes(cls, level)
    pmin, pmax = vertex_plane_bounds(plane)
    wv = water & np.isfinite(pmin)
    h[wv] = np.minimum(h[wv], pmin[wv] - P["piece_depth_m"])
    lp = (~water) & np.isfinite(pmax)
    piece_floor = np.where(lp, pmax + P["piece_freeboard_m"], -np.inf)
    h[lp] = np.maximum(h[lp], piece_floor[lp])
    land_floor = np.maximum(land_floor, piece_floor)
    rep["piece_consistency"] = {"water_vertices": int(wv.sum()), "land_vertices": int(lp.sum())}

    # 6. Narva crossing: V29 exact inside 480 m, blended to 600 m.
    dn = np.hypot(x - NARVA[0], z - NARVA[1])
    t = ease((dn - P["narva_radius_m"]) / P["narva_blend_m"])
    h = v29 * (1 - t) + h * t
    narva = dn <= P["narva_radius_m"]
    h[narva] = v29[narva]

    # 7. Slope cap with water, platforms and Narva fixed. High land is lowered towards its neighbours but never below
    #    the dry floor or, within the bank radius, below the water level + bank margin; land left too far below a
    #    neighbour is raised (embankments round perched lakes and road fills). Raising runs last, so where two fixed
    #    vertices are too far apart the slope stays on the low side.
    fixed = water | platform | narva
    fixed_vals = h.copy()
    floor = np.where(dry, land_floor, -np.inf)
    floor = np.where(bank, np.maximum(floor, near_lv + P["bank_margin_m"]), floor)
    floor = np.where(shore_land, np.maximum(floor, shore_floor), floor)
    cap = P["slope_cap_m"]

    def settle(h, lower):
        for it in range(4096):
            nh = h.copy()
            if lower:
                nh[:, 1:] = np.minimum(nh[:, 1:], h[:, :-1] + cap)
                nh[:, :-1] = np.minimum(nh[:, :-1], h[:, 1:] + cap)
                nh[1:, :] = np.minimum(nh[1:, :], h[:-1, :] + cap)
                nh[:-1, :] = np.minimum(nh[:-1, :], h[1:, :] + cap)
                nh = np.maximum(nh, floor)
            else:
                nh[:, 1:] = np.maximum(nh[:, 1:], h[:, :-1] - cap)
                nh[:, :-1] = np.maximum(nh[:, :-1], h[:, 1:] - cap)
                nh[1:, :] = np.maximum(nh[1:, :], h[:-1, :] - cap)
                nh[:-1, :] = np.maximum(nh[:-1, :], h[1:, :] - cap)
            nh[fixed] = fixed_vals[fixed]
            delta = float(np.max(np.abs(nh - h)))
            h = nh
            if delta < 1e-4:
                return h, it + 1
        return h, -1

    h = np.maximum(h, np.where(fixed, -np.inf, floor))
    h, it_low = settle(h, True)    # carve high land first (cliffs left by envelopes or fills)
    h, it_up = settle(h, False)    # then lift land left below a fixed or floored neighbour
    it = it_low
    rep["slope_cap_iterations"] = [it_low, it_up]
    rep["slope_cap_converged"] = it_low > 0 and it_up > 0
    # 8. Local repair of road platforms against the road gate (Narva zone fixed).
    from repair_roads_v30 import repair
    h, rrep = repair(h, water, rounds=4, fixed=narva)
    rep["road_repair"] = rrep["rounds"]
    # 9. The repair moved platform vertices by centimetres: settle the land around them once more.
    fixed_vals = h.copy()
    h, it_low2 = settle(h, True)
    h, it_up2 = settle(h, False)
    rep["slope_resettle_iterations"] = [it_low2, it_up2]
    assert np.isfinite(h).all() and np.array_equal(h[narva], v29[narva])
    h32 = h.astype("float32")
    np.savez_compressed(os.path.join(OUT, "terrain_v30.npz"), heights=h32, cls=cls, level=w["level"], platform=platform,
                        reserve=reserve, narva=narva, water=water, beach=beach)
    rep["height_range"] = [round(float(h32.min()), 2), round(float(h32.max()), 2)]
    # ASC for Terrain Builder, same header and float32 text as V29 (rows north to south, x = 200000 + 6c).
    asc = os.path.join(OUT, "baltic_terrain_v30.asc")
    with open(asc, "w", encoding="ascii", newline="\n") as f:
        f.write("ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n")
        np.savetxt(f, h32, fmt="%.9g")
    with rasterio.open(asc) as ds:
        assert np.array_equal(ds.read(1), h32), "ASC round trip"
    import hashlib
    rep["asc_sha256"] = hashlib.sha256(open(asc, "rb").read()).hexdigest()
    with open(os.path.join(OUT, "build_v30.json"), "wb") as f:
        f.write(json.dumps(rep, indent=1).encode("utf-8"))
    print(json.dumps({k: v for k, v in rep.items() if k != "params"}, indent=1))


if __name__ == "__main__":
    main()

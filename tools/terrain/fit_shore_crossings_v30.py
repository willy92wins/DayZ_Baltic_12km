"""Shorelines on the designed outline (BALTIC-007): terrain that meets the water where the outline crosses each edge.

The visible shore of a pond plane is where the native terrain (6 m grid, NW-SE diagonals) crosses the plane. Today
land touching water sits ~0.45 m above it and the first wet vertex ~0.28 m below, so the crossing keeps a fixed
fraction of every wet-land edge and draws the 6 m grid. Here, for every native edge between a wet vertex of a pond
class (2, 3, 5, 6, 7) and a land vertex whose signed distances to the designed outline agree in sign (sd/sd_sea of
tests/terrain_v30/water_v30.npz, the fields the V30 builder used), the terrain interpolated at the outline crossing
t* = |d_w| / (|d_w| + d_l) must equal the visible water there: the highest plane of the edge's cells, or the channel
piece surface where the vanilla channel fit (--channels) replaced the planes. One bounded sparse least-squares solve
over the edge ends, close to the current heights (weight --reg). The tidal sea and delta keep their coast.
Bounds keep every existing gate and protection: wet <= level - 0.101, <= adjacent planes - 0.0501 and <= a piece
surface - 0.0501; land >= 1.4001, >= nearest level + 0.0501 within 8.5 m, >= adjacent planes + 0.0501 and >= a
piece surface + 0.0501 under its footprint (this also lifts land under piece overhangs); groove vertices never rise
(--groove-may-rise lets them rise up to the depth bound, --groove-min-depth D up to level - D; exploratory).
Fixed exactly as tools/terrain/finish_shores_v30.py
(24 m channel corridors with a vertex margin, road platforms and reserves, Narva within 620 m, the nature envelope,
the map border) plus the beach and everything within 24 m of the 13 frozen shallow points of the wave margin. Then edits that make a land face steeper than 35 degrees (or than it was) are undone,
and so are the triangles of frozen dry samples that would lose their 0.05 m margin. Heights only.
Usage: fit_shore_crossings_v30.py --terrain <npz> --out <dir> [--channels <fit dir>] [--sea-cut 0.80] [--reg 0.1]
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import time

import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.optimize import lsq_linear
from scipy.sparse import coo_matrix

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'terrain'))
sys.path.insert(0, str(ROOT / 'tools' / 'water'))
from v30_common import N, POND_CLASSES, R, cell_planes, grid_xz, tri_sample, vertex_plane_bounds  # noqa: E402
from finish_shores_v30 import discard_steeper_land_faces, protect_corridors  # noqa: E402

P = dict(wet_min_depth_m=0.101, piece_depth_m=0.0501, freeboard_m=0.0501, bank_radius_m=8.5, dry_floor_m=1.4001,
         wet_raise_max_m=1.5, wet_lower_max_m=1.0, dry_raise_max_m=0.6, dry_lower_max_m=3.0, narva_radius_m=620.0,
         shallow_guard_m=24.0, dry_sample_margin_m=0.05001)
WATER = Path(R) / 'tests/terrain_v30/water_v30.npz'
NATURE = Path(R) / 'tests/regional_outline_v1/reference.npz'
SHALLOW = Path('E:/DayZ-Baltic-Build/v30-water-temporal-v2/reference.json')
DRY = Path('E:/DayZ-Baltic-Build/v30-continuity-dedup-package/runtime-fixture/reference.json')
SHALLOW_IDS = {362, 363, 416, 524, 548, 642, 765, 882, 1176, 1185, 1224, 1274, 1312}
EDGES = ((0, 1), (1, 0), (1, 1))      # native edges: east, south, NW-SE diagonal


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def edge_cells(r, c, dr, dc):
    """Cells sharing the edge (r,c)-(r+dr,c+dc): two for the axis edges, one for the diagonal."""
    if (dr, dc) == (0, 1):
        return [(r - 1, c), (r, c)]
    if (dr, dc) == (1, 0):
        return [(r, c - 1), (r, c)]
    return [(r, c)]


def channel_surface(fit_dir, planes):
    """Vanilla channel fit: surface at every vertex under a piece (NaN elsewhere); removed reach cells lose their plane."""
    import engine_water_model as ewm
    axes = json.loads((fit_dir / 'axes.json').read_text(encoding='utf-8'))
    pieces = [ewm.Piece(p['type'], p['matrix']) for reach in axes.values() for p in reach['pieces']]
    for reach in axes.values():
        for r, c in reach['removed_cells']:
            planes[r, c] = np.nan
    surf = np.full((N, N), np.nan)
    for p in pieces:
        c0, c1 = int(max(np.floor(p.box[0] / 6), 0)), int(min(np.ceil(p.box[2] / 6), N - 1))
        r0, r1 = int(max(np.floor((12282 - p.box[3]) / 6), 0)), int(min(np.ceil((12282 - p.box[1]) / 6), N - 1))
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                v = p.visual(6.0 * c, 12282.0 - 6.0 * r)
                if v is not None and not (v[0] <= surf[r, c]):
                    surf[r, c] = v[0]
    return pieces, surf, len(pieces)


def crossing_offsets(h, ew, el, t, wl, length):
    """Distance (m) along each edge between the terrain's crossing of its water level and the outline crossing;
    NaN where the terrain does not cross (land under the water or wet above it)."""
    hw, hl = h.ravel()[ew], h.ravel()[el]
    ok = (hw < wl) & (hl > wl)
    ta = np.where(ok, (wl - hw) / np.where(ok, hl - hw, 1.0), np.nan)
    return np.abs(ta - t) * length


def stats(v):
    v = v[np.isfinite(v)]
    return {'n': int(v.size), **({k: round(float(np.percentile(v, q)), 3) for k, q in
                                  (('p50', 50), ('p90', 90), ('p99', 99), ('max', 100))} if v.size else {})}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--terrain', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--channels', type=Path)
    ap.add_argument('--sea-cut', type=float, default=0.80)
    ap.add_argument('--reg', type=float, default=0.1)
    ap.add_argument('--water-v30', type=Path, default=WATER)
    ap.add_argument('--nature', type=Path, default=NATURE)
    ap.add_argument('--shallow-reference', type=Path, default=SHALLOW)
    ap.add_argument('--dry-reference', type=Path, default=DRY)
    ap.add_argument('--max-iter', type=int, default=1000)
    ap.add_argument('--dry-raise-max', type=float, default=P['dry_raise_max_m'])
    ap.add_argument('--near-min-depth', type=float, default=None,
                    help='EXPLORATORY (breaks the 0.10 m depth gate): minimum depth of wet vertices within --near-dist of the outline')
    ap.add_argument('--near-dist', type=float, default=2.0)
    ap.add_argument('--corridor-margin', type=int, choices=(0, 1), default=1,
                    help="1 keeps the one-vertex margin of finish_shores round the 24 m corridors fixed; 0 fixes only their exact faces")
    ap.add_argument('--groove-may-rise', action='store_true',
                    help='EXPLORATORY: centre-line (groove) vertices may rise up to the wet depth bound')
    ap.add_argument('--groove-min-depth', type=float, default=None,
                    help='EXPLORATORY: groove vertices may rise, but not above level minus this depth (m)')
    ap.add_argument('--sd-override', type=Path, default=None,
                    help='npz whose sd replaces the outline distance of water_v30 (e.g. with the Narva zone filled)')
    ap.add_argument('--narva-core-m', type=float, default=None,
                    help='EXPLORATORY: fix only this radius round the Narva bridge instead of the narva mask and 620 m')
    ap.add_argument('--free-corridor-box', default=None,
                    help='xmin,zmin,xmax,zmax: the 24 m corridor protection does not apply inside this box')
    ap.add_argument('--levee-cap', type=float, default=None,
                    help='a raised shore land vertex stays within this of its highest outer land neighbour (m)')
    a = ap.parse_args()
    assert not a.out.exists(), 'fresh output required'
    t0 = time.time()
    t = dict(np.load(a.terrain))
    w = np.load(a.water_v30)
    h0 = t['heights'].astype(float)
    cls, level = t['cls'], t['level'].astype(float)
    wet, dry = cls > 0, cls == 0
    planes = cell_planes(cls, level, sea_cut=a.sea_cut)
    corridor_exact, corridor, entries, _ = protect_corridors(planes)
    if a.corridor_margin == 0:
        corridor = corridor_exact
    if a.free_corridor_box:
        bx0, bz0, bx1, bz1 = (float(v) for v in a.free_corridor_box.split(','))
        gx, gz = grid_xz()
        inbox = (gx >= bx0) & (gx <= bx1) & (gz >= bz0) & (gz <= bz1)
        corridor_exact, corridor = corridor_exact & ~inbox, corridor & ~inbox
    surf, n_pieces = np.full((N, N), np.nan), 0
    if a.channels:
        _, surf, n_pieces = channel_surface(a.channels, planes)
    pmin, pmax = vertex_plane_bounds(planes)
    x, z = grid_xz()
    nature = np.load(a.nature)['reserve'].astype(bool)
    fixed = corridor | t['platform'] | t['reserve'] | nature | t['beach']
    if a.narva_core_m is None:
        fixed |= t['narva'] | (np.hypot(x - 2417.1428225906, z - 6889.8850822322) <= P['narva_radius_m'])
    else:
        fixed |= np.hypot(x - 2417.1428225906, z - 6889.8850822322) <= a.narva_core_m
    fixed |= (x < 12) | (z < 12) | (x > 12270) | (z > 12270)
    sd, sea_sd = w['sd'].astype(float), w['sd_sea'].astype(float)
    if a.sd_override is not None:
        sd = np.load(a.sd_override)['sd'].astype(float)
    use_sea = np.isfinite(sea_sd) & (~np.isfinite(sd) | (np.abs(sea_sd) < np.abs(sd)))
    signed = np.where(use_sea, sea_sd, sd)

    # wet-land edges of pond-class water with a visible surface (plane or channel piece) at the outline crossing
    ew, el, et, ewl, elen, ekind = [], [], [], [], [], []
    for dr, dc in EDGES:
        ra, ca = np.meshgrid(np.arange(N - dr), np.arange(N - dc), indexing='ij')
        rb, cb = ra + dr, ca + dc
        wa, wb = wet[ra, ca], wet[rb, cb]
        m = wa ^ wb
        ra, ca, rb, cb, wa = ra[m], ca[m], rb[m], cb[m], wa[m]
        rw, cw = np.where(wa, ra, rb), np.where(wa, ca, cb)
        rl, cl = np.where(wa, rb, ra), np.where(wa, cb, ca)
        dw, dl = signed[rw, cw], signed[rl, cl]
        ok = np.isin(cls[rw, cw], POND_CLASSES) & np.isfinite(dw) & np.isfinite(dl) & (dw <= 0) & (dl >= 0) & (dl - dw > 1e-6)
        rw, cw, rl, cl, dw, dl, ra, ca = rw[ok], cw[ok], rl[ok], cl[ok], dw[ok], dl[ok], ra[ok], ca[ok]
        tt = -dw / (dl - dw)
        wl = np.full(len(rw), -np.inf)
        for k, (r_, c_) in enumerate(edge_cells(ra, ca, dr, dc)):
            inside = (r_ >= 0) & (r_ < N - 1) & (c_ >= 0) & (c_ < N - 1)
            pv = np.full(len(rw), np.nan)
            pv[inside] = planes[r_[inside], c_[inside]]
            wl = np.fmax(wl, pv)
        # channel surface at the crossing: bilinear between the two ends' surfaces where both are under a piece
        sw, sl = surf[rw, cw], surf[rl, cl]
        sc = np.where(np.isfinite(sw) & np.isfinite(sl), sw + tt * (sl - sw), np.where(np.isfinite(sw), sw, sl))
        kind = np.where(np.isfinite(sc) & ~(sc < wl), 'channel', 'plane')
        wl = np.fmax(wl, sc)
        good = np.isfinite(wl)
        ew.append((rw * N + cw)[good]); el.append((rl * N + cl)[good]); et.append(tt[good]); ewl.append(wl[good])
        elen.append(np.full(good.sum(), 6.0 * (2 ** 0.5 if dr and dc else 1.0))); ekind.append(kind[good])
    ew, el, et, ewl, elen, ekind = [np.concatenate(v) for v in (ew, el, et, ewl, elen, ekind)]

    # bounds
    dist, nearest = distance_transform_edt(dry, sampling=6.0, return_indices=True)
    near_level = level[nearest[0], nearest[1]]
    land_lb = np.full((N, N), P['dry_floor_m'])
    land_lb = np.where(dist <= P['bank_radius_m'], np.fmax(land_lb, near_level + P['freeboard_m']), land_lb)
    land_lb = np.fmax(land_lb, pmax + P['freeboard_m'])
    land_lb = np.fmax(land_lb, surf + P['freeboard_m'])
    wet_ub = level - P['wet_min_depth_m']
    wet_ub = np.fmin(wet_ub, pmin - P['piece_depth_m'])
    wet_ub = np.fmin(wet_ub, surf - P['piece_depth_m'])
    if a.near_min_depth is not None:
        near = wet & np.isfinite(signed) & (np.abs(signed) <= a.near_dist)
        relaxed = np.fmin(np.fmin(level - a.near_min_depth, pmin - 0.0201), surf - 0.0201)
        wet_ub = np.where(near, relaxed, wet_ub)
    shallow = json.loads(a.shallow_reference.read_text())['points']
    shallow = [p for p in shallow if p.get('role') == 'frozen_shallow_failure' and p['id'] in SHALLOW_IDS]
    assert len(shallow) == 13
    guard = np.zeros((N, N), bool)
    for p in shallow:
        guard |= np.hypot(x - p['x'], z - p['z']) <= P['shallow_guard_m']
    fixed |= guard        # the wave-margin work owns these 13 neighbourhoods (land and water)
    no_raise = wet & w['groove'] & (not a.groove_may_rise) & (a.groove_min_depth is None)
    groove_cap = wet & w['groove'] & (a.groove_min_depth is not None)

    overhang = dry & ~fixed & np.isfinite(surf) & (h0 < surf + P['freeboard_m']) & ~(signed < 0)
    var_ids = np.unique(np.concatenate([ew, el, np.flatnonzero(overhang)]))
    var_ids = var_ids[~fixed.ravel()[var_ids]]
    col = -np.ones(N * N, np.int64)
    col[var_ids] = np.arange(len(var_ids))
    hv = h0.ravel()[var_ids]
    is_wet = wet.ravel()[var_ids]
    lb = np.where(is_wet, hv - P['wet_lower_max_m'], np.maximum(land_lb.ravel()[var_ids], hv - P['dry_lower_max_m']))
    ub = np.where(is_wet, np.minimum(wet_ub.ravel()[var_ids], hv + P['wet_raise_max_m']), hv + a.dry_raise_max)
    if a.levee_cap is not None:
        # no new ridge along the shore: a land variable rises at most to its highest outer land neighbour + cap
        outer = dry & ~np.isin(np.arange(N * N), var_ids).reshape(N, N)
        hp = np.pad(np.where(outer, h0, -np.inf), 1, constant_values=-np.inf)
        top = np.max(np.stack([hp[1 + dr:1 + dr + N, 1 + dc:1 + dc + N] for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                               if dr or dc]), axis=0).ravel()[var_ids]
        cap = np.where(np.isfinite(top), np.maximum(hv, top + a.levee_cap), np.inf)
        ub = np.where(~is_wet, np.minimum(ub, cap), ub)
    ub = np.where(is_wet & no_raise.ravel()[var_ids], np.minimum(ub, hv), ub)
    if a.groove_min_depth is not None:
        gcap = np.maximum(hv, level.ravel()[var_ids] - a.groove_min_depth)
        ub = np.where(is_wet & groove_cap.ravel()[var_ids], np.minimum(ub, gcap), ub)
    ub = np.where(~is_wet, np.maximum(ub, lb), ub)          # land forced up to its floor (overhangs)
    lb = np.where(is_wet, np.minimum(lb, ub), lb)           # wet forced down below its ceiling
    # lsq_linear needs lb < ub strictly: a vertex pinned by its bounds keeps a 1e-6 m slack on its free side
    tight = ub - lb < 1e-6
    ub = np.where(tight & ~is_wet, lb + 1e-6, ub)
    lb = np.where(tight & is_wet, ub - 1e-6, lb)
    assert np.all(lb < ub)

    # system: crossing rows + regularisation rows
    cw_, cl_ = col[ew], col[el]
    rows = np.arange(len(ew))
    b = ewl.copy()
    fixed_w, fixed_l = cw_ < 0, cl_ < 0
    b -= np.where(fixed_w, (1 - et) * h0.ravel()[ew], 0.0) + np.where(fixed_l, et * h0.ravel()[el], 0.0)
    use = ~(fixed_w & fixed_l)
    ri = np.concatenate([rows[use & ~fixed_w], rows[use & ~fixed_l]])
    ci = np.concatenate([cw_[use & ~fixed_w], cl_[use & ~fixed_l]])
    vi = np.concatenate([(1 - et)[use & ~fixed_w], et[use & ~fixed_l]])
    keep_rows = np.flatnonzero(use)
    remap = -np.ones(len(ew), np.int64)
    remap[keep_rows] = np.arange(len(keep_rows))
    ne = len(keep_rows)
    nv = len(var_ids)
    A = coo_matrix((np.concatenate([vi, np.full(nv, a.reg)]),
                    (np.concatenate([remap[ri], ne + np.arange(nv)]), np.concatenate([ci, np.arange(nv)]))),
                   shape=(ne + nv, nv)).tocsr()
    rhs = np.concatenate([b[keep_rows], a.reg * hv])
    t1 = time.time()
    sol = lsq_linear(A, rhs, bounds=(lb, ub), method='trf', lsmr_tol='auto', max_iter=a.max_iter, verbose=0)
    t2 = time.time()
    h1 = h0.copy()
    h1.ravel()[var_ids] = np.clip(sol.x, lb, ub)

    # undo steeper land faces, then frozen dry samples that would lose their margin (and recheck faces)
    h2, faces = discard_steeper_land_faces(h1, h0, cls)
    dry_pts = [p for p in json.loads(a.dry_reference.read_text())['points'] if p['kind'] == 'dry']
    dry_reverted = 0
    for _ in range(4):
        bad = []
        for p in dry_pts:
            plane = p['pond_plane_m'] if p['pond_plane_m'] is not None else 1.0
            if float(tri_sample(h2, p['x'], p['z'])) < plane + P['dry_sample_margin_m'] - 1e-7 and \
                    float(tri_sample(h0, p['x'], p['z'])) >= plane + P['dry_sample_margin_m'] - 1e-7:
                bad.append(p)
        if not bad:
            break
        for p in bad:
            c0, r0 = int(p['x'] // 6), int((12282 - p['z']) // 6)
            h2[r0:r0 + 2, c0:c0 + 2] = h0[r0:r0 + 2, c0:c0 + 2]
            dry_reverted += 1
        h2, faces = discard_steeper_land_faces(h2, h0, cls)
    h2 = h2.astype('float32').astype(float)

    # report
    changed = h2 != h0.astype('float32').astype(float)
    assert not np.any(changed & fixed), 'protected height changed'
    d = h2 - h0
    groups = {}
    for name, sel in (('all', np.ones(len(ew), bool)), ('channel', ekind == 'channel'),
                      *[(lab, (ekind == 'plane') & (cls.ravel()[ew] == code))
                        for code, lab in ((2, 'lake'), (3, 'navigable'), (5, 'river'), (6, 'stream'), (7, 'pond'))]):
        before = crossing_offsets(h0, ew[sel], el[sel], et[sel], ewl[sel], elen[sel])
        after = crossing_offsets(h2, ew[sel], el[sel], et[sel], ewl[sel], elen[sel])
        groups[name] = {'edges': int(sel.sum()), 'offset_m_before': stats(before), 'offset_m_after': stats(after),
                        'no_crossing_before': int(np.isnan(before).sum()), 'no_crossing_after': int(np.isnan(after).sum())}
    # what holds the remaining offsets (> 1 m): a fixed end, an end on its bound, or neither
    off = crossing_offsets(h2, ew, el, et, ewl, elen)
    big = ~(off <= 1.0)
    xs = np.full(N * N, np.nan); xs[var_ids] = h2.ravel()[var_ids]
    lbf = np.full(N * N, np.nan); lbf[var_ids] = lb
    ubf = np.full(N * N, np.nan); ubf[var_ids] = ub
    fw, fl = fixed.ravel()[ew], fixed.ravel()[el]
    w_at_ub = np.abs(xs[ew] - ubf[ew]) < 1e-3
    l_at_lb = np.abs(xs[el] - lbf[el]) < 1e-3
    limits = {'edges_over_1m': int(big.sum()), 'fixed_end': int((big & (fw | fl)).sum()),
              'wet_at_ceiling': int((big & ~(fw | fl) & w_at_ub).sum()),
              'land_at_floor': int((big & ~(fw | fl) & ~w_at_ub & l_at_lb).sum()),
              'unbound': int((big & ~(fw | fl) & ~w_at_ub & ~l_at_lb).sum())}
    over_before = int((dry & np.isfinite(surf) & (h0 < surf) & ~(signed < 0)).sum())
    over_after = int((dry & np.isfinite(surf) & (h2 < surf) & ~(signed < 0)).sum())
    # gate re-check on the final heights (edited vertices only; the rest is the source)
    gate = {
        'wet_too_shallow': int((changed & wet & (h2 > wet_ub + 1e-6)).sum()),
        'wet_raised_where_forbidden': int((changed & no_raise & (d > 1e-6)).sum()),
        'land_below_floor': int((changed & dry & (h2 < land_lb - 1e-6)).sum()),
    }
    a.out.mkdir(parents=True)
    dest = a.out / 'terrain_shore.npz'
    np.savez_compressed(dest, **{k: (h2.astype(t['heights'].dtype) if k == 'heights' else v) for k, v in t.items()})
    np.savez_compressed(a.out / 'masks.npz', changed=changed, fixed=fixed, variables=np.isin(np.arange(N * N), var_ids).reshape(N, N),
                        overhang=overhang)
    report = {
        'status': 'BUILT_PENDING_GATES_AND_ENGINE_VIEWS', 'params': P, 'reg': a.reg, 'sea_cut': a.sea_cut,
        'dry_raise_max_m': a.dry_raise_max, 'levee_cap_m': a.levee_cap, 'corridor_margin': a.corridor_margin,
        'near_min_depth_m': a.near_min_depth, 'near_dist_m': a.near_dist if a.near_min_depth is not None else None,
        'groove_may_rise': a.groove_may_rise, 'groove_min_depth_m': a.groove_min_depth,
        'sd_override': str(a.sd_override) if a.sd_override else None, 'narva_core_m': a.narva_core_m,
        'free_corridor_box': a.free_corridor_box,
        'corridor_faces_exact': bool(np.array_equal(h2[corridor_exact], h0.astype('float32').astype(float)[corridor_exact])),
        'channels': str(a.channels) if a.channels else None, 'channel_pieces': n_pieces,
        'edges': int(len(ew)), 'variables': int(nv), 'equations': int(ne),
        'solver': {'status': int(sol.status), 'message': str(sol.message), 'nit': int(sol.nit), 'cost': float(sol.cost),
                   'seconds': round(t2 - t1, 1)},
        'face_recovery': faces, 'dry_sample_triangles_reverted': dry_reverted,
        'changed_vertices': int(changed.sum()), 'wet_changed': int((changed & wet).sum()), 'land_changed': int((changed & dry).sum()),
        'raise_max_m': round(float(d.max()), 3), 'lower_max_m': round(float(-d.min()), 3),
        'abs_change_m_p50_p90': [round(float(np.percentile(np.abs(d[changed]), q)), 3) for q in (50, 90)] if changed.any() else None,
        'overhang_land_vertices_before_after': [over_before, over_after], 'gate_recheck': gate, 'offset_limits': limits,
        'crossing_offset_by_group': groups, 'protected_corridors': len(entries),
        'inputs': {str(p): sha(p) for p in [a.terrain, a.water_v30, a.nature, a.shallow_reference, a.dry_reference, Path(__file__)]},
        'output_sha256': sha(dest), 'seconds': round(time.time() - t0, 1),
        'limits': ['Heights only; classes, levels and pieces unchanged.',
                   'The tidal sea and delta coast are not reshaped (wet <= 0.45, land >= 1.40 there).',
                   'Engine views and the grouped gates decide acceptance.']}
    (a.out / 'report.json').write_text(json.dumps(report, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('inputs', 'params')}, indent=1))


if __name__ == '__main__':
    main()

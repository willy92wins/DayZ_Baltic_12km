"""Standing and flowing inland water shores V30 on one smoothed outline per component, and the inland-bed floor.

The water of every inland body is drawn per 6 m cell at a plane (v30_common.cell_planes); standing water (lakes,
ponds) sits at a flat centimetre level, a flowing body (navigable reach, river, stream) descends in 0.025 m plane
steps. The visible shore is where the native terrain (6 m grid, NW-SE diagonals) crosses those planes.
profile_lakes_v30.py and profile_rivers_v30.py fixed the same per kind of water, but each froze everything within
22 m of the other kind, so wetlands where ponds, lakes and rivers interleave kept the 6 m staircase. This tool
profiles both kinds in one pass, component by component, each with per-vertex levels:
1. Components in one id space: standing bodies by centimetre level (relevel_bodies_v30.label_bodies, 8-connected,
   bodies under 4 vertices left unlabelled), flowing bodies 8-connected above the 0.80 m plane cut, offset past the
   standing ids; components under --min-vertices are not profiled.
2. Outline: signed distance to the component (negative inside), Gaussian-smoothed (--sigma m) and clamped so the
   zero line moves at most --max-shift; then the exact distance to its zero contour, signed by the smoothed field.
   With --outline-sd PATH the smoothed vector outline of the design, given as a signed-distance field (npz key
   'sd', metres, negative inside water, NaN where undefined), replaces the raster field wherever its sign agrees
   with the input class (negative on the component, positive on land) and the class is one of
   --outline-sd-classes, so a straight raster row no longer keeps the waterline on a grid row.
3. Profile: a vertex ending a native edge (east, south, NW-SE diagonal) whose ends lie on opposite sides of the
   outline takes Lw + slope * sd, where Lw is the level of the nearest component vertex. The slope is --slope (0.15
   m per m), or per class with --slope-by-class SPEC ("2:0.167,5:0.25,6:0.2,7:0.167": lakes and ponds 1 m deep at 6 m
   from the shore, rivers about 1 m at the centre, streams about 0.4 m; Guillermo, 06-10), the class being the
   vertex's own on the component and the nearest component vertex's on land. Steeper on both sides, the profile still
   crosses Lw on the outline, so the water deepens and the first land vertex rises in proportion. With --bed-floor F
   a steeper class slope is held at (Lw - F) / --slope-ref (default 4 m) but never under --slope, so a water vertex up
   to --slope-ref inside the outline stays over the floor and the crossing stays on the outline. The side of a vertex is
   its INPUT class, never the sign of sd, so no class or level changes and the cell planes, and with them the
   existing water pieces, stay valid: water is capped at min(level - 0.10, plane - 0.02), land at
   max(nearest level + 0.05, plane, land floor) (1.40 m, 0.80 m on the beach); each move capped (--max-raise-water
   on water, --max-raise on land, --max-lower down); a vertex whose capped target still breaks its gate keeps its
   height. With --low-water-bank a land vertex the component forces whose floor comes from the 1.40 m land floor
   rather than from the water (its water level + 0.05 under it; the water level is the highest among its inland-water
   8-neighbours, at least the nearest one) is held at max(water level + 0.05, plane, --low-water-bank-min) instead, so the crossing of a very low water plane
   (level about 1.0 m) falls between the wet vertex and the bank. A land vertex edited by several components keeps
   the MAXIMUM of their targets, so it stays above every water it borders; a water vertex is edited only by its
   own component.
4. Edits that make a land face steeper than 35 degrees (or than it was) are undone.
5. Bed floor (--bed-floor F): every lake, pond, river and stream vertex of a profiled component outside the exact
   corridors, the Narva zone, the map border and the vanilla reach cells rises to min(F, level - --bed-min-depth,
   gate cap). Navigable reaches keep their depth (Guillermo, 05-10) unless --bed-floor-navigable: then their vertices,
   inside the exact corridor too, rise to min(F, level - --bed-floor-navigable-min-depth (1.0 m), gate cap), so a
   navigable reach keeps that depth of water: the full floor where its level allows it, and as high as that depth
   allows on the lower reaches towards the sea, with no step in the bed where the level crosses F + depth (Guillermo,
   07-10: the engine sea showed through the navigable rivers, BALTIC-018). High navigable vertices eligible for the
   full floor are included even when their component is too small for shore profiling; the other exclusions remain.
6. Gates: water depth, banks, land/beach floor, pieces and slopes are counted on the input and on the output
   (profile_rivers_v30.gate_counts) and the output counts must not exceed the input ones; with --low-water-bank
   the relaxed bank vertices standing at or above their own relaxed floor are lifted to the 1.40 m land floor for
   the output count, and 'low_water_bank' under 'vertices' reports the relaxed vertices below 1.40 m and below
   their own relaxed floor.
Fixed for the shore profile: platforms, reserves, the exact 24 m navigable and delta corridor vertices (only those,
so the channel edges stay free), the Narva zone and the map border, the sea and the delta, low inland water at or
below the 0.80 m plane cut (drawn by the engine sea), unlabelled standing water, the vertices of the vanilla channel
reaches (<channels>/axes.json removed cells), components below --min-vertices, and every vertex within
--band + --max-shift + 6 m of any of those. A vertex near two components is NOT fixed any more, so shores where a
lake or pond touches a river or stream are profiled (Guillermo, 06-10); the nature envelope is not fixed either,
its reserve stays the same while the drawing of its shores changes.
No class or level changes, so the cell planes and the existing water pieces stay valid: no water tile is rebuilt.
Usage: profile_inland_v30.py --terrain IN.npz --out OUTDIR --channels FITDIR [--slope 0.15] [--slope-by-class SPEC]
                             [--slope-ref 4.0] [--band 12]
                             [--sigma 12] [--max-shift 4] [--min-vertices 4] [--max-raise 2.0]
                             [--max-raise-water 6.0] [--max-lower 1.5] [--bed-floor F] [--bed-min-depth 0.30]
                             [--bed-floor-navigable] [--bed-floor-navigable-min-depth 1.0]
                             [--outline-sd PATH] [--outline-sd-classes 2,5,7] [--low-water-bank]
                             [--low-water-bank-min 1.0] [--narva-radius 620] [--sea-cut 0.51]
       profile_inland_v30.py --selftest
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import shapely
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v30_common import N, cell_planes, grid_xz, vertex_plane_bounds  # noqa: E402
from finish_shores_v30 import discard_steeper_land_faces, protect_corridors  # noqa: E402
from profile_coast_v30 import EDGES, NARVA, SEA_CLASSES, sha  # noqa: E402
from profile_lakes_v30 import G, EPS, window_lines  # noqa: E402
from relevel_bodies_v30 import label_bodies  # noqa: E402
from profile_rivers_v30 import PIECE_DEPTH, gate_counts, same_level  # noqa: E402

FLOWING = (3, 5, 6)
STANDING = (2, 7)
INLAND = STANDING + FLOWING


def edge_offsets(h, edges):
    """Distance (m) along each recorded native edge between the terrain crossing of the local level Lw and the
    outline crossing, per water-end class; edges whose terrain no longer crosses Lw are counted apart."""
    ra, ca, rb, cb, tstar, length, lv, k = edges
    out = {}
    for c in INLAND:
        out[c] = {'edges': 0}
    if ra.size == 0:
        return out
    ha, hb = h[ra, ca] - lv, h[rb, cb] - lv
    ok = ha * hb < 0
    t = np.where(ok, ha / np.where(ok, ha - hb, 1.0), np.nan)
    v = np.abs(t - tstar) * length
    for c in INLAND:
        m = k == c
        vv = v[m & ok]
        out[c] = {'edges': int(m.sum()), 'no_crossing': int((m & ~ok).sum()),
                  **({q: round(float(np.percentile(vv, p)), 3)
                      for q, p in (('p50', 50), ('p90', 90), ('p99', 99))} if vv.size else {})}
    return out


def profile(t, corridor, reach_vertices, a):
    """The whole method on the terrain arrays t; returns (output arrays, masks, report without inputs)."""
    h0 = t['heights'].astype(np.float64)
    cls0 = t['cls'].copy()
    level0 = t['level'].astype(np.float64)
    x, z = grid_xz()
    flow0 = np.isin(cls0, FLOWING)
    stand0 = np.isin(cls0, STANDING)
    land0 = cls0 == 0
    low = np.isin(cls0, INLAND) & (level0 <= G['plane_cut_m'])
    sids = label_bodies(cls0, level0)
    n_standing = int(sids.max())
    flab, n_flowing = ndimage.label(flow0 & ~low, structure=np.ones((3, 3), bool))
    ids = sids.copy()
    fm = flab > 0
    ids[fm] = (flab[fm] + n_standing).astype(np.int32)
    n_comp = n_standing + n_flowing
    narva = np.hypot(x - NARVA[0], z - NARVA[1]) <= a.narva_radius
    narva600 = np.hypot(x - NARVA[0], z - NARVA[1]) <= G['narva_zone_excluded_m']
    border = (x < 12) | (z < 12) | (x > 12270) | (z > 12270)

    # per-vertex gate fields from the input; exact for the output because no class or level changes
    planes = cell_planes(cls0, level0, sea_cut=a.sea_cut)
    pmin, pmax = vertex_plane_bounds(planes)
    dist, idx = ndimage.distance_transform_edt(land0, sampling=6.0, return_indices=True)
    near_lv = level0[idx[0], idx[1]]
    wcap = level0 - G['depth_min_m'] - EPS
    pm = np.isfinite(pmin)
    wcap[pm] = np.minimum(wcap[pm], pmin[pm] - PIECE_DEPTH - EPS)
    floor = np.where(t['beach'], G['beach_floor_m'], G['land_floor_m'])
    lfloor = np.fmax(near_lv + G['freeboard_m'], np.fmax(pmax, floor)) + EPS
    lwb = getattr(a, 'low_water_bank', False)
    if lwb:
        # level a relaxed bank vertex must clear: the highest level among its 8-neighbours that are inland water over
        # the plane cut (as verify_terrain_v30.py --low-water-bank-min checks it), at least the nearest level
        iw = np.isin(cls0, (2, 3, 5, 6, 7)) & (np.nan_to_num(level0, nan=-np.inf) > G['plane_cut_m'])
        pad = np.pad(np.where(iw, level0, -np.inf), 1, constant_values=-np.inf)
        adj = np.full((N, N), -np.inf)
        for dr in (0, 1, 2):
            for dc in (0, 1, 2):
                if (dr, dc) != (1, 1):
                    adj = np.fmax(adj, pad[dr:dr + N, dc:dc + N])
        bank_lv = np.fmax(near_lv, adj)

    reach = a.band + a.max_shift + 6.0
    rv = int(np.ceil(reach / 6.0))
    yy, xx = np.mgrid[-rv:rv + 1, -rv:rv + 1]
    disc = np.hypot(yy, xx) * 6.0 <= reach
    objs = ndimage.find_objects(ids)
    sizes = np.bincount(ids.ravel(), minlength=n_comp + 1)
    small = (ids > 0) & (sizes[ids] < a.min_vertices)
    loose = stand0 & (sids == 0) & ~low
    other = (np.isin(cls0, SEA_CLASSES) | low | reach_vertices | loose | small)
    near_other = ndimage.distance_transform_edt(~other) * 6.0 <= reach if other.any() else np.zeros((N, N), bool)
    fixed = t['platform'] | t['reserve'] | corridor | narva | border | other | near_other

    h1 = h0.copy()
    land_max = np.full((N, N), -np.inf)
    land_set = np.zeros((N, N), bool)
    land_n = np.zeros((N, N), np.uint8)
    relaxed = np.zeros((N, N), bool)
    masks = {k: np.zeros((N, N), bool) for k in ('band', 'forced', 'editable')}
    counts = dict(profiled=0, skipped_no_outline=0, forced_at_cap=0, kept_by_gate=0)
    profiled = np.zeros(n_comp + 1, bool)
    per_class = {k: dict(forced=0, changed=0) for k in INLAND}
    rows = []
    e_ra, e_ca, e_rb, e_cb, e_tstar, e_len, e_lv, e_k = ([] for _ in range(8))
    g = int(np.ceil((reach + 3 * a.sigma + 12.0) / 6.0))
    for i, sl in enumerate(objs, 1):
        if sl is None or sizes[i] < a.min_vertices:
            continue
        r0, r1 = max(sl[0].start - g, 0), min(sl[0].stop + g, N)
        c0, c1 = max(sl[1].start - g, 0), min(sl[1].stop + g, N)
        W = (slice(r0, r1), slice(c0, c1))
        B = ids[W] == i
        nb = int(B.sum())
        hw0 = h0[W]
        cls0w, level0w = cls0[W], level0[W]
        lw0 = land0[W]
        base = np.where(B, -ndimage.distance_transform_edt(B), ndimage.distance_transform_edt(~B)) * 6.0
        smooth = ndimage.gaussian_filter(base, a.sigma / 6.0)
        smooth = np.clip(smooth, base - a.max_shift, base + a.max_shift)
        near = np.abs(base) <= a.band + a.max_shift + 9.0
        lines = window_lines(smooth, near, r0, c0)
        if not lines:
            counts['skipped_no_outline'] += 1
            continue
        segs = np.concatenate([np.stack([ln[:-1], ln[1:]], axis=1) for ln in lines])
        tree = shapely.STRtree(shapely.linestrings(segs))
        xw, zw = x[W], z[W]
        _, d = tree.query_nearest(shapely.points(xw[near], zw[near]), return_distance=True, all_matches=False)
        sd = np.full(B.shape, np.nan)
        sd[near] = np.where(smooth[near] < 0, -d, d)
        # local level: the level of the nearest component vertex, for the profile target and the metric
        _, j = ndimage.distance_transform_edt(~B, return_indices=True)
        Lw = level0w[j[0], j[1]]
        wat_cls = cls0w[j[0], j[1]]
        # external outline of the design: where its sign agrees with the input class (negative on the component,
        # positive on land) and the class is in the list, it replaces the raster signed distance
        ext = getattr(a, 'ext_sd', None)
        if ext is not None:
            ew = ext[W]
            with np.errstate(invalid='ignore'):
                usew = ((B & np.isfinite(ew) & (ew < 0) & np.isin(cls0w, a.outline_sd_classes))
                        | (lw0 & np.isfinite(ew) & (ew > 0) & np.isin(wat_cls, a.outline_sd_classes)))
            sd = np.where(usew, ew, sd)
        bandm = near & np.isfinite(sd) & (np.abs(sd) <= a.band)
        edit = bandm & (B | lw0) & ~fixed[W]
        ends = B | lw0
        nr, nc = B.shape
        forced = np.zeros(B.shape, bool)
        for dr, dc in EDGES:
            sa, sb = sd[:nr - dr, :nc - dc], sd[dr:, dc:]
            with np.errstate(invalid='ignore'):
                cross = (np.isfinite(sa) & np.isfinite(sb) & (sa * sb < 0)
                         & ends[:nr - dr, :nc - dc] & ends[dr:, dc:])
            forced[:nr - dr, :nc - dc] |= cross
            forced[dr:, dc:] |= cross
            ra, ca = np.nonzero(cross)
            sac, sbc = sa[cross], sb[cross]
            e_ra.append(ra + r0)
            e_ca.append(ca + c0)
            e_rb.append(ra + r0 + dr)
            e_cb.append(ca + c0 + dc)
            e_tstar.append(np.abs(sac) / (np.abs(sac) + np.abs(sbc)))
            e_len.append(np.full(ra.size, 6.0 * (2 ** 0.5 if dr and dc else 1.0)))
            e_lv.append(Lw[:nr - dr, :nc - dc][cross])
            e_k.append(wat_cls[:nr - dr, :nc - dc][cross])
        forced &= edit
        # very low water: the bank vertices this component forces, whose floor comes from the 1.40 m land floor
        # rather than from the water, are held over a relaxed per-vertex floor so the plane crossing can fall
        # between the wet vertex and the bank
        lw_floor = lfloor[W]
        if lwb:
            cand = lw0 & forced & (bank_lv[W] + G['freeboard_m'] < floor[W])
            if cand.any():
                vf = np.fmax(np.fmax(bank_lv[W] + G['freeboard_m'], pmax[W]), a.low_water_bank_min) + EPS
                cand &= vf < lw_floor
                lw_floor = np.where(cand, vf, lw_floor)
                relaxed[W] |= cand
        # slope of the profile per vertex, from the class that decides it (its own on the component, the nearest
        # component vertex's on land): steeper per class with --slope-by-class, but never so steep that a water vertex
        # --slope-ref inside the outline would reach under the bed floor, and never gentler than --slope
        attr = np.where(B, cls0w, wat_cls)
        sbc = getattr(a, 'slope_by_class', None) or {}
        slope = a.slope
        if sbc:
            lut = np.full(256, a.slope)
            for k, v in sbc.items():
                lut[k] = v
            slope = lut[attr]
            if a.bed_floor is not None:
                with np.errstate(invalid='ignore'):
                    cap = np.clip((Lw - a.bed_floor) / getattr(a, 'slope_ref', 4.0), a.slope, slope)
                slope = np.where(slope > a.slope, cap, slope)
        # side = input class: water capped at its own gate, land held over its own floor
        with np.errstate(invalid='ignore'):
            want = np.where(forced, Lw + slope * np.nan_to_num(sd), hw0)
            want = np.where(B, np.minimum(want, wcap[W]), want)
            want = np.where(lw0, np.maximum(want, lw_floor), want)
            raise_cap = np.where(B, a.max_raise_water, a.max_raise)
            want_c = np.clip(want, hw0 - a.max_lower, hw0 + raise_cap)
            broke = (B & (want_c > wcap[W])) | (lw0 & (want_c < lw_floor))
        want_f = np.where(broke, hw0, want_c)
        # water is edited by its own component only; land keeps the maximum over every component that moves it (a
        # component that leaves a vertex where it was must not undo another component's lowering)
        em = edit & B
        lm = edit & lw0 & (want_f != hw0)
        hv = h1[W]
        hv[em] = want_f[em]
        land_max[W][lm] = np.fmax(land_max[W][lm], want_f[lm])
        land_set[W] |= lm
        land_n[W] += lm
        diff = edit & (want_f != hw0)
        masks['band'][W] |= bandm
        masks['forced'][W] |= forced
        masks['editable'][W] |= edit
        counts['profiled'] += 1
        profiled[i] = True
        counts['forced_at_cap'] += int((edit & forced & (want_c != want) & ~broke).sum())
        counts['kept_by_gate'] += int((edit & forced & broke).sum())
        for k in INLAND:
            per_class[k]['forced'] += int((forced & (attr == k)).sum())
            per_class[k]['changed'] += int((diff & (attr == k)).sum())
        rows.append(dict(id=i, vertices=nb,
                         cls_counts={k: int((B & (cls0w == k)).sum()) for k in INLAND},
                         level_min=round(float(level0w[B].min()), 3),
                         level_max=round(float(level0w[B].max()), 3),
                         changed=int(diff.sum())))
    h1[land_set] = land_max[land_set]

    # undo steepened land faces; nothing else about classes or levels ever moved
    h2, faces = discard_steeper_land_faces(h1, h0, cls0)
    h2 = h2.astype('float32').astype(np.float64)

    # bed floor on lakes, ponds, rivers and streams of profiled components; navigable reaches keep their depth unless
    # --bed-floor-navigable, and then rise as far as the minimum navigable depth of water allows;
    # may act inside fixed (the only place a fixed vertex may change), never lowers anything
    bed = np.zeros((N, N), bool)
    if a.bed_floor is not None:
        nav = (cls0 == 3) if getattr(a, 'bed_floor_navigable', False) else np.zeros((N, N), bool)
        dnav = getattr(a, 'bed_floor_navigable_min_depth', 1.0)
        # The shore profiler skips tiny components; that must not exempt a high
        # navigable bed from its floor. Low reaches keep the existing policy.
        high_nav = nav & (level0 >= a.bed_floor + dnav)
        body = (((profiled[ids] & (ids > 0) & (np.isin(cls0, (2, 5, 6, 7)) & ~corridor | nav)) | high_nav)
                & ~narva & ~border & ~reach_vertices & (level0 > G['plane_cut_m']))
        with np.errstate(invalid='ignore'):
            need = np.minimum(np.minimum(a.bed_floor, level0 - a.bed_min_depth), wcap)
            need = np.where(nav, np.minimum(np.minimum(a.bed_floor, level0 - dnav), wcap), need)
        bed = body & np.isfinite(need) & (h2 < need)
        h2[bed] = need[bed]
        h2 = h2.astype('float32').astype(np.float64)

    h0f = h0.astype('float32').astype(np.float64)
    changed = h2 != h0f
    assert np.array_equal(cls0, t['cls']), 'class changed'
    assert same_level(level0.astype(t['level'].dtype), t['level']), 'level changed'
    assert not np.any(changed & fixed & ~bed), 'protected height changed'

    gb = gate_counts(h0, cls0, level0, t['beach'], narva600, planes)
    ga = gate_counts(h2, cls0, level0, t['beach'], narva600, planes)
    if lwb:
        # the verifier with --low-water-bank-min passes a relaxed bank vertex standing at or above its own relaxed
        # floor; for the land floor count only, lift those to the land floor so only true failures count
        vf_all = np.fmax(np.fmax(bank_lv + G['freeboard_m'], pmax), a.low_water_bank_min) + EPS
        hg = h2.copy()
        hg[relaxed & (h2 >= vf_all - 1e-6)] = G['land_floor_m']
        ga['land_floor'] = gate_counts(hg, cls0, level0, t['beach'], narva600, planes)['land_floor']
    assert all(ga[k] <= gb[k] for k in ga), (gb, ga)

    edges = tuple(np.concatenate(v) if v else np.array([]) for v in (e_ra, e_ca, e_rb, e_cb, e_tstar, e_len, e_lv, e_k))
    ob, oa = edge_offsets(h0, edges), edge_offsets(h2, edges)
    rows.sort(key=lambda r: -r['vertices'])
    d = h2 - h0
    rep = {
        'components': {'standing': n_standing, 'flowing': n_flowing, 'profiled': counts['profiled'],
                       'skipped_small': int((sizes[1:n_comp + 1] < a.min_vertices).sum()),
                       'skipped_no_outline': counts['skipped_no_outline'],
                       'land_vertices_edited_by_two_or_more': int((land_n >= 2).sum())},
        'vertices': {'band': int(masks['band'].sum()), 'editable': int(masks['editable'].sum()),
                     'forced': int(masks['forced'].sum()), 'changed': int(changed.sum()),
                     'forced_at_move_cap': counts['forced_at_cap'], 'kept_by_gate': counts['kept_by_gate'],
                     'bed_raised': int(bed.sum()), 'face_recovery': faces,
                     **({'low_water_bank': {'vertices': int((relaxed & (h2 < G['land_floor_m'] - 1e-6)).sum()),
                                            'below_own_floor': int((relaxed & (h2 < vf_all - 1e-6)).sum())}}
                        if lwb else {})},
        'by_class': {k: {'forced': per_class[k]['forced'], 'changed': per_class[k]['changed'],
                         'bed_raised': int((bed & (cls0 == k)).sum()),
                         'crossing_offset_m_vs_smoothed_outline': {'before': ob[k], 'after': oa[k]}}
                     for k in (2, 3, 5, 6, 7)},
        'forced_water_depth_m_p50': {k: round(float(np.median((level0 - h2)[masks['forced'] & (cls0 == k)])), 3)
                                     for k in (2, 5, 6, 7) if np.any(masks['forced'] & (cls0 == k))},
        'gates': {k: {'before': gb[k], 'after': ga[k]} for k in gb},
        'bed_below_0p85': {k: {'before': int(((cls0 == k) & (level0 > G['plane_cut_m']) & (h0 < 0.85)).sum()),
                               'after': int(((cls0 == k) & (level0 > G['plane_cut_m']) & (h2 < 0.85)).sum())}
                           for k in (2, 3, 5, 6, 7)},
        'largest_components': rows[:10],
        'change_m': {'raise_max': round(float(d.max()), 3), 'lower_max': round(float(-d.min()), 3)}}
    return out_arrays(t, h2), dict(masks, changed=changed, bed_raised=bed), rep


def out_arrays(t, h2):
    out = dict(t)
    out['heights'] = h2.astype(t['heights'].dtype)
    return out


def selftest():
    n = N
    h = np.full((n, n), 4.6, np.float32)
    cls = np.zeros((n, n), np.uint8)
    level = np.full((n, n), np.nan, np.float32)
    r, c = np.mgrid[0:n, 0:n]
    cc = 1000 + (r - 800) // 7
    river = (r >= 800) & (r <= 1100) & (c >= cc - 1) & (c <= cc + 1)
    cls[river] = 5
    level[river] = (4.0 - 0.004 * (r - 800))[river]
    h[river] = level[river] - 0.6
    cc950 = 1000 + (950 - 800) // 7
    stream = (r == 950) & (c >= cc950 + 2) & (c <= cc950 + 80)
    cls[stream] = 6
    level[stream] = (3.4 + 0.003 * (c - cc950 - 2))[stream]
    h[stream] = level[stream] - 0.25
    cc1100 = 1000 + (1100 - 800) // 7
    lake = (r >= 1101) & (r <= 1115) & (c >= cc1100 - 7) & (c <= cc1100 + 7)
    cls[lake], level[lake], h[lake] = 2, 2.75, 2.0
    nav = (r >= 1300) & (r <= 1305) & (c >= 900) & (c <= 1300)
    cls[nav], level[nav], h[nav] = 3, 3.0, -0.5
    corridor = (r >= 1301) & (r <= 1304) & (c >= 900) & (c <= 1300)
    lowr = (r >= 300) & (r <= 305) & (c >= 300) & (c <= 400)
    cls[lowr], level[lowr], h[lowr] = 3, 0.7, 0.0
    lake_a = (np.maximum(abs(r - 1540), abs(c - 640)) <= 40) & (abs(r - 1540) + abs(c - 640) <= 60)
    island = np.maximum(abs(r - 1545), abs(c - 637)) <= 6
    lake_a &= ~island
    cls[lake_a], level[lake_a], h[lake_a] = 2, 4.0, 3.0
    cc900 = 1000 + (900 - 800) // 7
    pond = (r >= 898) & (r <= 902) & (c >= cc900 + 4) & (c <= cc900 + 8)
    cls[pond], level[pond], h[pond] = 7, 3.0, 2.6
    zero = np.zeros((n, n), bool)
    t = dict(heights=h, cls=cls, level=level, platform=zero, reserve=zero, narva=zero, water=cls > 0, beach=zero)
    a = argparse.Namespace(slope=0.15, band=12.0, sigma=12.0, max_shift=4.0, min_vertices=4, max_raise=2.0,
                           max_raise_water=6.0, max_lower=1.5, bed_floor=None, bed_min_depth=0.30,
                           narva_radius=620.0, sea_cut=0.51)
    out, masks, rep = profile(t, corridor, zero, a)
    assert all(v['before'] == 0 and v['after'] == 0 for v in rep['gates'].values()), rep['gates']
    assert np.array_equal(out['cls'], cls) and same_level(out['level'], level), 'class or level changed'
    assert np.array_equal(out['heights'][corridor], h[corridor]), 'corridor changed'
    R = a.band + a.max_shift + 6.0
    keep = ndimage.distance_transform_edt(~lowr) * 6.0 <= R
    assert not np.any(masks['changed'] & keep), 'change near the low reach'
    between = (cls == 0) & (r >= 898) & (r <= 902) & (c >= cc900 + 2) & (c <= cc900 + 3)
    assert np.any(masks['changed'][between]), 'river-pond contact not profiled'
    wm = river | pond
    assert not np.any(out['heights'][wm] > level[wm].astype(np.float64) - 0.10), 'water above its level - 0.10'
    for k in (2, 3, 5):
        obk = rep['by_class'][k]['crossing_offset_m_vs_smoothed_outline']['before']
        oak = rep['by_class'][k]['crossing_offset_m_vs_smoothed_outline']['after']
        assert oak['p90'] < obk['p90'], (k, obk, oak)
    assert np.any((out['cls'] == 0) & island), 'island lost'
    a.bed_floor = 3.5
    out2, _, _ = profile(t, corridor, zero, a)
    wk = np.isin(out2['cls'], (2, 5, 6, 7))
    lim = np.minimum(3.5, out2['level'][wk].astype(np.float64) - 0.30)
    assert np.all(out2['heights'][wk] >= lim - 1e-5), float(out2['heights'][wk].min())
    assert np.array_equal(out2['heights'][corridor], h[corridor]), 'corridor changed by the bed floor'
    # a steeper river slope deepens its forced water vertices; classes, levels and gates as before
    a.bed_floor = None
    a.slope_by_class = {5: 0.25}
    out3, masks3, rep3 = profile(t, corridor, zero, a)
    assert np.array_equal(out3['cls'], cls) and same_level(out3['level'], level), 'class or level changed (slopes)'
    assert all(v['after'] == 0 for v in rep3['gates'].values()), rep3['gates']
    fr = masks['forced'] & (cls == 5)
    d1 = float(np.median(level[fr] - out['heights'][fr]))
    d3 = float(np.median(level[fr] - out3['heights'][fr]))
    print(f'forced river depth p50: slope 0.15 {d1:.3f} m, river slope 0.25 {d3:.3f} m')
    assert d3 > d1, (d1, d3)
    # --bed-floor-navigable: the navigable reach rises to the floor, its exact corridor too; a navigable reach whose
    # level leaves less than the minimum depth over the floor (nearer the sea) rises only to level - that depth; the
    # low reach under the plane cut and everything that is not navigable stay as without the option
    a.slope_by_class = {}
    a.bed_floor, a.bed_floor_navigable_min_depth = 1.0, 1.0
    hn, cn, ln = h.copy(), cls.copy(), level.copy()
    seanav = (r >= 1400) & (r <= 1405) & (c >= 900) & (c <= 1000)
    cn[seanav], ln[seanav], hn[seanav] = 3, 1.5, -1.0
    tiny_nav = (r == 1700) & (c == 1700)
    cn[tiny_nav], ln[tiny_nav], hn[tiny_nav] = 3, 2.45, -1.0
    nav = nav | tiny_nav
    tn = dict(t, heights=hn, cls=cn, level=ln, water=cn > 0)
    a.bed_floor_navigable = False
    out4a, _, _ = profile(tn, corridor, zero, a)
    a.bed_floor_navigable = True
    out4, _, rep4 = profile(tn, corridor, zero, a)
    assert np.array_equal(out4['cls'], cn) and same_level(out4['level'], ln), 'class or level changed (navigable)'
    assert np.array_equal(out4a['heights'][corridor], hn[corridor]), 'corridor changed without the option'
    assert np.all(out4['heights'][nav] >= 1.0 - 1e-5), float(out4['heights'][nav].min())
    assert np.all(out4a['heights'][tiny_nav] == -1.0), 'disabled floor changed the isolated control'
    assert np.all(out4['heights'][tiny_nav] == 1.0), 'isolated navigable bed skipped its floor'
    h4, h4a = out4['heights'].astype(np.float64), out4a['heights'].astype(np.float64)
    assert np.all(h4 >= h4a - 1e-6), 'the option lowered a vertex'
    up = h4 > h4a
    assert np.all(h4[up & seanav] <= ln[up & seanav] - 1.0 + 1e-5), 'reach at the sea raised past level - 1.0 m'
    assert np.all(h4[seanav] >= np.minimum(h4a[seanav], 0.5) - 1e-5) and np.any(up & seanav), 'reach at the sea'
    assert np.array_equal(h4[lowr], h4a[lowr]), 'low reach raised'
    assert np.array_equal(h4[~(nav | seanav)], h4a[~(nav | seanav)]), 'non-navigable changed'
    assert all(v['after'] <= v['before'] for v in rep4['gates'].values()), rep4['gates']
    under = (cn == 3) & (ln > 0.80) & (h4 < 0.85)
    b3 = rep4['bed_below_0p85'][3]
    print(f"navigable vertices under 0.85 m: {b3['before']} -> {b3['after']}, all in the reach at the sea: "
          f"{bool(not np.any(under & ~seanav))}")
    assert not np.any(under & ~seanav) and np.any(under & seanav), b3
    print('SELFTEST PASS')


def main():
    if '--selftest' in sys.argv:
        selftest()
        return
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--terrain', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--channels', type=Path, default=None)
    ap.add_argument('--slope', type=float, default=0.15)
    ap.add_argument('--slope-by-class', default='')
    ap.add_argument('--slope-ref', type=float, default=4.0)
    ap.add_argument('--band', type=float, default=12.0)
    ap.add_argument('--sigma', type=float, default=12.0)
    ap.add_argument('--max-shift', type=float, default=4.0)
    ap.add_argument('--min-vertices', type=int, default=4)
    ap.add_argument('--max-raise', type=float, default=2.0)
    ap.add_argument('--max-raise-water', type=float, default=6.0)
    ap.add_argument('--max-lower', type=float, default=1.5)
    ap.add_argument('--bed-floor', type=float, default=None)
    ap.add_argument('--bed-min-depth', type=float, default=0.30)
    ap.add_argument('--bed-floor-navigable', action='store_true')
    ap.add_argument('--bed-floor-navigable-min-depth', type=float, default=1.0)
    ap.add_argument('--outline-sd', type=Path, default=None)
    ap.add_argument('--outline-sd-classes', default='2,5,7')
    ap.add_argument('--low-water-bank', action='store_true')
    ap.add_argument('--low-water-bank-min', type=float, default=1.0)
    ap.add_argument('--narva-radius', type=float, default=620.0)
    ap.add_argument('--sea-cut', type=float, default=0.51)
    a = ap.parse_args()
    if a.channels is None:
        ap.error('--channels is required')
    assert not a.out.exists(), 'fresh output required'
    a.outline_sd_classes = tuple(int(s) for s in a.outline_sd_classes.split(','))
    a.slope_by_class = {int(k): float(v) for k, v in (p.split(':') for p in a.slope_by_class.split(',') if p)}
    if a.outline_sd is not None:
        with np.load(a.outline_sd) as z:
            a.ext_sd = z['sd'].astype(np.float64)
    t0 = time.time()
    t = dict(np.load(a.terrain))
    planes = cell_planes(t['cls'], t['level'], sea_cut=a.sea_cut)
    corridor, _, _, _ = protect_corridors(planes)   # the exact corridor faces, not their one-vertex margin
    axes = json.loads((a.channels / 'axes.json').read_text(encoding='utf-8'))
    reach_vertices = np.zeros((N, N), bool)
    for reach in axes.values():
        for r, c in reach['removed_cells']:
            reach_vertices[r:r + 2, c:c + 2] = True
    out, masks, rep = profile(t, corridor, reach_vertices, a)
    a.out.mkdir(parents=True)
    np.savez_compressed(a.out / 'terrain_inland.npz', **out)
    np.savez_compressed(a.out / 'masks.npz', **masks)
    rep = {'status': 'BUILT_PENDING_GATES_AND_ENGINE_VIEWS',
           'params': {k: (str(v) if isinstance(v, Path) else v)
                      for k, v in vars(a).items() if k not in ('terrain', 'out', 'channels', 'ext_sd')},
           **rep,
           'inputs': {str(p): sha(p) for p in (a.terrain, a.channels / 'axes.json', Path(__file__))},
           'output_sha256': sha(a.out / 'terrain_inland.npz'), 'seconds': round(time.time() - t0, 1),
           'limits': ['Only heights change: classes, levels and the vanilla reach vertices stay as they are.',
                      'Water pieces stay valid (no class or level change); gates and engine views decide acceptance.']}
    (a.out / 'report.json').write_text(json.dumps(rep, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in rep.items() if k != 'inputs'}, indent=1))


if __name__ == '__main__':
    main()

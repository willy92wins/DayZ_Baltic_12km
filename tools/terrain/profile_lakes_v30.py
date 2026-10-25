"""Lake and pond shores V30 on a smoothed outline, islands included, and the lake-bed floor (BALTIC-007, BALTIC-018).

The water of a standing body (lake or pond, census labelling) is a flat plane at its level L drawn by water pieces; its
visible shore is where the native terrain (6 m grid, NW-SE diagonals) crosses that plane. The v3b fit kept wet vertices
~0.3 m under L and land ~0.4 m over it, so the crossing keeps a fixed fraction of every wet-land edge and shores and
islands draw the 6 m grid (evidence/v30-v5-candidate-2026-10-05). profile_coast_v30.py fixed the same for the sea; this
tool applies its method body by body, each with its own level, in a window around the body:
1. Outline: signed distance to the body (negative inside, islands included), Gaussian-smoothed (--sigma m) and clamped
   so the zero line moves at most --max-shift; then the exact distance to its zero contour, signed by the smoothed field.
2. Profile: a vertex ending a native edge (east, south, NW-SE diagonal) whose ends lie on opposite sides of the outline
   takes L + --slope * sd, within the gates of tools/terrain/verify_terrain_v30.py: water at most L - 0.10, land at
   least L + 0.05 and the land floor (1.40 m, 0.80 m on the beach); each move capped (--max-raise, --max-lower); no
   vertex between the two gates. Every other vertex keeps its height, except to meet those gates.
3. Classes and levels follow the heights inside the band: water of the body (its class, level L) below L, land above.
4. Edits that make a land face steeper than 35 degrees (or than it was) are undone, with their classes.
5. Bed floor (--bed-floor F): every water vertex of a profiled body outside the navigable corridors, the Narva zone and
   the two-vertex map border rises to max(h, min(F, L - --bed-min-depth)). The engine draws its sea (0.65-0.85 m) under any lake whose bed lies
   below it, and from the air the lake splits into bands (BALTIC-018, evidence/v30-bed-probe-2026-10-05). Navigable
   reaches keep their depth (Guillermo, 05-10).
Fixed for the shore profile: platforms, reserves, the nature envelope, the 24 m navigable and delta corridors (with their
margin), the Narva zone and the map border (those vertices themselves); the sea, the delta, navigable reaches, rivers,
streams and unlabelled standing water, each with every vertex within --band + --max-shift + 6 m of it; and every vertex
within that reach of two bodies (contacts between water stay as they are). Land next to a platform or the border may
be edited. Bodies at or below the 0.80 m pond-plane cut are drawn by the sea and not profiled.
The changed 48 m water tiles are rebuilt afterwards with tools/water/patch_water_tiles_v30.py.
Usage: profile_lakes_v30.py --terrain IN.npz --out OUTDIR [--slope 0.15] [--band 12] [--sigma 12] [--max-shift 4]
                            [--min-vertices 4] [--bed-floor 1.0] [--bed-min-depth 0.30]
       profile_lakes_v30.py --selftest
"""
import argparse
import json
import sys
import time
from pathlib import Path

import contourpy
import numpy as np
import shapely
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v30_common import N, cell_planes, grid_xz  # noqa: E402
from finish_shores_v30 import discard_steeper_land_faces, protect_corridors  # noqa: E402
from profile_coast_v30 import EDGES, NARVA, NATURE, SEA_CLASSES, sha, turning, zero_lines  # noqa: E402
from relevel_bodies_v30 import label_bodies  # noqa: E402

FLOWING = (3, 5, 6)
STANDING = (2, 7)
G = dict(depth_min_m=0.10, freeboard_m=0.05, land_floor_m=1.40, beach_floor_m=0.80, plane_cut_m=0.80,
         bank_radius_m=8.5, narva_zone_excluded_m=600.0)   # verify_terrain_v30.py G and its pieces rule
EPS = 1e-4   # m, margin of a dead-zone snap over the float32 rounding of heights near L


def window_lines(field, mask, r0, c0):
    """Zero lines of a window whose first vertex is (r0, c0), restricted to mask, in game x and z."""
    nr, nc = field.shape
    z = np.ma.masked_invalid(np.where(mask, field, np.nan))
    gen = contourpy.contour_generator(x=(c0 + np.arange(nc)) * 6.0, y=12282.0 - (r0 + np.arange(nr)) * 6.0, z=z,
                                      line_type=contourpy.LineType.Separate)
    return [ln for ln in gen.lines(0.0) if len(ln) >= 2]


def offsets(h, edges):
    """Distance (m) along each native edge crossing the smoothed outline between the terrain crossing of the body
    level and the outline crossing; edges whose terrain no longer crosses the level are counted apart."""
    if not edges:
        return {'edges': 0}
    ra, ca, rb, cb, tstar, length, lv = (np.concatenate(v) for v in zip(*edges))
    ha, hb = h[ra, ca] - lv, h[rb, cb] - lv
    ok = ha * hb < 0
    t = np.where(ok, ha / np.where(ok, ha - hb, 1.0), np.nan)
    v = (np.abs(t - tstar) * length)[ok]
    return {'edges': int(ok.size), 'no_crossing': int((~ok).sum()),
            **({k: round(float(np.percentile(v, q)), 3) for k, q in (('p50', 50), ('p90', 90), ('p99', 99))} if v.size else {})}


def gates(h, cls, level, beach, narva600):
    """Water depth, banks and land floor counts as verify_terrain_v30.py computes them."""
    water = cls > 0
    dist, idx = ndimage.distance_transform_edt(~water, sampling=6.0, return_indices=True)
    near_lv = level[idx[0], idx[1]]
    land = ~water
    b = land & (dist <= G['bank_radius_m']) & ~narva600
    with np.errstate(invalid='ignore'):
        return {'water_depth': int((water & ~narva600 & (level - h < G['depth_min_m'])).sum()),
                'banks': int((b & (h < near_lv + G['freeboard_m'])).sum()),
                'land_floor': int((land & ~narva600 & ~beach & (h < G['land_floor_m'] - 1e-6)).sum()),
                'beach_floor': int((beach & (h < G['beach_floor_m'] - 1e-6)).sum())}


def profile(t, nature, corridor, a):
    """The whole method on the terrain arrays t; returns (output arrays, masks, report without inputs)."""
    h0 = t['heights'].astype(np.float64)
    cls0, level0 = t['cls'].copy(), t['level'].astype(np.float64)
    x, z = grid_xz()
    sea0, flow0, land0 = np.isin(cls0, SEA_CLASSES), np.isin(cls0, FLOWING), cls0 == 0
    ids = label_bodies(cls0, level0)
    loose = np.isin(cls0, STANDING) & (ids == 0)
    narva = np.hypot(x - NARVA[0], z - NARVA[1]) <= a.narva_radius
    narva600 = np.hypot(x - NARVA[0], z - NARVA[1]) <= G['narva_zone_excluded_m']
    border = (x < 12) | (z < 12) | (x > 12270) | (z > 12270)
    reach = a.band + a.max_shift + 6.0
    rv = int(np.ceil(reach / 6.0))
    yy, xx = np.mgrid[-rv:rv + 1, -rv:rv + 1]
    disc = np.hypot(yy, xx) * 6.0 <= reach
    objs = ndimage.find_objects(ids)
    claims = np.zeros((N, N), np.uint8)
    for i, sl in enumerate(objs, 1):
        if sl is None:
            continue
        r0, r1 = max(sl[0].start - rv, 0), min(sl[0].stop + rv, N)
        c0, c1 = max(sl[1].start - rv, 0), min(sl[1].stop + rv, N)
        claims[r0:r1, c0:c1] += ndimage.binary_dilation(ids[r0:r1, c0:c1] == i, structure=disc).astype(np.uint8)
    other = sea0 | flow0 | loose
    near_other = ndimage.distance_transform_edt(~other) * 6.0 <= reach if other.any() else np.zeros((N, N), bool)
    fixed = (t['platform'] | t['reserve'] | nature | corridor | narva | border | other | near_other | (claims >= 2))

    h1, cls1, level1, ids1 = h0.copy(), cls0.copy(), level0.copy(), ids.copy()
    masks = {k: np.zeros((N, N), bool) for k in ('band', 'forced', 'editable')}
    counts = dict(profiled=0, skipped_small=0, skipped_low=0, skipped_no_outline=0, capped=0)
    profiled = np.zeros(len(objs) + 1, bool)
    level_of = np.full(len(objs) + 1, np.nan)
    rows, edges = [], []
    g = int(np.ceil((reach + 3 * a.sigma + 12.0) / 6.0))
    for i, sl in enumerate(objs, 1):
        if sl is None:
            continue
        r0, r1 = max(sl[0].start - g, 0), min(sl[0].stop + g, N)
        c0, c1 = max(sl[1].start - g, 0), min(sl[1].stop + g, N)
        W = (slice(r0, r1), slice(c0, c1))
        B = ids[W] == i
        nb = int(B.sum())
        L = float(np.median(level0[W][B]))
        level_of[i] = L
        if nb < a.min_vertices:
            counts['skipped_small'] += 1
            continue
        if L <= G['plane_cut_m']:
            counts['skipped_low'] += 1
            continue
        k = int(np.bincount(cls0[W][B]).argmax())
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
        _, dist = tree.query_nearest(shapely.points(xw[near], zw[near]), return_distance=True, all_matches=False)
        sd = np.full(B.shape, np.nan)
        sd[near] = np.where(smooth[near] < 0, -dist, dist)
        band = near & np.isfinite(sd) & (np.abs(sd) <= a.band)
        lw = land0[W]
        edit = band & (B | lw) & ~fixed[W]
        ends = B | lw
        nr, nc = B.shape
        forced = np.zeros(B.shape, bool)
        for dr, dc in EDGES:
            sa, sb = sd[:nr - dr, :nc - dc], sd[dr:, dc:]
            with np.errstate(invalid='ignore'):
                cross = (np.isfinite(sa) & np.isfinite(sb) & (sa * sb < 0) & ends[:nr - dr, :nc - dc] & ends[dr:, dc:])
            forced[:nr - dr, :nc - dc] |= cross
            forced[dr:, dc:] |= cross
            ra, ca = np.nonzero(cross)
            edges.append((ra + r0, ca + c0, ra + r0 + dr, ca + c0 + dc, np.abs(sa[cross]) / (np.abs(sa[cross]) + np.abs(sb[cross])),
                          np.full(ra.size, 6.0 * (2 ** 0.5 if dr and dc else 1.0)), np.full(ra.size, L)))
        forced &= edit
        hw = h0[W]
        want = np.where(forced, L + a.slope * np.nan_to_num(sd), hw)
        land_side = np.nan_to_num(sd) >= 0
        floor = np.where(t['beach'][W], G['beach_floor_m'], G['land_floor_m'])
        want = np.where(land_side, np.maximum(np.maximum(want, L + G['freeboard_m']), floor),
                        np.minimum(want, L - G['depth_min_m']))
        counts['capped'] += int((edit & ((want > hw + a.max_raise) | (want < hw - a.max_lower))).sum())
        want = np.clip(want, hw - a.max_lower, hw + a.max_raise)
        # an input that already breaks a gate can still end between the two: snap with a margin that survives float32,
        # and keep the move caps (such a vertex then stays on its old side)
        dead = (want > L - G['depth_min_m']) & (want < L + G['freeboard_m'])
        want = np.where(dead, np.where(want >= L, L + G['freeboard_m'] + EPS, L - G['depth_min_m'] - EPS), want)
        want = np.where(dead, np.clip(want, hw - a.max_lower, hw + a.max_raise), want)
        hv, cv, lv, iv = h1[W], cls1[W], level1[W], ids1[W]
        hv[edit] = want[edit]
        to_water = edit & lw & (want < L)
        to_land = edit & B & (want >= L)
        cv[to_water], lv[to_water], iv[to_water] = k, L, i
        cv[to_land], lv[to_land], iv[to_land] = 0, np.nan, 0
        masks['band'][W] |= band
        masks['forced'][W] |= forced
        masks['editable'][W] |= edit
        profiled[i] = True
        counts['profiled'] += 1
        rows.append(dict(id=i, level_m=round(L, 3), cls=k, vertices=nb, forced=int(forced.sum()),
                         changed=int((edit & (want != hw)).sum()), to_water=int(to_water.sum()),
                         to_land=int(to_land.sum())))

    # undo steepened land faces; reverted vertices get their classes back
    h2, faces = discard_steeper_land_faces(h1, h0, cls1)
    reverted = (h2 != h1.astype('float32').astype(float)) & (h2 == h0.astype('float32').astype(float))
    cls1[reverted], level1[reverted], ids1[reverted] = cls0[reverted], level0[reverted], ids[reverted]
    h2 = h2.astype('float32').astype(np.float64)

    # bed floor on the profiled bodies, navigable corridors, the Narva zone and the map border excepted: beyond the
    # border the engine continues the terrain from its edge, and a lake bed raised there above the sea drew a flat
    # untextured surface outside the map (v7 run 06e14fcf, lake 202); with the edge kept deep the sea continues the lake
    bed = np.zeros((N, N), bool)
    if a.bed_floor is not None:
        body = profiled[ids1] & (ids1 > 0) & np.isin(cls1, STANDING) & ~corridor & ~narva & ~border
        with np.errstate(invalid='ignore'):
            need = np.minimum(a.bed_floor, level1 - a.bed_min_depth)
            bed = body & (h2 < need)
        h2[bed] = need[bed]
        h2 = h2.astype('float32').astype(np.float64)
    beach1 = (t['beach'] | ((cls1 == 0) & (h2 < G['land_floor_m'] - 1e-6))) & (cls1 == 0) & ~narva
    changed = h2 != h0.astype('float32').astype(np.float64)
    assert not np.any(changed & fixed & ~bed), 'protected height changed'
    assert not np.any((cls1 != cls0) & fixed), 'protected class changed'

    # waterline turn of the profiled bodies inside their bands: zero lines of h - L, L of the nearest body water
    above = profiled[ids] & (ids > 0)
    _, j = ndimage.distance_transform_edt(~above, return_indices=True)
    lev_near = np.where(above, level0, np.nan)[j[0], j[1]]
    zone = masks['band']
    out = dict(t)
    out['heights'] = h2.astype(t['heights'].dtype)
    out['cls'] = cls1
    out['level'] = level1.astype(t['level'].dtype)
    out['water'] = cls1 > 0
    out['beach'] = beach1
    rows.sort(key=lambda r: -r['vertices'])
    d = h2 - h0
    rep = {
        'bodies': {'labelled': int(sum(1 for s in objs if s is not None)), 'profiled': counts['profiled'],
                   'skipped_small': counts['skipped_small'], 'skipped_at_or_below_plane_cut': counts['skipped_low'],
                   'skipped_no_outline': counts['skipped_no_outline'],
                   'claimed_twice_vertices': int((claims >= 2).sum())},
        'vertices': {'band': int(masks['band'].sum()), 'editable': int(masks['editable'].sum()),
                     'forced': int(masks['forced'].sum()), 'changed': int(changed.sum()),
                     'to_water': int(((cls0 == 0) & (cls1 != 0)).sum()), 'to_land': int(((cls0 != 0) & (cls1 == 0)).sum()),
                     'forced_at_move_cap': counts['capped'], 'bed_raised': int(bed.sum()), 'face_recovery': faces},
        'crossing_offset_m_vs_smoothed_outline': {'before': offsets(h0, edges), 'after': offsets(h2, edges)},
        'waterline_turn_deg_per_12m': {'before': turning(zero_lines(h0 - lev_near, zone)),
                                       'after': turning(zero_lines(h2 - lev_near, zone)),
                                       'note': 'turn per 12 m grows where a staircase becomes a curve; read the '
                                               'crossing offsets for the fit to the outline'},
        'gates': {'before': gates(h0, cls0, level0, t['beach'], narva600),
                  'after': gates(h2, cls1, level1, beach1, narva600)},
        'standing_bed_below_0p85': {'before': int((np.isin(cls0, STANDING) & (level0 > G['plane_cut_m']) & (h0 < 0.85)).sum()),
                                    'after': int((np.isin(cls1, STANDING) & (level1 > G['plane_cut_m']) & (h2 < 0.85)).sum())},
        'largest_bodies': rows[:10],
        'change_m': {'raise_max': round(float(d.max()), 3), 'lower_max': round(float(-d.min()), 3)}}
    return out, dict(masks, changed=changed, bed_raised=bed), rep


def selftest():
    n = N
    h = np.full((n, n), 3.0, np.float32)
    cls = np.zeros((n, n), np.uint8)
    level = np.full((n, n), np.nan, np.float32)
    r, c = np.mgrid[0:n, 0:n]
    lake_a = (np.maximum(abs(r - 1000), abs(c - 1000)) <= 40) & (abs(r - 1000) + abs(c - 1000) <= 60)
    island = np.maximum(abs(r - 1005), abs(c - 997)) <= 6
    lake_a &= ~island
    lake_b = np.maximum(abs(r - 1000), abs(c - 1120)) <= 8
    river = (c == 1300) & (r >= 900) & (r <= 1100)
    for m, k, lv, bed in ((lake_a, 2, 2.0, 1.0), (lake_b, 2, 2.5, 1.5), (river, 5, 2.2, 1.9)):
        cls[m], level[m], h[m] = k, lv, bed
    zero = np.zeros((n, n), bool)
    t = dict(heights=h, cls=cls, level=level, platform=zero, reserve=zero, narva=zero, water=cls > 0, beach=zero)
    a = argparse.Namespace(slope=0.15, band=12.0, sigma=12.0, max_shift=4.0, min_vertices=4, max_raise=2.0,
                           max_lower=1.5, bed_floor=None, bed_min_depth=0.30, narva_radius=620.0)
    out, masks, rep = profile(t, zero, zero, a)
    print(json.dumps({k: rep[k] for k in ('bodies', 'vertices', 'crossing_offset_m_vs_smoothed_outline', 'gates')}, indent=1))
    assert all(v == 0 for v in rep['gates']['after'].values()), rep['gates']
    near = ndimage.distance_transform_edt(~(lake_a | lake_b)) * 6.0 <= 22.0
    assert not np.any(masks['changed'] & ~near), 'change far from the lakes'
    keep = ndimage.distance_transform_edt(~river) * 6.0 <= 22.0
    assert np.array_equal(out['heights'][keep], h[keep]) and np.array_equal(out['cls'][keep], cls[keep]), 'river touched'
    ob, oa = rep['crossing_offset_m_vs_smoothed_outline']['before'], rep['crossing_offset_m_vs_smoothed_outline']['after']
    assert oa['p90'] < ob['p90'] and oa['no_crossing'] == 0, (ob, oa)
    assert np.any((out['cls'] == 0) & (np.maximum(abs(r - 1005), abs(c - 997)) <= 6)), 'island lost'
    a.bed_floor = 1.5
    out2, _, _ = profile(t, zero, zero, a)
    wa = (out2['cls'] == 2) & (np.abs(out2['level'] - 2.0) < 1e-6)
    assert wa.any() and out2['heights'][wa].min() >= 1.5 - 1e-6, out2['heights'][wa].min()
    print('SELFTEST PASS')


def main():
    if '--selftest' in sys.argv:
        selftest()
        return
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--terrain', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--slope', type=float, default=0.15)
    ap.add_argument('--band', type=float, default=12.0)
    ap.add_argument('--sigma', type=float, default=12.0)
    ap.add_argument('--max-shift', type=float, default=4.0)
    ap.add_argument('--min-vertices', type=int, default=4)
    ap.add_argument('--max-raise', type=float, default=2.0)
    ap.add_argument('--max-lower', type=float, default=1.5)
    ap.add_argument('--bed-floor', type=float, default=None)
    ap.add_argument('--bed-min-depth', type=float, default=0.30)
    ap.add_argument('--narva-radius', type=float, default=620.0)
    a = ap.parse_args()
    assert not a.out.exists(), 'fresh output required'
    t0 = time.time()
    t = dict(np.load(a.terrain))
    planes = cell_planes(t['cls'], t['level'])
    _, corridor, entries, _ = protect_corridors(planes)
    nature = np.load(NATURE)['reserve'].astype(bool)
    out, masks, rep = profile(t, nature, corridor, a)
    a.out.mkdir(parents=True)
    np.savez_compressed(a.out / 'terrain_lakes.npz', **out)
    np.savez_compressed(a.out / 'masks.npz', **masks)
    rep = {'status': 'BUILT_PENDING_GATES_AND_ENGINE_VIEWS',
           'params': {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(a).items() if k not in ('terrain', 'out')},
           **rep, 'protected_corridors': len(entries),
           'inputs': {str(p): sha(p) for p in (a.terrain, NATURE, Path(__file__))},
           'output_sha256': sha(a.out / 'terrain_lakes.npz'), 'seconds': round(time.time() - t0, 1),
           'limits': ['Standing bodies above the 0.80 m plane cut; contacts, flowing water and the sea untouched.',
                      'Water tiles must be patched for the changed cells; gates and engine views decide acceptance.']}
    (a.out / 'report.json').write_text(json.dumps(rep, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in rep.items() if k != 'inputs'}, indent=1))


if __name__ == '__main__':
    main()

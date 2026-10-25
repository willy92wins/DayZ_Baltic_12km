"""Shore profile for every standing water body of a V30 terrain: lakes, ponds, islands included.

A lake's water is a flat plane at the body level L, drawn by water objects; the visible shore is where the
terrain (6 m grid, NW-SE diagonals) crosses that plane. Wet vertices sit ~0.3 m below L and land ~0.4 m above
it, so the crossing falls at a fixed fraction of every wet-land edge and the shore draws the 6 m grid:
serrated coasts and pointy islands. The sea already got this treatment (profile_coast_v30.py); this tool
applies the same method per standing body, each with its own level.
1. Bodies: census labelling (classes 2 and 7, centimetre level, 8-connected). Bodies with >= --min-vertices
   vertices and a level above the 0.80 m sea cut are profiled; every body, however small, claims a
   --band + --max-shift + 6 m strip around itself, and vertices claimed by two bodies are fixed.
2. Outline per body, in a window around it: signed distance to the body (negative inside), Gaussian-smoothed
   (--sigma m) and clamped so the zero line moves at most --max-shift; then the exact distance to its zero
   contour, signed by the smoothed field (positive on land).
3. Profile: target = L + --slope * sd within --band. A vertex ending a native edge (east, south, NW-SE
   diagonal) whose ends lie on opposite sides takes the target, so the waterline at the lake level follows
   the outline, within the gates of verify_terrain_v30.py: wet at least --depth-min under L, land at least
   --freeboard over it (0.80 m on the old beach strip, else the 1.40 m land floor), each move capped
   (--max-raise / --max-lower), no vertex left between the two gates. Classes and levels follow the heights:
   land below L becomes water of the body class at level L; body vertices at or above L become land.
4. Bed floor: with --bed-floor F the bed of a profiled body rises to min(F, L - --bed-min-depth), so the
   engine never draws its own sea (0.65-0.85 m) through a lake.
5. Edits that make a land face steeper than 35 degrees (or than it was) are undone; the beach mask is
   re-authored as every land vertex below the 1.40 m floor.
Fixed: platforms, reserves, the nature envelope, the 24 m corridors, the Narva identity zone (--narva-radius),
the map border, the sea and all flowing water with their margin, and vertices claimed by two bodies.
Usage: profile_lakes_v30.py --terrain IN.npz --out OUTDIR [--slope 0.15] [--band 12] [--sigma 12]
                           [--max-shift 4] [--min-vertices 9] [--freeboard 0.05] [--depth-min 0.10]
                           [--max-raise 2.0] [--max-lower 1.5] [--bed-floor F] [--bed-min-depth 0.30]
                           [--narva-radius 620]
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
from profile_coast_v30 import EDGES, GATES, NATURE, NARVA, sha, turning, zero_lines  # noqa: E402,F401
from relevel_bodies_v30 import label_bodies  # noqa: E402

EPS = 1e-4              # headroom: verify_terrain_v30.py compares depth and bank clearance strictly on float32
EPSDZ = 1e-9            # keeps the dead-zone snap inclusive of the exact gate values
BANK_RADIUS_M = 8.5
BANK_MIN_M = 0.05
SLOPE_MAX_DEG = 35.01
NARVA_EXCLUDED_M = 600.0

DEFAULTS = dict(slope=0.15, band=12.0, sigma=12.0, max_shift=4.0, min_vertices=9, freeboard=0.05,
                depth_min=0.10, max_raise=2.0, max_lower=1.5, bed_floor=None, bed_min_depth=0.30,
                narva_radius=620.0)


def grow(sl, g):
    return (slice(max(sl[0].start - g, 0), min(sl[0].stop + g, N)),
            slice(max(sl[1].start - g, 0), min(sl[1].stop + g, N)))


def disc(radius):
    d = np.arange(-radius, radius + 1)
    yy, xx = np.meshgrid(d, d, indexing='ij')
    return (yy * yy + xx * xx) <= radius * radius


def window_lines(field, mask, r0, r1, c0, c1):
    """Zero contours of a window field restricted to mask, in game coordinates (zero_lines, per window)."""
    z = np.ma.masked_invalid(np.where(mask, field, np.nan))
    gen = contourpy.contour_generator(x=np.arange(c0, c1) * 6.0, y=12282.0 - np.arange(r0, r1) * 6.0, z=z,
                                      line_type=contourpy.LineType.Separate)
    return [ln for ln in gen.lines(0.0) if len(ln) >= 2]


def signed_distance(lines, xw, zw, near, smooth):
    segs = np.concatenate([np.stack([ln[:-1], ln[1:]], axis=1) for ln in lines])
    tree = shapely.STRtree(shapely.linestrings(segs))
    _, dist = tree.query_nearest(shapely.points(xw[near], zw[near]), return_distance=True, all_matches=False)
    sd = np.full(xw.shape, np.nan)
    sd[near] = np.where(smooth[near] < 0, -dist, dist)
    return sd


def gate_fails(h, cls, level, beach, zone):
    """Failure counts exactly as verify_terrain_v30.py computes them."""
    water = cls > 0
    m = water & ~zone
    with np.errstate(invalid='ignore'):
        wd = int((level[m] - h[m] < 0.10).sum())
    dist, idx = ndimage.distance_transform_edt(~water, sampling=6.0, return_indices=True)
    near_lv = level[idx[0], idx[1]]
    b = (~water) & (dist <= BANK_RADIUS_M) & ~zone
    with np.errstate(invalid='ignore'):
        bk = int(((h[b] - near_lv[b]) < BANK_MIN_M).sum())
    inland = (~water) & ~zone & ~beach
    lf = int((h[inland] < GATES['land_floor_m'] - 1e-6).sum())
    bf = int((h[beach] < GATES['beach_floor_m'] - 1e-6).sum())
    plane = cell_planes(cls, level)
    czone = zone[:-1, :-1] | zone[:-1, 1:] | zone[1:, :-1] | zone[1:, 1:]
    n = h.shape[0]
    pw = pl = 0
    for dr in (0, 1):
        for dc in (0, 1):
            hc = h[dr:dr + n - 1, dc:dc + n - 1]
            wc = water[dr:dr + n - 1, dc:dc + n - 1]
            ok = np.isfinite(plane) & ~czone
            with np.errstate(invalid='ignore'):
                pw += int((ok & wc & (hc > plane - 0.02)).sum())
                pl += int((ok & ~wc & (hc < plane)).sum())
    nw, ne, sw, se = h[:-1, :-1], h[:-1, 1:], h[1:, :-1], h[1:, 1:]
    au = np.degrees(np.arctan(np.hypot((ne - nw) / 6.0, (se - ne) / 6.0)))
    al = np.degrees(np.arctan(np.hypot((sw - nw) / 6.0, (se - sw) / 6.0)))
    land = ~water
    lnw, lne, lsw, lse = land[:-1, :-1], land[:-1, 1:], land[1:, :-1], land[1:, 1:]
    mu, ml = lnw & lne & lse, lnw & lsw & lse
    ang = np.r_[au[mu], al[ml]]
    sl = int((ang > SLOPE_MAX_DEG).sum())
    return dict(water_depth=wd, banks=bk, land_floor=lf, beach=bf, pieces=pw + pl, slopes=sl)


def run_core(t, nature, corridor, p):
    """Shore profile of every standing body. Returns (output terrain dict, full-grid masks, report dict)."""
    h0 = t['heights'].astype(np.float64)
    cls0 = t['cls'].copy()
    level0 = t['level'].astype(np.float64)
    beach0 = t['beach'].astype(bool)
    x, z = grid_xz()
    sea0 = np.isin(cls0, (1, 4))
    flowing0 = np.isin(cls0, (3, 5, 6))
    land0 = cls0 == 0
    ids = label_bodies(cls0, level0)
    nb = int(ids.max())
    objs = ndimage.find_objects(ids) if nb else []
    R_m = p['band'] + p['max_shift'] + 6.0
    gp = int(np.ceil(R_m / 6.0))
    Wv = int(np.ceil((R_m + 3.0 * p['sigma'] + 12.0) / 6.0))
    st = disc(gp)

    # bodies: level, class, size; every body claims its strip, however small
    info = {}
    claim = np.zeros((N, N), np.uint8)
    for bid in range(1, nb + 1):
        sl = objs[bid - 1]
        slc = grow(sl, gp)
        claim[slc] += ndimage.binary_dilation(ids[slc] == bid, structure=st)
        m = ids[sl] == bid
        info[bid] = dict(sl=sl, n=int(m.sum()), level=float(np.median(level0[sl][m])),
                         cls=int(np.bincount(cls0[sl][m]).argmax()))
    claimed_twice = claim >= 2

    narva_zone = np.hypot(x - NARVA[0], z - NARVA[1]) <= p['narva_radius']
    flow = sea0 | flowing0
    fixed = (t['platform'].astype(bool) | t['reserve'].astype(bool) | nature | corridor | narva_zone
             | (x < 12) | (z < 12) | (x > 12270) | (z > 12270) | flow
             | (ndimage.distance_transform_edt(~flow) * 6.0 <= R_m) | claimed_twice)

    h1, cls1, level1 = h0.copy(), cls0.copy(), level0.copy()
    band_f = np.zeros((N, N), bool)
    forced_f = np.zeros((N, N), bool)
    editable_f = np.zeros((N, N), bool)
    to_water_f = np.zeros((N, N), bool)
    to_land_f = np.zeros((N, N), bool)
    eid = np.zeros((N, N), np.int32)    # editable band -> body id
    eidw = np.zeros((N, N), np.int32)   # water of a profiled body (after step 3) -> body id
    band_specs = []
    per_body = {}
    fb = p['freeboard'] + EPS
    dm = p['depth_min'] + EPS
    capped_n = 0
    skipped_no = 0
    attempted = [b for b in info if info[b]['n'] >= p['min_vertices'] and info[b]['level'] > 0.80]

    for bid in attempted:
        B = info[bid]
        L = B['level']
        r0, r1 = max(B['sl'][0].start - Wv, 0), min(B['sl'][0].stop + Wv, N)
        c0, c1 = max(B['sl'][1].start - Wv, 0), min(B['sl'][1].stop + Wv, N)
        Bw = ids[r0:r1, c0:c1] == bid
        # signed distance to the body, as class_sd in profile_coast (negative inside)
        base = np.where(Bw, -ndimage.distance_transform_edt(Bw),
                        ndimage.distance_transform_edt(~Bw)) * 6.0
        smooth = ndimage.gaussian_filter(base, p['sigma'] / 6.0)
        smooth = np.clip(smooth, base - p['max_shift'], base + p['max_shift'])
        near = np.abs(base) <= p['band'] + p['max_shift'] + 9.0
        lines = window_lines(smooth, near, r0, r1, c0, c1)
        if not lines:
            skipped_no += 1
            continue
        xw, zw = x[r0:r1, c0:c1], z[r0:r1, c0:c1]
        with np.errstate(invalid='ignore'):
            sd = signed_distance(lines, xw, zw, near, smooth)
            band_B = near & (np.abs(sd) <= p['band'])
        land0w = land0[r0:r1, c0:c1]
        editable_B = band_B & (Bw | land0w) & ~fixed[r0:r1, c0:c1]
        forced_w = np.zeros(Bw.shape, bool)
        H, W = Bw.shape
        with np.errstate(invalid='ignore'):
            bl = Bw | land0w
            for dr, dc in EDGES:
                ra, ca = np.meshgrid(np.arange(H - dr), np.arange(W - dc), indexing='ij')
                rb, cb = ra + dr, ca + dc
                sa, sb = sd[ra, ca], sd[rb, cb]
                cross = np.isfinite(sa) & np.isfinite(sb) & (sa * sb < 0) & bl[ra, ca] & bl[rb, cb]
                forced_w[ra[cross], ca[cross]] = True
                forced_w[rb[cross], cb[cross]] = True
        forced_w &= editable_B

        h0w = h0[r0:r1, c0:c1]
        want = np.where(forced_w, L + p['slope'] * sd, h0w)
        land_side = sd >= 0
        floorw = np.where(beach0[r0:r1, c0:c1], GATES['beach_floor_m'], GATES['land_floor_m'])
        with np.errstate(invalid='ignore'):
            want = np.where(land_side, np.maximum(np.maximum(want, L + fb), floorw),
                            np.minimum(want, L - dm))
            capped = editable_B & ((want > h0w + p['max_raise']) | (want < h0w - p['max_lower']))
            want = np.clip(want, h0w - p['max_lower'], h0w + p['max_raise'])
            # no vertex may end between the two gates (too shallow for water, too low for the shore)
            dead = (want > L - p['depth_min'] - EPSDZ) & (want < L + p['freeboard'] + EPSDZ)
            want = np.where(dead, np.where(want >= L, L + fb, L - dm), want)
        capped_n += int(capped.sum())

        hv = h1[r0:r1, c0:c1]
        hv[editable_B] = want[editable_B]
        cv = cls1[r0:r1, c0:c1]
        lv1 = level1[r0:r1, c0:c1]
        to_water_w = editable_B & land0w & (want < L)
        to_land_w = editable_B & Bw & (want >= L)
        cv[to_water_w] = B['cls']
        lv1[to_water_w] = L
        cv[to_land_w] = 0
        lv1[to_land_w] = np.nan
        ew = eidw[r0:r1, c0:c1]
        ew[(Bw | to_water_w) & (cv > 0)] = bid
        eid[r0:r1, c0:c1][editable_B] = bid
        band_f[r0:r1, c0:c1] |= band_B
        forced_f[r0:r1, c0:c1] |= forced_w
        editable_f[r0:r1, c0:c1] |= editable_B
        to_water_f[r0:r1, c0:c1] |= to_water_w
        to_land_f[r0:r1, c0:c1] |= to_land_w
        band_specs.append((r0, r1, c0, c1, band_B, L))
        per_body[bid] = dict(to_water=int(to_water_w.sum()), to_land=int(to_land_w.sum()))

    # bed floor: the engine draws its sea (0.65-0.85 m) under any lake whose bed lies below it
    bed_raised = np.zeros((N, N), bool)
    if p['bed_floor'] is not None:
        g = int(np.ceil((p['band'] + p['max_shift']) / 6.0)) + 2
        for bid in per_body:
            slg = grow(info[bid]['sl'], g)
            tgt = min(p['bed_floor'], info[bid]['level'] - p['bed_min_depth'])
            mw = (eidw[slg] == bid) & ~corridor[slg] & ~narva_zone[slg]
            hv = h1[slg]
            old = hv[mw]
            hv[mw] = np.maximum(old, tgt)
            bed_raised[slg][mw] = tgt > old

    # undo edits that steepen land faces beyond 35 degrees (classes of reverted vertices go back too)
    h2, faces = discard_steeper_land_faces(h1, h0, cls1)
    h0f = h0.astype('float32').astype(np.float64)
    reverted = (h2 != h1.astype('float32').astype(float)) & (h2 == h0f)
    cls1[reverted] = cls0[reverted]
    level1[reverted] = level0[reverted]
    h = h2.astype('float32').astype(np.float64)
    changed = h != h0f
    bed_raised &= changed
    assert not np.any(changed & fixed & ~bed_raised), 'protected height changed'
    beach1 = (beach0 | ((cls1 == 0) & (h < GATES['land_floor_m'] - 1e-6))) & (cls1 == 0) & ~narva_zone

    lines_b, lines_a = [], []
    for (r0, r1, c0, c1, band_B, L) in band_specs:
        lines_b += window_lines(h0[r0:r1, c0:c1] - L, band_B, r0, r1, c0, c1)
        lines_a += window_lines(h[r0:r1, c0:c1] - L, band_B, r0, r1, c0, c1)

    zone600 = np.hypot(x - NARVA[0], z - NARVA[1]) <= NARVA_EXCLUDED_M
    gb = gate_fails(h0, cls0, level0, beach0, zone600)
    ga = gate_fails(h, cls1, level1, beach1, zone600)

    d = h - h0
    largest = []
    for b in sorted(per_body, key=lambda v: -info[v]['n'])[:10]:
        sel = (eid == b) | (eidw == b)
        largest.append({'id': int(b), 'level_m': round(info[b]['level'], 3), 'class': int(info[b]['cls']),
                        'vertices': info[b]['n'], 'changed': int((changed & sel).sum()),
                        'to_water': per_body[b]['to_water'], 'to_land': per_body[b]['to_land']})
    rep = {
        'status': 'BUILT_PENDING_GATES_AND_ENGINE_VIEWS',
        'params': dict(p),
        'bodies': {'profiled': len(per_body), 'skipped_small': nb - len(attempted),
                   'skipped_no_outline': skipped_no, 'claimed_twice_vertices': int(claimed_twice.sum())},
        'vertices': {'band': int(band_f.sum()), 'editable': int(editable_f.sum()), 'forced': int(forced_f.sum()),
                     'changed': int(changed.sum()), 'to_water': int(to_water_f.sum()),
                     'to_land': int(to_land_f.sum()), 'forced_at_move_cap': capped_n,
                     'bed_raised': int(bed_raised.sum()), 'face_recovery': faces},
        'waterline_turn_deg_per_12m': {'before': turning(lines_b), 'after': turning(lines_a)},
        'gates': {k: {'before': gb[k], 'after': ga[k]}
                  for k in ('water_depth', 'banks', 'land_floor', 'beach', 'pieces', 'slopes')},
        'largest_bodies': largest,
        'change_m': {'raise_max': round(float(d.max()), 3), 'lower_max': round(float(-d.min()), 3)},
    }
    out = dict(t)
    out['heights'] = h.astype(t['heights'].dtype)
    out['cls'] = cls1
    out['level'] = level1.astype(t['level'].dtype)
    out['water'] = cls1 > 0
    out['beach'] = beach1
    masks = dict(band=band_f, forced=forced_f, editable=editable_f, changed=changed, bed_raised=bed_raised)
    return out, masks, rep


def build_synthetic():
    h = np.full((N, N), 3.0)
    cls = np.zeros((N, N), np.uint8)
    level = np.full((N, N), np.nan)
    rr, cc = np.meshgrid(np.arange(N), np.arange(N), indexing='ij')
    dr, dc = rr - 1000, cc - 1000
    lakeA = (np.maximum(np.abs(dr), np.abs(dc)) <= 40) & (np.abs(dr) + np.abs(dc) <= 60)
    island = np.maximum(np.abs(rr - 1005), np.abs(cc - 997)) <= 6
    lakeB = np.maximum(np.abs(rr - 1000), np.abs(cc - 1120)) <= 8
    river = (cc == 1300) & (rr >= 900) & (rr <= 1100)
    cls[lakeA], level[lakeA], h[lakeA] = 2, 2.0, 1.0
    cls[island], level[island], h[island] = 0, np.nan, 3.0
    cls[lakeB], level[lakeB], h[lakeB] = 2, 2.5, 1.0
    cls[river], level[river], h[river] = 5, 2.2, 1.9
    false = np.zeros((N, N), bool)
    t = {'heights': h.astype(np.float32), 'cls': cls, 'level': level.astype(np.float32),
         'platform': false.copy(), 'reserve': false.copy(), 'narva': false.copy(),
         'water': cls > 0, 'beach': false.copy()}
    return t, lakeA, lakeB, river


def selftest():
    t, lakeA, lakeB, river = build_synthetic()
    zeros = np.zeros((N, N), bool)
    out, masks, rep = run_core(t, zeros, zeros, dict(DEFAULTS))
    assert all(g['after'] == 0 for g in rep['gates'].values()), rep['gates']
    h0 = t['heights'].astype(np.float64)
    reach = 12.0 + 4.0 + 6.0
    far = ndimage.distance_transform_edt(~(lakeA | lakeB)) * 6.0 > reach + 1e-6
    assert not np.any(masks['changed'] & far), 'edit beyond the claim radius'
    nr = ndimage.distance_transform_edt(~river) * 6.0 <= reach
    assert np.array_equal(out['heights'].astype(np.float64)[nr], h0[nr]), 'river heights changed'
    assert np.array_equal(out['cls'][nr], t['cls'][nr]), 'river classes changed'
    assert np.allclose(out['level'].astype(np.float64)[nr], t['level'].astype(np.float64)[nr], equal_nan=True)
    wt = rep['waterline_turn_deg_per_12m']
    assert wt['after']['p95'] < wt['before']['p95'], wt
    assert np.any(out['cls'][999:1012, 991:1004] == 0), 'island lost'
    out2, _, _ = run_core(t, zeros, zeros, dict(DEFAULTS, bed_floor=1.5))
    wetA = (out2['cls'] > 0) & lakeA
    assert bool((out2['heights'].astype(np.float64)[wetA] >= 1.5).all()), 'bed floor not applied'
    print('SELFTEST PASS')
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--terrain', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--slope', type=float, default=DEFAULTS['slope'])
    ap.add_argument('--band', type=float, default=DEFAULTS['band'])
    ap.add_argument('--sigma', type=float, default=DEFAULTS['sigma'])
    ap.add_argument('--max-shift', type=float, default=DEFAULTS['max_shift'])
    ap.add_argument('--min-vertices', type=int, default=DEFAULTS['min_vertices'])
    ap.add_argument('--freeboard', type=float, default=DEFAULTS['freeboard'])
    ap.add_argument('--depth-min', type=float, default=DEFAULTS['depth_min'])
    ap.add_argument('--max-raise', type=float, default=DEFAULTS['max_raise'])
    ap.add_argument('--max-lower', type=float, default=DEFAULTS['max_lower'])
    ap.add_argument('--bed-floor', type=float, default=DEFAULTS['bed_floor'])
    ap.add_argument('--bed-min-depth', type=float, default=DEFAULTS['bed_min_depth'])
    ap.add_argument('--narva-radius', type=float, default=DEFAULTS['narva_radius'])
    a = ap.parse_args()
    assert not a.out.exists(), 'fresh output required'
    t0 = time.time()
    t = dict(np.load(a.terrain))
    nature = np.load(NATURE)['reserve'].astype(bool)
    _, corridor, _, _ = protect_corridors(cell_planes(t['cls'], t['level'].astype(np.float64)))
    p = {k: getattr(a, k) for k in DEFAULTS}
    out, masks, rep = run_core(t, nature, corridor, p)
    a.out.mkdir(parents=True)
    np.savez_compressed(a.out / 'terrain_lakes.npz', **out)
    np.savez_compressed(a.out / 'masks.npz', **masks)
    rep['inputs'] = {str(pa): sha(pa) for pa in (a.terrain, NATURE, Path(__file__))}
    rep['output_sha256'] = sha(a.out / 'terrain_lakes.npz')
    rep['seconds'] = round(time.time() - t0, 1)
    (a.out / 'report.json').write_text(json.dumps(rep, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in rep.items() if k != 'inputs'}, indent=1))


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        sys.exit(selftest())
    main()

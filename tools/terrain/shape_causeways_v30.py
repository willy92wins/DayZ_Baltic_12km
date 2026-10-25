"""Causeways V30: rebuild road causeways over the sea as embankments on the road centre line.

The Kronstadt dam is the only road on a causeway over the sea (the other road sections with water on both sides are
bridges, whose centre line lies below the water). Its land is the road platform raster of build_v30.py: 12 to 24 m
wide in 6 m steps, crest at 1.45-1.53 m, inside the band the engine darkens (evidence/v30-v5-candidate-2026-10-05).
profile_coast_v30.py keeps platforms fixed, so the steps stay.

1. Sections: road samples every 0.5 m (verify_roads_v30.road_chains) with sea (classes 1 and 4) within --reach m on
   both sides and the centre line at or above the sea level, at least --min-length long (gaps under 20 m closed).
2. Crest: target = max(road profile, --crest) along each section; over --ramp m beyond each end the target falls
   linearly back to the road profile.
3. Embankment: height = target - --slope * (d - --half-width) beyond the crest, d the distance to the centre line.
   Where the axis has sea within --narrow m on both sides, the sea and the road's own platform and reserve below
   --crest + 0.5 m are rebuilt: new = max(embankment, smoothed sea bed), which removes the old steps. Everywhere else
   (the ends on Kotlin and on the shore, higher ground, the ramps) the embankment only fills.
4. Gates as profile_coast_v30.py: sea at least 0.10 m deep, land at least the 0.80 m beach floor, no vertex between
   the two; classes follow the heights (sea below 0.75 m); edits that steepen a land face beyond 35 degrees are
   undone; land below 1.40 m joins the beach mask and the crest joins the platform mask. Pond classes, pond planes,
   navigable corridors, the Narva zone and the map border stay fixed.
Usage: shape_causeways_v30.py --terrain IN.npz --out OUTDIR [--crest 1.70] [--half-width 10] [--slope 0.5]
                              [--reach 30] [--narrow 24] [--min-length 60] [--ramp 80]
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'terrain'))
from v30_common import N, POND_CLASSES, cell_planes, grid_xz, tri_sample, vertex_plane_bounds  # noqa: E402
from finish_shores_v30 import discard_steeper_land_faces, protect_corridors  # noqa: E402
from profile_coast_v30 import GATES, NARVA, SEA_CLASSES, sha, turning, zero_lines  # noqa: E402
from verify_roads_v30 import road_chains  # noqa: E402

STEP = 0.5


def to_rc(p):
    return (np.clip(np.rint((12282 - p[:, 1]) / 6).astype(int), 0, N - 1),
            np.clip(np.rint(p[:, 0] / 6).astype(int), 0, N - 1))


def find_sections(h, sea, a):
    """Causeway runs of every road chain: (chain, axis samples, road profile, target crest, core flag)."""
    out = []
    for n, p in enumerate(road_chains()):
        if len(p) < 2:
            continue
        st = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
        s = np.arange(0, st[-1], STEP)
        if len(s) < 3:
            continue
        q = np.column_stack([np.interp(s, st, p[:, d]) for d in (0, 1)])
        tg = np.gradient(q, axis=0)
        nrm = np.column_stack([-tg[:, 1], tg[:, 0]]) / np.maximum(np.linalg.norm(tg, axis=1)[:, None], 1e-9)
        left, right = np.zeros(len(q), bool), np.zeros(len(q), bool)
        nl, nr = np.zeros(len(q), bool), np.zeros(len(q), bool)
        for off in np.arange(6.0, a.reach + 0.1, 3.0):
            wl, wr = sea[to_rc(q + nrm * off)], sea[to_rc(q - nrm * off)]
            left |= wl
            right |= wr
            if off <= a.narrow:
                nl |= wl
                nr |= wr
        narrow = nl & nr
        idx = np.flatnonzero(left & right)
        if idx.size == 0:
            continue
        runs, start, prev = [], idx[0], idx[0]
        for i in idx[1:]:
            if (i - prev) * STEP > 20.0:
                runs.append((start, prev))
                start = i
            prev = i
        runs.append((start, prev))
        prof = tri_sample(h, q[:, 0], q[:, 1])
        for i0, i1 in runs:
            if (i1 - i0) * STEP < a.min_length or np.median(prof[i0:i1 + 1]) < a.sea:
                continue
            r = int(round(a.ramp / STEP))
            j0, j1 = max(i0 - r, 0), min(i1 + r, len(q) - 1)
            w = np.ones(j1 - j0 + 1)
            k = np.arange(j0, j1 + 1)
            w[k < i0] = 1 - (i0 - k[k < i0]) * STEP / a.ramp
            w[k > i1] = 1 - (k[k > i1] - i1) * STEP / a.ramp
            target = np.maximum(prof[j0:j1 + 1], a.crest * w + prof[j0:j1 + 1] * (1 - w))
            out.append(dict(chain=n, s0=float(s[i0]), s1=float(s[i1]), axis=q[j0:j1 + 1], profile=prof[j0:j1 + 1],
                            target=target, core=(k >= i0) & (k <= i1),
                            narrow=narrow[j0:j1 + 1] & (k >= i0) & (k <= i1)))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--terrain', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--sea', type=float, default=0.75)
    ap.add_argument('--crest', type=float, default=1.70)
    ap.add_argument('--half-width', type=float, default=10.0)
    ap.add_argument('--slope', type=float, default=0.5)
    ap.add_argument('--reach', type=float, default=30.0)
    ap.add_argument('--narrow', type=float, default=24.0)
    ap.add_argument('--min-length', type=float, default=60.0)
    ap.add_argument('--ramp', type=float, default=80.0)
    a = ap.parse_args()
    assert not a.out.exists(), 'fresh output required'
    t0 = time.time()
    t = dict(np.load(a.terrain))
    h0 = t['heights'].astype(np.float64)
    cls0, level0 = t['cls'].copy(), t['level'].astype(np.float64)
    x, z = grid_xz()
    sea0 = np.isin(cls0, SEA_CLASSES)
    land0 = cls0 == 0
    planes = cell_planes(cls0, level0)
    _, corridor, _, _ = protect_corridors(planes)
    pmin, pmax = vertex_plane_bounds(planes)
    narva_zone = np.hypot(x - NARVA[0], z - NARVA[1]) <= GATES['narva_radius_m']
    fixed = (np.isin(cls0, POND_CLASSES) | np.isfinite(pmin) | np.isfinite(pmax) | corridor | narva_zone
             | (x < 12) | (z < 12) | (x > 12270) | (z > 12270))
    editable = (land0 | sea0) & ~fixed

    secs = find_sections(h0, sea0, a)
    assert secs, 'no causeway section found'
    axis = np.concatenate([d['axis'] for d in secs])
    target = np.concatenate([d['target'] for d in secs])
    core = np.concatenate([d['core'] for d in secs])
    narrow = np.concatenate([d['narrow'] for d in secs])
    reach = a.half_width + (a.crest - (-8.0)) / a.slope
    # fail closed where the 1:2 side would still stand above the ground beyond the near cut-off (a deeper bed or a
    # target above the crest): the embankment would end in an underwater step there
    far = a.half_width + (float(target.max()) - float(h0.min())) / a.slope
    lo, hi = axis.min(axis=0) - far, axis.max(axis=0) + far
    wide = (x >= lo[0]) & (x <= hi[0]) & (z >= lo[1]) & (z <= hi[1])
    dw, jw = cKDTree(axis).query(np.column_stack([x[wide], z[wide]]), distance_upper_bound=far)
    ok = np.isfinite(dw) & (dw > reach)
    slope_top = target[jw[ok]] - a.slope * (dw[ok] - a.half_width)
    cut = int((editable[wide][ok] & (slope_top > h0[wide][ok] + 1e-6)).sum())
    assert cut == 0, f'{cut} vertices beyond the {reach:.1f} m reach lie under the embankment slope'
    lo, hi = axis.min(axis=0) - reach, axis.max(axis=0) + reach
    box = (x >= lo[0]) & (x <= hi[0]) & (z >= lo[1]) & (z <= hi[1])
    d, j = cKDTree(axis).query(np.column_stack([x[box], z[box]]), distance_upper_bound=reach)
    near = np.zeros((N, N), bool)
    near[box] = np.isfinite(d)
    dist = np.full((N, N), np.inf)
    dist[near] = d[np.isfinite(d)]
    jj = np.zeros((N, N), int)
    jj[near] = j[np.isfinite(d)]
    emb = np.full((N, N), -np.inf)
    emb[near] = target[jj[near]] - a.slope * np.maximum(0.0, dist[near] - a.half_width)
    in_core = near & core[jj]
    in_narrow = near & narrow[jj]

    # smoothed sea bed: sea vertices away from the old strip, filled inwards and blurred over 12 m
    strip = near & (dist <= a.half_width + 8.0)
    seed = sea0 & ~strip
    _, idx = ndimage.distance_transform_edt(~seed, return_indices=True)
    bed = ndimage.gaussian_filter(h0[idx[0], idx[1]], 2.0)
    bed = np.minimum(bed, a.sea - GATES['depth_min_m'])

    rebuild = editable & in_narrow & (h0 < a.crest + 0.5) & (sea0 | t['platform'] | t['reserve'])
    fill = editable & near & ~rebuild
    want = h0.copy()
    want[rebuild] = np.maximum(emb[rebuild], bed[rebuild])
    want[fill] = np.maximum(h0[fill], emb[fill])
    land_side = want >= a.sea
    want = np.where(land_side, np.maximum(want, GATES['beach_floor_m']), np.minimum(want, a.sea - GATES['depth_min_m']))
    dead = (want > a.sea - GATES['depth_min_m']) & (want < GATES['beach_floor_m'])
    want = np.where(dead, np.where(want >= (a.sea - GATES['depth_min_m'] + GATES['beach_floor_m']) / 2,
                                   GATES['beach_floor_m'], a.sea - GATES['depth_min_m']), want)
    h1 = np.where(rebuild | fill, want, h0)

    cls1, level1 = cls0.copy(), level0.copy()
    _, sidx = ndimage.distance_transform_edt(~sea0, return_indices=True)
    near_sea_cls = cls0[sidx[0], sidx[1]]
    to_sea = (rebuild | fill) & land0 & (h1 < a.sea)
    to_land = (rebuild | fill) & sea0 & (h1 >= a.sea)
    cls1[to_sea] = near_sea_cls[to_sea]
    level1[to_sea] = a.sea
    cls1[to_land] = 0
    level1[to_land] = np.nan
    h2, faces = discard_steeper_land_faces(h1, h0, cls1)
    reverted = (h2 != h1.astype('float32').astype(float)) & (h2 == h0.astype('float32').astype(float))
    cls1[reverted], level1[reverted] = cls0[reverted], level0[reverted]
    to_sea, to_land = to_sea & ~reverted, to_land & ~reverted
    h2 = h2.astype('float32').astype(np.float64)
    changed = h2 != h0.astype('float32').astype(np.float64)
    assert not np.any(changed & fixed), 'protected height changed'

    crest_zone = in_core & (dist <= a.half_width) & (cls1 == 0)
    platform1 = (t['platform'] & (cls1 == 0)) | crest_zone
    beach1 = (t['beach'] | ((cls1 == 0) & (h2 < GATES['land_floor_m'] - 1e-6))) & (cls1 == 0) & ~narva_zone
    out = dict(t)
    out['heights'] = h2.astype(t['heights'].dtype)
    out['cls'] = cls1
    out['level'] = level1.astype(t['level'].dtype)
    out['water'] = cls1 > 0
    out['beach'] = beach1
    out['platform'] = platform1
    sea1 = np.isin(cls1, SEA_CLASSES) & (np.hypot(x - NARVA[0], z - NARVA[1]) > 600.0)
    gate_check = {'sea_too_shallow': int((sea1 & (level1 - h2 < GATES['depth_min_m'] - 1e-6)).sum()),
                  'beach_below_floor': int((beach1 & (h2 < GATES['beach_floor_m'] - 1e-6)).sum()),
                  'land_below_floor_outside_beach': int(((cls1 == 0) & ~beach1 & ~narva_zone
                                                         & (h2 < GATES['land_floor_m'] - 1e-6)).sum())}
    zone = near & (dist <= a.half_width + 30.0)
    sections = []
    for s in secs:
        c = s['axis'][s['core']]
        hc = tri_sample(h2, c[:, 0], c[:, 1])
        sections.append(dict(chain=s['chain'], s0=round(s['s0'], 1), s1=round(s['s1'], 1),
                             length_m=round(s['s1'] - s['s0'], 1), ends=[c[0].round(1).tolist(), c[-1].round(1).tolist()],
                             crest_before_p5_p50_p95=[round(float(v), 2) for v in np.percentile(s['profile'][s['core']], [5, 50, 95])],
                             crest_after_p5_p50_p95=[round(float(v), 2) for v in np.percentile(hc, [5, 50, 95])]))
    dh = h2 - h0
    a.out.mkdir(parents=True)
    np.savez_compressed(a.out / 'terrain_causeway.npz', **out)
    np.savez_compressed(a.out / 'masks.npz', rebuild=rebuild, fill=fill, changed=changed, crest=crest_zone)
    rep = {
        'status': 'BUILT_PENDING_GATES_AND_ENGINE_VIEWS',
        'params': {k: v for k, v in vars(a).items() if k not in ('terrain', 'out')},
        'sections': sections,
        'vertices': {'rebuild': int(rebuild.sum()), 'fill': int(fill.sum()), 'changed': int(changed.sum()),
                     'lowered': int((changed & (h2 < h0 - 1e-6)).sum()),
                     'lowered_natural_land': int((changed & land0 & ~t['platform'] & ~t['reserve']
                                                  & (h2 < h0 - 1e-6)).sum()),
                     'to_sea': int(to_sea.sum()), 'to_land': int(to_land.sum()), 'face_recovery': faces,
                     'crest': int(crest_zone.sum())},
        'change_m': {'raise_max': round(float(dh.max()), 3), 'lower_max': round(float(-dh.min()), 3)},
        'waterline_turn_deg_per_12m_near_causeways': {'before': turning(zero_lines(h0 - a.sea, zone)),
                                                      'after': turning(zero_lines(h2 - a.sea, zone))},
        'land_1p40_to_1p60_near_causeways': {'before': int((zone & land0 & (h0 >= 1.40) & (h0 < 1.60)).sum()),
                                             'after': int((zone & (cls1 == 0) & (h2 >= 1.40) & (h2 < 1.60)).sum())},
        'gate_check': gate_check,
        'inputs': {str(p): sha(p) for p in (a.terrain, Path(__file__))},
        'output_sha256': sha(a.out / 'terrain_causeway.npz'), 'seconds': round(time.time() - t0, 1),
        'limits': ['Only road sections with sea on both sides; bridges and river crossings untouched.',
                   'Engine views and the grouped gates decide acceptance.']}
    (a.out / 'report.json').write_text(json.dumps(rep, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in rep.items() if k != 'inputs'}, indent=1))


if __name__ == '__main__':
    main()

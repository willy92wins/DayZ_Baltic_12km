"""Acceptance gate of the shore work: how the VISIBLE waterline follows the design outline, measured outside every
shaping tool.

The visible water is what the engine and build_surface_v30.py draw: terrain on the native triangles below the 6 m cell
plane (v30_common.cell_planes), or below the sea (0.75 m). The shore tools measured themselves against their own outline
and missed the staircase the 6 m lattice forces on the drawn edge (06-10); this tool measures the drawn surface instead.
Along every inland design outline (contour lakes, OSM ponds, river and stream bodies of the design folder), every
--step metres, the tool walks the outline normal from --search inside to --search outside in --ds steps and takes the
visible water edge nearest to the outline. Per class of the nearest design body:
- offset: |distance| from the design outline to the visible edge (p50, p90);
- zigzag: RMS of the offset minus its --smooth-m Gaussian along the outline, the 6-12 m wobble of a staircase;
- turning of the visible waterline (design point moved along its normal to the visible edge) and of the design outline
  itself, on --chord-steps * --step metre chords: share of points turning more than 30 and 45 degrees;
- missing: share of points with no visible edge within --search m.
Points within --border-m of the map border, --narva-m of the Narva bridge or --exclude-m of a navigable reach or the
delta are left out.

Usage: python tools/water/audit_waterline_v30.py --design DESIGN_DIR [--contour PATH] --terrain LABEL=terrain.npz
[--terrain LABEL2=terrain2.npz ...] [--json OUT] [--selftest]
"""
import argparse
import json
import os
import sys
import tempfile

import numpy as np
import shapely
from scipy.ndimage import gaussian_filter1d
from shapely.geometry import shape

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, 'terrain'))
from v30_common import N, R, cell_planes, grid_xz, tri_sample  # noqa: E402

NARVA = (2417.1428225906, 6889.8850822322)
Z0 = (N - 1) * 6.0                                  # 12282 m: z of vertex row 0, the map extent
STEP, SEARCH, DS = 2.0, 8.0, 0.25
BORDER_M, NARVA_M, EXCLUDE_M, SMOOTH_M, CHORD_STEPS = 66.0, 620.0, 30.0, 12.0, 3


def design_outline(design, contour_path, exclude_m=EXCLUDE_M, border_m=BORDER_M, narva_m=NARVA_M, step=STEP):
    feats = json.load(open(design + '/water_v3.geojson', encoding='utf-8'))['features']
    streams = [f for f in json.load(open(design + '/streams_candidates.geojson', encoding='utf-8'))['features']
               if f['properties']['tier_m'] >= 2500]
    contour = [f for f in json.load(open(contour_path, encoding='utf-8'))['features']
               if f['properties']['body'].startswith('lake')]
    bodies = ([(shape(f['geometry']), f['properties']['class']) for f in feats if f['properties']['class'] in ('river', 'pond')]
              + [(shape(f['geometry']), 'stream') for f in streams] + [(shape(f['geometry']), 'lake') for f in contour])
    excl = shapely.union_all([shape(f['geometry']).buffer(exclude_m) for f in feats
                              if f['properties']['class'] == 'navigable' or f['properties']['class'].startswith('delta')])
    union = shapely.union_all([g for g, _ in bodies])
    tree = shapely.STRtree([g for g, _ in bodies])
    kinds = np.array([k for _, k in bodies])
    pts, nrm, kind, ring_id = [], [], [], []
    rid = 0
    for poly in getattr(union, 'geoms', [union]):
        for ring in [poly.exterior] + list(poly.interiors):
            n = int(ring.length // step)
            if n < 4:
                continue
            d = np.arange(n) * step
            p = np.array([ring.interpolate(v).coords[0] for v in d])
            t = np.roll(p, -1, axis=0) - np.roll(p, 1, axis=0)
            t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
            nr = np.column_stack([t[:, 1], -t[:, 0]])
            # orient the normal outwards: a step outside must leave the water polygon
            probe = shapely.points(p + nr * 1.0)
            inside = shapely.contains(poly, probe)
            nr[inside] *= -1
            pts.append(p)
            nrm.append(nr)
            ring_id.append(np.full(n, rid))
            rid += 1
    P, Nn, RID = np.vstack(pts), np.vstack(nrm), np.concatenate(ring_id)
    near = tree.query_nearest(shapely.points(P), all_matches=False)
    K = kinds[near[1]] if near.ndim == 2 else kinds[near]
    keep = ((P[:, 0] > border_m) & (P[:, 0] < Z0 - border_m) & (P[:, 1] > border_m) & (P[:, 1] < Z0 - border_m)
            & (np.hypot(P[:, 0] - NARVA[0], P[:, 1] - NARVA[1]) > narva_m)
            & ~shapely.contains(excl, shapely.points(P)))
    return P, Nn, K, RID, keep


def measure(terrain, P, Nn, K, RID, keep, step=STEP, search=SEARCH, ds=DS, smooth_m=SMOOTH_M, chord_steps=CHORD_STEPS):
    t = np.load(terrain)
    h, cls, lev = t['heights'].astype(np.float64), t['cls'], t['level'].astype(np.float64)
    plane = cell_planes(cls, lev)
    steps = np.arange(-search, search + 1e-9, ds)
    off = np.full(len(P), np.nan)
    for i0 in range(0, len(P), 40000):
        sl = slice(i0, i0 + 40000)
        X = P[sl, 0, None] + Nn[sl, 0, None] * steps[None]
        Z = P[sl, 1, None] + Nn[sl, 1, None] * steps[None]
        Xc, Zc = np.clip(X, 0, Z0 - 0.1), np.clip(Z, 0, Z0 - 0.1)
        hh = tri_sample(h, Xc, Zc)
        pl = plane[np.clip(np.floor((Z0 - Zc) / 6).astype(int), 0, N - 2), np.clip(np.floor(Xc / 6).astype(int), 0, N - 2)]
        W = (np.isfinite(pl) & (hh < np.nan_to_num(pl, nan=-1e9))) | (hh < 0.75)
        ch = W[:, :-1] != W[:, 1:]                       # an edge between two steps
        pos = (steps[:-1] + steps[1:]) / 2
        dist = np.where(ch, np.abs(pos)[None], np.inf)
        j = np.argmin(dist, axis=1)
        ok = np.isfinite(dist[np.arange(len(j)), j])
        o = np.where(ok, pos[j], np.nan)
        off[sl] = o
    res = {}
    for k in ('lake', 'pond', 'river', 'stream', 'all'):
        sel = keep & ((K == k) if k != 'all' else True)
        o = off[sel]
        good = np.isfinite(o)
        # zigzag: offset minus its own Gaussian, ring by ring (only finite runs)
        zz = []
        for r in np.unique(RID[sel]):
            m = sel & (RID == r)
            v = off[m]
            if np.isfinite(v).sum() < 8:
                continue
            v = np.where(np.isfinite(v), v, np.nanmedian(v))
            zz.append(v - gaussian_filter1d(v, smooth_m / step, mode='wrap'))
        zz = np.concatenate(zz) if zz else np.array([np.nan])
        # turning of the visible waterline (design point moved along its normal to the visible edge) and of the
        # design outline itself, on chord_steps * step metre chords: share of points turning more than 30 and 45 degrees
        tv, td = [], []
        for r in np.unique(RID[sel]):
            m = sel & (RID == r)
            if m.sum() < 8:
                continue
            v = off[m]
            if not np.isfinite(v).all():
                v = np.where(np.isfinite(v), v, np.nanmedian(v) if np.isfinite(v).any() else 0.0)
            for pts_, out_ in ((P[m] + Nn[m] * v[:, None], tv), (P[m], td)):
                a = pts_ - np.roll(pts_, chord_steps, axis=0)
                b = np.roll(pts_, -chord_steps, axis=0) - pts_
                cosang = (a * b).sum(1) / np.maximum(np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1), 1e-9)
                out_.append(np.degrees(np.arccos(np.clip(cosang, -1, 1))))
        tv = np.concatenate(tv) if tv else np.array([np.nan])
        td = np.concatenate(td) if td else np.array([np.nan])
        res[k] = {'points': int(sel.sum()), 'missing_share': round(float(1 - good.mean()), 3) if sel.any() else None,
                  'offset_p50': round(float(np.nanpercentile(np.abs(o), 50)), 2) if good.any() else None,
                  'offset_p90': round(float(np.nanpercentile(np.abs(o), 90)), 2) if good.any() else None,
                  'zigzag_rms': round(float(np.sqrt(np.nanmean(zz ** 2))), 2),
                  'zigzag_abs_p50_p90': [round(float(np.nanpercentile(np.abs(zz), q)), 2) for q in (50, 90)],
                  'visible_turn_gt30_share': round(float(np.nanmean(tv > 30)), 3),
                  'visible_turn_gt45_share': round(float(np.nanmean(tv > 45)), 3),
                  'design_turn_gt30_share': round(float(np.nanmean(td > 30)), 3),
                  'design_turn_gt45_share': round(float(np.nanmean(td > 45)), 3)}
    return res, off


def _synthetic_terrain(path, staircase):
    """Full grid: a pond (class 7, level 3.0) inside the circle r = 60 m at (6000, 6000), land beyond."""
    xs, zs = grid_xz()
    d = np.hypot(xs - 6000.0, zs - 6000.0) - 60.0    # distance to the circle, negative inside
    wet = d < 0
    heights = np.full((N, N), 5.0, dtype=np.float32)
    cls = np.zeros((N, N), dtype=np.uint8)
    level = np.zeros((N, N), dtype=np.float32)
    cls[wet] = 7
    level[wet] = 3.0
    if staircase:
        heights[wet] = 2.5
        heights[~wet & (d <= 30)] = 3.5
    else:
        heights[wet] = 3.0 - 0.15 * -d[wet]
        heights[~wet & (d <= 30)] = 3.0 + 0.15 * d[~wet & (d <= 30)]
    np.savez_compressed(path, heights=heights, cls=cls, level=level)


def _selftest(args):
    """Synthetic circle: a smooth beach must hug the outline, a staircase must not."""
    with tempfile.TemporaryDirectory() as tmp:
        design = os.path.join(tmp, 'design')
        os.makedirs(design)
        circle = shapely.buffer(shapely.points(6000.0, 6000.0), 60.0)
        with open(os.path.join(design, 'water_v3.geojson'), 'w', encoding='utf-8') as f:
            json.dump({'type': 'FeatureCollection',
                       'features': [{'properties': {'class': 'pond'}, 'geometry': shapely.geometry.mapping(circle)}]}, f)
        with open(os.path.join(design, 'streams_candidates.geojson'), 'w', encoding='utf-8') as f:
            json.dump({'type': 'FeatureCollection', 'features': []}, f)
        contour = os.path.join(tmp, 'contour.geojson')
        with open(contour, 'w', encoding='utf-8') as f:
            json.dump({'type': 'FeatureCollection', 'features': []}, f)  # no lakes
        terrains = {}
        for label, staircase in (('SMOOTH', False), ('STAIRCASE', True)):
            path = os.path.join(tmp, label.lower() + '.npz')
            _synthetic_terrain(path, staircase)
            terrains[label] = path
        P, Nn, K, RID, keep = design_outline(design, contour, args.exclude_m, args.border_m, args.narva_m, args.step)
        res = {}
        for label, path in terrains.items():
            res[label], _ = measure(path, P, Nn, K, RID, keep,
                                    args.step, args.search, args.ds, args.smooth_m, args.chord_steps)
            print(label)
            for k, v in res[label].items():
                print(f'   {k:7}', v)
        a, b = res['SMOOTH']['pond'], res['STAIRCASE']['pond']
        assert a['missing_share'] == 0 and b['missing_share'] == 0, 'the circle outline must find a visible edge'
        assert a['offset_p90'] < 0.5, f'smooth beach should hug the circle, offset_p90 = {a["offset_p90"]}'
        assert a['visible_turn_gt45_share'] < 0.05, 'smooth beach should not turn sharply'
        assert b['offset_p90'] > a['offset_p90'], 'staircase must sit further from the circle'
        assert b['visible_turn_gt30_share'] > a['visible_turn_gt30_share'], 'staircase must turn more sharply'
        print('SELFTEST PASS')


def main():
    ap = argparse.ArgumentParser(description='Audit the VISIBLE waterline against the design outline '
                                             '(the module docstring has the details).')
    ap.add_argument('--design', help='design folder with water_v3.geojson and streams_candidates.geojson')
    ap.add_argument('--contour', default=os.path.join(R, 'evidence', 'regional-foundation-v1',
                                                      'water-surfaces-contour-v2.geojson'))
    ap.add_argument('--terrain', action='append', metavar='LABEL=PATH',
                    help='labelled terrain npz to audit, repeatable, at least one')
    ap.add_argument('--json', dest='out_json', help='write the per-label results as JSON')
    ap.add_argument('--step', type=float, default=STEP, help='sampling step along the outline, metres')
    ap.add_argument('--search', type=float, default=SEARCH, help='normal walk half-range, metres')
    ap.add_argument('--ds', type=float, default=DS, help='normal walk step, metres')
    ap.add_argument('--border-m', type=float, default=BORDER_M, dest='border_m', help='map border exclusion, metres')
    ap.add_argument('--narva-m', type=float, default=NARVA_M, dest='narva_m', help='Narva bridge exclusion, metres')
    ap.add_argument('--exclude-m', type=float, default=EXCLUDE_M, dest='exclude_m',
                    help='exclusion around navigable and delta bodies, metres')
    ap.add_argument('--smooth-m', type=float, default=SMOOTH_M, dest='smooth_m',
                    help='Gaussian width of the zigzag term, metres')
    ap.add_argument('--chord-steps', type=int, default=CHORD_STEPS, dest='chord_steps',
                    help='turning chord length in outline steps')
    ap.add_argument('--selftest', action='store_true', help='run the synthetic smooth/staircase check and exit')
    args = ap.parse_args()
    if args.selftest:
        _selftest(args)
        return
    if not args.design or not args.terrain:
        ap.error('--design and at least one --terrain are required')
    P, Nn, K, RID, keep = design_outline(args.design, args.contour,
                                         args.exclude_m, args.border_m, args.narva_m, args.step)
    allres = {}
    for spec in args.terrain:
        label, path = spec.split('=', 1)
        res, _ = measure(path, P, Nn, K, RID, keep,
                         args.step, args.search, args.ds, args.smooth_m, args.chord_steps)
        allres[label] = res
        print(label)
        for k, v in res.items():
            print(f'   {k:7}', v)
    if args.out_json:
        json.dump(allres, open(args.out_json, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


if __name__ == '__main__':
    main()

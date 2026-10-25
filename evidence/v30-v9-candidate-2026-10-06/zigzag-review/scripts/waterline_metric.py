"""How closely the VISIBLE waterline follows the design outline, measured outside every shaping tool.

The visible water is what the engine and build_surface_v30.py draw: terrain on the native triangles below the 6 m cell
plane (v30_common.cell_planes), or below the sea (0.75 m). Along every inland design outline (contour lakes, OSM ponds,
river and stream bodies of the design folder), every 2 m, the tool walks the outline normal from 8 m inside to 8 m
outside in 0.25 m steps and takes the visible water edge nearest to the outline. Per class of the nearest design body:
- offset: |distance| from the design outline to the visible edge (p50, p90);
- zigzag: RMS of the offset minus its 12 m Gaussian along the outline, the 6-12 m wobble of a staircase;
- missing: share of points with no visible edge within 8 m.
Points within 66 m of the map border, 620 m of the Narva bridge or 30 m of a navigable reach or the delta are left out.
Usage: waterline_metric.py DESIGN_DIR [--contour PATH] label=terrain.npz ... [--json OUT]"""
import json
import sys

import numpy as np
import shapely
from scipy.ndimage import gaussian_filter1d
from shapely.geometry import shape

sys.path.insert(0, r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees'
                   r'\codex-handoff-review-74f290\tools\terrain')
from v30_common import cell_planes, tri_sample  # noqa: E402

R = 'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/'
NARVA = (2417.1428225906, 6889.8850822322)
STEP, SEARCH, DS = 2.0, 8.0, 0.25


def design_outline(design, contour_path):
    feats = json.load(open(design + '/water_v3.geojson', encoding='utf-8'))['features']
    streams = [f for f in json.load(open(design + '/streams_candidates.geojson', encoding='utf-8'))['features']
               if f['properties']['tier_m'] >= 2500]
    contour = [f for f in json.load(open(contour_path, encoding='utf-8'))['features']
               if f['properties']['body'].startswith('lake')]
    bodies = ([(shape(f['geometry']), f['properties']['class']) for f in feats if f['properties']['class'] in ('river', 'pond')]
              + [(shape(f['geometry']), 'stream') for f in streams] + [(shape(f['geometry']), 'lake') for f in contour])
    excl = shapely.union_all([shape(f['geometry']).buffer(30) for f in feats
                              if f['properties']['class'] == 'navigable' or f['properties']['class'].startswith('delta')])
    union = shapely.union_all([g for g, _ in bodies])
    tree = shapely.STRtree([g for g, _ in bodies])
    kinds = np.array([k for _, k in bodies])
    pts, nrm, kind, ring_id = [], [], [], []
    rid = 0
    for poly in getattr(union, 'geoms', [union]):
        for ring in [poly.exterior] + list(poly.interiors):
            n = int(ring.length // STEP)
            if n < 4:
                continue
            d = np.arange(n) * STEP
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
    keep = ((P[:, 0] > 66) & (P[:, 0] < 12282 - 66) & (P[:, 1] > 66) & (P[:, 1] < 12282 - 66)
            & (np.hypot(P[:, 0] - NARVA[0], P[:, 1] - NARVA[1]) > 620)
            & ~shapely.contains(excl, shapely.points(P)))
    return P, Nn, K, RID, keep


def measure(terrain, P, Nn, K, RID, keep):
    t = np.load(terrain)
    h, cls, lev = t['heights'].astype(np.float64), t['cls'], t['level'].astype(np.float64)
    plane = cell_planes(cls, lev)
    steps = np.arange(-SEARCH, SEARCH + 1e-9, DS)
    off = np.full(len(P), np.nan)
    for i0 in range(0, len(P), 40000):
        sl = slice(i0, i0 + 40000)
        X = P[sl, 0, None] + Nn[sl, 0, None] * steps[None]
        Z = P[sl, 1, None] + Nn[sl, 1, None] * steps[None]
        Xc, Zc = np.clip(X, 0, 12281.9), np.clip(Z, 0, 12281.9)
        hh = tri_sample(h, Xc, Zc)
        pl = plane[np.clip(np.floor((12282 - Zc) / 6).astype(int), 0, 2046), np.clip(np.floor(Xc / 6).astype(int), 0, 2046)]
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
        # zigzag: offset minus its own 12 m Gaussian, ring by ring (only finite runs)
        zz = []
        for r in np.unique(RID[sel]):
            m = sel & (RID == r)
            v = off[m]
            if np.isfinite(v).sum() < 8:
                continue
            v = np.where(np.isfinite(v), v, np.nanmedian(v))
            zz.append(v - gaussian_filter1d(v, 12.0 / STEP, mode='wrap'))
        zz = np.concatenate(zz) if zz else np.array([np.nan])
        # turning of the visible waterline (design point moved along its normal to the visible edge) and of the
        # design outline itself, on 6 m chords: share of points turning more than 30 and 45 degrees
        tv, td = [], []
        for r in np.unique(RID[sel]):
            m = sel & (RID == r)
            if m.sum() < 8:
                continue
            v = off[m]
            if not np.isfinite(v).all():
                v = np.where(np.isfinite(v), v, np.nanmedian(v) if np.isfinite(v).any() else 0.0)
            for pts_, out_ in ((P[m] + Nn[m] * v[:, None], tv), (P[m], td)):
                a = pts_ - np.roll(pts_, 3, axis=0)
                b = np.roll(pts_, -3, axis=0) - pts_
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


def main():
    args = sys.argv[1:]
    out_json = None
    if '--json' in args:
        out_json = args[args.index('--json') + 1]
        del args[args.index('--json'):args.index('--json') + 2]
    contour = R + 'evidence/regional-foundation-v1/water-surfaces-contour-v2.geojson'
    if '--contour' in args:
        contour = args[args.index('--contour') + 1]
        del args[args.index('--contour'):args.index('--contour') + 2]
    design = args[0]
    P, Nn, K, RID, keep = design_outline(design, contour)
    allres = {}
    for a in args[1:]:
        label, path = a.split('=', 1)
        res, _ = measure(path, P, Nn, K, RID, keep)
        allres[label] = res
        print(label)
        for k, v in res.items():
            print(f'   {k:7}', v)
    if out_json:
        json.dump(allres, open(out_json, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


if __name__ == '__main__':
    main()

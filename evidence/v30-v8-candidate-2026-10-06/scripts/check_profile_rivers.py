"""Receiver check of a profile_rivers_v30 output against its input, independent of the tool's own code and report.

Usage: check_profile_rivers.py IN.npz OUT.npz --channels FITDIR [--bed-floor 1.0 --bed-min-depth 0.30] [--json OUT]
Checks (counts; 0 is the pass value unless stated):
- identity: class and level changes (none allowed), keys and dtypes;
- protected: changed vertices on platform, reserve, the Narva zone (620 m), the map border, the exact 24 m corridors,
  the vanilla channel reaches and 22 m around them, sea/delta/lake/pond vertices, changed vertices farther than 22 m
  from flowing water, and changed vertices within 22 m of sea, standing water or flowing water at or below 0.80 m other
  than river/stream bed raises; corridor-margin changes are reported, not gated (the channel edges are free);
- gates as verify_terrain_v30.py computes them (water depth, banks, land floor, pieces with sea cut 0.51, land slopes),
  before and after;
- bed floor (with --bed-floor): river and stream water above 0.80 m outside the corridors, the Narva zone, the border
  and the reaches, below min(floor, level - min_depth); beds under 0.85 m by class, before and after;
- shape: crossing offset of every flowing shore edge against a smoothed outline of its component (sigma 12 m, shift
  4 m), computed here, by class, before and after.
"""
import json
import sys
from pathlib import Path

import numpy as np
import shapely
from scipy import ndimage

W = Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290')
sys.path.insert(0, str(W / 'tools' / 'terrain'))
from finish_shores_v30 import protect_corridors  # noqa: E402
from profile_coast_v30 import EDGES, NARVA  # noqa: E402
from v30_common import N, cell_planes, grid_xz  # noqa: E402

import contourpy  # noqa: E402

FLOW = (3, 5, 6)


def arg(name, default=None, cast=str):
    return cast(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def gates(h, cls, level, beach, zone):
    water = cls > 0
    out = {'water_depth': int((water & ~zone & (level - h < 0.10)).sum())}
    dist, idx = ndimage.distance_transform_edt(~water, sampling=6.0, return_indices=True)
    near_lv = level[idx[0], idx[1]]
    b = ~water & (dist <= 8.5) & ~zone
    out['banks'] = int((b & (h - near_lv < 0.05)).sum())
    inland = ~water & ~zone & ~beach
    out['land_floor'] = int((inland & (h < 1.40 - 1e-6)).sum())
    out['beach_floor'] = int((beach & (h < 0.80 - 1e-6)).sum())
    plane = cell_planes(cls, level, sea_cut=0.51)
    czone = zone[:-1, :-1] | zone[:-1, 1:] | zone[1:, :-1] | zone[1:, 1:]
    pw = pl = 0
    for dr in (0, 1):
        for dc in (0, 1):
            hc, wc = h[dr:dr + N - 1, dc:dc + N - 1], water[dr:dr + N - 1, dc:dc + N - 1]
            ok = np.isfinite(plane) & ~czone
            with np.errstate(invalid='ignore'):
                pw += int((ok & wc & (hc > plane - 0.02)).sum())
                pl += int((ok & ~wc & (hc < plane)).sum())
    out['pieces_water'], out['pieces_land'] = pw, pl
    land = ~water
    nw, ne, sw, se = h[:-1, :-1], h[:-1, 1:], h[1:, :-1], h[1:, 1:]
    au = np.degrees(np.arctan(np.hypot((ne - nw) / 6, (se - ne) / 6)))
    al = np.degrees(np.arctan(np.hypot((sw - nw) / 6, (se - sw) / 6)))
    lnw, lne, lsw, lse = land[:-1, :-1], land[:-1, 1:], land[1:, :-1], land[1:, 1:]
    out['land_slopes_over_35p01'] = int(((lnw & lne & lse) & (au > 35.01)).sum() + ((lnw & lsw & lse) & (al > 35.01)).sum())
    return out


def window_lines(field, mask, r0, c0):
    nr, nc = field.shape
    z = np.ma.masked_invalid(np.where(mask, field, np.nan))
    gen = contourpy.contour_generator(x=(c0 + np.arange(nc)) * 6.0, y=12282.0 - (r0 + np.arange(nr)) * 6.0, z=z,
                                      line_type=contourpy.LineType.Separate)
    return [ln for ln in gen.lines(0.0) if len(ln) >= 2]


def offsets_by_class(hs, cls, level, flow):
    """Crossing offsets (m) of flowing shore edges against a smoothed outline, for each height array in hs."""
    x, z = grid_xz()
    land = cls == 0
    lab, n = ndimage.label(flow, structure=np.ones((3, 3), int))
    sizes = np.bincount(lab.ravel())
    res = [{k: [] for k in FLOW} for _ in hs]
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        if sl is None or sizes[i] < 4:
            continue
        r0, r1 = max(sl[0].start - 12, 0), min(sl[0].stop + 12, N)
        c0, c1 = max(sl[1].start - 12, 0), min(sl[1].stop + 12, N)
        Wn = (slice(r0, r1), slice(c0, c1))
        B = lab[Wn] == i
        base = np.where(B, -ndimage.distance_transform_edt(B), ndimage.distance_transform_edt(~B)) * 6.0
        smooth = np.clip(ndimage.gaussian_filter(base, 2.0), base - 4.0, base + 4.0)
        near = np.abs(base) <= 25.0
        lines = window_lines(smooth, near, r0, c0)
        if not lines:
            continue
        segs = np.concatenate([np.stack([ln[:-1], ln[1:]], axis=1) for ln in lines])
        tree = shapely.STRtree(shapely.linestrings(segs))
        _, dist = tree.query_nearest(shapely.points(x[Wn][near], z[Wn][near]), return_distance=True, all_matches=False)
        sd = np.full(B.shape, np.nan)
        sd[near] = np.where(smooth[near] < 0, -dist, dist)
        ll, cc, lnd = level[Wn], cls[Wn], land[Wn]
        nr, nc = B.shape
        for dr, dc in EDGES:
            for flip in (False, True):
                A, Bs = (slice(0, nr - dr), slice(0, nc - dc)), (slice(dr, nr), slice(dc, nc))
                wa, wb = (Bs, A) if flip else (A, Bs)
                e = B[wa] & lnd[wb]
                sa, sb = sd[wa][e], sd[wb][e]
                ok = np.isfinite(sa) & np.isfinite(sb) & (sa * sb < 0)
                tstar = np.abs(sa[ok]) / (np.abs(sa[ok]) + np.abs(sb[ok]))
                lw = ll[wa][e][ok]
                kk = cc[wa][e][ok]
                ln = 6.0 * (2 ** 0.5 if dr and dc else 1.0)
                for j, h in enumerate(hs):
                    hh = h[Wn]
                    ha, hb = hh[wa][e][ok] - lw, hh[wb][e][ok] - lw
                    with np.errstate(divide='ignore', invalid='ignore'):
                        tt = np.where(ha * hb < 0, ha / (ha - hb), np.nan)
                    for k in FLOW:
                        res[j][k].append((np.abs(tt - tstar) * ln)[kk == k])
    out = []
    for r in res:
        d = {}
        for k in FLOW:
            v = np.concatenate(r[k]) if r[k] else np.zeros(0)
            nan = int(np.isnan(v).sum())
            v = v[np.isfinite(v)]
            d[f'class_{k}'] = {'edges': int(v.size + nan), 'no_crossing': nan,
                               **({f'p{q}': round(float(np.percentile(v, q)), 2) for q in (50, 90, 99)} if v.size else {})}
        out.append(d)
    return out


def main():
    a, b = sys.argv[1], sys.argv[2]
    fit = Path(arg('--channels'))
    floor = arg('--bed-floor', None, float)
    mind = arg('--bed-min-depth', 0.30, float)
    t0, t1 = np.load(a), np.load(b)
    assert sorted(t0.files) == sorted(t1.files), (t0.files, t1.files)
    h0, h1 = t0['heights'].astype(float), t1['heights'].astype(float)
    c0, c1 = t0['cls'], t1['cls']
    l0, l1 = t0['level'].astype(float), t1['level'].astype(float)
    x, z = grid_xz()
    changed = h1 != h0
    narva = np.hypot(x - NARVA[0], z - NARVA[1]) <= 620.0
    zone = np.hypot(x - NARVA[0], z - NARVA[1]) <= 600.0
    border = (x < 12) | (z < 12) | (x > 12270) | (z > 12270)
    exact, margin, _, _ = protect_corridors(cell_planes(c0, l0))
    reach = np.zeros((N, N), bool)
    for r in json.loads((fit / 'axes.json').read_text(encoding='utf-8')).values():
        for rr, cc in r['removed_cells']:
            reach[rr:rr + 2, cc:cc + 2] = True
    flow = np.isin(c0, FLOW)
    low = flow & (l0 <= 0.80)
    other = np.isin(c0, (1, 2, 4, 7)) | low
    near_flow = ndimage.distance_transform_edt(~(flow & ~low)) * 6.0 <= 22.0
    near_other = ndimage.distance_transform_edt(~other) * 6.0 <= 22.0
    near_reach = ndimage.distance_transform_edt(~reach) * 6.0 <= 22.0
    bedlike = np.isin(c0, (5, 6)) & (h1 > h0)
    out = {'changed': int(changed.sum()),
           'identity': {'class_changed': int((c1 != c0).sum()),
                        'level_changed': int((~((l1 == l0) | (np.isnan(l1) & np.isnan(l0)))).sum()),
                        'dtype_changes': [k for k in t0.files if t0[k].dtype != t1[k].dtype]},
           'protected': {'platform': int((changed & t0['platform']).sum()), 'reserve': int((changed & t0['reserve']).sum()),
                         'narva_620': int((changed & narva).sum()), 'border': int((changed & border).sum()),
                         'corridor_exact': int((changed & exact).sum()),
                         'reach_and_22m': int((changed & near_reach).sum()),
                         'sea_delta_lake_pond_vertices': int((changed & np.isin(c0, (1, 2, 4, 7))).sum()),
                         'far_from_flowing_22m': int((changed & ~near_flow).sum()),
                         'near_other_water_22m_not_bed_raise': int((changed & near_other & ~bedlike).sum())},
           'reported': {'corridor_margin_changed': int((changed & margin & ~exact).sum()),
                        'changed_by_class': {str(k): int((changed & (c0 == k)).sum()) for k in (0, 3, 5, 6)},
                        'raise_max_m': round(float((h1 - h0).max()), 3), 'lower_max_m': round(float((h0 - h1).max()), 3)}}
    out['gates'] = {'before': gates(h0, c0, l0, t0['beach'], zone), 'after': gates(h1, c1, l1, t1['beach'], zone)}
    out['bed_below_0p85'] = {str(k): {'before': int(((c0 == k) & (l0 > 0.80) & (h0 < 0.85)).sum()),
                                      'after': int(((c1 == k) & (l1 > 0.80) & (h1 < 0.85)).sum())} for k in FLOW}
    if floor is not None:
        need = np.minimum(floor, l0 - mind)
        m = np.isin(c0, (5, 6)) & (l0 > 0.80) & ~exact & ~narva & ~border & ~reach
        out['bed_floor'] = {'river_stream_vertices': int(m.sum()), 'below_need_after': int((m & (h1 < need - 1e-4)).sum()),
                            'below_need_before': int((m & (h0 < need - 1e-4)).sum())}
    before, after = offsets_by_class([h0, h1], c0, l0, flow & ~low)
    out['crossing_offset_m_vs_smoothed_outline'] = {'before': before, 'after': after}
    print(json.dumps(out, indent=1))
    if '--json' in sys.argv:
        Path(arg('--json')).write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()

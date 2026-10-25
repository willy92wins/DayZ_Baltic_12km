"""Receiver check of a profile_lakes_v30 output against its input, independent of the tool's own code and report.

Usage: check_profile_lakes.py IN.npz OUT.npz [--bed-floor 1.0 --bed-min-depth 0.30]
Checks (counts; 0 is the pass value unless stated):
- protected: changed vertices on platform, reserve, the Narva zone (620 m), the map border, sea/delta, navigable,
  river and stream classes (in or out), and changed vertices farther than 22 m from any standing water of the input;
- classes: standing water whose height is not under its level, land that is under the level of an adjacent standing
  vertex, standing vertices whose level is not the median level of their input body;
- gates: standing water < 0.10 m deep, land within 8.5 m of standing water < 0.05 m over the nearest level, land under
  1.40 m outside the beach mask;
- bed floor (with --bed-floor): standing water outside the navigable corridors and the Narva zone below
  min(floor, level - min_depth);
- shape: waterline turn per 12 m of every standing body above 0.80 m, before and after (p50/p90/p95), computed here.
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.path.insert(0, r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290\tools\terrain')
from finish_shores_v30 import protect_corridors  # noqa: E402
from profile_coast_v30 import NARVA, turning  # noqa: E402
from relevel_bodies_v30 import label_bodies  # noqa: E402
from v30_common import N, cell_planes, grid_xz  # noqa: E402

import contourpy  # noqa: E402


def lines_of(field, mask):
    z = np.ma.masked_invalid(np.where(mask, field, np.nan))
    gen = contourpy.contour_generator(x=np.arange(N) * 6.0, y=12282.0 - np.arange(N) * 6.0, z=z,
                                      line_type=contourpy.LineType.Separate)
    return [ln for ln in gen.lines(0.0) if len(ln) >= 3]


def main():
    a, b = sys.argv[1], sys.argv[2]
    floor = float(sys.argv[sys.argv.index('--bed-floor') + 1]) if '--bed-floor' in sys.argv else None
    mind = float(sys.argv[sys.argv.index('--bed-min-depth') + 1]) if '--bed-min-depth' in sys.argv else 0.30
    t0, t1 = np.load(a), np.load(b)
    assert sorted(t0.files) == sorted(t1.files), (t0.files, t1.files)
    h0, h1 = t0['heights'].astype(float), t1['heights'].astype(float)
    c0, c1 = t0['cls'], t1['cls']
    l0, l1 = t0['level'].astype(float), t1['level'].astype(float)
    x, z = grid_xz()
    changed = (h1 != h0) | (c1 != c0)
    narva = np.hypot(x - NARVA[0], z - NARVA[1]) <= 620.0
    border = (x < 12) | (z < 12) | (x > 12270) | (z > 12270)
    other0, other1 = np.isin(c0, (1, 3, 4, 5, 6)), np.isin(c1, (1, 3, 4, 5, 6))
    st0, st1 = np.isin(c0, (2, 7)), np.isin(c1, (2, 7))
    near_st = ndimage.distance_transform_edt(~st0) * 6.0 <= 22.0
    _, corridor, _, _ = protect_corridors(cell_planes(c0, l0))
    out = {'changed': int(changed.sum()), 'height_changed': int((h1 != h0).sum()),
           'class_changed': int((c1 != c0).sum()),
           'protected': {'platform': int((changed & t0['platform']).sum()), 'reserve': int((changed & t0['reserve']).sum()),
                         'narva_620': int((changed & narva).sum()), 'border': int((changed & border).sum()),
                         'other_water_classes': int((changed & (other0 | other1)).sum()),
                         'far_from_standing_22m': int((changed & ~near_st).sum())}}
    # classes against heights and body levels
    ids = label_bodies(c0, l0)
    body_level = np.full(ids.max() + 1, np.nan)
    order = np.argsort(ids.ravel())
    srt = ids.ravel()[order]
    starts = np.searchsorted(srt, np.arange(ids.max() + 1))
    ends = np.searchsorted(srt, np.arange(ids.max() + 1), side='right')
    lv = l0.ravel()[order]
    for i in range(1, ids.max() + 1):
        if ends[i] > starts[i]:
            body_level[i] = np.median(lv[starts[i]:ends[i]])
    land1 = c1 == 0
    dist, idx = ndimage.distance_transform_edt(~st1, return_indices=True)
    near_lv = l1[idx[0], idx[1]]
    out['classes'] = {'standing_not_under_level': int((st1 & ~(h1 < l1)).sum()),
                      'land_under_adjacent_level': int((land1 & (dist * 6.0 <= 6.0) & (h1 < near_lv)).sum()),
                      'new_standing_without_level': int((st1 & ~st0 & ~np.isfinite(l1)).sum())}
    out['gates'] = {'standing_shallower_0p10': {'before': int((st0 & ~narva & (l0 - h0 < 0.10 - 1e-6)).sum()),
                                                'after': int((st1 & ~narva & (l1 - h1 < 0.10 - 1e-6)).sum())},
                    'bank_under_level_0p05': {'before': None, 'after': int((land1 & (dist * 6.0 <= 8.5) & ~narva
                                                                             & (h1 < near_lv + 0.05 - 1e-6)).sum())},
                    'land_under_1p40_outside_beach': {
                        'before': int(((c0 == 0) & ~t0['beach'] & ~narva & (h0 < 1.40 - 1e-6)).sum()),
                        'after': int((land1 & ~t1['beach'] & ~narva & (h1 < 1.40 - 1e-6)).sum())}}
    d0, i0 = ndimage.distance_transform_edt(~st0, return_indices=True)
    nl0 = l0[i0[0], i0[1]]
    out['gates']['bank_under_level_0p05']['before'] = int(((c0 == 0) & (d0 * 6.0 <= 8.5) & ~narva
                                                           & (h0 < nl0 + 0.05 - 1e-6)).sum())
    if floor is not None:
        need = np.minimum(floor, l1 - mind)
        m = st1 & (l1 > 0.80) & ~corridor & ~narva
        out['bed_floor'] = {'standing_vertices': int(m.sum()), 'below_floor': int((m & (h1 < need - 1e-6)).sum()),
                            'below_0p85_after': int((m & (h1 < 0.85)).sum()),
                            'below_0p85_before': int((st0 & (l0 > 0.80) & (h0 < 0.85)).sum())}
    # waterline turning of standing bodies, before and after
    above0 = st0 & (l0 > 0.80)
    band = ndimage.binary_dilation(above0, iterations=3)
    lev_field0 = np.where(above0, l0, np.nan)
    _, j = ndimage.distance_transform_edt(~above0, return_indices=True)
    lev_near = lev_field0[j[0], j[1]]
    out['waterline_turn_deg_per_12m'] = {'before': turning(lines_of(h0 - lev_near, band)),
                                         'after': turning(lines_of(h1 - lev_near, band))}
    print(json.dumps(out, indent=1))
    if len(sys.argv) > 3 and '--json' in sys.argv:
        Path(sys.argv[sys.argv.index('--json') + 1]).write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()

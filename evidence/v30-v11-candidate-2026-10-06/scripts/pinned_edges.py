"""Shore edges of inland water whose land end sits on the land floor: there the crossing of the water plane can only fall
near the wet vertex, so the visible waterline copies the 6 m lattice. Per edge (east, south, NW-SE diagonal) between a
land vertex and a wet vertex of classes 2, 5, 6, 7 above the 0.80 m cut: the water level L (the cell plane of the wet
vertex's side), land height hl, wet height hw, and the crossing distance from the wet vertex. Whole map and a window.
Usage: pinned_edges.py TERRAIN.npz [x0 z0 x1 z1]"""
import json
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees'
                   r'\codex-handoff-review-74f290\tools\terrain')
from v30_common import N, grid_xz  # noqa: E402

t = np.load(sys.argv[1])
h, cls, lev = t['heights'].astype(float), t['cls'], t['level'].astype(float)
beach = t['beach'] if 'beach' in t.files else np.zeros_like(cls, bool)
x, z = grid_xz()
win = None
if len(sys.argv) > 5:
    x0, z0, x1, z1 = (float(v) for v in sys.argv[2:6])
    win = (x >= x0) & (x <= x1) & (z >= z0) & (z <= z1)
wet = np.isin(cls, (2, 5, 6, 7)) & (np.nan_to_num(lev, nan=0) > 0.80)
land = cls == 0
rows = []
for dr, dc, length in ((0, 1, 6.0), (1, 0, 6.0), (1, 1, 6.0 * 2 ** 0.5)):
    a = (slice(0, N - dr), slice(0, N - dc))
    b = (slice(dr, N), slice(dc, N))
    for wa, la in ((a, b), (b, a)):
        m = wet[wa] & land[la]
        L = lev[wa][m]
        hw, hl = h[wa][m], h[la][m]
        ok = (hl > L) & (hw < L)
        frac = np.where(ok, (L - hw) / np.maximum(hl - hw, 1e-9), np.nan)   # 0 at the wet vertex, 1 at the land vertex
        xs = x[wa][m]
        zs = z[wa][m]
        inwin = win[wa][m] if win is not None else np.ones_like(L, bool)
        rows.append(np.column_stack([L, hw, hl, frac * length, np.full_like(L, length), xs, zs, inwin,
                                     cls[wa][m], beach[la][m]]))
E = np.vstack(rows)
L, hw, hl, dcross, length, xs, zs, inwin, kind, onbeach = E.T
floor = np.where(onbeach > 0, 0.80, 1.40)
at_floor = (hl <= np.maximum(floor, 1.60) + 0.02) & (hl - L > 0.20)
pinned = at_floor & (dcross <= 0.4 * length)


def summary(sel):
    n = int(sel.sum())
    return {'edges': n, 'land_on_floor_and_0.2m_above_water': int((at_floor & sel).sum()),
            'pinned_crossing_within_40pct_of_wet_vertex': int((pinned & sel).sum()),
            'pinned_share': round(float((pinned & sel).sum()) / max(n, 1), 3),
            'by_class': {str(int(k)): {'edges': int(((kind == k) & sel).sum()),
                                       'pinned': int(((kind == k) & sel & pinned).sum())} for k in (2, 5, 6, 7)},
            'level_of_pinned_p10_p50_p90': [round(float(np.nanpercentile(L[pinned & sel], q)), 2) for q in (10, 50, 90)]
            if (pinned & sel).any() else None}


out = {'map': summary(np.ones_like(L, bool))}
if win is not None:
    out['window'] = summary(inwin > 0)
print(json.dumps(out, indent=1))

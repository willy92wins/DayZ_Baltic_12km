"""Project the regions Guillermo marked on the v8 RIVER_80 view onto the terrain (ray march over the heightfield) and
say what water is there and why profile_rivers_v30 left it as it was."""
import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

W = Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290')
sys.path.insert(0, str(W / 'tools' / 'terrain'))
from v30_common import N, cell_planes, grid_xz  # noqa: E402
from finish_shores_v30 import protect_corridors  # noqa: E402
from profile_coast_v30 import NARVA, NATURE  # noqa: E402

M = [0.7071067690849304, 0, -0.7071067690849304, 0.4801260530948639, 0.7341374158859253, 0.4801260530948639,
     0.5191137194633484, -0.6790007948875427, 0.5191137194633484, 12012, 80, 1560]
aside, up, d, pos = np.array(M[0:3]), np.array(M[3:6]), np.array(M[6:9]), np.array(M[9:12])
f = 540 / np.tan(np.radians(68.5 / 2))
S = 1920 / 1885                       # Guillermo's screenshot is 1885 px wide
MARKS = {'A_left_channel': [(150, 340), (290, 310), (440, 270)],
         'B_top_center': [(720, 200), (760, 190), (865, 245), (950, 135)],
         'C_center_left': [(540, 385), (615, 410)],
         'D_right': [(1410, 250), (1650, 320), (1580, 300)],
         'E_bottom': [(855, 960), (840, 900)],
         'F_orange_patch': [(680, 40), (800, 30)],
         'G_middle_pond': [(790, 350)]}

t = np.load('E:/DayZ-Baltic-Build/v30-v8/rivers/terrain_rivers.npz')
h, cls, lev = t['heights'].astype(float), t['cls'], t['level'].astype(float)
x, z = grid_xz()


def hit(u, v):
    ray = d + (u * S - 960) / f * aside + (540 - v * S) / f * up
    ray = ray / np.linalg.norm(ray)
    for s in np.arange(1.0, 6000.0, 1.0):
        p = pos + s * ray
        if not (0 <= p[0] <= 12282 and 0 <= p[2] <= 12282):
            return p, None
        r, c = int(round((12282 - p[2]) / 6)), int(round(p[0] / 6))
        ground = max(h[r, c], lev[r, c] if np.isfinite(lev[r, c]) else -99)
        if p[1] <= ground:
            return p, (r, c)
    return None, None


# the fixed set of profile_rivers_v30 (same rules), to name the reason a vertex was left alone
flow = np.isin(cls, (3, 5, 6))
low = flow & (lev <= 0.80)
ids, n = ndimage.label(flow & ~low, structure=np.ones((3, 3), bool))
sizes = np.bincount(ids.ravel(), minlength=n + 1)
small = (ids > 0) & (sizes[ids] < 4)
axes = json.loads(Path('E:/DayZ-Baltic-Build/v30-v3/fit-v3b/axes.json').read_text(encoding='utf-8'))
reach = np.zeros((N, N), bool)
for rr in axes.values():
    for a, b in rr['removed_cells']:
        reach[a:a + 2, b:b + 2] = True
sea = np.isin(cls, (1, 4))
standing = np.isin(cls, (2, 7))
near = {k: ndimage.distance_transform_edt(~m) * 6.0 <= 22.0 for k, m in
        (('sea', sea), ('standing', standing), ('low', low), ('reach', reach), ('small', small))}
nature = np.load(NATURE)['reserve'].astype(bool)
exact, _, _, _ = protect_corridors(cell_planes(cls, lev, sea_cut=0.51))
narva = np.hypot(x - NARVA[0], z - NARVA[1]) <= 620.0
border = (x < 12) | (z < 12) | (x > 12270) | (z > 12270)
_, (ir, ic) = ndimage.distance_transform_edt(cls == 0, return_indices=True)

out = {}
for name, pts in MARKS.items():
    rows = []
    for (u, v) in pts:
        p, rc = hit(u, v)
        if rc is None:
            rows.append({'px': [u, v], 'world': None if p is None else [round(p[0]), round(p[2])], 'note': 'outside the map'})
            continue
        r, c = rc
        # the nearest water vertex and its class, level, depth and the fixed reasons around it
        wr, wc = ir[r, c], ic[r, c]
        k = int(cls[wr, wc])
        reasons = [nm for nm, m in (('nature', nature), ('corridor', exact), ('narva', narva), ('border', border),
                                    ('platform', t['platform']), ('reserve', t['reserve'])) if m[wr, wc]]
        reasons += ['near_' + nm for nm, m in near.items() if m[wr, wc]]
        rows.append({'px': [u, v], 'world': [int(x[r, c]), int(z[r, c])], 'water_at': [int(x[wr, wc]), int(z[wr, wc])],
                     'class': k, 'level': round(float(lev[wr, wc]), 2), 'bed': round(float(h[wr, wc]), 2),
                     'component_size': int(sizes[ids[wr, wc]]) if ids[wr, wc] else 0, 'fixed_reasons': reasons})
    out[name] = rows
print(json.dumps(out, indent=1))

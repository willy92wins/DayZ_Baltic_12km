"""Navigable water (class 3) above the 0.80 m plane cut, outside the 620 m Narva zone: by corridor-touching component,
level range and current depth, and how much of it could keep its bed at or above 0.85 m for a given draft D."""
import json, sys
from pathlib import Path
import numpy as np
from scipy import ndimage
W = Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290')
sys.path.insert(0, str(W / 'tools' / 'terrain'))
from v30_common import N, cell_planes, grid_xz
from finish_shores_v30 import protect_corridors
from profile_coast_v30 import NARVA
t = np.load(sys.argv[1])
h, cls, level = t['heights'].astype(float), t['cls'], t['level'].astype(float)
x, z = grid_xz()
narva = np.hypot(x - NARVA[0], z - NARVA[1]) <= 620.0
exact, margin, entries, _ = protect_corridors(cell_planes(cls, level))
nav = (cls == 3) & (level > 0.80) & ~narva
lab, n = ndimage.label(nav, structure=np.ones((3, 3), int))
rows = []
for i, sl in enumerate(ndimage.find_objects(lab), 1):
    m = lab == i
    k = int(m.sum())
    if k < 50:
        continue
    lv, d = level[m], level[m] - h[m]
    rows.append(dict(id=i, vertices=k, x=round(float(x[m].mean())), z=round(float(z[m].mean())),
                     level=[round(float(lv.min()), 2), round(float(np.median(lv)), 2), round(float(lv.max()), 2)],
                     depth_p50=round(float(np.median(d)), 2), in_corridor=int((m & exact).sum()),
                     bed_below_0p85=int((m & (h < 0.85)).sum())))
rows.sort(key=lambda r: -r['vertices'])
tot = int(nav.sum())
table = {}
for D in (0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.05):
    ok = nav & (level - D >= 0.85)
    table[str(D)] = {'vertices_bed_can_stay_above_0p85': int(ok.sum()), 'share': round(ok.sum() / tot, 3)}
print(json.dumps({'navigable_above_cut_outside_narva': tot, 'corridor_entries': [e['name'] for e in entries],
                  'components': rows[:15], 'by_draft': table}, indent=1, ensure_ascii=False))

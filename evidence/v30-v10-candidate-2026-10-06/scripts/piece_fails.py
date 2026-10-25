"""List the failing pond-piece corners of verify_terrain_v30.py (same rule: water corners >= 0.02 m under the cell
plane, land corners >= 0.00 m over it, outside the 600 m Narva zone) for several terrains and compare the vertex sets.
Usage: piece_fails.py LABEL=terrain.npz [...]"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees'
                   r'\codex-handoff-review-74f290\tools\terrain')
from v30_common import cell_planes  # noqa: E402

NARVA = (2417.1428225906, 6889.8850822322)
sets = {}
for arg in sys.argv[1:]:
    lab, p = arg.split('=', 1)
    t = np.load(p)
    h = t['heights'].astype(float)
    cls, level = t['cls'], t['level'].astype(float)
    water = cls > 0
    n = h.shape[0]
    c, r = np.meshgrid(np.arange(n), np.arange(n))
    zone = np.hypot(c * 6.0 - NARVA[0], 12282 - r * 6.0 - NARVA[1]) <= 600.0
    plane = cell_planes(cls, level, sea_cut=0.51)
    czone = zone[:-1, :-1] | zone[:-1, 1:] | zone[1:, :-1] | zone[1:, 1:]
    fails = []
    for dr in (0, 1):
        for dc in (0, 1):
            hc = h[dr:dr + n - 1, dc:dc + n - 1]
            wc = water[dr:dr + n - 1, dc:dc + n - 1]
            ok = np.isfinite(plane) & ~czone
            with np.errstate(invalid='ignore'):
                for kind, m in (('water', ok & wc & (hc > plane - 0.02)), ('land', ok & ~wc & (hc < plane))):
                    for i, j in zip(*np.nonzero(m)):
                        vr, vc = i + dr, j + dc
                        fails.append((kind, int(vr), int(vc), round(float(h[vr, vc]), 3), round(float(plane[i, j]), 3),
                                      int(cls[vr, vc])))
    sets[lab] = fails
    verts = sorted({(f[1], f[2]) for f in fails})
    print(f'{lab}: {len(fails)} failing corners on {len(verts)} vertices')
    for v in verts:
        rows = [f for f in fails if (f[1], f[2]) == v]
        k = rows[0]
        print(f'   x={6 * v[1]:5d} z={12282 - 6 * v[0]:5d} {k[0]:5s} cls={k[5]} h={k[3]} planes={[f[4] for f in rows]}')
labs = list(sets)
for a in labs:
    for b in labs:
        if a < b:
            va = {(f[1], f[2]) for f in sets[a]}
            vb = {(f[1], f[2]) for f in sets[b]}
            print(f'{a} vs {b}: only {a} {sorted(va - vb)}  only {b} {sorted(vb - va)}')

"""How much inland water of the final v11 terrain still has its bed under the engine sea (0.85 m, the top of its tide
band), by class, and where the navigable class (3) sits: connected components with their size, water level, bed range
and centroid. Read-only. Usage: navigable_below_sea.py INLAND_DIR"""
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

t = np.load(Path(sys.argv[1]) / 'terrain_inland.npz')
H, C, L, W = t['heights'], t['cls'], t['level'], t['water']
n = H.shape[0]
SEA = 0.85
inland = W & (C > 0)
print('inland water vertices', int(inland.sum()))
for k in sorted(set(C[inland].tolist())):
    m = inland & (C == k)
    below = m & (H < SEA)
    print(f'class {k}: {int(m.sum())} vertices, bed under {SEA} m: {int(below.sum())} '
          f'({100 * below.sum() / max(1, m.sum()):.1f} %), level p50 {np.median(L[m]):.2f} m')
nav = inland & (C == 3)
lab, nlab = ndimage.label(nav, structure=np.ones((3, 3)))
rows = []
for i in range(1, nlab + 1):
    m = lab == i
    cnt = int(m.sum())
    r, c = np.nonzero(m)
    below = int((m & (H < SEA)).sum())
    rows.append((cnt, below, float(np.median(L[m])), float(H[m].min()), float(np.median(H[m])),
                 c.mean() * 6.0, (n - 1 - r.mean()) * 6.0, (c.min() * 6, c.max() * 6, (n - 1 - r.max()) * 6, (n - 1 - r.min()) * 6)))
rows.sort(reverse=True)
print(f'navigable components: {nlab}')
for cnt, below, lvl, bmin, bmed, cx, cz, bb in rows[:12]:
    print(f'  {cnt:6d} vertices ({cnt * 36 / 1e4:.1f} ha), bed under sea {below} ({100 * below / cnt:.0f} %), level {lvl:.2f} m, '
          f'bed min {bmin:.2f} p50 {bmed:.2f} m, centre ({cx:.0f}, {cz:.0f}), x {bb[0]}-{bb[1]} z {bb[2]}-{bb[3]}')

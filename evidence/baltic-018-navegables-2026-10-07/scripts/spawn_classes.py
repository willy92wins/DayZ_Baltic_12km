"""Water classes, water levels and bed heights of the final v11 terrain (inland/terrain_inland.npz) across the river
south of the spawn (1185, 5392). The array orientation is fixed by matching the engine's surface heights at known land
points. Read-only. Usage: spawn_classes.py INLAND_DIR"""
import sys
from pathlib import Path

import numpy as np

t = np.load(Path(sys.argv[1]) / 'terrain_inland.npz')
H, C, L, W = t['heights'], t['cls'], t['level'], t['water']
n = H.shape[0]
known = {(6000, 6000): 4.83, (10408, 3924): 4.24, (11700, 1460): 3.20, (12000, 4998): 3.75}


def idx(x, z, north_up):
    c = int(round(x / 6.0))
    r = (n - 1 - int(round(z / 6.0))) if north_up else int(round(z / 6.0))
    return r, c


best = None
for north_up in (True, False):
    err = sum(abs(float(H[idx(x, z, north_up)]) - v) for (x, z), v in known.items())
    print('north_up' if north_up else 'south_up', 'abs error vs engine', round(err, 2))
    if best is None or err < best[0]:
        best = (err, north_up)
nu = best[1]
print('classes present near spawn:', sorted(set(C[idx(1185, 5392, nu)[0] - 60: idx(1185, 5392, nu)[0] + 60,
                                                  idx(1185, 5392, nu)[1] - 60: idx(1185, 5392, nu)[1] + 60].ravel().tolist())))
for z in (5300, 5250, 5200, 5150):
    cells = []
    for x in range(1100, 1461, 6):
        r, c = idx(x, z, nu)
        if W[r, c] or C[r, c]:
            cells.append(f'{x}:c{C[r, c]} h{H[r, c]:.2f} L{L[r, c]:.2f}')
        else:
            cells.append(f'{x}:land h{H[r, c]:.2f}')
    print(f'z={z}:')
    for i in range(0, len(cells), 6):
        print('   ' + ' | '.join(cells[i:i + 6]))

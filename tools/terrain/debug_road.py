"""Inspect one road chain around a point: terrain, final heights and station spacing."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v30_common import tri_sample  # noqa: E402
from verify_roads_v30 import road_chains  # noqa: E402

V30 = sys.argv[1]
px, pz = float(sys.argv[2]), float(sys.argv[3])
t = np.load(os.path.join(V30, "terrain_v30.npz"))
h = t["heights"].astype(float)
relief = np.load(r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\tests\relief_v30\relief_v30_mix.npz")["new"].astype(float)
chains = road_chains()
best = None
for ci, c in enumerate(chains):
    d = np.hypot(c[:, 0] - px, c[:, 1] - pz)
    if best is None or d.min() < best[0]:
        best = (d.min(), ci)
ci = best[1]
c = chains[ci]
station = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]
print("chain", ci, "points", len(c), "length", round(station[-1], 1), "min point spacing", round(float(np.diff(station).min()), 4))
dup = np.sum(np.diff(station) < 1e-6)
print("zero-length steps in the chain:", int(dup))
s = np.linspace(0, station[-1], int(np.ceil(station[-1])) + 1)
q = np.column_stack([np.interp(s, station, c[:, k]) for k in (0, 1)])
k = int(np.argmin(np.hypot(q[:, 0] - px, q[:, 1] - pz)))
for i in range(max(0, k - 12), min(len(s), k + 13), 2):
    print(f"s={s[i]:8.1f}  xz=({q[i,0]:8.1f},{q[i,1]:8.1f})  relief={tri_sample(relief, q[i:i+1,0], q[i:i+1,1])[0]:7.2f}  final={tri_sample(h, q[i:i+1,0], q[i:i+1,1])[0]:7.2f}")
# other chains passing within 15 m of this point
near = [cj for cj, cc in enumerate(chains) if cj != ci and np.hypot(cc[:, 0] - px, cc[:, 1] - pz).min() < 25]
print("other chains within 25 m:", near)

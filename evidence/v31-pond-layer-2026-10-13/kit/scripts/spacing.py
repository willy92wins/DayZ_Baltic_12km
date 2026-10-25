"""Chernarus streambed: nearest forward neighbour (+Z, upstream) per straight piece, aligned within 6 deg and |lx| < 1.5 m."""
import sys
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, r"E:/DayZ-Baltic-Build/vanilla-tricks-20261013/scripts")
from terrain import objects
S = [o for o in objects("chernarus") if "\streambed\\" in o["shape"] and "\misc\\" not in o["shape"]]
kind = lambda o: o["shape"].split("\\")[-1][:-4].split("_", 2)[2].replace("_2", "")
C = np.array([[o["x"], o["z"]] for o in S]); Y = np.array([o["y"] for o in S])
Zs = np.array([[o["az_x"], o["az_z"]] for o in S]); Zs /= np.linalg.norm(Zs, axis=1)[:, None]
tree = cKDTree(C); res = {}
for i, o in enumerate(S):
    if "straight" not in kind(o):
        continue
    best = None
    for j in tree.query_ball_point(C[i], 30):
        if j == i or "straight" not in kind(S[j]):
            continue
        v = C[j] - C[i]; lz = v @ Zs[i]; lx = v @ np.array([Zs[i][1], -Zs[i][0]])
        if lz > 0 and abs(lx) < 1.5 and Zs[i] @ Zs[j] > np.cos(np.radians(6)):
            if best is None or lz < best[0]:
                best = (lz, kind(S[j]), Y[j] - Y[i])
    if best:
        res.setdefault((kind(o), best[1]), []).append(best[0])
for k, v in sorted(res.items()):
    v = np.array(v); print(k, len(v), "spacing p10/50/90", np.percentile(v, [10, 50, 90]).round(2))

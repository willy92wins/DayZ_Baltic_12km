"""Chernarus streambed chaining: model counts, flow direction vs model Z, neighbour offsets and yaw steps per model."""
import sys, json, collections
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, r"E:/DayZ-Baltic-Build/vanilla-tricks-20261013/scripts")
from terrain import Terrain, objects
T = Terrain("chernarus")
S = [o for o in objects("chernarus") if "\streambed\\" in o["shape"] and "\misc\\" not in o["shape"]]
name = lambda o: o["shape"].split("\\")[-1].replace(".p3d", "")
kind = lambda n: n.split("_", 2)[2]          # long_straight, short_arrow, ...
print(collections.Counter(kind(name(o)) for o in S))
print(collections.Counter(name(o).split("_")[1] for o in S))
C = np.array([[o["x"], o["y"], o["z"]] for o in S])
A = [np.array([[o["ax_x"], o["ay_x"], o["az_x"]], [o["ax_y"], o["ay_y"], o["az_y"]], [o["ax_z"], o["ay_z"], o["az_z"]]]) for o in S]
# pitch along model Z (positive = +Z goes up)
pz = np.array([np.degrees(np.arcsin(a[1, 2] / np.linalg.norm(a[:, 2]))) for a in A])
print("pitch along +Z deg p10/50/90", np.percentile(pz, [10, 50, 90]).round(2), "share +Z downhill", round(float((pz < -0.05).mean()), 3), "uphill", round(float((pz > 0.05).mean()), 3))
# neighbour relations in local frame (horizontal)
tree = cKDTree(C[:, [0, 2]])
rel = collections.defaultdict(list)
for i, o in enumerate(S):
    a = A[i]; X = a[[0, 2], 0] / np.linalg.norm(a[[0, 2], 0]); Z = a[[0, 2], 2] / np.linalg.norm(a[[0, 2], 2])
    for j in tree.query_ball_point(C[i, [0, 2]], 30.0):
        if j == i: continue
        v = C[j, [0, 2]] - C[i, [0, 2]]
        lx, lz = float(v @ X), float(v @ Z)
        bj = A[j]; Zj = bj[[0, 2], 2] / np.linalg.norm(bj[[0, 2], 2])
        dyaw = float(np.degrees(np.arctan2(Z[0] * Zj[1] - Z[1] * Zj[0], Z @ Zj)))
        dy = float(C[j, 1] - C[i, 1])
        rel[kind(name(o))].append((round(lx, 1), round(lz, 1), round(dyaw, 1), round(dy, 2), kind(name(S[j]))))
out = {}
for k, lst in rel.items():
    a = np.array([r[:4] for r in lst])
    fwd = a[a[:, 1] > 0]; back = a[a[:, 1] < 0]
    out[k] = dict(n=len(lst), fwd_nearest=sorted(lst, key=lambda r: abs(r[0]) + abs(r[1]))[:0])
    for tag, b in (("fwd", fwd), ("back", back)):
        if len(b):
            # nearest per piece approximated: rows with |lx|<6 and 4<|lz|<26
            m = b[(np.abs(b[:, 0]) < 8) & (np.abs(b[:, 1]) > 4) & (np.abs(b[:, 1]) < 28)]
            if len(m):
                out[k][tag] = dict(n=len(m), lx=np.percentile(m[:, 0], [10, 50, 90]).round(2).tolist(), lz=np.percentile(m[:, 1], [10, 50, 90]).round(2).tolist(),
                                   dyaw=np.percentile(m[:, 2], [10, 50, 90]).round(1).tolist(), abs_dyaw_p90=round(float(np.percentile(np.abs(m[:, 2]), 90)), 1),
                                   dy=np.percentile(m[:, 3], [10, 50, 90]).round(2).tolist())
print(json.dumps(out, indent=1))

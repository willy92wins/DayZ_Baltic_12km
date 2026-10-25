import json, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
SP = sys.argv[1]
pick = json.load(open(f"{SP}/picked.json"))
G = {}
for line in open(f"{SP}/grid.log"):
    f = line.strip().split(";")
    if f[0] == "G":
        G[(int(f[1]), int(f[2]), int(f[3]))] = (float(f[4]), float(f[5]))
CELL = 7.5
votes = {"NWSE": 0, "NESW": 0, "flat": 0}
fig, axs = plt.subplots(3, 4, figsize=(20, 15))
for k, (p, ax) in enumerate(zip(pick, axs.T.ravel())):
    ground = np.array([[G[(k, i, j)][0] for i in range(-20, 21)] for j in range(-20, 21)])   # rows = z (j), cols = x (i)
    water = np.array([[G[(k, i, j)][1] for i in range(-20, 21)] for j in range(-20, 21)])
    wet = water > ground
    xs = p["x"] + np.arange(-20, 21); zs = p["z"] + np.arange(-20, 21)
    ax.imshow(np.where(wet, 1.0, 0.0), origin="lower", extent=[xs[0] - .5, xs[-1] + .5, zs[0] - .5, zs[-1] + .5], cmap="Blues", vmin=0, vmax=1.3)
    # terrain grid lines (7.5 m) for reference
    for gx in np.arange(np.ceil(xs[0] / CELL) * CELL, xs[-1], CELL): ax.axvline(gx, color="k", lw=0.3, alpha=0.4)
    for gz in np.arange(np.ceil(zs[0] / CELL) * CELL, zs[-1], CELL): ax.axhline(gz, color="k", lw=0.3, alpha=0.4)
    ax.set_title(f"{p['kind']} yaw {p['yaw']} wet {int(wet.sum())} m2")
    # triangulation vote per full cell
    X, Z = np.meshgrid(xs, zs)
    for cx in np.arange(np.ceil(xs[0] / CELL) * CELL, xs[-1] - CELL, CELL):
        for cz in np.arange(np.ceil(zs[0] / CELL) * CELL, zs[-1] - CELL, CELL):
            m = (X > cx + 0.3) & (X < cx + CELL - 0.3) & (Z > cz + 0.3) & (Z < cz + CELL - 0.3)
            if m.sum() < 20: continue
            u, v, h = (X[m] - cx) / CELL, (Z[m] - cz) / CELL, ground[m]
            res = {}
            for name, side in (("NWSE", u + v < 1), ("NESW", u < v)):        # NW-SE diagonal joins (0,1)-(1,0): u+v=1 ; NE-SW joins (0,0)-(1,1): u=v
                r = 0.0
                for s in (side, ~side):
                    if s.sum() < 3: continue
                    A = np.c_[u[s], v[s], np.ones(s.sum())]
                    coef, *_ = np.linalg.lstsq(A, h[s], rcond=None)
                    r += float(((A @ coef - h[s]) ** 2).sum())
                res[name] = r
            if max(res.values()) < 1e-4:
                votes["flat"] += 1
            else:
                votes[min(res, key=res.get)] += 1
fig.savefig(f"{SP}/chern_wet.png", dpi=55, bbox_inches="tight")
print("triangulation votes over full cells:", votes)

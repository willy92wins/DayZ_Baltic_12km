"""Render a dam_v31 placement: plan before/after (visible pond, engine sea at 0.75 m, dam visual LOD outline and notch,
raised vertices) and two north-south sections through the wall and the notch (terrain before/after, pond planes, tide
band, geometry LOD solid). The perspective view is render_view_dam_v31.py.
Usage: render_dam_v31.py <base_terrain.npz> <base_fp.npz> <terrain.npz> <fp.npz> <records.json> <report.json> <out_prefix>"""
import json, os, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dam_v31 as D
from dam_gates_v31 import raster
sys.path.insert(0, r"C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts")
from odol_reader import ODOL

bt, bfp, tp, fpp, recp, repp, outp = sys.argv[1:8]
H0 = np.load(bt)["heights"].astype(np.float64); H = np.load(tp)["heights"].astype(np.float64)
f0 = np.load(bfp); f1 = np.load(fpp)
recs = [r for r in json.load(open(recp)) if r["model"] == D.MODEL]; mats = [r["matrix"] for r in recs]
rep = json.load(open(repp))
od = ODOL.from_file(D.P3D)
vis = [l for l in od.lods if abs(l.resolution - 1.0) < 1e-6][0]
VV = np.array([(p.x, p.y, p.z) for p in vis.vertices])
TRI = []
for f in vis.faces:
    ids = list(f.vertex_indices)
    for i in range(1, len(ids) - 1):
        TRI.append(VV[[ids[0], ids[i], ids[i + 1]]])
TRI = np.array(TRI)


def world_tris(m):
    A = np.array(m[:9]).reshape(3, 3).T; t = np.array(m[9:12])
    return TRI @ A.T + t


x0, x1, z0, z1 = 2340, 2510, 6900, 7010   # Narva site window
fig, axs = plt.subplots(1, 2, figsize=(20, 7.6))
ls = LightSource(azdeg=315, altdeg=40)
for ax, (HH, fp, title) in zip(axs, ((H0, f0, "EV110 (before)"), (H, f1, "dam prototype (after)"))):
    X, Z, T, cov, P, F, pond = raster(HH, fp["plane"].astype(np.float64), fp["field"], x0, x1, z0, z1)
    shade = ls.hillshade(T, vert_exag=3, dx=0.25, dy=0.25)
    img = np.dstack([0.55 + 0.4 * shade, 0.5 + 0.38 * shade, 0.35 + 0.3 * shade])
    sea = (~cov) & (T < 0.75)
    img[sea] = (0.15, 0.32, 0.62)
    img[(~cov) & (T >= 0.75) & (T < 1.0)] = (0.55, 0.7, 0.85)
    img[pond] = (0.25, 0.68, 0.62)
    ax.imshow(np.clip(img, 0, 1), extent=(x0, x1, z0, z1), interpolation="nearest")
    cs = ax.contour(X, Z, T, levels=[1.5, 2.5, 3.5, 4.5], colors="k", linewidths=0.35)
    ax.clabel(cs, fontsize=6)
    if HH is H:
        for m in mats:
            W = world_tris(m)
            # outline = convex hull of the visual LOD in plan
            from scipy.spatial import ConvexHull
            pts = W[:, :, [0, 2]].reshape(-1, 2); hull = ConvexHull(pts)
            ax.fill(pts[hull.vertices, 0], pts[hull.vertices, 1], color=(0.55, 0.53, 0.5), alpha=0.95, zorder=5)
            # notch
            A = np.array(m[:9]).reshape(3, 3).T; t = np.array(m[9:12])
            nch = np.array([[-3.39, 0, -1.34], [3.37, 0, -1.34], [3.37, 0, 1.17], [-3.39, 0, 1.17]]) @ A.T + t
            ax.fill(nch[:, 0], nch[:, 2], color=(0.35, 0.33, 0.3), zorder=6)
        mv = np.argwhere(H != H0)
        ax.plot(6 * mv[:, 1], 12282 - 6 * mv[:, 0], "o", ms=4, mfc="none", mec="red", zorder=7, label="raised vertex")
        ax.legend(loc="lower right", fontsize=8)
    ax.set_xlim(x0, x1); ax.set_ylim(z0, z1); ax.set_aspect("equal")
    ax.set_title(title + ": pond (teal), engine sea < 0.75 (blue), 0.75-1.0 tide band (light blue), dam (grey, notch dark)", fontsize=9)
plt.tight_layout(); plt.savefig(outp + "-plan.png", dpi=85); plt.close()

# sections (north-south) through the wall and the notch
s = rep["sites"][0]
fig, axs = plt.subplots(1, 2, figsize=(18, 5))
for ax, xs in zip(axs, (2420.0, 2404.0)):
    zz = np.arange(6915.0, 6975.0, 0.1)
    h0 = [D.height(H0, xs, z) for z in zz]; h1 = [D.height(H, xs, z) for z in zz]
    ax.plot(zz, h0, color="0.6", lw=1, label="terrain EV110")
    ax.plot(zz, h1, color="saddlebrown", lw=1.6, label="terrain after")
    # pond / sea surfaces
    for fp, col, lab in ((f0, "tab:cyan", "pond EV110"), (f1, "teal", "pond after")):
        pl = fp["plane"]
        pz = [z for z in zz if np.isfinite(pl[int((12282 - z) // 6), int(xs // 6)])]
        if pz:
            lev = [float(pl[int((12282 - z) // 6), int(xs // 6)]) for z in pz]
            ax.plot(pz, lev, ".", ms=1.5, color=col, label=lab)
    ax.axhspan(0.5, 1.0, color="tab:blue", alpha=0.12, label="engine sea tide band 0.5-1.0")
    ax.axhline(0.75, color="tab:blue", lw=0.8)
    # dam section: solid membership on a (z, y) grid
    ZZ, YY = np.meshgrid(zz, np.arange(-4.0, 6.0, 0.05))
    ins = D.solid(mats, np.full(ZZ.shape, xs), YY, ZZ)
    ax.contourf(ZZ, YY, ins.astype(float), levels=[0.5, 1.5], colors=["0.45"], alpha=0.9)
    ax.set_title(f"N-S section at x = {xs:.0f} ({'spillway notch' if xs == 2404.0 else 'full wall'}); south = upstream pond, north = sea", fontsize=9)
    ax.set_xlabel("z (m, north ->)"); ax.set_ylabel("y (m)"); ax.set_ylim(-4.5, 6.5); ax.grid(alpha=0.3)
    ax.legend(fontsize=7, loc="lower left")
plt.tight_layout(); plt.savefig(outp + "-sections.png", dpi=85); plt.close()

print("ok")

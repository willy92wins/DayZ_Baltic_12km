"""Perspective view of a dam_v31 placement (painter's algorithm, flat-shaded): native 6 m terrain triangles, pond pieces
at their plane, engine sea at 0.75 m over every sea cell, the dam's visual LOD. Before and after side by side.
Usage: render_view_dam_v31.py <base_terrain.npz> <base_fp.npz> <terrain.npz> <fp.npz> <records.json> <out.png>
       [cam_x cam_y cam_z look_x look_y look_z]"""
import json, os, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dam_v31 as D
sys.path.insert(0, r"C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts")
from odol_reader import ODOL

bt, bfp, tp, fpp, recp, outp = sys.argv[1:7]
cam = np.array([float(v) for v in sys.argv[7:10]]) if len(sys.argv) > 9 else np.array([2372.0, 18.0, 6990.0])
look = np.array([float(v) for v in sys.argv[10:13]]) if len(sys.argv) > 12 else np.array([2428.0, 1.5, 6935.0])
od = ODOL.from_file(D.P3D)
vis = [l for l in od.lods if abs(l.resolution - 1.0) < 1e-6][0]
VV = np.array([(p.x, p.y, p.z) for p in vis.vertices])
TRI = np.array([VV[[f.vertex_indices[0], f.vertex_indices[i], f.vertex_indices[i + 1]]] for f in vis.faces
                for i in range(1, len(f.vertex_indices) - 1)])
LIGHT = np.array([-0.5, 0.8, 0.3]); LIGHT /= np.linalg.norm(LIGHT)


def scene(H, fp, mats, x0=2330, x1=2520, z0=6880, z1=7030):
    polys = []   # (world tris (3,3) in x,y,z, base colour)
    pl = fp["plane"]
    c0, c1 = x0 // 6, x1 // 6; r0, r1 = int((12282 - z1) // 6), int((12282 - z0) // 6)
    for r in range(r0, r1):
        for c in range(c0, c1):
            nw = (6 * c, H[r, c], 12282 - 6 * r); ne = (6 * c + 6, H[r, c + 1], 12282 - 6 * r)
            sw = (6 * c, H[r + 1, c], 12282 - 6 * r - 6); se = (6 * c + 6, H[r + 1, c + 1], 12282 - 6 * r - 6)
            for t in ((nw, ne, se), (nw, se, sw)):
                polys.append((np.array(t, float), (0.62, 0.56, 0.38)))
            p = pl[r, c]
            if np.isfinite(p):
                for t in ((nw, ne, se), (nw, se, sw)):
                    a = np.array(t, float); a[:, 1] = p; polys.append((a, (0.22, 0.6, 0.58)))
            elif min(nw[1], ne[1], sw[1], se[1]) < 0.75:
                for t in ((nw, ne, se), (nw, se, sw)):
                    a = np.array(t, float); a[:, 1] = 0.75; polys.append((a, (0.16, 0.3, 0.55)))
    for m in mats:
        A = np.array(m[:9]).reshape(3, 3).T; tt = np.array(m[9:12])
        for t in TRI @ A.T + tt:
            polys.append((t, (0.62, 0.6, 0.57)))
    return polys


def draw(ax, polys, title):
    f = look - cam; f /= np.linalg.norm(f)
    rgt = np.cross(f, [0, 1, 0]); rgt /= np.linalg.norm(rgt); up = np.cross(rgt, f)
    P2, cols, depth = [], [], []
    for t, col in polys:
        d = t - cam
        zc = d @ f
        if (zc < 1.0).any():
            continue
        xs = (d @ rgt) / zc; ys = (d @ up) / zc
        if np.abs(xs).max() > 1.2 or np.abs(ys).max() > 1.0:
            continue
        n = np.cross(t[1] - t[0], t[2] - t[0]); nn = np.linalg.norm(n)
        if nn < 1e-9:
            continue
        n /= nn
        if n @ (cam - t.mean(0)) < 0:
            n = -n
        k = 0.45 + 0.55 * max(0.0, float(n @ LIGHT))
        P2.append(np.stack([xs, ys], 1)); cols.append(tuple(min(1.0, ci * k) for ci in col)); depth.append(float(zc.mean()))
    order = np.argsort(depth)[::-1]
    ax.add_collection(PolyCollection([P2[i] for i in order], facecolors=[cols[i] for i in order], edgecolors="none"))
    ax.set_xlim(-1.0, 1.0); ax.set_ylim(-0.6, 0.45); ax.set_aspect("equal"); ax.axis("off"); ax.set_title(title, fontsize=10)


H0 = np.load(bt)["heights"].astype(np.float64); H = np.load(tp)["heights"].astype(np.float64)
mats = [r["matrix"] for r in json.load(open(recp)) if r["model"] == D.MODEL]
fig, axs = plt.subplots(2, 1, figsize=(14, 15))
draw(axs[0], scene(H0, np.load(bfp), []), f"EV110 from ({cam[0]:.0f}, {cam[2]:.0f}), {cam[1]:.0f} m up: pond (teal) meets the engine sea (blue)")
draw(axs[1], scene(H, np.load(fpp), mats), "dam prototype: 2 x dam_stone_40, pond behind the wall, sea and dry old bed in front")
plt.tight_layout(); plt.savefig(outp, dpi=80); print("ok")

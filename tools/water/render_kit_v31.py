"""Kit pilot view: A = EV107 waterline on hillshade, B = EV108 hillshade, remaining pond waterline, kit pieces (bed band
+-2.5 m grey, water +-1.75 m blue) and stones. Usage: render_kit_v31.py <out.png> <tA> <fpA> <tB> <fpB> <records.json> x,z,R ..."""
import json, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
out, tA, fA, tB, fB, recp = sys.argv[1:7]
sites = [tuple(map(float, a.split(","))) for a in sys.argv[7:]]
recs = json.load(open(recp))
def water(H, pl, r0, r1, c0, c1, K=4):
    h = H[r0:r1 + 1, c0:c1 + 1]; p = pl[r0:r1, c0:c1]
    o = np.full(((r1 - r0) * K, (c1 - c0) * K), np.nan)
    for i in range(K):
        for j in range(K):
            fr, fc = (i + .5) / K, (j + .5) / K
            nw, ne, sw, se = h[:-1, :-1], h[:-1, 1:], h[1:, :-1], h[1:, 1:]
            t = np.where(fc >= fr, nw + fc * (ne - nw) + fr * (se - ne), nw + fr * (sw - nw) + fc * (se - sw))
            o[i::K, j::K] = np.where(np.isfinite(p) & (t < p), 1.0, np.nan)
    return o
def shade(h):
    gy, gx = np.gradient(h, 6.0); return np.clip(0.6 + 0.35 * (-gx - gy) / np.sqrt(1 + gx ** 2 + gy ** 2), 0, 1)
fig, axs = plt.subplots(len(sites), 2, figsize=(14, 7 * len(sites)))
axs = np.atleast_2d(axs)
for row, (x, z, R) in enumerate(sites):
    c0, c1 = int((x - R) / 6), int((x + R) / 6); r0, r1 = int((12282 - (z + R)) / 6), int((12282 - (z - R)) / 6)
    ext = (6 * c0, 6 * c1, 12282 - 6 * r1, 12282 - 6 * r0)
    for col, (tp, fp, tag) in enumerate(((tA, fA, "A EV107"), (tB, fB, "B EV108 kit"))):
        H = np.load(tp)["heights"].astype(float); pl = np.load(fp)["plane"].astype(float)
        ax = axs[row, col]
        ax.imshow(shade(H[r0:r1 + 1, c0:c1 + 1]), cmap="gray", extent=ext, vmin=0, vmax=1)
        cs = ax.contour(np.linspace(ext[0], ext[1], c1 - c0 + 1), np.linspace(ext[3], ext[2], r1 - r0 + 1), H[r0:r1 + 1, c0:c1 + 1], levels=np.arange(0, 60, 1.0), colors="peru", linewidths=0.4)
        ax.imshow(water(H, pl, r0, r1, c0, c1), cmap="winter", extent=ext, alpha=0.8, vmin=0, vmax=1)
        if col == 1:
            for r in recs:
                m = r["matrix"]; X = np.array(m[0:3]); Z = np.array(m[6:9]); T = np.array(m[9:12])
                if r["piece"] == "stones":
                    ax.plot(T[0], T[2], "o", color="saddlebrown", ms=4); continue
                L = 12.0 if "short" in r["model"] else 24.0
                for half, colr in ((2.5, "dimgray"), (1.75, "deepskyblue")):
                    pts = [T + sx * half * X + sz * L / 2 * Z for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                    ax.add_patch(Polygon([(p[0], p[2]) for p in pts], closed=True, color=colr, alpha=0.85, lw=0))
        ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_title(f"{tag} ({x:.0f},{z:.0f})")
plt.tight_layout(); plt.savefig(out, dpi=80)

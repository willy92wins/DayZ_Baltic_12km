"""EV112 causeway track, before/after: hillshaded heights, exact waterline (red) and road platform (yellow); the title
quotes the gate's own measurements (gate.json of gate_causeway.py).
Usage: render_islet.py <before.npz> <before_fp.npz> <after.npz> <after_fp.npz> <gate.json> <out.png> [x0 x1 z0 z1 [label]]"""
import json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LightSource
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "tools", "water"))
import shore_ramp_v31 as sr                                   # evidence/v31-pond-layer-2026-10-13/ev112/causeway

bt, bf, at, af, gp, out = sys.argv[1:7]
x0, x1, z0, z1 = [float(v) for v in sys.argv[7:11]] if len(sys.argv) > 10 else (6600, 7700, 10080, 10820)
label = sys.argv[11] if len(sys.argv) > 11 else "Islet causeways (6900, 10500)"
g = json.load(open(gp, encoding="utf-8"))
c0, c1 = int(x0 / 6), int(x1 / 6) + 1
r0, r1 = int((12282 - z1) / 6), int((12282 - z0) / 6) + 1
panels = []
for tp, fpp in ((bt, bf), (at, af)):
    z = np.load(tp)
    H = z["heights"].astype(np.float64)
    f = np.load(fpp)
    plane = f["plane"].astype(np.float64)
    W, fp = sr.corner_water(plane, f["field"].astype(np.float64))
    seg = sr.extract_segments(H, W, fp, plane, r0, r1, c0, c1)
    panels.append((H, seg, z["platform"]))
w = (x1 - x0) / (z1 - z0)
fig, axs = plt.subplots(1, 2, figsize=(min(13 * w, 13) * 2, min(13, 13 / w) + 1.6))
ls = LightSource(azdeg=315, altdeg=35)
for axp, (H, seg, plat), title in zip(axs, panels, ("before (EV110 terrain)", "after (causeway_v31 round 2)")):
    h = H[r0:r1 + 1, c0:c1 + 1]
    rgb = ls.shade(np.clip(h, -2.5, 4.0), cmap=plt.cm.gist_earth, vert_exag=4, dx=6, dy=6, blend_mode="soft",
                   vmin=-2.5, vmax=4.0)
    ext = (6 * c0 - 3, 6 * (c1 + 1) - 3, 12282 - 6 * (r1 + 1) + 3, 12282 - 6 * r0 + 3)
    axp.imshow(rgb, extent=ext, interpolation="nearest")
    p = plat[r0:r1 + 1, c0:c1 + 1].astype(float)
    X = 6.0 * np.arange(c0, c1 + 1); Z = 12282 - 6.0 * np.arange(r0, r1 + 1)
    axp.contour(X, Z, p, [0.5], colors="#ffd000", linewidths=0.7)
    axp.add_collection(LineCollection(seg["p"], colors="#ff2040", linewidths=1.1))
    axp.set_xlim(x0, x1); axp.set_ylim(z0, z1); axp.set_aspect("equal")
    axp.set_title(title + "  -  red: exact waterline, yellow: road platform (frozen)", fontsize=11)
    axp.grid(alpha=0.25)
txt = []
for e in g.get("causeways", []):
    L, R = e["left_after"], e["right_after"]
    txt.append(f"{e['id']} chain {e['chain']} {e['interval'][0]:.0f}-{e['interval'][1]:.0f}: width {e['width']['median']:.2f} m on "
               f"{e['width']['core_frac'] * 100:.0f}% of the run; wiggle p90 over the whole run L {e['left_before']['wiggle_p90']}->"
               f"{L['wiggle_p90']}, R {e['right_before']['wiggle_p90']}->{R['wiggle_p90']} m; links p90 <= "
               f"{max(x for x in (L['link_s0']['wiggle_p90'], L['link_s1']['wiggle_p90'], R['link_s0']['wiggle_p90'], R['link_s1']['wiggle_p90']) if x is not None)} m")
fig.suptitle(label + f"  (gate verdict {g.get('verdict')})\n" + "\n".join(txt), fontsize=11)
plt.tight_layout()
plt.savefig(out, dpi=72)

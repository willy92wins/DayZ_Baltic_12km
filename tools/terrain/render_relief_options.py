"""Three-way relief comparison: V29, option A (moderate) and option B (regenerated), plus profiles."""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

A_DIR, B_DIR, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
a = np.load(os.path.join(A_DIR, "relief_v30.npz"))
b = np.load(os.path.join(B_DIR, "relief_v30.npz"))
v29, ha, hb = a["v29"].astype(float), a["new"].astype(float), b["new"].astype(float)
EXT = (0, 12288, 0, 12288)


def shade_rgb(h):
    gy, gx = np.gradient(h, 6.0)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    az, zen = np.radians(315), np.radians(50)
    hs = np.clip(np.cos(zen) * np.cos(slope) + np.sin(zen) * np.sin(slope) * np.cos(az - aspect), 0, 1)
    tint = plt.get_cmap("gist_earth")(np.clip((h + 5) / 115, 0.15, 1))[..., :3]
    rgb = tint * (0.30 + 0.70 * hs[..., None])
    rgb[h < 0.8] = (0.33, 0.52, 0.72)
    return rgb


fig, ax = plt.subplots(1, 3, figsize=(24, 8.6), dpi=80)
titles = ["V29 actual", "A · ajuste moderado (V29 en zonas altas, bordes eliminados, llanos)", "B · relieve regenerado desde la topografía real"]
for axis, h, t in zip(ax, (v29, ha, hb), titles):
    axis.imshow(shade_rgb(h), extent=EXT, interpolation="lanczos")
    axis.set_title(t, fontsize=12)
    axis.set_xticks([]); axis.set_yticks([])
fig.tight_layout()
fig.savefig(os.path.join(OUT, "relief-options.png"))
plt.close(fig)

fig, ax = plt.subplots(3, 1, figsize=(16, 10), dpi=80)
for axis, (name, kind, idx) in zip(ax, [("Oeste–este en z=7950 (zona A y antiguo rectángulo SPB)", "row", int((12282 - 7950) / 6)),
                                        ("Norte–sur en x=8200 (reserva)", "col", int(8200 / 6)),
                                        ("Oeste–este en z=1100 (zona B)", "row", int((12282 - 1100) / 6))]):
    pos = np.arange(2048) * 6.0 if kind == "row" else 12282 - np.arange(2048) * 6.0
    for h, lab, col, lw in ((v29, "V29", "gray", 1.0), (ha, "A", "tab:orange", 1.2), (hb, "B", "darkgreen", 1.2)):
        prof = h[idx, :] if kind == "row" else h[:, idx]
        axis.plot(pos, prof, color=col, lw=lw, label=lab)
    axis.set_title(name, fontsize=10)
    axis.set_ylabel("m")
    axis.legend(loc="upper right", fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "relief-options-profiles.png"))
plt.close(fig)
print("rendered")

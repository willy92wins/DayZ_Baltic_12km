import numpy as np, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
x0, x1, z0, z1 = [float(a) for a in sys.argv[1:5]]; out = sys.argv[5]
c0, c1 = int(x0/6), int(x1/6); r0, r1 = int(2047 - z1/6), int(2047 - z0/6)
fig, axs = plt.subplots(1, 2, figsize=(16, 8 * (r1 - r0) / (c1 - c0) + 0.6))
for ax, (name, p) in zip(axs, (("EV100", "E:/DayZ-Baltic-Build/v31-ev100-pond-banks-20261012/terrain-ev100.npz"), ("EV101", "E:/DayZ-Baltic-Build/v31-ev101-sea-bed-20261012/terrain-ev101.npz"))):
    H = np.load(p)["heights"][r0:r1, c0:c1].astype(float)
    d = np.ma.masked_where(H >= 0.75, H)
    ax.imshow(np.where(H >= 0.75, 1, np.nan), extent=[6*c0, 6*c1, 6*(2047-r1), 6*(2047-r0)], cmap="Greens", vmin=0, vmax=3, interpolation="nearest")
    im = ax.imshow(d, extent=[6*c0, 6*c1, 6*(2047-r1), 6*(2047-r0)], cmap="viridis", vmin=-4, vmax=0.75, interpolation="nearest")
    ax.set_title(f"{name} sea bed (m), clipped to -4")
fig.colorbar(im, ax=axs, shrink=0.7)
fig.savefig(out, dpi=70, bbox_inches="tight")

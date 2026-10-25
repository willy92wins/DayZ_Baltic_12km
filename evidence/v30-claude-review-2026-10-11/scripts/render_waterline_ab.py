import numpy as np, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import contourpy
cov = np.load("E:/DayZ-Baltic-Build/v30-shore-sdf-20261011/cover-level-ev98.npy")
VP = np.full((2048, 2048), -np.inf); cc = np.where(np.isfinite(cov), cov, -np.inf)
for dr in (0, 1):
    for dc in (0, 1):
        VP[dr:dr+2047, dc:dc+2047] = np.maximum(VP[dr:dr+2047, dc:dc+2047], cc)
WPL = np.where(np.isfinite(VP), VP, 0.75)
sites = [tuple(int(v) for v in s.split(",")) for s in sys.argv[2:]]
fig, axs = plt.subplots(len(sites), 2, figsize=(12, 6 * len(sites)))
axs = np.atleast_2d(axs)
for row, (x, z, R) in zip(axs, sites):
    c0, c1 = int((x-R)/6), int((x+R)/6); r0, r1 = int(2047-(z+R)/6), int(2047-(z-R)/6)
    for ax, (name, p) in zip(row, (("EV101", "E:/DayZ-Baltic-Build/v31-ev101-sea-bed-20261012/terrain-ev101.npz"), ("EV102", "E:/DayZ-Baltic-Build/v31-ev102-sills-cones-20261012/terrain-ev102.npz"))):
        z_ = np.load(p); H = z_["heights"][r0:r1, c0:c1].astype(float); road = (z_["reserve"] | z_["platform"])[r0:r1, c0:c1]
        w = WPL[r0:r1, c0:c1]; pond = np.isfinite(cov[r0:r1, c0:c1])
        img = np.zeros(H.shape + (3,)); img[:] = [0.45, 0.6, 0.35]
        img[road] = [0.85, 0.8, 0.65]
        img[(H < w) & (w <= 0.75)] = [0.65, 0.7, 0.78]
        img[(H < w) & (w > 0.75)] = [0.2, 0.4, 0.9]
        ext = [6*c0, 6*c1, 6*(2047-r1+1), 6*(2047-r0+1)]
        ax.imshow(img, extent=ext, interpolation="nearest")
        X, Y = np.meshgrid(6*np.arange(c0, c1), 6*(2047-np.arange(r0, r1)))
        f = H - w
        for line in contourpy.contour_generator(X, Y, f).lines(0.0):
            ax.plot(line[:, 0], line[:, 1], "k-", lw=0.8)
        cs = ax.contour(X, Y, H, levels=np.arange(-2, 12, 1.0), colors="w", linewidths=0.3)
        ax.set_title(f"{name} ({x},{z}) waterline black, 1 m contours white"); ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
fig.savefig(sys.argv[1], dpi=60, bbox_inches="tight")

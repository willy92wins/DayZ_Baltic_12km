"""Side-by-side waterlines: A = terrain + cell planes A, B = terrain + cell planes B (TRI model on the native diagonal).
Usage: render_ab_v31.py <out.png> <terrainA.npz> <planesA(.npy|footprint.npz)> <terrainB.npz> <planesB> x,z,R [x,z,R ...]"""
import sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import contourpy

K = 4


def planes(p):
    if p.endswith(".npz"):
        return np.load(p)["plane"].astype(float)
    return np.load(p).astype(float)


def tri_field(H, cp, r0, r1, c0, c1):
    """K x K samples per cell on the native NW-SE triangles, value = terrain - cell plane (sea 0.75 where no plane)."""
    h = H[r0:r1 + 1, c0:c1 + 1]; p = np.where(np.isfinite(cp[r0:r1, c0:c1]), cp[r0:r1, c0:c1], 0.75)
    nr, nc = r1 - r0, c1 - c0
    out = np.zeros((nr * K, nc * K))
    for i in range(K):
        for j in range(K):
            fr, fc = (i + 0.5) / K, (j + 0.5) / K
            nw, ne, sw, se = h[:-1, :-1], h[:-1, 1:], h[1:, :-1], h[1:, 1:]
            a = nw + fc * (ne - nw) + fr * (se - ne)          # triangle (NW, NE, SE): fc >= fr
            b = nw + fr * (sw - nw) + fc * (se - sw)          # triangle (NW, SE, SW): fc < fr
            out[i::K, j::K] = np.where(fc >= fr, a, b) - p
    return out, np.repeat(np.repeat(np.isfinite(cp[r0:r1, c0:c1]), K, 0), K, 1)


def main():
    out, ta, pa, tb, pb = sys.argv[1:6]
    sites = [tuple(float(v) for v in s.split(",")) for s in sys.argv[6:]]
    A = (np.load(ta)["heights"].astype(float), planes(pa)); B = (np.load(tb)["heights"].astype(float), planes(pb))
    fig, axs = plt.subplots(len(sites), 2, figsize=(14, 7 * len(sites)))
    axs = np.atleast_2d(axs)
    for row, (x, z, R) in zip(axs, sites):
        c0, c1 = int((x - R) / 6), int((x + R) / 6); r0, r1 = int((12282 - z - R) / 6), int((12282 - z + R) / 6)
        for ax, (name, (H, cp)) in zip(row, (("A", A), ("B", B))):
            f, pond = tri_field(H, cp, r0, r1, c0, c1)
            img = np.zeros(f.shape + (3,)); img[:] = [0.45, 0.62, 0.35]
            wet = f < 0
            img[wet & pond] = [0.2, 0.4, 0.9]; img[wet & ~pond] = [0.65, 0.7, 0.78]
            ext = [6 * c0, 6 * c1, 12282 - 6 * r1, 12282 - 6 * r0]
            ax.imshow(img, extent=ext, interpolation="nearest")
            X = 6 * c0 + (np.arange(f.shape[1]) + 0.5) * 6 / K; Y = 12282 - 6 * r0 - (np.arange(f.shape[0]) + 0.5) * 6 / K
            for line in contourpy.contour_generator(X, Y, f).lines(0.0):
                ax.plot(line[:, 0], line[:, 1], "k-", lw=0.7)
            ax.set_title(f"{name} ({x:.0f},{z:.0f})"); ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    fig.savefig(out, dpi=60, bbox_inches="tight")


if __name__ == "__main__":
    main()

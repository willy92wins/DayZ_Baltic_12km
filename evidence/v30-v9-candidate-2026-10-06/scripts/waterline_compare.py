"""Waterline of v8 and v9 side by side in map windows: the zero contour of terrain minus the level of the nearest
inland water vertex (what the engine shows where the terrain crosses the water plane), over a hillshade, inland
water only (classes 2, 3, 5, 6, 7). Usage: waterline_compare.py V8.npz V9.npz OUT.png"""
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LightSource  # noqa: E402
from scipy import ndimage  # noqa: E402

WINDOWS = [('Marcas de Guillermo en RIVER_80 (borde este)', (11850, 1450, 12282, 1990)),
           ('Zona RIVER_80 (sureste)', (11300, 1100, 12282, 2000)),
           ('Arroyos del centro', (6400, 6300, 7900, 7700))]


def field(t, x0, z0, x1, z1):
    c0, c1 = int(x0 // 6), int(np.ceil(x1 / 6)) + 1
    r0, r1 = int((12282 - z1) // 6), int(np.ceil((12282 - z0) / 6)) + 1
    h = t['heights'][r0:r1, c0:c1].astype(float)
    cls = t['cls'][r0:r1, c0:c1]
    lev = t['level'][r0:r1, c0:c1].astype(float)
    wet = np.isin(cls, (2, 3, 5, 6, 7)) & np.isfinite(lev)
    _, idx = ndimage.distance_transform_edt(~wet, return_indices=True)
    near = lev[idx[0], idx[1]]
    dist = ndimage.distance_transform_edt(~wet) * 6.0
    f = np.where(dist <= 18.0, h - near, np.nan)
    xs = np.arange(c0, c1) * 6.0
    zs = 12282.0 - np.arange(r0, r1) * 6.0
    return xs, zs, h, f


def main():
    t8, t9 = np.load(sys.argv[1]), np.load(sys.argv[2])
    fig, axes = plt.subplots(len(WINDOWS), 2, figsize=(14, 7 * len(WINDOWS)))
    ls = LightSource(azdeg=315, altdeg=45)
    for row, (title, (x0, z0, x1, z1)) in enumerate(WINDOWS):
        for col, (name, t) in enumerate((('v8', t8), ('v9', t9))):
            ax = axes[row, col]
            xs, zs, h, f = field(t, x0, z0, x1, z1)
            ax.imshow(ls.hillshade(h, vert_exag=4, dx=6, dy=6), cmap='gray', extent=(xs[0], xs[-1], zs[-1], zs[0]),
                      alpha=0.8)
            ax.contourf(xs, zs, np.where(np.isfinite(f) & (f < 0), 1.0, np.nan), levels=[0.5, 1.5], colors=['#5aa0d8'],
                        alpha=0.55)
            ax.contour(xs, zs, np.nan_to_num(f, nan=1.0), levels=[0.0], colors='#0b3d91', linewidths=0.9)
            ax.set_xlim(x0, x1)
            ax.set_ylim(z0, z1)
            ax.set_aspect('equal')
            ax.set_title(f'{name}: {title}', fontsize=10)
            ax.tick_params(labelsize=7)
    fig.suptitle('Línea de agua (terreno = nivel del agua más cercana), v8 frente a v9', fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.975))
    fig.savefig(sys.argv[3], dpi=110)


if __name__ == '__main__':
    main()

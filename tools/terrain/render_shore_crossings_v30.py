"""Offline figure: visible waterline before (red) and after (blue) the shore fit against the designed outline (black).

Per window: the native terrain (tri_sample) on a 0.5 m grid minus the visible water of each point (plane of its cell,
else the channel piece surface for the pilot reaches, else none), zero contour = visible shoreline; the designed outline
is drawn from the vector sources the V30 builder used (water_v3, streams >= 2.5 km, contour-v2 lakes).
Usage: render_shore_crossings_v30.py --before <npz> --after <npz> --out <png> --windows x,z,size;x,z,size;...
                                     [--sea-cut 0.51] [--channels <fit dir>]
"""
from pathlib import Path
import argparse
import json
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from shapely.geometry import box, shape  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'terrain'))
sys.path.insert(0, str(ROOT / 'tools' / 'water'))
from v30_common import R, cell_planes, tri_sample  # noqa: E402


def outline():
    W = Path(R)
    geoms = [shape(f['geometry']) for f in json.loads((W / 'tests/water_v3/water_v3.geojson').read_text(encoding='utf-8'))['features']]
    geoms += [shape(f['geometry']) for f in json.loads((W / 'tests/water_v3/streams_candidates.geojson').read_text(encoding='utf-8'))['features']
              if f['properties']['tier_m'] >= 2500]
    geoms += [shape(f['geometry']) for f in json.loads((W / 'evidence/regional-foundation-v1/water-surfaces-contour-v2.geojson').read_text(encoding='utf-8'))['features']
              if f['properties']['body'].startswith('lake')]
    return geoms


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before', type=Path, required=True)
    ap.add_argument('--after', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--windows', required=True)
    ap.add_argument('--sea-cut', type=float, default=0.51)
    ap.add_argument('--channels', type=Path)
    a = ap.parse_args()
    b, t = np.load(a.before), np.load(a.after)
    cls, level = t['cls'], t['level'].astype(float)
    planes = cell_planes(cls, level, sea_cut=a.sea_cut)
    pieces = []
    if a.channels:
        import engine_water_model as ewm
        axes = json.loads((a.channels / 'axes.json').read_text(encoding='utf-8'))
        pieces = [ewm.Piece(p['type'], p['matrix']) for reach in axes.values() for p in reach['pieces']]
        for reach in axes.values():
            for r, c in reach['removed_cells']:
                planes[r, c] = np.nan
    geoms = outline()
    wins = [tuple(float(v) for v in w.split(',')) for w in a.windows.split(';')]
    n = len(wins)
    cols = min(n, 3)
    rows = (n + cols - 1) // cols
    fig, axs = plt.subplots(rows, cols, figsize=(6 * cols, 6 * rows), squeeze=False)
    for k, (x0, z0, size) in enumerate(wins):
        ax = axs[k // cols][k % cols]
        xs = np.arange(x0, x0 + size, 0.5)
        zs = np.arange(z0, z0 + size, 0.5)
        X, Z = np.meshgrid(xs, zs)
        ci = np.clip(((12282 - Z) // 6).astype(int), 0, 2046)
        cj = np.clip((X // 6).astype(int), 0, 2046)
        wl = planes[ci, cj]
        if pieces:
            sel = ~np.isfinite(wl)
            for idx in np.flatnonzero(sel.ravel()):
                xv, zv = X.ravel()[idx], Z.ravel()[idx]
                best = None
                for p in pieces:
                    v = p.visual(xv, zv)
                    if v is not None and (best is None or v[0] > best):
                        best = v[0]
                if best is not None:
                    wl.ravel()[idx] = best
        for terr, colour in ((b['heights'].astype(float), 'red'), (t['heights'].astype(float), 'blue')):
            d = np.where(np.isfinite(wl), tri_sample(terr, X, Z) - wl, np.nan)
            ax.contour(X, Z, d, levels=[0.0], colors=colour, linewidths=1.2)
        win = box(x0, z0, x0 + size, z0 + size)
        for g in geoms:
            if not g.intersects(win):
                continue
            g = g.intersection(win)
            for part in getattr(g, 'geoms', [g]):
                if part.geom_type != 'Polygon':
                    continue
                for ring in [part.exterior, *part.interiors]:
                    xy = np.asarray(ring.coords)
                    ax.plot(xy[:, 0], xy[:, 1], color='black', linewidth=0.8)
        for gx in np.arange(np.ceil(x0 / 6) * 6, x0 + size, 6):
            ax.axvline(gx, color='0.88', linewidth=0.3, zorder=0)
        for gz in np.arange(np.ceil((z0 - 12282) / 6) * 6 + 12282, z0 + size, 6):
            ax.axhline(gz, color='0.88', linewidth=0.3, zorder=0)
        ax.set_xlim(x0, x0 + size)
        ax.set_ylim(z0, z0 + size)
        ax.set_aspect('equal')
        ax.set_title(f'x {x0:.0f}  z {z0:.0f}  ({size:.0f} m)', fontsize=9)
    for k in range(n, rows * cols):
        axs[k // cols][k % cols].axis('off')
    fig.suptitle('Waterline: red before, blue after, black designed outline (grid 6 m)', fontsize=11)
    fig.tight_layout()
    fig.savefig(a.out, dpi=110)
    print(a.out)


if __name__ == '__main__':
    main()

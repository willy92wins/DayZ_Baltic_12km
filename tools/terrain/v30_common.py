"""Shared helpers for terrain V30: native triangle sampling, vertex rasterisation and the road network graph.

Vertex grid: col c, row r -> x = 6c, z = 12282 - 6r (row 0 north). Each 6 m cell is split along its NW-SE diagonal,
as Terrain Builder's native grid (contract recorded in HANDOFF-history.md, "Contrato nativo LOCAL").
"""
import json
import os

import numpy as np
from affine import Affine
from rasterio.features import rasterize
from shapely.geometry import shape

R = r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev"
N = 2048
VERTEX = Affine(6, 0, -3, 0, -6, 12285)  # one pixel per vertex, game coordinates


def tri_sample(h, xs, zs):
    """Height on the native triangulated surface (NW-SE diagonal) at game coordinates."""
    c = np.clip(np.asarray(xs, dtype=float) / 6.0, 0, N - 1.000001)
    r = np.clip((12282 - np.asarray(zs, dtype=float)) / 6.0, 0, N - 1.000001)
    c0, r0 = np.floor(c).astype(int), np.floor(r).astype(int)
    fc, fr = c - c0, r - r0
    nw, ne = h[r0, c0], h[r0, c0 + 1]
    sw, se = h[r0 + 1, c0], h[r0 + 1, c0 + 1]
    upper = nw + fc * (ne - nw) + fr * (se - ne)
    lower = nw + fr * (sw - nw) + fc * (se - sw)
    return np.where(fc >= fr, upper, lower)


def raster_vertices(geoms, all_touched=False, values=None, dtype="uint8"):
    pairs = [(g, 1 if values is None else v) for g, v in zip(geoms, values if values is not None else [None] * len(geoms)) if not g.is_empty]
    if not pairs:
        return np.zeros((N, N), dtype=dtype)
    return rasterize(pairs, out_shape=(N, N), transform=VERTEX, dtype=dtype, all_touched=all_touched)


def grid_xz():
    c, r = np.meshgrid(np.arange(N), np.arange(N))
    return c * 6.0, 12282 - r * 6.0


def road_network():
    """V29 graded road network (union of shortest routes between 11 anchors): list of (LineString, properties)."""
    fc = json.load(open(os.path.join(R, "evidence", "regional-foundation-v1", "road-network-game.json"), encoding="utf-8"))
    return [(shape(f["geometry"]), f["properties"]) for f in fc["features"]]


def road_graph(step=3.0):
    """Densified graph of the road network: points (n,2), edges (m,2) with lengths; endpoints merged by OSM node id."""
    pts, edges, key_index = [], [], {}

    def node(key, xy):
        if key is not None and key in key_index:
            return key_index[key]
        pts.append(xy)
        idx = len(pts) - 1
        if key is not None:
            key_index[key] = idx
        return idx

    for line, prop in road_network():
        coords = np.asarray(line.coords)[:, :2]
        if len(coords) < 2 or line.length <= 0:
            continue
        n = max(1, int(np.ceil(line.length / step)))
        d = np.linspace(0, line.length, n + 1)
        xy = np.array([line.interpolate(v).coords[0][:2] for v in d])
        a = node(("osm", prop.get("node_a")) if prop.get("node_a") is not None else None, tuple(xy[0]))
        prev = a
        for k in range(1, n):
            cur = node(None, tuple(xy[k]))
            edges.append((prev, cur))
            prev = cur
        b = node(("osm", prop.get("node_b")) if prop.get("node_b") is not None else None, tuple(xy[-1]))
        edges.append((prev, b))
    pts = np.asarray(pts, dtype=float)
    edges = np.asarray(edges, dtype=int)
    lengths = np.hypot(*(pts[edges[:, 0]] - pts[edges[:, 1]]).T)
    keep = lengths > 1e-6
    return pts, edges[keep], lengths[keep]


POND_CLASSES = (2, 3, 5, 6, 7)


def cell_planes(cls, level, band=0.025, sea_cut=0.80):
    """Plane of every 6 m cell covered by a pond piece: the band of the mean level of its water corners (lakes,
    navigable, rivers, streams, ponds above the sea). NaN where the cell has no such corner. Pieces, builder and
    surface all use this rule. cell (i, j) lies between vertex rows i, i+1 and columns j, j+1."""
    # Production pieces and surfaces use float64. Without normalization,
    # float32(0.8) compares differently against 0.8 after promotion: consumers
    # omitted 467 existing pond cells merely by retaining the stored dtype.
    level = np.asarray(level, dtype=np.float64)
    wet = np.isin(cls, POND_CLASSES) & (np.nan_to_num(level, nan=-1.0) > sea_cut)
    lv = np.where(wet, level, 0.0)
    total = np.zeros((N - 1, N - 1))
    count = np.zeros((N - 1, N - 1))
    for dr in (0, 1):
        for dc in (0, 1):
            total += lv[dr:dr + N - 1, dc:dc + N - 1]
            count += wet[dr:dr + N - 1, dc:dc + N - 1]
    return np.where(count > 0, np.rint(total / np.maximum(count, 1) / band) * band, np.nan)


def vertex_plane_bounds(plane):
    """Lowest and highest plane among the up to four cells around each vertex (NaN where none is covered)."""
    p = np.pad(plane, 1, constant_values=np.nan)
    stack = np.stack([p[0:N, 0:N], p[0:N, 1:N + 1], p[1:N + 1, 0:N], p[1:N + 1, 1:N + 1]])
    with np.errstate(all="ignore"):
        return np.nanmin(stack, axis=0), np.nanmax(stack, axis=0)

"""Shared loaders and geometry helpers for the water V3 design (game coordinates: x = 6*col, z = 12282 - 6*row)."""
import json
import os

import numpy as np
import shapefile
from shapely import make_valid
from shapely.affinity import translate
from shapely.geometry import LineString, Polygon, shape
from shapely.ops import linemerge, unary_union

R = r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev"
EV = os.path.join(R, "evidence", "regional-foundation-v1")


def read_shp(name, types=None):
    sf = shapefile.Reader(os.path.join(R, "source", "vectors", name))
    out = []
    for sr in sf.iterShapeRecords():
        if not sr.shape.points:
            continue
        rec = {"osm_id": sr.record[0], "name": sr.record[1], "type": sr.record[2]}
        if types is not None and rec["type"] not in types:
            continue
        out.append((make_valid(translate(shape(sr.shape.__geo_interface__), xoff=-200000)), rec))
    return out


def load_relief():
    z = np.load(os.path.join(R, "tests", "relief_v30", "relief_v30_mix.npz"))
    return z["new"].astype("float64")


def sample_vertex(grid, xs, zs):
    """Bilinear sample of a vertex grid at game coordinates."""
    c = np.clip(np.asarray(xs) / 6.0, 0, grid.shape[1] - 1.001)
    r = np.clip((12282 - np.asarray(zs)) / 6.0, 0, grid.shape[0] - 1.001)
    c0, r0 = np.floor(c).astype(int), np.floor(r).astype(int)
    fc, fr = c - c0, r - r0
    return (grid[r0, c0] * (1 - fc) * (1 - fr) + grid[r0, c0 + 1] * fc * (1 - fr)
            + grid[r0 + 1, c0] * (1 - fc) * fr + grid[r0 + 1, c0 + 1] * fc * fr)


def resample(line, step):
    n = max(2, int(np.ceil(line.length / step)) + 1)
    d = np.linspace(0, line.length, n)
    pts = np.array([line.interpolate(v).coords[0] for v in d])
    return d, pts


def smooth_course(line, step, sigma_m):
    """A course smoothed along its arc (Gaussian of sigma_m metres), its two ends held in place over 2 sigma so
    junctions and mouths stay where they are. sigma_m <= 0 returns the line unchanged. The OSM courses turn more than
    20 degrees every ~23 m on average; a ribbon on such a line draws corners and blobs at 6 m
    (evidence/v30-v8-candidate-2026-10-06/general-review)."""
    if sigma_m <= 0 or line.length < 2 * step:
        return line
    from scipy.ndimage import gaussian_filter1d
    _, pts = resample(line, step)
    k = sigma_m / step
    sm = gaussian_filter1d(pts, k, axis=0, mode="nearest")
    i = np.arange(len(pts))
    w = np.clip(np.minimum(i, len(pts) - 1 - i) / (2 * k), 0, 1)[:, None]
    return LineString(pts + (sm - pts) * w)


def normals(pts, smooth=5):
    from scipy.ndimage import uniform_filter1d
    t = np.gradient(pts, axis=0)
    if smooth > 1 and len(t) > 2:
        # uniform_filter1d keeps the length; np.convolve(mode="same") grows short arrays to the kernel size
        t = uniform_filter1d(t, size=min(smooth, len(t)), axis=0, mode="nearest")
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
    return np.column_stack([-t[:, 1], t[:, 0]]), t


def smooth_noise(n, sigma, rng):
    from scipy.ndimage import gaussian_filter1d
    v = gaussian_filter1d(rng.standard_normal(n), sigma)
    return v / max(np.abs(v).max(), 1e-9)


def ribbon(pts, left, right):
    """Polygon between offset curves; left/right are per-sample offsets in metres."""
    nrm, _ = normals(pts)
    lp = pts + nrm * left[:, None]
    rp = pts - nrm * right[:, None]
    poly = Polygon(np.vstack([lp, rp[::-1]]))
    return make_valid(poly.buffer(0))


def merge_lines(geoms):
    u = unary_union(geoms)
    if u.geom_type == "LineString":
        return [u]
    m = linemerge(u)
    return list(m.geoms) if hasattr(m, "geoms") else [m]


def save_geojson(path, features):
    from shapely.geometry import mapping
    fc = {"type": "FeatureCollection", "coordinate_system": "game X/Z metres (TB minus 200000)",
          "features": [{"type": "Feature", "properties": p, "geometry": mapping(g)} for g, p in features]}
    with open(path, "wb") as f:
        f.write(json.dumps(fc, ensure_ascii=False).encode("utf-8"))

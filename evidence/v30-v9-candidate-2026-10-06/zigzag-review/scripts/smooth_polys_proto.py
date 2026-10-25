"""Prototype: smooth inland water polygons along their rings (Gaussian of sigma m on 1 m resampled rings, each point
moving at most max_shift m), keep the area (offset by (A0 - A1) / perimeter), keep rings that would collapse as they
are. Reports the share of outline points turning more than 45 degrees on 6 m chords before and after, per kind, and
the area change and shift percentiles. Usage: smooth_polys_proto.py DESIGN_DIR SIGMA MAX_SHIFT OUT.json"""
import json
import sys

import numpy as np
import shapely
from scipy.ndimage import gaussian_filter1d
from shapely.geometry import LinearRing, Polygon, shape
from shapely.validation import make_valid

R = 'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/'


def smooth_ring(coords, sigma, max_shift):
    ring = LinearRing(coords)
    L = ring.length
    n = max(int(L // 1.0), 8)
    d = np.linspace(0, L, n, endpoint=False)
    p = np.array([ring.interpolate(v).coords[0] for v in d])
    s = min(sigma, L / 8.0)                       # small rings: at most an eighth of their length
    q = np.column_stack([gaussian_filter1d(p[:, 0], s, mode='wrap'), gaussian_filter1d(p[:, 1], s, mode='wrap')])
    dv = q - p
    m = np.linalg.norm(dv, axis=1)
    over = m > max_shift
    q[over] = p[over] + dv[over] / m[over, None] * max_shift
    return q, np.minimum(m, max_shift)


def smooth_polygon(poly, sigma, max_shift):
    ext, shift = smooth_ring(poly.exterior.coords, sigma, max_shift)
    holes = []
    for r in poly.interiors:
        if Polygon(r).area < 200:                  # tiny islands stay
            holes.append(np.asarray(r.coords))
            continue
        h, _ = smooth_ring(r.coords, sigma, max_shift)
        holes.append(h)
    out = make_valid(Polygon(ext, holes))
    parts = [g for g in getattr(out, 'geoms', [out]) if g.geom_type == 'Polygon' and g.area > 1.0]
    if not parts:
        return poly, shift
    out = parts[0] if len(parts) == 1 else shapely.MultiPolygon(parts)
    # keep the area: one offset of (A0 - A1) / perimeter
    da = poly.area - out.area
    if abs(da) > 1e-6 and out.length > 0:
        out2 = make_valid(out.buffer(da / out.length, join_style=1))
        if not out2.is_empty:
            out = out2
    return out, shift


def turning(geom):
    vals = []
    for poly in getattr(geom, 'geoms', [geom]):
        if poly.geom_type != 'Polygon':
            continue
        for ring in [poly.exterior] + list(poly.interiors):
            n = int(ring.length // 2.0)
            if n < 8:
                continue
            p = np.array([ring.interpolate(v).coords[0] for v in np.arange(n) * 2.0])
            a = p - np.roll(p, 3, axis=0)
            b = np.roll(p, -3, axis=0) - p
            c = (a * b).sum(1) / np.maximum(np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1), 1e-9)
            vals.append(np.degrees(np.arccos(np.clip(c, -1, 1))))
    return np.concatenate(vals) if vals else np.array([])


def main():
    design, sigma, max_shift, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    feats = json.load(open(design + '/water_v3.geojson', encoding='utf-8'))['features']
    contour = json.load(open(R + 'evidence/regional-foundation-v1/water-surfaces-contour-v2.geojson', encoding='utf-8'))['features']
    groups = {'lake': [shape(f['geometry']) for f in contour if f['properties']['body'].startswith('lake')],
              'pond': [shape(f['geometry']) for f in feats if f['properties']['class'] == 'pond'],
              'river': [shape(f['geometry']) for f in feats if f['properties']['class'] == 'river']}
    rep = {}
    for k, geoms in groups.items():
        tb, ta, shifts, dA = [], [], [], []
        for g in geoms:
            polys = [p for p in getattr(g, 'geoms', [g]) if p.geom_type == 'Polygon']
            for p in polys:
                sp, sh = smooth_polygon(p, sigma, max_shift)
                tb.append(turning(p))
                ta.append(turning(sp))
                shifts.append(sh)
                dA.append((sp.area - p.area) / max(p.area, 1))
        tb, ta, shifts, dA = np.concatenate(tb), np.concatenate(ta), np.concatenate(shifts), np.array(dA)
        rep[k] = {'polygons': len(dA), 'turn_gt45_before': round(float((tb > 45).mean()), 3),
                  'turn_gt45_after': round(float((ta > 45).mean()), 3),
                  'turn_gt30_before': round(float((tb > 30).mean()), 3), 'turn_gt30_after': round(float((ta > 30).mean()), 3),
                  'shift_p50_p95': [round(float(np.percentile(shifts, q)), 2) for q in (50, 95)],
                  'area_change_p5_p95_pct': [round(float(np.percentile(dA, q)) * 100, 2) for q in (5, 95)]}
        print(k, rep[k])
    json.dump(rep, open(out, 'w'), indent=1)


if __name__ == '__main__':
    main()

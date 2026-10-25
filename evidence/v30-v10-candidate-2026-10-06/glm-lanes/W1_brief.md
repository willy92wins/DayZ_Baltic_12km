IMPORTANT PROCESS NOTE: write the complete files FIRST, in one pass, then stop. Keep internal deliberation focused.
The receiver re-runs every changed tool with its DEFAULTS and compares sha256 against archived outputs: with the
defaults, terrain/water/image outputs must be byte-identical to today's. Change nothing that the task does not ask for.
Code and comments in English; keep the style of the surrounding code (comment density, naming, idiom).
Output: one fenced block per changed or new file, each preceded by the line `FILE: <repo-relative path>`, whole file.
Coordinates: game metres, x east, z north; the vertex grid is N = 2048 vertices every 6 m, row r at z = 12282 - 6r,
column c at x = 6c (tools/terrain/v30_common.py).

# Task W1: new tool tools/water/smooth_water_outlines_v30.py
Smooth the inland water outlines of a water design along their rings, as decided by the owner on 06-10 (sigma 12 m,
each point moving at most 4 m, area kept): the contour-v2 lakes copy the 6 m staircase of the V29 raster and the OSM
ponds and river bodies are coarse polygons, so the visible shores keep their corners. A prototype (below,
smooth_polys_proto.py) measured on the design: points turning more than 45 degrees on 6 m chords, lakes 20.4 -> 8.6 %,
ponds 25.8 -> 16.9 %, rivers 9.0 -> 4.3 %, shift p95 4 m. Make it a production tool:
- Usage: smooth_water_outlines_v30.py --design IN_DIR --out OUT_DIR [--contour PATH] [--sigma 12] [--max-shift 4]
  [--narva-radius 600] [--contact-m 2.0]; and smooth_water_outlines_v30.py --selftest. OUT_DIR must not exist.
- Inputs: IN_DIR/water_v3.geojson (features with properties.class: navigable, delta_*, river, pond), the contour file
  (default R + evidence/regional-foundation-v1/water-surfaces-contour-v2.geojson, R from tools/water/water_common.py;
  features with properties.body 'lake_NNN' or 'river...' and level_m), IN_DIR/streams_candidates.geojson.
- Smoothed: water_v3 features of class 'river' and 'pond'; contour features whose body starts with 'lake'.
  Unchanged: navigable, delta_*, the contour 'river' bands, streams, and every feature whose geometry intersects the
  Narva disc (centre (2417.1428225906, 6889.8850822322), radius --narva-radius): Narva keeps the V29 rules.
- Ring smoothing as in the prototype (1 m resample, Gaussian of sigma m with wrap, sigma at most a ring's length / 8,
  shift capped at --max-shift), plus CONTACTS: a ring point within --contact-m of any OTHER inland body (all
  water_v3 features, the contour lakes and river bands, the streams; not the feature itself) does not move, and the
  cap grows linearly back to --max-shift over the next 10 m along the ring, so rivers keep meeting lakes and ponds.
  Islands (holes) under 200 m2 stay as they are.
- Validity: make_valid, keep polygonal parts over 1 m2 (a MultiPolygon stays multi). If the result is empty, or its
  area differs from the original by more than 15 %, retry with half the max shift, then keep the original; count
  these fallbacks.
- Area: after smoothing, restore the area with buffer((A0 - A1) / perimeter, join_style=round), twice.
- Outputs, in OUT_DIR: water_v3.geojson (the same features in the same ORDER with the same properties; only the
  geometries of the smoothed ones change; other tools index ponds by position), written with
  water_common.save_geojson; contour_lakes.geojson (the input contour file's JSON with only the smoothed lake
  geometries replaced, every other key and feature as it was); copies (byte copies) of streams_candidates.geojson,
  profiles.npz, navigable.geojson, navigable_report.json, navigable_samples.npz and water_v3_summary.json;
  smoothing_report.json: params, input sha256, and per kind (lake, pond, river): features, smoothed, unchanged_narva,
  fallbacks, shift p50/p95, area change p5/p95 (%), share of ring points turning more than 45 and 30 degrees on 6 m
  chords before and after (the prototype's turning()).
- --selftest: synthetic polygons on a temporary folder: a 6 m staircase blob (turning share must drop, area within
  2 %), two polygons that touch (they must still touch: distance 0 after), one inside the Narva disc (unchanged
  byte for byte), the order of features kept; print SELFTEST PASS.

### scratchpad prototype smooth_polys_proto.py (full file, 102 lines)
```python
   1| """Prototype: smooth inland water polygons along their rings (Gaussian of sigma m on 1 m resampled rings, each point
   2| moving at most max_shift m), keep the area (offset by (A0 - A1) / perimeter), keep rings that would collapse as they
   3| are. Reports the share of outline points turning more than 45 degrees on 6 m chords before and after, per kind, and
   4| the area change and shift percentiles. Usage: smooth_polys_proto.py DESIGN_DIR SIGMA MAX_SHIFT OUT.json"""
   5| import json
   6| import sys
   7| 
   8| import numpy as np
   9| import shapely
  10| from scipy.ndimage import gaussian_filter1d
  11| from shapely.geometry import LinearRing, Polygon, shape
  12| from shapely.validation import make_valid
  13| 
  14| R = 'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/'
  15| 
  16| 
  17| def smooth_ring(coords, sigma, max_shift):
  18|     ring = LinearRing(coords)
  19|     L = ring.length
  20|     n = max(int(L // 1.0), 8)
  21|     d = np.linspace(0, L, n, endpoint=False)
  22|     p = np.array([ring.interpolate(v).coords[0] for v in d])
  23|     s = min(sigma, L / 8.0)                       # small rings: at most an eighth of their length
  24|     q = np.column_stack([gaussian_filter1d(p[:, 0], s, mode='wrap'), gaussian_filter1d(p[:, 1], s, mode='wrap')])
  25|     dv = q - p
  26|     m = np.linalg.norm(dv, axis=1)
  27|     over = m > max_shift
  28|     q[over] = p[over] + dv[over] / m[over, None] * max_shift
  29|     return q, np.minimum(m, max_shift)
  30| 
  31| 
  32| def smooth_polygon(poly, sigma, max_shift):
  33|     ext, shift = smooth_ring(poly.exterior.coords, sigma, max_shift)
  34|     holes = []
  35|     for r in poly.interiors:
  36|         if Polygon(r).area < 200:                  # tiny islands stay
  37|             holes.append(np.asarray(r.coords))
  38|             continue
  39|         h, _ = smooth_ring(r.coords, sigma, max_shift)
  40|         holes.append(h)
  41|     out = make_valid(Polygon(ext, holes))
  42|     parts = [g for g in getattr(out, 'geoms', [out]) if g.geom_type == 'Polygon' and g.area > 1.0]
  43|     if not parts:
  44|         return poly, shift
  45|     out = parts[0] if len(parts) == 1 else shapely.MultiPolygon(parts)
  46|     # keep the area: one offset of (A0 - A1) / perimeter
  47|     da = poly.area - out.area
  48|     if abs(da) > 1e-6 and out.length > 0:
  49|         out2 = make_valid(out.buffer(da / out.length, join_style=1))
  50|         if not out2.is_empty:
  51|             out = out2
  52|     return out, shift
  53| 
  54| 
  55| def turning(geom):
  56|     vals = []
  57|     for poly in getattr(geom, 'geoms', [geom]):
  58|         if poly.geom_type != 'Polygon':
  59|             continue
  60|         for ring in [poly.exterior] + list(poly.interiors):
  61|             n = int(ring.length // 2.0)
  62|             if n < 8:
  63|                 continue
  64|             p = np.array([ring.interpolate(v).coords[0] for v in np.arange(n) * 2.0])
  65|             a = p - np.roll(p, 3, axis=0)
  66|             b = np.roll(p, -3, axis=0) - p
  67|             c = (a * b).sum(1) / np.maximum(np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1), 1e-9)
  68|             vals.append(np.degrees(np.arccos(np.clip(c, -1, 1))))
  69|     return np.concatenate(vals) if vals else np.array([])
  70| 
  71| 
  72| def main():
  73|     design, sigma, max_shift, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
  74|     feats = json.load(open(design + '/water_v3.geojson', encoding='utf-8'))['features']
  75|     contour = json.load(open(R + 'evidence/regional-foundation-v1/water-surfaces-contour-v2.geojson', encoding='utf-8'))['features']
  76|     groups = {'lake': [shape(f['geometry']) for f in contour if f['properties']['body'].startswith('lake')],
  77|               'pond': [shape(f['geometry']) for f in feats if f['properties']['class'] == 'pond'],
  78|               'river': [shape(f['geometry']) for f in feats if f['properties']['class'] == 'river']}
  79|     rep = {}
  80|     for k, geoms in groups.items():
  81|         tb, ta, shifts, dA = [], [], [], []
  82|         for g in geoms:
  83|             polys = [p for p in getattr(g, 'geoms', [g]) if p.geom_type == 'Polygon']
  84|             for p in polys:
  85|                 sp, sh = smooth_polygon(p, sigma, max_shift)
  86|                 tb.append(turning(p))
  87|                 ta.append(turning(sp))
  88|                 shifts.append(sh)
  89|                 dA.append((sp.area - p.area) / max(p.area, 1))
  90|         tb, ta, shifts, dA = np.concatenate(tb), np.concatenate(ta), np.concatenate(shifts), np.array(dA)
  91|         rep[k] = {'polygons': len(dA), 'turn_gt45_before': round(float((tb > 45).mean()), 3),
  92|                   'turn_gt45_after': round(float((ta > 45).mean()), 3),
  93|                   'turn_gt30_before': round(float((tb > 30).mean()), 3), 'turn_gt30_after': round(float((ta > 30).mean()), 3),
  94|                   'shift_p50_p95': [round(float(np.percentile(shifts, q)), 2) for q in (50, 95)],
  95|                   'area_change_p5_p95_pct': [round(float(np.percentile(dA, q)) * 100, 2) for q in (5, 95)]}
  96|         print(k, rep[k])
  97|     json.dump(rep, open(out, 'w'), indent=1)
  98| 
  99| 
 100| if __name__ == '__main__':
 101|     main()
 102| 
```

### tools/water/water_common.py (full file, 106 lines)
```python
   1| """Shared loaders and geometry helpers for the water V3 design (game coordinates: x = 6*col, z = 12282 - 6*row)."""
   2| import json
   3| import os
   4| 
   5| import numpy as np
   6| import shapefile
   7| from shapely import make_valid
   8| from shapely.affinity import translate
   9| from shapely.geometry import LineString, Polygon, shape
  10| from shapely.ops import linemerge, unary_union
  11| 
  12| R = r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev"
  13| EV = os.path.join(R, "evidence", "regional-foundation-v1")
  14| 
  15| 
  16| def read_shp(name, types=None):
  17|     sf = shapefile.Reader(os.path.join(R, "source", "vectors", name))
  18|     out = []
  19|     for sr in sf.iterShapeRecords():
  20|         if not sr.shape.points:
  21|             continue
  22|         rec = {"osm_id": sr.record[0], "name": sr.record[1], "type": sr.record[2]}
  23|         if types is not None and rec["type"] not in types:
  24|             continue
  25|         out.append((make_valid(translate(shape(sr.shape.__geo_interface__), xoff=-200000)), rec))
  26|     return out
  27| 
  28| 
  29| def load_relief():
  30|     z = np.load(os.path.join(R, "tests", "relief_v30", "relief_v30_mix.npz"))
  31|     return z["new"].astype("float64")
  32| 
  33| 
  34| def sample_vertex(grid, xs, zs):
  35|     """Bilinear sample of a vertex grid at game coordinates."""
  36|     c = np.clip(np.asarray(xs) / 6.0, 0, grid.shape[1] - 1.001)
  37|     r = np.clip((12282 - np.asarray(zs)) / 6.0, 0, grid.shape[0] - 1.001)
  38|     c0, r0 = np.floor(c).astype(int), np.floor(r).astype(int)
  39|     fc, fr = c - c0, r - r0
  40|     return (grid[r0, c0] * (1 - fc) * (1 - fr) + grid[r0, c0 + 1] * fc * (1 - fr)
  41|             + grid[r0 + 1, c0] * (1 - fc) * fr + grid[r0 + 1, c0 + 1] * fc * fr)
  42| 
  43| 
  44| def resample(line, step):
  45|     n = max(2, int(np.ceil(line.length / step)) + 1)
  46|     d = np.linspace(0, line.length, n)
  47|     pts = np.array([line.interpolate(v).coords[0] for v in d])
  48|     return d, pts
  49| 
  50| 
  51| def smooth_course(line, step, sigma_m):
  52|     """A course smoothed along its arc (Gaussian of sigma_m metres), its two ends held in place over 2 sigma so
  53|     junctions and mouths stay where they are. sigma_m <= 0 returns the line unchanged. The OSM courses turn more than
  54|     20 degrees every ~23 m on average; a ribbon on such a line draws corners and blobs at 6 m
  55|     (evidence/v30-v8-candidate-2026-10-06/general-review)."""
  56|     if sigma_m <= 0 or line.length < 2 * step:
  57|         return line
  58|     from scipy.ndimage import gaussian_filter1d
  59|     _, pts = resample(line, step)
  60|     k = sigma_m / step
  61|     sm = gaussian_filter1d(pts, k, axis=0, mode="nearest")
  62|     i = np.arange(len(pts))
  63|     w = np.clip(np.minimum(i, len(pts) - 1 - i) / (2 * k), 0, 1)[:, None]
  64|     return LineString(pts + (sm - pts) * w)
  65| 
  66| 
  67| def normals(pts, smooth=5):
  68|     from scipy.ndimage import uniform_filter1d
  69|     t = np.gradient(pts, axis=0)
  70|     if smooth > 1 and len(t) > 2:
  71|         # uniform_filter1d keeps the length; np.convolve(mode="same") grows short arrays to the kernel size
  72|         t = uniform_filter1d(t, size=min(smooth, len(t)), axis=0, mode="nearest")
  73|     t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
  74|     return np.column_stack([-t[:, 1], t[:, 0]]), t
  75| 
  76| 
  77| def smooth_noise(n, sigma, rng):
  78|     from scipy.ndimage import gaussian_filter1d
  79|     v = gaussian_filter1d(rng.standard_normal(n), sigma)
  80|     return v / max(np.abs(v).max(), 1e-9)
  81| 
  82| 
  83| def ribbon(pts, left, right):
  84|     """Polygon between offset curves; left/right are per-sample offsets in metres."""
  85|     nrm, _ = normals(pts)
  86|     lp = pts + nrm * left[:, None]
  87|     rp = pts - nrm * right[:, None]
  88|     poly = Polygon(np.vstack([lp, rp[::-1]]))
  89|     return make_valid(poly.buffer(0))
  90| 
  91| 
  92| def merge_lines(geoms):
  93|     u = unary_union(geoms)
  94|     if u.geom_type == "LineString":
  95|         return [u]
  96|     m = linemerge(u)
  97|     return list(m.geoms) if hasattr(m, "geoms") else [m]
  98| 
  99| 
 100| def save_geojson(path, features):
 101|     from shapely.geometry import mapping
 102|     fc = {"type": "FeatureCollection", "coordinate_system": "game X/Z metres (TB minus 200000)",
 103|           "features": [{"type": "Feature", "properties": p, "geometry": mapping(g)} for g, p in features]}
 104|     with open(path, "wb") as f:
 105|         f.write(json.dumps(fc, ensure_ascii=False).encode("utf-8"))
 106| 
```

# Reminder
# Task W1: new tool tools/water/smooth_water_outlines_v30.py
Smooth the inland water outlines of a water design along their rings, as decided by the owner on 06-10 (sigma 12 m,
each point moving at most 4 m, area kept): the contour-v2 lakes copy the 6 m staircase of the V29 raster and the OSM
ponds and river bodies are coarse polygons, so the visible shores keep their corners. A prototype (below,
smooth_polys_proto.py) measured on the design: points turning more than 45 degrees on 6 m chords, lakes 20.4 -> 8.6 %,
ponds 25.8 -> 16.9 %, rivers 9.0 -> 4.3 %, shift p95 4 m. Make it a production tool:
- Usage: smooth_water_outlines_v30.py --design IN_DIR --out OUT_DIR [--contour PATH] [--sigma 12] [--max-shift 4]
  [--narva-radius 600] [--contact-m 2.0]; and smooth_water_outlines_v30.py --selftest. OUT_DIR must not exist.
- Inputs: IN_DIR/water_v3.geojson (features with properties.class: navigable, delta_*, river, pond), the contour file
  (default R + evidence/regional-foundation-v1/water-surfaces-contour-v2.geojson, R from tools/water/water_common.py;
  features with properties.body 'lake_NNN' or 'river...' and level_m), IN_DIR/streams_candidates.geojson.
- Smoothed: water_v3 features of class 'river' and 'pond'; contour features whose body starts with 'lake'.
  Unchanged: navigable, delta_*, the contour 'river' bands, streams, and every feature whose geometry intersects the
  Narva disc (centre (2417.1428225906, 6889.8850822322), radius --narva-radius): Narva keeps the V29 rules.
- Ring smoothing as in the prototype (1 m resample, Gaussian of sigma m with wrap, sigma at most a ring's length / 8,
  shift capped at --max-shift), plus CONTACTS: a ring point within --contact-m of any OTHER inland body (all
  water_v3 features, the contour lakes and river bands, the streams; not the feature itself) does not move, and the
  cap grows linearly back to --max-shift over the next 10 m along the ring, so rivers keep meeting lakes and ponds.
  Islands (holes) under 200 m2 stay as they are.
- Validity: make_valid, keep polygonal parts over 1 m2 (a MultiPolygon stays multi). If the result is empty, or its
  area differs from the original by more than 15 %, retry with half the max shift, then keep the original; count
  these fallbacks.
- Area: after smoothing, restore the area with buffer((A0 - A1) / perimeter, join_style=round), twice.
- Outputs, in OUT_DIR: water_v3.geojson (the same features in the same ORDER with the same properties; only the
  geometries of the smoothed ones change; other tools index ponds by position), written with
  water_common.save_geojson; contour_lakes.geojson (the input contour file's JSON with only the smoothed lake
  geometries replaced, every other key and feature as it was); copies (byte copies) of streams_candidates.geojson,
  profiles.npz, navigable.geojson, navigable_report.json, navigable_samples.npz and water_v3_summary.json;
  smoothing_report.json: params, input sha256, and per kind (lake, pond, river): features, smoothed, unchanged_narva,
  fallbacks, shift p50/p95, area change p5/p95 (%), share of ring points turning more than 45 and 30 degrees on 6 m
  chords before and after (the prototype's turning()).
- --selftest: synthetic polygons on a temporary folder: a 6 m staircase blob (turning share must drop, area within
  2 %), two polygons that touch (they must still touch: distance 0 after), one inside the Narva disc (unchanged
  byte for byte), the order of features kept; print SELFTEST PASS.

Write the whole files now.

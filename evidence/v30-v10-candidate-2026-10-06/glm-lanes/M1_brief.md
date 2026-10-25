IMPORTANT PROCESS NOTE: write the complete files FIRST, in one pass, then stop. Keep internal deliberation focused.
The receiver re-runs every changed tool with its DEFAULTS and compares sha256 against archived outputs: with the
defaults, terrain/water/image outputs must be byte-identical to today's. Change nothing that the task does not ask for.
Code and comments in English; keep the style of the surrounding code (comment density, naming, idiom).
Output: one fenced block per changed or new file, each preceded by the line `FILE: <repo-relative path>`, whole file.
Coordinates: game metres, x east, z north; the vertex grid is N = 2048 vertices every 6 m, row r at z = 12282 - 6r,
column c at x = 6c (tools/terrain/v30_common.py).

# Task M1: new tool tools/water/audit_waterline_v30.py from the scratchpad script waterline_metric.py (below)
The script measures how the VISIBLE waterline (terrain on the native triangles below the 6 m cell plane, as the
engine and build_surface_v30.py draw it) follows the design outline, outside every shaping tool, and how sharply the
visible waterline turns. It is the acceptance gate of the shore work from now on. Make it a production tool with the
same algorithm and the same JSON output keys, and:
- argparse CLI: --design DIR (required), --contour PATH (default: R + evidence/regional-foundation-v1/
  water-surfaces-contour-v2.geojson), --terrain LABEL=PATH (repeatable, at least one), --json OUT (optional),
  --step 2.0, --search 8.0, --ds 0.25, --border-m 66, --narva-m 620, --exclude-m 30 (distance to navigable and delta
  bodies), --smooth-m 12 (the Gaussian of the zigzag term) and --chord-steps 3 (6 m chords at --step 2); defaults =
  the script's constants, so the default output equals the script's.
- `--selftest`: in a temporary folder build a synthetic design (water_v3.geojson with one 'pond' polygon: a circle of
  radius 60 m centred at (6000, 6000); an empty streams_candidates.geojson; a contour file with no lakes) and two
  synthetic terrain npz files on the full N x N grid (keys heights float32, cls uint8, level float32; heights 5.0 on
  land): (a) SMOOTH: a vertex inside the circle has cls 7, level 3.0 and height 3.0 - 0.15 * d_in, a land vertex
  within 30 m height 3.0 + 0.15 * d_out (d = distance to the circle, metres), so the plane crossing falls on the circle;
  (b) STAIRCASE: same classes and levels, but every wet vertex at 2.5 and every land vertex at 3.5, so the crossing
  falls at mid-edge on the 6 m lattice. Assert: (a) offset_p90 < 0.5 m and visible_turn_gt45_share < 0.05;
  (b) offset_p90 > (a) offset_p90 and visible_turn_gt30_share > (a)'s; missing_share 0 for both; print SELFTEST PASS.
  Keep the selftest under a minute (only the points near the circle are sampled anyway).
- Module docstring: what is measured, why (the shore tools measured themselves against their own outline and missed
  the staircase, 06-10), the exclusions, the output keys, Usage.

### scratchpad waterline_metric.py (full file, 162 lines)
```python
   1| """How closely the VISIBLE waterline follows the design outline, measured outside every shaping tool.
   2| 
   3| The visible water is what the engine and build_surface_v30.py draw: terrain on the native triangles below the 6 m cell
   4| plane (v30_common.cell_planes), or below the sea (0.75 m). Along every inland design outline (contour lakes, OSM ponds,
   5| river and stream bodies of the design folder), every 2 m, the tool walks the outline normal from 8 m inside to 8 m
   6| outside in 0.25 m steps and takes the visible water edge nearest to the outline. Per class of the nearest design body:
   7| - offset: |distance| from the design outline to the visible edge (p50, p90);
   8| - zigzag: RMS of the offset minus its 12 m Gaussian along the outline, the 6-12 m wobble of a staircase;
   9| - missing: share of points with no visible edge within 8 m.
  10| Points within 66 m of the map border, 620 m of the Narva bridge or 30 m of a navigable reach or the delta are left out.
  11| Usage: waterline_metric.py DESIGN_DIR [--contour PATH] label=terrain.npz ... [--json OUT]"""
  12| import json
  13| import sys
  14| 
  15| import numpy as np
  16| import shapely
  17| from scipy.ndimage import gaussian_filter1d
  18| from shapely.geometry import shape
  19| 
  20| sys.path.insert(0, r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees'
  21|                    r'\codex-handoff-review-74f290\tools\terrain')
  22| from v30_common import cell_planes, tri_sample  # noqa: E402
  23| 
  24| R = 'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/'
  25| NARVA = (2417.1428225906, 6889.8850822322)
  26| STEP, SEARCH, DS = 2.0, 8.0, 0.25
  27| 
  28| 
  29| def design_outline(design, contour_path):
  30|     feats = json.load(open(design + '/water_v3.geojson', encoding='utf-8'))['features']
  31|     streams = [f for f in json.load(open(design + '/streams_candidates.geojson', encoding='utf-8'))['features']
  32|                if f['properties']['tier_m'] >= 2500]
  33|     contour = [f for f in json.load(open(contour_path, encoding='utf-8'))['features']
  34|                if f['properties']['body'].startswith('lake')]
  35|     bodies = ([(shape(f['geometry']), f['properties']['class']) for f in feats if f['properties']['class'] in ('river', 'pond')]
  36|               + [(shape(f['geometry']), 'stream') for f in streams] + [(shape(f['geometry']), 'lake') for f in contour])
  37|     excl = shapely.union_all([shape(f['geometry']).buffer(30) for f in feats
  38|                               if f['properties']['class'] == 'navigable' or f['properties']['class'].startswith('delta')])
  39|     union = shapely.union_all([g for g, _ in bodies])
  40|     tree = shapely.STRtree([g for g, _ in bodies])
  41|     kinds = np.array([k for _, k in bodies])
  42|     pts, nrm, kind, ring_id = [], [], [], []
  43|     rid = 0
  44|     for poly in getattr(union, 'geoms', [union]):
  45|         for ring in [poly.exterior] + list(poly.interiors):
  46|             n = int(ring.length // STEP)
  47|             if n < 4:
  48|                 continue
  49|             d = np.arange(n) * STEP
  50|             p = np.array([ring.interpolate(v).coords[0] for v in d])
  51|             t = np.roll(p, -1, axis=0) - np.roll(p, 1, axis=0)
  52|             t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
  53|             nr = np.column_stack([t[:, 1], -t[:, 0]])
  54|             # orient the normal outwards: a step outside must leave the water polygon
  55|             probe = shapely.points(p + nr * 1.0)
  56|             inside = shapely.contains(poly, probe)
  57|             nr[inside] *= -1
  58|             pts.append(p)
  59|             nrm.append(nr)
  60|             ring_id.append(np.full(n, rid))
  61|             rid += 1
  62|     P, Nn, RID = np.vstack(pts), np.vstack(nrm), np.concatenate(ring_id)
  63|     near = tree.query_nearest(shapely.points(P), all_matches=False)
  64|     K = kinds[near[1]] if near.ndim == 2 else kinds[near]
  65|     keep = ((P[:, 0] > 66) & (P[:, 0] < 12282 - 66) & (P[:, 1] > 66) & (P[:, 1] < 12282 - 66)
  66|             & (np.hypot(P[:, 0] - NARVA[0], P[:, 1] - NARVA[1]) > 620)
  67|             & ~shapely.contains(excl, shapely.points(P)))
  68|     return P, Nn, K, RID, keep
  69| 
  70| 
  71| def measure(terrain, P, Nn, K, RID, keep):
  72|     t = np.load(terrain)
  73|     h, cls, lev = t['heights'].astype(np.float64), t['cls'], t['level'].astype(np.float64)
  74|     plane = cell_planes(cls, lev)
  75|     steps = np.arange(-SEARCH, SEARCH + 1e-9, DS)
  76|     off = np.full(len(P), np.nan)
  77|     for i0 in range(0, len(P), 40000):
  78|         sl = slice(i0, i0 + 40000)
  79|         X = P[sl, 0, None] + Nn[sl, 0, None] * steps[None]
  80|         Z = P[sl, 1, None] + Nn[sl, 1, None] * steps[None]
  81|         Xc, Zc = np.clip(X, 0, 12281.9), np.clip(Z, 0, 12281.9)
  82|         hh = tri_sample(h, Xc, Zc)
  83|         pl = plane[np.clip(np.floor((12282 - Zc) / 6).astype(int), 0, 2046), np.clip(np.floor(Xc / 6).astype(int), 0, 2046)]
  84|         W = (np.isfinite(pl) & (hh < np.nan_to_num(pl, nan=-1e9))) | (hh < 0.75)
  85|         ch = W[:, :-1] != W[:, 1:]                       # an edge between two steps
  86|         pos = (steps[:-1] + steps[1:]) / 2
  87|         dist = np.where(ch, np.abs(pos)[None], np.inf)
  88|         j = np.argmin(dist, axis=1)
  89|         ok = np.isfinite(dist[np.arange(len(j)), j])
  90|         o = np.where(ok, pos[j], np.nan)
  91|         off[sl] = o
  92|     res = {}
  93|     for k in ('lake', 'pond', 'river', 'stream', 'all'):
  94|         sel = keep & ((K == k) if k != 'all' else True)
  95|         o = off[sel]
  96|         good = np.isfinite(o)
  97|         # zigzag: offset minus its own 12 m Gaussian, ring by ring (only finite runs)
  98|         zz = []
  99|         for r in np.unique(RID[sel]):
 100|             m = sel & (RID == r)
 101|             v = off[m]
 102|             if np.isfinite(v).sum() < 8:
 103|                 continue
 104|             v = np.where(np.isfinite(v), v, np.nanmedian(v))
 105|             zz.append(v - gaussian_filter1d(v, 12.0 / STEP, mode='wrap'))
 106|         zz = np.concatenate(zz) if zz else np.array([np.nan])
 107|         # turning of the visible waterline (design point moved along its normal to the visible edge) and of the
 108|         # design outline itself, on 6 m chords: share of points turning more than 30 and 45 degrees
 109|         tv, td = [], []
 110|         for r in np.unique(RID[sel]):
 111|             m = sel & (RID == r)
 112|             if m.sum() < 8:
 113|                 continue
 114|             v = off[m]
 115|             if not np.isfinite(v).all():
 116|                 v = np.where(np.isfinite(v), v, np.nanmedian(v) if np.isfinite(v).any() else 0.0)
 117|             for pts_, out_ in ((P[m] + Nn[m] * v[:, None], tv), (P[m], td)):
 118|                 a = pts_ - np.roll(pts_, 3, axis=0)
 119|                 b = np.roll(pts_, -3, axis=0) - pts_
 120|                 cosang = (a * b).sum(1) / np.maximum(np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1), 1e-9)
 121|                 out_.append(np.degrees(np.arccos(np.clip(cosang, -1, 1))))
 122|         tv = np.concatenate(tv) if tv else np.array([np.nan])
 123|         td = np.concatenate(td) if td else np.array([np.nan])
 124|         res[k] = {'points': int(sel.sum()), 'missing_share': round(float(1 - good.mean()), 3) if sel.any() else None,
 125|                   'offset_p50': round(float(np.nanpercentile(np.abs(o), 50)), 2) if good.any() else None,
 126|                   'offset_p90': round(float(np.nanpercentile(np.abs(o), 90)), 2) if good.any() else None,
 127|                   'zigzag_rms': round(float(np.sqrt(np.nanmean(zz ** 2))), 2),
 128|                   'zigzag_abs_p50_p90': [round(float(np.nanpercentile(np.abs(zz), q)), 2) for q in (50, 90)],
 129|                   'visible_turn_gt30_share': round(float(np.nanmean(tv > 30)), 3),
 130|                   'visible_turn_gt45_share': round(float(np.nanmean(tv > 45)), 3),
 131|                   'design_turn_gt30_share': round(float(np.nanmean(td > 30)), 3),
 132|                   'design_turn_gt45_share': round(float(np.nanmean(td > 45)), 3)}
 133|     return res, off
 134| 
 135| 
 136| def main():
 137|     args = sys.argv[1:]
 138|     out_json = None
 139|     if '--json' in args:
 140|         out_json = args[args.index('--json') + 1]
 141|         del args[args.index('--json'):args.index('--json') + 2]
 142|     contour = R + 'evidence/regional-foundation-v1/water-surfaces-contour-v2.geojson'
 143|     if '--contour' in args:
 144|         contour = args[args.index('--contour') + 1]
 145|         del args[args.index('--contour'):args.index('--contour') + 2]
 146|     design = args[0]
 147|     P, Nn, K, RID, keep = design_outline(design, contour)
 148|     allres = {}
 149|     for a in args[1:]:
 150|         label, path = a.split('=', 1)
 151|         res, _ = measure(path, P, Nn, K, RID, keep)
 152|         allres[label] = res
 153|         print(label)
 154|         for k, v in res.items():
 155|             print(f'   {k:7}', v)
 156|     if out_json:
 157|         json.dump(allres, open(out_json, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
 158| 
 159| 
 160| if __name__ == '__main__':
 161|     main()
 162| 
```

### tools/terrain/v30_common.py (read only) (full file, 113 lines)
```python
   1| """Shared helpers for terrain V30: native triangle sampling, vertex rasterisation and the road network graph.
   2| 
   3| Vertex grid: col c, row r -> x = 6c, z = 12282 - 6r (row 0 north). Each 6 m cell is split along its NW-SE diagonal,
   4| as Terrain Builder's native grid (contract recorded in HANDOFF-history.md, "Contrato nativo LOCAL").
   5| """
   6| import json
   7| import os
   8| 
   9| import numpy as np
  10| from affine import Affine
  11| from rasterio.features import rasterize
  12| from shapely.geometry import shape
  13| 
  14| R = r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev"
  15| N = 2048
  16| VERTEX = Affine(6, 0, -3, 0, -6, 12285)  # one pixel per vertex, game coordinates
  17| 
  18| 
  19| def tri_sample(h, xs, zs):
  20|     """Height on the native triangulated surface (NW-SE diagonal) at game coordinates."""
  21|     c = np.clip(np.asarray(xs, dtype=float) / 6.0, 0, N - 1.000001)
  22|     r = np.clip((12282 - np.asarray(zs, dtype=float)) / 6.0, 0, N - 1.000001)
  23|     c0, r0 = np.floor(c).astype(int), np.floor(r).astype(int)
  24|     fc, fr = c - c0, r - r0
  25|     nw, ne = h[r0, c0], h[r0, c0 + 1]
  26|     sw, se = h[r0 + 1, c0], h[r0 + 1, c0 + 1]
  27|     upper = nw + fc * (ne - nw) + fr * (se - ne)
  28|     lower = nw + fr * (sw - nw) + fc * (se - sw)
  29|     return np.where(fc >= fr, upper, lower)
  30| 
  31| 
  32| def raster_vertices(geoms, all_touched=False, values=None, dtype="uint8"):
  33|     pairs = [(g, 1 if values is None else v) for g, v in zip(geoms, values if values is not None else [None] * len(geoms)) if not g.is_empty]
  34|     if not pairs:
  35|         return np.zeros((N, N), dtype=dtype)
  36|     return rasterize(pairs, out_shape=(N, N), transform=VERTEX, dtype=dtype, all_touched=all_touched)
  37| 
  38| 
  39| def grid_xz():
  40|     c, r = np.meshgrid(np.arange(N), np.arange(N))
  41|     return c * 6.0, 12282 - r * 6.0
  42| 
  43| 
  44| def road_network():
  45|     """V29 graded road network (union of shortest routes between 11 anchors): list of (LineString, properties)."""
  46|     fc = json.load(open(os.path.join(R, "evidence", "regional-foundation-v1", "road-network-game.json"), encoding="utf-8"))
  47|     return [(shape(f["geometry"]), f["properties"]) for f in fc["features"]]
  48| 
  49| 
  50| def road_graph(step=3.0):
  51|     """Densified graph of the road network: points (n,2), edges (m,2) with lengths; endpoints merged by OSM node id."""
  52|     pts, edges, key_index = [], [], {}
  53| 
  54|     def node(key, xy):
  55|         if key is not None and key in key_index:
  56|             return key_index[key]
  57|         pts.append(xy)
  58|         idx = len(pts) - 1
  59|         if key is not None:
  60|             key_index[key] = idx
  61|         return idx
  62| 
  63|     for line, prop in road_network():
  64|         coords = np.asarray(line.coords)[:, :2]
  65|         if len(coords) < 2 or line.length <= 0:
  66|             continue
  67|         n = max(1, int(np.ceil(line.length / step)))
  68|         d = np.linspace(0, line.length, n + 1)
  69|         xy = np.array([line.interpolate(v).coords[0][:2] for v in d])
  70|         a = node(("osm", prop.get("node_a")) if prop.get("node_a") is not None else None, tuple(xy[0]))
  71|         prev = a
  72|         for k in range(1, n):
  73|             cur = node(None, tuple(xy[k]))
  74|             edges.append((prev, cur))
  75|             prev = cur
  76|         b = node(("osm", prop.get("node_b")) if prop.get("node_b") is not None else None, tuple(xy[-1]))
  77|         edges.append((prev, b))
  78|     pts = np.asarray(pts, dtype=float)
  79|     edges = np.asarray(edges, dtype=int)
  80|     lengths = np.hypot(*(pts[edges[:, 0]] - pts[edges[:, 1]]).T)
  81|     keep = lengths > 1e-6
  82|     return pts, edges[keep], lengths[keep]
  83| 
  84| 
  85| POND_CLASSES = (2, 3, 5, 6, 7)
  86| 
  87| 
  88| def cell_planes(cls, level, band=0.025, sea_cut=0.80):
  89|     """Plane of every 6 m cell covered by a pond piece: the band of the mean level of its water corners (lakes,
  90|     navigable, rivers, streams, ponds above the sea). NaN where the cell has no such corner. Pieces, builder and
  91|     surface all use this rule. cell (i, j) lies between vertex rows i, i+1 and columns j, j+1."""
  92|     # Production pieces and surfaces use float64. Without normalization,
  93|     # float32(0.8) compares differently against 0.8 after promotion: consumers
  94|     # omitted 467 existing pond cells merely by retaining the stored dtype.
  95|     level = np.asarray(level, dtype=np.float64)
  96|     wet = np.isin(cls, POND_CLASSES) & (np.nan_to_num(level, nan=-1.0) > sea_cut)
  97|     lv = np.where(wet, level, 0.0)
  98|     total = np.zeros((N - 1, N - 1))
  99|     count = np.zeros((N - 1, N - 1))
 100|     for dr in (0, 1):
 101|         for dc in (0, 1):
 102|             total += lv[dr:dr + N - 1, dc:dc + N - 1]
 103|             count += wet[dr:dr + N - 1, dc:dc + N - 1]
 104|     return np.where(count > 0, np.rint(total / np.maximum(count, 1) / band) * band, np.nan)
 105| 
 106| 
 107| def vertex_plane_bounds(plane):
 108|     """Lowest and highest plane among the up to four cells around each vertex (NaN where none is covered)."""
 109|     p = np.pad(plane, 1, constant_values=np.nan)
 110|     stack = np.stack([p[0:N, 0:N], p[0:N, 1:N + 1], p[1:N + 1, 0:N], p[1:N + 1, 1:N + 1]])
 111|     with np.errstate(all="ignore"):
 112|         return np.nanmin(stack, axis=0), np.nanmax(stack, axis=0)
 113| 
```

# Reminder

# Task M1: new tool tools/water/audit_waterline_v30.py from the scratchpad script waterline_metric.py (below)
The script measures how the VISIBLE waterline (terrain on the native triangles below the 6 m cell plane, as the
engine and build_surface_v30.py draw it) follows the design outline, outside every shaping tool, and how sharply the
visible waterline turns. It is the acceptance gate of the shore work from now on. Make it a production tool with the
same algorithm and the same JSON output keys, and:
- argparse CLI: --design DIR (required), --contour PATH (default: R + evidence/regional-foundation-v1/
  water-surfaces-contour-v2.geojson), --terrain LABEL=PATH (repeatable, at least one), --json OUT (optional),
  --step 2.0, --search 8.0, --ds 0.25, --border-m 66, --narva-m 620, --exclude-m 30 (distance to navigable and delta
  bodies), --smooth-m 12 (the Gaussian of the zigzag term) and --chord-steps 3 (6 m chords at --step 2); defaults =
  the script's constants, so the default output equals the script's.
- `--selftest`: in a temporary folder build a synthetic design (water_v3.geojson with one 'pond' polygon: a circle of
  radius 60 m centred at (6000, 6000); an empty streams_candidates.geojson; a contour file with no lakes) and two
  synthetic terrain npz files on the full N x N grid (keys heights float32, cls uint8, level float32; heights 5.0 on
  land): (a) SMOOTH: a vertex inside the circle has cls 7, level 3.0 and height 3.0 - 0.15 * d_in, a land vertex
  within 30 m height 3.0 + 0.15 * d_out (d = distance to the circle, metres), so the plane crossing falls on the circle;
  (b) STAIRCASE: same classes and levels, but every wet vertex at 2.5 and every land vertex at 3.5, so the crossing
  falls at mid-edge on the 6 m lattice. Assert: (a) offset_p90 < 0.5 m and visible_turn_gt45_share < 0.05;
  (b) offset_p90 > (a) offset_p90 and visible_turn_gt30_share > (a)'s; missing_share 0 for both; print SELFTEST PASS.
  Keep the selftest under a minute (only the points near the circle are sampled anyway).
- Module docstring: what is measured, why (the shore tools measured themselves against their own outline and missed
  the staircase, 06-10), the exclusions, the output keys, Usage.

Write the whole file now.

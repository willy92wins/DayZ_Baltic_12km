IMPORTANT PROCESS NOTE: write the complete files FIRST, in one pass, then stop. Keep internal deliberation focused.
The receiver re-runs every changed tool with its DEFAULTS and compares sha256 against archived outputs: with the
defaults, terrain/water/image outputs must be byte-identical to today's. Change nothing that the task does not ask for.
Code and comments in English; keep the style of the surrounding code (comment density, naming, idiom).
Output: one fenced block per changed or new file, each preceded by the line `FILE: <repo-relative path>`, whole file.
Coordinates: game metres, x east, z north; the vertex grid is N = 2048 vertices every 6 m, row r at z = 12282 - 6r,
column c at x = 6c (tools/terrain/v30_common.py).

# Task E1: round the river ends where the border rule cuts them (tools/terrain/build_v30_water.py)
With --border-margin M > 0, clip_geom (lines 81-98) intersects every river body with the inner box
shapely.box(M, M, 12282 - M, 12282 - M); the cut leaves a straight end with two square corners, which reads from the
air as a dark rectangular frame (Guillermo, 06-10: "redondea el final de los ríos"). Add an option that rounds them.

1. Parse `--round-river-ends R` (metres, default 0 = today's behaviour) from sys.argv[3:] by hand like the other
   options (lines 43-53). It only acts with M > 0 and R > 0, and only on kind "rivers" (streams, lakes and ponds keep
   today's straight clip).
2. New module-level function `round_cut_ends(poly, inner, r_max)` -> (geometry, n_rounded). `poly` is one Polygon
   part of the clipped river (the parts that `polygons(g.intersection(inner))` returns). Algorithm:
   - cut segments: the line parts of poly.boundary.intersection(inner.exterior) (it can be a LineString,
     MultiLineString or GeometryCollection; merge touching pieces with shapely.line_merge; ignore points and lines
     shorter than 0.5 m);
   - for each cut segment s of length w: r = min(r_max, 0.45 * w). Round locally with a morphological opening that
     only acts near the cut:
         opened = poly.buffer(-r, quad_segs=16).buffer(r, quad_segs=16)
         near = s.buffer(2 * r, quad_segs=16)
         cand = poly.difference(near.difference(opened))
     keep only the polygonal parts of cand (the largest one if several: the cut end must not split the river).
     Guard: a square corner rounded with radius r loses (1 - pi / 4) r^2, two corners about 0.43 r^2. When
     poly.area - cand.area > 1.0 * r^2 (the river runs along the cut, or is narrower than 2 r there), halve r and
     retry; below r = 1.0 m leave this segment straight. Otherwise poly = cand and count it.
   - return the rounded polygon and the number of rounded segments.
3. In clip_geom, for kind == "rivers" and R > 0, apply round_cut_ends to every part before returning, and add
   "rivers_ends_rounded" (the total number of rounded segments) to `counts` only when R > 0, so the printed stats
   stay byte-identical with the defaults. The same rounded geometries must feed everything clip_geom already feeds
   (classes, levels, sd, inside_poly): do not round anywhere else.
4. `--selftest`: when present, run a synthetic check and exit 0 before any other work (the module reads
   sys.argv[1] and sys.argv[2] at import time, lines 42-53: move that parsing under `if __name__ == "__main__"` or guard
   it so `--selftest` alone works; with real arguments the behaviour must not change). The selftest, with
   inner = shapely.box(60, 60, 12222, 12222) and r_max = 15:
   a. a river 20 m wide crossing the east cut: poly = box(12100, 1000, 12300, 1020) & inner. Expected r = 9 (0.45 x 20),
      one rounded segment, area lost within 25 % of 0.429 x 81 = 34.8 m^2, the middle of the cut (12222, 1010) still
      within 0.05 m of the polygon, and the corner (12221.5, 1000.5) outside it;
   b. a river 22 m wide running along the cut: poly = box(12200, 1000, 12300, 2000) & inner. The guard must stop it
      losing more than r^2 per rounded segment and the polygon must keep at least 99 % of its area;
   c. a river inside the box (never cut): unchanged, zero rounded segments.
   Print one line per case and assert.
5. Docstring: add a paragraph for --round-river-ends after the --border-keep-m one, and the option to the Usage line.

# The file to change

### tools/terrain/build_v30_water.py (full file, 356 lines)
```python
   1| """Water rasters for terrain V30 on the vertex grid: class, level, distance to bank and the V29 water to remove.
   2| 
   3| Classes (uint8): 0 land, 1 sea, 2 kept lake, 3 navigable, 4 delta, 5 river, 6 stream, 7 pond.
   4| Levels: sea 0.75 m; kept lakes and navigable reaches take the V29 surface levels (contour-v2 bands); rivers and
   5| streams the nearest sample of their monotone profile; ponds their design level; delta channels the sea.
   6| Output <out>/water_v30.npz.
   7| 
   8| Map-border rule (Guillermo, 06-10): the borders are land, as in Chernarus. --border-margin M (default 0 = today's
   9| behaviour) intersects every inland water geometry (contour-v2 lakes, river bodies, streams, ponds) with the inner
  10| box shapely.box(M, M, 12282 - M, 12282 - M) before any rasterisation, so lakes, rivers, streams and ponds end about
  11| M metres before the border while the sea, the delta and the navigable reaches run on as today. Empty results are
  12| dropped. --drop-border-water-km2 A (default 0, used with M > 0) drops lakes and ponds whose ORIGINAL polygon
  13| reaches into the border band and whose area is below A km2 instead of clipping them. The same clipped geometries
  14| feed the classes, the levels, the signed distance sd and inside_poly, so everything derived stays coherent.
  15| --border-keep-m K (default 0, used with M > 0) keeps a lake or pond whole, neither dropped nor clipped, when its
  16| original polygon stays at least K m from the map edge although it reaches into the M band (Guillermo, 06-10: lakes
  17| 047 and 107, which only graze the band); rivers and streams are not affected.
  18| Self-check: with --border-margin 60 no vertex of classes 2, 5, 6, 7 lies within 60 m of the map border (x or z
  19| below 60 or above 12222) except those of the bodies kept whole; the printed stats count them as
  20| border_inland_vertices, with the clipped, dropped and kept bodies.
  21| --contour PATH reads the contour-v2 lakes and river bands from PATH (default: the regional-foundation-v1 file), for
  22| a design whose lake outlines were smoothed (tools/water/smooth_water_outlines_v30.py).
  23| Usage: build_v30_water.py <design dir> <out dir> [--border-margin M] [--drop-border-water-km2 A] [--border-keep-m K]
  24|                           [--contour PATH]
  25| """
  26| import json
  27| import os
  28| import sys
  29| 
  30| import numpy as np
  31| import contourpy
  32| from scipy.ndimage import binary_dilation, distance_transform_edt, gaussian_filter
  33| from scipy.spatial import cKDTree
  34| import shapely
  35| from shapely.geometry import shape
  36| 
  37| sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
  38| from v30_common import N, R, grid_xz, raster_vertices  # noqa: E402
  39| from verify_roads_v30 import road_chains  # noqa: E402
  40| import rasterio  # noqa: E402
  41| 
  42| W_DIR, OUT = sys.argv[1], sys.argv[2]
  43| BORDER_MARGIN, DROP_BORDER_KM2, BORDER_KEEP_M = 0.0, 0.0, 0.0
  44| CONTOUR = os.path.join(R, "evidence", "regional-foundation-v1", "water-surfaces-contour-v2.geojson")
  45| for _i, _a in enumerate(sys.argv[3:]):
  46|     if _a == "--border-margin":
  47|         BORDER_MARGIN = float(sys.argv[4 + _i])
  48|     elif _a == "--drop-border-water-km2":
  49|         DROP_BORDER_KM2 = float(sys.argv[4 + _i])
  50|     elif _a == "--border-keep-m":
  51|         BORDER_KEEP_M = float(sys.argv[4 + _i])
  52|     elif _a == "--contour":
  53|         CONTOUR = sys.argv[4 + _i]
  54| SEA_LEVEL = 0.75
  55| NARVA = (2417.1428225906, 6889.8850822322)
  56| NARVA_ZONE_M = 600.0
  57| STREAM_TIER = 2500
  58| 
  59| 
  60| def main():
  61|     v33 = np.load(os.path.join(R, "tests", "regional_outline_smoothing_v33", "reference.npz"))
  62|     contour = json.load(open(CONTOUR, encoding="utf-8"))["features"]
  63|     bodies = json.load(open(os.path.join(W_DIR, "water_v3.geojson"), encoding="utf-8"))["features"]
  64|     streams = [f for f in json.load(open(os.path.join(W_DIR, "streams_candidates.geojson"), encoding="utf-8"))["features"]
  65|                if f["properties"]["tier_m"] >= STREAM_TIER]
  66|     prof = np.load(os.path.join(W_DIR, "profiles.npz"))
  67| 
  68|     clip = BORDER_MARGIN > 0
  69|     counts = {"lakes_clipped": 0, "lakes_dropped": 0, "ponds_clipped": 0, "ponds_dropped": 0,
  70|               "rivers_clipped": 0, "streams_clipped": 0}
  71|     if BORDER_KEEP_M > 0:
  72|         counts.update(lakes_kept_whole=0, ponds_kept_whole=0)
  73|     inner = shapely.box(BORDER_MARGIN, BORDER_MARGIN, 12282.0 - BORDER_MARGIN, 12282.0 - BORDER_MARGIN)
  74|     border_band = shapely.box(0.0, 0.0, 12282.0, 12282.0).difference(inner)
  75| 
  76|     def polygons(g):
  77|         if g.geom_type == "Polygon":
  78|             return [g] if g.area > 0 else []
  79|         return [p for part in getattr(g, "geoms", []) for p in polygons(part)]
  80| 
  81|     def clip_geom(g, kind, drop=False):
  82|         # Border rule for one inland geometry: small border water is dropped, the rest is clipped to the inner box
  83|         # (polygonal parts only, so the shore rings below stay rings). Geometries inside the box are kept as they are.
  84|         if not clip or g.within(inner):
  85|             return g
  86|         if BORDER_KEEP_M > 0 and kind in ("lakes", "ponds"):
  87|             x0, z0, x1, z1 = g.bounds
  88|             if min(x0, z0, 12282.0 - x1, 12282.0 - z1) >= BORDER_KEEP_M:
  89|                 counts[kind + "_kept_whole"] += 1
  90|                 return g
  91|         if drop and DROP_BORDER_KM2 > 0 and g.intersects(border_band) and g.area < DROP_BORDER_KM2 * 1e6:
  92|             counts[kind + "_dropped"] += 1
  93|             return None
  94|         counts[kind + "_clipped"] += 1
  95|         parts = polygons(g.intersection(inner))
  96|         if not parts:
  97|             return None
  98|         return parts[0] if len(parts) == 1 else shapely.MultiPolygon(parts)
  99| 
 100|     cls = np.zeros((N, N), dtype=np.uint8)
 101|     level = np.full((N, N), np.nan)
 102|     cls[v33["ocean"]] = 1
 103|     level[v33["ocean"]] = SEA_LEVEL
 104| 
 105|     # V29 surface levels (lakes and river bands) on the vertex grid.
 106|     lakes = []
 107|     for f in contour:
 108|         if not f["properties"]["body"].startswith("lake"):
 109|             continue
 110|         g = clip_geom(shape(f["geometry"]), "lakes", drop=True)
 111|         if g is not None:
 112|             lakes.append((g, f["properties"]["level_m"]))
 113|     bands = [(shape(f["geometry"]), f["properties"]["level_m"]) for f in contour if f["properties"]["body"].startswith("river")]
 114|     lake_lv = raster_vertices([g for g, _ in lakes], values=[v for _, v in lakes], dtype="float32")
 115|     band_lv = raster_vertices([g for g, _ in bands], values=[v for _, v in bands], dtype="float32", all_touched=True)
 116|     lake_m = raster_vertices([g for g, _ in lakes]).astype(bool)
 117|     cls[lake_m & (cls == 0)] = 2
 118|     level[cls == 2] = lake_lv[cls == 2]
 119| 
 120|     def put(geoms, code, lv):
 121|         m = raster_vertices(geoms).astype(bool) & ~np.isin(cls, (1, 2))
 122|         cls[m] = code
 123|         level[m] = lv[m] if isinstance(lv, np.ndarray) else lv
 124|         return m
 125| 
 126|     # Navigable: V29 band levels, extended to the new banks by nearest band vertex.
 127|     nav = [shape(f["geometry"]) for f in bodies if f["properties"]["class"] == "navigable"]
 128|     known = band_lv > 0
 129|     _, idx = distance_transform_edt(~known, return_indices=True)
 130|     nav_lv = band_lv[idx[0], idx[1]].astype(float)
 131|     put(nav, 3, nav_lv)
 132|     put([shape(f["geometry"]) for f in bodies if f["properties"]["class"].startswith("delta")], 4, SEA_LEVEL)
 133| 
 134|     # Rivers and streams: nearest profile sample.
 135|     def profile_levels(feats, code, geoms=None):
 136|         pts, lv = [], []
 137|         if geoms is None:
 138|             geoms = [shape(f["geometry"]) for f in feats]
 139|         for f in feats:
 140|             key = f["properties"].get("id")
 141|             if key and key in prof.files:
 142|                 a = prof[key]
 143|                 pts.append(a[:, 1:3])
 144|                 lv.append(a[:, 4])
 145|         # Rivers of 8-20 m and streams of 3-6 m are narrower than two 6 m cells: every touched vertex joins the
 146|         # groove so the bed stays continuous; the visible water keeps the design width in phase 3.
 147|         m = raster_vertices(geoms, all_touched=True).astype(bool) & ~np.isin(cls, (1, 2, 3, 4))
 148|         if pts:
 149|             tree = cKDTree(np.vstack(pts))
 150|             x, z = grid_xz()
 151|             _, j = tree.query(np.column_stack([x[m], z[m]]))
 152|             vals = np.concatenate(lv)[j]
 153|         else:
 154|             vals = np.nan
 155|         cls[m] = code
 156|         level[m] = vals
 157|         return m
 158| 
 159|     river_feats = [f for f in bodies if f["properties"]["class"] == "river"]
 160|     river_geoms = []
 161|     for f in river_feats:
 162|         g = clip_geom(shape(f["geometry"]), "rivers")
 163|         if g is not None:
 164|             river_geoms.append(g)
 165|     profile_levels(river_feats, 5, geoms=river_geoms)
 166|     stream_geoms = []
 167|     for f in streams:
 168|         g = clip_geom(shape(f["geometry"]), "streams")
 169|         if g is not None:
 170|             stream_geoms.append(g)
 171|     profile_levels(streams, 6, geoms=stream_geoms)
 172|     ponds = []
 173|     for f in bodies:
 174|         if f["properties"]["class"] != "pond":
 175|             continue
 176|         g = clip_geom(shape(f["geometry"]), "ponds", drop=True)
 177|         if g is not None:
 178|             ponds.append((f, g))
 179|     pm = raster_vertices([g for _, g in ponds], values=[f["properties"]["level_m"] for f, _ in ponds], dtype="float32")
 180|     pmask = raster_vertices([g for _, g in ponds]).astype(bool) & (cls == 0)
 181|     cls[pmask] = 7
 182|     level[pmask] = pm[pmask]
 183| 
 184|     # Smooth shores: signed distance to the union of the inland outlines, and centre-line grooves.
 185|     other_geoms = [shape(f["geometry"]) for f in bodies if f["properties"]["class"] not in ("navigable", "pond", "river")]
 186|     inland = [g for g, _ in lakes] + nav + river_geoms + other_geoms + stream_geoms + [g for _, g in ponds]
 187|     segs = []
 188|     for g in inland:
 189|         for part in (g.geoms if hasattr(g, "geoms") else [g]):
 190|             for ring in [part.exterior] + list(part.interiors):
 191|                 xy = np.asarray(ring.coords)
 192|                 segs.append(np.stack([xy[:-1], xy[1:]], axis=1))
 193|     segs = np.concatenate(segs)
 194|     tree = shapely.STRtree(shapely.linestrings(segs))
 195|     inside_poly = raster_vertices(inland).astype(bool)
 196|     inland_cls = np.isin(cls, (2, 3, 4, 5, 6, 7))
 197|     near = binary_dilation(inside_poly | inland_cls, iterations=2)
 198|     x, z = grid_xz()
 199|     pts = shapely.points(x[near], z[near])
 200|     _, dist = tree.query_nearest(pts, return_distance=True, all_matches=False)
 201|     sd = np.full((N, N), np.nan, dtype=np.float32)
 202|     sd[near] = np.where(inside_poly[near], -dist, dist)
 203|     groove = np.zeros((N, N), dtype=bool)
 204|     for key in prof.files:
 205|         a = prof[key]
 206|         if not (key.startswith("river_") or key.startswith("stream_")):
 207|             continue
 208|         p = a[:, 1:3]
 209|         st = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
 210|         s = np.arange(0, st[-1] + 0.5, 1.0)
 211|         q = np.column_stack([np.interp(s, st, p[:, 0]), np.interp(s, st, p[:, 1])])
 212|         rr = np.clip(np.rint((12282 - q[:, 1]) / 6).astype(int), 0, N - 1)
 213|         cc = np.clip(np.rint(q[:, 0] / 6).astype(int), 0, N - 1)
 214|         groove[rr, cc] = True
 215|         diag = (np.abs(np.diff(rr)) == 1) & (np.abs(np.diff(cc)) == 1)
 216|         groove[rr[:-1][diag], cc[1:][diag]] = True
 217|     groove &= np.isin(cls, (5, 6))
 218|     touched_only = np.isin(cls, (5, 6)) & ~inside_poly & ~groove
 219|     cls[touched_only] = 0
 220|     level[touched_only] = np.nan
 221| 
 222|     # Smooth sea coast: 0.5 contour of the ocean mask after a 9 m Gaussian, signed distance within ~12 m.
 223|     sea0 = cls == 1
 224|     f = gaussian_filter(sea0.astype(np.float64), 1.5)
 225|     sea_new = f >= 0.5
 226|     lines = contourpy.contour_generator(z=f, line_type=contourpy.LineType.Separate).lines(0.5)
 227|     csegs = []
 228|     for ln in lines:
 229|         if len(ln) < 2:
 230|             continue
 231|         xy = np.column_stack([ln[:, 0] * 6.0, 12282.0 - ln[:, 1] * 6.0])
 232|         csegs.append(np.stack([xy[:-1], xy[1:]], axis=1))
 233|     ctree = shapely.STRtree(shapely.linestrings(np.concatenate(csegs)))
 234|     band = binary_dilation(sea_new, iterations=2) & binary_dilation(~sea_new, iterations=2)
 235|     _, cdist = ctree.query_nearest(shapely.points(x[band], z[band]), return_distance=True, all_matches=False)
 236|     sd_sea = np.full((N, N), np.nan, dtype=np.float32)
 237|     sd_sea[band] = np.where(sea_new[band], -cdist, cdist)
 238|     gained = sea_new & (cls == 0)
 239|     lost = ~sea_new & (cls == 1)
 240|     cls[gained] = 1
 241|     level[gained] = SEA_LEVEL
 242|     cls[lost] = 0
 243|     level[lost] = np.nan
 244| 
 245|     # Narva bridge zone: V29 water exactly (the builder keeps V29 heights there).
 246|     x, z = grid_xz()
 247|     zone = np.hypot(x - NARVA[0], z - NARVA[1]) <= NARVA_ZONE_M
 248|     v29_wet = v33["wet"] & ~v33["ocean"]
 249|     cls[zone & ~v33["ocean"]] = 0
 250|     level[zone & ~v33["ocean"]] = np.nan
 251|     cls[zone & v29_wet] = 3
 252|     level[zone & v29_wet] = nav_lv[zone & v29_wet]
 253|     sd[zone] = np.nan
 254|     groove[zone] = False
 255|     sd_sea[zone] = np.nan
 256| 
 257|     # Roads keep their ground: within 9 m of a graded road station, a vertex that was dry in V29 (above the high
 258|     # tide and not V29 inland water) stays land. That keeps the sea causeway and roads beside widened or new rivers;
 259|     # crossings V29 already had in the water stay water (bridge or ford reserves).
 260|     with rasterio.open(os.path.join(R, "tests", "regional_road_network_v29", "baltic_road_network_v29.asc")) as ds:
 261|         h29 = ds.read(1)
 262|     pts = []
 263|     for p in road_chains():
 264|         if len(p) < 2:
 265|             continue
 266|         st = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
 267|         s = np.arange(0, st[-1] + 0.5, 1.0)
 268|         pts.append(np.column_stack([np.interp(s, st, p[:, 0]), np.interp(s, st, p[:, 1])]))
 269|     cand = (cls > 0) & ~zone
 270|     dist_road, _ = cKDTree(np.vstack(pts)).query(np.column_stack([x[cand], z[cand]]), distance_upper_bound=9.0)
 271|     near_road = np.zeros((N, N), dtype=bool)
 272|     near_road[cand] = np.isfinite(dist_road)
 273|     v29_dry = (h29 >= 1.0) & ~(v33["wet"] & ~v33["ocean"])
 274|     keep_ground = near_road & v29_dry
 275|     allp = np.vstack(pts)
 276|     sr = np.clip(np.rint((12282 - allp[:, 1]) / 6).astype(int), 0, N - 1)
 277|     sc = np.clip(np.rint(allp[:, 0] / 6).astype(int), 0, N - 1)
 278|     causeway_st = allp[(cls[sr, sc] > 0) & v29_dry[sr, sc] & ~zone[sr, sc]]
 279|     if len(causeway_st):
 280|         d_cw, _ = cKDTree(causeway_st).query(np.column_stack([x[cand], z[cand]]), distance_upper_bound=6.5)
 281|         carriage = np.zeros((N, N), dtype=bool)
 282|         carriage[cand] = np.isfinite(d_cw)
 283|         keep_ground |= carriage
 284|     cls[keep_ground] = 0
 285|     level[keep_ground] = np.nan
 286|     sd[keep_ground] = np.nan
 287|     sd_sea[keep_ground] = np.nan
 288|     groove[keep_ground] = False
 289| 
 290|     # One plane per 6 m cell: corners of one cell must not disagree much. Standing water (lakes, ponds) higher
 291|     # than an adjacent different body by > 0.30 m gives that edge vertex to land; flowing water (navigable,
 292|     # rivers, streams) is capped at 0.25 m per 6 m towards its neighbours, lowering only, standing water fixed.
 293|     standing = np.isin(cls, (2, 7)) & ~zone
 294|     flowing = np.isin(cls, (3, 5, 6)) & ~zone
 295|     wetv = (cls > 0) & np.isfinite(level)
 296|     lvp = np.pad(np.where(wetv, level, np.nan), 1, constant_values=np.nan)
 297|     sep = np.zeros((N, N), dtype=bool)
 298|     for dr in (-1, 0, 1):
 299|         for dc in (-1, 0, 1):
 300|             if dr == 0 and dc == 0:
 301|                 continue
 302|             nb = lvp[1 + dr:1 + dr + N, 1 + dc:1 + dc + N]
 303|             with np.errstate(invalid="ignore"):
 304|                 sep |= standing & np.isfinite(nb) & (level - nb > 0.30)
 305|     cls[sep] = 0
 306|     level[sep] = np.nan
 307|     cap = 0.25
 308|     for it in range(4000):
 309|         cur = np.pad(np.where((cls > 0) & np.isfinite(level), level, np.inf), 1, constant_values=np.inf)
 310|         low = np.full((N, N), np.inf)
 311|         for dr in (-1, 0, 1):
 312|             for dc in (-1, 0, 1):
 313|                 if dr == 0 and dc == 0:
 314|                     continue
 315|                 low = np.minimum(low, cur[1 + dr:1 + dr + N, 1 + dc:1 + dc + N] + cap * (1.4142 if dr and dc else 1.0))
 316|         flowing = np.isin(cls, (3, 5, 6)) & ~zone
 317|         new = np.where(flowing & np.isfinite(low), np.minimum(level, low), level)
 318|         changed = flowing & np.isfinite(level) & (new < level - 1e-6)
 319|         level = np.where(changed, new, level)
 320|         if not changed.any():
 321|             break
 322|     cell_stats = {"standing_edge_to_land": int(sep.sum()), "level_cap_iterations": it + 1,
 323|                   "road_ground_kept": int(keep_ground.sum()), "causeway_stations": int(len(causeway_st))}
 324| 
 325|     # Rivers drawn only as polygons have no profile: give them their own low-bank level later in the builder.
 326|     missing = (cls >= 3) & ~np.isfinite(level)
 327|     inside = cls > 0
 328|     dist_bank = distance_transform_edt(inside) * 6.0          # metres from the nearest land vertex, inside water
 329|     dist_water = distance_transform_edt(~inside) * 6.0        # metres from the nearest water vertex, on land
 330|     _, nidx = distance_transform_edt(~inside, return_indices=True)
 331|     level_near = level[nidx[0], nidx[1]]                      # level of the nearest water vertex, for banks
 332| 
 333|     # V29 water that the new design no longer uses. Only "wet" is water: Codex's bank_support is 6.8 km2 of dry
 334|     # land around the water (median 2.89 m) and fairway_support lies inside wet.
 335|     v29_wet = v33["wet"] & ~v33["ocean"]
 336|     excess = v29_wet & ~binary_dilation(inside, iterations=1)
 337|     stats = {"vertices": {name: int((cls == code).sum()) for code, name in enumerate(
 338|         ["land", "sea", "lake", "navigable", "delta", "river", "stream", "pond"])},
 339|         "missing_level_vertices": int(missing.sum()), "excess_v29_water_vertices": int(excess.sum()),
 340|         "shore_shaped_vertices": int(np.isfinite(sd).sum()), "groove_vertices": int(groove.sum()),
 341|         "touched_reclassified_land": int(touched_only.sum()), "coast_shaped_vertices": int(np.isfinite(sd_sea).sum()),
 342|         "coast_gained_sea": int(gained.sum()), "coast_lost_sea": int(lost.sum()), **cell_stats}
 343|     if BORDER_MARGIN > 0 or DROP_BORDER_KM2 > 0:
 344|         edge = (x < BORDER_MARGIN) | (x > 12282.0 - BORDER_MARGIN) | (z < BORDER_MARGIN) | (z > 12282.0 - BORDER_MARGIN)
 345|         counts["border_inland_vertices"] = int((edge & np.isin(cls, (2, 5, 6, 7))).sum())
 346|         stats.update(counts)
 347|     np.savez_compressed(os.path.join(OUT, "water_v30.npz"), cls=cls, level=level.astype("float32"),
 348|                         dist_bank=dist_bank.astype("float32"), dist_water=dist_water.astype("float32"),
 349|                         level_near=level_near.astype("float32"), excess=excess, missing=missing,
 350|                         sd=sd, groove=groove, sd_sea=sd_sea)
 351|     print(json.dumps(stats, indent=1))
 352| 
 353| 
 354| if __name__ == "__main__":
 355|     main()
 356| 
```

# Reminder
Task E1: --round-river-ends R in tools/terrain/build_v30_water.py (rivers only, local opening near each border cut,
r = min(R, 0.45 x cut length), area guard 1.0 r^2 with halving, counts key "rivers_ends_rounded" only when R > 0,
--selftest with the three cases). Defaults byte-identical. Write the whole file now.

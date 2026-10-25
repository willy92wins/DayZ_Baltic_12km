IMPORTANT PROCESS NOTE: write the complete files FIRST, in one pass, then stop. Keep internal deliberation focused.
The receiver re-runs every changed tool with its DEFAULTS and compares sha256 against archived outputs: with the
defaults, terrain/water/image outputs must be byte-identical to today's. Change nothing that the task does not ask for.
Code and comments in English; keep the style of the surrounding code (comment density, naming, idiom).
Output: one fenced block per changed or new file, each preceded by the line `FILE: <repo-relative path>`, whole file.
Coordinates: game metres, x east, z north; the vertex grid is N = 2048 vertices every 6 m, row r at z = 12282 - 6r,
column c at x = 6c (tools/terrain/v30_common.py).

# Task D4: contour lakes path and a border keep rule
1. tools/terrain/build_v30_water.py. It parses --border-margin and --drop-border-water-km2 from sys.argv[3:] by hand
   (lines 35-41); parse two more options the same way, without argparse:
   - `--contour PATH`: the contour-v2 lakes file read in main() (the json.load of
     os.path.join(R, "evidence", "regional-foundation-v1", "water-surfaces-contour-v2.geojson")). Default: that path.
   - `--border-keep-m K` (metres, default 0 = today's behaviour): with --border-margin M > 0 and K > 0, a contour lake or a
     pond whose ORIGINAL polygon stays at least K m from the map edge (min(x0, z0, 12282 - x1, 12282 - z1) over its
     bounds is >= K) is kept whole: neither dropped nor clipped, although it reaches into the M band. Count them as
     "lakes_kept_whole" and "ponds_kept_whole" in `counts` (the stats only print counts when an option is non-default,
     keep that). Rivers and streams are not affected by K. Put the check inside clip_geom (lines 62-79) so all users
     share it; clip_geom gets the kind ("lakes", "ponds", "rivers", "streams") already.
   - Update the docstring (the border rule paragraph and the Usage line).
2. tools/terrain/polish_luga_head_v30.py: CONTOUR (line 32) stays as the default; add `--contour PATH` (default
   CONTOUR) to the argparse in main() and read it at line 104 instead of CONTOUR. If the report records inputs or
   params, record the path actually used.

# The files to change (full listings)

### tools/terrain/build_v30_water.py (full file, 337 lines)
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
  15| Self-check: with --border-margin 60 no vertex of classes 2, 5, 6, 7 lies within 60 m of the map border (x or z
  16| below 60 or above 12222); the printed stats count them as border_inland_vertices, with the clipped and dropped bodies.
  17| Usage: build_v30_water.py <design dir> <out dir> [--border-margin M] [--drop-border-water-km2 A]
  18| """
  19| import json
  20| import os
  21| import sys
  22| 
  23| import numpy as np
  24| import contourpy
  25| from scipy.ndimage import binary_dilation, distance_transform_edt, gaussian_filter
  26| from scipy.spatial import cKDTree
  27| import shapely
  28| from shapely.geometry import shape
  29| 
  30| sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
  31| from v30_common import N, R, grid_xz, raster_vertices  # noqa: E402
  32| from verify_roads_v30 import road_chains  # noqa: E402
  33| import rasterio  # noqa: E402
  34| 
  35| W_DIR, OUT = sys.argv[1], sys.argv[2]
  36| BORDER_MARGIN, DROP_BORDER_KM2 = 0.0, 0.0
  37| for _i, _a in enumerate(sys.argv[3:]):
  38|     if _a == "--border-margin":
  39|         BORDER_MARGIN = float(sys.argv[4 + _i])
  40|     elif _a == "--drop-border-water-km2":
  41|         DROP_BORDER_KM2 = float(sys.argv[4 + _i])
  42| SEA_LEVEL = 0.75
  43| NARVA = (2417.1428225906, 6889.8850822322)
  44| NARVA_ZONE_M = 600.0
  45| STREAM_TIER = 2500
  46| 
  47| 
  48| def main():
  49|     v33 = np.load(os.path.join(R, "tests", "regional_outline_smoothing_v33", "reference.npz"))
  50|     contour = json.load(open(os.path.join(R, "evidence", "regional-foundation-v1", "water-surfaces-contour-v2.geojson"), encoding="utf-8"))["features"]
  51|     bodies = json.load(open(os.path.join(W_DIR, "water_v3.geojson"), encoding="utf-8"))["features"]
  52|     streams = [f for f in json.load(open(os.path.join(W_DIR, "streams_candidates.geojson"), encoding="utf-8"))["features"]
  53|                if f["properties"]["tier_m"] >= STREAM_TIER]
  54|     prof = np.load(os.path.join(W_DIR, "profiles.npz"))
  55| 
  56|     clip = BORDER_MARGIN > 0
  57|     counts = {"lakes_clipped": 0, "lakes_dropped": 0, "ponds_clipped": 0, "ponds_dropped": 0,
  58|               "rivers_clipped": 0, "streams_clipped": 0}
  59|     inner = shapely.box(BORDER_MARGIN, BORDER_MARGIN, 12282.0 - BORDER_MARGIN, 12282.0 - BORDER_MARGIN)
  60|     border_band = shapely.box(0.0, 0.0, 12282.0, 12282.0).difference(inner)
  61| 
  62|     def polygons(g):
  63|         if g.geom_type == "Polygon":
  64|             return [g] if g.area > 0 else []
  65|         return [p for part in getattr(g, "geoms", []) for p in polygons(part)]
  66| 
  67|     def clip_geom(g, kind, drop=False):
  68|         # Border rule for one inland geometry: small border water is dropped, the rest is clipped to the inner box
  69|         # (polygonal parts only, so the shore rings below stay rings). Geometries inside the box are kept as they are.
  70|         if not clip or g.within(inner):
  71|             return g
  72|         if drop and DROP_BORDER_KM2 > 0 and g.intersects(border_band) and g.area < DROP_BORDER_KM2 * 1e6:
  73|             counts[kind + "_dropped"] += 1
  74|             return None
  75|         counts[kind + "_clipped"] += 1
  76|         parts = polygons(g.intersection(inner))
  77|         if not parts:
  78|             return None
  79|         return parts[0] if len(parts) == 1 else shapely.MultiPolygon(parts)
  80| 
  81|     cls = np.zeros((N, N), dtype=np.uint8)
  82|     level = np.full((N, N), np.nan)
  83|     cls[v33["ocean"]] = 1
  84|     level[v33["ocean"]] = SEA_LEVEL
  85| 
  86|     # V29 surface levels (lakes and river bands) on the vertex grid.
  87|     lakes = []
  88|     for f in contour:
  89|         if not f["properties"]["body"].startswith("lake"):
  90|             continue
  91|         g = clip_geom(shape(f["geometry"]), "lakes", drop=True)
  92|         if g is not None:
  93|             lakes.append((g, f["properties"]["level_m"]))
  94|     bands = [(shape(f["geometry"]), f["properties"]["level_m"]) for f in contour if f["properties"]["body"].startswith("river")]
  95|     lake_lv = raster_vertices([g for g, _ in lakes], values=[v for _, v in lakes], dtype="float32")
  96|     band_lv = raster_vertices([g for g, _ in bands], values=[v for _, v in bands], dtype="float32", all_touched=True)
  97|     lake_m = raster_vertices([g for g, _ in lakes]).astype(bool)
  98|     cls[lake_m & (cls == 0)] = 2
  99|     level[cls == 2] = lake_lv[cls == 2]
 100| 
 101|     def put(geoms, code, lv):
 102|         m = raster_vertices(geoms).astype(bool) & ~np.isin(cls, (1, 2))
 103|         cls[m] = code
 104|         level[m] = lv[m] if isinstance(lv, np.ndarray) else lv
 105|         return m
 106| 
 107|     # Navigable: V29 band levels, extended to the new banks by nearest band vertex.
 108|     nav = [shape(f["geometry"]) for f in bodies if f["properties"]["class"] == "navigable"]
 109|     known = band_lv > 0
 110|     _, idx = distance_transform_edt(~known, return_indices=True)
 111|     nav_lv = band_lv[idx[0], idx[1]].astype(float)
 112|     put(nav, 3, nav_lv)
 113|     put([shape(f["geometry"]) for f in bodies if f["properties"]["class"].startswith("delta")], 4, SEA_LEVEL)
 114| 
 115|     # Rivers and streams: nearest profile sample.
 116|     def profile_levels(feats, code, geoms=None):
 117|         pts, lv = [], []
 118|         if geoms is None:
 119|             geoms = [shape(f["geometry"]) for f in feats]
 120|         for f in feats:
 121|             key = f["properties"].get("id")
 122|             if key and key in prof.files:
 123|                 a = prof[key]
 124|                 pts.append(a[:, 1:3])
 125|                 lv.append(a[:, 4])
 126|         # Rivers of 8-20 m and streams of 3-6 m are narrower than two 6 m cells: every touched vertex joins the
 127|         # groove so the bed stays continuous; the visible water keeps the design width in phase 3.
 128|         m = raster_vertices(geoms, all_touched=True).astype(bool) & ~np.isin(cls, (1, 2, 3, 4))
 129|         if pts:
 130|             tree = cKDTree(np.vstack(pts))
 131|             x, z = grid_xz()
 132|             _, j = tree.query(np.column_stack([x[m], z[m]]))
 133|             vals = np.concatenate(lv)[j]
 134|         else:
 135|             vals = np.nan
 136|         cls[m] = code
 137|         level[m] = vals
 138|         return m
 139| 
 140|     river_feats = [f for f in bodies if f["properties"]["class"] == "river"]
 141|     river_geoms = []
 142|     for f in river_feats:
 143|         g = clip_geom(shape(f["geometry"]), "rivers")
 144|         if g is not None:
 145|             river_geoms.append(g)
 146|     profile_levels(river_feats, 5, geoms=river_geoms)
 147|     stream_geoms = []
 148|     for f in streams:
 149|         g = clip_geom(shape(f["geometry"]), "streams")
 150|         if g is not None:
 151|             stream_geoms.append(g)
 152|     profile_levels(streams, 6, geoms=stream_geoms)
 153|     ponds = []
 154|     for f in bodies:
 155|         if f["properties"]["class"] != "pond":
 156|             continue
 157|         g = clip_geom(shape(f["geometry"]), "ponds", drop=True)
 158|         if g is not None:
 159|             ponds.append((f, g))
 160|     pm = raster_vertices([g for _, g in ponds], values=[f["properties"]["level_m"] for f, _ in ponds], dtype="float32")
 161|     pmask = raster_vertices([g for _, g in ponds]).astype(bool) & (cls == 0)
 162|     cls[pmask] = 7
 163|     level[pmask] = pm[pmask]
 164| 
 165|     # Smooth shores: signed distance to the union of the inland outlines, and centre-line grooves.
 166|     other_geoms = [shape(f["geometry"]) for f in bodies if f["properties"]["class"] not in ("navigable", "pond", "river")]
 167|     inland = [g for g, _ in lakes] + nav + river_geoms + other_geoms + stream_geoms + [g for _, g in ponds]
 168|     segs = []
 169|     for g in inland:
 170|         for part in (g.geoms if hasattr(g, "geoms") else [g]):
 171|             for ring in [part.exterior] + list(part.interiors):
 172|                 xy = np.asarray(ring.coords)
 173|                 segs.append(np.stack([xy[:-1], xy[1:]], axis=1))
 174|     segs = np.concatenate(segs)
 175|     tree = shapely.STRtree(shapely.linestrings(segs))
 176|     inside_poly = raster_vertices(inland).astype(bool)
 177|     inland_cls = np.isin(cls, (2, 3, 4, 5, 6, 7))
 178|     near = binary_dilation(inside_poly | inland_cls, iterations=2)
 179|     x, z = grid_xz()
 180|     pts = shapely.points(x[near], z[near])
 181|     _, dist = tree.query_nearest(pts, return_distance=True, all_matches=False)
 182|     sd = np.full((N, N), np.nan, dtype=np.float32)
 183|     sd[near] = np.where(inside_poly[near], -dist, dist)
 184|     groove = np.zeros((N, N), dtype=bool)
 185|     for key in prof.files:
 186|         a = prof[key]
 187|         if not (key.startswith("river_") or key.startswith("stream_")):
 188|             continue
 189|         p = a[:, 1:3]
 190|         st = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
 191|         s = np.arange(0, st[-1] + 0.5, 1.0)
 192|         q = np.column_stack([np.interp(s, st, p[:, 0]), np.interp(s, st, p[:, 1])])
 193|         rr = np.clip(np.rint((12282 - q[:, 1]) / 6).astype(int), 0, N - 1)
 194|         cc = np.clip(np.rint(q[:, 0] / 6).astype(int), 0, N - 1)
 195|         groove[rr, cc] = True
 196|         diag = (np.abs(np.diff(rr)) == 1) & (np.abs(np.diff(cc)) == 1)
 197|         groove[rr[:-1][diag], cc[1:][diag]] = True
 198|     groove &= np.isin(cls, (5, 6))
 199|     touched_only = np.isin(cls, (5, 6)) & ~inside_poly & ~groove
 200|     cls[touched_only] = 0
 201|     level[touched_only] = np.nan
 202| 
 203|     # Smooth sea coast: 0.5 contour of the ocean mask after a 9 m Gaussian, signed distance within ~12 m.
 204|     sea0 = cls == 1
 205|     f = gaussian_filter(sea0.astype(np.float64), 1.5)
 206|     sea_new = f >= 0.5
 207|     lines = contourpy.contour_generator(z=f, line_type=contourpy.LineType.Separate).lines(0.5)
 208|     csegs = []
 209|     for ln in lines:
 210|         if len(ln) < 2:
 211|             continue
 212|         xy = np.column_stack([ln[:, 0] * 6.0, 12282.0 - ln[:, 1] * 6.0])
 213|         csegs.append(np.stack([xy[:-1], xy[1:]], axis=1))
 214|     ctree = shapely.STRtree(shapely.linestrings(np.concatenate(csegs)))
 215|     band = binary_dilation(sea_new, iterations=2) & binary_dilation(~sea_new, iterations=2)
 216|     _, cdist = ctree.query_nearest(shapely.points(x[band], z[band]), return_distance=True, all_matches=False)
 217|     sd_sea = np.full((N, N), np.nan, dtype=np.float32)
 218|     sd_sea[band] = np.where(sea_new[band], -cdist, cdist)
 219|     gained = sea_new & (cls == 0)
 220|     lost = ~sea_new & (cls == 1)
 221|     cls[gained] = 1
 222|     level[gained] = SEA_LEVEL
 223|     cls[lost] = 0
 224|     level[lost] = np.nan
 225| 
 226|     # Narva bridge zone: V29 water exactly (the builder keeps V29 heights there).
 227|     x, z = grid_xz()
 228|     zone = np.hypot(x - NARVA[0], z - NARVA[1]) <= NARVA_ZONE_M
 229|     v29_wet = v33["wet"] & ~v33["ocean"]
 230|     cls[zone & ~v33["ocean"]] = 0
 231|     level[zone & ~v33["ocean"]] = np.nan
 232|     cls[zone & v29_wet] = 3
 233|     level[zone & v29_wet] = nav_lv[zone & v29_wet]
 234|     sd[zone] = np.nan
 235|     groove[zone] = False
 236|     sd_sea[zone] = np.nan
 237| 
 238|     # Roads keep their ground: within 9 m of a graded road station, a vertex that was dry in V29 (above the high
 239|     # tide and not V29 inland water) stays land. That keeps the sea causeway and roads beside widened or new rivers;
 240|     # crossings V29 already had in the water stay water (bridge or ford reserves).
 241|     with rasterio.open(os.path.join(R, "tests", "regional_road_network_v29", "baltic_road_network_v29.asc")) as ds:
 242|         h29 = ds.read(1)
 243|     pts = []
 244|     for p in road_chains():
 245|         if len(p) < 2:
 246|             continue
 247|         st = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
 248|         s = np.arange(0, st[-1] + 0.5, 1.0)
 249|         pts.append(np.column_stack([np.interp(s, st, p[:, 0]), np.interp(s, st, p[:, 1])]))
 250|     cand = (cls > 0) & ~zone
 251|     dist_road, _ = cKDTree(np.vstack(pts)).query(np.column_stack([x[cand], z[cand]]), distance_upper_bound=9.0)
 252|     near_road = np.zeros((N, N), dtype=bool)
 253|     near_road[cand] = np.isfinite(dist_road)
 254|     v29_dry = (h29 >= 1.0) & ~(v33["wet"] & ~v33["ocean"])
 255|     keep_ground = near_road & v29_dry
 256|     allp = np.vstack(pts)
 257|     sr = np.clip(np.rint((12282 - allp[:, 1]) / 6).astype(int), 0, N - 1)
 258|     sc = np.clip(np.rint(allp[:, 0] / 6).astype(int), 0, N - 1)
 259|     causeway_st = allp[(cls[sr, sc] > 0) & v29_dry[sr, sc] & ~zone[sr, sc]]
 260|     if len(causeway_st):
 261|         d_cw, _ = cKDTree(causeway_st).query(np.column_stack([x[cand], z[cand]]), distance_upper_bound=6.5)
 262|         carriage = np.zeros((N, N), dtype=bool)
 263|         carriage[cand] = np.isfinite(d_cw)
 264|         keep_ground |= carriage
 265|     cls[keep_ground] = 0
 266|     level[keep_ground] = np.nan
 267|     sd[keep_ground] = np.nan
 268|     sd_sea[keep_ground] = np.nan
 269|     groove[keep_ground] = False
 270| 
 271|     # One plane per 6 m cell: corners of one cell must not disagree much. Standing water (lakes, ponds) higher
 272|     # than an adjacent different body by > 0.30 m gives that edge vertex to land; flowing water (navigable,
 273|     # rivers, streams) is capped at 0.25 m per 6 m towards its neighbours, lowering only, standing water fixed.
 274|     standing = np.isin(cls, (2, 7)) & ~zone
 275|     flowing = np.isin(cls, (3, 5, 6)) & ~zone
 276|     wetv = (cls > 0) & np.isfinite(level)
 277|     lvp = np.pad(np.where(wetv, level, np.nan), 1, constant_values=np.nan)
 278|     sep = np.zeros((N, N), dtype=bool)
 279|     for dr in (-1, 0, 1):
 280|         for dc in (-1, 0, 1):
 281|             if dr == 0 and dc == 0:
 282|                 continue
 283|             nb = lvp[1 + dr:1 + dr + N, 1 + dc:1 + dc + N]
 284|             with np.errstate(invalid="ignore"):
 285|                 sep |= standing & np.isfinite(nb) & (level - nb > 0.30)
 286|     cls[sep] = 0
 287|     level[sep] = np.nan
 288|     cap = 0.25
 289|     for it in range(4000):
 290|         cur = np.pad(np.where((cls > 0) & np.isfinite(level), level, np.inf), 1, constant_values=np.inf)
 291|         low = np.full((N, N), np.inf)
 292|         for dr in (-1, 0, 1):
 293|             for dc in (-1, 0, 1):
 294|                 if dr == 0 and dc == 0:
 295|                     continue
 296|                 low = np.minimum(low, cur[1 + dr:1 + dr + N, 1 + dc:1 + dc + N] + cap * (1.4142 if dr and dc else 1.0))
 297|         flowing = np.isin(cls, (3, 5, 6)) & ~zone
 298|         new = np.where(flowing & np.isfinite(low), np.minimum(level, low), level)
 299|         changed = flowing & np.isfinite(level) & (new < level - 1e-6)
 300|         level = np.where(changed, new, level)
 301|         if not changed.any():
 302|             break
 303|     cell_stats = {"standing_edge_to_land": int(sep.sum()), "level_cap_iterations": it + 1,
 304|                   "road_ground_kept": int(keep_ground.sum()), "causeway_stations": int(len(causeway_st))}
 305| 
 306|     # Rivers drawn only as polygons have no profile: give them their own low-bank level later in the builder.
 307|     missing = (cls >= 3) & ~np.isfinite(level)
 308|     inside = cls > 0
 309|     dist_bank = distance_transform_edt(inside) * 6.0          # metres from the nearest land vertex, inside water
 310|     dist_water = distance_transform_edt(~inside) * 6.0        # metres from the nearest water vertex, on land
 311|     _, nidx = distance_transform_edt(~inside, return_indices=True)
 312|     level_near = level[nidx[0], nidx[1]]                      # level of the nearest water vertex, for banks
 313| 
 314|     # V29 water that the new design no longer uses. Only "wet" is water: Codex's bank_support is 6.8 km2 of dry
 315|     # land around the water (median 2.89 m) and fairway_support lies inside wet.
 316|     v29_wet = v33["wet"] & ~v33["ocean"]
 317|     excess = v29_wet & ~binary_dilation(inside, iterations=1)
 318|     stats = {"vertices": {name: int((cls == code).sum()) for code, name in enumerate(
 319|         ["land", "sea", "lake", "navigable", "delta", "river", "stream", "pond"])},
 320|         "missing_level_vertices": int(missing.sum()), "excess_v29_water_vertices": int(excess.sum()),
 321|         "shore_shaped_vertices": int(np.isfinite(sd).sum()), "groove_vertices": int(groove.sum()),
 322|         "touched_reclassified_land": int(touched_only.sum()), "coast_shaped_vertices": int(np.isfinite(sd_sea).sum()),
 323|         "coast_gained_sea": int(gained.sum()), "coast_lost_sea": int(lost.sum()), **cell_stats}
 324|     if BORDER_MARGIN > 0 or DROP_BORDER_KM2 > 0:
 325|         edge = (x < BORDER_MARGIN) | (x > 12282.0 - BORDER_MARGIN) | (z < BORDER_MARGIN) | (z > 12282.0 - BORDER_MARGIN)
 326|         counts["border_inland_vertices"] = int((edge & np.isin(cls, (2, 5, 6, 7))).sum())
 327|         stats.update(counts)
 328|     np.savez_compressed(os.path.join(OUT, "water_v30.npz"), cls=cls, level=level.astype("float32"),
 329|                         dist_bank=dist_bank.astype("float32"), dist_water=dist_water.astype("float32"),
 330|                         level_near=level_near.astype("float32"), excess=excess, missing=missing,
 331|                         sd=sd, groove=groove, sd_sea=sd_sea)
 332|     print(json.dumps(stats, indent=1))
 333| 
 334| 
 335| if __name__ == "__main__":
 336|     main()
 337| 
```

### tools/terrain/polish_luga_head_v30.py (full file, 280 lines)
```python
   1| """Luga head polish (Guillermo, 04-10): the navigable Luga ends 140 m short of lake_014 and its last stretch steps
   2| down because ponds touch it; the contour-v2 lakes round it are rectangles. Inside --box:
   3| 1. Ponds 8-adjacent to navigable water whose level differs by more than 0.30 m become land, and the design pond the
   4|    connection replaces (the narrow strip the river end runs into) goes entirely. Navigable levels return to the
   5|    builder's band levels (nav_lv): the 0.25 m per 6 m cap had lowered them towards those ponds.
   6| 2. Connection channel: --channel polyline (Chaikin-smoothed), --channel-width wide, navigable class, level in a ramp
   7|    from the river level at the axis end to the lake level, bed at least --bed-depth below the water.
   8| 3. Contour-v2 lakes with their representative point in the box: straight-sided outlines lose their corners (opening by
   9|    r = min(--round-r, 0.8 x the inscribed radius)), stepped ones are Chaikin-smoothed; a wet vertex more than
  10|    --outside-tol outside the new outline becomes land when it lies on a lake bed and touches no other water.
  11| 4. Banks as the builder makes them: land within 8.5 m of water at least 0.35 m above the nearest level and above the
  12|    planes of the cells round it; land never below 1.40 m.
  13| 5. Signed distance to the design outline (build_v30_water.py rule: nearest segment of every inland outline, sign by
  14|    vertex rasterisation) recomputed in the box with the rounded lakes and the channel, after checking that the same
  15|    code reproduces the base field there with the original outlines.
  16| Usage: polish_luga_head_v30.py --terrain IN.npz --sd-base SD.npz --out OUTDIR [--box xmin,zmin,xmax,zmax] ..."""
  17| import argparse
  18| import hashlib
  19| import json
  20| import sys
  21| from pathlib import Path
  22| 
  23| import numpy as np
  24| import shapely
  25| from scipy.ndimage import binary_dilation, distance_transform_edt
  26| from shapely.geometry import LineString, shape
  27| 
  28| sys.path.insert(0, str(Path(__file__).resolve().parent))
  29| from v30_common import N, R, cell_planes, grid_xz, raster_vertices, vertex_plane_bounds  # noqa: E402
  30| 
  31| W_DIR = Path(R) / 'tests' / 'water_v3'
  32| CONTOUR = Path(R) / 'evidence' / 'regional-foundation-v1' / 'water-surfaces-contour-v2.geojson'
  33| STREAM_TIER = 2500
  34| BANK_RADIUS, BANK_MARGIN, DRY_FLOOR, SEPARATION = 8.5, 0.35, 1.4, 0.30
  35| # River end inside the navigable polygon, north along the replaced pond strip, across the 3.0 m flat to lake_014.
  36| CHANNEL = '10530,4150;10531,4176;10525,4205;10524,4248;10540,4285;10580,4310;10603,4338'
  37| 
  38| 
  39| def sha(p):
  40|     return hashlib.sha256(Path(p).read_bytes()).hexdigest()
  41| 
  42| 
  43| def chaikin(pts, rounds=3):
  44|     for _ in range(rounds):
  45|         p = np.asarray(pts)
  46|         q, r = 0.75 * p[:-1] + 0.25 * p[1:], 0.25 * p[:-1] + 0.75 * p[1:]
  47|         pts = np.vstack([p[:1], np.column_stack([q, r]).reshape(-1, 2), p[-1:]])
  48|     return pts
  49| 
  50| 
  51| def chaikin_ring(xy, rounds=3):
  52|     p = np.asarray(xy)[:-1]
  53|     for _ in range(rounds):
  54|         q = np.roll(p, -1, axis=0)
  55|         p = np.column_stack([0.75 * p + 0.25 * q, 0.25 * p + 0.75 * q]).reshape(-1, 2)
  56|     return np.vstack([p, p[:1]])
  57| 
  58| 
  59| def signed_distance(polys, pts_x, pts_z, inside):
  60|     segs = []
  61|     for g in polys:
  62|         for part in (g.geoms if hasattr(g, 'geoms') else [g]):
  63|             for ring in [part.exterior] + list(part.interiors):
  64|                 xy = np.asarray(ring.coords)
  65|                 segs.append(np.stack([xy[:-1], xy[1:]], axis=1))
  66|     tree = shapely.STRtree(shapely.linestrings(np.concatenate(segs)))
  67|     _, dist = tree.query_nearest(shapely.points(pts_x, pts_z), return_distance=True, all_matches=False)
  68|     return np.where(inside, -dist, dist)
  69| 
  70| 
  71| def main():
  72|     ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  73|     ap.add_argument('--terrain', type=Path, required=True)
  74|     ap.add_argument('--sd-base', type=Path, required=True)
  75|     ap.add_argument('--out', type=Path, required=True)
  76|     ap.add_argument('--design', type=Path, default=W_DIR)
  77|     ap.add_argument('--box', default='10150,3700,10700,4600')
  78|     ap.add_argument('--channel', default=CHANNEL)
  79|     ap.add_argument('--channel-width', type=float, default=20.0)
  80|     ap.add_argument('--bed-depth', type=float, default=0.35)
  81|     ap.add_argument('--round-r', type=float, default=8.0)
  82|     ap.add_argument('--outside-tol', type=float, default=1.5)
  83|     a = ap.parse_args()
  84|     assert not a.out.exists()
  85|     bx0, bz0, bx1, bz1 = (float(v) for v in a.box.split(','))
  86|     box = shapely.box(bx0, bz0, bx1, bz1)
  87|     t = dict(np.load(a.terrain))
  88|     cls, lev, h = t['cls'].copy(), t['level'].astype(np.float64), t['heights'].astype(np.float64)
  89|     cls0, lev0, h0 = cls.copy(), lev.copy(), h.copy()
  90|     x, z = grid_xz()
  91|     inbox = (x >= bx0) & (x <= bx1) & (z >= bz0) & (z <= bz1)
  92|     rep = {'box': a.box, 'design': str(a.design)}
  93| 
  94|     def nb8(m):
  95|         p = np.pad(m, 1)
  96|         out = np.zeros_like(m)
  97|         for dr in (-1, 0, 1):
  98|             for dc in (-1, 0, 1):
  99|                 if dr or dc:
 100|                     out |= p[1 + dr:1 + dr + N, 1 + dc:1 + dc + N]
 101|         return out
 102| 
 103|     # Design outlines, as build_v30_water.py reads them.
 104|     contour = json.load(open(CONTOUR, encoding='utf-8'))['features']
 105|     bodies = json.load(open(a.design / 'water_v3.geojson', encoding='utf-8'))['features']
 106|     streams = [f for f in json.load(open(a.design / 'streams_candidates.geojson', encoding='utf-8'))['features']
 107|                if f['properties']['tier_m'] >= STREAM_TIER]
 108|     lakes = [(f['properties']['body'], shape(f['geometry']), f['properties']['level_m']) for f in contour
 109|              if f['properties']['body'].startswith('lake')]
 110|     bands = [(shape(f['geometry']), f['properties']['level_m']) for f in contour if f['properties']['body'].startswith('river')]
 111|     nav = [shape(f['geometry']) for f in bodies if f['properties']['class'] == 'navigable']
 112|     other = [shape(f['geometry']) for f in bodies if f['properties']['class'] not in ('navigable', 'pond')]
 113|     ponds = [shape(f['geometry']) for f in bodies if f['properties']['class'] == 'pond']
 114|     stream_g = [shape(f['geometry']) for f in streams]
 115| 
 116|     # Builder band levels for navigable water (build_v30_water.py: V29 bands, nearest band vertex).
 117|     band_lv = raster_vertices([g for g, _ in bands], values=[v for _, v in bands], dtype='float32', all_touched=True)
 118|     _, idx = distance_transform_edt(~(band_lv > 0), return_indices=True)
 119|     nav_lv = band_lv[idx[0], idx[1]].astype(np.float64)
 120| 
 121|     # 2. Connection channel geometry and levels.
 122|     pts = np.array([[float(v) for v in p.split(',')] for p in a.channel.split(';')])
 123|     axis = LineString(chaikin(pts))
 124|     chan_poly = axis.buffer(a.channel_width / 2, quad_segs=16)
 125|     river_end = shapely.Point(pts[1])
 126|     s_end = axis.project(river_end)
 127|     lake_hit = [(n, g, lv) for n, g, lv in lakes if g.contains(shapely.Point(pts[-1]))]
 128|     assert len(lake_hit) == 1, 'channel must end inside exactly one lake'
 129|     lake_name, lake_g, lake_level = lake_hit[0]
 130|     s_lake = axis.project(lake_g.exterior.intersection(axis).representative_point()) if axis.intersects(lake_g.exterior) else axis.length
 131|     near_end = (cls == 3) & (np.hypot(x - pts[1][0], z - pts[1][1]) <= 20)
 132|     start_level = float(np.median(nav_lv[near_end]))
 133|     replaced_pond = [g for g in ponds if g.intersects(chan_poly) and g.intersection(chan_poly).area > 0.5 * g.area]
 134| 
 135|     # 1. Ponds that touch navigable water (or the channel) and the replaced strip become land.
 136|     chan_m = raster_vertices([chan_poly]).astype(bool) & inbox
 137|     new_chan = chan_m & ~np.isin(cls, (2, 3))
 138|     strip = raster_vertices(replaced_pond).astype(bool) & (cls == 7) & inbox if replaced_pond else np.zeros_like(chan_m)
 139|     cls[strip], lev[strip] = 0, np.nan
 140|     s_chan = np.array([axis.project(shapely.Point(px, pz)) for px, pz in zip(x[new_chan], z[new_chan])])
 141|     ramp = np.clip((s_chan - s_end) / max(s_lake - s_end, 1e-6), 0.0, 1.0)
 142|     cls[new_chan] = 3
 143|     lev[new_chan] = start_level + (lake_level - start_level) * ramp
 144|     h[new_chan] = np.minimum(h[new_chan], lev[new_chan] - a.bed_depth)
 145|     navm = (cls == 3) & inbox
 146|     restored = navm & ~new_chan & (nav_lv - lev > 1e-6)
 147|     lev[restored] = nav_lv[restored]
 148|     navlv_pad = np.pad(np.where(cls == 3, lev, np.nan), 1, constant_values=np.nan)
 149|     sep = np.zeros_like(chan_m)
 150|     for dr in (-1, 0, 1):
 151|         for dc in (-1, 0, 1):
 152|             if dr or dc:
 153|                 nb = navlv_pad[1 + dr:1 + dr + N, 1 + dc:1 + dc + N]
 154|                 with np.errstate(invalid='ignore'):
 155|                     sep |= (cls == 7) & inbox & np.isfinite(nb) & (np.abs(nb - lev) > SEPARATION)
 156|     cls[sep], lev[sep] = 0, np.nan
 157|     rep['channel'] = {'axis_m': round(axis.length, 1), 'width_m': a.channel_width, 'lake': lake_name,
 158|                       'level_start_m': round(start_level, 3), 'level_lake_m': lake_level, 'new_vertices': int(new_chan.sum()),
 159|                       'from_land': int((new_chan & (cls0 == 0)).sum()), 'from_pond': int((new_chan & (cls0 == 7)).sum()),
 160|                       'carved_vertices': int((h[new_chan] < h0[new_chan] - 1e-6).sum()),
 161|                       'carve_max_m': round(float((h0 - h)[new_chan].max()), 3) if new_chan.any() else 0.0,
 162|                       'depth_m_min_max': [round(float((lev - h)[new_chan].min()), 3), round(float((lev - h)[new_chan].max()), 3)]}
 163|     rep['navigable_levels_restored'] = {'vertices': int(restored.sum()),
 164|                                         'raise_max_m': round(float((lev - lev0)[restored].max()), 3) if restored.any() else 0.0}
 165|     rep['ponds_to_land'] = {'replaced_strip_vertices': int(strip.sum()), 'replaced_strip_polygons': len(replaced_pond),
 166|                             'separated_vertices': int(sep.sum())}
 167| 
 168|     # 3. Rounded lakes: straight-sided outlines lose their corners (opening by r, accepted when it stays one polygon
 169|     #    within 0.6 r of the original, i.e. only corners went); stepped contour outlines are Chaikin-smoothed, which
 170|     #    keeps their lobes. A wet vertex left outside goes to land only on a lake bed (not deeper than 2.05 m, the
 171|     #    builder's lake depth) and only when all its wet neighbours belong to the same lake.
 172|     sel = [(n, g, lv) for n, g, lv in lakes if box.contains(g.representative_point())]
 173|     other_wet = np.pad((cls > 0), 1)
 174|     rounded, rl = {}, {}
 175|     for name, g, level in sel:
 176|         r = min(a.round_r, 0.8 * shapely.maximum_inscribed_circle(g).length)
 177|         gr = shapely.make_valid(g.buffer(-r, quad_segs=16).buffer(r, quad_segs=16))
 178|         how = 'opening'
 179|         if gr.geom_type != 'Polygon' or g.hausdorff_distance(gr) > 0.6 * r:
 180|             gr = shapely.make_valid(shapely.Polygon(chaikin_ring(g.exterior.coords), [chaikin_ring(i.coords) for i in g.interiors]))
 181|             how = 'chaikin'
 182|         rounded[name] = gr
 183|         lw = (x >= g.bounds[0] - 6) & (x <= g.bounds[2] + 6) & (z >= g.bounds[1] - 6) & (z <= g.bounds[3] + 6)
 184|         rr, cc = np.nonzero(lw & (cls == 2) & np.isclose(lev, level, atol=1e-4))
 185|         ins = shapely.contains_xy(g, x[rr, cc], z[rr, cc])
 186|         rr, cc = rr[ins], cc[ins]
 187|         d = shapely.distance(gr, shapely.points(x[rr, cc], z[rr, cc]))
 188|         out = (d > a.outside_tol) & ~shapely.contains_xy(gr, x[rr, cc], z[rr, cc])
 189|         foreign = np.zeros(len(rr), bool)
 190|         for dr in (-1, 0, 1):
 191|             for dc in (-1, 0, 1):
 192|                 if dr or dc:
 193|                     nr, nc = rr + dr, cc + dc
 194|                     foreign |= other_wet[nr + 1, nc + 1] & ~((cls[nr, nc] == 2) & np.isclose(lev[nr, nc], level, atol=1e-4))
 195|         lakebed = h[rr, cc] >= level - 2.05
 196|         go = out & ~foreign & lakebed & inbox[rr, cc]
 197|         cls[rr[go], cc[go]], lev[rr[go], cc[go]] = 0, np.nan
 198|         rl[name] = {'level_m': level, 'method': how, 'r_m': round(r, 2), 'area_m2': [round(g.area), round(gr.area)],
 199|                     'hausdorff_m': round(g.hausdorff_distance(gr), 2), 'outside': int(out.sum()), 'to_land': int(go.sum()),
 200|                     'kept_touching_other_water': int((out & foreign).sum()), 'kept_deep_bed': int((out & ~foreign & ~lakebed).sum())}
 201|     rep['rounded_lakes'] = rl
 202| 
 203|     # 4. Banks where water changed (build_v30.py: level_near + 0.35 within 8.5 m, dry floor 1.40), and every such land
 204|     #    vertex above the planes of the cells round it (the pieces gate); untouched banks keep their finish.
 205|     water = cls > 0
 206|     changed_water = water & ((cls != cls0) | ~np.isclose(lev, lev0, equal_nan=True))
 207|     to_land = ~water & (cls0 > 0)
 208|     dist_w, nidx = distance_transform_edt(~water, sampling=6.0, return_indices=True)
 209|     near_lv = lev[nidx[0], nidx[1]]
 210|     dist_c = distance_transform_edt(~(changed_water | to_land), sampling=6.0)
 211|     _, pmax = vertex_plane_bounds(cell_planes(cls, lev, sea_cut=0.51))
 212|     land = ~water & inbox & ((dist_c <= BANK_RADIUS) | to_land)
 213|     floor = np.where(land, DRY_FLOOR, -np.inf)
 214|     floor = np.where(land & (dist_w <= BANK_RADIUS) & np.isfinite(near_lv), np.maximum(floor, near_lv + BANK_MARGIN), floor)
 215|     floor = np.where(land & np.isfinite(pmax), np.maximum(floor, pmax + 0.05), floor)
 216|     raise_m = land & (h < floor)
 217|     h[raise_m] = floor[raise_m]
 218|     rep['banks'] = {'raised_vertices': int(raise_m.sum()), 'raise_max_m': round(float((h - h0)[raise_m].max()), 3) if raise_m.any() else 0.0}
 219|     # Flowing water stays within the builder's cap towards its wet neighbours (0.25 m per 6 m).
 220|     wet_lv = np.pad(np.where(water, lev, np.inf), 1, constant_values=np.inf)
 221|     low = np.full((N, N), np.inf)
 222|     for dr in (-1, 0, 1):
 223|         for dc in (-1, 0, 1):
 224|             if dr or dc:
 225|                 low = np.minimum(low, wet_lv[1 + dr:1 + dr + N, 1 + dc:1 + dc + N] + 0.25 * (1.4142 if dr and dc else 1.0))
 226|     rep['cap_violations_in_box'] = int((np.isin(cls, (3, 5, 6)) & inbox & (lev > low + 1e-6)).sum())
 227|     stand_pad = np.pad(np.where(np.isin(cls, (2, 7)), lev, np.nan), 1, constant_values=np.nan)
 228|     gap = np.zeros_like(water)
 229|     for dr in (-1, 0, 1):
 230|         for dc in (-1, 0, 1):
 231|             if dr or dc:
 232|                 with np.errstate(invalid='ignore'):
 233|                     gap |= (cls == 3) & inbox & (np.abs(stand_pad[1 + dr:1 + dr + N, 1 + dc:1 + dc + N] - lev) > SEPARATION)
 234|     rep['navigable_next_to_standing_over_0_30m'] = int(gap.sum())
 235| 
 236|     # 5. Signed distance in the box: reproduce the base with the original outlines, then the polished ones.
 237|     sd = np.load(a.sd_base)['sd'].astype(np.float32).copy()
 238|     sd0 = sd.copy()
 239|     reach = box.buffer(200)
 240|     lake_orig = [g for _, g, _ in lakes if g.intersects(reach)]
 241|     keep = [g for g in nav + other + stream_g + ponds if g.intersects(reach)]
 242|     orig = lake_orig + keep
 243|     pol_lakes = [rounded.get(n, g) for n, g, _ in lakes if g.intersects(reach)]
 244|     pol = pol_lakes + [g for g in keep if not any(g.equals(p) for p in replaced_pond)] + [chan_poly]
 245|     win = inbox & np.isfinite(sd0)
 246|     inside_o = raster_vertices(orig).astype(bool)
 247|     rep_sd = signed_distance(orig, x[win], z[win], inside_o[win])
 248|     diff = np.abs(rep_sd - sd0[win])
 249|     rep['sd_reproduction'] = {'vertices': int(win.sum()), 'max_abs_m': round(float(diff.max()), 6),
 250|                               'over_1mm': int((diff > 1e-3).sum())}
 251|     assert rep['sd_reproduction']['over_1mm'] == 0, f"base sd not reproduced in the box: {rep['sd_reproduction']}"
 252|     near_o = binary_dilation(inside_o | np.isin(cls0, (2, 3, 4, 5, 6, 7)), iterations=2)
 253|     inside_p = raster_vertices(pol).astype(bool)
 254|     near_p = binary_dilation(inside_p | np.isin(cls, (2, 3, 4, 5, 6, 7)), iterations=2)
 255|     sup = inbox & (np.isfinite(sd0) | (near_p & ~near_o))
 256|     sd[sup] = signed_distance(pol, x[sup], z[sup], inside_p[sup]).astype(np.float32)
 257|     ch = sup & ~(np.isclose(sd, sd0, atol=1e-4) & np.isfinite(sd0))
 258|     rep['sd'] = {'support_vertices': int(sup.sum()), 'new_support': int((sup & ~np.isfinite(sd0)).sum()),
 259|                  'changed_vertices': int(ch.sum())}
 260| 
 261|     t['cls'], t['level'], t['heights'] = cls, lev.astype(np.float32), h.astype(np.float32)
 262|     if 'water' in t:
 263|         t['water'] = cls > 0
 264|     a.out.mkdir(parents=True)
 265|     np.savez_compressed(a.out / 'terrain_pilot.npz', **t)
 266|     np.savez_compressed(a.out / 'sd_polish.npz', sd=sd)
 267|     rep['changed'] = {'class': int((cls != cls0).sum()), 'level': int((~np.isclose(lev, lev0, equal_nan=True)).sum()),
 268|                       'heights': int((np.abs(h - h0) > 1e-6).sum()),
 269|                       'outside_box': int(((cls != cls0) | (np.abs(h - h0) > 1e-6) | ~np.isclose(lev, lev0, equal_nan=True))[~inbox].sum())}
 270|     rep['inputs'] = {'terrain_sha256': sha(a.terrain), 'sd_base_sha256': sha(a.sd_base)}
 271|     rep['outputs'] = {'terrain_sha256': sha(a.out / 'terrain_pilot.npz'), 'sd_sha256': sha(a.out / 'sd_polish.npz')}
 272|     rep['params'] = {'channel': a.channel, 'channel_width_m': a.channel_width, 'bed_depth_m': a.bed_depth,
 273|                      'round_r_m': a.round_r, 'outside_tol_m': a.outside_tol}
 274|     (a.out / 'report.json').write_text(json.dumps(rep, indent=1) + '\n', encoding='utf-8')
 275|     print(json.dumps(rep, indent=1))
 276| 
 277| 
 278| if __name__ == '__main__':
 279|     main()
 280| 
```

# Reminder
# Task D4: contour lakes path and a border keep rule
1. tools/terrain/build_v30_water.py. It parses --border-margin and --drop-border-water-km2 from sys.argv[3:] by hand
   (lines 35-41); parse two more options the same way, without argparse:
   - `--contour PATH`: the contour-v2 lakes file read in main() (the json.load of
     os.path.join(R, "evidence", "regional-foundation-v1", "water-surfaces-contour-v2.geojson")). Default: that path.
   - `--border-keep-m K` (metres, default 0 = today's behaviour): with --border-margin M > 0 and K > 0, a contour lake or a
     pond whose ORIGINAL polygon stays at least K m from the map edge (min(x0, z0, 12282 - x1, 12282 - z1) over its
     bounds is >= K) is kept whole: neither dropped nor clipped, although it reaches into the M band. Count them as
     "lakes_kept_whole" and "ponds_kept_whole" in `counts` (the stats only print counts when an option is non-default,
     keep that). Rivers and streams are not affected by K. Put the check inside clip_geom (lines 62-79) so all users
     share it; clip_geom gets the kind ("lakes", "ponds", "rivers", "streams") already.
   - Update the docstring (the border rule paragraph and the Usage line).
2. tools/terrain/polish_luga_head_v30.py: CONTOUR (line 32) stays as the default; add `--contour PATH` (default
   CONTOUR) to the argparse in main() and read it at line 104 instead of CONTOUR. If the report records inputs or
   params, record the path actually used.

Write the whole files now.

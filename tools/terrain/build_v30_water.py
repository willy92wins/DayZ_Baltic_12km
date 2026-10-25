"""Water rasters for terrain V30 on the vertex grid: class, level, distance to bank and the V29 water to remove.

Classes (uint8): 0 land, 1 sea, 2 kept lake, 3 navigable, 4 delta, 5 river, 6 stream, 7 pond.
Levels: sea 0.75 m; kept lakes and navigable reaches take the V29 surface levels (contour-v2 bands); rivers and
streams the nearest sample of their monotone profile; ponds their design level; delta channels the sea.
Output <out>/water_v30.npz.

Map-border rule (Guillermo, 06-10): the borders are land, as in Chernarus. --border-margin M (default 0 = today's
behaviour) intersects every inland water geometry (contour-v2 lakes, river bodies, streams, ponds) with the inner
box shapely.box(M, M, 12282 - M, 12282 - M) before any rasterisation, so lakes, rivers, streams and ponds end about
M metres before the border while the sea, the delta and the navigable reaches run on as today. Empty results are
dropped. --drop-border-water-km2 A (default 0, used with M > 0) drops lakes and ponds whose ORIGINAL polygon
reaches into the border band and whose area is below A km2 instead of clipping them. The same clipped geometries
feed the classes, the levels, the signed distance sd and inside_poly, so everything derived stays coherent.
--border-keep-m K (default 0, used with M > 0) keeps a lake or pond whole, neither dropped nor clipped, when its
original polygon stays at least K m from the map edge although it reaches into the M band (Guillermo, 06-10: lakes
047 and 107, which only graze the band); rivers and streams are not affected.
--round-river-ends R (default 0 = today's straight cut, used with M > 0) rounds the ends that the border cut leaves
on rivers instead of two square corners (Guillermo, 06-10): every cut segment is rounded with a local morphological
opening of radius min(R, 0.45 x its length, 0.9 x the half-width of the river at the cut), halved while the rounded
end no longer reaches the cut or the opening takes more than half of the river within 2 r of it (below 1 m the end
stays straight); within those end zones the centre-line groove keeps no vertex outside the rounded outline, so a
narrow river's end column does not hold the square end; streams, lakes and ponds keep the straight cut.
Self-check: with --border-margin 60 no vertex of classes 2, 5, 6, 7 lies within 60 m of the map border (x or z
below 60 or above 12222) except those of the bodies kept whole; the printed stats count them as
border_inland_vertices, with the clipped, dropped and kept bodies.
--contour PATH reads the contour-v2 lakes and river bands from PATH (default: the regional-foundation-v1 file), for
a design whose lake outlines were smoothed (tools/water/smooth_water_outlines_v30.py).
Usage: build_v30_water.py <design dir> <out dir> [--border-margin M] [--drop-border-water-km2 A] [--border-keep-m K]
                          [--round-river-ends R] [--contour PATH]
"""
import json
import os
import sys

import numpy as np
import contourpy
from scipy.ndimage import binary_dilation, distance_transform_edt, gaussian_filter
from scipy.spatial import cKDTree
import shapely
from shapely.geometry import shape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v30_common import N, R, grid_xz, raster_vertices  # noqa: E402
from verify_roads_v30 import road_chains  # noqa: E402
import rasterio  # noqa: E402

SELFTEST = "--selftest" in sys.argv[1:]
if SELFTEST:  # the self-check below runs alone, without the two directory arguments
    W_DIR = OUT = ""
else:
    W_DIR, OUT = sys.argv[1], sys.argv[2]
BORDER_MARGIN, DROP_BORDER_KM2, BORDER_KEEP_M, ROUND_RIVER_ENDS = 0.0, 0.0, 0.0, 0.0
CONTOUR = os.path.join(R, "evidence", "regional-foundation-v1", "water-surfaces-contour-v2.geojson")
for _i, _a in enumerate(sys.argv[3:]):
    if _a == "--border-margin":
        BORDER_MARGIN = float(sys.argv[4 + _i])
    elif _a == "--drop-border-water-km2":
        DROP_BORDER_KM2 = float(sys.argv[4 + _i])
    elif _a == "--border-keep-m":
        BORDER_KEEP_M = float(sys.argv[4 + _i])
    elif _a == "--round-river-ends":
        ROUND_RIVER_ENDS = float(sys.argv[4 + _i])
    elif _a == "--contour":
        CONTOUR = sys.argv[4 + _i]
SEA_LEVEL = 0.75
NARVA = (2417.1428225906, 6889.8850822322)
NARVA_ZONE_M = 600.0
STREAM_TIER = 2500


def round_cut_ends(poly, inner, r_max, zones=None):
    # Round the straight ends that the border cut leaves on one river polygon: each cut segment (a line part shared
    # with the inner box edge) is rounded with a local morphological opening, its radius halved until only the corners
    # go. Returns the polygon and the number of rounded segments; the zone of every rounded end (within 2 r of its cut)
    # is appended to `zones` when given.
    def parts(g, kind):
        if g.geom_type == kind:
            return [g]
        return [p for sub in getattr(g, "geoms", []) for p in parts(sub, kind)]

    lines = [g for g in parts(poly.boundary.intersection(inner.exterior), "LineString") if not g.is_empty]
    if not lines:
        return poly, 0
    merged = shapely.line_merge(shapely.MultiLineString(lines))
    rounded = 0
    for s in parts(merged, "LineString"):
        if s.length < 0.5:
            continue
        # A river crossing the cut obliquely has a cut longer than its width: the radius also stays under the half-width
        # of the river there (largest inscribed circle within reach of the cut), so the opening never erases it.
        local = max(parts(poly.intersection(s.buffer(max(s.length, 10.0), quad_segs=16)), "Polygon"),
                    key=lambda g: g.area, default=None)
        half_width = shapely.maximum_inscribed_circle(local).length if local is not None else 0.0
        r = min(r_max, 0.45 * s.length, 0.9 * half_width)
        while r >= 1.0:
            opened = poly.buffer(-r, quad_segs=16).buffer(r, quad_segs=16)
            near = s.buffer(2 * r, quad_segs=16)
            cand = poly.difference(near.difference(opened))
            kept = max(parts(cand, "Polygon"), key=lambda g: g.area, default=None)
            # only the corners may go: the rounded end still reaches the cut and loses at most half of the river within
            # 2 r of it (a square corner loses 0.21 r^2, an acute one where the river meets the cut obliquely up to
            # several r^2, so a bound in r^2 alone would reject oblique ends)
            if (kept is not None and kept.distance(s) <= 0.5
                    and poly.area - kept.area <= 0.5 * poly.intersection(near).area):
                poly, rounded = kept, rounded + 1
                if zones is not None:
                    zones.append(near)
                break
            r *= 0.5                  # below 1 m the end stays straight
    return poly, rounded


def main():
    v33 = np.load(os.path.join(R, "tests", "regional_outline_smoothing_v33", "reference.npz"))
    contour = json.load(open(CONTOUR, encoding="utf-8"))["features"]
    bodies = json.load(open(os.path.join(W_DIR, "water_v3.geojson"), encoding="utf-8"))["features"]
    streams = [f for f in json.load(open(os.path.join(W_DIR, "streams_candidates.geojson"), encoding="utf-8"))["features"]
               if f["properties"]["tier_m"] >= STREAM_TIER]
    prof = np.load(os.path.join(W_DIR, "profiles.npz"))

    clip = BORDER_MARGIN > 0
    counts = {"lakes_clipped": 0, "lakes_dropped": 0, "ponds_clipped": 0, "ponds_dropped": 0,
              "rivers_clipped": 0, "streams_clipped": 0}
    if BORDER_KEEP_M > 0:
        counts.update(lakes_kept_whole=0, ponds_kept_whole=0)
    if ROUND_RIVER_ENDS > 0:
        counts.update(rivers_ends_rounded=0, rivers_end_groove_trimmed=0)
    round_zones = []
    inner = shapely.box(BORDER_MARGIN, BORDER_MARGIN, 12282.0 - BORDER_MARGIN, 12282.0 - BORDER_MARGIN)
    border_band = shapely.box(0.0, 0.0, 12282.0, 12282.0).difference(inner)

    def polygons(g):
        if g.geom_type == "Polygon":
            return [g] if g.area > 0 else []
        return [p for part in getattr(g, "geoms", []) for p in polygons(part)]

    def clip_geom(g, kind, drop=False):
        # Border rule for one inland geometry: small border water is dropped, the rest is clipped to the inner box
        # (polygonal parts only, so the shore rings below stay rings). Geometries inside the box are kept as they are.
        if not clip or g.within(inner):
            return g
        if BORDER_KEEP_M > 0 and kind in ("lakes", "ponds"):
            x0, z0, x1, z1 = g.bounds
            if min(x0, z0, 12282.0 - x1, 12282.0 - z1) >= BORDER_KEEP_M:
                counts[kind + "_kept_whole"] += 1
                return g
        if drop and DROP_BORDER_KM2 > 0 and g.intersects(border_band) and g.area < DROP_BORDER_KM2 * 1e6:
            counts[kind + "_dropped"] += 1
            return None
        counts[kind + "_clipped"] += 1
        parts = polygons(g.intersection(inner))
        if not parts:
            return None
        if kind == "rivers" and ROUND_RIVER_ENDS > 0:
            # Rounded here only, so the classes, levels, sd and inside_poly below all see the same geometry.
            rounded = []
            for p in parts:
                p, n = round_cut_ends(p, inner, ROUND_RIVER_ENDS, round_zones)
                counts["rivers_ends_rounded"] += n
                rounded.append(p)
            parts = rounded
        return parts[0] if len(parts) == 1 else shapely.MultiPolygon(parts)

    cls = np.zeros((N, N), dtype=np.uint8)
    level = np.full((N, N), np.nan)
    cls[v33["ocean"]] = 1
    level[v33["ocean"]] = SEA_LEVEL

    # V29 surface levels (lakes and river bands) on the vertex grid.
    lakes = []
    for f in contour:
        if not f["properties"]["body"].startswith("lake"):
            continue
        g = clip_geom(shape(f["geometry"]), "lakes", drop=True)
        if g is not None:
            lakes.append((g, f["properties"]["level_m"]))
    bands = [(shape(f["geometry"]), f["properties"]["level_m"]) for f in contour if f["properties"]["body"].startswith("river")]
    lake_lv = raster_vertices([g for g, _ in lakes], values=[v for _, v in lakes], dtype="float32")
    band_lv = raster_vertices([g for g, _ in bands], values=[v for _, v in bands], dtype="float32", all_touched=True)
    lake_m = raster_vertices([g for g, _ in lakes]).astype(bool)
    cls[lake_m & (cls == 0)] = 2
    level[cls == 2] = lake_lv[cls == 2]

    def put(geoms, code, lv):
        m = raster_vertices(geoms).astype(bool) & ~np.isin(cls, (1, 2))
        cls[m] = code
        level[m] = lv[m] if isinstance(lv, np.ndarray) else lv
        return m

    # Navigable: V29 band levels, extended to the new banks by nearest band vertex.
    nav = [shape(f["geometry"]) for f in bodies if f["properties"]["class"] == "navigable"]
    known = band_lv > 0
    _, idx = distance_transform_edt(~known, return_indices=True)
    nav_lv = band_lv[idx[0], idx[1]].astype(float)
    put(nav, 3, nav_lv)
    put([shape(f["geometry"]) for f in bodies if f["properties"]["class"].startswith("delta")], 4, SEA_LEVEL)

    # Rivers and streams: nearest profile sample.
    def profile_levels(feats, code, geoms=None):
        pts, lv = [], []
        if geoms is None:
            geoms = [shape(f["geometry"]) for f in feats]
        for f in feats:
            key = f["properties"].get("id")
            if key and key in prof.files:
                a = prof[key]
                pts.append(a[:, 1:3])
                lv.append(a[:, 4])
        # Rivers of 8-20 m and streams of 3-6 m are narrower than two 6 m cells: every touched vertex joins the
        # groove so the bed stays continuous; the visible water keeps the design width in phase 3.
        m = raster_vertices(geoms, all_touched=True).astype(bool) & ~np.isin(cls, (1, 2, 3, 4))
        if pts:
            tree = cKDTree(np.vstack(pts))
            x, z = grid_xz()
            _, j = tree.query(np.column_stack([x[m], z[m]]))
            vals = np.concatenate(lv)[j]
        else:
            vals = np.nan
        cls[m] = code
        level[m] = vals
        return m

    river_feats = [f for f in bodies if f["properties"]["class"] == "river"]
    river_geoms = []
    for f in river_feats:
        g = clip_geom(shape(f["geometry"]), "rivers")
        if g is not None:
            river_geoms.append(g)
    profile_levels(river_feats, 5, geoms=river_geoms)
    stream_geoms = []
    for f in streams:
        g = clip_geom(shape(f["geometry"]), "streams")
        if g is not None:
            stream_geoms.append(g)
    profile_levels(streams, 6, geoms=stream_geoms)
    ponds = []
    for f in bodies:
        if f["properties"]["class"] != "pond":
            continue
        g = clip_geom(shape(f["geometry"]), "ponds", drop=True)
        if g is not None:
            ponds.append((f, g))
    pm = raster_vertices([g for _, g in ponds], values=[f["properties"]["level_m"] for f, _ in ponds], dtype="float32")
    pmask = raster_vertices([g for _, g in ponds]).astype(bool) & (cls == 0)
    cls[pmask] = 7
    level[pmask] = pm[pmask]

    # Smooth shores: signed distance to the union of the inland outlines, and centre-line grooves.
    other_geoms = [shape(f["geometry"]) for f in bodies if f["properties"]["class"] not in ("navigable", "pond", "river")]
    inland = [g for g, _ in lakes] + nav + river_geoms + other_geoms + stream_geoms + [g for _, g in ponds]
    segs = []
    for g in inland:
        for part in (g.geoms if hasattr(g, "geoms") else [g]):
            for ring in [part.exterior] + list(part.interiors):
                xy = np.asarray(ring.coords)
                segs.append(np.stack([xy[:-1], xy[1:]], axis=1))
    segs = np.concatenate(segs)
    tree = shapely.STRtree(shapely.linestrings(segs))
    inside_poly = raster_vertices(inland).astype(bool)
    inland_cls = np.isin(cls, (2, 3, 4, 5, 6, 7))
    near = binary_dilation(inside_poly | inland_cls, iterations=2)
    x, z = grid_xz()
    pts = shapely.points(x[near], z[near])
    _, dist = tree.query_nearest(pts, return_distance=True, all_matches=False)
    sd = np.full((N, N), np.nan, dtype=np.float32)
    sd[near] = np.where(inside_poly[near], -dist, dist)
    groove = np.zeros((N, N), dtype=bool)
    for key in prof.files:
        a = prof[key]
        if not (key.startswith("river_") or key.startswith("stream_")):
            continue
        p = a[:, 1:3]
        st = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
        s = np.arange(0, st[-1] + 0.5, 1.0)
        q = np.column_stack([np.interp(s, st, p[:, 0]), np.interp(s, st, p[:, 1])])
        rr = np.clip(np.rint((12282 - q[:, 1]) / 6).astype(int), 0, N - 1)
        cc = np.clip(np.rint(q[:, 0] / 6).astype(int), 0, N - 1)
        groove[rr, cc] = True
        diag = (np.abs(np.diff(rr)) == 1) & (np.abs(np.diff(cc)) == 1)
        groove[rr[:-1][diag], cc[1:][diag]] = True
    groove &= np.isin(cls, (5, 6))
    if round_zones:
        # at a rounded river end the centre-line groove must not keep the square end of the cut: within the rounded
        # zone it holds no vertex outside the rounded outline
        trim = groove & raster_vertices(round_zones).astype(bool) & ~inside_poly
        groove &= ~trim
        counts["rivers_end_groove_trimmed"] = int(trim.sum())
    touched_only = np.isin(cls, (5, 6)) & ~inside_poly & ~groove
    cls[touched_only] = 0
    level[touched_only] = np.nan

    # Smooth sea coast: 0.5 contour of the ocean mask after a 9 m Gaussian, signed distance within ~12 m.
    sea0 = cls == 1
    f = gaussian_filter(sea0.astype(np.float64), 1.5)
    sea_new = f >= 0.5
    lines = contourpy.contour_generator(z=f, line_type=contourpy.LineType.Separate).lines(0.5)
    csegs = []
    for ln in lines:
        if len(ln) < 2:
            continue
        xy = np.column_stack([ln[:, 0] * 6.0, 12282.0 - ln[:, 1] * 6.0])
        csegs.append(np.stack([xy[:-1], xy[1:]], axis=1))
    ctree = shapely.STRtree(shapely.linestrings(np.concatenate(csegs)))
    band = binary_dilation(sea_new, iterations=2) & binary_dilation(~sea_new, iterations=2)
    _, cdist = ctree.query_nearest(shapely.points(x[band], z[band]), return_distance=True, all_matches=False)
    sd_sea = np.full((N, N), np.nan, dtype=np.float32)
    sd_sea[band] = np.where(sea_new[band], -cdist, cdist)
    gained = sea_new & (cls == 0)
    lost = ~sea_new & (cls == 1)
    cls[gained] = 1
    level[gained] = SEA_LEVEL
    cls[lost] = 0
    level[lost] = np.nan

    # Narva bridge zone: V29 water exactly (the builder keeps V29 heights there).
    x, z = grid_xz()
    zone = np.hypot(x - NARVA[0], z - NARVA[1]) <= NARVA_ZONE_M
    v29_wet = v33["wet"] & ~v33["ocean"]
    cls[zone & ~v33["ocean"]] = 0
    level[zone & ~v33["ocean"]] = np.nan
    cls[zone & v29_wet] = 3
    level[zone & v29_wet] = nav_lv[zone & v29_wet]
    sd[zone] = np.nan
    groove[zone] = False
    sd_sea[zone] = np.nan

    # Roads keep their ground: within 9 m of a graded road station, a vertex that was dry in V29 (above the high
    # tide and not V29 inland water) stays land. That keeps the sea causeway and roads beside widened or new rivers;
    # crossings V29 already had in the water stay water (bridge or ford reserves).
    with rasterio.open(os.path.join(R, "tests", "regional_road_network_v29", "baltic_road_network_v29.asc")) as ds:
        h29 = ds.read(1)
    pts = []
    for p in road_chains():
        if len(p) < 2:
            continue
        st = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
        s = np.arange(0, st[-1] + 0.5, 1.0)
        pts.append(np.column_stack([np.interp(s, st, p[:, 0]), np.interp(s, st, p[:, 1])]))
    cand = (cls > 0) & ~zone
    dist_road, _ = cKDTree(np.vstack(pts)).query(np.column_stack([x[cand], z[cand]]), distance_upper_bound=9.0)
    near_road = np.zeros((N, N), dtype=bool)
    near_road[cand] = np.isfinite(dist_road)
    v29_dry = (h29 >= 1.0) & ~(v33["wet"] & ~v33["ocean"])
    keep_ground = near_road & v29_dry
    allp = np.vstack(pts)
    sr = np.clip(np.rint((12282 - allp[:, 1]) / 6).astype(int), 0, N - 1)
    sc = np.clip(np.rint(allp[:, 0] / 6).astype(int), 0, N - 1)
    causeway_st = allp[(cls[sr, sc] > 0) & v29_dry[sr, sc] & ~zone[sr, sc]]
    if len(causeway_st):
        d_cw, _ = cKDTree(causeway_st).query(np.column_stack([x[cand], z[cand]]), distance_upper_bound=6.5)
        carriage = np.zeros((N, N), dtype=bool)
        carriage[cand] = np.isfinite(d_cw)
        keep_ground |= carriage
    cls[keep_ground] = 0
    level[keep_ground] = np.nan
    sd[keep_ground] = np.nan
    sd_sea[keep_ground] = np.nan
    groove[keep_ground] = False

    # One plane per 6 m cell: corners of one cell must not disagree much. Standing water (lakes, ponds) higher
    # than an adjacent different body by > 0.30 m gives that edge vertex to land; flowing water (navigable,
    # rivers, streams) is capped at 0.25 m per 6 m towards its neighbours, lowering only, standing water fixed.
    standing = np.isin(cls, (2, 7)) & ~zone
    flowing = np.isin(cls, (3, 5, 6)) & ~zone
    wetv = (cls > 0) & np.isfinite(level)
    lvp = np.pad(np.where(wetv, level, np.nan), 1, constant_values=np.nan)
    sep = np.zeros((N, N), dtype=bool)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nb = lvp[1 + dr:1 + dr + N, 1 + dc:1 + dc + N]
            with np.errstate(invalid="ignore"):
                sep |= standing & np.isfinite(nb) & (level - nb > 0.30)
    cls[sep] = 0
    level[sep] = np.nan
    cap = 0.25
    for it in range(4000):
        cur = np.pad(np.where((cls > 0) & np.isfinite(level), level, np.inf), 1, constant_values=np.inf)
        low = np.full((N, N), np.inf)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                low = np.minimum(low, cur[1 + dr:1 + dr + N, 1 + dc:1 + dc + N] + cap * (1.4142 if dr and dc else 1.0))
        flowing = np.isin(cls, (3, 5, 6)) & ~zone
        new = np.where(flowing & np.isfinite(low), np.minimum(level, low), level)
        changed = flowing & np.isfinite(level) & (new < level - 1e-6)
        level = np.where(changed, new, level)
        if not changed.any():
            break
    cell_stats = {"standing_edge_to_land": int(sep.sum()), "level_cap_iterations": it + 1,
                  "road_ground_kept": int(keep_ground.sum()), "causeway_stations": int(len(causeway_st))}

    # Rivers drawn only as polygons have no profile: give them their own low-bank level later in the builder.
    missing = (cls >= 3) & ~np.isfinite(level)
    inside = cls > 0
    dist_bank = distance_transform_edt(inside) * 6.0          # metres from the nearest land vertex, inside water
    dist_water = distance_transform_edt(~inside) * 6.0        # metres from the nearest water vertex, on land
    _, nidx = distance_transform_edt(~inside, return_indices=True)
    level_near = level[nidx[0], nidx[1]]                      # level of the nearest water vertex, for banks

    # V29 water that the new design no longer uses. Only "wet" is water: Codex's bank_support is 6.8 km2 of dry
    # land around the water (median 2.89 m) and fairway_support lies inside wet.
    v29_wet = v33["wet"] & ~v33["ocean"]
    excess = v29_wet & ~binary_dilation(inside, iterations=1)
    stats = {"vertices": {name: int((cls == code).sum()) for code, name in enumerate(
        ["land", "sea", "lake", "navigable", "delta", "river", "stream", "pond"])},
        "missing_level_vertices": int(missing.sum()), "excess_v29_water_vertices": int(excess.sum()),
        "shore_shaped_vertices": int(np.isfinite(sd).sum()), "groove_vertices": int(groove.sum()),
        "touched_reclassified_land": int(touched_only.sum()), "coast_shaped_vertices": int(np.isfinite(sd_sea).sum()),
        "coast_gained_sea": int(gained.sum()), "coast_lost_sea": int(lost.sum()), **cell_stats}
    if BORDER_MARGIN > 0 or DROP_BORDER_KM2 > 0:
        edge = (x < BORDER_MARGIN) | (x > 12282.0 - BORDER_MARGIN) | (z < BORDER_MARGIN) | (z > 12282.0 - BORDER_MARGIN)
        counts["border_inland_vertices"] = int((edge & np.isin(cls, (2, 5, 6, 7))).sum())
        stats.update(counts)
    np.savez_compressed(os.path.join(OUT, "water_v30.npz"), cls=cls, level=level.astype("float32"),
                        dist_bank=dist_bank.astype("float32"), dist_water=dist_water.astype("float32"),
                        level_near=level_near.astype("float32"), excess=excess, missing=missing,
                        sd=sd, groove=groove, sd_sea=sd_sea)
    print(json.dumps(stats, indent=1))


def selftest():
    # Synthetic checks for the border-cut rounding, with inner = box(60, 60, 12222, 12222) and r_max = 15.
    inner = shapely.box(60, 60, 12222, 12222)

    # a 20 m river crossing the east cut: r = 0.45 * 20 = 9, the two rounded corners lose about 0.429 * 9^2
    poly = shapely.box(12100, 1000, 12300, 1020).intersection(inner)
    end, n = round_cut_ends(poly, inner, 15)
    lost = poly.area - end.area
    print(f"river across the cut: rounded_ends={n} area_lost={lost:.2f} m2")
    assert n == 1
    assert abs(lost - 34.8) <= 0.25 * 34.8
    assert shapely.points(12222.0, 1010.0).distance(end) <= 0.05
    assert shapely.points(12221.5, 1000.5).distance(end) > 0.0

    # a 22 m river running along the cut: the radius stays under its half-width, so the opening keeps the strip and
    # only rounds its two corners on the cut
    poly = shapely.box(12200, 1000, 12300, 2000).intersection(inner)
    end, n = round_cut_ends(poly, inner, 15)
    print(f"river along the cut: rounded_ends={n} area_lost={poly.area - end.area:.2f} m2")
    assert poly.area - end.area <= n * 15.0 ** 2
    assert end.area >= 0.99 * poly.area

    # a 15 m river meeting the cut at 30 degrees (cut about 30 m long, like the Volkhov): the radius follows its
    # half-width, not the cut, and the acute corner is rounded off
    from shapely.affinity import rotate
    band = rotate(shapely.box(11900, 992.5, 12500, 1007.5), 60, origin=(12222, 1000))
    poly = band.intersection(inner)
    end, n = round_cut_ends(poly, inner, 30)
    cut = poly.boundary.intersection(inner.exterior)
    zs = sorted(c[1] for c in cut.coords) if cut.geom_type == "LineString" else []
    print(f"oblique river: cut={cut.length:.1f} m rounded_ends={n} area_lost={poly.area - end.area:.2f} m2")
    assert n == 1 and len(zs) == 2
    tips = [shapely.points(12221.5, zs[0] + 0.5), shapely.points(12221.5, zs[1] - 0.5)]
    assert any(t.distance(end) > 0.0 for t in tips), 'the acute tip is still there'

    # a river inside the inner box is never cut and comes back unchanged
    river = shapely.box(2000, 4000, 2600, 4020)
    end, n = round_cut_ends(river, inner, 15)
    print(f"river inside the box: rounded_ends={n} geometry unchanged")
    assert n == 0 and end.equals(river)


if __name__ == "__main__":
    if SELFTEST:
        selftest()
    else:
        main()

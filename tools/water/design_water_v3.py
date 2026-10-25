"""Water V3 design on relief V30 (offline): delta, named rivers, stream candidates, ponds, levels and road crossings.

Decisions (Guillermo, 2026-10-02): navigable rivers natural with variable width (design_navigable.py); named rivers
8-20 m and the longest streams 3-6 m; Neva delta branches and islands restored; ponds from ~300 m2.
Inputs: <out>/navigable.geojson, tests/relief_v30/relief_v30_mix.npz, OSM layers in source/vectors, the V29 audit
(evidence/v29-water-color-audit-2026-10-02 rasters regenerated into the scratchpad audit folder).
Outputs in <out>: water_v3.geojson (all bodies with class, width and level), streams_candidates.geojson,
profiles.npz (river and stream level profiles) and water_v3_summary.json.
Options (off by default, so the design of 02-10 is reproduced byte for byte): --course-sigma-m S smooths every river
and stream course along its arc before its ribbon and profile are built (water_common.smooth_course; Guillermo, 06-10:
the OSM courses drew polygonal channels), and --seed-per-course draws each course's width noise from its own seed, so
changing one course does not shift the widths of every course after it.
Usage: design_water_v3.py <out> <audit> [--course-sigma-m 18] [--seed-per-course]
"""
import collections
import json
import os
import sys
import zlib

import numpy as np
from scipy.ndimage import gaussian_filter1d
from shapely import STRtree, make_valid
from shapely.geometry import LineString, Point, shape
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from water_common import (load_relief, merge_lines, normals, read_shp, resample, ribbon,  # noqa: E402
                          sample_vertex, save_geojson, smooth_course, smooth_noise)

OUT, AUDIT = sys.argv[1], sys.argv[2]
COURSE_SIGMA_M = float(sys.argv[sys.argv.index("--course-sigma-m") + 1]) if "--course-sigma-m" in sys.argv else 0.0
SEED_PER_COURSE = "--seed-per-course" in sys.argv
P = {
    "delta_names": {"Great Neva": "navigable", "Little Neva": "navigable", "Great Nevka": "branch", "Большая Невка": "branch",
                    "Little Nevka": "branch", "Middle Nevka": "branch", "Sea Canal": "branch"},
    "harbour_names": ["Coal Harbour", "Барочный бассейн", "Vostochny Basin", "Большая Турухтанная гавань", "Gutuevsky basin"],
    "delta_navigable_min_m": 30.0, "delta_branch_w": [12.0, 20.0],
    "river_polygon_min_area_m2": 1500.0, "river_line_min_m": 8000.0, "river_w": [8.0, 20.0],
    "stream_tiers_m": [4000.0, 2500.0, 1500.0], "stream_w": [3.0, 6.0],
    "pond_min_m2": 300.0, "pond_types": ["", "pond", "lake", "reservoir", "oxbow", "basin"],
    "river_freeboard_m": 0.4, "stream_freeboard_m": 0.25, "river_depth_m": 1.2, "stream_depth_m": 0.5,
    "pond_freeboard_m": 0.3, "sea_level_m": 0.75, "step_m": 6.0,
}
os.makedirs(OUT, exist_ok=True)
NAME_ALIASES = {"Волхов": "Volkhov", "Оредеж": "Oredezh", "Луга": "Luga", "Luga River": "Luga", "Нева": "Neva",
                "Narva river": "Narva", "Narva jõgi - Нарва": "Narva", "Нарва": "Narva"}
NAVIGABLE = {"Luga", "Narva", "Neva"}


def norm(name):
    return NAME_ALIASES.get(name, name)


def built_fraction(geom, built, transform_px=6.0):
    """Fraction of a polygon's satellite-grid pixels that are built water in V29."""
    from rasterio.features import rasterize
    from affine import Affine
    minx, minz, maxx, maxz = geom.bounds
    c0, c1 = int(max(0, minx // 6)), int(min(2047, maxx // 6) + 1)
    r0, r1 = int(max(0, (12288 - maxz) // 6)), int(min(2047, (12288 - minz) // 6) + 1)
    if c1 <= c0 or r1 <= r0:
        return 0.0, 0
    m = rasterize([(geom, 1)], out_shape=(r1 - r0, c1 - c0), transform=Affine(6, 0, c0 * 6, 0, -6, 12288 - r0 * 6), dtype="uint8").astype(bool)
    n = int(m.sum())
    return (float(built[r0:r1, c0:c1][m].mean()) if n else 0.0), n


def profile(line, relief, half_w, freeboard, depth, sink_at):
    """Monotone level profile from source to mouth along a line; the mouth never drops below the water it joins."""
    s, pts = resample(line, P["step_m"])
    nrm, _ = normals(pts, smooth=5)
    ground = np.min([sample_vertex(relief, pts[:, 0] + nrm[:, 0] * o, pts[:, 1] + nrm[:, 1] * o) for o in (-half_w, 0.0, half_w)], axis=0)
    if ground[0] < ground[-1]:  # orient source -> mouth by height
        s, pts, ground = s[::-1].max() - s[::-1], pts[::-1], ground[::-1]
    level = np.minimum.accumulate(gaussian_filter1d(ground, 3)) - freeboard
    sink = sink_at(pts[-1]) if sink_at else None
    if sink is not None:
        level = np.maximum(level, sink)
    return s, pts, ground, level, level - depth


def main():
    rng = np.random.default_rng(1002)
    relief = load_relief()
    audit = np.load(os.path.join(AUDIT, "layers.npz"))
    built_v29, pond_level, ids = audit["built"], audit["pond_level"], audit["ids"]
    water = read_shp("water")
    lines = read_shp("rivers", {"river", "canal"})
    nav_all = [(shape(f["geometry"]), f["properties"]) for f in json.load(open(os.path.join(OUT, "navigable.geojson"), encoding="utf-8"))["features"]]
    # The 25 fragments of Codex's "Delta Neva" fairway overlap the real branches and end in square stubs; the delta
    # route is the real Great Neva instead (it touches the sea), linked to the main stem by the OSM Neva polygon.
    nav = [(g, p) for g, p in nav_all if p["river"] != "Delta Neva"]
    neva_osm = unary_union([g for g, rec in water if rec["type"] == "river" and rec["name"] == "Neva"])
    link = neva_osm.buffer(max(0.0, (P["delta_navigable_min_m"] - 2 * neva_osm.area / max(neva_osm.length, 1)) / 2), join_style=1)
    nav.append((make_valid(link), {"id": "Neva_link", "class": "navigable", "river": "Neva", "length_m": None}))
    nav_union = unary_union([g for g, _ in nav])
    from water_common import R as REPO
    contour = json.load(open(os.path.join(REPO, "evidence", "regional-foundation-v1", "water-surfaces-contour-v2.geojson"), encoding="utf-8"))["features"]
    lakes = [(make_valid(shape(f["geometry"])), f["properties"]["level_m"]) for f in contour if f["properties"]["body"].startswith("lake")]
    ocean = unary_union([g for g, _ in read_shp("ocean")])
    standing = unary_union([g for g, _ in lakes] + [ocean])
    lake_tree = STRtree([g for g, _ in lakes])
    valid_level = np.isfinite(pond_level)

    def sink_at(pt):
        p = Point(pt)
        hits = [lakes[j][1] for j in lake_tree.query(p.buffer(15)) if lakes[j][0].distance(p) < 15]
        if hits:
            return max(hits)
        if ocean.distance(p) < 15:
            return P["sea_level_m"]
        if nav_union.distance(p) < 15:
            r, c = int((12288 - pt[1]) // 6), int(pt[0] // 6)
            win = pond_level[max(0, r - 8):r + 9, max(0, c - 8):c + 9]
            ok = np.isfinite(win)
            return float(np.nanmax(win)) if ok.any() else None
        return None

    feats, profiles, summary = [], {}, collections.OrderedDict()
    for g, p in nav:
        feats.append((g, {**p, "class": "navigable", "level": "existing V29 river bands"}))

    # 1. Neva delta: sea-level branches carved below the sea, no pond pieces needed.
    delta_feats = []
    for g, rec in water:
        if rec["type"] not in ("river", "canal", "harbour", "basin", ""):
            continue
        name = rec["name"]
        if name in P["delta_names"]:
            kind = P["delta_names"][name]
            target = P["delta_navigable_min_m"] if kind == "navigable" else P["delta_branch_w"][0]
            body = g.buffer(max(0.0, (target - 2 * g.area / max(g.length, 1)) / 2), join_style=1)
            delta_feats.append((make_valid(body), {"class": "delta_" + kind, "name": name, "level_m": P["sea_level_m"],
                                                   "carve_to_m": -2.5 if kind == "navigable" else -1.5, "area_m2": round(body.area)}))
        elif name in P["harbour_names"]:
            delta_feats.append((g, {"class": "delta_harbour", "name": name, "level_m": P["sea_level_m"], "carve_to_m": -2.5, "area_m2": round(g.area)}))
    feats += delta_feats
    summary["delta"] = {"bodies": len(delta_feats), "area_km2": round(sum(f[0].area for f in delta_feats) / 1e6, 4),
                        "names": sorted({f[1]["name"] for f in delta_feats})}

    # 2. Named waterways grouped by name and connectivity.
    groups = collections.defaultdict(list)
    for g, rec in lines:
        if rec["name"]:
            groups[norm(rec["name"])].append(g)
    poly_area = collections.Counter()
    poly_geoms = collections.defaultdict(list)
    for g, rec in water:
        if rec["type"] == "river" and rec["name"]:
            poly_area[norm(rec["name"])] += g.area
            poly_geoms[norm(rec["name"])].append(g)
    comps = []
    for name, gs in groups.items():
        if name in NAVIGABLE or name in P["delta_names"] or name in P["harbour_names"]:
            continue
        for part in merge_lines(gs):
            comps.append((name, part))
    by_name_len = collections.Counter()
    for name, part in comps:
        by_name_len[name] += part.length
    rivers, streams = [], []
    for name, part in comps:
        is_river = poly_area[name] >= P["river_polygon_min_area_m2"] or by_name_len[name] >= P["river_line_min_m"]
        (rivers if is_river else streams).append((name, part))
    # Rivers that only exist as polygons (no named line) still need a course: use the polygon itself.
    named_with_lines = {n for n, _ in comps}
    for name, area in poly_area.items():
        if area >= P["river_polygon_min_area_m2"] and name not in named_with_lines and name not in NAVIGABLE \
                and name not in P["delta_names"] and name not in P["harbour_names"]:
            rivers.append((name, unary_union(poly_geoms[name])))

    river_feats = []
    for i, (name, geom) in enumerate(rivers):
        if geom.geom_type in ("Polygon", "MultiPolygon"):
            body = geom.buffer(max(0.0, (P["river_w"][0] - 2 * geom.area / max(geom.length, 1)) / 2), join_style=1)
            river_feats.append((make_valid(body), {"class": "river", "name": name, "width_m": "polygon", "length_m": None}))
            continue
        if geom.length < 60:
            continue
        geom = smooth_course(geom, P["step_m"], COURSE_SIGMA_M)
        if SEED_PER_COURSE:
            rng = np.random.default_rng(zlib.crc32(f"river_{i:03d}".encode()))
        s, pts = resample(geom, P["step_m"])
        w_poly = max(P["river_w"][0], min(P["river_w"][1], 2 * poly_area[name] / max(by_name_len[name], 1) if by_name_len[name] else P["river_w"][0]))
        w = np.clip(w_poly * (1 + 0.15 * smooth_noise(len(s), 60 / P["step_m"], rng)), *P["river_w"])
        left = w / 2 + 0.5 * smooth_noise(len(s), 20 / P["step_m"], rng)
        right = w / 2 + 0.5 * smooth_noise(len(s), 20 / P["step_m"], rng)
        body = ribbon(pts, left, right)
        if poly_geoms.get(name):
            body = make_valid(unary_union([body] + [pg for pg in poly_geoms[name] if pg.distance(geom) < 30]))
        body = make_valid(body.difference(standing))  # OSM draws flow lines across lakes; those stretches are lake already
        if body.is_empty:
            continue
        key = f"river_{i:03d}"
        ss, pp, ground, level, bed = profile(geom, relief, float(np.median(w)) / 2, P["river_freeboard_m"], P["river_depth_m"], sink_at)
        profiles[key] = np.column_stack([ss, pp, ground, level, bed])
        river_feats.append((body, {"class": "river", "id": key, "name": name, "length_m": round(geom.length),
                                   "width_median_m": round(float(np.median(w)), 1), "level_drop_m": round(float(level[0] - level[-1]), 2),
                                   "max_cut_m": round(float(np.max(ground - bed)), 2)}))
    feats += river_feats
    summary["rivers"] = {"courses": len(river_feats), "km": round(sum(f[1]["length_m"] or 0 for f in river_feats) / 1000, 2),
                         "area_km2": round(sum(f[0].area for f in river_feats) / 1e6, 4),
                         "names": sorted({f[1]["name"] for f in river_feats})}

    # 3. Stream candidates by tier (Guillermo picks the threshold at the phase gate).
    by_stream = collections.Counter()
    for name, part in streams:
        by_stream[name] += part.length
    cand = []
    for i, (name, part) in enumerate(streams):
        total = by_stream[name]
        tier = next((t for t in P["stream_tiers_m"] if total >= t), None)
        if tier is None or part.length < 150:
            continue
        frac = np.clip((total - P["stream_tiers_m"][-1]) / (12000 - P["stream_tiers_m"][-1]), 0, 1)
        w = P["stream_w"][0] + (P["stream_w"][1] - P["stream_w"][0]) * frac
        part = smooth_course(part, P["step_m"], COURSE_SIGMA_M)
        if SEED_PER_COURSE:
            rng = np.random.default_rng(zlib.crc32(f"stream_{i:04d}".encode()))
        s, pts = resample(part, P["step_m"])
        left = w / 2 + 0.3 * smooth_noise(len(s), 15 / P["step_m"], rng)
        right = w / 2 + 0.3 * smooth_noise(len(s), 15 / P["step_m"], rng)
        key = f"stream_{i:04d}"
        ss, pp, ground, level, bed = profile(part, relief, w / 2, P["stream_freeboard_m"], P["stream_depth_m"], sink_at)
        profiles[key] = np.column_stack([ss, pp, ground, level, bed])
        body = make_valid(ribbon(pts, np.maximum(left, 1.2), np.maximum(right, 1.2)).difference(standing))
        if body.is_empty:
            continue
        cand.append((body,
                     {"class": "stream", "id": key, "name": name, "tier_m": tier, "name_total_m": round(total), "length_m": round(part.length),
                      "width_m": round(w, 1), "level_drop_m": round(float(level[0] - level[-1]), 2)}))
    save_geojson(os.path.join(OUT, "streams_candidates.geojson"), cand)
    summary["stream_tiers"] = {f">={int(t)}m": {"names": len({c[1]['name'] for c in cand if c[1]['tier_m'] >= t}),
                                                "km": round(sum(c[1]["length_m"] for c in cand if c[1]["tier_m"] >= t) / 1000, 1)}
                               for t in P["stream_tiers_m"]}

    # 4. Ponds >= 300 m2 that V29 does not build.
    ponds = []
    for idx, (g, rec) in enumerate(water):
        if rec["type"] not in P["pond_types"] or g.area < P["pond_min_m2"]:
            continue
        frac, n = built_fraction(g, built_v29)
        if frac >= 0.5:
            continue
        body = make_valid(g.buffer(1.5, join_style=1).buffer(-1.5, join_style=1).simplify(0.5))
        if body.is_empty:
            continue
        b = body.boundary
        bpts = np.array([b.interpolate(d).coords[0] for d in np.linspace(0, b.length, max(8, int(b.length / 6)))])
        rim = float(np.min(sample_vertex(relief, bpts[:, 0], bpts[:, 1])))
        level = rim - P["pond_freeboard_m"]
        ponds.append((body, {"class": "pond", "osm_id": rec["osm_id"], "name": rec["name"], "type": rec["type"], "area_m2": round(body.area),
                             "level_m": round(level, 2), "below_sea_risk": bool(level < 1.0)}))
    feats += ponds
    summary["ponds"] = {"count": len(ponds), "area_km2": round(sum(p[0].area for p in ponds) / 1e6, 4),
                        "near_sea_level": sum(1 for p in ponds if p[1]["below_sea_risk"])}

    # 5. Road crossings per class (bridges or fords at mapping time), excluding OSM bridges that already exist.
    roads = read_shp("roads")
    main_types = {"motorway", "trunk", "primary", "motorway_link", "trunk_link", "primary_link"}
    road_geoms = [(g, rec["type"] in main_types) for g, rec in roads if rec.get("type") and True]
    tree = STRtree([g for g, _ in road_geoms])
    def crossings(geoms):
        main = other = 0
        for g in geoms:
            for j in tree.query(g, predicate="intersects"):
                if road_geoms[j][1]:
                    main += 1
                else:
                    other += 1
        return {"main_roads": main, "secondary_tertiary": other}
    summary["road_crossings"] = {
        "navigable": crossings([g for g, _ in nav]),
        "rivers": crossings([g for g, _ in river_feats]),
        "streams_by_tier": {f">={int(t)}m": crossings([c[0] for c in cand if c[1]["tier_m"] >= t]) for t in P["stream_tiers_m"]},
        "note": "segment intersections, not unique bridges; existing OSM bridges are not subtracted",
    }
    summary["params"] = {k: v for k, v in P.items() if k not in ("delta_names",)}
    if COURSE_SIGMA_M > 0 or SEED_PER_COURSE:
        summary["course_options"] = {"course_sigma_m": COURSE_SIGMA_M, "seed_per_course": SEED_PER_COURSE}
    save_geojson(os.path.join(OUT, "water_v3.geojson"), feats)
    np.savez_compressed(os.path.join(OUT, "profiles.npz"), **profiles)
    with open(os.path.join(OUT, "water_v3_summary.json"), "wb") as f:
        f.write(json.dumps(summary, indent=1, ensure_ascii=False).encode("utf-8"))
    print(json.dumps({k: v for k, v in summary.items() if k != "params"}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()

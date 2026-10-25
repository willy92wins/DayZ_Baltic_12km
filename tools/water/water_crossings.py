"""Unique road-water crossings per water class: clusters of road pieces inside water, merged within 40 m."""
import json
import os
import sys

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from shapely.geometry import shape
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from water_common import read_shp  # noqa: E402

OUT = sys.argv[1]
MAIN = {"motorway", "trunk", "primary", "motorway_link", "trunk_link", "primary_link"}
SECOND = {"secondary", "secondary_link"}


def unique_points(water_geom, road_union, merge_m=40.0):
    inter = water_geom.intersection(road_union)
    if inter.is_empty:
        return []
    parts = list(inter.geoms) if hasattr(inter, "geoms") else [inter]
    pts = np.array([p.centroid.coords[0] for p in parts if not p.is_empty])
    if len(pts) < 2:
        return pts.tolist()
    labels = fcluster(linkage(pts, "single"), merge_m, criterion="distance")
    return [pts[labels == k].mean(axis=0).tolist() for k in np.unique(labels)]


def main():
    roads = read_shp("roads")
    main_u = unary_union([g for g, r in roads if r["type"] in MAIN])
    sec_u = unary_union([g for g, r in roads if r["type"] in SECOND])
    bodies = json.load(open(os.path.join(OUT, "water_v3.geojson"), encoding="utf-8"))["features"]
    streams = json.load(open(os.path.join(OUT, "streams_candidates.geojson"), encoding="utf-8"))["features"]
    groups = {
        "navigable": [shape(f["geometry"]) for f in bodies if f["properties"]["class"] == "navigable"],
        "delta": [shape(f["geometry"]) for f in bodies if f["properties"]["class"].startswith("delta")],
        "rivers": [shape(f["geometry"]) for f in bodies if f["properties"]["class"] == "river"],
        "ponds": [shape(f["geometry"]) for f in bodies if f["properties"]["class"] == "pond"],
    }
    for tier in (4000, 2500, 1500):
        groups[f"streams>={tier}m"] = [shape(f["geometry"]) for f in streams if f["properties"]["tier_m"] >= tier]
    result = {}
    for name, geoms in groups.items():
        u = unary_union(geoms)
        result[name] = {"main_roads": len(unique_points(u, main_u)), "secondary_roads": len(unique_points(u, sec_u))}
        print(name, result[name])
    with open(os.path.join(OUT, "crossings.json"), "wb") as f:
        f.write(json.dumps({"note": "unique crossing points (road pieces inside water merged within 40 m); tertiary roads excluded",
                            "crossings": result}, indent=1).encode("utf-8"))


if __name__ == "__main__":
    main()

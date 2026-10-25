"""Audit V29 water and ground colour against the reference, on the 6 m satellite grid.

Layers, all rasterised on the satellite pixel grid (pixel c,r covers x 6c..6c+6, z 12282-6r..12288-6r):
  reference  OSM water polygons + ocean polygon (source/vectors, TB coords minus 200000)
  built      engine sea (terrain below sea level) + 407 inland surfaces (contour-v2) above terrain
  painted    satellite pixels coloured as water (103,165,192) in source/sat_preview.png
Terrain height at a pixel centre = mean of its NW and SE vertices (native NW-SE diagonal).
"""
import collections
import json
import os
import sys

import numpy as np
import rasterio
import shapefile
from affine import Affine
from PIL import Image
from rasterio.features import rasterize
from scipy import ndimage
from shapely.affinity import translate
from shapely.geometry import shape

R = r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev"
OUT = sys.argv[1]
N = 2048
SAT = Affine(6, 0, 0, 0, -6, 12288)
SEA_LOW, SEA_HIGH = 0.5, 1.0
WATER_RGB = (103, 165, 192)
os.makedirs(OUT, exist_ok=True)


def load_heights():
    with rasterio.open(os.path.join(R, "tests", "regional_road_network_v29", "baltic_road_network_v29.asc")) as ds:
        h = ds.read(1).astype("float64")
    top = np.vstack([h[:1], h[:-1]])          # vertex row r-1 is the north edge of pixel r
    right = np.hstack([h[:, 1:], h[:, -1:]])  # vertex col c+1 is the east edge of pixel c
    return h, 0.5 * (top + right)             # centre on the NW-SE diagonal: mean(NW, SE)


def read_shp(name):
    sf = shapefile.Reader(os.path.join(R, "source", "vectors", name))
    out = []
    for sr in sf.iterShapeRecords():
        if not sr.shape.points:
            continue
        g = translate(shape(sr.shape.__geo_interface__), xoff=-200000)
        out.append((g, sr.record))
    return out


def main():
    verts, centre = load_heights()
    sat = np.array(Image.open(os.path.join(R, "source", "sat_preview.png")).convert("RGB"))
    painted = np.all(sat == np.array(WATER_RGB, dtype=np.uint8), axis=2)

    water = read_shp("water")
    ocean = read_shp("ocean")
    rivers = read_shp("rivers")
    ids = rasterize(((g, i + 1) for i, (g, _) in enumerate(water)), out_shape=(N, N), transform=SAT, dtype="int32")
    ref_poly = ids > 0
    ref_ocean = rasterize(((g, 1) for g, _ in ocean), out_shape=(N, N), transform=SAT, dtype="uint8").astype(bool)
    reference = ref_poly | ref_ocean
    streams = rasterize(((g, 1) for g, _ in rivers), out_shape=(N, N), transform=SAT, dtype="uint8", all_touched=True).astype(bool)

    feats = json.load(open(os.path.join(R, "evidence", "regional-foundation-v1", "water-surfaces-contour-v2.geojson"), encoding="utf-8"))["features"]
    level = np.full((N, N), -np.inf)
    body = np.zeros((N, N), dtype="int32")
    for i, f in enumerate(feats):
        m = rasterize([(shape(f["geometry"]), 1)], out_shape=(N, N), transform=SAT, dtype="uint8").astype(bool)
        upd = m & (f["properties"]["level_m"] > level)
        level[upd] = f["properties"]["level_m"]
        body[upd] = i + 1
    pond_wet = np.isfinite(level) & (centre < level)
    sea_wet = centre < SEA_LOW
    tidal = (centre >= SEA_LOW) & (centre < SEA_HIGH) & ~pond_wet
    built = sea_wet | pond_wet

    px = 36.0
    km2 = lambda m: round(float(m.sum()) * px / 1e6, 4)
    summary = {
        "grid": "satellite pixels 6 m; terrain V29 ASC ed6cdaa5; sea 0.5..1.0 m",
        "reference_km2": km2(reference), "built_km2": km2(built),
        "both_km2": km2(reference & built), "missing_km2": km2(reference & ~built), "extra_km2": km2(built & ~reference),
        "tidal_only_km2": km2(tidal),
        "sea_wet_km2": km2(sea_wet), "inland_wet_km2": km2(pond_wet & ~sea_wet),
        "sea_wet_inside_inland_surface_km2": km2(sea_wet & np.isfinite(level)),
        "painted_km2": km2(painted), "painted_and_built_km2": km2(painted & built),
        "painted_but_dry_km2": km2(painted & ~built), "built_but_not_painted_km2": km2(built & ~painted),
        "streams_pixels": int(streams.sum()), "streams_with_water_pct": round(100.0 * (streams & built).sum() / max(1, streams.sum()), 1),
    }

    # Per reference polygon: rasterised pixels and the fraction that is built water.
    total = np.bincount(ids.ravel(), minlength=len(water) + 1)
    hit = np.bincount(ids.ravel(), weights=built.ravel().astype(float), minlength=len(water) + 1)
    classes = [(0, 36, "<36 m² (below one pixel)"), (36, 1000, "36–1000 m²"), (1000, 10000, "0.1–1 ha"),
               (10000, 100000, "1–10 ha"), (100000, 1e12, ">10 ha")]
    table = collections.OrderedDict((label, {"polygons": 0, "area_m2": 0.0, "rasterised": 0, "mostly_built": 0, "mostly_missing": 0})
                                    for _, _, label in classes)
    missing_list = []
    for i, (g, rec) in enumerate(water):
        a = g.area
        label = next(l for lo, hi, l in classes if lo <= a < hi)
        row = table[label]
        row["polygons"] += 1
        row["area_m2"] += a
        n = total[i + 1]
        if n:
            row["rasterised"] += 1
            frac = hit[i + 1] / n
            row["mostly_built"] += frac >= 0.5
            row["mostly_missing"] += frac < 0.5
            if frac < 0.5 and a >= 2000:
                c = g.representative_point()
                missing_list.append({"index": i, "osm_id": rec[0], "name": rec[1], "type": rec[2], "area_m2": round(a),
                                     "built_fraction": round(float(frac), 3), "x": round(c.x), "z": round(c.y)})
    for row in table.values():
        row["area_m2"] = round(row["area_m2"])
        row["mostly_built"] = int(row["mostly_built"])
        row["mostly_missing"] = int(row["mostly_missing"])
    missing_list.sort(key=lambda d: -d["area_m2"])
    summary["reference_polygons_by_size"] = table
    summary["missing_polygons_over_2000m2"] = len(missing_list)
    summary["missing_top"] = missing_list[:40]

    # Colour palette of the satellite and how much of the map each class covers.
    flat = sat.reshape(-1, 3)
    colours, counts = np.unique(flat, axis=0, return_counts=True)
    order = np.argsort(-counts)
    summary["satellite_colours"] = [{"rgb": colours[k].tolist(), "km2": round(float(counts[k]) * px / 1e6, 3)} for k in order[:16]]

    np.savez_compressed(os.path.join(OUT, "layers.npz"), reference=reference, built=built, tidal=tidal, painted=painted,
                        streams=streams, pond_level=np.where(np.isfinite(level), level, np.nan).astype("float32"),
                        body=body, centre=centre.astype("float32"), ids=ids)
    with open(os.path.join(OUT, "summary.json"), "wb") as f:
        f.write(json.dumps(summary, indent=1, ensure_ascii=False).encode("utf-8"))
    print(json.dumps({k: v for k, v in summary.items() if k not in ("missing_top", "satellite_colours")}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()

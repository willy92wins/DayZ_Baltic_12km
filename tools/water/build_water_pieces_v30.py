"""Water surface pieces for terrain V30: horizontal pond planes on 48 m tiles, one per tile and 25 mm level band.

Coverage: every 6 m cell with a water corner of a lake, navigable reach, river, stream or pond above the sea. Every
triangle that touches water lies inside that cover, and its land corners are banks (>= level + 0.35 m within 8.5 m),
so the plane edge stays under the terrain and the visible shore is the terrain contour, not the piece outline.
A cell takes the band of the mean level of its water corners. Sea and delta channels are the engine sea (level <= 0.80 m).
Meshes come from Codex's water_mesh.write_water_mesh (vanilla pond material, class pond, roadway water), as in V29.
Usage: build_water_pieces_v30.py <terrain_v30.npz> <out_dir>   (out_dir must not exist)
Output: <out>/source/baltic_water_v30/*.p3d, config.cpp, $PBOPREFIX$; <out>/pieces.json (poses at authored origin).
"""
import hashlib
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np
from affine import Affine
from rasterio.features import shapes
from shapely import make_valid
from shapely.geometry import box, shape
from shapely.ops import unary_union

sys.path.insert(0, r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\tools\navigation")
from water_mesh import write_water_mesh  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "terrain"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v30_common import cell_planes  # noqa: E402

SEA_LEVEL, SEA_MARGIN = 0.75, 0.05
BAND, TILE, N = 0.025, 48, 2048
CLASSES = (2, 3, 5, 6, 7)
PREFIX = "baltic_water_v30"
CELL = Affine(6, 0, 0, 0, -6, 12282)  # cell (r, c): x in [6c, 6c + 6], z in [12276 - 6r, 12282 - 6r]


def main():
    terrain, out = sys.argv[1], sys.argv[2]
    assert not os.path.exists(out), "fresh output required"
    src = os.path.join(out, "source", PREFIX)
    os.makedirs(src)
    t = np.load(terrain)
    cls, level = t["cls"], t["level"].astype(float)
    wet = np.isin(cls, CLASSES) & (level > SEA_LEVEL + SEA_MARGIN)
    plane = cell_planes(cls, level, band=BAND, sea_cut=SEA_LEVEL + SEA_MARGIN)
    cb = np.where(np.isfinite(plane), np.rint(np.nan_to_num(plane) / BAND), -1).astype(np.int32)
    pieces = defaultdict(list)
    for geom, value in shapes(cb, mask=cb >= 0, transform=CELL, connectivity=4):
        g = shape(geom)
        x0, z0, x1, z1 = g.bounds
        for tx in range(math.floor(x0 / TILE), math.ceil(x1 / TILE)):
            for tz in range(math.floor(z0 / TILE), math.ceil(z1 / TILE)):
                part = g.intersection(box(tx * TILE - .01, tz * TILE - .01, (tx + 1) * TILE + .01, (tz + 1) * TILE + .01))
                if part.area > 1e-6:
                    pieces[(tx, tz, int(value))].append(part)
    print(f"cells {int((cb >= 0).sum())}, pieces {len(pieces)}", flush=True)

    models, poses, full_written = [], [], False
    full_box = box(-24.01, -24.01, 24.01, 24.01)
    for n, ((tx, tz, value), parts) in enumerate(sorted(pieces.items())):
        g = make_valid(unary_union(parts))
        origin = (tx * TILE + 24, tz * TILE + 24)
        tile = box(tx * TILE - .01, tz * TILE - .01, (tx + 1) * TILE + .01, (tz + 1) * TILE + .01)
        # full_48 extends 1 cm beyond the tile. It is valid only when that
        # complete footprint has this same band, including neighbouring cells.
        if g.covers(tile):
            name = "full_48"
            if not full_written:
                rep = write_water_mesh(full_box, os.path.join(src, name + ".p3d"), (0, 0), uv_local=True)
                rep["name"], rep["bounds_rel"] = name, [-24.01, -24.01, 24.01, 24.01]
                models.append(rep)
                full_written = True
            bounds = tile.bounds
        else:
            g = g.intersection(tile)
            name = f"edge_{len(models):05d}"
            rep = write_water_mesh(g, os.path.join(src, name + ".p3d"), origin, uv_local=True)
            bounds = g.bounds
            rep["name"] = name
            rep["bounds_rel"] = [bounds[0] - origin[0], bounds[1] - origin[1], bounds[2] - origin[0], bounds[3] - origin[1]]
            models.append(rep)
        poses.append({"model": f"{PREFIX}\\{name}.p3d", "origin": [origin[0], value * BAND, origin[1]], "band": value,
                      "area_m2": round(g.area, 3)})
        if n % 1000 == 0:
            print(f"piece {n}/{len(pieces)} models {len(models)}", flush=True)
    for m in models:
        with open(os.path.join(src, m["name"] + ".p3d"), "rb") as f:
            m["sha256"] = hashlib.sha256(f.read()).hexdigest()
    with open(os.path.join(src, "$PBOPREFIX$"), "w", encoding="ascii", newline="\n") as f:
        f.write(PREFIX)
    with open(os.path.join(src, "config.cpp"), "w", encoding="ascii", newline="\n") as f:
        f.write("class CfgPatches { class Baltic_Water_V30 { units[]={}; weapons[]={}; requiredVersion=0.1; "
                "requiredAddons[]={\"DZ_Water\"}; }; };\n")
    report = {"status": "GENERATED_NOT_PACKED", "instances": len(poses), "models": len(models),
              "triangles": sum(m["triangles"] for m in models), "cells": int((cb >= 0).sum()),
              "band_m": BAND, "tile_m": TILE, "sea_cutoff_m": SEA_LEVEL + SEA_MARGIN, "classes": list(CLASSES),
              "terrain_sha256": hashlib.sha256(open(terrain, "rb").read()).hexdigest(),
              "poses": poses, "model_list": models}
    with open(os.path.join(out, "pieces.json"), "w", encoding="utf-8") as f:
        json.dump(report, f)
    print(json.dumps({k: v for k, v in report.items() if k not in ("poses", "model_list")}, indent=1))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""patch_water_tiles_v30.py -- patch the changed 48 m tiles of a DayZ v30 water build.

Reads an existing build (--water DIR) made for an OLD water level field, recomputes
the per-cell water plane band indices for the OLD and the NEW level fields, and
regenerates only the 48 m tiles that contain at least one changed cell.  Every
other pose, model_list entry and .p3d file is carried over byte-identical.
Written by GLM-5.3-Flash (GX10 lane, 04-10); receiver change: tiles are rebuilt from a window one cell wider
than the tile and clipped to the tile box grown by 0.01 m, as build_water_pieces_v30.py does, so the 0.01 m
overlaps between neighbouring tiles survive (the consistency check allows that sliver area).

CLI:
    python patch_water_tiles_v30.py --water DIR --terrain-old OLD.npz \
        --terrain-new NEW.npz --sea-cut-old 0.80 --sea-cut-new 0.56 --out OUT
"""

import sys

sys.dont_write_bytecode = True  # no stray __pycache__ writes outside --out

import argparse
import hashlib
import json
import os
import shutil
from collections import Counter, defaultdict

import numpy as np
from affine import Affine
from rasterio.features import shapes
from shapely.geometry import box, shape
from shapely.ops import unary_union
from shapely.validation import make_valid

from v30_common import cell_planes
from water_mesh import write_water_mesh

BAND = 0.025            # metres per band index
CELL_AREA = 36.0        # one 6 m x 6 m cell
N = 2047                # cells per side
TOP_Z = 12282           # z of vertex row 0
TILE = 48               # tile edge in metres
FULL_MODEL = "baltic_water_v30\\full_48.p3d"
# cell (r, c): x in [6c, 6c + 6], z in [12276 - 6r, 12282 - 6r]
CELL_AFFINE = Affine(6, 0, 0, 0, -6, TOP_Z)


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def band_index(plane):
    """Band index per cell, exactly as the existing tools compute it."""
    return np.where(np.isfinite(plane), np.rint(np.nan_to_num(plane) / BAND), -1).astype(np.int32)


def load_level(path):
    """(cls, level) from a terrain NPZ, both (2048, 2048)."""
    with np.load(path) as z:
        cls, level = z["cls"], z["level"]
    if cls.shape != (2048, 2048) or level.shape != (2048, 2048):
        die(f"{path}: expected cls/level with shape (2048, 2048), got {cls.shape} / {level.shape}")
    return cls, level


def tile_of_pose(pose):
    o = pose["origin"]
    return int((o[0] - 24) // TILE), int((o[2] - 24) // TILE)


def tile_cells(tx, tz):
    """Clipped half-open cell window of tile (tx, tz).

    Rows range(2039 - 8*tz, 2047 - 8*tz), columns range(8*tx, 8*tx + 8), clipped to 0..2046.
    """
    return (max(0, 2039 - 8 * tz), min(N, 2047 - 8 * tz),
            max(0, 8 * tx), min(N, 8 * tx + 8))


def dependent_tiles(rows, columns):
    """Tiles whose 1 cm overlap reads a changed native cell, including corners."""
    rows, columns = np.asarray(rows), np.asarray(columns)
    x0, x1 = columns * 6.0, (columns + 1) * 6.0
    z0, z1 = TOP_Z - (rows + 1) * 6.0, TOP_Z - rows * 6.0
    west = np.floor((x0 - .01) / TILE).astype(int)
    east = np.floor((x1 + .01) / TILE).astype(int)
    south = np.floor((z0 - .01) / TILE).astype(int)
    north = np.floor((z1 + .01) / TILE).astype(int)
    return sorted({(int(x), int(z)) for xs in (west, east) for zs in (south, north)
                   for x, z in zip(xs, zs) if 0 <= x <= 255 and 0 <= z <= 255})


def regenerate_tile(cb_new, tx, tz, take_name):
    """Rebuild one 48 m tile from cb_new with the original builder rule.

    Reads one neighbouring cell around the tile, then clips to its 1 cm halo.
    Every band, including a full tile, keeps the footprint of those source cells.
    Returns (poses, geoms); geoms holds (name, geometry, origin) for the unique
    edge models, written later.
    """
    r_lo, r_hi, c_lo, c_hi = tile_cells(tx, tz)
    r_lo, r_hi, c_lo, c_hi = max(0, r_lo - 1), min(N, r_hi + 1), max(0, c_lo - 1), min(N, c_hi + 1)
    win = cb_new[r_lo:r_hi, c_lo:c_hi]
    aff = CELL_AFFINE * Affine.translation(c_lo, r_lo)   # window cell -> world metres
    expanded = box(tx * TILE - .01, tz * TILE - .01, (tx + 1) * TILE + .01, (tz + 1) * TILE + .01)
    parts = defaultdict(list)
    for geom, value in shapes(win, mask=win >= 0, transform=aff, connectivity=4):
        part = shape(geom).intersection(expanded)
        if part.area > 1e-6:
            parts[int(value)].append(part)
    ox, oz = tx * TILE + 24, tz * TILE + 24
    poses, geoms = [], []
    for value in sorted(parts):
        g = make_valid(unary_union(parts[value]))
        origin = [ox, value * BAND, oz]
        if g.covers(expanded):                           # shared model includes the 1 cm halo
            poses.append({"model": FULL_MODEL, "origin": origin, "band": value,
                          "area_m2": round(g.area, 3)})
        else:                                            # unique edge model
            g = g.intersection(expanded)
            name = take_name()
            poses.append({"model": "baltic_water_v30\\" + name + ".p3d", "origin": origin,
                          "band": value, "area_m2": round(g.area, 3)})
            geoms.append((name, g, (ox, oz)))
    return poses, geoms


def main():
    ap = argparse.ArgumentParser(description="Regenerate changed 48 m tiles of a v30 water build.")
    ap.add_argument("--water", required=True, help="input build folder (pieces.json + source/baltic_water_v30/)")
    ap.add_argument("--terrain-old", required=True, help="OLD terrain NPZ (cls, level)")
    ap.add_argument("--terrain-new", required=True, help="NEW terrain NPZ (cls, level)")
    ap.add_argument("--sea-cut-old", type=float, default=0.80, help="sea cut used by the input build")
    ap.add_argument("--sea-cut-new", type=float, default=0.56, help="sea cut of the patched build")
    ap.add_argument("--out", required=True, help="output folder (must not exist)")
    args = ap.parse_args()

    pieces_path = os.path.join(args.water, "pieces.json")
    src_models = os.path.join(args.water, "source", "baltic_water_v30")
    if not os.path.isfile(pieces_path):
        die(f"--water {args.water!r} has no pieces.json")
    if not os.path.isdir(src_models):
        die(f"--water {args.water!r} has no source/baltic_water_v30 folder")
    if os.path.exists(args.out):
        die(f"--out {args.out!r} already exists")

    with open(pieces_path, "rb") as f:
        raw = f.read()
    try:
        data = json.loads(raw)
    except ValueError as e:
        die(f"pieces.json is not valid JSON: {e}")
    if not isinstance(data.get("poses"), list) or not isinstance(data.get("model_list"), list):
        die("pieces.json: 'poses' and 'model_list' must be lists")

    # 1. band indices for both level fields
    try:
        cls_o, lvl_o = load_level(args.terrain_old)
        cls_n, lvl_n = load_level(args.terrain_new)
    except (OSError, KeyError, AttributeError, ValueError) as e:
        die(f"reading terrain NPZ: {e}")
    cb_old = band_index(cell_planes(cls_o, lvl_o.astype(np.float64), band=BAND, sea_cut=args.sea_cut_old))
    cb_new = band_index(cell_planes(cls_n, lvl_n.astype(np.float64), band=BAND, sea_cut=args.sea_cut_new))

    # 2. Regenerate every tile that reads a changed cell, including its overlap.
    ii, jj = np.nonzero(cb_old != cb_new)
    changed_cells = int(ii.size)
    affected = dependent_tiles(ii, jj)
    affected_set = set(affected)

    # 3. drop every pose (all bands) of an affected tile, keep the rest in original order
    in_poses = data["poses"]
    kept = [p for p in in_poses if tile_of_pose(p) not in affected_set]
    removed = len(in_poses) - len(kept)

    # 4. regenerate the affected tiles (new names never reuse an existing model name)
    input_names = {m["name"] for m in data["model_list"]}
    used_names = set(input_names)
    counter = 0

    def take_name():
        nonlocal counter
        while True:
            name = f"patch_{counter:05d}"
            counter += 1
            if name not in used_names:
                used_names.add(name)
                return name

    new_poses, new_geoms = [], []
    for tx, tz in affected:
        poses, geoms = regenerate_tile(cb_new, tx, tz, take_name)
        new_poses.extend(poses)
        new_geoms.extend(geoms)

    # 6. built-in consistency check (in memory, before anything is written)
    failures = []
    by_tile_band = defaultdict(float)
    for p in new_poses:
        by_tile_band[(tile_of_pose(p), p["band"])] += p["area_m2"]
    band_checks, max_err = 0, 0.0
    for tx, tz in affected:
        r_lo, r_hi, c_lo, c_hi = tile_cells(tx, tz)
        vals = cb_new[r_lo:r_hi, c_lo:c_hi]
        for v in np.unique(vals).tolist():
            if v < 0:
                continue
            expected = CELL_AREA * int((vals == v).sum())
            band_checks += 1
            sliver = 4 * 0.01 * (TILE + 0.01)                  # 0.01 m overlap into the four neighbours
            err = by_tile_band.get(((tx, tz), v), 0.0) - expected
            max_err = max(max_err, abs(err))
            if err < -0.01 or err > sliver + 0.01:
                failures.append(f"tile ({tx},{tz}) band {v}: summed pose area off by "
                                f"{err:.4f} m2 (expected {expected})")
    kept_in_affected = sum(1 for p in kept if tile_of_pose(p) in affected_set)
    if kept_in_affected:
        failures.append(f"{kept_in_affected} kept poses still lie in affected tiles")
    in_cnt = Counter(tile_of_pose(p) for p in in_poses)
    out_cnt = Counter(tile_of_pose(p) for p in kept)
    out_cnt.update(tile_of_pose(p) for p in new_poses)
    count_mismatches = sum(1 for t, n in in_cnt.items() if t not in affected_set and out_cnt[t] != n)
    if count_mismatches:
        failures.append(f"{count_mismatches} unaffected tiles did not keep exactly their input poses")
    leaked = sum(1 for p in new_poses if tile_of_pose(p) not in affected_set)
    if leaked:
        failures.append(f"{leaked} new poses lie outside affected tiles")
    if any(p["model"] == FULL_MODEL for p in new_poses):
        if "full_48" not in input_names:
            failures.append("a regenerated tile is full but the input model_list has no full_48")
        elif not os.path.isfile(os.path.join(src_models, "full_48.p3d")):
            failures.append("full_48.p3d is missing from the input source folder")
    if failures:
        for msg in failures:
            print("consistency check failed: " + msg, file=sys.stderr)
        sys.exit(1)

    # 5. write the output build
    out_src = os.path.join(args.out, "source", "baltic_water_v30")
    os.makedirs(out_src)
    shutil.copytree(src_models, out_src, dirs_exist_ok=True)
    new_models = []
    for name, g, (ox, oz) in new_geoms:
        path = os.path.join(out_src, name + ".p3d")
        rep = write_water_mesh(g, path, (ox, oz), uv_local=True)
        b = g.bounds
        new_models.append({"name": name,
                           "triangles": int(rep["triangles"]),
                           "points": int(rep["points"]),
                           "area_m2": float(rep["area_m2"]),
                           "coverage_error_m2": float(rep["coverage_error_m2"]),
                           "bounds_rel": [b[0] - ox, b[1] - oz, b[2] - ox, b[3] - oz],
                           "sha256": sha256_file(path)})

    data["poses"] = kept + new_poses
    data["model_list"] = list(data["model_list"]) + new_models
    data["instances"] = len(data["poses"])
    data["models"] = len(data["model_list"])
    data["triangles"] = sum(int(m["triangles"]) for m in data["model_list"])
    data["sea_cutoff_m"] = args.sea_cut_new
    data["status"] = "PATCHED_TILES_NOT_PACKED"
    data["patch"] = {"changed_cells": changed_cells,
                     "affected_tiles": [[tx, tz] for tx, tz in affected],
                     "removed_poses": removed,
                     "new_poses": len(new_poses),
                     "new_models": len(new_models),
                     "sea_cut_old": args.sea_cut_old,
                     "sea_cut_new": args.sea_cut_new,
                     "terrain_old_sha256": sha256_file(args.terrain_old),
                     "terrain_new_sha256": sha256_file(args.terrain_new),
                     "source_pieces_sha256": hashlib.sha256(raw).hexdigest(),
                     "consistency": {"affected_tiles_checked": len(affected),
                                     "band_area_checks": band_checks,
                                     "max_band_area_error_m2": round(max_err, 6),
                                     "kept_poses_in_affected_tiles": kept_in_affected,
                                     "unaffected_tile_count_mismatches": count_mismatches,
                                     "ok": True}}
    with open(os.path.join(args.out, "pieces.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=1)
        f.write("\n")

    # 7. one-line JSON summary
    print(json.dumps({"changed_cells": changed_cells,
                      "affected_tiles": len(affected),
                      "removed_poses": removed,
                      "new_poses": len(new_poses)}))


if __name__ == "__main__":
    main()

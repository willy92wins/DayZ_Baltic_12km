"""Surface patch V31: take the road paint off the ground that was cut away under the bridges (BALTIC-015).

The world PBO ships the EV95 layer textures: package_ev109.py copies every EV95 entry except the WRP. They were
painted from the EV95 terrain, where the road still ran over an embankment, so after bridges_v31.py and the end-fit
lower the ground, the 7 m road strip runs down the gully under the deck. This tool repaints only that ground:
  1 affected cells: native cells with a corner more than --min-drop (0.5 m) below the reference terrain
    (build_surface_v30.lowered_cells) that carried road paint in the shipped layers: a 1 m pixel centre within 3.5 m of
    a road chain that was dry on the reference terrain and water plane. A road under the reference water was painted
    as bed, not road, so a lowered river crossing (EV96 sea conversion at 4761,5505) is not repainted;
  1b with --include-changed NAME (repeatable): every native cell with a corner marked in the terrain array NAME (a bool
    vertex mask the chain writes, e.g. v31_causeway of causeway_v31.py), dilated by --include-pad cells (default 1),
    joins the affected cells: the ground there changed (water and shore classes, bed tone, road paint), so its pixels
    are regenerated from the target terrain. The pad covers the 0.8 px colour blur of the generator. Without the
    option the selection and the manifest are those of EV110 (review 1 of the causeway track, 17-10: the paint rule
    alone selected 0 of the 1,449 cells the causeway pass changed, so the old shoreline paint would have stayed);
  2 zone: the pixels of those cells, dilated by 2 px (Chebyshev), computed in world pixels so that overlapping tiles agree;
  3 tiles: every 512 px layer tile that the zone touches;
  4 regenerates those tiles with build_surface_v30.py on the target terrain, the EV95 surface flags, the target water
    plane (footprint.npz 'plane') and --road-off-lowered <reference>;
  5 composites the regenerated pixels into the shipped source PNGs inside the zone only. The source PNG of each tile is
    the one whose sibling PAA is byte-identical to the base PBO entry (EV95 wide-slope surface first, then EV82);
  6 converts the changed PNGs with ImageToPAA (TexConvert rules: _lco DXT1, _lca DXT5, as apply_surface_v30.py);
  7 writes manifest.json with the PBO entries to replace (data/layers/<name>.paa), for package_surface_patch_v31.py.
Outside the zone the layers stay the shipped ones: a whole-tile regeneration would also move thousands of water and
shore pixels per tile, because the water plane changed since EV95.
Usage: patch_surface_v31.py <terrain.npz> <out_dir> --footprint footprint.npz [--min-drop 0.5] [--workers 6]
           [--include-changed NAME ...] [--include-pad 1]
           [--include-cells mask.npy --include-cells-sha256 SHA]
           [--reference terrain.npz --reference-sha256 SHA] [--reference-plane plane.npy --reference-plane-sha256 SHA]
           [--base-pbo narva_trial.pbo --base-pbo-sha256 SHA] [--base-layers dir;dir]
Defaults are the EV95 inputs below. <out_dir> must not exist.
"""
import hashlib
import json
import os
import struct
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_surface_v30 import (N, OVER, ROAD_OFF_MIN_DROP, SEA_LEVEL, STEP, TILE, lowered_cells,  # noqa: E402
                               read_reference_heights, read_water_plane, road_tree, read_clearings)
from v30_common import tri_sample  # noqa: E402

GENERATOR = os.path.join(HERE, "build_surface_v30.py")
IMAGE_TO_PAA = r"C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\ImageToPAA\ImageToPAA.exe"
EV95 = "E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/build-wide-slope"
REFERENCE = EV95 + "/candidate/terrain.npz"
REFERENCE_SHA = "40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a"
# water plane of the EV95 surface (build-wide-slope/surface/surface.json); EV82, the source of the other tiles, used it too
REFERENCE_PLANE = "E:/DayZ-Baltic-Build/v30-narva-dry-bank-relief-20261010/candidate/plane.npy"
REFERENCE_PLANE_SHA = "768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0"
BASE_PBO = "P:/Mods/@DayZ_Baltic_EV95_WideBankPreviewV1/Addons/narva_trial.pbo"
BASE_PBO_SHA = "f1a148cab3e7d1d63473f0232a0971d45a9fea04e0fb456f01973235f4644b7d"
BASE_LAYERS = [EV95 + "/surface/layers", "E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/surface/layers"]
# EV95 surface flags: build-wide-slope/build_surface.py:63-67
EV95_FLAGS = ["--bed-tone", "depth-all", "--bed-surface", "gravel", "--shore-ring", "flowing",
              "--landcover", "smooth", "--landcover-sigma", "1.0"]
ZONE_PAD = 2


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def pbo_index(path):
    """Header of a PBO: properties and {name: (offset, size)}; names use '/'."""
    with open(path, "rb") as f:
        def cstr():
            b = bytearray()
            while True:
                c = f.read(1)
                if c in (b"\0", b""):
                    return b.decode("latin1")
                b += c
        props, ents = {}, []
        while True:
            name = cstr()
            mt, _, _, _, size = struct.unpack("<5I", f.read(20))
            if name == "" and mt == 0x56657273:
                while True:
                    k = cstr()
                    if k == "":
                        break
                    props[k] = cstr()
                continue
            if name == "":
                break
            ents.append((name.replace("\\", "/"), size))
        off, index = f.tell(), {}
        for n, s in ents:
            index[n] = (off, s)
            off += s
    return props, index


def pbo_read(path, index, name):
    off, size = index[name]
    with open(path, "rb") as f:
        f.seek(off)
        return f.read(size)


def pixel_cells(a, b, pad):
    """Native cell (row, col) under each 1 m pixel centre of tile (a, b), with a pad; -1 outside the map."""
    j = np.arange(-pad, TILE + pad) + 0.5
    x = STEP * a - OVER + j
    z = N * 6 - STEP * b + OVER - j
    col = np.floor(x / 6).astype(int)
    row = np.floor((12282 - z) / 6).astype(int)
    col[(x < 0) | (x >= 12282)] = -1
    row[(z <= 0) | (z > 12282)] = -1
    return row, col


def tile_zone(a, b, affected, pad=ZONE_PAD):
    row, col = pixel_cells(a, b, pad)
    R, C = np.meshgrid(row, col, indexing="ij")
    inside = (R >= 0) & (C >= 0)
    hit = np.zeros(R.shape, bool)
    hit[inside] = affected[R[inside], C[inside]]
    zone = binary_dilation(hit, structure=np.ones((3, 3), bool), iterations=pad)
    return hit[pad:-pad, pad:-pad], zone[pad:-pad, pad:-pad]


def clearing_zone(a, b, mask):
    """Exact world pixels, including the six metres beyond the native grid edge.
    Only RGB needs the generator's three-pixel Gaussian support; surface slots
    change on the clearing itself. Padding makes overlapping tiles agree.
    """
    pad = 3
    j = np.arange(-pad, TILE + pad) + 0.5
    X, Z = np.meshgrid(STEP * a - OVER + j, N * 6 - STEP * b + OVER - j)
    inside = (X >= 0) & (X < 12288) & (Z > 0) & (Z <= 12288)
    i = np.clip(np.floor(12288 - Z).astype(int), 0, 12287)
    c = np.clip(np.floor(X).astype(int), 0, 12287)
    hit = mask[i, c] & inside
    rgb = binary_dilation(hit, structure=np.ones((3, 3), bool), iterations=pad)
    return {"m": hit[pad:-pad, pad:-pad], "s": rgb[pad:-pad, pad:-pad]}


def affected_cells(lowered, tree, ref_heights, ref_plane):
    """Lowered cells that carried road paint in the shipped layers: a 1 m pixel centre within 3.5 m of a road chain
    sample (build_surface_v30.tile) that was dry on the reference terrain and water plane (water overrides the road)."""
    r, c = np.nonzero(lowered)
    j = np.arange(6) + 0.5
    jx, jz = np.meshgrid(j, j)
    X = (6 * c)[:, None] + jx.ravel()[None, :]
    Z = (12282 - 6 * r)[:, None] - jz.ravel()[None, :]
    d, _ = tree.query(np.column_stack([X.ravel(), Z.ravel()]), distance_upper_bound=6.0)
    near = d.reshape(X.shape) <= 3.5
    h0 = tri_sample(ref_heights, X, Z)
    p0 = ref_plane[r, c][:, None]
    wet = (np.isfinite(p0) & (h0 < np.nan_to_num(p0, nan=-1e9))) | (h0 < SEA_LEVEL)
    painted = near & ~wet
    has = painted.any(axis=1)
    out = np.zeros_like(lowered)
    out[r[has], c[has]] = True
    stats = {"painted_px_centres": int(painted.sum()), "near_road_wet_px_centres": int((near & wet).sum()),
             "lowered_cells_near_road_without_paint": int((near.any(axis=1) & ~has).sum())}
    return out, stats


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def args_all(name):
    return [sys.argv[i + 1] for i, a in enumerate(sys.argv[:-1]) if a == name]


def changed_cells(terrain, names, pad):
    """Cells with a corner marked in any of the terrain's bool vertex arrays `names`, dilated by `pad` cells."""
    z = np.load(terrain)
    mark = np.zeros((N, N), bool)
    per = {}
    for n in names:
        if n not in z.files:
            raise ValueError(f"--include-changed {n}: the terrain has no array '{n}'")
        m = z[n]
        if m.dtype != bool or m.shape != (N, N):
            raise ValueError(f"--include-changed {n}: expected a bool {N}x{N} vertex mask, got {m.dtype} {m.shape}")
        per[n] = int(m.sum())
        mark |= m
    cells = mark[:-1, :-1] | mark[:-1, 1:] | mark[1:, :-1] | mark[1:, 1:]
    core = cells.copy()
    if pad > 0:
        cells = binary_dilation(cells, structure=np.ones((3, 3), bool), iterations=pad)
    return cells, dict(arrays=names, marked_vertices=per, cells_with_marked_corner=int(core.sum()), pad_cells=pad,
                       cells=int(cells.sum()))


def read_included_cells(path, expected_sha):
    """Explicit native cells, e.g. a dry bed whose water changed without raising its vertices.

    The bool mask has one value per 6 m cell, row zero north. It joins the
    repaint selection exactly; the common two-pixel colour zone still applies.
    """
    if not path or not expected_sha:
        raise ValueError("--include-cells and --include-cells-sha256 are required together")
    if sha(path) != expected_sha.lower():
        raise ValueError("included cells SHA256 mismatch")
    mask = np.load(path, allow_pickle=False)
    if mask.dtype != bool or mask.shape != (N - 1, N - 1) or not mask.any():
        raise ValueError(f"included cells must be a nonempty bool {N-1}x{N-1} mask")
    return mask


def to_paa(png):
    paa = png[:-4] + ".paa"
    r = subprocess.run([IMAGE_TO_PAA, png, paa], capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(paa):
        raise RuntimeError(f"ImageToPAA failed for {png}: {r.stdout} {r.stderr}")
    return paa


def main():
    t0 = time.time()
    terrain, out = sys.argv[1], Path(sys.argv[2])
    footprint = arg("--footprint")
    if not footprint:
        raise ValueError("--footprint <footprint.npz> is required (the target water plane)")
    reference, reference_sha = arg("--reference", REFERENCE), arg("--reference-sha256", REFERENCE_SHA)
    ref_plane_path = arg("--reference-plane", REFERENCE_PLANE)
    ref_plane_sha = arg("--reference-plane-sha256", REFERENCE_PLANE_SHA).lower()
    ref_plane = read_water_plane(ref_plane_path, ref_plane_sha)
    base_pbo, base_pbo_sha = arg("--base-pbo", BASE_PBO), arg("--base-pbo-sha256", BASE_PBO_SHA)
    base_layers = arg("--base-layers", ";".join(BASE_LAYERS)).split(";")
    min_drop = float(arg("--min-drop", ROAD_OFF_MIN_DROP))
    workers = int(arg("--workers", 6))
    include_names = args_all("--include-changed")
    include_pad = int(arg("--include-pad", 1))
    cells_path, cells_sha = arg("--include-cells"), arg("--include-cells-sha256")
    explicit_cells = read_included_cells(cells_path, cells_sha) if cells_path or cells_sha else None
    clearings_path, clearings_sha = arg("--forest-clearings"), arg("--forest-clearings-sha256")
    clearings = read_clearings(clearings_path, clearings_sha) if clearings_path or clearings_sha else None
    if sha(reference) != reference_sha.lower():
        raise ValueError("reference terrain SHA256 mismatch")
    if sha(base_pbo) != base_pbo_sha.lower():
        raise ValueError("base PBO SHA256 mismatch")
    out.mkdir(parents=True, exist_ok=False)
    (out / "layers").mkdir()
    plane = np.load(footprint)["plane"]
    np.save(out / "plane.npy", plane)
    plane_sha = sha(out / "plane.npy")
    heights = np.load(terrain)["heights"]
    ref_heights = read_reference_heights(reference)
    lowered = lowered_cells(heights, ref_heights, min_drop)
    affected, paint_stats = affected_cells(lowered, road_tree(), ref_heights, ref_plane)
    include = None
    if include_names or explicit_cells is not None:
        inc_cells, include = changed_cells(terrain, include_names, include_pad)
        if explicit_cells is not None:
            inc_cells |= explicit_cells
            include["explicit_native_cells"] = {"path": str(Path(cells_path).resolve()), "sha256": cells_sha.lower(),
                                                 "cells": int(explicit_cells.sum()), "padding_cells": 0}
            include["cells"] = int(inc_cells.sum())
        include["paint_rule_cells"] = int(affected.sum())
        include["overlap_with_paint_rule"] = int((inc_cells & affected).sum())
        affected = affected | inc_cells
        include["affected_cells_total"] = int(affected.sum())
    if clearings is not None:
        # Native north edge is z=12282, six metres below the texture raster's edge.
        clearing_cells = clearings[6:12288, :12282].reshape(2047, 6, 2047, 6).any(axis=(1, 3))
        # Clearings select exact pixels below, independently of native cell zones.
    if not affected.any() and (clearings is None or not clearings.any()):
        raise ValueError("no lowered cell holds road paint: nothing to patch")
    tiles, zones, clearing_zones = [], {}, {}
    for b in range(32):
        for a in range(32):
            cells_px, zone = tile_zone(a, b, affected)
            cz = clearing_zone(a, b, clearings) if clearings is not None else None
            if zone.any() or (cz is not None and cz["s"].any()):
                tiles.append((a, b))
                zones[(a, b)] = (cells_px, zone)
                if cz is not None:
                    clearing_zones[(a, b)] = cz
    regen = out / "regen"
    cmd = [sys.executable, "-I", "-B", GENERATOR, terrain, str(regen), "--tiles", ";".join(f"{a},{b}" for a, b in tiles),
           "--workers", str(workers), *EV95_FLAGS, "--water-plane", str(out / "plane.npy"), "--water-plane-sha256", plane_sha,
           "--road-off-lowered", reference, "--road-off-min-drop", repr(min_drop)]
    if clearings is not None:
        cmd += ["--forest-clearings", clearings_path, "--forest-clearings-sha256", clearings_sha]
    with open(out / "regen.log", "w", encoding="utf-8") as log:
        done = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
    if done.returncode != 0:
        raise RuntimeError("surface generator failed; see regen.log")
    spec = json.loads((regen / "surface.json").read_text(encoding="utf-8"))
    assert spec["tiles"] == len(tiles) and spec["terrain_sha256"] == sha(terrain)
    assert spec["water_field"]["sha256"] == plane_sha and spec["road_off_lowered"]["cells"] == int(lowered.sum())
    props, index = pbo_index(base_pbo)
    records, convert = [], []
    for a, b in tiles:
        cells_px, zone = zones[(a, b)]
        rec = {"tile": [a, b], "affected_cell_px": int(cells_px.sum()), "zone_px": int((zone | clearing_zones[(a, b)]["s"]).sum()) if clearings is not None else int(zone.sum()), "layers": {}}
        for prefix, suffix in (("s", "lco"), ("m", "lca")):
            stem = f"{prefix}_{a:03d}_{b:03d}_{suffix}"
            entry = f"data/layers/{stem}.paa"
            shipped = pbo_read(base_pbo, index, entry)
            source = None
            for d in base_layers:
                png, paa = Path(d) / f"{stem}.png", Path(d) / f"{stem}.paa"
                if png.exists() and paa.exists() and paa.read_bytes() == shipped:
                    source = png
                    break
            if source is None:
                raise ValueError(f"no source PNG whose PAA matches the shipped {entry}")
            base = np.asarray(Image.open(source)).copy()
            new = np.asarray(Image.open(regen / "layers" / f"{stem}.png")).copy()
            assert base.shape == new.shape and base.dtype == new.dtype
            patched = base.copy()
            apply_zone = zone | clearing_zones[(a, b)][prefix] if clearings is not None else zone
            patched[apply_zone] = new[apply_zone]
            changed = int((patched != base).any(axis=-1).sum())
            lay = {"source_png": str(source), "source_png_sha256": sha(source), "changed_px": changed,
                   "entry": entry, "base_entry_sha256": hashlib.sha256(shipped).hexdigest()}
            if changed:
                dst = out / "layers" / f"{stem}.png"
                Image.fromarray(patched, "RGB" if prefix == "s" else "RGBA").save(dst)
                convert.append((rec, prefix, str(dst)))
            rec["layers"][prefix] = lay
        records.append(rec)
    with ThreadPoolExecutor(4) as ex:
        paas = list(ex.map(lambda item: to_paa(item[2]), convert))
    entries = []
    for (rec, prefix, png), paa in zip(convert, paas):
        lay = rec["layers"][prefix]
        lay.update(png=png, png_sha256=sha(png), paa=paa, paa_sha256=sha(paa))
        if lay["paa_sha256"] == lay["base_entry_sha256"]:
            raise ValueError(f"{lay['entry']}: pixels changed but the PAA did not")
        entries.append({"entry": lay["entry"], "file": paa, "sha256": lay["paa_sha256"], "base_sha256": lay["base_entry_sha256"]})
    entries.sort(key=lambda e: e["entry"])
    manifest = {
        "schema": "surface-patch-v31.v1",
        "terrain": str(Path(terrain).resolve()), "terrain_sha256": sha(terrain),
        "reference": str(Path(reference).resolve()), "reference_sha256": reference_sha.lower(),
        "reference_plane": str(Path(ref_plane_path).resolve()), "reference_plane_sha256": ref_plane_sha,
        "footprint": str(Path(footprint).resolve()), "footprint_sha256": sha(footprint),
        "water_plane": str(out / "plane.npy"), "water_plane_sha256": plane_sha,
        "base_pbo": str(Path(base_pbo).resolve()), "base_pbo_sha256": base_pbo_sha.lower(), "base_pbo_properties": props,
        "base_layers": base_layers, "generator": GENERATOR, "generator_sha256": sha(GENERATOR),
        "generator_flags": EV95_FLAGS, "min_drop_m": min_drop, "zone_pad_px": ZONE_PAD,
        "lowered_cells": int(lowered.sum()), "affected_cells": int(affected.sum()), **paint_stats,
        "tiles": [list(t) for t in tiles], "records": records,
        "changed_entries": [e["entry"] for e in entries], "entries": entries,
        "texheaders_note": "texHeaders.bin is not regenerated, as in every package since B (its entries already differ "
                           "from 1,497 of the 2,048 shipped layer PAAs).",
        "seconds": round(time.time() - t0, 1),
    }
    if clearings is not None:
        manifest["forest_clearings"] = {"path": str(Path(clearings_path).resolve()), "sha256": clearings_sha.lower(),
                                        "pixels": int(clearings.sum()), "native_cells": int(clearing_cells.sum()),
                                        "selection": "exact world pixels; RGB 3px blur support; slot 0px"}
    if include is not None:
        # every pixel of every included cell must lie inside the regenerated zone of a patched tile
        seen, uncovered = np.zeros_like(affected), np.zeros_like(affected)
        for a, b in tiles:
            row, col = pixel_cells(a, b, 0)
            R, C = np.meshgrid(row, col, indexing="ij")
            ins = (R >= 0) & (C >= 0)
            zn = zones[(a, b)][1]
            seen[R[ins], C[ins]] = True
            uncovered[R[ins & ~zn], C[ins & ~zn]] = True
        include["included_cells_outside_zone"] = int((inc_cells & (uncovered | ~seen)).sum())
        if include["included_cells_outside_zone"]:
            raise ValueError(f"{include['included_cells_outside_zone']} included cells outside the patched zone")
        manifest["include_changed"] = include
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k not in ("records", "entries")}, indent=1))


if __name__ == "__main__":
    main()

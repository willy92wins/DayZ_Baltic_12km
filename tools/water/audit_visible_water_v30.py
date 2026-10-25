#!/usr/bin/env python3
"""audit_visible_water_v30.py

Compare the water the DayZ engine SHOWS (sea plane + horizontal pond planes +
optional pitched channel pieces) against the DESIGNED water outline
(vector polygons + smoothed sea mask) on a 2 m grid over the whole 12.3 km map.

Reports flooded land, dry holes inside designed water, and how far the visible
waterline sits from the designed outline.  Outputs audit.json, masks.npz and
overview.png inside a freshly created OUTDIR.

Run:  python audit_visible_water_v30.py --terrain T.npz --out OUTDIR [options]
Self-test:  python audit_visible_water_v30.py --selftest --out OUTDIR

Known limits: the designed sea is the smoothed v33 ocean mask, whose first map column is not ocean, so a
strip of about 14 m along the west edge counts as flooded; the delta reference is water_v3, narrower than
the delta fairways carved from the full OSM source (BALTIC-013); waterline offsets are quantised to 2 m.
Written by GLM-5.3-Flash (GX10 lane, 04-10); receiver change: the tools/terrain path setup below.
"""

import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np
from affine import Affine
from PIL import Image
from rasterio.features import rasterize
from scipy import ndimage as ndi
from shapely.geometry import box, shape

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "terrain"))
from v30_common import N, cell_planes, tri_sample  # noqa: E402
from engine_water_model import Piece, top_visual  # noqa: E402

S = 6141                                   # 2 m pixels over the 12282 m map
TILE = 1024                                # tile size for the heavy per-pixel work
TRANSFORM = Affine(2, 0, 0, 0, -2, 12282)  # pixel (j, i) centre: x=1+2i, z=12281-2j
STRUCT8 = np.ones((3, 3), np.uint8)
CODE2NAME = {1: "stream", 2: "pond", 3: "river", 4: "lake",
             5: "delta", 6: "navigable", 7: "sea"}
NAME2CODE = {v: k for k, v in CODE2NAME.items()}
CAUSE2NAME = {1: "sea", 2: "plane", 3: "channel"}

R = r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev"
DEFAULTS = {
    "water_v3": R + r"\tests\water_v3\water_v3.geojson",
    "streams": R + r"\tests\water_v3\streams_candidates.geojson",
    "contour": R + r"\evidence\regional-foundation-v1\water-surfaces-contour-v2.geojson",
    "ocean": R + r"\tests\regional_outline_smoothing_v33\reference.npz",
}


# --------------------------------------------------------------------------- inputs
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def design_geometries(args):
    """List of (shapely geometry, designed class name) from the three vector inputs."""
    geoms = []
    with open(args.water_v3, encoding="utf-8") as f:
        for ft in json.load(f)["features"]:
            c = str((ft.get("properties") or {}).get("class", ""))
            name = "delta" if c.startswith("delta") else (
                c if c in ("navigable", "river", "pond") else None)
            if name and ft.get("geometry"):
                geoms.append((shape(ft["geometry"]), name))
    with open(args.streams, encoding="utf-8") as f:
        for ft in json.load(f)["features"]:
            if (ft.get("properties") or {}).get("tier_m", -1) >= 2500 and ft.get("geometry"):
                geoms.append((shape(ft["geometry"]), "stream"))
    with open(args.contour, encoding="utf-8") as f:
        for ft in json.load(f)["features"]:
            if str((ft.get("properties") or {}).get("body", "")).startswith("lake") \
                    and ft.get("geometry"):
                geoms.append((shape(ft["geometry"]), "lake"))
    return geoms


def load_pieces(channels_dir):
    """Build engine_water_model.Piece objects from <dir>/axes.json (empty if no dir)."""
    if not channels_dir:
        return []
    with open(os.path.join(channels_dir, "axes.json"), encoding="utf-8") as f:
        axes = json.load(f)
    return [Piece(pp["type"], pp["matrix"])
            for reach in axes.values() for pp in reach.get("pieces", [])]


# --------------------------------------------------------------------------- designed water
def sea_designed_mask(ocean):
    """f = gaussian(ocean, 1.5) on the vertex grid, bilinear at 2 m pixel centres, f >= 0.5."""
    out = np.zeros((S, S), bool)
    if ocean.any():
        f = ndi.gaussian_filter(ocean.astype(np.float64), 1.5)
        r = np.clip((1 + 2 * np.arange(S)) / 6.0, 0, N - 1.000001)  # row from z
        c = np.clip((1 + 2 * np.arange(S)) / 6.0, 0, N - 1.000001)  # col from x
        r0 = np.floor(r).astype(np.intp)
        c0 = np.floor(c).astype(np.intp)
        fr = (r - r0)[:, None]
        fc = (c - c0)[None, :]
        top = f[r0] * (1.0 - fr)          # (S, N)
        bot = f[r0 + 1] * fr
        out = (top[:, c0] * (1.0 - fc) + bot[:, c0] * fc) >= 0.5
    return out


def design_raster(geoms, ocean):
    """uint8 class-code raster (low priority painted first, sea mask last) + design bool."""
    items = sorted(((g, NAME2CODE[n]) for g, n in geoms), key=lambda t: t[1])
    if items:
        code = rasterize(items, out_shape=(S, S), transform=TRANSFORM,
                         fill=0, dtype="uint8")
    else:
        code = np.zeros((S, S), np.uint8)
    code[sea_designed_mask(ocean)] = 7
    return code, code > 0


# --------------------------------------------------------------------------- visible water
def visible_fields(heights, cls, level, p, pieces):
    """Per-pixel visible surface height, terrain height, cause code and visible bool."""
    sea_level, eps = p["sea_level"], p["eps"]
    planes = cell_planes(cls, level.astype(np.float64), sea_cut=p["sea_cut"])
    surf = np.full((S, S), sea_level, np.float32)
    ter = np.empty((S, S), np.float32)
    cause = np.zeros((S, S), np.uint8)
    visib = np.zeros((S, S), bool)
    boxes = [pc.box for pc in pieces]
    for j0 in range(0, S, TILE):
        j1 = min(j0 + TILE, S)
        for i0 in range(0, S, TILE):
            i1 = min(i0 + TILE, S)
            xs = 1.0 + 2.0 * np.arange(i0, i1)
            zs = 12281.0 - 2.0 * np.arange(j0, j1)
            X, Z = np.meshgrid(xs, zs)
            t = tri_sample(heights, X, Z)
            ph = planes[np.clip((1 + 2 * np.arange(j0, j1)) // 6, 0, N - 2)][:,
                 np.clip((1 + 2 * np.arange(i0, i1)) // 6, 0, N - 2)]
            ch = np.full(X.shape, np.nan)
            if boxes:
                um = np.zeros(X.shape, bool)
                for (xmin, zmin, xmax, zmax) in boxes:
                    um |= (X >= xmin) & (X <= xmax) & (Z >= zmin) & (Z <= zmax)
                jj, ii = np.nonzero(um)
                for k in range(jj.size):
                    hit = top_visual(pieces, float(X[jj[k], ii[k]]), float(Z[jj[k], ii[k]]))
                    if hit is not None:
                        ch[jj[k], ii[k]] = hit[0]
            sf = np.fmax(np.fmax(sea_level, ph), ch)      # fmax ignores NaN planes
            vis = sf > t + eps
            cz = np.zeros(vis.shape, np.uint8)
            cz[vis & (sea_level > t + eps)] = 1           # sea plane alone exceeds terrain
            rest = vis & (cz == 0)
            cz[rest & (ph > sea_level) & ~(np.isfinite(ch) & (ch > ph))] = 2
            cz[rest & (cz == 0)] = 3                      # channel is the raiser
            surf[j0:j1, i0:i1] = sf
            ter[j0:j1, i0:i1] = t
            cause[j0:j1, i0:i1] = cz
            visib[j0:j1, i0:i1] = vis
    return surf, ter, cause, visib


# --------------------------------------------------------------------------- analysis
def waterline_mask(visible, dd):
    """Visible pixels with a 4-neighbour not visible, within 30 m of the design boundary."""
    vp = np.pad(visible, 1, constant_values=False)
    enclosed = vp[:-2, 1:-1] & vp[2:, 1:-1] & vp[1:-1, :-2] & vp[1:-1, 2:]
    return visible & ~enclosed & (dd <= 30.0)


def pstats(v):
    if v.size == 0:
        return {"n": 0, "p50": 0.0, "p90": 0.0, "p99": 0.0, "max": 0.0}
    p50, p90, p99 = np.percentile(v, (50, 90, 99))
    return {"n": int(v.size), "p50": round(float(p50), 3), "p90": round(float(p90), 3),
            "p99": round(float(p99), 3), "max": round(float(v.max()), 3)}


def waterline_stats(wl, design, code, dd):
    empty = {"n": 0, "p50": 0.0, "p90": 0.0, "p99": 0.0, "max": 0.0}
    if not (wl.any() and design.any()):
        return {name: dict(empty) for name in list(CODE2NAME.values()) + ["all"]}
    _, idx = ndi.distance_transform_edt(~design, return_indices=True)
    cls_wl = code[idx[0][wl], idx[1][wl]]
    d = dd[wl].astype(np.float64)
    out = {name: pstats(d[cls_wl == c]) for c, name in CODE2NAME.items()}
    out["all"] = pstats(d)
    return out


def component_report(mask, depth, vals, names, key):
    """8-connected components of mask: top 40 by area + total count."""
    lab, n = ndi.label(mask, structure=STRUCT8)
    if n == 0:
        return [], 0
    rr, cc = np.nonzero(mask)
    l_at = lab[rr, cc]
    cnt = np.bincount(l_at, minlength=n + 1)
    sumx = np.bincount(l_at, weights=1.0 + 2.0 * cc, minlength=n + 1)
    sumz = np.bincount(l_at, weights=12281.0 - 2.0 * rr, minlength=n + 1)
    dom = np.bincount(l_at * 8 + vals, minlength=(n + 1) * 8) \
        .reshape(n + 1, 8)[:, 1:].argmax(axis=1) + 1
    maxd = ndi.maximum(depth, lab, index=np.arange(1, n + 1))
    slices = ndi.find_objects(lab)
    comps = []
    for L in range(1, n + 1):
        sl = slices[L - 1]
        comps.append({
            "pixels": int(cnt[L]),
            "area_m2": float(cnt[L] * 4),
            "centroid": [round(float(sumx[L] / cnt[L]), 1), round(float(sumz[L] / cnt[L]), 1)],
            "bbox": [round(float(1 + 2 * sl[1].start), 1),
                     round(float(12281 - 2 * (sl[0].stop - 1)), 1),
                     round(float(1 + 2 * (sl[1].stop - 1)), 1),
                     round(float(12281 - 2 * sl[0].start), 1)],
            "max_depth": round(float(maxd[L - 1]), 3),
            key: names[int(dom[L])],
        })
    comps.sort(key=lambda c: -c["area_m2"])
    return comps[:40], n


def run_pipeline(heights, cls, level, ocean, geoms, pieces, p):
    """Shared pipeline: returns (results dict for audit.json, dict of 4 full-res bool masks)."""
    code, design = design_raster(geoms, ocean)
    surf, ter, cause, visible = visible_fields(heights, cls, level, p, pieces)

    if design.any():
        dd = (np.where(design,
                       ndi.distance_transform_edt(design),
                       ndi.distance_transform_edt(~design)) * 2.0).astype(np.float32)
    else:
        dd = np.full((S, S), 1e9, np.float32)

    tol = p["tol"]
    flooded = visible & ~design & (dd > tol)
    holes = ~visible & design & (dd > tol)

    wl = waterline_mask(visible, dd)
    wl_stats = waterline_stats(wl, design, code, dd)

    cb = np.bincount(cause[flooded], minlength=4)
    flooded_by_cause = {CAUSE2NAME[c]: int(cb[c]) for c in (1, 2, 3)}
    hcode = code[holes]
    holes_by_class = {name: int((hcode == c).sum()) for c, name in CODE2NAME.items()}

    fcomps, fn = component_report(flooded, surf - ter,
                                  cause[flooded].astype(np.int64), CAUSE2NAME, "cause")
    hcomps, hn = component_report(holes, ter - surf,
                                  hcode.astype(np.int64), CODE2NAME, "cls")

    res = {
        "pixels": {"visible": int(visible.sum()), "design": int(design.sum()),
                   "flooded": int(flooded.sum()), "holes": int(holes.sum())},
        "area_m2": {"flooded": float(int(flooded.sum()) * 4),
                    "holes": float(int(holes.sum()) * 4)},
        "flooded_by_cause": flooded_by_cause,
        "holes_by_class": holes_by_class,
        "waterline_m_by_class": wl_stats,
        "flooded_components": fcomps,
        "holes_components": hcomps,
        "counts": {"flooded_components": fn, "holes_components": hn},
    }
    masks = {"visible": visible, "design": design, "flooded": flooded, "holes": holes}
    return res, masks


# --------------------------------------------------------------------------- outputs
def overview_rgb(masks):
    def blockmax(b):
        padded = np.zeros((6144, 6144), bool)          # 6141 -> pad to 3*2048
        padded[:S, :S] = b
        return padded.reshape(2048, 3, 2048, 3).max(axis=(1, 3))

    img = np.full((2048, 2048, 3), 128, np.uint8)
    img[blockmax(masks["visible"])] = (40, 90, 200)
    img[blockmax(masks["flooded"])] = (255, 0, 0)
    img[blockmax(masks["holes"])] = (255, 220, 0)
    return img


def write_outputs(out, res, masks, terrain_label, sha, params, seconds):
    doc = {"terrain": terrain_label, "terrain_sha256": sha, "params": params,
           **res, "seconds": round(seconds, 1)}
    with open(os.path.join(out, "audit.json"), "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1)
    np.savez_compressed(os.path.join(out, "masks.npz"), **masks)
    Image.fromarray(overview_rgb(masks), "RGB").save(os.path.join(out, "overview.png"))


# --------------------------------------------------------------------------- self-test
def selftest(args, params, t0):
    heights = np.full((N, N), 5.0, np.float32)
    level = np.full((N, N), np.nan, np.float32)
    cls = np.zeros((N, N), np.uint8)
    vx = 6.0 * np.arange(N)
    vz = 12282.0 - 6.0 * np.arange(N)
    X, Z = np.meshgrid(vx, vz)
    lake = (X >= 3000) & (X <= 3600) & (Z >= 3000) & (Z <= 3600)
    cls[lake] = 2
    level[lake] = 4.0
    heights[lake] = 3.0
    heights[(X >= 6000) & (X <= 6060) & (Z >= 6000) & (Z <= 6060)] = 0.3  # flood dip
    ocean = np.zeros((N, N), bool)
    geoms = [(box(3000.0, 3000.0, 3600.0, 3600.0), "lake")]

    res, _ = run_pipeline(heights, cls, level, ocean, geoms, [], params)

    fc = res["flooded_components"]
    assert fc, "expected at least one flooded component"
    near = min(fc, key=lambda c: (c["centroid"][0] - 6030.0) ** 2
               + (c["centroid"][1] - 6030.0) ** 2)
    assert 2000.0 <= near["area_m2"] <= 5000.0, near
    assert near["cause"] == "sea", near
    assert all(not (2900 <= c["centroid"][0] <= 3700 and 2900 <= c["centroid"][1] <= 3700)
               for c in fc), "flooded component inside the designed lake"
    assert res["area_m2"]["holes"] < 0.01 * 3600.0 * 3600.0, res["area_m2"]["holes"]
    assert res["waterline_m_by_class"]["lake"]["p90"] <= 6.0

    doc = {"terrain": "<synthetic>",
           "terrain_sha256": hashlib.sha256(heights.tobytes()).hexdigest(),
           "params": params, **res, "seconds": round(time.time() - t0, 1)}
    with open(os.path.join(args.out, "audit.json"), "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1)
    print("SELFTEST PASS")


# --------------------------------------------------------------------------- CLI
def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        description="Audit engine-visible water against the designed water outline (2 m grid).")
    ap.add_argument("--terrain", help="terrain NPZ (required without --selftest)")
    ap.add_argument("--out", required=True, help="output directory (must not exist)")
    ap.add_argument("--water-v3", default=DEFAULTS["water_v3"])
    ap.add_argument("--streams", default=DEFAULTS["streams"])
    ap.add_argument("--contour", default=DEFAULTS["contour"])
    ap.add_argument("--ocean", default=DEFAULTS["ocean"])
    ap.add_argument("--sea-level", type=float, default=0.54)
    ap.add_argument("--sea-cut", type=float, default=0.80)
    ap.add_argument("--eps", type=float, default=0.005)
    ap.add_argument("--tol", type=float, default=3.0)
    ap.add_argument("--channels", default=None, help="directory containing axes.json")
    ap.add_argument("--selftest", action="store_true")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    t0 = time.time()
    try:
        os.makedirs(args.out)                      # fails if OUTDIR exists
    except FileExistsError:
        sys.exit(f"OUTDIR already exists: {args.out}")
    params = {"sea_level": args.sea_level, "sea_cut": args.sea_cut, "eps": args.eps,
              "tol": args.tol, "grid_m": 2, "channels": args.channels}

    if args.selftest:
        selftest(args, params, t0)
        return

    if not args.terrain:
        sys.exit("--terrain is required (or use --selftest)")
    for key in ("water_v3", "streams", "contour", "ocean"):
        if not os.path.exists(getattr(args, key)):
            sys.exit(f"missing input --{key.replace('_', '-')}: {getattr(args, key)}")

    with np.load(args.terrain) as d:
        heights, cls, level = d["heights"], d["cls"], d["level"]
    with np.load(args.ocean) as o:
        ocean = o["ocean"].astype(bool)
    geoms = design_geometries(args)
    pieces = load_pieces(args.channels)

    res, masks = run_pipeline(heights, cls, level, ocean, geoms, pieces, params)
    write_outputs(args.out, res, masks, args.terrain,
                  sha256_file(args.terrain), params, time.time() - t0)


if __name__ == "__main__":
    main()

"""Surface V30: 1 m/px satellite and four-surface mask tiles in V29's layer layout.

Layout (from V29's layer materials): 32 x 32 tiles of 512 px at 1 m, step 384 m, 64 m overlap; tile (a, b) has
column a (x) and row b from the north: x0 = 384a - 64, z_top = 12288 - 384b + 64. Every V29 tile material holds the
four surfaces in a fixed order, so only the s_/m_ textures change and V29's materials and WRP material grid stay valid.

Classes per 1 m pixel:
  water   terrain on the native triangles below the local water level, inside the cells the pieces cover, or below
          the nominal sea (physical classification, not a guarantee of rendered water)
  shore   terrain less than 0.30 m above the water level, within 15 m of water
  road    within 3.5 m of a graded road centre line (Codex's chains)
  land    WorldCover 2021 on the crop (one class per 6 m vertex), majority-filtered over 5 x 5 vertices, boundaries
          warped by smooth noise (+-6 m); built-up is grass here (towns get buildings at mapping time)
Surfaces (V29 legend): 0 cp_gravel black, 1 cp_conifer_common1 red, 2 cp_grass green, 3 cp_grass_tall blue.
Colours: Chernarus+ satellite tones (dark olive), modulated by multi-octave value noise; fields carry row stripes.
Options: --bed-tone land paints the bed of lakes and ponds with the surrounding land colour and surface (darkened
with depth) instead of the dark gravel bed, so a pond whose water object is not drawn does not read as a hole;
--bed-tone depth blends that land colour (water up to 0.3 m deep) into the dark bed (1.2 m deep or more), for beds
raised above the sea (BALTIC-018), where 'land' would paint whole lakes in the land colour; --bed-tone depth-all
does the same under rivers and streams too, whose dark bed drew every shallow channel as a dark stroke with a rim
(v8 run ae5e7e32); deep navigable reaches stay dark;
--bed-surface gravel keeps that land colour but the gravel surface under the water, whose CfgSurfaces character is
"Empty" (DZ/surfaces/config.cpp, class cp_gravel): no grass or bushes stand out of shallow ponds;
--shore-ring flowing keeps the gravel shore band only next to rivers, streams, the delta and the sea;
--landcover smooth picks the land class from blurred per-class fields instead of the nearest 6 m vertex, so the
boundaries come out organic instead of 6 m teeth seen from the air (--landcover-sigma S, in vertices, default 1.0,
sets the blur width).
--water-plane and --water-plane-sha256 consume an immutable, verified physical water-cell field instead of
reconstructing it from cls/level. Use both for builds whose compiled water was frozen separately from terrain.
Usage: build_surface_v30.py <terrain_v30.npz> <out_dir> [--tiles a,b;a,b] [--workers 12] [--bed-tone land|depth|depth-all]
                             [--bed-surface gravel] [--shore-ring flowing] [--landcover smooth] [--landcover-sigma S]
                             [--water-plane plane.npy --water-plane-sha256 SHA256]
Output: <out>/layers/s_aaa_bbb_lco.png, m_aaa_bbb_lca.png, <out>/preview_sat.png, preview_mask.png, surface.json
"""
import json
import hashlib
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from scipy.ndimage import distance_transform_edt, gaussian_filter, uniform_filter
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from v30_common import N, R, cell_planes, tri_sample  # noqa: E402
from verify_roads_v30 import road_chains  # noqa: E402

TILE, STEP, OVER = 512, 384, 64
SEA_LEVEL = 0.75
SLOT_RGB = np.array([[0, 0, 0], [255, 0, 0], [0, 255, 0], [0, 0, 255]], np.uint8)
# WorldCover class -> (surface slot, satellite colour)
LAND = {10: (1, (27, 33, 17)), 20: (3, (44, 48, 25)), 30: (2, (56, 60, 30)), 40: (3, (74, 71, 37)),
        50: (2, (60, 62, 44)), 60: (0, (78, 72, 56)), 80: (2, (54, 59, 31)), 90: (3, (40, 47, 28)), 0: (2, (56, 60, 30))}
ROAD_RGB, SHORE_RGB, BED_RGB = (92, 86, 70), (60, 55, 41), (31, 35, 27)
G = {}


def read_water_plane(path, expected_sha256):
    """Read the physical cell field verified against the packaged water models."""
    if not path or not expected_sha256:
        raise ValueError("--water-plane and --water-plane-sha256 must be supplied together")
    raw = Path(path).read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_sha256.lower():
        raise ValueError(f"Water plane SHA256 mismatch: {actual}")
    from io import BytesIO
    plane = np.load(BytesIO(raw), allow_pickle=False)
    if not isinstance(plane, np.ndarray) or plane.shape != (N - 1, N - 1):
        raise ValueError("Water plane must have one value per native terrain cell")
    if plane.dtype.kind != "f" or np.isinf(plane).any() or not np.isfinite(plane).any():
        raise ValueError("Water plane must contain finite floating heights and NaN outside water")
    return plane


def load(terrain, water_plane=None, water_plane_sha256=None):
    t = np.load(terrain)
    h = t["heights"].astype(np.float64)
    cls, level = t["cls"], t["level"].astype(np.float64)
    water = cls > 0
    _, idx = distance_transform_edt(~water, return_indices=True)
    G["h"] = h
    G["lvl"] = level[idx[0], idx[1]]
    G["wcls"] = cls[idx[0], idx[1]]
    G["wdist"] = distance_transform_edt(~water) * 6.0
    G["plane"] = (read_water_plane(water_plane, water_plane_sha256)
                  if water_plane or water_plane_sha256 else cell_planes(cls, level))
    with rasterio.open(os.path.join(R, "derived", "gis", "worldcover_2021_3857.tif")) as ds:
        wc = ds.read(1)
    assert wc.shape == (N, N)
    classes = np.array(sorted(LAND))
    votes = np.stack([uniform_filter((wc == k).astype(np.float32), size=5, mode="nearest") for k in classes])
    G["wc"] = classes[np.argmax(votes, axis=0)].astype(np.uint8)
    if G.get("landcover") == "smooth":
        # blurred per-class fields, one float16 slice per class (~75 MB), for the bilinear pick in tile()
        fields = np.empty((len(classes), N, N), np.float16)
        for i, k in enumerate(classes):
            fields[i] = gaussian_filter((G["wc"] == k).astype(np.float32), G["landcover_sigma"])
        G["wcf"], G["wcf_classes"] = fields, classes
    pts = []
    for p in road_chains():
        if len(p) < 2:
            continue
        st = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
        s = np.arange(0, st[-1], 0.5)
        pts.append(np.column_stack([np.interp(s, st, p[:, 0]), np.interp(s, st, p[:, 1])]))
    G["roads"] = cKDTree(np.vstack(pts))
    rng = np.random.default_rng(30)
    G["grids"] = {k: rng.random((1024, 1024)) for k in ("a", "b", "c", "d", "wx", "wz", "ang")}


def noise(x, z, cell, key):
    g = G["grids"][key]
    fx, fz = x / cell, z / cell
    ix, iz = np.floor(fx).astype(np.int64), np.floor(fz).astype(np.int64)
    tx, tz = fx - ix, fz - iz
    tx, tz = tx * tx * (3 - 2 * tx), tz * tz * (3 - 2 * tz)
    m = 1024
    a = g[iz % m, ix % m]
    b = g[iz % m, (ix + 1) % m]
    c = g[(iz + 1) % m, ix % m]
    d = g[(iz + 1) % m, (ix + 1) % m]
    return 2 * ((a * (1 - tx) + b * tx) * (1 - tz) + (c * (1 - tx) + d * tx) * tz) - 1


def tile(ab):
    a, b = ab
    pad = 8
    n = TILE + 2 * pad
    x0, ztop = STEP * a - OVER - pad, N * 6 - STEP * b + OVER + pad
    px = np.arange(n) + 0.5
    X, Z = np.meshgrid(x0 + px, ztop - px)
    Xc, Zc = np.clip(X, 0, 12282), np.clip(Z, 0, 12282)
    h1 = tri_sample(G["h"], Xc, Zc)
    rr = np.clip(np.rint((12282 - Zc) / 6).astype(int), 0, N - 1)
    cc = np.clip(np.rint(Xc / 6).astype(int), 0, N - 1)
    lvl, wd = G["lvl"][rr, cc], G["wdist"][rr, cc]
    standing = np.isin(G["wcls"][rr, cc], (2, 7))   # nearest water is a lake or a pond
    cr = np.clip(np.floor((12282 - Zc) / 6).astype(int), 0, N - 2)
    ccl = np.clip(np.floor(Xc / 6).astype(int), 0, N - 2)
    plane = G["plane"][cr, ccl]
    water = (np.isfinite(plane) & (h1 < np.nan_to_num(plane, nan=-1e9))) | (h1 < SEA_LEVEL)
    lvl = np.where(np.isfinite(plane), plane, lvl)
    shore = ~water & (h1 < lvl + 0.30) & (wd <= 15.0)
    if G.get("shore_ring") == "flowing":
        shore &= ~standing
    d, _ = G["roads"].query(np.column_stack([Xc.ravel(), Zc.ravel()]), distance_upper_bound=6.0)
    d = d.reshape(X.shape)
    road = d <= 3.5
    # land classes with warped boundaries
    wx = 6.0 * noise(X, Z, 23.0, "wx") + 2.0 * noise(X, Z, 7.0, "wz")
    wz = 6.0 * noise(X, Z, 23.0, "wz") + 2.0 * noise(X, Z, 7.0, "wx")
    if G.get("landcover") == "smooth":
        # bilinear pick from the blurred class fields at the warped coordinates
        fr, fc = (12282 - (Zc + wz)) / 6, (Xc + wx) / 6
        r0 = np.clip(np.floor(fr).astype(int), 0, N - 2)
        c0 = np.clip(np.floor(fc).astype(int), 0, N - 2)
        tr, tc = np.clip(fr - r0, 0, 1), np.clip(fc - c0, 0, 1)
        best, bestv = np.zeros(X.shape, np.uint8), np.full(X.shape, -1.0, np.float32)
        for i, k in enumerate(G["wcf_classes"]):
            f = G["wcf"][i]
            v = (f[r0, c0].astype(np.float32) * (1 - tr) * (1 - tc) + f[r0, c0 + 1].astype(np.float32) * (1 - tr) * tc
                 + f[r0 + 1, c0].astype(np.float32) * tr * (1 - tc) + f[r0 + 1, c0 + 1].astype(np.float32) * tr * tc)
            m = v > bestv
            best[m], bestv[m] = k, v[m]
        wc = best
    else:
        lr = np.clip(np.rint((12282 - (Zc + wz)) / 6).astype(int), 0, N - 1)
        lc = np.clip(np.rint((Xc + wx) / 6).astype(int), 0, N - 1)
        wc = G["wc"][lr, lc]
    slot = np.full(X.shape, 2, np.uint8)
    rgb = np.zeros(X.shape + (3,), np.float64)
    for k, (s, col) in LAND.items():
        m = wc == k
        slot[m] = s
        rgb[m] = col
    other = ~np.isin(wc, list(LAND))
    rgb[other] = LAND[30][1]
    # modulation: broad patches, medium blotches, fine grain; field rows on cropland
    n1, n2, n3 = noise(X, Z, 90.0, "a"), noise(X, Z, 21.0, "b"), noise(X, Z, 4.0, "c")
    mod = 1 + 0.10 * n1 + 0.07 * n2 + 0.05 * n3
    crop = wc == 40
    ang = np.pi * noise(X, Z, 160.0, "ang")
    rows = np.sin(2 * np.pi * (X * np.cos(ang) + Z * np.sin(ang)) / 3.2)
    mod = np.where(crop, mod + 0.06 * rows, mod)
    forest = wc == 10
    mod = np.where(forest, mod + 0.12 * np.clip(noise(X, Z, 9.0, "d"), -1, 0.4), mod)
    rgb *= mod[..., None]
    land_rgb, land_slot = rgb.copy(), slot.copy()
    # shore, road and water override the land
    rgb[shore] = SHORE_RGB
    slot[shore] = 0
    edge = np.clip((3.5 - d) / 1.0, 0, 1)[..., None]
    rgb = np.where(road[..., None], rgb * (1 - edge) + np.array(ROAD_RGB) * edge, rgb)
    slot[road] = 0
    depth = np.clip(lvl - h1, 0, 3) / 3
    bed = np.array(BED_RGB) * (1 - 0.35 * depth[..., None])
    rgb[water] = bed[water]
    slot[water] = 0
    if G.get("bed_tone") in ("land", "depth", "depth-all"):
        still = water & ~(h1 < SEA_LEVEL)
        if G.get("bed_tone") != "depth-all":
            still &= standing
        tone = land_rgb * (0.85 - 0.15 * depth[..., None])
        if G.get("bed_tone") in ("depth", "depth-all"):
            w = np.clip((lvl - h1 - 0.3) / 0.9, 0, 1)[..., None]
            tone = tone * (1 - w) + bed * w
        rgb[still] = tone[still]
        if G.get("bed_surface") != "gravel":
            slot[still] = land_slot[still]
    rgb *= (1 + 0.025 * noise(X, Z, 1.3, "c"))[..., None]
    for ch in range(3):
        rgb[..., ch] = gaussian_filter(rgb[..., ch], 0.8)
    rgb = np.clip(np.rint(rgb), 0, 255).astype(np.uint8)[pad:-pad, pad:-pad]
    slot = slot[pad:-pad, pad:-pad]
    out = G["out"]
    Image.fromarray(rgb, "RGB").save(os.path.join(out, f"s_{a:03d}_{b:03d}_lco.png"))
    mask = np.concatenate([SLOT_RGB[slot], np.full(slot.shape + (1,), 255, np.uint8)], axis=2)
    Image.fromarray(mask, "RGBA").save(os.path.join(out, f"m_{a:03d}_{b:03d}_lca.png"))
    counts = np.bincount(slot.ravel(), minlength=4)
    return a, b, counts.tolist(), int(water[pad:-pad, pad:-pad].sum()), rgb[::16, ::16], slot[::16, ::16]


def init(terrain, out, bed_tone=None, shore_ring=None, bed_surface=None, landcover=None, landcover_sigma=1.0,
         water_plane=None, water_plane_sha256=None):
    G["landcover"], G["landcover_sigma"] = landcover, landcover_sigma
    load(terrain, water_plane, water_plane_sha256)
    G["out"] = out
    G["bed_tone"], G["shore_ring"], G["bed_surface"] = bed_tone, shore_ring, bed_surface


def main():
    terrain, out = sys.argv[1], sys.argv[2]
    water_plane = sys.argv[sys.argv.index("--water-plane") + 1] if "--water-plane" in sys.argv else None
    water_plane_sha256 = (sys.argv[sys.argv.index("--water-plane-sha256") + 1]
                          if "--water-plane-sha256" in sys.argv else None)
    if water_plane or water_plane_sha256:
        # Fail in the parent before the pool: a broken initializer otherwise keeps respawning workers.
        read_water_plane(water_plane, water_plane_sha256)
    layers = os.path.join(out, "layers")
    os.makedirs(layers, exist_ok=True)
    tiles = [(a, b) for b in range(32) for a in range(32)]
    if "--tiles" in sys.argv:
        tiles = [tuple(int(v) for v in t.split(",")) for t in sys.argv[sys.argv.index("--tiles") + 1].split(";")]
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 12
    bed_tone = sys.argv[sys.argv.index("--bed-tone") + 1] if "--bed-tone" in sys.argv else None
    shore_ring = sys.argv[sys.argv.index("--shore-ring") + 1] if "--shore-ring" in sys.argv else None
    bed_surface = sys.argv[sys.argv.index("--bed-surface") + 1] if "--bed-surface" in sys.argv else None
    landcover = sys.argv[sys.argv.index("--landcover") + 1] if "--landcover" in sys.argv else None
    landcover_sigma = float(sys.argv[sys.argv.index("--landcover-sigma") + 1]) if "--landcover-sigma" in sys.argv else 1.0
    t0 = time.time()
    with Pool(workers, initializer=init, initargs=(terrain, layers, bed_tone, shore_ring, bed_surface,
                                                   landcover, landcover_sigma, water_plane, water_plane_sha256)) as pool:
        res = pool.map(tile, tiles, chunksize=4)
    sat = np.zeros((32 * 24, 32 * 24, 3), np.uint8)
    msk = np.zeros((32 * 24, 32 * 24), np.uint8)
    for a, b, _, _, rgb, slot in res:
        # preview: the 384 m core of each tile, 16 m per preview pixel
        sat[b * 24:(b + 1) * 24, a * 24:(a + 1) * 24] = rgb[4:28, 4:28]
        msk[b * 24:(b + 1) * 24, a * 24:(a + 1) * 24] = slot[4:28, 4:28]
    if len(tiles) == 1024:
        Image.fromarray(sat, "RGB").save(os.path.join(out, "preview_sat.png"))
        Image.fromarray(SLOT_RGB[msk], "RGB").save(os.path.join(out, "preview_mask.png"))
    total = np.sum([r[2] for r in res], axis=0)
    report = {"tiles": len(res), "seconds": round(time.time() - t0, 1),
              "slot_pixels": {n: int(v) for n, v in zip(("gravel", "conifer", "grass", "grass_tall"), total)},
              "water_pixels": int(sum(r[3] for r in res)), "palette": {str(k): v[1] for k, v in LAND.items()},
              "road_rgb": ROAD_RGB, "shore_rgb": SHORE_RGB, "bed_rgb": BED_RGB,
              "bed_tone": bed_tone, "shore_ring": shore_ring, "bed_surface": bed_surface,
              "terrain_sha256": hashlib.sha256(Path(terrain).read_bytes()).hexdigest(),
              "water_field": {"mode": "verified_physical_cells" if water_plane else "legacy_cls_level",
                              "path": str(Path(water_plane).resolve()) if water_plane else None,
                              "sha256": water_plane_sha256.lower() if water_plane_sha256 else None}}
    if landcover:
        report["landcover"], report["landcover_sigma"] = landcover, landcover_sigma
    with open(os.path.join(out, "surface.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()

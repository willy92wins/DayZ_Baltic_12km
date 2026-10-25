IMPORTANT PROCESS NOTE: write the complete files FIRST, in one pass, then stop. Keep internal deliberation focused.
The receiver re-runs every changed tool with its DEFAULTS and compares sha256 against archived outputs: with the
defaults, terrain/water/image outputs must be byte-identical to today's. Change nothing that the task does not ask for.
Code and comments in English; keep the style of the surrounding code (comment density, naming, idiom).
Output: one fenced block per changed or new file, each preceded by the line `FILE: <repo-relative path>`, whole file.
Coordinates: game metres, x east, z north; the vertex grid is N = 2048 vertices every 6 m, row r at z = 12282 - 6r,
column c at x = 6c (tools/terrain/v30_common.py).

# Task S1: smooth land-cover boundaries in tools/terrain/build_surface_v30.py
Today tile() picks the WorldCover class of every 1 m pixel from the NEAREST 6 m vertex of the 5 x 5 majority raster
G["wc"], at coordinates warped by smooth noise (lines 124-128): boundaries come out as 6 m teeth seen from the air.
Add an option that picks it from blurred class fields instead (prototype, already checked visually by the owner:
6.7 % of the pixels change class, boundaries become organic):
```python
classes = np.array(sorted(LAND))
fr, fc = (12282 - (Zc + wz)) / 6, (Xc + wx) / 6
r0 = np.clip(np.floor(fr).astype(int), 0, N - 2); c0 = np.clip(np.floor(fc).astype(int), 0, N - 2)
tr, tc = np.clip(fr - r0, 0, 1), np.clip(fc - c0, 0, 1)
best, bestv = zeros(uint8), full(-1.0)
for i, k in enumerate(classes):
    f = field_k            # gaussian_filter((G["wc"] == k).astype(np.float32), sigma), precomputed
    v = (f[r0, c0] * (1 - tr) * (1 - tc) + f[r0, c0 + 1] * (1 - tr) * tc + f[r0 + 1, c0] * tr * (1 - tc)
         + f[r0 + 1, c0 + 1] * tr * tc)
    m = v > bestv; best[m], bestv[m] = k, v[m]
wc = best
```
Requirements:
- New options in main(), parsed like --bed-tone: `--landcover smooth` (default None = today's nearest pick) and
  `--landcover-sigma S` (in vertices, default 1.0).
- load(): when G["landcover"] == "smooth", precompute the fields once per worker as ONE float16 array
  G["wcf"] of shape (len(classes), N, N) (about 75 MB) and G["wcf_classes"]; evaluate the bilinear sum in float32.
- tile(): with smooth, wc comes from the fields as above (same warped coordinates wx, wz; note Xc/Zc are the clipped
  pixel centres); everything after (slot, colour, `other`) unchanged.
- init() and the Pool initargs: append the two settings as new parameters with defaults, keep the existing order.
- surface.json: add "landcover" and "landcover_sigma" ONLY when --landcover is given (so the default report is
  byte-identical); update the module docstring (Options and Usage).

# The files to change (full listings)

### tools/terrain/build_surface_v30.py (full file, 224 lines)
```python
   1| """Surface V30: 1 m/px satellite and four-surface mask tiles in V29's layer layout.
   2| 
   3| Layout (from V29's layer materials): 32 x 32 tiles of 512 px at 1 m, step 384 m, 64 m overlap; tile (a, b) has
   4| column a (x) and row b from the north: x0 = 384a - 64, z_top = 12288 - 384b + 64. Every V29 tile material holds the
   5| four surfaces in a fixed order, so only the s_/m_ textures change and V29's materials and WRP material grid stay valid.
   6| 
   7| Classes per 1 m pixel:
   8|   water   terrain on the native triangles below the local water level, inside the cells the pieces cover, or below
   9|           the sea (exactly where the engine shows water)
  10|   shore   terrain less than 0.30 m above the water level, within 15 m of water
  11|   road    within 3.5 m of a graded road centre line (Codex's chains)
  12|   land    WorldCover 2021 on the crop (one class per 6 m vertex), majority-filtered over 5 x 5 vertices, boundaries
  13|           warped by smooth noise (+-6 m); built-up is grass here (towns get buildings at mapping time)
  14| Surfaces (V29 legend): 0 cp_gravel black, 1 cp_conifer_common1 red, 2 cp_grass green, 3 cp_grass_tall blue.
  15| Colours: Chernarus+ satellite tones (dark olive), modulated by multi-octave value noise; fields carry row stripes.
  16| Options: --bed-tone land paints the bed of lakes and ponds with the surrounding land colour and surface (darkened
  17| with depth) instead of the dark gravel bed, so a pond whose water object is not drawn does not read as a hole;
  18| --bed-tone depth blends that land colour (water up to 0.3 m deep) into the dark bed (1.2 m deep or more), for beds
  19| raised above the sea (BALTIC-018), where 'land' would paint whole lakes in the land colour; --bed-tone depth-all
  20| does the same under rivers and streams too, whose dark bed drew every shallow channel as a dark stroke with a rim
  21| (v8 run ae5e7e32); deep navigable reaches stay dark;
  22| --bed-surface gravel keeps that land colour but the gravel surface under the water, whose CfgSurfaces character is
  23| "Empty" (DZ/surfaces/config.cpp, class cp_gravel): no grass or bushes stand out of shallow ponds;
  24| --shore-ring flowing keeps the gravel shore band only next to rivers, streams, the delta and the sea.
  25| Usage: build_surface_v30.py <terrain_v30.npz> <out_dir> [--tiles a,b;a,b] [--workers 12] [--bed-tone land|depth|depth-all]
  26|                             [--bed-surface gravel] [--shore-ring flowing]
  27| Output: <out>/layers/s_aaa_bbb_lco.png, m_aaa_bbb_lca.png, <out>/preview_sat.png, preview_mask.png, surface.json
  28| """
  29| import json
  30| import os
  31| import sys
  32| import time
  33| from multiprocessing import Pool
  34| 
  35| import numpy as np
  36| import rasterio
  37| from PIL import Image
  38| from scipy.ndimage import distance_transform_edt, gaussian_filter, uniform_filter
  39| from scipy.spatial import cKDTree
  40| 
  41| HERE = os.path.dirname(os.path.abspath(__file__))
  42| sys.path.insert(0, HERE)
  43| from v30_common import N, R, cell_planes, tri_sample  # noqa: E402
  44| from verify_roads_v30 import road_chains  # noqa: E402
  45| 
  46| TILE, STEP, OVER = 512, 384, 64
  47| SEA_LEVEL = 0.75
  48| SLOT_RGB = np.array([[0, 0, 0], [255, 0, 0], [0, 255, 0], [0, 0, 255]], np.uint8)
  49| # WorldCover class -> (surface slot, satellite colour)
  50| LAND = {10: (1, (27, 33, 17)), 20: (3, (44, 48, 25)), 30: (2, (56, 60, 30)), 40: (3, (74, 71, 37)),
  51|         50: (2, (60, 62, 44)), 60: (0, (78, 72, 56)), 80: (2, (54, 59, 31)), 90: (3, (40, 47, 28)), 0: (2, (56, 60, 30))}
  52| ROAD_RGB, SHORE_RGB, BED_RGB = (92, 86, 70), (60, 55, 41), (31, 35, 27)
  53| G = {}
  54| 
  55| 
  56| def load(terrain):
  57|     t = np.load(terrain)
  58|     h = t["heights"].astype(np.float64)
  59|     cls, level = t["cls"], t["level"].astype(np.float64)
  60|     water = cls > 0
  61|     _, idx = distance_transform_edt(~water, return_indices=True)
  62|     G["h"] = h
  63|     G["lvl"] = level[idx[0], idx[1]]
  64|     G["wcls"] = cls[idx[0], idx[1]]
  65|     G["wdist"] = distance_transform_edt(~water) * 6.0
  66|     G["plane"] = cell_planes(cls, level)
  67|     with rasterio.open(os.path.join(R, "derived", "gis", "worldcover_2021_3857.tif")) as ds:
  68|         wc = ds.read(1)
  69|     assert wc.shape == (N, N)
  70|     classes = np.array(sorted(LAND))
  71|     votes = np.stack([uniform_filter((wc == k).astype(np.float32), size=5, mode="nearest") for k in classes])
  72|     G["wc"] = classes[np.argmax(votes, axis=0)].astype(np.uint8)
  73|     pts = []
  74|     for p in road_chains():
  75|         if len(p) < 2:
  76|             continue
  77|         st = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
  78|         s = np.arange(0, st[-1], 0.5)
  79|         pts.append(np.column_stack([np.interp(s, st, p[:, 0]), np.interp(s, st, p[:, 1])]))
  80|     G["roads"] = cKDTree(np.vstack(pts))
  81|     rng = np.random.default_rng(30)
  82|     G["grids"] = {k: rng.random((1024, 1024)) for k in ("a", "b", "c", "d", "wx", "wz", "ang")}
  83| 
  84| 
  85| def noise(x, z, cell, key):
  86|     g = G["grids"][key]
  87|     fx, fz = x / cell, z / cell
  88|     ix, iz = np.floor(fx).astype(np.int64), np.floor(fz).astype(np.int64)
  89|     tx, tz = fx - ix, fz - iz
  90|     tx, tz = tx * tx * (3 - 2 * tx), tz * tz * (3 - 2 * tz)
  91|     m = 1024
  92|     a = g[iz % m, ix % m]
  93|     b = g[iz % m, (ix + 1) % m]
  94|     c = g[(iz + 1) % m, ix % m]
  95|     d = g[(iz + 1) % m, (ix + 1) % m]
  96|     return 2 * ((a * (1 - tx) + b * tx) * (1 - tz) + (c * (1 - tx) + d * tx) * tz) - 1
  97| 
  98| 
  99| def tile(ab):
 100|     a, b = ab
 101|     pad = 8
 102|     n = TILE + 2 * pad
 103|     x0, ztop = STEP * a - OVER - pad, N * 6 - STEP * b + OVER + pad
 104|     px = np.arange(n) + 0.5
 105|     X, Z = np.meshgrid(x0 + px, ztop - px)
 106|     Xc, Zc = np.clip(X, 0, 12282), np.clip(Z, 0, 12282)
 107|     h1 = tri_sample(G["h"], Xc, Zc)
 108|     rr = np.clip(np.rint((12282 - Zc) / 6).astype(int), 0, N - 1)
 109|     cc = np.clip(np.rint(Xc / 6).astype(int), 0, N - 1)
 110|     lvl, wd = G["lvl"][rr, cc], G["wdist"][rr, cc]
 111|     standing = np.isin(G["wcls"][rr, cc], (2, 7))   # nearest water is a lake or a pond
 112|     cr = np.clip(np.floor((12282 - Zc) / 6).astype(int), 0, N - 2)
 113|     ccl = np.clip(np.floor(Xc / 6).astype(int), 0, N - 2)
 114|     plane = G["plane"][cr, ccl]
 115|     water = (np.isfinite(plane) & (h1 < np.nan_to_num(plane, nan=-1e9))) | (h1 < SEA_LEVEL)
 116|     lvl = np.where(np.isfinite(plane), plane, lvl)
 117|     shore = ~water & (h1 < lvl + 0.30) & (wd <= 15.0)
 118|     if G.get("shore_ring") == "flowing":
 119|         shore &= ~standing
 120|     d, _ = G["roads"].query(np.column_stack([Xc.ravel(), Zc.ravel()]), distance_upper_bound=6.0)
 121|     d = d.reshape(X.shape)
 122|     road = d <= 3.5
 123|     # land classes with warped boundaries
 124|     wx = 6.0 * noise(X, Z, 23.0, "wx") + 2.0 * noise(X, Z, 7.0, "wz")
 125|     wz = 6.0 * noise(X, Z, 23.0, "wz") + 2.0 * noise(X, Z, 7.0, "wx")
 126|     lr = np.clip(np.rint((12282 - (Zc + wz)) / 6).astype(int), 0, N - 1)
 127|     lc = np.clip(np.rint((Xc + wx) / 6).astype(int), 0, N - 1)
 128|     wc = G["wc"][lr, lc]
 129|     slot = np.full(X.shape, 2, np.uint8)
 130|     rgb = np.zeros(X.shape + (3,), np.float64)
 131|     for k, (s, col) in LAND.items():
 132|         m = wc == k
 133|         slot[m] = s
 134|         rgb[m] = col
 135|     other = ~np.isin(wc, list(LAND))
 136|     rgb[other] = LAND[30][1]
 137|     # modulation: broad patches, medium blotches, fine grain; field rows on cropland
 138|     n1, n2, n3 = noise(X, Z, 90.0, "a"), noise(X, Z, 21.0, "b"), noise(X, Z, 4.0, "c")
 139|     mod = 1 + 0.10 * n1 + 0.07 * n2 + 0.05 * n3
 140|     crop = wc == 40
 141|     ang = np.pi * noise(X, Z, 160.0, "ang")
 142|     rows = np.sin(2 * np.pi * (X * np.cos(ang) + Z * np.sin(ang)) / 3.2)
 143|     mod = np.where(crop, mod + 0.06 * rows, mod)
 144|     forest = wc == 10
 145|     mod = np.where(forest, mod + 0.12 * np.clip(noise(X, Z, 9.0, "d"), -1, 0.4), mod)
 146|     rgb *= mod[..., None]
 147|     land_rgb, land_slot = rgb.copy(), slot.copy()
 148|     # shore, road and water override the land
 149|     rgb[shore] = SHORE_RGB
 150|     slot[shore] = 0
 151|     edge = np.clip((3.5 - d) / 1.0, 0, 1)[..., None]
 152|     rgb = np.where(road[..., None], rgb * (1 - edge) + np.array(ROAD_RGB) * edge, rgb)
 153|     slot[road] = 0
 154|     depth = np.clip(lvl - h1, 0, 3) / 3
 155|     bed = np.array(BED_RGB) * (1 - 0.35 * depth[..., None])
 156|     rgb[water] = bed[water]
 157|     slot[water] = 0
 158|     if G.get("bed_tone") in ("land", "depth", "depth-all"):
 159|         still = water & ~(h1 < SEA_LEVEL)
 160|         if G.get("bed_tone") != "depth-all":
 161|             still &= standing
 162|         tone = land_rgb * (0.85 - 0.15 * depth[..., None])
 163|         if G.get("bed_tone") in ("depth", "depth-all"):
 164|             w = np.clip((lvl - h1 - 0.3) / 0.9, 0, 1)[..., None]
 165|             tone = tone * (1 - w) + bed * w
 166|         rgb[still] = tone[still]
 167|         if G.get("bed_surface") != "gravel":
 168|             slot[still] = land_slot[still]
 169|     rgb *= (1 + 0.025 * noise(X, Z, 1.3, "c"))[..., None]
 170|     for ch in range(3):
 171|         rgb[..., ch] = gaussian_filter(rgb[..., ch], 0.8)
 172|     rgb = np.clip(np.rint(rgb), 0, 255).astype(np.uint8)[pad:-pad, pad:-pad]
 173|     slot = slot[pad:-pad, pad:-pad]
 174|     out = G["out"]
 175|     Image.fromarray(rgb, "RGB").save(os.path.join(out, f"s_{a:03d}_{b:03d}_lco.png"))
 176|     mask = np.concatenate([SLOT_RGB[slot], np.full(slot.shape + (1,), 255, np.uint8)], axis=2)
 177|     Image.fromarray(mask, "RGBA").save(os.path.join(out, f"m_{a:03d}_{b:03d}_lca.png"))
 178|     counts = np.bincount(slot.ravel(), minlength=4)
 179|     return a, b, counts.tolist(), int(water[pad:-pad, pad:-pad].sum()), rgb[::16, ::16], slot[::16, ::16]
 180| 
 181| 
 182| def init(terrain, out, bed_tone=None, shore_ring=None, bed_surface=None):
 183|     load(terrain)
 184|     G["out"] = out
 185|     G["bed_tone"], G["shore_ring"], G["bed_surface"] = bed_tone, shore_ring, bed_surface
 186| 
 187| 
 188| def main():
 189|     terrain, out = sys.argv[1], sys.argv[2]
 190|     layers = os.path.join(out, "layers")
 191|     os.makedirs(layers, exist_ok=True)
 192|     tiles = [(a, b) for b in range(32) for a in range(32)]
 193|     if "--tiles" in sys.argv:
 194|         tiles = [tuple(int(v) for v in t.split(",")) for t in sys.argv[sys.argv.index("--tiles") + 1].split(";")]
 195|     workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 12
 196|     bed_tone = sys.argv[sys.argv.index("--bed-tone") + 1] if "--bed-tone" in sys.argv else None
 197|     shore_ring = sys.argv[sys.argv.index("--shore-ring") + 1] if "--shore-ring" in sys.argv else None
 198|     bed_surface = sys.argv[sys.argv.index("--bed-surface") + 1] if "--bed-surface" in sys.argv else None
 199|     t0 = time.time()
 200|     with Pool(workers, initializer=init, initargs=(terrain, layers, bed_tone, shore_ring, bed_surface)) as pool:
 201|         res = pool.map(tile, tiles, chunksize=4)
 202|     sat = np.zeros((32 * 24, 32 * 24, 3), np.uint8)
 203|     msk = np.zeros((32 * 24, 32 * 24), np.uint8)
 204|     for a, b, _, _, rgb, slot in res:
 205|         # preview: the 384 m core of each tile, 16 m per preview pixel
 206|         sat[b * 24:(b + 1) * 24, a * 24:(a + 1) * 24] = rgb[4:28, 4:28]
 207|         msk[b * 24:(b + 1) * 24, a * 24:(a + 1) * 24] = slot[4:28, 4:28]
 208|     if len(tiles) == 1024:
 209|         Image.fromarray(sat, "RGB").save(os.path.join(out, "preview_sat.png"))
 210|         Image.fromarray(SLOT_RGB[msk], "RGB").save(os.path.join(out, "preview_mask.png"))
 211|     total = np.sum([r[2] for r in res], axis=0)
 212|     report = {"tiles": len(res), "seconds": round(time.time() - t0, 1),
 213|               "slot_pixels": {n: int(v) for n, v in zip(("gravel", "conifer", "grass", "grass_tall"), total)},
 214|               "water_pixels": int(sum(r[3] for r in res)), "palette": {str(k): v[1] for k, v in LAND.items()},
 215|               "road_rgb": ROAD_RGB, "shore_rgb": SHORE_RGB, "bed_rgb": BED_RGB,
 216|               "bed_tone": bed_tone, "shore_ring": shore_ring, "bed_surface": bed_surface}
 217|     with open(os.path.join(out, "surface.json"), "w", encoding="utf-8") as f:
 218|         json.dump(report, f, indent=1)
 219|     print(json.dumps(report, indent=1))
 220| 
 221| 
 222| if __name__ == "__main__":
 223|     main()
 224| 
```

# Reminder
# Task S1: smooth land-cover boundaries in tools/terrain/build_surface_v30.py
Today tile() picks the WorldCover class of every 1 m pixel from the NEAREST 6 m vertex of the 5 x 5 majority raster
G["wc"], at coordinates warped by smooth noise (lines 124-128): boundaries come out as 6 m teeth seen from the air.
Add an option that picks it from blurred class fields instead (prototype, already checked visually by the owner:
6.7 % of the pixels change class, boundaries become organic):
```python
classes = np.array(sorted(LAND))
fr, fc = (12282 - (Zc + wz)) / 6, (Xc + wx) / 6
r0 = np.clip(np.floor(fr).astype(int), 0, N - 2); c0 = np.clip(np.floor(fc).astype(int), 0, N - 2)
tr, tc = np.clip(fr - r0, 0, 1), np.clip(fc - c0, 0, 1)
best, bestv = zeros(uint8), full(-1.0)
for i, k in enumerate(classes):
    f = field_k            # gaussian_filter((G["wc"] == k).astype(np.float32), sigma), precomputed
    v = (f[r0, c0] * (1 - tr) * (1 - tc) + f[r0, c0 + 1] * (1 - tr) * tc + f[r0 + 1, c0] * tr * (1 - tc)
         + f[r0 + 1, c0 + 1] * tr * tc)
    m = v > bestv; best[m], bestv[m] = k, v[m]
wc = best
```
Requirements:
- New options in main(), parsed like --bed-tone: `--landcover smooth` (default None = today's nearest pick) and
  `--landcover-sigma S` (in vertices, default 1.0).
- load(): when G["landcover"] == "smooth", precompute the fields once per worker as ONE float16 array
  G["wcf"] of shape (len(classes), N, N) (about 75 MB) and G["wcf_classes"]; evaluate the bilinear sum in float32.
- tile(): with smooth, wc comes from the fields as above (same warped coordinates wx, wz; note Xc/Zc are the clipped
  pixel centres); everything after (slot, colour, `other`) unchanged.
- init() and the Pool initargs: append the two settings as new parameters with defaults, keep the existing order.
- surface.json: add "landcover" and "landcover_sigma" ONLY when --landcover is given (so the default report is
  byte-identical); update the module docstring (Options and Usage).

Write the whole files now.

"""EV112 forest placement across the Baltic map; approved sparse open bog design.

Writes stage_bridges_v31 records {model, matrix}: scaled model axes then position.
The validation candidate is AE, 2026-10-19 (surface-aware bush redistribution). Mechanical validation and
final terrain integration are separate from the user's in-game visual acceptance.

Inputs: --terrain (native 6 m mesh), --footprint (pond plane and envelope),
--stage-wrp (base objects, used for exclusion hulls), --pbo and repeatable
--layer-dir (shipped mask PNGs whose PAAs match the PBO), --cover (OSM wetland and
reserve rasters), --reference (Livonia palette, geometry and measured profiles),
--seed and --out. --exclude adds polygons with a margin, for the final dam and
causeways. --region filters written sample points, not the surrounding computation.

Forest: world-anchored fields and candidates. The original Livonia profiles,
palette, exclusions, target values and gate bands remain unchanged. Admission
calibration separates the base and existing10-15/15-20/20-25m tree-floor strata
inside each original texture class. Nonbush final records are generated first.
Their accepted tree centres define a global5m canopy with20m disc,60trees/ha,
components>=0.5ha and holes<100m2, matching the reference physical definition.
Bush floors and dry normalisation use that accepted canopy. The full original
exterior tree-floor bush companion is included in the target before normalising.
Each actual canopy context(interior,edge,open) uses conservative target-mass
redistribution: raw * G(target/G(raw)), with the same50m Gaussian/100m support.
The symmetric zero-padded operator preserves each context integral before
admission; two convolutions need200m support.450m raster padding covers that,
the150m profile dependency,40m maximum halo,32m candidate block and5m phase.
No arbitrary coefficient clamp or alternate target is introduced. Bog and
riparian intensities retain their original rules. Physical/consumer gates,
not conservation alone, establish acceptance.
Bush admission is recalibrated against the same final tree centres that are
written to the output. No local tree regeneration in bush-only passes.
These are generator corrections; only fresh consumer gates establish acceptance.

Bog: every OSM wetland component uses sparse pine, regardless of old forest-floor
paint. Core target is 40 trees/ha [DESIGN], pine/birch 0.92/0.08, low scales from
Livonia p1..p30; bushes 67.8/ha and dead wood 4.66/ha. Pine groups use 12 parents/ha,
5 m sigma and a 0.50 ungrouped floor. There is no separate wooded-bog generator.
The compatibility report key wooded_trees_ha therefore also reports 40.

Moss clearings use a world-anchored field smoothed over 20 m, connected patches
of at least 400 m2, a component target based on core share 0.60 and full share
0.40, and eligibility starting 5 m inside the bog. Allocation is uniform within
that eligible area. A plantable-core guard retains at least 20% after the gap.
All tree families leave 10.75 m around moss pixels (10 m design plus 0.75 m
raster allowance). Moss-covered dark floor must be repainted by the final
surface pass; successful placement alone does not prove surface agreement.

Pine intensity is normalised on the actual plantable component core and its
realised cluster field. A 50 m local correction, bounded to 0.5..2 of the
component value, then renormalised, avoids sparse halves of connected bogs.
The 25 m transition retains the original outer half. The inner profile uses
w - 5*max(w-0.5,0)^2*(1-w), w=smoothstep(depth/25). Forest and pine contributions
are separately normalised on the live pixels of the 0..12.5 and 12.5..25 m rings.
Both transition terms use a 50 m local correction, bounded to 0.5..2 of the
ring factor, then renormalised to preserve the exact component-ring integral.
Admission calibration is separate for core, outer rim and inner rim; it does
not change the expected density curve or the acceptance bands.
This repairs the generator; the original G2/G3/G7 acceptance bands are unchanged.

Tiles: default 500 m, 30 m halo and world-aligned raster padding. --calibration
reuses a prior report's K and accepted-canopy dependencies only after schema, seed, source, inputs and guide hashes match. Partition invariance must be checked against
another tile size using the same seed, region and calibration. Worker count
must not change output records. Reports include tool/input hashes and counts.

Exclusions: painted road width and low geometry faces; visible water and the
engine-sea margin; bridge and kit hulls with their clearance; corresponding
terrain masks; Narva; and --exclude polygons. Native terrain slopes and model
base support are checked before placement. The final run must use the final
terrain, pond footprint, staged objects and causeway/dam exclusions.

Outputs: records.json, report.json, instances.npy and work/*.npy rasters.
Usage: forest_v31.py --terrain T --footprint F --stage-wrp W --pbo P
  --layer-dir D [--layer-dir D ...] --cover C --reference R --seed N --out DIR
  [--region x0,z0,x1,z1] [--tile 500] [--halo 30] [--workers 4]
  [--calibration report.json] [--exclude polygons.json]
"""
import argparse
import hashlib
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import shapely
from PIL import Image
from scipy import ndimage
from scipy.spatial import ConvexHull, cKDTree
from scipy.special import ndtr, ndtri

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "terrain"))
sys.path.insert(0, r"C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts")
from build_surface_v30 import road_chains, road_tree  # noqa: E402
from odol_reader import ODOL  # noqa: E402
from patch_surface_v31 import pbo_index, pbo_read  # noqa: E402
from wrp0wzd import read as read_wrp  # noqa: E402
sys.path.insert(0, str(HERE))
from streambed_water_v31 import rasterize as rasterize_kit_water
KIT_GEOMETRY = HERE.parent / "water/streambed_kit_geometry_v31.json"

N, ZTOP, MAP = 2048, 12282, 12288
SEA, SEA_HIGH = 0.75, 1.0
FAM = ["conifer", "broadleaf", "bush", "dead", "reed"]
CLASSES = ["interior", "edge_in", "edge_out", "open", "riparian", "riparian_open", "bog_wooded", "bog_open", "bog_rim_outer", "bog_rim_inner"]
# per texture class: trees/ha, bushes/ha, dead/ha, reeds/ha, broadleaf share of trees, solitary target (nan = palette)
DESIGN = {"interior": (186.3, 32.4, 24.5, 0.0, 0.08, math.nan),
          "open": (12.2, 67.8, 4.66, 0.0, 0.46, 0.92)}
# v4 riparian (m4.json, Livonia whole map, land <= 25 m from water): 5 m bins of the distance to water
RIP_D = [2.5, 7.5, 12.5, 17.5, 22.5]
RIPARIAN_FOREST_TREES = 150.0                   # [DESIGN] trees/ha on forest texture (see the docstring, v4 point 4)
RIPARIAN_F = {"trees": [RIPARIAN_FOREST_TREES] * 5, "bush": [56.45, 73.99, 79.55, 84.59, 79.17],
              "dead": 6.19, "broadleaf": 0.6347}
RIPARIAN_O = {"trees": [36.25, 66.67, 71.21, 67.07, 59.66], "bush": [74.06, 131.62, 132.46, 109.31, 99.69],
              "dead": 6.19, "broadleaf": 0.7461}
REED_HA, REED_DECAY = 16.6, 4.0
REED_NORM = REED_DECAY / 25.0 * (1.0 - math.exp(-25.0 / REED_DECAY))   # E[exp(-d/4)] for d uniform on 0-25 m
EDGE_IN_M, EDGE_OUT_M = 25.0, 100.0             # texture-distance span of the Livonia edge profile
SPILL_SIGMA = ([-35.0, -15.0, 0.0], [1.118, 0.766, 0.231])  # log-normal sigma of the spill field vs dt (Livonia 50 m blocks)
SPILL_SMOOTH = 40.0
ROAD_SPAN = 30.0                                # m from the road edge where the Livonia road profile applies
CANOPY_SOL_SPAN = 25.0                          # v3: Livonia canopy edge context reaches 25 m into the canopy
CANOPY_BUSH = ([-20.0, -15.0, -10.0, -5.0, 5.0, 10.0, 15.0, 20.0], [54.5, 60.8, 69.6, 75.7, 81.5, 99.3, 101.8, 83.9])  # v3:
# Livonia bushes/ha by canopy distance bin (lower bound, m): forest-livonia/analysis.json edge_profile_canopy (sha256
# bf1fc3c7...); v4d extends it to -20 m (development map seed 3: edge.out_-20_-5.bush_share under Livonia's minimum in
# 5 windows, too few bushes per tree beyond the canopy edge)
CANOPY_TREES = ([10.0, 15.0, 20.0], [99.3, 207.0, 300.1])   # v4c: Livonia trees/ha by canopy bin (lower bound, m),
# conifer + broadleaf of analysis.json edge_profile_canopy (bins 10-15, 15-20, 20-25 m inside the canopy mask)
PALETTE_CUT = (5.0, -30.0)                      # dt >= 5: interior palette; -30 <= dt < 5: edge; below: open
RASTER_PAD = 450                                # 200m redistribution +150m profile +40m halo +32m candidate block +5m phase <450m
FIELD_BLOCK, CAND_BLOCK, BLOCK_OFF = 64, 32, 1 << 20
STAND_SIGMA, STAND_SMOOTH = 0.231, 30.0
CORE_FACTOR = 1.345
BROADLEAF_STANDS = (0.10, 0.60, 40.0)          # area share of broadleaf stands, their share, smoothing (m)
RIPARIAN_M = 25.0
BUSH_CLUSTER = (5.3e-4, 3.8, 0.15)             # parents per m2, sigma m, floor share (v3: fit to Livonia bush g(r))
DEAD_CLUSTER = (2.0e-4, 10.0, 0.30)
REED_REED, REED_TREE = 1.75, 2.21                 # Livonia p1: reed to reed, reed to nearest tree
REED_CLUSTER = (3.0e-4, 3.9, 0.05)
REED_SOFT = ([1.75, 2.5, 3.5], [0.3, 0.6, 1.0])        # Livonia reed NN p1/p5/p50 1.75/2.21/3.40 m
ROAD_HALF = 3.5
ROAD_CLEAR = {"conifer": 2.09, "broadleaf": 1.08, "bush": 0.71, "dead": 1.99, "reed": 0.71}
FOOT_H, FOOT_BURIED = 3.5, -0.05                # geometry faces in the vehicle band above the terrain
WATER_EXTRA, REED_WATER = 0.25, 0.25
BRIDGE_EXTRA, KIT_EXTRA, NARVA_M = 1.0, 0.5, 6.0
SLOPE_MAX = 36.0
SAFETY = 0.05
# bog: Livonia has no raised bog; [DESIGN] values are explained in the module docstring
BOG_TRANS_M = 25.0                              # [DESIGN] transition into the bog (Livonia canopy edge width analogue)
BOG_TREES, BOG_BUSH, BOG_DEAD = 40.0, 67.8, 4.66  # open bog trees [DESIGN]; bushes, dead = Livonia open land medians
WOODED_BOG_TREES = BOG_TREES                    # Compatibility report field; placement uses BOG_TREES for all bogs
BOG_BROADLEAF = 0.08                            # [DESIGN] birch share of the bog trees
BOG_MOSS_CORE, BOG_MOSS_SMOOTH, BOG_MOSS_MIN_M2 = 0.60, 20.0, 400.0   # [DESIGN] tree-free moss clearings (core share)
BOG_MOSS_FULL = 0.40                            # [DESIGN] v4h: moss covers at least this share of a component's open bog
BOG_MOSS_RAMP = (5.0, 25.0)                     # [DESIGN] eligibility starts at 5 m; ramp sets the component target, not a spatial threshold
BOG_MOSS_BUSH = 0.5                             # [DESIGN] bush factor in the moss clearings
BOG_MOSS_TRANS_M = 5.0                          # [DESIGN] r2: tree transition inside the moss clearings
BOG_MOSS_GAP_M = 10.0                            # [DESIGN] every tree family keeps this gap, plus 0.75 m raster allowance
BOG_PINE_CLUSTER = (1.2e-3, 5.0, 0.50)          # [DESIGN] pine groups: parents per m2, sigma m, floor share (v4e 0.50)
BOG_SCALE_Q = 0.30                              # [DESIGN] bog trees draw their scale from the Livonia p1..p30 only
BOG_PALETTE = {                                 # [DESIGN] weights; models and their scale/tilt are Livonia's
    "conifer": [["dz\\plants_bliss\\tree\\t_pinussylvestris_1s_summer.p3d", 0.40],
                ["dz\\plants_bliss\\tree\\t_pinussylvestris_1f_summer.p3d", 0.30],
                ["dz\\plants_bliss\\tree\\t_pinussylvestris_2s_summer.p3d", 0.12],
                ["dz\\plants_bliss\\tree\\t_pinussylvestris_2sb_summer.p3d", 0.08],
                ["dz\\plants_bliss\\tree\\t_pinussylvestris_2fb_summer.p3d", 0.05],
                ["dz\\plants_bliss\\tree\\t_pinussylvestris_3s_summer.p3d", 0.05]],
    "broadleaf": [["dz\\plants_bliss\\tree\\t_betulapendulae_1s_summer.p3d", 0.6],
                  ["dz\\plants_bliss\\tree\\t_betulapendulae_2s_summer.p3d", 0.4]],
    "bush": [["dz\\plants_bliss\\bush\\b_betulanana_1s_summer.p3d", 1.0]],
    "dead": [["dz\\plants_bliss\\tree\\d_betulapendula_stump.p3d", 0.5],
             ["dz\\plants_bliss\\tree\\d_piceaabies_fallend.p3d", 0.25],
             ["dz\\plants_bliss\\tree\\d_piceaabies_fallene.p3d", 0.25]],
    "reed": []}
# field ids (world-anchored random streams)
F_STAND, F_BROADLEAF, F_BUSH, F_DEAD, F_REED, F_SPILL, F_MOSS, F_PINE = 2, 3, 4, 5, 6, 7, 8, 9
GROUPS = ["reed", "trees", "dead", "bush"]
TREE_ADMISSION_STRATA = ["base", "canopy_10_15", "canopy_15_20", "canopy_20_25"]
NU = 10   # uniforms per candidate: pick, family, model, solitary, accept, scale, tilt, yaw, azimuth, priority


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def p3d_path(name):
    return "P:/DZ/" + name[3:].replace("\\", "/")


# ------------------------------------------------------------------ terrain sampling
def tri_eval(H, x, z):
    """Planar height and slope (deg) on the native NW-SE triangles; cell (row, col)."""
    c = np.clip(np.asarray(x, float) / 6.0, 0, N - 1.000001)
    r = np.clip((ZTOP - np.asarray(z, float)) / 6.0, 0, N - 1.000001)
    c0, r0 = np.floor(c).astype(int), np.floor(r).astype(int)
    fc, fr = c - c0, r - r0
    nw, ne, sw, se = H[r0, c0], H[r0, c0 + 1], H[r0 + 1, c0], H[r0 + 1, c0 + 1]
    up = fc >= fr
    h = np.where(up, nw + fc * (ne - nw) + fr * (se - ne), nw + fr * (sw - nw) + fc * (se - sw))
    dc = np.where(up, ne - nw, se - sw)
    dr = np.where(up, se - ne, sw - nw)
    slope = np.degrees(np.arctan(np.hypot(dc, dr) / 6.0))
    return h, slope, r0, c0


def vertex_bilinear(V, x, z):
    """Bilinear value of a vertex raster (vertex (r, c) at x = 6c, z = ZTOP - 6r)."""
    c = np.clip(np.asarray(x, float) / 6.0, 0, N - 1.000001)
    r = np.clip((ZTOP - np.asarray(z, float)) / 6.0, 0, N - 1.000001)
    c0, r0 = np.floor(c).astype(int), np.floor(r).astype(int)
    fc, fr = c - c0, r - r0
    V = np.asarray(V, float)
    return ((1 - fr) * ((1 - fc) * V[r0, c0] + fc * V[r0, c0 + 1]) + fr * ((1 - fc) * V[r0 + 1, c0] + fc * V[r0 + 1, c0 + 1]))


def wet_at(H, plane, env, x, z):
    h, _, r0, c0 = tri_eval(H, x, z)
    r0, c0 = np.minimum(r0, N - 2), np.minimum(c0, N - 2)
    pl = plane[r0, c0]
    water = (np.isfinite(pl) & (h < np.nan_to_num(pl, nan=-1e9))) | (h < SEA)
    sea = (h < SEA_HIGH) & ~np.isfinite(env[r0, c0])
    return water, sea


def trunk_drop(H, x, z, radius):
    """Largest terrain drop below the origin height over the trunk disc: 32 directions at radius and radius / 2, plus
    the grid vertices inside the disc (the planar minimum lies on the circle or at a vertex)."""
    h0, _, _, _ = tri_eval(H, x, z)
    lo = h0.copy()
    for f in (0.5, 1.0):
        for a in np.linspace(0, 2 * np.pi, 32, endpoint=False):
            hh, _, _, _ = tri_eval(H, x + np.cos(a) * radius * f, z + np.sin(a) * radius * f)
            lo = np.minimum(lo, hh)
    for dc in (0, 1):
        for dr in (0, 1):
            c = np.floor(x / 6.0).astype(int) + dc
            r = np.floor((ZTOP - z) / 6.0).astype(int) + dr
            vx, vz = 6.0 * c, ZTOP - 6.0 * r
            inside = np.hypot(vx - x, vz - z) <= radius
            lo = np.where(inside, np.minimum(lo, H[np.clip(r, 0, N - 1), np.clip(c, 0, N - 1)]), lo)
    return h0 - lo


def disc_wet_dense(H, plane, env, x, z, radius, step=0.25):
    """True where visible water or the engine sea band lies within radius + step: every terrain vertex within that
    radius (vertex_wet), the centre and concentric rings every step m out to radius + step, points every step m along
    each ring (v4i/v4j: the 73-point ring_wet missed wet slivers at single vertices under 3 long fallen trunks of the
    first production map, up to 0.165 m deep in the exact disc minimum of G1)."""
    x, z, radius = np.asarray(x, float), np.asarray(z, float), np.asarray(radius, float)
    hit = np.zeros(len(x), bool)
    if not len(x):
        return hit
    hit |= vertex_wet(H, plane, env, x, z, radius + step)
    w, s_ = wet_at(H, plane, env, x, z)
    hit |= w | s_
    nk = int(np.ceil((float(radius.max()) + step) / step))
    for k in range(1, nk + 1):
        r = k * step
        sel = np.flatnonzero(r <= radius + step + 1e-9)
        if not sel.size:
            break
        na = max(6, int(np.ceil(2 * np.pi * r / step)))
        for a in np.arange(na) * (2 * np.pi / na):
            w, s_ = wet_at(H, plane, env, x[sel] + np.cos(a) * r, z[sel] + np.sin(a) * r)
            hit[sel] |= w | s_
    return hit


def wet_vertices(H, plane, env):
    """(x, z) of every terrain vertex below the level of one of its four cells: below that cell's pond plane, below
    0.75 m, or below 1.0 m in a cell outside the envelope. On the planar triangles a cell holds water (or sea band) only
    next to such a vertex, so any wet point lies within one cell diagonal of one."""
    wet = H < SEA
    for dr in (0, 1):
        for dc in (0, 1):
            cr = np.clip(np.arange(N)[:, None] - dr, 0, N - 2)
            cc = np.clip(np.arange(N)[None, :] - dc, 0, N - 2)
            pl, ev = plane[cr, cc], env[cr, cc]
            wet |= (np.isfinite(pl) & (H < np.nan_to_num(pl, nan=-1e9))) | ((H < SEA_HIGH) & ~np.isfinite(ev))
    r, c = np.nonzero(wet)
    return np.c_[6.0 * c, ZTOP - 6.0 * r]


def vertex_wet(H, plane, env, x, z, radius):
    """True where a terrain vertex within radius is below the level of one of its cells (its wet sliver touches the
    vertex, so it reaches into the disc)."""
    hit = np.zeros(len(x), bool)
    k = int(np.ceil(float(radius.max()) / 6.0)) + 1
    c0 = np.floor(x / 6.0).astype(int)
    r0 = np.floor((ZTOP - z) / 6.0).astype(int)
    for dr in range(-k, k + 2):
        for dc in range(-k, k + 2):
            r, c = r0 + dr, c0 + dc
            inr = (np.hypot(6.0 * c - x, ZTOP - 6.0 * r - z) <= radius) & (r >= 0) & (r < N) & (c >= 0) & (c < N)
            if not inr.any():
                continue
            rr, cc = np.clip(r, 0, N - 1), np.clip(c, 0, N - 1)
            hv = H[rr, cc]
            wet = hv < SEA
            for ar in (0, 1):
                for ac in (0, 1):
                    cr, ccl = np.clip(rr - ar, 0, N - 2), np.clip(cc - ac, 0, N - 2)
                    pl, ev = plane[cr, ccl], env[cr, ccl]
                    wet |= (np.isfinite(pl) & (hv < np.nan_to_num(pl, nan=-1e9))) | ((hv < SEA_HIGH) & ~np.isfinite(ev))
            hit |= inr & wet
    return hit


def ring_wet(H, plane, env, x, z, radius):
    """True where visible water or the engine sea band lies within radius: centre plus 24 directions at 1/3, 2/3, 1."""
    ang = np.linspace(0, 2 * np.pi, 24, endpoint=False)
    hit = np.zeros(len(x), bool)
    pts = [(np.zeros(len(x)), np.zeros(len(x)))]
    for f in (1 / 3, 2 / 3, 1.0):
        for a in ang:
            pts.append((np.cos(a) * radius * f, np.sin(a) * radius * f))
    for dx, dz in pts:
        w, s = wet_at(H, plane, env, x + dx, z + dz)
        hit |= w | s
    return hit


# ------------------------------------------------------------------ shipped surface mask
class Mask:
    def __init__(self, pbo, dirs):
        self.pbo, self.dirs, self.idx, self.src = pbo, [Path(d) for d in dirs], pbo_index(pbo)[1], {}

    def tile(self, a, b):
        stem = f"m_{a:03d}_{b:03d}_lca"
        shipped = pbo_read(self.pbo, self.idx, f"data/layers/{stem}.paa")
        for d in self.dirs:
            png, paa = d / f"{stem}.png", d / f"{stem}.paa"
            if png.exists() and paa.exists() and paa.stat().st_size == len(shipped) and paa.read_bytes() == shipped:
                self.src[stem] = {"png": str(png), "png_sha256": sha(png), "paa_sha256": hashlib.sha256(shipped).hexdigest()}
                rgb = np.asarray(Image.open(png))[..., :3].astype(int)
                return np.where(rgb.max(-1) == 0, 0, np.argmax(rgb, -1) + 1).astype(np.uint8)
        raise SystemExit(f"no PNG with a PAA identical to the PBO entry for {stem}")

    def compose(self, x0, z0, x1, z1):
        """Slots at 1 m for x in [x0, x1), z in (z0, z1]; row 0 = north. Tile core: x in [384a, 384a + 384), 64 px overlap."""
        out = np.zeros((z1 - z0, x1 - x0), np.uint8)
        for a in range(x0 // 384, -(-x1 // 384)):
            for b in range((MAP - z1) // 384, -(-(MAP - z0) // 384)):
                cx0, cx1 = max(x0, 384 * a), min(x1, 384 * a + 384)
                cz1, cz0 = min(z1, MAP - 384 * b), max(z0, MAP - 384 * (b + 1))
                if cx0 >= cx1 or cz0 >= cz1:
                    continue
                img = self.tile(a, b)
                j0, i0 = cx0 - (384 * a - 64), (MAP - 384 * b + 64) - cz1
                oj, oi = cx0 - x0, z1 - cz1
                out[oi:oi + cz1 - cz0, oj:oj + cx1 - cx0] = img[i0:i0 + cz1 - cz0, j0:j0 + cx1 - cx0]
        return out


# ------------------------------------------------------------------ geometry helpers
def in_polygon(px, pz, poly):
    poly = np.asarray(poly, float)
    inside = np.zeros(np.shape(px), bool)
    for (xa, za), (xb, zb) in zip(poly, np.roll(poly, -1, axis=0)):
        cond = (za > pz) != (zb > pz)
        xi = xa + (pz - za) * (xb - xa) / np.where(zb == za, 1e-12, zb - za)
        inside ^= cond & (px < xi)
    return inside


def dist_to_polygon(px, pz, poly):
    """Distance from points to a closed polygon (0 inside)."""
    poly = np.asarray(poly, float)
    d = np.full(np.shape(px), np.inf)
    for (xa, za), (xb, zb) in zip(poly, np.roll(poly, -1, axis=0)):
        ex, ez = xb - xa, zb - za
        t = np.clip(((px - xa) * ex + (pz - za) * ez) / max(ex * ex + ez * ez, 1e-12), 0, 1)
        d = np.minimum(d, np.hypot(px - xa - t * ex, pz - za - t * ez))
    return np.where(in_polygon(px, pz, poly), 0.0, d)


def cell_distance(mask, x, z, reach):
    """Distance from points to the union of 6 m terrain cells having any flagged corner (cells beyond reach ignored)."""
    cm = mask[:-1, :-1] | mask[1:, :-1] | mask[:-1, 1:] | mask[1:, 1:]
    k = int(math.ceil(reach / 6.0)) + 1
    r0 = np.floor((ZTOP - z) / 6.0).astype(int)
    c0 = np.floor(x / 6.0).astype(int)
    d = np.full(len(x), np.inf)
    for dr in range(-k, k + 1):
        for dc in range(-k, k + 1):
            r, c = np.clip(r0 + dr, 0, N - 2), np.clip(c0 + dc, 0, N - 2)
            f = cm[r, c]
            if not f.any():
                continue
            cx0, cx1 = 6.0 * c, 6.0 * c + 6.0
            cz1, cz0 = ZTOP - 6.0 * r, ZTOP - 6.0 * r - 6.0
            ddx = np.maximum(np.maximum(cx0 - x, 0), x - cx1)
            ddz = np.maximum(np.maximum(cz0 - z, 0), z - cz1)
            d = np.where(f, np.minimum(d, np.hypot(ddx, ddz)), d)
    return d


def object_hulls(stage_wrp):
    w = read_wrp(Path(stage_wrp))
    boxes, out = {}, []
    for o in w["objects"]:
        name = o["name"]
        if "baltic_water_v30" in name:
            continue
        if name not in boxes:
            mi = ODOL.from_file(p3d_path(name)).model_info
            boxes[name] = (np.array([mi.bbox_min_visual.x, mi.bbox_min_visual.y, mi.bbox_min_visual.z]),
                           np.array([mi.bbox_max_visual.x, mi.bbox_max_visual.y, mi.bbox_max_visual.z]))
        lo, hi = boxes[name]
        m = np.asarray(o["matrix"], float)
        M = m[:9].reshape(3, 3).T
        corners = np.array([[a, b, c] for a in (lo[0], hi[0]) for b in (lo[1], hi[1]) for c in (lo[2], hi[2])])
        P = corners @ M.T + m[9:12]
        xz = P[:, [0, 2]]
        hull = xz[ConvexHull(xz).vertices]
        kind = "bridge" if "bridges" in name.lower() else "kit"
        out.append({"kind": kind, "model": name, "id": o["id"], "hull": hull})
    return out, max(o["id"] for o in w["objects"])


class RoadFootprint:
    """Geometry LOD of every palette model; an instance fails when a face in the vehicle band (below FOOT_H above the
    terrain, not fully buried) comes within ROAD_HALF + SAFETY of a road axis in plan (exact face-to-polyline
    distance; faces that are vertical in plan are taken as their outline)."""

    def __init__(self, names):
        self.lines = [shapely.LineString(np.asarray(p, float)) for p in road_chains() if len(p) >= 2]
        self.tree = shapely.STRtree(self.lines)
        self.kd = road_tree()
        self.geo = {}
        for nm in names:
            od = ODOL.from_file(p3d_path(nm))
            lods = [lod for lod in od.lods if 0.9e13 < lod.resolution < 1.1e13 and lod.vertices and lod.faces]
            if not lods:
                raise SystemExit(f"{nm}: no Geometry LOD")
            lod = lods[0]
            V = np.array([[v.x, v.y, v.z] for v in lod.vertices], float)
            faces = [np.asarray(f.vertex_indices, int) for f in lod.faces]
            diam = max(float(np.ptp(V[f][:, [0, 2]], axis=0).max()) * 1.4143 for f in faces)
            self.geo[nm] = (V, faces, float(np.linalg.norm(V, axis=1).max()), diam)

    def axis_distance(self, x, z):
        pts = shapely.points(np.c_[x, z])
        idx, dist = self.tree.query_nearest(pts, return_distance=True, all_matches=False)
        d = np.full(len(x), np.inf)
        d[idx[0]] = dist
        return d

    def clear(self, names, M, T, s, H):
        n = len(names)
        ok = np.ones(n, bool)
        if not n:
            return ok
        lim = ROAD_HALF + SAFETY
        reach = lim + np.array([self.geo[nm][2] for nm in names]) * s + 0.01
        d0 = self.kd.query(np.c_[T[:, 0], T[:, 2]], distance_upper_bound=float(reach.max()) + 1.0)[0] - 0.26
        for k in np.flatnonzero(d0 < reach):
            V, faces, _, diam = self.geo[names[k]]
            W = V @ M[k].T + T[k]
            gap = W[:, 1] - tri_eval(H, W[:, 0], W[:, 2])[0]
            band = [f for f in faces if gap[f].min() < FOOT_H and gap[f].max() > FOOT_BURIED]
            if not band:
                continue
            used = np.unique(np.concatenate(band))
            dv = self.kd.query(W[used][:, [0, 2]], distance_upper_bound=60.0)[0]
            if float(dv.min()) - 0.26 - diam * s[k] > lim:      # 0.5 m axis samples: <= 0.25 m chord error
                continue
            geoms = []
            for f in band:
                xy = W[f][:, [0, 2]]
                poly = shapely.Polygon(xy) if len(f) >= 3 else None
                geoms.append(poly if poly is not None and poly.is_valid and poly.area > 1e-8 else shapely.LineString(np.r_[xy, xy[:1]]))
            _, dist = self.tree.query_nearest(geoms, return_distance=True, all_matches=False)
            if float(np.min(dist)) < lim:
                ok[k] = False
        return ok


# ------------------------------------------------------------------ world-anchored random fields
def _gauss_std(sigma):
    """Standard deviation of unit white noise after scipy's 2D Gaussian filter (truncate 4): sum of the squared 1D taps."""
    r = int(4.0 * sigma + 0.5)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    return float((k * k).sum())


def _blocks(i0, i1, j0, j1, B):
    for bi in range(i0 // B, (i1 - 1) // B + 1):
        for bj in range(j0 // B, (j1 - 1) // B + 1):
            yield bi, bj


def _gen(*key):
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence([int(k) + (BLOCK_OFF if i > 1 else 0) for i, k in enumerate(key)])))


def smooth_field_w(seed, fid, i0, i1, j0, j1, sigma):
    """Standard normal field with Gaussian correlation sigma on world pixel rows [i0, i1) x cols [j0, j1) (row 0 =
    north): white noise drawn per FIELD_BLOCK world block, filtered, divided by the analytic standard deviation."""
    p = int(4.0 * sigma + 0.5) + 1
    a0, a1, b0, b1 = i0 - p, i1 + p, j0 - p, j1 + p
    nz = np.empty((a1 - a0, b1 - b0))
    B = FIELD_BLOCK
    for bi, bj in _blocks(a0, a1, b0, b1, B):
        blk = _gen(seed, fid, bi, bj).standard_normal((B, B))
        r0, r1 = max(a0, bi * B), min(a1, bi * B + B)
        c0, c1 = max(b0, bj * B), min(b1, bj * B + B)
        nz[r0 - a0:r1 - a0, c0 - b0:c1 - b0] = blk[r0 - bi * B:r1 - bi * B, c0 - bj * B:c1 - bj * B]
    g = ndimage.gaussian_filter(nz, sigma, mode="constant", truncate=4.0)[p:-p, p:-p]
    return g / _gauss_std(sigma)


def cluster_field_w(seed, fid, i0, i1, j0, j1, kappa, sigma, floor):
    """Thomas-process intensity with mean 1: Poisson parents (kappa per m2) drawn per FIELD_BLOCK world block at whole
    pixels, Gaussian kernels of sigma, divided by kappa (the expected value), floor + (1 - floor) x that."""
    p = int(4.0 * sigma + 0.5) + 1
    a0, a1, b0, b1 = i0 - p, i1 + p, j0 - p, j1 + p
    imp = np.zeros((a1 - a0, b1 - b0))
    B = FIELD_BLOCK
    for bi, bj in _blocks(a0, a1, b0, b1, B):
        g = _gen(seed, fid, bi, bj)
        n = g.poisson(kappa * B * B)
        ii, jj = bi * B + g.integers(0, B, n), bj * B + g.integers(0, B, n)
        k = (ii >= a0) & (ii < a1) & (jj >= b0) & (jj < b1)
        np.add.at(imp, (ii[k] - a0, jj[k] - b0), 1.0)
    f = ndimage.gaussian_filter(imp, sigma, mode="constant", truncate=4.0)[p:-p, p:-p] / kappa
    return floor + (1 - floor) * f


def sample_world(seed, gid, pas, lam, wi0, wj0, ri0, ri1, rj0, rj1):
    """Candidate points of one group: Poisson per CAND_BLOCK world block from the block's intensity (lam per m2 on the
    window whose first pixel is world row wi0, col wj0; every block touching the region rows [ri0, ri1) x cols
    [rj0, rj1) lies fully in the window), kept inside the region. Returns world x, z, window flat index, uniforms."""
    B = CAND_BLOCK
    xs, zs, fl, us = [], [], [], []
    Wc = lam.shape[1]
    for bi, bj in _blocks(ri0, ri1, rj0, rj1, B):
        w = lam[bi * B - wi0:bi * B - wi0 + B, bj * B - wj0:bj * B - wj0 + B]
        tot = float(w.sum())
        if tot <= 0:
            continue
        g = _gen(seed, 100 + gid, pas, bi, bj)
        n = g.poisson(tot)
        if n == 0:
            continue
        flat = g.choice(B * B, size=n, p=(w / tot).ravel())
        i, j = np.divmod(flat, B)
        x = bj * B + j + g.random(n)
        z = MAP - (bi * B + i) - g.random(n)
        u = g.random((n, NU))
        gi, gj = bi * B + i, bj * B + j
        k = (gi >= ri0) & (gi < ri1) & (gj >= rj0) & (gj < rj1)
        xs.append(x[k]), zs.append(z[k]), fl.append(((gi - wi0) * Wc + (gj - wj0))[k]), us.append(u[k])
    if not xs:
        return np.zeros(0), np.zeros(0), np.zeros(0, int), np.zeros((0, NU))
    return np.concatenate(xs), np.concatenate(zs), np.concatenate(fl), np.concatenate(us)


# ------------------------------------------------------------------ Livonia profiles
def road_profile(ref):
    """Livonia densities on forest surface against the distance to the road edge, at the bin centres (m)."""
    p = ref["road_profile_forest"]
    e = np.array(p["edges"], float)
    c = (e[:-1] + e[1:]) / 2
    keep = (e[:-1] >= 0) & (np.array(p["area_ha"], float) >= 1.0)
    g = lambda k: np.asarray(p[k], float)[keep]  # noqa: E731
    t = g("conifer") + g("broadleaf")
    q = ref["road_solitary_forest"]
    qe = np.array(q["edges"], float)
    return {"d": c[keep], "trees": t, "bush": g("bush"), "dead": g("dead"), "broadleaf": g("broadleaf") / np.maximum(t, 1e-9),
            "sol_d": (qe[:-1] + qe[1:]) / 2, "solitary": np.array(q["solitary_share_of_trees"], float)}


def canopy_solitary(ref):
    """Livonia solitary share of trees against the signed distance to the canopy (5 m bins by their lower bound; the
    empty 0 bin dropped)."""
    e = ref["edge_mix_canopy"]
    lo = np.array(e["bin_lo"], float)
    keep = lo != 0.0
    return lo[keep], np.array(e["solitary_share_trees"], float)[keep], np.array(e["broadleaf_share_trees"], float)[keep]


def edge_profile(ref):
    """Livonia densities and mix against the forest surface, at the bin centres (m, inside > 0)."""
    p = ref["texture_edge_profile"]
    lo = np.array(p["bin_lo"], float)
    area = np.array(p["area_ha"], float)
    keep = area >= 1.0
    d = np.where(lo >= 0, lo - 2.5, lo + 2.5)[keep]
    o = np.argsort(d)
    g = lambda a: np.asarray(a, float)[keep][o]  # noqa: E731
    per = p["per_ha"]
    return {"d": d[o], "trees": g(per["conifer"]) + g(per["broadleaf"]), "bush": g(per["bush"]), "dead": g(per["dead"]),
            "broadleaf": g(p["broadleaf_share_of_trees"]), "solitary": g(p["solitary_share_of_trees"])}


def spill_expectation(t, cap, sig):
    """E[min(t S, cap)] for S log-normal with mean 1 and log-sd sig (elementwise)."""
    t = np.maximum(t, 1e-12)
    a = np.log(cap / t)
    return t * ndtr((a - sig * sig / 2) / sig) + cap * (1.0 - ndtr((a + sig * sig / 2) / sig))


# ------------------------------------------------------------------ placement
class Grid:
    def __init__(self, cell):
        self.cell, self.d = cell, {}

    def near(self, x, z, r):
        cx, cz = int(x // self.cell), int(z // self.cell)
        k = int(math.ceil(r / self.cell))
        for a in range(cx - k, cx + k + 1):
            for b in range(cz - k, cz + k + 1):
                for item in self.d.get((a, b), ()):
                    dd = math.hypot(item[0] - x, item[1] - z)
                    if dd < r:
                        yield dd, item

    def add(self, x, z, payload):
        self.d.setdefault((int(x // self.cell), int(z // self.cell)), []).append((x, z, payload))


SOFT_R, SOFT_P = [0.0, 1.0, 2.0, 3.0, 4.0], [0.20, 0.30, 0.45, 0.75, 1.0]
BB_HARD, BB_SOFT_P = 0.45, [0.60, 0.75, 0.90, 1.0, 1.0]
DEAD_R, DEAD_P = [0.0, 1.0, 2.0, 3.0], [0.17, 0.28, 0.59, 1.0]


def accept_trees(x, z, size, fam, u, trees, reeds):
    keep = np.zeros(len(x), bool)
    for k in range(len(x)):
        p, ok = 1.0, True
        if any(True for _ in reeds.near(x[k], z[k], REED_TREE)):
            continue
        for d, (_, _, (s2, f2)) in trees.near(x[k], z[k], SOFT_R[-1]):
            if fam[k] == 1 and f2 == 1:              # broadleaf clumps (Livonia broadleaf NN p1/p5 0.47/1.02 m)
                hard, soft = BB_HARD, BB_SOFT_P
            else:
                hard = 2.2 if (size[k] == 3 and s2 == 3) else (1.13 if (size[k] >= 2 and s2 >= 2) else 0.7)
                soft = SOFT_P
            if d < hard:
                ok = False
                break
            p *= float(np.interp(d, SOFT_R, soft))
        if ok and u[k] < p:
            keep[k] = True
            trees.add(x[k], z[k], (int(size[k]), int(fam[k])))
    return keep


def accept_simple(x, z, u, own, own_r, trees, tree_rule, own_soft=None):
    keep = np.zeros(len(x), bool)
    for k in range(len(x)):
        if any(True for _ in own.near(x[k], z[k], own_r)):
            continue
        p = 1.0
        if own_soft is not None:
            for d, _ in own.near(x[k], z[k], own_soft[0][-1]):
                p *= float(np.interp(d, *own_soft))
        if tree_rule == "dead":
            for d, _ in trees.near(x[k], z[k], 3.0):
                p *= float(np.interp(d, DEAD_R, DEAD_P))
        elif any(True for _ in trees.near(x[k], z[k], tree_rule)):
            continue
        if u[k] < p:
            keep[k] = True
            own.add(x[k], z[k], 0)
    return keep


def transforms(ref_models, names, x, z, H, U, low=None):
    """Per instance: M (n, 3, 3) with the model axes as columns (scale included), position T = origin + M . bc, scale.
    Scale and tilt from the model's Livonia quantiles (uniforms U[:, 5], U[:, 6]), yaw U[:, 7], tilt azimuth U[:, 8];
    origin on the planar terrain. low (bog palette trees): scale from the Livonia quantiles p1..p(100 x BOG_SCALE_Q)."""
    n = len(x)
    s, tilt = np.empty(n), np.empty(n)
    u1, u2 = U[:, 5], U[:, 6]
    yaw, az = U[:, 7] * 2 * np.pi, U[:, 8] * 2 * np.pi
    bc = np.zeros((n, 3))
    q1 = 0.01 + 0.98 * u1 if low is None else np.where(low, 0.01 + (BOG_SCALE_Q - 0.01) * u1, 0.01 + 0.98 * u1)
    for nm in sorted(set(names.tolist())):
        m = ref_models[nm]
        sel = names == nm
        lv = np.array(m["scale_levels"], float) / 100
        s[sel] = np.interp(q1[sel], lv, m["scale_q"])
        tilt[sel] = np.interp(0.01 + 0.98 * u2[sel], lv, m["tilt_q"])
        bc[sel] = m["bc"]
    c, sn = np.cos(yaw), np.sin(yaw)
    R0 = np.zeros((n, 3, 3))
    R0[:, 0, 0], R0[:, 0, 2], R0[:, 1, 1], R0[:, 2, 0], R0[:, 2, 2] = c, sn, 1.0, -sn, c
    ax, az_ = np.cos(az), np.sin(az)
    Kx = np.zeros((n, 3, 3))
    Kx[:, 0, 1], Kx[:, 1, 0] = -az_, az_          # axis (ax, 0, az_): K = [[0, -a_z, a_y], [a_z, 0, -a_x], [-a_y, a_x, 0]]
    Kx[:, 1, 2], Kx[:, 2, 1] = -ax, ax
    ta = np.radians(tilt)
    Rt = np.eye(3)[None] + np.sin(ta)[:, None, None] * Kx + (1 - np.cos(ta))[:, None, None] * (Kx @ Kx)
    M = (Rt @ R0) * s[:, None, None]
    h, _, _, _ = tri_eval(H, x, z)
    T = np.c_[x, h, z] + np.einsum("nij,nj->ni", M, bc)
    return M, T, s


def record_matrix(M, T):
    return [float(a) for a in (*M[:, 0], *M[:, 1], *M[:, 2], *T)]


def model_limits(ref_models):
    lim = {}
    for nm, m in ref_models.items():
        embed = -min(m["visual_bottom_local"], 0.0)
        r = max(m["trunk_radius"], 1e-3)
        lim[nm] = min(SLOPE_MAX, math.degrees(math.atan(embed / r))) if m["family"] in ("conifer", "broadleaf", "bush") else SLOPE_MAX
    return lim


def edt(mask, big=1e3):
    """Euclidean distance (pixels) of every True pixel to the nearest False one; big everywhere when there is none
    (scipy measures to a phantom corner then)."""
    if mask.all():
        return np.full(mask.shape, float(big))
    return ndimage.distance_transform_edt(mask)


def read_global(arr, i0, i1, j0, j1, fill):
    """Window rows [i0, i1) x cols [j0, j1) of a global (MAP x MAP, row 0 = north) array; outside the map = fill."""
    out = np.full((i1 - i0, j1 - j0), fill, arr.dtype)
    a0, a1, b0, b1 = max(i0, 0), min(i1, MAP), max(j0, 0), min(j1, MAP)
    if a0 < a1 and b0 < b1:
        out[a0 - i0:a1 - i0, b0 - j0:b1 - j0] = arr[a0:a1, b0:b1]
    return out


def bog_transition_weight(distance):
    """Same 25m transition and outer half; retain more forest in the inner half.
    The monotone continuous profile prevents a sparse inner ring below its core.
    Mean forest contribution in the inner half rises from .1875 to .2352.
    """
    t = np.clip(distance / BOG_TRANS_M, 0., 1.)
    w = t*t*(3-2*t)
    return w - 5.*np.maximum(w-.5, 0.)**2*(1-w)


def object_gap_raster(hulls):
    """Mandatory unplantable hull interiors on the world 1m grid.

    These margins are lower bounds of exact_ok for every model: no vegetation
    can occupy a kit hull + KIT_EXTRA or a bridge hull + BRIDGE_EXTRA. They
    therefore participate in the same edge-distance profile as other forest
    boundaries, instead of being removed only after candidates are sampled.
    Exact model-specific exclusions still run unchanged for every instance.
    """
    out = np.zeros((MAP, MAP), bool)
    for obj in hulls:
        hull = obj["hull"]
        margin = obj.get("margin_m", BRIDGE_EXTRA if obj["kind"] == "bridge" else KIT_EXTRA)
        j0 = max(0, int(np.floor(hull[:, 0].min() - margin)))
        j1 = min(MAP, int(np.ceil(hull[:, 0].max() + margin)))
        i0 = max(0, int(np.floor(MAP - hull[:, 1].max() - margin)))
        i1 = min(MAP, int(np.ceil(MAP - hull[:, 1].min() + margin)))
        if i0 >= i1 or j0 >= j1:
            continue
        X, Z = np.meshgrid(np.arange(j0, j1) + 0.5, MAP - np.arange(i0, i1) - 0.5)
        out[i0:i1, j0:j1] |= (dist_to_polygon(X.ravel(), Z.ravel(), hull) < margin).reshape(X.shape)
    return out


def native_gap_raster(vertices):
    """Interiors of native cells excluded by exact_ok, on the 1m world grid.

    Vertex row zero is z=12282, while raster row zero is z=12288; preserve
    the six-metre north offset and leave the six-metre east strip outside
    the native mesh unmarked. Per-instance margins still apply in exact_ok.
    """
    assert vertices.shape == (N, N) and vertices.dtype == bool
    cells = vertices[:-1, :-1] | vertices[1:, :-1] | vertices[:-1, 1:] | vertices[1:, 1:]
    out = np.zeros((MAP, MAP), bool)
    out[MAP-ZTOP:, :ZTOP] = np.repeat(np.repeat(cells, 6, axis=0), 6, axis=1)
    return out


# ------------------------------------------------------------------ global pre-pass: surface, water, bog, moss
def prepass(a, work, log):
    """Global 1 m rasters (row 0 = north edge z = 12288): slot, water/sea bits, bog, moss. Saved in work/."""
    t0 = time.time()
    mk = Mask(a.pbo, a.layer_dir)
    slot = mk.compose(0, 0, MAP, MAP)
    np.save(work / "slot1m.npy", slot)
    t = np.load(a.terrain)
    fp = np.load(a.footprint)
    H = t["heights"].astype(np.float64)
    W = np.load(a.cover)["osm_wetland"].astype(np.float64)
    wsea = np.zeros((MAP, MAP), np.uint8)
    bog = np.zeros((MAP, MAP), bool)
    for i0 in range(0, MAP, 512):
        X, Z = np.meshgrid(np.arange(MAP) + 0.5, MAP - (i0 + np.arange(512)) - 0.5)
        w, s = wet_at(H, fp["plane"], fp["env_plane"], X, Z)
        wsea[i0:i0 + 512] = w.astype(np.uint8) | (s.astype(np.uint8) << 1)
        bog[i0:i0 + 512] = vertex_bilinear(W, X, Z) >= 0.5
    kit_water, kit_report = rasterize_kit_water(read_wrp(Path(a.stage_wrp))["objects"],
        json.loads(KIT_GEOMETRY.read_text(encoding="utf-8"))["models"], H,
        lambda heights, x, z: tri_eval(heights, x, z)[0])
    wsea |= kit_water.astype(np.uint8)
    np.save(work / "kit-water1m.npy", kit_water)
    log("staged kit water: " + json.dumps(kit_report))
    np.save(work / "wsea1m.npy", wsea)
    np.save(work / "bog1m.npy", bog)
    object_gap = object_gap_raster(object_hulls(a.stage_wrp)[0])
    native_gap = t["v31_kit"] | t["v31_bridge_cut"] | t["v31_bridge_fill"] | t["narva"]
    object_gap |= native_gap_raster(native_gap)
    if a.exclude:
        extra = json.loads(Path(a.exclude).read_text(encoding="utf-8"))["polygons"]
        object_gap |= object_gap_raster([dict(kind="kit", hull=np.asarray(v["polygon_xz"], float), margin_m=float(v["margin_m"])) for v in extra])
    np.save(work / "object-gap1m.npy", object_gap)
    log(f"mandatory object gap: {int(object_gap.sum())} pixels")
    log(f"prepass: slot, water, bog in {time.time() - t0:.0f} s")
    moss = np.zeros((MAP, MAP), bool)
    bogtree = np.zeros((MAP, MAP), np.float32)
    bogforest = np.ones((MAP, MAP), np.float32)
    lab, n = ndimage.label(bog)
    comps = []
    for k, sl in enumerate(ndimage.find_objects(lab)):
        if sl is None:
            continue
        i0, i1 = max(sl[0].start - 2, 0), min(sl[0].stop + 2, MAP)
        j0, j1 = max(sl[1].start - 2, 0), min(sl[1].stop + 2, MAP)
        comp = lab[i0:i1, j0:j1] == k + 1
        area = int(comp.sum())
        if area < BOG_MOSS_MIN_M2:
            continue
        bd = ndimage.distance_transform_edt(comp) - 0.5
        open_ = comp & (wsea[i0:i1, j0:j1] == 0)
        ramp = np.clip((bd - BOG_MOSS_RAMP[0]) / (BOG_MOSS_RAMP[1] - BOG_MOSS_RAMP[0]), 0.0, 1.0)
        ramp = np.where(open_, ramp * ramp * (3 - 2 * ramp), 0.0)
        target = min(max(BOG_MOSS_CORE * float(ramp.sum()), BOG_MOSS_FULL * float(open_.sum())), 0.95 * float((ramp > 0).sum()))
        rec = {"id": k + 1, "bbox_rows_cols": [i0, i1, j0, j1], "area_m2": area, "open_m2": int(open_.sum()),
               "moss_target_m2": round(target, 1), "moss_m2": 0}
        m = np.zeros(comp.shape, bool)
        if target >= BOG_MOSS_MIN_M2:
            mf = smooth_field_w(a.seed, F_MOSS, i0, i1, j0, j1, BOG_MOSS_SMOOTH)
            reg = ramp > 0
            # Allocate clearings throughout the eligible bog, not only its narrow core.
            thr = ndtri(1.0 - BOG_MOSS_CORE)
            z_ = mf[reg] - thr

            def moss_for(delta):
                m_ = np.zeros(comp.shape, bool)
                m_[reg] = z_ >= delta
                lm, nm = ndimage.label(m_)
                if nm:
                    keep = np.zeros(nm + 1, bool)
                    keep[1:] = ndimage.sum(np.ones(m_.shape), lm, index=np.arange(1, nm + 1)) >= BOG_MOSS_MIN_M2
                    m_ = keep[lm]
                return m_
            lo, hi = -3.0, 3.0                              # moss area decreases with delta
            for _ in range(24):
                mid = 0.5 * (lo + hi)
                if moss_for(mid).sum() > target:
                    lo = mid
                else:
                    hi = mid
            m = moss_for(hi)
            # Respect the 10 m tree-free gap while retaining enough plantable core.
            # With a 40/ha target, a 20% plantable share requires 200/ha before cluster normalisation;
            # the previous area-only moss allocation could silently hit the 255/ha cap.
            core = open_ & (bd >= BOG_TRANS_M)
            ref_core = core if core.sum() >= BOG_MOSS_MIN_M2 else open_
            def plantable_share(mask):
                gap_mask = (ndimage.distance_transform_edt(~mask) <= BOG_MOSS_GAP_M + 0.75) if mask.any() else np.zeros(mask.shape, bool)
                return float((ref_core & ~mask & ~gap_mask).sum()) / max(int(ref_core.sum()), 1)
            f_before = plantable_share(m)
            rec["moss_area_before_plantable_guard"] = int(m.sum())
            rec["plantable_before_guard"] = round(f_before, 6)
            if f_before < 0.20:
                low_delta, high_delta = hi, 8.0
                for _ in range(20):
                    middle_delta = 0.5 * (low_delta + high_delta)
                    if plantable_share(moss_for(middle_delta)) < 0.20:
                        low_delta = middle_delta
                    else:
                        high_delta = middle_delta
                hi = high_delta
                m = moss_for(hi)
            moss[i0:i1, j0:j1] |= m
            rec["moss_m2"], rec["delta"] = int(m.sum()), round(hi, 6)
        gap = open_ & ~m & (ndimage.distance_transform_edt(~m) <= BOG_MOSS_GAP_M + 0.75) if m.any() else np.zeros(comp.shape, bool)
        treed = open_ & ~m & ~gap
        core_o = open_ & (bd >= BOG_TRANS_M)
        ref_a = core_o if core_o.sum() >= BOG_MOSS_MIN_M2 else open_
        f = float((treed & ref_a).sum()) / max(int(ref_a.sum()), 1)
        # Normalise the realised world-anchored pine intensity on the actual plantable core,
        # not its global expectation (one). Small bogs otherwise depend on where Poisson
        # cluster parents happen to fall relative to their clearings.
        pine_field = cluster_field_w(a.seed, F_PINE, i0, i1, j0, j1, *BOG_PINE_CLUSTER)
        weighted_f = float(pine_field[treed & ref_a].sum()) / max(int(ref_a.sum()), 1)
        val = BOG_TREES / weighted_f if weighted_f > 0 else 0.0
        rec["pine_weighted_core_share"] = round(weighted_f, 8)
        bt = bogtree[i0:i1, j0:j1]
        # Compensate on a physical 50 m neighbourhood, not only over the whole component.
        # A connected bog may have a moss-heavy half and a tree-heavy half; one scalar
        # does not retain the designed 40 trees/ha in both. The field stays world based.
        numerator = ndimage.gaussian_filter(ref_a.astype(float), 50.0, mode="constant")
        denominator = ndimage.gaussian_filter(pine_field * (treed & ref_a), 50.0, mode="constant")
        local_val = BOG_TREES * numerator / np.maximum(denominator, 1e-8)
        # A Gaussian ratio outside its core support is ill-conditioned. Limit the
        # correction to 2:1 and renormalise its actual core integral to the original
        # 40/ha target; the rim retains the component scalar and its original blend.
        local_val = np.clip(local_val, 0.5 * val, 2.0 * val)
        realised = float((local_val * pine_field)[treed & ref_a].sum()) / max(int(ref_a.sum()), 1)
        if realised > 0:
            local_val *= BOG_TREES / realised
        bt[treed] = val
        bt[treed & ref_a] = local_val[treed & ref_a]
        # Preserve the intended transition integral after moss and its 10 m gap.
        # Both terms need compensation: a core scalar alone depresses the rim.
        w = bog_transition_weight(bd)
        bf = bogforest[i0:i1, j0:j1]
        rec["rim_normalisation"] = []
        for low, high in ((0., 12.5), (12.5, BOG_TRANS_M)):
            zone = open_ & (bd >= low) & (bd < high)
            live = zone & treed
            fw = float((1-w)[zone].sum()); fw_live = float((1-w)[live].sum())
            bw = float(w[zone].sum()); bw_live = float((w*pine_field)[live].sum())
            forest_factor = fw / fw_live if fw_live > 0 else 0.
            bog_factor = BOG_TREES*bw / bw_live if bw_live > 0 else 0.
            # Local compensation keeps a moss-heavy subsection from losing its transition.
            # Normalise the weighted live support on the same physical 50 m scale as the core.
            forest_n = ndimage.gaussian_filter((1-w)*zone, 50., mode="constant")
            forest_d = ndimage.gaussian_filter((1-w)*live, 50., mode="constant")
            local_f = np.clip(forest_n / np.maximum(forest_d, 1e-8), .5*forest_factor, 2.*forest_factor)
            local_f_total = float((local_f*(1-w))[live].sum())
            if local_f_total > 0:local_f *= fw/local_f_total
            pine_n = ndimage.gaussian_filter(w*zone, 50., mode="constant")
            pine_d = ndimage.gaussian_filter(w*pine_field*live, 50., mode="constant")
            local_b = np.clip(BOG_TREES*pine_n / np.maximum(pine_d, 1e-8), .5*bog_factor, 2.*bog_factor)
            local_b_total = float((local_b*w*pine_field)[live].sum())
            if local_b_total > 0:local_b *= BOG_TREES*bw/local_b_total
            bf[live] = local_f[live]; bt[live] = local_b[live]
            rec["rim_normalisation"].append(dict(depth=[low,high],forest_factor=forest_factor,bog_factor=bog_factor,live_pixels=int(live.sum()),local_sigma_m=50.,forest_integral_before=fw,forest_integral_after=float((local_f*(1-w))[live].sum()),pine_integral_before=BOG_TREES*bw,pine_integral_after=float((local_b*w*pine_field)[live].sum())))
        rec["treed_share_of_core"], rec["treed_trees_ha"] = round(f, 4), val
        comps.append(rec)
    del lab
    np.save(work / "moss1m.npy", moss)
    np.save(work / "bogtree1m.npy", bogtree)
    np.save(work / "bogforest1m.npy", bogforest)
    del bogforest
    del bogtree
    log(f"prepass: {len(comps)} bog components >= {BOG_MOSS_MIN_M2:.0f} m2, moss {int(moss.sum()) / 1e4:.1f} ha, "
        f"{time.time() - t0:.0f} s")
    return comps, {k: v["png_sha256"] for k, v in sorted(mk.src.items())}


# ------------------------------------------------------------------ per-tile placement (worker)
A = {}


def init_worker(cfg):
    a = argparse.Namespace(**cfg)
    t = np.load(a.terrain)
    fp = np.load(a.footprint)
    cv = np.load(a.cover)
    ref = json.loads(Path(a.reference).read_text(encoding="utf-8"))
    work = Path(a.out) / "work"
    pal_names = sorted(ref["models"])
    guide = cfg.get("accepted_canopy")
    A["accepted_sd"] = np.load(guide["sd"]["path"], mmap_mode="r") if guide else None
    A["accepted_trees"] = np.load(guide["points"]["path"], mmap_mode="r") if guide else None
    A["accepted_tree_index"] = cKDTree(A["accepted_trees"]) if guide else None
    planned = cfg.get("planned_clearings")
    A["planned_clearings"] = np.load(planned["path"], mmap_mode="r", allow_pickle=False) if planned else None
    if planned and (A["planned_clearings"].shape != (MAP, MAP) or A["planned_clearings"].dtype != bool):
        raise ValueError("invalid planned clearing raster")
    A.update({"a": a, "ref": ref, "H": t["heights"].astype(np.float64), "plane": fp["plane"], "env": fp["env_plane"],
              "narva": t["narva"], "kit_cells": t["v31_kit"], "bridge_cells": t["v31_bridge_cut"] | t["v31_bridge_fill"],
              "core": cv["osmres_relation_5351287"] | cv["osmres_relation_5351299"],
              "slot": np.load(work / "slot1m.npy", mmap_mode="r"), "wsea": np.load(work / "wsea1m.npy", mmap_mode="r"),
              "object_gap": np.load(work / "object-gap1m.npy", mmap_mode="r"),
              "bog": np.load(work / "bog1m.npy", mmap_mode="r"), "moss": np.load(work / "moss1m.npy", mmap_mode="r"),
              "bogtree": np.load(work / "bogtree1m.npy", mmap_mode="r"),
              "bogforest": np.load(work / "bogforest1m.npy", mmap_mode="r"),
              "roads": road_tree(), "hulls": object_hulls(a.stage_wrp)[0], "limits": model_limits(ref["models"]),
              "wetv": cKDTree(wet_vertices(t["heights"].astype(np.float64), fp["plane"], fp["env_plane"])),
              "edge_profile": edge_profile(ref), "road_profile": road_profile(ref), "footprint": RoadFootprint(pal_names),
              "canopy_solitary": canopy_solitary(ref), "pal_names": pal_names,
              "exclude": json.loads(Path(a.exclude).read_text(encoding="utf-8"))["polygons"] if a.exclude else []})


def place_tile(job):
    """job=(tile, core rows, core cols, pass, K). Pass0 calibrates nonbush;
    pass2 places final nonbush; pass3 calibrates bushes against those final
    tree centres; pass4 places final bushes. Sampling streams remain0/1.
    Calibration passes return expected/accepted counts; placement returns
    core instances. The bush guide is global, independent of tile size."""
    ti, ci0, ci1, cj0, cj1, pas, K = job
    a, ref, H, plane, env = A["a"], A["ref"], A["H"], A["plane"], A["env"]
    seed, halo = a.seed, a.halo
    # Consumer canopy cells have boundaries at x,z multiples of5m. North-up
    # row indices therefore need MAP%5 phase, since MAP is not divisible by5.
    # Keep the same physical padding, 1m fields and world-anchored candidates.
    phase = MAP % 5
    wi0, wj0 = (ci0 - RASTER_PAD - phase) // 5 * 5 + phase, (cj0 - RASTER_PAD) // 5 * 5
    wi1, wj1 = -(-(ci1 + RASTER_PAD - phase) // 5) * 5 + phase, -(-(cj1 + RASTER_PAD) // 5) * 5
    ri0, ri1, rj0, rj1 = ci0 - halo, ci1 + halo, cj0 - halo, cj1 + halo
    Hh, Ww = wi1 - wi0, wj1 - wj0
    X, Z = np.meshgrid(wj0 + np.arange(Ww) + 0.5, MAP - wi0 - np.arange(Hh) - 0.5)
    h1, slope1, _, _ = tri_eval(H, X, Z)
    ws = read_global(A["wsea"], wi0, wi1, wj0, wj1, 3)
    water1, sea1 = (ws & 1) > 0, (ws & 2) > 0
    slot = read_global(A["slot"], wi0, wi1, wj0, wj1, 255)
    bog = read_global(A["bog"], wi0, wi1, wj0, wj1, False)
    moss = read_global(A["moss"], wi0, wi1, wj0, wj1, False)
    bogtree = read_global(A["bogtree"], wi0, wi1, wj0, wj1, 0).astype(np.float64)
    bogforest = read_global(A["bogforest"], wi0, wi1, wj0, wj1, 1).astype(np.float64)
    corepx = np.zeros(X.shape, bool)
    corepx[ci0 - wi0:ci1 - wi0, cj0 - wj0:cj1 - wj0] = True
    vr = np.clip(np.rint((ZTOP - Z) / 6).astype(int), 0, N - 1)
    vc = np.clip(np.rint(X / 6).astype(int), 0, N - 1)
    core = A["core"][vr, vc]
    dwat = edt(~water1, 1e9)
    object_gap = read_global(A["object_gap"], wi0, wi1, wj0, wj1, False) & ~bog
    forest = (slot == 1) & ~water1 & ~sea1 & ~object_gap
    bd = np.where(bog, edt(bog) - 0.5, -1.0)
    wb = np.where(bog, bog_transition_weight(bd), 0.0)
    wm = np.clip(bd / BOG_MOSS_TRANS_M, 0.0, 1.0)
    wm = wm * wm * (3 - 2 * wm)
    dt = np.where(forest, edt(forest) - 0.5, 0.5 - edt(~forest))
    ci_ = CLASSES.index
    tcls = np.full(forest.shape, ci_("open"), np.int8)
    tcls[forest & (dt >= EDGE_IN_M)] = ci_("interior")
    tcls[forest & (dt < EDGE_IN_M)] = ci_("edge_in")
    tcls[~forest & (dt >= -EDGE_OUT_M)] = ci_("edge_out")
    rip = dwat <= RIPARIAN_M
    cls = tcls.copy()
    cls[rip & forest] = ci_("riparian")
    cls[rip & ~forest] = ci_("riparian_open")
    cls[bog] = ci_("bog_open")
    # Calibrate actual admission separately for each physical transition stratum.
    # A core of low pines and a rim with mature forest trees have different losses.
    # Expected intensity, palettes, moss, and transition curve are unchanged.
    cls[bog & (bd < BOG_TRANS_M/2)] = ci_("bog_rim_outer")
    cls[bog & (bd >= BOG_TRANS_M/2) & (bd < BOG_TRANS_M)] = ci_("bog_rim_inner")
    edge = np.isin(tcls, [ci_("edge_in"), ci_("edge_out")]) & ~rip
    ep = A["edge_profile"]
    prof = lambda key: np.interp(dt, ep["d"], ep[key])  # noqa: E731
    fld = lambda fid, sg: smooth_field_w(seed, fid, wi0, wi1, wj0, wj1, sg)  # noqa: E731
    cfl = lambda fid, prm: cluster_field_w(seed, fid, wi0, wi1, wj0, wj1, *prm)  # noqa: E731
    stand = np.exp(STAND_SIGMA * fld(F_STAND, STAND_SMOOTH) - STAND_SIGMA ** 2 / 2)
    coref = np.where(core, CORE_FACTOR, 1.0)
    bfield = fld(F_BROADLEAF, BROADLEAF_STANDS[2])
    bush_c = cfl(F_BUSH, BUSH_CLUSTER)
    dead_c = cfl(F_DEAD, DEAD_CLUSTER)
    # trees: Livonia edge profile with patchy spill outside the texture, analytic mean correction
    sig = np.interp(dt, *SPILL_SIGMA)
    S = np.exp(sig * fld(F_SPILL, SPILL_SMOOTH) - sig ** 2 / 2)
    t_raw = prof("trees")
    cap = float(np.interp(0.5, ep["d"], ep["trees"]))
    neg = dt < 0
    t_edge = np.where(neg, np.minimum(t_raw * S, cap) * t_raw / spill_expectation(t_raw, cap, sig), t_raw)
    D = {c: DESIGN[c] for c in DESIGN}
    lam_t = np.where(tcls == ci_("interior"), D["interior"][0], D["open"][0])
    lam_t = np.where(edge, t_edge, lam_t)
    dense = np.isin(tcls, [ci_("interior"), ci_("edge_in")]) & ~rip
    lam_t = lam_t * np.where(dense, stand * coref, 1.0)
    rf, ro = (rip & forest), (rip & ~forest)
    lam_t = np.where(rf, np.interp(dwat, RIP_D, RIPARIAN_F["trees"]) * stand, lam_t)
    lam_t = np.where(ro, np.interp(dwat, RIP_D, RIPARIAN_O["trees"]), lam_t)
    lam_t = lam_t / 1e4
    bint = DESIGN["interior"][4]
    low = (bint - BROADLEAF_STANDS[0] * BROADLEAF_STANDS[1]) / (1 - BROADLEAF_STANDS[0])
    bl = np.where(tcls == ci_("interior"), np.where(bfield >= ndtri(1 - BROADLEAF_STANDS[0]), BROADLEAF_STANDS[1], low), DESIGN["open"][4])
    bl = np.where(edge, prof("broadleaf"), bl)
    bl = np.where(rf, RIPARIAN_F["broadleaf"], np.where(ro, RIPARIAN_O["broadleaf"], bl))
    solt = np.where(tcls == ci_("open"), DESIGN["open"][5], math.nan)
    solt = np.where(edge, prof("solitary"), solt)
    solt = np.where(rip, math.nan, solt)
    lam_b = np.where(tcls == ci_("interior"), D["interior"][1], D["open"][1])
    lam_b = np.where(edge, prof("bush"), lam_b)
    lam_b = np.where(rf, np.interp(dwat, RIP_D, RIPARIAN_F["bush"]), np.where(ro, np.interp(dwat, RIP_D, RIPARIAN_O["bush"]), lam_b))
    lam_b = lam_b / 1e4 * bush_c
    lam_d = np.where(tcls == ci_("interior"), D["interior"][2], D["open"][2])
    lam_d = np.where(edge, prof("dead"), lam_d)
    lam_d = np.where(rf, RIPARIAN_F["dead"], np.where(ro, RIPARIAN_O["dead"], lam_d))
    lam_d = lam_d / 1e4 * dead_c
    # road side on the forest texture (Livonia road profile on forest surface)
    road_px = A["roads"].query(np.c_[X.ravel(), Z.ravel()], distance_upper_bound=60.0)[0].reshape(X.shape)
    d_re = road_px - ROAD_HALF
    rs = forest & (d_re < ROAD_SPAN) & ~rip
    rp = A["road_profile"]
    rpf = lambda key: np.interp(d_re, rp["d"], rp[key])  # noqa: E731
    lam_t = np.where(rs, rpf("trees") / 1e4 * stand * coref, lam_t)
    lam_b = np.where(rs, rpf("bush") / 1e4 * bush_c, lam_b)
    lam_d = np.where(rs, rpf("dead") / 1e4 * dead_c, lam_d)
    bl = np.where(rs, rpf("broadleaf"), bl)
    solt = np.where(rs, np.interp(d_re, rp["sol_d"], rp["solitary"]), solt)
    pctx = np.full(forest.shape, 2, np.int8)                         # 0 interior, 1 edge, 2 open, 3 riparian palette
    pctx[tcls == ci_("interior")] = 0
    pctx[edge & (dt >= PALETTE_CUT[0])] = 0
    pctx[edge & (dt < PALETTE_CUT[0]) & (dt >= PALETTE_CUT[1])] = 1
    pctx[rip] = 3
    # Approved sparse open bog on every old texture; clearings are repainted downstream
    pine_c = cfl(F_PINE, BOG_PINE_CLUSTER)
    lam_t_bog = bogtree * pine_c / 1e4  # approved sparse open bog, irrespective of old floor paint
    lam_b_bog = BOG_BUSH / 1e4 * bush_c * np.where(moss, BOG_MOSS_BUSH, 1.0)
    lam_d_bog = BOG_DEAD / 1e4 * dead_c
    lam_t = np.where(bog, (1 - wb) * bogforest * lam_t + wb * lam_t_bog, lam_t)
    # Every tree family respects the moss clearing, including the surrounding forest
    # blended into the rim. 0.75 m covers a 1 m pixel's corner relative to its centre.
    moss_distance = ndimage.distance_transform_edt(~moss) if moss.any() else np.full(moss.shape, np.inf)
    lam_t = np.where(moss_distance <= BOG_MOSS_GAP_M + 0.75, 0.0, lam_t)
    lam_b = np.where(bog, (1 - wb) * lam_b + wb * lam_b_bog, lam_b)
    lam_d = np.where(bog, (1 - wb) * lam_d + wb * lam_d_bog, lam_d)
    PAL = ["interior", "edge", "open", "riparian", "bog"]
    reed_c = cfl(F_REED, REED_CLUSTER)
    # admissible pixels (raster pre-filter; exact checks follow per instance)
    land_ok = ~water1 & ~sea1 & (road_px > ROAD_HALF + 0.5) & (slope1 <= SLOPE_MAX) & (slot != 255)
    not_gravel = slot != 0
    adm = land_ok & not_gravel & ~object_gap
    lam_t, lam_b, lam_d = lam_t * adm, lam_b * adm, lam_d * adm
    # Exact exclusions create internal forest boundaries independently of floor paint.
    # Cover the texture transition plus the canopy mantle to reach interior intensity continuously from
    # an unplantable gap. The later canopy-relative floor has its own reference profile.
    gap_distance = edt(~object_gap, 1e9)
    gap_span = 60.0  # [DESIGN] calibrated exterior width; reference canopy densities stay fixed
    gap_weight = np.clip(gap_distance / gap_span, 0.0, 1.0)
    gap_weight = np.where(bog | rip, 1.0, gap_weight * gap_weight * (3.0 - 2.0 * gap_weight))
    lam_t *= gap_weight
    lam_r = np.where(rip & land_ok & ~bog, REED_HA / 1e4 * np.exp(-dwat / REED_DECAY) / REED_NORM * reed_c, 0.0)
    # canopy-relative solitary target: expected-density provisional canopy with
    # 5m cells, 20m disc and >=60 trees/ha. Producer and measurement cells share
    # physical x,z boundaries at multiples of5m despite the north-up producer.
    lt5 = lam_t.reshape(Hh // 5, 5, Ww // 5, 5).sum(axis=(1, 3))
    yy, xx = np.mgrid[-4:5, -4:5]
    disc = ((xx * 5.0) ** 2 + (yy * 5.0) ** 2 <= 400.0).astype(float)
    fm5 = ndimage.convolve(lt5, disc, mode="nearest") / (disc.sum() * 25.0 / 1e4) >= 60.0
    sd5 = np.where(fm5, ndimage.distance_transform_edt(fm5), -ndimage.distance_transform_edt(~fm5)) * 5.0 if fm5.any() and not fm5.all() \
        else np.full(fm5.shape, 1e3 if fm5.all() else -1e3)
    sd1 = np.repeat(np.repeat(sd5, 5, 0), 5, 1)
    c_lo, c_sol, c_broad = A["canopy_solitary"]
    solc = c_sol[np.clip(np.searchsorted(c_lo, np.floor(sd1 / 5.0) * 5.0, side="right") - 1, 0, len(c_lo) - 1)]
    # Family mix must use the same canopy distance as the reference's open-land
    # context. Forest-floor paint alone can persist in a sparse clearing.
    broadc = c_broad[np.clip(np.searchsorted(c_lo, np.floor(sd1 / 5.0) * 5.0, side="right") - 1, 0, len(c_lo) - 1)]
    open_mix = np.clip((-sd1 - 25.0) / 10.0, 0.0, 1.0) * (~rip & ~bog)
    bl = np.maximum(bl, (1.0 - open_mix) * bl + open_mix * broadc)
    near_c = (sd1 < CANOPY_SOL_SPAN) & ~rip
    solt = np.where(near_c, np.where(rs, np.maximum(np.nan_to_num(solt, nan=0.0), solc), solc), solt)
    # Bush contexts come from the final accepted trees when available. This
    # raster is global to the run, independent of the placement tile size.
    bush_sd = sd1
    if A["accepted_sd"] is not None:
        gr = np.floor((math.ceil(MAP / 5) * 5 - Z) / 5).astype(int)
        gc = np.floor(X / 5).astype(int)
        valid = (gr >= 0) & (gc >= 0) & (gr < A["accepted_sd"].shape[0]) & (gc < A["accepted_sd"].shape[1])
        bush_sd = np.full(sd1.shape, -1000.0)
        bush_sd[valid] = A["accepted_sd"][gr[valid], gc[valid]]
    cb_lo, cb_v = np.array(CANOPY_BUSH[0]), np.array(CANOPY_BUSH[1])
    # [DESIGN] Use the same one-cell support extension as the tree mantle
    # near mandatory gaps; retain every measured bush-bin value and onset.
    cb_span = CANOPY_SOL_SPAN + np.where(gap_distance < gap_span + CANOPY_SOL_SPAN, 5.0, 0.0)
    in_cb = (bush_sd >= cb_lo[0]) & (bush_sd < cb_span) & ~rip & ~bog
    cbv = cb_v[np.clip(np.searchsorted(cb_lo, np.floor(bush_sd / 5.0) * 5.0, side="right") - 1, 0, len(cb_lo) - 1)]
    # [DESIGN] The texture profile governs the immediate painted boundary.
    # Blend the extra canopy mantle continuously on both sides over20m, the
    # consumer canopy disc radius. Y's25m overlap depleted the actual canopy
    # edge mix. Keep all measured densities, 25m canopy support and normalisation.
    bush_floor_distance = np.clip(np.abs(dt) / 20.0, 0.0, 1.0)
    bush_floor_weight = bush_floor_distance * bush_floor_distance * (3.0 - 2.0 * bush_floor_distance)
    # The downstream painter creates real texture boundaries around tree-free
    # patches. The canopy extra must fade at those boundaries too. Preserve
    # the complete original context target below; use this only to shape its
    # conservative redistribution, never as a new density target or gate cap.
    stale_floor = np.zeros_like(lam_b)
    if pas in (3, 4):
        if A["planned_clearings"] is None:
            raise ValueError("bush pass requires planned clearing guide")
        planned_forest = forest & ~read_global(A["planned_clearings"], wi0, wi1, wj0, wj1, False)
        planned_dt = np.where(planned_forest, edt(planned_forest)-0.5, 0.5-edt(~planned_forest))
        painted_u = np.clip(np.minimum(np.abs(dt), np.abs(planned_dt))/20.0, 0.0, 1.0)
        painted_weight = painted_u*painted_u*(3.0-2.0*painted_u)
        stale_floor = np.where(in_cb, np.maximum(cbv/1e4*adm-lam_b/np.maximum(bush_c, 1e-12), 0.0)*(bush_floor_weight-painted_weight), 0.0)
    lam_b = np.where(in_cb, lam_b + np.maximum(cbv / 1e4 * bush_c * adm - lam_b, 0.0) * bush_floor_weight, lam_b)
    bush_dry = ~bog & ~rip
    bush_target = lam_b / np.maximum(bush_c, 1e-12)
    # Canopy mantle: original Livonia bins at the adjusted provisional distance.
    ct_lo, ct_v = np.array(CANOPY_TREES[0]), np.array(CANOPY_TREES[1])
    # The traced actual canopy inner mantle is one 5m cell inward from the
    # provisional canopy near mandatory gaps. Use the original reference bins
    # at that distance, without attenuating those canopy-relative values again.
    ct_sd = sd1 - np.where(gap_distance < gap_span + CANOPY_SOL_SPAN, 5.0, 0.0)
    in_ct = (ct_sd >= ct_lo[0]) & (ct_sd < CANOPY_SOL_SPAN) & ~rip & ~bog & (moss_distance > BOG_MOSS_GAP_M + 0.75) & ~object_gap
    ctv = ct_v[np.clip(np.searchsorted(ct_lo, np.floor(ct_sd / 5.0) * 5.0, side="right") - 1, 0, len(ct_lo) - 1)]
    tree_before_canopy_floor = lam_t
    lam_t = np.where(in_ct, np.maximum(lam_t, ctv / 1e4 * stand * coref * adm), lam_t)
    # [DESIGN] The extra exterior tree mantle needs its reference bush
    # companion. Use the bush/tree ratio from the same Livonia canopy bin,
    # including the existing5m near-gap distance correction. This term
    # accompanies the added tree intensity without changing that intensity.
    companion_bush = cb_v[np.clip(np.searchsorted(cb_lo, np.floor(ct_sd / 5.0) * 5.0, side="right") - 1, 0, len(cb_lo) - 1)]
    exterior_u = np.clip(-dt / 20.0, 0.0, 1.0)
    exterior_weight = exterior_u * exterior_u * (3.0 - 2.0 * exterior_u)
    extra_tree_intensity = np.maximum(lam_t - tree_before_canopy_floor, 0.0)
    companion_intensity = extra_tree_intensity / np.maximum(stand * coref, 1e-12) * companion_bush / np.maximum(ctv, 1e-12)
    # Include the complete companion target in the same normalisation.
    bush_target = bush_target + np.where(bush_dry, companion_intensity * exterior_weight, 0.0)
    shaped_target = bush_target-stale_floor
    if (shaped_target < -1e-12).any():
        raise ValueError("clearing redistribution removed base bush intensity")
    raw_bush = np.maximum(shaped_target, 0.0) * bush_c
    bush_context = np.where(bush_sd >= 25.0, 0, np.where(bush_sd >= -10.0, 1, 2))
    bush_correction = np.ones_like(lam_b)
    for context in (0, 1, 2):
        mask = bush_dry & (bush_context == context)
        target = bush_target * mask
        raw = raw_bush * mask
        # Conservative redistribution with the symmetric Gaussian operator G:
        # lambda = raw * G(target / G(raw)). For a finite zero-padded window,
        # sum(lambda) = sum(target), since G is its own transpose. The former
        # raw * G(target)/G(raw) lost target mass on fragmented contexts.
        denominator = ndimage.gaussian_filter(raw, 50.0, mode="constant", truncate=2.0)
        if np.any((target > 0) & (denominator <= 0)):
            raise ValueError("positive bush target has no redistribution support")
        allocation = np.divide(target, denominator, out=np.zeros_like(target), where=denominator > 0)
        factor = ndimage.gaussian_filter(allocation, 50.0, mode="constant", truncate=2.0)
        balanced = raw * factor
        target_mass = float(target.sum())
        if not np.isfinite(balanced).all() or abs(float(balanced.sum())-target_mass) > max(1.0,target_mass)*1e-12:
            raise ValueError("bush target mass was not conserved")
        bush_correction = np.where(mask, factor, bush_correction)
    lam_b = np.where(bush_dry, raw_bush * bush_correction, lam_b)
    tree_admission = np.where(in_ct, 1 + np.clip(np.searchsorted(ct_lo, ct_sd, side="right") - 1, 0, 2), 0)
    ref_models = ref["models"]
    pal = dict(ref["palette"], bog=BOG_PALETTE)
    lim, hulls = A["limits"], A["hulls"]

    def choose(fam_idx, pc, st, slope_pt, r, r2):
        names = np.empty(len(pc), object)
        for k in range(len(pc)):
            lst = [(nm, w) for nm, w in pal[PAL[pc[k]]][FAM[fam_idx[k]]] if lim[nm] >= slope_pt[k]]
            if fam_idx[k] in (0, 1) and np.isfinite(st[k]):
                want = bool(r2[k] < st[k])
                sub = [(nm, w) for nm, w in lst if bool(ref_models[nm]["solitary"]) == want]
                lst = sub or lst
            if not lst:
                names[k] = None
                continue
            ws_ = np.array([w for _, w in lst])
            names[k] = lst[int(np.searchsorted(np.cumsum(ws_) / ws_.sum(), r[k], side="right"))][0] if r[k] < 1 else lst[-1][0]
        return names

    def exact_ok(x, z, fam_name, names, scale_guess):
        """Exact exclusion checks at the instance position (scale_guess = upper scale used for the margins)."""
        n = len(x)
        ok = np.ones(n, bool)
        if not n:
            return ok
        d_road = A["roads"].query(np.c_[x, z], distance_upper_bound=60.0)[0]
        clr = np.array([ROAD_CLEAR[f] for f in fam_name])
        ok &= ~(d_road < ROAD_HALF + clr + SAFETY)
        _, sl, _, _ = tri_eval(H, x, z)
        ok &= ~(sl > np.array([lim[nm] for nm in names]))
        base_r = np.array([ref_models[nm]["base_radius_plan"] for nm in names]) * scale_guess
        crown = np.array([ref_models[nm]["crown_halfwidth"] for nm in names]) * scale_guess
        reed = np.array([f == "reed" for f in fam_name])
        mw = np.where(reed, REED_WATER, base_r + WATER_EXTRA) + SAFETY
        idx = np.flatnonzero(ok)
        if idx.size:                                  # v4i: dense disc check where water or sea lies within reach
            dv = A["wetv"].query(np.c_[x[idx], z[idx]], distance_upper_bound=float(mw[idx].max()) + 9.0)[0]
            near = dv <= mw[idx] + 8.6                # a wet point lies within one cell diagonal (8.49 m) of a wet vertex
            if near.any():
                ok[idx[near][disc_wet_dense(H, plane, env, x[idx][near], z[idx][near], mw[idx][near])]] = False
        for hobj in hulls:
            hb = hobj["hull"]
            if hb[:, 0].min() - 40 > x.max() or hb[:, 0].max() + 40 < x.min() or hb[:, 1].min() - 40 > z.max() or hb[:, 1].max() + 40 < z.min():
                continue
            need = (crown + BRIDGE_EXTRA if hobj["kind"] == "bridge" else base_r + KIT_EXTRA) + SAFETY
            ok &= ~(dist_to_polygon(x, z, hb) < need)
        for key, msk, extra in (("bridge_cells", A["bridge_cells"], BRIDGE_EXTRA), ("kit_cells", A["kit_cells"], KIT_EXTRA), ("narva", A["narva"], NARVA_M)):
            need = (crown + extra if key == "bridge_cells" else (base_r + extra if key == "kit_cells" else np.full(n, extra))) + SAFETY
            ok &= ~(cell_distance(msk, x, z, float(need.max())) < need)
        for ex in A["exclude"]:
            pg = np.asarray(ex["polygon_xz"], float)
            ok &= ~(dist_to_polygon(x, z, pg) < float(ex["margin_m"]) + base_r + SAFETY)
        return ok

    def scale_cap(names):
        return np.array([ref_models[nm]["scale_q"][-1] for nm in names])

    trees, bushes, deads, reeds = Grid(3.0), Grid(3.0), Grid(3.0), Grid(3.0)
    # Bush-only passes use the same globally accepted tree centres as the
    # written forest. Include every possible transformed bush centre plus
    # the 0.52m tree clearance; no new tree decisions are made here.
    if pas in (3, 4):
        if A["accepted_tree_index"] is None:
            raise ValueError("bush pass requires accepted tree guide")
        bc_max = max(np.linalg.norm(m["bc"]) * m["scale_q"][-1]
                     for m in ref_models.values() if m["family"] == "bush")
        centre = ((rj0+rj1)/2, MAP-(ri0+ri1)/2)
        radius = math.hypot((rj1-rj0)/2, (ri1-ri0)/2) + bc_max + 0.52
        ids = A["accepted_tree_index"].query_ball_point(centre, radius)
        for tx, tz in A["accepted_trees"][ids]:
            trees.add(tx, tz, 0)
    out = {k: [] for k in ("x", "z", "names", "fam", "cls", "M", "T", "s", "dt", "bd", "pick")}
    stats = {}
    cls_f, wb_f, pctx_f, solt_f, bl_f, core_f = cls.ravel(), wb.ravel(), pctx.ravel(), solt.ravel(), bl.ravel(), corepx.ravel()
    for gid, group in enumerate(GROUPS):
        if (pas == 2 and group == "bush") or (pas in (3, 4) and group != "bush"):
            continue
        lam = {"trees": lam_t, "dead": lam_d, "bush": lam_b, "reed": lam_r}[group]
        if group == "trees" and K is not None:
            lamK = lam * np.asarray(K["tree_admission"], float)[cls, tree_admission]
        else:
            lamK = lam * (np.asarray(K[group], float)[cls] if K is not None and pas != 3 else 1.0)
        sample_pass = 0 if pas in (0, 3) else 1
        x, z, flat, U = sample_world(seed, gid, sample_pass, lamK, wi0, wj0, ri0, ri1, rj0, rj1)
        pick = U[:, 0] < wb_f[flat]                                   # this instance follows the bog design
        if group == "trees":
            fam_idx = np.where(U[:, 1] < np.where(pick, BOG_BROADLEAF, bl_f[flat]), 1, 0)
        else:
            fam_idx = np.full(len(x), {"dead": 3, "bush": 2, "reed": 4}[group])
        _, slp, _, _ = tri_eval(H, x, z)
        pc = np.where(pick, PAL.index("bog"), pctx_f[flat])
        st = np.where(pick, math.nan, solt_f[flat])
        names = choose(fam_idx, pc, st, slp, U[:, 2], U[:, 3])
        okn = np.array([nm is not None for nm in names], bool)
        x, z, flat, fam_idx, names, pick, U = x[okn], z[okn], flat[okn], fam_idx[okn], names[okn], pick[okn], U[okn]
        ok = exact_ok(x, z, [FAM[f] for f in fam_idx], names, scale_cap(names))
        x, z, flat, fam_idx, names, pick, U = x[ok], z[ok], flat[ok], fam_idx[ok], names[ok], pick[ok], U[ok]
        M, T, s = transforms(ref_models, names, x, z, H, U, low=pick & (fam_idx <= 1))
        solid = np.isin(fam_idx, [0, 1, 2])
        tr = np.array([ref_models[nm]["trunk_radius"] for nm in names]) * s * 1.02
        emb = np.array([-min(ref_models[nm]["visual_bottom_local"], 0.0) for nm in names]) * s
        ok2 = ~solid | (trunk_drop(H, x, z, tr) <= emb - 0.005) if len(x) else np.zeros(0, bool)
        ok2 &= A["footprint"].clear(names, M, T, s, H)
        x, z, flat, fam_idx, names, pick, U, M, T, s = (x[ok2], z[ok2], flat[ok2], fam_idx[ok2], names[ok2], pick[ok2], U[ok2],
                                                       M[ok2], T[ok2], s[ok2])
        if group == "trees":
            size = np.array([ref_models[nm]["size"] for nm in names], int)
            order = np.lexsort((U[:, 9], -size))
        else:
            order = np.argsort(U[:, 9], kind="stable")
        x, z, flat, fam_idx, names, pick, U, M, T, s = (x[order], z[order], flat[order], fam_idx[order], names[order], pick[order],
                                                       U[order], M[order], T[order], s[order])
        if group == "trees":
            keep = accept_trees(T[:, 0], T[:, 2], size[order], fam_idx, U[:, 4], trees, reeds)
        elif group == "dead":
            keep = accept_simple(T[:, 0], T[:, 2], U[:, 4], deads, 0.77, trees, "dead")
        elif group == "bush":
            keep = accept_simple(T[:, 0], T[:, 2], U[:, 4], bushes, 0.28, trees, 0.52)
        else:
            keep = accept_simple(T[:, 0], T[:, 2], U[:, 4], reeds, REED_REED, trees, REED_TREE, REED_SOFT)
        inc = keep & core_f[flat]
        if pas in (0, 3):
            stats[group] = {"exp": np.bincount(cls_f[core_f], weights=lam.ravel()[core_f], minlength=len(CLASSES)).tolist(),
                            "got": np.bincount(cls_f[flat[inc]], minlength=len(CLASSES)).tolist()}
            if group == "trees":
                detail = (cls * len(TREE_ADMISSION_STRATA) + tree_admission).ravel()
                stats["tree_admission"] = {
                    "exp": np.bincount(detail[core_f], weights=lam.ravel()[core_f], minlength=len(CLASSES)*4).tolist(),
                    "got": np.bincount(detail[flat[inc]], minlength=len(CLASSES)*4).tolist()}
            continue
        for k_, v_ in (("x", x), ("z", z), ("names", names), ("fam", fam_idx), ("cls", cls_f[flat]), ("M", M), ("T", T), ("s", s),
                       ("dt", dt.ravel()[flat]), ("bd", bd.ravel()[flat]), ("pick", pick)):
            out[k_].append(v_[inc])
    if pas in (0, 3):
        return ti, None, stats
    o = {k: np.concatenate(v) for k, v in out.items()}
    o["names_idx"] = np.array([A["pal_names"].index(nm) for nm in o["names"]], np.uint16)
    del o["names"]
    return ti, o, None


# ------------------------------------------------------------------ driver
def tiles_for(region, size):
    x0, z0, x1, z1 = region
    i_lo, i_hi, j_lo, j_hi = MAP - z1, MAP - z0, x0, x1
    out = []
    for ti, i in enumerate(range((i_lo // size) * size, i_hi, size)):
        for tj, j in enumerate(range((j_lo // size) * size, j_hi, size)):
            ci0, ci1 = max(i, i_lo), min(i + size, i_hi)
            cj0, cj1 = max(j, j_lo), min(j + size, j_hi)
            if ci0 < ci1 and cj0 < cj1:
                out.append((len(out), ci0, ci1, cj0, cj1))
    return out


def write_accepted_canopy(results, work):
    """Same physical canopy definition as Livonia:5m,20m disc,60/ha,
    components>=0.5ha, holes<100m2. Global north-up raster, x/z phase0.
    Source centres are exactly the nonbush records later written to output.
    """
    points = np.concatenate([r[1]["T"][r[1]["fam"] <= 1][:, (0, 2)] for r in results])
    n = math.ceil(MAP / 5)
    # Lower-inclusive world cells first, then reverse to north-up.
    # floor((north-z)/5) puts exact5m boundaries into the adjacent row.
    row = n - 1 - np.floor(points[:, 1]/5).astype(int)
    col = np.floor(points[:, 0]/5).astype(int)
    ok = (row >= 0) & (col >= 0) & (row < n) & (col < n)
    count = np.bincount(row[ok]*n+col[ok], minlength=n*n).reshape(n,n).astype(float)
    yy, xx = np.mgrid[-4:5,-4:5]
    disc = ((xx*5)**2+(yy*5)**2 <= 400).astype(float)
    fm = ndimage.convolve(count, disc, mode="constant")/(disc.sum()*25/1e4) >= 60
    lab, num = ndimage.label(fm)
    sizes = np.bincount(lab.ravel())*25
    keep = sizes >= 5000
    keep[0] = False
    fm = keep[lab]
    holes = ndimage.binary_fill_holes(fm) & ~fm
    lab, num = ndimage.label(holes)
    sizes = np.bincount(lab.ravel())*25
    small = sizes < 100
    small[0] = False
    fm |= small[lab]
    sd = np.where(fm, ndimage.distance_transform_edt(fm), -ndimage.distance_transform_edt(~fm))*5 if fm.any() and not fm.all() else np.full(fm.shape,1000. if fm.all() else -1000.)
    paths = {"points": work/"accepted-tree-centres.npy", "sd": work/"accepted-canopy-sd5m.npy"}
    np.save(paths["points"], points)
    np.save(paths["sd"], sd.astype(np.float32))
    return {k:{"path":str(p),"sha256":sha(p)} for k,p in paths.items()}


def write_planned_clearings(guide, work):
    """Predict the unchanged independent painter400 from final accepted trees.
    Native1m,10m tree distance,8-connected400m2 patches,3m blend and complete
    10.75m moss fringe. Later acceptance compares this against the separate
    exporter and actual final surface. A regional run predicts its own trees;
    partition runs reuse the full-map guide through validated calibration.
    """
    points_path = Path(guide["points"]["path"])
    if sha(points_path) != guide["points"]["sha256"]:
        raise ValueError("changed tree guide for planned clearings")
    points = np.load(points_path, allow_pickle=False)
    if points.ndim != 2 or points.shape[1] != 2 or not len(points) or not np.isfinite(points).all():
        raise ValueError("invalid tree guide for planned clearings")
    paths = {name:work/name for name in ("slot1m.npy", "wsea1m.npy", "moss1m.npy")}
    slot = np.load(paths["slot1m.npy"], mmap_mode="r", allow_pickle=False)
    wet = np.load(paths["wsea1m.npy"], mmap_mode="r", allow_pickle=False)
    moss = np.load(paths["moss1m.npy"], mmap_mode="r", allow_pickle=False)
    if slot.shape != (MAP,MAP) or wet.shape != slot.shape or moss.shape != slot.shape or moss.dtype != bool:
        raise ValueError("invalid rasters for planned clearings")
    tree = cKDTree(points);raw = np.zeros(slot.shape,bool)
    for i0 in range(0,MAP,128):
        forest = (slot[i0:i0+128] == 1) & ((wet[i0:i0+128] & 1) == 0)
        ii,jj = np.nonzero(forest)
        q = np.c_[jj+0.5,MAP-i0-ii-0.5]
        dist = tree.query(q,distance_upper_bound=10.0)[0]
        raw[i0+ii,jj] = dist >= 10.0
    labels,_ = ndimage.label(raw,structure=np.ones((3,3),bool))
    sizes = np.bincount(labels.ravel());keep = sizes >= 400;keep[0] = False
    mask = keep[labels];del labels,raw
    mask = ndimage.binary_dilation(mask,iterations=3) & (slot == 1) & ((wet & 1) == 0)
    gap = (ndimage.distance_transform_edt(~moss) <= 10.75) if moss.any() else np.zeros(mask.shape,bool)
    mask |= gap & (slot == 1) & ((wet & 1) == 0)
    output = work/"planned-clearings.npy"
    if output.exists():
        raise ValueError("planned clearing output already exists")
    np.save(output,mask)
    return dict(path=str(output),sha256=sha(output),points_sha256=guide["points"]["sha256"],
                input_sha256={k:sha(p) for k,p in paths.items()},minimum_patch_m2=400,
                tree_free_distance_m=10.0,blend_margin_m=3.0,moss_margin_m=10.75)


def calibration_ratio(exp, got):
    exp, got = np.asarray(exp,float), np.asarray(got,float)
    ratio = np.divide(exp,got,out=np.ones_like(exp),where=got>=5)
    return np.round(np.clip(ratio,1.,3.),4).tolist()


def validate_calibration(report, a):
    if report.get("classes") != CLASSES or report.get("tree_admission_strata") != TREE_ADMISSION_STRATA:
        raise ValueError("calibration class/stratum schema mismatch")
    if report.get("seed") != a.seed or report.get("tool_sha256") != sha(__file__):
        raise ValueError("calibration seed/source mismatch")
    for k,v in report["inputs"].items():
        if sha(getattr(a,k.replace("-","_"))) != v["sha256"]:
            raise ValueError("calibration input mismatch: "+k)
    expected_exclude = report.get("exclude")
    if bool(a.exclude) != bool(expected_exclude) or (a.exclude and sha(a.exclude) != expected_exclude["sha256"]):
        raise ValueError("calibration exclusions mismatch")
    if a.layer_dir != report["layer_dirs"]:
        raise ValueError("calibration layer directories mismatch")
    K = report["calibration_K"]
    for group in GROUPS+["tree_admission"]:
        values = np.asarray(K[group],float)
        shape = (len(CLASSES),4) if group == "tree_admission" else (len(CLASSES),)
        if values.shape != shape or not np.isfinite(values).all() or (values<1).any() or (values>3).any():
            raise ValueError("invalid calibration coefficients: "+group)
    guide = report["accepted_canopy"]
    for k in ("points","sd"):
        if sha(guide[k]["path"]) != guide[k]["sha256"]:
            raise ValueError("changed accepted-canopy dependency: "+k)
    planned = report["planned_clearings"]
    if sha(planned["path"]) != planned["sha256"] or planned["points_sha256"] != guide["points"]["sha256"]:
        raise ValueError("changed planned clearing dependency")
    if (planned["minimum_patch_m2"],planned["tree_free_distance_m"],planned["blend_margin_m"],planned["moss_margin_m"]) != (400,10.0,3.0,10.75):
        raise ValueError("planned clearing contract mismatch")
    for name,digest in planned["input_sha256"].items():
        if report["work_sha256"].get(name) != digest:
            raise ValueError("planned clearing raster binding mismatch")
    return K, guide


def main():
    ap = argparse.ArgumentParser()
    for k in ("terrain", "footprint", "stage-wrp", "pbo", "cover", "reference", "out"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--layer-dir", action="append", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--region", default=f"0,0,{MAP},{MAP}")
    ap.add_argument("--tile", type=int, default=500)
    ap.add_argument("--halo", type=int, default=30)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--calibration")
    ap.add_argument("--exclude")
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        raise SystemExit(f"{out} exists")
    region = [int(v) for v in a.region.split(",")]
    if a.tile % 5 or a.halo < 0 or a.halo > 40 or not (0 <= region[0] < region[2] <= MAP and 0 <= region[1] < region[3] <= MAP):
        raise SystemExit("tile must be a multiple of 5, halo in 0..40, region inside the map")
    work = out / "work"
    work.mkdir(parents=True)
    t0 = time.time()
    lines = []

    def log(s):
        lines.append(s)
        print(s, flush=True)
    comps, mask_png = prepass(a, work, log)
    ref = json.loads(Path(a.reference).read_text(encoding="utf-8"))
    for f_, lst_ in BOG_PALETTE.items():
        for nm_, _ in lst_:
            if nm_ not in ref["models"]:
                raise SystemExit(f"bog palette model {nm_} ({f_}) is not in the Livonia reference")
    land = ~np.load(work / "wsea1m.npy", mmap_mode="r").astype(bool)
    jobs = []
    for ti, ci0, ci1, cj0, cj1 in tiles_for(region, a.tile):
        if land[max(ci0 - a.halo, 0):ci1 + a.halo, max(cj0 - a.halo, 0):cj1 + a.halo].any():
            jobs.append((ti, ci0, ci1, cj0, cj1))
    del land
    cfgd = vars(a).copy()
    if a.calibration:
        calibration_report = json.loads(Path(a.calibration).read_text(encoding="utf-8"))
        K, guide = validate_calibration(calibration_report, a)
        calib = {"source":str(a.calibration), "sha256":sha(a.calibration)}
    else:
        sizes = {g:len(CLASSES) for g in GROUPS}
        sizes["tree_admission"] = len(CLASSES)*4
        agg = {g:{"exp":np.zeros(n),"got":np.zeros(n)} for g,n in sizes.items()}
        with ProcessPoolExecutor(a.workers,initializer=init_worker,initargs=(cfgd,)) as ex:
            for _,_,st in ex.map(place_tile,[j+(0,None) for j in jobs],chunksize=1):
                for g in agg:
                    for key in ("exp","got"):agg[g][key] += st[g][key]
        K = {g:calibration_ratio(v["exp"],v["got"]) for g,v in agg.items()}
        K["tree_admission"] = np.asarray(K["tree_admission"]).reshape(len(CLASSES),4).tolist()
        calib = {"source":"nonbush pass0 plus bush pass0 against accepted final trees",
                 "expected":{g:v["exp"].round(3).tolist() for g,v in agg.items()},
                 "accepted":{g:v["got"].astype(int).tolist() for g,v in agg.items()}}
        log(f"nonbush calibration done in {time.time()-t0:.0f} s")
    with ProcessPoolExecutor(a.workers,initializer=init_worker,initargs=(cfgd,)) as ex:
        nonbush = list(ex.map(place_tile,[j+(2,K) for j in jobs],chunksize=1))
    log(f"final nonbush placement done in {time.time()-t0:.0f} s")
    if not a.calibration:
        guide = write_accepted_canopy(nonbush, work)
    cfgd["accepted_canopy"] = guide
    planned = calibration_report["planned_clearings"] if a.calibration else write_planned_clearings(guide, work)
    cfgd["planned_clearings"] = planned
    log(f"planned clearing guide ready in {time.time()-t0:.0f} s")
    with ProcessPoolExecutor(a.workers,initializer=init_worker,initargs=(cfgd,)) as ex:
        if not a.calibration:
            exp, got = np.zeros(len(CLASSES)), np.zeros(len(CLASSES))
            for _,_,st in ex.map(place_tile,[j+(3,None) for j in jobs],chunksize=1):
                exp += st["bush"]["exp"];got += st["bush"]["got"]
            K["bush"] = calibration_ratio(exp,got)
            calib["bush_final_tree_admission"] = {"expected":exp.round(3).tolist(),"accepted":got.astype(int).tolist()}
            log(f"bush calibration done in {time.time()-t0:.0f} s")
        bush = list(ex.map(place_tile,[j+(4,K) for j in jobs],chunksize=1))
    by_tile = {r[0]:r[1] for r in bush}
    res = [(ti,{k:np.concatenate([o[k],by_tile[ti][k]]) for k in o},None) for ti,o,_ in nonbush]
    log(f"final bush placement done in {time.time()-t0:.0f} s")
    res.sort(key=lambda r: r[0])
    o = {k: np.concatenate([r[1][k] for r in res]) for k in res[0][1]}
    tile_of = np.concatenate([np.full(len(r[1]["x"]), r[0], np.uint32) for r in res])
    pal_names = sorted(ref["models"])
    n = len(o["x"])
    h = hashlib.sha256()
    with open(out / "records.json", "wb") as f:
        f.write(b"[\n")
        h.update(b"[\n")
        step = 50000
        for s0 in range(0, n, step):
            chunk = []
            for k in range(s0, min(n, s0 + step)):
                rec = {"model": pal_names[o["names_idx"][k]], "matrix": record_matrix(o["M"][k], o["T"][k])}
                chunk.append(json.dumps(rec))
            b = (",\n".join(chunk) + (",\n" if s0 + step < n else "\n")).encode("ascii")
            f.write(b)
            h.update(b)
        f.write(b"]\n")
        h.update(b"]\n")
    arr = np.zeros(n, dtype=[("tile", "<u4"), ("fam", "u1"), ("cls", "u1"), ("model", "<u2"), ("x", "<f8"), ("z", "<f8"),
                             ("tx", "<f8"), ("tz", "<f8"), ("scale", "<f4"), ("dt", "<f4"), ("bd", "<f4"), ("bogpal", "u1")])
    arr["tile"], arr["fam"], arr["cls"], arr["model"] = tile_of, o["fam"], o["cls"], o["names_idx"]
    arr["x"], arr["z"], arr["tx"], arr["tz"] = o["x"], o["z"], o["T"][:, 0], o["T"][:, 2]
    arr["scale"], arr["dt"], arr["bd"], arr["bogpal"] = o["s"], o["dt"], o["bd"], o["pick"]
    np.save(out / "instances.npy", arr)
    hulls, max_id = object_hulls(a.stage_wrp)
    counts = {FAM[f]: int((o["fam"] == f).sum()) for f in range(5)}
    by_cls = {CLASSES[c]: {FAM[f]: int(((o["cls"] == c) & (o["fam"] == f)).sum()) for f in range(5)} for c in range(len(CLASSES))}
    ep = edge_profile(ref)
    report = {"schema": "baltic-forest-v31-report.v4", "seed": a.seed, "region": region, "tile_m": a.tile, "halo_m": a.halo,
              "raster_pad_m": RASTER_PAD, "n_tiles": len(jobs), "n_records": n, "records_sha256": h.hexdigest(),
              "staged_id_range": [max_id + 1, max_id + n], "base_max_id": max_id,
              "inputs": {k: {"path": str(Path(getattr(a, k.replace("-", "_")))), "sha256": sha(getattr(a, k.replace("-", "_")))}
                         for k in ("terrain", "footprint", "stage-wrp", "pbo", "cover", "reference")},
              "exclude": ({"path": str(a.exclude), "sha256": sha(a.exclude)} if a.exclude else None),
              "tool_sha256": sha(__file__), "kit_water_dependencies": {"geometry": sha(KIT_GEOMETRY), "rasterizer": sha(HERE / "streambed_water_v31.py")}, "layer_dirs": a.layer_dir, "mask_png_sha256": mask_png,
              "work_sha256": {p.name: sha(p) for p in sorted(work.glob("*.npy"))},
              "exclusion_objects": {"bridge": sum(1 for x_ in hulls if x_["kind"] == "bridge"), "kit": sum(1 for x_ in hulls if x_["kind"] == "kit")},
              "palette_models": pal_names, "classes": CLASSES, "counts": counts, "counts_by_class": by_cls,
              "calibration_K": K, "calibration": calib, "tree_admission_strata": TREE_ADMISSION_STRATA, "accepted_canopy": guide, "planned_clearings": planned,
              "bog_components": comps,
              "design": {"texture_classes": {c: dict(zip(("trees_ha", "bush_ha", "dead_ha", "reed_ha", "broadleaf_share", "solitary_target"),
                                                         [None if isinstance(x_, float) and math.isnan(x_) else x_ for x_ in v])) for c, v in DESIGN.items()},
                         "riparian_forest": RIPARIAN_F, "riparian_open": RIPARIAN_O, "riparian_bins_m": RIP_D, "reeds_ha": REED_HA,
                         "edge_profile": {k: [round(float(x_), 4) for x_ in v] for k, v in ep.items()},
                         "road_span_m": ROAD_SPAN, "spill_sigma": [list(SPILL_SIGMA[0]), list(SPILL_SIGMA[1])], "spill_smooth_m": SPILL_SMOOTH,
                         "edge_span_m": [EDGE_IN_M, -EDGE_OUT_M], "palette_cut_m": list(PALETTE_CUT), "canopy_solitary_span_m": CANOPY_SOL_SPAN, "canopy_trees_floor": [list(CANOPY_TREES[0]), list(CANOPY_TREES[1])],
                         "mandatory_gap_transition": {"span_m": 60.0, "curve": "smoothstep", "canopy_tree_floor_weighted": False, "canopy_tree_distance_shift_m": 5.0, "canopy_bush_extra_support_m": 5.0, "canopy_bush_floor_blend_m": 20.0, "canopy_bush_floor_weight": "smoothstep(abs(texture_distance)/20)", "dry_bush_cluster_local_sigma_m": 50.0, "dry_bush_cluster_local_support_m": 100.0, "dry_bush_cluster_local_bounds": None, "dry_bush_conservative_operator": "raw*G(target/G(raw)); constant-zero symmetric Gaussian", "dry_bush_combined_support_m": 200.0, "dry_bush_normalisation_profile_weighted": True, "dry_bush_stratum_shrinkage": None, "dry_bush_context": "accepted final trees: interior/edge/open", "planned_texture_floor": "same20m fade at painter400 boundary shapes raw intensity; original context target integral retained", "tree_admission": TREE_ADMISSION_STRATA, "exterior_tree_bush_companion": "same_corrected_canopy_bin_reference_ratio", "exterior_companion_blend_m": 20.0, "raster_pad_m": 450, "extra_support_max_gap_distance_m": 85.0, "bog_and_riparian_weight": 1.0, "producer_vs_measurement_grid_phase_m": 0.0},
                         "road_geometry": {"band_m": [FOOT_BURIED, FOOT_H], "min_axis_distance_m": ROAD_HALF + SAFETY},
                         "bog": {"transition_m": BOG_TRANS_M, "open_trees_ha": BOG_TREES, "wooded_trees_ha": WOODED_BOG_TREES,
                                 "bush_ha": BOG_BUSH, "dead_ha": BOG_DEAD, "broadleaf_share": BOG_BROADLEAF, "moss_core_share": BOG_MOSS_CORE,
                                 "moss_smooth_m": BOG_MOSS_SMOOTH, "moss_min_m2": BOG_MOSS_MIN_M2, "moss_ramp_m": list(BOG_MOSS_RAMP),
                                 "moss_full_share_min": BOG_MOSS_FULL,
                                 "moss_bush_factor": BOG_MOSS_BUSH, "moss_transition_m": BOG_MOSS_TRANS_M, "moss_gap_m": BOG_MOSS_GAP_M,
                                 "pine_cluster": list(BOG_PINE_CLUSTER), "scale_quantile_max": BOG_SCALE_Q, "palette": BOG_PALETTE}}}
    (out / "report.json").write_bytes((json.dumps(report, indent=1) + "\n").encode("utf-8"))
    log(f"records {n} {counts} sha256 {h.hexdigest()} in {time.time() - t0:.0f} s")
    (out / "run.log").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

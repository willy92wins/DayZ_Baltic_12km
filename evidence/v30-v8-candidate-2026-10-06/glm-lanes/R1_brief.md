IMPORTANT PROCESS NOTE: write the complete file FIRST, in one pass, then stop. Do not simulate the self-test by hand;
the receiver runs it. Keep internal deliberation focused.

# Task (one sentence)
Write one Python 3.11 command-line tool, `tools/terrain/profile_rivers_v30.py`, that reshapes the terrain along every
navigable reach, river and stream of a DayZ terrain so that the visible shoreline (where the terrain crosses the water
surface) follows a smoothed outline instead of the 6 m vertex staircase, and optionally raises river and stream beds,
keeping every existing gate and never changing a vertex class or water level.

# Why
Water surfaces are drawn per 6 m cell at a plane (`v30_common.cell_planes`); the visible shore is where the terrain (6 m
grid, NW-SE diagonals) crosses that plane. Today wet vertices sit well under the level and land well over it, so the
crossing falls at a fixed fraction of every wet-land edge and the shore draws the 6 m grid. The lakes already got the
fix: `tools/terrain/profile_lakes_v30.py` (listed below in full) is the REFERENCE IMPLEMENTATION, and your tool is the
same method for flowing water. Measured on the real terrain: crossing offset against the smoothed outline p50/p90 of
1.47/3.72 m (navigable), 1.45/3.51 m (rivers), 0.66/1.98 m (streams); the lakes went from 0.80/2.57 to 0.00/1.22 m.
Differences from the lakes, which are the whole point of this brief:
- Flowing water is not flat: every vertex has its own `level` (a river descends in 0.025 m plane steps). The profile
  target and the gates use per-vertex levels and planes, never one level per body.
- No vertex changes class or level, by construction (the side of a vertex is its input class, not the sign of sd).
  Then the cell planes, and so the existing water pieces, stay valid.
- Navigable reaches keep their 24 m useful channel: only the exact corridor vertices are fixed (the faces that
  intersect the 24 m polygon), not the one-vertex margin the lakes tool fixed, so the channel edges are free.
- The vanilla channel reaches R1-R3 (cells listed in <channels>/axes.json) are drawn by vanilla pieces, not by planes:
  their vertices and everything near them stay fixed.

# Role and success criterion
You are the implementer. The receiver runs `--selftest` and then the tool on the real 2048 x 2048 terrain. Success = the
file runs unchanged with the stated CLI, the self-test passes, the report follows the schema below, no class or level
changes, and no gate count grows. Prefer vectorised numpy/scipy, import the helpers listed below (do not copy them), and
follow profile_lakes_v30.py wherever this brief does not say otherwise.
Only the Python stdlib, numpy, scipy, contourpy and shapely 2.x are available.

# Environment limits you cannot see
- Windows, Python 3.11. Grid N = 2048 vertices per side, 6 m spacing; vertex (r, c) is at game x = 6c, z = 12282 - 6r
  (row 0 north). `v30_common.grid_xz()` returns those x, z arrays.
- About 160 components of flowing water, from 1 to ~24,000 vertices; the largest spans several km. Runtime target under
  10 minutes, peak memory under 8 GB: work in a window around each component, never full-grid per component.
- The tool lives next to the helpers: `sys.path.insert(0, str(Path(__file__).resolve().parent))`, then import from
  `v30_common` (N, cell_planes, vertex_plane_bounds, grid_xz), `finish_shores_v30` (protect_corridors,
  discard_steeper_land_faces), `profile_coast_v30` (EDGES, NARVA, NATURE, SEA_CLASSES, sha, turning, zero_lines) and
  `profile_lakes_v30` (window_lines, G, EPS). Importing those modules has no side effects.

# Verified facts about the input (do not change these conventions)
Terrain NPZ keys: `heights` float32 (N, N) m; `cls` uint8 (N, N): 0 land, 1 sea, 2 lake, 3 navigable, 4 delta, 5 river,
6 stream, 7 pond; `level` float32 (N, N) water level per vertex, NaN on land; bool masks `platform`, `reserve`, `narva`,
`water`, `beach`. Write every key back with its dtype; only `heights` changes.
- `protect_corridors(planes)` returns (exact, margin, entries, sources): exact = every vertex of a face that intersects a
  24 m navigable or delta corridor polygon; margin = exact dilated by one vertex. This tool fixes `exact` only.
- `<channels>/axes.json` = {reach name: {..., 'removed_cells': [[r, c], ...], ...}}; cell (r, c) has the corner
  vertices (r, c), (r, c+1), (r+1, c), (r+1, c+1).
- Gates (tools/terrain/verify_terrain_v30.py, listed below; the receiver runs it with --sea-cut 0.51): every water
  vertex at least 0.10 m below its own level (600 m Narva zone excluded); every land vertex within 8.5 m of water at
  least 0.05 m above the level of the nearest water vertex (scipy edt nearest index over cls > 0); land >= 1.40 m except
  `beach` (>= 0.80 m); land triangles (three land corners) <= 35.01 degrees; in every cell with a plane
  (cell_planes(cls, level, sea_cut=0.51)), water corners <= plane - 0.02 and land corners >= plane, outside the 600 m
  Narva zone. The input already fails 6 water_depth (streams) and 31 pieces (28 water corners, 3 land corners): those
  vertices must not get worse, and need not be fixed.

# What to compute (exact method)
Parameters (argparse, defaults): --terrain PATH, --out DIR, --channels DIR (required unless --selftest), --slope 0.15,
--band 12, --sigma 12, --max-shift 4, --min-vertices 4, --max-raise 2.0 (land), --max-raise-water 6.0, --max-lower 1.5,
--bed-floor (default None: off), --bed-min-depth 0.30, --narva-radius 620, --sea-cut 0.51. Do not add other options.
Constants: FLOWING = (3, 5, 6); STANDING = (2, 7); depth_min 0.10, freeboard 0.05, piece_depth 0.02, land floor 1.40,
beach floor 0.80, plane cut 0.80 (from profile_lakes_v30.G where it has them); EPS = profile_lakes_v30.EPS (1e-4).
Factor the algorithm into `profile(t, nature, corridor, reach_vertices, a)` returning (out arrays dict, masks dict,
report dict without inputs), so main() and the self-test share it.
1. Load as profile_lakes_v30.py does (float64 copies h0, level0; cls0). x, z = grid_xz().
   flow0 = cls0 in FLOWING; land0 = cls0 == 0; low = flow0 & (level0 <= 0.80) (drawn by the engine sea).
   ids = scipy.ndimage.label(flow0 & ~low, structure=np.ones((3, 3))) -> components. A component with fewer than
   --min-vertices vertices is not profiled and counts as `other` below.
2. Per-vertex gate fields, computed ONCE on the whole grid from the input (they stay exact for the output because no
   class or level changes):
   planes = cell_planes(cls0, level0, sea_cut=a.sea_cut); pmin, pmax = vertex_plane_bounds(planes) (NaN where no plane).
   dist, idx = distance_transform_edt(cls0 == 0, sampling=6.0, return_indices=True); near_lv = level0[idx[0], idx[1]]
   (exactly as verify_terrain_v30.py lines 50-51).
   wcap (water vertices) = min(level0 - 0.10, pmin - 0.02) - EPS, ignoring the pmin term where it is NaN.
   lfloor (land vertices) = max(near_lv + 0.05, pmax, floor) + EPS, floor = 0.80 where `beach` else 1.40, ignoring the
   pmax term where it is NaN.
3. Fixed vertices (never changed by the shore profile):
   platform | reserve | nature | corridor (`exact`) | Narva zone (hypot(x - NARVA[0], z - NARVA[1]) <= --narva-radius)
   | map border (x < 12 or z < 12 or x > 12270 or z > 12270) | other | near_other | claimed twice,
   where other = sea (cls 1, 4) | standing (cls 2, 7) | low | reach_vertices | vertices of components below
   --min-vertices; near_other = every vertex within R = --band + --max-shift + 6 m of `other`
   (distance_transform_edt(~other) * 6 <= R); claims: every profiled component claims the vertices within R of it
   (dilate its mask by a disc of radius ceil(R / 6) vertices inside its window, accumulate a uint8 count), and every
   vertex with count >= 2 is fixed.
4. For each profiled component i, window = bounding box grown by g = ceil((R + 3 * sigma + 12) / 6) vertices, clipped:
   a. base, smooth, near, lines, sd and band exactly as profile_lakes_v30.py lines 142-156, with the component mask B.
      Skip (and count) a component without lines.
   b. Lw = level0 of the nearest vertex of B, for every window vertex (distance_transform_edt(~B, return_indices=True)
      inside the window): the local level for the profile target.
   c. edit = band & (B | land0) & ~fixed. Forced edges as profile_lakes_v30.py lines 159-171 (both ends in B | land0, sd
      of opposite sign; forced &= edit); for the offset metric record each crossing edge with the level Lw at its first
      end instead of a body level.
   d. want = Lw + slope * sd on forced vertices, h0 elsewhere. Side = INPUT CLASS: on vertices of B,
      want = min(want, wcap); on land vertices, want = max(want, lfloor). Then the move caps:
      want_c = clip(want, h0 - max_lower, h0 + raise_cap), raise_cap = max_raise_water on vertices of B and max_raise
      on land (a navigable edge vertex 3.5 m deep must reach its shallow target, or the crossing moves the wrong way);
      where want_c breaks its side's gate (water: want_c > wcap;
      land: want_c < lfloor), keep h0 (this also leaves the vertices that already fail a gate as they are).
      Count forced vertices at a cap and vertices kept by the gate.
   e. h1 = want on edit. cls and level never change.
5. Undo steepening as profile_lakes_v30.py lines 200-204: h2, faces = discard_steeper_land_faces(h1, h0, cls0), then the
   float32 round trip.
6. Bed floor (only with --bed-floor F): bedmask = vertices of profiled components with cls0 in (5, 6) (rivers and
   streams; navigable reaches keep their depth) & ~corridor & ~Narva zone & ~map border & ~reach_vertices
   & (level0 > 0.80). need = min(F, level0 - bed_min_depth, wcap). Raise h2 to need where h2 < need; float32 round trip.
   It never lowers anything and may act inside `fixed` (only there and nowhere else may a fixed vertex change).
7. Fail closed (assert): cls and level arrays identical to the input; no fixed vertex changed except bed raises; the
   gate counts of step 8 after <= before, each.
8. Gates, computed exactly as verify_terrain_v30.py computes them (water_depth outside the 600 m Narva zone, banks within
   8.5 m outside that zone, land_floor and beach_floor, pieces water and land corners with cell_planes(cls, level,
   sea_cut=a.sea_cut) outside the zone, slopes = land triangles over 35.01 degrees), each {"before": n, "after": n}.

# Report (<out>/report.json) and outputs
Write <out>/terrain_rivers.npz (np.savez_compressed, the same keys and dtypes as the input) and <out>/masks.npz (bool
arrays band, forced, editable, changed, bed_raised). report.json keys, plain JSON numbers/strings:
- status: "BUILT_PENDING_GATES_AND_ENGINE_VIEWS"; params: every argparse value except paths;
- components: {"labelled": n, "profiled": n, "skipped_small": n, "skipped_no_outline": n, "claimed_twice_vertices": n};
- vertices: {"band": n, "editable": n, "forced": n, "changed": n, "forced_at_move_cap": n, "kept_by_gate": n,
  "bed_raised": n, "face_recovery": <the dict discard_steeper_land_faces returns>};
- by_class: for k in 3, 5, 6 (class of the water end of the edge or of the vertex): {"forced": n, "changed": n,
  "bed_raised": n, "crossing_offset_m_vs_smoothed_outline": {"before": ..., "after": ...}}, where the offset of a
  recorded crossing edge is |t - t*| * edge length, t = terrain crossing of Lw along the edge, t* = outline crossing
  (as profile_lakes_v30.offsets, but with the per-edge level), reported as {"edges", "no_crossing", "p50", "p90",
  "p99"};
- gates: step 8; bed_below_0p85: for k in 3, 5, 6, {"before", "after"} counts of cls == k & level > 0.80 & h < 0.85;
- largest_components: the 10 largest profiled components: id, vertices, class counts {3, 5, 6}, level min and max,
  changed;
- change_m: {"raise_max", "lower_max"}; inputs: {path: sha(path)} for the terrain, NATURE, axes.json and this file;
  output_sha256 of terrain_rivers.npz; seconds; limits (two short strings).
Print the report without "inputs". OUTDIR must not exist: create it; fail if it exists.

# Self-test (--selftest, no other arguments)
Synthetic terrain in memory at full size N x N: land at 4.6 m (cls 0, level NaN, all masks False). Let cc(r) =
1000 + (r - 800) // 7.
- River (cls 5): rows 800..1100, columns cc(r) - 1 .. cc(r) + 1 (a 3-wide diagonal staircase); level 4.0 - 0.004 *
  (r - 800); bed = level - 0.6.
- Stream (cls 6): row 950, columns cc(950) + 2 .. cc(950) + 80; level 3.4 + 0.003 * (c - cc(950) - 2); bed = level -
  0.25.
- Lake (cls 2) touching the river mouth: rows 1101..1115, columns cc(1100) - 7 .. cc(1100) + 7; level 2.75; bed 2.0.
- Navigable (cls 3): rows 1300..1305, columns 900..1300, level 3.0, bed -0.5; its corridor mask: rows 1301..1304,
  columns 900..1300.
- Low reach (cls 3): rows 300..305, columns 300..400, level 0.7, bed 0.0.
Pass nature = all False, reach_vertices = all False. Assert:
- the synthetic input passes every gate of step 8 (all before == 0), and every gate after == 0;
- cls and level identical; corridor vertices unchanged; every vertex within R of the lake and of the low reach unchanged;
- crossing offset p90 after < before for classes 5 and 3;
- in a second call with bed floor 3.5: every class 5 and 6 water vertex is >= min(3.5, level - 0.30) - 1e-5, and the
  corridor vertices are still unchanged.
Print "SELFTEST PASS" and exit 0, or raise.

# Output format
Reply with exactly one fenced block preceded by the line `FILE: tools/terrain/profile_rivers_v30.py`, containing the
whole file (module docstring in the style of profile_lakes_v30.py: what, why, method, fixed, usage). No other files.
English identifiers and comments; comments sparse, in the tone of the reference file.

# Reference implementation and helpers (read them; import, do not copy)

### tools/terrain/profile_lakes_v30.py (lines 1-333)
```python
   1| """Lake and pond shores V30 on a smoothed outline, islands included, and the lake-bed floor (BALTIC-007, BALTIC-018).
   2| 
   3| The water of a standing body (lake or pond, census labelling) is a flat plane at its level L drawn by water pieces; its
   4| visible shore is where the native terrain (6 m grid, NW-SE diagonals) crosses that plane. The v3b fit kept wet vertices
   5| ~0.3 m under L and land ~0.4 m over it, so the crossing keeps a fixed fraction of every wet-land edge and shores and
   6| islands draw the 6 m grid (evidence/v30-v5-candidate-2026-10-05). profile_coast_v30.py fixed the same for the sea; this
   7| tool applies its method body by body, each with its own level, in a window around the body:
   8| 1. Outline: signed distance to the body (negative inside, islands included), Gaussian-smoothed (--sigma m) and clamped
   9|    so the zero line moves at most --max-shift; then the exact distance to its zero contour, signed by the smoothed field.
  10| 2. Profile: a vertex ending a native edge (east, south, NW-SE diagonal) whose ends lie on opposite sides of the outline
  11|    takes L + --slope * sd, within the gates of tools/terrain/verify_terrain_v30.py: water at most L - 0.10, land at
  12|    least L + 0.05 and the land floor (1.40 m, 0.80 m on the beach); each move capped (--max-raise, --max-lower); no
  13|    vertex between the two gates. Every other vertex keeps its height, except to meet those gates.
  14| 3. Classes and levels follow the heights inside the band: water of the body (its class, level L) below L, land above.
  15| 4. Edits that make a land face steeper than 35 degrees (or than it was) are undone, with their classes.
  16| 5. Bed floor (--bed-floor F): every water vertex of a profiled body outside the navigable corridors, the Narva zone and
  17|    the two-vertex map border rises to max(h, min(F, L - --bed-min-depth)). The engine draws its sea (0.65-0.85 m) under any lake whose bed lies
  18|    below it, and from the air the lake splits into bands (BALTIC-018, evidence/v30-bed-probe-2026-10-05). Navigable
  19|    reaches keep their depth (Guillermo, 05-10).
  20| Fixed for the shore profile: platforms, reserves, the nature envelope, the 24 m navigable and delta corridors (with their
  21| margin), the Narva zone and the map border (those vertices themselves); the sea, the delta, navigable reaches, rivers,
  22| streams and unlabelled standing water, each with every vertex within --band + --max-shift + 6 m of it; and every vertex
  23| within that reach of two bodies (contacts between water stay as they are). Land next to a platform or the border may
  24| be edited. Bodies at or below the 0.80 m pond-plane cut are drawn by the sea and not profiled.
  25| The changed 48 m water tiles are rebuilt afterwards with tools/water/patch_water_tiles_v30.py.
  26| Usage: profile_lakes_v30.py --terrain IN.npz --out OUTDIR [--slope 0.15] [--band 12] [--sigma 12] [--max-shift 4]
  27|                             [--min-vertices 4] [--bed-floor 1.0] [--bed-min-depth 0.30]
  28|        profile_lakes_v30.py --selftest
  29| """
  30| import argparse
  31| import json
  32| import sys
  33| import time
  34| from pathlib import Path
  35| 
  36| import contourpy
  37| import numpy as np
  38| import shapely
  39| from scipy import ndimage
  40| 
  41| sys.path.insert(0, str(Path(__file__).resolve().parent))
  42| from v30_common import N, cell_planes, grid_xz  # noqa: E402
  43| from finish_shores_v30 import discard_steeper_land_faces, protect_corridors  # noqa: E402
  44| from profile_coast_v30 import EDGES, NARVA, NATURE, SEA_CLASSES, sha, turning, zero_lines  # noqa: E402
  45| from relevel_bodies_v30 import label_bodies  # noqa: E402
  46| 
  47| FLOWING = (3, 5, 6)
  48| STANDING = (2, 7)
  49| G = dict(depth_min_m=0.10, freeboard_m=0.05, land_floor_m=1.40, beach_floor_m=0.80, plane_cut_m=0.80,
  50|          bank_radius_m=8.5, narva_zone_excluded_m=600.0)   # verify_terrain_v30.py G and its pieces rule
  51| EPS = 1e-4   # m, margin of a dead-zone snap over the float32 rounding of heights near L
  52| 
  53| 
  54| def window_lines(field, mask, r0, c0):
  55|     """Zero lines of a window whose first vertex is (r0, c0), restricted to mask, in game x and z."""
  56|     nr, nc = field.shape
  57|     z = np.ma.masked_invalid(np.where(mask, field, np.nan))
  58|     gen = contourpy.contour_generator(x=(c0 + np.arange(nc)) * 6.0, y=12282.0 - (r0 + np.arange(nr)) * 6.0, z=z,
  59|                                       line_type=contourpy.LineType.Separate)
  60|     return [ln for ln in gen.lines(0.0) if len(ln) >= 2]
  61| 
  62| 
  63| def offsets(h, edges):
  64|     """Distance (m) along each native edge crossing the smoothed outline between the terrain crossing of the body
  65|     level and the outline crossing; edges whose terrain no longer crosses the level are counted apart."""
  66|     if not edges:
  67|         return {'edges': 0}
  68|     ra, ca, rb, cb, tstar, length, lv = (np.concatenate(v) for v in zip(*edges))
  69|     ha, hb = h[ra, ca] - lv, h[rb, cb] - lv
  70|     ok = ha * hb < 0
  71|     t = np.where(ok, ha / np.where(ok, ha - hb, 1.0), np.nan)
  72|     v = (np.abs(t - tstar) * length)[ok]
  73|     return {'edges': int(ok.size), 'no_crossing': int((~ok).sum()),
  74|             **({k: round(float(np.percentile(v, q)), 3) for k, q in (('p50', 50), ('p90', 90), ('p99', 99))} if v.size else {})}
  75| 
  76| 
  77| def gates(h, cls, level, beach, narva600):
  78|     """Water depth, banks and land floor counts as verify_terrain_v30.py computes them."""
  79|     water = cls > 0
  80|     dist, idx = ndimage.distance_transform_edt(~water, sampling=6.0, return_indices=True)
  81|     near_lv = level[idx[0], idx[1]]
  82|     land = ~water
  83|     b = land & (dist <= G['bank_radius_m']) & ~narva600
  84|     with np.errstate(invalid='ignore'):
  85|         return {'water_depth': int((water & ~narva600 & (level - h < G['depth_min_m'])).sum()),
  86|                 'banks': int((b & (h < near_lv + G['freeboard_m'])).sum()),
  87|                 'land_floor': int((land & ~narva600 & ~beach & (h < G['land_floor_m'] - 1e-6)).sum()),
  88|                 'beach_floor': int((beach & (h < G['beach_floor_m'] - 1e-6)).sum())}
  89| 
  90| 
  91| def profile(t, nature, corridor, a):
  92|     """The whole method on the terrain arrays t; returns (output arrays, masks, report without inputs)."""
  93|     h0 = t['heights'].astype(np.float64)
  94|     cls0, level0 = t['cls'].copy(), t['level'].astype(np.float64)
  95|     x, z = grid_xz()
  96|     sea0, flow0, land0 = np.isin(cls0, SEA_CLASSES), np.isin(cls0, FLOWING), cls0 == 0
  97|     ids = label_bodies(cls0, level0)
  98|     loose = np.isin(cls0, STANDING) & (ids == 0)
  99|     narva = np.hypot(x - NARVA[0], z - NARVA[1]) <= a.narva_radius
 100|     narva600 = np.hypot(x - NARVA[0], z - NARVA[1]) <= G['narva_zone_excluded_m']
 101|     border = (x < 12) | (z < 12) | (x > 12270) | (z > 12270)
 102|     reach = a.band + a.max_shift + 6.0
 103|     rv = int(np.ceil(reach / 6.0))
 104|     yy, xx = np.mgrid[-rv:rv + 1, -rv:rv + 1]
 105|     disc = np.hypot(yy, xx) * 6.0 <= reach
 106|     objs = ndimage.find_objects(ids)
 107|     claims = np.zeros((N, N), np.uint8)
 108|     for i, sl in enumerate(objs, 1):
 109|         if sl is None:
 110|             continue
 111|         r0, r1 = max(sl[0].start - rv, 0), min(sl[0].stop + rv, N)
 112|         c0, c1 = max(sl[1].start - rv, 0), min(sl[1].stop + rv, N)
 113|         claims[r0:r1, c0:c1] += ndimage.binary_dilation(ids[r0:r1, c0:c1] == i, structure=disc).astype(np.uint8)
 114|     other = sea0 | flow0 | loose
 115|     near_other = ndimage.distance_transform_edt(~other) * 6.0 <= reach if other.any() else np.zeros((N, N), bool)
 116|     fixed = (t['platform'] | t['reserve'] | nature | corridor | narva | border | other | near_other | (claims >= 2))
 117| 
 118|     h1, cls1, level1, ids1 = h0.copy(), cls0.copy(), level0.copy(), ids.copy()
 119|     masks = {k: np.zeros((N, N), bool) for k in ('band', 'forced', 'editable')}
 120|     counts = dict(profiled=0, skipped_small=0, skipped_low=0, skipped_no_outline=0, capped=0)
 121|     profiled = np.zeros(len(objs) + 1, bool)
 122|     level_of = np.full(len(objs) + 1, np.nan)
 123|     rows, edges = [], []
 124|     g = int(np.ceil((reach + 3 * a.sigma + 12.0) / 6.0))
 125|     for i, sl in enumerate(objs, 1):
 126|         if sl is None:
 127|             continue
 128|         r0, r1 = max(sl[0].start - g, 0), min(sl[0].stop + g, N)
 129|         c0, c1 = max(sl[1].start - g, 0), min(sl[1].stop + g, N)
 130|         W = (slice(r0, r1), slice(c0, c1))
 131|         B = ids[W] == i
 132|         nb = int(B.sum())
 133|         L = float(np.median(level0[W][B]))
 134|         level_of[i] = L
 135|         if nb < a.min_vertices:
 136|             counts['skipped_small'] += 1
 137|             continue
 138|         if L <= G['plane_cut_m']:
 139|             counts['skipped_low'] += 1
 140|             continue
 141|         k = int(np.bincount(cls0[W][B]).argmax())
 142|         base = np.where(B, -ndimage.distance_transform_edt(B), ndimage.distance_transform_edt(~B)) * 6.0
 143|         smooth = ndimage.gaussian_filter(base, a.sigma / 6.0)
 144|         smooth = np.clip(smooth, base - a.max_shift, base + a.max_shift)
 145|         near = np.abs(base) <= a.band + a.max_shift + 9.0
 146|         lines = window_lines(smooth, near, r0, c0)
 147|         if not lines:
 148|             counts['skipped_no_outline'] += 1
 149|             continue
 150|         segs = np.concatenate([np.stack([ln[:-1], ln[1:]], axis=1) for ln in lines])
 151|         tree = shapely.STRtree(shapely.linestrings(segs))
 152|         xw, zw = x[W], z[W]
 153|         _, dist = tree.query_nearest(shapely.points(xw[near], zw[near]), return_distance=True, all_matches=False)
 154|         sd = np.full(B.shape, np.nan)
 155|         sd[near] = np.where(smooth[near] < 0, -dist, dist)
 156|         band = near & np.isfinite(sd) & (np.abs(sd) <= a.band)
 157|         lw = land0[W]
 158|         edit = band & (B | lw) & ~fixed[W]
 159|         ends = B | lw
 160|         nr, nc = B.shape
 161|         forced = np.zeros(B.shape, bool)
 162|         for dr, dc in EDGES:
 163|             sa, sb = sd[:nr - dr, :nc - dc], sd[dr:, dc:]
 164|             with np.errstate(invalid='ignore'):
 165|                 cross = (np.isfinite(sa) & np.isfinite(sb) & (sa * sb < 0) & ends[:nr - dr, :nc - dc] & ends[dr:, dc:])
 166|             forced[:nr - dr, :nc - dc] |= cross
 167|             forced[dr:, dc:] |= cross
 168|             ra, ca = np.nonzero(cross)
 169|             edges.append((ra + r0, ca + c0, ra + r0 + dr, ca + c0 + dc, np.abs(sa[cross]) / (np.abs(sa[cross]) + np.abs(sb[cross])),
 170|                           np.full(ra.size, 6.0 * (2 ** 0.5 if dr and dc else 1.0)), np.full(ra.size, L)))
 171|         forced &= edit
 172|         hw = h0[W]
 173|         want = np.where(forced, L + a.slope * np.nan_to_num(sd), hw)
 174|         land_side = np.nan_to_num(sd) >= 0
 175|         floor = np.where(t['beach'][W], G['beach_floor_m'], G['land_floor_m'])
 176|         want = np.where(land_side, np.maximum(np.maximum(want, L + G['freeboard_m']), floor),
 177|                         np.minimum(want, L - G['depth_min_m']))
 178|         counts['capped'] += int((edit & ((want > hw + a.max_raise) | (want < hw - a.max_lower))).sum())
 179|         want = np.clip(want, hw - a.max_lower, hw + a.max_raise)
 180|         # an input that already breaks a gate can still end between the two: snap with a margin that survives float32,
 181|         # and keep the move caps (such a vertex then stays on its old side)
 182|         dead = (want > L - G['depth_min_m']) & (want < L + G['freeboard_m'])
 183|         want = np.where(dead, np.where(want >= L, L + G['freeboard_m'] + EPS, L - G['depth_min_m'] - EPS), want)
 184|         want = np.where(dead, np.clip(want, hw - a.max_lower, hw + a.max_raise), want)
 185|         hv, cv, lv, iv = h1[W], cls1[W], level1[W], ids1[W]
 186|         hv[edit] = want[edit]
 187|         to_water = edit & lw & (want < L)
 188|         to_land = edit & B & (want >= L)
 189|         cv[to_water], lv[to_water], iv[to_water] = k, L, i
 190|         cv[to_land], lv[to_land], iv[to_land] = 0, np.nan, 0
 191|         masks['band'][W] |= band
 192|         masks['forced'][W] |= forced
 193|         masks['editable'][W] |= edit
 194|         profiled[i] = True
 195|         counts['profiled'] += 1
 196|         rows.append(dict(id=i, level_m=round(L, 3), cls=k, vertices=nb, forced=int(forced.sum()),
 197|                          changed=int((edit & (want != hw)).sum()), to_water=int(to_water.sum()),
 198|                          to_land=int(to_land.sum())))
 199| 
 200|     # undo steepened land faces; reverted vertices get their classes back
 201|     h2, faces = discard_steeper_land_faces(h1, h0, cls1)
 202|     reverted = (h2 != h1.astype('float32').astype(float)) & (h2 == h0.astype('float32').astype(float))
 203|     cls1[reverted], level1[reverted], ids1[reverted] = cls0[reverted], level0[reverted], ids[reverted]
 204|     h2 = h2.astype('float32').astype(np.float64)
 205| 
 206|     # bed floor on the profiled bodies, navigable corridors, the Narva zone and the map border excepted: beyond the
 207|     # border the engine continues the terrain from its edge, and a lake bed raised there above the sea drew a flat
 208|     # untextured surface outside the map (v7 run 06e14fcf, lake 202); with the edge kept deep the sea continues the lake
 209|     bed = np.zeros((N, N), bool)
 210|     if a.bed_floor is not None:
 211|         body = profiled[ids1] & (ids1 > 0) & np.isin(cls1, STANDING) & ~corridor & ~narva & ~border
 212|         with np.errstate(invalid='ignore'):
 213|             need = np.minimum(a.bed_floor, level1 - a.bed_min_depth)
 214|             bed = body & (h2 < need)
 215|         h2[bed] = need[bed]
 216|         h2 = h2.astype('float32').astype(np.float64)
 217|     beach1 = (t['beach'] | ((cls1 == 0) & (h2 < G['land_floor_m'] - 1e-6))) & (cls1 == 0) & ~narva
 218|     changed = h2 != h0.astype('float32').astype(np.float64)
 219|     assert not np.any(changed & fixed & ~bed), 'protected height changed'
 220|     assert not np.any((cls1 != cls0) & fixed), 'protected class changed'
 221| 
 222|     # waterline turn of the profiled bodies inside their bands: zero lines of h - L, L of the nearest body water
 223|     above = profiled[ids] & (ids > 0)
 224|     _, j = ndimage.distance_transform_edt(~above, return_indices=True)
 225|     lev_near = np.where(above, level0, np.nan)[j[0], j[1]]
 226|     zone = masks['band']
 227|     out = dict(t)
 228|     out['heights'] = h2.astype(t['heights'].dtype)
 229|     out['cls'] = cls1
 230|     out['level'] = level1.astype(t['level'].dtype)
 231|     out['water'] = cls1 > 0
 232|     out['beach'] = beach1
 233|     rows.sort(key=lambda r: -r['vertices'])
 234|     d = h2 - h0
 235|     rep = {
 236|         'bodies': {'labelled': int(sum(1 for s in objs if s is not None)), 'profiled': counts['profiled'],
 237|                    'skipped_small': counts['skipped_small'], 'skipped_at_or_below_plane_cut': counts['skipped_low'],
 238|                    'skipped_no_outline': counts['skipped_no_outline'],
 239|                    'claimed_twice_vertices': int((claims >= 2).sum())},
 240|         'vertices': {'band': int(masks['band'].sum()), 'editable': int(masks['editable'].sum()),
 241|                      'forced': int(masks['forced'].sum()), 'changed': int(changed.sum()),
 242|                      'to_water': int(((cls0 == 0) & (cls1 != 0)).sum()), 'to_land': int(((cls0 != 0) & (cls1 == 0)).sum()),
 243|                      'forced_at_move_cap': counts['capped'], 'bed_raised': int(bed.sum()), 'face_recovery': faces},
 244|         'crossing_offset_m_vs_smoothed_outline': {'before': offsets(h0, edges), 'after': offsets(h2, edges)},
 245|         'waterline_turn_deg_per_12m': {'before': turning(zero_lines(h0 - lev_near, zone)),
 246|                                        'after': turning(zero_lines(h2 - lev_near, zone)),
 247|                                        'note': 'turn per 12 m grows where a staircase becomes a curve; read the '
 248|                                                'crossing offsets for the fit to the outline'},
 249|         'gates': {'before': gates(h0, cls0, level0, t['beach'], narva600),
 250|                   'after': gates(h2, cls1, level1, beach1, narva600)},
 251|         'standing_bed_below_0p85': {'before': int((np.isin(cls0, STANDING) & (level0 > G['plane_cut_m']) & (h0 < 0.85)).sum()),
 252|                                     'after': int((np.isin(cls1, STANDING) & (level1 > G['plane_cut_m']) & (h2 < 0.85)).sum())},
 253|         'largest_bodies': rows[:10],
 254|         'change_m': {'raise_max': round(float(d.max()), 3), 'lower_max': round(float(-d.min()), 3)}}
 255|     return out, dict(masks, changed=changed, bed_raised=bed), rep
 256| 
 257| 
 258| def selftest():
 259|     n = N
 260|     h = np.full((n, n), 3.0, np.float32)
 261|     cls = np.zeros((n, n), np.uint8)
 262|     level = np.full((n, n), np.nan, np.float32)
 263|     r, c = np.mgrid[0:n, 0:n]
 264|     lake_a = (np.maximum(abs(r - 1000), abs(c - 1000)) <= 40) & (abs(r - 1000) + abs(c - 1000) <= 60)
 265|     island = np.maximum(abs(r - 1005), abs(c - 997)) <= 6
 266|     lake_a &= ~island
 267|     lake_b = np.maximum(abs(r - 1000), abs(c - 1120)) <= 8
 268|     river = (c == 1300) & (r >= 900) & (r <= 1100)
 269|     for m, k, lv, bed in ((lake_a, 2, 2.0, 1.0), (lake_b, 2, 2.5, 1.5), (river, 5, 2.2, 1.9)):
 270|         cls[m], level[m], h[m] = k, lv, bed
 271|     zero = np.zeros((n, n), bool)
 272|     t = dict(heights=h, cls=cls, level=level, platform=zero, reserve=zero, narva=zero, water=cls > 0, beach=zero)
 273|     a = argparse.Namespace(slope=0.15, band=12.0, sigma=12.0, max_shift=4.0, min_vertices=4, max_raise=2.0,
 274|                            max_lower=1.5, bed_floor=None, bed_min_depth=0.30, narva_radius=620.0)
 275|     out, masks, rep = profile(t, zero, zero, a)
 276|     print(json.dumps({k: rep[k] for k in ('bodies', 'vertices', 'crossing_offset_m_vs_smoothed_outline', 'gates')}, indent=1))
 277|     assert all(v == 0 for v in rep['gates']['after'].values()), rep['gates']
 278|     near = ndimage.distance_transform_edt(~(lake_a | lake_b)) * 6.0 <= 22.0
 279|     assert not np.any(masks['changed'] & ~near), 'change far from the lakes'
 280|     keep = ndimage.distance_transform_edt(~river) * 6.0 <= 22.0
 281|     assert np.array_equal(out['heights'][keep], h[keep]) and np.array_equal(out['cls'][keep], cls[keep]), 'river touched'
 282|     ob, oa = rep['crossing_offset_m_vs_smoothed_outline']['before'], rep['crossing_offset_m_vs_smoothed_outline']['after']
 283|     assert oa['p90'] < ob['p90'] and oa['no_crossing'] == 0, (ob, oa)
 284|     assert np.any((out['cls'] == 0) & (np.maximum(abs(r - 1005), abs(c - 997)) <= 6)), 'island lost'
 285|     a.bed_floor = 1.5
 286|     out2, _, _ = profile(t, zero, zero, a)
 287|     wa = (out2['cls'] == 2) & (np.abs(out2['level'] - 2.0) < 1e-6)
 288|     assert wa.any() and out2['heights'][wa].min() >= 1.5 - 1e-6, out2['heights'][wa].min()
 289|     print('SELFTEST PASS')
 290| 
 291| 
 292| def main():
 293|     if '--selftest' in sys.argv:
 294|         selftest()
 295|         return
 296|     ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
 297|     ap.add_argument('--terrain', type=Path, required=True)
 298|     ap.add_argument('--out', type=Path, required=True)
 299|     ap.add_argument('--slope', type=float, default=0.15)
 300|     ap.add_argument('--band', type=float, default=12.0)
 301|     ap.add_argument('--sigma', type=float, default=12.0)
 302|     ap.add_argument('--max-shift', type=float, default=4.0)
 303|     ap.add_argument('--min-vertices', type=int, default=4)
 304|     ap.add_argument('--max-raise', type=float, default=2.0)
 305|     ap.add_argument('--max-lower', type=float, default=1.5)
 306|     ap.add_argument('--bed-floor', type=float, default=None)
 307|     ap.add_argument('--bed-min-depth', type=float, default=0.30)
 308|     ap.add_argument('--narva-radius', type=float, default=620.0)
 309|     a = ap.parse_args()
 310|     assert not a.out.exists(), 'fresh output required'
 311|     t0 = time.time()
 312|     t = dict(np.load(a.terrain))
 313|     planes = cell_planes(t['cls'], t['level'])
 314|     _, corridor, entries, _ = protect_corridors(planes)
 315|     nature = np.load(NATURE)['reserve'].astype(bool)
 316|     out, masks, rep = profile(t, nature, corridor, a)
 317|     a.out.mkdir(parents=True)
 318|     np.savez_compressed(a.out / 'terrain_lakes.npz', **out)
 319|     np.savez_compressed(a.out / 'masks.npz', **masks)
 320|     rep = {'status': 'BUILT_PENDING_GATES_AND_ENGINE_VIEWS',
 321|            'params': {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(a).items() if k not in ('terrain', 'out')},
 322|            **rep, 'protected_corridors': len(entries),
 323|            'inputs': {str(p): sha(p) for p in (a.terrain, NATURE, Path(__file__))},
 324|            'output_sha256': sha(a.out / 'terrain_lakes.npz'), 'seconds': round(time.time() - t0, 1),
 325|            'limits': ['Standing bodies above the 0.80 m plane cut; contacts, flowing water and the sea untouched.',
 326|                       'Water tiles must be patched for the changed cells; gates and engine views decide acceptance.']}
 327|     (a.out / 'report.json').write_text(json.dumps(rep, indent=1) + '\n', encoding='utf-8')
 328|     print(json.dumps({k: v for k, v in rep.items() if k != 'inputs'}, indent=1))
 329| 
 330| 
 331| if __name__ == '__main__':
 332|     main()
 333| 
```

### tools/terrain/profile_coast_v30.py (lines 36-93)
```python
  36| import numpy as np
  37| import shapely
  38| from scipy import ndimage
  39| 
  40| ROOT = Path(__file__).resolve().parents[2]
  41| sys.path.insert(0, str(ROOT / 'tools' / 'terrain'))
  42| from v30_common import N, POND_CLASSES, R, cell_planes, grid_xz, vertex_plane_bounds  # noqa: E402
  43| from finish_shores_v30 import discard_steeper_land_faces, protect_corridors  # noqa: E402
  44| 
  45| WATER = Path(R) / 'tests/terrain_v30/water_v30.npz'
  46| NATURE = Path(R) / 'tests/regional_outline_v1/reference.npz'
  47| SEA_CLASSES = (1, 4)
  48| EDGES = ((0, 1), (1, 0), (1, 1))
  49| NARVA = (2417.1428225906, 6889.8850822322)
  50| GATES = dict(depth_min_m=0.10, land_floor_m=1.40, beach_floor_m=0.80, narva_radius_m=480.0)   # verify_terrain_v30.py:30
  51| 
  52| 
  53| def sha(path):
  54|     return hashlib.sha256(Path(path).read_bytes()).hexdigest()
  55| 
  56| 
  57| def zero_lines(field, mask=None):
  58|     z = np.ma.masked_invalid(np.where(mask, field, np.nan)) if mask is not None else np.ma.masked_invalid(field)
  59|     gen = contourpy.contour_generator(x=np.arange(N) * 6.0, y=12282.0 - np.arange(N) * 6.0, z=z,
  60|                                       line_type=contourpy.LineType.Separate)
  61|     return [ln for ln in gen.lines(0.0) if len(ln) >= 3]
  62| 
  63| 
  64| def turning(lines, scale=12.0):
  65|     vals = []
  66|     for ln in lines:
  67|         s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(ln, axis=0), axis=1))]
  68|         if s[-1] < 4 * scale:
  69|             continue
  70|         q = np.arange(0, s[-1], scale)
  71|         p = np.column_stack([np.interp(q, s, ln[:, 0]), np.interp(q, s, ln[:, 1])])
  72|         a = np.degrees(np.arctan2(*np.diff(p, axis=0).T[::-1]))
  73|         vals.append(np.abs((np.diff(a) + 180) % 360 - 180))
  74|     v = np.concatenate(vals) if vals else np.array([np.nan])
  75|     return {'n': int(v.size), 'p50': round(float(np.nanpercentile(v, 50)), 1), 'p90': round(float(np.nanpercentile(v, 90)), 1),
  76|             'p95': round(float(np.nanpercentile(v, 95)), 1)}
  77| 
  78| 
  79| def crossing_offsets(h, sd, level, edges):
  80|     """Distance (m) between the terrain crossing of the sea level and the outline crossing, per crossing edge."""
  81|     out, nocross = [], 0
  82|     for (ra, ca, rb, cb, length) in edges:
  83|         sa, sb = sd[ra, ca], sd[rb, cb]
  84|         tstar = sa / (sa - sb)
  85|         ha, hb = h[ra, ca] - level, h[rb, cb] - level
  86|         ok = ha * hb < 0
  87|         t = np.where(ok, ha / np.where(ok, ha - hb, 1.0), np.nan)
  88|         nocross += int((~ok).sum())
  89|         out.append(np.abs(t - tstar)[ok] * length)
  90|     v = np.concatenate(out) if out else np.array([])
  91|     return {'edges': int(v.size + nocross), 'no_crossing': nocross,
  92|             **({k: round(float(np.percentile(v, q)), 3) for k, q in (('p50', 50), ('p90', 90), ('p99', 99))} if v.size else {})}
  93| 
```

### tools/terrain/v30_common.py (lines 1-112)
```python
   1| """Shared helpers for terrain V30: native triangle sampling, vertex rasterisation and the road network graph.
   2| 
   3| Vertex grid: col c, row r -> x = 6c, z = 12282 - 6r (row 0 north). Each 6 m cell is split along its NW-SE diagonal,
   4| as Terrain Builder's native grid (contract recorded in HANDOFF-history.md, "Contrato nativo LOCAL").
   5| """
   6| import json
   7| import os
   8| 
   9| import numpy as np
  10| from affine import Affine
  11| from rasterio.features import rasterize
  12| from shapely.geometry import shape
  13| 
  14| R = r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev"
  15| N = 2048
  16| VERTEX = Affine(6, 0, -3, 0, -6, 12285)  # one pixel per vertex, game coordinates
  17| 
  18| 
  19| def tri_sample(h, xs, zs):
  20|     """Height on the native triangulated surface (NW-SE diagonal) at game coordinates."""
  21|     c = np.clip(np.asarray(xs, dtype=float) / 6.0, 0, N - 1.000001)
  22|     r = np.clip((12282 - np.asarray(zs, dtype=float)) / 6.0, 0, N - 1.000001)
  23|     c0, r0 = np.floor(c).astype(int), np.floor(r).astype(int)
  24|     fc, fr = c - c0, r - r0
  25|     nw, ne = h[r0, c0], h[r0, c0 + 1]
  26|     sw, se = h[r0 + 1, c0], h[r0 + 1, c0 + 1]
  27|     upper = nw + fc * (ne - nw) + fr * (se - ne)
  28|     lower = nw + fr * (sw - nw) + fc * (se - sw)
  29|     return np.where(fc >= fr, upper, lower)
  30| 
  31| 
  32| def raster_vertices(geoms, all_touched=False, values=None, dtype="uint8"):
  33|     pairs = [(g, 1 if values is None else v) for g, v in zip(geoms, values if values is not None else [None] * len(geoms)) if not g.is_empty]
  34|     if not pairs:
  35|         return np.zeros((N, N), dtype=dtype)
  36|     return rasterize(pairs, out_shape=(N, N), transform=VERTEX, dtype=dtype, all_touched=all_touched)
  37| 
  38| 
  39| def grid_xz():
  40|     c, r = np.meshgrid(np.arange(N), np.arange(N))
  41|     return c * 6.0, 12282 - r * 6.0
  42| 
  43| 
  44| def road_network():
  45|     """V29 graded road network (union of shortest routes between 11 anchors): list of (LineString, properties)."""
  46|     fc = json.load(open(os.path.join(R, "evidence", "regional-foundation-v1", "road-network-game.json"), encoding="utf-8"))
  47|     return [(shape(f["geometry"]), f["properties"]) for f in fc["features"]]
  48| 
  49| 
  50| def road_graph(step=3.0):
  51|     """Densified graph of the road network: points (n,2), edges (m,2) with lengths; endpoints merged by OSM node id."""
  52|     pts, edges, key_index = [], [], {}
  53| 
  54|     def node(key, xy):
  55|         if key is not None and key in key_index:
  56|             return key_index[key]
  57|         pts.append(xy)
  58|         idx = len(pts) - 1
  59|         if key is not None:
  60|             key_index[key] = idx
  61|         return idx
  62| 
  63|     for line, prop in road_network():
  64|         coords = np.asarray(line.coords)[:, :2]
  65|         if len(coords) < 2 or line.length <= 0:
  66|             continue
  67|         n = max(1, int(np.ceil(line.length / step)))
  68|         d = np.linspace(0, line.length, n + 1)
  69|         xy = np.array([line.interpolate(v).coords[0][:2] for v in d])
  70|         a = node(("osm", prop.get("node_a")) if prop.get("node_a") is not None else None, tuple(xy[0]))
  71|         prev = a
  72|         for k in range(1, n):
  73|             cur = node(None, tuple(xy[k]))
  74|             edges.append((prev, cur))
  75|             prev = cur
  76|         b = node(("osm", prop.get("node_b")) if prop.get("node_b") is not None else None, tuple(xy[-1]))
  77|         edges.append((prev, b))
  78|     pts = np.asarray(pts, dtype=float)
  79|     edges = np.asarray(edges, dtype=int)
  80|     lengths = np.hypot(*(pts[edges[:, 0]] - pts[edges[:, 1]]).T)
  81|     keep = lengths > 1e-6
  82|     return pts, edges[keep], lengths[keep]
  83| 
  84| 
  85| POND_CLASSES = (2, 3, 5, 6, 7)
  86| 
  87| 
  88| def cell_planes(cls, level, band=0.025, sea_cut=0.80):
  89|     """Plane of every 6 m cell covered by a pond piece: the band of the mean level of its water corners (lakes,
  90|     navigable, rivers, streams, ponds above the sea). NaN where the cell has no such corner. Pieces, builder and
  91|     surface all use this rule. cell (i, j) lies between vertex rows i, i+1 and columns j, j+1."""
  92|     # Production pieces and surfaces use float64. Without normalization,
  93|     # float32(0.8) compares differently against 0.8 after promotion: consumers
  94|     # omitted 467 existing pond cells merely by retaining the stored dtype.
  95|     level = np.asarray(level, dtype=np.float64)
  96|     wet = np.isin(cls, POND_CLASSES) & (np.nan_to_num(level, nan=-1.0) > sea_cut)
  97|     lv = np.where(wet, level, 0.0)
  98|     total = np.zeros((N - 1, N - 1))
  99|     count = np.zeros((N - 1, N - 1))
 100|     for dr in (0, 1):
 101|         for dc in (0, 1):
 102|             total += lv[dr:dr + N - 1, dc:dc + N - 1]
 103|             count += wet[dr:dr + N - 1, dc:dc + N - 1]
 104|     return np.where(count > 0, np.rint(total / np.maximum(count, 1) / band) * band, np.nan)
 105| 
 106| 
 107| def vertex_plane_bounds(plane):
 108|     """Lowest and highest plane among the up to four cells around each vertex (NaN where none is covered)."""
 109|     p = np.pad(plane, 1, constant_values=np.nan)
 110|     stack = np.stack([p[0:N, 0:N], p[0:N, 1:N + 1], p[1:N + 1, 0:N], p[1:N + 1, 1:N + 1]])
 111|     with np.errstate(all="ignore"):
 112|         return np.nanmin(stack, axis=0), np.nanmax(stack, axis=0)
```

### tools/terrain/finish_shores_v30.py (lines 29-111)
```python
  29| def ease(v):
  30|     t = np.clip(v, 0, 1)
  31|     return t*t*t*(10+t*(-15+6*t))
  32| 
  33| 
  34| def protect_corridors(planes):
  35|     fixed = np.zeros((2048, 2048), bool)
  36|     sources = [ROOT/'evidence/v30-offline-followup-2026-10-02/corridors.geojson',
  37|                ROOT/'evidence/v30-delta-fairways-2026-10-02/axes-corridors.geojson']
  38|     entries = []
  39|     for path in sources:
  40|         for f in json.loads(path.read_text())['features']:
  41|             if f['properties'].get('kind', 'corridor24m') != 'corridor24m':
  42|                 continue
  43|             rec = records(shape(f['geometry']), planes)
  44|             ids = np.unique(rec['ids'])
  45|             fixed.ravel()[ids] = True
  46|             entries.append(dict(name=f['properties'].get('name', f['properties'].get('river')),
  47|                                 face_vertices=len(ids)))
  48|     if len(entries) < 20:
  49|         raise ValueError('Incomplete main and delta channel protection')
  50|     # A vertex margin prevents the bank shoulder from starting on the last
  51|     # certified face. Exact main/delta protected faces are also saved separately.
  52|     return fixed, binary_dilation(fixed), entries, sources
  53| 
  54| 
  55| def recover_dry_gradients(h, original, dry):
  56|     """Cancel excessive dry-bank lowering at a fixed neighbour, never raise
  57|     land above original or touch water. Existing per-edge differences larger
  58|     than 2.88 are retained as ceilings, not newly imposed on an old surface.
  59|     Geometry is assessed independently on both native triangle halves later.
  60|     """
  61|     cx = np.maximum(PARAMS['axis_cap_m'], np.abs(np.diff(original, axis=1)))
  62|     cy = np.maximum(PARAMS['axis_cap_m'], np.abs(np.diff(original, axis=0)))
  63|     dx, dy = dry[:, :-1] & dry[:, 1:], dry[:-1, :] & dry[1:, :]
  64|     for iteration in range(PARAMS['iterations_max']):
  65|         nh = h.copy()
  66|         nh[:, 1:] = np.maximum(nh[:, 1:], np.where(dx, h[:, :-1]-cx, -np.inf))
  67|         nh[:, :-1] = np.maximum(nh[:, :-1], np.where(dx, h[:, 1:]-cx, -np.inf))
  68|         nh[1:, :] = np.maximum(nh[1:, :], np.where(dy, h[:-1, :]-cy, -np.inf))
  69|         nh[:-1, :] = np.maximum(nh[:-1, :], np.where(dy, h[1:, :]-cy, -np.inf))
  70|         if np.any(nh[dry] > original[dry]+1e-7):
  71|             raise ValueError('Dry recovery cannot increase the source')
  72|         delta = float(np.max(np.abs(nh-h)))
  73|         h = nh
  74|         if delta < 1e-6:
  75|             return h, iteration+1
  76|     raise ValueError('Dry recovery did not converge within the declared budget')
  77| 
  78| 
  79| def discard_steeper_land_faces(proposal, original, cls):
  80|     """Keep useful edits, but cancel an edit if it creates/worsens a >35 deg
  81|     native face touching land. Reverting one face can affect its neighbours,
  82|     so propagate until stable. Reversion only restores original vertices;
  83|     it cannot lower a dry floor or make a wet vertex shallower.
  84|     """
  85|     n = original.shape[0]
  86|     row, col = np.indices((n-1, n-1))
  87|     limits = []
  88|     for offsets in [((0,0),(0,1),(1,1)), ((0,0),(1,0),(1,1))]:
  89|         ids = [(row+dr)*n+col+dc for dr,dc in offsets]
  90|         a,b,c = [original.ravel()[ix] for ix in ids]
  91|         angle = np.degrees(np.arctan(np.hypot(b-a,c-b)/6.))
  92|         land = np.logical_or.reduce([cls.ravel()[ix]==0 for ix in ids])
  93|         limits.append((ids, np.maximum(angle, 35.) + 1e-4, land))
  94|     h = proposal.astype('float32').astype(float)
  95|     reverted = np.zeros_like(cls, dtype=bool)
  96|     for iteration in range(PARAMS['iterations_max']):
  97|         undo = np.zeros_like(cls, dtype=bool)
  98|         for ids, ceiling, land in limits:
  99|             a,b,c = [h.ravel()[ix] for ix in ids]
 100|             angle = np.degrees(np.arctan(np.hypot(b-a,c-b)/6.))
 101|             bad = land & (angle > ceiling)
 102|             for ix in ids:
 103|                 undo.ravel()[ix[bad]] = True
 104|         undo &= h != original
 105|         if not undo.any():
 106|             return h, dict(iterations=iteration+1, reverted_vertices=int(reverted.sum()))
 107|         h[undo] = original[undo]
 108|         reverted |= undo
 109|     raise ValueError('Face recovery did not converge within the declared budget')
 110| 
 111| 
```

### tools/terrain/verify_terrain_v30.py (lines 1-111)
```python
   1| """Offline gates for terrain V30 other than roads (roads: verify_roads_v30.py).
   2| 
   3| water_depth  every water vertex at least 0.10 m below its level (sea 0.75 m), Narva zone excluded (V29 exact)
   4| banks        every land vertex within 8.5 m of water at least 0.05 m above the nearest water level (shores are
   5|              slopes from the smooth outline; the plane edge must still lie under land)
   6| land_floor   every land vertex >= 1.40 m (the sea, 0.5-1.0 m with tide, never floods land), except the beach strip
   7|              along the smoothed coast (terrain mask 'beach'), which must stay >= 0.80 m
   8| slopes       land triangles (all three corners land) <= 35 degrees (+0.01 for float32: V29 itself is capped at
   9|              35.000x in the Narva zone); triangles touching water reported, not gated
  10| bed_floor    no vertex below -12.0 m, V29's deepest sea floor (a bed is cut, never dug as a pit)
  11| pieces       every cell a pond piece covers (v30_common.cell_planes): water corners >= 0.02 m under the plane, land
  12|              corners >= 0.00 m over it, outside the 600 m Narva zone
  13| narva        heights within 480 m of the bridge centre identical to V29 (ASC ed6cdaa5)
  14| Usage: verify_terrain_v30.py <terrain.npz> [--json out.json] [--sea-cut 0.80]  (pond planes above the sea cut)
  15| """
  16| import json
  17| import hashlib
  18| import os
  19| import sys
  20| from pathlib import Path
  21| 
  22| import numpy as np
  23| import rasterio
  24| from scipy.ndimage import distance_transform_edt
  25| 
  26| sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
  27| from v30_common import cell_planes  # noqa: E402
  28| 
  29| R = r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev"
  30| NARVA = (2417.1428225906, 6889.8850822322)
  31| G = {"depth_min_m": 0.10, "bank_radius_m": 8.5, "bank_min_m": 0.05, "land_floor_m": 1.40, "beach_floor_m": 0.80, "slope_max_deg": 35.0, "slope_tol_deg": 0.01, "bed_floor_m": -12.0,
  32|      "narva_radius_m": 480.0, "narva_zone_excluded_m": 600.0}
  33| 
  34| 
  35| def main():
  36|     t = np.load(sys.argv[1])
  37|     h = t["heights"].astype(float)
  38|     cls, level = t["cls"], t["level"].astype(float)
  39|     water = cls > 0
  40|     n = h.shape[0]
  41|     c, r = np.meshgrid(np.arange(n), np.arange(n))
  42|     dn = np.hypot(c * 6.0 - NARVA[0], 12282 - r * 6.0 - NARVA[1])
  43|     out = {}
  44|     zone = dn <= G["narva_zone_excluded_m"]
  45|     m = water & ~zone
  46|     depth = level[m] - h[m]
  47|     out["water_depth"] = {"vertices": int(m.sum()), "fail": int((depth < G["depth_min_m"]).sum()),
  48|                           "min_m": round(float(depth.min()), 3),
  49|                           "by_class_fail": {int(k): int(((level - h) < G["depth_min_m"])[m & (cls == k)].sum()) for k in range(1, 8)}}
  50|     dist, idx = distance_transform_edt(~water, sampling=6.0, return_indices=True)
  51|     near_lv = level[idx[0], idx[1]]
  52|     b = (~water) & (dist <= G["bank_radius_m"]) & ~zone
  53|     over = h[b] - near_lv[b]
  54|     out["banks"] = {"vertices": int(b.sum()), "fail": int((over < G["bank_min_m"]).sum()), "min_m": round(float(over.min()), 3)}
  55|     land = ~water
  56|     sea_cut = float(sys.argv[sys.argv.index("--sea-cut") + 1]) if "--sea-cut" in sys.argv else 0.80
  57|     plane = cell_planes(cls, level, sea_cut=sea_cut)
  58|     czone = zone[:-1, :-1] | zone[:-1, 1:] | zone[1:, :-1] | zone[1:, 1:]
  59|     pw = pl = 0
  60|     for dr in (0, 1):
  61|         for dc in (0, 1):
  62|             hc = h[dr:dr + n - 1, dc:dc + n - 1]
  63|             wc = water[dr:dr + n - 1, dc:dc + n - 1]
  64|             ok = np.isfinite(plane) & ~czone
  65|             with np.errstate(invalid="ignore"):
  66|                 pw += int((ok & wc & (hc > plane - 0.02)).sum())
  67|                 pl += int((ok & ~wc & (hc < plane)).sum())
  68|     out["pieces"] = {"cells": int((np.isfinite(plane) & ~czone).sum()), "water_corner_fail": pw, "land_corner_fail": pl,
  69|                      "fail": pw + pl}
  70|     out["bed_floor"] = {"fail": int((h < G["bed_floor_m"] - 1e-6).sum()), "min_m": round(float(h.min()), 3)}
  71|     beach = t["beach"] if "beach" in t.files else np.zeros_like(land)
  72|     inland = land & ~zone & ~beach
  73|     out["land_floor"] = {"vertices": int(inland.sum()), "fail": int((h[inland] < G["land_floor_m"] - 1e-6).sum()),
  74|                          "min_m": round(float(h[inland].min()), 3),
  75|                          "beach_vertices": int(beach.sum()),
  76|                          "beach_fail": int((h[beach] < G["beach_floor_m"] - 1e-6).sum())}
  77|     nw, ne, sw, se = h[:-1, :-1], h[:-1, 1:], h[1:, :-1], h[1:, 1:]
  78|     au = np.degrees(np.arctan(np.hypot((ne - nw) / 6, (se - ne) / 6)))
  79|     al = np.degrees(np.arctan(np.hypot((sw - nw) / 6, (se - sw) / 6)))
  80|     lnw, lne, lsw, lse = land[:-1, :-1], land[:-1, 1:], land[1:, :-1], land[1:, 1:]
  81|     mu, ml = lnw & lne & lse, lnw & lsw & lse
  82|     su, sl = (lnw | lne | lse) & ~mu, (lnw | lsw | lse) & ~ml
  83|     land_ang = np.r_[au[mu], al[ml]]
  84|     shore_ang = np.r_[au[su], al[sl]]
  85|     out["slopes"] = {"land_triangles": int(land_ang.size), "fail": int((land_ang > G["slope_max_deg"] + G["slope_tol_deg"]).sum()),
  86|                      "within_tolerance": int(((land_ang > G["slope_max_deg"]) & (land_ang <= G["slope_max_deg"] + G["slope_tol_deg"])).sum()),
  87|                      "max_deg": round(float(land_ang.max()), 2),
  88|                      "shore_triangles_over_35": int((shore_ang > G["slope_max_deg"]).sum()),
  89|                      "shore_max_deg": round(float(shore_ang.max()), 2)}
  90|     with rasterio.open(os.path.join(R, "tests", "regional_road_network_v29", "baltic_road_network_v29.asc")) as ds:
  91|         v29 = ds.read(1).astype("float32")
  92|     nz = dn <= G["narva_radius_m"]
  93|     out["narva"] = {"vertices": int(nz.sum()), "identical": bool(np.array_equal(t["heights"][nz], v29[nz])),
  94|                     "max_diff_m": float(np.abs(t["heights"][nz] - v29[nz]).max())}
  95|     gates = [out["water_depth"]["fail"], out["banks"]["fail"], out["land_floor"]["fail"], out["land_floor"]["beach_fail"],
  96|              out["slopes"]["fail"], out["pieces"]["fail"],
  97|              out["bed_floor"]["fail"]]
  98|     out["status"] = "PASS" if all(g == 0 for g in gates) and out["narva"]["identical"] else "FAIL"
  99|     out["limits"] = dict(G, sea_cut_m=sea_cut)
 100|     out['terrain_sha256'] = hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest()
 101|     out['sources'] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (
 102|         Path(__file__), Path(cell_planes.__code__.co_filename),
 103|         Path(R) / 'tests/regional_road_network_v29/baltic_road_network_v29.asc')}
 104|     print(json.dumps(out, indent=1))
 105|     if "--json" in sys.argv:
 106|         with open(sys.argv[sys.argv.index("--json") + 1], "wb") as f:
 107|             f.write(json.dumps(out, indent=1).encode("utf-8"))
 108| 
 109| 
 110| if __name__ == "__main__":
 111|     main()
```

### tools/terrain/verify_channel_reaches_v30.py (lines 1-40)
```python
   1| """Gate re-check aware of the vanilla channel reaches (BALTIC-015 candidates).
   2| 
   3| verify_terrain_v30's water_depth and pieces rules, except that the reach cells whose pond planes the channel fit removed
   4| (<fit>/axes.json removed_cells) are judged against the vanilla piece surface instead of a plane that the engine no
   5| longer has: wet vertices touching those cells must lie under a piece, land vertices there must not lie below one.
   6| Usage: verify_channel_reaches_v30.py <terrain npz> <fit dir> <sea_cut> <out json>
   7| """
   8| import json
   9| import sys
  10| from pathlib import Path
  11| 
  12| import numpy as np
  13| 
  14| ROOT = Path(__file__).resolve().parents[2]
  15| sys.path.insert(0, str(ROOT / 'tools' / 'terrain'))
  16| sys.path.insert(0, str(ROOT / 'tools' / 'water'))
  17| from v30_common import N, cell_planes  # noqa: E402
  18| import engine_water_model as ewm  # noqa: E402
  19| 
  20| NARVA = (2417.1428225906, 6889.8850822322)
  21| 
  22| 
  23| def main():
  24|     path, fit, sea_cut, out = sys.argv[1], Path(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
  25|     t = np.load(path)
  26|     h, cls, level = t['heights'].astype(float), t['cls'], t['level'].astype(float)
  27|     axes = json.loads((fit / 'axes.json').read_text(encoding='utf-8'))
  28|     removed = np.zeros((N - 1, N - 1), bool)
  29|     for reach in axes.values():
  30|         for r, c in reach['removed_cells']:
  31|             removed[r, c] = True
  32|     pieces = [ewm.Piece(p['type'], p['matrix']) for reach in axes.values() for p in reach['pieces']]
  33|     c_, r_ = np.meshgrid(np.arange(N), np.arange(N))
  34|     zone = np.hypot(c_ * 6.0 - NARVA[0], 12282 - r_ * 6.0 - NARVA[1]) <= 600
  35|     water = cls > 0
  36|     plane = cell_planes(cls, level, sea_cut=sea_cut)
  37|     plane[removed] = np.nan
  38|     czone = zone[:-1, :-1] | zone[:-1, 1:] | zone[1:, :-1] | zone[1:, 1:]
  39|     rv = np.zeros((N, N), bool)                      # vertices touching a removed reach cell
  40|     for dr in (0, 1):
```

# Reminder of the task
# What to compute (exact method)
Parameters (argparse, defaults): --terrain PATH, --out DIR, --channels DIR (required unless --selftest), --slope 0.15,
--band 12, --sigma 12, --max-shift 4, --min-vertices 4, --max-raise 2.0 (land), --max-raise-water 6.0, --max-lower 1.5,
--bed-floor (default None: off), --bed-min-depth 0.30, --narva-radius 620, --sea-cut 0.51. Do not add other options.
Constants: FLOWING = (3, 5, 6); STANDING = (2, 7); depth_min 0.10, freeboard 0.05, piece_depth 0.02, land floor 1.40,
beach floor 0.80, plane cut 0.80 (from profile_lakes_v30.G where it has them); EPS = profile_lakes_v30.EPS (1e-4).
Factor the algorithm into `profile(t, nature, corridor, reach_vertices, a)` returning (out arrays dict, masks dict,
report dict without inputs), so main() and the self-test share it.
1. Load as profile_lakes_v30.py does (float64 copies h0, level0; cls0). x, z = grid_xz().
   flow0 = cls0 in FLOWING; land0 = cls0 == 0; low = flow0 & (level0 <= 0.80) (drawn by the engine sea).
   ids = scipy.ndimage.label(flow0 & ~low, structure=np.ones((3, 3))) -> components. A component with fewer than
   --min-vertices vertices is not profiled and counts as `other` below.
2. Per-vertex gate fields, computed ONCE on the whole grid from the input (they stay exact for the output because no
   class or level changes):
   planes = cell_planes(cls0, level0, sea_cut=a.sea_cut); pmin, pmax = vertex_plane_bounds(planes) (NaN where no plane).
   dist, idx = distance_transform_edt(cls0 == 0, sampling=6.0, return_indices=True); near_lv = level0[idx[0], idx[1]]
   (exactly as verify_terrain_v30.py lines 50-51).
   wcap (water vertices) = min(level0 - 0.10, pmin - 0.02) - EPS, ignoring the pmin term where it is NaN.
   lfloor (land vertices) = max(near_lv + 0.05, pmax, floor) + EPS, floor = 0.80 where `beach` else 1.40, ignoring the
   pmax term where it is NaN.
3. Fixed vertices (never changed by the shore profile):
   platform | reserve | nature | corridor (`exact`) | Narva zone (hypot(x - NARVA[0], z - NARVA[1]) <= --narva-radius)
   | map border (x < 12 or z < 12 or x > 12270 or z > 12270) | other | near_other | claimed twice,
   where other = sea (cls 1, 4) | standing (cls 2, 7) | low | reach_vertices | vertices of components below
   --min-vertices; near_other = every vertex within R = --band + --max-shift + 6 m of `other`
   (distance_transform_edt(~other) * 6 <= R); claims: every profiled component claims the vertices within R of it
   (dilate its mask by a disc of radius ceil(R / 6) vertices inside its window, accumulate a uint8 count), and every
   vertex with count >= 2 is fixed.
4. For each profiled component i, window = bounding box grown by g = ceil((R + 3 * sigma + 12) / 6) vertices, clipped:
   a. base, smooth, near, lines, sd and band exactly as profile_lakes_v30.py lines 142-156, with the component mask B.
      Skip (and count) a component without lines.
   b. Lw = level0 of the nearest vertex of B, for every window vertex (distance_transform_edt(~B, return_indices=True)
      inside the window): the local level for the profile target.
   c. edit = band & (B | land0) & ~fixed. Forced edges as profile_lakes_v30.py lines 159-171 (both ends in B | land0, sd
      of opposite sign; forced &= edit); for the offset metric record each crossing edge with the level Lw at its first
      end instead of a body level.
   d. want = Lw + slope * sd on forced vertices, h0 elsewhere. Side = INPUT CLASS: on vertices of B,
      want = min(want, wcap); on land vertices, want = max(want, lfloor). Then the move caps:
      want_c = clip(want, h0 - max_lower, h0 + raise_cap), raise_cap = max_raise_water on vertices of B and max_raise
      on land (a navigable edge vertex 3.5 m deep must reach its shallow target, or the crossing moves the wrong way);
      where want_c breaks its side's gate (water: want_c > wcap;
      land: want_c < lfloor), keep h0 (this also leaves the vertices that already fail a gate as they are).
      Count forced vertices at a cap and vertices kept by the gate.
   e. h1 = want on edit. cls and level never change.
5. Undo steepening as profile_lakes_v30.py lines 200-204: h2, faces = discard_steeper_land_faces(h1, h0, cls0), then the
   float32 round trip.
6. Bed floor (only with --bed-floor F): bedmask = vertices of profiled components with cls0 in (5, 6) (rivers and
   streams; navigable reaches keep their depth) & ~corridor & ~Narva zone & ~map border & ~reach_vertices
   & (level0 > 0.80). need = min(F, level0 - bed_min_depth, wcap). Raise h2 to need where h2 < need; float32 round trip.
   It never lowers anything and may act inside `fixed` (only there and nowhere else may a fixed vertex change).
7. Fail closed (assert): cls and level arrays identical to the input; no fixed vertex changed except bed raises; the
   gate counts of step 8 after <= before, each.
8. Gates, computed exactly as verify_terrain_v30.py computes them (water_depth outside the 600 m Narva zone, banks within
   8.5 m outside that zone, land_floor and beach_floor, pieces water and land corners with cell_planes(cls, level,
   sea_cut=a.sea_cut) outside the zone, slopes = land triangles over 35.01 degrees), each {"before": n, "after": n}.

# Report (<out>/report.json) and outputs
Write <out>/terrain_rivers.npz (np.savez_compressed, the same keys and dtypes as the input) and <out>/masks.npz (bool
arrays band, forced, editable, changed, bed_raised). report.json keys, plain JSON numbers/strings:
- status: "BUILT_PENDING_GATES_AND_ENGINE_VIEWS"; params: every argparse value except paths;
- components: {"labelled": n, "profiled": n, "skipped_small": n, "skipped_no_outline": n, "claimed_twice_vertices": n};
- vertices: {"band": n, "editable": n, "forced": n, "changed": n, "forced_at_move_cap": n, "kept_by_gate": n,
  "bed_raised": n, "face_recovery": <the dict discard_steeper_land_faces returns>};
- by_class: for k in 3, 5, 6 (class of the water end of the edge or of the vertex): {"forced": n, "changed": n,
  "bed_raised": n, "crossing_offset_m_vs_smoothed_outline": {"before": ..., "after": ...}}, where the offset of a
  recorded crossing edge is |t - t*| * edge length, t = terrain crossing of Lw along the edge, t* = outline crossing
  (as profile_lakes_v30.offsets, but with the per-edge level), reported as {"edges", "no_crossing", "p50", "p90",
  "p99"};
- gates: step 8; bed_below_0p85: for k in 3, 5, 6, {"before", "after"} counts of cls == k & level > 0.80 & h < 0.85;
- largest_components: the 10 largest profiled components: id, vertices, class counts {3, 5, 6}, level min and max,
  changed;
- change_m: {"raise_max", "lower_max"}; inputs: {path: sha(path)} for the terrain, NATURE, axes.json and this file;
  output_sha256 of terrain_rivers.npz; seconds; limits (two short strings).
Print the report without "inputs". OUTDIR must not exist: create it; fail if it exists.

# Self-test (--selftest, no other arguments)
Synthetic terrain in memory at full size N x N: land at 4.6 m (cls 0, level NaN, all masks False). Let cc(r) =
1000 + (r - 800) // 7.
- River (cls 5): rows 800..1100, columns cc(r) - 1 .. cc(r) + 1 (a 3-wide diagonal staircase); level 4.0 - 0.004 *
  (r - 800); bed = level - 0.6.
- Stream (cls 6): row 950, columns cc(950) + 2 .. cc(950) + 80; level 3.4 + 0.003 * (c - cc(950) - 2); bed = level -
  0.25.
- Lake (cls 2) touching the river mouth: rows 1101..1115, columns cc(1100) - 7 .. cc(1100) + 7; level 2.75; bed 2.0.
- Navigable (cls 3): rows 1300..1305, columns 900..1300, level 3.0, bed -0.5; its corridor mask: rows 1301..1304,
  columns 900..1300.
- Low reach (cls 3): rows 300..305, columns 300..400, level 0.7, bed 0.0.
Pass nature = all False, reach_vertices = all False. Assert:
- the synthetic input passes every gate of step 8 (all before == 0), and every gate after == 0;
- cls and level identical; corridor vertices unchanged; every vertex within R of the lake and of the low reach unchanged;
- crossing offset p90 after < before for classes 5 and 3;
- in a second call with bed floor 3.5: every class 5 and 6 water vertex is >= min(3.5, level - 0.30) - 1e-5, and the
  corridor vertices are still unchanged.
Print "SELFTEST PASS" and exit 0, or raise.


Write the whole file now, in one fenced block preceded by `FILE: tools/terrain/profile_rivers_v30.py`.

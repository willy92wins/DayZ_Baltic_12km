"""Assemble the GLM implementation brief for tools/terrain/profile_lakes_v30.py (lake and pond shores, islands)."""
from pathlib import Path

W = Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290')
T = W / 'tools' / 'terrain'
OUT = Path(__file__).parent / 'lanes' / 'B_profile_lakes_brief.md'


def numbered(path, a=1, b=None):
    lines = path.read_text(encoding='utf-8').split('\n')
    b = len(lines) if b is None else b
    body = '\n'.join('%4d| %s' % (i, lines[i - 1]) for i in range(a, min(b, len(lines)) + 1))
    rel = path.relative_to(W).as_posix()
    return '\n### %s (lines %d-%d)\n```python\n%s\n```\n' % (rel, a, min(b, len(lines)), body)


TASK = r'''IMPORTANT PROCESS NOTE: write the complete file FIRST, in one pass, then stop. Do not simulate the self-test by hand;
the receiver runs it. Keep internal deliberation focused.

# Task (one sentence)
Write one Python 3.11 command-line tool, `tools/terrain/profile_lakes_v30.py`, that reshapes the terrain around every
lake and pond of a DayZ terrain so that the visible shoreline (where the terrain crosses the flat water plane of that
lake) follows a smoothed outline instead of the 6 m vertex staircase, islands included, keeping every existing gate.

# Why
The water of a lake is a flat plane at the lake level L, drawn by water objects; the visible shore is where the terrain
(6 m grid, triangulated with NW-SE diagonals) crosses that plane. Today wet vertices sit ~0.3 m below L and land ~0.4 m
above it, so the crossing falls at a fixed fraction of every wet-land edge and the shore draws the 6 m grid: serrated
coasts and pointy islands. The sea already got this treatment: `tools/terrain/profile_coast_v30.py` (listed below in
full) is the REFERENCE IMPLEMENTATION; your tool is the same method applied per standing water body with its own level.

# Role and success criterion
You are the implementer. The receiver runs `--selftest` and then the tool on the real 2048 x 2048 terrain. Success = the
file runs unchanged with the stated CLI, the self-test passes, the report follows the schema below, and the real run
leaves every gate count at 0 for the bodies it touched. Prefer plain vectorised numpy/scipy, reuse the helpers listed
below by importing them (do not copy them), and follow profile_coast_v30.py wherever this brief does not say otherwise.
Only the Python stdlib, numpy, scipy, contourpy and shapely 2.x are available (the imports profile_coast_v30.py uses).

# Environment limits you cannot see
- Windows, Python 3.11. Grid N = 2048 vertices per side, 6 m spacing; vertex (r, c) is at game x = 6c, z = 12282 - 6r
  (row 0 north). `v30_common.grid_xz()` returns those x, z arrays.
- About 620 standing bodies, from 4 vertices to 128,410 vertices (the largest touches the map border). Runtime target
  under 10 minutes, peak memory under 8 GB: work in a window around each body, never full-grid per body.
- The tool lives next to the helpers: `sys.path.insert(0, str(Path(__file__).resolve().parent))` then import from
  `v30_common`, `finish_shores_v30`, `profile_coast_v30` (constants and `sha`, `zero_lines`, `turning`, `EDGES`, `NARVA`)
  and `relevel_bodies_v30` (`label_bodies`). Importing those modules has no side effects.

# Verified facts about the input (do not change these conventions)
Terrain NPZ keys: `heights` float32 (N, N) m; `cls` uint8 (N, N): 0 land, 1 sea, 2 lake, 3 navigable, 4 delta, 5 river,
6 stream, 7 pond; `level` float32 (N, N) water level per vertex, NaN on land; bool masks `platform`, `reserve`, `narva`,
`water`, `beach`. Keep every key in the output; rewrite `heights`, `cls`, `level`, `water` (= cls > 0) and `beach`.
- Standing bodies: `label_bodies(cls, level)` from relevel_bodies_v30 (classes 2 and 7, centimetre level, 8-connected)
  returns int32 ids, 0 elsewhere. A body's level L = median of its `level`; its class k = most common cls in it.
- Pond planes: `cell_planes(cls, level)` gives the plane of each 6 m cell that has a water corner of classes 2,3,5,6,7
  above 0.80 m; `vertex_plane_bounds(planes)` the lowest/highest plane around a vertex.
- Gates (tools/terrain/verify_terrain_v30.py, summarised): every water vertex at least 0.10 m below its level; every land
  vertex within 8.5 m of water at least 0.05 m above the nearest water level; land >= 1.40 m except the `beach` mask
  (>= 0.80 m); land triangles <= 35 degrees; in every cell a pond plane covers, water corners >= 0.02 m under the plane
  and land corners >= 0.00 m over it; nothing within 480 m of NARVA changes.

# What to compute (exact method)
Parameters (argparse, defaults): --slope 0.15, --band 12, --sigma 12, --max-shift 4, --min-vertices 9,
--freeboard 0.05, --depth-min 0.10, --max-raise 2.0, --max-lower 1.5, --bed-floor (default None: off),
--bed-min-depth 0.30, --narva-radius 620. Do not add other options.
1. Load as profile_coast_v30.py does (float64 copies). sea0 = cls in (1, 4); flowing0 = cls in (3, 5, 6);
   land0 = cls == 0. ids = label_bodies(cls0, level0). Profiled bodies: >= --min-vertices vertices and L > 0.80.
2. Fixed vertices (never changed by the shore profile): platform | reserve | nature (np.load(NATURE)['reserve'], the
   same file profile_coast_v30.py uses) | corridor (second value of protect_corridors(cell_planes(cls0, level0)))
   | Narva zone (hypot(x - NARVA[0], z - NARVA[1]) <= --narva-radius) | map border (x < 12 or z < 12 or x > 12270 or
   z > 12270) | sea0 | flowing0 | every vertex within (--band + --max-shift + 6) m of a sea0 or flowing0 vertex
   (scipy.ndimage.distance_transform_edt on the complement, times 6) | every vertex claimed by two or more bodies.
   Claim radius R = --band + --max-shift + 6 m: a vertex is claimed by a body when it lies within R of that body
   (dilate each body mask by ceil(R / 6) vertices with a disc-shaped structure inside its window and accumulate a
   uint8 count). Bodies with fewer than --min-vertices vertices also claim (so a small pond next to a lake fixes the
   strip between them) but are not profiled.
3. For each profiled body B (level L, class k), in a window = bounding box of B grown by R + 3 * sigma + 12 m, clipped:
   a. base (m) = -edt(B) * 6 inside B and +edt(~B) * 6 outside, computed in the window (as class_sd in profile_coast,
      line 134, with the body mask instead of sea0).
   b. smooth = gaussian_filter(base, sigma / 6), then clipped to [base - max_shift, base + max_shift].
   c. near = |base| <= band + max_shift + 9. Zero contour lines of smooth restricted to near, with contourpy in the
      window's coordinates (x = 6 * column, y = 12282 - 6 * row; the same convention as zero_lines). Lines with fewer
      than 2 points are dropped. If a body yields no line, skip it and count it in the report.
   d. sd = exact distance from every `near` vertex to those lines (shapely STRtree over the line segments,
      query_nearest with return_distance), negative where smooth < 0 (inside), NaN outside `near`.
   e. band_B = near & |sd| <= band. editable_B = band_B & (B | land0) & ~fixed (fixed already excludes every vertex
      claimed by another body).
   f. forced: for each native edge (dr, dc) in EDGES = ((0, 1), (1, 0), (1, 1)) inside the window, both ends in
      (B | land0), sd finite at both and of opposite sign -> both ends forced; forced &= editable_B.
   g. target = L + slope * sd.
   h. want = target on forced vertices, h0 elsewhere. Then the gates, in this order:
      - land side (sd >= 0): want = max(want, L + freeboard, floor), floor = 0.80 where `beach`, else 1.40;
      - water side (sd < 0): want = min(want, L - depth_min);
      - move caps: want = clip(want, h0 - max_lower, h0 + max_raise) (a capped vertex may stay on its old side);
      - dead zone: where L - depth_min < want < L + freeboard, snap to L + freeboard when want >= L, else to
        L - depth_min.
      h1 = want on editable_B.
   i. Classes follow the heights on editable_B: land0 vertices with h1 < L become water of class k at level L; vertices
      of B with h1 >= L become land (cls 0, level NaN).
   Process bodies one after another on shared h1 / cls1 / level1 arrays (windows of different bodies only overlap on
   fixed vertices, because shared vertices are claimed twice).
4. Bed floor (only with --bed-floor F): every water vertex of a profiled body (after step 3) outside corridor and the
   Narva zone rises to max(h, min(F, L - bed_min_depth)). It never lowers anything and is allowed inside `nature`.
   (Reason, for the report only: the engine draws its sea, 0.65-0.85 m, under any lake whose bed lies below it.)
5. Undo steepening exactly as profile_coast_v30.py lines 195-197 (discard_steeper_land_faces on the whole grid with
   h0 as the original; reverted vertices get their old cls and level back).
6. beach = (input beach | (cls1 == 0) & (h < 1.40)) & (cls1 == 0) & ~narva_zone (as profile_coast line 208).
7. Assert that no vertex in `fixed` changed height, except bed-floor raises (step 4) on water vertices.

# Report (<out>/report.json) and outputs
Write <out>/terrain_lakes.npz (np.savez_compressed, same keys and dtypes as the input) and <out>/masks.npz (bool
arrays: band, forced, editable, changed, bed_raised). report.json keys, all plain JSON numbers/strings:
- status: "BUILT_PENDING_GATES_AND_ENGINE_VIEWS"; params: every argparse value except paths;
- bodies: {"profiled": n, "skipped_small": n, "skipped_no_outline": n, "claimed_twice_vertices": n};
- vertices: {"band": n, "editable": n, "forced": n, "changed": n, "to_water": n, "to_land": n,
  "forced_at_move_cap": n, "bed_raised": n, "face_recovery": <the dict discard_steeper_land_faces returns>};
- waterline_turn_deg_per_12m: {"before": turning(...), "after": turning(...)} where the lines are the zero contours
  of (h - L) of every profiled body inside its band_B (before with h0, after with the result), concatenated over
  bodies before calling turning (turning takes a list of lines);
- gates: counts on the result, computed exactly as verify_terrain_v30.py computes them (water_depth fails for all
  water outside the 600 m Narva zone; banks fails within 8.5 m; land_floor and beach fails; pieces water/land corner
  fails using cell_planes(cls1, level1) with sea_cut 0.80; slopes fails for land triangles over 35.01 degrees),
  each as {"before": n, "after": n};
- largest_bodies: for the 10 largest profiled bodies: id, level_m, class, vertices, changed, to_water, to_land;
- change_m: {"raise_max", "lower_max"}; inputs: {path: sha(path)} for the terrain, NATURE and this file;
  output_sha256 of terrain_lakes.npz; seconds.
Print the report without "inputs". OUTDIR must not exist: create it; fail if it exists.

# Self-test (--selftest, no other arguments)
Build a synthetic terrain in memory at full size N x N: land at 3.0 m everywhere (cls 0, level NaN, all masks False);
lake A: vertices within 40 vertices of (r, c) = (1000, 1000) on a square-ish staircase (use max(|dr|, |dc|) <= 40 with
the four corners cut by |dr| + |dc| <= 60), cls 2, level 2.0, bed 1.0; an island inside A: max(|dr - 5|, |dc + 3|) <= 6
set back to land at 3.0 m; lake B: max(|dr|, |dc - 120|) <= 8 around (1000, 1120) at level 2.5 (claims overlap A's
strip? they are 72 vertices apart, so no); a river (cls 5, level 2.2, bed 1.9) running from (900, 1300) to (1100, 1300)
one vertex wide. Run the same core function (factor the algorithm into a function that takes the arrays and returns the
result and the report dict, so main() and the self-test share it; let the self-test pass a nature mask of False instead
of loading NATURE) and assert: gates after are all 0; every changed vertex lies within 12 + 4 + 6 m of A or B; the
river and every vertex within R of it are unchanged; waterline turn p95 after < before for the profiled bodies; the
island still exists (some land vertex within 6 vertices of (1005, 997)); with --bed-floor 1.5 semantics applied in a
second call, every water vertex of A is >= 1.5 m. Print "SELFTEST PASS" and exit 0, or raise.

# Output format
Reply with exactly one fenced block preceded by the line `FILE: tools/terrain/profile_lakes_v30.py`, containing the
whole file (module docstring in the style of profile_coast_v30.py: what, why, method, fixed, usage). No other files.
English identifiers and comments; comments sparse, in the tone of the reference file.
'''


def main():
    parts = [TASK, '\n# Reference implementation and helpers (read them; import, do not copy)\n',
             numbered(T / 'profile_coast_v30.py'),
             numbered(T / 'v30_common.py', 1, 112),
             numbered(T / 'finish_shores_v30.py', 1, 111),
             numbered(T / "relevel_bodies_v30.py", 1, 70),
             numbered(T / 'verify_terrain_v30.py', 1, 111),
             '\n# Reminder of the task\n' + TASK[TASK.index('# What to compute'):TASK.index('# Output format')]
             + '\nWrite the whole file now, in one fenced block preceded by `FILE: tools/terrain/profile_lakes_v30.py`.\n']
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = ''.join(parts)
    OUT.write_text(text, encoding='utf-8', newline='\n')
    print(OUT, len(text), 'chars')


if __name__ == '__main__':
    main()

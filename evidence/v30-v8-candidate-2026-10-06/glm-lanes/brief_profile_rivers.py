"""Assemble the GLM implementation brief for tools/terrain/profile_rivers_v30.py (navigable, river and stream shores)."""
from pathlib import Path

W = Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290')
T = W / 'tools' / 'terrain'
OUT = Path(__file__).parent / 'lanes' / 'R1_profile_rivers_brief.md'


def numbered(path, a=1, b=None):
    lines = path.read_text(encoding='utf-8').split('\n')
    b = len(lines) if b is None else b
    body = '\n'.join('%4d| %s' % (i, lines[i - 1]) for i in range(a, min(b, len(lines)) + 1))
    rel = path.relative_to(W).as_posix()
    return '\n### %s (lines %d-%d)\n```python\n%s\n```\n' % (rel, a, min(b, len(lines)), body)


TASK = r'''IMPORTANT PROCESS NOTE: write the complete file FIRST, in one pass, then stop. Do not simulate the self-test by hand;
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
'''


def main():
    parts = [TASK, '\n# Reference implementation and helpers (read them; import, do not copy)\n',
             numbered(T / 'profile_lakes_v30.py'),
             numbered(T / 'profile_coast_v30.py', 36, 93),
             numbered(T / 'v30_common.py', 1, 112),
             numbered(T / 'finish_shores_v30.py', 29, 111),
             numbered(T / 'verify_terrain_v30.py', 1, 111),
             numbered(T / 'verify_channel_reaches_v30.py', 1, 40),
             '\n# Reminder of the task\n' + TASK[TASK.index('# What to compute'):TASK.index('# Output format')]
             + '\nWrite the whole file now, in one fenced block preceded by `FILE: tools/terrain/profile_rivers_v30.py`.\n']
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = ''.join(parts)
    OUT.write_text(text, encoding='utf-8', newline='\n')
    print(OUT, len(text), 'chars')


if __name__ == '__main__':
    main()

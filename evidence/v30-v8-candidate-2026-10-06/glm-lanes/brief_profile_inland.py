"""Assemble the GLM implementation brief for tools/terrain/profile_inland_v30.py (one pass over all inland water)."""
from pathlib import Path

W = Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290')
T = W / 'tools' / 'terrain'
OUT = Path(__file__).parent / 'lanes' / 'I1_profile_inland_brief.md'


def numbered(path, a=1, b=None):
    lines = path.read_text(encoding='utf-8').split('\n')
    b = len(lines) if b is None else b
    body = '\n'.join('%4d| %s' % (i, lines[i - 1]) for i in range(a, min(b, len(lines)) + 1))
    rel = path.relative_to(W).as_posix()
    return '\n### %s (lines %d-%d)\n```python\n%s\n```\n' % (rel, a, min(b, len(lines)), body)


TASK = r'''IMPORTANT PROCESS NOTE: write the complete file FIRST, in one pass, then stop. Do not simulate the self-test by hand;
the receiver runs it. Keep internal deliberation focused.

# Task (one sentence)
Write one Python 3.11 command-line tool, `tools/terrain/profile_inland_v30.py`, that does in ONE pass what
`tools/terrain/profile_lakes_v30.py` (standing water) and `tools/terrain/profile_rivers_v30.py` (flowing water) do
separately today, so that shores where a lake or pond touches a river or stream are profiled instead of frozen.

# Why
Both tools move the visible shoreline onto a smoothed outline. Each freezes everything within 22 m of the other kind
of water, so wetlands where ponds, lakes and rivers interleave keep the 6 m staircase (2.5 % of all inland shore edges,
clustered exactly where the eye goes). The lake tool also froze the nature envelope; Guillermo decided on 06-10 that
those shores are profiled too (the reserve stays the same; only the drawing of the shore changes).

# Role and success criterion
You are the implementer. The receiver runs `--selftest` and then the tool on the real 2048 x 2048 terrain. Success = the
file runs unchanged with the stated CLI, the self-test passes, no class or level changes, no gate count grows, and the
report follows the schema. START FROM `profile_rivers_v30.py` (listed in full below; it is reviewed and correct) and
change only what this brief says. Import helpers, do not copy them. Only the Python stdlib, numpy, scipy, contourpy and
shapely 2.x are available.

# Environment limits you cannot see
- Windows, Python 3.11. Grid N = 2048, 6 m spacing; vertex (r, c) is at x = 6c, z = 12282 - 6r (row 0 north).
- About 620 standing bodies (4 to 128,410 vertices) and 160 flowing components. Runtime under 15 minutes, memory under
  8 GB: work in a window around each component.
- Imports, exactly: from v30_common import N, cell_planes, grid_xz, vertex_plane_bounds; from finish_shores_v30 import
  discard_steeper_land_faces, protect_corridors; from profile_coast_v30 import EDGES, NARVA, NATURE, SEA_CLASSES, sha;
  from profile_lakes_v30 import G, EPS, window_lines; from relevel_bodies_v30 import label_bodies;
  from profile_rivers_v30 import PIECE_DEPTH, gate_counts, same_level.

# What changes against profile_rivers_v30.py (everything else stays as it is there)
1. Classes: STANDING = (2, 7), FLOWING = (3, 5, 6), INLAND = STANDING + FLOWING.
   low = cls0 in INLAND & level0 <= 0.80 (drawn by the engine sea; this now includes standing water).
2. Components, one id space:
   - standing ids = label_bodies(cls0, level0) (standing bodies by centimetre level, 8-connected; it already drops
     bodies under 4 vertices, which keep id 0); a standing vertex with id 0 that is not low is "loose";
   - flowing ids = scipy.ndimage.label(flow0 & ~low, structure=np.ones((3, 3), bool)), offset by the number of standing
     ids so the two ranges do not overlap;
   - a component with fewer than --min-vertices vertices is "small" and is not profiled.
3. other = sea classes (1, 4) | low | reach_vertices | loose standing | small components; near_other = within
   R = --band + --max-shift + 6 m of other (as in profile_rivers_v30.py).
4. fixed = platform | reserve | corridor (the exact corridor, first value of protect_corridors) | Narva zone | map
   border | other | near_other. NO nature envelope (drop the `nature` argument entirely) and NO claims: a vertex near two
   components is NOT fixed any more.
5. Several components may edit the same LAND vertex. Keep, per vertex, the edits of every component that edits it and
   take the MAXIMUM of their want_f (the land must stay above every water it borders; the per-vertex lfloor already holds
   the nearest level and the highest plane). A WATER vertex is edited only by its own component (it is never in another
   component's edit mask because edit = band & (B | land0) & ~fixed). Implement with an array `land_max` initialised to
   -inf and a bool `land_set`; after the loop, h1[land_set] = land_max[land_set]. Water edits are written directly.
6. Bed floor (--bed-floor F): body = vertices of profiled components with cls0 in (2, 5, 6, 7) (navigable reaches keep
   their depth), outside the exact corridor, the Narva zone, the map border and reach_vertices, with level0 > 0.80;
   need = min(F, level0 - bed_min_depth, wcap); raise where h2 < need. It may act inside fixed.
7. Report: as profile_rivers_v30.py, with by_class for k in (2, 3, 5, 6, 7) and bed_below_0p85 for the same classes;
   components: {"standing": n, "flowing": n, "profiled": n, "skipped_small": n, "skipped_no_outline": n,
   "land_vertices_edited_by_two_or_more": n}; status "BUILT_PENDING_GATES_AND_ENGINE_VIEWS"; output file
   <out>/terrain_inland.npz and <out>/masks.npz.
8. CLI: --terrain, --out, --channels (required unless --selftest), --slope 0.15, --band 12, --sigma 12, --max-shift 4,
   --min-vertices 4, --max-raise 2.0, --max-raise-water 6.0, --max-lower 1.5, --bed-floor (default None),
   --bed-min-depth 0.30, --narva-radius 620, --sea-cut 0.51. main() as in profile_rivers_v30.py (exact corridor:
   `corridor, _, _, _ = protect_corridors(planes)`), without loading NATURE.

# Self-test (--selftest)
Use the synthetic terrain of profile_rivers_v30.py's self-test (land 4.6 m, the river, the stream, the lake touching the
river mouth, the navigable reach with its corridor, the low reach) and ADD:
- lake A with the shape of profile_lakes_v30.py's self-test (the square-ish staircase with cut corners and its
  island), centred at (r, c) = (1540, 640) instead of (1000, 1000), island centred at (1545, 637), cls 2, level 4.0,
  bed 3.0 (land stays 4.6 m everywhere);
- a pond (cls 7, level 3.0, bed 2.6) of 5 x 5 vertices whose nearest vertex is 2 vertices (12 m) east of the river at
  row 900: rows 898..902, columns cc(900) + 4 .. cc(900) + 8.
Assert:
- every gate before == 0 and after == 0; cls and level identical; the corridor unchanged;
- every vertex within R of the low reach unchanged;
- some land vertex strictly between the river and the pond changed height (the contact is profiled), and none of the
  river or pond water vertices is above its own level - 0.10;
- crossing offset p90 after < before for classes 2, 3 and 5;
- the island of lake A still has land vertices;
- with bed floor 3.5 in a second call: every class 2, 5, 6, 7 water vertex is >= min(3.5, level - 0.30) - 1e-5, and
  the corridor is still unchanged.
Print "SELFTEST PASS".

# Output format
Reply with exactly one fenced block preceded by the line `FILE: tools/terrain/profile_inland_v30.py`, containing the
whole file (module docstring in the style of profile_rivers_v30.py: what, why, method, fixed, usage). No other files.
English identifiers and comments; comments sparse.
'''


def main():
    parts = [TASK, '\n# Reference implementation (start from this file) and helpers\n',
             numbered(T / 'profile_rivers_v30.py'),
             numbered(T / 'profile_lakes_v30.py', 1, 60),
             numbered(T / 'profile_lakes_v30.py', 258, 290),
             numbered(T / 'relevel_bodies_v30.py', 40, 75),
             numbered(T / 'v30_common.py', 85, 112),
             numbered(T / 'finish_shores_v30.py', 34, 52),
             '\n# Reminder of the task\n' + TASK[TASK.index('# What changes'):TASK.index('# Output format')]
             + '\nWrite the whole file now, in one fenced block preceded by `FILE: tools/terrain/profile_inland_v30.py`.\n']
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = ''.join(parts)
    OUT.write_text(text, encoding='utf-8', newline='\n')
    print(OUT, len(text), 'chars')


if __name__ == '__main__':
    main()

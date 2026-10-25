"""Assemble the GLM review brief for tools/terrain/profile_lakes_v30.py."""
from pathlib import Path

W = Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290')
T = W / 'tools' / 'terrain'
OUT = Path(__file__).parent / 'lanes' / 'D_review_brief.md'


def numbered(path, a=1, b=None):
    lines = path.read_text(encoding='utf-8').split('\n')
    b = len(lines) if b is None else b
    body = '\n'.join('%4d| %s' % (i, lines[i - 1]) for i in range(a, min(b, len(lines)) + 1))
    rel = path.relative_to(W).as_posix()
    return '\n### %s (lines %d-%d)\n```python\n%s\n```\n' % (rel, a, min(b, len(lines)), body)


TASK = """# Role
You are a code reviewer from a different model family than the author. Find real defects; do not restyle.

# What the code does (author's summary, verify it against the code, do not trust it)
`tools/terrain/profile_lakes_v30.py` (new) reshapes the shores of every lake and pond of a DayZ terrain (2048 x 2048
vertices, 6 m spacing; vertex (r, c) is at game x = 6c, z = 12282 - 6r, row 0 north) so that the visible shoreline
(where the terrain, triangulated with NW-SE diagonals, crosses the flat water plane at the body level L) follows a
smoothed outline instead of the 6 m staircase, islands included, and optionally lifts every lake bed to a floor.
It is profile_coast_v30.py (listed below, already reviewed) applied per standing body in a window. Claims to check:
- only vertices in `edit` (band of the body, body water or land, not fixed) change in the shore step; fixed covers
  platforms, reserves, nature, corridors, Narva, map border, sea/delta/navigable/river/stream and unlabelled standing
  water plus every vertex within `reach` of them, and every vertex claimed by two bodies;
- classes stay consistent with heights (water of the body below L, land at or above L), and no vertex changes class
  because the outline shift is clamped to 4 m, less than the 6 m spacing (the real run reports 0 class changes);
- gates after the edit: water at most L - 0.10, land at least L + 0.05 and >= 1.40 (0.80 on the beach);
- the bed floor (after the face recovery) only raises water of profiled bodies outside corridors and Narva;
- report numbers measure what their keys say (crossing offsets before/after are measured along the edges that cross
  the smoothed outline; 'after' is exact by construction where both ends of an edge took the target).
Real run (report below): 623 bodies, 40,899 forced vertices, 0 class changes, gates unchanged, beds under 0.85 m from
287,813 to 1,155 vertices; an independent receiver check found 0 class changes and 0 changes far from standing water.

# What to look for (in this order)
1. Correctness bugs: window slicing and view assignment (h1[W] and the others are numpy views), r/c vs x/z, sign
   conventions of base/smooth/sd, the forced-edge construction for the three edge directions (including the edges list
   used by offsets()), a body whose window touches the map edge, bodies processed in sequence on shared arrays (can an
   earlier body's edit change what a later body reads?), the claims count (uint8), NaN handling, the class restore
   after discard_steeper_land_faces, the bed-floor mask (profiled[ids1]).
2. Gate violations the code could produce on some input (for example a forced land vertex capped below L + 0.05, a
   vertex left in the dead zone, land under 1.40 outside the beach).
3. The self-test: does it really test what it claims?
4. Anything in the helpers ONLY as it affects this tool.

# Output format (strict; the receiver parses it mechanically)
For each finding, exactly this block:

### F<n> | <BLOCKER|MAJOR|MINOR> | <one-line claim>
EVID: <path>:<line> `<an exact substring copied from that numbered line, at least 12 characters>`
SCENARIO: <concrete input or state -> wrong output or crash>
FIX: <one or two sentences>

Rules: every finding needs at least one EVID line whose substring really appears on that line of the listing below
(copy it character by character; do not include the line-number prefix). No finding without a concrete scenario.
Style, naming, comments and performance are out of scope unless they cause a wrong result. If you find nothing
real, say so: an empty review is a valid answer. End with one line: `VERDICT: <ACCEPT|ACCEPT_WITH_FIXES|REJECT>`.
Do not simulate long computations by hand; reason about the code. The answer should be under 1,500 words.
"""


def main():
    parts = [TASK, '\n# Code under review\n',
             numbered(T / 'profile_lakes_v30.py'),
             '\n# Helpers (context only)\n',
             numbered(T / 'profile_coast_v30.py'),
             numbered(T / 'v30_common.py', 14, 112),
             numbered(T / 'finish_shores_v30.py', 29, 111),
             numbered(T / 'relevel_bodies_v30.py', 1, 70),
             '\n# Report of the real run\n```json\n'
             + Path('E:/DayZ-Baltic-Build/v30-v7/lakes/report.json').read_text(encoding='utf-8') + '\n```\n',
             '\n# Reminder of the task\n' + TASK[TASK.index('# What to look for'):]]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = ''.join(parts)
    OUT.write_text(text, encoding='utf-8', newline='\n')
    print(OUT, len(text), 'chars')


if __name__ == '__main__':
    main()

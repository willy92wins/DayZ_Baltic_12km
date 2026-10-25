"""Assemble the GLM review brief for shape_causeways_v30.py and the --bed-surface change (commit f6b3825)."""
import subprocess
from pathlib import Path

W = Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290')
T = W / 'tools' / 'terrain'
OUT = Path(__file__).parent / 'lanes' / 'A_review_brief.md'


def numbered(path, a=1, b=None):
    lines = path.read_text(encoding='utf-8').split('\n')
    b = len(lines) if b is None else b
    body = '\n'.join('%4d| %s' % (i, lines[i - 1]) for i in range(a, b + 1) if i <= len(lines))
    rel = path.relative_to(W).as_posix()
    return '\n### %s (lines %d-%d)\n```python\n%s\n```\n' % (rel, a, min(b, len(lines)), body)


TASK = """# Role
You are a code reviewer from a different model family than the author. Find real defects; do not restyle.

# What the code does (author's summary, verify it against the code, do not trust it)
- `tools/terrain/shape_causeways_v30.py` rebuilds the road causeways that cross the sea on a DayZ terrain
  (2048 x 2048 vertices, 6 m spacing; vertex (r, c) is at game x = 6c, z = 12282 - 6r, row 0 north) as an embankment
  on the road centre line: crest at max(road profile, 1.70 m), 1:2 side slopes down to a smoothed sea bed, 80 m ramps.
  It must never lower natural land, must keep pond classes / pond planes / navigable corridors / the Narva zone / the
  map border fixed, and must pass the same height gates as `profile_coast_v30.py` (sea at least 0.10 m deep below the
  0.75 m sea level, i.e. sea vertices <= 0.65 m; land at least 0.80 m on the beach and 1.40 m elsewhere; no vertex in the
  dead zone between 0.65 and 0.80 m).
- On the real map it found two sections (403.5 m and 618.5 m), changed 1,731 vertices, lowered 748 (0 natural land),
  270 sea vertices became land and 1 land vertex became sea; gate counts after: 0 / 0 / 0.
- `tools/terrain/build_surface_v30.py` gained `--bed-surface gravel`: under standing water it keeps the land colour
  (from `--bed-tone land`) but leaves the surface slot as gravel (slot 0, cp_gravel, whose CfgSurfaces character is
  "Empty", so the engine plants no grass there). Without the option the output must be byte-identical to before.

# What to look for (in this order)
1. Correctness bugs in shape_causeways_v30.py: wrong masks or sign conventions, row/column vs x/z mix-ups, an edit
   that can lower natural land or break a gate it claims to keep, classes that disagree with heights after the edit,
   off-by-one in section detection (gap closing, minimum length, ramps), wrong distance used for the embankment,
   arrays modified in place that are reused later as "original", divisions by zero, empty-array crashes
   (np.percentile / np.median of empty selections), and report numbers that do not measure what their key says.
2. The --bed-surface change: can it alter any output when the option is absent? Is the option threaded through the
   worker pool correctly?
3. Anything in the imported helpers shown below ONLY as it affects these two changes (do not review the helpers
   for their own sake).

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
Keep the internal deliberation focused; the answer itself should be under 1,500 words.
"""


def main():
    diff = subprocess.run(['git', '-C', str(W), 'show', 'f6b3825', '--', 'tools/terrain/build_surface_v30.py'],
                          capture_output=True, text=True, encoding='utf-8', check=True).stdout
    diff = diff[diff.index('diff --git'):]
    parts = [TASK, '\n# Code under review\n',
             numbered(T / 'shape_causeways_v30.py'),
             '\n# Diff of build_surface_v30.py in commit f6b3825\n```diff\n' + diff + '\n```\n',
             numbered(T / 'build_surface_v30.py', 95, 210),
             '\n# Imported helpers (context only)\n',
             numbered(T / 'v30_common.py', 14, 112),
             numbered(T / 'finish_shores_v30.py', 29, 111),
             numbered(T / 'profile_coast_v30.py'),
             numbered(T / 'verify_roads_v30.py', 22, 43),
             '\n# Report the tool wrote on the real map (E:/DayZ-Baltic-Build/v30-v6/causeway/report.json)\n```json\n'
             + Path('E:/DayZ-Baltic-Build/v30-v6/causeway/report.json').read_text(encoding='utf-8') + '\n```\n',
             '\n# Reminder of the task\n' + TASK[TASK.index('# What to look for'):]]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = ''.join(parts)
    OUT.write_text(text, encoding='utf-8', newline='\n')
    print(OUT, len(text), 'chars')


if __name__ == '__main__':
    main()

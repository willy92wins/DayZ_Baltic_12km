"""Assemble the GLM review brief for raise_beds_v30.py and build_surface_v30.py --bed-tone depth (commit cf0e0f0)."""
import subprocess
from pathlib import Path

W = Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290')
T = W / 'tools' / 'terrain'
OUT = Path(__file__).parent / 'lanes' / 'C_review_brief.md'


def numbered(path, a=1, b=None):
    lines = path.read_text(encoding='utf-8').split('\n')
    b = len(lines) if b is None else b
    body = '\n'.join('%4d| %s' % (i, lines[i - 1]) for i in range(a, min(b, len(lines)) + 1))
    rel = path.relative_to(W).as_posix()
    return '\n### %s (lines %d-%d)\n```python\n%s\n```\n' % (rel, a, min(b, len(lines)), body)


TASK = """# Role
You are a code reviewer from a different model family than the author. Find real defects; do not restyle.

# What the code does (author's summary, verify it against the code, do not trust it)
- `tools/terrain/raise_beds_v30.py` (new) lifts the bed of chosen standing water bodies of a DayZ terrain (2048 x 2048
  vertices, 6 m spacing; vertex (r, c) is at game x = 6c, z = 12282 - 6r, row 0 north) so that the engine sea
  (0.65-0.85 m) is not drawn under them: every vertex of a chosen body goes to max(h, min(floor, level - min_depth)).
  Bodies are chosen by a point inside them, with the census labelling `label_bodies` (classes 2 and 7). It must only
  raise, never touch any vertex outside the chosen bodies, keep classes and levels, and write the same NPZ keys.
  On the real map it raised 125,292 vertices of one body (level 2.64 m) from -5.36 m to 1.0 m.
- `tools/terrain/build_surface_v30.py` gained `--bed-tone depth`: like `--bed-tone land` (standing-water bed in the
  surrounding land colour, darkened with depth) but blended into the dark bed colour `bed` by
  w = clip((level - h - 0.3) / 0.9, 0, 1). With `--bed-tone land` the output must stay byte-identical to before
  (checked by the author on two tiles).

# What to look for (in this order)
1. Correctness bugs in raise_beds_v30.py: wrong row/column or x/z conversion of --at, a body chosen wrongly, NaN
   handling (level is NaN on land), dtype changes on write (heights float32 in, float32 out), the round-trip check,
   report numbers that do not measure what their key says.
2. The depth tone: do `lvl`, `h1`, `bed` and `depth` mean what the blend assumes at that point of `tile()`? Can the
   `land` branch output change? Any broadcasting error ([..., None]) or a pixel class that now gets the wrong colour?
3. Anything in the helpers below ONLY as it affects these two changes.

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
Keep the internal deliberation focused; the answer itself should be under 1,200 words.
"""


def main():
    diff = subprocess.run(['git', '-C', str(W), 'show', 'cf0e0f0', '--', 'tools/terrain/build_surface_v30.py'],
                          capture_output=True, text=True, encoding='utf-8', check=True).stdout
    diff = diff[diff.index('diff --git'):]
    parts = [TASK, '\n# Code under review\n',
             numbered(T / 'raise_beds_v30.py'),
             '\n# Diff of build_surface_v30.py in commit cf0e0f0\n```diff\n' + diff + '\n```\n',
             numbered(T / 'build_surface_v30.py', 30, 180),
             '\n# Helpers (context only)\n',
             numbered(T / 'relevel_bodies_v30.py', 1, 70),
             numbered(T / 'v30_common.py', 14, 45),
             '\n# Report the tool wrote on the real map\n```json\n'
             + Path('E:/DayZ-Baltic-Build/v30-v7probe/beds/report.json').read_text(encoding='utf-8') + '\n```\n',
             '\n# Reminder of the task\n' + TASK[TASK.index('# What to look for'):]]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = ''.join(parts)
    OUT.write_text(text, encoding='utf-8', newline='\n')
    print(OUT, len(text), 'chars')


if __name__ == '__main__':
    main()

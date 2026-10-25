"""Assemble two GLM briefs (lanes P1, P2) that make the chain tools with fixed inputs take them as arguments."""
from pathlib import Path

W = Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290')
OUT = Path(__file__).parent / 'lanes'


def numbered(rel):
    path = W / rel
    lines = path.read_text(encoding='utf-8').split('\n')
    body = '\n'.join('%4d| %s' % (i, lines[i - 1]) for i in range(1, len(lines) + 1))
    return '\n### %s (full file, %d lines)\n```python\n%s\n```\n' % (rel, len(lines), body)


COMMON = r'''IMPORTANT PROCESS NOTE: write the complete files FIRST, in one pass, then stop. Keep internal deliberation focused.

# Task
Make the DayZ terrain chain tools listed below take their fixed inputs as command-line arguments, so the chain can be
re-run from a new water design. Every new argument DEFAULTS to the value hard-coded today, so a run without the new
arguments must produce byte-identical outputs and reports (the receiver re-runs each tool with its defaults and
compares sha256 against the archived outputs). This is a mechanical refactor: change nothing else.

# Rules (all tools)
1. A hard-coded input terrain or folder `SOURCE` with its expected hash becomes `--source PATH` (default SOURCE) and
   `--source-sha HEX` (default the hard-coded hash). The special value `--source-sha any` skips the hash check; the
   report then records the real sha256 of the file it read instead of the hard-coded constant. With the defaults, the
   check and the report stay exactly as today (same keys, same values, same order).
2. Hard-coded data paths become arguments with the same defaults:
   - `--design DIR` for ROOT/'tests/water_v3' (water_v3.geojson, streams_candidates.geojson, profiles.npz);
   - `--water-v30 PATH` for ROOT/'tests/terrain_v30/water_v30.npz' (or Path(R)/...);
   - `--nature PATH` for ROOT/'tests/regional_outline_v1/reference.npz' (or Path(R)/...);
   - any other fixed E:/ file (reference.json files) gets an argument named after its role, listed per tool below.
   Keep module-level constants as the defaults (do not delete them: other modules import some of them).
3. Reports: where a report lists inputs ({path: sha}), list the paths actually used. With defaults this is the same
   list as today.
4. Do not reformat, rename, reorder or "improve" anything else. Keep the comment style. No new dependencies.
5. Output: one fenced block per changed file, each preceded by the line `FILE: <repo-relative path>`, with the WHOLE
   file. Nothing else.
'''

P1 = COMMON + r'''
# Files for this lane
- tools/terrain/repair_delta_fairways_v30.py: SOURCE/SOURCE_SHA (lines 23-24) -> --source/--source-sha; AXES (line 25)
  -> --axes PATH.
- tools/terrain/finish_shores_v30.py: SOURCE/EXPECTED (lines 19-20) -> --source/--source-sha (line 116 checks it, line
  194 reports source_sha256=EXPECTED: with `any` report the real sha); wpath (line 120) -> --water-v30; naturepath
  (line 121) -> --nature. ALSO `protect_corridors(planes)` (lines 34-52) reads two fixed corridor files: add an optional
  keyword parameter `sources=None` (None = the two files of today) and a CLI option `--corridors PATH [PATH ...]` in
  main() passed through. protect_corridors is imported by other tools with the call `protect_corridors(planes)`: that
  call must keep working unchanged.
- tools/terrain/restore_narva_ponds_v30.py: SOURCE/EXPECTED (lines 20-21) -> --source/--source-sha; design (line 30)
  -> --design (the folder; the file is water_v3.geojson inside it); nature (line 36) -> --nature.
'''

P2 = COMMON + r'''
# Files for this lane
- tools/terrain/connect_small_watercourses_v30.py: SOURCE/SOURCE_SHA (lines 20-21) -> --source/--source-sha; water,
  streams, profpath (lines 27-28) -> --design (folder with water_v3.geojson, streams_candidates.geojson, profiles.npz);
  naturepath (line 54) -> --nature.
- tools/water/deduplicate_water_v30.py: SOURCE (line 18, a water folder) with PBO_SHA and MANIFEST_SHA (lines 19-20)
  -> --source DIR, --pbo-sha HEX, --manifest-sha HEX (each accepts `any`).
- tools/terrain/deepen_wave_margins_v30.py: SOURCE/SOURCE_SHA (lines 19-20) -> --source/--source-sha; REFERENCE
  (line 21) -> --reference PATH; the parent reference (line 57) -> --parent-reference PATH; nature_path (line 140) ->
  --nature; design_path (line 142) -> --design (folder).
- tools/terrain/fit_shore_crossings_v30.py: WATER (line 42) -> --water-v30; NATURE (line 43) -> --nature; SHALLOW
  (line 44) -> --shallow-reference PATH; DRY (line 45) -> --dry-reference PATH. It already has argparse (line 99):
  add the options there.
'''


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, text, files in (('P1', P1, ['tools/terrain/repair_delta_fairways_v30.py', 'tools/terrain/finish_shores_v30.py',
                                          'tools/terrain/restore_narva_ponds_v30.py']),
                              ('P2', P2, ['tools/terrain/connect_small_watercourses_v30.py', 'tools/water/deduplicate_water_v30.py',
                                          'tools/terrain/deepen_wave_margins_v30.py', 'tools/terrain/fit_shore_crossings_v30.py'])):
        body = text + '\n# The files (full listings)\n' + ''.join(numbered(f) for f in files) + \
            '\n# Reminder\n' + text[text.index('# Rules'):] + '\nWrite the whole changed files now.\n'
        p = OUT / f'{name}_parametrize_brief.md'
        p.write_text(body, encoding='utf-8', newline='\n')
        print(p, len(body))


if __name__ == '__main__':
    main()

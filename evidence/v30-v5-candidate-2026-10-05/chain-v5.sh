#!/usr/bin/env bash
# Candidate v5 (05-10): v4 + land floor 1.60 m (Guillermo). The coast step ran before this script:
#   profile_coast_v30.py --terrain v30-v3/shore-v3b/terrain_shore.npz --out v30-v5/coast --floor 1.60 --raise-land
# Then the same gates, surface and worktree package as v4 (water pieces of v3b) and the visible-water audit at the
# swell crest. Sequential and low priority: the box is shared with another session's DayZ tests.
set -euo pipefail
W="/c/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
WWIN="C:\\Users\\guill\\OneDrive\\Documentos\\DayZ Projects\\DayZ_Baltic_12km_dev\\.claude\\worktrees\\codex-handoff-review-74f290"
V3=E:/DayZ-Baltic-Build/v30-v3
P=E:/DayZ-Baltic-Build/v30-v5
PY="/c/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe"
export PYTHONUTF8=1
WW="C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
export PYTHONPATH="$WW/tools/terrain;$WW/tools/navigation;$WW/tools/water"
# children inherit a BelowNormal priority class from their parent (CreateProcess)
WINPID=$(cat /proc/$$/winpid)
powershell.exe -NoProfile -Command "(Get-Process -Id $WINPID).PriorityClass='BelowNormal'; (Get-Process -Id $WINPID).PriorityClass"
t0=$(date +%s); step() { echo "[$(( $(date +%s) - t0 )) s] $*"; }
T=$P/coast/terrain_coast.npz
test -f $T
step gates and surface
"$PY" "$W/tools/terrain/verify_terrain_v30.py" $T --sea-cut 0.51 > $P/verify-v5.json 2> $P/verify-v5.err || echo "verify_terrain exit $?"
"$PY" "$W/tools/terrain/verify_roads_v30.py" "$T::heights" "$T::water" --json $P/roads-v5.json > $P/roads-v5.log 2>&1 || echo "verify_roads exit $?"
"$PY" "$W/tools/terrain/verify_channel_reaches_v30.py" $T $V3/fit-v3b 0.51 $P/channel-reaches.json > $P/channel-reaches.log 2>&1 || echo "verify_channel_reaches exit $?"
"$PY" "$W/tools/terrain/build_surface_v30.py" $T $P/surface --workers 4 --bed-tone land --shore-ring flowing > $P/surface.log 2>&1
step package
env -u PYTHONPATH powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$WWIN\\tools\\terrain\\build_v30_package.ps1" -Build 'E:\DayZ-Baltic-Build\v30-v5\package' -Terrain 'E:\DayZ-Baltic-Build\v30-v5\coast\terrain_coast.npz' -Pieces 'E:\DayZ-Baltic-Build\v30-v3\fit-v3b\water' -Layers 'E:\DayZ-Baltic-Build\v30-v5\surface' > $P/package-run.log 2>&1
grep -q "Built:" $P/package-run.log
step census and audit
"$PY" "$W/tools/water/audit_visible_water_v30.py" --terrain $T --out $P/audit-v5-085 --sea-level 0.85 --sea-cut 0.51 --channels $V3/fit-v3b > $P/audit-v5-085.log 2>&1 || echo "audit v5 0.85 exit $?"
"$PY" "$W/tools/water/census_perched_water_v30.py" --terrain $T --out $P/census > $P/census.log 2>&1 || echo "census exit $?"
step done

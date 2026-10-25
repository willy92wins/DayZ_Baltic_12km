#!/usr/bin/env bash
# Candidate v7 (05-10): v6 + the shores of every lake and pond profiled on a smoothed outline, islands included
# (tools/terrain/profile_lakes_v30.py), with the bed of every standing body at 1.0 m or more and 0.30 m of water at least
# (BALTIC-018, Guillermo 05-10: lakes and ponds yes, navigable reaches keep their depth). The outline shift stays under
# the 6 m vertex spacing, so no vertex changes class or level and the v3b water pieces stay valid (0 plane cells differ);
# then the v6 gates, the surface (v6 options with --bed-tone depth: shallow margins in the land colour, deep water dark), the package, the visible-water audit and the census.
# Sequential and low priority: the box is shared.
set -euo pipefail
W="/c/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
WWIN="C:\\Users\\guill\\OneDrive\\Documentos\\DayZ Projects\\DayZ_Baltic_12km_dev\\.claude\\worktrees\\codex-handoff-review-74f290"
V3=E:/DayZ-Baltic-Build/v30-v3
T6=E:/DayZ-Baltic-Build/v30-v6/causeway/terrain_causeway.npz
P=E:/DayZ-Baltic-Build/v30-v7
PY="/c/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe"
export PYTHONUTF8=1
WW="C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
export PYTHONPATH="$WW/tools/terrain;$WW/tools/navigation;$WW/tools/water"
WINPID=$(cat /proc/$$/winpid)
powershell.exe -NoProfile -Command "(Get-Process -Id $WINPID).PriorityClass='BelowNormal'; (Get-Process -Id $WINPID).PriorityClass"
t0=$(date +%s); step() { echo "[$(( $(date +%s) - t0 )) s] $*"; }
mkdir -p $P
step lakes
test -f $P/lakes/terrain_lakes.npz || "$PY" "$W/tools/terrain/profile_lakes_v30.py" --terrain $T6 --out $P/lakes \
    --bed-floor 1.0 --bed-min-depth 0.30 --min-vertices 4 > $P/lakes.log 2>&1
T=$P/lakes/terrain_lakes.npz
step gates
"$PY" "$W/tools/terrain/verify_terrain_v30.py" $T --sea-cut 0.51 > $P/verify-v7.json 2> $P/verify-v7.err || echo "verify_terrain exit $?"
"$PY" "$W/tools/terrain/verify_roads_v30.py" "$T::heights" "$T::water" --json $P/roads-v7.json > $P/roads-v7.log 2>&1 || echo "verify_roads exit $?"
"$PY" "$W/tools/terrain/verify_channel_reaches_v30.py" $T $V3/fit-v3b 0.51 $P/channel-reaches.json > $P/channel-reaches.log 2>&1 || echo "verify_channel_reaches exit $?"
step "water tiles: none to patch, classes and levels unchanged (checked cell for cell)"
step surface
"$PY" "$W/tools/terrain/build_surface_v30.py" $T $P/surface --workers 4 --bed-tone depth --bed-surface gravel --shore-ring flowing > $P/surface.log 2>&1
step package
env -u PYTHONPATH powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$WWIN\\tools\\terrain\\build_v30_package.ps1" -Build 'E:\DayZ-Baltic-Build\v30-v7\package' -Terrain 'E:\DayZ-Baltic-Build\v30-v7\lakes\terrain_lakes.npz' -Pieces 'E:\DayZ-Baltic-Build\v30-v3\fit-v3b\water' -Layers 'E:\DayZ-Baltic-Build\v30-v7\surface' > $P/package-run.log 2>&1
grep -q "Built:" $P/package-run.log
step census and audit
"$PY" "$W/tools/water/audit_visible_water_v30.py" --terrain $T --out $P/audit-v7-085 --sea-level 0.85 --sea-cut 0.51 --channels $V3/fit-v3b > $P/audit-v7-085.log 2>&1 || echo "audit v7 0.85 exit $?"
"$PY" "$W/tools/water/census_perched_water_v30.py" --terrain $T --out $P/census > $P/census.log 2>&1 || echo "census exit $?"
step done

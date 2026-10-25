#!/usr/bin/env bash
# Candidate v8 (06-10): v7d + the shores of every navigable reach, river and stream profiled on a smoothed outline
# (tools/terrain/profile_rivers_v30.py), with river and stream beds at 1.0 m or more and 0.30 m of water at least
# (BALTIC-018); navigable reaches keep their depth and their exact 24 m corridors, and their edges are free. No vertex
# changes class or level, so the v3b water pieces stay valid; then the v7 gates, the surface (v7 options), the package,
# the visible-water audit and the census. Sequential and low priority: the box is shared.
set -euo pipefail
W="/c/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
WWIN="C:\\Users\\guill\\OneDrive\\Documentos\\DayZ Projects\\DayZ_Baltic_12km_dev\\.claude\\worktrees\\codex-handoff-review-74f290"
E="$W/evidence/v30-v8-candidate-2026-10-06"
V3=E:/DayZ-Baltic-Build/v30-v3
T7=E:/DayZ-Baltic-Build/v30-v7/lakes-b/terrain_lakes.npz
P=E:/DayZ-Baltic-Build/v30-v8
PY="/c/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe"
export PYTHONUTF8=1
WW="C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
export PYTHONPATH="$WW/tools/terrain;$WW/tools/navigation;$WW/tools/water"
WINPID=$(cat /proc/$$/winpid)
powershell.exe -NoProfile -Command "(Get-Process -Id $WINPID).PriorityClass='BelowNormal'; (Get-Process -Id $WINPID).PriorityClass"
t0=$(date +%s); step() { echo "[$(( $(date +%s) - t0 )) s] $*"; }
mkdir -p $P
step rivers
test -f $P/rivers/terrain_rivers.npz || "$PY" "$W/tools/terrain/profile_rivers_v30.py" --terrain $T7 --out $P/rivers \
    --channels $V3/fit-v3b --bed-floor 1.0 --bed-min-depth 0.30 > $P/rivers.log 2>&1
T=$P/rivers/terrain_rivers.npz
step check
"$PY" "$E/scripts/check_profile_rivers.py" $T7 $T --channels $V3/fit-v3b --bed-floor 1.0 --bed-min-depth 0.30 \
    --json $P/check-profile-rivers.json > $P/check-profile-rivers.log 2>&1 || echo "check exit $?"
step gates
"$PY" "$W/tools/terrain/verify_terrain_v30.py" $T --sea-cut 0.51 > $P/verify-v8.json 2> $P/verify-v8.err || echo "verify_terrain exit $?"
"$PY" "$W/tools/terrain/verify_roads_v30.py" "$T::heights" "$T::water" --json $P/roads-v8.json > $P/roads-v8.log 2>&1 || echo "verify_roads exit $?"
"$PY" "$W/tools/terrain/verify_channel_reaches_v30.py" $T $V3/fit-v3b 0.51 $P/channel-reaches.json > $P/channel-reaches.log 2>&1 || echo "verify_channel_reaches exit $?"
step "water tiles: none to patch, classes and levels unchanged (the check counts them)"
step surface
"$PY" "$W/tools/terrain/build_surface_v30.py" $T $P/surface --workers 4 --bed-tone depth --bed-surface gravel --shore-ring flowing > $P/surface.log 2>&1
step package
env -u PYTHONPATH powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$WWIN\\tools\\terrain\\build_v30_package.ps1" -Build 'E:\DayZ-Baltic-Build\v30-v8\package' -Terrain 'E:\DayZ-Baltic-Build\v30-v8\rivers\terrain_rivers.npz' -Pieces 'E:\DayZ-Baltic-Build\v30-v3\fit-v3b\water' -Layers 'E:\DayZ-Baltic-Build\v30-v8\surface' > $P/package-run.log 2>&1
grep -q "Built:" $P/package-run.log
step census and audit
"$PY" "$W/tools/water/audit_visible_water_v30.py" --terrain $T --out $P/audit-v8-085 --sea-level 0.85 --sea-cut 0.51 --channels $V3/fit-v3b > $P/audit-v8-085.log 2>&1 || echo "audit v8 0.85 exit $?"
"$PY" "$W/tools/water/census_perched_water_v30.py" --terrain $T --out $P/census > $P/census.log 2>&1 || echo "census exit $?"
step done

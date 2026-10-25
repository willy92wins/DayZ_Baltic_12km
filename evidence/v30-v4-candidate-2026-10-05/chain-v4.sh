#!/usr/bin/env bash
# Candidate v4 (05-10): the v3b chain unchanged up to the shore fit (same inputs and flags, so water-v3b, fit-v3b and
# shore-v3b are reused as they are), then the coast profile (tools/terrain/profile_coast_v30.py, defaults), gates,
# surface and the package built by THIS worktree's script (derive_world_v30.py with MaxTide 1.5 / MaxWave 0.1).
# The relaxed 0.03 m depth near the outline is left out: it breaks the 0.10 m gate and the plan keeps it out of 1.0.
# Visible-water audits at the new swell: 0.65 (trough), 0.85 (crest) and 0.97 (crest + the 0.12 m fake wave), on
# v3b and v4 alike.
set -euo pipefail
W="/c/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
WWIN="C:\\Users\\guill\\OneDrive\\Documentos\\DayZ Projects\\DayZ_Baltic_12km_dev\\.claude\\worktrees\\codex-handoff-review-74f290"
V3=E:/DayZ-Baltic-Build/v30-v3
P=E:/DayZ-Baltic-Build/v30-v4
PY="/c/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe"
export PYTHONUTF8=1
WW="C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
export PYTHONPATH="$WW/tools/terrain;$WW/tools/navigation;$WW/tools/water"
mkdir -p $P
# children inherit a BelowNormal priority class from their parent (CreateProcess)
WINPID=$(cat /proc/$$/winpid)
powershell.exe -NoProfile -Command "(Get-Process -Id $WINPID).PriorityClass='BelowNormal'; (Get-Process -Id $WINPID).PriorityClass"
t0=$(date +%s); step() { echo "[$(( $(date +%s) - t0 )) s] $*"; }
step coast profile
"$PY" "$W/tools/terrain/profile_coast_v30.py" --terrain $V3/shore-v3b/terrain_shore.npz --out $P/coast > $P/coast.log 2>&1
T=$P/coast/terrain_coast.npz
step gates and surface
# sequential, low priority and 4 surface workers: the box runs another session's DayZ test with ~2 GB of RAM free
"$PY" "$W/tools/terrain/verify_terrain_v30.py" $T --sea-cut 0.51 > $P/verify-v4.json 2> $P/verify-v4.err || echo "verify_terrain exit $?"
"$PY" "$W/tools/terrain/verify_roads_v30.py" "$T::heights" "$T::water" --json $P/roads-v4.json > $P/roads-v4.log 2>&1 || echo "verify_roads exit $?"
"$PY" "$W/tools/terrain/verify_channel_reaches_v30.py" $T $V3/fit-v3b 0.51 $P/channel-reaches.json > $P/channel-reaches.log 2>&1 || echo "verify_channel_reaches exit $?"
"$PY" "$W/tools/terrain/build_surface_v30.py" $T $P/surface --workers 4 --bed-tone land --shore-ring flowing > $P/surface.log 2>&1
step package
env -u PYTHONPATH powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$WWIN\\tools\\terrain\\build_v30_package.ps1" -Build 'E:\DayZ-Baltic-Build\v30-v4\package' -Terrain 'E:\DayZ-Baltic-Build\v30-v4\coast\terrain_coast.npz' -Pieces 'E:\DayZ-Baltic-Build\v30-v3\fit-v3b\water' -Layers 'E:\DayZ-Baltic-Build\v30-v4\surface' > $P/package-run.log 2>&1
grep -q "Built:" $P/package-run.log
step census and audits
for lv in 0.65 0.85 0.97; do
  tag=${lv/./}
  "$PY" "$W/tools/water/audit_visible_water_v30.py" --terrain $T --out $P/audit-v4-$tag --sea-level $lv --sea-cut 0.51 --channels $V3/fit-v3b > $P/audit-v4-$tag.log 2>&1 || echo "audit v4 $lv exit $?"
  "$PY" "$W/tools/water/audit_visible_water_v30.py" --terrain $V3/shore-v3b/terrain_shore.npz --out $P/audit-v3b-$tag --sea-level $lv --sea-cut 0.51 --channels $V3/fit-v3b > $P/audit-v3b-$tag.log 2>&1 || echo "audit v3b $lv exit $?"
done
"$PY" "$W/tools/water/census_perched_water_v30.py" --terrain $T --out $P/census > $P/census.log 2>&1 || echo "census exit $?"
step done

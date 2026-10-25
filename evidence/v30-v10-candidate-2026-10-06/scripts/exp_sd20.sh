#!/usr/bin/env bash
# Experiment on v10: the inland shore pass reading the builder's vector signed distance (step 20, sign by
# point-in-polygon of the smoothed design) instead of the step-22 outline (re-smoothed without keeping area, signed by
# the class raster). Same terrain input and options otherwise; gates and the visible-waterline metric against v10.
set -uo pipefail
W="/c/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
PY="/c/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe"
N=E:/DayZ-Baltic-Build/v30-v10
X=E:/DayZ-Baltic-Build/v30-v10-exp-sd20
CONT=$N/design/contour_lakes.geojson
export PYTHONUTF8=1
WW="C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
export PYTHONPATH="$WW/tools/terrain;$WW/tools/navigation;$WW/tools/water"
WINPID=$(cat /proc/$$/winpid)
powershell.exe -NoProfile -Command "(Get-Process -Id $WINPID).PriorityClass='BelowNormal'" > /dev/null
[ -e $X ] && { echo "$X exists"; exit 1; }
mkdir -p $X
t0=$(date +%s); step() { echo "[$(( $(date +%s) - t0 )) s] $*" | tee -a $X/exp.log; }
step "inland pass, outline from step 20 sd"
"$PY" "$W/tools/terrain/profile_inland_v30.py" --terrain $N/v6/terrain_causeway.npz --out $X/inland \
    --channels $N/24 --bed-floor 1.0 --bed-min-depth 0.30 --outline-sd $N/20/sd_polish.npz --outline-sd-classes 2,5,7 \
    --low-water-bank --low-water-bank-min 1.0 > $X/inland.log 2>&1 || { step "inland FAILED"; exit 1; }
T=$X/inland/terrain_inland.npz
step "gates"
"$PY" "$W/tools/terrain/verify_terrain_v30.py" $T --sea-cut 0.51 --low-water-bank-min 1.0 > $X/verify.json 2> $X/verify.err || step "verify exit $?"
"$PY" "$W/tools/terrain/verify_roads_v30.py" "$T::heights" "$T::water" --json $X/roads.json > $X/roads.log 2>&1 || step "roads exit $?"
"$PY" "$W/tools/terrain/verify_channel_reaches_v30.py" $T $N/24 0.51 $X/channel-reaches.json > $X/reaches.log 2>&1 || step "reaches exit $?"
step "visible waterline metric"
"$PY" "$W/tools/water/audit_waterline_v30.py" --design $N/design --contour "$CONT" \
    --terrain "v10=$N/inland/terrain_inland.npz" --terrain "exp=$T" --json $X/waterline-metric.json > $X/waterline.log 2>&1 || step "waterline exit $?"
step "done"

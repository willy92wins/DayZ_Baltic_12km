#!/usr/bin/env bash
# Depth variants of the inland pass on the v10 inputs (as v10b, step-20 design sd), to compare against v10b and the
# first slope set: A = steeper slopes, B = first slopes with streams on the design outline too. Gates, roads, the
# visible waterline, the depth census and the depth on the river and stream axes for each.
set -uo pipefail
W="/c/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
PY="/c/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe"
SP="$(cd "$(dirname "$0")" && pwd -W)"
N10=E:/DayZ-Baltic-Build/v30-v10
N10B=E:/DayZ-Baltic-Build/v30-v10b
V=E:/DayZ-Baltic-Build/v30-v11-verify
export PYTHONUTF8=1
WW="C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
export PYTHONPATH="$WW/tools/terrain;$WW/tools/navigation;$WW/tools/water"
WINPID=$(cat /proc/$$/winpid)
powershell.exe -NoProfile -Command "(Get-Process -Id $WINPID).PriorityClass='BelowNormal'" > /dev/null
variant() {
    local name=$1 slopes=$2 classes=$3
    rm -rf $V/inland-$name
    "$PY" "$W/tools/terrain/profile_inland_v30.py" --terrain $N10/v6/terrain_causeway.npz --out $V/inland-$name --channels $N10/24 \
        --bed-floor 1.0 --bed-min-depth 0.30 --outline-sd $N10/20/sd_polish.npz --outline-sd-classes $classes \
        --low-water-bank --low-water-bank-min 1.0 --slope-by-class "$slopes" --slope-ref 4.0 > $V/inland-$name.log 2>&1 \
        || { echo "$name inland exit $?"; return; }
    local T=$V/inland-$name/terrain_inland.npz
    "$PY" "$W/tools/terrain/verify_terrain_v30.py" $T --sea-cut 0.51 --low-water-bank-min 1.0 > $V/verify-$name.json 2> $V/verify-$name.err
    "$PY" "$W/tools/terrain/verify_roads_v30.py" "$T::heights" "$T::water" --json $V/roads-$name.json > $V/roads-$name.log 2>&1
    "$PY" "$SP/depth_census.py" $T $name > $V/depth-$name.json 2> /dev/null
    "$PY" "$W/tools/water/audit_waterline_v30.py" --design $N10/design --contour "$N10/design/contour_lakes.geojson" \
        --terrain "$name=$T" --json $V/waterline-$name.json > $V/waterline-$name.log 2>&1
    echo "$name done"
}
variant C "2:0.25,5:0.4,6:0.35,7:0.25" 2,5,6,7 &
wait
echo "done variants"

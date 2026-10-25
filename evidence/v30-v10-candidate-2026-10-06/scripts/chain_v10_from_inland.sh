#!/usr/bin/env bash
# Candidate v10 (Guillermo, 06-10): the v9 chain on the design whose lakes, ponds and river bodies were smoothed along
# their rings (sigma 12 m, shift <= 4 m, contacts and Narva kept), lakes 047 and 107 kept whole at the border, the v9
# level list as the signed list, the inland shore pass on the vector outline (lakes, ponds, rivers; streams keep the
# raster outline) with the low-water bank rule, smooth land-cover boundaries, then gates, package, audits and the
# visible-waterline metric against v9. One step after another; stops at the first failure. Low priority.
set -uo pipefail
W="/c/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
M="C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev"
PY="/c/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe"
SPD="$(cd "$(dirname "$0")" && pwd -W)"
N=E:/DayZ-Baltic-Build/v30-v10
N9=E:/DayZ-Baltic-Build/v30-redesign
B=E:/DayZ-Baltic-Build
NAT="$M/tests/regional_outline_v1/reference.npz"
CHAN="10530,4150;10531,4176;10525,4205;10524,4248;10540,4285;10580,4310;10603,4338;10620,4360"
export PYTHONUTF8=1
WW="C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
export PYTHONPATH="$WW/tools/terrain;$WW/tools/navigation;$WW/tools/water"
WINPID=$(cat /proc/$$/winpid)
powershell.exe -NoProfile -Command "(Get-Process -Id $WINPID).PriorityClass='BelowNormal'" > /dev/null
mkdir -p $N
t0=$(date +%s); step() { echo "[$(( $(date +%s) - t0 )) s] $*" | tee -a $N/chain.log; }
run() {
    local label=$1 log=$2; shift 2
    "$@" > "$log" 2>&1; local rc=$?
    if [ $rc -ne 0 ]; then echo "  $label FAILED (exit $rc), see $log" | tee -a $N/chain.log; exit $rc; fi
}
soft() {
    local label=$1 log=$2; shift 2
    "$@" > "$log" 2>&1 || echo "  $label exit $?" | tee -a $N/chain.log
}
CONT=$N/design/contour_lakes.geojson
echo "--- resumed at the inland pass (banks at the highest adjacent level) ---" | tee -a $N/chain.log
rm -rf $N/inland $N/surface $N/package $N/audit-v10-085 $N/census $N/verify-v10.json $N/verify-v10.err $N/roads-v10.json $N/channel-reaches.json $N/shore_failure_census_v10.json $N/shore_failure_map_v10.png $N/waterline-metric-v10.json $N/waterline-metric-v9.json
step "inland shores and beds (vector outline for lakes, ponds and rivers; low-water banks)"
run inland $N/inland.log "$PY" "$W/tools/terrain/profile_inland_v30.py" --terrain $N/v6/terrain_causeway.npz --out $N/inland \
    --channels $N/24 --bed-floor 1.0 --bed-min-depth 0.30 --outline-sd $N/22/sd_shape.npz --outline-sd-classes 2,5,7 \
    --low-water-bank --low-water-bank-min 1.0
T=$N/inland/terrain_inland.npz
step "gates"
"$PY" "$W/tools/terrain/verify_terrain_v30.py" $T --sea-cut 0.51 --low-water-bank-min 1.0 > $N/verify-v10.json 2> $N/verify-v10.err || echo "  verify_terrain exit $?" | tee -a $N/chain.log
soft roads $N/roads-v10.log "$PY" "$W/tools/terrain/verify_roads_v30.py" "$T::heights" "$T::water" --json $N/roads-v10.json
soft reaches $N/channel-reaches.log "$PY" "$W/tools/terrain/verify_channel_reaches_v30.py" $T $N/24 0.51 $N/channel-reaches.json
step "surface (smooth land cover)"
run surface $N/surface.log "$PY" "$W/tools/terrain/build_surface_v30.py" $T $N/surface --workers 4 --bed-tone depth-all \
    --bed-surface gravel --shore-ring flowing --landcover smooth --landcover-sigma 1.0
step "package (OutsideTerrain with synthesis)"
env -u PYTHONPATH powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$W")\\tools\\terrain\\build_v30_package.ps1" \
    -Build "$(cygpath -w $N/package)" -Terrain "$(cygpath -w $T)" -WaterSource "$(cygpath -w $N/24/water)" \
    -Layers "$(cygpath -w $N/surface)" -OutsideSynth > $N/package-run.log 2>&1
grep -q "Built:" $N/package-run.log || { echo "  package FAILED, see $N/package-run.log" | tee -a $N/chain.log; exit 1; }
step "audits"
soft audit $N/audit-v10-085.log "$PY" "$W/tools/water/audit_visible_water_v30.py" --terrain $T --out $N/audit-v10-085 \
    --sea-level 0.85 --sea-cut 0.51 --channels $N/24 --water-v3 "$(cygpath -w $N/design/water_v3.geojson)" \
    --streams "$(cygpath -w $N/design/streams_candidates.geojson)" --contour "$(cygpath -w $CONT)"
soft census $N/census.log "$PY" "$W/tools/water/census_perched_water_v30.py" --terrain $T --out $N/census
soft shore-census $N/shore-census.log "$PY" "$SPD/shore_failure_census.py" $N/v6/terrain_causeway.npz $T $N/24 \
    $N/shore_failure_census_v10.json $N/shore_failure_map_v10.png v10
soft waterline-v10 $N/waterline-v10.log "$PY" "$W/tools/water/audit_waterline_v30.py" --design $N/design --contour "$CONT" \
    --terrain "v10=$T" --terrain "v10-step25=$N/v6/terrain_causeway.npz" --json $N/waterline-metric-v10.json
soft waterline-v9 $N/waterline-v9.log "$PY" "$W/tools/water/audit_waterline_v30.py" --design $N9/design \
    --terrain "v9=$N9/inland/terrain_inland.npz" --json $N/waterline-metric-v9.json
step "done v10"

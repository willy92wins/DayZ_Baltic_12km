#!/usr/bin/env bash
# Candidate v10b (06-10): v10 with the inland shore pass reading the builder's vector signed distance (step 20: distance
# to the smoothed design rings, sign by point-in-polygon) instead of the step-22 outline, which re-smooths the rings
# without keeping area (small ponds shrink by up to 4 m) and signs the distance by the class raster, so its zero line
# can only cross the class-change edges and the shore copies the 6 m staircase. Upstream steps are v10's, unchanged.
# Then gates, surface, package, audits and the visible-waterline metric against v10. Stops at the first failure.
set -uo pipefail
W="/c/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
PY="/c/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe"
SPD="$W/evidence/v30-v10-candidate-2026-10-06/scripts"
N=E:/DayZ-Baltic-Build/v30-v10
V=E:/DayZ-Baltic-Build/v30-v10b
X=E:/DayZ-Baltic-Build/v30-v10-exp-sd20
CONT=$N/design/contour_lakes.geojson
export PYTHONUTF8=1
WW="C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
export PYTHONPATH="$WW/tools/terrain;$WW/tools/navigation;$WW/tools/water"
WINPID=$(cat /proc/$$/winpid)
powershell.exe -NoProfile -Command "(Get-Process -Id $WINPID).PriorityClass='BelowNormal'" > /dev/null
[ -e $V ] && { echo "$V exists"; exit 1; }
mkdir -p $V
t0=$(date +%s); step() { echo "[$(( $(date +%s) - t0 )) s] $*" | tee -a $V/chain.log; }
run() {
    local label=$1 log=$2; shift 2
    "$@" > "$log" 2>&1; local rc=$?
    if [ $rc -ne 0 ]; then echo "  $label FAILED (exit $rc), see $log" | tee -a $V/chain.log; exit $rc; fi
}
soft() {
    local label=$1 log=$2; shift 2
    "$@" > "$log" 2>&1 || echo "  $label exit $?" | tee -a $V/chain.log
}
step "inland shores and beds (outline: step 20 vector sd for lakes, ponds and rivers; low-water banks)"
run inland $V/inland.log "$PY" "$W/tools/terrain/profile_inland_v30.py" --terrain $N/v6/terrain_causeway.npz --out $V/inland \
    --channels $N/24 --bed-floor 1.0 --bed-min-depth 0.30 --outline-sd $N/20/sd_polish.npz --outline-sd-classes 2,5,7 \
    --low-water-bank --low-water-bank-min 1.0
T=$V/inland/terrain_inland.npz
a=$(sha256sum $T | cut -c1-64); b=$(sha256sum $X/inland/terrain_inland.npz | cut -c1-64)
step "terrain sha256 $a (experiment $b): $([ "$a" = "$b" ] && echo same || echo DIFFERENT)"
step "gates"
"$PY" "$W/tools/terrain/verify_terrain_v30.py" $T --sea-cut 0.51 --low-water-bank-min 1.0 > $V/verify-v10b.json 2> $V/verify-v10b.err || echo "  verify_terrain exit $?" | tee -a $V/chain.log
soft roads $V/roads-v10b.log "$PY" "$W/tools/terrain/verify_roads_v30.py" "$T::heights" "$T::water" --json $V/roads-v10b.json
soft reaches $V/channel-reaches.log "$PY" "$W/tools/terrain/verify_channel_reaches_v30.py" $T $N/24 0.51 $V/channel-reaches.json
step "surface (smooth land cover)"
run surface $V/surface.log "$PY" "$W/tools/terrain/build_surface_v30.py" $T $V/surface --workers 4 --bed-tone depth-all \
    --bed-surface gravel --shore-ring flowing --landcover smooth --landcover-sigma 1.0
step "package (OutsideTerrain with synthesis)"
env -u PYTHONPATH powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$W")\\tools\\terrain\\build_v30_package.ps1" \
    -Build "$(cygpath -w $V/package)" -Terrain "$(cygpath -w $T)" -WaterSource "$(cygpath -w $N/24/water)" \
    -Layers "$(cygpath -w $V/surface)" -OutsideSynth > $V/package-run.log 2>&1
grep -q "Built:" $V/package-run.log || { echo "  package FAILED, see $V/package-run.log" | tee -a $V/chain.log; exit 1; }
step "audits"
soft audit $V/audit-v10b-085.log "$PY" "$W/tools/water/audit_visible_water_v30.py" --terrain $T --out $V/audit-v10b-085 \
    --sea-level 0.85 --sea-cut 0.51 --channels $N/24 --water-v3 "$(cygpath -w $N/design/water_v3.geojson)" \
    --streams "$(cygpath -w $N/design/streams_candidates.geojson)" --contour "$(cygpath -w $CONT)"
soft census $V/census.log "$PY" "$W/tools/water/census_perched_water_v30.py" --terrain $T --out $V/census
soft shore-census $V/shore-census.log "$PY" "$SPD/shore_failure_census.py" $N/v6/terrain_causeway.npz $T $N/24 \
    $V/shore_failure_census_v10b.json $V/shore_failure_map_v10b.png v10b
soft waterline $V/waterline.log "$PY" "$W/tools/water/audit_waterline_v30.py" --design $N/design --contour "$CONT" \
    --terrain "v10b=$T" --terrain "v10=$N/inland/terrain_inland.npz" --json $V/waterline-metric-v10b.json
step "done v10b"

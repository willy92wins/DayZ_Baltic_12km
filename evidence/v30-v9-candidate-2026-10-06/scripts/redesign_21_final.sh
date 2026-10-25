#!/usr/bin/env bash
# Candidate v9 (plan steps 2 and 3): chain steps 21-25 on the smoothed design with the level list derived by rule
# (levels/bodies-rule.json), then the coast (v5 flags), the causeway, one inland shore pass (profile_inland_v30.py,
# beds at 1.0 m with 0.30 m of water at least), the gates, the surface (--bed-tone depth-all), the package with
# OutsideTerrain and synthesis, the visible-water audit, the census and the shore-defect census against v8.
# Sequential and low priority: the box is shared.
set -uo pipefail
W="/c/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
WWIN="C:\\Users\\guill\\OneDrive\\Documentos\\DayZ Projects\\DayZ_Baltic_12km_dev\\.claude\\worktrees\\codex-handoff-review-74f290"
PY="/c/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe"
SPD="$(cd "$(dirname "$0")" && pwd -W)"
N=E:/DayZ-Baltic-Build/v30-redesign
B=E:/DayZ-Baltic-Build
export PYTHONUTF8=1
WW="C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
export PYTHONPATH="$WW/tools/terrain;$WW/tools/navigation;$WW/tools/water"
WINPID=$(cat /proc/$$/winpid)
powershell.exe -NoProfile -Command "(Get-Process -Id $WINPID).PriorityClass='BelowNormal'" > /dev/null
t0=$(date +%s); step() { echo "[$(( $(date +%s) - t0 )) s] $*" | tee -a $N/chain.log; }
run() {
    local label=$1 log=$2; shift 2
    "$@" > "$log" 2>&1; local rc=$?
    if [ $rc -ne 0 ]; then echo "  $label FAILED (exit $rc), see $log" | tee -a $N/chain.log; exit $rc; fi
}
soft() {  # gates and audits: a non-zero exit is a finding, not a stop
    local label=$1 log=$2; shift 2
    "$@" > "$log" 2>&1 || echo "  $label exit $?" | tee -a $N/chain.log
}
step "21 relevel (list by rule)"
run 21 $N/21.log "$PY" "$W/tools/terrain/relevel_bodies_v30.py" --terrain $N/20/terrain_pilot.npz --out $N/21 \
    --river Luga_0:4440:3.14 --with-river-box 10150,3700,10700,4600:3.9 --bodies $N/levels/bodies-rule.json --design $N/design
step "22 shape"
run 22 $N/22.log "$PY" "$W/tools/terrain/smooth_shore_outline_v30.py" --terrain $N/21/terrain_relevel.npz --sd $N/20/sd_polish.npz --out $N/22
step "23 patch"
run 23 $N/23.log "$PY" "$W/tools/water/patch_water_tiles_v30.py" --water $N/17-water --terrain-old $N/16/terrain_pilot.npz \
    --terrain-new $N/22/terrain_shape.npz --sea-cut-old 0.51 --sea-cut-new 0.51 --out $N/23-water
step "24 channel fit"
run 24 $N/24.log "$PY" "$W/tools/water/fit_channel_pieces_v30.py" --terrain $N/22/terrain_shape.npz --water $N/23-water \
    --library $B/v30-vanilla-channel-pilot/library.json --overlap-all --no-pad --sea-cut 0.51 --out $N/24 --design $N/design
step "25 shore fit"
run 25 $N/25.log "$PY" "$W/tools/terrain/fit_shore_crossings_v30.py" --terrain $N/24/terrain_pilot.npz --channels $N/24 --sea-cut 0.51 \
    --reg 0.05 --max-iter 3000 --dry-raise-max 0.4 --levee-cap 0.15 --corridor-margin 0 --sd-override $N/22/sd_shape.npz \
    --narva-core-m 0 --free-corridor-box 10150,3700,10700,4600 --water-v30 $N/terrain_v30/water_v30.npz --out $N/25
step "v5 coast"
run v5 $N/v5.log "$PY" "$W/tools/terrain/profile_coast_v30.py" --terrain $N/25/terrain_shore.npz --out $N/v5 --floor 1.60 --raise-land
step "v6 causeway"
run v6 $N/v6.log "$PY" "$W/tools/terrain/shape_causeways_v30.py" --terrain $N/v5/terrain_coast.npz --out $N/v6
step "inland shores and beds (one pass)"
run inland $N/inland.log "$PY" "$W/tools/terrain/profile_inland_v30.py" --terrain $N/v6/terrain_causeway.npz --out $N/inland \
    --channels $N/24 --bed-floor 1.0 --bed-min-depth 0.30
T=$N/inland/terrain_inland.npz
step "gates"
"$PY" "$W/tools/terrain/verify_terrain_v30.py" $T --sea-cut 0.51 > $N/verify-v9.json 2> $N/verify-v9.err || echo "  verify_terrain exit $?" | tee -a $N/chain.log
soft roads $N/roads-v9.log "$PY" "$W/tools/terrain/verify_roads_v30.py" "$T::heights" "$T::water" --json $N/roads-v9.json
soft reaches $N/channel-reaches.log "$PY" "$W/tools/terrain/verify_channel_reaches_v30.py" $T $N/24 0.51 $N/channel-reaches.json
step "surface"
run surface $N/surface.log "$PY" "$W/tools/terrain/build_surface_v30.py" $T $N/surface --workers 4 --bed-tone depth-all \
    --bed-surface gravel --shore-ring flowing
step "package (new water, OutsideTerrain with synthesis)"
env -u PYTHONPATH powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$WWIN\\tools\\terrain\\build_v30_package.ps1" \
    -Build "$(cygpath -w $N/package)" -Terrain "$(cygpath -w $T)" -WaterSource "$(cygpath -w $N/24/water)" \
    -Layers "$(cygpath -w $N/surface)" -OutsideSynth > $N/package-run.log 2>&1
grep -q "Built:" $N/package-run.log || { echo "  package FAILED, see $N/package-run.log" | tee -a $N/chain.log; exit 1; }
step "audit, census, shore defects"
soft audit $N/audit-v9-085.log "$PY" "$W/tools/water/audit_visible_water_v30.py" --terrain $T --out $N/audit-v9-085 \
    --sea-level 0.85 --sea-cut 0.51 --channels $N/24 --water-v3 "$(cygpath -w $N/design/water_v3.geojson)" \
    --streams "$(cygpath -w $N/design/streams_candidates.geojson)"
soft census $N/census.log "$PY" "$W/tools/water/census_perched_water_v30.py" --terrain $T --out $N/census
soft shore-census $N/shore-census.log "$PY" "$SPD/shore_failure_census.py" $N/v6/terrain_causeway.npz $T $N/24 \
    $N/shore_failure_census_v9.json $N/shore_failure_map_v9.png v9
step "done v9"

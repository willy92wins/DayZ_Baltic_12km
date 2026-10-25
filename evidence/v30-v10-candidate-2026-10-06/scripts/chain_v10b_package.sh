#!/usr/bin/env bash
# Resume of chain_v10b.sh at the package. The first try failed before writing anything: with -WaterSource the package
# script makes the DZ/bin/core junctions inside the water folder, and v10's package had already left them in
# v30-v10/24/water/source (New-Item refused the existing DZ junction; nothing was removed, P:\DZ checked). The water does
# not change from v10 to v10b (the inland pass moves no class and no level, so the cell planes and pieces are v10's),
# so the package reuses v10's water build with -Pieces: its baltic_water_v30.pbo (c00e5687) and binarized models.
set -uo pipefail
W="/c/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
PY="/c/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe"
SPD="$W/evidence/v30-v10-candidate-2026-10-06/scripts"
N=E:/DayZ-Baltic-Build/v30-v10
V=E:/DayZ-Baltic-Build/v30-v10b
CONT=$N/design/contour_lakes.geojson
T=$V/inland/terrain_inland.npz
export PYTHONUTF8=1
WW="C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
export PYTHONPATH="$WW/tools/terrain;$WW/tools/navigation;$WW/tools/water"
WINPID=$(cat /proc/$$/winpid)
powershell.exe -NoProfile -Command "(Get-Process -Id $WINPID).PriorityClass='BelowNormal'" > /dev/null
t0=$(date +%s); step() { echo "[$(( $(date +%s) - t0 )) s] $*" | tee -a $V/chain.log; }
soft() {
    local label=$1 log=$2; shift 2
    "$@" > "$log" 2>&1 || echo "  $label exit $?" | tee -a $V/chain.log
}
echo "--- resumed at the package, water reused from v10 with -Pieces ---" | tee -a $V/chain.log
[ -e $V/package ] && { echo "$V/package exists" | tee -a $V/chain.log; exit 1; }
mv $V/package-run.log $V/package-run-first-try.log
step "package (OutsideTerrain with synthesis; water of v10)"
env -u PYTHONPATH powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$W")\\tools\\terrain\\build_v30_package.ps1" \
    -Build "$(cygpath -w $V/package)" -Terrain "$(cygpath -w $T)" -Pieces "$(cygpath -w $N/24/water)" \
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

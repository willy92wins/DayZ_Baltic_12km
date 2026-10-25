#!/usr/bin/env bash
# Candidate v12 (Guillermo, 07-10): the v11 with the beds of the navigable rivers raised to the 1.0 m floor of the rest
# of the inland water (profile_inland_v30.py --bed-floor-navigable): the engine sea showed through the navigable
# rivers as swell, foam and colour patches (BALTIC-018). Every navigable vertex keeps at least 1.0 m of water: the full
# floor where the level allows it, level - 1.0 m on the lower reaches towards the sea, so the bed has no step where the
# level crosses 2.0 m (a first run with a cut there, kept in v30-v12-stepbed, left a jump of 3-8 m in the bed). The
# Narva zone is left out, as the inland pass leaves it. Everything up to the v6 causeway is the v11's, and so is the water
# (the inland pass moves no class and no level, so the cell planes and the pieces are the v11's: -Pieces, as v10b did).
# This reruns the inland pass and what follows it: the check that only navigable heights changed and only upwards,
# gates, surface, package and audits. One step after another; stops at the first failure.
set -uo pipefail
W="/c/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
PY="/c/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe"
SPD="$(cd "$(dirname "$0")" && pwd -W)"
N11=E:/DayZ-Baltic-Build/v30-v11
N=E:/DayZ-Baltic-Build/v30-v12
SLOPES="2:0.25,5:0.4,6:0.35,7:0.25"
CONT=$N11/design/contour_lakes.geojson
export PYTHONUTF8=1
WW="C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
export PYTHONPATH="$WW/tools/terrain;$WW/tools/navigation;$WW/tools/water"
WINPID=$(cat /proc/$$/winpid)
powershell.exe -NoProfile -Command "(Get-Process -Id $WINPID).PriorityClass='BelowNormal'" > /dev/null
[ -e $N ] && { echo "$N exists"; exit 1; }
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
step "inland shores and beds (v11 parameters; navigable beds to the 1.0 m floor)"
run inland $N/inland.log "$PY" "$W/tools/terrain/profile_inland_v30.py" --terrain $N11/v6/terrain_causeway.npz --out $N/inland \
    --channels $N11/24 --bed-floor 1.0 --bed-min-depth 0.30 --outline-sd $N11/20/sd_polish.npz --outline-sd-classes 2,5,6,7 \
    --low-water-bank --low-water-bank-min 1.0 --slope-by-class "$SLOPES" --slope-ref 4.0 \
    --bed-floor-navigable --bed-floor-navigable-min-depth 1.0
T=$N/inland/terrain_inland.npz
step "check: against the v11, only navigable heights changed, and only upwards"
run check $N/check-v12-vs-v11.log "$PY" "$SPD/check_v12_vs_v11.py" $N11/inland/terrain_inland.npz $T $N/check-v12-vs-v11.json
step "gates"
"$PY" "$W/tools/terrain/verify_terrain_v30.py" $T --sea-cut 0.51 --low-water-bank-min 1.0 > $N/verify-v12.json 2> $N/verify-v12.err || echo "  verify_terrain exit $?" | tee -a $N/chain.log
soft roads $N/roads-v12.log "$PY" "$W/tools/terrain/verify_roads_v30.py" "$T::heights" "$T::water" --json $N/roads-v12.json
soft reaches $N/channel-reaches.log "$PY" "$W/tools/terrain/verify_channel_reaches_v30.py" $T $N11/24 0.51 $N/channel-reaches.json
step "surface (smooth land cover)"
run surface $N/surface.log "$PY" "$W/tools/terrain/build_surface_v30.py" $T $N/surface --workers 4 --bed-tone depth-all \
    --bed-surface gravel --shore-ring flowing --landcover smooth --landcover-sigma 1.0
step "package (OutsideTerrain with synthesis; water of the v11 with -Pieces)"
env -u PYTHONPATH powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$W")\\tools\\terrain\\build_v30_package.ps1" \
    -Build "$(cygpath -w $N/package)" -Terrain "$(cygpath -w $T)" -Pieces "$(cygpath -w $N11/24/water)" \
    -Layers "$(cygpath -w $N/surface)" -OutsideSynth > $N/package-run.log 2>&1
grep -q "Built:" $N/package-run.log || { echo "  package FAILED, see $N/package-run.log" | tee -a $N/chain.log; exit 1; }
step "audits"
soft audit $N/audit-v12-085.log "$PY" "$W/tools/water/audit_visible_water_v30.py" --terrain $T --out $N/audit-v12-085 \
    --sea-level 0.85 --sea-cut 0.51 --channels $N11/24 --water-v3 "$(cygpath -w $N11/design/water_v3.geojson)" \
    --streams "$(cygpath -w $N11/design/streams_candidates.geojson)" --contour "$(cygpath -w $CONT)"
soft navigable $N/navigable-below-sea.log "$PY" "$W/evidence/baltic-018-navegables-2026-10-07/scripts/navigable_below_sea.py" $N/inland
step "done v12"

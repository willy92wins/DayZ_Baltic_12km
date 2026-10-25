#!/usr/bin/env bash
# Resume of the redesign chain at step 13 (the frozen points that the smoothed courses moved are left out and
# reported), then 14, 16, 18, 20, the level list derived by rule on the step-20 terrain, and the water patches 15 and
# 17 once the water branch of redesign_05_20.sh (10, pack, 12) has finished. Low priority; the box is shared.
set -uo pipefail
W="/c/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
M="C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev"
PY="/c/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe"
SPD="$(cd "$(dirname "$0")" && pwd -W)"
N=E:/DayZ-Baltic-Build/v30-redesign
B=E:/DayZ-Baltic-Build
NAT="$M/tests/regional_outline_v1/reference.npz"
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
step "13 wave margins (resume, moved frozen points skipped)"
run 13 $N/13.log "$PY" "$W/tools/terrain/deepen_wave_margins_v30.py" --source $N/11/terrain_v30.npz --source-sha any \
    --reference $B/v30-water-temporal-v2/reference.json \
    --parent-reference $B/v30-continuity-dedup-package/runtime-fixture/reference.json \
    --design $N/design --nature "$NAT" --out $N/13 --constrained --skip-moved-points
step "14 river mouths"
run 14 $N/14.log "$PY" "$W/tools/water/profile_river_mouths_v30.py" --terrain $N/13/terrain_v30.npz --out $N/14
step "16 Narva moats"
run 16 $N/16.log "$PY" "$W/tools/terrain/narva_moats_v30.py" $N/14/terrain_mouths.npz $N/16
step "18 Narva V29 outline"
mkdir -p $N/18
run 18 $N/18.log "$PY" "$W/tools/terrain/narva_v29_outline_v30.py" $N/16/terrain_pilot.npz $N/18/sd_v29.npz --water-v30 $N/terrain_v30/water_v30.npz
step "20 Luga polish"
run 20 $N/20.log "$PY" "$W/tools/terrain/polish_luga_head_v30.py" --terrain $N/16/terrain_pilot.npz --sd-base $N/18/sd_v29.npz --out $N/20 \
    --design $N/design \
    --channel "10530,4150;10531,4176;10525,4205;10524,4248;10540,4285;10580,4310;10603,4338;10620,4360" \
    --channel-width 30 --bed-depth 3.05
step "levels: classification of the step-20 terrain (v2 parameters) and the list by rule"
run classify $N/levels-classify.log "$PY" "$W/tools/water/classify_perched_water_v30.py" --terrain $N/20/terrain_pilot.npz \
    --out $N/levels/classify --root "$(cygpath -w $N/root)" --big-area 1500000 --perched-min 0.3 --dike-lower 1.0 \
    --ring-margin 0.05 --ring-in 12 --ring-out 36 \
    --channel "10530,4150;10531,4176;10525,4205;10524,4248;10540,4285;10580,4310;10603,4338" --channel-width 20
run derive $N/levels-derive.log "$PY" "$W/tools/water/derive_signed_levels_v30.py" --terrain $N/20/terrain_pilot.npz \
    --classification $N/levels/classify/classification.json --signed $B/v30-v3/bodies-v3b.json \
    --out-list $N/levels/bodies-rule.json --out-report $N/levels/report.json
cat $N/levels-derive.log | tee -a $N/chain.log
step "waiting for the water branch"
until grep -q "water branch done\|10 FAILED\|10pack FAILED\|12 FAILED" $N/chain.log; do sleep 20; done
grep -q "water branch done" $N/chain.log || { echo "  water branch FAILED" | tee -a $N/chain.log; exit 1; }
step "15 patch"
run 15 $N/15.log "$PY" "$W/tools/water/patch_water_tiles_v30.py" --water $N/12-water --terrain-old $N/13/terrain_v30.npz \
    --terrain-new $N/14/terrain_mouths.npz --sea-cut-old 0.80 --sea-cut-new 0.51 --out $N/15-water
step "17 patch"
run 17 $N/17.log "$PY" "$W/tools/water/patch_water_tiles_v30.py" --water $N/15-water --terrain-old $N/14/terrain_mouths.npz \
    --terrain-new $N/16/terrain_pilot.npz --sea-cut-old 0.51 --sea-cut-new 0.51 --out $N/17-water
step "done 13-20"

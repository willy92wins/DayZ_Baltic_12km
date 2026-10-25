#!/usr/bin/env bash
# Chain steps 5-20 on the smoothed design with the map-border rule (plan step 2), same tools and parameters as the
# replay (evidence/v30-chain-replay-2026-10-06), source hashes not pinned. The water branch (10, pack, 12) runs
# beside the terrain branch (11, 13, 14, 16, 18, 20); the patches 15 and 17 follow both. Low priority; the box is
# shared.
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
run() {  # label log command...: stop the chain on failure
    local label=$1 log=$2; shift 2
    "$@" > "$log" 2>&1; local rc=$?
    if [ $rc -ne 0 ]; then echo "  $label FAILED (exit $rc), see $log" | tee -a $N/chain.log; exit $rc; fi
}
same() {  # label new archived: whether a product equals the archived one
    a=$(sha256sum "$2" | cut -c1-16); b=$(sha256sum "$3" | cut -c1-16)
    if [ "$a" = "$b" ]; then echo "  SAME $1 $a" | tee -a $N/chain.log; else echo "  NEW  $1 $a (archived $b)" | tee -a $N/chain.log; fi
}
step "05 terrain"
cd $N && run 05 $N/05-terrain.log "$PY" "$W/tools/terrain/build_v30.py" $N/terrain_v30 $N/terrain_v30
step "06 Luga bed fix"
run 06 $N/06.log "$PY" "$W/tools/terrain/audit_fairway_triangles_v30.py" --terrain $N/terrain_v30/terrain_v30.npz --design $N/design \
    --out $N/06-evidence --candidate $N/06/terrain_v30.npz --max-lowering-m 1.55
same "06 corridors" $N/06-evidence/corridors.geojson "$W/evidence/v30-offline-followup-2026-10-02/corridors.geojson"
step "07 delta"
run 07 $N/07.log "$PY" "$W/tools/terrain/repair_delta_fairways_v30.py" --source $N/06/terrain_v30.npz --source-sha any --out $N/07 --evidence $N/07-evidence
same "07 axes" $N/07-evidence/axes-corridors.geojson "$W/evidence/v30-delta-fairways-2026-10-02/axes-corridors.geojson"
step "08 shore finish"
run 08 $N/08.log "$PY" "$W/tools/terrain/finish_shores_v30.py" --source $N/07/terrain_v30.npz --source-sha any --water-v30 $N/terrain_v30/water_v30.npz \
    --nature "$NAT" --corridors $N/06-evidence/corridors.geojson $N/07-evidence/axes-corridors.geojson --out $N/08
step "09 Narva ponds"
run 09 $N/09.log "$PY" "$W/tools/terrain/restore_narva_ponds_v30.py" --source $N/08/terrain_v30.npz --source-sha any --design $N/design --nature "$NAT" --out $N/09
water_branch() {
    step "10 water pieces"
    run 10 $N/10.log "$PY" "$W/tools/water/build_water_pieces_v30.py" $N/09/terrain_v30.npz $N/10-water
    step "10 pack"
    run 10pack $N/10-pack.log powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$W")\tools\water\pack_water_v30.ps1" -Water "$(cygpath -w $N/10-water)"
    step "12 deduplication"
    run 12 $N/12.log "$PY" "$W/tools/water/deduplicate_water_v30.py" --source $N/10-water --pbo-sha any --manifest-sha any --out $N/12-water
    step "water branch done"
}
water_branch &
WPID=$!
step "11 small watercourses"
run 11 $N/11.log "$PY" "$W/tools/terrain/connect_small_watercourses_v30.py" --source $N/09/terrain_v30.npz --source-sha any --design $N/design --nature "$NAT" --out $N/11
step "13 wave margins"
run 13 $N/13.log "$PY" "$W/tools/terrain/deepen_wave_margins_v30.py" --source $N/11/terrain_v30.npz --source-sha any \
    --reference $B/v30-water-temporal-v2/reference.json \
    --parent-reference $B/v30-continuity-dedup-package/runtime-fixture/reference.json \
    --design $N/design --nature "$NAT" --out $N/13 --constrained
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
step "terrain branch done; waiting for the water branch"
wait $WPID || { echo "  water branch FAILED" | tee -a $N/chain.log; exit 1; }
step "15 patch"
run 15 $N/15.log "$PY" "$W/tools/water/patch_water_tiles_v30.py" --water $N/12-water --terrain-old $N/13/terrain_v30.npz \
    --terrain-new $N/14/terrain_mouths.npz --sea-cut-old 0.80 --sea-cut-new 0.51 --out $N/15-water
step "17 patch"
run 17 $N/17.log "$PY" "$W/tools/water/patch_water_tiles_v30.py" --water $N/15-water --terrain-old $N/14/terrain_mouths.npz \
    --terrain-new $N/16/terrain_pilot.npz --sea-cut-old 0.51 --sea-cut-new 0.51 --out $N/17-water
step "done 05-20"

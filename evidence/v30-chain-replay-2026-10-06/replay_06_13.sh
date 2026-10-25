#!/usr/bin/env bash
# Replay of the terrain chain steps 6-13 (Luga bed fix, delta, shore finish, Narva ponds, small watercourses, wave
# margins), each step on the previous step's replayed output, with the tools parametrized on 06-10. Every product is
# compared with the archived one by sha256. Low priority; the box is shared.
set -uo pipefail
W="/c/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
M="C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev"
PY="/c/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe"
P=E:/DayZ-Baltic-Build/v30-replay
B=E:/DayZ-Baltic-Build
NAT="$M/tests/regional_outline_v1/reference.npz"
export PYTHONUTF8=1
WINPID=$(cat /proc/$$/winpid)
powershell.exe -NoProfile -Command "(Get-Process -Id $WINPID).PriorityClass='BelowNormal'" > /dev/null
t0=$(date +%s); step() { echo "[$(( $(date +%s) - t0 )) s] $*" | tee -a $P/replay.log; }
cmp_sha() {  # label replayed archived
    a=$(sha256sum "$2" 2>/dev/null | cut -c1-16); b=$(sha256sum "$3" 2>/dev/null | cut -c1-16)
    if [ -n "$a" ] && [ "$a" = "$b" ]; then echo "  MATCH $1 $a" | tee -a $P/replay.log; else echo "  DIFF  $1 replay=$a archived=$b" | tee -a $P/replay.log; fi
}
step "06 Luga bed fix"
"$PY" "$W/tools/terrain/audit_fairway_triangles_v30.py" --terrain $P/terrain_v30/terrain_v30.npz --design $P/design \
    --out $P/06-evidence --candidate $P/06/terrain_v30.npz --max-lowering-m 1.55 > $P/06.log 2>&1 || echo "  06 exit $?" | tee -a $P/replay.log
cmp_sha "06 terrain" $P/06/terrain_v30.npz $B/v30-fairway-candidate-bounded/terrain_v30.npz
cmp_sha "06 corridors" $P/06-evidence/corridors.geojson "$W/evidence/v30-offline-followup-2026-10-02/corridors.geojson"
step "07 delta"
"$PY" "$W/tools/terrain/repair_delta_fairways_v30.py" --source $P/06/terrain_v30.npz --out $P/07 --evidence $P/07-evidence \
    > $P/07.log 2>&1 || echo "  07 exit $?" | tee -a $P/replay.log
cmp_sha "07 terrain" $P/07/terrain_v30.npz $B/v30-delta-candidate/terrain_v30.npz
cmp_sha "07 axes" $P/07-evidence/axes-corridors.geojson "$W/evidence/v30-delta-fairways-2026-10-02/axes-corridors.geojson"
step "08 shore finish"
"$PY" "$W/tools/terrain/finish_shores_v30.py" --source $P/07/terrain_v30.npz --water-v30 $P/terrain_v30/water_v30.npz \
    --nature "$NAT" --corridors $P/06-evidence/corridors.geojson $P/07-evidence/axes-corridors.geojson --out $P/08 \
    > $P/08.log 2>&1 || echo "  08 exit $?" | tee -a $P/replay.log
cmp_sha "08 terrain" $P/08/terrain_v30.npz $B/v30-shore-finish-corrected/terrain_v30.npz
step "09 Narva ponds"
"$PY" "$W/tools/terrain/restore_narva_ponds_v30.py" --source $P/08/terrain_v30.npz --design $P/design --nature "$NAT" \
    --out $P/09 > $P/09.log 2>&1 || echo "  09 exit $?" | tee -a $P/replay.log
cmp_sha "09 terrain" $P/09/terrain_v30.npz $B/v30-pond-recovery/terrain_v30.npz
step "11 small watercourses"
"$PY" "$W/tools/terrain/connect_small_watercourses_v30.py" --source $P/09/terrain_v30.npz --design $P/design \
    --nature "$NAT" --out $P/11 > $P/11.log 2>&1 || echo "  11 exit $?" | tee -a $P/replay.log
cmp_sha "11 terrain" $P/11/terrain_v30.npz $B/v30-watercourse-continuity/terrain_v30.npz
step "13 wave margins"
"$PY" "$W/tools/terrain/deepen_wave_margins_v30.py" --source $P/11/terrain_v30.npz \
    --reference $B/v30-water-temporal-v2/reference.json \
    --parent-reference $B/v30-continuity-dedup-package/runtime-fixture/reference.json \
    --design $P/design --nature "$NAT" --out $P/13 --constrained > $P/13.log 2>&1 || echo "  13 exit $?" | tee -a $P/replay.log
cmp_sha "13 terrain" $P/13/terrain_v30.npz $B/v30-wave-margin-constrained/terrain_v30.npz
step "done 06-13"

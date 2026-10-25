#!/usr/bin/env bash
# Replay of v5 (coast profile), v6 (causeway), v7d (lake shores and beds) and v8 (river shores and beds) on the
# replayed v3b terrain, each compared with the archived terrain by sha256.
set -uo pipefail
W="/c/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
PY="/c/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe"
P=E:/DayZ-Baltic-Build/v30-replay
B=E:/DayZ-Baltic-Build
export PYTHONUTF8=1
WINPID=$(cat /proc/$$/winpid)
powershell.exe -NoProfile -Command "(Get-Process -Id $WINPID).PriorityClass='BelowNormal'" > /dev/null
t0=$(date +%s); step() { echo "[$(( $(date +%s) - t0 )) s] $*" | tee -a $P/replay.log; }
cmp_sha() {
    a=$(sha256sum "$2" 2>/dev/null | cut -c1-16); b=$(sha256sum "$3" 2>/dev/null | cut -c1-16)
    if [ -n "$a" ] && [ "$a" = "$b" ]; then echo "  MATCH $1 $a" | tee -a $P/replay.log; else echo "  DIFF  $1 replay=$a archived=$b" | tee -a $P/replay.log; fi
}
step "v5 coast"
"$PY" "$W/tools/terrain/profile_coast_v30.py" --terrain $P/25/terrain_shore.npz --out $P/v5 --floor 1.60 --raise-land > $P/v5.log 2>&1 || echo "  v5 exit $?" | tee -a $P/replay.log
cmp_sha "v5 terrain" $P/v5/terrain_coast.npz $B/v30-v5/coast/terrain_coast.npz
step "v6 causeway"
"$PY" "$W/tools/terrain/shape_causeways_v30.py" --terrain $P/v5/terrain_coast.npz --out $P/v6 > $P/v6.log 2>&1 || echo "  v6 exit $?" | tee -a $P/replay.log
cmp_sha "v6 terrain" $P/v6/terrain_causeway.npz $B/v30-v6/causeway/terrain_causeway.npz
step "v7d lakes"
"$PY" "$W/tools/terrain/profile_lakes_v30.py" --terrain $P/v6/terrain_causeway.npz --out $P/v7d --bed-floor 1.0 \
    --bed-min-depth 0.30 --min-vertices 4 > $P/v7d.log 2>&1 || echo "  v7d exit $?" | tee -a $P/replay.log
cmp_sha "v7d terrain" $P/v7d/terrain_lakes.npz $B/v30-v7/lakes-b/terrain_lakes.npz
step "v8 rivers"
"$PY" "$W/tools/terrain/profile_rivers_v30.py" --terrain $P/v7d/terrain_lakes.npz --out $P/v8 --channels $P/24 \
    --bed-floor 1.0 --bed-min-depth 0.30 > $P/v8.log 2>&1 || echo "  v8 exit $?" | tee -a $P/replay.log
cmp_sha "v8 terrain" $P/v8/terrain_rivers.npz $B/v30-v8/rivers/terrain_rivers.npz
step "done v5-v8"

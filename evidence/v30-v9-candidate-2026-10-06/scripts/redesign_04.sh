#!/usr/bin/env bash
# Step 4 of the chain on the smoothed design, with the map-border rule (Guillermo, 06-10).
set -uo pipefail
W="/c/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
PY="/c/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe"
N=E:/DayZ-Baltic-Build/v30-redesign
export PYTHONUTF8=1
WINPID=$(cat /proc/$$/winpid)
powershell.exe -NoProfile -Command "(Get-Process -Id $WINPID).PriorityClass='BelowNormal'" > /dev/null
mkdir -p $N/terrain_v30
"$PY" "$W/tools/terrain/build_v30_water.py" $N/design $N/terrain_v30 --border-margin 60 --drop-border-water-km2 0.05 > $N/04-water.log 2>&1; echo "04 exit $?"

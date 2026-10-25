#!/usr/bin/env bash
# D4 defaults: step 4 on the replay design (96d4a7de), step 4 of v9 with its border flags (98067e22), step 20 on the
# replay (1c0a52fb, sd 11564fdb).
set -uo pipefail
W="/c/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
PY="/c/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe"
P=E:/DayZ-Baltic-Build/v30-replay
N=E:/DayZ-Baltic-Build/v30-redesign
V=E:/DayZ-Baltic-Build/v30-v10-verify
export PYTHONUTF8=1
WINPID=$(cat /proc/$$/winpid)
powershell.exe -NoProfile -Command "(Get-Process -Id $WINPID).PriorityClass='BelowNormal'" > /dev/null
mkdir -p $V/04a $V/04b $V/20
"$PY" "$W/tools/terrain/build_v30_water.py" $P/design $V/04a > $V/04a.log 2>&1
"$PY" "$W/tools/terrain/build_v30_water.py" $N/design $V/04b --border-margin 60 --drop-border-water-km2 0.05 > $V/04b.log 2>&1
rm -rf $V/20; "$PY" "$W/tools/terrain/polish_luga_head_v30.py" --terrain $P/16/terrain_pilot.npz --sd-base $P/18/sd_v29.npz --out $V/20 \
    --channel "10530,4150;10531,4176;10525,4205;10524,4248;10540,4285;10580,4310;10603,4338;10620,4360" \
    --channel-width 30 --bed-depth 3.05 > $V/20.log 2>&1
echo "04a $(sha256sum $V/04a/water_v30.npz | cut -c1-8) (expect 96d4a7de)"
echo "04b $(sha256sum $V/04b/water_v30.npz | cut -c1-8) (expect 98067e22)"
echo "20  $(sha256sum $V/20/terrain_pilot.npz | cut -c1-8) (expect 1c0a52fb) sd $(sha256sum $V/20/sd_polish.npz | cut -c1-8) (expect 11564fdb)"

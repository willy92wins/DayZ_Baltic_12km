#!/usr/bin/env bash
# Receipt of the GLM lanes E1 (rounded river ends) and P4 (per-class shore slope), installed in the worktree:
# defaults byte-identical to v10 (step-4 water) and v10b (inland terrain aa1c093c), selftests, then the new options
# on the same inputs: river-end counts, and the depth, waterline, gates and roads of the steeper profile against v10b.
set -uo pipefail
W="/c/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
PY="/c/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe"
SP="$(cd "$(dirname "$0")" && pwd -W)"
N10=E:/DayZ-Baltic-Build/v30-v10
N10B=E:/DayZ-Baltic-Build/v30-v10b
V=E:/DayZ-Baltic-Build/v30-v11-verify
SLOPES="2:0.167,5:0.25,6:0.2,7:0.167"
export PYTHONUTF8=1
WW="C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
export PYTHONPATH="$WW/tools/terrain;$WW/tools/navigation;$WW/tools/water"
WINPID=$(cat /proc/$$/winpid)
powershell.exe -NoProfile -Command "(Get-Process -Id $WINPID).PriorityClass='BelowNormal'" > /dev/null
mkdir -p $V
which_lane="${1:-all}"
if [ "$which_lane" = all ] || [ "$which_lane" = E1 ]; then
    "$PY" "$W/tools/terrain/build_v30_water.py" --selftest > $V/e1-selftest.log 2>&1; echo "E1 selftest exit $?"; tail -4 $V/e1-selftest.log
    for k in default rounded; do rm -rf $V/water-$k; mkdir -p $V/water-$k; done
    "$PY" "$W/tools/terrain/build_v30_water.py" $N10/design $V/water-default --border-margin 60 --drop-border-water-km2 0.05 \
        --border-keep-m 45 --contour "$(cygpath -w $N10/design/contour_lakes.geojson)" > $V/water-default.log 2>&1 || echo "E1 default exit $?"
    echo "E1 default $(sha256sum $V/water-default/water_v30.npz | cut -c1-12) v10 $(sha256sum $N10/terrain_v30/water_v30.npz | cut -c1-12)"
    "$PY" "$W/tools/terrain/build_v30_water.py" $N10/design $V/water-rounded --border-margin 60 --drop-border-water-km2 0.05 \
        --border-keep-m 45 --contour "$(cygpath -w $N10/design/contour_lakes.geojson)" --round-river-ends 30 > $V/water-rounded.log 2>&1 \
        || echo "E1 rounded exit $?"
    grep -E '"rivers_(clipped|ends_rounded)"|border_inland' $V/water-rounded.log
fi
if [ "$which_lane" = all ] || [ "$which_lane" = P4 ]; then
    "$PY" "$W/tools/terrain/profile_inland_v30.py" --selftest > $V/p4-selftest.log 2>&1; echo "P4 selftest exit $?"; tail -3 $V/p4-selftest.log
    rm -rf $V/inland-default $V/inland-slopes
    "$PY" "$W/tools/terrain/profile_inland_v30.py" --terrain $N10/v6/terrain_causeway.npz --out $V/inland-default --channels $N10/24 \
        --bed-floor 1.0 --bed-min-depth 0.30 --outline-sd $N10/20/sd_polish.npz --outline-sd-classes 2,5,7 \
        --low-water-bank --low-water-bank-min 1.0 > $V/inland-default.log 2>&1 || echo "P4 default exit $?"
    echo "P4 default $(sha256sum $V/inland-default/terrain_inland.npz | cut -c1-12) v10b $(sha256sum $N10B/inland/terrain_inland.npz | cut -c1-12)"
    "$PY" "$W/tools/terrain/profile_inland_v30.py" --terrain $N10/v6/terrain_causeway.npz --out $V/inland-slopes --channels $N10/24 \
        --bed-floor 1.0 --bed-min-depth 0.30 --outline-sd $N10/20/sd_polish.npz --outline-sd-classes 2,5,7 \
        --low-water-bank --low-water-bank-min 1.0 --slope-by-class "$SLOPES" --slope-ref 4.0 > $V/inland-slopes.log 2>&1 \
        || echo "P4 slopes exit $?"
    T=$V/inland-slopes/terrain_inland.npz
    "$PY" "$W/tools/terrain/verify_terrain_v30.py" $T --sea-cut 0.51 --low-water-bank-min 1.0 > $V/verify-slopes.json 2> $V/verify-slopes.err \
        || echo "  verify exit $?"
    "$PY" "$W/tools/terrain/verify_roads_v30.py" "$T::heights" "$T::water" --json $V/roads-slopes.json > $V/roads-slopes.log 2>&1 \
        || echo "  roads exit $?"
    "$PY" "$W/tools/terrain/verify_channel_reaches_v30.py" $T $N10/24 0.51 $V/reaches-slopes.json > $V/reaches-slopes.log 2>&1 \
        || echo "  reaches exit $?"
    "$PY" "$SP/depth_census.py" $T slopes > $V/depth-slopes.json 2> $V/depth-slopes.err || echo "  depth exit $?"
    "$PY" "$W/tools/water/audit_waterline_v30.py" --design $N10/design --contour "$N10/design/contour_lakes.geojson" \
        --terrain "slopes=$T" --terrain "v10b=$N10B/inland/terrain_inland.npz" --json $V/waterline-slopes.json > $V/waterline-slopes.log 2>&1 \
        || echo "  waterline exit $?"
fi
echo "done verify ($which_lane)"

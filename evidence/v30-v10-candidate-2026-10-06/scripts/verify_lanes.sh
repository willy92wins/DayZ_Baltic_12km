#!/usr/bin/env bash
# Receipt of the GLM lanes S1, P3 and W1 (installed in the worktree): defaults byte-identical to the v9 products,
# P3's outline option against the scratchpad prototype, W1's selftest and run on the v9 design.
set -uo pipefail
W="/c/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
PY="/c/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe"
N9=E:/DayZ-Baltic-Build/v30-redesign
V=E:/DayZ-Baltic-Build/v30-v10-verify
export PYTHONUTF8=1
WW="C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
export PYTHONPATH="$WW/tools/terrain;$WW/tools/navigation;$WW/tools/water"
WINPID=$(cat /proc/$$/winpid)
powershell.exe -NoProfile -Command "(Get-Process -Id $WINPID).PriorityClass='BelowNormal'" > /dev/null
mkdir -p $V
which_lane="${1:-all}"
if [ "$which_lane" = all ] || [ "$which_lane" = S1 ]; then
    TILES="0,0;5,7;10,10;15,15;20,20;25,25;31,27;31,31;2,29;29,2;12,3;3,12;18,9;9,18;27,14;14,27"
    rm -rf $V/surface-default
    "$PY" "$W/tools/terrain/build_surface_v30.py" $N9/inland/terrain_inland.npz $V/surface-default --tiles "$TILES" --workers 4 \
        --bed-tone depth-all --bed-surface gravel --shore-ring flowing > $V/surface-default.log 2>&1 || echo "S1 default exit $?"
    same=0; diff=0
    for f in $V/surface-default/layers/*.png; do
        b=$(basename $f)
        if cmp -s $f $N9/surface/layers/$b; then same=$((same+1)); else diff=$((diff+1)); echo "  S1 differs: $b"; fi
    done
    echo "S1 default tiles: $same same, $diff differ"
    rm -rf $V/surface-smooth
    "$PY" "$W/tools/terrain/build_surface_v30.py" $N9/inland/terrain_inland.npz $V/surface-smooth --tiles "31,27" --workers 1 \
        --bed-tone depth-all --bed-surface gravel --shore-ring flowing --landcover smooth --landcover-sigma 1.0 > $V/surface-smooth.log 2>&1 \
        || echo "S1 smooth exit $?"
    ls -la $V/surface-smooth/layers/ | tail -3
fi
if [ "$which_lane" = all ] || [ "$which_lane" = P3 ]; then
    "$PY" "$W/tools/terrain/profile_inland_v30.py" --selftest > $V/p3-selftest.log 2>&1; tail -1 $V/p3-selftest.log
    rm -rf $V/inland-default $V/inland-allclasses
    "$PY" "$W/tools/terrain/profile_inland_v30.py" --terrain $N9/v6/terrain_causeway.npz --out $V/inland-default --channels $N9/24 \
        --bed-floor 1.0 --bed-min-depth 0.30 > $V/inland-default.log 2>&1 || echo "P3 default exit $?"
    echo "P3 default $(sha256sum $V/inland-default/terrain_inland.npz | cut -c1-8) (expect e27f0f3e)"
    "$PY" "$W/tools/terrain/profile_inland_v30.py" --terrain $N9/v6/terrain_causeway.npz --out $V/inland-allclasses --channels $N9/24 \
        --bed-floor 1.0 --bed-min-depth 0.30 --outline-sd $N9/22/sd_shape.npz --outline-sd-classes 2,3,5,6,7 > $V/inland-allclasses.log 2>&1 \
        || echo "P3 all-classes exit $?"
    echo "P3 all classes $(sha256sum $V/inland-allclasses/terrain_inland.npz | cut -c1-8) (prototype $(sha256sum $N9/proto-inland-sd/terrain_inland.npz | cut -c1-8))"
    "$PY" "$W/tools/terrain/verify_terrain_v30.py" $N9/inland/terrain_inland.npz --sea-cut 0.51 > $V/verify-default.json 2> $V/verify-default.err
    "$PY" -c "
import json
a = json.load(open('$V/verify-default.json')); b = json.load(open('$N9/verify-v9.json'))
a.pop('sources'); b.pop('sources')
print('P3 verify_terrain default', 'SAME' if a == b else 'DIFF')
"
fi
if [ "$which_lane" = all ] || [ "$which_lane" = W1 ]; then
    "$PY" "$W/tools/water/smooth_water_outlines_v30.py" --selftest > $V/w1-selftest.log 2>&1; tail -2 $V/w1-selftest.log
    rm -rf $V/design-smooth
    "$PY" "$W/tools/water/smooth_water_outlines_v30.py" --design $N9/design --out $V/design-smooth --sigma 12 --max-shift 4 \
        > $V/w1-run.log 2>&1 || echo "W1 run exit $?"
    tail -40 $V/w1-run.log
fi
echo "done verify lanes ($which_lane)"

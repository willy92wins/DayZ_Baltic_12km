#!/usr/bin/env bash
# Replay of steps 10-25 (water pieces, deduplication, river mouths, patches, Narva moats and outline, Luga polish,
# relevel, shape, channel fit, shore fit) up to the v3b terrain fac76aea, each step on the previous replayed output.
# The step-10 PBO and binarized temp are copied from the archive only when the replayed sources and manifest are
# byte-identical (AddonBuilder packs the same sources; its output is not part of the terrain chain).
set -uo pipefail
W="/c/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
M="C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev"
PY="/c/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe"
P=E:/DayZ-Baltic-Build/v30-replay
B=E:/DayZ-Baltic-Build
export PYTHONUTF8=1
WW="C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
export PYTHONPATH="$WW/tools/terrain;$WW/tools/navigation;$WW/tools/water"
WINPID=$(cat /proc/$$/winpid)
powershell.exe -NoProfile -Command "(Get-Process -Id $WINPID).PriorityClass='BelowNormal'" > /dev/null
t0=$(date +%s); step() { echo "[$(( $(date +%s) - t0 )) s] $*" | tee -a $P/replay.log; }
cmp_sha() {
    a=$(sha256sum "$2" 2>/dev/null | cut -c1-16); b=$(sha256sum "$3" 2>/dev/null | cut -c1-16)
    if [ -n "$a" ] && [ "$a" = "$b" ]; then echo "  MATCH $1 $a" | tee -a $P/replay.log; else echo "  DIFF  $1 replay=$a archived=$b" | tee -a $P/replay.log; fi
}
SPD="$(dirname "$0")"
cmp_tree() {  # label replayed_dir archived_dir: every file of the archived tree, by sha (one Python process)
    "$PY" "$SPD/compare_tree.py" "$1" "$2" "$3" | tee -a $P/replay.log
}
step "10 water pieces"
test -f $P/10-water/pieces.json || "$PY" "$W/tools/water/build_water_pieces_v30.py" $P/09/terrain_v30.npz $P/10-water > $P/10.log 2>&1 || echo "  10 exit $?" | tee -a $P/replay.log
cmp_sha "10 pieces.json" $P/10-water/pieces.json $B/v30-pond-recovery/water/pieces.json
cmp_tree "10 source" $P/10-water/source $B/v30-pond-recovery/water/source
if cmp -s $P/10-water/pieces.json $B/v30-pond-recovery/water/pieces.json; then
    cp $B/v30-pond-recovery/water/baltic_water_v30.pbo $P/10-water/ && cp -r $B/v30-pond-recovery/water/temp $P/10-water/temp
    echo "  10 packed: archived PBO and temp reused (identical sources)" | tee -a $P/replay.log
fi
step "12 deduplication"
"$PY" "$W/tools/water/deduplicate_water_v30.py" --source $P/10-water --out $P/12-water > $P/12.log 2>&1 || echo "  12 exit $?" | tee -a $P/replay.log
cmp_sha "12 pieces.json" $P/12-water/pieces.json $B/v30-water-deduplicated/pieces.json
cmp_tree "12 source" $P/12-water/source $B/v30-water-deduplicated/source
step "14 river mouths"
"$PY" "$W/tools/water/profile_river_mouths_v30.py" --terrain $P/13/terrain_v30.npz --out $P/14 > $P/14.log 2>&1 || echo "  14 exit $?" | tee -a $P/replay.log
cmp_sha "14 terrain" $P/14/terrain_mouths.npz $B/v30-shore-sdf/mouths3/terrain_mouths.npz
step "15 patch"
"$PY" "$W/tools/water/patch_water_tiles_v30.py" --water $P/12-water --terrain-old $P/13/terrain_v30.npz \
    --terrain-new $P/14/terrain_mouths.npz --sea-cut-old 0.80 --sea-cut-new 0.51 --out $P/15-water > $P/15.log 2>&1 || echo "  15 exit $?" | tee -a $P/replay.log
cmp_sha "15 pieces.json" $P/15-water/pieces.json $B/v30-shore-sdf/water-mouths/pieces.json
step "16 Narva moats"
"$PY" "$W/tools/terrain/narva_moats_v30.py" $P/14/terrain_mouths.npz $P/16 > $P/16.log 2>&1 || echo "  16 exit $?" | tee -a $P/replay.log
cmp_sha "16 terrain" $P/16/terrain_pilot.npz $B/v30-narva-shore/mouths-moats/terrain_pilot.npz
step "17 patch"
"$PY" "$W/tools/water/patch_water_tiles_v30.py" --water $P/15-water --terrain-old $P/14/terrain_mouths.npz \
    --terrain-new $P/16/terrain_pilot.npz --sea-cut-old 0.51 --sea-cut-new 0.51 --out $P/17-water > $P/17.log 2>&1 || echo "  17 exit $?" | tee -a $P/replay.log
cmp_sha "17 pieces.json" $P/17-water/pieces.json $B/v30-narva-shore/water-moats/pieces.json
step "18 Narva V29 outline"
mkdir -p $P/18
"$PY" "$W/tools/terrain/narva_v29_outline_v30.py" $P/16/terrain_pilot.npz $P/18/sd_v29.npz > $P/18.log 2>&1 || echo "  18 exit $?" | tee -a $P/replay.log
echo "  18 sd_v29 $(sha256sum $P/18/sd_v29.npz | cut -c1-16) (expected d756a5da)" | tee -a $P/replay.log
step "20 Luga polish"
"$PY" "$W/tools/terrain/polish_luga_head_v30.py" --terrain $P/16/terrain_pilot.npz --sd-base $P/18/sd_v29.npz --out $P/20 \
    --channel "10530,4150;10531,4176;10525,4205;10524,4248;10540,4285;10580,4310;10603,4338;10620,4360" \
    --channel-width 30 --bed-depth 3.05 > $P/20.log 2>&1 || echo "  20 exit $?" | tee -a $P/replay.log
cmp_sha "20 terrain" $P/20/terrain_pilot.npz $B/v30-v3/polish/terrain_pilot.npz
cmp_sha "20 sd" $P/20/sd_polish.npz $B/v30-v3/polish/sd_polish.npz
step "21 relevel"
"$PY" "$W/tools/terrain/relevel_bodies_v30.py" --terrain $P/20/terrain_pilot.npz --out $P/21 --river Luga_0:4440:3.14 \
    --with-river-box 10150,3700,10700,4600:3.9 --bodies $B/v30-v3/bodies-v3b.json > $P/21.log 2>&1 || echo "  21 exit $?" | tee -a $P/replay.log
cmp_sha "21 terrain" $P/21/terrain_relevel.npz $B/v30-v3/relevel-b/terrain_relevel.npz
step "22 shape"
"$PY" "$W/tools/terrain/smooth_shore_outline_v30.py" --terrain $P/21/terrain_relevel.npz --sd $P/20/sd_polish.npz \
    --out $P/22 > $P/22.log 2>&1 || echo "  22 exit $?" | tee -a $P/replay.log
cmp_sha "22 terrain" $P/22/terrain_shape.npz $B/v30-v3/shape-b/terrain_shape.npz
cmp_sha "22 sd" $P/22/sd_shape.npz $B/v30-v3/shape-b/sd_shape.npz
step "23 patch"
"$PY" "$W/tools/water/patch_water_tiles_v30.py" --water $P/17-water --terrain-old $P/16/terrain_pilot.npz \
    --terrain-new $P/22/terrain_shape.npz --sea-cut-old 0.51 --sea-cut-new 0.51 --out $P/23-water > $P/23.log 2>&1 || echo "  23 exit $?" | tee -a $P/replay.log
cmp_sha "23 pieces.json" $P/23-water/pieces.json $B/v30-v3/water-v3b/pieces.json
step "24 channel fit"
"$PY" "$W/tools/water/fit_channel_pieces_v30.py" --terrain $P/22/terrain_shape.npz --water $P/23-water \
    --library $B/v30-vanilla-channel-pilot/library.json --overlap-all --no-pad --sea-cut 0.51 --out $P/24 > $P/24.log 2>&1 || echo "  24 exit $?" | tee -a $P/replay.log
cmp_sha "24 terrain" $P/24/terrain_pilot.npz $B/v30-v3/fit-v3b/terrain_pilot.npz
cmp_sha "24 pieces.json" $P/24/water/pieces.json $B/v30-v3/fit-v3b/water/pieces.json
step "25 shore fit"
"$PY" "$W/tools/terrain/fit_shore_crossings_v30.py" --terrain $P/24/terrain_pilot.npz --channels $P/24 --sea-cut 0.51 \
    --reg 0.05 --max-iter 3000 --dry-raise-max 0.4 --levee-cap 0.15 --corridor-margin 0 --sd-override $P/22/sd_shape.npz \
    --narva-core-m 0 --free-corridor-box 10150,3700,10700,4600 --out $P/25 > $P/25.log 2>&1 || echo "  25 exit $?" | tee -a $P/replay.log
cmp_sha "25 terrain (v3b)" $P/25/terrain_shore.npz $B/v30-v3/shore-v3b/terrain_shore.npz
step "done 10-25"

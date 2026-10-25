#!/usr/bin/env bash
# Candidate v10 (Guillermo, 06-10): the v9 chain on the design whose lakes, ponds and river bodies were smoothed along
# their rings (sigma 12 m, shift <= 4 m, contacts and Narva kept), lakes 047 and 107 kept whole at the border, the v9
# level list as the signed list, the inland shore pass on the vector outline (lakes, ponds, rivers; streams keep the
# raster outline) with the low-water bank rule, smooth land-cover boundaries, then gates, package, audits and the
# visible-waterline metric against v9. One step after another; stops at the first failure. Low priority.
set -uo pipefail
W="/c/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
M="C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev"
PY="/c/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe"
SPD="$(cd "$(dirname "$0")" && pwd -W)"
N=E:/DayZ-Baltic-Build/v30-v10
N9=E:/DayZ-Baltic-Build/v30-redesign
B=E:/DayZ-Baltic-Build
NAT="$M/tests/regional_outline_v1/reference.npz"
CHAN="10530,4150;10531,4176;10525,4205;10524,4248;10540,4285;10580,4310;10603,4338;10620,4360"
export PYTHONUTF8=1
WW="C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
export PYTHONPATH="$WW/tools/terrain;$WW/tools/navigation;$WW/tools/water"
WINPID=$(cat /proc/$$/winpid)
powershell.exe -NoProfile -Command "(Get-Process -Id $WINPID).PriorityClass='BelowNormal'" > /dev/null
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
step "design: smooth lakes, ponds and river bodies"
test -d $N/design || run design $N/design.log "$PY" "$W/tools/water/smooth_water_outlines_v30.py" --design $N9/design --out $N/design \
    --sigma 12 --max-shift 4
CONT=$N/design/contour_lakes.geojson
step "04 water (border rule, lakes 047 and 107 kept whole)"
mkdir -p $N/terrain_v30
run 04 $N/04-water.log "$PY" "$W/tools/terrain/build_v30_water.py" $N/design $N/terrain_v30 --border-margin 60 \
    --drop-border-water-km2 0.05 --border-keep-m 45 --contour "$(cygpath -w $CONT)"
step "05 terrain"
cd $N && run 05 $N/05-terrain.log "$PY" "$W/tools/terrain/build_v30.py" $N/terrain_v30 $N/terrain_v30
step "06 Luga bed fix"
run 06 $N/06.log "$PY" "$W/tools/terrain/audit_fairway_triangles_v30.py" --terrain $N/terrain_v30/terrain_v30.npz --design $N/design \
    --out $N/06-evidence --candidate $N/06/terrain_v30.npz --max-lowering-m 1.55
step "07 delta"
run 07 $N/07.log "$PY" "$W/tools/terrain/repair_delta_fairways_v30.py" --source $N/06/terrain_v30.npz --source-sha any --out $N/07 --evidence $N/07-evidence
step "08 shore finish"
run 08 $N/08.log "$PY" "$W/tools/terrain/finish_shores_v30.py" --source $N/07/terrain_v30.npz --source-sha any --water-v30 $N/terrain_v30/water_v30.npz \
    --nature "$NAT" --corridors $N/06-evidence/corridors.geojson $N/07-evidence/axes-corridors.geojson --out $N/08
step "09 Narva ponds"
run 09 $N/09.log "$PY" "$W/tools/terrain/restore_narva_ponds_v30.py" --source $N/08/terrain_v30.npz --source-sha any --design $N/design --nature "$NAT" --out $N/09
step "10 water pieces and pack"
run 10 $N/10.log "$PY" "$W/tools/water/build_water_pieces_v30.py" $N/09/terrain_v30.npz $N/10-water
run 10pack $N/10-pack.log powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$W")\tools\water\pack_water_v30.ps1" -Water "$(cygpath -w $N/10-water)"
step "11 small watercourses"
run 11 $N/11.log "$PY" "$W/tools/terrain/connect_small_watercourses_v30.py" --source $N/09/terrain_v30.npz --source-sha any --design $N/design --nature "$NAT" --out $N/11
step "12 deduplication"
run 12 $N/12.log "$PY" "$W/tools/water/deduplicate_water_v30.py" --source $N/10-water --pbo-sha any --manifest-sha any --out $N/12-water
step "13 wave margins"
run 13 $N/13.log "$PY" "$W/tools/terrain/deepen_wave_margins_v30.py" --source $N/11/terrain_v30.npz --source-sha any \
    --reference $B/v30-water-temporal-v2/reference.json --parent-reference $B/v30-continuity-dedup-package/runtime-fixture/reference.json \
    --design $N/design --nature "$NAT" --out $N/13 --constrained --skip-moved-points
step "14 river mouths"
run 14 $N/14.log "$PY" "$W/tools/water/profile_river_mouths_v30.py" --terrain $N/13/terrain_v30.npz --out $N/14
step "15 patch"
run 15 $N/15.log "$PY" "$W/tools/water/patch_water_tiles_v30.py" --water $N/12-water --terrain-old $N/13/terrain_v30.npz \
    --terrain-new $N/14/terrain_mouths.npz --sea-cut-old 0.80 --sea-cut-new 0.51 --out $N/15-water
step "16 Narva moats"
run 16 $N/16.log "$PY" "$W/tools/terrain/narva_moats_v30.py" $N/14/terrain_mouths.npz $N/16
step "17 patch"
run 17 $N/17.log "$PY" "$W/tools/water/patch_water_tiles_v30.py" --water $N/15-water --terrain-old $N/14/terrain_mouths.npz \
    --terrain-new $N/16/terrain_pilot.npz --sea-cut-old 0.51 --sea-cut-new 0.51 --out $N/17-water
step "18 Narva V29 outline"
mkdir -p $N/18
run 18 $N/18.log "$PY" "$W/tools/terrain/narva_v29_outline_v30.py" $N/16/terrain_pilot.npz $N/18/sd_v29.npz --water-v30 $N/terrain_v30/water_v30.npz
step "20 Luga polish"
run 20 $N/20.log "$PY" "$W/tools/terrain/polish_luga_head_v30.py" --terrain $N/16/terrain_pilot.npz --sd-base $N/18/sd_v29.npz --out $N/20 \
    --design $N/design --contour "$CONT" --channel "$CHAN" --channel-width 30 --bed-depth 3.05
step "levels: classification and the list (signed list = v9 list, approved 06-10)"
mkdir -p $N/root/tests $N/root/evidence/regional-foundation-v1
test -e $N/root/tests/water_v3 || powershell.exe -NoProfile -Command "New-Item -ItemType Junction -Path '$(cygpath -w $N/root/tests/water_v3)' -Target '$(cygpath -w $N/design)' | Out-Null"
cp "$CONT" $N/root/evidence/regional-foundation-v1/water-surfaces-contour-v2.geojson
run classify $N/levels-classify.log "$PY" "$W/tools/water/classify_perched_water_v30.py" --terrain $N/20/terrain_pilot.npz \
    --out $N/levels/classify --root "$(cygpath -w $N/root)" --big-area 1500000 --perched-min 0.3 --dike-lower 1.0 \
    --ring-margin 0.05 --ring-in 12 --ring-out 36 \
    --channel "10530,4150;10531,4176;10525,4205;10524,4248;10540,4285;10580,4310;10603,4338" --channel-width 20
run derive $N/levels-derive.log "$PY" "$W/tools/water/derive_signed_levels_v30.py" --terrain $N/20/terrain_pilot.npz \
    --classification $N/levels/classify/classification.json --signed $N9/levels/bodies-rule.json \
    --out-list $N/levels/bodies-rule.json --out-report $N/levels/report.json
cat $N/levels-derive.log | tee -a $N/chain.log
step "21 relevel"
run 21 $N/21.log "$PY" "$W/tools/terrain/relevel_bodies_v30.py" --terrain $N/20/terrain_pilot.npz --out $N/21 \
    --river Luga_0:4440:3.14 --with-river-box 10150,3700,10700,4600:3.9 --bodies $N/levels/bodies-rule.json --design $N/design
step "22 shape"
run 22 $N/22.log "$PY" "$W/tools/terrain/smooth_shore_outline_v30.py" --terrain $N/21/terrain_relevel.npz --sd $N/20/sd_polish.npz --out $N/22
step "23 patch"
run 23 $N/23.log "$PY" "$W/tools/water/patch_water_tiles_v30.py" --water $N/17-water --terrain-old $N/16/terrain_pilot.npz \
    --terrain-new $N/22/terrain_shape.npz --sea-cut-old 0.51 --sea-cut-new 0.51 --out $N/23-water
step "24 channel fit"
run 24 $N/24.log "$PY" "$W/tools/water/fit_channel_pieces_v30.py" --terrain $N/22/terrain_shape.npz --water $N/23-water \
    --library $B/v30-vanilla-channel-pilot/library.json --overlap-all --no-pad --sea-cut 0.51 --out $N/24 --design $N/design
step "25 shore fit"
run 25 $N/25.log "$PY" "$W/tools/terrain/fit_shore_crossings_v30.py" --terrain $N/24/terrain_pilot.npz --channels $N/24 --sea-cut 0.51 \
    --reg 0.05 --max-iter 3000 --dry-raise-max 0.4 --levee-cap 0.15 --corridor-margin 0 --sd-override $N/22/sd_shape.npz \
    --narva-core-m 0 --free-corridor-box 10150,3700,10700,4600 --water-v30 $N/terrain_v30/water_v30.npz --out $N/25
step "v5 coast"
run v5 $N/v5.log "$PY" "$W/tools/terrain/profile_coast_v30.py" --terrain $N/25/terrain_shore.npz --out $N/v5 --floor 1.60 --raise-land
step "v6 causeway"
run v6 $N/v6.log "$PY" "$W/tools/terrain/shape_causeways_v30.py" --terrain $N/v5/terrain_coast.npz --out $N/v6
step "inland shores and beds (vector outline for lakes, ponds and rivers; low-water banks)"
run inland $N/inland.log "$PY" "$W/tools/terrain/profile_inland_v30.py" --terrain $N/v6/terrain_causeway.npz --out $N/inland \
    --channels $N/24 --bed-floor 1.0 --bed-min-depth 0.30 --outline-sd $N/22/sd_shape.npz --outline-sd-classes 2,5,7 \
    --low-water-bank --low-water-bank-min 1.0
T=$N/inland/terrain_inland.npz
step "gates"
"$PY" "$W/tools/terrain/verify_terrain_v30.py" $T --sea-cut 0.51 --low-water-bank-min 1.0 > $N/verify-v10.json 2> $N/verify-v10.err || echo "  verify_terrain exit $?" | tee -a $N/chain.log
soft roads $N/roads-v10.log "$PY" "$W/tools/terrain/verify_roads_v30.py" "$T::heights" "$T::water" --json $N/roads-v10.json
soft reaches $N/channel-reaches.log "$PY" "$W/tools/terrain/verify_channel_reaches_v30.py" $T $N/24 0.51 $N/channel-reaches.json
step "surface (smooth land cover)"
run surface $N/surface.log "$PY" "$W/tools/terrain/build_surface_v30.py" $T $N/surface --workers 4 --bed-tone depth-all \
    --bed-surface gravel --shore-ring flowing --landcover smooth --landcover-sigma 1.0
step "package (OutsideTerrain with synthesis)"
env -u PYTHONPATH powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$W")\\tools\\terrain\\build_v30_package.ps1" \
    -Build "$(cygpath -w $N/package)" -Terrain "$(cygpath -w $T)" -WaterSource "$(cygpath -w $N/24/water)" \
    -Layers "$(cygpath -w $N/surface)" -OutsideSynth > $N/package-run.log 2>&1
grep -q "Built:" $N/package-run.log || { echo "  package FAILED, see $N/package-run.log" | tee -a $N/chain.log; exit 1; }
step "audits"
soft audit $N/audit-v10-085.log "$PY" "$W/tools/water/audit_visible_water_v30.py" --terrain $T --out $N/audit-v10-085 \
    --sea-level 0.85 --sea-cut 0.51 --channels $N/24 --water-v3 "$(cygpath -w $N/design/water_v3.geojson)" \
    --streams "$(cygpath -w $N/design/streams_candidates.geojson)" --contour "$(cygpath -w $CONT)"
soft census $N/census.log "$PY" "$W/tools/water/census_perched_water_v30.py" --terrain $T --out $N/census
soft shore-census $N/shore-census.log "$PY" "$SPD/shore_failure_census.py" $N/v6/terrain_causeway.npz $T $N/24 \
    $N/shore_failure_census_v10.json $N/shore_failure_map_v10.png v10
soft waterline-v10 $N/waterline-v10.log "$PY" "$W/tools/water/audit_waterline_v30.py" --design $N/design --contour "$CONT" \
    --terrain "v10=$T" --terrain "v10-step25=$N/v6/terrain_causeway.npz" --json $N/waterline-metric-v10.json
soft waterline-v9 $N/waterline-v9.log "$PY" "$W/tools/water/audit_waterline_v30.py" --design $N9/design \
    --terrain "v9=$N9/inland/terrain_inland.npz" --json $N/waterline-metric-v9.json
step "done v10"

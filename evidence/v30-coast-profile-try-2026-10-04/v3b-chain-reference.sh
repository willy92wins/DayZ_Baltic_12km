#!/usr/bin/env bash
# Candidate v3 (04-10 evening): after polish (navigable channel 30 m x 3.05 m), relevel (Luga 3.14 m, moats 2.45 m)
# and shape (Narva margin and shelf, smoothed outline). Same downstream chain and flags as the v2 polish candidate.
set -euo pipefail
W="/c/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
M="C:\\Users\\guill\\OneDrive\\Documentos\\DayZ Projects\\DayZ_Baltic_12km_dev"
N=E:/DayZ-Baltic-Build/v30-narva-shore
P=E:/DayZ-Baltic-Build/v30-v3
PY="/c/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe"
export PYTHONUTF8=1
WW="C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290"
export PYTHONPATH="$WW/tools/terrain;$WW/tools/navigation;$WW/tools/water"
t0=$(date +%s); step() { echo "[$(( $(date +%s) - t0 )) s] $*"; }
step water patch
"$PY" "$W/tools/water/patch_water_tiles_v30.py" --water $N/water-moats --terrain-old $N/mouths-moats/terrain_pilot.npz --terrain-new $P/shape-b/terrain_shape.npz --sea-cut-old 0.51 --sea-cut-new 0.51 --out $P/water-v3b > $P/water-v3b.log 2>&1
step channel fit
"$PY" "$W/tools/water/fit_channel_pieces_v30.py" --terrain $P/shape-b/terrain_shape.npz --water $P/water-v3b --library E:/DayZ-Baltic-Build/v30-vanilla-channel-pilot/library.json --overlap-all --no-pad --sea-cut 0.51 --out $P/fit-v3b > $P/fit-v3b.log 2>&1
step shore fit
"$PY" "$W/tools/terrain/fit_shore_crossings_v30.py" --terrain $P/fit-v3b/terrain_pilot.npz --channels $P/fit-v3b --sea-cut 0.51 --reg 0.05 --max-iter 3000 --dry-raise-max 0.4 --levee-cap 0.15 --corridor-margin 0 --sd-override $P/shape-b/sd_shape.npz --narva-core-m 0 --free-corridor-box 10150,3700,10700,4600 --out $P/shore-v3b > $P/shore-v3b.log 2>&1
step gates and surface
( "$PY" "$W/tools/terrain/verify_terrain_v30.py" $P/shore-v3b/terrain_shore.npz --sea-cut 0.51 > $P/verify-v3b.json 2> $P/verify-v3b.err ) &
( "$PY" "$W/tools/terrain/verify_roads_v30.py" "$P/shore-v3b/terrain_shore.npz::heights" "$P/shore-v3b/terrain_shore.npz::water" --json $P/roads-v3b.json > $P/roads-v3b.log 2>&1 ) &
( "$PY" "$W/tools/terrain/verify_channel_reaches_v30.py" $P/shore-v3b/terrain_shore.npz $P/fit-v3b 0.51 $P/channel-reaches-b.json > $P/channel-reaches-b.log 2>&1 ) &
( "$PY" "$W/tools/terrain/build_surface_v30.py" $P/shore-v3b/terrain_shore.npz $P/surface-b --workers 12 --bed-tone land --shore-ring flowing > $P/surface-b.log 2>&1 ) &
wait
step package
env -u PYTHONPATH powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$M\\tools\\terrain\\build_v30_package.ps1" -Build 'E:\DayZ-Baltic-Build\v30-v3\package-b' -Terrain 'E:\DayZ-Baltic-Build\v30-v3\shore-v3b\terrain_shore.npz' -WaterSource 'E:\DayZ-Baltic-Build\v30-v3\fit-v3b\water' -Layers 'E:\DayZ-Baltic-Build\v30-v3\surface-b' > $P/package-b-run.log 2>&1
grep -q "Built:" $P/package-b-run.log
step census and audit
( "$PY" "$W/tools/water/audit_visible_water_v30.py" --terrain $P/shore-v3b/terrain_shore.npz --out $P/audit-v3b-low --sea-level 0.54 --sea-cut 0.51 --channels $P/fit-v3b > $P/audit-v3b.log 2>&1 ) &
( "$PY" "$W/tools/water/census_perched_water_v30.py" --terrain $P/shore-v3b/terrain_shore.npz --out $P/census-b > $P/census-b.log 2>&1 ) &
wait
step done

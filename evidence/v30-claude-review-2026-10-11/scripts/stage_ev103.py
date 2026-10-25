"""Stage EV103: EV101 editable WRP (objects and materials unchanged) with the EV103 heights (sills, road cones, buried sill remnants)."""
import shutil, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, r"C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/tools/terrain")
from wrp0wzd import read, write
import runpy
sha = runpy.run_path("build_bisect.py", run_name="lib")["sha"]
EV100 = Path("E:/DayZ-Baltic-Build/v31-ev101-sea-bed-20261012")
OUT = Path("E:/DayZ-Baltic-Build/v31-ev103-sills-cones-20261012")
src_tree = EV100 / "stage/root/dayz_baltic_12km_dev/tb/narva_trial"
assert sha(src_tree / "baltic_trial.wrp") == "e8d4bcd3dd68412e1a8d46b9178cdb15c02fe07507269ffd2aa5e14837e10806"
assert sha(EV100 / "terrain-ev101.npz") == "2d21ccdcbb3a508ee4197c637c3bd87bdde41ed3786a25830f7358f0e79ad2f0"
assert sha(OUT / "terrain-ev103.npz") == "a1f458efae757cecea3e39973b2c25be65f264f0fe6bb6e3827249fbb3c205cc"
w = read(src_tree / "baltic_trial.wrp")
assert np.array_equal(w["heights"], np.load(EV100 / "terrain-ev101.npz")["heights"][::-1])
H = np.load(OUT / "terrain-ev103.npz")["heights"]
dst_tree = OUT / "stage/root/dayz_baltic_12km_dev/tb/narva_trial"
shutil.copytree(src_tree, dst_tree)
(dst_tree / "baltic_trial.wrp").unlink()
write(dst_tree / "baltic_trial.wrp", w["header"], H[::-1], w["materials"], [o["bytes"] for o in w["objects"]], w["terminator"])
back = read(dst_tree / "baltic_trial.wrp")
assert np.array_equal(back["heights"], H[::-1]) and [o["bytes"] for o in back["objects"]] == [o["bytes"] for o in w["objects"]] and back["materials"] == w["materials"]
print("staged", sha(dst_tree / "baltic_trial.wrp"), "objects", len(back["objects"]))

"""Stage EV101: EV100 editable WRP (objects and materials unchanged) with the EV101 heights (smoothed engine-sea bed)."""
import shutil, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, r"C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/tools/terrain")
from wrp0wzd import read, write
import runpy
sha = runpy.run_path("build_bisect.py", run_name="lib")["sha"]
EV100 = Path("E:/DayZ-Baltic-Build/v31-ev100-pond-banks-20261012")
OUT = Path("E:/DayZ-Baltic-Build/v31-ev101-sea-bed-20261012")
src_tree = EV100 / "stage/root/dayz_baltic_12km_dev/tb/narva_trial"
assert sha(src_tree / "baltic_trial.wrp") == "11debe1f7faec1e0d56dce318f6ec0be4685fa14c1139214b3cea22b826b8909"
assert sha(EV100 / "terrain-ev100.npz") == "d5565f63c2665507188bb9ea424b2af84e69ea65c0e4ec98af0f72dd9c99fa87"
assert sha(OUT / "terrain-ev101.npz") == "2d21ccdcbb3a508ee4197c637c3bd87bdde41ed3786a25830f7358f0e79ad2f0"
w = read(src_tree / "baltic_trial.wrp")
assert np.array_equal(w["heights"], np.load(EV100 / "terrain-ev100.npz")["heights"][::-1])
H = np.load(OUT / "terrain-ev101.npz")["heights"]
dst_tree = OUT / "stage/root/dayz_baltic_12km_dev/tb/narva_trial"
shutil.copytree(src_tree, dst_tree)
(dst_tree / "baltic_trial.wrp").unlink()
write(dst_tree / "baltic_trial.wrp", w["header"], H[::-1], w["materials"], [o["bytes"] for o in w["objects"]], w["terminator"])
back = read(dst_tree / "baltic_trial.wrp")
assert np.array_equal(back["heights"], H[::-1]) and [o["bytes"] for o in back["objects"]] == [o["bytes"] for o in w["objects"]] and back["materials"] == w["materials"]
print("staged", sha(dst_tree / "baltic_trial.wrp"), "objects", len(back["objects"]))

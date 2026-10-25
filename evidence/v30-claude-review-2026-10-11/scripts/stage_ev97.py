"""Stage EV97: EV96 editable WRP (objects and materials unchanged) with the EV97 smoothed heights."""
import json, shutil, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, r"C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/tools/terrain")
from wrp0wzd import read, write
import runpy
sha = runpy.run_path("build_bisect.py", run_name="lib")["sha"]
EV96 = Path("E:/DayZ-Baltic-Build/v30-water-two-colour-fix-20261011")
OUT = Path("E:/DayZ-Baltic-Build/v30-dry-relief-smoothing-20261011")
src_tree = EV96 / "stage/root/dayz_baltic_12km_dev/tb/narva_trial"
assert sha(src_tree / "baltic_trial.wrp") == "c30742f1bbdd611c8174bc4a494bf174a7b84b010c12f625975220feb3fdf6c8"
assert sha(EV96 / "terrain-ev96.npz") == "46eb90ac667a8be9eb73f88d2037dc3a84822281872fabfcde525c633f4af274"
w = read(src_tree / "baltic_trial.wrp")
ev96 = np.load(EV96 / "terrain-ev96.npz")["heights"]
assert np.array_equal(w["heights"], ev96[::-1])
H = np.load(OUT / "terrain-ev97.npz")["heights"]
dst_tree = OUT / "stage/root/dayz_baltic_12km_dev/tb/narva_trial"
shutil.copytree(src_tree, dst_tree)
(dst_tree / "baltic_trial.wrp").unlink()
write(dst_tree / "baltic_trial.wrp", w["header"], H[::-1], w["materials"], [o["bytes"] for o in w["objects"]], w["terminator"])
back = read(dst_tree / "baltic_trial.wrp")
assert np.array_equal(back["heights"], H[::-1]) and [o["bytes"] for o in back["objects"]] == [o["bytes"] for o in w["objects"]]
assert back["materials"] == w["materials"]
print("staged", sha(dst_tree / "baltic_trial.wrp"), "objects", len(back["objects"]))

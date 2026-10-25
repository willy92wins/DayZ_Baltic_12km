"""Stage EV100: EV98 editable WRP (objects and materials unchanged) with the EV99 heights (sea-sdf shore + lake rims)."""
import shutil, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, r"C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/tools/terrain")
from wrp0wzd import read, write
import runpy
sha = runpy.run_path("build_bisect.py", run_name="lib")["sha"]
EV98 = Path("E:/DayZ-Baltic-Build/v30-pond-sea-separation-20261011-b")
OUT = Path("E:/DayZ-Baltic-Build/v31-ev100-pond-banks-20261012")
src_tree = EV98 / "stage/root/dayz_baltic_12km_dev/tb/narva_trial"
assert sha(src_tree / "baltic_trial.wrp") == "50e57cf9f41c1faec8da7aab18dda281ebaec50b2df57fd447396ce2a1016bff"
assert sha(EV98 / "terrain-ev98.npz") == "483b6ec00ffcb25d7ed47665f9ea96f6268e9d9b59daa07c239292c50bb9cf05"
assert sha(OUT / "terrain-ev100.npz") == "d5565f63c2665507188bb9ea424b2af84e69ea65c0e4ec98af0f72dd9c99fa87"
w = read(src_tree / "baltic_trial.wrp")
assert np.array_equal(w["heights"], np.load(EV98 / "terrain-ev98.npz")["heights"][::-1])
H = np.load(OUT / "terrain-ev100.npz")["heights"]
dst_tree = OUT / "stage/root/dayz_baltic_12km_dev/tb/narva_trial"
shutil.copytree(src_tree, dst_tree)
(dst_tree / "baltic_trial.wrp").unlink()
write(dst_tree / "baltic_trial.wrp", w["header"], H[::-1], w["materials"], [o["bytes"] for o in w["objects"]], w["terminator"])
back = read(dst_tree / "baltic_trial.wrp")
assert np.array_equal(back["heights"], H[::-1]) and [o["bytes"] for o in back["objects"]] == [o["bytes"] for o in w["objects"]] and back["materials"] == w["materials"]
print("staged", sha(dst_tree / "baltic_trial.wrp"), "objects", len(back["objects"]))

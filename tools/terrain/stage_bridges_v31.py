"""Stage a world WRP with new heights and appended bridge records on top of an already staged v31 WRP (same water).
The base must already carry the pond pieces of the final footprint: when the bridges seal pond cells (pond mode), first
recompute the footprint from the new terrain and envelope, author and stage that water (stage_pond_pilot_v31.py --full),
then append the records here; staging on an older water leaves the sealed channels dry.
Usage: stage_bridges_v31.py <base_stage_tree> <terrain.npz> <records.json> <out_stage_tree> <report.json>"""
import hashlib, json, shutil, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290\tools\terrain")
from wrp0wzd import read, write, object_record
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
base, terrain, recs, out, rep_path = sys.argv[1:6]
out = Path(out); assert not out.exists()
w = read(Path(base) / "baltic_trial.wrp")
H = np.load(terrain)["heights"].astype("<f4")[::-1, :]
records = [o["bytes"] for o in w["objects"]]
nid = max(o["id"] for o in w["objects"]) + 1
added = []
for k, r in enumerate(json.load(open(recs))):
    records.append(object_record(r["matrix"], nid + k, r["model"].encode("ascii"))); added.append(dict(id=nid + k, **r))
shutil.copytree(base, out, ignore=shutil.ignore_patterns("baltic_trial.wrp"))
write(out / "baltic_trial.wrp", w["header"], H, w["materials"], records, w["terminator"])
b = read(out / "baltic_trial.wrp")
checks = dict(heights=bool(np.array_equal(b["heights"], H)), old_records_exact=[o["bytes"] for o in b["objects"][:len(w["objects"])]] == [o["bytes"] for o in w["objects"]],
              added=len(b["objects"]) == len(w["objects"]) + len(added), ids_unique=len({o["id"] for o in b["objects"]}) == len(b["objects"]),
              header=b["header"] == w["header"], materials=b["materials"] == w["materials"], terminator=b["terminator"] == w["terminator"])
rep = dict(base_wrp_sha256=sha(Path(base) / "baltic_trial.wrp"), wrp_sha256=sha(out / "baltic_trial.wrp"), terrain_sha256=sha(terrain), checks=checks, added=added)
json.dump(rep, open(rep_path, "w"), indent=1); print(json.dumps({k: v for k, v in rep.items() if k != "added"}, indent=1)); assert all(checks.values())

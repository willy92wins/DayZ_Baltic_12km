"""Package EV105: the EV95 world PBO with only baltic_trial.wrp replaced by the EV105 compiled OPRW, plus the merged
water PBO (EV98 water + p31 pilot pieces on the P1 terrain)."""
import json, runpy, shutil, subprocess
from pathlib import Path
lib = runpy.run_path("build_bisect.py", run_name="lib")
read_pbo, sha, FILEBANK = lib["read_pbo"], lib["sha"], lib["FILEBANK"]
OUT = Path("E:/DayZ-Baltic-Build/v31-pond-layer-20261013/p1b")
EV95_MOD = Path("P:/Mods/@DayZ_Baltic_EV95_WideBankPreviewV1/Addons")
MOD = Path("P:/Mods/@DayZ_Baltic_EV105_PondLayerPilotP1V1/Addons")
WATER = OUT / "water/packed/baltic_water_v30.pbo"
assert sha(EV95_MOD / "narva_trial.pbo") == "f1a148cab3e7d1d63473f0232a0971d45a9fea04e0fb456f01973235f4644b7d"
stage = json.loads((OUT / "stage-report.json").read_text())
assert sha(WATER) == stage["water_sha256"] and json.loads((OUT / "verify-compiled.json").read_text())["pass"]
props, base = read_pbo(EV95_MOD / "narva_trial.pbo")
_, compiled = read_pbo(OUT / "stage/out/narva_trial.pbo")
wrp = compiled["baltic_trial.wrp"]
assert wrp[:4] == b"OPRW" and wrp != base["baltic_trial.wrp"]
dist = OUT / "distribution/narva_trial"; packed = OUT / "packed"
dist.mkdir(parents=True, exist_ok=False); packed.mkdir(exist_ok=False)
for name, data in base.items():
    p = dist / name
    assert p.resolve().is_relative_to(dist.resolve())
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(wrp if name == "baltic_trial.wrp" else data)
cmd = [FILEBANK]
for k, v in props.items():
    cmd += ["-property", k + "=" + v]
done = subprocess.run(cmd + ["-dst", str(packed), str(dist)], capture_output=True, text=True)
(OUT / "filebank.log").write_text(done.stdout + "\n" + done.stderr)
assert done.returncode == 0
p2, after = read_pbo(packed / "narva_trial.pbo")
assert p2 == props and after.keys() == base.keys()
changed = [k for k in base if after[k] != base[k]]
assert changed == ["baltic_trial.wrp"], changed
MOD.mkdir(parents=True, exist_ok=False)
for src in (packed / "narva_trial.pbo", WATER):
    shutil.copyfile(src, MOD / src.name)
    assert sha(src) == sha(MOD / src.name)
receipt = dict(schema="ev105-pond-layer-pilot-p1-package.v1", mod=str(MOD.parent), world_sha256=sha(MOD / "narva_trial.pbo"),
               water_sha256=sha(MOD / "baltic_water_v30.pbo"), base_world_sha256="f1a148cab3e7d1d63473f0232a0971d45a9fea04e0fb456f01973235f4644b7d",
               changed_entries=changed, stage_report_sha256=sha(OUT / "stage-report.json"), verify_sha256=sha(OUT / "verify-compiled.json"))
(OUT / "deploy.json").write_text(json.dumps(receipt, indent=1))
print(receipt)

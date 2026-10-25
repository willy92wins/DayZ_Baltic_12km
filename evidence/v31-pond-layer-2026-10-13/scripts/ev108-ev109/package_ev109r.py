"""Package EV109R: EV109 with the render keys of Chernarus/Livonia (terrainNormalTexture = a global normal map generated
from the EV109 heights in Chernarus' encoding, heightBlendingMode=1, bicubicMode=1): compiled WRP, config.bin and the
normal map replace the base entries; everything else as EV109."""
import json, runpy, shutil, subprocess
from pathlib import Path
lib = runpy.run_path("build_bisect.py", run_name="lib")
read_pbo, sha, FILEBANK = lib["read_pbo"], lib["sha"], lib["FILEBANK"]
OUT = Path("E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev109r")
EV106 = Path("E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev109w")
EV95_MOD = Path("P:/Mods/@DayZ_Baltic_EV95_WideBankPreviewV1/Addons")
MOD = Path("P:/Mods/@DayZ_Baltic_EV109R_RenderKeysV1/Addons")
WATER = EV106 / "water/packed/baltic_water_v30.pbo"
assert sha(EV95_MOD / "narva_trial.pbo") == "f1a148cab3e7d1d63473f0232a0971d45a9fea04e0fb456f01973235f4644b7d"
stage = json.loads((EV106 / "stage-report.json").read_text())
assert sha(WATER) == stage["water_sha256"] and json.loads((EV106 / "verify-exact.json").read_text())["pass"]
props, base = read_pbo(EV95_MOD / "narva_trial.pbo")
_, compiled = read_pbo(OUT / "stage/out/narva_trial.pbo")
wrp = compiled["baltic_trial.wrp"]
assert wrp[:4] == b"OPRW" and wrp != base["baltic_trial.wrp"]
dist = OUT / "distribution/narva_trial"; packed = OUT / "packed"
dist.mkdir(parents=True, exist_ok=False); packed.mkdir(exist_ok=False)
NOHQ = "data/baltic_global_nohq.paa"
take = {"baltic_trial.wrp": wrp, "config.bin": compiled["config.bin"], NOHQ: compiled[NOHQ]}
for name, data in list(base.items()) + [(NOHQ, None)]:
    p = dist / name
    assert p.resolve().is_relative_to(dist.resolve())
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(take.get(name, data))
cmd = [FILEBANK]
for k, v in props.items():
    cmd += ["-property", k + "=" + v]
done = subprocess.run(cmd + ["-dst", str(packed), str(dist)], capture_output=True, text=True)
(OUT / "filebank.log").write_text(done.stdout + "\n" + done.stderr)
assert done.returncode == 0
p2, after = read_pbo(packed / "narva_trial.pbo")
assert p2 == props and set(after) == set(base) | {NOHQ}
changed = [k for k in base if after[k] != base[k]] + [NOHQ]
assert sorted(changed) == sorted(["baltic_trial.wrp", "config.bin", NOHQ]), changed
assert after["config.bin"] == compiled["config.bin"] and after[NOHQ] == compiled[NOHQ]
MOD.mkdir(parents=True, exist_ok=False)
for src in (packed / "narva_trial.pbo", WATER):
    shutil.copyfile(src, MOD / src.name)
    assert sha(src) == sha(MOD / src.name)
receipt = dict(schema="ev109r-render-keys-package.v1", mod=str(MOD.parent), world_sha256=sha(MOD / "narva_trial.pbo"),
               water_sha256=sha(MOD / "baltic_water_v30.pbo"), base_world_sha256="f1a148cab3e7d1d63473f0232a0971d45a9fea04e0fb456f01973235f4644b7d",
               changed_entries=changed, stage_report_sha256=sha(OUT / "stage-report.json"), verify_sha256=sha(EV106 / "verify-exact.json"))
(OUT / "deploy.json").write_text(json.dumps(receipt, indent=1))
print(receipt)

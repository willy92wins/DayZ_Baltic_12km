"""Pack a world PBO from the EV95 base, a compiled WRP and the layer PAAs of patch_surface_v31.py.

Successor of package_ev109.py (evidence/v31-pond-layer-2026-10-13/scripts/ev108-ev109/): every base entry is kept
except baltic_trial.wrp (taken from --wrp-from, a compiled narva_trial.pbo) and the data/layers/*.paa entries listed in
the manifest. FileBank packs with the base PBO properties; the result is read back and the changed entries must be
exactly the manifest entries plus the WRP. texHeaders.bin is kept as shipped since B: its entries already differ from
1,497 of the 2,048 layer PAAs (binarize -texheader over the shipped PAAs), so the patch does not create that state.
No deployment: copy packed/narva_trial.pbo and the water PBO into a fresh P:/Mods/@... folder as package_ev109.py:35-38.
Usage: package_surface_patch_v31.py <manifest.json> <out_dir> [--wrp-from compiled_narva_trial.pbo]
           [--base-pbo narva_trial.pbo --base-pbo-sha256 SHA]   (default: the manifest's base PBO)
<out_dir> must not exist.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

FILEBANK = "C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from patch_surface_v31 import pbo_index, sha  # noqa: E402


def read_pbo(path):
    props, index = pbo_index(path)
    with open(path, "rb") as f:
        data = {}
        for name, (off, size) in index.items():
            f.seek(off)
            data[name] = f.read(size)
    return props, data


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main():
    manifest_path, out = Path(sys.argv[1]), Path(sys.argv[2])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema"] == "surface-patch-v31.v1"
    base_pbo = arg("--base-pbo", manifest["base_pbo"])
    base_sha = arg("--base-pbo-sha256", manifest["base_pbo_sha256"]).lower()
    if sha(base_pbo) != base_sha:
        raise ValueError("base PBO SHA256 mismatch")
    props, base = read_pbo(base_pbo)
    replace = {}
    for e in manifest["entries"]:
        data = Path(e["file"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != e["sha256"]:
            raise ValueError(f"{e['file']} changed since the manifest was written")
        if e["entry"] not in base or not e["entry"].startswith("data/layers/") or not e["entry"].endswith(".paa"):
            raise ValueError(f"{e['entry']} is not a layer entry of the base PBO")
        if base[e["entry"]] == data:
            raise ValueError(f"{e['entry']} equals the base entry")
        replace[e["entry"]] = data
    assert sorted(replace) == sorted(manifest["changed_entries"])
    expected = sorted(replace)
    wrp_from = arg("--wrp-from")
    if wrp_from:
        _, compiled = read_pbo(wrp_from)
        wrp = compiled["baltic_trial.wrp"]
        assert wrp[:4] == b"OPRW"
        if wrp != base["baltic_trial.wrp"]:
            replace["baltic_trial.wrp"] = wrp
            expected = sorted(expected + ["baltic_trial.wrp"])
    dist, packed = out / "distribution" / "narva_trial", out / "packed"
    dist.mkdir(parents=True, exist_ok=False)
    packed.mkdir()
    for name, data in base.items():
        p = dist / name
        assert p.resolve().is_relative_to(dist.resolve())
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(replace.get(name, data))
    cmd = [FILEBANK]
    for k, v in props.items():
        cmd += ["-property", k + "=" + v]
    done = subprocess.run(cmd + ["-dst", str(packed), str(dist)], capture_output=True, text=True)
    (out / "filebank.log").write_text(done.stdout + "\n" + done.stderr, encoding="utf-8")
    assert done.returncode == 0, "FileBank failed; see filebank.log"
    p2, after = read_pbo(packed / "narva_trial.pbo")
    assert p2 == props and after.keys() == base.keys()
    changed = sorted(k for k in base if after[k] != base[k])
    assert changed == expected, (changed, expected)
    assert all(after[k] == v for k, v in replace.items())
    receipt = {"schema": "surface-patch-package-v31.v1", "pbo": str(packed / "narva_trial.pbo"),
               "pbo_sha256": sha(packed / "narva_trial.pbo"), "base_pbo": str(Path(base_pbo).resolve()),
               "base_pbo_sha256": base_sha, "wrp_from": str(Path(wrp_from).resolve()) if wrp_from else None,
               "wrp_from_sha256": sha(wrp_from) if wrp_from else None,
               "manifest": str(manifest_path.resolve()), "manifest_sha256": sha(manifest_path),
               "changed_entries": changed, "layer_entries": len(manifest["changed_entries"])}
    (out / "package.json").write_text(json.dumps(receipt, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=1))


if __name__ == "__main__":
    main()

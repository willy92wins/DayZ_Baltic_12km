"""Pond layer v31, steps S7 and S8: merge the p31 models into the current water PBO (pilot) or use them alone (--full),
and restage the world WRP.

Water: the current baltic_water_v30.pbo (3946db8b, unchanged since EV98) plus the compiled p31_* entries; asserts as in
package_global_seams.py:17-28 (same properties, same config.bin, disjoint names, FileBank round trip).
World: the base editable WRP with its heights replaced by the terrain's (rows reversed), every non-water record and
every water record outside the window byte-identical and in order; water records whose compiled roadway centroid falls
inside the window tiles are dropped; one record per p31 instance is appended at origin + ODOL bounding centre with
identity rotation (author_global_visual.py:74-86), ids from max(id) + 1.
With --full every baltic_water_v30 record is replaced and the water PBO holds only the p31 models (S14).
Usage: stage_pond_pilot_v31.py <author_dir> <terrain.npz> <base_stage_tree> <out_dir> (--window x0 x1 z0 z1 | --full)
"""
import argparse, hashlib, json, os, shutil, subprocess, sys
from pathlib import Path
import numpy as np
sys.path[:0] = [r"C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts",
                r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290\tools\terrain",
                r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290\tools\playtest"]
from odol_reader import ODOL
from wrp0wzd import read, write, object_record
from attach_navmesh import read_pbo

OLD_WATER = Path("P:/Mods/@DayZ_Baltic_EV95_WideBankPreviewV1/Addons/baltic_water_v30.pbo")
OLD_WATER_SHA = "3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14"
FILEBANK = "C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe"
PREFIX, TILE = "baltic_water_v30\\", 48
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def odol(path):
    od = ODOL.from_file(str(path))
    bc = od.model_info.bounding_center
    road = min(od.lods, key=lambda l: abs(l.resolution - 3e15))
    rv = np.array([(v.x, v.y, v.z) for v in road.vertices])
    return np.array([bc.x, bc.y, bc.z]), rv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("author"); ap.add_argument("terrain"); ap.add_argument("base_tree"); ap.add_argument("out")
    ap.add_argument("--window", nargs=4, type=float)
    ap.add_argument("--full", action="store_true")
    a = ap.parse_args()
    out = Path(a.out); assert not out.exists(); out.mkdir(parents=True)
    assert bool(a.window) != a.full
    window = a.window or [0.0, 12288.0, 0.0, 12288.0]
    wx0, wx1, wz0, wz1 = window
    assert all(v % TILE == 0 for v in window)
    author = Path(a.author)
    # S7 water merge
    assert sha(OLD_WATER) == OLD_WATER_SHA
    _, props, old = read_pbo(OLD_WATER)
    _, pprops, extra = read_pbo(author / "baltic_water_v30.pbo")
    assert props == pprops and old["config.bin"] == extra["config.bin"] and set(old) & set(extra) == {"config.bin"}
    merged = dict(extra) if a.full else {**old, **extra}
    temp = out / "water/temp/baltic_water_v30"; temp.mkdir(parents=True)
    for name, data in merged.items():
        t = temp / name; t.parent.mkdir(parents=True, exist_ok=True); t.write_bytes(data)
    packed = out / "water/packed"; packed.mkdir()
    cmd = [FILEBANK]
    for k, v in props.items():
        cmd += ["-property", k + "=" + v]
    r = subprocess.run(cmd + ["-dst", str(packed), str(temp)], capture_output=True)
    (out / "water/filebank.log").write_bytes(r.stdout + r.stderr); assert r.returncode == 0
    _, gp, got = read_pbo(packed / "baltic_water_v30.pbo"); assert gp == props and got == merged
    # S8 world
    base_wrp = Path(a.base_tree) / "baltic_trial.wrp"
    w = read(base_wrp)
    H = np.load(a.terrain)["heights"].astype("<f4")[::-1, :]
    keep, dropped, cache = [], [], {}
    for o in w["objects"]:
        if o["name"].startswith(PREFIX):
            name = o["name"][len(PREFIX):]
            if a.full:
                dropped.append(dict(id=o["id"], name=name, centroid=None))
                continue
            if name not in cache:
                cache[name] = odol(temp / name)
            c, rv = cache[name]
            m = np.array(o["matrix"]); rot, pos = m[:9].reshape(3, 3), m[9:12]
            assert np.array_equal(rot, np.eye(3)), o["id"]
            cx, _, cz = pos + rv.mean(axis=0)
            if wx0 <= cx < wx1 and wz0 <= cz < wz1:
                dropped.append(dict(id=o["id"], name=name, centroid=[float(cx), float(cz)]))
                continue
        keep.append(o)
    pieces = json.loads((author / "pieces.json").read_text())
    next_id = max(o["id"] for o in w["objects"]) + 1
    records, added = [o["bytes"] for o in keep], []
    for k, inst in enumerate(pieces["instance_list"]):
        name = inst["model"].split("\\")[-1]
        c, rv = odol(author / "temp/baltic_water_v30" / name)
        pos = np.array(inst["origin"]) + c
        matrix = [1, 0, 0, 0, 1, 0, 0, 0, 1, *pos.tolist()]
        records.append(object_record(matrix, next_id + k, inst["model"].encode("ascii")))
        added.append(dict(id=next_id + k, model=name, position=pos.tolist(), origin=inst["origin"]))
    tree = out / "stage/root/dayz_baltic_12km_dev/tb/narva_trial"
    shutil.copytree(a.base_tree, tree, ignore=shutil.ignore_patterns("baltic_trial.wrp"))
    wp = tree / "baltic_trial.wrp"
    write(wp, w["header"], H, w["materials"], records, w["terminator"])
    back = read(wp)
    kept_bytes = [o["bytes"] for o in keep]
    checks = dict(heights_exact=bool(np.array_equal(back["heights"], H)), header=back["header"] == w["header"],
                  materials=back["materials"] == w["materials"], terminator=back["terminator"] == w["terminator"],
                  kept_records_exact_in_order=[o["bytes"] for o in back["objects"][:len(keep)]] == kept_bytes,
                  ids_unique=len({o["id"] for o in back["objects"]}) == len(back["objects"]),
                  added=len(back["objects"]) == len(keep) + len(added),
                  non_water_untouched=sum(not o["name"].startswith(PREFIX) for o in back["objects"]) == sum(not o["name"].startswith(PREFIX) for o in w["objects"]))
    rep = dict(schema="pond-pilot-stage-v31.v1", window=window, full=a.full, old_water_sha256=OLD_WATER_SHA, water_sha256=sha(packed / "baltic_water_v30.pbo"),
               base_wrp_sha256=sha(base_wrp), wrp_sha256=sha(wp), terrain_sha256=sha(a.terrain), checks=checks,
               water_records_before=sum(o["name"].startswith(PREFIX) for o in w["objects"]), dropped=len(dropped), added=len(added),
               dropped_families={f: sum(d["name"].startswith(f) for d in dropped) for f in sorted({d["name"].split("_")[0] for d in dropped})},
               dropped_list=dropped, added_list=added)
    (out / "stage-report.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps({k: v for k, v in rep.items() if not k.endswith("_list")}, indent=1))
    assert all(checks.values())


if __name__ == "__main__":
    main()

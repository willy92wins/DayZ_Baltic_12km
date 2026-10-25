"""Regression of streambed_kit_v31.py v9 against the EV110 kit (v8): run v9 on HANDOFF step 1's inputs with the EV110 sites
(kit-118, kit-7, component mode) and '--no-mounds'; heights, every other npz array, cover, envelope and every non-stone
record must be identical to ev110/kit (terrain-kit.npz, cover-ev108.npy, envelope-ev108.npy, kit-records.json). Prints PASS
or FAIL. Usage: regression_ev110.py <tool.py> <out_dir>   (out_dir must not exist)"""
import json, os, subprocess, sys
import numpy as np
B = "E:/DayZ-Baltic-Build/v31-pond-layer-20261013"
tool, out = sys.argv[1:3]
os.makedirs(out, exist_ok=False)
cmd = [sys.executable, "-I", tool, "bridges/terrain-ev107.npz", "bridges/fp-ev107/footprint.npz",
       "E:/DayZ-Baltic-Build/v30-shore-sdf-20261011/cover-level-ev98.npy", "bridges/envelope-ev107.npy", "ev108-kit/sites.json",
       out + "/terrain-kit.npz", out + "/cover.npy", out + "/env.npy", out + "/kit-records.json", out + "/kit-report.json", "--no-mounds"]
pr = subprocess.run(cmd, cwd=B, capture_output=True, text=True)
res = dict(cmd=" ".join(cmd), exit=pr.returncode, stderr=pr.stderr[-600:])
if pr.returncode == 0:
    a, b = np.load(out + "/terrain-kit.npz"), np.load(B + "/ev110/kit/terrain-kit.npz")
    res["npz_keys_same"] = sorted(a.files) == sorted(b.files)
    res["npz_arrays_differing"] = [k for k in a.files if k in b.files and not np.array_equal(a[k], b[k], equal_nan=a[k].dtype.kind == "f")]
    res["cover_equal"] = bool(np.array_equal(np.load(out + "/cover.npy"), np.load(B + "/ev110/kit/cover-ev108.npy"), equal_nan=True))
    res["envelope_equal"] = bool(np.array_equal(np.load(out + "/env.npy"), np.load(B + "/ev110/kit/envelope-ev108.npy"), equal_nan=True))
    ra = [r for r in json.load(open(out + "/kit-records.json")) if r["piece"] != "stones"]
    rb = [r for r in json.load(open(B + "/ev110/kit/kit-records.json")) if r["piece"] != "stones"]
    res["pieces"] = [len(ra), len(rb)]
    res["piece_records_equal"] = ra == rb
    res["stones_v9_v8"] = [sum(1 for r in json.load(open(out + "/kit-records.json")) if r["piece"] == "stones"),
                           sum(1 for r in json.load(open(B + "/ev110/kit/kit-records.json")) if r["piece"] == "stones")]
    res["passed"] = bool(res["npz_keys_same"] and not res["npz_arrays_differing"] and res["cover_equal"] and res["envelope_equal"]
                         and res["piece_records_equal"])
else:
    res["passed"] = False
json.dump(res, open(out + "/regression.json", "w"), indent=1)
print(json.dumps(res, indent=1))
print("REGRESSION-EV110", "PASS" if res["passed"] else "FAIL")

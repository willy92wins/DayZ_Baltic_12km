"""G1 (EV112): the step-1 command of the EV112 chain runs and writes complete outputs. The command is read from
chain-ev112-step1.json (gatelib.CHAIN): it must name tools/water/streambed_kit_v31.py with 10 arguments whose first four
inputs are HANDOFF.md step 1's (terrain-ev107, fp-ev107 footprint, cover-level-ev98, envelope-ev107; 'Reconstruir EV108 y
EV109', item 1) and whose sites file is the given one; the worktree tool's Usage must list the same 10 arguments (v9 adds only
the optional '--no-mounds'). The gate runs it from E:/DayZ-Baltic-Build/v31-pond-layer-20261013 with the five output basenames
under <out_dir> (refuses to overwrite). Pass: exit 0, five fresh outputs, terrain keys = input keys + v31_kit with equal shapes,
cover/envelope 2047 x 2047, records with site/piece/model/matrix of 12 finite numbers, report schema streambed-kit-v31.v9,
every site of the sites file in the report (built, or skipped with a reason), the report's object counts equal to the records.
Usage: gate_g1_cli.py [out_dir]"""
import json, math, os, re, subprocess, sys, time
import numpy as np
sys.dont_write_bytecode = True; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatelib as G
out = sys.argv[1] if len(sys.argv) > 1 else G.OUT
ch = G.chain(); args = ch["args"]
text = open(G.WT + "/HANDOFF.md", encoding="utf-8").read()
sec = text[text.index("## Reconstruir EV108 y EV109"):]
hargs = re.search(r"1\. Kit: `([^`]*)`", sec, re.S).group(1).split()
res = dict(chain=ch, handoff_step1=" ".join(hargs), tool=args[0], n_args=len(args) - 1)
res["inputs_as_handoff"] = args[1:5] == hargs[1:5]
src = open(G.WT + "/tools/water/streambed_kit_v31.py", encoding="utf-8").read()
u = src[src.index("Usage: streambed_kit_v31.py"):].split()
res["usage"] = " ".join(u[:u.index("[--no-mounds]") + 1]) if "[--no-mounds]" in u else None
res["usage_10_args"] = res["usage"] is not None and len([t for t in res["usage"].split()[2:] if t.startswith("<")]) == 10
ins = args[1:6]; outs = [out + "/" + os.path.basename(a) for a in args[6:11]]
assert not any(os.path.exists(o) for o in outs), "outputs exist: use a fresh out dir"
os.makedirs(out, exist_ok=True)
t0 = time.time()
cmd = [sys.executable, "-I", G.WT + "/" + args[0]] + ins + outs
with open(out + "/kit-run.log", "w", newline="\n") as log:
    log.write(" ".join(cmd) + "\n"); log.flush()
    pr = subprocess.run(cmd, cwd=G.B, stdout=log, stderr=subprocess.STDOUT, text=True)
tail = open(out + "/kit-run.log").read()[-600:]
res.update(cmd=" ".join(cmd), cwd=G.B, exit=pr.returncode, seconds=round(time.time() - t0, 1), stderr_tail=tail, outputs=outs)
fresh = all(os.path.exists(o) and os.path.getmtime(o) >= t0 - 1 for o in outs)
checks = dict(fresh=fresh)
if pr.returncode == 0 and fresh:
    zi = np.load(G.B + "/" + ins[0]); zo = np.load(outs[0])
    checks["terrain_keys"] = sorted(zo.files) == sorted(set(zi.files) | {"v31_kit"})
    checks["terrain_shapes"] = all(zo[k].shape == zi[k].shape for k in zi.files)
    checks["cover_env_shape"] = np.load(outs[1]).shape == (2047, 2047) and np.load(outs[2]).shape == (2047, 2047)
    recs = json.load(open(outs[3]))
    checks["records"] = bool(recs) and all({"site", "piece", "model", "matrix"} <= set(r) and len(r["matrix"]) == 12
                                           and all(isinstance(x, (int, float)) and math.isfinite(x) for x in r["matrix"]) for r in recs)
    rep = json.load(open(outs[4]))
    checks["report_schema"] = rep["schema"] == "streambed-kit-v31.v9"
    sites = json.load(open(G.B + "/" + ins[4] if not os.path.isabs(ins[4]) else ins[4]))
    ids = [s["id"] for s in sites]; rids = [s["site"] for s in rep["sites"]]
    checks["every_site_reported"] = sorted(ids) == sorted(rids) and all("skipped" not in s or s["skipped"] for s in rep["sites"])
    n_p = sum(1 for r in recs if r["piece"] != "stones"); n_s = sum(1 for r in recs if r["piece"] == "stones")
    checks["counts"] = rep["counts"]["pieces"] == n_p and rep["counts"]["stones"] == n_s and rep["counts"]["objects"] == len(recs)
    res.update(sites=len(ids), built=sum(1 for s in rep["sites"] if "skipped" not in s),
               skipped=[dict(site=s["site"], why=s["skipped"]) for s in rep["sites"] if "skipped" in s], counts=rep["counts"])
res["checks"] = checks
res["passed"] = (res["tool"] == "tools/water/streambed_kit_v31.py" and res["n_args"] == 10 and res["inputs_as_handoff"] and res["usage_10_args"]
                 and pr.returncode == 0 and all(checks.values()) and len(checks) == 8)
print(json.dumps(res, indent=1))
json.dump(res, open(out + "/gate-g1.json", "w"), indent=1)
print("G1", "PASS" if res["passed"] else "FAIL")
sys.exit(0 if res["passed"] else 1)

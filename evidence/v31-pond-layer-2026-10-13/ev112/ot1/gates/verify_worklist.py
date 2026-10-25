"""Rebuild step 0 in a fresh process; independently check census scope and bytes."""
import csv, hashlib, json, pathlib, subprocess, sys
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import gatelib as G
root = pathlib.Path(G.B)/"ev112-ot1-20261018"
baseline_sites = pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else root/"sites.json"
baseline_worklist = pathlib.Path(sys.argv[2]) if len(sys.argv)>2 else root/"worklist.json"
out = pathlib.Path(sys.argv[3]) if len(sys.argv)>3 else root/"step0-b"
out.mkdir(exist_ok=False)
census = pathlib.Path(G.B)/"ev112-wip/kit/census"
cmd = [sys.executable,"-I",G.WT+"/tools/water/kit_worklist_v31.py",str(census),
       G.B+"/bridges/terrain-ev107.npz",G.B+"/bridges/fp-ev107/footprint.npz",G.B+"/bridges/envelope-ev107.npy",
       G.WT+"/evidence/v31-pond-layer-2026-10-13/bridges/ev110/sites-ev110.json",G.B+"/ev108-kit/sites.json",
       str(out/"sites.json"),str(out/"worklist.json"),G.B+"/ev112-wip/kit/exclusions-ev112.json"]
proc = subprocess.run(cmd,capture_output=True,text=True)
(out/"command.log").write_text("\n".join(cmd)+"\n"+proc.stdout+proc.stderr,encoding="utf-8")
checks = {"exit_zero":proc.returncode==0}
if proc.returncode==0:
    for name,baseline in (("sites.json",baseline_sites),("worklist.json",baseline_worklist)):
        checks[name+"_byte_identical"] = baseline.read_bytes()==(out/name).read_bytes()
    reaches = list(csv.DictReader(open(census/"census-reaches.csv")))
    worst = {}
    for s in csv.DictReader(open(census/"census-segments.csv")):
        worst[s["reach"]] = max(worst.get(s["reach"],0),float(s["wiggle"]))
    expected = {r["reach"] for r in reaches if float(r["width_p50"]) <= 6 and
                (float(r["wiggle"]) >= .25 or worst.get(r["reach"],0) >= .40)}
    rep = json.loads((out/"worklist.json").read_text())
    checks["exact_census_selection"] = expected == {r["reach"] for r in rep["in_stems"]}
    checks["excluded_report_complete"] = len(rep["in_stems"])+len(rep["out_stems"])==len(reaches)
    checks["built_reaches_within_scope"] = all(s.get("mode")!="reach" or s["reach"] in expected
                                               for s in json.loads((out/"sites.json").read_text()))
    checks["wide_control_present_and_excluded"] = any(float(r["width_p50"])>6 for r in reaches) and all(r["width_p50"]<=6 for r in rep["in_stems"])
    checks["smooth_control_present_and_excluded"] = any(float(r["wiggle"])<.25 and worst.get(r["reach"],0)<.40 for r in reaches)
result = dict(checks=checks,passed=all(checks.values()),command=cmd)
(out/"gate-worklist.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
print("WORKLIST", "PASS" if result["passed"] else "FAIL")
sys.exit(0 if result["passed"] else 1)

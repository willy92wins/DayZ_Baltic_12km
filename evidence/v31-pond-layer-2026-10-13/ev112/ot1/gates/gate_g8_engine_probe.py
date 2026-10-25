"""G8: ENGINE acceptance of the kit, separate from the geometric G2-G4. Reads the server probe log of <run>/probe/points.csv
(missions BalticBridgeProbeV2 or BalticKitProbeV1; rows P;id;ground;sea;pond;surface;depth;roadY;objects, depth =
GetWaterDepth at ground + 0.01) and classifies the probe_points_kit.py points by their KIND (review 2 of 15-10: the 'expect' label alone let relabelled or
unlabelled dry controls skip the dry check); a kit point whose label is absent or does not fit its kind FAILs:
  wet  (kit_axis, kit_confluence, and lips/joints over a water_ext face) liquid controls: depth > 0;
  test (kit_lip / kit_joint over concrete_ext lips only)     functional continuity at the joints: depth > 0;
  dry  (kit_side, kit_joint_side, old_bed)                   dry controls: depth <= 0.
Also: header BALTIC_*_PROBE_*, BEGIN;N and END;N with N = the points, one P row per id, at least one object streamed at every
kit point, and the engine ground within 0.05 m of the npz ground (else the probed build is not this run).
Every reading used (ground, depth) and every reference (the npz ground) must be finite; one non-finite value FAILs
(review 2: depth NaN read as dry and ground NaN skipped build_mismatch).
Without a log the gate prints 'G8 NOT_RUN' and exits 3: functional continuity stays pending, never assumed.
Usage: gate_g8_engine_probe.py [run_dir] [--log path]"""
import json, os, sys
from collections import Counter, defaultdict
sys.dont_write_bytecode = True; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatelib as G
import math
KIND_EXPECT = {"kit_axis": ("wet",), "kit_confluence": ("wet",), "kit_lip": ("wet", "test"), "kit_joint": ("wet", "test"),
               "kit_side": ("dry",), "kit_joint_side": ("dry",), "old_bed": ("dry",)}
args = sys.argv[1:]
log = None
if "--log" in args:
    log = args[args.index("--log") + 1]; args = args[:args.index("--log")]
run = args[0] if args else G.OUT
if log is None:
    for name in ("baltic_bridge_probe_v2.log", "baltic_kit_probe_v1.log"):
        if os.path.exists(run + "/probe/" + name):
            log = run + "/probe/" + name; break
res = dict(log=log, points=run + "/probe/points.json")
if not log or not os.path.exists(log):
    res["status"] = "NOT_RUN"
    json.dump(res, open(run + "/gate-g8.json", "w"), indent=1)
    print(json.dumps(res))
    print("G8 NOT_RUN (no server probe log: engine water at lips/joints unverified)")
    sys.exit(3)
pts = {p["id"]: p for p in json.load(open(run + "/probe/points.json"))}
fails = defaultdict(list); rows = {}; head = begin = end = None
for line in open(log, encoding="utf-8", errors="replace"):
    a = line.strip().split(";")
    if a[0].startswith("BALTIC_") and "_PROBE_" in a[0]:
        head = a[0]
    elif a[0] == "BEGIN":
        begin = int(a[1])
    elif a[0] == "END":
        end = int(a[1])
    elif a[0] == "P":
        i = int(a[1])
        if i in rows:
            fails["duplicate_row"].append(i)
        try:
            rows[i] = dict(ground=float(a[2]), pond=a[4], depth=float(a[6]), road=float(a[7]), objects=int(a[8]))
        except (ValueError, IndexError):
            fails["unparsable_row"].append(line.strip()[:120]); continue
    elif a[0] == "FAIL":
        fails["probe_fail"].append(line.strip())
if not head or begin != len(pts) or end != len(pts):
    fails["log_frame"].append((head, begin, end, len(pts)))
missing = sorted(set(pts) - set(rows))
if missing:
    fails["missing_rows"].extend(missing[:20])
table = defaultdict(Counter)
for i, p in pts.items():
    r = rows.get(i)
    if r is None:
        continue
    if p["kind"] in KIND_EXPECT:
        if p.get("expect") not in KIND_EXPECT[p["kind"]]:
            fails["label"].append((i, p["kind"], p.get("expect")))
        exp = "dry" if KIND_EXPECT[p["kind"]] == ("dry",) else ("wet" if KIND_EXPECT[p["kind"]] == ("wet",) else p.get("expect"))
    elif "expect" in p:
        exp = p["expect"]
    else:
        continue
    if not (math.isfinite(r["ground"]) and math.isfinite(r["depth"])):
        fails["non_finite_reading"].append((i, p["kind"], r["ground"], r["depth"])); continue
    ref = p.get("ground")
    if not (isinstance(ref, (int, float)) and math.isfinite(ref)):
        fails["non_finite_reference"].append((i, p["kind"], ref)); continue
    wet = r["depth"] > 0
    table[(p["kind"], exp)]["wet" if wet else "dry"] += 1
    if p["kind"].startswith("kit_") and p["kind"] not in ("kit_side", "kit_joint_side") and r["objects"] < 1:
        fails["not_streamed"].append(i)
    if not abs(r["ground"] - ref) <= 0.05:
        fails["build_mismatch"].append((i, ref, r["ground"]))
    if exp == "wet" and not wet:
        fails["liquid_control_dry"].append((i, p["kind"], r["depth"]))
    elif exp == "test" and not wet:
        fails["lip_joint_dry"].append((i, p["kind"], p.get("piece_kind") or p.get("piece_kinds"), round(p["x"], 2), round(p["z"], 2), r["depth"]))
    elif exp == "dry" and wet:
        fails["dry_control_wet"].append((i, p["kind"], r["depth"]))
res.update(status="RUN", head=head, rows=len(rows), table={f"{k[0]}/{k[1]}": dict(v) for k, v in sorted(table.items())},
           failures={k: dict(n=len(v), first=[str(x) for x in v[:10]]) for k, v in fails.items()})
res["passed"] = not fails
json.dump(res, open(run + "/gate-g8.json", "w"), indent=1)
print(json.dumps(res))
print("G8", "PASS" if res["passed"] else "FAIL")
sys.exit(0 if res["passed"] else 1)

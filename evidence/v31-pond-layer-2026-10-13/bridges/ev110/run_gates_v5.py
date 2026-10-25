"""Run the EV110 bridge gates (gates_v5.py) on a bridges_v31 v5 run, build the fixtures they need and the negative controls
that must FAIL. Everything is written under <out>/ (v4-baseline/, gates/, fixtures/, negative/); nothing is deleted, and a
tool output that already exists is reused (so use a fresh <out> after changing a tool).
Usage: run_gates_v5.py --out DIR --terrain NPZ --envelope NPY --sites JSON --sites-v4 JSON --tool V5 --tool-v4 V4
                       [--proto PROTOTYPE] [--tool-r1 V5R1] [--r1-run DIR]
  --out      folder of the v5 run (terrain-br.npz, envelope-br.npy, bridge-records.json, bridge-report.json; built with
             --tool when missing); the v4 baseline of the same inputs goes to <out>/v4-baseline (built with --tool-v4 from
             --sites-v4, the EV109 sites: v4 knows neither stack nor model swaps, so it must not see the EV110 sites)
  --proto    end-fit prototype (W < 6 m neighbour rule): negative for G3 (W 5.9/6.0/6.1) and G7 (overlap fixture)
  --tool-r1  the first v5 (fixed 0.25 m compensation step): negative for the G3 continuity check at W = 5.900390625 /
             5.9005859375 (its opening fell 4.770 -> 4.001 m there)
  --r1-run   the first v5's EV108 run (015-42: two feet hanging 0.075 / 0.196 m): negative for G4
Negative controls whose gate already FAILs on the run (G2: wood ramp air; G5: frozen corridor vertices inherited from
v4) also record whether the mutation itself was detected."""
import argparse, json, math, shutil, subprocess, sys
sys.dont_write_bytecode = True
from pathlib import Path
import numpy as np

PY = sys.executable
HERE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
for k in ("out", "terrain", "envelope", "sites", "sites_v4", "tool", "tool_v4"):
    ap.add_argument("--" + k.replace("_", "-"), required=True)
for k in ("proto", "tool_r1", "r1_run"):
    ap.add_argument("--" + k.replace("_", "-"))
A = ap.parse_args()
O, TIN, EIN, SITES, SITES4, TOOL5, TOOL4 = map(Path, (A.out, A.terrain, A.envelope, A.sites, A.sites_v4, A.tool, A.tool_v4))
PROTO, TOOLR1, R1RUN = (Path(p) if p else None for p in (A.proto, A.tool_r1, A.r1_run))
V4 = O / "v4-baseline"; G = O / "gates"; FX = O / "fixtures"; NEG = O / "negative"
NAMES = ("terrain-br.npz", "envelope-br.npy", "bridge-records.json", "bridge-report.json")
SWEEP = (5.9, 5.900390625, 5.9005859375, 5.905, 5.91, 5.925, 5.95, 5.975, 5.99, 5.9999, 6.0, 6.0001, 6.01, 6.025, 6.05, 6.075, 6.1)


def tool(path, sites, out):
    out.mkdir(parents=True, exist_ok=True)
    if all((out / n).exists() for n in NAMES):
        return 0
    with open(out / "run.log", "w") as log:
        rc = subprocess.run([PY, "-I", "-B", str(path), str(TIN), str(EIN), str(sites), *[str(out / n) for n in NAMES]], stdout=log, stderr=subprocess.STDOUT).returncode
    if rc:
        raise SystemExit(f"tool {path} failed on {sites} (see {out / 'run.log'})")
    return rc


def gate(g, run, out, extra=()):
    args = [PY, "-I", "-B", str(HERE / "gates_v5.py"), g, "--run", str(run), "--v4", str(V4), "--input", str(TIN), "--sites", str(SITES), "--out", str(out), *extra]
    r = subprocess.run(args, capture_output=True, text=True)
    first = (r.stdout.splitlines() or ["?"])[0]
    return first.split()[-1] if first.startswith(g) else f"ERROR {r.stderr[-300:]}"


def clone(src, dst, terrain=None, records=None, envelope=None, report=None):
    """A run folder: copies of src, optionally with a modified terrain (heights), records, envelope or report."""
    dst.mkdir(parents=True, exist_ok=True)
    for n in NAMES:
        if not (dst / n).exists():
            shutil.copyfile(src / n, dst / n)
    if terrain is not None:
        z = np.load(src / "terrain-br.npz"); a = {k: z[k] for k in z.files}; a["heights"] = terrain.astype(np.float32); np.savez(dst / "terrain-br.npz", **a)
    if records is not None:
        json.dump(records, open(dst / "bridge-records.json", "w", newline="\n"), indent=1)
    if envelope is not None:
        np.save(dst / "envelope-br.npy", envelope.astype(np.float32))
    if report is not None:
        json.dump(report, open(dst / "bridge-report.json", "w", newline="\n"), indent=1)
    return dst


def sweep(tool_path, root, widths, v4_from=None):
    dirs = []
    for w in widths:
        d = root / f"W{w:.10g}"; d.mkdir(parents=True, exist_ok=True)
        json.dump([dict(s25, width=w)], open(d / "sites.json", "w", newline="\n"), indent=1)
        if v4_from is not None and not (d / "v4").exists():
            shutil.copytree(v4_from / f"W{w:.10g}" / "v4", d / "v4")
        tool(TOOL4, d / "sites.json", d / "v4"); tool(tool_path, d / "sites.json", d / "run"); dirs.append(str(d))
    return dirs


for d in (G, FX, NEG):
    d.mkdir(parents=True, exist_ok=True)
tool(TOOL5, SITES, O); tool(TOOL4, SITES4, V4)
sites = json.load(open(SITES))
res = dict(positive={}, negative={}, detected={}, fixtures={})
# ---- fixtures: a W sweep at 015-25 (G3) and two overlapping 015-13 sites (G7)
s25 = [s for s in sites if s["id"] == "015-25"][0]
wdirs = sweep(TOOL5, FX / "W-sweep", SWEEP); res["fixtures"]["W-sweep"] = list(SWEEP)
s13 = [s for s in sites if s["id"] == "015-13"][0]
ov = FX / "overlap"; ov.mkdir(exist_ok=True)
json.dump([s13, dict(s13, id="015-13b", x=s13["x"] + 18.0, z=s13["z"] + 6.0)], open(ov / "sites.json", "w", newline="\n"), indent=1)
tool(TOOL5, ov / "sites.json", ov / "run")
# ---- positive gates
for g in ("G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8"):
    extra = ("--fixture", *wdirs) if g == "G3" else (("--fixture", str(ov / "run")) if g == "G7" else ())
    res["positive"][g] = gate(g, O, G / f"{g}.json", extra)
# ---- negative controls (each must FAIL)
sys.path.insert(0, str(HERE)); import gates_v5 as gv
H = np.load(O / "terrain-br.npz")["heights"].astype(np.float64); H0 = np.load(TIN)["heights"].astype(np.float64)
rec = json.load(open(O / "bridge-records.json")); env = np.load(O / "envelope-br.npy"); rep = json.load(open(O / "bridge-report.json"))
# G1: lift the triangle under the tightest end strip (015-8 end 1) by 0.05 m above its clearance
r8 = [r for r in rec if r["site"] == "015-8" and not r.get("role")]; m8 = gv.model("bridge_metal_25")
up = sorted(r8, key=lambda r: r["span"])[-1]; best = (np.inf, None)
for T in m8["deck"]:
    P = gv.clip(T, lambda Q: (m8["hi"] - Q[:, m8["ax"]]), 2.0)
    if len(P) >= 3:
        C = gv.cands(gv.world(up["matrix"], P)); cl = C[:, 1] - gv.terr(H, C[:, 0], C[:, 2]); i = int(np.argmin(cl))
        if cl[i] < best[0]:
            best = (cl[i], C[i])
Hn = H.copy()
for v in gv.tri_vertices(best[1][0], best[1][2]):
    Hn[v] += best[0] + 0.05
res["negative"]["G1 strip lifted 0.05 m over the deck"] = gate("G1", clone(O, NEG / "G1", terrain=Hn), NEG / "G1.json")
# G2: the v4 terrain (015-13 bare corner); G2 already fails on wood air, so the metal end must be caught
k = "G2 v4 terrain (015-13 bare corner)"
res["negative"][k] = gate("G2", V4, NEG / "G2.json")
res["detected"][k] = any(not e["pass_"] for ends in json.load(open(NEG / "G2.json"))["sites"].values() for e in ends if e["kind"] == "block")
# G3: a wet vertex under the 015-25 deck raised above the stream
L25 = [x for x in rep["sites"] if x["site"] == "015-25"][0]["level"]
dv = gv.deck_vertices(H, s25, gv.model(s25["model"]), [r for r in rec if r["site"] == "015-25" and not r.get("role")])
wv = sorted(v for v in dv if H[v] < L25)
Hn = H.copy(); Hn[wv[0]] = L25 + 0.5
res["negative"]["G3 wet vertex under 015-25 raised"] = gate("G3", clone(O, NEG / "G3", terrain=Hn), NEG / "G3.json")
if PROTO:
    pdirs = sweep(PROTO, NEG / "G3-proto", (5.9, 6.0, 6.1), v4_from=FX / "W-sweep")
    res["negative"]["G3 prototype (W < 6 m neighbour rule) on W 5.9/6.0/6.1"] = gate("G3", O, NEG / "G3-proto.json", ("--fixture", *pdirs))
if TOOLR1:
    rdirs = sweep(TOOLR1, NEG / "G3-r1", (5.900390625, 5.9005859375), v4_from=FX / "W-sweep")
    res["negative"]["G3 first v5 (0.25 m step) at W 5.900390625 / 5.9005859375: continuity"] = gate("G3", O, NEG / "G3-r1.json", ("--fixture", *rdirs))
# G4: stack copy at 5.30 m, the v4 records (no stack, no swap), a lower copy of the wrong model, the first v5 run
rn = [dict(r) for r in rec]
for r in rn:
    if r.get("role") == "stack-lower":
        u = [x for x in rec if x["site"] == r["site"] and x["span"] == r["span"] and not x.get("role")][0]["matrix"]
        r["matrix"] = u[:9] + list(np.array(u[9:12]) - 5.30 * np.array(u[3:6]))
res["negative"]["G4 stack offset 5.30 m"] = gate("G4", clone(O, NEG / "G4-offset", records=rn), NEG / "G4-offset.json")
res["negative"]["G4 v4 records (no stack, no swap)"] = gate("G4", clone(O, NEG / "G4-v4rec", records=json.load(open(V4 / "bridge-records.json"))), NEG / "G4-v4rec.json")
rw = [dict(r) for r in rec]
for r in rw:
    if r["site"] == "015-19" and r.get("role") == "stack-lower":
        r["model"] = gv.model_path("bridge_metal_25")
lowm = clone(O, NEG / "lower-model", records=rw)
res["negative"]["G4 015-19 lower copy is bridge_metal_25"] = gate("G4", lowm, NEG / "G4-lower-model.json")
if R1RUN:
    res["negative"]["G4 first v5 run (015-42 feet hanging)"] = gate("G4", R1RUN, NEG / "G4-r1.json")
# G5: a frozen vertex 300 m from every bridge moved 0.3 m; a frozen vertex outside every footprint but inside a v4 corridor
# (|s| <= flat half-span) lowered 0.3 m. G5 already fails on the inherited corridor vertices: the mutation must be listed.
z = np.load(O / "terrain-br.npz"); frz = z["reserve"] | z["platform"] | z["narva"]
far = np.ones(frz.shape, bool)
for s_ in sites:
    rc, cc = int((12282 - s_["z"]) / 6), int(s_["x"] / 6); far[max(rc - 50, 0):rc + 51, max(cc - 50, 0):cc + 51] = False
v = tuple(int(i) for i in np.argwhere(frz & far)[0]); Hn = H.copy(); Hn[v] += 0.3
k = "G5 far frozen vertex +0.3 m"
res["negative"][k] = gate("G5", clone(O, NEG / "G5", terrain=Hn), NEG / "G5.json")
res["detected"][k] = list(v) in [x["vertex"] for x in json.load(open(NEG / "G5.json"))["outside_list"]]
sup = gv.footprint_support(gv.load_run(O)); best = None
for s_ in sites:
    m_ = gv.model(s_["model"]); flat = int(s_.get("spans", 1)) * (m_["hi"] - m_["lo"]) / 2 - 6.5; b = math.radians(s_["bearing"])
    rc, cc = int((12282 - s_["z"]) / 6), int(s_["x"] / 6)
    for r_ in range(rc - 25, rc + 26):
        for c_ in range(cc - 25, cc + 26):
            X, Z = 6.0 * c_ - s_["x"], 12282 - 6.0 * r_ - s_["z"]
            if abs(X * math.sin(b) + Z * math.cos(b)) <= flat and frz[r_, c_] and not sup[r_, c_] and H[r_, c_] == H0[r_, c_]:
                d_ = math.hypot(X, Z)
                if best is None or d_ < best[0]:
                    best = (d_, (r_, c_), s_["id"])
Hn = H.copy(); Hn[best[1]] -= 0.3
k = f"G5 frozen corridor vertex outside the footprint lowered 0.3 m ({best[2]} {list(best[1])})"
res["negative"][k] = gate("G5", clone(O, NEG / "G5-corridor", terrain=Hn), NEG / "G5-corridor.json")
res["detected"][k] = list(best[1]) in [x["vertex"] for x in json.load(open(NEG / "G5-corridor.json"))["outside_list"]]
# G6: a 20 m spike beside 015-11
rc, cc = int((12282 - 7003.2) / 6) + 8, int(8574.7 / 6) + 8; Hn = H.copy(); Hn[rc, cc] += 20.0
res["negative"]["G6 20 m spike"] = gate("G6", clone(O, NEG / "G6", terrain=Hn), NEG / "G6.json")
# G7: prototype on the overlap fixture, the v4 terrain, a report without its final end measurements, a deck-centre spike
if PROTO:
    tool(PROTO, ov / "sites.json", NEG / "G7-proto" / "run")
    res["negative"]["G7 prototype on the overlap fixture"] = gate("G7", O, NEG / "G7-proto.json", ("--fixture", str(NEG / "G7-proto" / "run")))
res["negative"]["G7 v4 terrain (no joint fit)"] = gate("G7", clone(O, NEG / "G7-v4", terrain=np.load(V4 / "terrain-br.npz")["heights"].astype(np.float64)), NEG / "G7-v4.json")
rp = json.loads(json.dumps(rep))
for s_ in rp["sites"]:
    s_.pop("fit_ends", None)
res["negative"]["G7 report without fit_ends"] = gate("G7", clone(O, NEG / "G7-no-fit-ends", report=rp), NEG / "G7-no-fit-ends.json")
s11 = [s for s in sites if s["id"] == "015-11"][0]; tv = (round((12282 - s11["z"]) / 6), round(s11["x"] / 6))
Hn = H.copy(); Hn[tv] = max(r["matrix"][10] for r in rec if r["site"] == "015-11") + 20.0
res["negative"][f"G7 015-11 deck-centre vertex {list(tv)} raised over the deck"] = gate("G7", clone(O, NEG / "G7-spike", terrain=Hn), NEG / "G7-spike.json")
# G7 (review 2 of 15-10): at the first stacked site (015-19 when stacked) the ground under the upper feet that stand on the
# ground, not on the lower copy, lowered 3 m; the report is refreshed from this script's own measurements, so the only
# defect left is those hanging upper feet. And a lower copy whose matrix holds a NaN (G7 and G8).
stk = [s_["id"] for s_ in sites if s_.get("stack")]
su = "015-19" if "015-19" in stk else stk[0]
rr = gv.site_records(gv.load_run(O))[su]; upr = sorted(rr["upper"], key=lambda r_: r_["span"])[0]
lor = [r_ for r_ in rr["lower"] if r_["span"] == upr["span"]][0]; mu = gv.model(gv.mname(upr))
feet_v = set()
for F, c in zip(gv.legs(mu), gv.contact(mu, gv.model(gv.mname(lor)), 1.0, gv.rel_frame(upr, lor))):
    if c is None or c > gv.LEG_GAP:
        Wf = gv.world(upr["matrix"], F); feet_v.update(v_ for x_, _, z_ in Wf for v_ in gv.tri_vertices(x_, z_))
Hn = H.copy()
for v_ in feet_v:
    Hn[v_] -= 3.0
q = gv.load_run(O); q["H"] = Hn
_, qd1 = gv.g1(q); _, qd2 = gv.g2(q); qdk = gv.deck_clear(q); qlg = gv.leg_gaps(q, sites)
rp = json.loads(json.dumps(rep))
for s_ in rp["sites"]:
    sid_ = s_["site"]; s_["deck_strip_min_clear_m"] = min(qd1["min_clearance_m"][sid_]); s_["deck_min_clear_m"] = qdk[sid_]
    s_["fit_ends"] = [dict(e_) for e_ in qd2["sites"][sid_]]
    for role_, l_ in qlg.get(sid_, {}).items():
        if role_ in ("lower", "upper"):
            s_.setdefault("legs", {})[role_] = l_
k = f"G7 {su} upper feet on the ground: ground lowered 3 m ({len(feet_v)} vertices), report refreshed"
res["negative"][k] = gate("G7", clone(O, NEG / "G7-upper-feet", terrain=Hn, report=rp), NEG / "G7-upper-feet.json", ("--fixture", str(ov / "run")))
res["detected"][k] = json.load(open(NEG / "G7-upper-feet.json"))["legs"][su]["upper_stack"]["hanging"] > 0
rn = json.loads(json.dumps(rec))
[r_ for r_ in rn if r_["site"] == su and r_.get("role") == "stack-lower"][0]["matrix"][10] = float("nan")
nanr = clone(O, NEG / "nan-lower", records=rn)
for g_ in ("G7", "G8"):
    k = f"{g_} {su} lower copy matrix[10] = NaN"
    res["negative"][k] = gate(g_, nanr, NEG / f"{g_}-nan-lower.json", ("--fixture", str(ov / "run")) if g_ == "G7" else ())
    res["detected"][k] = bool(json.load(open(NEG / f"{g_}-nan-lower.json")).get("invalid_matrices"))
# G8: one record moved 1 cm, one envelope cell changed, a lower copy of the wrong model
rn = [dict(r) for r in rec]; rn[0]["matrix"] = rn[0]["matrix"][:9] + [rn[0]["matrix"][9] + 0.01] + rn[0]["matrix"][10:]
res["negative"]["G8 record moved 1 cm"] = gate("G8", clone(O, NEG / "G8-rec", records=rn), NEG / "G8-rec.json")
en = env.copy(); i = tuple(np.argwhere(np.isfinite(en))[0]); en[i] += 0.1
res["negative"]["G8 envelope cell +0.1 m"] = gate("G8", clone(O, NEG / "G8-env", envelope=en), NEG / "G8-env.json")
res["negative"]["G8 015-19 lower copy is bridge_metal_25"] = gate("G8", lowm, NEG / "G8-lower-model.json")
res["negatives_all_fail"] = all(v_ == "FAIL" for v_ in res["negative"].values())
res["negatives_all_detected"] = all(res["detected"].values())
json.dump(res, open(G / "summary.json", "w", newline="\n"), indent=1)
print(json.dumps(res, indent=1))

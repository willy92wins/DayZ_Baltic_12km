"""Run the EV112 bridge gates (gates_v6.py: G1-G14) on a bridges_v31 v6 run, build the fixtures they need and the negative
controls that must FAIL (the 22 EV110 ones, adapted, and the new ones of G8-G14, plus the tool's own refusal of a NaN
height). Everything is written under <out>/ (v4-baseline/, gates/, fixtures/, negative/, gates-work/, records/); nothing is
deleted, and a tool output that already exists is reused (so use a fresh <out> after changing a tool).
Usage: run_gates_v6.py --out DIR --terrain NPZ --envelope NPY --cover NPY --input-fp DIR --sites JSON --sites-v4 JSON
                       --tool V6 --tool-v4 V4 --v5-run DIR --pilot-records JSON --kit-records JSON --stage-base WRP
                       --merge-tool PY --stage-tool PY [--proto PROTOTYPE] [--tool-r1 V5R1] [--r1-run DIR]
                       [--v4-fixtures DIR] [--prev-run DIR]
  --input-fp     footprint of --terrain (footprint.npz, footprint-report.json): G11 reference and G12's bury reference
  --v5-run       the EV110 v5 run of the same inputs (G9/G10 negatives, G11 reference)
  --v4-fixtures  a W-sweep folder whose W*/v4 runs (v4 tool, same inputs) are copied instead of rebuilt
  --pilot-records / --kit-records  bridges/records.json (015-15) and the kit records of the chain (G14)
  --stage-base   a staged baltic_trial.wrp of the chain (copied, never written): G14 stages the merged records on the copy
  --prev-run     the first v6 run (EV112 review 1: 015-18 / 015-40 mouths in different water bodies, soft wings): G10 / G13
                 negatives
Negative controls whose gate already FAILs on the run (G2, G5, G9, G11) also record whether the mutation itself was
detected."""
import argparse, json, math, shutil, subprocess, sys
sys.dont_write_bytecode = True
from pathlib import Path
import numpy as np

PY = sys.executable
HERE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
for k in ("out", "terrain", "envelope", "cover", "input_fp", "sites", "sites_v4", "tool", "tool_v4", "v5_run"):
    ap.add_argument("--" + k.replace("_", "-"), required=True)
for k in ("pilot_records", "kit_records", "stage_base", "merge_tool", "stage_tool"):
    ap.add_argument("--" + k.replace("_", "-"), required=True)
for k in ("proto", "tool_r1", "r1_run", "v4_fixtures", "prev_run"):
    ap.add_argument("--" + k.replace("_", "-"))
A = ap.parse_args()
O, TIN, EIN, COVER, FPIN, SITES, SITES4, TOOL, TOOL4, V5RUN = map(Path, (A.out, A.terrain, A.envelope, A.cover, A.input_fp, A.sites, A.sites_v4, A.tool, A.tool_v4, A.v5_run))
PROTO, TOOLR1, R1RUN, V4FX, PREV = (Path(p) if p else None for p in (A.proto, A.tool_r1, A.r1_run, A.v4_fixtures, A.prev_run))
PILOT, KIT, SBASE, MERGE, STAGE = map(Path, (A.pilot_records, A.kit_records, A.stage_base, A.merge_tool, A.stage_tool))
RECS = O / "records"
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


def gate(g, run, out, extra=(), work=None, sites=None):
    args = [PY, "-I", "-B", str(HERE / "gates_v6.py"), g, "--run", str(run), "--v4", str(V4), "--input", str(TIN), "--input-env", str(EIN),
            "--input-fp", str(FPIN), "--cover", str(COVER), "--sites", str(sites or SITES), "--work", str(work or Path(out).parent / (Path(out).stem + "-work")),
            "--out", str(out), *extra]
    r = subprocess.run(args, capture_output=True, text=True)
    first = (r.stdout.splitlines() or ["?"])[0]
    return first.split()[-1] if first.startswith(g) else f"ERROR {r.stderr[-400:]}"


def clone(src, dst, terrain=None, records=None, envelope=None, report=None):
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
        if v4_from is not None and (v4_from / f"W{w:.10g}" / "v4").exists() and not (d / "v4").exists():
            shutil.copytree(v4_from / f"W{w:.10g}" / "v4", d / "v4")
        tool(TOOL4, d / "sites.json", d / "v4"); tool(tool_path, d / "sites.json", d / "run"); dirs.append(str(d))
    return dirs


def jl(p):
    return json.load(open(p, encoding="utf-8"))


def stage(records, out):
    """stage_bridges_v31.py on a copy of --stage-base (a folder holding only that WRP); returns the staged WRP."""
    base = RECS / "stage-base"
    if not (base / "baltic_trial.wrp").exists():
        base.mkdir(parents=True, exist_ok=True); shutil.copyfile(SBASE, base / "baltic_trial.wrp")
    if not (out / "baltic_trial.wrp").exists():
        with open(str(out) + ".log", "w") as log:
            rc = subprocess.run([PY, "-I", "-B", str(STAGE), str(base), str(O / "terrain-br.npz"), str(records), str(out), str(out) + "-report.json"],
                                stdout=log, stderr=subprocess.STDOUT).returncode
        if rc:
            raise SystemExit(f"stage failed on {records} (see {out}.log)")
    return out / "baltic_trial.wrp"


for d in (G, FX, NEG, RECS):
    d.mkdir(parents=True, exist_ok=True)
tool(TOOL, SITES, O); tool(TOOL4, SITES4, V4)
sites = json.load(open(SITES))
res = dict(positive={}, negative={}, detected={}, fixtures={}, tool_refusals={})
MERGED = RECS / "records-merged.json"
if not MERGED.exists():
    with open(RECS / "merge.log", "w") as log:
        if subprocess.run([PY, "-I", "-B", str(MERGE), "--pilot", str(PILOT), "--kit", str(KIT), "--bridges", str(O / "bridge-records.json"),
                           "--sites", str(SITES), "--out", str(MERGED)], stdout=log, stderr=subprocess.STDOUT).returncode:
            raise SystemExit(f"merge failed (see {RECS / 'merge.log'})")
SWRP = stage(MERGED, RECS / "stage")
G14X = ("--merged", str(MERGED), "--pilot", str(PILOT), "--kit", str(KIT), "--stage-wrp", str(SWRP), "--base-wrp", str(RECS / "stage-base" / "baltic_trial.wrp"))
# ---- fixtures: a W sweep at 015-25 (G3) and two overlapping 015-13 sites (G7)
s25 = [s for s in sites if s["id"] == "015-25"][0]
wdirs = sweep(TOOL, FX / "W-sweep", SWEEP, v4_from=V4FX); res["fixtures"]["W-sweep"] = list(SWEEP)
s13 = [s for s in sites if s["id"] == "015-13"][0]
ov = FX / "overlap"; ov.mkdir(exist_ok=True)
json.dump([s13, dict(s13, id="015-13b", x=s13["x"] + 18.0, z=s13["z"] + 6.0)], open(ov / "sites.json", "w", newline="\n"), indent=1)
tool(TOOL, ov / "sites.json", ov / "run")
# ---- positive gates
for g in ("G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10", "G11", "G12", "G13", "G14"):
    extra = ("--fixture", *wdirs) if g == "G3" else (("--fixture", str(ov / "run")) if g == "G7" else (("--v5", str(V5RUN)) if g == "G11" else
                                                                                                    (G14X if g == "G14" else ())))
    res["positive"][g] = gate(g, O, G / f"{g}.json", extra, work=O / "gates-work")
sys.path.insert(0, str(HERE)); import gates_v6 as g6
gv = g6.gv
H = np.load(O / "terrain-br.npz")["heights"].astype(np.float64); H0 = np.load(TIN)["heights"].astype(np.float64)
rec = jl(O / "bridge-records.json"); env = np.load(O / "envelope-br.npy"); rep = jl(O / "bridge-report.json")
# ================= EV110 negatives, on the v6 run =================
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
k = "G2 v4 terrain (015-13 bare corner)"
res["negative"][k] = gate("G2", V4, NEG / "G2.json")
res["detected"][k] = any(not e["pass_"] for ends in jl(NEG / "G2.json")["sites"].values() for e in ends if e["kind"] == "block")
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
rn = [dict(r) for r in rec]
for r in rn:
    if r.get("role") == "stack-lower":
        u = [x for x in rec if x["site"] == r["site"] and x["span"] == r["span"] and not x.get("role")][0]["matrix"]
        r["matrix"] = u[:9] + list(np.array(u[9:12]) - 5.30 * np.array(u[3:6]))
res["negative"]["G4 stack offset 5.30 m"] = gate("G4", clone(O, NEG / "G4-offset", records=rn), NEG / "G4-offset.json")
res["negative"]["G4 v4 records (no stack, no swap)"] = gate("G4", clone(O, NEG / "G4-v4rec", records=jl(V4 / "bridge-records.json")), NEG / "G4-v4rec.json")
rw = [dict(r) for r in rec]
for r in rw:
    if r["site"] == "015-19" and r.get("role") == "stack-lower":
        r["model"] = gv.model_path("bridge_metal_25")
lowm = clone(O, NEG / "lower-model", records=rw)
res["negative"]["G4 015-19 lower copy is bridge_metal_25"] = gate("G4", lowm, NEG / "G4-lower-model.json")
if R1RUN:
    res["negative"]["G4 first v5 run (015-42 feet hanging)"] = gate("G4", R1RUN, NEG / "G4-r1.json")
z = np.load(O / "terrain-br.npz"); frz = z["reserve"] | z["platform"] | z["narva"]
far = np.ones(frz.shape, bool)
for s_ in sites:
    rc, cc = int((12282 - s_["z"]) / 6), int(s_["x"] / 6); far[max(rc - 50, 0):rc + 51, max(cc - 50, 0):cc + 51] = False
v = tuple(int(i) for i in np.argwhere(frz & far)[0]); Hn = H.copy(); Hn[v] += 0.3
k = "G5 far frozen vertex +0.3 m"
res["negative"][k] = gate("G5", clone(O, NEG / "G5", terrain=Hn), NEG / "G5.json")
res["detected"][k] = list(v) in [x["vertex"] for x in jl(NEG / "G5.json")["outside_list"]]
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
res["detected"][k] = list(best[1]) in [x["vertex"] for x in jl(NEG / "G5-corridor.json")["outside_list"]]
rc, cc = int((12282 - 7003.2) / 6) + 8, int(8574.7 / 6) + 8; Hn = H.copy(); Hn[rc, cc] += 20.0
res["negative"]["G6 20 m spike"] = gate("G6", clone(O, NEG / "G6", terrain=Hn), NEG / "G6.json")
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
res["detected"][k] = jl(NEG / "G7-upper-feet.json")["legs"][su]["upper_stack"]["hanging"] > 0
rn = json.loads(json.dumps(rec))
[r_ for r_ in rn if r_["site"] == su and r_.get("role") == "stack-lower"][0]["matrix"][10] = float("nan")
nanr = clone(O, NEG / "nan-lower", records=rn)
for g_ in ("G7", "G8"):
    k = f"{g_} {su} lower copy matrix[10] = NaN"
    res["negative"][k] = gate(g_, nanr, NEG / f"{g_}-nan-lower.json", ("--fixture", str(ov / "run")) if g_ == "G7" else ())
    res["detected"][k] = bool(jl(NEG / f"{g_}-nan-lower.json").get("invalid_matrices"))
rn = [dict(r) for r in rec]; rn[0]["matrix"] = rn[0]["matrix"][:9] + [rn[0]["matrix"][9] + 0.01] + rn[0]["matrix"][10:]
res["negative"]["G8 record moved 1 cm"] = gate("G8", clone(O, NEG / "G8-rec", records=rn), NEG / "G8-rec.json")
e4 = np.load(V4 / "envelope-br.npy")
en = env.copy(); i = tuple(np.argwhere(np.isfinite(e4))[0]); en[i] += 0.1
res["negative"]["G8 v4 envelope cell +0.1 m"] = gate("G8", clone(O, NEG / "G8-env", envelope=en), NEG / "G8-env.json")
res["negative"]["G8 015-19 lower copy is bridge_metal_25"] = gate("G8", lowm, NEG / "G8-lower-model.json")
# ================= new negatives (v6) =================
# G8: a NaN cell within 100 m of 015-8 sealed at the level + 1 (on EV108 the v6 envelope equals v4's, so there is no v6-only
# cell to corrupt); a NaN cell >= 300 m from every site sealed at a level
L8 = [x for x in rep["sites"] if x["site"] == "015-8"][0]["level"]
nan8 = np.argwhere(~np.isfinite(env) & ~np.isfinite(e4))
dist8 = np.hypot(6 * nan8[:, 1] + 3 - 7116.9, 12282 - 6 * nan8[:, 0] - 3 - 6920.0)
en = env.copy(); c8 = tuple(int(i) for i in nan8[np.argmin(np.where(dist8 >= 20.0, dist8, np.inf))])
en[c8] = L8 + 1.0
k = f"G8 NaN cell {list(c8)} beside 015-8 sealed at the level + 1 m"
res["negative"][k] = gate("G8", clone(O, NEG / "G8-seal-level", envelope=en), NEG / "G8-seal-level.json")
res["detected"][k] = list(c8) in [x["cell"] for x in jl(NEG / "G8-seal-level.json")["envelope_bad_cells"]]
farc = tuple(int(i) for i in np.argwhere(~np.isfinite(env) & far[:-1, :-1])[0])                  # >= 300 m from every site
en = env.copy(); en[farc] = L8
k = f"G8 NaN cell {list(farc)} far from every site sealed"
res["negative"][k] = gate("G8", clone(O, NEG / "G8-far-seal", envelope=en), NEG / "G8-far-seal.json")
res["detected"][k] = list(farc) in [x["cell"] for x in jl(NEG / "G8-far-seal.json")["envelope_bad_cells"]]
# G9: the v5 run (015-13 end 0 corner), and a run vertex under the 015-8 end-0 zone lowered 0.5 m
k = "G9 the v5 run (EV110, 015-13 end 0)"
res["negative"][k] = gate("G9", V5RUN, NEG / "G9-v5.json")
res["detected"][k] = not [e for e in jl(NEG / "G9-v5.json")["sites"]["015-13"] if e["end"] == 0][0]["pass_"]
z8 = g6.zone_geometry(m8, 0); r8u = sorted(r8, key=lambda r: r["span"])[0]
P = np.zeros(3); P[m8["ax"]] = m8["lo"] + z8[0] / 2; P[m8["lat"]] = m8["c_lat"]; W8 = gv.world(r8u["matrix"], [P])[0]
Hn = H.copy()
for v_ in gv.tri_vertices(W8[0], W8[2]):
    Hn[v_] -= 0.5
k = "G9 015-8 end-0 zone triangle lowered 0.5 m"
res["negative"][k] = gate("G9", clone(O, NEG / "G9-zone", terrain=Hn), NEG / "G9-zone.json")
res["detected"][k] = not [e for e in jl(NEG / "G9-zone.json")["sites"]["015-8"] if e["end"] == 0][0]["pass_"]
# G10: the v5 run with its straight axis + links written as a centreline; the run's centreline shifted 10 m across
r5 = jl(V5RUN / "bridge-report.json"); s_by = {s_["id"]: s_ for s_ in sites}
for s_ in r5["sites"]:
    sd = s_by[s_["site"]]; wb = math.radians(sd["water_bearing"]); wd = np.array([math.sin(wb), math.cos(wb)]); c0 = np.array([sd["x"], sd["z"]])
    up_, dn_ = s_["cut_up_down"]; pts = {-1: [c0 - dn_ * wd], 1: [c0 + up_ * wd]}
    for lk in s_.get("links", []):
        pts[lk["side"]] = [np.array(lk["start"]), np.array(lk["target"])]
    cl = [p for p in pts[-1][::-1]] + [c0] + pts[1]
    s_["channel"] = dict(centreline=[list(map(float, p)) for p in cl], straight_m=[0.0, 0.0])
k = "G10 the v5 run, straight axis + links as its centreline"
res["negative"][k] = gate("G10", clone(V5RUN, NEG / "G10-v5", report=r5), NEG / "G10-v5.json")
res["detected"][k] = any(v_["max_turn_deg"] > 30 for v_ in jl(NEG / "G10-v5.json")["sites"].values())
rp = json.loads(json.dumps(rep))
for s_ in rp["sites"]:
    sd = s_by[s_["site"]]; wb = math.radians(sd["water_bearing"]); wn = np.array([-math.cos(wb), math.sin(wb)])
    s_["channel"]["centreline"] = [list(np.array(p) + 10.0 * wn) for p in s_["channel"]["centreline"]]
k = "G10 the run's centreline shifted 10 m across the stream"
res["negative"][k] = gate("G10", clone(O, NEG / "G10-shift", report=rp), NEG / "G10-shift.json")
res["detected"][k] = any(v_["dry_samples"] > 0 or v_["errors"] for v_ in jl(NEG / "G10-shift.json")["sites"].values())
# G11: the positive fails at every site (grid limit, see wiggle_bound.py); its own control: a 1.5 m sawtooth on the 015-42
# banks must raise that site's p90 over the run's
L42 = [x for x in rep["sites"] if x["site"] == "015-42"][0]["level"]; s42 = s_by["015-42"]
rc, cc = int((12282 - s42["z"]) / 6), int(s42["x"] / 6); Hn = H.copy()
for r_ in range(rc - 8, rc + 9):
    for c_ in range(cc - 8, cc + 9):
        if abs(Hn[r_, c_] - L42) < 1.0 and (r_ + c_) % 2 == 0 and not frz[r_, c_]:
            Hn[r_, c_] += 1.5
k = "G11 sawtooth (+1.5 m on alternate bank vertices) at 015-42"
res["negative"][k] = gate("G11", clone(O, NEG / "G11-saw", terrain=Hn), NEG / "G11-saw.json")
res["detected"][k] = jl(NEG / "G11-saw.json")["sites"]["015-42"]["p90"] > jl(G / "G11.json")["sites"]["015-42"]["p90"] + 0.02
# G12: a cover cell dropped from the envelope; a NaN cell over the engine sea sealed
cov = np.load(COVER); cc_ = tuple(int(i) for i in np.argwhere(np.isfinite(cov))[0]); en = env.copy(); en[cc_] = np.nan
res["negative"][f"G12 cover cell {list(cc_)} dropped from the envelope"] = gate("G12", clone(O, NEG / "G12-cover", envelope=en), NEG / "G12-cover.json")
mn = np.minimum(np.minimum(H[:-1, :-1], H[:-1, 1:]), np.minimum(H[1:, :-1], H[1:, 1:]))
sc = tuple(int(i) for i in np.argwhere(~np.isfinite(env) & (mn < 0.75) & (mn > 0.0))[0]); en = env.copy(); en[sc] = 1.5
k = f"G12 cell {list(sc)} over the engine sea sealed at 1.5 m"
res["negative"][k] = gate("G12", clone(O, NEG / "G12-sea", envelope=en), NEG / "G12-sea.json")
res["detected"][k] = list(sc) in jl(NEG / "G12-sea.json")["added_over_sea"]
# ================= review 1 of EV112 (18-10) =================
# NaN height: the tool must refuse it (no output) and G8 must FAIL on a run carrying it
z_in = np.load(TIN); arr_in = {k_: z_in[k_] for k_ in z_in.files}; hn = arr_in["heights"].copy(); hn[34, 1315] = np.nan; arr_in["heights"] = hn
nd = NEG / "tool-nan-input"; nd.mkdir(parents=True, exist_ok=True)
if not (nd / "terrain-nan.npz").exists():
    np.savez(nd / "terrain-nan.npz", **arr_in)
with open(nd / "run.log", "w") as log:
    rc = subprocess.run([PY, "-I", "-B", str(TOOL), str(nd / "terrain-nan.npz"), str(EIN), str(SITES), *[str(nd / n) for n in NAMES]],
                        stdout=log, stderr=subprocess.STDOUT).returncode
refused = rc != 0 and not any((nd / n).exists() for n in NAMES) and "non-finite heights" in (nd / "run.log").read_text()
res["tool_refusals"]["bridges_v31 on an input with heights[34, 1315] = NaN"] = dict(returncode=rc, refused=refused,
                                                                                     outputs_written=[n for n in NAMES if (nd / n).exists()])
Hn = H.copy(); Hn[34, 1315] = np.nan
k = "G8 run heights[34, 1315] = NaN"
res["negative"][k] = gate("G8", clone(O, NEG / "G8-nan-height", terrain=Hn), NEG / "G8-nan-height.json")
res["detected"][k] = not jl(NEG / "G8-nan-height.json").get("heights_and_masks_ok", True)
# G10: coverage (empty site list; a report without 015-40) and the first v6 run (two mouths apart)
(NEG / "sites-empty.json").write_text("[]", newline="\n")
k = "G10 empty site list"
res["negative"][k] = gate("G10", O, NEG / "G10-no-sites.json", sites=NEG / "sites-empty.json")
res["detected"][k] = jl(NEG / "G10-no-sites.json")["coverage"]["sites"] == 0
rp = json.loads(json.dumps(rep)); rp["sites"] = [x for x in rp["sites"] if x["site"] != "015-40"]
k = "G10 report without 015-40"
res["negative"][k] = gate("G10", clone(O, NEG / "G10-missing", report=rp), NEG / "G10-missing.json")
res["detected"][k] = "015-40" in jl(NEG / "G10-missing.json")["coverage"]["missing"]
if PREV:
    k = "G10 the first v6 run (015-18 / 015-40 axis dry under the deck)"
    res["negative"][k] = gate("G10", PREV, NEG / "G10-prev.json")
    pv = jl(NEG / "G10-prev.json")["sites"]
    res["detected"][k] = all(not pv[x]["ends_connected"] and pv[x]["dry_samples"] > 0 for x in ("015-18", "015-40"))
    k = "G13 the first v6 run (soft wings)"
    res["negative"][k] = gate("G13", PREV, NEG / "G13-prev.json")
    res["detected"][k] = not [e for e in jl(NEG / "G13-prev.json")["sites"]["015-13"] if e["end"] == 0][0]["pass_"]
# G13: under the 015-8 end-0 wing point closest to its profile, the triangle's vertices lowered up to 1 m but kept dry
# (level + 0.05): a raise fixes it without touching the water, so the gate must FAIL that end
L8_ = [x for x in rep["sites"] if x["site"] == "015-8"][0]["level"]
W8, _ = g6.wing_points(m8, r8u, 0, m8["lo"], 1.0, L8_)
i8 = int(np.argmax(W8[:, 1] - gv.terr(H, W8[:, 0], W8[:, 2]))); v8s = gv.tri_vertices(W8[i8, 0], W8[i8, 2])
Hn = H.copy()
for v_ in v8s:
    Hn[v_] -= max(min(1.0, H[v_] - L8_ - 0.05), 0.0)
k = f"G13 015-8 end-0 wing triangle {[list(v_) for v_ in v8s]} lowered up to 1 m, kept dry"
res["negative"][k] = gate("G13", clone(O, NEG / "G13-wing", terrain=Hn), NEG / "G13-wing.json")
res["detected"][k] = not [e for e in jl(NEG / "G13-wing.json")["sites"]["015-8"] if e["end"] == 0][0]["pass_"]
# G14: the review's recipe (kit + bridge records, no pilot) staged; a bridge record twice; the pilot moved 1 cm
nop = RECS / "records-no-pilot.json"
if not nop.exists():
    json.dump(jl(KIT) + jl(O / "bridge-records.json"), open(nop, "w", newline="\n"), indent=1)
k = "G14 recipe kit + bridge-records (no pilot), staged"
res["negative"][k] = gate("G14", O, NEG / "G14-no-pilot.json", ("--merged", str(nop), "--pilot", str(PILOT), "--kit", str(KIT),
                                                                  "--stage-wrp", str(stage(nop, RECS / "stage-no-pilot")), "--base-wrp", str(RECS / "stage-base" / "baltic_trial.wrp")))
res["detected"][k] = jl(NEG / "G14-no-pilot.json")["stage"]["pilot_objects_at_pose"].get("015-15") == 0
mg = jl(MERGED); dupf = RECS / "records-dup.json"
if not dupf.exists():
    json.dump(mg + [mg[-1]], open(dupf, "w", newline="\n"), indent=1)
k = "G14 merged list with the last bridge record twice"
res["negative"][k] = gate("G14", O, NEG / "G14-dup.json", ("--merged", str(dupf), "--pilot", str(PILOT), "--kit", str(KIT)))
res["detected"][k] = any("repeated" in e_ for e_ in jl(NEG / "G14-dup.json")["errors"])
mvf = RECS / "records-pilot-moved.json"
if not mvf.exists():
    mv = json.loads(json.dumps(mg)); mv[0]["matrix"][9] += 0.01; json.dump(mv, open(mvf, "w", newline="\n"), indent=1)
k = "G14 pilot record moved 1 cm"
res["negative"][k] = gate("G14", O, NEG / "G14-moved.json", ("--merged", str(mvf), "--pilot", str(PILOT), "--kit", str(KIT)))
res["detected"][k] = any("missing" in e_ for e_ in jl(NEG / "G14-moved.json")["errors"])
res["negatives_all_fail"] = all(v_ == "FAIL" for v_ in res["negative"].values())
res["tool_refusals_ok"] = all(v_["refused"] for v_ in res["tool_refusals"].values())
res["negatives_all_detected"] = all(res["detected"].values())
json.dump(res, open(G / "summary.json", "w", newline="\n"), indent=1)
print(json.dumps(res, indent=1))

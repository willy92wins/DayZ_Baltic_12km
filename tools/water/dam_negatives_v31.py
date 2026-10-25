"""Negative controls of the dam track. Every case perturbs the positive inputs and must be rejected for the stated reason.
Gate cases (dam_gates_v31.py): rc 1, the named gate FAILs and, where given, the named predicate of that gate is false;
'isolated' cases also need every other gate to PASS. n01-n11 are the round-0 controls (integral: they may fail several
gates; n09 is the round-0 'budget - 1' recast as 'one approved vertex not moved', since the budget became the contract).
n12-n18 close the round-2 review gaps, one per gap. Tool cases: t01-t02 verify_pond_exact_v31.py (through
run_with_odol56.py) on a one-record copy of the water stage, t03-t04 dam_v31.py refusals, t05 eval_dam_probe_v31.py on
synthetic logs, t06 shows the round-2 probe expectations were wrong (a demonstration, not a control of new code).
Usage: dam_negatives_v31.py --proto DIR --base-terrain T0 --base-footprint FP0 --base-envelope E0 --base-cover C0
       --contract K --sites S --water-stage stage-report.json --water-temp DIR --old-points points.json --out DIR
proto DIR holds terrain-dam-buried.npz, bury-work/fp0/footprint.npz, dam-records.json, envelope-dam.npy, cover-dam.npy,
dam-report.json and probe/points.json of the positive run on T0."""
import argparse, json, os, shutil, struct, subprocess, sys, types
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
ap = argparse.ArgumentParser()
for k in ("proto", "base-terrain", "base-footprint", "base-envelope", "base-cover", "contract", "sites", "water-stage",
          "water-temp", "old-points", "out"):
    ap.add_argument("--" + k, required=True)
A = ap.parse_args()
out = A.out
os.makedirs(out, exist_ok=False)
T = os.path.join(A.proto, "terrain-dam-buried.npz"); FP = os.path.join(A.proto, "bury-work", "fp0", "footprint.npz")
REC = os.path.join(A.proto, "dam-records.json"); ENV = os.path.join(A.proto, "envelope-dam.npy"); COV = os.path.join(A.proto, "cover-dam.npy")
rep = json.load(open(os.path.join(A.proto, "dam-report.json")))
recs = json.load(open(REC))
con = json.load(open(A.contract))
ZTOP = 12282


def wjson(name, obj):
    p = os.path.join(out, name); json.dump(obj, open(p, "w", newline="\n"), indent=1); return p


def wterrain(name, H=None, **masks):
    z = np.load(T); a = {k: z[k].copy() for k in z.files}
    if H is not None:
        a["heights"] = H.astype(np.float32)
    a.update(masks)
    p = os.path.join(out, name); np.savez(p, **a); return p


def rc_of(x, z):
    return int(round((ZTOP - z) / 6)), int(round(x / 6))


def shifted(dx, dz, dy=0.0, drop=None):
    rr = []
    for k, r in enumerate(recs):
        if drop is not None and k == drop:
            continue
        m = list(r["matrix"]); m[9] += dx; m[10] += dy; m[11] += dz
        rr.append(dict(r, matrix=m))
    return rr


H = np.load(T)["heights"].astype(np.float64); H0 = np.load(A.base_terrain)["heights"].astype(np.float64)
cases = []   # (name, overrides, gate, predicate or None, isolated)
cases.append(("n01_base_no_dam", dict(t=A.base_terrain, fp=A.base_footprint, rec=wjson("empty.json", [])), "G1_seam", None, False))
cases.append(("n02_cut_without_dam", dict(rec=wjson("empty2.json", [])), "G1_seam", None, False))
cases.append(("n03_dam_3m_south", dict(rec=wjson("south3.json", shifted(0, -3))), "G1_seam", None, False))
cases.append(("n04_dam_3m_north", dict(rec=wjson("north3.json", shifted(0, 3))), "G1_seam", None, False))
cases.append(("n05_east_piece_missing", dict(rec=wjson("west_only.json", shifted(0, 0, drop=1))), "G1_seam", None, False))
cases.append(("n06_dam_2m_up_floating", dict(rec=wjson("up2.json", shifted(0, 0, 2.0))), "G2_seat", None, False))
cases.append(("n07_dam_3m_down_buried", dict(rec=wjson("down3.json", shifted(0, 0, -3.0))), "G2_seat", None, False))
# no abutments: abutment vertices back to the base terrain; one that is also a bury vertex keeps the highest bury height
bury = {(v[0], v[1]): v[3] for s in rep["sites"] for v in s["bury_vertices"]}
abut = {(v[0], v[1]) for s in rep["sites"] for v in s["abutment"]["vertices"]}
plain_bury = max(h for k, h in bury.items() if k not in abut)
Hn = H.copy()
for (x, z) in abut:
    r, c = rc_of(x, z)
    Hn[r, c] = plain_bury if (x, z) in bury else H0[r, c]
cases.append(("n08_no_abutments", dict(t=wterrain("noabut.npz", Hn)), "G2_seat", None, False))
Hv = H.copy(); r9, c9 = rc_of(2388, 6954); Hv[r9, c9] = H0[r9, c9]           # approved sea vertex left unmoved
cases.append(("n09_approved_vertex_not_moved", dict(t=wterrain("unmoved.npz", Hv)), "G4_frozen", "frozen_moved_is_contract", False))
Hf = H.copy(); Hf[1000, 1000] += 0.5
cases.append(("n10_vertex_moved_far", dict(t=wterrain("far.npz", Hf)), "G4_frozen", "none_far", False))
fz = np.load(FP); a = {k: fz[k] for k in fz.files}
pl = a["plane"].copy(); r, c = int((ZTOP - 6980) // 6), int(2412 // 6)      # a sea cell north of the dam
assert not np.isfinite(pl[r, c]); pl[r, c] = 1.95; a["plane"] = pl
fld = a["field"].copy(); fld[r, c] = 1.95; a["field"] = fld
pfp = os.path.join(out, "fp_over_sea.npz"); np.savez(pfp, **a)
cases.append(("n11_pond_cell_over_sea", dict(fp=pfp), "G3_water", None, False))
# --- round-2 gaps
# G3: new water far from the dam, in footprint AND envelope (the reviewer's repro: it used to PASS)
a = {k: fz[k].copy() for k in fz.files}; e = np.load(ENV).copy(); rr_, cc_ = 1000, 1000
assert not np.isfinite(e[rr_, cc_]) and H[rr_:rr_ + 2, cc_:cc_ + 2].min() > 0.75
lv = float(H[rr_:rr_ + 2, cc_:cc_ + 2].max() + 1)
for k in ("plane", "env_plane"):
    if k in a:
        a[k][rr_, cc_] = lv
a["field"][rr_, cc_] = lv
if "visible" in a:
    a["visible"][rr_, cc_] = True
e[rr_, cc_] = lv
p12f = os.path.join(out, "extra-water.npz"); np.savez(p12f, **a); p12e = os.path.join(out, "extra-envelope.npy"); np.save(p12e, e)
cases.append(("n12_new_water_far", dict(fp=p12f, env=p12e), "G3_water", "no_new_footprint", True))
# G4: the narva mask stripped at the 21 vertices (used to PASS even with budget 0)
zt = np.load(T); nv = zt["narva"].copy(); nv[H != H0] = False
cases.append(("n13_narva_mask_stripped", dict(t=wterrain("stripped.npz", narva=nv)), "G4_frozen", "arrays_unchanged", True))
# G4: sub-millimetre lowering below the base at an approved vertex (used to PASS after rounding)
Hl = H.copy(); rl, cl = 890, 402
assert H[rl, cl] != H0[rl, cl] and H0[rl, cl] == 1.0
Hl[rl, cl] = float(np.float32(H0[rl, cl] - 0.0004))
cases.append(("n14_small_lowering", dict(t=wterrain("lowered.npz", Hl)), "G4_frozen", "no_lowering", False))
# G4: a frozen narva vertex outside the list raised 0.01 m (old bed downstream, away from the seat samples)
Ho = H.copy(); ro, co = rc_of(2412, 6960); assert (ro, co) not in {(v["r"], v["c"]) for v in con["vertices"]}
Ho[ro, co] += 0.01
cases.append(("n15_frozen_outside_list", dict(t=wterrain("outside.npz", Ho)), "G4_frozen", "frozen_moved_is_contract", True))
# G4: the contract file edited (one new height + 0.01): sha256 != pinned
ct = json.loads(json.dumps(con)); ct["vertices"][0]["new"] += 0.01
cases.append(("n16_contract_tampered", dict(con=wjson("contract-tampered.json", ct)), "G4_frozen", "contracts", False))
# G4: an approved vertex 0.01 m above its approved height (contract intact)
Hm = H.copy(); Hm[r9, c9] += 0.01
cases.append(("n17_new_height_off_contract", dict(t=wterrain("offheight.npz", Hm)), "G4_frozen", "new_heights", True))
# G3: a kept envelope cell (upstream pond) changes level by 0.01 m
e2 = np.load(ENV).copy(); rk, ck = int((ZTOP - 6930) // 6), int(2420 // 6); assert np.isfinite(e2[rk, ck])
e2[rk, ck] += 0.01; p18 = os.path.join(out, "envelope-level.npy"); np.save(p18, e2)
cases.append(("n18_kept_envelope_level_changed", dict(env=p18), "G3_water", "levels_kept", True))
res = []
for name, ov, gate, pred, iso in cases:
    args = ["--terrain", ov.get("t", T), "--footprint", ov.get("fp", FP), "--records", ov.get("rec", REC),
            "--envelope", ov.get("env", ENV), "--cover", ov.get("cov", COV), "--base-terrain", A.base_terrain,
            "--base-footprint", A.base_footprint, "--base-envelope", A.base_envelope, "--base-cover", A.base_cover,
            "--contract", ov.get("con", A.contract), "--out", os.path.join(out, name + ".json"), "--label", name]
    p = subprocess.run([PY, "-I", os.path.join(HERE, "dam_gates_v31.py")] + args, capture_output=True, text=True)
    g = json.load(open(os.path.join(out, name + ".json")))["gates"]
    st = {k: v["status"] for k, v in g.items()}
    ok = p.returncode == 1 and st[gate] == "FAIL"
    if pred is not None:
        ok &= g[gate]["checks"][pred] is False
    if iso:
        ok &= all(v == "PASS" for k, v in st.items() if k != gate)
    false_preds = {k: [q for q, b in v["checks"].items() if not b] for k, v in g.items() if "checks" in v}
    res.append(dict(case=name, expected_fail=gate, predicate=pred, isolated=iso, rc=p.returncode, gates=st,
                    false_predicates=false_preds, detected=bool(ok)))
    print(name, "rc", p.returncode, st, false_preds, "DETECTED" if ok else "MISSED", flush=True)


# --- tool cases
def run(args):
    return subprocess.run([PY, "-I"] + args, capture_output=True, text=True)


tools = []
# t01/t02: verify_pond_exact on a one-record copy of the water stage
st_rep = json.load(open(A.water_stage)); inst = st_rep["added_list"][0]
raw = open(os.path.join(A.water_temp, inst["model"]), "rb").read()
sys.path.insert(0, r"C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts")
src_path = r"C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts\odol_reader.py"
src = open(src_path, encoding="utf-8").read()
anchor = "            if v >= 54:\n                mi.force_not_alpha = reader.read_uint32()\n            else:\n                mi.force_not_alpha = int(reader.read_bool())\n"
assert src.count(anchor) == 1
probe_mod = types.ModuleType("odol_probe"); probe_mod._POS = []          # the reader, also recording where the v56 bytes sit
exec(compile(src.replace(anchor, anchor + "        if v == 56:\n            _POS.append(reader.position)\n            reader.read_uint32()\n"),
             "odol_probe", "exec"), probe_mod.__dict__)
od = probe_mod.ODOL.from_bytes(raw)
assert od.version == 56 and len(probe_mod._POS) == 1, (od.version, probe_mod._POS)
extra_pos = probe_mod._POS[0]
assert raw[extra_pos:extra_pos + 4] == b"\0\0\0\0"
road_ids = [i for i, rres in enumerate(od.resolutions) if abs(rres - 3e15) <= 3e9]
assert len(road_ids) == 1
cells_ = set()
fpz = np.load(FP)
V = np.array([[q.x, q.y, q.z] for q in next(l for l in od.lods if abs(l.resolution - 3e15) <= 3e9).vertices]) + np.array(inst["position"])
for f in next(l for l in od.lods if abs(l.resolution - 3e15) <= 3e9).faces:
    tri = V[list(f.vertex_indices)]
    cells_.add((int(np.floor((ZTOP - tri[:, 2].max()) / 6 + 1e-6)), int(np.floor(tri[:, 0].min() / 6 + 1e-6))))
pl1 = np.full(fpz["plane"].shape, np.nan, np.float32); fl1 = np.full(fpz["field"].shape, np.nan, fpz["field"].dtype)
for (r_, c_) in cells_:
    pl1[r_, c_] = fpz["plane"][r_, c_]; fl1[r_, c_] = fpz["field"][r_, c_]
fp1 = os.path.join(out, "verify-footprint.npz"); np.savez(fp1, plane=pl1, field=fl1)
st1 = wjson("verify-stage.json", {"added_list": [inst]})
variants = {"original": bytes(raw)}
mut = bytearray(raw); res_off = raw.find(struct.pack("<f", od.resolutions[road_ids[0]]), 0, 4096)
assert res_off > 0
struct.pack_into("<f", mut, res_off, 2e15); variants["no-roadway-lod"] = bytes(mut)
chk = probe_mod.ODOL.from_bytes(bytes(mut))                     # the mutation hits the resolution table, nothing else
assert not any(abs(x - 3e15) <= 3e9 for x in chk.resolutions) and len(chk.resolutions) == len(od.resolutions)
mut2 = bytearray(raw); struct.pack_into("<I", mut2, extra_pos, 1); variants["v56-extra-nonzero"] = bytes(mut2)
vres = {}
for tag, data in variants.items():
    d = os.path.join(out, "verify-" + tag); os.makedirs(d); open(os.path.join(d, inst["model"]), "wb").write(data)
    o = os.path.join(out, f"verify-{tag}.json")
    p = run([os.path.join(HERE, "run_with_odol56.py"), os.path.join(HERE, "verify_pond_exact_v31.py"), st1, fp1, d, o])
    vres[tag] = dict(rc=p.returncode, result=json.load(open(o)) if os.path.exists(o) else None, stderr=p.stderr[-800:])
pos_ok = vres["original"]["rc"] == 0 and vres["original"]["result"]["pass"] is True
for tag, cname in (("no-roadway-lod", "t01_verify_model_without_roadway_lod"), ("v56-extra-nonzero", "t02_odol56_extra_bytes_nonzero")):
    r_ = vres[tag]["result"]
    ok = pos_ok and vres[tag]["rc"] == 1 and r_ is not None and r_["pass"] is False and r_["model_errors"] == 1
    tools.append(dict(case=cname, rc=vres[tag]["rc"], positive_control_rc=vres["original"]["rc"],
                      model_errors=None if r_ is None else r_["model_error_list"], detected=bool(ok)))
    print(cname, "rc", vres[tag]["rc"], "DETECTED" if ok else "MISSED", None if r_ is None else r_["model_error_list"], flush=True)
# t03/t04: dam_v31 refusals (fresh output folder each; nothing may be written)
for cname, mutate in (("t03_dam_tool_tin_changed_at_contract_vertex", "terrain"), ("t04_dam_tool_contract_tampered", "contract")):
    d = os.path.join(out, cname); os.makedirs(d)
    tin = A.base_terrain; sites = A.sites
    if mutate == "terrain":
        zb = np.load(A.base_terrain); ab = {k: zb[k].copy() for k in zb.files}
        v = con["vertices"][5]; ab["heights"][v["r"], v["c"]] += np.float32(0.01)
        tin = os.path.join(d, "t_in.npz"); np.savez(tin, **ab)
    else:
        sd = os.path.join(d, "sites"); os.makedirs(sd)
        shutil.copy(A.sites, os.path.join(sd, "sites-dam.json"))
        json.dump(ct, open(os.path.join(sd, os.path.basename(A.contract)), "w", newline="\n"), indent=1)
        sites = os.path.join(sd, "sites-dam.json")
    outs = [os.path.join(d, n) for n in ("terrain.npz", "cover.npy", "envelope.npy", "records.json", "report.json")]
    p = run([os.path.join(HERE, "dam_v31.py"), tin, A.base_cover, A.base_envelope, sites] + outs)
    msg = (p.stderr.strip().splitlines() or [""])[-1]
    ok = p.returncode != 0 and "refused" in msg and not any(os.path.exists(o) for o in outs)
    tools.append(dict(case=cname, rc=p.returncode, message=msg[:400], outputs_written=[o for o in outs if os.path.exists(o)], detected=bool(ok)))
    print(cname, "rc", p.returncode, "DETECTED" if ok else "MISSED", msg[:200], flush=True)
# t05: eval_dam_probe_v31 on synthetic logs
P = json.load(open(os.path.join(A.proto, "probe", "points.json")))
pts = P["points"]


def ideal(L):
    rows = {}
    for p in pts:
        g = p["terrain_y"]
        if p["pond_class"] == "wet" or (p["pond_class"] == "edge" and p["plane"] is not None and p["plane"] > g):
            v = dict(sea=False, pond=True, surface=p["plane"], depth=p["plane"] - g)
        elif g < L:
            v = dict(sea=True, pond=False, surface=L, depth=L - g)
        else:
            v = dict(sea=False, pond=False, surface=L, depth=L - g)
        v.update(ground=g, roadY=p["expect_roadway_y"] if p["kind"] == "crest" else g)
        rows[p["id"]] = v
    return rows


def wlog(name, rows, drop=()):
    pth = os.path.join(out, name)
    with open(pth, "w", newline="\n") as f:
        f.write("BALTIC_BRIDGE_PROBE_V2;BalticTrial\nBEGIN;%d\n" % len(rows))
        for i, v in sorted(rows.items()):
            if i in drop:
                continue
            f.write(f"P;{i};{v['ground']:.6f};{str(v['sea']).lower()};{str(v['pond']).lower()};{v['surface']:.6f};{v['depth']:.6f};{v['roadY']:.6f};1\n")
        f.write("END;%d\n" % len(rows))
    return pth


ev = []
crest_ramp = [p["id"] for p in pts if p["kind"] == "crest" and abs(p["expect_roadway_y"] - 5.0848) > 0.02 and p["expect_roadway_y"] > 4.0]
up_wet = next(p["id"] for p in pts if p["kind"] == "up" and p["pond_class"] == "wet")
shelf = next(p["id"] for p in pts if p["kind"] == "shelf" and p["tide_class"] == "never_sea")
synth = {}
synth["e00_ideal_mid_tide"] = (ideal(0.659), (), 0)
synth["e00h_ideal_high_tide"] = (ideal(0.98), (), 0)
r1 = ideal(0.659)
for i in crest_ramp:
    r1[i] = dict(r1[i], roadY=5.085)                                   # the round-2 two-height approximation
synth["e01_crest_ramp_at_flat_height"] = (r1, (), 1)
r2 = ideal(0.659); r2[up_wet] = dict(r2[up_wet], sea=True)
synth["e02_upstream_reports_sea"] = (r2, (), 1)
r3 = ideal(0.659); pl_up = next(p["plane"] for p in pts if p["id"] == up_wet)
r3[shelf] = dict(r3[shelf], pond=True, surface=pl_up, depth=pl_up - r3[shelf]["ground"])
synth["e03_downstream_reports_pond_water"] = (r3, (), 1)
synth["e04_missing_row"] = (ideal(0.659), (pts[0]["id"],), 1)
r5 = ideal(0.659)
for i in r5:
    r5[i] = dict(r5[i], sea=False)
synth["e05_no_sea_reference"] = (r5, (), 1)
for name, (rows_, drop, want_rc) in synth.items():
    lg = wlog(name + ".log", rows_, drop)
    o = os.path.join(out, name + ".json")
    p = run([os.path.join(HERE, "eval_dam_probe_v31.py"), os.path.join(A.proto, "probe", "points.json"), lg, o])
    ok = p.returncode == want_rc
    ev.append(dict(case=name, rc=p.returncode, expected_rc=want_rc, detected=bool(ok), summary=p.stdout.strip()[:300]))
    print(name, "rc", p.returncode, "OK" if ok else "WRONG", p.stdout.strip()[:200], flush=True)
tools.append(dict(case="t05_probe_evaluator", synthetic=ev, detected=all(e["detected"] for e in ev),
                  note="e00/e00h are built from the same classes the evaluator judges: they only show the mechanics; "
                       "e01-e05 show it rejects each defect"))
# t06: the round-2 points file against the synthetic truth (roadway triangles, terrain vs tide)
old = json.load(open(A.old_points))
truth = {(p["x"], p["z"]): p for p in pts}
bad_old = dict(crest=[], sea_mid=[], sea_high=[])
for o in old:
    p = truth.get((o["x"], o["z"]))
    if p is None:
        continue
    if o["kind"] == "crest" and abs(o["expect_surface_y"] - p["expect_roadway_y"]) > 0.02:
        bad_old["crest"].append(o["id"])
    if o.get("expect_sea") and p["terrain_y"] > 0.659 + 0.05:
        bad_old["sea_mid"].append(o["id"])
    if o.get("expect_sea") and p["terrain_y"] > 1.0 + 0.05:
        bad_old["sea_high"].append(o["id"])
tools.append(dict(case="t06_round2_points_contradicted", contradicted=bad_old,
                  detected=bool(bad_old["crest"] and bad_old["sea_high"])))
print("t06 round-2 points contradicted:", bad_old, flush=True)
summary = dict(gate_cases=res, tool_cases=tools,
               all_detected=all(r_["detected"] for r_ in res) and all(t["detected"] for t in tools),
               n_gate_cases=len(res), n_tool_cases=len(tools))
json.dump(summary, open(os.path.join(out, "negatives.json"), "w", newline="\n"), indent=1)
print("all detected:", summary["all_detected"])
sys.exit(0 if summary["all_detected"] else 1)

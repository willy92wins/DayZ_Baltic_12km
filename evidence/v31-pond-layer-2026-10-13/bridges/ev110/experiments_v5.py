"""Conflict experiments on bridges_v31 v5 (not product runs).
  no-deck-rows    drops the deck/strip/cap upper rows (the ramp fill may then cover the deck)
  no-water-guard  lets raises narrow the opening (no compensation, no caps)
      Usage: experiments_v5.py <mode> <tool> <terrain> <envelope> <sites> <out dir>
  deck-flush      G2 proposal, measured offline on a finished run: every wood record (upper and stack copy) moved down its
                  own Y axis by a sink: 'rise' = the whole ramp rise (flat roadway - roadway end, 2.21 m: the flat deck
                  where the ramp ends lay), 'leg' = the roadway rise at the first leg (the ramp up to its first leg goes
                  into the ground and the road meets the ramp there), as Chernarus seats wood_25 (census of 66 ends:
                  terrain above the ramp roadway at 65). Terrain, envelope and report unchanged; writes the moved records
                  and deck-flush.json (ramp air, ramp burial, flat-deck clearance, roadway above water, legs, G1/G2/G4).
      Usage: experiments_v5.py deck-flush <run dir> <sites> <out dir> [rise|leg]"""
import json, shutil, sys, importlib.util
sys.dont_write_bytecode = True
from pathlib import Path
import numpy as np
mode = sys.argv[1]
if mode in ("no-deck-rows", "no-water-guard"):
    tool = sys.argv[2]
    spec = importlib.util.spec_from_file_location("b5", tool); b5 = importlib.util.module_from_spec(spec); spec.loader.exec_module(b5)
    if mode == "no-deck-rows":
        orig = b5.build_rows
        def br(geo, ctx, Hf):
            r = orig(geo, ctx, Hf); r["ub"] = np.where(np.isin(r["kind"], ["deck", "strip", "cap"]), np.inf, r["ub"]); return r
        b5.build_rows = br
    else:
        b5.compensate = lambda Hc, c, ts, target, *a, **k: (Hc, [])
        b5.FIT_ROUNDS = 1
    out = Path(sys.argv[6]); out.mkdir(parents=True, exist_ok=True)
    sys.argv = ["x", *sys.argv[3:6], *[str(out / n) for n in ("terrain-br.npz", "envelope-br.npy", "bridge-records.json", "bridge-report.json")]]
    b5.main()
elif mode == "deck-flush":
    sys.path.insert(0, str(Path(__file__).resolve().parent)); import gates_v5 as gv
    src, sites, out = Path(sys.argv[2]), json.load(open(sys.argv[3])), Path(sys.argv[4]); out.mkdir(parents=True, exist_ok=True)
    sink = sys.argv[5] if len(sys.argv) > 5 else "rise"
    def sink_m(m):
        if sink == "rise":
            return float(m["road"][..., 1].max() - np.mean(m["ends"]))
        _, a_leg = gv.ramp_points(m, 0); X = np.zeros((1, 3)); X[0, m["ax"]] = m["lo"] + a_leg; X[0, m["lat"]] = m["c_lat"]
        return float(gv.ray_top(m["road"], X[:, 0], X[:, 2])[0] - m["ends"][0])
    for n in ("terrain-br.npz", "envelope-br.npy", "bridge-report.json"):
        if not (out / n).exists():
            shutil.copyfile(src / n, out / n)
    rec = json.load(open(src / "bridge-records.json")); rise = {}
    for r in rec:
        m = gv.model(gv.mname(r))
        if m["name"] == "bridge_metal_25":
            continue
        rise[r["site"]] = sink_m(m)
        M = np.asarray(r["matrix"], float); r["matrix"] = [*M[:9].tolist(), *(M[9:12] - rise[r["site"]] * M[3:6]).tolist()]
    json.dump(rec, open(out / "bridge-records.json", "w", newline="\n"), indent=1)
    base, run = gv.load_run(src), gv.load_run(out); H = run["H"]; res = {}
    for sid, rr in gv.site_records(run).items():
        if sid not in rise:
            continue
        m = gv.model(gv.mname(rr["upper"][0])); L = gv.level(run, sid); top = m["road"][..., 1].max()
        flat = m["road"][m["road"][..., 1].min(1) >= top - 0.01]; row = dict(rise_m=round(rise[sid], 3), ends=[])
        for rec_, ei, e, inw in gv.outer_ends(m, rr["upper"]):
            P, a_leg = gv.ramp_points(m, ei); W = gv.world(rec_["matrix"], P); air = W[:, 1] - gv.terr(H, W[:, 0], W[:, 2])
            ramp = [T for T in m["deck"] if T[..., 1].min() < top - 1e-3 and ((T[:, m["ax"]] - e) * inw).max() < 8.0]
            bur = max(float((gv.terr(H, C[:, 0], C[:, 2]) - C[:, 1]).max()) for C in (gv.cands(gv.world(rec_["matrix"], T)) for T in ramp))
            row["ends"].append(dict(end=ei, ramp_air_max_m=round(float(air.max()), 3), ramp_roadway_buried_max_m=round(bur, 3)))
        fc = min(float((C[:, 1] - gv.terr(H, C[:, 0], C[:, 2])).min()) for rec_ in rr["upper"] for C in (gv.cands(gv.world(rec_["matrix"], T)) for T in flat))
        pc = np.zeros(3); pc[m["ax"]] = (m["lo"] + m["hi"]) / 2; pc[m["lat"]] = m["c_lat"]; pc[1] = top
        before = [r for r in base["rec"] if r["site"] == sid and not r.get("role")][0]
        row.update(flat_deck_min_clear_m=round(fc, 3),
                   roadway_above_water_m=dict(before=round(float(gv.world(before["matrix"], [pc])[0][1] - L), 3),
                                              after=round(float(gv.world(rr["upper"][0]["matrix"], [pc])[0][1] - L), 3)))
        if not rr["lower"] and m["name"] not in gv.VARIANT_MODELS:
            g = [float(gv.world(rr["upper"][0]["matrix"], F)[:, 1].min() - gv.terr(H, *gv.world(rr["upper"][0]["matrix"], F)[:, [0, 2]].T).max()) for F in gv.legs(m)]
            row["legs"] = dict(n=len(g), hanging=int(sum(x > 0.05 for x in g)), max_gap_m=round(max(g), 3))
        res[sid] = row
    ok1, d1 = gv.g1(run); ok2, d2 = gv.g2(run); ok4, d4 = gv.g4(run, sites)
    for sid, d in d4["sites"].items():
        if sid in res:
            res[sid]["legs"] = {k: d[k] for k in ("upper_hanging", "upper_max_gap_m") if k in d} if "spans" not in d else \
                {k: d["spans"][0][k] for k in ("lower_hanging", "lower_max_gap_m", "upper_hanging", "upper_max_gap_m", "zfighting_pairs")}
    summary = dict(rule=f"deck-flush proposal (offline, terrain unchanged): wood records moved down Y by the sink '{sink}'", sites=res,
                   G1=dict(verdict="PASS" if ok1 else "FAIL", min_clearance_m=d1["min_clearance_m"]),
                   G2_wood=dict(verdict="PASS" if all(e["pass_"] for ends in d2["sites"].values() for e in ends if e["kind"] == "ramp") else "FAIL",
                                ends={sid: [e["max_air_m"] for e in ends] for sid, ends in d2["sites"].items() if ends[0]["kind"] == "ramp"}),
                   G4=dict(verdict="PASS" if ok4 else "FAIL"))
    json.dump(summary, open(out / "deck-flush.json", "w", newline="\n"), indent=1)
    print(json.dumps(summary, indent=1))
else:
    raise SystemExit(f"unknown mode {mode}")

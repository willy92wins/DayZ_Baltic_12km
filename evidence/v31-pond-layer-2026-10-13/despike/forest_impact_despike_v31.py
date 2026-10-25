"""Forest records against a re-shaped terrain (despike review 1, D2: re-seating the EV111 forest in Y alone leaves 8 of
44,957 instances inside the forest water exclusion). Re-seats every record on the new planar terrain and re-runs the
terrain-dependent exclusions of tools/vegetation/forest_v31.py with that module's own functions and constants:
  slope   planar slope at the origin <= model_limits()[model]                       (exact_ok, "slope")
  water   ring_wet(H, plane, env_plane, origin, r), r = REED_WATER for reeds, else base_radius_plan x the model's
          largest Livonia scale + WATER_EXTRA; + SAFETY                               (exact_ok, "water_or_sea")
  trunk   conifer, broadleaf, bush: trunk_drop(H, origin, trunk_radius x scale x 1.02) <= embed x scale - 0.005
                                                                                      (place_sector, "trunk_drop")
  road    RoadFootprint.clear(models, M, T, scale, H): Geometry LOD faces in the vehicle band vs the road axes
                                                                                      (place_sector, "road_geometry")
Plan-only exclusions (road origin distance, bridge and kit hulls and cells, narva, sector polygon) depend on x and z,
which re-seating does not move; they are not re-run. A new stage WRP or new kit/bridge masks need a fresh forest_v31
placement, not this check.
Record: matrix = model X, Y, Z axes as columns (scale included), then the position T; origin = T - M . bc (forest_v31
transforms()); scale = |M column|.
Verdicts:
  BASELINE      the records as given on --before: every origin within 1e-3 m of the planar terrain and 0 failures
                (otherwise this check does not reproduce the placement: FAIL).
  RESEAT_ONLY   the records re-seated in Y on --after: failures counted and listed (information: it says whether a Y
                re-seat alone is enough; for EV111 on the despiked EV110 it is not).
  REVALIDATED   records-revalidated.json (re-seated, every failing record removed) re-checked from the written file on
                --after: 0 failures.
  NEG           a passing record moved into a pond cell (all 4 corners 0.2 m or more below its plane) must fail the water check.
Exit 0 only if BASELINE PASS, REVALIDATED PASS and NEG DETECTED.
Usage: forest_impact_despike_v31.py --before T0.npz --after T1.npz --footprint fp.npz --records records.json
       --reference livonia-reference-v31.json --out DIR [--no-road-geometry] [--forest-dir <worktree>/tools/vegetation]
"""
import argparse, hashlib, json, os, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
fv = None   # tools/vegetation/forest_v31.py, imported in main() from --forest-dir


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def unpack(recs, ref_models):
    names = np.array([r["model"] for r in recs], object)
    m = np.array([r["matrix"] for r in recs], float)
    M = m[:, :9].reshape(-1, 3, 3).transpose(0, 2, 1)
    T = m[:, 9:12].copy()
    s = np.linalg.norm(M[:, :, 0], axis=1)
    bc = np.array([ref_models[n]["bc"] for n in names], float)
    origin = T - np.einsum("nij,nj->ni", M, bc)
    return names, M, T, s, origin


def check(H, plane, env, names, M, T, s, origin, ref_models, lim, road):
    x, z = origin[:, 0], origin[:, 2]
    fam = np.array([ref_models[n]["family"] for n in names], object)
    fails = {}
    _, sl, _, _ = fv.tri_eval(H, x, z)
    fails["slope"] = sl > np.array([lim[n] for n in names])
    cap = np.array([ref_models[n]["scale_q"][-1] for n in names])
    base_r = np.array([ref_models[n]["base_radius_plan"] for n in names]) * cap
    mw = np.where(fam == "reed", fv.REED_WATER, base_r + fv.WATER_EXTRA) + fv.SAFETY
    fails["water_or_sea"] = fv.ring_wet(H, plane, env, x, z, mw)
    solid = np.isin(fam, ["conifer", "broadleaf", "bush"])
    tr = np.array([ref_models[n]["trunk_radius"] for n in names]) * s * 1.02
    emb = np.array([-min(ref_models[n]["visual_bottom_local"], 0.0) for n in names]) * s
    fails["trunk_drop"] = solid & (fv.trunk_drop(H, x, z, tr) > emb - 0.005)
    if road is not None:
        fails["road_geometry"] = ~road.clear(list(names), M, T, s, H)
    anyf = np.zeros(len(names), bool)
    for v in fails.values():
        anyf |= v
    return anyf, {k: int(v.sum()) for k, v in fails.items()}, fails


def main():
    ap = argparse.ArgumentParser()
    for k in ("before", "after", "footprint", "records", "reference", "out"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--no-road-geometry", action="store_true")
    ap.add_argument("--forest-dir", default=str(HERE.parents[2] / "tools" / "vegetation"),
                    help="folder of forest_v31.py (default: <worktree>/tools/vegetation next to this evidence folder)")
    o = ap.parse_args()
    global fv
    sys.path.insert(0, o.forest_dir)
    import forest_v31
    fv = forest_v31
    os.makedirs(o.out, exist_ok=False)
    H0 = np.load(o.before)["heights"].astype(np.float64)
    H1 = np.load(o.after)["heights"].astype(np.float64)
    fp = np.load(o.footprint)
    plane, env = fp["plane"], fp["env_plane"]
    ref_models = json.loads(Path(o.reference).read_text(encoding="utf-8"))["models"]
    lim = fv.model_limits(ref_models)
    recs = json.loads(Path(o.records).read_text(encoding="utf-8"))
    names, M, T, s, origin = unpack(recs, ref_models)
    road = None if o.no_road_geometry else fv.RoadFootprint(sorted(set(names.tolist())))
    rep = dict(schema="forest-impact-despike-v31.v2", records=o.records, records_sha256=sha(o.records), n=len(recs),
               before=o.before, before_sha256=sha(o.before), after=o.after, after_sha256=sha(o.after),
               footprint=o.footprint, footprint_sha256=sha(o.footprint), reference_sha256=sha(o.reference),
               forest_tool_sha256=sha(fv.__file__), road_geometry=road is not None)
    # baseline
    h0, _, _, _ = fv.tri_eval(H0, origin[:, 0], origin[:, 2])
    seat_err = float(np.abs(origin[:, 1] - h0).max())
    f0, c0, _ = check(H0, plane, env, names, M, T, s, origin, ref_models, lim, road)
    base_ok = seat_err <= 1e-3 and not f0.any()
    rep["BASELINE"] = dict(ok=bool(base_ok), origin_seat_max_err_m=seat_err, failures=int(f0.sum()), by_check=c0)
    # re-seat in Y on the new terrain
    h1, _, _, _ = fv.tri_eval(H1, origin[:, 0], origin[:, 2])
    dy = h1 - h0
    T1 = T.copy(); T1[:, 1] += dy
    o1 = origin.copy(); o1[:, 1] += dy
    f1, c1, why1 = check(H1, plane, env, names, M, T1, s, o1, ref_models, lim, road)
    rep["RESEAT_ONLY"] = dict(failures=int(f1.sum()), by_check=c1, moved_gt_1cm=int((np.abs(dy) > 0.01).sum()),
                              dY_min=float(dy.min()), dY_max=float(dy.max()),
                              failed=[dict(index=int(i), model=str(names[i]), origin_xz=[round(float(origin[i, 0]), 3), round(float(origin[i, 2]), 3)],
                                           dY=round(float(dy[i]), 4), checks=[k for k, v in why1.items() if v[i]]) for i in np.flatnonzero(f1)])
    out_all = [dict(model=recs[i]["model"], matrix=list(recs[i]["matrix"][:9]) + [float(v) for v in T1[i]]) for i in range(len(recs))]
    kept = [out_all[i] for i in np.flatnonzero(~f1)]
    for nm, data in (("records-reseated.json", out_all), ("records-revalidated.json", kept)):
        (Path(o.out) / nm).write_bytes((json.dumps(data, indent=0) + "\n").encode("ascii"))
    # re-check the written file
    p2 = str(Path(o.out) / "records-revalidated.json")
    recs2 = json.loads(Path(p2).read_text(encoding="utf-8"))
    n2, M2, T2, s2, or2 = unpack(recs2, ref_models)
    h2, _, _, _ = fv.tri_eval(H1, or2[:, 0], or2[:, 2])
    f2, c2, _ = check(H1, plane, env, n2, M2, T2, s2, or2, ref_models, lim, road)
    err2 = float(np.abs(or2[:, 1] - h2).max()) if len(recs2) else 0.0
    rep["REVALIDATED"] = dict(ok=bool(not f2.any() and err2 <= 1e-3 and len(recs2) == int((~f1).sum())), n=len(recs2),
                              removed=int(f1.sum()), failures=int(f2.sum()), by_check=c2, origin_seat_max_err_m=err2,
                              sha256=sha(p2), reseated_sha256=sha(str(Path(o.out) / "records-reseated.json")))
    # negative control: a passing record moved onto a pond vertex
    pl = np.nan_to_num(plane, nan=-1e9) - 0.2      # cell array: cell (r, c) has corners (r..r+1, c..c+1)
    rr, cc = np.nonzero(np.isfinite(plane) & (H1[:-1, :-1] < pl) & (H1[:-1, 1:] < pl) & (H1[1:, :-1] < pl) & (H1[1:, 1:] < pl))
    k = int(np.flatnonzero(~f1)[0]); j = len(rr) // 2
    dx = 6.0 * cc[j] + 2.0 - origin[k, 0]; dz = (12282.0 - 6.0 * rr[j] - 4.0) - origin[k, 2]
    oN = o1[k:k + 1].copy(); TN = T1[k:k + 1].copy()
    oN[:, 0] += dx; oN[:, 2] += dz; TN[:, 0] += dx; TN[:, 2] += dz
    hN, _, _, _ = fv.tri_eval(H1, oN[:, 0], oN[:, 2]); TN[:, 1] += hN - oN[:, 1]; oN[:, 1] = hN
    fN, cN, _ = check(H1, plane, env, names[k:k + 1], M[k:k + 1], TN, s[k:k + 1], oN, ref_models, lim, road)
    rep["NEG"] = dict(detected=bool(fN[0] and cN["water_or_sea"] == 1), record=k, model=str(names[k]),
                      moved_to_xz=[round(float(oN[0, 0]), 3), round(float(oN[0, 2]), 3)], by_check=cN)
    allok = rep["BASELINE"]["ok"] and rep["REVALIDATED"]["ok"] and rep["NEG"]["detected"]
    rep["overall"] = "PASS" if allok else "FAIL"
    with open(os.path.join(o.out, "report.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    print("BASELINE:", "PASS" if rep["BASELINE"]["ok"] else "FAIL", json.dumps({k_: v for k_, v in rep["BASELINE"].items() if k_ != "ok"}))
    print("RESEAT_ONLY:", f"{rep['RESEAT_ONLY']['failures']} failing of {len(recs)}", json.dumps(c1),
          json.dumps(rep["RESEAT_ONLY"]["failed"][:10]))
    print("REVALIDATED:", "PASS" if rep["REVALIDATED"]["ok"] else "FAIL", json.dumps({k_: v for k_, v in rep["REVALIDATED"].items() if k_ != "ok"}))
    print("NEG:", "DETECTED" if rep["NEG"]["detected"] else "MISSED", json.dumps(rep["NEG"]))
    print("OVERALL:", rep["overall"])
    sys.exit(0 if allok else 1)


if __name__ == "__main__":
    main()

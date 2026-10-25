"""G4: GEOMETRIC engine margin (roadway-LOD faces of any texture vs the native terrain). It does NOT show that the engine
reports water there: about a quarter of the samples (all joints but a few) lie on concrete_ext lips only, where the EV108
probe has no reading (it had no point off water_ext); engine acceptance is G8 (server probe log of probe_points_kit.py's
kit_lip / kit_joint points with liquid and dry controls), pending until that probe runs. Axis samples per site, inside the wet span (station on the lattice polyline from the first piece's flat
run to the last one's): the lattice polyline every 0.5 m plus its vertices, every piece's rung-midpoint centreline every 0.5 m
plus every rung point (plate ends and lip breaks), and the midpoint of every joint (consecutive pieces' overlapping ends).
Margin = highest roadway-LOD face of the kit over the sample (any texture) minus the terrain on its native triangle.
Pass when 100 % of the samples have a roadway face and margin >= 0.10 m. Also reports, per source, the samples off every water_ext
face (diagnostic for G8: the joints between flat runs are concrete_ext lips in Chernarus too).
Usage: gate_g4_engine_margin.py [run_dir]"""
import json, os, sys
import numpy as np
sys.dont_write_bytecode = True; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatelib as G
run = sys.argv[1] if len(sys.argv) > 1 else G.OUT
models, recs, rep, H, sites, pieces = G.load(run)
ok_all = True; out = {}
for sid, S in sites.items():
    P = pieces[sid]; V = np.array(S["lattice"]); span = S["wet_span"]
    cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(V, axis=0), axis=1))]
    pts, src = [G.at(V, np.r_[np.arange(0, cum[-1], 0.5), cum])], ["lattice"]
    for p in P:
        C = p.world(p.centre_model)
        R, _ = G.resample(C, 0.5)
        pts.append(np.vstack([R[:, [0, 2]], C[:, [0, 2]]])); src.append(p.kind)
    joint_pts = []
    order = sorted(P, key=lambda p: p.rec["station"][0])
    for a, b in zip(order[:-1], order[1:]):
        joint_pts.append(G.at(V, [0.5 * (a.rec["station"][1] + b.rec["station"][0])])[0])
    if joint_pts:
        pts.append(np.array(joint_pts)); src.append("joint")
    labels = np.concatenate([[s] * len(a) for s, a in zip(src, pts)]); A = np.vstack(pts)
    _, st = G.project(V, A)
    keep = (st >= span[0] - 1e-6) & (st <= span[1] + 1e-6)
    A, labels = A[keep], labels[keep]
    road = G.surface(P, A, "road"); ext = G.surface(P, A, "road_ext")
    ty = G.terrain_y(H, A[:, 0], A[:, 1]); m = road - ty
    bad = ~np.isfinite(road) | (m < 0.10)
    passed = not bad.any(); ok_all &= passed
    by = {k: dict(samples=int((labels == k).sum()), min=round(float(m[labels == k].min()), 4)) for k in sorted(set(labels))}
    out[sid] = dict(samples=len(A), no_roadway=int((~np.isfinite(road)).sum()), below_0p10=int(bad.sum()), margin_min=round(float(m.min()), 4),
                    margin_p10_50_90=np.percentile(m, [10, 50, 90]).round(3).tolist(), by_source=by,
                    water_ext_only_share_ge_0p10=round(float(((ext - ty) >= 0.10).mean()), 3), engine_water_verified=False,
                    off_water_ext={k: int(((labels == k) & ~np.isfinite(ext)).sum()) for k in sorted(set(labels))},
                    worst=[dict(xz=A[i].round(2).tolist(), src=str(labels[i]), margin=round(float(m[i]), 4)) for i in np.argsort(m)[:5]], passed=passed)
    print(sid, json.dumps(out[sid]))
json.dump(out, open(run + "/gate-g4.json", "w"), indent=1)
print("G4", "PASS (geometric margin only; engine water: G8)" if ok_all else "FAIL")
sys.exit(0 if ok_all else 1)

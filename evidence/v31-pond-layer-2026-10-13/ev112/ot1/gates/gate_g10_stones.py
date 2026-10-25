"""G10 (EV112): stones placed like Chernarus, independent of the generator: the visual LOD (resolution closest to 1.0) is read
from the ODOL on P: (as the stone check of 17-10, scratchpad stones_check.py), not from streambed_stones_geometry_v31.json.
Per stone record: world vertices = V . M^T + T; base ring = the vertices at or below the 10th percentile of WORLD y; base gap
= max over the base ring of (y - terrain on its native triangle) on <run>/terrain-kit.npz; q = distance of the origin to the
nearest point of the rung-midpoint centrelines (every 0.25 m) of ALL kit pieces; blocking = share of the LOD vertices that stand
over visible kit water (water-proxy face above the terrain) AND above that water; ribbon = such a vertex within 0.6 m of a
centreline. Chernarus reference (same definitions, 572 stones within 30 m of 1,639 pieces, scratchpad ev112-kit/chern-stones.json):
q p25/p50/p75 1.058/2.049/3.230 m; base gap p50 -0.011, p90 0.493.
Pass (all stones): base gap p50 <= 0.0 m and p90 <= 0.25 m (the orchestrator's gate of 17-10); q p50 within [1.058, 3.230];
every stone: at least 25 percent of ALL visual-LOD vertices above terrain; blocking <= 0.25 (Chernarus p90 0.245), no ribbon vertex, no vertex over a triangle with a reserve/platform/narva/
v31_bridge_cut vertex, no vertex over kept pond water (an envelope cell of the output whose plane is above the terrain there);
every built site: stones within [0.9 n, n], n = round(wet span km x 17) (Chernarus 17.0 per km).
Usage: gate_g10_stones.py [run_dir]   (negative controls: a copy of the EV110 kit outputs, v8 stones, must FAIL)"""
import json, os, sys
from collections import defaultdict
import numpy as np
from scipy.spatial import cKDTree
sys.dont_write_bytecode = True; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatelib as G
sys.path.insert(0, r"C:/Users/guill/.claude/skills/dayz-p3d-debinarizer/scripts")
from odol_reader import ODOL
run = sys.argv[1] if len(sys.argv) > 1 else G.OUT
models = json.load(open(G.GEOM))["models"]
recs = json.load(open(run + "/kit-records.json"))
rep = json.load(open(run + "/kit-report.json"))
zt = np.load(run + "/terrain-kit.npz"); H = zt["heights"].astype(np.float64)
frozen = zt["reserve"] | zt["platform"] | zt["narva"] | zt["v31_bridge_cut"]
ftri = frozen[:-1, :-1] | frozen[:-1, 1:] | frozen[1:, :-1] | frozen[1:, 1:]
env = np.load(run + "/envelope-ev108.npy").astype(np.float64)
pieces = [G.Piece(r, models) for r in recs if r["piece"] != "stones"]
by_site = defaultdict(list)
for p in pieces:
    by_site[p.rec["site"]].append(p)
C = []
for p in pieces:
    Cw = p.world(p.centre_model); R, _ = G.resample(Cw, 0.25); C.append(R[:, [0, 2]])
tree = cKDTree(np.vstack(C))
cache = {}


def lodv(model):
    if model not in cache:
        od = ODOL.from_file("P:/" + model.replace("\\", "/").replace("dz/", "DZ/", 1))
        l = min(od.lods, key=lambda l: abs(l.resolution - 1.0))
        cache[model] = np.array([(p.x, p.y, p.z) for p in l.vertices], float)
    return cache[model]


def cell_of(P):
    c = np.clip(np.floor(P[:, 0] / 6.0).astype(int), 0, 2046); r = np.clip(np.floor((G.ZTOP - P[:, 1]) / 6.0).astype(int), 0, 2046)
    return r, c


rows = []
for r in recs:
    if r["piece"] != "stones":
        continue
    m = r["matrix"]; M = np.array([m[0:3], m[3:6], m[6:9]], float).T; T = np.array(m[9:12], float)
    if not np.isfinite(M).all() or not np.isfinite(T).all():
        rows.append(dict(site=r["site"], bad_matrix=True)); continue
    W = lodv(r["model"]) @ M.T + T
    g = G.terrain_y(H, W[:, 0], W[:, 2])
    low = W[:, 1] <= np.percentile(W[:, 1], 10)
    sp = [p for p in pieces if p.lo[0] - 8 <= T[0] <= p.hi[0] + 8 and p.lo[1] - 8 <= T[2] <= p.hi[1] + 8]
    wy = G.surface(sp, W[:, [0, 2]], "water") if sp else np.full(len(W), -np.inf)
    above = (wy > g) & (W[:, 1] > wy)
    dq = tree.query(W[:, [0, 2]])[0]
    rr, cc = cell_of(W[:, [0, 2]])
    pond = np.isfinite(env[rr, cc]) & (env[rr, cc] > g)
    rows.append(dict(site=r["site"], model=r["model"].split("\\")[-1], x=round(float(T[0]), 2), z=round(float(T[2]), 2),
                     base_gap_max=float((W[low, 1] - g[low]).max()), q=float(tree.query(T[[0, 2]])[0]),
                     visible_share=float((W[:, 1] > g).mean()), blocking=float(above.mean()), ribbon=int((above & (dq < 0.6)).sum()), frozen_tri=int(ftri[rr, cc].sum()),
                     over_pond=int(pond.sum()), sink=float(T[1] - G.terrain_y(H, T[0], T[2]))))
fails = defaultdict(list)
ok_rows = [x for x in rows if not x.get("bad_matrix")]
if len(ok_rows) != len(rows):
    fails["bad_matrix"].append(len(rows) - len(ok_rows))
gap = np.array([x["base_gap_max"] for x in ok_rows]); q = np.array([x["q"] for x in ok_rows])
res = dict(stones=len(rows))
if len(ok_rows):
    res.update(base_gap_p10_50_90_max=np.percentile(gap, [10, 50, 90, 100]).round(3).tolist(), q_p10_25_50_75_90=np.percentile(q, [10, 25, 50, 75, 90]).round(3).tolist(),
               sink_p10_50_90=np.percentile([x["sink"] for x in ok_rows], [10, 50, 90]).round(3).tolist(),
               blocking_p50_90_max=np.percentile([x["blocking"] for x in ok_rows], [50, 90, 100]).round(3).tolist())
    if not np.percentile(gap, 50) <= 0.0:
        fails["base_gap_p50"].append(round(float(np.percentile(gap, 50)), 3))
    if not np.percentile(gap, 90) <= 0.25:
        fails["base_gap_p90"].append(round(float(np.percentile(gap, 90)), 3))
    if not 1.058 <= np.percentile(q, 50) <= 3.230:
        fails["q_p50_outside_chernarus_p25_p75"].append(round(float(np.percentile(q, 50)), 3))
    for x in ok_rows:
        for k, bad in (("blocking", x["blocking"] > 0.25), ("ribbon", x["ribbon"] > 0), ("frozen_triangle", x["frozen_tri"] > 0),
                       ("over_pond", x["over_pond"] > 0), ("visibility_below_25_percent", x["visible_share"] < 0.25)):
            if bad:
                fails[k].append([x["site"], x["x"], x["z"]])
else:
    fails["no_stones"].append(0)
per_site = {}
for s in rep["sites"]:
    if "skipped" in s:
        continue
    n = int(round((s["wet_span"][1] - s["wet_span"][0]) * 17.0 / 1000.0))
    k = sum(1 for x in rows if x["site"] == s["site"])
    per_site[s["site"]] = dict(wet_span_m=round(s["wet_span"][1] - s["wet_span"][0], 1), target=n, stones=k,
                               per_km=round(k / max(s["wet_span"][1] - s["wet_span"][0], 1e-9) * 1000, 1))
    if not (0.9 * n - 1e-9 <= k <= n):
        fails["density"].append([s["site"], k, n])
res.update(per_site=per_site, failures={k: dict(n=len(v), first=v[:8]) for k, v in fails.items()}, passed=not fails)
json.dump(dict(res, rows=rows), open(run + "/gate-g10.json", "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "per_site"}))
print("G10", "PASS" if res["passed"] else "FAIL")
sys.exit(0 if res["passed"] else 1)

"""How Chernarus dresses its thin streams: stones_* and p_phragmites around stream_14 and streambed pieces.
Per object: nearest piece centre (<= 30 m), lateral offset q along the piece's model X, along-offset t along model Z,
sink = object y - terrain y, yaw relative to the stream axis, scale = |model X axis|."""
import sys, json
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, r"E:/DayZ-Baltic-Build/vanilla-tricks-20261013/scripts")
from terrain import Terrain, objects
T = Terrain("chernarus")
rows = objects("chernarus")
def fam(s):
    s = s.lower()
    if "\streambed\misc\stones_" in s: return "stones"
    if "\streambed\\" in s: return "streambed"
    if "\streams\stream_14" in s: return "stream_14"
    if "p_phragmites" in s: return "reed"
    if "t_salixalba" in s: return "willow"
    return None
by = {}
for r in rows:
    f = fam(r["shape"])
    if f: by.setdefault(f, []).append(r)
print({k: len(v) for k, v in by.items()})
out = {}
for net in ("streambed", "stream_14"):
    P = by[net]
    C = np.array([[o["x"], o["z"]] for o in P])
    X = np.array([[o["ax_x"], o["ax_z"]] for o in P]); X /= np.linalg.norm(X, axis=1)[:, None]
    Z = np.array([[o["az_x"], o["az_z"]] for o in P]); Z /= np.linalg.norm(Z, axis=1)[:, None]
    tree = cKDTree(C)
    length_km = len(P) * 0.020   # ~20-24 m per piece, rough
    res = {"pieces": len(P), "length_km_rough": round(length_km, 1)}
    for f in ("stones", "reed", "willow"):
        O = by[f]; Pp = np.array([[o["x"], o["z"]] for o in O])
        d, i = tree.query(Pp, distance_upper_bound=30)
        ok = np.isfinite(d)
        v = Pp[ok] - C[i[ok]]
        q = np.abs((v * X[i[ok]]).sum(1)); t = (v * Z[i[ok]]).sum(1)
        ys = np.array([o["y"] for o in O])[ok]; ty = T.y(Pp[ok, 0], Pp[ok, 1]); sink = ys - ty
        ox = np.array([[o["ax_x"], o["ax_z"]] for o in O])[ok]; sc = np.linalg.norm(np.array([[o["ax_x"], o["ax_y"], o["ax_z"]] for o in O])[ok], axis=1)
        oz = np.array([[o["az_x"], o["az_z"]] for o in O])[ok]; oz /= np.linalg.norm(oz, axis=1)[:, None]
        rel = np.degrees(np.arccos(np.clip(np.abs((oz * Z[i[ok]]).sum(1)), 0, 1)))
        pct = lambda a: [round(float(x), 2) for x in np.percentile(a, [10, 50, 90])] if len(a) else None
        res[f] = dict(n_within_30m=int(ok.sum()), per_km=round(ok.sum() / length_km, 1), q_p10_50_90=pct(q),
                      n_q_le_10=int((q <= 10).sum()), sink_p10_50_90=pct(sink), scale_p10_50_90=pct(sc), yaw_rel_axis_p10_50_90=pct(rel))
    out[net] = res
# reeds: global share near any stream/water piece; nearest-neighbour spacing within clusters
R = np.array([[o["x"], o["z"]] for o in by["reed"]]); tr = cKDTree(R); dd, _ = tr.query(R, k=2)
out["reed_nn_spacing_p10_50_90"] = [round(float(x), 2) for x in np.percentile(dd[:, 1], [10, 50, 90])]
S = by["stones"]; names = {}
for o in S: names[o["shape"].split("\\")[-1]] = names.get(o["shape"].split("\\")[-1], 0) + 1
out["stones_models"] = names
json.dump(out, open(r"E:/DayZ-Baltic-Build/vanilla-tricks-20261013/data/bank_dressing_orch.json", "w", newline="\n"), indent=1)
print(json.dumps(out, indent=1))

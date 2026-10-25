"""Negative controls of gate_causeway.py: each perturbed output must FAIL (exit 1) on the gate named in EXPECT.
Geometric cases come with an honest report (its output hash is the perturbed file's), so G0 does not mask them.
Usage: negatives.py <gate_causeway.py> <before.npz> <before_fp.npz> <after.npz> <cover.npy> <envelope.npy> <report.json>
       <spec.json> <tools_dir> <out_dir>"""
import copy, hashlib, json, os, subprocess, sys
import numpy as np

gate, before, before_fp, after, cover, env, report, spec_p, tools, out = sys.argv[1:11]
os.makedirs(out, exist_ok=False)
sys.path.insert(0, os.path.join(tools, "terrain"))
from verify_roads_v30 import road_chains  # noqa: E402
py = sys.executable
zb, za = np.load(before), np.load(after)
A = {k: za[k] for k in za.files}
Hb, Ha = zb["heights"].astype(np.float64), za["heights"].astype(np.float64)
ch = A["v31_causeway"]
rep = json.load(open(report, encoding="utf-8"))
spec = json.load(open(spec_p, encoding="utf-8"))
ZTOP = 12282.0
rr, cc = np.nonzero(ch)
xs, zs = 6.0 * cc, ZTOP - 6.0 * rr
chains = road_chains()


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def station(chain, x, z):
    """Station, distance and side (+1 left) of points on a road chain (densified to 0.25 m)."""
    raw = chains[chain]
    s = np.r_[0.0, np.cumsum(np.hypot(*np.diff(raw, axis=0).T))]
    t = np.arange(0, s[-1], 0.25)
    q = np.column_stack([np.interp(t, s, raw[:, 0]), np.interp(t, s, raw[:, 1])])
    from scipy.spatial import cKDTree
    d, j = cKDTree(q).query(np.column_stack([x, z]))
    g = np.gradient(q, axis=0)
    v = np.column_stack([x, z]) - q[j]
    side = np.sign(g[j, 0] * v[:, 1] - g[j, 1] * v[:, 0])
    return t[j], d, side


def write(name, H, extra=None):
    arr = dict(A)
    if extra:
        arr.update(extra)
    h32 = H.astype(np.float32)
    arr["heights"] = h32
    arr["v31_causeway"] = h32 != zb["heights"]
    p = os.path.join(out, name + ".npz")
    np.savez(p, **arr)
    return p


def honest(name, terrain, edit=None):
    r = copy.deepcopy(rep)
    r["output"]["terrain_sha256"] = sha(terrain)
    if edit:
        edit(r)
    p = os.path.join(out, name + "-report.json")
    json.dump(r, open(p, "w", encoding="utf-8"), indent=1)
    return p


# which causeway owns each changed vertex: the nearer road chain
s104, d104, side104 = station(104, xs, zs)
s62, d62, side62 = station(62, xs, zs)
own62 = d62 < d104
cases = []
# n1: the terrain before the pass (no causeway rule)
p = write("n1_no_pass", Hb); cases.append(("n1_no_pass", p, honest("n1_no_pass", p), spec_p, ["G1"]))
# n2: one platform vertex next to the causeway raised 5 cm
H = Ha.copy(); pr, pc = np.nonzero(zb["platform"][255:290, 1160:1260]); H[255 + pr[0], 1160 + pc[0]] += 0.05
p = write("n2_platform", H); cases.append(("n2_platform", p, honest("n2_platform", p), spec_p, ["G3"]))
# n3: teeth: every 3rd changed vertex within 0.4 m of the sea level raised 0.3 m
H = Ha.copy(); near = np.nonzero(np.abs(Ha[rr, cc] - 0.75) < 0.4)[0][::3]
H[rr[near], cc[near]] += 0.3
p = write("n3_teeth", H); cases.append(("n3_teeth", p, honest("n3_teeth", p), spec_p, ["G1"]))
# n4: toe of c0 (chain 104) moved 1 m outward on its left over stations 1150-1250 (ramp + s * 1 m)
t0 = [t for t in rep["treated"] if t["id"] == "c0"][0]
m = (~own62) & (s104 >= 1150) & (s104 <= 1250) & (np.abs(Ha[rr, cc] - 0.75) < 1.2)
m &= side104 > 0
H = Ha.copy(); H[rr[m], cc[m]] += t0["slope_s"] * 1.0
p = write("n4_width", H); cases.append(("n4_width", p, honest("n4_width", p), spec_p, ["G2"]))
# n5: a free islet vertex with dry neighbours lowered under the sea: a new sea pocket
H = Ha.copy()
win = np.zeros(Ha.shape, bool); win[255:300, 1130:1180] = True
dry9 = np.ones(Ha.shape, bool)
for dr in (-1, 0, 1):
    for dc in (-1, 0, 1):
        dry9 &= np.roll(np.roll(Ha >= 1.0, dr, 0), dc, 1)
cand = np.argwhere(win & dry9 & ~(zb["platform"] | zb["reserve"] | zb["narva"]))
r, c = cand[len(cand) // 2]; H[r, c] = 0.5
p = write("n5_pocket", H); cases.append(("n5_pocket", p, honest("n5_pocket", p), spec_p, ["G5"]))
# n6: a footprint border vertex that also touches a non-envelope cell lowered under its plane (exposed edge)
fb = np.load(before_fp); pl = fb["plane"].astype(np.float64); fp = np.isfinite(pl)
vin = np.zeros(Hb.shape, bool); vout = np.zeros(Hb.shape, bool); vP = np.full(Hb.shape, -np.inf)
envc = np.isfinite(np.load(env)); nonenv = np.zeros(Hb.shape, bool)
for dr in (0, 1):
    for dc in (0, 1):
        vin[dr:dr + 2047, dc:dc + 2047] |= fp; vout[dr:dr + 2047, dc:dc + 2047] |= ~fp
        vP[dr:dr + 2047, dc:dc + 2047] = np.maximum(vP[dr:dr + 2047, dc:dc + 2047], np.where(fp, pl, -np.inf))
        nonenv[dr:dr + 2047, dc:dc + 2047] |= ~envc
frz = zb["platform"] | zb["reserve"] | zb["narva"]
bv = np.argwhere(vin & vout & nonenv & (Hb >= vP + 0.2) & ~frz)
r, c = bv[len(bv) // 2]; H = Ha.copy(); H[r, c] = vP[r, c] - 0.02
p = write("n6_exposed", H); cases.append(("n6_exposed", p, honest("n6_exposed", p), spec_p, ["G4"]))
# n7: an interior pond vertex lowered under the engine sea
iv = np.argwhere(vin & ~vout & ~frz & (Hb > 0.9))
r, c = iv[len(iv) // 3]; H = Ha.copy(); H[r, c] = 0.5
p = write("n7_pond_sea", H); cases.append(("n7_pond_sea", p, honest("n7_pond_sea", p), spec_p, ["G6"]))
# n8: a changed vertex raised 6 m (slopes)
H = Ha.copy(); H[rr[len(rr) // 2], cc[len(cc) // 2]] += 6.0
p = write("n8_slope", H); cases.append(("n8_slope", p, honest("n8_slope", p), spec_p, ["G7"]))
# n9 (review 1, critical): c1 (chain 62) reverted to the input and c1 omitted from the report
H = Ha.copy(); H[rr[own62], cc[own62]] = Hb[rr[own62], cc[own62]]
p9 = write("n9_reverted_c1", H)
cases.append(("n9_omit_c1", p9, honest("n9_omit_c1", p9, lambda r: r.update(treated=[t for t in r["treated"] if t["id"] != "c1"])),
              spec_p, ["G0", "G1"]))
# n10: the same terrain with an honest report (c1 listed)
cases.append(("n10_reverted_c1_honest", p9, honest("n10_reverted_c1_honest", p9), spec_p, ["G1"]))
# n11: another array of the terrain changed (cls)
cls = A["cls"].copy(); cls[1010, 1200] = (int(cls[1010, 1200]) + 1) % 255
p = write("n11_array", Ha, dict(cls=cls)); cases.append(("n11_array", p, honest("n11_array", p), spec_p, ["G3"]))
# n12: report with c0 duplicated
cases.append(("n12_duplicate", after, honest("n12_duplicate", after, lambda r: r["treated"].append(copy.deepcopy(r["treated"][0]))),
              spec_p, ["G0"]))
# n13: report with an unexpected causeway id
def add13(r):
    e = copy.deepcopy(r["treated"][0]); e["id"] = "c9"; r["treated"].append(e)
cases.append(("n13_unexpected", after, honest("n13_unexpected", after, add13), spec_p, ["G0"]))
# n14: spec with the c1 interval shrunk (and a report that agrees with it)
sp = copy.deepcopy(spec)
for c in sp["clusters"]:
    if c["id"] == "c1":
        c["s0"], c["s1"] = 200.0, 300.0
p14 = os.path.join(out, "n14_spec.json"); json.dump(sp, open(p14, "w", encoding="utf-8"), indent=1)
def e14(r):
    r["inputs"]["spec_sha256"] = sha(p14)
    for t in r["treated"]:
        if t["id"] == "c1":
            t["s0"], t["s1"] = 200.0, 300.0
cases.append(("n14_spec_shrunk", after, honest("n14_spec_shrunk", after, e14), p14, ["G0"]))
# n15: report whose input terrain is another file
cases.append(("n15_input_hash", after, honest("n15_input_hash", after, lambda r: r["inputs"].update(terrain_sha256="0" * 64)),
              spec_p, ["G0"]))
# n16: teeth only in the link beyond the run: c1 mainland end, changed vertices near the sea at stations < 87
m = own62 & (s62 < 80) & (np.abs(Ha[rr, cc] - 0.75) < 0.4)
H = Ha.copy(); idx = np.nonzero(m)[0][::2]; H[rr[idx], cc[idx]] += 0.3
p = write("n16_link_teeth", H); cases.append(("n16_link_teeth", p, honest("n16_link_teeth", p), spec_p, ["G1L"]))
# n17: a deep sea vertex 100 m from the stream crossing c3 lowered 0.1 m (no other gate sees it)
c3 = [c for c in spec["clusters"] if c["id"] == "c3"][0]
R_, C_ = np.mgrid[0:2048, 0:2048]
dist = np.hypot(6.0 * C_ - c3["x"], ZTOP - 6.0 * R_ - c3["z"])
cand = np.argwhere((dist > 60) & (dist < 120) & (Hb < -0.5) & ~frz & ~vin)
r, c = cand[0]; H = Ha.copy(); H[r, c] -= 0.1
p = write("n17_cluster_touch", H); cases.append(("n17_cluster_touch", p, honest("n17_cluster_touch", p), spec_p, ["G8"]))
res = []
for name, tp, rp, spp, expect in cases:
    o = os.path.join(out, name + "-gate.json")
    pr_ = subprocess.run([py, "-I", gate, before, before_fp, tp, cover, env, rp, spp, os.path.join(out, name + "-work"), o,
                          "--tools", tools], capture_output=True, text=True)
    g = json.load(open(o, encoding="utf-8")) if os.path.exists(o) else dict(verdict="ERROR", fails=[pr_.stderr[-800:]])
    hit = {e: any(f.startswith(e + " ") for f in g["fails"]) for e in expect}
    res.append(dict(case=name, expect=expect, exit=pr_.returncode, verdict=g["verdict"], expected_gates_failed=hit,
                    fails=g["fails"]))
    print(name, g["verdict"], pr_.returncode, "expected", expect, "hit" if all(hit.values()) else f"MISSED {hit}", flush=True)
ok = all(r["verdict"] == "FAIL" and r["exit"] == 1 and all(r["expected_gates_failed"].values()) for r in res)
json.dump(dict(cases=res, all_fail_as_expected=ok), open(os.path.join(out, "negatives.json"), "w", encoding="utf-8"), indent=1)
print("ALL NEGATIVES FAIL AS EXPECTED" if ok else "NEGATIVE CONTROL PROBLEM")
sys.exit(0 if ok else 1)

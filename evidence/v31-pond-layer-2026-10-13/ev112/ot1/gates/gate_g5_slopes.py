"""G5: terrain edits. Every native triangle with a changed vertex (input bridges/terrain-ev107.npz vs output terrain-kit.npz)
has slope <= max(35 deg, its slope before) + 1e-4; zero reserve/platform/narva vertices changed; reserve/platform/narva masks
identical. Also prints volumes and the largest raise/cut. Usage: gate_g5_slopes.py [run_dir]"""
import json, os, sys
import numpy as np
sys.dont_write_bytecode = True; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatelib as G
run = sys.argv[1] if len(sys.argv) > 1 else G.OUT
z0 = np.load(G.B + "/bridges/terrain-ev107.npz"); z1 = np.load(run + "/terrain-kit.npz")
H0 = z0["heights"].astype(np.float64); H1 = z1["heights"].astype(np.float64)
frozen = z0["reserve"] | z0["platform"] | z0["narva"]
masks_same = all(np.array_equal(z0[k], z1[k]) for k in ("reserve", "platform", "narva"))
ch = H1 != H0
def slopes(A):
    nw, ne, sw, se = A[:-1, :-1], A[:-1, 1:], A[1:, :-1], A[1:, 1:]
    # upper triangle NW-NE-SE and lower NW-SE-SW of the NW-SE split: gradient magnitude of the plane
    up = np.degrees(np.arctan(np.hypot((ne - nw) / 6.0, (se - ne) / 6.0)))
    lo = np.degrees(np.arctan(np.hypot((se - sw) / 6.0, (sw - nw) / 6.0)))
    return up, lo
u0, l0 = slopes(H0); u1, l1 = slopes(H1)
cu = ch[:-1, :-1] | ch[:-1, 1:] | ch[1:, 1:]; cl = ch[:-1, :-1] | ch[1:, 1:] | ch[1:, :-1]
bad_u = cu & (u1 > np.maximum(35.0, u0) + 1e-4); bad_l = cl & (l1 > np.maximum(35.0, l0) + 1e-4)
after = np.r_[u1[cu], l1[cl]]
d = H1 - H0
res = dict(changed_vertices=int(ch.sum()), changed_triangles=int(cu.sum() + cl.sum()), triangles_violating=int(bad_u.sum() + bad_l.sum()),
           violating_xz=[[6 * int(c) + 3, round(G.ZTOP - 6 * int(r) - 3, 1)] for r, c in np.argwhere(bad_u | bad_l)[:20]],
           slope_after_p50_p90_max=np.percentile(after, [50, 90, 100]).round(2).tolist(), over35_after=int((after > 35).sum()),
           frozen_changed=int((ch & frozen).sum()), masks_identical=bool(masks_same), fill_m3=round(float(d[d > 0].sum() * 36), 0),
           cut_m3=round(float(-d[d < 0].sum() * 36), 0), max_raise=round(float(d.max()), 3), max_cut=round(float(-d.min()), 3))
res["passed"] = res["triangles_violating"] == 0 and res["frozen_changed"] == 0 and masks_same
print(json.dumps(res))
json.dump(res, open(run + "/gate-g5.json", "w"), indent=1)
print("G5", "PASS" if res["passed"] else "FAIL")
sys.exit(0 if res["passed"] else 1)

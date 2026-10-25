"""How smooth can a straight channel's waterline be on the 6 m NW-SE grid? (EV112, gate G11 of gates_v6.py.)
A synthetic 40 x 40 vertex window, a straight channel at angle th through its centre, waterline width wl; the waterline is the
exact contour of the planar triangles at the level and is scored with the shore gates' wiggle (0.5 m samples, residual to a
12 m Savitzky-Golay quadratic; gates_v6.py: polylines/wiggle), p90 over the samples 20 m or more inside the window.
  trapezoid  H = max(level + 0.5 (|q| - wl/2), level - 0.5): the v4/v6 bank (BANK 0.5, bed at level - 0.5)
  lsq        the vertex heights that best put every crossed grid edge's zero where the target line crosses it (one
             equation per crossed E-W, N-S and NW-SE edge, weight 10) with a weak pull to 0.5 x signed distance: the shore
             pass's method (shore_ramp_v31.py 'ramp'), its best case here because the targets are exactly straight
Scope (review of 18-10): this compares these two constructions at five angles; it bounds what they reach, not what the grid
allows. A channel aligned with the grid lines reaches p90 0 at 5.5-10 m (the review's bound_construction.py), so G11's FAIL
is an open defect, not a proven impossibility.
Usage: wiggle_bound.py <out.json>"""
import json, math, sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix, identity, vstack
from scipy.sparse.linalg import lsqr
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gates_v6 as g6

n = 40
r, c = np.mgrid[0:n, 0:n]
X, Z = 6.0 * c, -6.0 * r
cx, cz = X.mean(), Z.mean()


def contour(D):
    segs = []
    for rr in range(n - 1):
        for cc in range(n - 1):
            for tri in (((rr, cc), (rr, cc + 1), (rr + 1, cc + 1)), ((rr, cc), (rr + 1, cc + 1), (rr + 1, cc))):
                d = [D[v] for v in tri]; w = [x < 0 for x in d]
                if sum(w) in (1, 2):
                    pts = []
                    for a, b in ((0, 1), (1, 2), (2, 0)):
                        if w[a] != w[b]:
                            t = d[a] / (d[a] - d[b]); A, B = tri[a], tri[b]
                            pts.append((6.0 * (A[1] + t * (B[1] - A[1])), -6.0 * (A[0] + t * (B[0] - A[0]))))
                    segs.append(pts)
    return np.array(segs)


def p90(segs, margin=20.0):
    if not len(segs):
        return None
    vals = []
    for line, closed in g6.polylines(segs):
        q, v = g6.wiggle(line, closed)
        keep = (np.abs(q[:, 0] - cx) < 3 * n - margin) & (np.abs(q[:, 1] - cz) < 3 * n - margin) & np.isfinite(v)
        vals.append(v[keep])
    v = np.concatenate(vals)
    return round(float(np.percentile(v, 90)), 4) if len(v) else None


def run(wl, th, s=0.5):
    d = np.array([math.sin(math.radians(th)), math.cos(math.radians(th))]); nrm = np.array([-d[1], d[0]])
    q = (X - cx) * nrm[0] + (Z - cz) * nrm[1]
    trap = p90(contour(np.maximum(s * (np.abs(q) - wl / 2), -0.5)))
    rows, cols, vals, k = [], [], [], 0
    for dr, dc in ((0, 1), (1, 0), (1, 1)):
        for rr in range(n - dr):
            for cc in range(n - dc):
                qa, qb = q[rr, cc], q[rr + dr, cc + dc]
                for side in (1, -1):
                    ga, gb = side * qa - wl / 2, side * qb - wl / 2
                    if ga * gb < 0:
                        t = ga / (ga - gb)
                        rows += [k, k]; cols += [rr * n + cc, (rr + dr) * n + cc + dc]; vals += [1 - t, t]; k += 1
    A = coo_matrix((vals, (rows, cols)), shape=(k, n * n)).tocsr(); lam = 0.05
    D = lsqr(vstack([A * 10.0, identity(n * n) * lam]).tocsr(), np.concatenate([np.zeros(k), lam * s * (np.abs(q) - wl / 2).ravel()]),
             atol=1e-12, btol=1e-12, iter_lim=20000)[0].reshape(n, n)
    return trap, p90(contour(D))


out = []
for wl in (4.0, 5.5, 6.3, 8.0, 10.0, 12.0, 17.0):
    for th in (7.0, 22.0, 37.0, 52.0, 71.0):
        trap, lsq = run(wl, th)
        out.append(dict(waterline_width_m=wl, angle_deg=th, p90_trapezoid_m=trap, p90_lsq_m=lsq))
        print(out[-1])
best = {}
for r_ in out:
    w = r_["waterline_width_m"]; b = min(x for x in (r_["p90_trapezoid_m"], r_["p90_lsq_m"]) if x is not None)
    best[w] = max(best.get(w, 0.0), b)
summary = dict(worst_angle_best_method_p90_m=best, gate_m=0.08, methods=["trapezoid", "lsq"], angles_deg=[7.0, 22.0, 37.0, 52.0, 71.0],
               reading="scope: straight channels only, two constructions (the v4/v6 trapezoid bank and the shore pass's least "
                       "squares) at five angles; with these two, p90 <= 0.08 m at every tested angle only from about 12 m of "
                       "waterline width (bridge streams: 5.5-6.3 m wood, 10 m metal). Not a proof that narrower channels cannot "
                       "reach 0.08 m: grid-aligned 5.5-10 m channels reach p90 0 (review of 18-10, bound_construction.py); G11 "
                       "is an open FAIL, not a demonstrated impossibility")
Path(sys.argv[1]).write_text(json.dumps(dict(rows=out, summary=summary), indent=1), newline="\n")
print(json.dumps(summary, indent=1))

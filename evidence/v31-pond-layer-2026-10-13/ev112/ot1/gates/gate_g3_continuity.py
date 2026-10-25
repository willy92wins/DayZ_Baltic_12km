"""G3: continuity of the visible water. Per site, the water-proxy LOD0 faces of every piece (with their lips) are rasterised
at 0.1 m (pixel centres; highest face wins), wet = face above the terrain interpolated on its native triangle. Pass when every
lattice-polyline sample of the wet span (first piece's flat run to the last one's, every 0.1 m, joints included) is wet, all of them
fall in one 4-connected wet region, AND the whole wet union of the site is that one region (no stray sheet: the first version
only checked the axis region and passed an added detached sheet of 272.65 m2, review of 15-10).
EV112: same definition, computed in 64 m tiles (a 10 km reach does not fit one raster): each tile is labelled 4-connected and
the labels are joined across tile borders (pixel pairs wet on both sides) with a union-find, so the regions are those of the
whole raster. Usage: gate_g3_continuity.py [run_dir]"""
import json, sys, math
import numpy as np
from scipy.ndimage import label
import os; sys.dont_write_bytecode = True; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatelib as G
run = sys.argv[1] if len(sys.argv) > 1 else G.OUT
models, recs, rep, H, sites, pieces = G.load(run)
PX, TS = 0.1, 640                                                  # pixel size, tile size in pixels (64 m)


class UF:
    def __init__(self):
        self.p = {}

    def find(self, a):
        self.p.setdefault(a, a)
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]; a = self.p[a]
        return a

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)


ok_all = True; out = {}
for sid, S in sites.items():
    P = pieces[sid]
    tiles = {}                                                     # (ti, tj) -> float32 max water height
    for p in P:
        for t in p.water:
            a, b, c = t[:, [0, 2]]
            tlo = np.minimum(np.minimum(a, b), c); thi = np.maximum(np.maximum(a, b), c)
            i0, i1 = int(math.floor(tlo[0] / PX)), int(math.ceil(thi[0] / PX))
            j0, j1 = int(math.floor(tlo[1] / PX)), int(math.ceil(thi[1] / PX))
            v0, v1 = b - a, c - a; den = v0[0] * v1[1] - v0[1] * v1[0]
            if abs(den) < 1e-12:
                continue
            for ti in range(i0 // TS, (i1 - 1) // TS + 1):
                for tj in range(j0 // TS, (j1 - 1) // TS + 1):
                    ia, ib = max(i0, ti * TS), min(i1, (ti + 1) * TS); ja, jb = max(j0, tj * TS), min(j1, (tj + 1) * TS)
                    if ia >= ib or ja >= jb:
                        continue
                    X, Z = np.meshgrid((np.arange(ia, ib) + 0.5) * PX, (np.arange(ja, jb) + 0.5) * PX)
                    dx, dz = X - a[0], Z - a[1]
                    u = (dx * v1[1] - dz * v1[0]) / den; v = (v0[0] * dz - v0[1] * dx) / den
                    ins = (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
                    if not ins.any():
                        continue
                    y = t[0, 1] + u * (t[1, 1] - t[0, 1]) + v * (t[2, 1] - t[0, 1])
                    W = tiles.setdefault((ti, tj), np.full((TS, TS), -np.inf, np.float32))
                    blk = W[ja - tj * TS:jb - tj * TS, ia - ti * TS:ib - ti * TS]
                    W[ja - tj * TS:jb - tj * TS, ia - ti * TS:ib - ti * TS] = np.where(ins, np.maximum(blk, y), blk)
    wet, lab, area = {}, {}, {}
    uf = UF()
    for (ti, tj), W in tiles.items():
        jj, ii = np.nonzero(np.isfinite(W))
        m = np.zeros((TS, TS), bool)
        ty = G.terrain_y(H, (ti * TS + ii + 0.5) * PX, (tj * TS + jj + 0.5) * PX)
        m[jj, ii] = W[jj, ii] > ty
        L, n = label(m)
        wet[(ti, tj)] = m; lab[(ti, tj)] = L
        cnt = np.bincount(L.ravel())
        for k in range(1, n + 1):
            uf.find((ti, tj, k)); area[(ti, tj, k)] = cnt[k] * PX * PX
    for (ti, tj), L in lab.items():
        for (di, dj) in ((1, 0), (0, 1)):
            nb = (ti + di, tj + dj)
            if nb not in lab:
                continue
            if di:                                                 # right border: column TS-1 of this tile, column 0 of nb
                a_, b_ = L[:, -1], lab[nb][:, 0]
            else:                                                  # tiles index z upwards: row TS-1 of this tile meets row 0 of nb
                a_, b_ = L[-1, :], lab[nb][0, :]
            both = (a_ > 0) & (b_ > 0)
            for x, y in set(zip(a_[both].tolist(), b_[both].tolist())):
                uf.union((ti, tj, x), (nb[0], nb[1], y))
    roots = {}
    for key, ar in area.items():
        r = uf.find(key); roots[r] = roots.get(r, 0.0) + ar
    V = np.array(S["lattice"]); span = S["wet_span"]
    st = np.r_[np.arange(span[0], span[1], PX), span[1]]
    A = G.at(V, np.clip(st, 0, None))
    cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(V, axis=0), axis=1))]
    u0 = (V[1] - V[0]) / np.linalg.norm(V[1] - V[0]); u1 = (V[-1] - V[-2]) / np.linalg.norm(V[-1] - V[-2])
    A = np.where((st < 0)[:, None], V[0] + st[:, None] * u0, A)
    A = np.where((st > cum[-1])[:, None], V[-1] + (st - cum[-1])[:, None] * u1, A)
    ia = np.floor(A[:, 0] / PX).astype(int); ja = np.floor(A[:, 1] / PX).astype(int)
    aw = np.zeros(len(A), bool); al = []
    for k in range(len(A)):
        key = (ia[k] // TS, ja[k] // TS)
        if key not in wet:
            al.append(None); continue
        w_ = wet[key][ja[k] - key[1] * TS, ia[k] - key[0] * TS]
        aw[k] = w_
        al.append(uf.find((key[0], key[1], int(lab[key][ja[k] - key[1] * TS, ia[k] - key[0] * TS]))) if w_ else None)
    labs = sorted({x for x in al if x is not None})
    dry = np.nonzero(~aw)[0]
    dry_runs = []
    if len(dry):
        brk = np.r_[0, np.nonzero(np.diff(dry) > 1)[0] + 1, len(dry)]
        for a_, b_ in zip(brk[:-1], brk[1:]):
            k0, k1 = dry[a_], dry[b_ - 1]
            dry_runs.append(dict(from_xz=A[k0].round(2).tolist(), to_xz=A[k1].round(2).tolist(), length_m=round((k1 - k0 + 1) * PX, 2)))
    stray = []
    for root,ar in roots.items():
        if root in labs:
            continue
        coordinates=[]
        for (ti,tj,k) in area:
            if uf.find((ti,tj,k)) != root:
                continue
            jj,ii=np.nonzero(lab[(ti,tj)]==k)
            coordinates.append(np.c_[(ti*TS+ii+.5)*PX,(tj*TS+jj+.5)*PX])
        q=np.vstack(coordinates)
        stray.append(dict(area_m2=round(float(ar),2),bounds_xz=[q.min(0).round(2).tolist(),q.max(0).round(2).tolist()],centre_xz=q.mean(0).round(3).tolist()))
    passed = bool(aw.all() and len(labs) == 1 and len(roots) == 1)
    ok_all &= passed
    out[sid] = dict(pieces=len(P), tiles=len(tiles), axis_samples=len(st), axis_dry_samples=int((~aw).sum()), dry_runs=dry_runs[:20],
                    regions_on_axis=len(labs), wet_regions_total=len(roots), stray_regions=len(stray),
                    stray_area_m2_total=round(sum(s_["area_m2"] for s_ in stray), 2), stray_area_max_m2=max([s_["area_m2"] for s_ in stray] or [0]),
                    stray_details=stray[:20],
                    axis_region_area_m2=round(float(sum(roots[r] for r in labs)), 1), passed=passed)
    print(sid, json.dumps(out[sid]), flush=True)
json.dump(out, open(run + "/gate-g3.json", "w"), indent=1)
print("G3", "PASS" if ok_all else "FAIL")
sys.exit(0 if ok_all else 1)

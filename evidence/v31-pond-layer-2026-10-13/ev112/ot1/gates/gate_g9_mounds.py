"""G9 (EV112): no polygonal pyramid at the sides of the kit streams (Guillermo, 17-10: 'a los lados hay monticulos poligonales
piramidales que suavizar ... lo mismo con monticulos y rios por todo el mapa'). A pyramid on the 6 m NW-SE grid is a small
shape whose lowest vertex stands more than 0.50 m above the highest vertex of its native ring: a single vertex, an edge pair
(E, S or SE neighbour) or a native triangle (the shape classes of the despike census, ev112-wip/despike).
Owner = the 24m lattice band, two-cell dilation of actual kit changes and 15m discs around every kit/stone record.
Seat vertices are included. Frozen vertices and wet retained pond/rims below plane+0.35 are protected.
Pass: 0 judged shapes on <run>/terrain-kit.npz AND 0 new prominent 1/2/3-vertex shapes anywhere influenced by
a changed shape vertex or native neighbour. Also prints the counts before (EV107) and after,
in the band and map-wide (outside the bands nothing is smoothed by this track; the despike track works there).
Usage: gate_g9_mounds.py [run_dir]"""
import json, os, sys
import numpy as np
from scipy.ndimage import binary_dilation
sys.dont_write_bytecode = True; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatelib as G
run = sys.argv[1] if len(sys.argv) > 1 else G.OUT
TH, BAND, RING = 0.50, 24.0, 6.01  # Approved EV112 OT1 criterion, including native pairs and triangles.
z0 = np.load(G.B + "/bridges/terrain-ev107.npz"); z1 = np.load(run + "/terrain-kit.npz")
H0 = z0["heights"].astype(np.float64); H1 = z1["heights"].astype(np.float64)
frozen = z0["reserve"] | z0["platform"] | z0["narva"] | z0["v31_bridge_cut"]
planes = np.load(run + "/envelope-ev108.npy")
env = np.isfinite(planes)
envv = np.zeros(H0.shape, bool)
vp = np.full(H0.shape, -np.inf)
for dr in (0, 1):
    for dc in (0, 1):
        envv[dr:dr + 2047, dc:dc + 2047] |= env
        vp[dr:dr + 2047, dc:dc + 2047] = np.maximum(vp[dr:dr + 2047, dc:dc + 2047],np.where(env,planes,-np.inf))
rep = json.load(open(run + "/kit-report.json"))
N6 = ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1))


def prom(H):
    n = np.full(H.shape, -np.inf)
    for dr, dc in N6:
        sh = np.full(H.shape, -np.inf)
        sh[max(-dr, 0):H.shape[0] - max(dr, 0), max(-dc, 0):H.shape[1] - max(dc, 0)] = H[max(dr, 0):H.shape[0] - max(-dr, 0), max(dc, 0):H.shape[1] - max(-dc, 0)]
        n = np.maximum(n, sh)
    p = H - n
    p[0, :] = p[-1, :] = -np.inf; p[:, 0] = p[:, -1] = -np.inf
    return p


band = np.zeros(H0.shape, bool); ring = np.zeros(H0.shape, bool)
for s in rep["sites"]:
    if "skipped" in s:
        continue
    V = np.array(s["lattice"])
    u0 = (V[1] - V[0]) / np.linalg.norm(V[1] - V[0]); u1 = (V[-1] - V[-2]) / np.linalg.norm(V[-1] - V[-2])
    X = V                                                          # the path itself (the tool's band has no extension)
    xc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(V, axis=0), axis=1))]
    best = {}                                                      # (r, c) -> (q, station), exact over every segment near it
    for i, (a, b) in enumerate(zip(X[:-1], X[1:])):
        lo_, hi_ = np.minimum(a, b) - BAND - 6, np.maximum(a, b) + BAND + 6
        ra, rb = max(int((G.ZTOP - hi_[1]) / 6), 0), min(int((G.ZTOP - lo_[1]) / 6) + 1, 2047)
        ca, cb = max(int(lo_[0] / 6), 0), min(int(hi_[0] / 6) + 1, 2047)
        RR, CC = np.mgrid[ra:rb + 1, ca:cb + 1]; Pp = np.c_[6.0 * CC.ravel(), G.ZTOP - 6.0 * RR.ravel()]
        ab = b - a; t = np.clip(((Pp - a) @ ab) / (ab @ ab), 0, 1); d = np.linalg.norm(Pp - (a + t[:, None] * ab), axis=1)
        stt = xc[i] + t * (xc[i + 1] - xc[i])
        for k in np.nonzero(d <= BAND)[0]:
            key = (int(RR.ravel()[k]), int(CC.ravel()[k]))
            if key not in best or d[k] < best[key][0] - 1e-9:
                best[key] = (float(d[k]), float(stt[k]))
    for (r, c), (qq, stv) in best.items():
        band[r, c] = True
        if qq <= RING and s["plate_span"][0] - 1e-6 <= stv <= s["plate_span"][1] + 1e-6:
            ring[r, c] = True
p0, p1 = prom(H0), prom(H1)
changed = H1 != H0
owner = band | binary_dilation(z1["v31_kit"], np.ones((3, 3), bool), iterations=2)
for rec in json.load(open(run + "/kit-records.json")):
    x, _, z = rec["matrix"][9:12]
    ra, rb = max(0, int((G.ZTOP-z-15)/6)), min(2047, int((G.ZTOP-z+15)/6)+1)
    ca, cb = max(0, int((x-15)/6)), min(2047, int((x+15)/6)+1)
    rr, cc = np.mgrid[ra:rb+1, ca:cb+1]
    owner[ra:rb+1, ca:cb+1] |= np.hypot(cc*6-x, G.ZTOP-rr*6-z) <= 15
judged = owner & ~frozen & ~(envv & (H1 < vp + .35))  # Seats and dry pond rims have no blanket exemption.
new = changed & (p1 > TH) & ~(p0 > TH)
SH = (((0, 0),), ((0, 0), (0, 1)), ((0, 0), (1, 0)), ((0, 0), (1, 1)), ((0, 0), (0, 1), (1, 1)), ((0, 0), (1, 1), (1, 0)))


def sh(A, dr, dc, fill):
    B = np.full(A.shape, fill, A.dtype)
    B[max(-dr, 0):A.shape[0] - max(dr, 0), max(-dc, 0):A.shape[1] - max(dc, 0)] = A[max(dr, 0):A.shape[0] - max(-dr, 0), max(dc, 0):A.shape[1] - max(-dc, 0)]
    return B


def shapes(H, mask_all, mask_any, before=None):
    """Count shapes standing > TH above their ring with every vertex in mask_all (and at least one in mask_any)."""
    n, xz = 0, []
    for S in SH:
        ring = sorted({(a + dr, b + dc) for a, b in S for dr, dc in N6} - set(S))
        rmax = np.full(H.shape, -np.inf)
        for dr, dc in ring:
            rmax = np.maximum(rmax, sh(H, dr, dc, np.inf))
        smin = np.full(H.shape, np.inf); allm = np.ones(H.shape, bool); anym = np.zeros(H.shape, bool)
        for dr, dc in S:
            smin = np.minimum(smin, sh(H, dr, dc, -np.inf)); allm &= sh(mask_all, dr, dc, False); anym |= sh(mask_any, dr, dc, False)
        hit = (smin - rmax > TH) & allm & anym
        if before is not None:
            oldring = np.full(H.shape, -np.inf); oldmin = np.full(H.shape, np.inf)
            for dr, dc in ring:
                oldring = np.maximum(oldring, sh(before, dr, dc, np.inf))
            for dr, dc in S:
                oldmin = np.minimum(oldmin, sh(before, dr, dc, -np.inf))
            hit &= oldmin - oldring <= TH
        n += int(hit.sum()); xz += [[len(S), 6 * int(c), round(G.ZTOP - 6 * int(r), 1), round(float((smin - rmax)[r, c]), 3)] for r, c in np.argwhere(hit)[:5]]
    return n, xz


nj1, xz1 = shapes(H1, judged, judged); nj0, _ = shapes(H0, judged, judged)
nb1, _ = shapes(H1, band, band); nb0, _ = shapes(H0, band, band)
everyw = np.ones(H0.shape, bool)
nm1, _ = shapes(H1, everyw, everyw); nm0, _ = shapes(H0, everyw, everyw)
new_shapes, new_shapes_xz = shapes(H1, everyw, binary_dilation(changed,np.ones((3,3),bool)), before=H0)
bad = judged & (p1 > TH)
res = dict(band_vertices=int(band.sum()), judged=int(judged.sum()),
           band_prominent_before=int((band & (p0 > TH)).sum()), band_prominent_after=int((band & (p1 > TH)).sum()),
           judged_prominent_before=int((judged & (p0 > TH)).sum()), judged_prominent_after=int(bad.sum()),
           not_judged_prominent_after=dict(frozen=int((band & frozen & (p1 > TH)).sum()), pond_or_sill=int((band & envv & ~frozen & (p1 > TH)).sum()),
                                           seat_ring=int((band & ring & ~frozen & ~envv & (p1 > TH)).sum())),
           new_prominent_changed=int(new.sum()), new_xz=[[6 * int(c), round(G.ZTOP - 6 * int(r), 1), round(float(p1[r, c]), 3)] for r, c in np.argwhere(new)[:20]],
           judged_xz=[[6 * int(c), round(G.ZTOP - 6 * int(r), 1), round(float(p1[r, c]), 3)] for r, c in np.argwhere(bad)[:20]],
           map_prominent_before_after=[int((p0 > TH).sum()), int((p1 > TH).sum())],
           max_prominence_band_after=round(float(p1[judged].max()), 3) if judged.any() else None)
res.update(threshold_m=TH, owner_vertices=int(owner.sum()), new_shapes=new_shapes, new_shapes_xz=new_shapes_xz,
           judged_shapes_before_after=[nj0, nj1], judged_shapes_xz=xz1, band_shapes_before_after=[nb0, nb1], map_shapes_before_after=[nm0, nm1])
res["passed"] = bool(nj1 == 0 and new_shapes == 0 and res["new_prominent_changed"] == 0 and judged.any())
print(json.dumps(res))
json.dump(res, open(run + "/gate-g9.json", "w"), indent=1)
print("G9", "PASS" if res["passed"] else "FAIL")
sys.exit(0 if res["passed"] else 1)

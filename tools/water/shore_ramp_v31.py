"""Shore ramp pass v31: straight, smooth waterlines of wide water (the engine sea at 0.75 m and one pond plane at a time)
on the native 6 m TRI grid. Runs on the terrain after bury_edges_v31; bury_edges_v31 and the footprint follow it.

Grid: 2048 x 2048 vertices of 6 m, row 0 north, x = 6 c, z = 12282 - 6 r. Native triangles split NW-SE: A = (NW, NE, SE)
where fc >= fr, B = (NW, SW, SE). Water per cell corner: footprint cells (plane finite) use the visual field F (footprint.npz
'field', corners NW, NE, SW, SE as in pond_footprint_v31.py:30-31 and :92); every other cell the engine sea SEA = 0.75
(tools/terrain/bridges_v31.py 'SEA, SEA_BED'). D = H - W is linear per triangle, so the waterline is exact: one straight
segment per mixed triangle, wet iff D < 0.

Steps
  census     unless --worklist: the waterline of wide water (within 24 m of water that is >= 18 m from land; channels with
             the far bank within W_NARROW across water belong to the streams/kit track) is cut in 60 m windows every 20 m and
             scored by wiggle p90 (lateral residual against a 12 m Savitzky-Golay quadratic, 0.5 m samples). Windows above
             --threshold are grouped per chain (gaps <= 2 EXT_MIN); each group is cut at natural points: the first point
             EXT_MIN..EXT_MAX m beyond its windows whose wiggle stays below CUT_QUIET within +-CUT_HALF m, or a chain end
             (the prototype cut at box edges and left splice kinks). Groups whose cut intervals overlap are merged, so the
             stretches of one chain never overlap. Extent = union of the windows, not 60 + 20 (n - 1) (the prototype's
             worklist counted 40 m gaps as 20 m and lost 240 m over the map).
  chains     segments are joined only where their shared crossing point coincides (<= 1e-6 m); a shared edge with two
             different crossing points (two pond fields meeting on one edge) ends both chains. The prototype averaged the
             two points (up to 1.06 m apart), so its measured waterline left the exact intersections.
  target     per stretch, the waterline of its body within TUBE of the stretch polyline is smoothed by an arc-length
             spline through the pins (beta/alpha = sigma^4; sigma is passed explicitly to every call: the prototype bound
             it as a default argument, so changing it had no effect). Pins = waterline points on an edge whose two ends
             are protected, and the first/last END_PIN m of every open portion. Side constraints (strict: a protected
             vertex with |D| > 0.1 and its free native-edge neighbours keep their side, SIDE_MARGIN m clear) are solved
             inside the spline as soft pulls (PULL_W), up to SIDE_MAX m from the unconstrained spline: the prototype added
             6 m Gaussian bumps after the spline, and those bumps were the wiggle left in its target.
  ramp       every free vertex within B0 of the target gets D = s * sd in least squares with one equation per crossed
             grid edge (weight W_EDGE); blend to the old terrain up to B1 with the side enforced; pond beds stay >= 1.0 m
             where they were; vertices of non-envelope cells stay dry for a pond. Vertices changed by an earlier stretch
             are protected for the later ones.
Protected, never changed: platform, narva; v31_kit, v31_bridge_cut and any v31_lattice* / v31_bridge_* mask dilated by 1
vertex; v31_lagoon; every vertex within CROSS_EXCL m of a pending 015 crossing (--crossings, default derived from
evidence/v31-pond-layer-2026-10-13/bridges: crossings-ev106.json minus the sites built in sites-pilot.json,
ev109/sites-rollout.json and any --built file); for the sea every vertex of
an envelope cell (two-colour rule); for a pond every vertex of an envelope cell of another level or with F != plane.
Reserve-only vertices (reserve & ~platform & ~narva) may move (Guillermo, 15-10: the frozen 2-vertex reserve fringe pinned
the staircase of the islet causeways).
Guards that REJECT a stretch (its vertices keep the input heights; never only reported):
  fixed      a portion whose pinned waterline points exceed FIXED_FRAC_MAX is not treated (variant A of the prototype made
             r01 worse, 9.2 -> 13.9 teeth/km, when frozen points dominated).
  slope      a changed triangle that crosses SLOPE_MAX (at most SLOPE_MAX before, over it after; no tolerance), or one
             already over it that gets steeper by more than SLOPE_EPS (review 1: the tolerance also admitted crossings).
  side       B-strict on the final float32 heights: every changed vertex whose protected native-edge neighbours (|D| >
             0.1) are all on one side ends on that side (vertices of non-envelope cells dry for a pond). The solve
             pulls the target; vertices still on the wrong side are then set SIDE_CLR m onto the required side, and
             any violation left after the clamps and the float32 cast rejects the stretch (review 1: 277 changed
             vertices of 16 stretches ended on the wrong side; the pulls were soft and never checked).
  rounds     the candidate is written, its footprint regenerated with pond_footprint_v31.py, and a stretch fails when
             near its changed vertices (owner map, ATTR_RINGS rings): a new exposed footprint border vertex, a new pond
             cell with a corner under the engine sea, a new pond vertex below its plane on a non-envelope cell (the
             envelope would have to grow), a new bed under 1.0 m, a new field corner off its plane by > 0.35 m, a sea
             component created, removed, split or merged (labels over the native triangle edges E, S and NW-SE: the
             prototype's 4-neighbour count split a pocket joined only by the diagonal), or a wiggle p90 over all its
             changed triangles (exact waterline, regenerated footprint) above max(WIG_ABS, WIG_REL * before), or
             a waterline its triangles cannot measure: no finite sample before or after, a segment on a chain too
             short for the wiggle window (a new or vanished islet or puddle), a change in the number of chains through
             its triangles or in the closed chains lying wholly inside them (review 1: an unmeasurable islet scored
             p90 = 0 and passed). A segment shorter than the 0.5 m sample step on a measured chain is covered by
             that chain's samples. A failed
             stretch is solved again with the next RETRY variant; after the last one it is rejected. The pass is re-run
             until a round fails nothing; a failure that no stretch owns aborts, and no output is written otherwise.
Output: every input array byte-identical except heights, plus v31_shore_ramp (bool, vertex changed by this pass); the
prototype saved 4 of 17 arrays and the next pass could not run on it. Exactness is reported, not claimed: distance from
the new waterline in every changed triangle to the target (the prototype measured only cells with 4 changed corners).
Usage: shore_ramp_v31.py <terrain.npz> <footprint.npz> <envelope.npy> <cover.npy> <out_terrain.npz> <report.json>
       [--worklist W.json] [--threshold 0.15] [--sigma 12] [--built SITES.json ...] [--crossings C.json] [--work DIR]
       [--footprint-tool P] [--focus NAME:x0,x1,z0,z1] [--param KEY=VALUE]
--built adds a built-sites file of a later chain (e.g. evidence/.../bridges/ev110/sites-ev110.json) to the sites removed
from the inventory. --crossings replaces the inventory: every entry must be an inventory crossing with its inventory
coordinates (checked), ids unique; its sha256 is reported. The gates derive the pending set from the evidence on their own.
The footprint must be the footprint of the terrain with that cover and envelope (checked by regenerating it).
Writes <out_terrain.npz>, <report.json>, and in the work dir (fresh; default <out_terrain>-work): worklist.json (reusable
with --worklist), owner.npy (int32 stretch id per vertex, -1 none), targets.json and round<k>/ (candidate terrain, owner,
targets and footprint of every validation round).
"""
import argparse, hashlib, json, os, subprocess, sys, time
from collections import defaultdict
import numpy as np
from scipy import sparse
from scipy.ndimage import binary_dilation, distance_transform_edt, label
from scipy.signal import savgol_filter
from scipy.sparse.linalg import spsolve
from scipy.spatial import cKDTree

N = 2048
NC = N - 1
ZTOP = 6.0 * NC
SEA = 0.75
K3 = np.ones((3, 3), bool)
S6 = np.array([[1, 1, 0], [1, 1, 1], [0, 1, 1]], bool)     # vertex neighbours along native edges: E-W, N-S, NW-SE
HERE = os.path.dirname(os.path.abspath(__file__))
PARAMS = dict(B0=9.0, B1=15.0, S_MIN=0.05, S_MAX=0.35, CLR_LAND=0.30, CLR_WATER=0.10, BED=1.0, END_PIN=6.0,
              MIN_PORTION=24.0, W_EDGE=100.0, SIDE_ITERS=10, SIDE_MARGIN=1.5, PULL_W=1e3, PULL_STIFF=1.0, SIDE_MAX=6.5,
              W_NARROW=17.0, NARROW_ARC=30.0, DEV_MAX=0.8, WIDE_CORE=18.0, WIN=60.0, STEPW=20.0, EXT_MIN=6.0, EXT_MAX=48.0,
              CUT_QUIET=0.04, CUT_HALF=6.0, TUBE=6.0,
              BOXM=30.0, FIXED_FRAC_MAX=0.20, SLOPE_MAX=35.0, SLOPE_EPS=0.01, CROSS_EXCL=60.0, WIG_ABS=0.08, WIG_REL=0.5,
              WIG_W=12.0, WIG_STEP=0.5, MAX_ROUNDS=16, ATTR_RINGS=3, PROT_DILATE=1, EDGE_MARGIN=0.05, FIELD_MAX_DEV=0.35,
              SIDE_CLR=0.05)
# Per-stretch retries: a stretch rejected by a guard is solved again with the next variant (overrides of PARAMS)
# before it is rejected for good. Measured on EV109 (dev sweep 15-10): the margin and the edge weight decide whether
# the waterline next to protected vertices follows the target, and different stretches pass with different ones.
# With the strict side enforced on the final heights (review 1) the vertices next to frozen ground that the pulls leave
# on the wrong side are clamped and the waterline kinks there; variants 4-6 push the target further out (margin, reach
# and iterations of the pulls) so fewer vertices need the clamp (dev sweep 15-10 on the islet stretches 8, 10, 25, 29).
RETRY = ({}, dict(SIDE_MARGIN=1.0), dict(SIDE_MARGIN=0.5, W_EDGE=10.0), dict(PULL_STIFF=2.0),
         dict(SIDE_MARGIN=3.5, SIDE_MAX=12.0, SIDE_ITERS=30), dict(SIDE_MARGIN=2.5, SIDE_MAX=10.0, SIDE_ITERS=30),
         dict(SIDE_MARGIN=2.5, SIDE_MAX=10.0, SIDE_ITERS=30, PULL_STIFF=2.0))
REQUIRED = ("heights", "reserve", "platform", "narva", "v31_kit", "v31_bridge_cut", "v31_lagoon")
OUT_MASK = "v31_shore_ramp"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------- grid helpers
def vxz(r, c):
    return 6.0 * c, ZTOP - 6.0 * r


def c2v(m):
    """Cell mask (2047^2) -> vertices incident to a marked cell."""
    out = np.zeros((N, N), bool)
    for dr in (0, 1):
        for dc in (0, 1):
            out[dr:dr + NC, dc:dc + NC] |= m
    return out


def c2v_max(val):
    out = np.full((N, N), -np.inf)
    for dr in (0, 1):
        for dc in (0, 1):
            out[dr:dr + NC, dc:dc + NC] = np.maximum(out[dr:dr + NC, dc:dc + NC], val)
    return out


def tri_h(H, x, z):
    """Planar interpolation on the native triangles."""
    c, r = np.asarray(x, float) / 6.0, (ZTOP - np.asarray(z, float)) / 6.0
    c0 = np.clip(np.floor(c).astype(int), 0, NC - 1); r0 = np.clip(np.floor(r).astype(int), 0, NC - 1)
    fc, fr = c - c0, r - r0
    nw, ne, sw, se = H[r0, c0], H[r0, c0 + 1], H[r0 + 1, c0], H[r0 + 1, c0 + 1]
    return np.where(fc >= fr, nw + fc * (ne - nw) + fr * (se - ne), nw + fr * (sw - nw) + fc * (se - sw))


def tri_slopes(h):
    """Slope (deg) of triangles A and B of every cell of a vertex window h."""
    nw, ne, sw, se = h[:-1, :-1], h[:-1, 1:], h[1:, :-1], h[1:, 1:]
    ga = np.degrees(np.arctan(np.hypot((ne - nw) / 6.0, (ne - se) / 6.0)))
    gb = np.degrees(np.arctan(np.hypot((se - sw) / 6.0, (nw - sw) / 6.0)))
    return ga, gb


def corner_water(plane, field):
    fp = np.isfinite(plane)
    return np.where(fp[:, :, None], field, SEA), fp


# ---------------------------------------------------------------- exact waterline
TRIS = ((0, 1, 3), (0, 2, 3))               # A: NW NE SE, B: NW SW SE (corner index NW0 NE1 SW2 SE3)
COFF = ((0, 0), (0, 1), (1, 0), (1, 1))


def extract_segments(H, W, fp, plane, r0=0, r1=NC, c0=0, c1=NC):
    """Waterline segments in cells r0 <= r < r1, c0 <= c < c1: p (n,2,2) xz, key (n,2) edge keys, cell (n,2), tri (n,),
    pond (n,), lev (n,) = the cell's plane for a pond cell, SEA otherwise."""
    Hs = H[r0:r1 + 1, c0:c1 + 1]
    Ws = W[r0:r1, c0:c1]
    fps = fp[r0:r1, c0:c1]
    pls = plane[r0:r1, c0:c1]
    nr, nc = Ws.shape[:2]
    cor = [Hs[dr:dr + nr, dc:dc + nc] for dr, dc in COFF]
    out = dict(p=[], key=[], cell=[], tri=[], pond=[], lev=[])
    for ti, idx in enumerate(TRIS):
        d = [cor[k] - Ws[:, :, k] for k in idx]
        nwet = (d[0] < 0).astype(int) + (d[1] < 0) + (d[2] < 0)
        sel = np.nonzero((nwet > 0) & (nwet < 3))
        if sel[0].size == 0:
            continue
        R, C = sel
        dv = np.stack([di[sel] for di in d], 1)
        wv = dv < 0
        m = R.size
        P = np.zeros((m, 2, 2)); K = np.zeros((m, 2), np.int64); slot = np.zeros(m, int)
        for a, b in ((0, 1), (1, 2), (2, 0)):
            ka, kb = idx[a], idx[b]
            cross = wv[:, a] != wv[:, b]
            t = dv[:, a] / np.where(cross, dv[:, a] - dv[:, b], 1.0)
            ra = R + COFF[ka][0] + r0; ca = C + COFF[ka][1] + c0
            rb = R + COFF[kb][0] + r0; cb = C + COFF[kb][1] + c0
            x = 6.0 * (ca + t * (cb - ca)); zz = ZTOP - 6.0 * (ra + t * (rb - ra))
            va = ra.astype(np.int64) * N + ca; vb = rb.astype(np.int64) * N + cb
            key = np.minimum(va, vb) * (N * N) + np.maximum(va, vb)
            i = np.nonzero(cross)[0]
            s = slot[i]
            P[i, s, 0] = x[i]; P[i, s, 1] = zz[i]; K[i, s] = key[i]
            slot[i] += 1
        assert (slot == 2).all()
        out["p"].append(P); out["key"].append(K)
        out["cell"].append(np.stack([R + r0, C + c0], 1)); out["tri"].append(np.full(m, ti))
        isp = fps[sel]
        out["pond"].append(isp); out["lev"].append(np.where(isp, pls[sel].astype(np.float64), SEA))
    empty = dict(p=np.zeros((0, 2, 2)), key=np.zeros((0, 2), np.int64), cell=np.zeros((0, 2), int), tri=np.zeros(0, int),
                 pond=np.zeros(0, bool), lev=np.zeros(0))
    return {k: (np.concatenate(v) if v else empty[k]) for k, v in out.items()}


def subseg(seg, m):
    return {k: v[m] for k, v in seg.items()}


def discontinuities(seg, tol=1e-6):
    """Edge keys shared by two segments whose crossing points differ (two water surfaces on one edge)."""
    keys = seg["key"].ravel(); xy = seg["p"].reshape(-1, 2)
    if len(keys) < 2:
        return 0, 0.0
    o = np.argsort(keys, kind="stable")
    same = keys[o[:-1]] == keys[o[1:]]
    d = np.hypot(*(xy[o[:-1]] - xy[o[1:]]).T)
    bad = same & (d > tol)
    return int(bad.sum()), float(d[bad].max(initial=0.0))


def chain(seg, tol=1e-6):
    """Polylines of segments joined through a shared edge key AND a coincident crossing point. Returns a list of dicts:
    order (segment indices), pts (len(order)+1, 2), closed."""
    K, P = seg["key"], seg["p"]
    n = len(K)
    adj = defaultdict(list)
    for i in range(n):
        adj[K[i, 0]].append((i, 0)); adj[K[i, 1]].append((i, 1))
    used = np.zeros(n, bool)

    def step(i, e):
        k = K[i, e]; pt = P[i, e]
        for j, ej in adj[k]:
            if not used[j] and abs(P[j, ej, 0] - pt[0]) <= tol and abs(P[j, ej, 1] - pt[1]) <= tol:
                return j, ej
        return None

    chains = []
    for i in range(n):
        if used[i]:
            continue
        used[i] = True
        fwd = [(i, 0)]                                    # (segment, entry endpoint)
        cur, ein = i, 0
        while True:
            nx = step(cur, 1 - ein)
            if nx is None:
                break
            j, ej = nx; used[j] = True; fwd.append((j, ej)); cur, ein = j, ej
        back = []
        cur, eout = i, 0
        while True:
            nx = step(cur, eout)
            if nx is None:
                break
            j, ej = nx; used[j] = True; back.append((j, 1 - ej)); cur, eout = j, 1 - ej
        seq = list(reversed(back)) + fwd
        s0, e0 = seq[0]
        pts = [P[s0, e0]] + [P[s, 1 - e] for s, e in seq]
        keys = [K[s0, e0]] + [K[s, 1 - e] for s, e in seq]
        sl, el = seq[-1]
        closed = (len(seq) > 2 and K[sl, 1 - el] == K[s0, e0]
                  and np.hypot(*(P[sl, 1 - el] - P[s0, e0])) <= tol)
        chains.append(dict(order=np.array([s for s, _ in seq]), pts=np.array(pts), keys=np.array(keys, np.int64),
                           closed=bool(closed)))
    return chains


def arclen(p):
    return np.r_[0.0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))] if len(p) else np.zeros(0)


def resample(p, step, closed=False):
    if closed and np.hypot(*(p[0] - p[-1])) > 1e-9:
        p = np.vstack([p, p[:1]])
    s = arclen(p)
    if s[-1] < step:
        return p.copy(), s
    t = np.arange(0, s[-1], step)
    return np.column_stack([np.interp(t, s, p[:, 0]), np.interp(t, s, p[:, 1])]), t


def wiggle_profile(p, closed, w, step):
    """Lateral wiggle (m): distance of each resampled point to a local quadratic Savitzky-Golay fit (window w m).
    Returns positions, values (NaN where the chain is too short to be measured)."""
    q, t = resample(p, step, closed)
    k = int(round(w / step)) | 1
    if len(q) <= k + 2:
        return q, np.full(len(q), np.nan)
    mode = "wrap" if closed else "interp"
    sm = np.column_stack([savgol_filter(q[:, 0], k, 2, mode=mode), savgol_filter(q[:, 1], k, 2, mode=mode)])
    return q, np.hypot(*(q - sm).T)


def sub_poly(p, lo, hi, closed, step=0.5):
    """Points of arc interval [lo, hi] of polyline p (wrapping for a closed one)."""
    if closed and np.hypot(*(p[0] - p[-1])) > 1e-9:
        p = np.vstack([p, p[:1]])
    s = arclen(p); L = s[-1]
    if closed and hi - lo >= L:
        lo, hi = 0.0, L
    if not closed:
        lo, hi = max(lo, 0.0), min(hi, L)
    t = np.r_[np.arange(lo, hi, step), hi]
    if closed:
        t = np.mod(t, L) if L > 0 else t
    return np.column_stack([np.interp(t, s, p[:, 0]), np.interp(t, s, p[:, 1])])


# ---------------------------------------------------------------- census and worklist
def natural_cut(wg, prm, pos, direction, L, closed):
    """End of a stretch: the first point EXT_MIN..EXT_MAX m beyond pos (direction -1 / +1) whose wiggle stays below
    CUT_QUIET within +-CUT_HALF m, else the quietest one; the end of an open chain is a natural cut. The prototype cut
    at box edges and left splice kinks where its 6 m end pins met a staircase."""
    step = prm["WIG_STEP"]
    cands = pos + direction * np.arange(prm["EXT_MIN"], prm["EXT_MAX"] + 1e-9, step)
    if not closed:
        cands = np.clip(cands, 0.0, L)
    n = len(wg)
    h = int(round(prm["CUT_HALF"] / step))
    loc = np.full(len(cands), np.inf)
    for i, k in enumerate(np.round(cands / step).astype(int)):
        if not closed and (cands[i] <= 0.0 or cands[i] >= L):
            loc[i] = -1.0                              # chain end
            continue
        ks = np.arange(k - h, k + h + 1)
        ks = np.mod(ks, n) if closed else ks[(ks >= 0) & (ks < n)]
        if len(ks):
            loc[i] = wg[ks].max()
    quiet = np.nonzero(loc < prm["CUT_QUIET"])[0]
    i = quiet[0] if len(quiet) else int(np.argmin(loc))
    return float(cands[i])


def census(H, W, fp, plane, arrays, prm, threshold):
    seg = extract_segments(H, W, fp, plane)
    vP = c2v_max(np.where(fp, plane, -np.inf))
    wet = (H < SEA) | (H < vP)
    edt = distance_transform_edt(wet) * 6.0
    yy, xx = np.mgrid[-4:5, -4:5]
    wideV = binary_dilation(edt >= prm["WIDE_CORE"], (yy ** 2 + xx ** 2) <= 16) & wet
    R, C = seg["cell"][:, 0], seg["cell"][:, 1]
    segwide = wideV[R, C] | wideV[R + 1, C] | wideV[R, C + 1] | wideV[R + 1, C + 1]
    frozen = arrays["reserve"] | arrays["platform"] | arrays["narva"]

    def c2(m):
        return m[:-1, :-1] | m[:-1, 1:] | m[1:, :-1] | m[1:, 1:]
    cfz1 = c2(binary_dilation(frozen, K3))
    cres = c2(binary_dilation(arrays["reserve"] & ~arrays["platform"], K3)); cplat = c2(binary_dilation(arrays["platform"], K3))
    cnarva = c2(arrays["narva"])
    chains = chain(seg)
    pts = np.vstack([c["pts"] for c in chains]); cid = np.concatenate([np.full(len(c["pts"]), i) for i, c in enumerate(chains)])
    arcs = np.concatenate([arclen(c["pts"]) for c in chains])
    lev = np.concatenate([np.full(len(c["pts"]), np.median(seg["lev"][c["order"]])) for c in chains])
    pairs = cKDTree(pts).query_pairs(prm["W_NARROW"], output_type="ndarray")
    i, j = pairs[:, 0], pairs[:, 1]
    ok = ((cid[i] != cid[j]) | (np.abs(arcs[i] - arcs[j]) >= prm["NARROW_ARC"])) & (np.hypot(*(pts[i] - pts[j]).T) > 1.0) \
        & (np.abs(lev[i] - lev[j]) < 1e-3)
    i, j = i[ok], j[ok]
    mid = 0.5 * (pts[i] + pts[j])
    wetmid = tri_h(H, mid[:, 0], mid[:, 1]) - lev[i] < 0
    narrow_pt = np.zeros(len(pts), bool)
    narrow_pt[i[wetmid]] = True; narrow_pt[j[wetmid]] = True
    off = 0
    windows = []
    chain_wig = {}
    WIN, STEPW = prm["WIN"], prm["STEPW"]
    for ci, c in enumerate(chains):
        order, p, closed = c["order"], c["pts"], c["closed"]
        npt = narrow_pt[off:off + len(p)]; off += len(p)
        s = arclen(p); L = s[-1]
        body = "pond" if seg["pond"][order].mean() >= 0.5 else "sea"
        w_ok = segwide[order] & ~(npt[:-1] | npt[1:])
        if L < 40 or w_ok.mean() < 0.2:
            continue
        _, wg = wiggle_profile(p, closed, prm["WIG_W"], prm["WIG_STEP"])
        chain_wig[ci] = wg
        tw = np.arange(len(wg)) * prm["WIG_STEP"]                 # resample() samples at 0, step, 2 step, ...
        smid = 0.5 * (s[:-1] + s[1:])
        for a in np.arange(0, max(L - WIN, 0) + 1e-6, STEPW):
            b = a + WIN
            m = (smid >= a) & (smid < b)
            if m.sum() < 4 or w_ok[m].mean() < 0.5:
                continue
            mw = (tw >= a) & (tw < b) & np.isfinite(wg)
            if not mw.any():
                continue
            idx = order[m]
            q = p[(s >= a) & (s < b)]
            cx, cz = q.mean(0)
            ffz = float(cfz1[R[idx], C[idx]].mean()); fres = float(cres[R[idx], C[idx]].mean())
            fpl = float(cplat[R[idx], C[idx]].mean()); fnar = float(cnarva[R[idx], C[idx]].mean())
            if ffz >= 0.25:
                cause = "frozen-narva" if fnar >= 0.5 else ("frozen-reserve-fringe" if fres >= fpl else "frozen-platform")
            else:
                cause = "free"
            windows.append(dict(chain=ci, body=body, a=float(a), x=float(cx), z=float(cz),
                                level=float(np.median(seg["lev"][idx])), wig_p90=float(np.percentile(wg[mw], 90)),
                                cause=cause))
    wl = [w for w in windows if w["wig_p90"] > threshold]
    wl.sort(key=lambda w: (w["chain"], w["a"]))
    groups = []
    for w in wl:
        g = groups[-1] if groups else None
        if g and g["chain"] == w["chain"] and w["a"] <= g["a1"] + 2 * prm["EXT_MIN"] and abs(w["level"] - g["level"]) < 1e-3:
            g["w"].append(w); g["a1"] = w["a"] + WIN
        else:
            groups.append(dict(chain=w["chain"], level=w["level"], a1=w["a"] + WIN, w=[w]))
    for g in groups:
        c = chains[g["chain"]]
        L = arclen(c["pts"])[-1]
        wg = np.nan_to_num(chain_wig[g["chain"]], nan=0.0)
        g["lo"] = natural_cut(wg, prm, g["w"][0]["a"], -1, L, c["closed"])
        g["hi"] = natural_cut(wg, prm, g["w"][-1]["a"] + WIN, 1, L, c["closed"])
    merged = []
    for g in groups:                                   # extended stretches of one chain never overlap
        m = merged[-1] if merged else None
        if m and m["chain"] == g["chain"] and abs(m["level"] - g["level"]) < 1e-3 and g["lo"] <= m["hi"]:
            m["w"] += g["w"]; m["hi"] = max(m["hi"], g["hi"])
        else:
            merged.append(g)
    stretches = []
    for g in merged:
        c = chains[g["chain"]]
        ws = g["w"]
        a0, a1 = ws[0]["a"], ws[-1]["a"] + WIN
        covered = 0.0; cur = None
        for w in ws:                                   # union of window intervals
            lo, hi = w["a"], w["a"] + WIN
            if cur is None or lo > cur[1]:
                if cur:
                    covered += cur[1] - cur[0]
                cur = [lo, hi]
            else:
                cur[1] = max(cur[1], hi)
        covered += cur[1] - cur[0]
        poly = sub_poly(c["pts"], g["lo"], g["hi"], c["closed"], 1.0)
        causes = defaultdict(int)
        for w in ws:
            causes[w["cause"]] += 1
        stretches.append(dict(body=ws[0]["body"], level=g["level"], chain_len_m=round(float(arclen(c["pts"])[-1]), 1),
                              closed=c["closed"], a0=a0, a1=a1, cut=[round(float(g["lo"]), 1), round(float(g["hi"]), 1)],
                              extent_m=round(a1 - a0, 1), covered_m=round(covered, 1),
                              treated_interval_m=round(float(g["hi"] - g["lo"]), 1),
                              windows=len(ws), wig_p90_max=round(max(w["wig_p90"] for w in ws), 3),
                              x=round(float(np.mean([w["x"] for w in ws])), 1), z=round(float(np.mean([w["z"] for w in ws])), 1),
                              cause=max(causes, key=causes.get), poly=np.round(poly, 3).tolist()))
    stretches.sort(key=lambda s: -s["wig_p90_max"] * np.sqrt(s["windows"]))
    for k, s in enumerate(stretches):
        s["id"] = k
    wp = np.array([w["wig_p90"] for w in windows]) if windows else np.zeros(1)
    summ = dict(segments=int(len(seg["key"])), chains=len(chains), discontinuities=discontinuities(seg)[0],
                windows=len(windows), windows_over_threshold=len(wl), threshold=threshold,
                window_wig_p90=dict(p50=round(float(np.percentile(wp, 50)), 3), p90=round(float(np.percentile(wp, 90)), 3)),
                stretches=len(stretches), extent_km=round(sum(s["extent_m"] for s in stretches) / 1000, 3),
                covered_km=round(sum(s["covered_m"] for s in stretches) / 1000, 3))
    return stretches, summ


# ---------------------------------------------------------------- protection
def pending_crossings(path=None, extra_built=()):
    """Pending 015 crossings: the inventory crossings-ev106.json minus the built sites (sites-pilot.json,
    ev109/sites-rollout.json, extra_built). An override file (path) must hold inventory crossings only, with their
    inventory coordinates and unique ids."""
    ev = os.path.normpath(os.path.join(HERE, "..", "..", "evidence", "v31-pond-layer-2026-10-13", "bridges"))
    inv_p = os.path.join(ev, "crossings-ev106.json")
    inv = {f"015-{c['n']}": c for c in json.load(open(inv_p, encoding="utf-8"))}
    assert len(inv) == len(json.load(open(inv_p, encoding="utf-8"))), "duplicate numbers in the crossing inventory"
    if path:
        cr = json.load(open(path, encoding="utf-8"))
        out = [dict(id=str(c.get("id", c.get("n"))), x=float(c["x"]), z=float(c["z"])) for c in cr]
        ids = [c["id"] for c in out]
        assert len(ids) == len(set(ids)), "duplicate ids in --crossings"
        for c in out:
            assert c["id"] in inv, f"--crossings {c['id']} is not in {inv_p}"
            ref = inv[c["id"]]
            assert abs(c["x"] - float(ref["x"])) <= 0.01 and abs(c["z"] - float(ref["z"])) <= 0.01, \
                f"--crossings {c['id']} coordinates differ from the inventory"
        return out, dict(source=path, sha256=sha(path), inventory=inv_p, inventory_sha256=sha(inv_p), override=True)
    src = [os.path.join(ev, "sites-pilot.json"), os.path.join(ev, "ev109", "sites-rollout.json")] + list(extra_built)
    built = set()
    for p in src:
        for s in json.load(open(p, encoding="utf-8")):
            built.add(int(str(s["id"]).split("-")[-1]))
    out = [dict(id=k, x=float(c["x"]), z=float(c["z"]), plan=c.get("plan")) for k, c in inv.items() if int(c["n"]) not in built]
    return out, dict(source=[inv_p] + src, sha256=[sha(inv_p)] + [sha(p) for p in src], built=sorted(built), override=False)


def base_protection(arrays, crossings, prm):
    k = np.ones((2 * prm["PROT_DILATE"] + 1,) * 2, bool)
    prot = arrays["platform"] | arrays["narva"] | arrays["v31_lagoon"]
    dil = []
    for name in arrays:
        if name in ("v31_kit", "v31_bridge_cut") or name.startswith("v31_lattice") or name.startswith("v31_bridge_"):
            if arrays[name].dtype == bool and arrays[name].shape == (N, N):
                prot |= binary_dilation(arrays[name], k); dil.append(name)
    rr, cc = np.mgrid[0:N, 0:N]
    xs, zs = vxz(rr, cc)
    near = np.zeros((N, N), bool)
    for c in crossings:
        near |= np.hypot(xs - c["x"], zs - c["z"]) < prm["CROSS_EXCL"]
    prot |= near
    return prot, dict(dilated=dil, crossing_vertices=int(near.sum()))


class BodyProt:
    def __init__(self, base, env_plane, plane, field):
        self.base, self.env_plane, self.env = base, env_plane, np.isfinite(env_plane)
        fpm = np.isfinite(plane)
        dev = np.zeros(plane.shape, bool)
        dev[fpm] = np.max(np.abs(field[fpm] - plane[fpm][:, None]), axis=-1) > 1e-3
        self.fdev = dev
        self.nonenv_v = c2v(~self.env)
        self.cache = {}

    def get(self, body, level):
        key = ("sea",) if body == "sea" else ("pond", round(level, 4))
        if key not in self.cache:
            if body == "sea":
                p = self.base | c2v(self.env)
            else:
                other = self.env & (np.abs(self.env_plane - level) > 1e-3)
                p = self.base | c2v(other | self.fdev)
            self.cache[key] = p
        return self.cache[key]


# ---------------------------------------------------------------- one stretch
def smooth_pinned(p, pinned, closed, sigma, pull_idx=None, pull_xy=None, pull_w=0.0):
    """Arc-length smoothing spline: min sum w |C - p|^2 + pull_w |C[pull_idx] - pull_xy|^2 + sigma^4 |D2 C|^2,
    w = 1e8 on pins, 1 elsewhere. sigma is always passed by the caller."""
    n = len(p)
    if n < 5:
        return p.copy()
    lam = float(sigma) ** 4
    if closed:
        idx = np.arange(n)
        Dm = sparse.csr_matrix((np.r_[np.ones(n), -2 * np.ones(n), np.ones(n)],
                                (np.r_[idx, idx, idx], np.r_[(idx - 1) % n, idx, (idx + 1) % n])), shape=(n, n))
    else:
        idx = np.arange(1, n - 1)
        Dm = sparse.csr_matrix((np.r_[np.ones(n - 2), -2 * np.ones(n - 2), np.ones(n - 2)],
                                (np.r_[idx - 1, idx - 1, idx - 1], np.r_[idx - 1, idx, idx + 1])), shape=(n - 2, n))
    w = np.where(pinned, 1e8, 1.0)
    rx, rz = w * p[:, 0], w * p[:, 1]
    if pull_idx is not None and len(pull_idx):
        w = w.copy()
        np.add.at(w, pull_idx, pull_w)
        rx = rx.copy(); rz = rz.copy()
        np.add.at(rx, pull_idx, pull_w * pull_xy[:, 0]); np.add.at(rz, pull_idx, pull_w * pull_xy[:, 1])
    A = (sparse.diags(w) + lam * (Dm.T @ Dm)).tocsc()
    return np.column_stack([spsolve(A, rx), spsolve(A, rz)])


def stretch_box(st, prm):
    poly = np.asarray(st["poly"])
    m = prm["BOXM"]
    return float(poly[:, 0].min() - m), float(poly[:, 0].max() + m), float(poly[:, 1].min() - m), float(poly[:, 1].max() + m)


def run_stretch(H, W, fp, plane, prot, nonenv_v, st, sigma, prm):
    """Returns (rows, cols, new heights, info, portions); rows empty when nothing is treated (reason in info)."""
    body, level = st["body"], st["level"]
    x0, x1, z0, z1 = box = stretch_box(st, prm)
    r0 = max(int((ZTOP - z1) / 6) - 6, 0); r1 = min(int((ZTOP - z0) / 6) + 7, NC)
    c0 = max(int(x0 / 6) - 6, 0); c1 = min(int(x1 / 6) + 7, NC)
    nr, nc = r1 - r0 + 1, c1 - c0 + 1
    RR, CC = np.mgrid[r0:r1 + 1, c0:c1 + 1]
    R, Cc = RR.ravel(), CC.ravel()
    Hw = H[r0:r1 + 1, c0:c1 + 1].astype(np.float64)
    D0 = Hw.ravel() - level
    pw = prot[r0:r1 + 1, c0:c1 + 1].ravel()
    info = dict(box=[round(v, 1) for v in box])
    # side requirements (strict): protected vertices with |D| > 0.1 and their free native-edge neighbours
    req = np.zeros(len(R))
    pm = pw & (np.abs(D0) > 0.1)
    req[pm] = np.sign(D0[pm])
    rq = req.reshape(nr, nc)
    nb = np.zeros((nr, nc))
    for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0), (-1, -1), (1, 1)):
        sh = np.zeros_like(rq)
        src = rq[max(-dr, 0):nr - max(dr, 0), max(-dc, 0):nc - max(dc, 0)]
        sh[max(dr, 0):nr - max(-dr, 0), max(dc, 0):nc - max(-dc, 0)] = src
        nb = np.where(nb == 0, sh, np.where((sh != 0) & (sh != nb), 9, nb))
    nb = nb.ravel()
    add = (req == 0) & ~pw & (nb != 0) & (nb != 9)
    req[add] = nb[add]
    if body != "sea":
        req[nonenv_v[r0:r1 + 1, c0:c1 + 1].ravel()] = 1.0
    sel = req != 0
    cxy = np.column_stack(vxz(R[sel], Cc[sel])); creq = req[sel]
    # waterline of the body in the window
    seg = extract_segments(H, W, fp, plane, r0, r1, c0, c1)
    keep = ~seg["pond"] if body == "sea" else seg["pond"] & (np.abs(seg["lev"] - level) < 1e-3)
    other_seg = subseg(seg, ~keep); seg = subseg(seg, keep)
    if len(seg["key"]) == 0:
        info["reason"] = "no waterline of the body in the window"
        return np.zeros(0, int), np.zeros(0, int), np.zeros(0), info, []
    chains = chain(seg)
    allp = np.vstack([c["pts"] for c in chains]); cid = np.concatenate([np.full(len(c["pts"]), i) for i, c in enumerate(chains)])
    arc = np.concatenate([arclen(c["pts"]) for c in chains])
    narrow = np.zeros(len(allp), bool)
    pr = cKDTree(allp).query_pairs(prm["W_NARROW"], output_type="ndarray")
    if len(pr):
        i, j = pr[:, 0], pr[:, 1]
        ok = ((cid[i] != cid[j]) | (np.abs(arc[i] - arc[j]) >= prm["NARROW_ARC"])) & (np.hypot(*(allp[i] - allp[j]).T) > 1.0)
        i, j = i[ok], j[ok]
        mid = 0.5 * (allp[i] + allp[j])
        wm = tri_h(H, mid[:, 0], mid[:, 1]) - level < 0
        narrow[i[wm]] = True; narrow[j[wm]] = True
    tube = cKDTree(sub_poly(np.asarray(st["poly"]), 0, 1e12, False, 0.5))
    pflat = prot.ravel()
    portions, untouched, skipped = [], [], []
    off = 0
    END_PIN = prm["END_PIN"]
    for c in chains:
        p, closed = c["pts"], c["closed"]
        nar = narrow[off:off + len(p)]; off += len(p)
        ek = c["keys"]                                            # grid edge of every point
        va, vb = ek // (N * N), ek % (N * N)
        pin = pflat[va] & pflat[vb]
        dtube, _ = tube.query(p)
        inb = (dtube <= prm["TUBE"]) & ~nar & (p[:, 0] >= x0) & (p[:, 0] <= x1) & (p[:, 1] >= z0) & (p[:, 1] <= z1)
        if closed and inb.all():
            runs = [(0, len(p), True)]
        else:
            runs, i = [], 0
            while i < len(p):
                if inb[i]:
                    j = i
                    while j < len(p) and inb[j]:
                        j += 1
                    runs.append((i, j, False)); i = j
                else:
                    i += 1
        covered = np.zeros(len(p), bool)
        for a, b, cl in runs:
            q = p[a:b]
            if len(q) < 3:
                continue
            s = arclen(q)
            if s[-1] < prm["MIN_PORTION"]:
                continue
            ffrac = float(pin[a:b].mean())
            if ffrac > prm["FIXED_FRAC_MAX"]:
                skipped.append(dict(reason="fixed_fraction", fixed_frac=round(ffrac, 3), length_m=round(float(s[-1]), 1)))
                continue
            covered[a:b] = True
            pins_s = s[pin[a:b]]
            grid = np.arange(0, s[-1], 1.0)
            if not cl:
                grid = np.r_[grid, s[-1]]
            ss = np.unique(np.r_[grid, pins_s])
            qq = np.column_stack([np.interp(ss, s, q[:, 0]), np.interp(ss, s, q[:, 1])])
            pinned = np.isin(ss, pins_s)
            if not cl:
                pinned |= (ss <= END_PIN) | (ss >= s[-1] - END_PIN)
            if cl and np.hypot(*(qq[0] - qq[-1])) < 1e-6:
                qq, ss, pinned = qq[:-1], ss[:-1], pinned[:-1]
            d = np.diff(q, axis=0); mid = 0.5 * (q[:-1] + q[1:])
            ln = np.hypot(d[:, 0], d[:, 1])
            nrm = np.column_stack([-d[:, 1], d[:, 0]]) / np.maximum(ln, 1e-9)[:, None]
            okm = ln > 0.2
            if not okm.any():
                okm = ln > 0
            dl = tri_h(H, mid[okm, 0] + 0.3 * nrm[okm, 0], mid[okm, 1] + 0.3 * nrm[okm, 1]) - level
            wet_left = 1 if np.mean(dl < 0) >= 0.5 else -1
            C = C_free = smooth_pinned(qq, pinned, cl, sigma)
            n_side = n_unres = 0
            if len(cxy):
                # side constraints enter the spline as soft pulls (the prototype added 6 m Gaussian bumps after the
                # spline, and those bumps were the wiggle left in the target); the pulled target stays a spline
                pulls = {}
                C_ref = None
                for it in range(prm["SIDE_ITERS"]):
                    dist, jj = cKDTree(C).query(cxy)
                    g = np.gradient(C, axis=0); g /= np.maximum(np.hypot(g[:, 0], g[:, 1]), 1e-9)[:, None]
                    v = cxy - C[jj]
                    cr = g[jj, 0] * v[:, 1] - g[jj, 1] * v[:, 0]
                    sdv = np.where(cr * wet_left > 0, -dist, dist)
                    near = (dist < prm["B0"]) & ~pinned[jj]
                    if not cl:
                        near &= (ss[jj] > END_PIN) & (ss[jj] < ss[-1] - END_PIN)
                    need = prm["SIDE_MARGIN"] - creq * sdv
                    viol = near & (need > 0)
                    if it == 0:
                        n_side = int(viol.sum())
                    if not viol.any():
                        break
                    wetdir = np.column_stack([-g[:, 1], g[:, 0]]) * wet_left
                    step = {}
                    for k in np.nonzero(viol)[0]:
                        amt = need[k] * creq[k]
                        j = int(jj[k])
                        if j not in step or abs(amt) > abs(step[j]):
                            step[j] = amt
                    for j, amt in step.items():
                        pulls[j] = C[j] + amt * wetdir[j]
                    pidx = np.array(sorted(pulls)); pxy = np.array([pulls[j] for j in pidx])
                    Cn = smooth_pinned(qq, pinned, cl, sigma * prm["PULL_STIFF"], pidx, pxy, prm["PULL_W"])
                    if C_ref is None:
                        C_ref = C_free if prm["PULL_STIFF"] == 1.0 else smooth_pinned(qq, pinned, cl, sigma * prm["PULL_STIFF"])
                    disp = np.hypot(*(Cn - C_ref).T)
                    if disp.max() > prm["SIDE_MAX"]:
                        break
                    C = Cn
                dist, jj = cKDTree(C).query(cxy)
                g = np.gradient(C, axis=0); g /= np.maximum(np.hypot(g[:, 0], g[:, 1]), 1e-9)[:, None]
                v = cxy - C[jj]; cr = g[jj, 0] * v[:, 1] - g[jj, 1] * v[:, 0]
                sdv = np.where(cr * wet_left > 0, -dist, dist)
                near = (dist < prm["B0"]) & ~pinned[jj]
                if not cl:
                    near &= (ss[jj] > END_PIN) & (ss[jj] < ss[-1] - END_PIN)
                n_unres = int((near & (creq * sdv < 0)).sum())
            portions.append(dict(C=C, closed=cl, wet_left=wet_left, n_pins=int(pin[a:b].sum()), fixed_frac=round(ffrac, 3),
                                 n_side=n_side, n_unres=n_unres, L=float(s[-1])))
        if (~covered).any():
            untouched.append(p[~covered])
    info["skipped_portions"] = skipped
    if not portions:
        info["reason"] = "no treatable portion (fixed fraction, narrow, short or outside the tube)"
        return np.zeros(0, int), np.zeros(0, int), np.zeros(0), info, []
    # signed distance of the window vertices to the targets
    tp, tg, tw_, tend = [], [], [], []
    for po in portions:
        C2 = np.vstack([po["C"], po["C"][:1]]) if po["closed"] else po["C"]
        s = arclen(C2)
        t = np.arange(0, s[-1], 0.25)
        q = np.column_stack([np.interp(t, s, C2[:, 0]), np.interp(t, s, C2[:, 1])])
        g = np.gradient(q, axis=0); g /= np.maximum(np.hypot(g[:, 0], g[:, 1]), 1e-9)[:, None]
        tp.append(q); tg.append(g); tw_.append(np.full(len(q), po["wet_left"]))
        tend.append(np.zeros(len(q), bool) if po["closed"] else (t < END_PIN) | (t > s[-1] - END_PIN))
    tp = np.vstack(tp); tg = np.vstack(tg); tw_ = np.concatenate(tw_); tend = np.concatenate(tend)
    ttree = cKDTree(tp)
    xv, zv = vxz(R, Cc)
    xz = np.column_stack([xv, zv])
    dist, jn = ttree.query(xz)
    v = xz - tp[jn]
    crs = tg[jn, 0] * v[:, 1] - tg[jn, 1] * v[:, 0]
    sd = np.where(crs * tw_[jn] > 0, -dist, dist)
    endz = tend[jn]
    inbox = (xv >= x0) & (xv <= x1) & (zv >= z0) & (zv <= z1)
    keep_v = np.zeros((nr, nc), bool)
    if len(other_seg["cell"]):
        rr, cc = other_seg["cell"][:, 0] - r0, other_seg["cell"][:, 1] - c0
        for dr in (0, 1):
            for dc in (0, 1):
                keep_v[np.clip(rr + dr, 0, nr - 1), np.clip(cc + dc, 0, nc - 1)] = True
    if untouched:
        up = np.vstack(untouched)
        uc = (up[:, 0] / 6).astype(int) - c0; ur = ((ZTOP - up[:, 1]) / 6).astype(int) - r0
        for dr in (-1, 0, 1, 2):
            for dc in (-1, 0, 1, 2):
                keep_v[np.clip(ur + dr, 0, nr - 1), np.clip(uc + dc, 0, nc - 1)] = True
        du, _ = cKDTree(up).query(xz)
        keep_v.ravel()[du < dist] = True
    keep_v = keep_v.ravel()
    free = inbox & ~pw & ~endz & ~keep_v
    B0, B1 = prm["B0"], prm["B1"]
    E = free & (np.abs(sd) <= B0)
    E2 = free & (np.abs(sd) > B0) & (np.abs(sd) <= B1)
    if not E.any():
        info["reason"] = "no free vertex within B0 of the target"
        return np.zeros(0, int), np.zeros(0, int), np.zeros(0), info, []
    loc = -np.ones(nr * nc, int)
    loc[np.nonzero(E)[0]] = np.arange(E.sum())
    gi = np.arange(nr * nc).reshape(nr, nc)
    pairs = [(gi[:, :-1].ravel(), gi[:, 1:].ravel()), (gi[:-1, :].ravel(), gi[1:, :].ravel()),
             (gi[:-1, :-1].ravel(), gi[1:, 1:].ravel())]
    a = np.concatenate([q[0] for q in pairs]); b = np.concatenate([q[1] for q in pairs])
    crossm = (np.sign(sd[a]) != np.sign(sd[b])) & (E[a] | E[b]) & (np.abs(sd[a]) < B0 + 9) & (np.abs(sd[b]) < B0 + 9)
    a, b = a[crossm], b[crossm]
    t = sd[a] / (sd[a] - sd[b])
    fitm = E & (np.abs(sd) > 0.5)
    s_fit = float(np.sum(sd[fitm] * D0[fitm]) / max(np.sum(sd[fitm] ** 2), 1e-9))
    s = float(np.clip(s_fit, prm["S_MIN"], prm["S_MAX"]))
    s_bed = None
    if body != "sea":
        cv = np.unique(np.r_[a, b])
        deep = np.max(np.r_[0.0, -sd[cv][sd[cv] < 0]])
        if deep > 0:
            s_bed = (level - prm["BED"]) / deep
            s = min(s, s_bed)
    nE = int(E.sum())
    rows, cols, vals, rhs = [], [], [], []
    WE = prm["W_EDGE"]
    for k, (ia, ib, tt) in enumerate(zip(a, b, t)):
        rv = 0.0
        for vtx, wgt in ((ia, 1 - tt), (ib, tt)):
            if E[vtx]:
                rows.append(k); cols.append(loc[vtx]); vals.append(WE * wgt)
            else:
                rv -= WE * wgt * D0[vtx]
        rhs.append(rv)
    k = len(a)
    Eidx = np.nonzero(E)[0]
    rows += list(range(k, k + nE)); cols += list(loc[Eidx]); vals += [1.0] * nE; rhs += list(s * sd[Eidx])
    A = sparse.csr_matrix((vals, (rows, cols)), shape=(k + nE, nE))
    sol = spsolve((A.T @ A).tocsc(), A.T @ np.array(rhs))
    Dn = D0.copy()
    Dn[Eidx] = sol
    capped = E & (np.abs(Dn - s * sd) > prm["DEV_MAX"])
    Dn = np.where(capped, s * sd + np.clip(Dn - s * sd, -prm["DEV_MAX"], prm["DEV_MAX"]), Dn)
    bad = E & (np.sign(Dn) != np.sign(sd)) & (np.abs(sd) > 1e-6)
    Dn[bad] = s * sd[bad]
    u = np.clip((np.abs(sd) - B0) / (B1 - B0), 0, 1); u = u * u * (3 - 2 * u)
    Db = (1 - u) * s * sd + u * D0
    Db = np.where(sd > 0, np.maximum(Db, np.minimum(s * sd, prm["CLR_LAND"])),
                  np.minimum(Db, -np.minimum(s * np.abs(sd), prm["CLR_WATER"])))
    Dn[E2] = Db[E2]
    Hn = level + Dn
    Hold = Hw.ravel()
    bed_clamped = 0
    if body != "sea":
        need = (E | E2) & (Hn < prm["BED"]) & (Hold >= prm["BED"])
        bed_clamped = int((need & E).sum())
        Hn = np.where(need, prm["BED"], Hn)
        need2 = (E | E2) & (Hn < Hold) & (Hold < prm["BED"])
        Hn = np.where(need2, Hold, Hn)
        nev = nonenv_v[r0:r1 + 1, c0:c1 + 1].ravel()
        envbad = (E | E2) & nev & (Hn < level + prm["CLR_LAND"])
        Hn = np.where(envbad, np.maximum(Hn, level + prm["CLR_LAND"]), Hn)
    # B-strict on the final heights: the pulls of the target are soft, so the vertices still on the wrong side of their
    # protected neighbours are set SIDE_CLR m onto the required side (the waterline then runs one triangle out from the
    # frozen ground, as the strict contract states); the pond bed rule is applied again and the result is checked below
    Dc = Hn - level
    side_fix = (E | E2) & (((req > 0) & (Dc < 0)) | ((req < 0) & (Dc >= 0)))
    Hn = np.where(side_fix, level + req * prm["SIDE_CLR"], Hn)
    if body != "sea":
        Hn = np.where((E | E2) & (Hn < prm["BED"]) & (Hold >= prm["BED"]), prm["BED"], Hn)
    Hn32 = Hn.astype(np.float32).astype(np.float64)
    Hold32 = Hold.astype(np.float32).astype(np.float64)
    ch = (E | E2) & (Hn32 != Hold32)
    assert not (ch & pw).any(), "protected vertex changed"
    D32 = Hn32 - level
    side_bad = ch & (((req > 0) & (D32 < 0)) | ((req < 0) & (D32 >= 0)))
    info["side_projected"] = int((side_fix & ch).sum())
    info["side_violations_final"] = int(side_bad.sum())
    info.update(portions=len(portions), portion_len_m=round(sum(p["L"] for p in portions), 1),
                pins=int(sum(p["n_pins"] for p in portions)), fixed_frac_max=max(p["fixed_frac"] for p in portions),
                side_constraint_hits=int(sum(p["n_side"] for p in portions)),
                side_unresolved=int(sum(p["n_unres"] for p in portions)), s_fit=round(s_fit, 4), s=round(s, 4),
                s_bed=None if s_bed is None else round(s_bed, 4), ramp_vertices=nE, blend_vertices=int(E2.sum()),
                crossed_edges=int(len(t)), crossed_edges_with_fixed_end=int(np.sum(~E[a] | ~E[b])),
                dev_capped=int(capped.sum()), sign_fixed=int(bad.sum()), bed_clamped_in_ramp=bed_clamped)
    return R[ch], Cc[ch], Hn32[ch], info, portions


SLOPE_TOL = 1e-6      # deg: guard margin for the difference between this slope formula and a normal-vector one


def slope_bad(s0, s1, prm):
    """Triangles that cross SLOPE_MAX (no tolerance: <= limit before, > limit after) or that were over it and get steeper
    by more than SLOPE_EPS. The guard counts a triangle within SLOPE_TOL of the limit as crossing it. A non-finite slope
    after is bad."""
    lim, eps = prm["SLOPE_MAX"], prm["SLOPE_EPS"]
    over0 = s0 > lim + SLOPE_TOL
    cross = ~over0 & (s1 > lim - SLOPE_TOL) & (s1 > s0)
    worse = over0 & (s1 > s0 + eps)
    return cross | worse | ~np.isfinite(s1)


def slope_guard(H, rows, cols, vals, prm):
    """Changed triangles that cross SLOPE_MAX or get steeper above it. Returns (count, max before, max after)."""
    r0, r1 = max(rows.min() - 1, 0), min(rows.max() + 2, N); c0, c1 = max(cols.min() - 1, 0), min(cols.max() + 2, N)
    h0 = H[r0:r1, c0:c1].astype(np.float64); h1 = h0.copy()
    h1[rows - r0, cols - c0] = vals
    chv = np.zeros(h0.shape, bool); chv[rows - r0, cols - c0] = True
    a0, b0 = tri_slopes(h0); a1, b1 = tri_slopes(h1)
    ca = chv[:-1, :-1] | chv[:-1, 1:] | chv[1:, 1:]
    cb = chv[:-1, :-1] | chv[1:, :-1] | chv[1:, 1:]
    n = int((slope_bad(a0, a1, prm) & ca).sum() + (slope_bad(b0, b1, prm) & cb).sum())
    mb = float(max(a0[ca].max(initial=0), b0[cb].max(initial=0))); ma = float(max(a1[ca].max(initial=0), b1[cb].max(initial=0)))
    return n, mb, ma


def run_pass(H0, W, fp, plane, bprot, stretches, rejected, sigma, prm, attempt):
    H = H0.copy()
    owner = np.full((N, N), -1, np.int32)
    res, targets = {}, {}
    for st in stretches:
        sid = st["id"]
        r = dict(id=sid)
        if sid in rejected:
            r["status"] = "rejected"; res[sid] = r
            continue
        prot = bprot.get(st["body"], st["level"]) | (owner >= 0)
        r["variant"] = attempt.get(sid, 0)
        sprm = dict(prm, **RETRY[r["variant"]])
        rows, cols, vals, info, portions = run_stretch(H, W, fp, plane, prot, bprot.nonenv_v, st, sigma, sprm)
        r["info"] = info
        if len(rows) == 0:
            r["status"] = "skipped"; res[sid] = r
            continue
        n35, smb, sma = slope_guard(H, rows, cols, vals, prm)
        r["slope_max_changed_tris_deg"] = dict(before=round(smb, 2), after=round(sma, 2)); r["new_tris_over_limit"] = n35
        loc = []
        if n35:
            loc.append(f"slope: {n35} changed triangles cross {prm['SLOPE_MAX']} deg or get steeper above it")
        if info["side_violations_final"]:
            loc.append(f"strict side: {info['side_violations_final']} changed vertices end on the wrong side")
        if loc:
            r["status"] = "rejected"; r["reject_local"] = loc
            res[sid] = r
            continue
        H[rows, cols] = vals
        owner[rows, cols] = sid
        r["status"] = "treated"; r["vertices_changed"] = int(len(rows))
        res[sid] = r
        targets[sid] = [dict(C=np.round(p["C"], 3).tolist(), closed=p["closed"]) for p in portions]
    return H, owner, res, targets


# ---------------------------------------------------------------- validation
def fp_masks(H, plane, field, env, prm):
    fpm = np.isfinite(plane)
    vin = c2v(fpm)
    vout = c2v(~fpm) | np.pad(np.zeros((N - 2, N - 2), bool), 1, constant_values=True)
    vP = c2v_max(np.where(fpm, plane, -np.inf))
    border = vin & vout
    cmin = np.minimum.reduce([H[:-1, :-1], H[:-1, 1:], H[1:, :-1], H[1:, 1:]])
    dev = np.abs(field - plane[:, :, None])
    vmaxF = c2v_max(np.where(fpm[:, :, None], field, -np.inf).max(axis=-1))
    return dict(exposed=border & (H < vP + prm["EDGE_MARGIN"]),
                env_leak=vin & c2v(~env) & (H < vP),
                bed_low=vin & (H < 1.0) & (H < np.maximum(vmaxF, vP)),
                pond_sea=c2v(fpm & (cmin < SEA)),
                field_dev=c2v(np.nan_to_num(dev, nan=0.0).max(axis=-1) > prm["FIELD_MAX_DEV"] + 1e-9),
                n_pond_sea_cells=int((fpm & (cmin < SEA)).sum()), n_fp_cells=int(fpm.sum()))


def sea_topology(Hb, Ha):
    """Correspondence of engine-sea components (H < SEA) over native triangle edges. Returns lists of vertex masks."""
    wb, wa = Hb < SEA, Ha < SEA
    Lb, nb = label(wb, S6); La, na = label(wa, S6)
    both = wb & wa
    pr = np.unique(np.stack([Lb[both], La[both]], 1), axis=0) if both.any() else np.zeros((0, 2), int)
    cb = np.bincount(pr[:, 0], minlength=nb + 1); ca = np.bincount(pr[:, 1], minlength=na + 1)
    created = [l for l in range(1, na + 1) if ca[l] == 0]
    removed = [l for l in range(1, nb + 1) if cb[l] == 0]
    split = [l for l in range(1, nb + 1) if cb[l] > 1]
    merged = [l for l in range(1, na + 1) if ca[l] > 1]
    bad = []
    if created:
        bad.append(("sea component created", np.isin(La, created)))
    if removed:
        bad.append(("sea component removed", np.isin(Lb, removed)))
    if split:
        bad.append(("sea component split", np.isin(Lb, split) & ~wa))
    if merged:
        bad.append(("sea components merged", np.isin(La, merged) & ~wb))
    return dict(before=int(nb), after=int(na), created=len(created), removed=len(removed), split=len(split),
                merged=len(merged)), bad


def canonical(p, closed):
    """Start and direction independent of how a polyline was walked: open ones start at their lexicographically smaller
    end; closed ones at their smallest vertex, counter-clockwise. The 0.5 m samples of the wiggle then fall on the same
    points in any implementation (an arbitrary start moved the p90 of a stretch by up to 0.011 m)."""
    p = np.asarray(p, float)
    if not closed:
        return p[::-1].copy() if (p[-1, 0], p[-1, 1]) < (p[0, 0], p[0, 1]) else p
    if len(p) > 1 and p[0, 0] == p[-1, 0] and p[0, 1] == p[-1, 1]:
        p = p[:-1]
    if len(p) < 3:
        return p
    area = np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])
    if area < 0:
        p = p[::-1]
    k = np.lexsort((p[:, 1], p[:, 0]))[0]
    return np.vstack([np.roll(p, -k, axis=0), np.roll(p, -k, axis=0)[:1]])


def wiggle_samples(H, W, fp, plane, prm):
    """Wiggle samples of the whole waterline, and its geometry: seg plus, per segment, its chain (seg["chain"]) and, per
    chain, measured (some finite sample), closed and number of segments (seg["chains"])."""
    seg = extract_segments(H, W, fp, plane)
    qs, vs = [], []
    sc = np.full(len(seg["key"]), -1)
    meas, clo, nseg = [], [], []
    for ci, c in enumerate(chain(seg)):
        q, v = wiggle_profile(canonical(c["pts"], c["closed"]), c["closed"], prm["WIG_W"], prm["WIG_STEP"])
        qs.append(q); vs.append(v)
        sc[c["order"]] = ci
        meas.append(bool(np.isfinite(v).any())); clo.append(c["closed"]); nseg.append(len(c["order"]))
    assert (sc >= 0).all()
    seg["chain"] = sc
    seg["chains"] = dict(measured=np.array(meas), closed=np.array(clo), nseg=np.array(nseg))
    return np.vstack(qs), np.concatenate(vs), seg


def chain_coverage(seg, idx):
    """Coverage of the waterline segments idx: segments on chains too short to be measured, chains touched, closed
    chains lying wholly inside idx."""
    ch, info = seg["chain"][idx], seg["chains"]
    un = ~info["measured"][ch]
    lines = np.unique(ch)
    cnt = np.bincount(ch, minlength=len(info["measured"]))
    inside = int(sum(1 for l in lines if info["closed"][l] and cnt[l] == info["nseg"][l]))
    return dict(segments=int(len(idx)), unmeasured_segments=int(un.sum()), chains=int(len(lines)), closed_inside=inside)


def tri_owner_cols(owner, x, z):
    """Owners (n,3) of the three vertices of the native triangle holding each point."""
    c, r = np.asarray(x) / 6.0, (ZTOP - np.asarray(z)) / 6.0
    c0 = np.clip(np.floor(c).astype(int), 0, NC - 1); r0 = np.clip(np.floor(r).astype(int), 0, NC - 1)
    A = (c - c0) >= (r - r0)
    o1 = owner[r0, c0]; o3 = owner[r0 + 1, c0 + 1]
    o2 = np.where(A, owner[r0, c0 + 1], owner[r0 + 1, c0])
    return np.stack([o1, o2, o3], 1)


def group_by_owner(own3):
    out = defaultdict(list)
    for col in range(3):
        idx = np.nonzero(own3[:, col] >= 0)[0]
        for i, o in zip(idx, own3[idx, col]):
            out[int(o)].append(i)
    return {k: np.unique(v) for k, v in out.items()}


def seg_owner_cols(owner, seg):
    r, c, t = seg["cell"][:, 0], seg["cell"][:, 1], seg["tri"]
    o1 = owner[r, c]; o3 = owner[r + 1, c + 1]
    o2 = np.where(t == 0, owner[r, c + 1], owner[r + 1, c])
    return np.stack([o1, o2, o3], 1)


def pct(a, q):
    return round(float(np.percentile(a, q)), 4) if len(a) else None


def validate(ctx, Hc, owner, targets, rnd, prm):
    work, arrays = ctx["work"], ctx["arrays"]
    rd = os.path.join(work, f"round{rnd}")
    os.makedirs(rd)
    cand = os.path.join(rd, "terrain.npz")
    write_terrain(cand, arrays, Hc, ctx["H0"])
    np.save(os.path.join(rd, "owner.npy"), owner)
    with open(os.path.join(rd, "targets.json"), "w", encoding="utf-8") as f:
        json.dump({str(k): v for k, v in targets.items()}, f)
    fpdir = os.path.join(rd, "fp")
    subprocess.run([sys.executable, "-I", ctx["fp_tool"], cand, ctx["cover"], fpdir, ctx["env_path"]], check=True,
                   stdout=subprocess.DEVNULL)
    f1 = np.load(os.path.join(fpdir, "footprint.npz"))
    plane1, field1 = f1["plane"].astype(np.float64), f1["field"].astype(np.float64)
    W1, fp1 = corner_water(plane1, field1)
    rej = defaultdict(list)
    unattributed = []

    def attribute(vmask, reason):
        if not vmask.any():
            return 0
        d = binary_dilation(vmask, K3, iterations=prm["ATTR_RINGS"])
        ids = np.unique(owner[d]); ids = ids[ids >= 0]
        if len(ids) == 0:
            unattributed.append(dict(reason=reason, n=int(vmask.sum()), at=[list(map(int, x)) for x in np.argwhere(vmask)[:5]]))
        for i in ids:
            rej[int(i)].append(reason)
        return int(vmask.sum())

    m1 = fp_masks(Hc, plane1, field1, ctx["env"], prm)
    m0 = ctx["m0"]
    met = dict(footprint_cells=m1["n_fp_cells"], pond_cells_corner_below_sea=m1["n_pond_sea_cells"])
    for name, why in (("exposed", "new exposed footprint border vertex"), ("env_leak", "pond below its plane on a non-envelope cell"),
                      ("bed_low", "new pond bed under 1.0 m"), ("pond_sea", "new pond cell with a corner under the engine sea"),
                      ("field_dev", "new field corner off its plane by > 0.35 m")):
        met["new_" + name] = attribute(m1[name] & ~m0[name], why)
    topo, bad = sea_topology(ctx["H0"], Hc)
    met["sea_topology"] = topo
    for why, vm in bad:
        attribute(vm, why)
    # slopes, map-wide on triangles with a changed vertex
    chv = Hc != ctx["H0"]
    a0, b0 = ctx["slopes0"]; a1, b1 = tri_slopes(Hc)
    ca = chv[:-1, :-1] | chv[:-1, 1:] | chv[1:, 1:]; cb = chv[:-1, :-1] | chv[1:, :-1] | chv[1:, 1:]
    sa = slope_bad(a0, a1, prm) & ca; sb = slope_bad(b0, b1, prm) & cb
    met["new_tris_over_limit"] = attribute(c2v(sa | sb), "slope over limit")
    # wiggle and exactness per treated stretch, over every changed triangle
    qa, va, sega = wiggle_samples(Hc, W1, fp1, plane1, prm)
    qb, vb, segb = ctx["wig0"]
    gsb = group_by_owner(seg_owner_cols(owner, segb))
    gb = group_by_owner(tri_owner_cols(owner, qb[:, 0], qb[:, 1]))
    ga = group_by_owner(tri_owner_cols(owner, qa[:, 0], qa[:, 1]))
    gs = group_by_owner(seg_owner_cols(owner, sega))
    per = {}
    for sid, tg in targets.items():
        ib, ia = gb.get(sid, np.zeros(0, int)), ga.get(sid, np.zeros(0, int))
        wb_, wa_ = vb[ib], va[ia]
        mb_, ma_ = wb_[np.isfinite(wb_)], wa_[np.isfinite(wa_)]
        # no sample is not a zero: an unmeasurable waterline rejects the stretch
        p90b = float(np.percentile(mb_, 90)) if len(mb_) else float("nan")
        p90a = float(np.percentile(ma_, 90)) if len(ma_) else float("nan")
        lim_w = max(prm["WIG_ABS"], prm["WIG_REL"] * p90b) if len(mb_) else float("nan")
        cvb = chain_coverage(segb, gsb.get(sid, np.zeros(0, int)))
        cva = chain_coverage(sega, gs.get(sid, np.zeros(0, int)))
        if not len(mb_) or not len(ma_):
            rej[sid].append(f"wiggle: no finite sample (before {len(mb_)}, after {len(ma_)})")
        if cvb["unmeasured_segments"] or cva["unmeasured_segments"]:
            rej[sid].append(f"wiggle: waterline on a chain too short to measure (segments before {cvb['unmeasured_segments']}, "
                            f"after {cva['unmeasured_segments']})")
        if cvb["chains"] != cva["chains"]:
            rej[sid].append(f"waterline chains through the stretch {cvb['chains']} -> {cva['chains']}")
        if cvb["closed_inside"] != cva["closed_inside"]:
            rej[sid].append(f"closed waterline chains inside the stretch {cvb['closed_inside']} -> {cva['closed_inside']}")
        dense = []
        for po in tg:
            C = np.asarray(po["C"]); C2 = np.vstack([C, C[:1]]) if po["closed"] else C
            s = arclen(C2); tq = np.arange(0, s[-1], 0.1)
            dense.append(np.column_stack([np.interp(tq, s, C2[:, 0]), np.interp(tq, s, C2[:, 1])]))
        si = gs.get(sid, np.zeros(0, int))
        ex = cKDTree(np.vstack(dense)).query(sega["p"][si].reshape(-1, 2))[0] if len(si) else np.zeros(0)
        per[sid] = dict(wiggle_p90_before=None if not len(mb_) else round(p90b, 4),
                        wiggle_p90_after=None if not len(ma_) else round(p90a, 4),
                        wiggle_limit=None if not len(mb_) else round(lim_w, 4),
                        samples_before=int(len(mb_)), samples_after=int(len(ma_)), coverage_before=cvb, coverage_after=cva,
                        unmeasured_samples=dict(before=int(len(wb_) - len(mb_)), after=int(len(wa_) - len(ma_))),
                        exact_to_target_m=dict(n_points=int(len(ex)), p50=pct(ex, 50), p90=pct(ex, 90), p99=pct(ex, 99),
                                               max=round(float(ex.max()), 4) if len(ex) else None))
        if len(mb_) and len(ma_) and not p90a <= lim_w + 1e-12:
            rej[sid].append(f"wiggle p90 {p90a:.3f} > {lim_w:.3f}")
    met["unattributed"] = unattributed
    return dict(rejections={k: sorted(set(v)) for k, v in rej.items()}, metrics=met, per_stretch=per,
                footprint_report=os.path.join(fpdir, "footprint-report.json"))


def write_terrain(path, arrays, Hc, H0):
    out = {}
    for k, v in arrays.items():
        out[k] = v
    h32 = Hc.astype(arrays["heights"].dtype)
    out["heights"] = h32
    out[OUT_MASK] = h32 != arrays["heights"]
    np.savez(path, **out)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    for a in ("terrain", "footprint", "envelope", "cover", "out_terrain", "report"):
        ap.add_argument(a)
    ap.add_argument("--worklist"); ap.add_argument("--threshold", type=float, default=0.15)
    ap.add_argument("--sigma", type=float, default=12.0); ap.add_argument("--crossings")
    ap.add_argument("--built", action="append", default=[], help="built-sites file of a later chain (repeatable)")
    ap.add_argument("--work"); ap.add_argument("--footprint-tool", default=os.path.join(HERE, "pond_footprint_v31.py"))
    ap.add_argument("--focus", action="append", default=None, help="NAME:x0,x1,z0,z1 (listed in the report)")
    ap.add_argument("--param", action="append", default=[], help="KEY=VALUE override of PARAMS (reported)")
    a = ap.parse_args()
    prm = dict(PARAMS)
    for kv in a.param:
        k, v = kv.split("=")
        assert k in prm, f"unknown parameter {k}"
        prm[k] = type(prm[k])(float(v)) if not isinstance(prm[k], int) else int(float(v))
    t0 = time.time()
    for p in (a.out_terrain, a.report):
        assert not os.path.exists(p), f"fresh output required: {p}"
    work = a.work or os.path.splitext(a.out_terrain)[0] + "-work"
    os.makedirs(work, exist_ok=False)
    assert os.path.exists(a.footprint_tool), a.footprint_tool
    z = np.load(a.terrain)
    arrays = {k: z[k] for k in z.files}
    for k in REQUIRED:
        assert k in arrays, f"input terrain lacks '{k}'"
    assert OUT_MASK not in arrays, f"input already carries {OUT_MASK}: the pass runs once per chain"
    H0 = arrays["heights"].astype(np.float64)
    f0 = np.load(a.footprint)
    plane0, field0 = f0["plane"].astype(np.float64), f0["field"].astype(np.float64)
    env_plane = np.load(a.envelope).astype(np.float64)
    env = np.isfinite(env_plane)
    # the footprint must belong to this terrain, cover and envelope
    ref_dir = os.path.join(work, "fp-input-check")
    subprocess.run([sys.executable, "-I", a.footprint_tool, a.terrain, a.cover, ref_dir, a.envelope], check=True,
                   stdout=subprocess.DEVNULL)
    fr = np.load(os.path.join(ref_dir, "footprint.npz"))
    same = all(np.array_equal(fr[k], f0[k], equal_nan=True) for k in ("plane", "field", "env_plane", "visible"))
    assert same, "the given footprint is not the footprint of the given terrain/cover/envelope"
    W0, fp0 = corner_water(plane0, field0)
    assert not (a.crossings and a.built), "--crossings replaces the inventory; do not combine it with --built"
    crossings, cr_src = pending_crossings(a.crossings, a.built)
    base, pinfo = base_protection(arrays, crossings, prm)
    bprot = BodyProt(base, env_plane, plane0, field0)
    if a.worklist:
        stretches = json.load(open(a.worklist, encoding="utf-8"))
        csum = dict(source=a.worklist, sha256=sha(a.worklist), stretches=len(stretches))
    else:
        stretches, csum = census(H0, W0, fp0, plane0, arrays, prm, a.threshold)
    json.dump(stretches, open(os.path.join(work, "worklist.json"), "w", encoding="utf-8"))
    print(f"[shore] census {json.dumps(csum)} {time.time() - t0:.1f}s", flush=True)
    ctx = dict(work=work, arrays=arrays, H0=H0, cover=a.cover, env_path=a.envelope, env=env, fp_tool=a.footprint_tool,
               m0=fp_masks(H0, plane0, field0, env, prm), slopes0=tri_slopes(H0))
    ctx["wig0"] = wiggle_samples(H0, W0, fp0, plane0, prm)
    rejected, attempt, history = {}, {}, defaultdict(list)
    rounds = []
    ok = False

    def fail(sid, reasons, rnd):
        history[sid].append(dict(round=rnd, variant=attempt.get(sid, 0), reasons=reasons))
        if attempt.get(sid, 0) + 1 < len(RETRY):
            attempt[sid] = attempt.get(sid, 0) + 1
        else:
            rejected[sid] = dict(round=rnd, reasons=reasons, attempts=history[sid])
    for rnd in range(prm["MAX_ROUNDS"]):
        Hc, owner, res, targets = run_pass(H0, W0, fp0, plane0, bprot, stretches, rejected, a.sigma, prm, attempt)
        nloc = 0
        for sid, r in res.items():
            if r.get("reject_local") and sid not in rejected:
                fail(sid, r["reject_local"], rnd); nloc += 1
        val = validate(ctx, Hc, owner, targets, rnd, prm)
        new = {k: v for k, v in val["rejections"].items() if k not in rejected and res[k]["status"] == "treated"}
        rounds.append(dict(round=rnd, treated=sum(1 for r in res.values() if r["status"] == "treated"),
                           failed_local=nloc, failed_validation=len(new), metrics=val["metrics"]))
        print(f"[shore] round {rnd}: treated {rounds[-1]['treated']}, local fails {nloc}, validation fails {len(new)}, "
              f"unattributed {len(val['metrics']['unattributed'])} {time.time() - t0:.1f}s", flush=True)
        assert not val["metrics"]["unattributed"], f"failure not attributable to a stretch: {val['metrics']['unattributed']}"
        if not new and not nloc:
            ok = True
            break
        for k, v in new.items():
            fail(k, v, rnd)
    assert ok, f"no clean round after {prm['MAX_ROUNDS']} rounds"
    write_terrain(a.out_terrain, arrays, Hc, H0)
    np.save(os.path.join(work, "owner.npy"), owner)
    json.dump({str(k): v for k, v in targets.items()}, open(os.path.join(work, "targets.json"), "w", encoding="utf-8"))
    # report
    out32 = Hc.astype(np.float32); in32 = arrays["heights"]
    ch = out32 != in32
    resv_only = arrays["reserve"] & ~arrays["platform"] & ~arrays["narva"]
    focus = []
    for f in (a.focus or ["islet:6650,7750,10050,10800"]):
        nm, bx = f.split(":"); focus.append((nm, [float(v) for v in bx.split(",")]))
    srep = []
    for st in stretches:
        sid = st["id"]
        r = res[sid]
        poly = np.asarray(st["poly"])
        e = dict({k: st[k] for k in ("id", "body", "level", "x", "z", "cause", "windows", "wig_p90_max", "extent_m", "covered_m",
                                      "a0", "a1") if k in st}, status=r["status"])
        e["focus"] = [nm for nm, (x0, x1, z0, z1) in focus
                      if ((poly[:, 0] >= x0) & (poly[:, 0] <= x1) & (poly[:, 1] >= z0) & (poly[:, 1] <= z1)).any()]
        if sid in rejected:
            e["rejected"] = rejected[sid]
        elif history.get(sid):
            e["earlier_attempts"] = history[sid]
        e["variant"] = dict(index=r.get("variant", attempt.get(sid, 0)), overrides=RETRY[r.get("variant", attempt.get(sid, 0))])
        if "info" in r:
            e["pass"] = r["info"]
        if r["status"] == "treated":
            m = owner == sid
            dH = (Hc - H0)[m]
            e.update(vertices_changed=int(m.sum()), reserve_only_changed=int((m & resv_only).sum()),
                     dH_max_abs=round(float(np.abs(dH).max()), 3), slope_max_changed_tris_deg=r["slope_max_changed_tris_deg"],
                     **val["per_stretch"][sid])
        srep.append(e)
    treated = [e for e in srep if e["status"] == "treated"]
    allex = [e["exact_to_target_m"] for e in treated]
    rep = dict(schema="shore-ramp-v31.v1", tool=os.path.abspath(__file__), tool_sha256=sha(os.path.abspath(__file__)),
               inputs=dict(terrain=a.terrain, terrain_sha256=sha(a.terrain), footprint=a.footprint, footprint_sha256=sha(a.footprint),
                           envelope=a.envelope, envelope_sha256=sha(a.envelope), cover=a.cover, cover_sha256=sha(a.cover),
                           footprint_tool=a.footprint_tool, footprint_tool_sha256=sha(a.footprint_tool),
                           worklist=a.worklist),
               output=dict(terrain=a.out_terrain, terrain_sha256=sha(a.out_terrain), work=work, mask=OUT_MASK),
               params=dict(prm, retry_variants=RETRY, sigma_used=a.sigma, threshold=a.threshold, strict=True, reserve_only_movable=True),
               protection=dict(pinfo, crossings=crossings, crossings_source=cr_src), census=csum, rounds=rounds,
               summary=dict(stretches=len(stretches), treated=len(treated),
                            rejected=sum(1 for e in srep if e["status"] == "rejected"),
                            skipped=sum(1 for e in srep if e["status"] == "skipped"),
                            treated_extent_km=round(sum(e["extent_m"] for e in treated) / 1000, 3),
                            vertices_changed=int(ch.sum()), reserve_only_changed=int((ch & resv_only).sum()),
                            platform_changed=int((ch & arrays["platform"]).sum()), narva_changed=int((ch & arrays["narva"]).sum()),
                            protected_changed=int((ch & base).sum()),
                            exact_to_target_worst_p99_m=max([x["p99"] for x in allex if x["p99"] is not None], default=None),
                            exact_to_target_worst_max_m=max([x["max"] for x in allex if x["max"] is not None], default=None),
                            focus={nm: [e["id"] for e in srep if nm in e["focus"]] for nm, _ in focus},
                            seconds=round(time.time() - t0, 1)),
               stretches=srep)
    assert rep["summary"]["platform_changed"] == 0 and rep["summary"]["narva_changed"] == 0 and rep["summary"]["protected_changed"] == 0
    with open(a.report, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps(rep["summary"], indent=1))


if __name__ == "__main__":
    main()

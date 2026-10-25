"""Causeway pass v31: road embankments over the engine sea with a constant width, straight shorelines on both sides and
rounded junctions, exact on the native 6 m TRI grid. Runs after shore_ramp_v31 and before bury_edges_v31 (it replaces
the shore pass on the causeways of the acceptance inventory); the footprint follows it.

Grid: 2048 x 2048 vertices of 6 m, row 0 north, x = 6 c, z = 12282 - 6 r, native triangles split NW-SE. Water per cell
corner as in shore_ramp_v31 (footprint field on footprint cells, the engine sea SEA = 0.75 elsewhere). D = H - W is
linear per triangle, so the waterline is one straight segment per mixed triangle.

Defect (EV110, Guillermo 17-10 on the islet causeways at (6900, 10500): "suavizar esos caminos ... por ambos lados"): the
shore pass left 7-11 cm teeth where the causeway shoreline meets the frozen road platform. Review 1 of this pass (17-10):
the first version straightened only a producer-chosen core, left the junctions with the islet and the mainland worse
than before (wiggle p90 0.08-0.21 m) and stretch 313 (7565, 10730) untreated, and its gate trusted the report's list.

Inventory: --spec (evidence/v31-pond-layer-2026-10-13/ev112/causeway/acceptance-ev112.json, frozen by hash in
gate_causeway.py) lists the 8 census clusters; the 'causeway' ones carry a road chain (verify_roads_v30.road_chains, the
chains build_surface_v30.py:58 paints) and a station interval [s0, s1]. This pass treats exactly those, in spec order.
It re-runs its own census (a dry road station with water within REACH m on both sides, 1 m stations, gaps <= GAP m,
runs >= L_MIN m) and stops if the census and the spec disagree (another causeway, or an interval off by > 1 m): the
inventory is never re-derived silently. Every cluster is classified against the census and reported.
Rule per causeway
  axis     the chain over [s0, s1] plus up to EXT m per end (stopping where the radius drops under R_MIN), smoothed with an
           arc-length spline (AX_SIGMA m). Station s and signed offset u (left > 0) of any point; a = |u|.
  T        one toe offset for both sides: the smallest multiple of 0.25 m with T_MARGIN m of clearance beyond every
           triangle of [s0, s1] that holds a protected vertex (platform, narva, kit, bridge and lagoon masks, pending
           crossings, sea-envelope and footprint cells: shore_ramp_v31.base_protection and BodyProt), leaving out the
           stations within 10 m of natural land beyond the toe (the junctions).
  band     E = {a <= u*(s)}: u* = T on [s0 - RUN_PAD, s1 + RUN_PAD], tapering beyond with a parabola of radius R_TAPER
           (u* = T - d^2 / (2 R_TAPER), d = stations past that interval), so where the natural coast is narrower than T
           the band ends inside it instead of with a step.
  land     L = E U N U P_in U F, rasterised at PX m: N natural land (the interpolated land of the triangles that hold a
           dry vertex outside the band that is not reserve-only fringe within FRINGE_W m of the toe; the fringe counts as
           water), P_in the triangles of dry protected vertices within 2 R_FILL + 10 m of E (they stay on land, so no cut
           triangle holds a protected vertex), F the components of closing(E U N U P, radius R_FILL) minus (E U N U P)
           that touch E or P_in: the junction fillets. Concavities of the natural coast alone are not filled. Triangles of
           wet protected vertices stay water (counted; > 0 rejects).
  target   phi = signed distance to the boundary of L (positive on land): the analytic band offset u*(s) - a where L
           equals E for BLEND0..BLEND1 m around, the Gaussian-smoothed (SDF_SIGMA) raster distance elsewhere. Away from
           the changed land (L differs from the old land) phi blends into the signed distance to the exact old waterline
           over TREAT_D..TREAT_D + BLEND_T m, so the treated shoreline joins the untouched coast on itself.
  heights  every free vertex of the target-cut triangles of the waterline components that pass within CHG_HIT m of the
           changed land is solved in least squares: one equation per crossed native edge putting the crossing exactly on
           the target (bisection of phi along the edge), the crossed edges of the adjacent untouched triangles kept at
           their old crossing (weight W_SEAM), and a weak pull (W_REG) to SEA + s phi (to the old height where the blend
           is old). The sign of phi is enforced (CLR_L). s = min(S_DESIGN, (road crest - SEA - CREST_CLR) / deepest
           landward ramp vertex). Other free vertices of the zone: old water or band vertices on land get
           max(old, min(crest, SEA + s phi)) (shoulder at road height, fill only); dry vertices on the water side
           (reserve-only fringe, teeth; never outer natural land) are cut to min(SEA - CLR_W, SEA + s phi); the bed in
           front of the toe is filled to the ramp and then S2 (at most SEA - CLR_W). All of it blended by the target
           weight. Earlier causeways' vertices are frozen for later ones.
Never changed: platform, narva and every protected vertex (asserted). Reserve-only vertices may move (approved 15-10).
Checks that reject the whole pass (no output is written): a protected vertex changed; a target-cut triangle with a frozen
vertex; land over a wet protected triangle; a natural dry vertex lowered into the sea; a changed triangle crossing
SLOPE_MAX; any engine-sea component created, removed, split or merged; a footprint change after regenerating it; a new
exposed border vertex, pond cell over the engine sea, bed under 1 m or field corner off its plane; and per causeway side,
on the exact waterline of the regenerated footprint (nearest shoreline per 1 m station of [s0, s1]): wiggle p90 >
WIG_MAX; station coverage < COVER_MIN inside [s0 + R_FILL, s1 - R_FILL] or a gap that does not touch an end of
[s0, s1] or is longer than R_FILL m (the fillets may take the water away from the last stations); width outside the
median +- WIDTH_TOL on a contiguous core shorter than CORE_MIN of the run, narrower than the core anywhere, or an offset
that falls by more than MONO_TOL m going out from the core; and in each link window (the run ends +- LINK_W m, waterline
samples in triangles with a changed vertex) wiggle p90 > LINK_WIG_MAX. gate_causeway.py re-measures everything on its own.
Output: every input array byte-identical except heights, plus v31_causeway (bool, vertex changed by this pass).
Usage: causeway_v31.py <terrain.npz> <footprint.npz> <envelope.npy> <cover.npy> <out_terrain.npz> <report.json>
       --spec ACCEPTANCE.json [--work DIR] [--built SITES.json ...] [--crossings C.json] [--param KEY=VALUE ...]
--built/--crossings: as shore_ramp_v31 (pending 015 crossings are protected). Writes <out_terrain>, <report.json> and, in
the work dir (fresh; default <out_terrain>-work): fp-input-check/, fp/ (regenerated footprint), candidate terrain on a
rejection, axes.json (axis every 1 m, u* profile, T per causeway; informative: the gate builds its own axis).
"""
import argparse, hashlib, json, os, subprocess, sys, time
import numpy as np
from scipy.ndimage import distance_transform_edt as edt, gaussian_filter, gaussian_filter1d, map_coordinates, label, \
    binary_dilation
from scipy.sparse import coo_matrix, vstack as svstack
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import lsqr
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "terrain"))
import shore_ramp_v31 as sr                                   # noqa: E402
from verify_roads_v30 import road_chains                      # noqa: E402

N, NC, ZTOP, SEA = sr.N, sr.NC, sr.ZTOP, sr.SEA
PARAMS = dict(REACH=30.0, GAP=5.0, L_MIN=60.0, EXT=60.0, R_MIN=80.0, AX_SIGMA=10.0, T_MARGIN=0.5, T_MAX=40.0,
              RUN_PAD=8.0, R_TAPER=120.0, R_FILL=40.0, PX=0.5, SDF_SIGMA=2.0, BLEND0=3.0, BLEND1=13.0, FRINGE_W=15.0,
              PD_MARGIN=0.5, PW_MARGIN=0.5, TREAT_D=15.0, BLEND_T=10.0, CHG_HIT=3.0, W_SEAM=20.0, W_REG=0.05,
              S_DESIGN=0.12, S_MIN=0.04, CREST_CLR=0.05, S2=0.35, CLR_W=0.10, CLR_L=0.02, SEA_REACH=25.0,
              PLAT_HALF=15.0, SLOPE_MAX=35.0, WIG_MAX=0.03, COVER_MIN=0.98, WIDTH_TOL=0.5, CORE_MIN=0.75,
              MONO_TOL=0.25, LINK_W=60.0, LINK_WIG_MAX=0.06, CLUSTER_R=200.0, SPEC_TOL=1.0)
OUT_MASK = "v31_causeway"
REQUIRED = ("heights", "reserve", "platform", "narva", "v31_kit", "v31_bridge_cut", "v31_lagoon")
FP_NONE = np.zeros((NC, NC), bool)
PL_NONE = np.full((NC, NC), np.nan, np.float32)
W_SEA = np.full((NC, NC, 4), SEA, np.float32)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def triflags(v):
    """Per cell: triangle A (NW NE SE) / B (NW SW SE) holds a marked vertex."""
    nw, ne, sw, se = v[:-1, :-1], v[:-1, 1:], v[1:, :-1], v[1:, 1:]
    return nw | ne | se, nw | sw | se


def level_at(H, plane, x, z):
    """Terrain and water level at points (exact native triangles; pond plane on footprint cells, SEA elsewhere)."""
    h = sr.tri_h(H, x, z)
    c = np.clip(np.floor(np.asarray(x) / 6.0).astype(int), 0, NC - 1)
    r = np.clip(np.floor((ZTOP - np.asarray(z)) / 6.0).astype(int), 0, NC - 1)
    p = plane[r, c]
    pond = np.isfinite(p)
    return h, np.where(pond, p, SEA), pond


def chain_stations(p, step=1.0):
    st = np.r_[0.0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
    s = np.arange(0.0, st[-1], step)
    q = np.column_stack([np.interp(s, st, p[:, 0]), np.interp(s, st, p[:, 1])])
    return s, q, st[-1]


# ---------------------------------------------------------------- census
def side_profile(H, plane, q, prm):
    """Per station and side (+1 left, -1 right): first wet offset (inf if none within REACH) and whether that water
    is a pond."""
    tg = np.gradient(q, axis=0)
    tg /= np.maximum(np.hypot(*tg.T), 1e-9)[:, None]
    nr = np.column_stack([-tg[:, 1], tg[:, 0]])
    offs = np.arange(0.5, prm["REACH"] + 1e-9, 0.5)
    out = {}
    for sgn in (1, -1):
        P = q[:, None, :] + sgn * offs[None, :, None] * nr[:, None, :]
        h, lev, pond = level_at(H, plane, P[..., 0].ravel(), P[..., 1].ravel())
        w = (h < lev).reshape(P.shape[:2]); pond = pond.reshape(P.shape[:2])
        k = np.argmax(w, 1); has = w.any(1)
        out[sgn] = (np.where(has, offs[k], np.inf), has & pond[np.arange(len(q)), k])
    h, lev, _ = level_at(H, plane, q[:, 0], q[:, 1])
    return out, h >= lev


def runs_of(mask, gap):
    """Index runs of True, with gaps of at most gap samples closed."""
    idx = np.nonzero(mask)[0]
    if not len(idx):
        return []
    out, a, b = [], idx[0], idx[0]
    for i in idx[1:]:
        if i - b - 1 <= gap:
            b = i
        else:
            out.append((a, b)); a = b = i
    out.append((a, b))
    return out


def census(H, plane, prm, l_min=None):
    l_min = prm["L_MIN"] if l_min is None else l_min
    found = []
    for n, p in enumerate(road_chains()):
        if len(p) < 2:
            continue
        s, q, L = chain_stations(p)
        if len(q) < 5:
            continue
        side, dry = side_profile(H, plane, q, prm)
        both = (side[1][0] <= prm["REACH"]) & (side[-1][0] <= prm["REACH"]) & dry
        for a, b in runs_of(both, int(prm["GAP"])):
            if s[b] - s[a] < l_min:
                continue
            m = slice(a, b + 1)
            pond_frac = {sg: float(np.mean(side[sg][1][m][np.isfinite(side[sg][0][m])])) for sg in (1, -1)}
            found.append(dict(chain=n, s0=float(s[a]), s1=float(s[b]), length_m=round(float(s[b] - s[a]), 1),
                              x=round(float(q[m, 0].mean()), 1), z=round(float(q[m, 1].mean()), 1),
                              left_pond_frac=round(pond_frac[1], 3), right_pond_frac=round(pond_frac[-1], 3),
                              poly=np.round(q[m], 2).tolist()))
    return found


def classify_clusters(spec, runs, short, prm):
    """Every spec cluster against the census: the census run it lies on (>= L_MIN) or the longest short run near it."""
    out = []
    for cl in spec["clusters"]:
        x, z = float(cl["x"]), float(cl["z"])

        def dist(r):
            return float(np.min(np.hypot(np.asarray(r["poly"])[:, 0] - x, np.asarray(r["poly"])[:, 1] - z)))

        near = [r for r in runs if dist(r) <= prm["CLUSTER_R"]]
        e = dict(id=cl["id"], x=x, z=z, spec_class=cl["class"])
        if near:
            r = min(near, key=dist)
            e.update(verdict="causeway", chain=r["chain"], s0=r["s0"], s1=r["s1"], distance_m=round(dist(r), 1),
                     left_pond_frac=r["left_pond_frac"], right_pond_frac=r["right_pond_frac"])
        else:
            ns = [r for r in short if dist(r) <= prm["CLUSTER_R"]]
            lr = max(ns, key=lambda r: r["length_m"]) if ns else None
            e.update(verdict="not a causeway", longest_both_sides_run_m=None if lr is None else lr["length_m"],
                     longest_run=None if lr is None else {k: lr[k] for k in ("chain", "s0", "s1", "left_pond_frac",
                                                                             "right_pond_frac")})
        out.append(e)
    return out


# ---------------------------------------------------------------- axis
class Axis:
    def __init__(self, chain_xy, s0, s1, prm):
        s, q, L = chain_stations(chain_xy)
        # extension per end, stopped where the raw chain turns tighter than R_MIN (junction curves)
        g = np.gradient(q, axis=0); g2 = np.gradient(g, axis=0)
        kap = np.abs(g[:, 0] * g2[:, 1] - g[:, 1] * g2[:, 0]) / np.maximum(np.hypot(*g.T), 1e-9) ** 3
        kap = np.convolve(kap, np.ones(5) / 5, mode="same")
        i0, i1 = int(np.searchsorted(s, s0)), int(np.searchsorted(s, s1))
        lo = i0
        while lo > 0 and s[i0] - s[lo - 1] <= prm["EXT"] and kap[lo - 1] < 1.0 / prm["R_MIN"]:
            lo -= 1
        hi = i1
        while hi < len(s) - 1 and s[hi + 1] - s[i1] <= prm["EXT"] and kap[hi + 1] < 1.0 / prm["R_MIN"]:
            hi += 1
        qq = q[lo:hi + 1]
        qs = sr.smooth_pinned(qq, np.zeros(len(qq), bool), False, prm["AX_SIGMA"])     # 1 m samples: sigma in m
        t = np.arange(0, len(qs) - 1 + 1e-9, 0.05)
        self.p = np.column_stack([np.interp(t, np.arange(len(qs)), qs[:, 0]), np.interp(t, np.arange(len(qs)), qs[:, 1])])
        self.s = s[lo] + t                                   # station = chain station (arc of the raw chain)
        gg = np.gradient(self.p, axis=0)
        self.g = gg / np.maximum(np.hypot(*gg.T), 1e-9)[:, None]
        self.tree = cKDTree(self.p)
        self.raw_dev_max = float(np.max(np.hypot(*(qs - qq).T)))
        self.s_lo, self.s_hi, self.s0, self.s1 = float(s[lo]), float(s[hi]), float(s0), float(s1)

    def locate(self, x, z):
        """Station, signed offset (left > 0) and validity (nearest point not an axis end) of points."""
        xz = np.column_stack([np.ravel(x), np.ravel(z)])
        d, j = self.tree.query(xz)
        v = xz - self.p[j]
        cr = self.g[j, 0] * v[:, 1] - self.g[j, 1] * v[:, 0]
        u = np.where(cr >= 0, d, -d)
        ok = (j > 0) & (j < len(self.p) - 1)
        return self.s[j], u, ok


# ---------------------------------------------------------------- one causeway
def treat(H_cur, owner, prot, arrays, chain_xy, s0, s1, prm):
    """Heights of one causeway on the current terrain H_cur. owner: vertices of earlier causeways (frozen, not
    protected land). Returns (rows, cols, new heights, info, axis, u* grid)."""
    t0 = time.time()
    resonly = arrays["reserve"] & ~arrays["platform"] & ~arrays["narva"]
    ax = Axis(chain_xy, s0, s1, prm)
    pad = prm["T_MAX"] + 2 * prm["R_FILL"] + 40
    r0 = max(int((ZTOP - (ax.p[:, 1].max() + pad)) / 6), 0)
    r1 = min(int((ZTOP - (ax.p[:, 1].min() - pad)) / 6) + 1, NC)
    c0 = max(int((ax.p[:, 0].min() - pad) / 6), 0)
    c1 = min(int((ax.p[:, 0].max() + pad) / 6) + 1, NC)
    x0, x1, z1, z0 = 6.0 * c0, 6.0 * c1, ZTOP - 6.0 * r0, ZTOP - 6.0 * r1
    RR, CC = np.mgrid[r0:r1 + 1, c0:c1 + 1]
    vx, vz = sr.vxz(RR, CC)
    vst, vu, vok = ax.locate(vx, vz)
    vst, vu, vok = vst.reshape(RR.shape), vu.reshape(RR.shape), vok.reshape(RR.shape)
    va, vside = np.abs(vu), np.sign(vu).astype(int)
    Hw = H_cur[r0:r1 + 1, c0:c1 + 1].astype(np.float64)
    pw = prot[r0:r1 + 1, c0:c1 + 1]
    fz = pw | owner[r0:r1 + 1, c0:c1 + 1]
    plat = arrays["platform"][r0:r1 + 1, c0:c1 + 1]
    ro = resonly[r0:r1 + 1, c0:c1 + 1]
    dry = Hw >= SEA
    nr, nc = RR.shape
    gi = np.arange(nr * nc).reshape(nr, nc)
    tri = np.concatenate([np.stack([gi[:-1, :-1].ravel(), gi[:-1, 1:].ravel(), gi[1:, 1:].ravel()], 1),
                          np.stack([gi[:-1, :-1].ravel(), gi[1:, :-1].ravel(), gi[1:, 1:].ravel()], 1)])
    af, sf, okf, pwf, fzf, Hf = va.ravel(), vside.ravel(), vok.ravel(), pw.ravel(), fz.ravel(), Hw.ravel()
    # ---- T
    natv = dry & ~ro & ~pw & vok
    t_ok = okf[tri].all(1) & (sf[tri] == sf[tri][:, :1]).all(1) & (sf[tri][:, 0] != 0)
    tst = vst.ravel()[tri].mean(1)
    tmin, tmax = af[tri].min(1), af[tri].max(1)
    T, T_need = None, None
    for _ in range(8):
        Tg = 20.0 if T is None else T
        blk = np.zeros(int(ax.s_hi) + 2, bool)
        for v in np.round(vst[natv & (va > Tg) & (va <= Tg + 12)]).astype(int):
            blk[max(v - 10, 0):max(v + 11, 0)] = True
        tb = blk[np.clip(np.round(tst).astype(int), 0, len(blk) - 1)]
        tp = t_ok & pwf[tri].any(1) & (tst >= s0) & (tst <= s1) & ~tb & (tmin < prm["T_MAX"])
        assert tp.any(), "no protected triangle along the causeway"
        T_need = float(tmax[tp].max())
        Tn = float(np.ceil((T_need + prm["T_MARGIN"]) / 0.25) * 0.25)
        if Tn == T:
            break
        T = Tn
    # ---- u*(s)
    sg_grid = np.arange(np.floor(ax.s_lo), np.ceil(ax.s_hi) + 1.0, 0.5)
    beyond = np.maximum(np.maximum((s0 - prm["RUN_PAD"]) - sg_grid, sg_grid - (s1 + prm["RUN_PAD"])), 0.0)
    ustar = T - beyond ** 2 / (2 * prm["R_TAPER"])

    def u_of(st):
        return np.interp(st, sg_grid, ustar)

    # ---- target land on a PX raster
    PX = prm["PX"]
    xs = x0 + (np.arange(int(round((x1 - x0) / PX))) + 0.5) * PX
    zs = z1 - (np.arange(int(round((z1 - z0) / PX))) + 0.5) * PX
    X, Z = np.meshgrid(xs, zs)
    st, u, ok = ax.locate(X, Z)
    st, u, ok = st.reshape(X.shape), u.reshape(X.shape), ok.reshape(X.shape)
    E = ok & (np.abs(u) <= u_of(st))
    ustv = u_of(vst)
    fringe = vok & ro & dry & (va <= ustv + prm["FRINGE_W"])
    outer = dry & ~fringe & ~(vok & (va <= ustv))
    Hn = H_cur.astype(np.float64).copy()
    sub = Hn[r0:r1 + 1, c0:c1 + 1]
    sub[fringe] = SEA - 1.0
    cc = np.clip(np.floor(X / 6).astype(int), c0, c1 - 1); rr = np.clip(np.floor((ZTOP - Z) / 6).astype(int), r0, r1 - 1)
    isA = (X / 6 - cc) >= ((ZTOP - Z) / 6 - rr)
    lr_, lc_ = rr - r0, cc - c0
    OA, OB = triflags(outer)
    Nm = (sr.tri_h(Hn, X, Z) >= SEA) & np.where(isA, OA[lr_, lc_], OB[lr_, lc_])
    Nold = sr.tri_h(H_cur, X, Z) >= SEA
    TAd, TBd = triflags(pw & dry); TAw, TBw = triflags(pw & ~dry)
    Pd = edt(~np.where(isA, TAd[lr_, lc_], TBd[lr_, lc_])) * PX <= prm["PD_MARGIN"]
    Pw = edt(~np.where(isA, TAw[lr_, lc_], TBw[lr_, lc_])) * PX <= prm["PW_MARGIN"]
    R = prm["R_FILL"]
    Zn = edt(~E) * PX <= 2 * R + 10
    Pd_in = Pd & Zn
    L0 = E | Nm | Pd
    clo = edt(edt(~L0) * PX <= R) * PX > R
    F = clo & ~L0 & Zn
    lab, nlab = label(F, np.ones((3, 3), bool))
    keep = np.zeros(nlab + 1, bool)
    keep[np.unique(lab[binary_dilation(E | Pd_in, np.ones((3, 3), bool)) & F])] = True
    keep[0] = False
    L = E | Nm | Pd_in | keep[lab]
    conflict = int((L & Pw).sum())
    L &= ~Pw
    # ---- phi
    sdf = gaussian_filter((edt(L) - edt(~L)) * PX, prm["SDF_SIGMA"] / PX)
    dD = edt(~((L != E) | ~ok)) * PX
    wA = smoothstep((dD - prm["BLEND0"]) / (prm["BLEND1"] - prm["BLEND0"]))
    oseg = sr.extract_segments(H_cur, W_SEA, FP_NONE, PL_NONE, r0, r1, c0, c1)
    op = oseg["p"]
    nseg = np.maximum(np.ceil(np.hypot(*(op[:, 1] - op[:, 0]).T) / 0.05).astype(int), 1)
    tt = np.concatenate([np.arange(k + 1) / k for k in nseg])
    si = np.repeat(np.arange(len(op)), nseg + 1)
    otree = cKDTree(op[si, 0] + tt[:, None] * (op[si, 1] - op[si, 0]))
    chg = L != Nold
    dchg = edt(~chg) * PX
    wT = 1.0 - smoothstep((dchg - prm["TREAT_D"]) / prm["BLEND_T"])

    def phi_at(px, pz, parts=False):
        px, pz = np.asarray(px, float).ravel(), np.asarray(pz, float).ravel()
        ci = (px - x0) / PX - 0.5; ri = (z1 - pz) / PX - 0.5
        pr = map_coordinates(sdf, [ri, ci], order=1, mode="nearest")
        w = map_coordinates(wA, [ri, ci], order=1, mode="nearest")
        wt = map_coordinates(wT, [ri, ci], order=1, mode="nearest")
        s_, u_, ok_ = ax.locate(px, pz)
        w = np.where(ok_, w, 0.0)
        pt = w * (u_of(s_) - np.abs(u_)) + (1 - w) * pr
        do = otree.query(np.column_stack([px, pz]))[0]
        po = np.where(sr.tri_h(H_cur, px, pz) >= SEA, do, -do)
        ph = wt * pt + (1 - wt) * po
        return (ph, wt) if parts else ph

    phf, wtf = phi_at(vx, vz, parts=True)
    vd = map_coordinates(dchg, [((z1 - vz) / PX - 0.5).ravel(), ((vx - x0) / PX - 0.5).ravel()], order=1, mode="nearest")
    vZn = map_coordinates(Zn.astype(float), [((z1 - vz) / PX - 0.5).ravel(), ((vx - x0) / PX - 0.5).ravel()], order=0,
                          mode="nearest") > 0.5
    # ---- treated triangles: target-cut, in the zone, on a waterline component that passes the changed land
    cut = (phf[tri] > 0).any(1) & (phf[tri] <= 0).any(1)
    cand = cut & (wtf[tri] > 0).any(1) & vZn[tri].all(1)
    ntc = (nr - 1) * (nc - 1)
    kk = np.arange(ntc).reshape(nr - 1, nc - 1)
    pairs = []
    for ka, kb, ea_, eb_ in ((kk, kk + ntc, gi[:-1, :-1], gi[1:, 1:]),                      # A-B diagonal
                             (kk[1:, :], kk[:-1, :] + ntc, gi[1:-1, :-1], gi[1:-1, 1:]),   # A north = B(r-1) south
                             (kk[:, :-1], kk[:, 1:] + ntc, gi[:-1, 1:-1], gi[1:, 1:-1])):  # A east = B(c+1) west
        ka, kb, ea_, eb_ = ka.ravel(), kb.ravel(), ea_.ravel(), eb_.ravel()
        m = cand[ka] & cand[kb] & ((phf[ea_] > 0) != (phf[eb_] > 0))
        pairs.append(np.stack([ka[m], kb[m]], 1))
    pairs = np.concatenate(pairs)
    _, comp = connected_components(coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])),
                                              shape=(len(tri), len(tri))), directed=False)
    keepc = np.zeros(comp.max() + 1, bool)
    keepc[np.unique(comp[cand & (vd[tri].min(1) <= prm["CHG_HIT"])])] = True
    tcut = cand & keepc[comp]
    skipped = int(len(np.unique(comp[cand & ~keepc[comp]])))
    frozen_in_cut = int((tcut & fzf[tri].any(1)).sum())
    rampv = np.zeros(nr * nc, bool); rampv[np.unique(tri[tcut])] = True
    rampv &= ~fzf
    # ---- crossings
    edges = np.unique(np.sort(np.concatenate([tri[tcut][:, [0, 1]], tri[tcut][:, [1, 2]], tri[tcut][:, [0, 2]]]), 1), axis=0)
    ea, eb = edges[:, 0], edges[:, 1]
    xe = (phf[ea] > 0) != (phf[eb] > 0)
    ea, eb = ea[xe], eb[xe]
    xa, za, xb, zb = vx.ravel()[ea], vz.ravel()[ea], vx.ravel()[eb], vz.ravel()[eb]
    lo, hi = np.zeros(len(ea)), np.ones(len(ea))
    pa0 = phf[ea] > 0
    for _ in range(30):
        m = 0.5 * (lo + hi)
        same = (phi_at(xa + m * (xb - xa), za + m * (zb - za)) > 0) == pa0
        lo = np.where(same, m, lo); hi = np.where(same, hi, m)
    t = 0.5 * (lo + hi)
    hh = Hf - SEA
    oldcut = (hh[tri] >= 0).any(1) & (hh[tri] < 0).any(1)
    seam_t = cut & ~tcut & oldcut & rampv[tri].any(1)
    sedges = np.unique(np.sort(np.concatenate([tri[seam_t][:, [0, 1]], tri[seam_t][:, [1, 2]], tri[seam_t][:, [0, 2]]]),
                               1), axis=0) if seam_t.any() else np.zeros((0, 2), int)
    if len(sedges):
        sedges = sedges[(hh[sedges[:, 0]] >= 0) != (hh[sedges[:, 1]] >= 0)]
        have = set(map(tuple, np.stack([np.minimum(ea, eb), np.maximum(ea, eb)], 1).tolist()))
        sedges = np.array([e for e in sedges.tolist() if tuple(e) not in have], int).reshape(-1, 2)
    # ---- slope s and road crest
    pl_w = plat & vok & (va < prm["PLAT_HALF"])
    bins = np.arange(int(np.floor(ax.s_lo)), int(np.ceil(ax.s_hi)) + 1)
    pb = np.round(vst[pl_w]).astype(int); ph = Hw[pl_w]
    crest = np.full(len(bins), np.nan)
    for i, b in enumerate(bins):
        mm = np.abs(pb - b) <= 6
        if mm.any():
            crest[i] = np.median(ph[mm])
    fin = np.isfinite(crest)
    assert fin.any(), "no platform vertex along the causeway"
    crest = np.interp(np.arange(len(bins)), np.nonzero(fin)[0], crest[fin])
    crest_run = float(np.median(crest[(bins >= s0) & (bins <= s1)]))
    vcap = np.maximum(crest[np.clip(np.round(vst).astype(int) - bins[0], 0, len(bins) - 1)], crest_run).ravel()
    dl = float(phf[rampv & (phf > 0)].max(initial=0.0))
    s = min(prm["S_DESIGN"], (crest_run - SEA - prm["CREST_CLR"]) / max(dl, 1e-6))
    assert s >= prm["S_MIN"], f"ramp slope {s:.3f} under S_MIN"
    # ---- least squares on the ramp vertices
    idx = -np.ones(nr * nc, int); fv = np.nonzero(rampv)[0]; idx[fv] = np.arange(len(fv))
    rows_, cols_, vals_, rhs = [], [], [], []
    k = 0
    for (va_, vb_, tv, w_) in [(ea[i], eb[i], t[i], 1.0) for i in range(len(ea))] + \
            [(a_, b_, hh[a_] / (hh[a_] - hh[b_]), prm["W_SEAM"]) for a_, b_ in sedges]:
        r_ = 0.0
        for v, w in ((va_, 1 - tv), (vb_, tv)):
            if idx[v] >= 0:
                rows_.append(k); cols_.append(idx[v]); vals_.append(w * w_)
            else:
                r_ -= w * w_ * hh[v]
        rhs.append(r_); k += 1
    A1 = coo_matrix((vals_, (rows_, cols_)), shape=(k, len(fv)))
    A2 = coo_matrix((np.full(len(fv), prm["W_REG"]), (np.arange(len(fv)), np.arange(len(fv)))), shape=(len(fv), len(fv)))
    bm = np.r_[np.array(rhs), prm["W_REG"] * (wtf[fv] * s * phf[fv] + (1 - wtf[fv]) * hh[fv])]
    h = lsqr(svstack([A1, A2]).tocsr(), bm, atol=1e-12, btol=1e-12, iter_lim=50000)[0]
    resid = np.abs(A1 @ h - np.array(rhs))
    pos = phf[fv] > 0
    side_clamped = int((pos & (h < prm["CLR_L"])).sum() + (~pos & (h > -prm["CLR_L"])).sum())
    h = np.where(pos, np.maximum(h, prm["CLR_L"]), np.minimum(h, -prm["CLR_L"]))
    h = np.where(pos, np.minimum(h, vcap[fv] - SEA), h)
    new = Hf.copy()
    new[fv] = SEA + h
    # ---- the rest of the zone
    free = ~fzf & ~rampv & okf
    ustf = np.interp(vst.ravel(), sg_grid, ustar)
    zone = vZn & (wtf > 0) & ((af <= ustf + prm["SEA_REACH"]) | (wtf >= 1))
    outerf = outer.ravel()
    land = free & zone & (phf > 0) & ((Hf < SEA + 0.3) | (okf & (af <= ustf)))
    tgt = np.maximum(Hf, np.minimum(vcap, SEA + s * phf))
    new[land] = wtf[land] * tgt[land] + (1 - wtf[land]) * Hf[land]
    cutback = free & zone & (phf <= 0) & (Hf >= SEA - prm["CLR_W"]) & ~outerf
    tgt = np.minimum(Hf, np.minimum(SEA - prm["CLR_W"], SEA + s * phf))
    new[cutback] = wtf[cutback] * tgt[cutback] + (1 - wtf[cutback]) * Hf[cutback]
    ds = float(-phf[rampv & (phf < 0)].min(initial=0.0))
    shelf = free & zone & (phf < 0) & (-phf <= prm["SEA_REACH"]) & (Hf < SEA)
    Es = np.minimum(np.maximum(Hf, SEA - s * ds - prm["S2"] * (-phf - ds)), SEA - prm["CLR_W"])
    new[shelf] = wtf[shelf] * Es[shelf] + (1 - wtf[shelf]) * Hf[shelf]
    nat_low = rampv & outerf & (new < SEA)
    new[nat_low] = SEA + prm["CLR_L"]
    n32 = new.reshape(RR.shape).astype(np.float32).astype(np.float64)
    ch = n32 != Hw.astype(np.float32).astype(np.float64)
    assert not (ch & fz).any(), "protected or earlier-causeway vertex changed"
    rr_, cc_ = np.nonzero(ch)
    info = dict(chain=None, s0=s0, s1=s1, axis_station_range=[round(ax.s_lo, 1), round(ax.s_hi, 1)],
                axis_dev_from_chain_max_m=round(ax.raw_dev_max, 3), T=float(T), width_m=float(2 * T),
                T_need=round(T_need, 3), slope_s=round(float(s), 4), crest_run=round(crest_run, 3),
                ramp_depth_land_m=round(dl, 3), ramp_depth_sea_m=round(ds, 3), ramp_vertices=int(len(fv)),
                crossed_edges=int(len(ea)), seam_edges=int(len(sedges)), lsq_resid_max=round(float(resid.max(initial=0)), 5),
                side_clamped=side_clamped, natural_ramp_kept_dry=int(nat_low.sum()), wet_protected_land_px=conflict,
                frozen_in_cut_triangles=frozen_in_cut, untouched_waterline_components=skipped,
                fill_area_m2=round(float((keep[lab] & ~L0).sum()) * PX * PX, 1),
                vertices_changed=int(ch.sum()),
                old_dry_lowered_to_sea=int((ch & (Hw >= SEA) & (n32 < SEA)).sum()),
                natural_dry_lowered_to_sea=int((ch & (Hw >= SEA) & (n32 < SEA) & ~ro).sum()),
                old_wet_raised_to_land=int((ch & (Hw < SEA) & (n32 >= SEA)).sum()),
                dH_max_abs=round(float(np.abs(n32 - Hw)[ch].max()) if ch.any() else 0.0, 3),
                seconds=round(time.time() - t0, 1))
    return rr_ + r0, cc_ + c0, n32[ch], info, ax, (sg_grid, ustar)


# ---------------------------------------------------------------- self-check measurement
class Loc:
    """Road axis for measurement: the raw chain, densified to 0.25 m and Gaussian-smoothed (10 m)."""

    def __init__(self, raw):
        s = np.r_[0.0, np.cumsum(np.hypot(*np.diff(raw, axis=0).T))]
        t = np.arange(0, s[-1], 0.25)
        q = np.column_stack([np.interp(t, s, raw[:, 0]), np.interp(t, s, raw[:, 1])])
        self.p = np.column_stack([gaussian_filter1d(q[:, 0], 40, mode="nearest"), gaussian_filter1d(q[:, 1], 40, mode="nearest")])
        self.s = t
        g = np.gradient(self.p, axis=0); self.g = g / np.hypot(*g.T)[:, None]
        self.tree = cKDTree(self.p)

    def __call__(self, pts):
        d, j = self.tree.query(pts)
        v = pts - self.p[j]
        cr = self.g[j, 0] * v[:, 1] - self.g[j, 1] * v[:, 0]
        return self.s[j], np.where(cr >= 0, d, -d), (j > 0) & (j < len(self.p) - 1)


def measure(H, W, fp, plane, chv, raw, s0, s1, prm):
    """Nearest shoreline per 1 m station of [s0, s1] per side (wiggle, coverage, gaps, offsets), width core and links."""
    loc = Loc(raw)
    m = (loc.s >= s0 - prm["LINK_W"] - 20) & (loc.s <= s1 + prm["LINK_W"] + 20)
    pad = 80
    r0 = max(int((ZTOP - (loc.p[m, 1].max() + pad)) / 6), 0); r1 = min(int((ZTOP - (loc.p[m, 1].min() - pad)) / 6) + 1, NC)
    c0 = max(int((loc.p[m, 0].min() - pad) / 6), 0); c1 = min(int((loc.p[m, 0].max() + pad) / 6) + 1, NC)
    seg = sr.extract_segments(H, W, fp, plane, r0, r1, c0, c1)
    seg = sr.subseg(seg, ~seg["pond"])
    qs, vs = [], []
    for c in sr.chain(seg):
        q, v = sr.wiggle_profile(sr.canonical(c["pts"], c["closed"]), c["closed"], 12.0, 0.5)
        qs.append(q); vs.append(v)
    q, v = np.vstack(qs), np.concatenate(vs)
    cel = seg["cell"]
    chc = chv[cel[:, 0], cel[:, 1]] | chv[cel[:, 0] + 1, cel[:, 1]] | chv[cel[:, 0], cel[:, 1] + 1] | chv[cel[:, 0] + 1, cel[:, 1] + 1]
    qchg = chc[cKDTree(seg["p"].mean(1)).query(q)[1]]
    sq, uq, okq = loc(q)
    nb = int(round(s1 - s0)) + 1
    out, inner = {}, {}
    for sg, nm in ((1, "left"), (-1, "right")):
        sel = okq & (np.sign(uq) == sg) & (sq >= s0 - 0.5) & (sq <= s1 + 0.5)
        b = np.clip(np.round(sq[sel] - s0).astype(int), 0, nb - 1)
        oq = np.abs(uq[sel])
        inn = np.full(nb, np.inf)
        np.minimum.at(inn, b, oq)
        near = oq <= inn[b] + 1.0
        vv = v[sel][near]; fin = np.isfinite(vv)
        cov = np.isfinite(inn)
        mid = slice(int(prm["R_FILL"]), nb - int(prm["R_FILL"]))
        gaps = runs_of(~cov, 0)
        bad_gaps = [(int(a), int(b_)) for a, b_ in gaps if not (a == 0 or b_ == nb - 1) or b_ - a + 1 > prm["R_FILL"]]
        e = dict(samples=int(near.sum()), wiggle_p90=round(float(np.percentile(vv[fin], 90)), 4) if fin.any() else None,
                 wiggle_max=round(float(vv[fin].max()), 4) if fin.any() else None,
                 coverage_full=round(float(cov.mean()), 4), coverage_inner=round(float(cov[mid].mean()), 4),
                 gaps=[[round(s0 + a, 1), round(s0 + b_, 1)] for a, b_ in gaps], bad_gaps=bad_gaps)
        for end, (lo, hi) in (("link0", (s0 - prm["LINK_W"], s0 + prm["LINK_W"])), ("link1", (s1 - prm["LINK_W"], s1 + prm["LINK_W"]))):
            ml = okq & (np.sign(uq) == sg) & (sq >= lo) & (sq <= hi) & qchg & np.isfinite(v)
            e[end] = dict(samples=int(ml.sum()), wiggle_p90=round(float(np.percentile(v[ml], 90)), 4) if ml.any() else None,
                          wiggle_max=round(float(v[ml].max()), 4) if ml.any() else None)
        out[nm] = e
        inner[nm] = inn
    w = inner["left"] + inner["right"]
    fin = np.isfinite(w)
    midw = w[nb // 4:3 * nb // 4]
    wc = float(np.median(midw[np.isfinite(midw)])) if np.isfinite(midw).any() else float("nan")
    K = fin & (np.abs(w - wc) <= prm["WIDTH_TOL"])
    best, cur, bs = 0, 0, 0
    for i, kv in enumerate(K):
        cur = cur + 1 if kv else 0
        if cur > best:
            best, bs = cur, i - cur + 1
    narrow = fin & (w < wc - prm["WIDTH_TOL"])
    mono = {}
    for nm in ("left", "right"):
        o = inner[nm]
        drops = []
        for rng in (range(bs + best, nb), range(bs - 1, -1, -1)):
            run = -np.inf
            for i in rng:
                if np.isfinite(o[i]):
                    run = max(run, o[i])
                    drops.append(run - o[i])
        mono[nm] = round(float(max(drops, default=0.0)), 4)
    width = dict(median=round(wc, 4), core=[s0 + bs, s0 + bs + best - 1] if best else None, core_frac=round(best / nb, 4),
                 narrower_than_core_stations=int(narrow.sum()), outward_drop_max=mono,
                 min=round(float(w[fin].min()), 3) if fin.any() else None, max=round(float(w[fin].max()), 3) if fin.any() else None)
    return out, width


def check(meas, width, prm, tag):
    f = []
    for nm, e in meas.items():
        if e["wiggle_p90"] is None or e["wiggle_p90"] > prm["WIG_MAX"]:
            f.append(f"{tag} {nm}: wiggle p90 {e['wiggle_p90']} > {prm['WIG_MAX']}")
        if e["coverage_inner"] < prm["COVER_MIN"] or e["bad_gaps"]:
            f.append(f"{tag} {nm}: coverage {e['coverage_inner']} gaps {e['bad_gaps']}")
        for end in ("link0", "link1"):
            p = e[end]["wiggle_p90"]
            if p is not None and p > prm["LINK_WIG_MAX"]:
                f.append(f"{tag} {nm} {end}: wiggle p90 {p} > {prm['LINK_WIG_MAX']}")
    if width["core_frac"] < prm["CORE_MIN"]:
        f.append(f"{tag}: constant-width core {width['core_frac']} < {prm['CORE_MIN']}")
    if width["narrower_than_core_stations"]:
        f.append(f"{tag}: {width['narrower_than_core_stations']} stations narrower than the core")
    for nm, d in width["outward_drop_max"].items():
        if d > prm["MONO_TOL"]:
            f.append(f"{tag} {nm}: offset falls {d} m going out from the core")
    return f


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    for k in ("terrain", "footprint", "envelope", "cover", "out_terrain", "report"):
        ap.add_argument(k)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--work"); ap.add_argument("--crossings")
    ap.add_argument("--built", action="append", default=[])
    ap.add_argument("--footprint-tool", default=os.path.join(HERE, "pond_footprint_v31.py"))
    ap.add_argument("--param", action="append", default=[])
    a = ap.parse_args()
    prm = dict(PARAMS)
    for kv in a.param:
        k, v = kv.split("=")
        assert k in prm, f"unknown parameter {k}"
        prm[k] = float(v)
    t0 = time.time()
    for p in (a.out_terrain, a.report):
        assert not os.path.exists(p), f"fresh output required: {p}"
    work = a.work or os.path.splitext(a.out_terrain)[0] + "-work"
    os.makedirs(work, exist_ok=False)
    spec = json.load(open(a.spec, encoding="utf-8"))
    ids = [c["id"] for c in spec["clusters"]]
    assert len(ids) == len(set(ids)), "duplicate cluster ids in the spec"
    cws = [c for c in spec["clusters"] if c["class"] == "causeway"]
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
    ref_dir = os.path.join(work, "fp-input-check")
    subprocess.run([sys.executable, "-I", a.footprint_tool, a.terrain, a.cover, ref_dir, a.envelope], check=True,
                   stdout=subprocess.DEVNULL)
    fr = np.load(os.path.join(ref_dir, "footprint.npz"))
    assert all(np.array_equal(fr[k], f0[k], equal_nan=True) for k in ("plane", "field", "env_plane", "visible")), \
        "the given footprint is not the footprint of the given terrain/cover/envelope"
    W0, fp0 = sr.corner_water(plane0, field0)
    assert not (a.crossings and a.built), "--crossings replaces the inventory; do not combine it with --built"
    crossings, cr_src = sr.pending_crossings(a.crossings, a.built)
    base, pinfo = sr.base_protection(arrays, crossings, dict(sr.PARAMS))
    bprot = sr.BodyProt(base, env_plane, plane0, field0)
    prot = bprot.get("sea", SEA) | sr.c2v(np.isfinite(plane0))        # sea rule + every footprint cell stays as is
    runs = census(H0, plane0, prm)
    short = census(H0, plane0, prm, l_min=0.0)
    chains = road_chains()
    # the inventory is the spec: the census must agree with it
    inv_fail = []
    for c in cws:
        mt = [r for r in runs if r["chain"] == c["chain"] and abs(r["s0"] - c["s0"]) <= prm["SPEC_TOL"]
              and abs(r["s1"] - c["s1"]) <= prm["SPEC_TOL"]]
        if len(mt) != 1:
            inv_fail.append(f"spec causeway {c['id']} (chain {c['chain']} {c['s0']}-{c['s1']}) has {len(mt)} census matches")
    for r in runs:
        if not any(r["chain"] == c["chain"] and abs(r["s0"] - c["s0"]) <= prm["SPEC_TOL"] for c in cws):
            inv_fail.append(f"census causeway chain {r['chain']} {r['s0']}-{r['s1']} is not in the spec")
    clusters = classify_clusters(spec, runs, short, prm)
    for e in clusters:
        if (e["verdict"] == "causeway") != (e["spec_class"] == "causeway"):
            inv_fail.append(f"cluster {e['id']}: census verdict '{e['verdict']}' vs spec class '{e['spec_class']}'")
    if inv_fail:
        raise SystemExit("inventory mismatch (re-freeze the spec explicitly):\n  " + "\n  ".join(inv_fail))
    print(f"[causeway] census agrees with the spec: {len(runs)} causeways {time.time() - t0:.1f}s", flush=True)
    treated = []
    H = H0.copy()
    owner = np.zeros((N, N), bool)
    axes = {}
    for c in cws:
        rows, cols, vals, info, ax, (sgg, ust) = treat(H, owner, prot, arrays, chains[c["chain"]], float(c["s0"]),
                                                       float(c["s1"]), prm)
        H[rows, cols] = vals
        owner[rows, cols] = True
        info["chain"] = c["chain"]
        treated.append(dict(id=c["id"], **info))
        axes[c["id"]] = dict(chain=c["chain"], s0=c["s0"], s1=c["s1"], T=info["T"], axis=np.round(ax.p[::20], 4).tolist(),
                             station=np.round(ax.s[::20], 3).tolist(), ustar_station=sgg[::2].tolist(),
                             ustar=np.round(ust[::2], 4).tolist())
        print(f"[causeway] {c['id']}: chain {c['chain']} T {info['T']} s {info['slope_s']} changed {info['vertices_changed']}"
              f" {info['seconds']}s", flush=True)
    out32 = H.astype(np.float32)
    ch = out32 != arrays["heights"]
    for k_ in ("platform", "narva"):
        assert not (ch & arrays[k_]).any(), f"{k_} changed"
    assert not (ch & prot).any(), "protected vertex changed"
    cand = os.path.join(work, "candidate.npz")
    out = dict(arrays); out["heights"] = out32; out[OUT_MASK] = ch
    np.savez(cand, **out)
    fpdir = os.path.join(work, "fp")
    subprocess.run([sys.executable, "-I", a.footprint_tool, cand, a.cover, fpdir, a.envelope], check=True,
                   stdout=subprocess.DEVNULL)
    f1 = np.load(os.path.join(fpdir, "footprint.npz"))
    fp_same = {k: bool(np.array_equal(f1[k], f0[k], equal_nan=True)) for k in ("plane", "field", "env_plane", "visible")}
    plane1, field1 = f1["plane"].astype(np.float64), f1["field"].astype(np.float64)
    W1, fp1 = sr.corner_water(plane1, field1)
    Hc = out32.astype(np.float64)
    m0 = sr.fp_masks(H0, plane0, field0, env, dict(sr.PARAMS))
    m1 = sr.fp_masks(Hc, plane1, field1, env, dict(sr.PARAMS))
    newm = {n: int((m1[n] & ~m0[n]).sum()) for n in ("exposed", "env_leak", "bed_low", "pond_sea", "field_dev")}
    topo, bad = sr.sea_topology(H0, Hc)
    a0, b0 = sr.tri_slopes(H0); a1, b1 = sr.tri_slopes(Hc)
    ca = ch[:-1, :-1] | ch[:-1, 1:] | ch[1:, 1:]; cb = ch[:-1, :-1] | ch[1:, :-1] | ch[1:, 1:]
    sprm = dict(sr.PARAMS, SLOPE_MAX=prm["SLOPE_MAX"])
    n_slope = int((sr.slope_bad(a0, a1, sprm) & ca).sum() + (sr.slope_bad(b0, b1, sprm) & cb).sum())
    fails = []
    if not all(fp_same.values()):
        fails.append(f"footprint changed: {fp_same}")
    for n, v in newm.items():
        if v:
            fails.append(f"new {n}: {v}")
    if bad:
        fails.append(f"sea topology: {topo}")
    if n_slope:
        fails.append(f"{n_slope} changed triangles cross {prm['SLOPE_MAX']} deg")
    for t in treated:
        for k_ in ("wet_protected_land_px", "frozen_in_cut_triangles", "natural_dry_lowered_to_sea"):
            if t[k_]:
                fails.append(f"{t['id']}: {k_} {t[k_]}")
        c = [c for c in cws if c["id"] == t["id"]][0]
        before, wb = measure(H0, W0, fp0, plane0, ch, chains[c["chain"]], float(c["s0"]), float(c["s1"]), prm)
        after, wa = measure(Hc, W1, fp1, plane1, ch, chains[c["chain"]], float(c["s0"]), float(c["s1"]), prm)
        t["sides_before"], t["sides_after"], t["width_before"], t["width_after"] = before, after, wb, wa
        fails += check(after, wa, prm, t["id"])
    rep = dict(schema="causeway-v31.v2", tool=os.path.abspath(__file__), tool_sha256=sha(os.path.abspath(__file__)),
               inputs=dict(terrain=a.terrain, terrain_sha256=sha(a.terrain), footprint=a.footprint, footprint_sha256=sha(a.footprint),
                           envelope=a.envelope, envelope_sha256=sha(a.envelope), cover=a.cover, cover_sha256=sha(a.cover),
                           spec=a.spec, spec_sha256=sha(a.spec),
                           footprint_tool=a.footprint_tool, footprint_tool_sha256=sha(a.footprint_tool)),
               params=prm, protection=dict(pinfo, crossings_source=cr_src),
               census=[{k: v for k, v in r.items() if k != "poly"} for r in runs], clusters=clusters,
               treated=treated,
               validation=dict(fails=fails, footprint_identical=fp_same, new_masks=newm, sea_topology=topo,
                               slope_crossings=n_slope, footprint_report=os.path.join(fpdir, "footprint-report.json")),
               summary=dict(causeways=len(cws), treated=len(treated), vertices_changed=int(ch.sum()),
                            reserve_only_changed=int((ch & arrays["reserve"] & ~arrays["platform"] & ~arrays["narva"]).sum()),
                            platform_changed=int((ch & arrays["platform"]).sum()), narva_changed=int((ch & arrays["narva"]).sum()),
                            protected_changed=int((ch & prot).sum()), sea_to_land=int((ch & (H0 < SEA) & (Hc >= SEA)).sum()),
                            land_to_sea=int((ch & (H0 >= SEA) & (Hc < SEA)).sum()), seconds=round(time.time() - t0, 1)))
    with open(os.path.join(work, "axes.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(axes, f)
    if fails:
        with open(a.report + ".failed.json", "w", encoding="utf-8", newline="\n") as f:
            json.dump(rep, f, indent=1)
        raise SystemExit("causeway pass rejected:\n  " + "\n  ".join(fails))
    os.replace(cand, a.out_terrain)
    rep["output"] = dict(terrain=a.out_terrain, terrain_sha256=sha(a.out_terrain), work=work, mask=OUT_MASK)
    with open(a.report, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps(rep["summary"], indent=1))


if __name__ == "__main__":
    main()

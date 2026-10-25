"""EV102/EV103 (Guillermo, 2026-10-12): rounded land sills where a pond piece meets the engine sea, and rounded embankment
cones where a road stands as a cliff over water. Terrain only; pieces, roads and Narva unchanged; heights only rise.

A. Sills (choice "umbral de tierra"). A pond piece (plane >= 0.95 m) that ends over engine sea (0.75 m) shows two water
   heights, two shaders and the straight cell-aligned piece edge. Every vertex touching a covered cell and 8-adjacent to
   a sea vertex is a sill source. Crest = its piece plane + SILL_FREE + SILL_DOME * (1 - (r / R)^2), r = distance to
   the centroid of its 8-connected source group and R = that group's largest r + 6 m: the crest is highest mid-contact,
   so both waterlines bow out in a curve instead of running parallel to the straight piece edge. Outside the pieces the
   sill is the upper envelope of crest + profile(d, SILL_TOP, SILL_SLOPE) (round in plan); under the pieces it is the
   steeper envelope crest + profile(d, 0, POND_SLOPE), so it only buries the piece edge and the pond keeps its area.
B. Cones (choice "terraplen en cono pero redondeado"). A dry road vertex (reserve | platform) more than CLIFF_M above
   the water plane of an 8-adjacent wet vertex is a cliff; dry road vertices within CONE_SPREAD cells of a cliff are cone
   sources with their own height. The cone is the envelope of H_q + profile(d, 0, CONE_SLOPE), kept within CONE_REACH.
profile(d, top, slope) = -slope * ROUND_M * (softplus((d - top) / ROUND_M) - softplus(-top / ROUND_M)): 0 at the source,
flat to about `top`, a rounded shoulder of width ~ROUND_M, then `slope`. The result is a smooth maximum of terrain and
envelope (rounded toe, width ROUND_TOE m) where the envelope is within 1 m of the terrain; road/narva vertices are kept
and no vertex is lowered. Guards: a pond body may not lose more than BODY_LOSS_MAX of its cells, nor a sea body of its
wet vertices (sea pockets at a sill excepted), and no raised triangle may end steeper than max(SLOPE_MAX_DEG, its slope before).
Usage: sills_and_cones_ev102.py <in.npz> <cover.npy> <out.npz> <report.json>
"""
import json, sys
import numpy as np
from scipy.ndimage import binary_dilation, grey_dilation, distance_transform_edt, label, find_objects

SEA = 0.75
SILL_FREE, SILL_DOME, SILL_TOP, SILL_SLOPE = 0.30, 0.60, 6.0, 0.12   # m above plane, extra mid-contact m, crest half-width m, ~1:8
POND_SLOPE = 0.35                                                    # sill flank under the pieces, ~1:3
CLIFF_M, CONE_SPREAD, CONE_SLOPE, CONE_REACH = 2.0, 2, 0.5, 24.0   # cone 1:2
SLOPE_MAX_DEG, GUARD_ITERS = 35.0, 12
BODY_LOSS_MAX, POCKET_MAX = 0.25, 200   # a pond body may lose <= 25 % of its cells, a sea body of its wet vertices
POND_POCKET_MAX = 20                    # pond bodies under this many cells that touch a sill source are buried, not kept
ROUND_M, ROUND_TOE = 3.0, 0.3
N8 = np.ones((3, 3), bool)
S4 = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)


def vertex_plane(cover):
    p = np.full((2048, 2048), -np.inf)
    c = np.where(np.isfinite(cover), cover, -np.inf)
    for dr in (0, 1):
        for dc in (0, 1):
            p[dr:dr + 2047, dc:dc + 2047] = np.maximum(p[dr:dr + 2047, dc:dc + 2047], c)
    return p


def softplus(u):
    return np.logaddexp(0.0, u)


def envelope(src_h, top, slope, radius_cells):
    k = int(radius_cells)
    yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
    d = 6.0 * np.hypot(yy, xx)
    st = -slope * ROUND_M * (softplus((d - top) / ROUND_M) - softplus(-top / ROUND_M))
    st[d > 6.0 * k + 1e-6] = -1e6
    return grey_dilation(src_h, structure=st, mode="constant", cval=-1e6)


def tri_slopes(H):
    """Slope in degrees of the native NW-SE triangles: A = (NW, NE, SE), B = (NW, SE, SW); 6 m cells."""
    nw, ne, sw, se = H[:-1, :-1], H[:-1, 1:], H[1:, :-1], H[1:, 1:]
    ga = np.hypot((ne - nw) / 6.0, (ne - se) / 6.0)
    gb = np.hypot((se - sw) / 6.0, (nw - sw) / 6.0)
    return np.degrees(np.arctan(ga)), np.degrees(np.arctan(gb))


def offending(H, H0, s0):
    """Vertices that are corners of a triangle with a changed corner steeper than max(SLOPE_MAX_DEG, base)."""
    ch = H != H0
    s1 = tri_slopes(H)
    out = np.zeros(H.shape, bool)
    for (a0, a1), corners in zip(zip(s0, s1), (((0, 0), (0, 1), (1, 1)), ((0, 0), (1, 1), (1, 0)))):
        chc = np.zeros(a0.shape, bool)
        for dr, dc in corners:
            chc |= ch[dr:dr + 2047, dc:dc + 2047]
        bad = chc & (a1 > np.maximum(SLOPE_MAX_DEG, a0))   # no tolerance: the shore harness adds 0.01 against an older base
        for dr, dc in corners:
            out[dr:dr + 2047, dc:dc + 2047] |= bad
    return out


def piece_edge_violations(H, cover, VP):
    covered = np.isfinite(cover)
    unc_touch = np.zeros(H.shape, bool)            # corners of uncovered cells
    for dr in (0, 1):
        for dc in (0, 1):
            unc_touch[dr:dr + 2047, dc:dc + 2047] |= ~covered
    edge = np.isfinite(VP) & unc_touch               # vertex on a piece boundary
    return edge & (H < VP + 0.05)


def main():
    src, cover_path, dst, rep_path = sys.argv[1:5]
    z = np.load(src)
    arrays = {k: z[k].copy() for k in z.files}
    H0 = arrays["heights"].astype(np.float64)
    cover = np.load(cover_path)
    VP = vertex_plane(cover)
    touch = np.isfinite(VP)
    WPL = np.where(touch, VP, SEA)
    wet = H0 < WPL
    sea = (H0 < SEA) & ~touch
    road = arrays["reserve"] | arrays["platform"]
    keep = (road & ~wet) | arrays["narva"]

    # A. sills
    sill_src = touch & binary_dilation(sea, N8)
    crest = np.where(sill_src, VP + SILL_FREE, -1e6)
    glab, ng = label(sill_src, N8)
    for i, sl in enumerate(find_objects(glab), 1):
        rr, cc = np.nonzero(glab[sl] == i)
        rr = rr + sl[0].start; cc = cc + sl[1].start
        r = 6.0 * np.hypot(rr - rr.mean(), cc - cc.mean())
        crest[rr, cc] += SILL_DOME * (1.0 - (r / (r.max() + 6.0)) ** 2)
    reachA = SILL_TOP + (np.max(crest[sill_src]) - np.min(H0[binary_dilation(sill_src, np.ones((9, 9)))])) / SILL_SLOPE
    kA = min(int(np.ceil(reachA / 6.0)), 8)
    sill = np.where(touch, envelope(crest, 0.0, POND_SLOPE, 3), envelope(crest, SILL_TOP, SILL_SLOPE, kA))
    # B. cones
    nb_gap = np.zeros(H0.shape)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr or dc:
                w = np.roll(np.roll(wet, dr, 0), dc, 1)
                p = np.roll(np.roll(WPL, dr, 0), dc, 1)
                nb_gap = np.maximum(nb_gap, np.where(w, H0 - p, 0.0))
    cliff = road & ~wet & (nb_gap > CLIFF_M)
    cone_src = road & ~wet & binary_dilation(cliff, np.ones((2 * CONE_SPREAD + 1,) * 2, bool))
    kB = int(np.ceil(CONE_REACH / 6.0))
    cone = envelope(np.where(cone_src, H0, -1e6), 0.0, CONE_SLOPE, kB)
    near_src = distance_transform_edt(~cone_src) * 6.0 <= CONE_REACH
    cone = np.where(near_src, cone, -1e6)

    target = np.maximum(sill, cone)
    act = target > -1e5
    smax = 0.5 * (H0 + target + np.sqrt((H0 - target) ** 2 + ROUND_TOE ** 2))   # >= max(H0, target)
    H = np.where(act & ~keep & (target > H0 - 1.0), smax, H0)   # cut where the excess is < 2.2 cm
    # slope guard: a native triangle with a raised corner may not exceed max(SLOPE_MAX_DEG, its base slope); halve the
    # raise of the raised corners of each offending triangle, and after GUARD_ITERS passes drop those raises entirely
    # body guard. Pond bodies are 8-connected covered cells; a cell is lost when all four corners end at or above its
    # plane. A pond body losing more than BODY_LOSS_MAX of its cells keeps every vertex touching it unraised (e.g. a
    # stream running along a road). Sea bodies (4-connected wet vertices with no piece) losing more than BODY_LOSS_MAX
    # of their wet vertices keep them unraised. Exempt, because the sill is meant to bury them: sea pockets of
    # < POCKET_MAX vertices next to a sill source and pond bodies of < POND_POCKET_MAX cells touching one.
    covered = np.isfinite(cover)
    PB, npb = label(covered, N8)
    cmin = lambda A: np.minimum.reduce([A[:-1, :-1], A[1:, :-1], A[:-1, 1:], A[1:, 1:]])
    cell_lost = covered & (cmin(H0) < cover) & ~(cmin(H) < cover)
    psize = np.bincount(PB.ravel(), minlength=npb + 1)
    plost = np.bincount(PB[cell_lost].ravel(), minlength=npb + 1)
    cell_at_sill = covered & (sill_src[:-1, :-1] | sill_src[:-1, 1:] | sill_src[1:, :-1] | sill_src[1:, 1:])
    pond_at_sill = np.bincount(PB[cell_at_sill].ravel(), minlength=npb + 1) > 0
    prevert = (plost > BODY_LOSS_MAX * psize) & ~(pond_at_sill & (psize < POND_POCKET_MAX))
    prevert[0] = False
    rcell = prevert[PB]
    rv = np.zeros(H.shape, bool)
    for dr in (0, 1):
        for dc in (0, 1):
            rv[dr:dr + 2047, dc:dc + 2047] |= rcell
    seawet = wet & ~touch
    L0, n0 = label(seawet, S4)
    size0 = np.bincount(L0.ravel(), minlength=n0 + 1)
    lost = np.bincount(L0[seawet & ~(H < WPL)].ravel(), minlength=n0 + 1)
    at_sill = np.bincount(L0[seawet & binary_dilation(sill_src, N8)].ravel(), minlength=n0 + 1) > 0
    srevert = (lost > BODY_LOSS_MAX * size0) & ~(at_sill & (size0 < POCKET_MAX))
    srevert[0] = False
    rv |= seawet & srevert[L0]
    H = np.where(rv, H0, H)
    kept_bodies = []
    for lab_, ids, kind in ((PB, np.nonzero(prevert)[0], "pond"), (L0, np.nonzero(srevert)[0], "sea")):
        for i in ids:
            rr, cc_ = np.nonzero(lab_ == i)
            kept_bodies.append([int(6 * cc_.mean()), int(6 * (2047 - rr.mean())), int(len(rr)), kind])
    H = H.astype(np.float32).astype(np.float64)   # check what is written (float32), not the float64 intermediate
    s0 = tri_slopes(H0)
    guard = 0
    for it in range(GUARD_ITERS + 1):
        bad = offending(H, H0, s0)
        if not bad.any():
            break
        fix = bad & (H != H0)
        guard += int(fix.sum())
        H = np.where(fix, H0 if it == GUARD_ITERS else H0 + 0.5 * (H - H0), H).astype(np.float32).astype(np.float64)
    assert not offending(H, H0, s0).any()
    ch = H != H0
    assert not (ch & keep).any() and not (H < H0).any()

    # report
    pe0 = piece_edge_violations(H0, cover, VP); pe1 = piece_edge_violations(H, cover, VP)
    cmin = lambda A: np.minimum.reduce([A[:-1, :-1], A[1:, :-1], A[:-1, 1:], A[1:, 1:]])
    covered = np.isfinite(cover)
    def contacts(A):
        sc = (~covered) & (cmin(A) < SEA)
        return int((covered & binary_dilation(sc, N8)).sum())
    wet1 = H < WPL
    def cliffs(A, w, lim=CLIFF_M):
        g = np.zeros(A.shape)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr or dc:
                    ww = np.roll(np.roll(w, dr, 0), dc, 1); p = np.roll(np.roll(WPL, dr, 0), dc, 1)
                    g = np.maximum(g, np.where(ww, A - p, 0.0))
        return int((road & ~w & (g > lim)).sum())
    nav = arrays["cls"] == 3
    lostA = sea & ~(H < SEA)
    rep = dict(schema="ev102-sills-cones.v1",
               params=dict(POND_POCKET_MAX=POND_POCKET_MAX, SILL_FREE=SILL_FREE, SILL_DOME=SILL_DOME, SILL_TOP=SILL_TOP, SILL_SLOPE=SILL_SLOPE, POND_SLOPE=POND_SLOPE, CLIFF_M=CLIFF_M, CONE_SPREAD=CONE_SPREAD,
                           CONE_SLOPE=CONE_SLOPE, CONE_REACH=CONE_REACH, ROUND_M=ROUND_M, ROUND_TOE=ROUND_TOE),
               sill_sources=int(sill_src.sum()), sill_groups=int(ng), cliff_vertices_before=int(cliff.sum()), cone_sources=int(cone_src.sum()),
               body_guard=dict(bodies_kept=len(kept_bodies), vertices_restored=int(rv.sum()), kept_x_z_size_kind=kept_bodies),
               slope_guard_vertex_fixes=guard, changed=int(ch.sum()), raise_m_q50_90_max=[round(float(v), 2) for v in np.quantile((H - H0)[ch], [.5, .9, 1])],
               piece_edge_violations=dict(before=int(pe0.sum()), after=int(pe1.sum()), new=int((pe1 & ~pe0).sum())),
               pond_sea_contact_cells=dict(before=contacts(H0), after=contacts(H)),
               road_cliff_vertices=dict(before=cliffs(H0, wet), after=cliffs(H, wet1)),
               road_cliff_vertices_over_3p5m=dict(before=cliffs(H0, wet, 3.5), after=cliffs(H, wet1, 3.5)),
               sea_vertices_turned_dry=int(lostA.sum()), navigable_cls3_turned_dry=int((lostA & nav).sum()),
               pond_vertices_turned_dry=int((touch & wet & ~wet1).sum()))
    arrays["heights"] = H.astype(np.float32)
    arrays["ev102_raised"] = ch
    np.savez(dst, **arrays)
    open(rep_path, "w").write(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()

"""Shoreline evaluation harness v3 for round 3 (pond banks on EV99). Frozen: record its sha256 and never edit it.

Usage:
  python -I -B eval_shore_v3.py <candidate.npz> <out.json>
  python -I -B eval_shore_v3.py --selftest <outdir>

Base and cover are fixed and hash-checked before every run (a mismatch stops the run):
  base  EV99  v31-ev99-shore-lakes-20261012/terrain-ev99.npz (sha256 8e35c3ab...)
  cover       v30-shore-sdf-20261011/cover-level-ev98.npy    (sha256 7421b17c..., unchanged since EV98)
v2 (round2/harness/eval_shore_v2.py, sha256 422bf818...) is imported read-only after checking its hash and the hash of
v1 (eval_shore.py, sha256 343f5716...). Its base_context() and evaluate() run unchanged with base = EV99, so the six
v1 gates and the twelve v2 gates keep their code and thresholds and are measured relative to EV99. The v2 report is
written as the sidecar <out>.v2.json (its v1 sidecar is <out>.v2.v1.json) and copied into this report under "v2".

New gates (violation counts, 0 = pass; groups G_island, G_navdry, G_navband, G_steep in gate_groups_pass):
  island_lost       TRI model (v2 tri_field, K=3, 2 m pixels). Dry = not TRI-wet, dry bodies 8-connected (the dual of
                    4-connected water); island = base dry body that does not touch the raster border and has >= 9 px
                    (36 m2). Violation = base islands with no pixel still dry in the candidate.
  island_keep_lt80  base islands whose pixels still dry in the candidate are < 80 % of their base pixels (lost included).
  nav_dry           cls 3 vertices wet in the base (H < vertex plane; v2 x.wet0) that are not wet in the candidate.
  nav_band          cls 3 vertices with draft (vertex plane - H) in [0.95, 1.0): n0 in the base, n1 in the candidate;
                    violation = max(0, n1 - n0 - floor(n0 / 100)), i.e. at most +1 % versus the base.
  steep_count       native NW-SE triangles (A = NW,NE,SE and B = NW,SE,SW counted separately; v1 tri_slopes) whose slope
                    rises by more than 20 deg versus the base; violation = max(0, count - 50).
  steep_over35      of those steepened triangles, the ones steeper than 35 deg in the candidate.
Info only, not gated: new TRI water inside and outside covered cells, islands joined to the border-touching land.

Self-test (--selftest): input hashes; EV99 vs EV99 with all 24 gates zero and equal metrics; the v2 report produced
in-process equals a standalone run of the unchanged v2 file with --base EV99 (v1 sidecar too); the EV99 base metrics
equal the candidate side of the round-2 integration run harness-v2-ev99.json (EV98 -> EV99); planted negative controls
for every new gate fail (drown an islet, shrink an island, dry a navigable vertex, push into the band 2 % of the base
band count and, separately, 2 % of all cls 3 vertices, steepen 60 triangles, six triangles above 35 deg) and threshold
controls just inside the limits pass (band +1 %, 48 steepened triangles); the v2 negative controls re-planted on EV99,
the v1 negative control replayed on EV99, a v1 pond_bed control and a water-body merge control (v2 has none) fire
their gates; every one of the 24 gates fires in at least one negative control. Exit status 1 when any check fails.
"""
import argparse, hashlib, importlib.util, json, math, os, subprocess, sys, time
sys.dont_write_bytecode = True
import numpy as np
from scipy.ndimage import label, find_objects, binary_dilation, distance_transform_edt

ROOT = 'E:/DayZ-Baltic-Build/v30-shore-sdf-20261011'
V1_PATH = ROOT + '/eval_shore.py'
V1_SHA256 = '343f5716aeba0c8eb4e48497c71b8df07f32d058bacf53a65e6b46383f69922e'
V2_PATH = ROOT + '/round2/harness/eval_shore_v2.py'
V2_SHA256 = '422bf8186e0d75f9b6c3aab241bd96eec26c20a501377d7542d10d108aa7b9b4'
EV99_PATH = 'E:/DayZ-Baltic-Build/v31-ev99-shore-lakes-20261012/terrain-ev99.npz'
EV99_SHA256 = '8e35c3ab3638ae423728f57d5968e6657efd7d52a4c1d22e980d71e14b4fc5a3'
COVER_PATH = ROOT + '/cover-level-ev98.npy'
COVER_SHA256 = '7421b17ce8c3ad711c7bf7fa4ee227d98503df4cdf3b63f35798586d22680ba3'
# round-2 integration run of the unchanged v2 on EV99 (base EV98, candidate EV99); its candidate side = EV99 metrics
EV99_V2_RUN = 'E:/DayZ-Baltic-Build/v31-ev99-shore-lakes-20261012/harness-v2-ev99.json'
EV99_V2_RUN_SHA256 = '6e696f3bdc96ef03b3eb75344c091b382844603870225b9a7bd20ebae40b8a22'

ISLAND_MIN_PX, ISLAND_KEEP = 9, 0.80          # 9 TRI px of 2 m = 36 m2
NAV_CLS, NAVBAND_LO, NAVBAND_HI, NAVBAND_PCT = 3, 0.95, 1.0, 1
STEEP_INCR_DEG, STEEP_MAX_NEW, STEEP_CEIL_DEG = 20.0, 50, 35.0
S8 = np.ones((3, 3), int)
V2_ONLY_GATES = ('area_large', 'area_mid', 'area_total', 'topo_vtx_lost', 'topo_vtx_split', 'topo_vtx_merge',
                 'topo_tri_lost', 'topo_tri_split', 'topo_tri_merge', 'flood', 'nav_shallow', 'nav_channel_raised')
V3_GATES = ('island_lost', 'island_keep_lt80', 'nav_dry', 'nav_band', 'steep_count', 'steep_over35')
V3_GROUPS = {'G_island': ('island_lost', 'island_keep_lt80'), 'G_navdry': ('nav_dry',), 'G_navband': ('nav_band',),
             'G_steep': ('steep_count', 'steep_over35')}
THRESHOLDS = dict(island_min_m2=36.0, island_keep_min_frac=ISLAND_KEEP, nav_cls=NAV_CLS,
                  nav_band_draft_m=[NAVBAND_LO, NAVBAND_HI], nav_band_max_increase_pct=NAVBAND_PCT,
                  steep_increase_deg=STEEP_INCR_DEG, steep_max_new=STEEP_MAX_NEW, steep_ceiling_deg=STEEP_CEIL_DEG)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for ch in iter(lambda: fh.read(1 << 20), b''):
            h.update(ch)
    return h.hexdigest()


def load_v2():
    for p, h in ((V1_PATH, V1_SHA256), (V2_PATH, V2_SHA256)):
        got = sha256(p)
        if got != h:
            raise SystemExit(f'hash mismatch for {p} ({got} != {h}); refusing to run')
    spec = importlib.util.spec_from_file_location('eval_shore_v2_ro', V2_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)          # v2 re-checks the v1 hash itself before importing it
    if mod.V1_SHA256 != V1_SHA256 or tuple(mod.V1_GATES) != ('frozen', 'band', 'pond_bed', 'piece_edge', 'new_sea', 'slope'):
        raise SystemExit('v2 module does not pin the expected v1')
    return mod


H2 = load_v2()
EV = H2.EV
K = H2.K
ALL_GATES = tuple(H2.V1_GATES) + V2_ONLY_GATES + V3_GATES


def check_inputs():
    for p, h in ((EV99_PATH, EV99_SHA256), (COVER_PATH, COVER_SHA256)):
        got = sha256(p)
        if got != h:
            raise SystemExit(f'input hash mismatch for {p} ({got} != {h}); refusing to run')


# ---------------------------------------------------------------- base context (v2 context + v3 fields)
def base_context():
    check_inputs()
    x = H2.base_context(EV99_PATH, COVER_PATH)
    t0 = time.time()
    # islands on the TRI raster (judge_r2_hunt.py: dry = ~W0t, 8-connected, not touching the border, >= 9 px)
    D0 = ~x.W0t
    x.Ld0, x.nd0 = label(D0, S8)
    border = np.unique(np.r_[x.Ld0[0], x.Ld0[-1], x.Ld0[:, 0], x.Ld0[:, -1]])
    x.ard0 = np.bincount(x.Ld0.ravel(), minlength=x.nd0 + 1)
    isl = np.ones(x.nd0 + 1, bool); isl[0] = False; isl[border] = False
    x.isl_all = np.where(isl)[0]
    x.isl_ids = np.where(isl & (x.ard0 >= ISLAND_MIN_PX))[0]
    big = np.zeros(x.nd0 + 1, bool); big[x.isl_ids] = True
    x.islpx = big[x.Ld0]
    del D0
    # slopes per native triangle (v1 tri_slopes), navigable draft band
    x.s0a, x.s0b = EV.tri_slopes(x.H0)
    x.d0 = -x.f0
    x.band0 = x.nav & (x.d0 >= NAVBAND_LO) & (x.d0 < NAVBAND_HI)
    x.nband0 = int(x.band0.sum())
    x.covpx = np.repeat(np.repeat(x.covered, K, 0), K, 1)
    x.ext_runtime_s = round(time.time() - t0, 1)
    return x


# ---------------------------------------------------------------- v3 gates
def tri_corner_minmax(H):
    nw, ne, sw, se = H[:-1, :-1], H[:-1, 1:], H[1:, :-1], H[1:, 1:]
    return ((np.minimum.reduce([nw, ne, se]), np.maximum.reduce([nw, ne, se])),
            (np.minimum.reduce([nw, se, sw]), np.maximum.reduce([nw, se, sw])))


def v3_part(x, H1):
    gates, det = {}, {}
    pa = H2.PX * H2.PX
    # G_island
    F1 = H2.tri_field(H1, x.cp32)
    W1t = F1 < 0
    del F1
    D1 = ~W1t
    m = x.islpx & D1
    lab0 = x.Ld0[m]
    keep = np.bincount(lab0, minlength=x.nd0 + 1)
    ids = x.isl_ids
    frac = keep[ids] / x.ard0[ids]
    lost = ids[keep[ids] == 0]
    low = ids[frac < ISLAND_KEEP]
    Ld1, nd1 = label(D1, S8)
    border1 = np.unique(np.r_[Ld1[0], Ld1[-1], Ld1[:, 0], Ld1[:, -1]])
    ar1 = np.bincount(Ld1.ravel(), minlength=nd1 + 1)
    isl1 = np.ones(nd1 + 1, bool); isl1[0] = False; isl1[border1] = False
    bmask = np.zeros(nd1 + 1, bool); bmask[border1] = True; bmask[0] = False
    joined = np.unique(lab0[bmask[Ld1[m]]])
    del Ld1, m, lab0
    order = ids[np.argsort(frac, kind='stable')][:8]
    worst = H2.locate(x.Ld0, order, x.ard0, H2.tri_xz, maxn=8, largest_first=False)
    fr = dict(zip(ids.tolist(), frac.tolist()))
    det['island'] = dict(base_islands_ge36=int(ids.size), base_islands_all=int(x.isl_all.size),
                         cand_islands_ge36=int((isl1 & (ar1 >= ISLAND_MIN_PX)).sum()), cand_islands_all=int(isl1.sum()),
                         lost=int(lost.size), keep_lt80=int(low.size), keep_lt95=int((frac < 0.95).sum()),
                         min_keep_frac=round(float(frac.min()), 4) if ids.size else None,
                         joined_border_land=int(joined.size),
                         worst_x_z_m2_keep=[w + [round(fr[int(t)], 4)] for w, t in zip(worst, order)],
                         lost_x_z_m2=H2.locate(x.Ld0, lost, x.ard0, H2.tri_xz, maxn=8) if lost.size else [])
    gates['island_lost'] = int(lost.size)
    gates['island_keep_lt80'] = int(low.size)
    neww = W1t & ~x.W0t
    det['info_new_tri_water'] = dict(covered_m2=float((neww & x.covpx).sum() * pa),
                                     uncovered_m2=float((neww & ~x.covpx).sum() * pa),
                                     new_dry_m2=float((x.W0t & ~W1t).sum() * pa))
    del W1t, D1, neww
    # G_navdry
    f1 = H1.astype(np.float64) - x.vpl
    d1 = -f1
    dH = H1.astype(np.float64) - x.H0.astype(np.float64)
    navdry = x.nav & x.wet0 & ~(f1 < 0)
    rr, cc = np.nonzero(navdry)
    det['nav_dry'] = dict(navigable_vertices=int(x.nav.sum()), navigable_wet_base=int((x.nav & x.wet0).sum()),
                          turned_dry=int(rr.size),
                          by_bank_dist_m={'le6': int((navdry & (x.bankdist <= 6)).sum()),
                                          'gt6': int((navdry & (x.bankdist > 6)).sum())},
                          x_z_draft0_dH=[[6 * int(c), 6 * (2047 - int(r)), round(float(x.d0[r, c]), 3),
                                          round(float(dH[r, c]), 3)] for r, c in zip(rr[:8], cc[:8])])
    gates['nav_dry'] = int(rr.size)
    # G_navband
    band1 = x.nav & (d1 >= NAVBAND_LO) & (d1 < NAVBAND_HI)
    n0, n1 = x.nband0, int(band1.sum())
    allowed = n0 * NAVBAND_PCT // 100
    det['nav_band'] = dict(base=n0, cand=n1, increase=n1 - n0, allowed_increase=allowed,
                           increase_pct=round(100.0 * (n1 - n0) / max(n0, 1), 3),
                           entered=int((band1 & ~x.band0).sum()), left=int((x.band0 & ~band1).sum()),
                           entered_from_ge1p0=int((band1 & ~x.band0 & (x.d0 >= NAVBAND_HI)).sum()),
                           entered_from_lt0p95=int((band1 & ~x.band0 & (x.d0 < NAVBAND_LO)).sum()))
    gates['nav_band'] = max(0, n1 - n0 - allowed)
    # G_steep
    s1a, s1b = EV.tri_slopes(H1)
    ia = (s1a - x.s0a) > STEEP_INCR_DEG
    ib = (s1b - x.s0b) > STEEP_INCR_DEG
    n = int(ia.sum() + ib.sum())
    over = int((ia & (s1a > STEEP_CEIL_DEG)).sum() + (ib & (s1b > STEEP_CEIL_DEG)).sum())
    (amn, amx), (bmn, bmx) = tri_corner_minmax(H1.astype(np.float64))
    st = dict(underwater=0, straddle=0, dry=0)
    for msk, mn, mx in ((ia, amn, amx), (ib, bmn, bmx)):
        uw = msk & (mx < x.cp64); dr = msk & (mn >= x.cp64)
        st['underwater'] += int(uw.sum()); st['dry'] += int(dr.sum()); st['straddle'] += int((msk & ~uw & ~dr).sum())
    r_, c_ = np.indices(ia.shape)
    cx, cz = 6.0 * c_ + 3, 6.0 * (2047 - r_) - 3
    spb = (cx >= EV.SPB[0]) & (cx <= EV.SPB[1]) & (cz >= EV.SPB[2]) & (cz <= EV.SPB[3])
    top = []
    for tri, msk, s0, s1 in (('A', ia, x.s0a, s1a), ('B', ib, x.s0b, s1b)):
        ii, jj = np.nonzero(msk)
        top += [[int(cx[i, j]), int(cz[i, j]), tri, round(float(s0[i, j]), 2), round(float(s1[i, j]), 2)]
                for i, j in zip(ii, jj)]
    top.sort(key=lambda t: -(t[4] - t[3]))
    det['steep'] = dict(steepened=n, over35=over, in_spb=int((ia & spb).sum() + (ib & spb).sum()), **st,
                        max_increase_deg=round(float(max((s1a - x.s0a).max(), (s1b - x.s0b).max())), 3),
                        worst_x_z_tri_base_cand=top[:10])
    gates['steep_count'] = max(0, n - STEEP_MAX_NEW)
    gates['steep_over35'] = over
    return gates, det


def evaluate(x, cand_path, out_path):
    t0 = time.time()
    stem = out_path[:-5] if out_path.endswith('.json') else out_path
    v2_out = stem + '.v2.json'
    r2 = H2.evaluate(x, cand_path, v2_out)
    t1 = time.time()
    H1 = np.load(cand_path)['heights']
    g3, det = v3_part(x, H1)
    gates = dict(r2['gates_violations'])
    if tuple(gates) != tuple(H2.V1_GATES) + V2_ONLY_GATES:
        raise SystemExit('v2 gate set differs from the frozen eighteen gates')
    gates.update(g3)
    groups = dict(r2['gate_groups_pass'])
    for g, ks in V3_GROUPS.items():
        groups[g] = all(gates[k] == 0 for k in ks)
    res = dict(schema='shore-eval.v3', harness=os.path.abspath(__file__).replace('\\', '/'),
               harness_sha256=sha256(__file__), v2_harness=V2_PATH, v2_sha256=V2_SHA256, v1_sha256=V1_SHA256,
               candidate=cand_path, candidate_sha256=r2['candidate_sha256'],
               base=EV99_PATH, base_sha256=r2['base_sha256'], cover=COVER_PATH, cover_sha256=r2['cover_sha256'],
               gates_violations=gates, gates_pass=all(v == 0 for v in gates.values()), gate_groups_pass=groups,
               thresholds_v3=THRESHOLDS, changed_vertices=r2['changed_vertices'], max_abs_change_m=r2['max_abs_change_m'],
               details_v3=det, summary_base_cand=r2['summary_base_cand'], v2_sidecar=v2_out, v2=r2,
               runtime_s=dict(base_context=x.runtime_s, base_context_v3=x.ext_runtime_s, v2=round(t1 - t0, 1),
                              v3=round(time.time() - t1, 1)))
    if res['base_sha256'] != EV99_SHA256 or res['cover_sha256'] != COVER_SHA256:
        raise SystemExit('base or cover hash changed during the run')
    with open(out_path, 'w') as fh:
        fh.write(json.dumps(res, indent=1))
    return res


# ---------------------------------------------------------------- self-test controls
def vertex_min_plane(x):
    p = np.full((2048, 2048), np.inf)
    for a, b in ((slice(None, -1), slice(None, -1)), (slice(None, -1), slice(1, None)),
                 (slice(1, None), slice(None, -1)), (slice(1, None), slice(1, None))):
        p[a, b] = np.minimum(p[a, b], x.cp64)
    return p


def island_pixels(x, objs, t):
    sl = objs[t - 1]
    ii, jj = np.nonzero(x.Ld0[sl] == t)
    return ii + sl[0].start, jj + sl[1].start


def drown(x, H, cm, vminp):
    vm = H2.corners_of(cm)
    H[vm] = np.minimum(H[vm], vminp[vm] - 0.3)   # every corner below every incident plane: all TRI samples wet
    return vm


def nc3_drown_islet(x):
    objs = find_objects(x.Ld0); vminp = vertex_min_plane(x)
    for t in x.isl_ids[np.argsort(x.ard0[x.isl_ids], kind='stable')]:
        ii, jj = island_pixels(x, objs, t)
        cm = np.zeros((2047, 2047), bool); cm[ii // K, jj // K] = True
        if x.covered[cm].any() or (H2.corners_of(cm) & x.frozen).any():
            continue
        H = x.H0.astype(np.float64).copy()
        drown(x, H, cm, vminp)
        H = H.astype(np.float32)
        xx, zz = H2.tri_xz(ii.mean(), jj.mean())
        return H, dict(island=int(t), base_m2=float(x.ard0[t] * 4), x=round(float(xx)), z=round(float(zz)),
                       cells=int(cm.sum()), lowered_vertices=int((H != x.H0).sum()))
    raise SystemExit('no sea islet for nc3_drown_islet')


def nc3_shrink_island(x):
    objs = find_objects(x.Ld0); vminp = vertex_min_plane(x)
    for t in x.isl_ids[np.argsort(-x.ard0[x.isl_ids], kind='stable')]:
        if not (150 <= x.ard0[t] <= 5000):
            continue
        ii, jj = island_pixels(x, objs, t)
        cr, cc = ii // K, jj // K
        cm = np.zeros((2047, 2047), bool); cm[cr, cc] = True
        if x.covered[cm].any() or (H2.corners_of(cm) & x.frozen).any():
            continue
        key, cnt = np.unique(cc * 4096 + cr, return_counts=True)       # cells ordered west -> east
        take = key[np.cumsum(cnt) <= 0.35 * ii.size]
        if take.size < 2 or take.size > 0.6 * key.size:
            continue
        sub = np.zeros((2047, 2047), bool); sub[take % 4096, take // 4096] = True
        H = x.H0.astype(np.float64).copy()
        drown(x, H, sub, vminp)
        H = H.astype(np.float32)
        xx, zz = H2.tri_xz(ii.mean(), jj.mean())
        return H, dict(island=int(t), base_m2=float(x.ard0[t] * 4), x=round(float(xx)), z=round(float(zz)),
                       drowned_cells=int(take.size), island_cells=int(key.size),
                       drowned_px_share=round(float(cnt[np.cumsum(cnt) <= 0.35 * ii.size].sum() / ii.size), 3))
    raise SystemExit('no island for nc3_shrink_island')


def nc3_dry_nav(x):
    cand = x.nav & x.wet0 & ~x.frozen
    pref = cand & (x.d0 < 0.5)
    rr, cc = np.nonzero(pref if pref.any() else cand)
    r, c = int(rr[0]), int(cc[0])
    H = x.H0.copy(); H[r, c] = np.float32(x.vpl[r, c] + 0.1)
    return H, dict(vertex=[r, c], x=6 * c, z=6 * (2047 - r), draft0=round(float(x.d0[r, c]), 3), expect_nav_dry=1)


def navband_push(x, k):
    cand = x.nav & x.wet0 & ~x.frozen & (x.d0 >= NAVBAND_HI) & (x.d0 <= 3.0)
    rr, cc = np.nonzero(cand)
    if rr.size < k:
        raise SystemExit('not enough deep navigable vertices for the band control')
    sel = np.unique(np.linspace(0, rr.size - 1, k).round().astype(np.int64))
    r, c = rr[sel], cc[sel]
    H = x.H0.copy(); H[r, c] = (x.vpl[r, c] - 0.97).astype(np.float32)
    d1 = x.vpl[r, c] - H[r, c].astype(np.float64)
    if not ((d1 >= NAVBAND_LO) & (d1 < NAVBAND_HI)).all():
        raise SystemExit('band control did not land in the band')
    return H, dict(pushed=int(sel.size), base_band=x.nband0, allowed_increase=x.nband0 * NAVBAND_PCT // 100,
                   draft_after_min_max=[round(float(d1.min()), 4), round(float(d1.max()), 4)])


def nc3_navband_2pct(x):
    k = -(-2 * x.nband0 // 100)                       # ceil(2 % of the base band count)
    return navband_push(x, k)


def nc3_navband_2pct_of_nav(x):
    k = -(-2 * int(x.nav.sum()) // 100)               # ceil(2 % of all cls 3 vertices)
    return navband_push(x, k)


def pc3_navband_at_allowance(x):
    return navband_push(x, x.nband0 * NAVBAND_PCT // 100)


def steepen(x, nvert, slope_deg):
    """Raise isolated flat dry vertices by 6 tan(slope_deg); each touches 6 triangles (4 at slope_deg, 2 steeper)."""
    s0 = np.maximum(x.s0a, x.s0b)
    vmax = np.full((2048, 2048), np.inf)
    vmax[1:-1, 1:-1] = np.maximum.reduce([s0[:-1, :-1], s0[:-1, 1:], s0[1:, :-1], s0[1:, 1:]])
    drydist = distance_transform_edt(~x.wet0) * 6.0
    ok = (vmax < 1.0) & ~x.wet0 & (x.cls == 0) & (drydist >= 60.0) & ~binary_dilation(x.frozen, S8)
    grid = np.zeros_like(ok); grid[16:-16:16, 16:-16:16] = True
    rr, cc = np.nonzero(ok & grid)
    if rr.size < nvert:
        raise SystemExit('not enough flat dry vertices for the steep control')
    sel = np.unique(np.linspace(0, rr.size - 1, nvert).round().astype(np.int64))
    dh = 6.0 * math.tan(math.radians(slope_deg))
    H = x.H0.astype(np.float64).copy(); H[rr[sel], cc[sel]] += dh
    H = H.astype(np.float32)
    s1a, s1b = EV.tri_slopes(H)
    ia, ib = (s1a - x.s0a) > STEEP_INCR_DEG, (s1b - x.s0b) > STEEP_INCR_DEG
    n = int(ia.sum() + ib.sum())
    over = int((ia & (s1a > STEEP_CEIL_DEG)).sum() + (ib & (s1b > STEEP_CEIL_DEG)).sum())
    return H, dict(vertices=int(sel.size), raise_m=round(dh, 3), predicted_steepened=n, predicted_over35=over,
                   first_x_z=[6 * int(cc[sel[0]]), 6 * (2047 - int(rr[sel[0]]))])


def nc3_steepen_60(x):
    return steepen(x, 10, 23.75)


def pc3_steepen_48(x):
    return steepen(x, 8, 23.75)


def nc3_steep_over35(x):
    return steepen(x, 1, 40.0)


def nc_merge_bodies(x):
    """Drown a disk of cells on the Voronoi boundary between two base VTX water bodies >= 36 m2 (v2 has no merge
    control): the narrowest such gap with every disk cell uncovered and no frozen corner."""
    av = np.bincount(x.L0v.ravel(), minlength=x.n0v + 1)
    big = av >= H2.TOPO_MIN_PX; big[0] = False
    ow = x.owner
    dcell = x.dist0t.reshape(2047, K, 2047, K).min(axis=(1, 3))
    fcell = np.maximum.reduce([x.frozen[:-1, :-1], x.frozen[:-1, 1:], x.frozen[1:, :-1], x.frozen[1:, 1:]])
    okc = ~x.covered & ~fcell & (dcell >= 4.0) & (dcell <= 12.0)
    cand = np.zeros((2047, 2047), bool)
    for a, b, sa, sb in ((ow[:, :-1], ow[:, 1:], (slice(None), slice(None, -1)), (slice(None), slice(1, None))),
                         (ow[:-1, :], ow[1:, :], (slice(None, -1), slice(None)), (slice(1, None), slice(None)))):
        m = (a != b) & big[a] & big[b]
        cand[sa] |= m & okc[sa]
        cand[sb] |= m & okc[sb]
    rr, cc = np.nonzero(cand)
    vminp = vertex_min_plane(x)
    for i in np.argsort(dcell[rr, cc], kind='stable'):
        r, c = int(rr[i]), int(cc[i])
        R = int(math.ceil((dcell[r, c] + 12.0) / 6.0))
        r0, r1, c0, c1 = max(r - R, 0), min(r + R + 1, 2047), max(c - R, 0), min(c + R + 1, 2047)
        gr, gc = np.mgrid[r0:r1, c0:c1]
        disk = np.zeros((2047, 2047), bool); disk[r0:r1, c0:c1] = (gr - r) ** 2 + (gc - c) ** 2 <= R * R
        if x.covered[disk].any() or fcell[disk].any():
            continue
        H = x.H0.astype(np.float64).copy()
        drown(x, H, disk, vminp)
        nb = sorted({int(ow[r, c])} | {int(v_) for v_ in ow[disk]} - {0})
        return H.astype(np.float32), dict(cell=[r, c], x=6 * c + 3, z=6 * (2047 - r) - 3, gap_half_m=round(float(dcell[r, c]), 2),
                                          radius_cells=R, owners_in_disk=nb[:6], base_m2=[float(av[t] * 4) for t in nb[:6]])
    raise SystemExit('no gap for nc_merge_bodies')


def nc_v1_replay(x):
    b = np.load(H2.BASE_DEFAULT)['heights']; n = np.load(H2.V1NEG)['heights']
    idx = np.nonzero(n != b)
    H = x.H0.copy(); H[idx] = n[idx]
    return H, dict(vertices=[[int(r), int(c)] for r, c in zip(*idx)],
                   ev98=[round(float(v), 3) for v in b[idx]], ev99=[round(float(v), 3) for v in x.H0[idx]],
                   planted=[round(float(v), 3) for v in n[idx]])


def nc_v1_pond_bed(x):
    cand = x.pondv & (x.H0 < x.vpl) & (x.H0 >= 1.2) & (x.vpl > 1.0) & ~x.frozen
    rr, cc = np.nonzero(cand)
    r, c = int(rr[0]), int(cc[0])
    H = x.H0.copy(); H[r, c] = np.float32(0.9)
    return H, dict(vertex=[r, c], x=6 * c, z=6 * (2047 - r), plane=round(float(x.vpl[r, c]), 3),
                   h0=round(float(x.H0[r, c]), 3), h1=0.9)


# (name, builder, gates that must fire, gates that must stay 0, exact expectations on details_v3)
V3_CONTROLS = (
    ('nc3_drown_islet', nc3_drown_islet, ('island_lost', 'island_keep_lt80'), (), {}),
    ('nc3_shrink_island', nc3_shrink_island, ('island_keep_lt80',), ('island_lost',), {}),
    ('nc3_dry_nav', nc3_dry_nav, ('nav_dry',), (), {('nav_dry', 'turned_dry'): 1}),
    ('nc3_navband_2pct', nc3_navband_2pct, ('nav_band',), ('nav_dry',), {}),
    ('nc3_navband_2pct_of_nav', nc3_navband_2pct_of_nav, ('nav_band',), ('nav_dry',), {}),
    ('pc3_navband_at_allowance', pc3_navband_at_allowance, (), ('nav_band', 'nav_dry'), {}),
    ('nc3_steepen_60', nc3_steepen_60, ('steep_count',), ('steep_over35',), {('steep', 'steepened'): 60}),
    ('pc3_steepen_48', pc3_steepen_48, (), ('steep_count', 'steep_over35'), {('steep', 'steepened'): 48}),
    ('nc3_steep_over35', nc3_steep_over35, ('steep_over35',), ('steep_count',), {('steep', 'steepened'): 6}),
)


def strip_v2(r):
    r = json.loads(json.dumps(r))
    r.pop('runtime_s', None)
    r['details'].pop('v1_sidecar', None)
    return r


def selftest(outdir):
    t0 = time.time()
    os.makedirs(outdir, exist_ok=True)
    checks = []

    def ck(name, ok, got=None, exp=None):
        checks.append(dict(name=name, ok=bool(ok), got=got, exp=exp))

    for p, h in ((V1_PATH, V1_SHA256), (V2_PATH, V2_SHA256), (EV99_PATH, EV99_SHA256), (COVER_PATH, COVER_SHA256),
                 (EV99_V2_RUN, EV99_V2_RUN_SHA256), (H2.BASE_DEFAULT, H2.INPUT_SHA[H2.BASE_DEFAULT]),
                 (H2.V1NEG, H2.INPUT_SHA[H2.V1NEG])):
        g = sha256(p)
        ck(f'input_sha:{os.path.basename(p)}', g == h, g, h)
    x = base_context()
    runs = {}

    def run(key, path):
        r = evaluate(x, path, os.path.join(outdir, f'{key}.json'))
        runs[key] = r
        return r

    # 1. EV99 vs EV99
    r = run('base', EV99_PATH)
    g = r['gates_violations']
    ck('base:gate_set', tuple(g) == ALL_GATES, list(g), list(ALL_GATES))
    ck('base:all_gates_zero', all(v == 0 for v in g.values()), {k: v for k, v in g.items() if v})
    ck('base:all_groups_pass', all(r['gate_groups_pass'].values()), r['gate_groups_pass'])
    for m in ('engine_tri', 'quads'):
        ck(f'base:{m}_metrics_equal', r['v2']['metrics'][m]['base'] == r['v2']['metrics'][m]['cand'])
    v = r['v2']['metrics']['v1']
    ck('base:v1_metrics_equal', v['base_map'] == v['cand_map'] and v['base_spb'] == v['cand_spb'])
    ck('base:changed_vertices_zero', r['changed_vertices'] == 0, r['changed_vertices'])
    d = r['details_v3']
    got = [d['island']['lost'], d['island']['keep_lt80'], d['island']['min_keep_frac'], d['island']['joined_border_land'],
           d['island']['cand_islands_ge36'] - d['island']['base_islands_ge36'], d['nav_dry']['turned_dry'],
           d['nav_band']['increase'], d['nav_band']['entered'], d['nav_band']['left'], d['steep']['steepened'],
           d['steep']['max_increase_deg'], d['info_new_tri_water']['covered_m2'], d['info_new_tri_water']['uncovered_m2']]
    ck('base:v3_details_zero', got == [0, 0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0], got,
       [0, 0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0])
    ck('base:has_islands_and_band', d['island']['base_islands_ge36'] > 0 and d['nav_band']['base'] > 0,
       [d['island']['base_islands_ge36'], d['nav_band']['base']])
    # 2. the unchanged v2 file run standalone with --base EV99 gives the same report as the in-process run
    sa = os.path.join(outdir, 'v2-standalone-ev99.json')
    p = subprocess.run([sys.executable, '-I', '-B', V2_PATH, EV99_PATH, sa, '--base', EV99_PATH, '--cover', COVER_PATH],
                       capture_output=True, text=True)
    ck('v2_standalone:exit0', p.returncode == 0, p.returncode, 0)
    if p.returncode == 0:
        with open(sa) as fh:
            rs = json.load(fh)
        a, b = strip_v2(rs), strip_v2(r['v2'])
        diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
        ck('v2_standalone:report_equal', not diff, diff, [])
        with open(sa[:-5] + '.v1.json') as fh:
            v1a = json.load(fh)
        with open(r['v2']['details']['v1_sidecar']) as fh:
            v1b = json.load(fh)
        ck('v2_standalone:v1_sidecar_equal', v1a == v1b)
        ck('v2_standalone:harness_sha', rs['harness_sha256'] == V2_SHA256, rs['harness_sha256'], V2_SHA256)
    # 3. EV99 base metrics equal the candidate side of the round-2 integration run (EV98 -> EV99, same v2)
    with open(EV99_V2_RUN) as fh:
        ref = json.load(fh)
    ck('ev99_ref:harness_and_candidate', (ref['harness_sha256'], ref['candidate_sha256'], ref['cover_sha256']) ==
       (V2_SHA256, EV99_SHA256, COVER_SHA256), [ref['harness_sha256'], ref['candidate_sha256'], ref['cover_sha256']])
    for m in ('engine_tri', 'quads'):
        ck(f'ev99_ref:{m}_metrics', ref['metrics'][m]['cand'] == r['v2']['metrics'][m]['base'])
    vr = ref['metrics']['v1']
    ck('ev99_ref:v1_metrics', (vr['cand_map'], vr['cand_spb']) == (v['base_map'], v['base_spb']))
    sb = r['summary_base_cand']
    bad = [f'{k}.{m}' for k in sb for m in sb[k] if ref['summary_base_cand'][k][m][1] != sb[k][m][0]]
    ck('ev99_ref:summary', not bad, bad, [])
    ck('ev99_ref:navigable_vertices', ref['details']['nav']['navigable_vertices'] == d['nav_dry']['navigable_vertices'],
       d['nav_dry']['navigable_vertices'], ref['details']['nav']['navigable_vertices'])
    head = (sb['tri_spb_sea']['sawtooth_per_km'][0], sb['tri_spb_pond']['sawtooth_per_km'][0],
            sb['tri_spb_pond']['corners_per_km'][0])
    ck('ev99_ref:headline_spb_sea_saw_pond_saw_pond_corners', head == (3.47, 13.972, 12.14), head, (3.47, 13.972, 12.14))
    # 4. v3 controls
    fired_any = {k: 0 for k in ALL_GATES}
    ncs = {}

    def plant(name, builder):
        H, info = builder(x)
        pth = os.path.join(outdir, f'{name}.npz')
        np.savez(pth, heights=H)
        rr_ = run(name, pth)
        fired = {k: v_ for k, v_ in rr_['gates_violations'].items() if v_}
        if not name.startswith('pc'):            # threshold (positive) controls do not count as negative controls
            for k_ in fired:
                fired_any[k_] += 1
        return rr_, info, fired

    for name, builder, must, zero, exact in V3_CONTROLS:
        rr_, info, fired = plant(name, builder)
        gv = rr_['gates_violations']
        ok = all(gv[k_] > 0 for k_ in must) and all(gv[k_] == 0 for k_ in zero)
        ok = ok and all(rr_['details_v3'][a_][b_] == e_ for (a_, b_), e_ in exact.items())
        if name.startswith('nc'):
            groups_failed = sorted({gname for gname, ks in V3_GROUPS.items() if any(k_ in must for k_ in ks)})
            ok = ok and not rr_['gates_pass'] and all(not rr_['gate_groups_pass'][gname] for gname in groups_failed)
        if name.startswith('nc3_navband') or name.startswith('pc3_navband'):
            ok = ok and rr_['details_v3']['nav_band']['increase'] == info['pushed']
        if 'steep' in name:
            ok = ok and rr_['details_v3']['steep']['steepened'] == info['predicted_steepened']
        got = dict(must={k_: gv[k_] for k_ in must}, zero={k_: gv[k_] for k_ in zero},
                   exact={f'{a_}.{b_}': rr_['details_v3'][a_][b_] for (a_, b_) in exact})
        ck(f'control:{name}', ok, got, dict(must='> 0', zero='== 0', exact={f'{a_}.{b_}': e_ for (a_, b_), e_ in exact.items()}))
        ncs[name] = dict(info=info, must_fire=list(must), must_stay_zero=list(zero), fired=fired,
                         details_v3={k_: rr_['details_v3'][k_] for k_ in ('island', 'nav_dry', 'nav_band', 'steep')})
    # 5. v2 negative controls re-planted on EV99, v1 negative control replayed on EV99, v1 pond_bed control
    for name, builder, targets in H2.NEG_CONTROLS:
        rr_, info, fired = plant('v2_' + name, builder)
        ok = all(rr_['gates_violations'][k_] > 0 for k_ in targets)
        ck(f'control:v2_{name}', ok, {k_: rr_['gates_violations'][k_] for k_ in targets}, '> 0')
        ncs['v2_' + name] = dict(info=info, must_fire=list(targets), fired=fired)
    exp_v1 = tuple(k_ for k_, v_ in H2.EXP_V1NEG.items() if v_)
    for name, builder, targets in (('nc_v1_replay', nc_v1_replay, exp_v1), ('nc_v1_pond_bed', nc_v1_pond_bed, ('pond_bed',)),
                                   ('nc_merge_bodies', nc_merge_bodies, ('topo_vtx_merge', 'topo_tri_merge'))):
        rr_, info, fired = plant(name, builder)
        ok = all(rr_['gates_violations'][k_] > 0 for k_ in targets)
        ck(f'control:{name}', ok, {k_: rr_['gates_violations'][k_] for k_ in targets}, '> 0')
        ncs[name] = dict(info=info, must_fire=list(targets), fired=fired)
    never = [k_ for k_, n_ in fired_any.items() if n_ == 0]
    ck('coverage:every_gate_fires_in_some_negative_control', not never, never, [])
    passed = all(c_['ok'] for c_ in checks)
    keep = ('gates_violations', 'gates_pass', 'gate_groups_pass', 'runtime_s')
    base_metrics = dict(engine_tri=r['v2']['metrics']['engine_tri']['base'], quads=r['v2']['metrics']['quads']['base'],
                        v1=dict(map=v['base_map'], spb=v['base_spb']),
                        islands=dict(ge36=d['island']['base_islands_ge36'], all=d['island']['base_islands_all']),
                        nav=dict(navigable=d['nav_dry']['navigable_vertices'], navigable_wet=d['nav_dry']['navigable_wet_base'],
                                 band_0p95_1p0=d['nav_band']['base'], allowed_increase=d['nav_band']['allowed_increase']),
                        area_total_m2=r['v2']['details']['area']['base_total_m2'],
                        topo=dict(tri_bodies=r['v2']['details']['topo_tri']['base_n'],
                                  vtx_bodies=r['v2']['details']['topo_vtx']['base_n']))
    out = dict(schema='shore-eval.v3.selftest', harness=os.path.abspath(__file__).replace('\\', '/'),
               harness_sha256=sha256(__file__), v2_sha256=V2_SHA256, v1_sha256=V1_SHA256,
               base=EV99_PATH, base_sha256=EV99_SHA256, cover=COVER_PATH, cover_sha256=COVER_SHA256,
               selftest_pass=passed, n_checks=len(checks), n_failed=sum(not c_['ok'] for c_ in checks),
               checks=checks, ev99_base_metrics=base_metrics, gate_fire_counts=fired_any, controls=ncs,
               runs={k_: {kk: v_[kk] for kk in keep} for k_, v_ in runs.items()}, runtime_s=round(time.time() - t0, 1))
    with open(os.path.join(outdir, 'selftest.json'), 'w') as fh:
        fh.write(json.dumps(out, indent=1))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('candidate', nargs='?'); ap.add_argument('out', nargs='?')
    ap.add_argument('--selftest', metavar='OUTDIR')
    a = ap.parse_args()
    if a.selftest:
        res = selftest(a.selftest)
        print(json.dumps({k: res[k] for k in ('selftest_pass', 'n_checks', 'n_failed', 'runtime_s')}))
        print(json.dumps([c for c in res['checks'] if not c['ok']], indent=1))
        sys.exit(0 if res['selftest_pass'] else 1)
    if not (a.candidate and a.out):
        ap.error('candidate and out are required')
    x = base_context()
    res = evaluate(x, a.candidate, a.out)
    print(json.dumps({k: res[k] for k in ('gates_violations', 'gates_pass', 'gate_groups_pass', 'runtime_s')}, indent=1))


if __name__ == '__main__':
    main()

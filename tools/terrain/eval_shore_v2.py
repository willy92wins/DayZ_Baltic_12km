"""Shoreline evaluation harness v2 for EV98 candidates. Frozen: record its sha256 and never edit it afterwards.

Usage:
  python -I eval_shore_v2.py <candidate.npz> <out.json> [--base terrain-ev98.npz] [--cover cover-level-ev98.npy]
  python -I eval_shore_v2.py --selftest <outdir>

v1 (eval_shore.py, sha256 343f5716...) is imported read-only and its main() runs unchanged on the same inputs, so its
six gates (frozen, band, pond_bed, piece_edge, new_sea, slope) keep their code and thresholds; its JSON is kept as the
sidecar <out>.v1.json and copied into this report. v2 refuses to run if the v1 file hash differs.

Water models. Cell plane = cover level where the cell has a pond piece, else engine sea 0.75 m; native NW-SE diagonal.
  TRI    engine triangles, K=3 cell-centred samples per cell (2 m pixels), water 4-connected (judge_checks.fine_f).
  VTX    vertex-aligned K=3 samples at cell fractions 0, 1/3, 2/3, water 8-connected (judge_vtx.wet).
  EXACT  analytic wet area of every native triangle (judge_exact_area). Area bodies are the VTX base bodies; each
         cell's exact area goes to the base body owning its (1/3, 1/3) sample by nearest base-wet pixel (Voronoi).
  QUADS  v1 vertex model, f = H - vertex plane (NaN -> 0.75), bilinear contour (secondary metric only).

New gates (violation counts, 0 = pass; units: bodies for area/topo, 2 m TRI pixels for flood, vertices for nav;
groups G_area, G_topo, G_flood, G_nav in gate_groups_pass):
  area_large           bodies with base exact area >= 2000 m2 whose exact area changes by more than 5 %.
  area_mid             bodies 200-2000 m2 changing by more than 10 %, beyond floor(2 % of their number).
  area_total           1 when the total exact wet area changes by 0.5 % or more.
  topo_{vtx,tri}_lost  base bodies >= 36 m2 (9 px) with no wet overlap in the candidate.
  topo_{vtx,tri}_split base bodies >= 36 m2 that overlap two or more candidate bodies >= 36 m2.
  topo_{vtx,tri}_merge candidate bodies >= 36 m2 that overlap two or more base bodies >= 36 m2.
  flood                TRI pixels wet in the candidate, dry in the base and more than 8 m from base TRI water.
  nav_shallow          cls 3 (navigable) vertices with draft (plane - H) < 0.95 m in the candidate but not in the base.
  nav_channel_raised   cls 3 vertices wet in the base and >= 12 m from the nearest base-dry vertex whose height rises.
Metrics, base and candidate, map and St Petersburg window (v1 SPB), TRI primary and QUADS secondary: length;
sawtooth = local maxima of turning over 12 m above 60 deg per km; corners = the same over 30 m above 45 deg; split
SEA / POND by the plane under each point (TRI: the cell's cover; QUADS: the nearest vertex's plane); grid_aligned_frac =
share of 6 m chords (two 3 m resampling steps) whose direction lies within 5 deg of 0/45/90/135 deg.
Self-test (--selftest): input hashes; base vs base all zero with equal metrics; judge numbers for base/sdf/fair within
1 %; v1 numbers and the v1 negative control reproduced; planted negative controls for every new gate must fail.
"""
import argparse, contextlib, hashlib, importlib.util, io, json, os, sys, time
sys.dont_write_bytecode = True
from types import SimpleNamespace
import numpy as np
from scipy.ndimage import label, distance_transform_edt, binary_dilation, maximum_filter1d, find_objects
import contourpy

ROOT = 'E:/DayZ-Baltic-Build/v30-shore-sdf-20261011'
V1_PATH = ROOT + '/eval_shore.py'
V1_SHA256 = '343f5716aeba0c8eb4e48497c71b8df07f32d058bacf53a65e6b46383f69922e'
V1_GATES = ('frozen', 'band', 'pond_bed', 'piece_edge', 'new_sea', 'slope')
BASE_DEFAULT = 'E:/DayZ-Baltic-Build/v30-pond-sea-separation-20261011-b/terrain-ev98.npz'
COVER_DEFAULT = ROOT + '/cover-level-ev98.npy'

K = 3
PX = 6.0 / K                      # 2 m raster pixels
N_VTX = K * 2047 + 1
S4 = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
S8 = np.ones((3, 3), int)
AREA_LARGE_M2, AREA_LARGE_TOL = 2000.0, 0.05
AREA_MID_LO, AREA_MID_HI, AREA_MID_TOL, AREA_MID_SHARE = 200.0, 2000.0, 0.10, 0.02
AREA_TOTAL_TOL = 0.005
TOPO_MIN_PX = 9                   # 36 m2
FLOOD_M = 8.0
NAV_CLS, NAV_DRAFT_M, NAV_CHANNEL_M = 3, 0.95, 12.0
SAW, CORNER = (12.0, 60.0), (30.0, 45.0)
MIN_LINE_M, STEP_M = 40.0, 3.0
ALIGN_STEPS, ALIGN_TOL_DEG = 2, 5.0
GROUPS = ('all', 'sea', 'pond')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for ch in iter(lambda: fh.read(1 << 20), b''):
            h.update(ch)
    return h.hexdigest()


def load_v1():
    got = sha256(V1_PATH)
    if got != V1_SHA256:
        raise SystemExit(f'v1 harness hash mismatch ({got} != {V1_SHA256}); refusing to run')
    spec = importlib.util.spec_from_file_location('eval_shore_v1_ro', V1_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


EV = load_v1()


def run_v1(cand_path, side_out, base_path, cover_path):
    argv = sys.argv
    sys.argv = ['eval_shore.py', cand_path, side_out, '--base', base_path, '--cover', cover_path]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            EV.main()
    finally:
        sys.argv = argv
    with open(side_out) as fh:
        res = json.load(fh)
    if tuple(res['gates_violations']) != V1_GATES:
        raise SystemExit('v1 gate set differs from the frozen six gates')
    return res


# ---------------------------------------------------------------- water rasters (copied from the judge scripts)
def tri_field(H, cellplane):
    """TRI: K x K cell-centred samples on the NW-SE triangles minus the cell plane (judge_checks.fine_f)."""
    H = H.astype(np.float32)
    nw, ne, sw, se = H[:-1, :-1], H[:-1, 1:], H[1:, :-1], H[1:, 1:]
    out = np.empty((2047 * K, 2047 * K), np.float32)
    for i in range(K):
        v = (i + 0.5) / K
        for j in range(K):
            u = (j + 0.5) / K
            if u >= v:
                h = nw + u * (ne - nw) + v * (se - ne)
            else:
                h = nw + v * (sw - nw) + u * (se - sw)
            out[i::K, j::K] = h - cellplane
    return out


_I = np.arange(N_VTX)
CELL = np.minimum(_I // K, 2046)
FRAC = _I / K - CELL


def vtx_wet(H, cellplane):
    """VTX: vertex-aligned K=3 samples (judge_vtx.wet)."""
    H = H.astype(np.float32); out = np.empty((N_VTX, N_VTX), bool); u = FRAC[None, :].astype(np.float32); c = CELL
    for i0 in range(0, N_VTX, 512):
        i1 = min(N_VTX, i0 + 512); r = CELL[i0:i1]; v = FRAC[i0:i1][:, None].astype(np.float32)
        nw = H[r][:, c]; ne = H[r][:, c + 1]; sw = H[r + 1][:, c]; se = H[r + 1][:, c + 1]
        z = np.where(u >= v, nw + u * (ne - nw) + v * (se - ne), nw + v * (sw - nw) + u * (se - sw))
        out[i0:i1] = z < cellplane[np.ix_(r, c)]
    return out


def tri_wet_frac(a, b, c):
    """Fraction of a triangle where the linear function with corner values a, b, c is < 0 (judge_exact_area)."""
    n = (a < 0).astype(np.int8) + (b < 0) + (c < 0)
    out = np.zeros(a.shape, np.float64)
    out[n == 3] = 1.0
    with np.errstate(divide='ignore', invalid='ignore'):
        for p, q, r in ((a, b, c), (b, a, c), (c, a, b)):
            m1 = (n == 1) & (p < 0)
            out[m1] = (p[m1] ** 2) / ((p[m1] - q[m1]) * (p[m1] - r[m1]))
            m2 = (n == 2) & (p >= 0)
            out[m2] = 1.0 - (p[m2] ** 2) / ((p[m2] - q[m2]) * (p[m2] - r[m2]))
    return np.clip(np.nan_to_num(out), 0, 1)


def cell_wet_m2(H, cp):
    H = H.astype(np.float64)
    nw, ne, sw, se = H[:-1, :-1] - cp, H[:-1, 1:] - cp, H[1:, :-1] - cp, H[1:, 1:] - cp
    return 18.0 * (tri_wet_frac(nw, ne, se) + tri_wet_frac(nw, se, sw))


def tri_xz(i, j):
    return PX * (np.asarray(j) + 0.5), 6.0 * 2047 - PX * (np.asarray(i) + 0.5)


def vtx_xz(i, j):
    return PX * np.asarray(j), 6.0 * 2047 - PX * np.asarray(i)


# ---------------------------------------------------------------- shoreline metrics
def tri_lines(F):
    gen = contourpy.contour_generator(z=F, name='serial', line_type=contourpy.LineType.Separate)
    return [(PX * (c[:, 0] + 0.5), 6.0 * 2047 - PX * (c[:, 1] + 0.5)) for c in gen.lines(0.0)]


def quad_lines(f):
    gen = contourpy.contour_generator(z=f.astype(np.float64), name='serial', line_type=contourpy.LineType.Separate)
    return [(c[:, 0] * 6.0, (2047 - c[:, 1]) * 6.0) for c in gen.lines(0.0)]


def pond_by_cell(covered):
    def f(x, z):
        c = np.clip(np.floor(x / 6.0).astype(np.int64), 0, 2046)
        r = np.clip(np.floor((6.0 * 2047 - z) / 6.0).astype(np.int64), 0, 2046)
        return covered[r, c]
    return f


def pond_by_vertex(pondv):
    def f(x, z):
        c = np.clip(np.rint(x / 6.0).astype(np.int64), 0, 2047)
        r = np.clip(np.rint(2047 - z / 6.0).astype(np.int64), 0, 2047)
        return pondv[r, c]
    return f


def line_metrics(lines, is_pond, window=None):
    """v1 waterline_metrics logic on world polylines (same clipping, 40 m floor, 3 m resampling, thresholds), with each
    peak, segment and chord attributed to SEA or POND, plus grid alignment of 6 m chords."""
    acc = {g: dict(length_km=0.0, sawtooth=0, corners=0, chords=0, aligned=0) for g in GROUPS}
    short_n, short_len = 0, 0.0
    for x, z in lines:
        if window is not None:
            x0, x1, z0, z1 = window
            keep = (x >= x0) & (x <= x1) & (z >= z0) & (z <= z1)
            if keep.sum() < 4:
                continue
            x, z = x[keep], z[keep]
        seg = np.hypot(np.diff(x), np.diff(z))
        s = np.r_[0, np.cumsum(seg)]
        if s[-1] < MIN_LINE_M:
            short_n += 1; short_len += s[-1] / 1000
            continue
        t = np.arange(0, s[-1], STEP_M)
        xi, zi = np.interp(t, s, x), np.interp(t, s, z)
        acc['all']['length_km'] += s[-1] / 1000
        segp = is_pond(0.5 * (x[:-1] + x[1:]), 0.5 * (z[:-1] + z[1:]))
        acc['pond']['length_km'] += float(seg[segp].sum()) / 1000
        acc['sea']['length_km'] += float(seg[~segp].sum()) / 1000
        pp = is_pond(xi, zi)
        for (w, thr), key in ((SAW, 'sawtooth'), (CORNER, 'corners')):
            k = int(round(w / 2 / STEP_M))
            if len(t) <= 2 * k + 1:
                continue
            d1 = np.arctan2(zi[k:-k] - zi[:-2 * k], xi[k:-k] - xi[:-2 * k])
            d2 = np.arctan2(zi[2 * k:] - zi[k:-k], xi[2 * k:] - xi[k:-k])
            turn = np.degrees(np.abs(np.angle(np.exp(1j * (d2 - d1)))))
            peak = (turn == maximum_filter1d(turn, 2 * k + 1)) & (turn > thr)
            n = int(peak.sum()); npond = int((peak & pp[k:-k]).sum())
            acc['all'][key] += n; acc['pond'][key] += npond; acc['sea'][key] += n - npond
        m = ALIGN_STEPS
        if len(t) > m:
            ang = np.degrees(np.arctan2(zi[m:] - zi[:-m], xi[m:] - xi[:-m])) % 45.0
            al = np.minimum(ang, 45.0 - ang) <= ALIGN_TOL_DEG
            cpond = pp[m // 2:m // 2 + al.size]
            na, nap = int(al.sum()), int((al & cpond).sum()); nc, ncp = int(al.size), int(cpond.sum())
            acc['all']['chords'] += nc; acc['all']['aligned'] += na
            acc['pond']['chords'] += ncp; acc['pond']['aligned'] += nap
            acc['sea']['chords'] += nc - ncp; acc['sea']['aligned'] += na - nap
    out = {}
    for g in GROUPS:
        a = acc[g]; L = max(a['length_km'], 1e-9)
        out[g] = dict(length_km=round(a['length_km'], 3), sawtooth=a['sawtooth'], corners=a['corners'],
                      sawtooth_per_km=round(a['sawtooth'] / L, 3), corners_per_km=round(a['corners'] / L, 3),
                      chords=a['chords'], grid_aligned_frac=round(a['aligned'] / max(a['chords'], 1), 4))
    out['all'].update(short_lines=short_n, short_len_km=round(short_len, 3))
    return out


def window_metrics(lines, is_pond):
    return dict(map=line_metrics(lines, is_pond), spb=line_metrics(lines, is_pond, EV.SPB))


# ---------------------------------------------------------------- topology (judge_checks.topo + offender ids)
def topo(L0, n0, L1, n1, W0, W1, minpx):
    both = W0 & W1
    a, b = L0[both], L1[both]
    code = np.unique(a.astype(np.int64) * (int(n1) + 1) + b.astype(np.int64)) if a.size else np.zeros(0, np.int64)
    pairs = np.stack([code // (int(n1) + 1), code % (int(n1) + 1)]).T
    area0 = np.bincount(L0.ravel(), minlength=n0 + 1); area1 = np.bincount(L1.ravel(), minlength=n1 + 1)
    has0 = np.zeros(n0 + 1, bool); has0[pairs[:, 0]] = True
    has1 = np.zeros(n1 + 1, bool); has1[pairs[:, 1]] = True
    nper0 = np.bincount(pairs[:, 0], minlength=n0 + 1)
    nper1 = np.bincount(pairs[:, 1], minlength=n1 + 1)
    big1 = area1 >= minpx; big0 = area0 >= minpx
    sigp = pairs[big1[pairs[:, 1]] & big0[pairs[:, 0]]]
    snper0 = np.bincount(sigp[:, 0], minlength=n0 + 1); snper1 = np.bincount(sigp[:, 1], minlength=n1 + 1)
    lost = np.where(~has0[1:])[0] + 1
    new = np.where(~has1[1:])[0] + 1
    pa = PX * PX
    res = dict(base_n=int(n0), cand_n=int(n1),
               lost=int(lost.size), lost_area_m2=float(area0[lost].sum() * pa) if lost.size else 0.0,
               lost_ge_minpx=int((area0[lost] >= minpx).sum()), lost_max_m2=float(area0[lost].max() * pa) if lost.size else 0.0,
               new=int(new.size), new_area_m2=float(area1[new].sum() * pa) if new.size else 0.0,
               new_ge_minpx=int((area1[new] >= minpx).sum()), new_max_m2=float(area1[new].max() * pa) if new.size else 0.0,
               split=int((nper0[1:] >= 2).sum()), split_sig=int((snper0[1:] >= 2).sum()),
               merged=int((nper1[1:] >= 2).sum()), merged_sig=int((snper1[1:] >= 2).sum()))
    ids = dict(lost=lost[area0[lost] >= minpx], split=np.where(snper0[1:] >= 2)[0] + 1,
               merge=np.where(snper1[1:] >= 2)[0] + 1)
    return res, ids, area0, area1


def locate(L, ids, area, to_xz, maxn=8, largest_first=True):
    """[x, z, area_m2] of the bounding-box centre of up to maxn labels (largest first unless told to keep order)."""
    if len(ids) == 0:
        return []
    ids = np.asarray(ids)
    if largest_first:
        ids = ids[np.argsort(-area[ids], kind='stable')]
    ids = ids[:maxn]
    objs = find_objects(L, max_label=int(ids.max()))
    out = []
    for t in ids:
        sl = objs[t - 1]
        x, z = to_xz(0.5 * (sl[0].start + sl[0].stop - 1), 0.5 * (sl[1].start + sl[1].stop - 1))
        out.append([round(float(x)), round(float(z)), float(area[t] * PX * PX)])
    return out


# ---------------------------------------------------------------- base context
def base_context(base_path, cover_path):
    t0 = time.time()
    b = np.load(base_path)
    H0 = b['heights']
    if H0.shape != (2048, 2048):
        raise SystemExit('base heights must be 2048x2048')
    cover = np.load(cover_path)
    x = SimpleNamespace(base_path=base_path, cover_path=cover_path, H0=H0, cls=b['cls'],
                        frozen=b['reserve'] | b['platform'], cover=cover)
    x.base_arrays = {k: b[k] for k in b.files if k != 'heights'}
    x.covered = np.isfinite(cover)
    vp = EV.vertex_plane(cover)
    x.pondv = np.isfinite(vp)
    x.vpl = np.where(x.pondv, vp, EV.SEA)
    x.cp64 = np.where(x.covered, cover, EV.SEA).astype(np.float64)
    x.cp32 = x.cp64.astype(np.float32)
    x.pond_cell, x.pond_vertex = pond_by_cell(x.covered), pond_by_vertex(x.pondv)
    # TRI
    F0 = tri_field(H0, x.cp32)
    x.W0t = F0 < 0
    x.mt = window_metrics(tri_lines(F0), x.pond_cell)
    del F0
    x.L0t, x.n0t = label(x.W0t, S4)
    x.dist0t = distance_transform_edt(~x.W0t) * PX
    # VTX + EXACT ownership
    x.W0v = vtx_wet(H0, x.cp32)
    x.L0v, x.n0v = label(x.W0v, S8)
    idx = distance_transform_edt(~x.W0v, return_distances=False, return_indices=True)
    ci = K * np.arange(2047) + 1
    x.owner = x.L0v[idx[0][np.ix_(ci, ci)], idx[1][np.ix_(ci, ci)]]
    del idx
    x.A0c = cell_wet_m2(H0, x.cp64)
    x.a0 = np.bincount(x.owner.ravel(), weights=x.A0c.ravel(), minlength=x.n0v + 1)
    # QUADS / vertex model
    x.f0 = H0.astype(np.float64) - x.vpl
    x.wet0 = x.f0 < 0
    x.mq = window_metrics(quad_lines(x.f0), x.pond_vertex)
    # NAV
    x.nav = x.cls == NAV_CLS
    x.bankdist = distance_transform_edt(x.wet0) * 6.0
    x.channel = x.nav & x.wet0 & (x.bankdist >= NAV_CHANNEL_M)
    x.base_sha256, x.cover_sha256 = sha256(base_path), sha256(cover_path)
    x.runtime_s = round(time.time() - t0, 1)
    return x


# ---------------------------------------------------------------- evaluation
def area_classes(a0, rel):
    out = {}
    for lo, hi, name in ((36, 200, '36-200m2'), (200, 2000, '200-2000m2'), (2000, 10000, '2000-10000m2'),
                         (10000, 1e12, 'ge10000m2')):
        m = (a0 >= lo) & (a0 < hi); m[0] = False
        out[name] = dict(n=int(m.sum()), over5=int((m & (np.abs(rel) > 0.05)).sum()),
                         over10=int((m & (np.abs(rel) > 0.10)).sum()),
                         p50_abs_pct=round(float(np.median(np.abs(rel[m]))) * 100, 2) if m.any() else None,
                         worst=round(float(rel[m][np.argmax(np.abs(rel[m]))]) * 100, 2) if m.any() else None)
    return out


def evaluate(x, cand_path, out_path):
    t0 = time.time()
    side = (out_path[:-5] if out_path.endswith('.json') else out_path) + '.v1.json'
    v1 = run_v1(cand_path, side, x.base_path, x.cover_path)
    c = np.load(cand_path)
    H1 = c['heights']
    if H1.shape != (2048, 2048) or not np.isfinite(H1).all():
        raise SystemExit('candidate heights must be finite 2048x2048')
    others = {}
    for k, A in x.base_arrays.items():
        others[k] = bool(k in c.files and c[k].dtype == A.dtype and c[k].shape == A.shape
                         and np.array_equal(A, c[k], equal_nan=A.dtype.kind == 'f'))
    dH = H1.astype(np.float64) - x.H0.astype(np.float64)
    gates = dict(v1['gates_violations'])
    det = dict(v1_sidecar=side, v1_gates_pass=bool(v1['gates_pass']), candidate_heights_dtype=str(H1.dtype),
               non_height_arrays_identical=others)

    # TRI: topology, flood, metrics
    F1 = tri_field(H1, x.cp32)
    W1t = F1 < 0
    mt1 = window_metrics(tri_lines(F1), x.pond_cell)
    del F1
    L1t, n1t = label(W1t, S4)
    tt, ids, ar0, ar1 = topo(x.L0t, x.n0t, L1t, n1t, x.W0t, W1t, TOPO_MIN_PX)
    tt['lost_sig_x_z_m2'] = locate(x.L0t, ids['lost'], ar0, tri_xz)
    tt['split_sig_x_z_m2'] = locate(x.L0t, ids['split'], ar0, tri_xz)
    tt['merge_sig_x_z_m2'] = locate(L1t, ids['merge'], ar1, tri_xz)
    det['topo_tri'] = tt
    del L1t
    newwet = W1t & ~x.W0t
    nd = x.dist0t[newwet]
    far = newwet & (x.dist0t > FLOOD_M)
    pa = PX * PX
    fl = dict(new_wet_m2=float(nd.size * pa), new_dry_m2=float((x.W0t & ~W1t).sum() * pa),
              **{f'new_wet_gt{d}_m2': float((nd > d).sum() * pa) for d in (4, 6, 8, 12, 24)},
              new_wet_max_dist_m=round(float(nd.max()), 1) if nd.size else 0.0, far_clusters_x_z_m2=[])
    if far.any():
        Lf, nf = label(far, S8)
        sz = np.bincount(Lf.ravel())
        fl['far_clusters_x_z_m2'] = locate(Lf, np.arange(1, nf + 1), sz, tri_xz, 5)
        del Lf
    det['flood'] = fl
    gates_new = {}
    del W1t, newwet, far

    # VTX topology
    W1v = vtx_wet(H1, x.cp32)
    L1v, n1v = label(W1v, S8)
    tv, idv, av0, av1 = topo(x.L0v, x.n0v, L1v, n1v, x.W0v, W1v, TOPO_MIN_PX)
    tv['lost_sig_x_z_m2'] = locate(x.L0v, idv['lost'], av0, vtx_xz)
    tv['split_sig_x_z_m2'] = locate(x.L0v, idv['split'], av0, vtx_xz)
    tv['merge_sig_x_z_m2'] = locate(L1v, idv['merge'], av1, vtx_xz)
    det['topo_vtx'] = tv
    del W1v, L1v

    # EXACT area per base body
    A1c = cell_wet_m2(H1, x.cp64)
    a1 = np.bincount(x.owner.ravel(), weights=A1c.ravel(), minlength=x.n0v + 1)
    a0 = x.a0
    rel = (a1 - a0) / np.maximum(a0, 1e-9)
    tot0, tot1 = float(x.A0c.sum()), float(A1c.sum())
    trel = (tot1 - tot0) / tot0
    large = (a0 >= AREA_LARGE_M2); large[0] = False
    mid = (a0 >= AREA_MID_LO) & (a0 < AREA_MID_HI); mid[0] = False
    mid_over = int((mid & (np.abs(rel) > AREA_MID_TOL)).sum())
    mid_allow = int(np.floor(AREA_MID_SHARE * mid.sum()))
    offl = np.where(large & (np.abs(rel) > AREA_LARGE_TOL))[0]
    offm = np.where(mid & (np.abs(rel) > AREA_MID_TOL))[0]
    def body_list(ids_):
        ids_ = ids_[np.argsort(-np.abs(rel[ids_]))][:8]
        loc = locate(x.L0v, ids_, np.ones(x.n0v + 1), vtx_xz, len(ids_), largest_first=False) if len(ids_) else []
        return [[l[0], l[1], round(float(a0[t]), 1), round(float(rel[t]) * 100, 2)] for l, t in zip(loc, ids_)]
    det['area'] = dict(base_total_m2=round(tot0, 1), cand_total_m2=round(tot1, 1), total_rel_pct=round(trel * 100, 4),
                       base_bodies=int(x.n0v), classes=area_classes(a0, rel),
                       large_n=int(large.sum()), large_over5=int(offl.size),
                       mid_n=int(mid.sum()), mid_over10=mid_over, mid_allowed=mid_allow,
                       large_offenders_x_z_basem2_relpct=body_list(offl),
                       mid_offenders_x_z_basem2_relpct=body_list(offm))
    gates_new['area_large'] = int(offl.size)
    gates_new['area_mid'] = max(0, mid_over - mid_allow)
    gates_new['area_total'] = int(abs(trel) >= AREA_TOTAL_TOL)
    for kind, t in (('vtx', tv), ('tri', tt)):
        gates_new[f'topo_{kind}_lost'] = t['lost_ge_minpx']
        gates_new[f'topo_{kind}_split'] = t['split_sig']
        gates_new[f'topo_{kind}_merge'] = t['merged_sig']
    gates_new['flood'] = int(round(fl['new_wet_gt8_m2'] / pa))

    # NAV
    f1 = H1.astype(np.float64) - x.vpl
    d0, d1 = -x.f0, -f1
    shallow = x.nav & (d1 < NAV_DRAFT_M) & ~(d0 < NAV_DRAFT_M)
    raised = x.channel & (dH > 0)
    navw = x.nav & x.wet0
    det['nav'] = dict(navigable_vertices=int(x.nav.sum()), navigable_wet_vertices=int(navw.sum()),
                      channel_vertices=int(x.channel.sum()), new_shallow=int(shallow.sum()),
                      new_shallow_by_bank_dist_m={'le6': int((shallow & (x.bankdist <= 6)).sum()),
                                                  '6-12': int((shallow & (x.bankdist > 6) & (x.bankdist < 12)).sum()),
                                                  'ge12': int((shallow & (x.bankdist >= 12)).sum())},
                      new_shallow_now_dry=int((shallow & (d1 <= 0)).sum()),
                      channel_raised=int(raised.sum()),
                      channel_raised_gt_1cm=int((raised & (dH > 0.01)).sum()),
                      channel_max_raise_m=round(float(dH[x.channel].max()), 4) if x.channel.any() else 0.0,
                      depth_lost_below_1p5=int((navw & (d0 >= 1.5) & (d1 < 1.5)).sum()))
    gates_new['nav_shallow'] = int(shallow.sum())
    gates_new['nav_channel_raised'] = int(raised.sum())
    gates.update(gates_new)

    # QUADS metrics and consistency with v1
    mq1 = window_metrics(quad_lines(f1), x.pond_vertex)
    vm = v1['metrics']
    match = all(all(vm[f'{side_}_{win}'][k] == mq[win]['all'][k] for k in ('length_km', 'sawtooth', 'corners'))
                for side_, mq in (('base', x.mq), ('cand', mq1)) for win in ('map', 'spb'))
    groups = dict(v1=all(gates[k] == 0 for k in V1_GATES),
                  G_area=all(gates[k] == 0 for k in ('area_large', 'area_mid', 'area_total')),
                  G_topo=all(gates[k] == 0 for k in gates if k.startswith('topo_')),
                  G_flood=gates['flood'] == 0,
                  G_nav=gates['nav_shallow'] == 0 and gates['nav_channel_raised'] == 0)
    summary = {}
    for model, mb, mc in (('tri', x.mt, mt1), ('quads', x.mq, mq1)):
        for win in ('map', 'spb'):
            for g in GROUPS:
                summary[f'{model}_{win}_{g}'] = {k: [mb[win][g][k], mc[win][g][k]] for k in
                                                 ('length_km', 'sawtooth_per_km', 'corners_per_km', 'grid_aligned_frac')}
    res = dict(schema='shore-eval.v2', harness=os.path.abspath(__file__).replace('\\', '/'),
               harness_sha256=sha256(__file__), v1_sha256=V1_SHA256,
               candidate=cand_path, candidate_sha256=sha256(cand_path),
               base=x.base_path, base_sha256=x.base_sha256, cover=x.cover_path, cover_sha256=x.cover_sha256,
               gates_violations=gates, gates_pass=all(v == 0 for v in gates.values()), gate_groups_pass=groups,
               changed_vertices=int((dH != 0).sum()), max_abs_change_m=round(float(np.abs(dH).max()), 3),
               details=det,
               metrics=dict(engine_tri=dict(model='TRI K=3 cell-centred, primary', base=x.mt, cand=mt1),
                            quads=dict(model='v1 vertex quads, secondary', base=x.mq, cand=mq1),
                            quads_all_match_v1=bool(match), v1=vm),
               summary_base_cand=summary,
               runtime_s=dict(base_context=x.runtime_s, candidate=round(time.time() - t0, 1)))
    with open(out_path, 'w') as fh:
        fh.write(json.dumps(res, indent=1))
    return res


# ---------------------------------------------------------------- self-test
SDF = ROOT + '/sdf/cand-sdf-it8.npz'
FAIR = ROOT + '/fair/fair-cand2.npz'
HYBRID = ROOT + '/hybrid/cand-hybrid-1.npz'
V1NEG = ROOT + '/negative-control.npz'
INPUT_SHA = {BASE_DEFAULT: '483b6ec00ffcb25d7ed47665f9ea96f6268e9d9b59daa07c239292c50bb9cf05',
             COVER_DEFAULT: '7421b17ce8c3ad711c7bf7fa4ee227d98503df4cdf3b63f35798586d22680ba3',
             SDF: '2c07d7e57bfbd8a68691117d7767a7a30af2dd6cd30e6dfa94ac56eff9363e68',
             FAIR: 'ea306da565f52179c89a1c97f8fcefac27f7f4eef565f00844bf0565c1411652',
             HYBRID: '5ee33b3b638315b50cf9a40cd3adf35f20c30033b607e66c16b80247a2a0be1d',
             V1NEG: 'eda19817e6e497e7027ad738a09280586e0be842177ea500e0d610f6d46bc158'}
# Judge numbers (judge/checks-{base-selftest,sdf,fair}.json triangle_model_metrics / topology_water_triangle /
# wet_dry_flips_triangle / heights; judge/vtx-{sdf,fair}.json water_8conn; judge/exact-area.json; v1 JSONs).
EXP_TRI = {'base': {'map': (402.081, 5105, 3293, 12.696, 8.19), 'spb': (19.761, 253, 165, 12.803, 8.35)},
           'sdf': {'map': (397.561, 4309, 3158, 10.839, 7.943), 'spb': (19.258, 181, 139, 9.399, 7.218)},
           'fair': {'map': (382.09, 2649, 2625, 6.933, 6.87), 'spb': (18.829, 98, 111, 5.205, 5.895)}}
EXP_TOPO_TRI = {'sdf': dict(base_n=2657, cand_n=2643, lost=9, lost_ge_minpx=0, split=3, split_sig=2, merged=3, merged_sig=1),
                'fair': dict(base_n=2657, cand_n=2873, lost=189, lost_ge_minpx=17, split=290, split_sig=143, merged=290,
                             merged_sig=192)}
EXP_TOPO_VTX = {'sdf': dict(base_n=858, cand_n=858, lost=0, lost_ge_minpx=0, split=0, split_sig=0, merged=0, merged_sig=0),
                'fair': dict(base_n=858, cand_n=961, lost=0, lost_ge_minpx=0, split=25, split_sig=20, merged=18, merged_sig=9)}
EXP_AREA = {'sdf': dict(total_m2=35472535.5, total_rel_pct=-0.0158,
                        cls={'36-200m2': (73, 1, 1), '200-2000m2': (455, 6, 0), '2000-10000m2': (109, 0, 0),
                             'ge10000m2': (37, 0, 0)}),
            'fair': dict(total_m2=35469600.5, total_rel_pct=-0.0241,
                         cls={'36-200m2': (73, 59, 54), '200-2000m2': (455, 252, 114), '2000-10000m2': (109, 22, 4),
                              'ge10000m2': (37, 2, 1)})}
EXP_FLOOD = {'sdf': dict(new_wet_m2=33892.0, new_dry_m2=36536.0, new_wet_gt12_m2=0.0, new_wet_max_dist_m=6.0),
             'fair': dict(new_wet_m2=133184.0, new_dry_m2=127688.0, new_wet_gt12_m2=2540.0, new_wet_gt24_m2=1160.0,
                          new_wet_max_dist_m=112.9)}
EXP_NAV = {'sdf': 3449, 'fair': 152}
EXP_V1 = {'sdf': dict(map=(3.608, 6.121), spb=(5.01, 6.644)), 'fair': dict(map=(3.188, 5.585), spb=(3.775, 5.743)),
          'hybrid': dict(map=(3.544, 6.026), spb=(4.57, 6.323)), 'base': dict(map=(4.028, 6.292), spb=(6.07, 7.211))}
EXP_V1NEG = dict(frozen=1, band=1, pond_bed=0, piece_edge=1, new_sea=0, slope=0)


def close(got, exp, tol=0.01):
    if exp == 0:
        return got == 0
    return abs(got - exp) <= tol * abs(exp)


def corners_of(cm):
    vm = np.zeros((2048, 2048), bool)
    vm[:-1, :-1] |= cm; vm[:-1, 1:] |= cm; vm[1:, :-1] |= cm; vm[1:, 1:] |= cm
    return vm


def body_vertices(x, objs, t, dilate):
    sl = objs[t - 1]
    ii, jj = np.nonzero(x.L0v[sl] == t)
    ii = ii + sl[0].start; jj = jj + sl[1].start
    cm = np.zeros((2047, 2047), bool); cm[CELL[ii], CELL[jj]] = True
    cells = cm.copy()
    if dilate:
        cm = binary_dilation(cm, S8)
    return ii, jj, cells, corners_of(cm)


def dry_level(x):
    return np.maximum(x.vpl, EV.SEA)


def ring_raise(x, H, vm):
    wetv = vm & x.wet0
    ring = wetv & binary_dilation(~x.wet0, S8)
    H[ring] = dry_level(x)[ring] + 0.2
    return int(ring.sum())


def nc_lost_pond(x):
    objs = find_objects(x.L0v)
    for t in range(1, x.n0v + 1):
        if not (400 <= x.a0[t] < 1500):
            continue
        ii, jj, cells, vm = body_vertices(x, objs, t, True)
        if not x.covered[cells].all() or (vm & x.frozen).any():
            continue
        H = x.H0.astype(np.float64).copy()
        H[vm] = np.maximum(H[vm], dry_level(x)[vm] + 0.5)
        xx, zz = vtx_xz(ii.mean(), jj.mean())
        return H.astype(np.float32), dict(body=t, base_exact_m2=round(float(x.a0[t]), 1), x=round(float(xx)),
                                          z=round(float(zz)), raised_vertices=int((H != x.H0).sum()))
    raise SystemExit('no pond body for nc_lost_pond')


def nc_split_stream(x):
    objs = find_objects(x.L0v)
    for prefer_stream in (True, False):
        for t in range(1, x.n0v + 1):
            if not (1000 <= x.a0[t] < 20000):
                continue
            ii, jj, cells, vm = body_vertices(x, objs, t, True)
            if (vm & x.frozen).any():
                continue
            if prefer_stream and not (x.cls[vm & x.wet0] == 6).mean() > 0.5:
                continue
            px, pz = vtx_xz(ii, jj)
            C = np.cov(np.stack([px, pz]))
            ev_, evec = np.linalg.eigh(C)
            if np.sqrt(ev_[1] / max(ev_[0], 1e-9)) < 6:
                continue
            ax = evec[:, 1]
            p = (px - px.mean()) * ax[0] + (pz - pz.mean()) * ax[1]
            pm = float(np.median(p))
            if (p < pm - 12).sum() < 40 or (p > pm + 12).sum() < 40:
                continue
            # the body must also be one TRI (4-connected) body with >= 40 px on both sides of the cut
            rows, cols = np.nonzero(cells)
            R0, R1, C0, C1 = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1
            sub = x.L0t[K * R0:K * R1, K * C0:K * C1]
            inbody = np.repeat(np.repeat(cells[R0:R1, C0:C1], K, 0), K, 1) & (sub > 0)
            if not inbody.any():
                continue
            labs, cnt = np.unique(sub[inbody], return_counts=True)
            u = labs[np.argmax(cnt)]
            if cnt.max() < 0.95 * cnt.sum():
                continue
            ti, tj = np.nonzero(sub == u)
            tx, tz = tri_xz(ti + K * R0, tj + K * C0)
            pt = (tx - px.mean()) * ax[0] + (tz - pz.mean()) * ax[1]
            if (pt < pm - 12).sum() < 40 or (pt > pm + 12).sum() < 40:
                continue
            rr, cc = np.nonzero(vm)
            vx, vz = 6.0 * cc, 6.0 * (2047 - rr)
            pv = (vx - px.mean()) * ax[0] + (vz - pz.mean()) * ax[1]
            sel = np.abs(pv - pm) <= 12.0
            H = x.H0.astype(np.float64).copy()
            r_, c_ = rr[sel], cc[sel]
            H[r_, c_] = np.maximum(H[r_, c_], dry_level(x)[r_, c_] + 2.0)
            cx = px.mean() + pm * ax[0]; cz = pz.mean() + pm * ax[1]
            return H.astype(np.float32), dict(body=t, base_exact_m2=round(float(x.a0[t]), 1), stream=prefer_stream,
                                              cut_x=round(float(cx)), cut_z=round(float(cz)),
                                              raised_vertices=int((H != x.H0).sum()))
    raise SystemExit('no elongated body for nc_split_stream')


def nc_flood_inland(x):
    dcell = x.dist0t.reshape(2047, K, 2047, K).min(axis=(1, 3))
    okv = ~x.pondv & ~x.frozen & (x.H0 > EV.SEA_CREST + 0.2)
    okc = okv[:-1, :-1] & okv[:-1, 1:] & okv[1:, :-1] & okv[1:, 1:] & ~x.covered & (dcell >= 18) & (dcell <= 22)
    r0, r1 = int(2047 - EV.SPB[3] / 6), int(2047 - EV.SPB[2] / 6)
    c0, c1 = int(EV.SPB[0] / 6), int(EV.SPB[1] / 6)
    sub = np.zeros_like(okc); sub[r0:r1, c0:c1] = True
    rr, cc = np.nonzero(okc & sub)
    if not rr.size:
        rr, cc = np.nonzero(okc)
    r, c = int(rr[0]), int(cc[0])
    H = x.H0.astype(np.float64).copy()
    H[r:r + 2, c:c + 2] = EV.SEA - 0.5
    return H.astype(np.float32), dict(cell=[r, c], x=6 * c + 3, z=6 * (2047 - r) - 3,
                                      cell_min_dist_to_base_wet_m=round(float(dcell[r, c]), 2))


def nc_nav_channel_raised(x):
    cand = x.channel & (x.bankdist <= 18) & (-x.f0 >= 2.0) & ~x.frozen
    rr, cc = np.nonzero(cand)
    r, c = int(rr[0]), int(cc[0])
    H = x.H0.astype(np.float64).copy(); H[r, c] += 0.25
    return H.astype(np.float32), dict(vertex=[r, c], x=6 * c, z=6 * (2047 - r), draft0=round(float(-x.f0[r, c]), 3),
                                      bank_dist_m=round(float(x.bankdist[r, c]), 2), raise_m=0.25)


def nc_nav_new_shallow(x):
    d0 = -x.f0
    cand = x.nav & x.wet0 & (x.bankdist < NAV_CHANNEL_M) & (d0 >= 1.0) & (d0 <= 2.0) & ~x.frozen
    rr, cc = np.nonzero(cand)
    r, c = int(rr[0]), int(cc[0])
    H = x.H0.astype(np.float64).copy(); H[r, c] = x.vpl[r, c] - 0.8
    return H.astype(np.float32), dict(vertex=[r, c], x=6 * c, z=6 * (2047 - r), draft0=round(float(d0[r, c]), 3),
                                      draft1=0.8, bank_dist_m=round(float(x.bankdist[r, c]), 2))


def nc_area_large(x):
    objs = find_objects(x.L0v)
    for t in range(1, x.n0v + 1):
        if not (2000 <= x.a0[t] < 6000):
            continue
        sl = objs[t - 1]
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        npx = int((x.L0v[sl] == t).sum())
        if npx / (h * w) < 0.45 or max(h, w) / min(h, w) > 2.5:
            continue
        ii, jj, cells, vm = body_vertices(x, objs, t, False)
        if (vm & x.frozen).any():
            continue
        H = x.H0.astype(np.float64).copy()
        n = ring_raise(x, H, vm)
        xx, zz = vtx_xz(ii.mean(), jj.mean())
        return H.astype(np.float32), dict(body=t, base_exact_m2=round(float(x.a0[t]), 1), x=round(float(xx)),
                                          z=round(float(zz)), ring_vertices=n)
    raise SystemExit('no compact body for nc_area_large')


def nc_area_mid(x):
    objs = find_objects(x.L0v)
    H = x.H0.astype(np.float64).copy(); bodies = []
    for t in range(1, x.n0v + 1):
        if len(bodies) >= 12:
            break
        if not (AREA_MID_LO <= x.a0[t] < AREA_MID_HI):
            continue
        _, _, _, vm = body_vertices(x, objs, t, False)
        if (vm & x.frozen).any():
            continue
        ring_raise(x, H, vm); bodies.append(t)
    n_mid = int(((x.a0 >= AREA_MID_LO) & (x.a0 < AREA_MID_HI))[1:].sum())
    return H.astype(np.float32), dict(bodies=bodies, mid_n=n_mid, allowed=int(np.floor(AREA_MID_SHARE * n_mid)))


def nc_area_total(x):
    return (x.H0.astype(np.float64) + 0.5).astype(np.float32), dict(uplift_m=0.5)


NEG_CONTROLS = (('nc_lost_pond', nc_lost_pond, ('topo_vtx_lost', 'topo_tri_lost')),
                ('nc_split_stream', nc_split_stream, ('topo_vtx_split', 'topo_tri_split')),
                ('nc_flood_inland', nc_flood_inland, ('flood',)),
                ('nc_nav_channel_raised', nc_nav_channel_raised, ('nav_channel_raised',)),
                ('nc_nav_new_shallow', nc_nav_new_shallow, ('nav_shallow',)),
                ('nc_area_large', nc_area_large, ('area_large',)),
                ('nc_area_mid', nc_area_mid, ('area_mid',)),
                ('nc_area_total', nc_area_total, ('area_total',)))


def selftest(outdir):
    t0 = time.time()
    os.makedirs(outdir, exist_ok=True)
    checks = []

    def ck(name, ok, got=None, exp=None):
        checks.append(dict(name=name, ok=bool(ok), got=got, exp=exp))

    ck('v1_constants', (EV.SEA, EV.SEA_CREST, EV.SEA_CLEAR, EV.BAND_M, EV.EDGE_MARGIN) == (0.75, 0.95, 1.0, 24.0, 0.05),
       [EV.SEA, EV.SEA_CREST, EV.SEA_CLEAR, EV.BAND_M, EV.EDGE_MARGIN], [0.75, 0.95, 1.0, 24.0, 0.05])
    for p, h in INPUT_SHA.items():
        g = sha256(p)
        ck(f'input_sha:{os.path.basename(p)}', g == h, g, h)
    x = base_context(BASE_DEFAULT, COVER_DEFAULT)
    runs = {}

    def run(key, path):
        r = evaluate(x, path, os.path.join(outdir, f'{key}.json'))
        runs[key] = r
        return r

    # 1. base vs base
    r = run('base', BASE_DEFAULT)
    ck('base:all_gates_zero', all(v == 0 for v in r['gates_violations'].values()), r['gates_violations'])
    for m in ('engine_tri', 'quads'):
        ck(f'base:{m}_metrics_equal', r['metrics'][m]['base'] == r['metrics'][m]['cand'])
    v = r['metrics']['v1']
    ck('base:v1_metrics_equal', v['base_map'] == v['cand_map'] and v['base_spb'] == v['cand_spb'])
    ck('base:area_total_zero', r['details']['area']['total_rel_pct'] == 0.0, r['details']['area']['total_rel_pct'])
    ck('base:changed_vertices_zero', r['changed_vertices'] == 0, r['changed_vertices'])
    # base numbers against the judge
    for win in ('map', 'spb'):
        a = r['metrics']['engine_tri']['base'][win]['all']
        got = (a['length_km'], a['sawtooth'], a['corners'], a['sawtooth_per_km'], a['corners_per_km'])
        ck(f'judge_tri:base_{win}', all(close(g, e) for g, e in zip(got, EXP_TRI['base'][win])), got, EXP_TRI['base'][win])
    ar = r['details']['area']
    got = (ar['base_total_m2'], ar['base_bodies'], ar['classes']['36-200m2']['n'], ar['classes']['200-2000m2']['n'],
           ar['classes']['2000-10000m2']['n'], ar['classes']['ge10000m2']['n'])
    exp = (35478158.8, 858, 73, 455, 109, 37)
    ck('judge_area:base', all(close(g, e) for g, e in zip(got, exp)), got, exp)
    ck('judge_nav:base_navigable_wet', r['details']['nav']['navigable_wet_vertices'] == 36553,
       r['details']['nav']['navigable_wet_vertices'], 36553)
    tb = r['details']['topo_tri']
    ck('judge_topo:base_counts', (tb['base_n'], r['details']['topo_vtx']['base_n']) == (2657, 858),
       [tb['base_n'], r['details']['topo_vtx']['base_n']], [2657, 858])
    # 2. judge reproduction for sdf and fair
    for key, path in (('sdf', SDF), ('fair', FAIR)):
        r = run(key, path)
        for win in ('map', 'spb'):
            a = r['metrics']['engine_tri']['cand'][win]['all']
            got = (a['length_km'], a['sawtooth'], a['corners'], a['sawtooth_per_km'], a['corners_per_km'])
            ck(f'judge_tri:{key}_{win}', all(close(g, e) for g, e in zip(got, EXP_TRI[key][win])), got, EXP_TRI[key][win])
        for kind, exp in (('topo_tri', EXP_TOPO_TRI[key]), ('topo_vtx', EXP_TOPO_VTX[key])):
            got = {k: r['details'][kind][k] for k in exp}
            ck(f'judge_{kind}:{key}', all(close(got[k], exp[k]) for k in exp), got, exp)
        ar = r['details']['area']; ea = EXP_AREA[key]
        got = dict(total_m2=ar['cand_total_m2'], total_rel_pct=ar['total_rel_pct'],
                   cls={k: (ar['classes'][k]['n'], ar['classes'][k]['over5'], ar['classes'][k]['over10']) for k in ea['cls']})
        ok = close(got['total_m2'], ea['total_m2']) and close(got['total_rel_pct'], ea['total_rel_pct']) and all(
            all(close(g, e) for g, e in zip(got['cls'][k], ea['cls'][k])) for k in ea['cls'])
        ck(f'judge_area:{key}', ok, got, ea)
        got = {k: r['details']['flood'][k] for k in EXP_FLOOD[key]}
        ck(f'judge_flood:{key}', all(close(got[k], EXP_FLOOD[key][k]) for k in got), got, EXP_FLOOD[key])
        g = r['details']['nav']['depth_lost_below_1p5']
        ck(f'judge_nav:{key}_depth_lost_1p5', close(g, EXP_NAV[key]), g, EXP_NAV[key])
    # 3. v1 wiring (v1 numbers reproduced inside v2; quads metric equals v1)
    r = run('hybrid', HYBRID)
    r_neg = run('v1_negative_control', V1NEG)
    for key in ('base', 'sdf', 'fair', 'hybrid'):
        vm = runs[key]['metrics']['v1']; e = EXP_V1[key]
        got = dict(map=(vm['cand_map']['sawtooth_per_km'], vm['cand_map']['corners_per_km']),
                   spb=(vm['cand_spb']['sawtooth_per_km'], vm['cand_spb']['corners_per_km']))
        ck(f'v1_metrics:{key}', got == {k: tuple(v_) for k, v_ in e.items()}, got, e)
        ck(f'quads_match_v1:{key}', runs[key]['metrics']['quads_all_match_v1'])
    for key in ('sdf', 'fair', 'hybrid'):
        g = {k: runs[key]['gates_violations'][k] for k in V1_GATES}
        ck(f'v1_gates:{key}_pass', all(v_ == 0 for v_ in g.values()), g)
    g = {k: r_neg['gates_violations'][k] for k in V1_GATES}
    ck('v1_gates:negative_control', g == EXP_V1NEG, g, EXP_V1NEG)
    # 4. planted negative controls for the new gates
    ncs = {}
    for name, builder, targets in NEG_CONTROLS:
        H, info = builder(x)
        p = os.path.join(outdir, f'{name}.npz')
        np.savez(p, heights=H)
        r = run(name, p)
        fired = {k: v_ for k, v_ in r['gates_violations'].items() if v_}
        ok = all(r['gates_violations'][k] > 0 for k in targets)
        ncs[name] = dict(info=info, targets=list(targets), fired=fired, v1_gates_pass=r['gate_groups_pass']['v1'])
        ck(f'negative:{name}', ok, {k: r['gates_violations'][k] for k in targets}, '> 0')
    passed = all(c_['ok'] for c_ in checks)
    keep = ('gates_violations', 'gates_pass', 'gate_groups_pass', 'runtime_s')
    out = dict(schema='shore-eval.v2.selftest', harness_sha256=sha256(__file__), v1_sha256=V1_SHA256,
               selftest_pass=passed, n_checks=len(checks), n_failed=sum(not c_['ok'] for c_ in checks),
               checks=checks, negative_controls=ncs, runs={k: {kk: v_[kk] for kk in keep} for k, v_ in runs.items()},
               runtime_s=round(time.time() - t0, 1))
    with open(os.path.join(outdir, 'selftest.json'), 'w') as fh:
        fh.write(json.dumps(out, indent=1))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('candidate', nargs='?'); ap.add_argument('out', nargs='?')
    ap.add_argument('--base', default=BASE_DEFAULT); ap.add_argument('--cover', default=COVER_DEFAULT)
    ap.add_argument('--selftest', metavar='OUTDIR')
    a = ap.parse_args()
    if a.selftest:
        res = selftest(a.selftest)
        print(json.dumps({k: res[k] for k in ('selftest_pass', 'n_checks', 'n_failed', 'runtime_s')}))
        print(json.dumps([c for c in res['checks'] if not c['ok']], indent=1))
        sys.exit(0 if res['selftest_pass'] else 1)
    if not (a.candidate and a.out):
        ap.error('candidate and out are required')
    x = base_context(a.base, a.cover)
    res = evaluate(x, a.candidate, a.out)
    print(json.dumps({k: res[k] for k in ('gates_violations', 'gates_pass', 'gate_groups_pass', 'runtime_s')}, indent=1))


if __name__ == '__main__':
    main()

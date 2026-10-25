"""EV112 bridge gates for tools/terrain/bridges_v31.py v6 (BALTIC-015, Guillermo in game 17-10). Independent of the tool:
G1-G6 are the EV110 gates (../ev110/gates_v5.py, imported unchanged); G7 and G8 are the EV110 ones with one clause each
replaced (G8 also checks the heights since EV112 review 1), declared below; G9-G14 are new. Each gate prints 'G<n> PASS'
or 'G<n> FAIL' with its numbers and writes JSON.

  G7  as gates_v5.g7, except the wood ramp-fill cap: final terrain <= max(v4, INPUT, underside - 0.05) + 0.002 instead of
      max(v4, underside - 0.05). v6 no longer cuts the v4 straight channel and links beyond the straight part, so where the
      v4 cut had lowered the input ground (015-42 end 1: the old link) the untouched input is not a fill (measured on the
      v6 dev run: 0.0075 m over the v5 reference there, 0 m of fill).
  G8  as gates_v5.g8 (records, arrays, matrices), except the envelope: instead of byte-identical to v4 (v6 seals along the
      curves), every cell of the v4 envelope keeps its v4 value, every other changed cell (NaN in v4) lies within 100 m of
      a site and holds that site's level, and no cover cell leaves the envelope. Added (review of 18-10: a NaN height
      passed G6/G8/G10/G12 and only the WRP stage stopped it): heights a finite float32 (2048, 2048) array, the masks
      reserve/platform/narva/v31_bridge_cut/v31_bridge_fill (2048, 2048) booleans, the envelope (2047, 2047) without inf.
  G9  deck-end air (17-10, 015-13): at every outer end of every site, air = underside plane - terrain <= 0.10 m on a 0.1 m
      grid over the zone from the end to the abutment face (metal: the block's inner face) or the first leg (wood),
      across the whole width there (visual LOD within 0.6 m of the plane and every roadway-LOD vertex, kerbs included);
      the plane is this script's own fit (metal: the lowest visual face within 0.6 m under the roadway; wood: the lower
      envelope of the ramp slab). The failing points of a triangle are a listed water exception only if every raise
      tried that fixes them (all its dry vertices by the largest deficit; each dry vertex alone by deficit / weight, up to
      5 m) narrows the opening (gates_v5.opening) below the run's; a triangle no such raise fixes fails too.
  G10 channel shape and continuity: every site of --sites must have its report and centreline (an empty or partial
      report FAILs; review of 18-10: sites=[] passed). Per site the reported centreline (1 m) is checked, not trusted:
      (a) no turning > 30 deg between consecutive 6 m chords, the junctions included: past each join the chord continues
      along the natural stream's direction as this script estimates it from the INPUT terrain (J to the centroid of the
      input water 3-18 m beyond the join in a +-75 deg cone, 0.5 m samples; none when the stream ends there); (b) at
      every native triangle boundary and interval midpoint of the ORIGINAL centreline, straight part under the deck included (v6 exempted it: 015-18 and 015-40
      were dry over 4.1 and 3.3 m there), the output terrain is under the level and the sample's cell holds water at the
      level in the run's envelope; (c) each join lies within 3 m of input water at the level; (d) both ends of the
      centreline lie in the same connected body of wet vertices (H < level, linked along the NW-SE triangle edges: exact
      for the planar triangles, a wet region of a triangle always holds a wet vertex).
  G11 waterline wiggle within 60 m of each site centre: p90 <= 0.08 m, with the shore gates' metric (exact TRI waterline of
      the terrain against the water field of a footprint regenerated here with pond_footprint_v31.py; chains, 0.5 m
      samples, residual to a 12 m Savitzky-Golay quadratic: functions copied from
      E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev110/scripts/shore-gates/gatelib.py :63-206). Input and v5 values are
      reported beside the run's when given.
      Scope of wiggle_bound.py (review of 18-10): two straight-channel constructions at five angles; it does not prove that
      0.08 m is out of reach for these widths (grid-aligned channels reach p90 0). A FAIL here is an open defect.
  G12 pond-layer invariants on the run: cover subset of the envelope; no envelope cell this run adds over the engine sea
      (a corner under 0.75 m); the regenerated footprint has 0 beds under 1.0 m under water; bury_edges_v31.py on the run
      (reference: the input terrain and its footprint report) ends with 0 new exposed border vertices.
  G13 1:1.5 wings (review of 18-10: v6's soft wing rows left 015-13 end 0 0.21-0.58 m under the profile and no gate
      saw it). At every outer end, this script's own profile from its own end zone (G9's zone_geometry): beyond the zone
      (abutment face or first leg) toward the channel, 0.25-12 m, across the zone width, y = plane(a_end) - 0.09 - r/1.5;
      beside the zone, 0.25-6 m out from each side, y = plane(a) - 0.09 - r/1.5; 0.25 m samples; only where y > level +
      0.3 (the wing ends at the water). Deficit = y - terrain <= 0.10 m. The failing points of a triangle are a listed
      water conflict only if every raise of its dry vertices that fixes them (all of them together; each alone by deficit /
      weight; none above the zone plane - 0.09, the top of the wing) narrows the opening (gates_v5.opening) below the
      run's or dries a 0.5 m sample of the run's centreline, or if none fixes them and the triangle has a wet vertex. It
      fails if a fixing raise breaks nothing, or if the fixing raises break other rules instead (listed: G5 a frozen vertex
      outside the footprint, G6 a new triangle over 55 deg, G1/G7 terrain over a deck face; a decision, not water), or
      if nothing fixes a dry triangle. Slope: the triangles under wing
      points the run changed and left steeper than 1:1.5 + 1 deg and than the input are counted per end; one with a
      failing deficit point fails with it (the wing falls faster than 1:1.5 there); one whose points all meet the profile
      is listed, not failed (the ground stands above the 1:1.5 line, e.g. a zone vertex the 6 m grid lifts over the plane).
  G14 records into the WRP (review of 18-10: the EV112 recipe kit + bridge-records dropped the pilot 015-15 and the stage
      still passed every check). --merged must be exactly --pilot + --kit + the run's bridge-records.json (each record
      once, nothing else, no repeated pilot/bridge site/span/role nor record, no repeated model + float32 matrix consumed by WRP, matrices 12 finite numbers, no
      pilot site among --sites), and with --stage-wrp the staged WRP must hold every merged record once at its exact pose
      (float32 matrix, model name) after the base's objects, the pilot included, and no base object of the same model
      within 2 m of a merged bridge.

Usage: gates_v6.py <G1..G14> --run DIR [--v4 DIR] [--input NPZ] [--input-env NPY] [--input-fp DIR] [--cover NPY]
                   [--sites JSON] [--fixture DIR ...] [--v5 DIR] [--work DIR] [--out JSON]
                   [--merged JSON --pilot JSON --kit JSON [--stage-wrp WRP --base-wrp WRP]]
"""
import argparse, hashlib, json, math, os, subprocess, sys
from pathlib import Path
import numpy as np
from scipy.signal import savgol_filter

HERE = Path(__file__).resolve().parent
WT_DEFAULT = Path("C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c")
EV110 = HERE.parent / "ev110" if (HERE.parent / "ev110" / "gates_v5.py").exists() else WT_DEFAULT / "evidence/v31-pond-layer-2026-10-13/bridges/ev110"
sys.path.insert(0, str(EV110))
import gates_v5 as gv                                                                # G1-G8 of EV110
from scipy.ndimage import label

PY = sys.executable
WT = HERE.parents[3] if (HERE.parents[3] / "tools" / "water" / "pond_footprint_v31.py").exists() else WT_DEFAULT
FP_TOOL = WT / "tools" / "water" / "pond_footprint_v31.py"
BURY_TOOL = WT / "tools" / "water" / "bury_edges_v31.py"
ZT, GN, NC = gv.ZT, gv.GN, gv.GN - 1
SEA = 0.75
AIR_MAX, TURN_MAX, WIG_MAX, WIG_R = 0.10, 30.0, 0.08, 60.0


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------- G7 / G8 with the replaced clauses ----------
def g7(run, v4, sites, fixture, H0):
    orig = gv.ramp_caps

    def caps(run_, v4_):
        out = {}
        for sid, rr in gv.site_records(run_).items():
            m = gv.model(gv.mname(rr["upper"][0]))
            if m["name"] == "bridge_metal_25":
                continue
            vals = []
            for rec, ei, e, inw in gv.outer_ends(m, rr["upper"]):
                P, _ = gv.ramp_points(m, ei); W = gv.world(rec["matrix"], P)
                t5 = gv.terr(run_["H"], W[:, 0], W[:, 2])
                ref = np.maximum(gv.terr(v4_["H"], W[:, 0], W[:, 2]), gv.terr(H0, W[:, 0], W[:, 2]))
                vals.append(round(float((t5 - np.maximum(ref, W[:, 1] - 0.05)).max()), 4))
            out[sid] = vals
        return out
    gv.ramp_caps = caps
    try:
        ok, det = gv.g7(run, v4, sites, fixture)
    finally:
        gv.ramp_caps = orig
    det["rule"] = det["rule"].replace("max(v4, underside - 0.05)", "max(v4, input, underside - 0.05)")
    return ok, det


def g8(run, v4, sites, cover):
    sites_by = {s["id"]: s for s in sites}
    ok_v5, det = gv.g8(run, v4, sites)
    # every clause of gates_v5.g8 but the envelope one, recomputed from its own output
    rec_ok = all(v.get("identical", True) and v.get("ok", True) and (v.get("intended", True) and v.get("axes_identical", True)
                 and v.get("world_roadway_max_dev_m", 0.0) <= 0.005 and v.get("fields_ok", True)) for v in det["records"].values())
    lower_ok = sorted(tuple(k) for k in det["expected_lower"]) == sorted((r["site"], r["span"]) for r in run["rec"] if r.get("role"))
    up_run = [(r["site"], r["span"]) for r in run["rec"] if not r.get("role")]
    rec_ok = rec_ok and sorted(up_run) == sorted((r["site"], r["span"]) for r in v4["rec"]) and len(set(up_run)) == len(up_run)
    arrays_ok = all(det["arrays_identical"].values())
    E, E0 = run["env"].astype(np.float32), v4["env"].astype(np.float32)
    same = (E == E0) | (np.isnan(E) & np.isnan(E0))
    kept = bool(same[np.isfinite(E0)].all())
    ch = np.argwhere(~same)
    rows, bad = [], []
    lv = {s["site"]: s["level"] for s in run["rep"]["sites"]}
    for r, c in ch:
        x, z = 6.0 * c + 3, ZT - 6.0 * r - 3
        sid, dmin = min(((s["id"], math.hypot(s["x"] - x, s["z"] - z)) for s in sites), key=lambda t: t[1])
        good = dmin <= 100.0 and not np.isfinite(E0[r, c]) and np.isfinite(E[r, c]) and abs(float(E[r, c]) - np.float32(lv[sid])) <= 1e-6
        rows.append(dict(cell=[int(r), int(c)], site=sid, dist_m=round(dmin, 1), value=float(E[r, c]), ok=bool(good)))
        if not good:
            bad.append(rows[-1])
    cov = np.load(cover)
    cov_ok = bool(np.isfinite(E[np.isfinite(cov)]).all())
    hz = run["npz"]["heights"]; arr_err = []                                          # review of 18-10: finite heights
    if hz.dtype != np.float32 or hz.shape != (GN, GN):
        arr_err.append(f"heights {hz.dtype} {hz.shape}, not float32 ({GN}, {GN})")
    nf = np.argwhere(~np.isfinite(hz)) if hz.dtype.kind == "f" else np.zeros((0, 2), int)
    if len(nf):
        arr_err.append(f"{len(nf)} non-finite heights, first {nf[:5].tolist()}")
    for k in ("reserve", "platform", "narva", "v31_bridge_cut", "v31_bridge_fill"):
        a_ = run["npz"][k] if k in run["npz"].files else None
        if a_ is None or a_.dtype != bool or a_.shape != (GN, GN):
            arr_err.append(f"mask {k} missing or not a ({GN}, {GN}) boolean array")
    if run["env"].shape != (GN - 1, GN - 1) or np.isinf(run["env"]).any():
        arr_err.append("envelope not (2047, 2047) or holding inf")
    ok = rec_ok and lower_ok and arrays_ok and not det["invalid_matrices"] and kept and not bad and cov_ok and not arr_err
    det.update(rule="as gates_v5.g8 (records, arrays, finite matrices) but the envelope: v4-envelope cells keep their v4 value, "
                    "every other changed cell (NaN in v4) within 100 m of a site at that site's level, cover subset of the envelope; "
                    "heights finite float32 (2048, 2048), masks (2048, 2048) booleans, envelope (2047, 2047) without inf",
               records_ok=rec_ok, lower_records_ok=lower_ok, arrays_ok=arrays_ok, v4_cells_kept=kept,
               heights_and_masks_ok=not arr_err, heights_and_masks_errors=arr_err,
               envelope_cells_changed=len(rows), envelope_bad_cells=bad[:50], cover_subset_of_envelope=cov_ok,
               envelope_changed_per_site={s: sum(1 for x in rows if x["site"] == s) for s in sites_by},
               v5_rule_verdict_envelope_identical_to_v4=det.get("envelope_identical"))
    return ok, det


# ---------- G9 deck-end air ----------
def zone_geometry(m, ei):
    """(a_end, plane y0, slope, lat_lo, lat_hi) of one outer end, in model coordinates (this script's own reading)."""
    d = m[1.0]; V, lab, T = d["V"], d["lab"], d["T"]; ax, lat = m["ax"], m["lat"]
    e, inw = (m["lo"], 1.0) if ei == 0 else (m["hi"], -1.0)
    a = (V[:, ax] - e) * inw
    if m["name"] == "bridge_metal_25":
        B = gv.block_faces(m, ei); a_end = float(((B[..., ax] - e) * inw).max())
        hi = T[T[..., 1].min(1) >= m["ends"][ei] - 0.6]
        A_, L_ = np.meshgrid(np.linspace(0.2, a_end - 0.2, 12), np.linspace(-5.0, 5.0, 11), indexing="ij")
        X = np.zeros(A_.shape + (3,)); X[..., ax] = e + inw * A_; X[..., lat] = m["c_lat"] + L_
        y = gv.ray_top(hi, X[..., 0], X[..., 2], lowest=True); k = np.isfinite(y)
        s, y0 = np.polyfit(A_[k], y[k], 1)
    else:
        P, a_end = gv.ramp_points(m, ei)
        s, y0 = np.polyfit((P[:, ax] - e) * inw, P[:, 1], 1)
    sel = (a >= 0) & (a <= a_end) & (V[:, 1] >= y0 + s * np.clip(a, 0, a_end) - 0.6)
    rv = m["road"].reshape(-1, 3); ar = (rv[:, ax] - e) * inw
    lv = np.r_[V[sel, lat], rv[(ar >= 0) & (ar <= a_end), lat]] - m["c_lat"]
    return float(a_end), float(y0), float(s), float(lv.min()), float(lv.max())


def g9(run, sites):
    s_by = {s["id"]: s for s in sites}; out, ok = {}, True
    for sid, rr in gv.site_records(run).items():
        s = s_by[sid]; m = gv.model(gv.mname(rr["upper"][0])); L = gv.level(run, sid); ends = []
        base_open = gv.opening(run["H"], s, m, L)
        for rec, ei, e, inw in gv.outer_ends(m, rr["upper"]):
            a_end, y0, sl, lo, hi = zone_geometry(m, ei)
            A_, L_ = np.meshgrid(np.arange(0.05, a_end + 1e-9, 0.1), np.arange(lo, hi + 1e-9, 0.1), indexing="ij")
            P = np.zeros(A_.shape + (3,)); P[..., m["ax"]] = e + inw * A_; P[..., m["lat"]] = m["c_lat"] + L_; P[..., 1] = y0 + sl * A_
            W = gv.world(rec["matrix"], P.reshape(-1, 3)); air = W[:, 1] - gv.terr(run["H"], W[:, 0], W[:, 2])
            badi = np.flatnonzero(air > AIR_MAX)
            tri = {}
            for i in badi:
                tri.setdefault(tuple(gv.tri_vertices(W[i, 0], W[i, 2])), []).append(i)
            exc_t, fail_t = [], []
            for key, pts in tri.items():
                need = float((air[pts] - AIR_MAX).max()); Q = W[pts]
                dry = [v for v in key if run["H"][v] >= L]
                wts = {}
                for v in dry:                                                              # planar weight of v at each point
                    Hn = run["H"].copy(); Hn[v] += 1.0
                    wts[v] = gv.terr(Hn, Q[:, 0], Q[:, 2]) - gv.terr(run["H"], Q[:, 0], Q[:, 2])
                options = [{v: need for v in dry}] + [{v: float(min(((air[pts] - AIR_MAX) / np.maximum(wts[v], 1e-9)).max(), 5.0))}
                                                     for v in dry if wts[v].min() > 0.05]
                fixed_dry, fixed_wet = False, False
                for opt in options:                                                         # does a raise fix the points, and
                    Hn = run["H"].copy()                                                    # at what cost to the opening
                    for v, dz in opt.items():
                        Hn[v] += dz
                    if (Q[:, 1] - gv.terr(Hn, Q[:, 0], Q[:, 2])).max() > AIR_MAX + 1e-6:
                        continue
                    if gv.opening(Hn, s, m, L) < base_open - 1e-6:
                        fixed_wet = True
                    else:
                        fixed_dry = True; break
                row = dict(triangle=[list(v) for v in key], deficit_m=round(need, 4), points=len(pts),
                           why="a raise fixes it without narrowing the opening" if fixed_dry else
                               ("every raise that fixes it narrows the opening" if fixed_wet else "no raise of its dry vertices fixes it"))
                (exc_t if fixed_wet and not fixed_dry else fail_t).append(row)
            exc_keys = {tuple(tuple(v) for v in t["triangle"]) for t in exc_t}
            n_exc = int(sum(1 for i in badi if tuple(gv.tri_vertices(W[i, 0], W[i, 2])) in exc_keys))
            good = not fail_t
            ends.append(dict(end=ei, kind="block" if m["name"] == "bridge_metal_25" else "ramp", a_end_m=round(a_end, 3),
                             plane=[round(y0, 4), round(sl, 4)], lat=[round(lo, 3), round(hi, 3)], points=int(air.size),
                             max_air_m=round(float(air.max()), 4), points_over=int(len(badi)), water_exception_points=n_exc,
                             water_exception_triangles=exc_t, failing_triangles=len(fail_t),
                             max_air_failing_m=round(max((t["deficit_m"] for t in fail_t), default=-AIR_MAX) + AIR_MAX, 4), pass_=good))
            ok &= good
        out[sid] = ends
    return ok, dict(rule=f"air under the deck-end underside <= {AIR_MAX} m over the whole end zone (end to abutment face or first "
                         "leg, full width with kerbs), every outer end of every site; exception only where raising the "
                         "point's triangle (dry vertices) would narrow the opening below the run's (listed)", sites=out,
                    failing_ends=[f"{k}/{e['end']}" for k, v in out.items() for e in v if not e["pass_"]])


# ---------- G10 channel shape ----------
def resample(P, step):
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    t = np.arange(0, s[-1] + 1e-9, step)
    return np.column_stack([np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])])


def native_breaks(P):
    """Split each original segment at every native x/z/diagonal edge, plus interval midpoints.

    Heights are affine between adjacent breaks, so endpoint maxima prove the whole
    segment is wet. Midpoints inspect the water cell on each open interval.
    """
    points = []
    for a, b in zip(P[:-1], P[1:]):
        ts = [0.0, 1.0]
        for va, vb in ((a[0] / 6, b[0] / 6), ((ZT-a[1]) / 6, (ZT-b[1]) / 6),
                       ((a[0]+a[1]-ZT) / 6, (b[0]+b[1]-ZT) / 6)):
            if abs(vb-va) < 1e-12:
                continue
            for edge in range(math.floor(min(va, vb))+1, math.ceil(max(va, vb))):
                t = (edge-va)/(vb-va)
                if 0 < t < 1:
                    ts.append(t)
        ts = np.unique(ts)
        ts = np.sort(np.r_[ts, (ts[:-1]+ts[1:])/2])
        points.extend(a + ts[:, None]*(b-a))
    return np.asarray(points)


def turning(P, chord=6.0):
    P = resample(P, 1.0); k = int(chord)
    if len(P) < 2 * k + 1:
        return np.zeros(0), P
    a, b = P[k:-k] - P[:-2 * k], P[2 * k:] - P[k:-k]
    cs = (a * b).sum(1) / np.maximum(np.hypot(*a.T) * np.hypot(*b.T), 1e-12)
    return np.degrees(np.arccos(np.clip(cs, -1, 1))), P


def natural_direction(H0, envc, J, t_out, L):
    """Direction from J to the centroid of the input water (planar terrain under L - 0.01 inside an envelope cell at L)
    sampled every 0.5 m in the cone +-75 deg around t_out, 3-18 m from J; None when fewer than 8 samples are wet (the
    stream ends there, e.g. a pool)."""
    rr, aa = np.meshgrid(np.arange(3.0, 18.0 + 1e-9, 0.5), np.radians(np.arange(-75, 75.1, 2.5)), indexing="ij")
    base = math.atan2(t_out[1], t_out[0])
    X, Z = J[0] + rr * np.cos(base + aa), J[1] + rr * np.sin(base + aa)
    r, c = np.floor((ZT - Z) / 6).astype(int), np.floor(X / 6).astype(int)
    wet = (gv.terr(H0, X, Z) < L - 0.01) & envc[np.clip(r, 0, NC - 1), np.clip(c, 0, NC - 1)]
    if wet.sum() < 8:
        return None, int(wet.sum())
    u = np.array([X[wet].mean() - J[0], Z[wet].mean() - J[1]])
    return u / np.hypot(*u), int(wet.sum())


def wet_bodies(H, L):
    """Connected bodies of wet vertices (H < L) along the NW-SE triangle edges (E-W, N-S, NW-SE)."""
    return label(H < L, structure=np.array([[1, 1, 0], [1, 1, 1], [0, 1, 1]]))[0]


def g10(run, sites, H0, env_in):
    out, ok, s_by = {}, True, {s["id"]: s for s in (sites or [])}
    rep_by = {s["site"]: s for s in run["rep"].get("sites", [])}
    coverage = dict(sites=len(s_by), missing=sorted(set(s_by) - set(rep_by)), extra=sorted(set(rep_by) - set(s_by)))
    if not s_by or coverage["missing"] or coverage["extra"]:
        ok = False
    E = run["env"]
    for sid in s_by:
        s = rep_by.get(sid)
        if s is None:
            out[sid] = dict(pass_=False, errors=["no report"]); continue
        L = s["level"]; ch = s.get("channel")
        if not ch or not ch.get("centreline"):
            out[sid] = dict(pass_=False, errors=["no centreline in the report"]); ok = False; continue
        cl = resample(np.array(ch["centreline"], float), 1.0); envc = np.isfinite(env_in) & (np.abs(env_in - L) < 0.05)
        if len(cl) < 13:
            out[sid] = dict(pass_=False, errors=["centreline shorter than 12 m"]); ok = False; continue
        ext, junction, errs = [cl], [], []
        for end, sgn in ((0, -1), (-1, 1)):
            J = cl[end]; t_out = cl[end] - cl[end + (1 if end == 0 else -1) * 6]; t_out = t_out / np.hypot(*t_out)
            u, n = natural_direction(H0, envc, J, t_out, L)
            wet = [gv.terr(H0, J[0] + dx, J[1] + dz) < L for dx in (-3, 0, 3) for dz in (-3, 0, 3)]
            if not any(wet):
                errs.append(f"join {J.round(1).tolist()} not within 3 m of input water at the level")
            junction.append(dict(join=J.round(2).tolist(), natural_dir=None if u is None else u.round(4).tolist(), natural_points=n,
                                 angle_deg=None if u is None else round(float(np.degrees(np.arccos(np.clip(u @ t_out, -1, 1)))), 2)))
            if u is not None:
                seg = np.array([J + u * (i + 1) for i in range(12)])
                ext = [seg[::-1]] + ext if end == 0 else ext + [seg]
        full = np.vstack(ext)
        tr, P = turning(full)
        i_max = int(np.argmax(tr)) if len(tr) else 0
        Q = native_breaks(np.asarray(ch["centreline"], float)); hv = gv.terr(run["H"], Q[:, 0], Q[:, 1])
        r_, c_ = np.floor((ZT - Q[:, 1]) / 6).astype(int), np.floor(Q[:, 0] / 6).astype(int)
        ev = E[np.clip(r_, 0, NC - 1), np.clip(c_, 0, NC - 1)].astype(float)
        water = np.isfinite(ev) & (np.abs(ev - L) <= 0.05) if L != SEA else ~np.isfinite(ev)
        dry = np.flatnonzero(hv >= L); nowater = np.flatnonzero(~water)
        lab = wet_bodies(run["H"], L)
        bodies = [sorted({int(lab[v]) for v in gv.tri_vertices(*p) if run["H"][v] < L}) for p in (Q[0], Q[-1])]
        joined = bool(set(bodies[0]) & set(bodies[1]))
        st = ch.get("straight_m") or [0.0, 0.0]
        if not (0 <= st[0] <= 60 and 0 <= st[1] <= 60):
            errs.append(f"straight part {st} outside 0-60 m")
        good = bool(len(tr)) and tr.max() <= TURN_MAX and not len(dry) and not len(nowater) and joined and not errs
        out[sid] = dict(max_turn_deg=round(float(tr.max()) if len(tr) else 0.0, 2), at=P[i_max + 6].round(1).tolist() if len(tr) else None,
                        turns_over_30=int((tr > TURN_MAX).sum()) if len(tr) else 0, junctions=junction,
                        centreline_samples=int(len(Q)), dry_samples=int(len(dry)), dry_at=Q[dry[:5]].round(1).tolist(),
                        samples_without_water_cell=int(len(nowater)), without_water_at=Q[nowater[:5]].round(1).tolist(),
                        max_terrain_minus_level_m=round(float((hv - L).max()), 3), end_bodies=bodies, ends_connected=joined,
                        errors=errs, pass_=bool(good))
        ok &= bool(good)
    return ok, dict(rule=f"every site of --sites reported with a centreline; per site: turning <= {TURN_MAX} deg between consecutive 6 m "
                         "chords, continued 12 m along the input natural stream's own direction past each join (J to the centroid "
                         "of the input water 3-18 m ahead); at every native triangle crossing and interval midpoint of the original centreline (no straight-part "
                         "exemption) output terrain under the level and the cell holding water at the level in the run's "
                         "envelope; each join within 3 m of input water; both centreline ends in one body of wet vertices "
                         "(H < level, NW-SE triangle edges)", coverage=coverage, sites=out)


# ---------- G11 waterline wiggle (shore-gates metric, copied) ----------
def footprint(terrain, cover, env, outdir):
    if not (Path(outdir) / "footprint.npz").exists():
        subprocess.run([PY, "-I", str(FP_TOOL), str(terrain), str(cover), str(outdir), str(env)], check=True, stdout=subprocess.DEVNULL)
    return np.load(Path(outdir) / "footprint.npz"), json.load(open(Path(outdir) / "footprint-report.json"))


def corner_water(plane, field):
    return np.where(np.isfinite(plane)[:, :, None], field, SEA)


def waterline(H, Wc):
    out_p = []
    h = [H[:-1, :-1], H[:-1, 1:], H[1:, :-1], H[1:, 1:]]
    off = [(0, 0), (0, 1), (1, 0), (1, 1)]
    r, c = np.mgrid[0:NC, 0:NC]
    for idx in ((0, 1, 3), (0, 2, 3)):
        d = np.stack([h[k] - Wc[:, :, k] for k in idx], -1); w = d < 0; nw = w.sum(-1); m = (nw == 1) | (nw == 2)
        dm, wm, rm, cm = d[m], w[m], r[m], c[m]; pts = []
        for a, b in ((0, 1), (1, 2), (2, 0)):
            x = wm[:, a] != wm[:, b]
            t = np.where(x, dm[:, a] / np.where(x, dm[:, a] - dm[:, b], 1), np.nan)
            ra, ca, rb, cb = rm + off[idx[a]][0], cm + off[idx[a]][1], rm + off[idx[b]][0], cm + off[idx[b]][1]
            pts.append(np.stack([6.0 * (ca + t * (cb - ca)), ZT - 6.0 * (ra + t * (rb - ra))], -1))
        pts = np.stack(pts, 1); okp = np.isfinite(pts[:, :, 0])
        order = np.argsort(~okp, axis=1, kind="stable")[:, :2]
        out_p.append(np.take_along_axis(pts, order[:, :, None], 1))
    return np.concatenate(out_p)


def polylines(p):
    keys = np.round(p.reshape(-1, 2) * 1e6).astype(np.int64)
    uk, inv = np.unique(keys, axis=0, return_inverse=True); inv = inv.ravel()
    a, b = inv[0::2], inv[1::2]; n = len(uk)
    deg = np.bincount(np.r_[a, b], minlength=n); nbr = [[] for _ in range(n)]
    for s_, (u, v) in enumerate(zip(a, b)):
        nbr[u].append((s_, v)); nbr[v].append((s_, u))
    used = np.zeros(len(a), bool); lines = []
    first = np.full(n, -1); first[inv[::-1]] = np.arange(len(inv))[::-1]; coords = p.reshape(-1, 2)[first]

    def walk(start, s0, nxt):
        seq = [start, nxt]; used[s0] = True; cur = nxt
        while deg[cur] == 2:
            cand = [(s_, v) for s_, v in nbr[cur] if not used[s_]]
            if not cand:
                break
            s_, v = cand[0]; used[s_] = True; seq.append(v); cur = v
        return seq
    for start in range(n):
        if deg[start] != 2:
            for s_, v in nbr[start]:
                if not used[s_]:
                    seq = walk(start, s_, v); lines.append((coords[seq], False))
    for s_ in range(len(a)):
        if not used[s_]:
            seq = walk(a[s_], s_, b[s_]); lines.append((coords[seq], seq[0] == seq[-1]))
    return lines


def wiggle(p, closed, w=12.0, step=0.5):
    if closed and np.hypot(*(p[0] - p[-1])) > 1e-9:
        p = np.vstack([p, p[:1]])
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
    if s[-1] < step:
        return p, np.full(len(p), np.nan)
    t = np.arange(0, s[-1], step)
    q = np.column_stack([np.interp(t, s, p[:, 0]), np.interp(t, s, p[:, 1])])
    k = int(round(w / step)) | 1
    if len(q) <= k + 2:
        return q, np.full(len(q), np.nan)
    mode = "wrap" if closed else "interp"
    sm = np.column_stack([savgol_filter(q[:, 0], k, 2, mode=mode), savgol_filter(q[:, 1], k, 2, mode=mode)])
    return q, np.hypot(*(q - sm).T)


def wiggle_near(H, fp, sites):
    Wc = corner_water(fp["plane"].astype(float), fp["field"].astype(float))
    qs, vs = [], []
    for line, closed in polylines(waterline(H, Wc)):
        q, v = wiggle(line, closed); qs.append(q); vs.append(v)
    q, v = np.vstack(qs), np.concatenate(vs); out = {}
    for s in sites:
        k = (np.hypot(q[:, 0] - s["x"], q[:, 1] - s["z"]) <= WIG_R) & np.isfinite(v)
        out[s["id"]] = dict(samples=int(k.sum()), p50=round(float(np.percentile(v[k], 50)), 4) if k.any() else None,
                            p90=round(float(np.percentile(v[k], 90)), 4) if k.any() else None, max=round(float(v[k].max()), 4) if k.any() else None)
    return out


def g11(run, sites, cover, work, input_npz=None, input_fp=None, v5=None):
    fp, rep = footprint(run["dir"] / "terrain-br.npz", cover, run["dir"] / "envelope-br.npy", Path(work) / "fp-run")
    res = wiggle_near(run["H"], fp, sites)
    ref = {}
    if input_npz and input_fp:
        ref["input"] = wiggle_near(np.load(input_npz)["heights"].astype(float), np.load(Path(input_fp) / "footprint.npz"), sites)
    if v5:
        v5 = Path(v5); f5, _ = footprint(v5 / "terrain-br.npz", cover, v5 / "envelope-br.npy", Path(work) / "fp-v5")
        ref["v5"] = wiggle_near(np.load(v5 / "terrain-br.npz")["heights"].astype(float), f5, sites)
    fail = [k for k, v in res.items() if v["p90"] is None or v["p90"] > WIG_MAX]
    return not fail, dict(rule=f"waterline wiggle p90 <= {WIG_MAX} m within {WIG_R} m of each site centre (shore-gates metric, "
                               "regenerated footprint)", sites=res, references=ref, failing=fail,
                          footprint=str(Path(work) / "fp-run"), footprint_sha256=sha(Path(work) / "fp-run" / "footprint.npz"))


# ---------- G12 pond-layer invariants ----------
def g12(run, env_in, cover, work, input_npz, input_fp):
    E = run["env"]; cov = np.load(cover)
    cov_ok = bool(np.isfinite(E[np.isfinite(cov)]).all())
    if not cov_ok:                                                                     # the footprint tool refuses such an envelope
        return False, dict(rule="cover subset of envelope (checked first)", cover_subset=False,
                           cover_cells_missing=np.argwhere(np.isfinite(cov) & ~np.isfinite(E))[:20].tolist())
    added = np.isfinite(E) & ~np.isfinite(env_in)
    H = run["H"]; mn = np.minimum(np.minimum(H[:-1, :-1], H[:-1, 1:]), np.minimum(H[1:, :-1], H[1:, 1:]))
    over_sea = np.argwhere(added & (mn < SEA))
    fp, rep = footprint(run["dir"] / "terrain-br.npz", cover, run["dir"] / "envelope-br.npy", Path(work) / "fp-run")
    bed_ok = rep.get("bed_below_1m_under_water") == 0
    bdir = Path(work) / "bury"
    if not (bdir / "bury-report.json").exists():
        bdir.mkdir(parents=True, exist_ok=True)
        subprocess.run([PY, "-I", str(BURY_TOOL), str(run["dir"] / "terrain-br.npz"), str(input_npz), str(cover),
                        str(run["dir"] / "envelope-br.npy"), str(Path(input_fp) / "footprint-report.json"), str(bdir / "terrain-buried.npz"),
                        str(bdir / "work"), str(bdir / "bury-report.json")], check=True, stdout=subprocess.DEVNULL)
    br = json.load(open(bdir / "bury-report.json"))
    passes = br.get("passes", [])
    last_new = br.get("final_new_exposed")
    Hb = np.load(bdir / "terrain-buried.npz")["heights"]
    changed = int((Hb != np.load(run["dir"] / "terrain-br.npz")["heights"]).sum())
    bury_ok = last_new == [] if last_new is not None else False
    ok = cov_ok and not len(over_sea) and bed_ok and bury_ok
    return ok, dict(rule="cover subset of envelope; no envelope cell added by the run with a corner under the engine sea (0.75); "
                         "regenerated footprint: 0 beds under 1.0 m under water; bury_edges_v31 ends with 0 new exposed border "
                         "vertices (reference: the input terrain and its footprint report)",
                    cover_subset=cov_ok, envelope_cells_added=int(added.sum()), added_over_sea=over_sea[:20].tolist(),
                    footprint_bed_below_1m_under_water=rep.get("bed_below_1m_under_water"),
                    footprint_exposed_border=rep.get("exposed_border_lt_0p05"), bury_passes=passes, bury_vertices_changed=changed,
                    bury_report=str(bdir / "bury-report.json"))


# ---------- G13 1:1.5 wings ----------
WING_S, WING_TOL, WING_DEG = 1.5, 0.10, math.degrees(math.atan(1 / 1.5)) + 1.0


def wing_points(m, rec, ei, e, inw, L):
    """World profile points of one outer end's wings (see G13), the zone from zone_geometry."""
    a_end, y0, sl, lo, hi = zone_geometry(m, ei); pts = []
    R_, L_ = np.meshgrid(np.arange(0.25, 12.0 + 1e-9, 0.25), np.arange(lo, hi + 1e-9, 0.25), indexing="ij")
    P = np.zeros(R_.shape + (3,)); P[..., m["ax"]] = e + inw * (a_end + R_); P[..., m["lat"]] = m["c_lat"] + L_
    P[..., 1] = y0 + sl * a_end - 0.09 - R_ / WING_S; pts.append(P.reshape(-1, 3))
    for side, l0 in ((-1, lo), (1, hi)):
        A_, R_ = np.meshgrid(np.arange(0.05, a_end + 1e-9, 0.25), np.arange(0.25, 6.0 + 1e-9, 0.25), indexing="ij")
        P = np.zeros(A_.shape + (3,)); P[..., m["ax"]] = e + inw * A_; P[..., m["lat"]] = m["c_lat"] + l0 + side * R_
        P[..., 1] = y0 + sl * A_ - 0.09 - R_ / WING_S; pts.append(P.reshape(-1, 3))
    W = gv.world(rec["matrix"], np.concatenate(pts))
    return W[W[:, 1] > L + 0.3], (a_end, y0, sl, lo, hi)


def site_deck_clear(H, ups, m):
    """min over the site's deck faces (upper records) of deck - terrain, exact (gates_v5.deck_clear for one site)."""
    mn = np.inf
    for rec in ups:
        for T in m["deck"]:
            C = gv.cands(gv.world(rec["matrix"], T)); mn = min(mn, float((C[:, 1] - gv.terr(H, C[:, 0], C[:, 2])).min()))
    return mn


def path_dry(H, Q, L):
    return gv.terr(H, Q[:, 0], Q[:, 1]) >= L


def g13(run, sites, H0):
    s_by = {s["id"]: s for s in sites}; out, ok = {}, True
    S0, S1 = gv.slopes(H0), gv.slopes(run["H"])
    frz = run["npz"]["reserve"] | run["npz"]["platform"] | run["npz"]["narva"]; sup = gv.footprint_support(run)
    for sid, rr in gv.site_records(run).items():
        s = s_by[sid]; m = gv.model(gv.mname(rr["upper"][0])); L = gv.level(run, sid); ends = []
        base_open = gv.opening(run["H"], s, m, L)
        ch = [x for x in run["rep"]["sites"] if x["site"] == sid][0].get("channel") or {}
        Qc = resample(np.array(ch["centreline"], float), 0.5) if ch.get("centreline") else np.zeros((0, 2))
        dry0 = path_dry(run["H"], Qc, L) if len(Qc) else np.zeros(0, bool)
        for rec, ei, e, inw in gv.outer_ends(m, rr["upper"]):
            W, zg = wing_points(m, rec, ei, e, inw, L)
            dfc = W[:, 1] - gv.terr(run["H"], W[:, 0], W[:, 2])
            badi = np.flatnonzero(dfc > WING_TOL); tri = {}
            for i in badi:
                tri.setdefault(tuple(gv.tri_vertices(W[i, 0], W[i, 2])), []).append(i)
            exc_t, fail_t = [], []
            ya = zg[1] + zg[2] * zg[0] - 0.09                                          # top of the wings: zone plane - 0.09
            for key, pts in tri.items():
                need = float((dfc[pts] - WING_TOL).max()); Q = W[pts]
                dry = [v for v in key if run["H"][v] >= L]; wet_v = [v for v in key if run["H"][v] < L]; wts = {}
                for v in dry:
                    Hn = run["H"].copy(); Hn[v] += 1.0
                    wts[v] = gv.terr(Hn, Q[:, 0], Q[:, 2]) - gv.terr(run["H"], Q[:, 0], Q[:, 2])
                options = []                                                         # dry raises, never above ya
                if dry:
                    dz = need / max(float(sum(wts[u].min() for u in dry)), 1e-9)
                    options.append({v: dz for v in dry})
                for v in dry:
                    if wts[v].min() > 0.05:
                        options.append({v: float(((dfc[pts] - WING_TOL) / np.maximum(wts[v], 1e-9)).max())})
                verdicts = []
                for opt in options:
                    if any(run["H"][v] + dz > max(ya, run["H"][v]) + 1e-9 for v, dz in opt.items()):
                        continue
                    Hn = run["H"].copy()
                    for v, dz in opt.items():
                        Hn[v] += dz
                    if (Q[:, 1] - gv.terr(Hn, Q[:, 0], Q[:, 2])).max() > WING_TOL + 1e-6:
                        continue
                    br = []
                    if gv.opening(Hn, s, m, L) < base_open - 1e-6:
                        br.append("water: narrows the opening")
                    if len(Qc) and (path_dry(Hn, Qc, L) & ~dry0).any():
                        br.append("water: dries the centreline")
                    if any(frz[v] and not sup[v] for v in opt):
                        br.append("G5: frozen vertex outside the footprint")
                    S2 = gv.slopes(Hn); r0_ = min(v[0] for v in opt) - 1; c0_ = min(v[1] for v in opt) - 1
                    win = (slice(None), slice(max(r0_, 0), r0_ + 3), slice(max(c0_, 0), c0_ + 3))
                    if ((S2[win] > 55.0) & ~(S1[win] > 55.0)).any():
                        br.append("G6: a new triangle over 55 deg")
                    if site_deck_clear(Hn, rr["upper"], m) < 0.01:
                        br.append("G1/G7: terrain over a deck face")
                    verdicts.append(br)
                free = any(not br for br in verdicts)
                water_only = bool(verdicts) and all(any(x.startswith("water") for x in br) for br in verdicts)
                if free:
                    why, kind = "a dry raise (<= zone plane) fixes it and breaks nothing", "fail"
                elif water_only:
                    why, kind = "every dry raise that fixes it touches the water: " + "; ".join(sorted({x for br in verdicts for x in br if x.startswith("water")})), "water"
                elif verdicts:
                    why, kind = "the dry raises that fix it break " + "; ".join(sorted({x for br in verdicts for x in br if not x.startswith("water")})), "fail"
                elif wet_v:
                    why, kind = "only raising a wet vertex fixes it (dry raises capped at the zone plane)", "water"
                else:
                    why, kind = "no dry raise up to the zone plane fixes it", "fail"
                row = dict(triangle=[list(v) for v in key], deficit_m=round(need + WING_TOL, 4), points=len(pts), wet_vertices=len(wet_v), why=why)
                (exc_t if kind == "water" else fail_t).append(row)
            fail_keys = {tuple(tuple(v) for v in t["triangle"]) for t in fail_t}
            steep, seen = {}, set()
            for x, z in W[:, [0, 2]]:
                v = gv.tri_vertices(x, z); half = 0 if v[1][0] == v[0][0] else 1; k_ = (v[0][0], v[0][1], half)
                if k_ in seen:
                    continue
                seen.add(k_)
                a1, a0 = float(S1[half, v[0][0], v[0][1]]), float(S0[half, v[0][0], v[0][1]])
                if any(run["H"][q] != H0[q] for q in v) and a1 > WING_DEG and a1 > a0 + 1e-4:
                    steep[k_] = dict(triangle=[list(q) for q in v], deg=round(a1, 2), input_deg=round(a0, 2),
                                     wet_vertices=sum(run["H"][q] < L for q in v), with_failing_deficit=tuple(v) in fail_keys)
            n_exc = int(sum(t["points"] for t in exc_t))
            good = not fail_t
            ends.append(dict(end=ei, kind="block" if m["name"] == "bridge_metal_25" else "ramp", zone=[round(x, 4) for x in zg], points=int(len(W)),
                             max_deficit_m=round(float(dfc.max()), 4) if len(W) else None, points_over=int(len(badi)),
                             water_conflict_points=n_exc, water_conflict_triangles=exc_t, failing_triangles=len(fail_t),
                             failing_detail=fail_t[:20], max_deficit_failing_m=round(max((t["deficit_m"] for t in fail_t), default=0.0), 4),
                             steep_triangles=len(steep), steep_max_deg=round(max((t["deg"] for t in steep.values()), default=0.0), 2),
                             steep_with_failing_deficit=sum(t["with_failing_deficit"] for t in steep.values()),
                             steep_listed=sorted(steep.values(), key=lambda t: -t["deg"])[:10], pass_=good))
            ok &= good
        out[sid] = ends
    return ok, dict(rule=f"1:{WING_S} wings from this script's end zone (beyond: 0.25-12 m, zone width; beside: 0.25-6 m; profile "
                         f"> level + 0.3): deficit <= {WING_TOL} m; a failing triangle is a listed water conflict only if no raise "
                         "of its dry vertices fixes it without narrowing the opening or drying the centreline; slope: changed "
                         f"triangles under wing points steeper than {WING_DEG:.2f} deg and than the input counted, failing with "
                         "their deficit points, listed where the profile holds", sites=out,
                    failing_ends=[f"{k}/{e['end']}" for k, v in out.items() for e in v if not e["pass_"]])


# ---------- G14 records into the WRP ----------
def rec_key(r):
    return (r.get("site"), r.get("span"), r.get("piece"), r.get("role"))


def g14(run, sites, merged, pilot, kit, stage_wrp=None, base_wrp=None):
    errs = []
    M, Pl, K, Br = (json.load(open(p, encoding="utf-8")) for p in (merged, pilot, kit, run["dir"] / "bridge-records.json"))
    want = Pl + K + Br
    canon = lambda r: json.dumps(r, sort_keys=True)
    cm, cw = [canon(r) for r in M], [canon(r) for r in want]
    from collections import Counter
    miss = Counter(cw) - Counter(cm); extra = Counter(cm) - Counter(cw)
    if miss:
        errs.append(f"{sum(miss.values())} records missing from the merged list (first: {json.loads(next(iter(miss)))['site']})")
    if extra:
        errs.append(f"{sum(extra.values())} records in the merged list that no part holds")
    ids = {r.get("site") for r in Pl + Br}                                            # kit pieces repeat their keys ('stones')
    keys = Counter(rec_key(r) for r in M if r.get("site") in ids); dup = [k for k, n in keys.items() if n > 1]
    dup += [k for k, n in Counter(cm).items() if n > 1][:1]
    if dup:
        errs.append(f"repeated site/span/piece/role {dup[:3]}")
    poses = Counter((r.get("model"), tuple(np.float32(r.get("matrix") or []))) for r in M)
    if any(n > 1 for n in poses.values()):
        errs.append("repeated model + float32 matrix consumed by WRP")
    bad_m = [rec_key(r) for r in M if not (isinstance(r.get("matrix"), list) and len(r["matrix"]) == 12 and
                                           all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in r["matrix"]))]
    if bad_m:
        errs.append(f"invalid matrices {bad_m[:3]}")
    pilot_ids = sorted({r["site"] for r in Pl}); site_ids = {s["id"] for s in sites}
    if not pilot_ids:
        errs.append("no pilot record")
    if set(pilot_ids) & site_ids:
        errs.append(f"pilot site among the sites {sorted(set(pilot_ids) & site_ids)}")
    pilot_in = {sid: sum(1 for r in M if r.get("site") == sid) for sid in pilot_ids}
    stage = None
    if stage_wrp:
        sys.path.insert(0, str(WT_WRP))
        from wrp0wzd import read
        w = read(stage_wrp); objs = w["objects"]; nb = len(read(base_wrp)["objects"]) if base_wrp else len(objs) - len(M)
        app = objs[nb:]; serr = []
        actual_poses = Counter((o["name"], tuple(np.float32(o["matrix"]))) for o in app)
        if any(n > 1 for n in actual_poses.values()):
            serr.append("repeated appended model + float32 pose in the staged WRP")
        if len(app) != len(M):
            serr.append(f"{len(app)} appended objects for {len(M)} merged records")
        for o, r in zip(app, M):
            if o["name"] != r["model"] or not np.array_equal(np.float32(o["matrix"]), np.float32(r["matrix"])):
                serr.append(f"appended object {o['id']} is not {rec_key(r)} at its pose"); break
        found = {}
        for r in Pl:
            mt = np.float32(r["matrix"])
            found[r["site"]] = sum(1 for o in objs if o["name"] == r["model"] and np.array_equal(np.float32(o["matrix"]), mt))
            if found[r["site"]] != 1:
                serr.append(f"pilot {r['site']}: {found[r['site']]} objects at its exact pose in the WRP")
        near = []
        for o in objs[:nb]:
            if "bridges" not in o["name"]:
                continue
            p = np.array(o["matrix"][9:12])
            for r in M:
                if r["model"] == o["name"] and np.hypot(*(np.array(r["matrix"][9:12]) - p)[[0, 2]]) < 2.0:
                    near.append([o["id"], rec_key(r)])
        if near:
            serr.append(f"{len(near)} base bridge objects within 2 m of a merged record")
        stage = dict(wrp=str(stage_wrp), base_objects=nb, appended=len(app), pilot_objects_at_pose=found, base_duplicates=near[:5], errors=serr)
        errs += serr
    ok = not errs
    return ok, dict(rule="merged = pilot + kit + run records, each once, no repeated keys or poses, finite matrices, no pilot site among "
                         "the sites; staged WRP: every merged record appended once at its exact float32 pose, the pilot included, "
                         "no base bridge of the same model within 2 m", counts=dict(merged=len(M), pilot=len(Pl), kit=len(K), bridges=len(Br)),
                    pilot_records_in_merged=pilot_in, stage=stage, errors=errs)


WT_WRP = Path("C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/tools/terrain")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("gate"); ap.add_argument("--run", required=True); ap.add_argument("--v4")
    for k in ("input", "input_env", "input_fp", "cover", "sites", "v5", "work", "out", "merged", "pilot", "kit", "stage_wrp", "base_wrp"):
        ap.add_argument("--" + k.replace("_", "-"))
    ap.add_argument("--fixture", nargs="*")
    a = ap.parse_args()
    run = gv.load_run(a.run); v4 = gv.load_run(a.v4) if a.v4 else None
    sites = json.load(open(a.sites)) if a.sites else []
    H0 = np.load(a.input)["heights"].astype(np.float64) if a.input else None
    env_in = np.load(a.input_env).astype(np.float64) if a.input_env else None
    work = Path(a.work or (Path(a.run) / "gates-work")); work.mkdir(parents=True, exist_ok=True)
    g = a.gate.upper()
    table = {"G1": lambda: gv.g1(run), "G2": lambda: gv.g2(run), "G3": lambda: gv.g3(run, v4, sites, a.fixture),
             "G4": lambda: gv.g4(run, sites), "G5": lambda: gv.g5(run, v4, H0, sites), "G6": lambda: gv.g6(run, v4, H0, sites),
             "G7": lambda: g7(run, v4, sites, a.fixture[0] if a.fixture else None, H0), "G8": lambda: g8(run, v4, sites, a.cover),
             "G9": lambda: g9(run, sites), "G10": lambda: g10(run, sites, H0, env_in),
             "G11": lambda: g11(run, sites, a.cover, work, a.input, a.input_fp, a.v5),
             "G12": lambda: g12(run, env_in, a.cover, work, a.input, a.input_fp),
             "G13": lambda: g13(run, sites, H0),
             "G14": lambda: g14(run, sites, a.merged, a.pilot, a.kit, a.stage_wrp, a.base_wrp)}
    ok, det = table[g]()
    det = dict(gate=g, verdict="PASS" if ok else "FAIL", run=str(a.run), **det)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(det, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)), newline="\n")
    print(f"{g} {'PASS' if ok else 'FAIL'}")
    print(json.dumps({k: v for k, v in det.items() if k not in ("gate", "verdict", "run", "rule")}, default=lambda o: o.item() if hasattr(o, "item") else str(o))[:3000])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

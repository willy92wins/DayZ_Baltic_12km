"""Mechanical gates for dam_v31.py placements, on the FINAL terrain and footprint of a chain (after bury_edges), against
the frozen BASE inputs of the dam step (T_IN, its footprint, its envelope and cover) and the pinned frozen-exception
contract of every dam site.

G1 seam (0.25 m plan raster over the dam records' bounding box + 30 m; terrain and pond surface on the planar NW-SE
   triangles; pond surface = footprint 'field', the visual LOD height; dam solid = geometry LOD of every record):
   a. no visible pond pixel is 8-adjacent to a visible engine-sea pixel at low, mid or high tide (0.5 / 0.75 / 1.0 m),
      'visible' meaning outside the dam solid at the pond surface height, resp. at the sea level;
   b. no exposed pond edge (visible pond pixel next to an uncovered pixel whose terrain is under the pond plane - 0.05)
      outside the dam solid within 18 m of visible sea;
   c. the cut line: every visible pond pixel within CUT_W of a cell that is in the BASE footprint and not in this one
      lies inside the dam solid (the wall stands on the whole line where the pond was cut back; a shoreline that moved
      inside a kept cell because the ground rose is not a cut and is not tested here).
G2 seat, per record, against Livonia's 7 dam_stone_40 measured with the same function (dam_v31.seat):
   water_rel within Livonia's range; every free end's exposure (roadway top - terrain at x_local = +-20, three lines)
   within Livonia's range (beyond the top = floating end, below the minimum = buried end); bottom clearance >= 0 (no air
   under the wall); top burial <= Livonia's maximum (the walkway not sunk deeper than any Livonia end). Bottom clearance
   is also compared with Livonia's range and reported, not gated (see the report's note). The free-end exposure has
   0.02 m of slack by construction: dam_v31 targets roadway top - Livonia max + 0.02 at the end samples.
G3 water invariants against the base inputs (no rounding; NaN = no water):
   footprint within this envelope and within the BASE envelope; no footprint, envelope or cover cell that the base
   lacks; the envelope and the cover lose exactly the contract's cut cells and the footprint loses only cut cells; every
   kept cell keeps its level in footprint plane, envelope and cover; no footprint cell over the engine sea (corner <
   0.75) in the window, and no more in the whole map than in the base footprint.
G4 frozen vertices against the base terrain and the contracts (each pinned by sha256 below and in dam_v31.py):
   every base array but 'heights' is unchanged (masks, classes, levels; NaN-equal) and the only new array is v31_dam,
   which marks exactly the contract vertices; no vertex is lower than in the base (exact float32 comparison); the moved
   frozen vertices (base reserve | platform | narva) are exactly the contract vertices, each with base height == old
   and final height == new +- 1e-4 m and the masks the contract states; the sea vertices turned dry are exactly the
   contract's; any other moved vertex lies within ABUT_R + 6 m of a record's plan footprint.
Usage: dam_gates_v31.py --terrain T --footprint FP --records R --envelope E --cover C --base-terrain T0
       --base-footprint FP0 --base-envelope E0 --base-cover C0 --contract K [--contract K2 ...] --out out.json [--label name]
Exit 0 only if every gate passes; 1 otherwise.
"""
import argparse, hashlib, json, os, sys
import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dam_v31 as D

PX, SEAM_R, EDGE_TOL = 0.25, 18.0, 0.05
CUT_W = 1.0     # m; the buried cut edge (vertex at plane + 0.06 over a 1.0 m bed) puts the waterline <= 0.34 m inside it
TIDES = (0.5, 0.75, 1.0)
N8 = np.ones((3, 3), bool)
# Same pins as dam_v31.PINNED_CONTRACTS, kept here on purpose: the gate does not trust the tool it checks.
PINNED_CONTRACTS = {"narva-dam": "28191cce4fe4ec7f240bbaf14cc7a07546748a98fdaa5221661b1649150668a2"}
NEW_KEYS_ALLOWED = {"v31_dam"}


def interp_cell(Hc, fx, fz):
    nw, ne, sw, se = Hc[..., 0], Hc[..., 1], Hc[..., 2], Hc[..., 3]
    return np.where(fx >= fz, nw + fx * (ne - nw) + fz * (se - ne), nw + fz * (sw - nw) + fx * (se - sw))


def raster(H, plane, field, x0, x1, z0, z1):
    xs = np.arange(x0 + PX / 2, x1, PX); zs = np.arange(z1 - PX / 2, z0, -PX)
    X, Z = np.meshgrid(xs, zs)
    c = np.floor(X / 6).astype(int); r = np.floor((D.ZTOP - Z) / 6).astype(int)
    fx = X / 6 - c; fz = (D.ZTOP - Z) / 6 - r
    T = interp_cell(np.stack([H[r, c], H[r, c + 1], H[r + 1, c], H[r + 1, c + 1]], -1), fx, fz)
    cov = np.isfinite(plane[r, c])
    P = np.where(cov, plane[r, c], np.nan)
    F = np.where(cov, interp_cell(np.nan_to_num(field[r, c], nan=-99.0), fx, fz), np.nan)
    pond = cov & (F > T)
    return X, Z, T, cov, P, F, pond


def nb_any(m):
    return binary_dilation(m, N8)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def same(a, b):
    """Exact equality, NaN == NaN, same shape and dtype."""
    return a.shape == b.shape and a.dtype == b.dtype and bool(np.array_equal(a, b, equal_nan=a.dtype.kind == "f"))


def cells(m):
    return {(int(r), int(c)) for r, c in np.argwhere(m)}


def c2v_any(m):
    o = np.zeros((m.shape[0] + 1, m.shape[1] + 1), bool)
    for dr in (0, 1):
        for dc in (0, 1):
            o[dr:dr + m.shape[0], dc:dc + m.shape[1]] |= m
    return o


def parse():
    ap = argparse.ArgumentParser()
    for k in ("terrain", "footprint", "records", "envelope", "cover", "base-terrain", "base-footprint", "base-envelope",
              "base-cover", "out"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--contract", action="append", required=True)
    ap.add_argument("--label", default="run")
    return ap.parse_args()


def main():
    a = parse()
    zt = np.load(a.terrain); zb = np.load(a.base_terrain)
    H = zt["heights"].astype(np.float64); H0 = zb["heights"].astype(np.float64)
    fp = np.load(a.footprint); plane = fp["plane"].astype(np.float64); field = fp["field"]
    bfp = np.load(a.base_footprint); bplane = bfp["plane"].astype(np.float64); bfield = bfp["field"]
    env = np.load(a.envelope); benv = np.load(a.base_envelope)
    cov_ = np.load(a.cover); bcov = np.load(a.base_cover)
    recs = [r for r in json.load(open(a.records)) if r["model"] == D.MODEL]
    mats = [r["matrix"] for r in recs]
    out = dict(label=a.label, terrain=a.terrain, footprint=a.footprint, records=a.records, n_dam_records=len(recs),
               inputs={k: dict(path=getattr(a, k.replace("-", "_")), sha256=sha(getattr(a, k.replace("-", "_"))))
                       for k in ("terrain", "footprint", "records", "envelope", "cover", "base-terrain", "base-footprint",
                                 "base-envelope", "base-cover")})
    gates = {}
    # ---------------------------------------------------------------- contracts (used by G3 and G4)
    con_checks, contracts = {}, []
    for p in a.contract:
        h = sha(p) if os.path.isfile(p) else None
        con = json.load(open(p)) if h else {}
        sid = con.get("site")
        ok = h is not None and sid in PINNED_CONTRACTS and h == PINNED_CONTRACTS[sid] == D.PINNED_CONTRACTS.get(sid) \
            and con.get("schema") == "dam-frozen-exception.v1"
        con_checks[p] = dict(site=sid, sha256=h, pinned=PINNED_CONTRACTS.get(sid), ok=bool(ok))
        if ok:
            contracts.append(con)
    rec_sites = sorted({r["site"] for r in recs})
    con_sites = sorted(c["site"] for c in contracts)
    contracts_ok = all(v["ok"] for v in con_checks.values()) and rec_sites == con_sites
    out["contracts"] = dict(files=con_checks, record_sites=rec_sites, contract_sites=con_sites, ok=contracts_ok)
    cv = {}                      # (r, c) -> contract vertex
    for con in contracts:
        for v in con["vertices"]:
            cv[(v["r"], v["c"])] = v
    cut_set = {(k["r"], k["c"]) for con in contracts for k in con["cut_cells"]}
    # ---------------------------------------------------------------- G1 seam
    if mats:
        pts = np.array([[m[9] + sx * 20.03 * m[0] + sz * 2.04 * m[6], m[11] + sx * 20.03 * m[2] + sz * 2.04 * m[8]]
                        for m in mats for sx in (-1, 1) for sz in (-1, 1)])
    else:
        pts = np.array(json.loads(os.environ.get("DAM_GATE_WINDOW", "[[2384, 6936], [2472, 6972]]")))
    x0, z0 = np.floor(pts.min(0) - 30.0); x1, z1 = np.ceil(pts.max(0) + 30.0)
    out["window"] = [float(x0), float(x1), float(z0), float(z1)]
    X, Z, T, cov, P, F, pond = raster(H, plane, field, x0, x1, z0, z1)
    _, _, Tb, covb, Pb, Fb, pondb = raster(H0, bplane, bfield, x0, x1, z0, z1)
    yref = float(np.nanmax(P)) if np.isfinite(P).any() else 2.0
    hid_p = D.solid(mats, X, np.where(np.isfinite(F), F, yref), Z) if mats else np.zeros(X.shape, bool)
    hid_ref = D.solid(mats, X, np.full(X.shape, yref), Z) if mats else np.zeros(X.shape, bool)
    vis_pond = pond & ~hid_p
    g1 = dict(pond_px=int(pond.sum()), pond_hidden_px=int((pond & hid_p).sum()))
    ok = True
    for L in TIDES:
        sea = (~cov) & (T < L)
        hid_s = D.solid(mats, X, np.full(X.shape, L), Z) if mats else np.zeros(X.shape, bool)
        vis_sea = sea & ~hid_s
        adj = vis_pond & nb_any(vis_sea)
        expo = np.zeros(X.shape, bool)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr or dc:
                    nu = np.roll(np.roll(~cov, -dr, 0), -dc, 1); nT = np.roll(np.roll(T, -dr, 0), -dc, 1)
                    nh = np.roll(np.roll(hid_ref, -dr, 0), -dc, 1)
                    expo |= vis_pond & nu & (nT < P - EDGE_TOL) & ~nh
        expo[[0, -1], :] = False; expo[:, [0, -1]] = False
        dsea = distance_transform_edt(~vis_sea) * PX if vis_sea.any() else np.full(X.shape, np.inf)
        expo_near = expo & (dsea <= SEAM_R)
        g1[f"tide_{L}"] = dict(sea_px=int(sea.sum()), sea_hidden_px=int((sea & hid_s).sum()), pond_sea_adjacent_px=int(adj.sum()),
                               exposed_edge_px_near_sea=int(expo_near.sum()),
                               adjacent_xz=[[round(float(X[i, j]), 2), round(float(Z[i, j]), 2)] for i, j in np.argwhere(adj)[:20]],
                               exposed_xz=[[round(float(X[i, j]), 2), round(float(Z[i, j]), 2)] for i, j in np.argwhere(expo_near)[:20]])
        ok &= not adj.any() and not expo_near.any()
    removed = covb & ~cov
    dcut = distance_transform_edt(~removed) * PX if removed.any() else np.full(X.shape, np.inf)
    new_edge = pond & (dcut <= CUT_W)
    new_edge_vis = new_edge & ~hid_p
    g1["removed_cell_px"] = int(removed.sum()); g1["new_edge_px"] = int(new_edge.sum()); g1["new_edge_visible_px"] = int(new_edge_vis.sum())
    g1["new_edge_visible_xz"] = [[round(float(X[i, j]), 2), round(float(Z[i, j]), 2)] for i, j in np.argwhere(new_edge_vis)[:20]]
    ok &= not new_edge_vis.any()
    gates["G1_seam"] = dict(status="PASS" if ok else "FAIL", **g1)
    # ---------------------------------------------------------------- G2 seat
    liv = D.seat_livonia(); rng = D.ranges(liv)
    sample = lambda x, z: D.height(H, x, z)
    seats, ok2 = [], bool(mats)
    for k, m in enumerate(mats):
        ax = np.array([m[0], m[2]]); t = np.array([m[9], m[11]])
        free = []
        for sgn in (-1, 1):
            e = t + sgn * 20.03 * ax
            joined = any(np.hypot(*(e - (np.array([o[9], o[11]]) - sgn * 20.03 * np.array([o[0], o[2]])))) < 0.5 for j, o in enumerate(mats) if j != k)
            if not joined:
                free.append(sgn)
        az = np.array([m[6], m[8]])
        best = None
        for side in (-1, 1):
            vals = []
            for xl in np.arange(-19.0, 19.01, 2.0):
                for dz in (3.0, 4.5, 6.0):
                    p = t + xl * ax + side * dz * az
                    c = int(p[0] // 6); r = int((D.ZTOP - p[1]) // 6)
                    if np.isfinite(plane[r, c]):
                        vals.append(float(plane[r, c]))
            if vals and (best is None or len(vals) > best[1]):
                best = (max(vals), len(vals), side)
        st = D.seat(sample, m, tuple(free), None if best is None else best[0])
        st["free_ends"] = free; st["upstream_side"] = None if best is None else best[2]
        chk = dict(water=st["water_rel"] is not None and rng["water_rel"][0] <= st["water_rel"] <= rng["water_rel"][1],
                   ends=all(rng["end_exposure"][0] <= e <= rng["end_exposure"][1] for e in st["end_exposure"]),
                   no_air=st["bottom_clearance_min"] >= 0.0,
                   top_not_buried=st["top_burial_max"] <= rng["top_burial_max"][1])
        st["checks"] = chk
        st["end_exposure_margin_m"] = round(rng["end_exposure"][1] - max(st["end_exposure"]), 3) if st["end_exposure"] else None
        st["bottom_clearance_vs_livonia"] = "inside" if rng["bottom_clearance_min"][0] <= st["bottom_clearance_min"] <= rng["bottom_clearance_min"][1] else "outside (not gated)"
        ok2 &= all(chk.values())
        seats.append(st)
    gates["G2_seat"] = dict(status="PASS" if ok2 else "FAIL", livonia_ranges=rng, records=seats,
                            note="bottom clearance = how deep the base sits under the lowest ground of the footprint; "
                                 "Livonia's ponds are 2.5-5 m deep at the wall, the Narva pond 1 m, so at Livonia's "
                                 "water_rel the base sits deeper than Livonia's; it is invisible and only reported")
    # ---------------------------------------------------------------- G3 water invariants
    envc, benvc = np.isfinite(env), np.isfinite(benv)
    covc, bcovc = np.isfinite(cov_), np.isfinite(bcov)
    fpc, bfpc = np.isfinite(plane), np.isfinite(bplane)
    cmin = lambda A: np.minimum.reduce([A[:-1, :-1], A[1:, :-1], A[:-1, 1:], A[1:, 1:]])
    over_sea = fpc & (cmin(H) < 0.75); over_sea_b = bfpc & (cmin(H0) < 0.75)
    r0, r1 = int((D.ZTOP - z1) // 6), int((D.ZTOP - z0) // 6) + 1; c0, c1 = int(x0 // 6), int(x1 // 6) + 1
    both_fp, both_env, both_cov = fpc & bfpc, envc & benvc, covc & bcovc
    env_removed, cov_removed, fp_removed = cells(benvc & ~envc), cells(bcovc & ~covc), cells(bfpc & ~fpc)
    g3 = dict(footprint_outside_envelope=int((fpc & ~envc).sum()), footprint_outside_base_envelope=int((fpc & ~benvc).sum()),
              new_footprint_cells_vs_base=int((fpc & ~bfpc).sum()), new_envelope_cells_vs_base=int((envc & ~benvc).sum()),
              new_cover_cells_vs_base=int((covc & ~bcovc).sum()),
              footprint_removed=len(fp_removed), footprint_removed_outside_cut=len(fp_removed - cut_set),
              envelope_removed=len(env_removed), cover_removed=len(cov_removed), contract_cut_cells=len(cut_set),
              footprint_level_changed=int((both_fp & (plane != bplane)).sum()),
              envelope_level_changed=int((both_env & (env != benv)).sum()),
              cover_level_changed=int((both_cov & (cov_ != bcov)).sum()),
              over_sea_window=int(over_sea[r0:r1, c0:c1].sum()), over_sea_map=int(over_sea.sum()), over_sea_map_base=int(over_sea_b.sum()),
              new_footprint_xz=[[int(6 * c), int(D.ZTOP - 6 * r)] for r, c in np.argwhere(fpc & ~bfpc)[:10]],
              new_envelope_xz=[[int(6 * c), int(D.ZTOP - 6 * r)] for r, c in np.argwhere(envc & ~benvc)[:10]])
    chk3 = dict(contracts=contracts_ok,
                footprint_in_envelope=g3["footprint_outside_envelope"] == 0,
                footprint_in_base_envelope=g3["footprint_outside_base_envelope"] == 0,
                no_new_footprint=g3["new_footprint_cells_vs_base"] == 0,
                no_new_envelope=g3["new_envelope_cells_vs_base"] == 0,
                no_new_cover=g3["new_cover_cells_vs_base"] == 0,
                envelope_cut_is_contract=env_removed == cut_set,
                cover_cut_is_contract=cov_removed == cut_set,
                footprint_removed_within_cut=g3["footprint_removed_outside_cut"] == 0,
                levels_kept=g3["footprint_level_changed"] == 0 and g3["envelope_level_changed"] == 0 and g3["cover_level_changed"] == 0,
                not_over_sea=g3["over_sea_window"] == 0 and g3["over_sea_map"] <= g3["over_sea_map_base"])
    gates["G3_water"] = dict(status="PASS" if all(chk3.values()) else "FAIL", checks=chk3, **g3)
    # ---------------------------------------------------------------- G4 frozen vertices
    base_keys = [k for k in zb.files if k != "heights"]
    mask_changed = [k for k in base_keys if k not in zt.files or not same(zt[k], zb[k])]
    new_keys = sorted(set(zt.files) - set(zb.files))
    moved = H != H0
    lowered = H < H0
    frozen = zb["reserve"] | zb["platform"] | zb["narva"]
    fz_set = cells(moved & frozen)
    want = set(cv)
    old_bad = [[v["x"], v["z"]] for k, v in sorted(cv.items()) if np.float32(H0[k]) != np.float32(v["old"])]
    new_bad = [[v["x"], v["z"], float(H[k]), v["new"]] for k, v in sorted(cv.items()) if abs(float(H[k]) - v["new"]) > D.NEW_TOL]
    cmask_bad = [[v["x"], v["z"]] for k, v in sorted(cv.items()) if any(bool(zb[m][k]) != v[m] for m in ("reserve", "platform", "narva"))]
    vfp_b = c2v_any(bcovc | benvc)
    sea_dry = cells(moved & (H0 < D.SEA_DRY) & ~vfp_b & (H >= D.SEA_DRY))
    dry_want = {k for k, v in cv.items() if v["sea_to_dry"]}
    v31 = cells(zt["v31_dam"]) if "v31_dam" in zt.files else None
    other = moved.copy()
    for k in want:
        other[k] = False
    rr, cc = np.nonzero(other)
    far = []
    for r, c in zip(rr, cc):
        x, zz = 6.0 * c, D.ZTOP - 6.0 * r
        dmin = min(abs(float(np.array([x - m[9], zz - m[11]]) @ np.array([m[6], m[8]]))) +
                   max(0.0, abs(float(np.array([x - m[9], zz - m[11]]) @ np.array([m[0], m[2]]))) - 20.03) for m in mats) if mats else 1e9
        if dmin > D.ABUT_R + 6.0:
            far.append([int(x), int(zz)])
    g4 = dict(moved=int(moved.sum()), frozen_moved=len(fz_set), contract_vertices=len(want),
              frozen_moved_outside_contract=[[6 * c, int(D.ZTOP - 6 * r)] for r, c in sorted(fz_set - want)][:20],
              contract_vertices_not_moved=[[6 * c, int(D.ZTOP - 6 * r)] for r, c in sorted(want - fz_set)][:20],
              old_height_mismatch=old_bad[:20], new_height_mismatch=new_bad[:20], contract_mask_mismatch=cmask_bad[:20],
              lowered=int(lowered.sum()), max_lower_m=float((H - H0).min()) if moved.any() else 0.0,
              lowered_xz=[[int(6 * c), int(D.ZTOP - 6 * r)] for r, c in np.argwhere(lowered)[:10]],
              arrays_changed=mask_changed, arrays_new=new_keys,
              v31_dam_vertices=None if v31 is None else len(v31),
              sea_to_dry=[[6 * c, int(D.ZTOP - 6 * r)] for r, c in sorted(sea_dry)], sea_to_dry_contract=len(dry_want),
              moved_far_from_dam=far[:20], n_far=len(far),
              max_raise=round(float((H - H0).max()), 3) if moved.any() else 0.0)
    chk4 = dict(contracts=contracts_ok,
                arrays_unchanged=not mask_changed,
                only_v31_dam_new=set(new_keys) <= NEW_KEYS_ALLOWED,
                v31_dam_is_contract=v31 is not None and v31 == want,
                no_lowering=not lowered.any(),
                frozen_moved_is_contract=fz_set == want,
                old_heights=not old_bad,
                new_heights=not new_bad,
                contract_masks=not cmask_bad,
                sea_to_dry_is_contract=sea_dry == dry_want,
                none_far=not far)
    gates["G4_frozen"] = dict(status="PASS" if all(chk4.values()) else "FAIL", checks=chk4, **g4)
    out["gates"] = gates
    out["verdict"] = "PASS" if all(g["status"] == "PASS" for g in gates.values()) else "FAIL"
    with open(a.out, "w", newline="\n") as f:
        json.dump(out, f, indent=1)
    print(a.label, out["verdict"], {k: g["status"] for k, g in gates.items()},
          {k: [p for p, v in g["checks"].items() if not v] for k, g in gates.items() if "checks" in g})
    sys.exit(0 if out["verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main()

"""EV88-Q single-patch fairing author. Default invocation is read-only preflight; --solve is gated."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(r"E:/DayZ-Baltic-Build")
OUT = ROOT / "v30-wide-bank-fairing-pilot-20261010"
B_DIR = ROOT / "v30-mixed-bank-incremental-fixed-20261010"
EV79_DIR = ROOT / "v30-narva-dry-bank-relief-20261010"
PRIOR_DIR = ROOT / "v30-remaining-exact-dry-support-20261009"
CENTER = (840, 370)
SEA = 0.85
CELL = 6.0
STRICT_EPS = 1e-4
HARD_TIMEOUT_S = 120.0
EXPECTED = {
    "B": "f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0",
    "EV79": "dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c",
    "P": "768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0",
    "F": "f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c",
    "EV79_CONSTRAINTS": "ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c",
    "PRIOR_CONSTRAINTS": "18a3639907a68a8ceda37fe2a402884c2c4bc111fe8c7775d0a7d07dac02d370",
}
PATHS = {
    "B": B_DIR / "candidate/terrain.npz",
    "EV79": EV79_DIR / "candidate/terrain.npz",
    "P": EV79_DIR / "candidate/plane.npy",
    "F": EV79_DIR / "candidate/visible-field.npy",
    "EV79_CONSTRAINTS": EV79_DIR / "constraints.npz",
    "PRIOR_CONSTRAINTS": PRIOR_DIR / "constraints.npz",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def verify_linked_identities(schema_path: Path):
    schema=json.loads(schema_path.read_text(encoding="utf-8"))
    rows=schema["identity_inputs"]
    observed={}
    for name,row in rows.items():
        if name=="compiled_WRP_identity":
            deploy=json.loads(Path(rows["B_deploy_manifest"]["path"]).read_text(encoding="utf-8"))
            value=deploy.get("compiled_wrp_sha256")
            if value != row["sha256"]:
                raise RuntimeError(f"embedded compiled WRP identity mismatch: {value}")
            observed[name]={"path":row["path"],"sha256":value,"verified_via":rows["B_deploy_manifest"]["path"]}
            continue
        path=Path(row["path"])
        value=sha256(path)
        if value != row["sha256"]:
            raise RuntimeError(f"linked identity mismatch {name}: {value} != {row['sha256']}")
        observed[name]={"path":str(path),"sha256":value}
    return schema,observed


def canonical_sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def windows():
    r, c = CENTER
    return {
        "outer17": (r - 8, r + 9, c - 8, c + 9),
        "core13": (r - 6, r + 7, c - 6, c + 7),
    }


def crossing_height_bounds(hw: float, lw: float, hd: float, ld: float, edge_len: float, max_shift: float = 1.0):
    """Return admissible height interval at dry endpoint; wet endpoint is fixed.

    Parameter t runs from wet endpoint to dry endpoint. Formula is monotone
    decreasing in dry height, so both movement directions become scalar bounds.
    """
    gw, gd = float(hw) - float(lw), float(hd) - float(ld)
    if not (gw < 0.0 and gd > 0.0 and edge_len > 0 and max_shift >= 0):
        raise ValueError("crossing must have fixed wet and dry endpoints")
    t0 = -gw / (gd - gw)
    dt = max_shift / edge_len
    tlo, thi = max(0.0, t0 - dt), min(1.0, t0 + dt)
    if not (0.0 < t0 < 1.0 and tlo <= t0 <= thi):
        raise ValueError("invalid baseline crossing")
    lower = float(ld) + gw * (1.0 - 1.0 / thi)
    upper = math.inf if tlo <= 0.0 else float(ld) + gw * (1.0 - 1.0 / tlo)
    return lower, upper, {"t0": t0, "tlo": tlo, "thi": thi, "edge_len_m": edge_len, "max_shift_m": max_shift}


def new_nearflat_cells(before: np.ndarray, after: np.ndarray, threshold: float):
    """Mask of 2x2 spans that newly enter the frozen near-flat class."""
    def spans(a):
        x = np.stack((a[:-1, :-1], a[:-1, 1:], a[1:, :-1], a[1:, 1:]), axis=0)
        return np.max(x, axis=0) - np.min(x, axis=0)
    bspan, hspan = spans(np.asarray(before)), spans(np.asarray(after))
    return (bspan > threshold) & (hspan <= threshold)


def one_to_one_extrema_match(old_extrema, new_extrema, radius=1):
    """Bipartite augmenting-path matching; same type, Chebyshev radius, B prom >= H prom."""
    old = list(old_extrema)
    new = list(new_extrema)
    adj = []
    for h in new:
        choices = [i for i, b in enumerate(old)
                   if b[2] == h[2] and max(abs(int(b[0]) - int(h[0])), abs(int(b[1]) - int(h[1]))) <= radius
                   and float(b[3]) + 1e-12 >= float(h[3])]
        choices.sort(key=lambda i: (max(abs(int(old[i][0]) - int(h[0])), abs(int(old[i][1]) - int(h[1]))), -float(old[i][3]), i))
        adj.append(choices)
    owner = [-1] * len(old)
    def augment(hi, seen):
        for oi in adj[hi]:
            if oi in seen:
                continue
            seen.add(oi)
            if owner[oi] < 0 or augment(owner[oi], seen):
                owner[oi] = hi
                return True
        return False
    matched = sum(augment(i, set()) for i in range(len(new)))
    return {"matched": matched, "new_count": len(new), "unmatched_new_indices": [i for i in range(len(new)) if i not in owner], "pass": matched == len(new)}


def collar_energy_gate(before_energy: float, after_energy: float) -> bool:
    return float(after_energy) <= float(before_energy)


def collar_hinge_gate(before_max_deg: float, after_max_deg: float) -> bool:
    return float(after_max_deg) <= float(before_max_deg)


def no_new_steep_hinges(before_deg: np.ndarray, after_deg: np.ndarray, threshold: float = 30.0001) -> bool:
    before = np.asarray(before_deg, dtype=np.float64) > threshold
    after = np.asarray(after_deg, dtype=np.float64) > threshold
    return not bool(np.any(after & ~before))


def slope_gate(before_slopes: np.ndarray, after_slopes: np.ndarray) -> bool:
    b, h = np.asarray(before_slopes, dtype=np.float64), np.asarray(after_slopes, dtype=np.float64)
    if b.shape != h.shape:
        return False
    return bool(np.all(h <= np.maximum(35.0, b)))


def fixed_unchanged(before: np.ndarray, after: np.ndarray, fixed_mask: np.ndarray) -> bool:
    return bool(np.array_equal(np.asarray(before)[fixed_mask], np.asarray(after)[fixed_mask]))


def rowcol_prominence(h: np.ndarray):
    """Largest strict cardinal prominence of any peak in each row and column."""
    a = np.asarray(h, dtype=np.float64)
    row = np.zeros(a.shape[0], dtype=np.float64)
    col = np.zeros(a.shape[1], dtype=np.float64)
    if a.shape[1] >= 3:
        p = np.minimum(a[:, 1:-1] - a[:, :-2], a[:, 1:-1] - a[:, 2:])
        row = np.maximum(row, np.maximum(0.0, np.max(p, axis=1)))
    if a.shape[0] >= 3:
        p = np.minimum(a[1:-1, :] - a[:-2, :], a[1:-1, :] - a[2:, :])
        col = np.maximum(col, np.maximum(0.0, np.max(p, axis=0)))
    return row, col


def no_rowcol_prominence_increase(before: np.ndarray, after: np.ndarray) -> bool:
    br, bc = rowcol_prominence(before); ar, ac = rowcol_prominence(after)
    return bool(np.all(ar <= br + 1e-12) and np.all(ac <= bc + 1e-12))


def hinge_coeffs(kind: str, r: int, c: int):
    if kind == "xx": return ((r, c, 1.0), (r, c + 1, -2.0), (r, c + 2, 1.0))
    if kind == "zz": return ((r, c, 1.0), (r + 1, c, -2.0), (r + 2, c, 1.0))
    if kind == "xz": return ((r, c, -0.25), (r, c + 2, 0.25), (r + 2, c, 0.25), (r + 2, c + 2, -0.25))
    raise ValueError(kind)


def frozen_stencils(vars_rc, bounds):
    r0, r1, c0, c1 = bounds
    vset = {tuple(map(int, x)) for x in vars_rc}
    out = []
    for r in range(r0, r1):
        for c in range(c0, c1 - 2):
            if any((rr, cc) in vset for rr, cc, _ in hinge_coeffs("xx", r, c)):
                out.append(("xx", r, c))
    for r in range(r0, r1 - 2):
        for c in range(c0, c1):
            if any((rr, cc) in vset for rr, cc, _ in hinge_coeffs("zz", r, c)):
                out.append(("zz", r, c))
    for r in range(r0, r1 - 2):
        for c in range(c0, c1 - 2):
            if any((rr, cc) in vset for rr, cc, _ in hinge_coeffs("xz", r, c)):
                out.append(("xz", r, c))
    return out


def _corner_values_local(p, f, r, c):
    return ((r, c, 0), (r, c + 1, 1), (r + 1, c, 2), (r + 1, c + 1, 3))


def load_inputs():
    got = {k: sha256(v) for k, v in PATHS.items()}
    for k, want in EXPECTED.items():
        if got[k] != want:
            raise RuntimeError(f"{k} identity mismatch: {got[k]} != {want}")
    b = load_npz(PATHS["B"])
    e = load_npz(PATHS["EV79"])
    p = np.load(PATHS["P"], allow_pickle=False)
    f = np.load(PATHS["F"], allow_pickle=False)
    if np.isinf(p).any() or np.isinf(f).any():
        raise RuntimeError("P/F contains infinity; only NaN has defined absence semantics")
    con = load_npz(PATHS["EV79_CONSTRAINTS"])
    prior = load_npz(PATHS["PRIOR_CONSTRAINTS"])
    if b["heights"].shape != (2048, 2048) or p.shape != (2047, 2047) or f.shape != (2047, 2047, 4):
        raise RuntimeError("unexpected B/P/F dimensions")
    return got, b, e, p, f, con, prior


def local_inputs():
    got, b, e, p, f, con, prior = load_inputs()
    (r0, r1, c0, c1) = windows()["outer17"]
    cls = b["cls"][r0:r1, c0:c1]
    hb = b["heights"][r0:r1, c0:c1]
    he = e["heights"][r0:r1, c0:c1]
    # Incident corner samples: max design level plus actual wetness for every sample.
    lev = np.full(hb.shape, SEA, dtype=np.float64)
    actual_wet = hb <= SEA
    partial_cells = []
    crossing_cells = set()
    for cr in range(r0 - 1, r1):
        for cc in range(c0 - 1, c1):
            if not (0 <= cr < p.shape[0] and 0 <= cc < p.shape[1]):
                continue
            fv = np.asarray(f[cr, cc], dtype=np.float64)
            finite_f = np.isfinite(fv)
            if 0 < int(finite_f.sum()) < 4:
                partial_cells.append((cr, cc))
            pl = float(p[cr, cc])
            for vr, vc, k in _corner_values_local(p, f, cr, cc):
                if not (r0 <= vr < r1 and c0 <= vc < c1):
                    continue
                i, j = vr - r0, vc - c0
                samples = [SEA]
                if np.isfinite(pl): samples.append(pl)
                if finite_f[k]: samples.append(float(fv[k]))
                lev[i, j] = max(lev[i, j], max(samples))
                if hb[i, j] <= max(samples):
                    actual_wet[i, j] = True
    other = con["other_fixed"][r0:r1, c0:c1].astype(bool)
    eng = con["engineering_halo"][r0:r1, c0:c1].astype(bool)
    large = prior["large_lake_banks"][r0:r1, c0:c1].astype(bool)
    reserve = b["reserve"][r0:r1, c0:c1].astype(bool)
    platform = b["platform"][r0:r1, c0:c1].astype(bool)
    protect = other | eng | large | reserve | platform | (cls != 0) | actual_wet
    mr0, mr1, mc0, mc1 = windows()["core13"]
    sl = np.s_[mr0-r0:mr1-r0, mc0-c0:mc1-c0]
    mutable_mask = ~protect[sl]
    rr, cc = np.nonzero(mutable_mask)
    vars_rc = np.column_stack((rr + mr0, cc + mc0)).astype(np.int32)
    lower = np.maximum(he[sl].astype(np.float64) - 2.0, np.minimum(he[sl].astype(np.float64), 1.8))
    lower = np.maximum(lower, np.minimum(he[sl].astype(np.float64), lev[sl] + STRICT_EPS))
    upper = np.minimum(he[sl].astype(np.float64) + 2.0, hb[sl].astype(np.float64) + 0.50)
    out = {
        "hashes": got, "b": b, "ev79": e, "p": p, "f": f, "constraints": con, "prior": prior,
        "bounds17": (r0, r1, c0, c1), "bounds13": (mr0, mr1, mc0, mc1), "B_local": hb,
        "EV79_local": he, "P_local": p[r0-1:r1, c0-1:c1], "F_local": f[r0-1:r1, c0-1:c1],
        "water_level_local": lev, "actual_wet_local": actual_wet, "protect_local": protect,
        "variables": vars_rc, "lower13": lower, "upper13": upper, "partial_cells": partial_cells,
        "masks": {"other_fixed": other, "engineering_halo": eng, "large_lake_banks": large,
                  "reserve": reserve, "platform": platform, "nonzero_class": cls != 0, "actually_wet": actual_wet},
    }
    return out


def crossing_bounds(local):
    h, p, f = local["B_local"], local["p"], local["f"]
    r0, r1, c0, c1 = local["bounds17"]
    vars_rc = {tuple(x) for x in local["variables"].tolist()}
    # Full-world scalar bounds for only the 13x13 mutable coordinates.
    lb, ub = local["lower13"].copy(), local["upper13"].copy()
    mr0, mr1, mc0, mc1 = local["bounds13"]
    records = []
    partial = set(local["partial_cells"])
    if partial:
        raise RuntimeError(f"partial F cells touch local evaluation window: {sorted(partial)[:8]}")
    offsets = ((0,0,0),(0,1,1),(1,0,2),(1,1,3))
    tris = ((0,1,3),(0,2,3))
    for cr in range(r0-1, r1):
        for cc in range(c0-1, c1):
            if not (0 <= cr < p.shape[0] and 0 <= cc < p.shape[1]): continue
            cell_f = np.asarray(f[cr, cc], dtype=np.float64)
            cell_p = float(p[cr, cc])
            layers = [("SEA", (SEA,)*4)]
            if np.isfinite(cell_p): layers.append(("P", (cell_p,)*4))
            if np.isfinite(cell_f).all(): layers.append(("F", tuple(map(float, cell_f))))
            for layer_name, levels in layers:
                for tri in tris:
                    for ia, ib in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
                        va = (cr+offsets[ia][0], cc+offsets[ia][1]); vb=(cr+offsets[ib][0], cc+offsets[ib][1])
                        if not (r0 <= va[0] < r1 and c0 <= va[1] < c1 and r0 <= vb[0] < r1 and c0 <= vb[1] < c1):
                            continue
                        ia_loc=(va[0]-r0,va[1]-c0); ib_loc=(vb[0]-r0,vb[1]-c0)
                        ga=float(h[ia_loc]-levels[ia]); gb=float(h[ib_loc]-levels[ib])
                        if ga*gb >= 0: continue
                        va_mut=va in vars_rc; vb_mut=vb in vars_rc
                        if va_mut and vb_mut: raise RuntimeError(f"crossing edge has two mutable endpoints: {va},{vb},{layer_name}")
                        if va_mut == vb_mut: continue
                        dry,dry_i,wet,wet_i = (va,ia, vb,ib) if va_mut else (vb,ib,va,ia)
                        gd=float(h[dry[0]-r0,dry[1]-c0]-levels[dry_i]); gw=float(h[wet[0]-r0,wet[1]-c0]-levels[wet_i])
                        if not (gd>0 and gw<0): raise RuntimeError(f"crossing endpoint role mismatch {dry},{wet},{layer_name}")
                        length=CELL if va[0]==vb[0] or va[1]==vb[1] else CELL*math.sqrt(2.)
                        lo,hi,detail=crossing_height_bounds(float(h[wet[0]-r0,wet[1]-c0]),float(levels[wet_i]),float(h[dry[0]-r0,dry[1]-c0]),float(levels[dry_i]),length)
                        ir,ic=dry[0]-mr0,dry[1]-mc0
                        lb[ir,ic]=max(lb[ir,ic],lo); ub[ir,ic]=min(ub[ir,ic],hi)
                        records.append({"layer":layer_name,"cell_rc":[cr,cc],"edge_rc":[list(va),list(vb)],"dry_rc":list(dry),"wet_rc":list(wet),**detail,"lower_m":lo,"upper_m":(hi if np.isfinite(hi) else None),"upper_unbounded":not np.isfinite(hi)})
    if np.any(lb>ub): raise RuntimeError("crossing/floor intervals are empty")
    return lb,ub,records


def build_matrix(local):
    vars_rc=local["variables"]; bounds=local["bounds17"]
    stencils=frozen_stencils(vars_rc,bounds)
    idx={tuple(rc):i for i,rc in enumerate(vars_rc.tolist())}
    base=local["B_local"]; r0,r1,c0,c1=bounds
    A=[]; b=[]; weights=[]
    for kind,r,c in stencils:
        scale=math.sqrt(2.0) if kind=="xz" else 1.0
        row=np.zeros(len(vars_rc),np.float64); fixed=0.0
        for rr,cc,coef in hinge_coeffs(kind,r,c):
            coeff=coef*scale
            key=(rr,cc)
            if key in idx: row[idx[key]]=coeff
            else: fixed += coeff*float(base[rr-r0,cc-c0])
        A.append(row); b.append(-fixed); weights.append(kind)
    for i,(rr,cc) in enumerate(vars_rc):
        row=np.zeros(len(vars_rc),np.float64); row[i]=0.25
        A.append(row); b.append(0.25*float(base[rr-r0,cc-c0])); weights.append("fidelity")
    return np.asarray(A,np.float64),np.asarray(b,np.float64),stencils,weights


def _solve_worker(a,b,lower,upper,conn):
    try:
        from scipy.optimize import lsq_linear
        res=lsq_linear(a,b,bounds=(lower,upper),method="bvls",tol=1e-10,max_iter=1000,verbose=0)
        conn.send({"success":bool(res.success),"status":int(res.status),"message":str(res.message),"nit":int(res.nit),"cost":float(res.cost),"x":res.x.tolist()})
    except BaseException as ex:
        conn.send({"error":repr(ex)})
    finally:
        conn.close()


def solve_once(a,b,lower,upper,timeout=HARD_TIMEOUT_S):
    """One dense BVLS call, forcibly terminable by its parent; not run in preflight."""
    ctx=mp.get_context("spawn"); recv,send=ctx.Pipe(duplex=False)
    proc=ctx.Process(target=_solve_worker,args=(a,b,lower,upper,send),daemon=True)
    proc.start(); send.close(); proc.join(timeout)
    if proc.is_alive():
        proc.terminate(); proc.join()
        raise TimeoutError(f"single BVLS call exceeded hard timeout {timeout}s")
    if not recv.poll(): raise RuntimeError(f"BVLS worker exited without result, exitcode={proc.exitcode}")
    result=recv.recv(); recv.close()
    if "error" in result: raise RuntimeError(result["error"])
    if not result["success"]: raise RuntimeError(f"BVLS unsuccessful: {result}")
    return result


def preflight_report(local, lower, upper, stencils, matrix_shape):
    # B is stored float32; promote exact stored heights before differences and quantile.
    before=local["B_local"][2:15,2:15].astype(np.float64)
    spans=np.stack((before[:-1,:-1],before[:-1,1:],before[1:,:-1],before[1:,1:]),axis=0).max(axis=0)-np.stack((before[:-1,:-1],before[:-1,1:],before[1:,:-1],before[1:,1:]),axis=0).min(axis=0)
    tau=float(np.quantile(spans.ravel(),0.05,method="linear"))
    fixed_collar=set()
    r0,r1,c0,c1=local["bounds17"]
    for r in range(r0,r1):
        for c in range(c0,c1):
            if r<r0+2 or r>=r1-2 or c<c0+2 or c>=c1-2: fixed_collar.add((r,c))
    collar_stencils=[s for s in stencils if any((rr,cc) in fixed_collar for rr,cc,_ in hinge_coeffs(s[0],s[1],s[2]))]
    varsha=hashlib.sha256(np.asarray(local["variables"],dtype="<i4").tobytes()).hexdigest()
    stencil_rows=[list(x) for x in stencils]
    stencilsha=canonical_sha(stencil_rows)
    return {
        "status":"PREFLIGHT_READY_SOLVER_NOT_RUN",
        "input_sha256":local["hashes"],
        "center_rc":list(CENTER),"windows_rc_halfopen":{k:list(v) for k,v in windows().items()},
        "mutable_count":int(len(local["variables"])),"mutable_nodes_sha256_le_i32":varsha,
        "partial_F_cells_touching_window":len(local["partial_cells"]),
        "crossing_records":len(local.get("crossings",[])),"frozen_stencils":len(stencils),"collar_impact_stencils":len(collar_stencils),
        "matrix_shape":list(matrix_shape),"bounds_empty":bool(np.any(lower>upper)),
        "near_flat_threshold_m":tau,"near_flat_source":"B stored float32 heights promoted to float64 before 2x2 max-min; 144 core13 spans; np.quantile(q=.05,method='linear')",
        "core13_spans_count":int(spans.size),"core13_nearflat_count_at_threshold":int(np.count_nonzero(spans<=tau)),
        "stencil_sha256_canonical_json":stencilsha,
        "collar_stencil_sha256_canonical_json":canonical_sha([list(x) for x in collar_stencils]),
        "scipy":None,
        "solver_invoked":False,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--solve",action="store_true",help="run the one BVLS solve; requires integrator approval")
    args=parser.parse_args()
    plan_path=OUT/"plan.md"
    schema_path=OUT/"author/preflight/receipt-schema.json"
    local=local_inputs()
    if len(local["variables"]) != 98:
        raise RuntimeError(f"mutable count changed from frozen expected 98: {len(local['variables'])}")
    lb,ub,crossings=crossing_bounds(local); local["crossings"]=crossings
    a,b,stencils,weights=build_matrix(local)
    report=preflight_report(local,lb,ub,stencils,a.shape)
    report["crossing_records_sha256"]=canonical_sha(crossings)
    pre_dir=OUT/"author/preflight"
    pre_dir.mkdir(parents=True,exist_ok=True)
    domain_obj={
        "status":"DIAGNOSTIC_ONLY_RECONSTRUCT_IN_CONSUMER",
        "source_input_sha256":local["hashes"],
        "bounds17":list(local["bounds17"]),"bounds13":list(local["bounds13"]),
        "mutable_nodes_rc":local["variables"].astype(int).tolist(),
        "mutable_nodes_sha256_le_i32":report["mutable_nodes_sha256_le_i32"],
        "protection_masks_local":{k:v.astype(np.uint8).tolist() for k,v in local["masks"].items()},
    }
    domain_path=pre_dir/"domain-diagnostic.json"
    domain_path.write_text(json.dumps(domain_obj,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    crossings_path=pre_dir/"crossing-bounds.json"
    crossings_path.write_text(json.dumps({"status":"DIAGNOSTIC_ONLY_RECONSTRUCT_IN_CONSUMER","records":crossings},indent=2,allow_nan=False)+"\n",encoding="utf-8")
    stencils_path=pre_dir/"frozen-stencils.json"
    collar_set=set()
    r0,r1,c0,c1=local["bounds17"]
    for rr in range(r0,r1):
        for cc in range(c0,c1):
            if rr<r0+2 or rr>=r1-2 or cc<c0+2 or cc>=c1-2: collar_set.add((rr,cc))
    collar=[s for s in stencils if any((rr,cc) in collar_set for rr,cc,_ in hinge_coeffs(s[0],s[1],s[2]))]
    stencil_obj={"status":"FROZEN_BEFORE_SOLVE_DIAGNOSTIC_ONLY","stencils":[list(s) for s in stencils],"collar_impact_stencils":[list(s) for s in collar],"sha256":report["stencil_sha256_canonical_json"],"collar_sha256":report["collar_stencil_sha256_canonical_json"]}
    stencils_path.write_text(json.dumps(stencil_obj,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    report["diagnostic_artifacts"]={str(domain_path):sha256(domain_path),str(crossings_path):sha256(crossings_path),str(stencils_path):sha256(stencils_path)}
    from scipy import __version__ as scipy_version
    linked_schema,linked_before=verify_linked_identities(schema_path)
    report["plan_sha256"]=sha256(plan_path)
    report["receipt_schema_sha256"]=sha256(schema_path)
    report["linked_identity_sha256"]=linked_before
    report["scipy_api_source_json_sha256"]=sha256(OUT/"author/preflight/scipy-api.json")
    report["scipy"]={"version":scipy_version,"method":"bvls","dense":True,"tol":1e-10,"max_iter":1000,"hard_timeout_seconds":HARD_TIMEOUT_S}
    if report["bounds_empty"] or local["partial_cells"]:
        report["status"]="PREFLIGHT_BLOCKED"
    (pre_dir/"preflight.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k not in ("input_sha256",)},indent=2))
    if not args.solve:
        return 0
    if report["status"] != "PREFLIGHT_READY_SOLVER_NOT_RUN":
        raise RuntimeError("solver blocked by preflight")
    preflight_path=pre_dir/"preflight.json"
    fixture_path=pre_dir/"fixtures.json"
    plan_sha_before=sha256(plan_path)
    schema_sha_before=sha256(schema_path)
    preflight_sha=sha256(preflight_path)
    fixture_sha=sha256(fixture_path)
    # Solver output is not published until a successful complete result exists.
    result=solve_once(a,b,lb[np.nonzero(~local["protect_local"][2:15,2:15])],ub[np.nonzero(~local["protect_local"][2:15,2:15])])
    post_solver_hashes={k:sha256(v) for k,v in PATHS.items()}
    if post_solver_hashes != local["hashes"]:
        raise RuntimeError(f"author inputs changed during solve: {post_solver_hashes}")
    plan_sha_after=sha256(plan_path); schema_sha_after=sha256(schema_path)
    if plan_sha_after!=plan_sha_before or schema_sha_after!=schema_sha_before or sha256(preflight_path)!=preflight_sha or sha256(fixture_path)!=fixture_sha:
        raise RuntimeError("plan/schema/preflight/fixtures changed during solve")
    linked_schema_after,linked_after=verify_linked_identities(schema_path)
    if linked_after!=linked_before:
        raise RuntimeError("linked deployed/corridor identities changed during solve")
    heights=local["b"]["heights"].copy()
    for (r,c),value in zip(local["variables"],result["x"]): heights[r,c]=np.float32(value)
    candidate={k:v.copy() for k,v in local["b"].items()}
    candidate["heights"]=heights
    out=OUT/"candidate-terrain.npz"; tmp=OUT/"candidate-terrain.npz.tmp"
    with tmp.open("wb") as fobj: np.savez_compressed(fobj,**candidate)
    os.replace(tmp,out)
    meta={"status":"AUTHORED_PENDING_INDEPENDENT_CONSUMER","candidate_path":str(out),"candidate_sha256":sha256(out),
          "input_paths_and_sha256":{k:{"path":str(PATHS[k]),"sha256":local["hashes"][k]} for k in PATHS},
          "input_sha256_pre_solver":local["hashes"],
          "post_solver_input_sha256":post_solver_hashes,"linked_identity_inputs":linked_schema["identity_inputs"],"linked_identity_sha256_before":linked_before,"linked_identity_sha256_after":linked_after,
          "plan_path":str(plan_path),"plan_sha256_before":plan_sha_before,"plan_sha256_after":plan_sha_after,
          "receipt_schema_path":str(schema_path),"receipt_schema_sha256":schema_sha_before,
          "preflight_path":str(preflight_path),"preflight_sha256":preflight_sha,
          "fixtures_path":str(fixture_path),"fixtures_sha256":fixture_sha,
          "preflight_artifacts":report["diagnostic_artifacts"],
          "preflight_artifact_paths_and_sha256":{**report["diagnostic_artifacts"],str(preflight_path):preflight_sha,str(fixture_path):fixture_sha},
          "preflight":{"status":report["status"],"mutable_count":report["mutable_count"],"mutable_nodes_sha256_le_i32":report["mutable_nodes_sha256_le_i32"],
                        "frozen_stencils_count":report["frozen_stencils"],"frozen_stencils_sha256":report["stencil_sha256_canonical_json"],"collar_stencil_count":report["collar_impact_stencils"],
                        "collar_stencils_sha256":report["collar_stencil_sha256_canonical_json"],"crossing_records_count":report["crossing_records"],"crossing_records_sha256":report["crossing_records_sha256"],
                        "near_flat_threshold_m":report["near_flat_threshold_m"],"near_flat_source":report["near_flat_source"],"near_flat_count_B":report["core13_nearflat_count_at_threshold"],"matrix_shape":report["matrix_shape"]},
          "solver":{"method":"scipy.optimize.lsq_linear/BVLS","scipy_version":scipy_version,"dense":True,"tol":1e-10,"max_iter":1000,"hard_timeout_seconds":HARD_TIMEOUT_S,
                    "success":result["success"],"status":result["status"],"nit":result["nit"],"cost":result["cost"]}}
    (OUT/"authoring.json").write_text(json.dumps(meta,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return 0


if __name__=="__main__":
    raise SystemExit(main())

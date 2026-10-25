#!/usr/bin/env python
"""Exhaustively assess only the approved 10-node +/-1-f32-ULP neighborhood.

`--self-test` is synthetic-only. `--enumerate` is the sole real-data mode and
has deliberately not been invoked during preparation/review.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import sys
import time
from collections import Counter

import numpy as np
from scipy import sparse
from shapely.geometry import LineString, shape

HERE = Path(__file__).resolve().parent
G = Path(r"E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010")
ROOT = G / "G/wet-bank-pilot"
PREP = ROOT / "prepared-runs/attempt-08/prepared.npz"
SOL = ROOT / "solve-once/solution.npz"
BASE = G / "global-operator-prototype/real-sector-preflight/ev94-rebase/slope-bound/composition-run-01/terrain.npz"
P_PATH = G / "build-focal/candidate/plane.npy"
F_PATH = G / "build-focal/candidate/visible-field.npy"
DESIGN = Path(r"E:/DayZ-Baltic-Build/v30-v11/design/water_v3.geojson")
FRACTION_DIAG = ROOT / "postsolve-consumer/crossing-geometry-fraction-v2.json"
ORDER_CLOSURE = G / "global-operator-prototype/real-sector-preflight/order-closure/projection.py"
RUNNER_SOURCE = ROOT / "run_once.py"
BUILDER_SOURCE = ROOT / "prepare_wet_bank_matrices.py"
CONSUMER_SOURCE = ROOT / "postsolve-consumer/verify_wet_bank_result.py"
PLAN = HERE / "PLAN.md"
TEST_SOURCE = HERE / "test_executor.py"
OUT = HERE / "real-enumeration-01"

PIN = {
    PREP: "52409a8d074d15ec068bddc6e9265bc3782e84e9d54582b8a6d7b0a6675a787f",
    SOL: "1b7a23ebb3c203427f1c77cb8de6becfca750746e47f5494bba6723b0610eab1",
    BASE: "40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a",
    P_PATH: "768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0",
    F_PATH: "f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c",
    DESIGN: "caa333e365c2a4511f839937a9d76a5aa157a0ef925d6ee4b5efcc4ebb38f8a9",
    FRACTION_DIAG: "a0331f83ec496d196ba2599eb96d2d0b1861793a871f60e424614326c372b5e8",
    ORDER_CLOSURE: "a990dc2d33fca4fd2a446b958f0412a2d752a5d3072a85d82058bb634cfaf44b",
    RUNNER_SOURCE: "c1a349fc23b440221d54f3624037785380c62d8e4283d0d29b4ca8842e25766e",
    BUILDER_SOURCE: "65e05a6540026b08df7effa53c58534121bb2fa89e116a2ef07ad46ba0edf286",
    CONSUMER_SOURCE: "1f3e1fe776bcca2d98a522b9755b9f0c5daa4d6144796d8f16bb8eb8099b4c70",
}
ORIGIN = (855, 1179)
EXPECTED_NODES_RC = (
    (862,1186),(862,1187),(863,1187),(864,1187),(865,1187),
    (865,1188),(866,1187),(866,1188),(867,1187),(867,1188),
)
MAX_SECONDS = 120.0
MAX_PEAK_WS_BYTES = 1_073_741_824
TOTAL_ASSIGNMENTS = 3 ** len(EXPECTED_NODES_RC)

class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def sha_map(paths):
    return {str(Path(p).resolve()): sha256(Path(p)) for p in paths}

def memory_peak_ws_bytes() -> int:
    if os.name != "nt":
        raise RuntimeError("This executor is pinned to the Windows GIS runtime")
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX), wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    counters = PROCESS_MEMORY_COUNTERS_EX()
    counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return int(counters.PeakWorkingSetSize)

def f32_next(level: float, above: bool) -> np.float32:
    return np.nextafter(np.float32(level), np.float32(np.inf if above else -np.inf), dtype=np.float32)

def as_fraction(value) -> Fraction:
    return Fraction.from_float(float(value))

def csr_from_npz(z, prefix: str):
    return sparse.csr_matrix((z[prefix+"_data"], z[prefix+"_indices"], z[prefix+"_indptr"]),
                             shape=tuple(z[prefix+"_shape"]))

def collect_points(geometry, output):
    if geometry.is_empty:
        return
    if geometry.geom_type == "Point":
        output.append(geometry)
    elif hasattr(geometry, "geoms"):
        for child in geometry.geoms:
            collect_points(child, output)

def design_t_ab(edge, boundary) -> Fraction:
    (ra,ca),(rb,cb) = edge
    a = (ca*6.0, 12282.0-ra*6.0)
    b = (cb*6.0, 12282.0-rb*6.0)
    hits=[]
    collect_points(LineString((a,b)).intersection(boundary), hits)
    unique=[]
    seen=set()
    for hit in hits:
        xy=(float(hit.x),float(hit.y))
        if xy not in seen:
            seen.add(xy);unique.append(hit)
    if len(unique)!=1:
        raise ValueError(f"expected one design intersection for {edge}; got {len(unique)}")
    point=unique[0];dx=b[0]-a[0];dz=b[1]-a[1]
    return as_fraction(((point.x-a[0])*dx+(point.y-a[1])*dz)/(dx*dx+dz*dz))

@dataclass(frozen=True)
class CrossSpec:
    key: tuple
    surface: str
    cell_rc: tuple[int,int]
    edge_rc: tuple[tuple[int,int],tuple[int,int]]
    local_a: tuple[int,int]
    local_b: tuple[int,int]
    level_a: Fraction
    level_b: Fraction
    dry_endpoint: int
    t_lower: Fraction
    t_upper: Fraction
    dry_level: Fraction
    wet_level: Fraction
    dry_rc: tuple[int,int]
    wet_rc: tuple[int,int]

@dataclass(frozen=True)
class SignSpec:
    rc: tuple[int,int]
    local_rc: tuple[int,int]
    level: Fraction
    sign: int  # +1 strict above, -1 strict below, 0 exact baseline contact
    baseline: np.float32
    surface: str

def local_rc(global_rc):
    return (int(global_rc[0])-ORIGIN[0], int(global_rc[1])-ORIGIN[1])

def get_levels(P, F, cell, edge, surface):
    r,c=map(int,cell)
    if surface=="P":
        v=float(P[r,c]);return v,v
    corners={(r,c):0,(r,c+1):1,(r+1,c):2,(r+1,c+1):3}
    return (float(F[r,c,corners[tuple(edge[0])]]),float(F[r,c,corners[tuple(edge[1])]]))

def build_direct_specs(meta, Bgrid, P, F, boundary):
    crossing=[]; sign_specs=[]; seen=set()
    for m in meta:
        typ=m["type"]
        if typ=="cross_lower":
            cell=tuple(map(int,m["cell_rc"])); edge=tuple(tuple(map(int,e)) for e in m["edge_rc"])
            key=(cell,edge,m["surface"])
            if key in seen: continue
            seen.add(key)
            la,lb=get_levels(P,F,cell,edge,m["surface"])
            ha=float(Bgrid[local_rc(edge[0])]);hb=float(Bgrid[local_rc(edge[1])])
            da,db=as_fraction(ha)-as_fraction(la),as_fraction(hb)-as_fraction(lb)
            if da*db>=0: raise ValueError(f"baseline crossing absent for {key}")
            dry=0 if da>0 else 1; wet=1-dry
            tbase=(da/(da-db)) if dry==0 else (db/(db-da))
            td=design_t_ab(edge,boundary)
            tdry=td if dry==0 else 1-td
            lo,hi=min(tbase,tdry),max(tbase,tdry)
            dry_rc=edge[dry];wet_rc=edge[wet]
            crossing.append(CrossSpec(key,m["surface"],cell,edge,local_rc(edge[0]),local_rc(edge[1]),
                as_fraction(la),as_fraction(lb),dry,lo,hi,
                as_fraction(la if dry==0 else lb),as_fraction(lb if dry==0 else la),
                tuple(dry_rc),tuple(wet_rc)))
        elif typ=="sign_only":
            cell=tuple(map(int,m["cell_rc"]));edge=tuple(tuple(map(int,e)) for e in m["edge_rc"])
            levels=get_levels(P,F,cell,edge,m["surface"])
            deltas=(float(m["delta_a_m"]),float(m["delta_b_m"]))
            for endpoint,(rc,level,delta) in enumerate(zip(edge,levels,deltas)):
                baseline=np.float32(Bgrid[local_rc(rc)])
                sign=1 if delta>0 else -1 if delta<0 else 0
                if sign==0 and as_fraction(baseline)!=as_fraction(level):
                    raise ValueError(f"baseline contact not exactly representable at {rc}/{m['surface']}")
                sign_specs.append(SignSpec(tuple(rc),local_rc(rc),as_fraction(level),sign,baseline,m["surface"]))
    if len(crossing)!=116:
        raise ValueError(f"expected 116 independent P/F crossings, got {len(crossing)}")
    # Baseline cross edges also have separate strict sign rows; check signs using the same f32 rule.
    return tuple(crossing),tuple(sign_specs)

def derive_material_target(diag, metadata, C_cross, vars_rc):
    """Derive the ten editable nodes from the five physical-failure groups."""
    if diag.get("schema")!="ev94.wet-bank-crossing-geometry-fraction.v2":
        raise ValueError("unexpected Fraction-v2 diagnostic schema")
    physical=diag.get("physical_crossing",{})
    groups=physical.get("candidate_failed_native_edges",[])
    if physical.get("candidate_direct_failures")!=20 or len(groups)!=5:
        raise ValueError("diagnostic no longer identifies exactly five edges / twenty material rows")
    if C_cross.shape[0]!=528 or len(vars_rc)==0:
        raise ValueError("unexpected crossing matrix or variable inventory")
    cross_meta=[m for m in metadata if m.get("type")!="sign_only"]
    if len(cross_meta)!=C_cross.shape[0]:
        raise ValueError("crossing metadata is not aligned to C_cross rows")
    row_ids=[]; edge_keys=set()
    for group in groups:
        edge=tuple(tuple(map(int,rc)) for rc in group["edge_rc"])
        if len(edge)!=2 or edge in edge_keys: raise ValueError("duplicate or malformed failed native edge")
        edge_keys.add(edge)
        cells=tuple(tuple(map(int,rc)) for rc in group.get("cells",[]))
        if len(cells)!=2 or set(group.get("surfaces",[]))!={"P","F"}:
            raise ValueError("failed edge must represent both P/F surfaces and its two incident cells")
        rows=[int(v) for v in group["rows"]]
        if len(rows)!=4 or len(set(rows))!=4: raise ValueError("each failed edge must name four P/F incident-cell rows")
        for row in rows:
            if row<0 or row>=C_cross.shape[0]: raise ValueError("failed crossing row outside C_cross")
            m=cross_meta[row]
            if m.get("type") not in ("cross_lower","cross_upper"):
                raise ValueError("physical failure rows must map to interval rows, not sign summaries")
            medge=tuple(tuple(map(int,rc)) for rc in m["edge_rc"])
            if medge!=edge: raise ValueError("diagnostic C_cross row does not match aligned metadata edge")
        expected_edge_ids={i for i,rc in enumerate(vars_rc) if tuple(map(int,rc)) in edge}
        actual_edge_ids=set()
        for row in rows:
            actual_edge_ids.update(int(i) for i in C_cross.getrow(row).indices)
        if len(expected_edge_ids)!=2 or actual_edge_ids!=expected_edge_ids:
            raise ValueError("failed-edge CSR support does not equal its two endpoint variables")
        expected_rows={(cell,surface) for cell in cells for surface in ("P","F")}
        actual_rows={(tuple(map(int,cross_meta[row]["cell_rc"])),cross_meta[row]["surface"]) for row in rows}
        if actual_rows!=expected_rows:
            raise ValueError("failed-edge rows do not cover exactly P/F on both incident cells")
        row_ids.extend(rows)
    if len(row_ids)!=20 or len(set(row_ids))!=20:
        raise ValueError("failed crossing row inventory is not 20 unique rows")
    support=set()
    for row in row_ids:
        support.update(int(i) for i in C_cross.getrow(row).indices)
    derived=tuple(sorted(tuple(map(int,vars_rc[i])) for i in support))
    if derived!=EXPECTED_NODES_RC:
        raise ValueError(f"CSR support of five direct-failure edges differs from reviewed target set: {derived}")
    return derived,tuple(sorted(row_ids)),tuple(sorted(edge_keys))

def direct_signs_pass(grid, cross_specs, sign_specs):
    passed=True
    for spec in cross_specs:
        dry_h=as_fraction(np.float32(grid[local_rc(spec.dry_rc)]))
        wet_h=as_fraction(np.float32(grid[local_rc(spec.wet_rc)]))
        if dry_h <= spec.dry_level or wet_h >= spec.wet_level:
            passed=False
    for spec in sign_specs:
        h32=np.float32(grid[spec.local_rc]);h=as_fraction(h32)
        if spec.sign>0 and h <= spec.level: passed=False
        if spec.sign<0 and h >= spec.level: passed=False
        if spec.sign==0 and h32.view(np.uint32)!=spec.baseline.view(np.uint32): passed=False
    return passed

def direct_crossings_pass(grid, specs):
    passed=True
    for spec in specs:
        ha=as_fraction(np.float32(grid[spec.local_a]));hb=as_fraction(np.float32(grid[spec.local_b]))
        da=ha-spec.level_a;db=hb-spec.level_b
        if da*db>=0:
            passed=False
            continue
        tab=da/(da-db)
        th=tab if spec.dry_endpoint==0 else 1-tab
        if th<spec.t_lower or th>spec.t_upper:passed=False
    return passed

def d8_pass(grid, witnesses):
    passed=True
    for cr,cc,wr,wc in witnesses:
        if not np.float32(grid[int(cr),int(cc)]) >= np.float32(grid[int(wr),int(wc)]):
            passed=False
    return passed

def cone_metrics(x, Gmat, k, radii):
    q=(Gmat @ x + k).reshape(-1,2)
    excess=np.linalg.norm(q,axis=1)-radii
    return bool(np.all(excess<=0.0)),float(np.max(excess,initial=-np.inf))

def objective_cost(A, rhs, x):
    residual=A@x-rhs
    return 0.5*float(np.sum(residual*residual))

def closure_energy_pass(raw_cost, closed_cost, baseline_cost):
    allowance=1e-7*max(1.0,float(raw_cost))
    return bool(float(closed_cost)-float(raw_cost)<=allowance and float(closed_cost)<float(baseline_cost)),allowance

def rank_candidate(steps, target_rc, candidate_x, x64):
    l1=sum(abs(int(s)) for s in steps)
    d2=math.fsum((float(v)-float(x))**2 for v,x in zip(candidate_x,x64))
    # Include zero steps too: this is the complete row-major assignment tuple.
    lex=tuple((int(target_rc[i,0]),int(target_rc[i,1]),int(step)) for i,step in enumerate(steps))
    return (l1,d2,lex)

def build_neighbor_options(current, lower, upper):
    current=np.asarray(current,dtype=np.float32)
    lower=np.asarray(lower,dtype=np.float32);upper=np.asarray(upper,dtype=np.float32)
    if current.ndim!=1 or current.shape!=lower.shape or current.shape!=upper.shape:
        raise ValueError("target values and physical bounds must be same-length vectors")
    if np.any(lower>upper): raise ValueError("inverted physical bounds")
    # Do not prune options here: out-of-box assignments still get all gates.
    opts=[]
    for x,lo,hi in zip(current,lower,upper):
        x=np.float32(x)
        row=[]
        for step in (-1,0,1):
            y=x if step==0 else np.nextafter(x,np.float32(-np.inf if step<0 else np.inf),dtype=np.float32)
            # Preserve adjacent values even outside the box so every assignment
            # still receives independent results for all other gates.
            row.append(np.float32(y))
        opts.append(tuple(row))
    return tuple(opts)

def source_paths():
    return (*PIN.keys(),PLAN,HERE/"executor.py",TEST_SOURCE)

def source_readset_check(start):
    end=sha_map(source_paths())
    if end!=start:
        raise RuntimeError("source/input readset changed during enumeration")
    return end

def load_real_inputs():
    start=sha_map(source_paths())
    for path,want in PIN.items():
        if want and start[str(path.resolve())]!=want:
            raise ValueError(f"pinned input changed: {path}")
    with np.load(PREP,allow_pickle=False) as z, np.load(SOL,allow_pickle=False) as s, np.load(BASE,allow_pickle=False) as b:
        context=z["base_heights_context"].copy()
        closed=s["closed_float32_grid"].copy();raw=s["raw_float32_grid"].copy()
        if context.dtype!=np.float32 or closed.dtype!=np.float32 or raw.dtype!=np.float32:
            raise ValueError("prepared/base/candidate grid dtype changed")
        if not np.array_equal(raw.view(np.uint32),closed.view(np.uint32)):
            raise ValueError("frozen raw and closed arrays differ; this diagnostic is pinned to the reviewed v2 report")
        if context.shape!=(15,15) or closed.shape!=context.shape:
            raise ValueError("unexpected context shape")
        if not np.array_equal(context.view(np.uint32),b["heights"][855:870,1179:1194].view(np.uint32)):
            raise ValueError("prepared context differs from pinned EV94 base")
        vars_rc=z["variables_rc"].astype(np.int32)
        target=np.asarray(EXPECTED_NODES_RC,dtype=np.int32)
        # Preserve row-major variable indexing while resolving exact node IDs.
        index={tuple(map(int,rc)):i for i,rc in enumerate(vars_rc)}
        target_idx=np.asarray([index[tuple(map(int,rc))] for rc in target],dtype=np.int32)
        if len(set(target_idx.tolist()))!=10: raise ValueError("target node IDs are not unique")
        lo=z["lo_absolute_float32_inward"].copy();hi=z["hi_absolute_float32_inward"].copy()
        if lo.dtype!=np.float32 or hi.dtype!=np.float32 or np.any(lo>hi): raise ValueError("invalid frozen float32 bounds")
        A=csr_from_npz(z,"A");rhs=z["rhs_A"].copy();Gmat=csr_from_npz(z,"G");k=z["k_G"].copy();radii=z["radii_G"].copy()
        C_cross=csr_from_npz(z,"C_cross")
        witnesses=z["d8_witnesses_local"].astype(np.int32)
        x0=z["x0_absolute"].copy()
        x64=s["solution_float64"].copy()
        metadata=json.loads(z["crossing_rows_json"].tobytes().decode("utf-8"))
        diag=json.loads(FRACTION_DIAG.read_text(encoding="utf-8"))
        diagnostic_pins={str(Path(p).resolve()):str(h) for p,h in diag.get("inputs_sha256",{}).items()}
        required_diag_pins={str(Path(p).resolve()):PIN[p] for p in (PREP,SOL,BASE,P_PATH,F_PATH,DESIGN,BUILDER_SOURCE)}
        if diagnostic_pins!=required_diag_pins:
            raise ValueError("Fraction-v2 diagnostic input pins do not match this executor's frozen sources")
        target_rc,material_rows,failed_edges=derive_material_target(diag,metadata,C_cross,vars_rc)
        if target_rc!=EXPECTED_NODES_RC: raise ValueError("derived target nodes differ from frozen requested set")
        P=np.load(P_PATH,mmap_mode="r",allow_pickle=False);F=np.load(F_PATH,mmap_mode="r",allow_pickle=False)
        design=json.loads(DESIGN.read_text(encoding="utf-8-sig"))
        feature=next(q for q in design["features"] if q.get("id")=="river_041" or q.get("properties",{}).get("id")=="river_041")
        boundary=shape(feature["geometry"]).boundary
        cross_specs,sign_specs=build_direct_specs(metadata,context,P,F,boundary)
        return {
            "source_start":start,"context":context,"closed":closed,"raw":raw,"vars_rc":vars_rc,
            "target_rc":np.asarray(target_rc,dtype=np.int32),"target_idx":target_idx,
            "material_crossing_rows":material_rows,"failed_native_edges":failed_edges,
            "lo":lo,"hi":hi,"A":A,"rhs":rhs,
            "G":Gmat,"k":k,"radii":radii,"witnesses":witnesses,"x0":x0,"x64":x64,
            "cross_specs":cross_specs,"sign_specs":sign_specs,
            "raw_x":closed[tuple((vars_rc-np.asarray(ORIGIN)).T)].astype(np.float64),
            "flat_origin":np.asarray(ORIGIN),
        }

def eval_gates(data, grid):
    rc=data["vars_rc"];local=rc-np.asarray(ORIGIN);x=grid[tuple(local.T)].astype(np.float64)
    box=bool(np.all(x>=data["lo"]) and np.all(x<=data["hi"]))
    signs=direct_signs_pass(grid,data["cross_specs"],data["sign_specs"])
    crossings=direct_crossings_pass(grid,data["cross_specs"])
    d8=d8_pass(grid,data["witnesses"])
    cone,cone_excess=cone_metrics(x,data["G"],data["k"],data["radii"])
    raw_cost=objective_cost(data["A"],data["rhs"],data["raw_x"])
    closed_cost=objective_cost(data["A"],data["rhs"],x)
    baseline_cost=objective_cost(data["A"],data["rhs"],data["x0"])
    energy,allowance=closure_energy_pass(raw_cost,closed_cost,baseline_cost)
    return {"bounds":box,"PF_signs":signs,"all_116_direct_crossings":crossings,"D8_direct":d8,
            "face_cones":cone,"closure_energy_and_improvement":energy,
            "cone_max_excess":cone_excess,"raw_cost":raw_cost,"closed_cost":closed_cost,
            "baseline_cost":baseline_cost,"closure_allowance":allowance}

def offsets_for(combo, options):
    return np.asarray([opts[int(step)+1] for step,opts in zip(combo,options)],dtype=np.float32)

def set_ten_values(grid, data, values):
    out=grid.copy()
    loc=data["target_rc"]-np.asarray(ORIGIN)
    out[tuple(loc.T)]=values
    outside=np.ones(out.shape,dtype=bool)
    outside[tuple(loc.T)]=False
    if not np.array_equal(out[outside].view(np.uint32),grid[outside].view(np.uint32)):
        raise AssertionError("non-target context values changed")
    return out

def verify_controls(data):
    # Baseline is positive for geometry/order/box/cones; energy is not a baseline control.
    B=data["context"].copy()
    bx=B[tuple((data["vars_rc"]-np.asarray(ORIGIN)).T)].astype(np.float64)
    if data["x0"].shape!=bx.shape or not np.array_equal(data["x0"],bx):
        raise ValueError("prepared x0 is not exactly the baseline context at variable nodes")
    baseline_positive={
        "baseline_box":bool(np.all(bx>=data["lo"]) and np.all(bx<=data["hi"])),
        "baseline_PF_signs":direct_signs_pass(B,data["cross_specs"],data["sign_specs"]),
        "baseline_116_crossings":direct_crossings_pass(B,data["cross_specs"]),
        "baseline_D8":d8_pass(B,data["witnesses"]),
        "baseline_cones":cone_metrics(bx,data["G"],data["k"],data["radii"])[0],
    }
    if not all(baseline_positive.values()):
        raise ValueError(f"baseline positive control failed: {baseline_positive}")
    raw_bad=eval_gates(data,data["raw"])
    if raw_bad["all_116_direct_crossings"]:
        raise ValueError("negative raw candidate control unexpectedly passes direct shoreline checks")
    return baseline_positive,raw_bad

def rank_json(rank):
    l1,d2,lex=rank
    return {"total_abs_ulp_steps":int(l1),"squared_distance_to_x64":float(d2),
            "lexicographic_row_major_steps":[list(x) for x in lex]}

def write_candidate(path, data, best):
    steps,grid,gates,rank=best
    values=grid[tuple((data["target_rc"]-np.asarray(ORIGIN)).T)].copy()
    np.savez_compressed(path/"neighbor-candidate.npz",grid_float32=grid,variables_rc=data["target_rc"],
        values_float32=values,ulp_steps=np.asarray(steps,dtype=np.int8),
        source_candidate_sha256=np.asarray(PIN[SOL]))
    rec={"schema":"ev94.wet-bank-f32-neighborhood.v1","status":"DIAGNOSTIC_CANDIDATE_UNACCEPTED",
        "candidate_path":str((path/"neighbor-candidate.npz").resolve()),
        "candidate_sha256":sha256(path/"neighbor-candidate.npz"),
        "selected_steps_row_major":[{"rc":list(map(int,rc)),"step":int(step)} for rc,step in zip(data["target_rc"],steps)],
        "rank":rank_json(rank),"gates":gates,
        "statement":"Diagnostic-only one-ULP candidate. It is not accepted, promoted, or a terrain artifact."}
    (path/"candidate-receipt.json").write_text(json.dumps(rec,indent=2,allow_nan=False)+"\n",encoding="utf-8")

def enumerate_real():
    if OUT.exists(): raise FileExistsError(f"fixed output already exists; no retry: {OUT}")
    data=load_real_inputs()
    rc=data["target_rc"]
    if tuple(map(tuple,rc.tolist()))!=EXPECTED_NODES_RC: raise ValueError("derived 10-node set differs from reviewed direct diagnosis")
    baseline_control,raw_control=verify_controls(data)
    current=data["closed"][tuple((rc-np.asarray(ORIGIN)).T)].copy()
    options=build_neighbor_options(current,data["lo"][data["target_idx"]],data["hi"][data["target_idx"]])
    OUT.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter();last_ws=memory_peak_ws_bytes();counts=Counter();best=None
    ledger=OUT/"enumeration.jsonl"
    try:
        with ledger.open("x",encoding="utf-8",newline="\n") as stream:
            for number,combo in enumerate(itertools.product((-1,0,1),repeat=10),start=1):
                if number % 256 == 0:
                    elapsed=time.perf_counter()-started
                    if elapsed>MAX_SECONDS: raise TimeoutError(f"120s enumeration budget exceeded at {number}")
                if number % 1024 == 0:
                    last_ws=memory_peak_ws_bytes()
                    if last_ws>MAX_PEAK_WS_BYTES: raise MemoryError(f"1GiB peak WS exceeded: {last_ws}")
                values=offsets_for(combo,options)
                grid=set_ten_values(data["closed"],data,values)
                actual=grid[tuple((rc-np.asarray(ORIGIN)).T)]
                if not np.array_equal(actual.view(np.uint32),values.view(np.uint32)):
                    raise AssertionError("ULP assignment write/read mismatch")
                gates=eval_gates(data,grid)
                for name,passed in gates.items():
                    if isinstance(passed,bool) and not passed:counts[name]+=1
                if all(gates[k] for k in ("bounds","PF_signs","all_116_direct_crossings","D8_direct","face_cones","closure_energy_and_improvement")):
                    full_x=grid[tuple((data["vars_rc"]-np.asarray(ORIGIN)).T)].astype(np.float64)
                    rank=rank_candidate(combo,rc,full_x,data["x64"])
                    if best is None or rank<best[3]:best=(tuple(combo),grid,gates,rank)
                record={"assignment_index":number,"steps":[int(x) for x in combo],"gates":gates,
                        "accepted_all_gates":bool(all(gates.get(k,False) for k in ("bounds","PF_signs","all_116_direct_crossings","D8_direct","face_cones","closure_energy_and_improvement")))}
                stream.write(json.dumps(record,separators=(",",":"),allow_nan=False)+"\n")
            stream.flush();os.fsync(stream.fileno())
        elapsed=time.perf_counter()-started
        if number!=TOTAL_ASSIGNMENTS:raise AssertionError(f"incomplete assignment count {number}")
        if elapsed>MAX_SECONDS:raise TimeoutError("enumeration completed past numerical deadline")
        last_ws=memory_peak_ws_bytes()
        if last_ws>MAX_PEAK_WS_BYTES:raise MemoryError(f"1GiB peak WS exceeded: {last_ws}")
        source_end=source_readset_check(data["source_start"])
        if best is not None:write_candidate(OUT,data,best)
        else:
            source_end=source_readset_check(data["source_start"])
        summary={"schema":"ev94.wet-bank-f32-neighborhood-run.v1",
            "status":"DIAGNOSTIC_CANDIDATE_UNACCEPTED" if best else "NO_FEASIBLE_NEIGHBOR",
            "enumeration_count":TOTAL_ASSIGNMENTS,"complete_ledger_path":str(ledger.resolve()),
            "complete_ledger_sha256":sha256(ledger),"numerical_elapsed_s":elapsed,
            "peak_working_set_bytes":last_ws,"max_seconds":MAX_SECONDS,"max_peak_ws_bytes":MAX_PEAK_WS_BYTES,
            "source_readset_start":data["source_start"],"source_readset_end":source_end,
            "target_nodes_rc":[list(map(int,rc)) for rc in data["target_rc"]],
            "material_crossing_rows":[int(v) for v in data["material_crossing_rows"]],
            "failed_native_edges":[[list(a),list(b)] for a,b in data["failed_native_edges"]],
            "baseline_positive_control":baseline_control,"known_raw_negative_control":raw_control,
            "rejection_counts_by_gate_nonexclusive":dict(counts),
            "selected":None if best is None else {"steps":[int(v) for v in best[0]],"rank":rank_json(best[3]),"gates":best[2]},
            "candidate_path":None if best is None else str((OUT/"neighbor-candidate.npz").resolve()),
            "statement":"No solver call. Only ten f32 nodes were changed in memory; all other context bytes equal the frozen prior grid."}
        (OUT/"receipt.json").write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8")
        print(json.dumps({"status":summary["status"],"assignments":TOTAL_ASSIGNMENTS,"elapsed_s":elapsed,
            "peak_ws":last_ws,"candidate":summary["candidate_path"],"receipt":str(OUT/"receipt.json")}))
    except Exception as exc:
        # The fixed run directory stays as terminal/incomplete evidence; never retry over it.
        failure={"schema":"ev94.wet-bank-f32-neighborhood-run.v1","status":"INCOMPLETE_TERMINAL",
            "exception_type":type(exc).__name__,"exception":str(exc),"enumerated_assignments":locals().get("number",0),
            "source_readset_start":data["source_start"],"source_readset_end":sha_map(source_paths()),
            "elapsed_s":time.perf_counter()-started}
        (OUT/"failure.json").write_text(json.dumps(failure,indent=2,allow_nan=False)+"\n",encoding="utf-8")
        raise

def run_self_tests():
    import unittest
    from test_executor import ExecutorFixtures
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ExecutorFixtures)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1

def main():
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test",action="store_true")
    group.add_argument("--enumerate",action="store_true")
    args=parser.parse_args()
    if args.self_test:raise SystemExit(run_self_tests())
    enumerate_real()

if __name__=="__main__":main()

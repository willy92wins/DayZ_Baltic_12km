#!/usr/bin/env python
"""Prepare an exact physical-row tangent bound for the pinned 121-node diagnostic.

This module intentionally does not run a real LP by default. `prepare_real_model`
loads and checks the pinned artifacts; `dual_from_linprog` is a separate callable
which accepts a solver result, so the real LP remains gated pending attribution of
the independent protection/topology failures in recovery-v4.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time
from types import SimpleNamespace

import numpy as np

HERE = Path(__file__).resolve().parent
V2_PATH = HERE.parent / "certified_tangent.py"
ROOT = Path(r"E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/G/wet-bank-pilot")
EXECUTOR_PATH = ROOT / "postsolve-consumer/float32-neighborhood-v1/executor.py"
PREP = ROOT / "prepared-runs/attempt-08/prepared.npz"
DIAG = ROOT / "postsolve-consumer/float32-component-conversion-v1/robust-f32-design/candidate-only-milp/d8-sign-fix-v1/real-run-01/rejected-diagnostic.npz"
DIAG_RECEIPT = DIAG.with_name("receipt.json")
ASSESSMENT = ROOT / "postsolve-consumer/rejected-diagnostic-assessment-v1/recovery-v4/run-01/assessment.json"
BASE = Path(r"E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/global-operator-prototype/real-sector-preflight/ev94-rebase/slope-bound/composition-run-01/terrain.npz")
LATTICE = ROOT / "postsolve-consumer/float32-component-conversion-v1/robust-f32-design/candidate-only-milp/d8-sign-fix-v1/lattice_milp.py"
EXPECTED = {
    V2_PATH: "AF7B9A28BBFECF935D97F4F6F796B5BEE99A7D86484EC29133C5F07FA006C16D",
    EXECUTOR_PATH: "9A0DBFFC55E9956209083FE4963E2636B6F0174DE1DC150BDFA15F070D48149E",
    PREP: "52409A8D074D15EC068BDD C6E9265BC3782E84E9D54582B8A6D7B0A6675A787F".replace(" ", ""),
    DIAG: "2209DF7542098403C EDA8E27E87C91935A9832527F04663FDF8F5D8AC70149AE".replace(" ", ""),
    DIAG_RECEIPT: "F540FB0E8672886C8C70A2AF7C8D6AE16C3698CE7D0392E97D9CCC2D50E00902",
    ASSESSMENT: "79A4F1B09B30E98CF210E35BFC12E81388ED977C272DFFD44612AEC1DF013279",
    BASE: "40C174E31C8A3BF44855DAD72E53A7A5E0A26F41A1FBAC0AFC74A98D1513C58A",
    LATTICE: "2A62D1D73AF6D71AF97B60B5512787A653A3637D1C54F8EB001C9D905252E396",
}
TARGET_RAW_COST = 155.94405102975674
TARGET_ALLOWANCE = 1.5594405102975674e-5
PHYSICAL_GATE_THRESHOLD = 155.94406662416185
REAL_LP_ENABLED = False
MAX_SECONDS = 10.0
MAX_RSS_BYTES = 256 * 1024 * 1024


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def verify_pins(paths=EXPECTED):
    got = {}
    for p, want in paths.items():
        p = Path(p)
        if not p.is_file():
            raise FileNotFoundError(p)
        digest = sha256(p)
        if digest != want.upper():
            raise ValueError(f"pinned input drift: {p}; got {digest}, expected {want}")
        got[str(p.resolve())] = digest
    return got


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _fraction_api():
    return load_module(V2_PATH, "energy_lower_bound_v2_certified_tangent")


def _executor_api():
    return load_module(EXECUTOR_PATH, "energy_lower_bound_pinned_executor")


def physical_rows_from_specs(base_context, variables_local, lo_physical, hi_physical,
                             cross_specs, sign_specs, d8_witnesses, v2):
    """Reconstruct exact physical halfspaces; no float32-conversion fixed nodes.

    Rows are Mx>=b with strict signs relaxed to non-strict. We use very wide
    finite float32 placeholders only to invoke the frozen row constructor, then
    drop its final 2*n inward-box rows; actual LP bounds remain float64 physical
    lo/hi from prepared.npz. `fixed_raw_only_indices` are intentionally absent.
    """
    base = np.asarray(base_context)
    rc = np.asarray(variables_local, dtype=np.int32)
    lo64 = np.asarray(lo_physical, dtype=np.float64)
    hi64 = np.asarray(hi_physical, dtype=np.float64)
    if base.dtype != np.float32 or rc.shape != (len(rc), 2):
        raise ValueError("base/context or variable-coordinate shape mismatch")
    n = len(rc)
    if lo64.shape != (n,) or hi64.shape != (n,) or not np.isfinite(lo64).all() or not np.isfinite(hi64).all() or np.any(lo64 > hi64):
        raise ValueError("invalid physical float64 box")
    crossings = []
    for c in cross_specs:
        crossings.append(SimpleNamespace(
            a_rc=tuple(map(int, c.local_a)), b_rc=tuple(map(int, c.local_b)),
            level_a=c.level_a, level_b=c.level_b, dry_endpoint=int(c.dry_endpoint),
            t_lower=c.t_lower, t_upper=c.t_upper))
    signs = [SimpleNamespace(rc=tuple(map(int, s.local_rc)), sign=int(s.sign),
                             level=s.level, baseline=s.baseline)
             for s in sign_specs]
    witnesses = []
    for row in np.asarray(d8_witnesses, dtype=np.int32):
        if row.shape != (4,):
            raise ValueError("D8 witness row must be [center_r,center_c,other_r,other_c]")
        witnesses.append(((int(row[0]), int(row[1])), (int(row[2]), int(row[3]))))
    # build_physical_rows appends float32 box halfspaces. Strip them: physical
    # float64 bounds below are the contract for this relaxation.
    wide_lo = np.full(n, np.float32(-1.0e30), dtype=np.float32)
    wide_hi = np.full(n, np.float32(+1.0e30), dtype=np.float32)
    rows_all = v2.build_physical_rows(base, rc, wide_lo, wide_hi,
                                     crossings=crossings, signs=signs,
                                     d8_witnesses=witnesses, fixed_indices=())
    rows = rows_all[:-2*n] if n else rows_all
    if n and any(not label.startswith("box_") for _, _, label in rows_all[-2*n:]):
        raise AssertionError("row constructor box suffix changed")
    if any(label.startswith("source_fixed_") for _, _, label in rows):
        raise AssertionError("float32 conversion fixed nodes leaked into physical domain")
    return rows, lo64, hi64


def global_rc_to_local(global_rc, origin):
    g = np.asarray(global_rc, dtype=np.int64)
    o = np.asarray(origin, dtype=np.int64)
    if g.shape[-1:] != (2,) or o.shape != (2,):
        raise ValueError("coordinates must end in an (r,c) pair and origin must be length two")
    out = g - o
    if not np.array_equal(out + o, g):
        raise AssertionError("global/local RC roundtrip failed")
    return out.astype(np.int32)


def evaluate_exact_rows(rows, x):
    vals = [v2q(xi) for xi in x]
    for coeff, rhs, label in rows:
        lhs = sum((a * vals[j] for j, a in coeff.items()), Fraction(0))
        if lhs < rhs:
            return False, {"label": label, "lhs": str(lhs), "rhs": str(rhs)}
    return True, None


def v2q(v):
    from fractions import Fraction as F
    if isinstance(v, F):
        return v
    if isinstance(v, (int, np.integer)):
        return F(int(v))
    f = float(v)
    if not math.isfinite(f):
        raise ValueError("non-finite value in exact row evaluation")
    return F.from_float(f)


def safe_csr_float64_eval_error_bound(A_rows, rhs, lo, hi):
    """Conservative exact-Fraction rounding bound with explicit square/sum guards."""
    Q = v2q
    u = Fraction(1, 1 << 53)
    eta = Fraction(1, 1 << 1074)
    maxf = Q(np.finfo(np.float64).max)
    margin = maxf / 16
    l = [Q(x) for x in lo]; h = [Q(x) for x in hi]
    bvec = [Q(x) for x in rhs]
    if len(l) != len(h) or len(A_rows) != len(bvec):
        raise ValueError("shape mismatch")
    def gamma(k):
        ku = int(k) * u
        if ku >= 1:
            raise ValueError("invalid operation count")
        return ku / (1 - ku)
    square_sum = Fraction(0)
    error_sum = Fraction(0)
    for row, b in zip(A_rows, bvec):
        S = Fraction(0)
        for j, aa in row.items():
            j = int(j)
            if not 0 <= j < len(l):
                raise ValueError("A column outside physical bounds")
            S += abs(Q(aa)) * max(abs(l[j]), abs(h[j]))
        E = S + abs(b)
        ops = 2 * len(row) + 2
        delta = gamma(ops) * E + ops * eta
        mag = E + delta
        # Check squared/intermediate and aggregate values BEFORE using them in
        # a float conversion; the old max/4 guard did not bound mag*mag.
        square = mag * mag
        if square > margin:
            raise OverflowError("residual square lacks binary64 overflow margin")
        row_err = delta * (2 * E + delta) + u * square + (ops + 1) * eta
        row_sum = (1 + u) * square + eta
        if row_err > margin or row_sum > margin:
            raise OverflowError("per-row accumulation lacks binary64 overflow margin")
        error_sum += row_err
        square_sum += row_sum
        if error_sum > margin or square_sum > margin:
            raise OverflowError("objective accumulation lacks binary64 overflow margin")
    total = Fraction(1, 2) * (error_sum + gamma(max(1, len(A_rows))) * square_sum + max(1, len(A_rows)) * eta)
    if total > margin:
        raise OverflowError("total objective error bound lacks binary64 overflow margin")
    ftotal = float(total)
    if not math.isfinite(ftotal):
        raise OverflowError("error bound cannot be represented as finite binary64")
    return total


def gate_threshold_exact(raw_cost, allowance):
    """Upper bound on the threshold implied by rounded (closed_cost-raw_cost)."""
    raw = v2q(raw_cost); allow = v2q(allowance)
    if allow < 0:
        raise ValueError("negative allowance")
    u = Fraction(1, 1 << 53)
    eta = Fraction(1, 1 << 1074)
    # For positive d, fl(d)<=allow implies exact d<=allow/(1-u)+eta.
    return raw + allow / (1 - u) + eta


def dual_certificate(Jref, grad, intercept, rows, lo, hi, lambdas,
                     eval_error, raw_cost, allowance):
    lb = v2q(intercept)
    residual = [v2q(g) for g in grad]
    if len(rows) != len(lambdas) or len(residual) != len(lo) or len(lo) != len(hi):
        raise ValueError("dual certificate dimensions mismatch")
    for k, ((row, rhs, label), lam0) in enumerate(zip(rows, lambdas)):
        lam = v2q(lam0)
        if lam < 0:
            raise ValueError(f"negative dual multiplier at row {k}: {label}")
        lb += lam * v2q(rhs)
        for j, a in row.items():
            residual[int(j)] -= lam * v2q(a)
    for r, l, h in zip(residual, lo, hi):
        lb += min(r * v2q(l), r * v2q(h))
    err = v2q(eval_error)
    threshold = gate_threshold_exact(raw_cost, allowance)
    # Closed exact objective >= lb. The float64 evaluator can undershoot by err.
    certified_closed_float_lower = lb - err
    impossible = certified_closed_float_lower > threshold
    return {
        "tangent_lower_bound_exact": str(lb),
        "float64_eval_error_bound_exact": str(err),
        "closed_float_lower_bound_exact": str(certified_closed_float_lower),
        "gate_threshold_upper_exact": str(threshold),
        "excludes_energy_gate": bool(impossible),
    }


def _memory_status():
    """Windows memory reader used only if a real dual call is later enabled."""
    import ctypes
    from ctypes import wintypes
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                    ("PrivateUsage", ctypes.c_size_t)]
    ms = MEMORYSTATUSEX(); ms.dwLength = ctypes.sizeof(ms)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms)):
        raise OSError("GlobalMemoryStatusEx failed")
    pm = PROCESS_MEMORY_COUNTERS_EX(); pm.cb = ctypes.sizeof(pm)
    h = ctypes.windll.kernel32.GetCurrentProcess()
    if not ctypes.windll.psapi.GetProcessMemoryInfo(h, ctypes.byref(pm), pm.cb):
        raise OSError("GetProcessMemoryInfo failed")
    return {"available_phys_bytes": int(ms.ullAvailPhys), "working_set_bytes": int(pm.WorkingSetSize),
            "private_bytes": int(pm.PrivateUsage)}


def _assert_budget(start, t0):
    if time.perf_counter() - t0 > MAX_SECONDS:
        raise TimeoutError("10-second analysis budget exceeded")
    mem = _memory_status()
    if mem["working_set_bytes"] > MAX_RSS_BYTES:
        raise MemoryError(f"working set exceeds 256 MiB cap: {mem['working_set_bytes']}")
    return mem


def prepare_real_model():
    """Load pinned rows only; never invokes linprog or emits a terrain artifact."""
    started = time.perf_counter()
    initial_memory = _memory_status()
    if initial_memory["working_set_bytes"] > MAX_RSS_BYTES:
        raise MemoryError("GIS interpreter already exceeds 256 MiB cap")
    pins0 = verify_pins()
    v2 = _fraction_api()
    exe = _executor_api()
    executor_pin_start = verify_pins({Path(k): v for k, v in exe.PIN.items()})
    after_import_memory = _memory_status()
    if after_import_memory["working_set_bytes"] > MAX_RSS_BYTES:
        raise MemoryError("pinned helper imports exceed 256 MiB cap")
    if time.perf_counter() - started > MAX_SECONDS:
        raise TimeoutError("pinned helper import exceeded 10 seconds")
    data = exe.load_real_inputs()
    mem_after_load = _assert_budget(None, started)
    prep_sha = sha256(PREP); diag_sha = sha256(DIAG); assessment_sha = sha256(ASSESSMENT)
    report = json.loads(ASSESSMENT.read_text(encoding="utf-8"))
    if report.get("inputs", {}).get("diagnostic", {}).get("sha256", "").upper() != EXPECTED[DIAG]:
        raise ValueError("assessment does not pin the exact-physical diagnostic")
    # Fail closed unless this is still the recovery-v4 assessment described in
    # the handoff. Other physical/coverage failures are blockers to actionability,
    # not evidence that this local tangent bound proves global validity.
    checks = report.get("checks", {})
    failed = sorted(k for k, val in checks.items() if val is False)
    if report.get("schema") != "ev93.rejected-physical-diagnostic-assessment.v1":
        raise ValueError("unexpected diagnostic assessment schema")
    if "direct_PF_signs_and_all_116_crossings" not in checks or not checks["direct_PF_signs_and_all_116_crossings"]:
        raise ValueError("exact direct P/F row gate no longer passes")
    if "all_150_D8_witnesses" not in checks or not checks["all_150_D8_witnesses"]:
        raise ValueError("exact D8 gate no longer passes")
    required_blockers = {"protected_and_civil_context_exact", "local_compiled_water_topology_unchanged",
                         "energy_budget_and_strict_baseline_improvement"}
    if not required_blockers.issubset(set(failed)):
        raise ValueError("v4 non-energy blockers changed; require fresh review before using this driver")
    receipt = json.loads(DIAG_RECEIPT.read_text(encoding="utf-8"))
    if report.get("inputs", {}).get("rejection_receipt", {}).get("sha256", "").upper() != EXPECTED[DIAG_RECEIPT]:
        raise ValueError("recovery-v4 assessment does not pin the expected rejection receipt")
    metric = receipt.get("direct_executor_metrics", {})
    if metric.get("raw_cost") != TARGET_RAW_COST or metric.get("closure_allowance") != TARGET_ALLOWANCE:
        raise ValueError("assessment raw objective/allowance differs from the pinned threshold anchors")
    with np.load(PREP, allow_pickle=False) as z, np.load(DIAG, allow_pickle=False) as d:
        base = z["base_heights_context"].copy()
        rc_global = z["variables_rc"].copy()
        lo = z["lo_absolute_float64"].copy(); hi = z["hi_absolute_float64"].copy()
        witnesses = z["d8_witnesses_local"].copy()
        A = v2.csr_rows_from_arrays(z["A_data"], z["A_indices"], z["A_indptr"], tuple(z["A_shape"]))
        rhs = z["rhs_A"].copy()
        diag_grid = d["context_grid"].copy()
        diag_rc = d["variables_rc"].copy()
        diag_base = d["source_base_context"].copy()
    origin = np.asarray(exe.ORIGIN, dtype=np.int32)
    rc_local = global_rc_to_local(rc_global, origin)
    if not np.array_equal(rc_global, diag_rc):
        raise ValueError("diagnostic variable order differs from prepared variables")
    if len({tuple(map(int, q)) for q in rc_global}) != len(rc_global):
        raise ValueError("duplicate global variable coordinates")
    if not np.array_equal(base.view(np.uint32), diag_base.view(np.uint32)):
        raise ValueError("diagnostic baseline context differs from prepared base")
    if not np.array_equal(base.view(np.uint32), data["context"].view(np.uint32)):
        raise ValueError("executor context disagrees with prepared baseline")
    # Independently verify global-to-local translation and context containment.
    if not np.array_equal(rc_local + origin, rc_global):
        raise AssertionError("global/local coordinate translation failed")
    if np.any(rc_local < 0) or np.any(rc_local >= np.asarray(base.shape)):
        raise ValueError("variable outside prepared context")
    xref = diag_grid[tuple(rc_local.T)].astype(np.float64)
    rows, lo, hi = physical_rows_from_specs(base, rc_local, lo, hi,
                                             data["cross_specs"], data["sign_specs"],
                                             witnesses, v2)
    mem_after_rows = _assert_budget(None, started)
    expected_rows = 4 * len(data["cross_specs"]) + len(witnesses) + sum(2 if int(s.sign) == 0 else 1 for s in data["sign_specs"])
    if len(data["cross_specs"]) != 116 or len(witnesses) != 150 or len(rows) != expected_rows:
        raise ValueError("physical-row counts differ from the exact 116/150 source contract")
    feasible_base, base_bad = evaluate_exact_rows(rows, base[tuple(rc_local.T)])
    feasible_ref, ref_bad = evaluate_exact_rows(rows, xref)
    if not feasible_base or not feasible_ref:
        raise ValueError(f"physical exact superset feasibility failed: base={base_bad}, diagnostic={ref_bad}")
    Jref, grad, intercept = v2.objective_tangent(A, rhs, xref)
    err = safe_csr_float64_eval_error_bound(A, rhs, lo, hi)
    raw, allow = TARGET_RAW_COST, TARGET_ALLOWANCE
    # These numeric anchors are the actual pinned executor gate, not an estimate.
    if v2.Q(raw) != v2.Q(TARGET_RAW_COST) or v2.Q(allow) != v2.Q(TARGET_ALLOWANCE):
        raise ValueError("energy gate anchors differ from the reviewed executor receipt")
    pins1 = verify_pins()
    executor_pin_end = verify_pins({Path(k): v for k, v in exe.PIN.items()})
    if executor_pin_end != executor_pin_start:
        raise RuntimeError("executor pinned source set changed during model construction")
    executor_pins_end = exe.source_readset_check(data["source_start"])
    if executor_pins_end != data["source_start"]:
        raise RuntimeError("executor readset changed during model construction")
    if pins1 != pins0:
        raise RuntimeError("input readset changed during real-model construction")
    mem_before_return = _assert_budget(None, started)
    return {
        "status": "MODEL_PREPARED_LP_NOT_RUN",
        "assessment_failures": failed,
        "physical_row_count": len(rows), "variable_count": len(rc_global),
        "crossing_count": len(data["cross_specs"]), "sign_row_source_count": len(data["sign_specs"]),
        "d8_witness_count": len(witnesses), "global_to_local_verified": True,
        "base_exact_rows_feasible": feasible_base, "diagnostic_exact_rows_feasible": feasible_ref,
        "objective_reference_exact": str(Jref), "gradient_exact": [str(x) for x in grad],
        "intercept_exact": str(intercept), "float64_eval_error_exact": str(err),
        "gate_threshold_upper_exact": str(gate_threshold_exact(raw, allow)),
        "energy_gate_threshold_float": PHYSICAL_GATE_THRESHOLD,
        "pins_start": pins0, "pins_end": pins1,
        "executor_pins_start": executor_pin_start, "executor_pins_end": executor_pin_end,
        "executor_source_readset_start": data["source_start"], "executor_source_readset_end": executor_pins_end,
        "working_set_before_bytes": initial_memory["working_set_bytes"],
        "working_set_after_import_bytes": after_import_memory["working_set_bytes"],
        "working_set_after_load_bytes": mem_after_load["working_set_bytes"],
        "working_set_after_rows_bytes": mem_after_rows["working_set_bytes"],
        "working_set_before_return_bytes": mem_before_return["working_set_bytes"],
        "real_lp_enabled": REAL_LP_ENABLED,
    }, {"rows": rows, "lo": lo, "hi": hi, "gradient": grad,
        "intercept": intercept, "Jref": Jref, "error": err, "pins": pins1,
        "assessment_failures": failed, "started_perf": started}


def dual_from_linprog(model, scipy_result):
    """Certify a supplied minimization dual; this does not itself run an LP."""
    lam = -np.asarray(scipy_result.ineqlin.marginals, dtype=np.float64)
    return dual_certificate(model["Jref"], model["gradient"], model["intercept"],
                            model["rows"], model["lo"], model["hi"], lam,
                            model["error"], TARGET_RAW_COST, TARGET_ALLOWANCE)


def obtain_dual_from_linprog(model, *, allow_real_lp=False, budget_seconds=5.0):
    """Ask HiGHS only for a dual vector; exact Fraction code certifies afterward.

    This function is intentionally opt-in. Current recovery-v4 reports two
    non-energy blockers, so even `allow_real_lp=True` cannot run for this anchor.
    """
    if not allow_real_lp or not REAL_LP_ENABLED:
        raise RuntimeError("real LP disabled pending attribution of recovery-v4 topology/protection failures")
    if model.get("assessment_failures"):
        raise RuntimeError("real LP blocked while assessment has non-energy failures")
    if not (0 < float(budget_seconds) <= 5.0):
        raise ValueError("LP time limit must be in (0,5] seconds")
    t0 = time.perf_counter()
    run_started = float(model["started_perf"])
    remaining_global = MAX_SECONDS - (t0 - run_started)
    lp_cap = min(float(budget_seconds), remaining_global)
    if lp_cap <= 0:
        raise TimeoutError("overall 10-second budget expired before LP")
    mem0 = _memory_status()
    if mem0["working_set_bytes"] > MAX_RSS_BYTES:
        raise MemoryError("process already exceeds 256 MiB cap")
    from scipy import sparse
    from scipy.optimize import linprog
    m = len(model["rows"]); n = len(model["lo"])
    data=[]; indices=[]; indptr=[0]; rhs=[]
    for row, b, label in model["rows"]:
        for j, a in sorted(row.items()):
            data.append(-float(a)); indices.append(int(j))
        indptr.append(len(data)); rhs.append(-float(b))
    A_ub=sparse.csr_matrix((np.asarray(data,dtype=np.float64),
                            np.asarray(indices,dtype=np.int32),
                            np.asarray(indptr,dtype=np.int32)),shape=(m,n))
    if time.perf_counter()-t0 > lp_cap or time.perf_counter()-run_started > MAX_SECONDS:
        raise TimeoutError("LP model construction exceeded its time budget")
    remaining=min(lp_cap-(time.perf_counter()-t0), MAX_SECONDS-(time.perf_counter()-run_started))
    if remaining <= 0:
        raise TimeoutError("no LP time remains after model construction")
    result=linprog(np.asarray([float(x) for x in model["gradient"]],dtype=np.float64),
                   A_ub=A_ub,b_ub=np.asarray(rhs,dtype=np.float64),
                   bounds=list(zip(model["lo"],model["hi"])),method="highs",
                   options={"time_limit":remaining})
    mem1=_memory_status()
    if time.perf_counter()-t0 > lp_cap or time.perf_counter()-run_started > MAX_SECONDS:
        raise TimeoutError("dual LP exceeded its time budget")
    if mem1["working_set_bytes"] > MAX_RSS_BYTES:
        raise MemoryError("dual LP exceeded 256 MiB cap")
    if not result.success or result.ineqlin is None or result.ineqlin.marginals is None:
        raise RuntimeError(f"LP did not return usable duals: status={result.status} message={result.message}")
    cert=dual_from_linprog(model,result)
    return {"lp_status":int(result.status),"lp_message":str(result.message),
            "elapsed_seconds":time.perf_counter()-t0,"memory_before":mem0,
            "memory_after":mem1,"certificate":cert}


if __name__ == "__main__":
    raise SystemExit("Preparation-only module: no CLI path executes real inputs or an LP.")


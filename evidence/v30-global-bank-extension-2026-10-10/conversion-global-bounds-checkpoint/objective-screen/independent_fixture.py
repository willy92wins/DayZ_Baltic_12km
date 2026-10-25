"""Small independent checks for the objective screen; never loads global arrays."""
from __future__ import annotations

import hashlib
import importlib.util
import sys
import tempfile
import time
import types
from pathlib import Path

import numpy as np
from scipy.sparse.linalg import LinearOperator, cg


ROOT = Path(__file__).resolve().parents[1]
SCREEN_PATH = Path(__file__).resolve().parent / "screen.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run():
    opmod = load(ROOT / "global-structured-operator" / "structured_operator.py", "review_structured")
    fused = load(ROOT / "global-structured-operator" / "optimized-normal" / "fused_normal.py", "review_fused")
    screen = load(SCREEN_PATH, "review_screen")

    # Exercise the exact operator/RHS/diagonal used by screen.py on a tiny SPD case.
    base = np.arange(16, dtype=np.float64).reshape(4, 4) / 7.0
    variables = np.asarray([(r, c) for r in range(4) for c in range(4)], dtype=np.int32)
    op = opmod.build_operators(base, variables)
    action = fused.FusedNormalAction(op)
    rhs = op.rmatvec_a(op.rhs_a)
    eye = np.eye(op.n, dtype=np.float64)
    dense = np.column_stack([action.a_normal(eye[:, j]) for j in range(op.n)])
    eigen_min = float(np.linalg.eigvalsh(dense).min())
    assert np.allclose(dense, dense.T, atol=1e-12) and eigen_min > 0.0
    normal = LinearOperator((op.n, op.n), matvec=action.a_normal, dtype=np.float64)
    pre = LinearOperator((op.n, op.n), matvec=lambda x: x / op.diag_a, dtype=np.float64)
    x, info = cg(normal, rhs, x0=base.ravel(), rtol=1e-12, atol=1e-13, maxiter=1000, M=pre)
    x_ref = np.linalg.solve(dense, rhs)
    solve_error = float(np.max(np.abs(x - x_ref)))
    assert info == 0 and solve_error < 1e-10

    # Positive/negative checks exercise screen.constraints, not a copied predicate.
    fake = types.SimpleNamespace(
        base=np.zeros((3, 3), dtype=np.float64),
        variables=np.asarray([(r, c) for r in range(3) for c in range(3)], dtype=np.int32),
        d8_witnesses=np.asarray([0], dtype=np.int64),
        d8_centers=np.asarray([4], dtype=np.int64),
    )
    lo = np.full(9, -1.0); hi = np.full(9, 1.0); radii = np.ones(8)
    flat = np.zeros(9, dtype=np.float64)
    pos = screen.constraints(fake, flat, lo, hi, radii)
    assert pos["above_box"] == pos["below_box"] == pos["D8_violations"] == pos["face_radius_violations"] == 0
    bad = flat.copy(); bad[0] = 2.0
    neg = screen.constraints(fake, bad, lo, hi, radii)
    assert neg["above_box"] == 1 and neg["D8_violations"] == 1 and neg["face_radius_violations"] > 0

    # Guard checks reject an expired deadline and a process peak over cap.
    class Memory:
        peak = 0
        free = 20 * 1024**3
        def process_peak_working_set(self): return self.peak
        def memory_status(self): return {"available_physical_bytes": self.free}

    mem = Memory()
    timed = screen.Guard(mem, started=time.perf_counter() - screen.MAX_SECONDS - 1)
    try:
        timed.check()
        raise AssertionError("expired runtime was accepted")
    except TimeoutError:
        pass
    mem.peak = screen.MAX_PEAK + 1
    over = screen.Guard(mem)
    try:
        over.check()
        raise AssertionError("peak over cap was accepted")
    except MemoryError:
        pass

    # load() verifies the exact bytes it executes.
    with tempfile.TemporaryDirectory(prefix="screen-pin-fixture-") as td:
        temp = Path(td) / "pinned_module.py"
        temp.write_text("value = 7\n", encoding="utf-8")
        screen.PINS[temp] = hashlib.sha256(temp.read_bytes()).hexdigest()
        assert screen.load(temp, "review_pinned_module").value == 7
        temp.write_text("value = 8\n", encoding="utf-8")
        try:
            screen.load(temp, "review_tampered_module")
            raise AssertionError("changed bytes were executed despite pin mismatch")
        except ValueError as exc:
            assert "Source pin drift" in str(exc)
        finally:
            del screen.PINS[temp]

    return {
        "status": "PASS_SMALL_SCREEN_FIXTURE",
        "global_data_loaded": False,
        "global_cg_called": False,
        "synthetic_spd_n": int(op.n),
        "synthetic_spd_min_eigenvalue": eigen_min,
        "screen_cg_info": int(info),
        "screen_cg_vs_dense_max_abs": solve_error,
        "direct_constraints_positive_pass": True,
        "direct_constraints_negative_detected": True,
        "runtime_guard_negative_pass": True,
        "memory_guard_negative_pass": True,
        "pinned_loader_tamper_negative_pass": True,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2, allow_nan=False))

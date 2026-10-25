"""Small independent equivalence fixtures; never load global terrain arrays."""
from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OP_PATH = HERE.parent.parent / "global-structured-operator" / "structured_operator.py"
FUSED_PATH = HERE.parent.parent / "global-structured-operator" / "optimized-normal" / "fused_normal.py"
OP_SHA = "d3017e58bbae3b71c891fab6892a5bf8d9386ae8a51a451a94c9b05769ac750a"
FUSED_SHA = "19a3e3a493f643702e66aaf265c705739535d386412f74659369d7746117ffaa"


def _load(path, name, expected):
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise AssertionError(f"source pin mismatch: {path} {actual}")
    spec = importlib.util.spec_from_loader(name, loader=None, origin=str(path))
    mod = importlib.util.module_from_spec(spec)
    mod.__file__ = str(path)
    sys.modules[name] = mod
    exec(compile(data, str(path), "exec"), mod.__dict__)
    return mod


def run_fixtures():
    import a_only_operator as aonly
    fullmod = _load(OP_PATH, "a_only_fixture_full_operator", OP_SHA)
    fusedmod = _load(FUSED_PATH, "a_only_fixture_fused_normal", FUSED_SHA)
    fixtures = []
    cases = [
        ((1, 1), [(0, 0)]),
        ((2, 3), [(0, 0), (1, 2)]),
        ((3, 5), [(0, 1), (1, 3), (2, 4)]),
        ((7, 6), [(0, 0), (0, 5), (2, 1), (3, 3), (5, 2), (6, 5)]),
        ((5, 8), [(r, c) for r in range(5) for c in range(8)]),
    ]
    for case_id, (shape, coords) in enumerate(cases):
        rng = np.random.default_rng(701 + case_id)
        base = rng.normal(size=shape).astype(np.float64)
        variables = np.asarray(sorted(coords), dtype=np.int32)
        full = fullmod.build_operators(base, variables)
        small = aonly.build_a_only(base, variables)
        assert np.array_equal(small.xx_rc, full.xx_rc)
        assert np.array_equal(small.zz_rc, full.zz_rc)
        assert np.array_equal(small.xz_rc, full.xz_rc)
        assert np.array_equal(small.rhs_a, full.rhs_a)
        assert np.array_equal(small.diag_a, full.diag_a)
        x = rng.normal(size=small.n)
        y = rng.normal(size=small.n_a)
        av1, av2 = small.matvec_a(x), full.matvec_a(x)
        at1, at2 = small.rmatvec_a(y), full.rmatvec_a(y)
        assert np.array_equal(av1, av2)
        assert np.array_equal(at1, at2)
        lhs, rhs = float(np.dot(av1, y)), float(np.dot(x, at1))
        assert abs(lhs-rhs) <= 1e-12 * max(1.0, abs(lhs), abs(rhs))
        fused_a = fusedmod.FusedNormalAction(small).a_normal(x)
        fused_full = fusedmod.FusedNormalAction(full).a_normal(x)
        assert np.allclose(fused_a, fused_full, rtol=0.0, atol=1e-12)
        fixtures.append({
            "shape": list(shape), "variables": len(coords),
            "A_rows": small.n_a,
            "anchor_counts": {"xx": len(small.xx_rc), "zz": len(small.zz_rc), "xz": len(small.xz_rc)},
            "rhs_exact": True, "diag_exact": True, "A_exact": True, "AT_exact": True,
            "adjoint_relative_error": abs(lhs-rhs)/max(1.0, abs(lhs), abs(rhs)),
            "fused_normal_max_abs": float(np.max(np.abs(fused_a-fused_full), initial=0.0)),
        })
    # Invalid input controls exercise the actual A-only domain validator.
    try:
        aonly.build_a_only(np.zeros((2, 2)), np.asarray([[1, 1], [0, 0]], dtype=np.int32))
    except ValueError:
        bad_order_rejected = True
    else:
        raise AssertionError("unsorted variable domain was accepted")
    try:
        aonly.build_a_only(np.asarray([[0.0, np.nan]]), np.asarray([[0, 0]], dtype=np.int32))
    except ValueError:
        nonfinite_base_rejected = True
    else:
        raise AssertionError("nonfinite base was accepted")
    return {"status": "PASS_A_ONLY_FIXTURES", "global_arrays_loaded": False,
            "full_operator_sha256": OP_SHA, "fused_normal_sha256": FUSED_SHA,
            "cases": fixtures, "negative_controls": {
                "unsorted_variables_rejected": bad_order_rejected,
                "nonfinite_base_rejected": nonfinite_base_rejected}}


if __name__ == "__main__":
    import json
    print(json.dumps(run_fixtures(), indent=2))

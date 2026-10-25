from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy import sparse


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OPERATOR = HERE / "structured_operator.py"
EV88 = ROOT / "prototype.py"
CP = ROOT / "face-slope-cone-pilot" / "pilot.py"
FIXTURE_REPORT = HERE / "fixture-report.json"
EXPECTED = {
    OPERATOR: "d3017e58bbae3b71c891fab6892a5bf8d9386ae8a51a451a94c9b05769ac750a",
    EV88: "5b4b8f08e5205e1f9cc90bcc8e82e61dade45bb82bd22da8ee69303aa4475cc4",
    CP: "d743f5006e0aa6606024a3c3291a74cb52b78f76c1aa5c6dfd95cdd26cdc9d2a",
    FIXTURE_REPORT: "8b877d0fbce0566b8c6691f75bc7c0b2a0d9c98eeee24deca2bdcd6166833c28",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load pinned reference: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def max_abs(value) -> float:
    return float(np.max(np.abs(np.asarray(value)), initial=0.0))


def scalar_d8_reference(base: np.ndarray):
    h, w = base.shape
    pairs = []
    exempt = []
    for r in range(h):
        for c in range(w):
            neighbors = sorted(
                (rr, cc)
                for rr in range(max(0, r - 1), min(h, r + 2))
                for cc in range(max(0, c - 1), min(w, c + 2))
                if (rr, cc) != (r, c)
            )
            if not neighbors:
                continue
            minimum = min(float(base[p]) for p in neighbors)
            if float(base[r, c]) < minimum:
                exempt.append((r, c))
            else:
                witness = min(p for p in neighbors if float(base[p]) == minimum)
                pairs.append((r * w + c, witness[0] * w + witness[1]))
    return pairs, exempt


def case(base, coordinates, tag, operator_module, ev88, cp):
    nodes = np.asarray(sorted(map(tuple, np.asarray(coordinates).tolist())), dtype=np.int32).reshape(-1, 2)
    op = operator_module.build_operators(base, nodes)

    stencils = ev88.all_stencils(base.shape, nodes)
    records = ev88.row_records(base, nodes, stencils)
    A, rhs_a = ev88.csr_from_records(records, len(nodes))
    witnesses, exempt = cp.d8_witnesses(base)
    C, d_c = cp.build_d8(base, nodes, witnesses)
    G, k_g, *_ = cp.build_face_operator(base, nodes)

    if (op.n_a, op.n_c, op.n_g) != (A.shape[0], C.shape[0], G.shape[0]):
        raise AssertionError("operator row counts differ from pinned CP CSR")

    expected_xx = np.asarray([(r, c) for kind, r, c in stencils if kind == "xx"], dtype=np.int32).reshape(-1, 2)
    expected_zz = np.asarray([(r, c) for kind, r, c in stencils if kind == "zz"], dtype=np.int32).reshape(-1, 2)
    expected_xz = np.asarray([(r, c) for kind, r, c in stencils if kind == "xz"], dtype=np.int32).reshape(-1, 2)
    for actual, expected, label in ((op.xx_rc, expected_xx, "xx"), (op.zz_rc, expected_zz, "zz"), (op.xz_rc, expected_xz, "xz")):
        if not np.array_equal(actual, expected):
            raise AssertionError(f"{label} stencil row ordering differs from EV88")

    scalar_pairs, scalar_exempt = scalar_d8_reference(base)
    actual_pairs = list(zip(op.d8_centers.tolist(), op.d8_witnesses.tolist()))
    if actual_pairs != scalar_pairs or [tuple(x) for x in exempt] != scalar_exempt:
        raise AssertionError("D8 witness/exemption rows differ from independent scalar lex reference")

    rng = np.random.default_rng(9182 + tag)
    x = rng.normal(size=len(nodes))
    ya = rng.normal(size=A.shape[0])
    yc = rng.normal(size=C.shape[0])
    yg = rng.normal(size=G.shape[0])
    errors = {
        "A_matvec": max_abs(op.matvec_a(x) - A @ x),
        "A_rmatvec": max_abs(op.rmatvec_a(ya) - A.T @ ya),
        "C_matvec": max_abs(op.matvec_c(x) - C @ x),
        "C_rmatvec": max_abs(op.rmatvec_c(yc) - C.T @ yc),
        "G_matvec": max_abs(op.matvec_g(x) - G @ x),
        "G_rmatvec": max_abs(op.rmatvec_g(yg) - G.T @ yg),
        "A_rhs": max_abs(op.rhs_a - rhs_a),
        "C_rhs": max_abs(op.d_c - d_c),
        "G_affine_k": max_abs(op.k_g - k_g),
        "A_diagonal": max_abs(op.diag_a - np.asarray(A.multiply(A).sum(axis=0)).ravel()),
        "C_diagonal": max_abs(op.diag_c - np.asarray(C.multiply(C).sum(axis=0)).ravel()),
        "G_diagonal": max_abs(op.diag_g - np.asarray(G.multiply(G).sum(axis=0)).ravel()),
    }
    rho = 0.61
    H = (A.T @ A + rho * (sparse.eye(len(nodes), format="csr") + C.T @ C + G.T @ G)).tocsr()
    errors["normal_operator"] = max_abs(op.normal_operator(rho) @ x - H @ x)
    errors["normal_diagonal"] = max_abs(op.normal_diagonal(rho) - H.diagonal())
    rhs_probe = rng.normal(size=A.shape[0])
    zi = rng.normal(size=len(nodes))
    zc = rng.normal(size=C.shape[0])
    zg = rng.normal(size=G.shape[0])
    normal_rhs = A.T @ rhs_probe + rho * (zi + C.T @ zc + G.T @ (zg - k_g))
    errors["normal_affine_rhs"] = max_abs(op.normal_rhs(rhs_probe, zi, zc, zg, rho) - normal_rhs)

    if max(errors.values(), default=0.0) > 1e-10:
        raise AssertionError(f"CP mismatch for {base.shape}/{len(nodes)} vars: {errors}")
    return {
        "shape": list(base.shape),
        "variables": len(nodes),
        "rows": {"A": A.shape[0], "C": C.shape[0], "G": G.shape[0]},
        "d8_rows": len(witnesses),
        "strict_minimum_exemptions": len(exempt),
        "max_abs_errors": errors,
    }


def run():
    readset = {str(p): sha256(p) for p in EXPECTED}
    for path, expected in EXPECTED.items():
        if readset[str(path)] != expected:
            raise RuntimeError(f"source pin mismatch: {path}")
    opm = load_module("review_structured_operator", OPERATOR)
    ev88 = load_module("review_ev88_reference", EV88)
    cp = load_module("review_cp_reference", CP)

    shapes = [(1, 7), (2, 4), (2, 2), (3, 2), (3, 3), (4, 5), (5, 7), (7, 4), (9, 11)]
    cases = []
    for index, shape in enumerate(shapes):
        h, w = shape
        rr, cc = np.indices(shape)
        # Float32-promoted data reproduces the plateau/tie behavior of the source domain.
        base = np.asarray(0.3 * rr * rr + 0.2 * cc + np.sin(rr + cc), dtype=np.float32).astype(np.float64)
        if h >= 3 and w >= 3:
            base[1, 1] = base[0, 0] = base[0, 2] = np.float32(1.0)
        if index % 2:
            mask = np.zeros(shape, dtype=bool)
            mask[0, :] = mask[-1, :] = True
            mask[:, 0] = mask[:, -1] = True
            if h > 2 and w > 2:
                mask[h // 2, w // 2] = True
        else:
            mask = np.ones(shape, dtype=bool)
        coordinates = np.column_stack(np.nonzero(mask))
        cases.append(case(base, coordinates, index, opm, ev88, cp))

    sparse_cases = [
        ((6, 8), [(0, 0)]),
        ((6, 8), [(0, 0), (0, 7)]),
        ((6, 8), [(0, 0), (0, 7), (5, 3)]),
        ((4, 4), [(0, 0), (1, 1), (3, 3)]),
        ((1, 5), [(0, 2)]),
    ]
    for index, (shape, coords) in enumerate(sparse_cases, start=20):
        h, w = shape
        rr, cc = np.indices(shape)
        base = np.asarray(2.0 + 0.07 * rr - 0.11 * cc + 0.03 * rr * cc, dtype=np.float32).astype(np.float64)
        cases.append(case(base, coords, index, opm, ev88, cp))

    invalid = []
    for label, base, variables in (
        ("empty_variables", np.zeros((3, 4)), np.empty((0, 2), dtype=np.int32)),
        ("all_fixed_domain", np.ones((3, 4)), np.empty((0, 2), dtype=np.int32)),
    ):
        try:
            opm.build_operators(base, variables)
        except ValueError:
            invalid.append({"case": label, "rejected": True})
        else:
            raise AssertionError(f"invalid empty domain accepted: {label}")

    # Explicit edge tie: center [1,1] has equal minimum neighbors [0,0] and [0,2].
    tie_base = np.full((3, 3), 9.0, dtype=np.float32).astype(np.float64)
    tie_base[0, 0] = tie_base[0, 2] = 1.0
    tie_base[1, 1] = 4.0
    tie_op = opm.build_operators(tie_base, np.asarray([[1, 1]], dtype=np.int32))
    tie_row = int(np.flatnonzero(tie_op.d8_centers == 4)[0])
    if int(tie_op.d8_witnesses[tie_row]) != 0:
        raise AssertionError("explicit D8 equal-minimum tie did not choose row-major [0,0]")

    # Recheck after the fixture pass to bind the result to a stable source set.
    readset_end = {str(p): sha256(p) for p in EXPECTED}
    if readset != readset_end:
        raise RuntimeError("source drift during independent fixture run")
    worst = max(max(c["max_abs_errors"].values()) for c in cases)
    return {
        "schema": "matrix-free-operator-independent-review.v1",
        "status": "PASS_STRUCTURED_OPERATOR_INDEPENDENT_REVIEW",
        "operator_sha256": readset[str(OPERATOR)],
        "fixture_report_sha256": readset[str(FIXTURE_REPORT)],
        "references": {str(EV88): readset[str(EV88)], str(CP): readset[str(CP)]},
        "source_readset_start": readset,
        "source_readset_end": readset_end,
        "fixtures": {
            "cp_csr_shapes": cases,
            "sparse_variable_counts_1_2_3": True,
            "edge_dimensions_1_2_3": True,
            "d8_scalar_lex_reference_all_centers": True,
            "explicit_equal_minimum_tie_chooses_row_major": True,
            "empty_and_all_fixed_rejected": invalid,
            "max_abs_error": worst,
        },
        "limitations": [
            "Synthetic domains only; no global raster action or solver was run.",
            "Resource use and physical-memory behavior remain unmeasured.",
            "The normal_rhs interface should document that split variables supplied to it are already adjusted by their duals (z-u).",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, allow_nan=False))

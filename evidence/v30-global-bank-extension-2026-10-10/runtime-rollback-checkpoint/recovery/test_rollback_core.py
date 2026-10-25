"""Small independent fixtures for monotonic rollback primitives.

These exercise production functions against the pinned EV87 oracle on small
arrays only. They never load or mutate the 2048x2048 terrain.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rollback_core as rc
EV87_PATH=Path(r'E:\DayZ-Baltic-Build\v30-global-strict-bank-relief-20261010\review-independent\verify_ev87.py')
EV87_SHA='964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27'
OP_SHA='d3017e58bbae3b71c891fab6892a5bf8d9386ae8a51a451a94c9b05769ac750a'

def _load_ev87_functions():
    source=EV87_PATH.read_bytes()
    if hashlib.sha256(source).hexdigest()!=EV87_SHA:raise AssertionError('EV87 oracle source pin drift')
    tree=ast.parse(source.decode('utf-8-sig'),filename=str(EV87_PATH))
    names={'triangle_normals','edge_angles','edge_vertex_slices','incident_any'}
    selected=[node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in names]
    if {n.name for n in selected}!=names:raise AssertionError('EV87 oracle functions unavailable')
    namespace={'np':np,'__name__':'ev87_formula_oracle'}
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(EV87_PATH),'exec'),namespace)
    return SimpleNamespace(**{name:namespace[name] for name in names})


EV87=_load_ev87_functions()


def _hinge_incident_nodes(mask,kind):
    if kind=='diag': offsets=((0,0),(0,1),(1,0),(1,1));extra=(1,1)
    elif kind=='vertical': offsets=((0,0),(0,1),(1,1),(1,2));extra=(1,2)
    else: offsets=((0,0),(1,0),(1,1),(2,1));extra=(2,1)
    nodes=np.zeros((mask.shape[0]+extra[0],mask.shape[1]+extra[1]),dtype=bool)
    for dr,dc in offsets:nodes[dr:dr+mask.shape[0],dc:dc+mask.shape[1]]|=mask
    return nodes


def _expected_new_hinges(base, candidate):
    b = dict(EV87.edge_angles(base))
    h = dict(EV87.edge_angles(candidate))
    counts = {}
    marks = np.zeros(base.shape, dtype=bool)
    for kind in ("diag", "vertical", "horizontal"):
        mask = (b[kind] <= 30.0) & (h[kind] > 30.0)
        counts[kind] = int(mask.sum())
        marks |= _hinge_incident_nodes(mask, kind)
    return counts, marks


def _hinge_compare(base, candidate, chunk_rows):
    changed = candidate != base
    marked = np.zeros(base.shape, dtype=bool)
    got = rc.rollback_new_hinges_over30(base, candidate, changed, marked, chunk_rows)
    counts, expected = _expected_new_hinges(base, candidate)
    assert got["diag"] == counts["diag"]
    assert got["vertical"] == counts["vertical"]
    assert got["horizontal"] == counts["horizontal"]
    assert np.array_equal(marked, expected & changed)


def test_hinge_chunking_matches_ev87_multiple_shapes_and_boundaries():
    rng = np.random.default_rng(7102026)
    for shape in ((3, 3), (4, 7), (9, 5), (13, 17)):
        r, c = np.indices(shape)
        base = (0.21 * r - 0.13 * c + 0.002 * r * c).astype(np.float32)
        candidate = base.copy()
        # Include edge, interior, and chunk-boundary changes.
        points = [(0, 0), (shape[0] - 1, shape[1] - 1),
                  (shape[0] // 2, shape[1] // 2)]
        for rr, cc in points:
            candidate[rr, cc] += np.float32(rng.choice([-8.0, -3.0, 3.0, 8.0]))
        for chunk_rows in (1, 2, 3, 8):
            _hinge_compare(base, candidate, chunk_rows)


def test_flat_baseline_has_no_new_hinges_and_spike_is_rolled_back():
    base = np.zeros((7, 8), dtype=np.float32)
    changed = base.copy()
    changed[3, 4] = 5.0
    _hinge_compare(base, changed, 2)
    counts, marks = _expected_new_hinges(base, changed)
    assert sum(counts.values()) > 0
    assert marks[3, 4]


def test_face_cone_reverts_all_changed_corners_and_baseline_is_feasible():
    rr,cc=np.indices((5,6))
    base=(.15*rr-.11*cc+.003*rr*cc).astype(np.float32)
    nw,ne,sw,se=base[:-1,:-1].astype(np.float64),base[:-1,1:].astype(np.float64),base[1:,:-1].astype(np.float64),base[1:,1:].astype(np.float64)
    # Independent spelling of prepare_global_dry_bounds.py's per-face radii.
    radii=np.stack((np.sqrt((ne-nw)**2+(ne-se)**2),np.sqrt((se-sw)**2+(nw-sw)**2)),axis=-1)
    assert np.array_equal(np.stack(rc._face_gradient_pair(base.astype(np.float64)),axis=-1),radii)
    no_change = base.copy()
    changed = no_change != base
    rollback = np.zeros_like(changed)
    out = rc.rollback_face_cones(base, no_change, changed, rollback, radii, 1)
    assert out["bad_cells"] == 0 and not rollback.any()

    trial = base.copy()
    trial[2, 3] = 2.0
    changed = trial != base
    rollback = np.zeros_like(changed)
    out = rc.rollback_face_cones(base, trial, changed, rollback, radii, 2)
    assert out["bad_cells"] > 0
    assert rollback[2, 3]
    assert np.count_nonzero(rollback) == 1  # only changed incident nodes are selected


def test_d8_witness_marks_changed_endpoints_and_ignores_fixed_ones():
    base = np.array([[0, 1, 2], [0, 1, 2], [0, 1, 2]], dtype=np.float32)
    trial = base.copy()
    trial[1, 1] = -1.0
    changed = trial != base
    rollback = np.zeros_like(changed)
    centers = np.array([4, 5], dtype=np.int32)
    witnesses = np.array([3, 4], dtype=np.int32)
    # Row 0 fails at center 4 vs witness 3; center 5 vs 4 is also checked.
    info = rc.rollback_d8(base, trial, changed, rollback, centers, witnesses)
    assert info["bad_rows"] == 1
    assert rollback[1, 1]
    assert not rollback[1, 0]  # fixed witness is never marked for rollback


def test_chunked_d8_witnesses_match_pinned_full_operator_ties_and_edges():
    op_path=HERE.parent / "global-structured-operator" / "structured_operator.py"
    if hashlib.sha256(op_path.read_bytes()).hexdigest()!=OP_SHA:raise AssertionError('structured operator oracle pin drift')
    spec=importlib.util.spec_from_file_location("structured_operator_oracle",op_path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    for shape in ((1,1),(2,4),(5,7),(11,9)):
        rng=np.random.default_rng(shape[0]*100+shape[1])
        h=rng.integers(-2,3,size=shape).astype(np.float32)
        expected=module.d8_witness_arrays(h)
        for chunk in (1,2,4,32):
            calls=[]
            actual=rc.d8_witness_arrays_chunked(h,chunk,lambda *x:calls.append(x))
            assert np.array_equal(actual[0],expected[0])
            assert np.array_equal(actual[1],expected[1])
            assert calls  # guard is polled at each row chunk


def test_monotone_round_returns_baseline_when_all_changed_nodes_are_incident():
    base = np.zeros((7, 8), dtype=np.float32)
    trial = base.copy()
    trial[3, 4] = 5.0
    centers = np.empty(0, dtype=np.int32)
    witnesses = np.empty(0, dtype=np.int32)
    radii = np.full((6, 7, 2), 1e-6, dtype=np.float64)
    h, changed, report = rc.rollback_round(base, trial, centers, witnesses, radii, 2)
    assert report["changed_before"] == 1
    assert report["changed_after"] == 0
    assert not changed.any() and np.array_equal(h, base)


def test_rollback_cascade_rechecks_after_each_monotone_round():
    rng=np.random.default_rng(0);shape=(12,13)
    base=(rng.normal(size=shape).astype(np.float32)*.1)
    radii=np.stack(rc._face_gradient_pair(base.astype(np.float64)),axis=-1)+100.0
    centers,witnesses=rc.d8_witness_arrays_chunked(base,4)
    trial=base.copy();mask=rng.random(shape)<.18
    trial[mask]+=rng.choice(np.array([-6.,-3.,3.,6.],np.float32),size=int(mask.sum()))
    before=int(np.count_nonzero(trial!=base));first,changed1,report1=rc.rollback_round(base,trial,centers,witnesses,radii,2)
    assert report1['changed_after']==1 and report1['changed_after']<before
    second,changed2,report2=rc.rollback_round(base,first.copy(),centers,witnesses,radii,2)
    assert report2['changed_after']==0 and report2['changed_after']<report1['changed_after']
    assert not changed2.any() and np.array_equal(second,base)


def test_constraint_failure_with_only_fixed_incident_vertices_fails_closed():
    base=np.zeros((4,4),dtype=np.float32)
    trial=base.copy();trial[0,3]=0.001  # away from the deliberately invalid first cell
    radii=np.full((3,3,2),1.0,dtype=np.float64);radii[0,0,0]=-1.0
    try:
        rc.rollback_round(base,trial,np.empty(0,np.int32),np.empty(0,np.int32),radii,1)
    except RuntimeError as exc:
        assert 'no changed incident vertex' in str(exc)
    else:
        raise AssertionError('fixed-only failing constraint did not fail closed')


def test_clip_is_inside_inward_float32_box_and_rejects_bad_box():
    lo = np.array([-1.0, 0.25, -2.0], dtype=np.float32)
    hi = np.array([1.0, 0.75, 2.0], dtype=np.float32)
    got = rc.clip_solution_float32(np.array([-3., .5, 4.]), lo, hi)
    assert got.dtype == np.float32
    assert np.all(got >= lo) and np.all(got <= hi)
    try:
        rc.clip_solution_float32(np.zeros(2), np.array([1, 0], np.float32), np.array([0, 1], np.float32))
    except ValueError:
        pass
    else:
        raise AssertionError("infeasible inward box was accepted")


def run_all():
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    for test in tests:
        test()
    return {"passed": len(tests), "tests": [t.__name__ for t in tests]}


if __name__ == "__main__":
    print(run_all())

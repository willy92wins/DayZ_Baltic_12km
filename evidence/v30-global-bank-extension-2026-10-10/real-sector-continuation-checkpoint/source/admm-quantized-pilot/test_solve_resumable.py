"""Small, synthetic cut/resume equivalence fixture for solve_resumable.py."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np

import solve_resumable as resumable


def run_fixture():
    frozen = resumable.load_original()
    if frozen.MAX_ITER != 10000:
        raise AssertionError(f'original default changed: {frozen.MAX_ITER}')
    prior = frozen.load_prior()
    base, nodes, A, rhs, C, d, witnesses, exempt, centers, lo, hi, x0, records = \
        frozen.problem(prior, 'reference49')

    # Continuous reference uses the untouched source and only shortens its
    # in-memory loop boundary for this synthetic comparison; no source edits.
    frozen.MAX_ITER = 177
    x_full, diag_full, history_full, state_full = frozen.solve(
        A, rhs, C, d, lo, hi, x0, 60.0, lambda _row: None)

    x_50, diag_50, history_50, state_50 = resumable.solve(
        A, rhs, C, d, lo, hi, x0, 60.0, lambda _row: None,
        stop_iteration=50)
    if diag_50['iteration'] != 50 or diag_50['status'] != 'ITERATION_LIMIT':
        raise AssertionError(f'first chunk did not stop at 50: {diag_50}')
    x_resume, diag_resume, history_resume, state_resume = resumable.solve(
        A, rhs, C, d, lo, hi, x0, 60.0, lambda _row: None,
        state=state_50, stop_iteration=177)

    vector_fields = ('x64', 'y_box', 'y_d8', 'z_box', 'z_d8')
    exact_vectors = all(np.array_equal(
        state_resume.get(key, x_resume if key == 'x64' else None),
        state_full.get(key, x_full if key == 'x64' else None))
        for key in vector_fields)
    numeric_fields = ('iteration', 'cg_iterations', 'rho', 'primal', 'dual',
                      'eps_primal', 'eps_dual', 'stationarity', 'status', 'rho_updates')
    diagnostics_equal = all(diag_resume[k] == diag_full[k] for k in numeric_fields)
    if not exact_vectors or not diagnostics_equal:
        raise AssertionError({
            'vectors_exact': exact_vectors,
            'diagnostics_equal': diagnostics_equal,
            'resume': {k: diag_resume.get(k) for k in numeric_fields},
            'continuous': {k: diag_full.get(k) for k in numeric_fields},
        })

    # State validation negatives: shape, finiteness, rho, counters, and sets.
    bad_states = {}
    def expect_reject(name, mutate):
        bad = copy.deepcopy(state_50); mutate(bad)
        try:
            resumable.validate_state(bad, A.shape[1], C.shape[0], lo, hi, d)
        except (ValueError, TypeError):
            bad_states[name] = True
        else:
            bad_states[name] = False
            raise AssertionError(f'malformed state accepted: {name}')
    expect_reject('wrong_dual_shape', lambda q: q.update(y_box=q['y_box'][:-1]))
    expect_reject('nonfinite_x', lambda q: q['x64'].__setitem__(0, np.nan))
    expect_reject('rho_zero', lambda q: q.update(rho=0.0))
    expect_reject('bool_iteration', lambda q: q.update(iteration=True))
    expect_reject('negative_cg_count', lambda q: q.update(cg_iterations=-1))
    expect_reject('infeasible_z_box', lambda q: q['z_box'].__setitem__(0, hi[0]+1.0))
    expect_reject('infeasible_z_d8', lambda q: q['z_d8'].__setitem__(0, d[0]-1.0))
    real_scale_state = copy.deepcopy(state_50)
    real_scale_state['cg_iterations'] = 170910
    resumable.validate_state(real_scale_state, A.shape[1], C.shape[0], lo, hi, d)

    # A scaled/unscaled dual mix-up is semantically numeric, so it cannot be
    # inferred from shape/finiteness. This negative must diverge from reference.
    wrong_dual = copy.deepcopy(state_50)
    wrong_dual['y_box'] *= 2.0
    wrong_dual['y_d8'] *= 2.0
    x_wrong, diag_wrong, _, _ = resumable.solve(
        A, rhs, C, d, lo, hi, x0, 60.0, lambda _row: None,
        state=wrong_dual, stop_iteration=177)
    dual_misconversion_detected = not np.array_equal(x_wrong, x_full)
    if not dual_misconversion_detected:
        raise AssertionError('dual mis-conversion negative did not diverge')

    # Global ceiling and explicit-extension rules are checked without solving.
    ceiling_rejected = False
    try:
        resumable.solve(A, rhs, C, d, lo, hi, x0, 60.0, lambda _row: None,
                        stop_iteration=10001)
    except ValueError:
        ceiling_rejected = True
    if not ceiling_rejected:
        raise AssertionError('no-state extension beyond original 10,000 was accepted')
    max_budget_rejected = False
    try:
        resumable.solve(A, rhs, C, d, lo, hi, x0, 600.001, lambda _row: None,
                        stop_iteration=1)
    except ValueError:
        max_budget_rejected = True
    if not max_budget_rejected:
        raise AssertionError('budget above 600 seconds was accepted')
    extra_budget_rejected = False
    try:
        resumable.solve(A, rhs, C, d, lo, hi, x0, 600.0,
                        lambda _row: None, state=state_50,
                        stop_iteration=51)
    except ValueError:
        extra_budget_rejected = True
    if not extra_budget_rejected:
        raise AssertionError('continuation above 300 additional seconds was accepted')
    helper_symbols = all(callable(getattr(resumable, name, None)) for name in
                         ('load_closure', 'close_float32', 'check_float32', 'objective'))
    if not helper_symbols:
        raise AssertionError('frozen verifier/helper API is missing')

    return {
        'status': 'PASS_SYNTHETIC_CONTINUATION_EQUIVALENCE',
        'scope': 'reference49 only; no sector run or candidate',
        'continuous_iterations': diag_full['iteration'],
        'cut_iterations': diag_50['iteration'],
        'resumed_final_iteration': diag_resume['iteration'],
        'vectors_exact': exact_vectors,
        'numerical_diagnostics_exact': diagnostics_equal,
        'rho_updates': diag_full['rho_updates'],
        'malformed_state_rejections': bad_states,
        'production_scale_cg_count_accepted': True,
        'dual_misconversion_diverged': dual_misconversion_detected,
        'no_state_extension_rejected': ceiling_rejected,
        'budget_over_600_rejected': max_budget_rejected,
        'continuation_over_300_additional_rejected': extra_budget_rejected,
        'original_helper_api_exposed': helper_symbols,
        'objective_continuous': frozen.objective(A, rhs, x_full),
        'objective_resumed': frozen.objective(A, rhs, x_resume),
        'original_default_max_iter': 10000,
        'explicit_cumulative_iteration_ceiling': resumable.MAX_CUMULATIVE_ITERATION,
        'cumulative_budget_ceiling_s': resumable.MAX_CUMULATIVE_BUDGET_S,
    }


if __name__ == '__main__':
    report = run_fixture()
    output = Path(__file__).with_name('resume-fixture-report.json')
    output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n',
                      encoding='utf-8')
    print(json.dumps({'status': report['status'], 'report': str(output)}, indent=2))

"""Read-only schema fixture for the continuation consumer's lineage gate."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CONSUMER = HERE/'verify_real_sector_continuation.py'


def main():
    spec = importlib.util.spec_from_file_location('continuation_consumer_fixture', CONSUMER)
    consumer = importlib.util.module_from_spec(spec); spec.loader.exec_module(consumer)
    with np.load(HERE/'preflight-run-02/prepared.npz', allow_pickle=False) as z:
        prepared = {key: z[key] for key in z.files}
    with np.load(HERE/'solve-run-02/solver-state.npz', allow_pickle=False) as z:
        state = {key: z[key] for key in z.files}
    parent = json.loads((HERE/'solve-run-02/solve-result.json').read_text(encoding='utf-8'))
    diag = parent['diagnostics']; resource0 = parent['resource_measurement']
    dt = 0.1
    cont = {
        'schema':'real-sector-continuation.v1',
        'parent_result_path':str(consumer.PARENT_RESULT),
        'parent_result_sha256':consumer.PINS[consumer.PARENT_RESULT],
        'parent_state_path':str(HERE/'solve-run-02/solver-state.npz'),
        'parent_state_sha256':parent['solver_state_sha256'],
        'parent_preflight_path':str(HERE/'preflight-run-02/preflight.json'),
        'parent_preflight_sha256':parent['preflight_sha256'],
        'parent_prepared_path':str(HERE/'preflight-run-02/prepared.npz'),
        'parent_prepared_sha256':consumer.sha(HERE/'preflight-run-02/prepared.npz'),
        'parent_driver_sha256':parent['driver_sha256_after'],
        'start_iteration':10000,'end_iteration':10001,
        'start_cg_iterations':170910,'end_cg_iterations':170911,
        'rho_start':2.0,'rho_end':2.0,
        'rho_updates_start':diag['rho_updates'],'rho_updates_end':diag['rho_updates'],
        'stop_iteration':20000,'additional_limit_seconds':300.0,
        'solver_budget_cumulative_seconds':float(np.nextafter(diag['elapsed_s']+300.0,-np.inf)),
        'parent_solver_elapsed_seconds':diag['elapsed_s'],
        'total_solver_elapsed_seconds':diag['elapsed_s']+dt,
        'additional_solver_elapsed_seconds':dt,
        'parent_resource_elapsed_seconds':resource0['elapsed_seconds'],
        'additional_measured_resource_seconds':dt,
        'cumulative_measured_resource_seconds':resource0['elapsed_seconds']+dt,
    }
    result = {
        'continuation':cont,
        'diagnostics':{'iteration':10001,'cg_iterations':170911,'rho':2.0,
                       'elapsed_s':diag['elapsed_s']+dt,'rho_updates':diag['rho_updates']},
        'resource_measurement':{'prior_attempt_measured_seconds':resource0['elapsed_seconds'],
                                'elapsed_seconds':dt,
                                'cumulative_measured_seconds':resource0['elapsed_seconds']+dt,
                                'limit_violated':False,'peak_working_set_bytes':1000000000},
        'available_physical_bytes_before_solver':4*1024**3,
    }
    pre = {'continuation_parent':{
        'result_sha256':consumer.PINS[consumer.PARENT_RESULT],
        'state_sha256':parent['solver_state_sha256'],
        'preflight_sha256':parent['preflight_sha256'],
        'prepared_sha256':cont['parent_prepared_sha256'],
        'arrays_bitwise_identical_to_parent':True,'array_count':19}}
    hashes = {str(consumer.PARENT_RESULT):consumer.PINS[consumer.PARENT_RESULT]}
    good = consumer.verify_continuation_lineage(pre,result,prepared,state,hashes)
    if not all(good.values()):
        raise AssertionError(f'synthetic valid lineage rejected: {good}')
    bad = dict(result)
    bad['continuation'] = dict(cont, start_iteration=9999)
    rejected = consumer.verify_continuation_lineage(pre,bad,prepared,state,hashes)
    if rejected['continuation_counters_rho_budget_exact']:
        raise AssertionError('off-by-one parent iteration was accepted')
    return {'status':'PASS_SYNTHETIC_LINEAGE_GATE',
            'valid_lineage_checks':good,
            'invalid_start_iteration_rejected':True,
            'scope':'schema only; no continuation, solver, or candidate'}


if __name__ == '__main__':
    print(json.dumps(main(), sort_keys=True, indent=2))

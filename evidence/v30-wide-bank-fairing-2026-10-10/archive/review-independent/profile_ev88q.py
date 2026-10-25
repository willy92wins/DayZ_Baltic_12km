import importlib.util, sys, time, datetime
from pathlib import Path
consumer = Path(r'E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/review-independent/verify_ev88q.py')
spec = importlib.util.spec_from_file_location('ev88q_profiled_consumer', consumer)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def wrap(name):
    original = getattr(mod, name)
    def timed(*args, **kwargs):
        started = time.perf_counter()
        print(f"START {name} utc={datetime.datetime.now(datetime.timezone.utc).isoformat()}", flush=True)
        try:
            result = original(*args, **kwargs)
        except BaseException as exc:
            print(f"FAIL {name} elapsed_s={time.perf_counter()-started:.3f} error={type(exc).__name__}:{exc}", flush=True)
            raise
        details = ''
        if name == 'corridor_depth_report':
            details = f" all_covered={result['all_covered']} min_depth={result['global_minimum_nominal_depth_m']} features={[(x['id'],round(x['coverage_error_m2'],6),round(x['unknown_P_area_m2'],6),round(x['unknown_P_area_changed_between_pair_m2'] or 0,6),round(x['unknown_P_area_exact_between_pair_m2'] or 0,6),round(x['unknown_P_max_triangle_vertex_delta_m'] or 0,9),x['native_triangles']) for x in result['corridors']]}"
        elif name == 'coverage_and_compiled_gates':
            details = f" gates={result['gates']} scanned_cells={result['scanned_cells']} changed_support_cells={result['changed_support_cells']}"
        print(f"DONE {name} elapsed_s={time.perf_counter()-started:.3f}{details}", flush=True)
        return result
    setattr(mod, name, timed)

for function in ('checked_sources','verify_preflight','verify_authoring_receipt','topology_check','corridor_depth_report','high_bed_floor_report','coverage_and_compiled_gates'):
    wrap(function)
args = ['verify_ev88q.py', '--candidate', r'E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/candidate-terrain.npz',
        '--authoring-receipt', r'E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/authoring.json',
        '--report', r'E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/review-independent/ev88q-review.json']
sys.argv = args
started = time.perf_counter();print(f"RUN_START utc={datetime.datetime.now(datetime.timezone.utc).isoformat()} consumer_sha={mod.sha(consumer)}",flush=True)
rc=mod.main();print(f"RUN_END rc={rc} elapsed_s={time.perf_counter()-started:.3f}",flush=True);raise SystemExit(rc)

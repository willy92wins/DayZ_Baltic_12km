"""Describe two completed empty-server runs, without claiming causal capacity."""
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'evidence/regional-outline-v3'
EXPECTED = {
    'tile25': '2121e876507b5b5045d7bc76d56ea5499e99ae38792acafddf04ea662225c467',
    'tile12p5': '55d7163c06b53ebc8a5b9336a8b653e14d78eb06722b232d1a6550cd1581bebc',
}


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def describe(label, expected):
    launch = read_json(OUT / f'perf-{label}-launch.json')
    engine = read_json(OUT / f'perf-{label}-engine.json')
    process_file = OUT / f'perf-{label}-process.jsonl'
    raw = process_file.read_bytes()
    rows = [json.loads(line) for line in raw.decode('utf-8-sig').splitlines()]
    assert launch['pbo_sha256'].lower() == expected and launch['run_id']
    assert 'startNavmeshDataServer' not in launch['command']
    assert engine['status'] == 'PASS_COMPLETE_SERVER_BASELINE_MEASUREMENT'
    assert len(rows) == 170
    for i, row in enumerate(rows):
        assert row['sample'] == i and row['process_id'] == launch['process_id']
        assert row['start_utc'] == launch['start_utc']
        assert row['private_bytes'] > 0 and row['working_set_bytes'] > 0
        if i:
            assert 0 < row['elapsed_s'] - rows[i-1]['elapsed_s'] < 3
            assert row['cpu_total_s'] >= rows[i-1]['cpu_total_s']
    # Use only the later measured engine window. The first stale log footer,
    # which may remain briefly before this run opens its log, cannot qualify.
    settled = []
    for row in rows:
        fields = row.get('engine_last_line', '').split(';')
        if row['elapsed_s'] >= 60 and len(fields) == 12 and fields[0] == 'S' and 30 <= int(fields[1]) <= 120:
            settled.append(row)
    assert len(settled) >= 80, 'Insufficient measured steady-window samples'
    elapsed = settled[-1]['elapsed_s'] - settled[0]['elapsed_s']
    cpu = settled[-1]['cpu_total_s'] - settled[0]['cpu_total_s']
    return dict(run_id=launch['run_id'], pbo_sha256=expected,
                process_log_sha256=hashlib.sha256(raw).hexdigest(),
                engine_log_sha256=engine['log_sha256'],
                steady_process_samples=len(settled), steady_process_seconds=elapsed,
                resident_median_mib=statistics.median(r['working_set_bytes'] for r in settled) / 2**20,
                resident_peak_mib=max(r['working_set_bytes'] for r in rows) / 2**20,
                private_median_mib=statistics.median(r['private_bytes'] for r in settled) / 2**20,
                cpu_fraction_of_one_core=cpu / elapsed,
                mean_update_rate_hz=engine['mean_update_rate_hz'],
                max_update_timeslice_ms=engine['max_update_timeslice_ms'],
                updates_over50ms=engine['updates_over_50ms'])


if __name__ == '__main__':
    result = dict(status='COMPLETE_DESCRIPTIVE_PAIR_NOT_CAPACITY_BENCHMARK',
                  variants={label: describe(label, expected) for label, expected in EXPECTED.items()},
                  limits=['One run per variant on a shared desktop; uncontrolled background activity.',
                          'No CE, AI population or clients. No 80-100-player capacity claim.',
                          'Resident memory is not exclusively navmesh memory.',
                          'OnUpdate rate and timeslice are not CPU frame execution timings.'])
    dest = OUT / 'nav-cost-comparison.json'
    if dest.exists():
        raise ValueError('Fresh comparison output required')
    dest.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))

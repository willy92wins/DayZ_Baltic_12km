"""Validate completeness of a measured server baseline, not player capacity."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics


def verify(text):
    lines = text.splitlines()
    if len(lines) != 124 or lines[0] != 'BALTIC_TERRAIN_PERF_V1;BalticTrial;SERVER;NO_CE_NO_PLAYERS':
        raise ValueError('Missing, duplicate or wrong-world measurement')
    initial = lines[1].split(';')
    end = lines[-1].split(';')
    columns = 'columns;sample;tick;mission_ms;window_s;updates;sum_timeslice;max_timeslice;over50ms;fps_min64;fps_max64;fps_avg64'
    if len(initial) != 3 or initial[0] != 'INIT' or len(end) != 3 or end[:2] != ['END', '120'] or lines[2] != columns:
        raise ValueError('Missing initial/final marker')
    start = float(initial[1])
    rows = []
    previous_time = start
    previous_ms = int(initial[2])
    for expected, line in enumerate(lines[3:-1], 1):
        parts = line.split(';')
        if len(parts) != 12 or parts[0] != 'S' or int(parts[1]) != expected:
            raise ValueError('Wrong row count/order/shape')
        v = [float(x) for x in parts[2:]]
        tick, ms, duration, updates, sumdt, maxdt, over50, low, high, avg = v
        if not all(math.isfinite(x) for x in v) or not math.isfinite(start):
            raise ValueError('Nonfinite measurement')
        if tick <= previous_time or ms <= previous_ms or not 0.999 <= duration <= 3:
            raise ValueError('Discontinuous clock or excessive sample gap')
        if expected == 1 and tick-start < 31:
            raise ValueError('Warmup missing')
        if expected > 1 and abs(tick-previous_time-duration) > .002:
            raise ValueError('Sample interval mismatch')
        if updates < 1 or updates != int(updates) or over50 != int(over50) or not 0 <= over50 <= updates:
            raise ValueError('Invalid update counters')
        if sumdt <= 0 or maxdt <= 0 or maxdt > sumdt or not 0 < low <= avg <= high:
            raise ValueError('Invalid frame measurements')
        rows.append(v)
        previous_time, previous_ms = tick, ms
    if len(rows) != 120 or float(end[2]) != rows[-1][0]:
        raise ValueError('Incomplete final interval')
    elapsed = sum(r[2] for r in rows)
    return {'status': 'PASS_COMPLETE_SERVER_BASELINE_MEASUREMENT', 'samples': len(rows),
            'measurement_seconds': elapsed, 'warmup_seconds': rows[0][0]-rows[0][2]-start,
            'mean_update_rate_hz': sum(r[3] for r in rows)/elapsed,
            'native_fps_avg64_median': statistics.median(r[9] for r in rows),
            'native_fps_min64_minimum': min(r[7] for r in rows),
            'native_fps_avg64_range': [min(r[9] for r in rows), max(r[9] for r in rows)],
            'max_update_timeslice_ms': max(r[5] for r in rows)*1000,
            'updates_over_50ms': sum(int(r[6]) for r in rows),
            'limits': ['Isolated server, no CE/AI/players. Not 80-100-player capacity.',
                       'Native FPS are rolling 64-frame samples, not a frame-time percentile.',
                       'Headless native FPS may be stale or use another clock: do not equate this API value with OnUpdate rate or player performance.',
                       'OnUpdate timeslice is simulation delta, not CPU execution duration.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError('Fresh output required')
    raw = args.log.read_bytes()
    try:
        report = verify(raw.decode('utf-8-sig'))
    except (ValueError, IndexError) as exc:
        report = {'status': 'FAIL_MEASUREMENT', 'reason': str(exc)}
    report['log_sha256'] = hashlib.sha256(raw).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['status'].startswith('PASS') else 1)

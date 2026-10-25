"""Judge a native infected trajectory against the frozen Narva crossing gates."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def assess(text):
    lines = text.splitlines()
    if not lines or lines[0] != 'BALTIC_INFECTED_V1' or 'world=BalticTrial' not in lines:
        return {'status': 'INCONCLUSIVE', 'reason': 'Wrong or missing mission header'}
    stages = {n: [] for n in range(3)}
    reached = set()
    complete = False
    for line in lines[3:]:
        parts = line.split(';')
        if parts[0] == 'GOAL':
            continue
        if len(parts) != 11:
            return {'status': 'INCONCLUSIVE', 'reason': 'Malformed or truncated record'}
        try:
            vals = [float(p) for p in parts[1:10]]
        except ValueError:
            return {'status': 'INCONCLUSIVE', 'reason': 'Invalid numeric record'}
        if not all(math.isfinite(v) for v in vals):
            return {'status': 'FAIL', 'reason': 'Non-finite trajectory'}
        stage = int(vals[1])
        if vals[1] != stage or stage not in (0, 1, 2, 3):
            return {'status': 'INCONCLUSIVE', 'reason': 'Invalid stage identifier'}
        if parts[0] == 'COMPLETE_ALL_STAGES':
            complete = stage == 3
        if parts[0] == 'REACHED':
            reached.add(stage)
        if parts[0] in ('SPAWN', 'SAMPLE', 'REACHED', 'FAILED_ACTOR') and stage in stages:
            # t, x, y, z, health, mind; axis is recomputed from positions.
            stages[stage].append([vals[i] for i in (0, 2, 3, 4, 7, 8)])
    report = {}
    for stage, rows in stages.items():
        if len(rows) < 2:
            report[str(stage)] = {'passed': False, 'reason': 'No trajectory'}
            continue
        t, x, y, z, hp, mind = zip(*rows)
        d = [(a-2417.143)*.988364361-(b-6889.885)*.152104866 for a, b in zip(x, z)]
        cross = [(a-2417.143)*.152104866+(b-6889.885)*.988364361 for a, b in zip(x, z)]
        gaps = [b-a for a, b in zip(t, t[1:])]
        steps = [math.dist(a[1:4], b[1:4]) for a, b in zip(rows, rows[1:])]
        checks = {'completion_marker': stage in reached, 'time_order': min(gaps) >= 0,
                  'sample_gap_at_most_0_6s': max(gaps) <= .6, 'alive': min(hp) > 0,
                  'max_step_2_5m': max(steps) <= 2.5}
        if stage == 0:
            checks.update(control_start=d[0] <= -28, control_end=d[-1] <= -42, alert=any(1 <= m <= 4 for m in mind))
        else:
            span = [i for i, a in enumerate(d) if abs(a) <= 12.5]
            checks.update(start=(d[0] <= -28 if stage == 1 else d[0] >= 28),
                          end=(d[-1] >= 25 if stage == 1 else d[-1] <= -25),
                          span_sampled=len(span) >= 10,
                          on_deck=bool(span) and all(1.7 <= y[i] <= 2.4 for i in span),
                          within_bridge=bool(span) and all(abs(cross[i]) <= 2.5 for i in span))
        report[str(stage)] = {'passed': all(checks.values()), 'checks': checks,
                              'samples': len(rows), 'd_start_end': [d[0], d[-1]],
                              'max_step_m': max(steps), 'health_min': min(hp)}
    passed = complete and all(v['passed'] for v in report.values())
    return {'status': 'PASS_NATIVE_AI_BOTH_DIRECTIONS' if passed else 'INCONCLUSIVE_OR_FAILED_STAGE',
            'complete': complete, 'stages': report,
            'limit': 'One infected per stage in Narva; not regional AI, CE or load acceptance.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--log', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    r = assess(a.log.read_text())
    r['log_sha256'] = hashlib.sha256(a.log.read_bytes()).hexdigest()
    a.out.write_text(json.dumps(r, indent=2)+'\n')
    print(json.dumps(r, indent=2))
    raise SystemExit(0 if r['status'] == 'PASS_NATIVE_AI_BOTH_DIRECTIONS' else 1)


if __name__ == '__main__':
    main()

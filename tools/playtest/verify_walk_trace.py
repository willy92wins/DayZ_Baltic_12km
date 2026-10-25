"""Judge the actual server trajectory, not the client's requested input."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np


def assess(server, client_text):
    if server.ndim != 2 or server.shape[1] != 6 or len(server) < 2:
        return {'status': 'INCONCLUSIVE', 'reason': 'Missing server samples'}
    t, x, y, z, health, swim = server.T
    d = (x-2417.143)*.988364361 - (z-6889.885)*.152104866
    lateral = (x-2417.143)*.152104866 + (z-6889.885)*.988364361
    east = np.flatnonzero(d >= 28)
    back = np.array([], dtype=int)
    if len(east):
        back = np.flatnonzero((np.arange(len(d)) > east[0]) & (d <= -28))
    completion = 'COMPLETE_BOTH_DIRECTIONS;' in client_text
    if not len(east) or not len(back) or not completion:
        return {'status': 'INCONCLUSIVE', 'reason': 'No complete authoritative round trip',
                'server_samples': len(server), 'min_d': float(d.min()), 'max_d': float(d.max()),
                'client_completion': completion}
    end = back[0]
    segments = [d[:east[0]+1], d[east[0]:end+1]]
    gaps = []
    bridge_counts = []
    for segment in segments:
        values = np.sort(segment[(segment >= -13) & (segment <= 13)])
        bridge_counts.append(len(values))
        gaps.append(float(np.diff(values).max()) if len(values) > 1 else 999)
    bridge = np.abs(d[:end+1]) <= 12.5
    steps = np.sqrt(np.diff(x[:end+1])**2 + np.diff(z[:end+1])**2)
    checks = {
        'at_least_80_server_samples': bool(end+1 >= 80),
        'monotonic_time': bool(np.all(np.diff(t[:end+1]) > 0)),
        'starts_at_west': bool(d[0] <= -28),
        'both_spans_sampled': all(c >= 20 for c in bridge_counts),
        'bridge_sampling_gaps_under_1_5m': all(g <= 1.5 for g in gaps),
        'no_teleport_steps_over_2m': bool(np.all(steps <= 2)),
        'lateral_corridor_under_2_5m': bool(np.all(np.abs(lateral[:end+1]) < 2.5)),
        'feet_on_bridge_1_7_to_2_4m': bool(np.any(bridge) and np.all((y[:end+1][bridge] >= 1.7) & (y[:end+1][bridge] <= 2.4))),
        'alive_on_server': bool(np.all(health[:end+1] > 0)),
        'no_swimming_on_server': bool(np.all(swim[:end+1] == 0)),
    }
    return {'status': 'PASS_SERVER_ROUND_TRIP' if all(checks.values()) else 'FAIL',
            'checks': checks, 'server_samples': int(end+1),
            'bridge_samples_out_back': bridge_counts, 'max_sampling_gaps_m': gaps,
            'max_step_m': float(steps.max()), 'max_lateral_error_m': float(np.abs(lateral[:end+1]).max()),
            'bridge_y_range_m': [float(y[:end+1][bridge].min()), float(y[:end+1][bridge].max())] if np.any(bridge) else [],
            'server_health_min': float(health[:end+1].min()),
            'server_time_range_s': [float(t[0]), float(t[end])],
            'limit': 'Script-driven human locomotion with client and server overrides; not a manual-input, vehicle, AI navigation or load test.'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--server', type=Path, required=True)
    ap.add_argument('--client', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    with a.server.open(newline='') as f:
        reader = csv.reader(f, delimiter=';')
        if next(reader) != ['t', 'x', 'y', 'z', 'health', 'swim']:
            raise ValueError('Wrong server schema')
        data = np.array([[float(x) for x in row] for row in reader if row])
    result = assess(data, a.client.read_text())
    result['hashes'] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (a.server, a.client)}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'] == 'PASS_SERVER_ROUND_TRIP' else 1)


if __name__ == '__main__':
    main()

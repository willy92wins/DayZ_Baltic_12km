"""Rebase a frozen shore readback reference onto a new terrain without moving or reclassifying points.

Coordinates, kinds, pond planes, sites, mission and tolerances stay frozen; only the expected
ground is re-sampled on the native triangles of the new terrain (v30_common.tri_sample, the
sampler the engine readback matched to 0.0006 m). Before rebasing, the same sampler must
reproduce every stored expectation on the reference's own terrain; otherwise nothing is written.
"""
from pathlib import Path
import argparse
import hashlib
import json

import numpy as np

from v30_common import tri_sample


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reference', type=Path, required=True)
    ap.add_argument('--reference-terrain', type=Path, required=True)
    ap.add_argument('--terrain', type=Path, required=True)
    ap.add_argument('--expected-sha256', required=True)
    ap.add_argument('--world-pbo-sha256', required=True)
    ap.add_argument('--water-pbo-sha256', required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.exists(), 'Preserve prior fixtures'
    ref = json.loads(a.reference.read_text(encoding='utf-8-sig'))
    assert sha(a.reference_terrain) == ref['terrain_sha256'], 'Reference terrain differs from the frozen one'
    assert sha(a.terrain) == a.expected_sha256.lower(), 'Candidate terrain differs from the approved one'
    old = np.load(a.reference_terrain)['heights'].astype(float)
    new = np.load(a.terrain)['heights'].astype(float)
    xs = np.array([p['x'] for p in ref['points']])
    zs = np.array([p['z'] for p in ref['points']])
    stored = np.array([p['expected_ground_m'] for p in ref['points']])
    replay = tri_sample(old, xs, zs)
    replay_error = float(np.max(np.abs(replay - stored)))
    assert replay_error <= 1e-9, ('Sampler does not reproduce the frozen expectations', replay_error)
    rebased = tri_sample(new, xs, zs)
    changed = []
    for p, before, after in zip(ref['points'], stored, rebased):
        p['previous_ground_m'] = float(before)
        p['expected_ground_m'] = float(after)
        if after != before:
            changed.append(dict(id=p['id'], kind=p['kind'], before_m=float(before), after_m=float(after),
                                pond_plane_m=p['pond_plane_m']))
    parent = dict(reference_sha256=sha(a.reference), terrain_sha256=ref['terrain_sha256'],
                  world_pbo_sha256=ref.get('world_pbo_sha256'), water_pbo_sha256=ref.get('water_pbo_sha256'))
    ref.update(status='FROZEN_BEFORE_RUNTIME', terrain_sha256=a.expected_sha256.lower(),
               world_pbo_sha256=a.world_pbo_sha256.lower(), water_pbo_sha256=a.water_pbo_sha256.lower(),
               rebased_from=parent,
               rebase=dict(sampler='tools/terrain/v30_common.py tri_sample', replay_max_error_m=replay_error,
                           changed_points=len(changed), max_abs_change_m=max((abs(c['after_m'] - c['before_m'])
                                                                              for c in changed), default=0.0),
                           points=changed),
               limits=ref.get('limits', []) + ['Rebased expectation: same coordinates, kinds and planes as the parent '
                                               'reference; only expected ground follows the new terrain.'])
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(ref, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=ref['status'], replay_max_error_m=replay_error, changed_points=len(changed),
                          max_abs_change_m=ref['rebase']['max_abs_change_m'], out=str(a.out)), indent=2))


if __name__ == '__main__':
    main()

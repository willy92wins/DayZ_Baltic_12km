"""Preserve complete native cells supported by water outside a shore edit's class.

An unchanged water vertex does not preserve its triangles when an adjacent land
vertex moves. This guard is derived only from the frozen classification, never
from acceptance stations or candidate errors. It cannot enlarge an edit.
"""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from scipy.ndimage import binary_dilation
from finish_shores_v30 import discard_steeper_land_faces


def protected_support(cls, target_class):
    foreign = (cls > 0) & (cls != target_class)
    # Every foreign vertex belongs to four cells: preserve all their corners.
    return binary_dilation(foreign, structure=np.ones((3, 3), dtype=bool))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--candidate', type=Path, required=True)
    ap.add_argument('--source-sha', required=True)
    ap.add_argument('--candidate-sha', required=True)
    ap.add_argument('--target-class', type=int, default=3)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert not a.out.exists(), 'Preserve existing output'
    assert sha(a.source) == a.source_sha and sha(a.candidate) == a.candidate_sha, 'Input identity changed'
    with np.load(a.source) as f: base = dict(f)
    with np.load(a.candidate) as f: candidate = dict(f)
    assert base.keys() == candidate.keys()
    assert all(np.array_equal(v, candidate[k], equal_nan=True) for k, v in base.items() if k != 'heights')
    h = base['heights'].astype(float)
    proposed = candidate['heights'].astype(float)
    assert np.isfinite(proposed).all()
    guard = protected_support(base['cls'], a.target_class)
    reverted = (proposed != h) & guard
    proposed[guard] = h[guard]
    proposed, recovery = discard_steeper_land_faces(proposed, h, base['cls'])
    result = proposed.astype(base['heights'].dtype)
    changed = result != base['heights']
    assert not np.any(changed & guard)
    assert not np.any(changed & (candidate['heights'] == base['heights']))
    a.out.mkdir(parents=True)
    np.savez_compressed(a.out/'terrain_inland.npz', **{**base, 'heights': result})
    np.savez_compressed(a.out/'mask.npz', protected_support=guard, reverted=reverted)
    report = {'status': 'PENDING_INDEPENDENT_GATES', 'source_sha256': a.source_sha,
              'candidate_sha256': a.candidate_sha, 'target_class': a.target_class,
              'protected_vertices': int(guard.sum()), 'directly_reverted_vertices': int(reverted.sum()),
              'face_recovery': recovery, 'remaining_changed_vertices': int(changed.sum()),
              'output_sha256': sha(a.out/'terrain_inland.npz')}
    (a.out/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

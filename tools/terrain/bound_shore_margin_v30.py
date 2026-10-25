"""Bound a shore candidate by its original clearance to every incident water plane.

This is a conservative height bound, NOT a guarantee about outline normals or
shoreline topology. Acceptance remains with the independent frozen-station gates.
No station, failed coordinate, new class or new water level enters this producer.
"""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from v30_common import cell_planes
from finish_shores_v30 import discard_steeper_land_faces


def bound_margin(original, proposal, planes):
    clearance = np.full(original.shape, np.inf)
    nr, nc = planes.shape
    for dr, dc in ((0, 0), (0, 1), (1, 0), (1, 1)):
        target = (slice(dr, dr+nr), slice(dc, dc+nc))
        distance = np.abs(original[target]-planes)
        clearance[target] = np.fmin(clearance[target], distance)
    bound = .5*clearance
    delta = np.clip(proposal-original, -bound, bound)
    return original+delta, clearance


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--candidate', type=Path, required=True)
    ap.add_argument('--source-sha', required=True)
    ap.add_argument('--candidate-sha', required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.exists(), 'Fresh destination required'
    assert sha(a.source) == a.source_sha and sha(a.candidate) == a.candidate_sha
    with np.load(a.source) as f: base = dict(f)
    with np.load(a.candidate) as f: candidate = dict(f)
    assert base.keys() == candidate.keys()
    assert all(np.array_equal(v, candidate[k], equal_nan=True) for k, v in base.items() if k != 'heights')
    h, before = base['heights'].astype(float), candidate['heights'].astype(float)
    assert h.shape == (2048, 2048) and np.isfinite(h).all() and np.isfinite(before).all()
    planes = cell_planes(base['cls'], base['level'], sea_cut=.51)
    bounded, clearance = bound_margin(h, before, planes)
    clipped = np.abs(before-h) > .5*clearance
    # Round towards the source if nearest float32 would cross the exact bound.
    # Use the result's representable spacing, not the source's smaller ulp.
    rounded = bounded.astype(base['heights'].dtype)
    overshoot = np.abs(rounded.astype(float)-h) > .5*clearance
    rounded[overshoot] = np.nextafter(rounded[overshoot], base['heights'][overshoot])
    result, recovery = discard_steeper_land_faces(rounded, h, base['cls'])
    result = result.astype(base['heights'].dtype)
    changed = result != base['heights']
    assert not np.any(changed & (h == before)), 'Expanded edit'
    assert not np.any((result.astype(float)-h)*(before-h) < 0), 'Reversed edit'
    assert np.all(np.abs(result.astype(float)-h) <= .5*clearance)
    a.out.mkdir(parents=True)
    np.savez_compressed(a.out/'terrain_inland.npz', **{**base, 'heights': result})
    np.savez_compressed(a.out/'margin-clipped.npz', clipped=clipped)
    report = dict(status='PENDING_INDEPENDENT_GATES', source_sha256=a.source_sha,
                  candidate_sha256=a.candidate_sha, fraction=.5, sea_cut=.51,
                  capped_vertices=int(clipped.sum()), changed_vertices=int(changed.sum()),
                  inward_rounded_vertices=int(overshoot.sum()),
                  face_recovery=recovery, output_sha256=sha(a.out/'terrain_inland.npz'))
    (a.out/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

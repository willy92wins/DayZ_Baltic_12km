"""Raise the bed of chosen lakes V30 above the engine sea (BALTIC-018 probe).

The engine draws its sea wherever the terrain lies below the sea surface (0.65-0.85 m with the swell), also under a
lake whose water objects sit higher: 324,155 of 382,745 inland water vertices of the v5 terrain have the bed below
0.85 m (evidence/v30-v5-candidate-2026-10-05). Seen from the air such a lake splits into bands. This tool lifts the
bed of chosen standing bodies so that no sea is drawn under them, and changes nothing else.

Bodies: the census labelling (relevel_bodies_v30.label_bodies: classes 2 and 7, centimetre level, 8-connected). A body
is chosen by a point inside it (--at x,z, repeatable). Every vertex of a chosen body goes to
max(h, min(--floor, level - --min-depth)): beds only rise, a raised bed keeps at least --min-depth of water (beds that
were already shallower stay as they were), and classes, levels and every other vertex stay.
Output <out>/terrain_beds.npz (same keys as the input) and <out>/report.json.
Usage: raise_beds_v30.py --terrain IN.npz --out OUTDIR --at X,Z [--at X,Z ...] [--floor 1.00] [--min-depth 0.30]
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from relevel_bodies_v30 import label_bodies  # noqa: E402
from v30_common import N  # noqa: E402

SEA_CREST = 0.85


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--terrain', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--at', action='append', required=True, help='x,z of a point inside a body (game metres)')
    ap.add_argument('--floor', type=float, default=1.00)
    ap.add_argument('--min-depth', type=float, default=0.30)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=False)
    t0 = time.time()
    t = np.load(a.terrain)
    arrays = {k: t[k] for k in t.files}
    h0, cls, level = arrays['heights'], arrays['cls'], arrays['level']
    ids = label_bodies(cls, level)
    bodies = []
    chosen = np.zeros(cls.shape, bool)
    for spec in a.at:
        x, z = (float(v) for v in spec.split(','))
        r, c = int(round((12282 - z) / 6)), int(round(x / 6))
        assert 0 <= r < N and 0 <= c < N, spec
        i = int(ids[r, c])
        assert i > 0, 'no standing body at %s (cls %d)' % (spec, cls[r, c])
        b = ids == i
        chosen |= b
        lv = float(np.median(level[b]))
        bodies.append({'at': [x, z], 'id': i, 'vertices': int(b.sum()), 'level_m': round(lv, 3),
                       'bed_below_crest_before': int((h0[b] < SEA_CREST).sum()),
                       'bed_p5_p50_p95_before': np.percentile(h0[b], [5, 50, 95]).round(2).tolist()})
    target = np.minimum(np.float32(a.floor), level - np.float32(a.min_depth))
    h = h0.copy()
    raise_mask = chosen & (h0 < target)
    h[raise_mask] = target[raise_mask]
    for body in bodies:
        b = ids == body['id']
        body['raised'] = int((raise_mask & b).sum())
        body['bed_below_crest_after'] = int((h[b] < SEA_CREST).sum())
        body['bed_p5_p50_p95_after'] = np.percentile(h[b], [5, 50, 95]).round(2).tolist()
        r = raise_mask & b
        body['depth_min_raised_m'] = round(float((level[r] - h[r]).min()), 3) if r.any() else None
        body['depth_min_untouched_m'] = round(float((level[b & ~r] - h[b & ~r]).min()), 3) if (b & ~r).any() else None
    assert not np.any(h < h0), 'a bed went down'
    assert np.array_equal(h[~chosen], h0[~chosen]), 'a vertex outside the chosen bodies changed'
    arrays['heights'] = h.astype(h0.dtype)
    path = out / 'terrain_beds.npz'
    np.savez_compressed(path, **arrays)
    back = np.load(path)
    assert all(np.array_equal(back[k], arrays[k], equal_nan=back[k].dtype.kind == 'f') for k in arrays)
    report = {'status': 'BUILT_PENDING_ENGINE_VIEWS',
              'params': {'floor': a.floor, 'min_depth': a.min_depth, 'sea_crest': SEA_CREST},
              'bodies': bodies, 'raised_vertices': int(raise_mask.sum()),
              'raise_max_m': round(float((h - h0).max()), 3),
              'inputs': {a.terrain: sha(a.terrain), __file__: sha(__file__)},
              'output_sha256': sha(path), 'seconds': round(time.time() - t0, 1),
              'limits': ['Beds only; water objects, classes, levels and shores unchanged.',
                         'A probe of BALTIC-018, not a level policy.']}
    (out / 'report.json').write_text(json.dumps(report, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()

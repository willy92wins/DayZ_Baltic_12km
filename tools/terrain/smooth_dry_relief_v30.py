"""Bounded local smoothing of dry V30 relief; preserves authored water and engineering.

Pilot only until the independent consumer gates and engine views pass. Gaussian
local detail is removed, with its 180 m component subtracted before applying a
1 m cap. Water/banks, nature, road reserve/platforms, Narva, border and upland
summits remain exact; a quintic blend avoids a hard boundary at protections.
"""
from pathlib import Path
import argparse
import hashlib
import json
import time

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, maximum_filter

from finish_shores_v30 import discard_steeper_land_faces
from v30_common import grid_xz


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ease(v):
    t = np.clip(v, 0.0, 1.0)
    return t * t * t * (10.0 + t * (-15.0 + 6.0 * t))


def smooth(t, nature, high, sigma, max_shift=1.0, water_margin=36.0,
           blend=60.0, regional_scale=180.0):
    if not (0 < sigma < regional_scale and max_shift > 0 and blend > 0 and water_margin >= 12):
        raise ValueError('Invalid smoothing scales or displacement budget')
    h = t['heights'].astype(np.float64)
    if h.shape != (2048, 2048) or not np.isfinite(h).all():
        raise ValueError('Expected a finite native Baltic vertex grid')
    x, z = grid_xz()
    wet = (t['cls'] > 0) | t['water']
    near_water = distance_transform_edt(~wet, sampling=6.0) <= water_margin
    # Frozen before any smoothing: retain summit heights and positions at the
    # same regional scale used by the low-frequency displacement gate.
    summits = (high >= 0.5) & (h == maximum_filter(h, size=61, mode='nearest'))
    fixed = (near_water | t['platform'] | t['reserve'] | t['narva'] | t['beach']
             | nature | summits | (h < 1.4)
             | (np.hypot(x - 2417.1428225906, z - 6889.8850822322) <= 620.0)
             | (x < 66) | (x > 12216) | (z < 66) | (z > 12216))
    weight = ease(distance_transform_edt(~fixed, sampling=6.0) / blend)
    delta = gaussian_filter(h, sigma / 6.0, mode='nearest') - h
    delta -= gaussian_filter(delta, regional_scale / 6.0, mode='nearest')
    delta = weight * max_shift * np.tanh(delta / max_shift)
    delta -= weight * gaussian_filter(delta, regional_scale / 6.0, mode="nearest")
    candidate = h + np.clip(delta, -max_shift, max_shift)
    candidate[~fixed] = np.maximum(candidate[~fixed], 1.4)
    candidate[fixed] = h[fixed]
    candidate, recovery = discard_steeper_land_faces(candidate, h, t['cls'])
    out = candidate.astype(np.float32)
    if np.any(out[fixed] != t['heights'][fixed]):
        raise ValueError('A protected height changed')
    moved = out != t['heights']
    return out, fixed, summits, {'changed_vertices': int(moved.sum()),
                               'max_height_change_m': float(np.max(np.abs(out.astype(float) - h))),
                               'summits_preserved': int(summits.sum()), 'face_recovery': recovery}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--terrain', type=Path, required=True)
    ap.add_argument('--source-sha', required=True)
    ap.add_argument('--nature', type=Path, required=True)
    ap.add_argument('--relief', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--sigma', type=float, required=True)
    a = ap.parse_args()
    if a.out.exists() or sha(a.terrain) != a.source_sha:
        raise ValueError('Fresh output and exact input hash are required')
    started = time.monotonic()
    with np.load(a.terrain) as data:
        t = dict(data)
    with np.load(a.nature) as data:
        nature = data['reserve'].astype(bool)
    with np.load(a.relief) as data:
        high = data['high']
    out, fixed, summits, stats = smooth(t, nature, high, a.sigma)
    t['heights'] = out
    a.out.mkdir(parents=True)
    np.savez_compressed(a.out / 'terrain_dry.npz', **t)
    np.savez_compressed(a.out / 'masks.npz', fixed=fixed, summits=summits)
    report = {'status': 'BUILT_PENDING_INDEPENDENT_GATES_AND_ENGINE', 'params': {'sigma_m': a.sigma,
              'max_shift_m': 1.0, 'water_margin_m': 36.0, 'protection_blend_m': 60.0, 'regional_scale_m': 180.0},
              'inputs': {str(p): sha(p) for p in (a.terrain, a.nature, a.relief, Path(__file__))},
              'output_sha256': sha(a.out / 'terrain_dry.npz'), 'seconds': round(time.monotonic() - started, 2), **stats}
    (a.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
